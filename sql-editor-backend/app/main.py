# Python 3.12+ compatibility: use pure-sasl instead of sasl
# Must be set BEFORE importing thrift_sasl/pyhive/impyla
import os
os.environ['THRIFT_SASL_PURE_SASL'] = '1'

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings
from app.models import init_db
from app.api import datasource, sql, metadata, kerberos


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    init_db()
    yield
    # 关闭时清理


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="无用户系统的 SQL 编辑器后端服务",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(datasource.router, prefix=settings.API_V1_STR)
app.include_router(sql.router, prefix=settings.API_V1_STR)
app.include_router(metadata.router, prefix=settings.API_V1_STR)
app.include_router(kerberos.router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "SQL Editor Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
