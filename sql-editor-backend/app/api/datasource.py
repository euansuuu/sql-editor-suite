from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Generic, TypeVar, Dict, Any
from pydantic import BaseModel

from app.models import DataSource, SessionLocal
from app.schemas import (
    DataSourceCreate, 
    DataSourceUpdate, 
    DataSource as DataSourceSchema,
    ApiResponse
)
from app.connectors.hiveserver2 import HiveServer2Connector


T = TypeVar('T')

class PaginatedResult(BaseModel, Generic[T]):
    """分页返回结果（兼容前端）"""
    list: List[T]
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
    """获取数据库会话（修复并发关闭问题）"""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        try:
            if session.is_active:
                session.close()
        except Exception:
            pass  # 忽略关闭时的错误，避免重复关闭导致异常


@router.get("", response_model=ApiResponse[PaginatedResult[DataSourceSchema]])
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
    
    result = PaginatedResult[DataSourceSchema](
        list=datasources,
        total=total,
        page=page,
        pageSize=pageSize
    )
    return ApiResponse.success(data=result)


@router.get("/{datasource_id}", response_model=ApiResponse[DataSourceSchema])
def get_datasource(datasource_id: int, db: Session = Depends(get_db)):
    """获取单个数据源"""
    datasource = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return ApiResponse.success(data=datasource)


@router.post("", response_model=ApiResponse[DataSourceSchema])
async def create_datasource(request: Request, db: Session = Depends(get_db)):
    """创建数据源"""
    # 先解析原始 JSON（避免 Pydantic 过滤掉前端的 authType/kerberos 字段）
    raw_data: Dict[str, Any] = await request.json()
    
    # 检查名称是否已存在
    existing = db.query(DataSource).filter(DataSource.name == raw_data.get('name')).first()
    if existing:
        raise HTTPException(status_code=400, detail="数据源名称已存在")

    # 处理前端字段映射兼容
    # 前端传的是 authType 字符串
    auth_type = raw_data.pop('authType', None)
    use_kerberos = auth_type and auth_type.lower() == 'kerberos'
    
    # 前端传的是嵌套 kerberos 对象
    kerberos_obj = raw_data.pop('kerberos', None)
    kerberos_principal = None
    kerberos_keytab_path = None
    extra_config = raw_data.get('extra_config', {}) or {}
    
    if kerberos_obj:
        kerberos_principal = kerberos_obj.get('principal')
        kerberos_keytab_path = kerberos_obj.get('keytab_path') or kerberos_obj.get('keytabPath')
        # 把额外的 Kerberos 配置存入 extra_config
        for k, v in kerberos_obj.items():
            if k not in ['principal', 'keytab_path', 'keytabPath']:
                extra_config[f'kerberos_{k}'] = v
    
    # 标准化数据源类型，兼容前端别名（hive -> hiveserver2, presto -> trino）
    ds_type = normalize_datasource_type(raw_data.get("type", "hiveserver2"))
    
    datasource = DataSource(
        name=raw_data.get('name'),
        type=ds_type,
        host=raw_data.get('host'),
        port=raw_data.get('port'),
        database=raw_data.get('database'),
        username=raw_data.get('username'),
        password=raw_data.get('password'),
        use_kerberos=use_kerberos,
        kerberos_principal=kerberos_principal,
        kerberos_keytab_path=kerberos_keytab_path,
        extra_config=extra_config,
    )
    
    db.add(datasource)
    db.commit()
    db.refresh(datasource)
    return ApiResponse.success(data=datasource, message="创建成功")


