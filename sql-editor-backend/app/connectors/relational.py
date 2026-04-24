import time
import uuid
from typing import Optional

from .base import BaseConnector, ConnectionError, QueryExecutionError


class RelationalConnector(BaseConnector):
    """Base connector for synchronous Python DB-API databases."""

    display_name = "Relational"
    default_port: int | None = None

    def __init__(self, config: dict):
        super().__init__(config)
        self.host = config.get("host")
        self.port = config.get("port", self.default_port)
        self.database = config.get("database")
        self.username = config.get("username")
        self.password = config.get("password")
        self.connect_timeout = config.get("connect_timeout", 10)
        self._queries = {}

    def _connect(self):
        raise NotImplementedError

    def connect(self) -> None:
        try:
            self.connection = self._connect()
            self.cursor = self.connection.cursor()
        except Exception as e:
            raise ConnectionError(f"{self.display_name} 连接失败: {str(e)}") from e

    def disconnect(self) -> None:
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
        except Exception:
            pass
        finally:
            self.cursor = None
            self.connection = None

    def test_connection(self) -> bool:
        try:
            self.connect()
            self.cursor.execute("SELECT 1")
            return self.cursor.fetchone() is not None
        except Exception:
            return False
        finally:
            self.disconnect()

    def execute(self, sql: str, parameters: Optional[dict] = None) -> str:
        query_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            if not self.cursor:
                self.connect()

            cleaned_sql = sql.strip().rstrip(";").strip()
            self._queries[query_id] = {
                "status": "RUNNING",
                "sql": sql,
                "cleaned_sql": cleaned_sql,
                "start_time": start_time,
                "cursor": self.cursor,
            }

            self.cursor.execute(cleaned_sql, parameters or None)
            if self.connection:
                self.connection.commit()

            self._queries[query_id]["status"] = "SUCCESS"
            self._queries[query_id]["end_time"] = time.time()
            return query_id
        except Exception as e:
            if self.connection:
                try:
                    self.connection.rollback()
                except Exception:
                    pass
            if query_id in self._queries:
                self._queries[query_id]["status"] = "FAILED"
                self._queries[query_id]["error"] = str(e)
            raise QueryExecutionError(f"SQL 执行失败: {str(e)}") from e

    def get_status(self, query_id: str) -> dict:
        if query_id not in self._queries:
            return {"status": "UNKNOWN", "error": "查询不存在"}

        query = self._queries[query_id]
        execution_time = None
        if "end_time" in query and "start_time" in query:
            execution_time = int((query["end_time"] - query["start_time"]) * 1000)

        return {
            "status": query["status"],
            "error": query.get("error"),
            "execution_time": execution_time,
        }

    def get_result(self, query_id: str, fetch_size: int = 1000, offset: int = 0) -> dict:
        if query_id not in self._queries:
            raise QueryExecutionError("查询不存在")

        query = self._queries[query_id]
        if query["status"] != "SUCCESS":
            raise QueryExecutionError(f"查询未成功: {query['status']}")

        try:
            cursor = query["cursor"]
            if cursor.description is None:
                return {
                    "columns": [],
                    "data": [],
                    "total_rows": cursor.rowcount if cursor.rowcount and cursor.rowcount > 0 else 0,
                    "has_more": False,
                }

            columns = [{"name": col[0], "type": str(col[1])} for col in cursor.description]
            data = cursor.fetchall()
            total_rows = len(data)
            paginated_data = data[offset:offset + fetch_size]

            return {
                "columns": columns,
                "data": paginated_data,
                "total_rows": total_rows,
                "has_more": (offset + fetch_size) < total_rows,
            }
        except Exception as e:
            raise QueryExecutionError(f"获取结果失败: {str(e)}") from e

    def cancel(self, query_id: str) -> bool:
        if query_id not in self._queries:
            return False
        query = self._queries[query_id]
        if query["status"] == "RUNNING":
            query["status"] = "CANCELLED"
        return True

    def get_partitions(self, database: str, table: str) -> list[dict]:
        return []
