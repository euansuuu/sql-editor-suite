import time
import uuid
from typing import Optional

from impala.dbapi import connect as impala_connect

from .base import BaseConnector, ConnectionError, QueryExecutionError


class ImpalaConnector(BaseConnector):
    """Impala connector using the HiveServer2-compatible Impala protocol."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.host = config.get("host")
        self.port = config.get("port", 21050)
        self.database = config.get("database", "default")
        self.username = config.get("username")
        self.password = config.get("password")
        self.use_kerberos = config.get("use_kerberos", False)
        self._queries = {}

    def connect(self) -> None:
        try:
            auth_mechanism = self.config.get("auth_mechanism")
            if not auth_mechanism:
                auth_mechanism = "GSSAPI" if self.use_kerberos else "NOSASL"

            connect_kwargs = {
                "host": self.host,
                "port": int(self.port or 21050),
                "database": self.database or "default",
                "auth_mechanism": auth_mechanism,
            }

            if self.username:
                connect_kwargs["user"] = self.username
            if self.password and auth_mechanism.upper() in {"PLAIN", "LDAP"}:
                connect_kwargs["password"] = self.password
            if self.use_kerberos:
                connect_kwargs["kerberos_service_name"] = self.config.get("kerberos_service_name", "impala")
            if self.config.get("use_ssl"):
                connect_kwargs["use_ssl"] = True
            if self.config.get("ca_cert"):
                connect_kwargs["ca_cert"] = self.config["ca_cert"]

            self.connection = impala_connect(**connect_kwargs)
            self.cursor = self.connection.cursor()
        except Exception as e:
            raise ConnectionError(f"Impala 连接失败: {str(e)}") from e

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

            self.cursor.execute(cleaned_sql, parameters or {})
            self._queries[query_id]["status"] = "SUCCESS"
            self._queries[query_id]["end_time"] = time.time()
            return query_id
        except Exception as e:
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
                return {"columns": [], "data": [], "total_rows": 0, "has_more": False}

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
        try:
            query = self._queries[query_id]
            if query["status"] == "RUNNING" and hasattr(query["cursor"], "cancel_operation"):
                query["cursor"].cancel_operation()
            query["status"] = "CANCELLED"
            return True
        except Exception:
            return False

    def get_databases(self) -> list[str]:
        if not self.cursor:
            self.connect()
        self.cursor.execute("SHOW DATABASES")
        return [row[0] for row in self.cursor.fetchall()]

    def get_tables(self, database: str) -> list[dict]:
        if not self.cursor:
            self.connect()
        self.cursor.execute(f"SHOW TABLES IN {database}")
        return [{"name": row[0], "type": "TABLE", "comment": None} for row in self.cursor.fetchall()]

    def get_columns(self, database: str, table: str) -> list[dict]:
        if not self.cursor:
            self.connect()
        self.cursor.execute(f"DESCRIBE {database}.{table}")
        return [
            {"name": row[0], "type": row[1], "comment": row[2] if len(row) > 2 else None, "nullable": True}
            for row in self.cursor.fetchall()
            if row and row[0] and not str(row[0]).startswith("#")
        ]

    def get_partitions(self, database: str, table: str) -> list[dict]:
        if not self.cursor:
            self.connect()
        try:
            self.cursor.execute(f"SHOW PARTITIONS {database}.{table}")
            return [{"name": str(row[0]), "values": {}} for row in self.cursor.fetchall()]
        except Exception:
            return []
