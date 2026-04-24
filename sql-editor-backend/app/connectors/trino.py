import uuid
import time
from typing import Any, Optional
from trino.dbapi import connect
from .base import BaseConnector, ConnectionError, QueryExecutionError


class TrinoConnector(BaseConnector):
    """Trino/Presto 连接器"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.host = config.get("host")
        self.port = config.get("port", 8080)
        self.catalog = config.get("catalog", "hive")
        self.schema = config.get("database", "default")
        self.username = config.get("username", "trino")
        self.password = config.get("password")
        self.use_kerberos = config.get("use_kerberos", False)
        self.kerberos_principal = config.get("kerberos_principal")
        self._queries = {}

    def connect(self) -> None:
        """建立 Trino 连接"""
        try:
            connect_kwargs = {
                "host": self.host,
                "port": self.port,
                "user": self.username,
                "catalog": self.catalog,
                "schema": self.schema,
            }

            if self.password:
                connect_kwargs["auth"] = self.password

            if self.use_kerberos:
                # Trino Kerberos 认证需要额外配置
                connect_kwargs["http_scheme"] = "https"
                connect_kwargs["verify"] = False

            self.connection = connect(**connect_kwargs)
            self.cursor = self.connection.cursor()
        except Exception as e:
            raise ConnectionError(f"Trino 连接失败: {str(e)}") from e

    def disconnect(self) -> None:
        """关闭连接"""
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
        """测试连接"""
        try:
            self.connect()
            self.cursor.execute("SELECT 1")
            result = self.cursor.fetchone()
            return result is not None
        except Exception:
            return False
        finally:
            self.disconnect()

    def execute(self, sql: str, parameters: Optional[dict] = None) -> str:
        """执行 SQL"""
        query_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            if not self.cursor:
                self.connect()

            self._queries[query_id] = {
                "status": "RUNNING",
                "sql": sql,
                "start_time": start_time,
                "cursor": self.cursor,
            }

            self.cursor.execute(sql, parameters or {})
            self._queries[query_id]["status"] = "SUCCESS"
            self._queries[query_id]["end_time"] = time.time()

            return query_id
        except Exception as e:
            if query_id in self._queries:
                self._queries[query_id]["status"] = "FAILED"
                self._queries[query_id]["error"] = str(e)
            raise QueryExecutionError(f"SQL 执行失败: {str(e)}") from e

    def get_status(self, query_id: str) -> dict:
        """获取查询状态"""
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
        """获取查询结果"""
        if query_id not in self._queries:
            raise QueryExecutionError("查询不存在")

        query = self._queries[query_id]
        if query["status"] != "SUCCESS":
            raise QueryExecutionError(f"查询未成功: {query['status']}")

        try:
            cursor = query["cursor"]
            description = cursor.description

            if description is None:
                return {
                    "columns": [],
                    "data": [],
                    "row_count": cursor.rowcount,
                    "has_more": False,
                }

            columns = [{"name": col[0], "type": str(col[1])} for col in description]

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
        """取消查询"""
        if query_id not in self._queries:
            return False

        try:
            query = self._queries[query_id]
            if query["status"] == "RUNNING":
                cursor = query["cursor"]
                if hasattr(cursor, "cancel"):
                    cursor.cancel()
                query["status"] = "CANCELLED"
            return True
        except Exception:
            return False

    def get_databases(self) -> list[str]:
        """获取数据库列表"""
        if not self.cursor:
            self.connect()

        self.cursor.execute("SHOW SCHEMAS")
        results = self.cursor.fetchall()
        return [row[0] for row in results]

    def get_tables(self, database: str) -> list[dict]:
        """获取表列表"""
        if not self.cursor:
            self.connect()

        self.cursor.execute(f"SHOW TABLES FROM {database}")
        results = self.cursor.fetchall()

        tables = []
        for row in results:
            tables.append({
                "name": row[0],
                "type": "TABLE",
                "comment": None,
            })

        return tables

    def get_columns(self, database: str, table: str) -> list[dict]:
        """获取列信息"""
        if not self.cursor:
            self.connect()

        self.cursor.execute(f"DESCRIBE {database}.{table}")
        results = self.cursor.fetchall()

        columns = []
        for row in results:
            if len(row) >= 2:
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "comment": row[2] if len(row) > 2 else None,
                    "nullable": True,
                })

        return columns

    def get_partitions(self, database: str, table: str) -> list[dict]:
        """获取分区信息"""
        if not self.cursor:
            self.connect()

        try:
            self.cursor.execute(f"SHOW PARTITIONS FROM {database}.{table}")
            results = self.cursor.fetchall()

            partitions = []
            for row in results:
                partitions.append({
                    "name": str(row),
                    "values": dict(zip([col[0] for col in self.cursor.description], row)),
                })

            return partitions
        except Exception:
            return []
