from pydantic import BaseModel, Field
from typing import Optional, Any, List, Generic, TypeVar
from datetime import datetime
from enum import Enum

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """通用 API 响应格式（兼容前端）"""
    code: int = Field(default=0, description="响应码，0 表示成功")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    
    @classmethod
    def success(cls, data: T = None, message: str = "success"):
        return cls(code=0, message=message, data=data)
    
    @classmethod
    def error(cls, message: str, code: int = -1, data: T = None):
        return cls(code=code, message=message, data=data)


class DataSourceType(str, Enum):
    HIVESERVER2 = "hiveserver2"
    HIVE = "hive"  # 兼容前端
    IMPALA = "impala"
    SPARK = "spark"
    TRINO = "trino"
    PRESTO = "presto"  # 兼容 Presto 别名
    JDBC = "jdbc"


class QueryStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# DataSource Schemas
class DataSourceBase(BaseModel):
    name: str = Field(..., description="数据源名称")
    type: DataSourceType = Field(..., description="数据源类型")
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口")
    database: Optional[str] = Field(None, description="默认数据库")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    use_kerberos: bool = Field(False, description="是否使用 Kerberos")
    kerberos_principal: Optional[str] = Field(None, description="客户端 Kerberos Principal（用户身份）")
    kerberos_keytab_path: Optional[str] = Field(None, description="Keytab 文件路径")
    kerberos_service_name: Optional[str] = Field("hive", description="Kerberos 服务名称（hive）")
    kerberos_host_name: Optional[str] = Field(None, description="Kerberos 服务主机名（可选，默认从 host 提取）")
    auth_mechanism: Optional[str] = Field("KERBEROS", description="认证机制：KERBEROS/PLAIN/NOSASL/LDAP")
    extra_config: Optional[dict] = Field(default_factory=dict)


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceUpdate(DataSourceBase):
    pass


class DataSource(DataSourceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# SQL Execution Schemas
class SQLExecuteRequest(BaseModel):
    datasource_id: int = Field(..., description="数据源 ID")
    sql: str = Field(..., description="SQL 语句")
    max_rows: Optional[int] = Field(1000, description="最大返回行数")


class QueryStatusResponse(BaseModel):
    id: str
    datasource_id: int
    status: QueryStatus
    sql: str
    error_message: Optional[str]
    execution_time: Optional[int]
    row_count: Optional[int]
    created_at: datetime
    updated_at: datetime


class QueryResultResponse(BaseModel):
    id: str
    status: QueryStatus
    columns: list[dict]
    data: list[list[Any]]
    has_more: bool
    total_rows: int


# Kerberos Schemas
class KerberosKinitRequest(BaseModel):
    principal: str = Field(..., description="Kerberos Principal")
    keytab_path: Optional[str] = Field(None, description="Keytab 文件路径")
    password: Optional[str] = Field(None, description="密码（用于密码认证）")


class KerberosStatusResponse(BaseModel):
    principal: Optional[str]
    ticket_expires: Optional[datetime]
    valid: bool
    message: str


# Metadata Schemas
class DatabaseInfo(BaseModel):
    name: str
    description: Optional[str] = None


class TableInfo(BaseModel):
    name: str
    type: Optional[str] = None
    comment: Optional[str] = None


class ColumnInfo(BaseModel):
    name: str
    type: str
    comment: Optional[str] = None
    nullable: bool = True


class PartitionInfo(BaseModel):
    name: str
    type: str
    values: Optional[list[str]] = None
