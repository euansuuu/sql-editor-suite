from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import settings

engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class DataSource(Base):
    __tablename__ = "datasources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    type = Column(String(50), nullable=False)  # hiveserver2, impala, spark, trino, jdbc
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database = Column(String(255))
    username = Column(String(255))
    password = Column(String(255))
    use_kerberos = Column(Boolean, default=False)
    kerberos_principal = Column(String(255))
    kerberos_keytab_path = Column(String(255))
    extra_config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QueryExecution(Base):
    __tablename__ = "query_executions"

    id = Column(String(100), primary_key=True, index=True)
    datasource_id = Column(Integer, index=True)
    sql = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING")  # PENDING, RUNNING, SUCCESS, FAILED, CANCELLED
    error_message = Column(Text)
    execution_time = Column(Integer)  # milliseconds
    row_count = Column(Integer)
    result_columns = Column(JSON)
    result_path = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)


def init_db():
    Base.metadata.create_all(bind=engine)
