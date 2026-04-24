from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.models import DataSource, SessionLocal
from app.schemas import DataSourceCreate, DataSourceUpdate, DataSource as DataSourceSchema
from app.connectors.hiveserver2 import HiveServer2Connector


class PaginatedResult(BaseModel):
    """分页返回结果（兼容前端）"""
    list: List[DataSourceSchema]
    total: int
    page: int
    pageSize: int

router = APIRouter(prefix="/datasources", tags=["datasources"])

# 数据源类型映射：前端别名 -> 后端内部类型
TYPE_MAPPING = {
    "hive": "hiveserver2",
    "hiveserver2": "hiveserver2",
    "presto": "trino",
    "trino": "trino",
    "impala": "impala",
    "spark": "spark",
    "jdbc": "jdbc",
}


def normalize_datasource_type(type_str: str) -> str:
    """标准化数据源类型，兼容前端别名"""
    return TYPE_MAPPING.get(type_str.lower(), type_str)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=PaginatedResult)
def list_datasources(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取数据源列表（分页）"""
    query = db.query(DataSource)
    
    # 关键词搜索
    if keyword:
        query = query.filter(DataSource.name.contains(keyword))
    
    # 获取总数
    total = query.count()
    
    # 分页
    datasources = query.order_by(DataSource.created_at.desc()) \
        .offset((page - 1) * pageSize) \
        .limit(pageSize) \
        .all()
    
    return PaginatedResult(
        list=datasources,
        total=total,
        page=page,
        pageSize=pageSize
    )


@router.get("/{datasource_id}", response_model=DataSourceSchema)
def get_datasource(datasource_id: int, db: Session = Depends(get_db)):
    """获取单个数据源"""
    datasource = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return datasource


@router.post("", response_model=DataSourceSchema)
def create_datasource(data: DataSourceCreate, db: Session = Depends(get_db)):
    """创建数据源"""
    # 检查名称是否已存在
    existing = db.query(DataSource).filter(DataSource.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="数据源名称已存在")

    # 标准化数据源类型，兼容前端别名（hive -> hiveserver2, presto -> trino）
    data_dict = data.dict()
    data_dict["type"] = normalize_datasource_type(data.type)
    datasource = DataSource(**data_dict)
    db.add(datasource)
    db.commit()
    db.refresh(datasource)
    return datasource


@router.put("/{datasource_id}", response_model=DataSourceSchema)
def update_datasource(datasource_id: int, data: DataSourceUpdate, db: Session = Depends(get_db)):
    """更新数据源"""
    datasource = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")

    for key, value in data.dict().items():
        setattr(datasource, key, value)

    db.commit()
    db.refresh(datasource)
    return datasource


@router.delete("/{datasource_id}")
def delete_datasource(datasource_id: int, db: Session = Depends(get_db)):
    """删除数据源"""
    datasource = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")

    db.delete(datasource)
    db.commit()
    return {"success": True, "message": "删除成功"}


@router.post("/{datasource_id}/test")
def test_connection(datasource_id: int, db: Session = Depends(get_db)):
    """测试数据源连接"""
    datasource = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")

    try:
        config = {
            "host": datasource.host,
            "port": datasource.port,
            "database": datasource.database,
            "username": datasource.username,
            "password": datasource.password,
            "use_kerberos": datasource.use_kerberos,
            "kerberos_principal": datasource.kerberos_principal,
            "kerberos_keytab_path": datasource.kerberos_keytab_path,
            **(datasource.extra_config or {}),
        }

        connector = HiveServer2Connector(config)
        success = connector.test_connection()

        if success:
            return {"success": True, "message": "连接成功"}
        else:
            return {"success": False, "message": "连接失败"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}
