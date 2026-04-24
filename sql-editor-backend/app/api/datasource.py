from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models import DataSource, SessionLocal
from app.schemas import DataSourceCreate, DataSourceUpdate, DataSource as DataSourceSchema
from app.connectors.hiveserver2 import HiveServer2Connector

router = APIRouter(prefix="/datasources", tags=["datasources"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[DataSourceSchema])
def list_datasources(db: Session = Depends(get_db)):
    """获取所有数据源"""
    return db.query(DataSource).order_by(DataSource.created_at.desc()).all()


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

    datasource = DataSource(**data.dict())
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
