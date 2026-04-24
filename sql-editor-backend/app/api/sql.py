from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import SessionLocal, QueryExecution
from app.schemas import SQLExecuteRequest, QueryStatusResponse, QueryResultResponse
from app.services.execution import ExecutionService

router = APIRouter(prefix="/query", tags=["query"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/execute")
def execute_sql(request: SQLExecuteRequest, db: Session = Depends(get_db)):
    """执行 SQL 查询"""
    try:
        service = ExecutionService(db)
        query_id = service.execute(request.datasource_id, request.sql, request.max_rows)
        return {"query_id": query_id, "message": "查询已提交"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{query_id}", response_model=QueryStatusResponse)
def get_query_status(query_id: str, db: Session = Depends(get_db)):
    """获取查询状态"""
    service = ExecutionService(db)
    query = service.get_status(query_id)
    if not query:
        raise HTTPException(status_code=404, detail="查询不存在")
    return query


@router.get("/result/{query_id}", response_model=QueryResultResponse)
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
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
