from .hiveserver2 import HiveServer2Connector


class SparkSQLConnector(HiveServer2Connector):
    """Spark SQL Thrift Server connector."""

    def __init__(self, config: dict):
        config = {**config, "auth_mechanism": config.get("auth_mechanism", "NOSASL")}
        super().__init__(config)
