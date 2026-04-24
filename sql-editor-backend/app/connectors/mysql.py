from .relational import RelationalConnector


class MySQLConnector(RelationalConnector):
    """MySQL connector."""

    display_name = "MySQL"
    default_port = 3306

    def _connect(self):
        try:
            import pymysql
        except ImportError as e:
            raise RuntimeError("缺少 MySQL 驱动，请先安装 pymysql") from e

        return pymysql.connect(
            host=self.host,
            port=int(self.port or self.default_port),
            user=self.username,
            password=self.password,
            database=self.database or None,
            connect_timeout=int(self.connect_timeout),
            charset=self.config.get("charset", "utf8mb4"),
            autocommit=False,
        )

    def get_databases(self) -> list[str]:
        if not self.cursor:
            self.connect()
        self.cursor.execute("SHOW DATABASES")
        return [row[0] for row in self.cursor.fetchall()]

    def get_tables(self, database: str) -> list[dict]:
        if not self.cursor:
            self.connect()
        self.cursor.execute(
            """
            SELECT table_name, table_type, table_comment
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name
            """,
            (database,),
        )
        return [
            {"name": row[0], "type": row[1], "comment": row[2] or None}
            for row in self.cursor.fetchall()
        ]

    def get_columns(self, database: str, table: str) -> list[dict]:
        if not self.cursor:
            self.connect()
        self.cursor.execute(
            """
            SELECT column_name, column_type, column_comment, is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (database, table),
        )
        return [
            {
                "name": row[0],
                "type": row[1],
                "comment": row[2] or None,
                "nullable": row[3] == "YES",
            }
            for row in self.cursor.fetchall()
        ]
