import uuid
import threading
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models import QueryExecution, DataSource
from app.connectors.hiveserver2 import HiveServer2Connector
from app.connectors.trino import TrinoConnector
from config.settings import settings


class ExecutionService:
    """SQL 执行管理服务"""

    def __init__(self, db: Session):
        self.db = db
        self.result_dir = Path("./query_results")
        self.result_dir.mkdir(parents=True, exist_ok=True)
        self._running_queries = {}

    def _get_connector(self, datasource: DataSource):
        """根据数据源类型获取连接器"""
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
            # 其他连接器可在此扩展
        }

        connector_class = connector_map.get(datasource.type)
        if not connector_class:
            raise ValueError(f"不支持的数据源类型: {datasource.type}")

        return connector_class(config)

    def _execute_worker(self, query_id: str, datasource: DataSource, sql: str, max_rows: int):
        """异步执行工作线程"""
        connector = None
        start_time = time.time()

        try:
            # 更新状态为 RUNNING
            query = self.db.query(QueryExecution).filter(QueryExecution.id == query_id).first()
            if query:
                query.status = "RUNNING"
                query.updated_at = datetime.utcnow()
                self.db.commit()

            connector = self._get_connector(datasource)
            connector.connect()

            # 执行 SQL
            connector.execute(sql)

            # 获取结果
            status = connector.get_status(query_id)

            if status["status"] == "SUCCESS":
                result = connector.get_result(query_id, fetch_size=max_rows)

                # 保存结果到文件
                result_path = self.result_dir / f"{query_id}.json"
                with open(result_path, 'w') as f:
                    json.dump({
                        "columns": result["columns"],
                        "data": result["data"],
                    }, f, default=str)

                # 更新查询记录
                if query:
                    query.status = "SUCCESS"
                    query.row_count = result["total_rows"]
                    query.result_columns = result["columns"]
                    query.result_path = str(result_path)
                    query.execution_time = int((time.time() - start_time) * 1000)
                    query.completed_at = datetime.utcnow()
                    query.updated_at = datetime.utcnow()
                    self.db.commit()
            else:
                if query:
                    query.status = status["status"]
                    query.error_message = status.get("error")
                    query.execution_time = int((time.time() - start_time) * 1000)
                    query.completed_at = datetime.utcnow()
                    query.updated_at = datetime.utcnow()
                    self.db.commit()

        except Exception as e:
            # 更新状态为 FAILED
            query = self.db.query(QueryExecution).filter(QueryExecution.id == query_id).first()
            if query:
                query.status = "FAILED"
                query.error_message = str(e)
                query.execution_time = int((time.time() - start_time) * 1000)
                query.completed_at = datetime.utcnow()
                query.updated_at = datetime.utcnow()
                self.db.commit()
        finally:
            if connector:
                connector.disconnect()
            self._running_queries.pop(query_id, None)

    def execute(self, datasource_id: int, sql: str, max_rows: int = 1000) -> str:
        """执行 SQL（异步）"""
        # 验证数据源存在
        datasource = self.db.query(DataSource).filter(DataSource.id == datasource_id).first()
        if not datasource:
            raise ValueError(f"数据源不存在: {datasource_id}")

        # 创建查询记录
        query_id = str(uuid.uuid4())
        query = QueryExecution(
            id=query_id,
            datasource_id=datasource_id,
            sql=sql,
            status="PENDING",
        )
        self.db.add(query)
        self.db.commit()

        # 启动异步执行线程
        thread = threading.Thread(
            target=self._execute_worker,
            args=(query_id, datasource, sql, max_rows),
            daemon=True,
        )
        thread.start()
        self._running_queries[query_id] = thread

        return query_id

    def get_status(self, query_id: str) -> Optional[QueryExecution]:
        """获取查询状态"""
        return self.db.query(QueryExecution).filter(QueryExecution.id == query_id).first()

    def get_result(self, query_id: str, offset: int = 0, limit: int = 1000) -> dict:
        """获取查询结果"""
        query = self.db.query(QueryExecution).filter(QueryExecution.id == query_id).first()
        if not query:
            raise ValueError(f"查询不存在: {query_id}")

        if query.status not in ["SUCCESS", "FAILED"]:
            return {
                "id": query_id,
                "status": query.status,
                "columns": [],
                "data": [],
                "has_more": False,
                "total_rows": 0,
            }

        if query.status == "FAILED":
            return {
                "id": query_id,
                "status": "FAILED",
                "error": query.error_message,
                "columns": [],
                "data": [],
                "has_more": False,
                "total_rows": 0,
            }

        # 从文件读取结果
        result_path = Path(query.result_path)
        if not result_path.exists():
            return {
                "id": query_id,
                "status": "SUCCESS",
                "columns": query.result_columns or [],
                "data": [],
                "has_more": False,
                "total_rows": query.row_count or 0,
            }

        with open(result_path, 'r') as f:
            result_data = json.load(f)

        all_data = result_data.get("data", [])
        paginated_data = all_data[offset:offset + limit]

        return {
            "id": query_id,
            "status": "SUCCESS",
            "columns": result_data.get("columns", []),
            "data": paginated_data,
            "has_more": (offset + limit) < len(all_data),
            "total_rows": len(all_data),
        }

    def cancel(self, query_id: str) -> bool:
        """取消查询"""
        query = self.db.query(QueryExecution).filter(QueryExecution.id == query_id).first()
        if not query:
            return False

        if query.status in ["SUCCESS", "FAILED", "CANCELLED"]:
            return True

        # 更新状态
        query.status = "CANCELLED"
        query.updated_at = datetime.utcnow()
        query.completed_at = datetime.utcnow()
        self.db.commit()

        return True

    def get_history(self, datasource_id: Optional[int] = None, limit: int = 100, offset: int = 0) -> list[QueryExecution]:
        """获取查询历史"""
        query = self.db.query(QueryExecution)

        if datasource_id:
            query = query.filter(QueryExecution.datasource_id == datasource_id)

        return query.order_by(QueryExecution.created_at.desc()).offset(offset).limit(limit).all()
