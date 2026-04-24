from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import SessionLocal, QueryExecution
from app.schemas import SQLExecuteRequest, QueryStatusResponse, QueryResultResponse, ApiResponse
from app.services.execution import ExecutionService

router = APIRouter(prefix="/query", tags=["query"])


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


@router.post("/execute", response_model=ApiResponse[dict])
def execute_sql(request: SQLExecuteRequest, db: Session = Depends(get_db)):
    """执行 SQL 查询"""
    try:
        service = ExecutionService(db)
        query_id = service.execute(request.datasource_id, request.sql, request.max_rows)
        return ApiResponse.success(data={"query_id": query_id}, message="查询已提交")
    except Exception as e:
        return ApiResponse.error(message=str(e))


@router.get("/status/{query_id}", response_model=ApiResponse[QueryStatusResponse])
def get_query_status(query_id: str, db: Session = Depends(get_db)):
    """获取查询状态"""
    service = ExecutionService(db)
    query = service.get_status(query_id)
    if not query:
        raise HTTPException(status_code=404, detail="查询不存在")
    return ApiResponse.success(data=query)


@router.get("/result/{query_id}", response_model=ApiResponse[QueryResultResponse])
def get_query_result(
    query_id: str,
    offset: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
):
    """获取查询结果"""
    try:
        service = ExecutionService(db)
        result = service.get_result(query_id, offset, limit)
        return ApiResponse.success(data=result)
    except Exception as e:
        return ApiResponse.error(message=str(e))


@router.post("/cancel/{query_id}")
def cancel_query(query_id: str, db: Session = Depends(get_db)):
    """取消查询"""
    service = ExecutionService(db)
    success = service.cancel(query_id)
    if success:
        return {"success": True, "message": "查询已取消"}
    else:
        raise HTTPException(status_code=404, detail="查询不存在或无法取消")


@router.get("/history", response_model=List[QueryStatusResponse])
def get_query_history(
    datasource_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """获取查询历史"""
    service = ExecutionService(db)
    return service.get_history(datasource_id, limit, offset)
