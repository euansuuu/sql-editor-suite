from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models import SessionLocal, DataSource
from app.schemas import DatabaseInfo, TableInfo, ColumnInfo, PartitionInfo
from app.connectors.hiveserver2 import HiveServer2Connector
from app.connectors.trino import TrinoConnector

router = APIRouter(prefix="/metadata", tags=["metadata"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_connector(datasource: DataSource):
    """获取连接器实例"""
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

    connector_map = {
        "hiveserver2": HiveServer2Connector,
        "trino": TrinoConnector,
    }

    connector_class = connector_map.get(datasource.type)
    if not connector_class:
        raise ValueError(f"不支持的数据源类型: {datasource.type}")

    return connector_class(config)


@router.get("/{datasource_id}/databases", response_model=List[DatabaseInfo])
def list_databases(datasource_id: int, db: Session = Depends(get_db)):
    """获取数据库列表"""
    datasource = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")

    try:
        connector = get_connector(datasource)
        with connector.session():
            databases = connector.get_databases()
            return [{"name": name, "description": None} for name in databases]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库列表失败: {str(e)}")


@router.get("/{datasource_id}/tables/{database}", response_model=List[TableInfo])
def list_tables(datasource_id: int, database: str, db: Session = Depends(get_db)):
    """获取表列表"""
    datasource = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")

    try:
        connector = get_connector(datasource)
        with connector.session():
            return connector.get_tables(database)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表列表失败: {str(e)}")


@router.get("/{datasource_id}/columns/{database}/{table}", response_model=List[ColumnInfo])
def list_columns(datasource_id: int, database: str, table: str, db: Session = Depends(get_db)):
    """获取列信息"""
    datasource = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")

    try:
        connector = get_connector(datasource)
        with connector.session():
            return connector.get_columns(database, table)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取列信息失败: {str(e)}")


@router.get("/{datasource_id}/partitions/{database}/{table}", response_model=List[PartitionInfo])
def list_partitions(datasource_id: int, database: str, table: str, db: Session = Depends(get_db)):
    """获取分区信息"""
    datasource = db.query(DataSource).filter(DataSource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")

    try:
        connector = get_connector(datasource)
        with connector.session():
            return connector.get_partitions(database, table)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分区信息失败: {str(e)}")
