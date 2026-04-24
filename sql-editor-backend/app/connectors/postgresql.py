from .relational import RelationalConnector


class PostgreSQLConnector(RelationalConnector):
    """PostgreSQL connector."""

    display_name = "PostgreSQL"
    default_port = 5432

    def _connect(self):
        try:
            import psycopg2
        except ImportError as e:
            raise RuntimeError("缺少 PostgreSQL 驱动，请先安装 psycopg2-binary") from e

        return psycopg2.connect(
            host=self.host,
            port=int(self.port or self.default_port),
            dbname=self.database or "postgres",
            user=self.username,
            password=self.password,
            connect_timeout=int(self.connect_timeout),
        )

    def get_databases(self) -> list[str]:
        if not self.cursor:
            self.connect()
        self.cursor.execute(
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT LIKE 'pg_%'
              AND schema_name <> 'information_schema'
            ORDER BY schema_name
            """
        )
        return [row[0] for row in self.cursor.fetchall()]

    def get_tables(self, database: str) -> list[dict]:
        if not self.cursor:
            self.connect()
        self.cursor.execute(
            """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name
            """,
            (database,),
        )
        return [
            {"name": row[0], "type": row[1], "comment": None}
            for row in self.cursor.fetchall()
        ]

    def get_columns(self, database: str, table: str) -> list[dict]:
        if not self.cursor:
            self.connect()
        self.cursor.execute(
            """
            SELECT column_name, data_type, is_nullable
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
                "comment": None,
                "nullable": row[2] == "YES",
            }
            for row in self.cursor.fetchall()
        ]