@router.put("/{datasource_id}", response_model=ApiResponse[DataSourceSchema])
def update_datasource(datasource_id: int, data: DataSourceUpdate, db: Session = Depends(get_db)):
    """更新数据源"""
    datasource = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")

    data_dict = data.dict(exclude_unset=True)
    
    # 处理不在 SQLAlchemy 模型中的额外 Kerberos 字段
    extra_fields = ["kerberos_service_name", "kerberos_host_name", "auth_mechanism"]
    extra_config = datasource.extra_config or {}
    
    for field in extra_fields:
        if field in data_dict and data_dict[field] is not None:
            extra_config[field] = data_dict[field]
            data_dict.pop(field)
    
    data_dict["extra_config"] = extra_config
    
    for key, value in data_dict.items():
        setattr(datasource, key, value)

    db.commit()
    db.refresh(datasource)
    return ApiResponse.success(data=datasource, message="更新成功")


@router.delete("/{datasource_id}", response_model=ApiResponse[dict])
def delete_datasource(datasource_id: int, db: Session = Depends(get_db)):
    """删除数据源"""
    datasource = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")

    db.delete(datasource)
    db.commit()
    return ApiResponse.success(data={"success": True}, message="删除成功")


@router.post("/{datasource_id}/test", response_model=ApiResponse[dict])
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
            return ApiResponse.success(data={"success": True}, message="连接成功")
        else:
            return ApiResponse.error(data={"success": False}, message="连接失败")
    except Exception as e:
        return ApiResponse.error(data={"success": False}, message=f"连接失败: {str(e)}")


@router.post("/test", response_model=ApiResponse[dict])
async def test_connection_new(request: Request, db: Session = Depends(get_db)):
    """测试数据源连接（用于新建时测试）"""
    try:
        # 先解析原始 JSON（避免 Pydantic 过滤掉前端的 authType/kerberos 字段）
        raw_data: Dict[str, Any] = await request.json()
        
        # 处理前端字段映射兼容
        # 前端传的是 authType 字符串
        auth_type = raw_data.pop('authType', None)
        use_kerberos = auth_type and auth_type.lower() == 'kerberos'
        
        # 前端传的是嵌套 kerberos 对象
        kerberos_obj = raw_data.pop('kerberos', None)
        kerberos_principal = None
        kerberos_keytab_path = None
        if kerberos_obj:
            kerberos_principal = kerberos_obj.get('principal')
            kerberos_keytab_path = kerberos_obj.get('keytab_path') or kerberos_obj.get('keytabPath')
        
        config = {
            "host": raw_data.get('host'),
            "port": raw_data.get('port'),
            "database": raw_data.get('database', 'default'),
            "username": raw_data.get('username'),
            "password": raw_data.get('password'),
            "use_kerberos": use_kerberos,
            "kerberos_principal": kerberos_principal,
            "kerberos_keytab_path": kerberos_keytab_path,
        }
        
        # Kerberos 模式下才添加相关配置
        if use_kerberos:
            config["kerberos_service_name"] = raw_data.get('kerberos_service_name') or (kerberos_obj.get('service_name') if kerberos_obj else None) or 'hive'
            config["kerberos_host_name"] = raw_data.get('kerberos_host_name') or (kerberos_obj.get('host_name') if kerberos_obj else None)
            config["auth_mechanism"] = raw_data.get('auth_mechanism', 'KERBEROS')

        connector = HiveServer2Connector(config)
        success = connector.test_connection()

        if success:
            return ApiResponse.success(data={"success": True}, message="连接成功")
        else:
            return ApiResponse.error(data={"success": False}, message="连接失败：无法建立连接，请检查网络和配置")
    except Exception as e:
        import traceback
        error_detail = str(e)
        error_stack = traceback.format_exc()
        
        # 提取关键错误信息
        if "Kerberos" in error_detail or "GSS" in error_detail or "krb" in error_detail:
            message = f"Kerberos 认证失败: {error_detail}"
        elif "Connection refused" in error_detail:
            message = f"连接被拒绝: {data.host}:{data.port}，请检查网络和端口"
        elif "Authentication" in error_detail:
            message = f"认证失败: {error_detail}"
        else:
            message = f"连接失败: {error_detail}"
        
        return ApiResponse.error(
            data={"success": False, "error": error_detail, "stacktrace": error_stack},
            message=message
        )
