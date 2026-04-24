from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import DataSource


TYPE_MAPPING = {
    "hive": "hiveserver2",
    "hiveserver2": "hiveserver2",
    "presto": "trino",
    "trino": "trino",
    "mysql": "mysql",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "pgsql": "postgresql",
    "impala": "impala",
    "spark": "spark-sql",
    "spark-sql": "spark-sql",
    "sparksql": "spark-sql",
    "spark_sql": "spark-sql",
}

CONNECTOR_IMPORTS = {
    "hiveserver2": ("app.connectors.hiveserver2", "HiveServer2Connector"),
    "trino": ("app.connectors.trino", "TrinoConnector"),
    "mysql": ("app.connectors.mysql", "MySQLConnector"),
    "postgresql": ("app.connectors.postgresql", "PostgreSQLConnector"),
    "spark-sql": ("app.connectors.spark_sql", "SparkSQLConnector"),
    "impala": ("app.connectors.impala", "ImpalaConnector"),
}


def normalize_datasource_type(type_str: str | None) -> str:
    if not type_str:
        return "hiveserver2"
    return TYPE_MAPPING.get(type_str.lower(), type_str.lower())


def datasource_to_config(datasource: "DataSource") -> dict:
    return {
        "type": normalize_datasource_type(datasource.type),
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


def create_connector(config: dict):
    datasource_type = normalize_datasource_type(config.get("type"))
    connector_import = CONNECTOR_IMPORTS.get(datasource_type)
    if not connector_import:
        raise ValueError(f"不支持的数据源类型: {datasource_type}")

    module_name, class_name = connector_import
    module = __import__(module_name, fromlist=[class_name])
    connector_class = getattr(module, class_name)
    normalized_config = {**config, "type": datasource_type}
    return connector_class(normalized_config)
