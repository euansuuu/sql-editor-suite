import uuid
import time
import os
import subprocess
import logging
from typing import Any, Optional
from pyhive import hive
from impala.dbapi import connect as impala_connect
from .base import BaseConnector, ConnectionError, QueryExecutionError

logger = logging.getLogger(__name__)


class HiveServer2Connector(BaseConnector):
    """HiveServer2 连接器"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.host = config.get("host")
        self.port = config.get("port", 10000)
        self.database = config.get("database", "default")
        self.username = config.get("username")
        self.password = config.get("password")
        self.use_kerberos = config.get("use_kerberos", False)
        self.kerberos_principal = config.get("kerberos_principal")
        self.auth = "KERBEROS" if self.use_kerberos else "NOSASL"
        self._queries = {}  # 存储查询状态

    def connect(self) -> None:
        """建立 HiveServer2 连接"""
        try:
            # 如果使用 Kerberos，先确保有票据
            if self.use_kerberos and self.kerberos_principal:
                keytab_path = self.config.get("kerberos_keytab_path")
                
                # 如果配置中没有 keytab 路径，尝试从默认位置查找
                if not keytab_path or not os.path.exists(keytab_path):
                    from pathlib import Path
                    from config.settings import settings
                    safe_principal = self.kerberos_principal.replace('/', '_').replace('@', '_')
                    keytab_path = str(settings.KEYTAB_DIR / f"{safe_principal}.keytab")
                    logger.info(f"尝试从默认位置加载 keytab: {keytab_path}")
                
                if keytab_path and os.path.exists(keytab_path):
                    self._kinit(self.kerberos_principal, keytab_path)
                else:
                    logger.warning(f"Keytab 不存在: {keytab_path}，使用系统默认票据")

            # 认证机制：优先用配置的 auth_mechanism
            auth = self.config.get("auth_mechanism", "KERBEROS" if self.use_kerberos else "NOSASL")
            
            # 基础配置
            connect_kwargs = {
                "host": self.host,
                "port": self.port,
                "database": self.database,
                "username": self.username or "anonymous",
                "auth": auth,
            }

            # PyHive only accepts password for LDAP/CUSTOM authentication.
            if self.password and str(auth).upper() in {"LDAP", "CUSTOM"}:
                connect_kwargs["password"] = self.password

            # Kerberos 配置
            if self.use_kerberos:
                # 服务端 Principal 名称（默认为 hive）
                service_name = self.config.get("kerberos_service_name", "hive")
                connect_kwargs["kerberos_service_name"] = service_name
                
                # 如果配置了 kerberos_host_name（主机名），用它替换 host 参数
                # 因为 Kerberos Principal 是 hive/hostname@REALM，必须用主机名而不是 IP
                kerberos_host_name = self.config.get("kerberos_host_name")
                if kerberos_host_name:
                    connect_kwargs["host"] = kerberos_host_name
                    logger.info(f"Kerberos 配置: service={service_name}, 使用主机名={kerberos_host_name} (原 host={self.host})")
                else:
                    logger.info(f"Kerberos 配置: service={service_name}, host={self.host}")
            
            logger.info(f"Connecting to HiveServer2: host={self.host}, port={self.port}, auth={self.auth}")
            logger.debug(f"Connection kwargs: {connect_kwargs}")
            
            self.connection = hive.Connection(**connect_kwargs)
            self.cursor = self.connection.cursor()
            logger.info("HiveServer2 连接成功")
        except Exception as e:
            error_msg = f"HiveServer2 连接失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ConnectionError(error_msg) from e

    def _kinit(self, principal: str, keytab_path: str) -> None:
        """使用 keytab 执行 kinit 获取 Kerberos 票据"""
        try:
            from pathlib import Path
            from config.settings import settings
            
            # 使用与 KerberosService 一致的票据缓存路径
            safe_principal = principal.replace('/', '_').replace('@', '_')
            krb5cc_path = settings.TICKET_CACHE_DIR / f"krb5cc_{safe_principal}"
            krb5cc_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"执行 kinit: principal={principal}, keytab={keytab_path}, cache={krb5cc_path}")
            
            env = os.environ.copy()
            env['KRB5CCNAME'] = str(krb5cc_path)
            
            result = subprocess.run(
                ["kinit", "-kt", keytab_path, principal],
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            
            if result.returncode == 0:
                logger.info("kinit 成功")
                # 重要：设置 KRB5CCNAME 环境变量，供 pyhive 使用
                os.environ['KRB5CCNAME'] = str(krb5cc_path)
            else:
                logger.warning(f"kinit 失败: {result.stderr}")
        except Exception as e:
            logger.warning(f"kinit 执行失败: {e}")

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

            # 重要：Hive JDBC/Thrift 不接受末尾的分号，需要去除
            # 处理: SELECT 1;  -> SELECT 1
            # 处理: SELECT 1;;  -> SELECT 1
            # 处理: SELECT 1; \n  -> SELECT 1
            cleaned_sql = sql.strip().rstrip(';').strip()
            
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
                # 非查询语句 (CREATE, INSERT, etc.)
                return {
                    "columns": [],
                    "data": [],
                    "row_count": cursor.rowcount,
                    "has_more": False,
                }

            columns = [{"name": col[0], "type": str(col[1])} for col in description]

            # 获取所有结果
            data = cursor.fetchall()
            total_rows = len(data)

            # 分页
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
                # 尝试取消查询
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

        self.cursor.execute("SHOW DATABASES")
        results = self.cursor.fetchall()
        return [row[0] for row in results]

    def get_tables(self, database: str) -> list[dict]:
        """获取表列表"""
        if not self.cursor:
            self.connect()

        self.cursor.execute(f"USE {database}")
        self.cursor.execute("SHOW TABLES")
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

        self.cursor.execute(f"DESCRIBE FORMATTED {database}.{table}")
        results = self.cursor.fetchall()

        columns = []
        in_columns_section = False

        for row in results:
            col_name = row[0].strip() if row[0] else ""

            if col_name.startswith("# col_name"):
                in_columns_section = True
                continue
            if col_name.startswith("#") or col_name == "":
                in_columns_section = False
                continue

            if in_columns_section and len(row) >= 2:
                columns.append({
                    "name": col_name,
                    "type": row[1].strip() if row[1] else "unknown",
                    "comment": row[2].strip() if len(row) > 2 and row[2] else None,
                    "nullable": True,
                })

        return columns

    def get_partitions(self, database: str, table: str) -> list[dict]:
        """获取分区信息"""
        if not self.cursor:
            self.connect()

        try:
            self.cursor.execute(f"SHOW PARTITIONS {database}.{table}")
            results = self.cursor.fetchall()

            partitions = []
            for row in results:
                partition_str = row[0]
                # 解析分区字符串，如: year=2023/month=1
                parts = partition_str.split('/')
                partition_info = {}
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        partition_info[key] = value

                partitions.append({
                    "name": partition_str,
                    "values": partition_info,
                })

            return partitions
        except Exception:
            return []
