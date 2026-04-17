"""PostgreSQL connector implementation using SQLAlchemy."""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import QueuePool
from services.database.AbstractDatabaseConnector import AbstractDatabaseConnector

logger = logging.getLogger(__name__)


class PostgreSQLConnector(AbstractDatabaseConnector):

    def __init__(self):
        self._engine = None
        self._connection_config = None

    def connect(self, connection_config: Dict[str, Any]) -> bool:
        try:
            self._connection_config = connection_config
            url = self._build_connection_url(connection_config)

            self._engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=3,
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=1800,
                connect_args=self._build_connect_args(connection_config),
            )

            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info(
                "Connected to PostgreSQL: %s:%s/%s",
                connection_config.get("host"),
                connection_config.get("port"),
                connection_config.get("database_name"),
            )
            return True

        except Exception as e:
            logger.error("Failed to connect to PostgreSQL: %s", str(e))
            raise ConnectionError(f"Failed to connect: {str(e)}")

    def disconnect(self) -> None:
        if self._engine:
            self._engine.dispose()
            self._engine = None

    def test_connection(self) -> bool:
        if not self._engine:
            return False
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def get_tables(self) -> List[str]:
        self._ensure_connected()
        inspector = inspect(self._engine)
        schema = self._connection_config.get("schema_name", "public") if self._connection_config else "public"
        return sorted(inspector.get_table_names(schema=schema))

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        self._ensure_connected()
        inspector = inspect(self._engine)
        schema = self._connection_config.get("schema_name", "public") if self._connection_config else "public"

        pk_columns = set()
        pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
        if pk_constraint:
            pk_columns = set(pk_constraint.get("constrained_columns", []))

        columns = []
        for col in inspector.get_columns(table_name, schema=schema):
            columns.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "primary_key": col["name"] in pk_columns,
                "default": str(col.get("default", "")) if col.get("default") else None,
            })

        row_count = 0
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                row_count = result.scalar()
        except Exception:
            pass

        return {"table_name": table_name, "columns": columns, "row_count": row_count}

    def execute_query(self, query: str, params: Optional[Dict] = None, row_limit: int = 1000) -> List[Dict[str, Any]]:
        self._ensure_connected()

        stripped = query.strip().upper()
        if not stripped.startswith("SELECT") and not stripped.startswith("WITH"):
            raise ValueError("Only SELECT queries are allowed")

        if "LIMIT" not in stripped:
            query = f"{query.rstrip().rstrip(';')} LIMIT {row_limit}"

        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                columns = list(result.keys())
                return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            logger.error("Query execution failed: %s", str(e))
            raise RuntimeError(f"Query execution failed: {str(e)}")

    def get_sample_data(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self.execute_query(f'SELECT * FROM "{table_name}" LIMIT {limit}')

    def _build_connection_url(self, config: Dict[str, Any]) -> str:
        host = config.get("host", "localhost")
        port = config.get("port", 5432)
        database = config.get("database_name", "")
        username = config.get("username", "")
        password = config.get("password", "")
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"

    def _build_connect_args(self, config: Dict[str, Any]) -> Dict:
        args = {}
        if config.get("ssl_enabled"):
            args["sslmode"] = "require"
        return args

    def _ensure_connected(self):
        if not self._engine:
            raise ConnectionError("Not connected. Call connect() first.")
