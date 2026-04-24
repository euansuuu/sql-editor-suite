from abc import ABC, abstractmethod
from typing import Any, Generator, Optional, List
from contextlib import contextmanager


class BaseConnector(ABC):
    """数据源连接器基类"""

    def __init__(self, config: dict):
        self.config = config
        self.connection = None
        self.cursor = None

    @abstractmethod
    def connect(self) -> None:
        """建立连接"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """关闭连接"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接"""
        pass

    @abstractmethod
    def execute(self, sql: str, parameters: Optional[dict] = None) -> str:
        """执行 SQL，返回执行 ID"""
        pass

    @abstractmethod
    def get_status(self, query_id: str) -> dict:
        """获取查询状态"""
        pass

    @abstractmethod
    def get_result(self, query_id: str, fetch_size: int = 1000, offset: int = 0) -> dict:
        """获取查询结果"""
        pass

    @abstractmethod
    def cancel(self, query_id: str) -> bool:
        """取消查询"""
        pass

    @abstractmethod
    def get_databases(self) -> List[str]:
        """获取数据库列表"""
        pass

    @abstractmethod
    def get_tables(self, database: str) -> List[dict]:
        """获取表列表"""
        pass

    @abstractmethod
    def get_columns(self, database: str, table: str) -> List[dict]:
        """获取列信息"""
        pass

    @abstractmethod
    def get_partitions(self, database: str, table: str) -> List[dict]:
        """获取分区信息"""
        pass

    @contextmanager
    def session(self):
        """上下文管理器，自动管理连接生命周期"""
        try:
            self.connect()
            yield self
        finally:
            self.disconnect()


class ConnectionError(Exception):
    """连接异常"""
    pass


class QueryExecutionError(Exception):
    """查询执行异常"""
    pass


class QueryCancelledError(Exception):
    """查询已取消异常"""
    pass
