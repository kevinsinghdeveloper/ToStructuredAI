"""Factory for creating database connector instances based on db_type."""
from typing import Dict, Any
from services.database.AbstractDatabaseConnector import AbstractDatabaseConnector


class ConnectorFactory:

    _CONNECTOR_MAP = {
        "postgresql": "services.database.PostgreSQLConnector.PostgreSQLConnector",
        # Future: "mysql": "services.database.MySQLConnector.MySQLConnector",
        # Future: "mssql": "services.database.MSSQLConnector.MSSQLConnector",
    }

    @staticmethod
    def get_connector(db_type: str) -> AbstractDatabaseConnector:
        """Create and return a database connector for the given type.

        Raises:
            ValueError: If the database type is not supported.
        """
        class_path = ConnectorFactory._CONNECTOR_MAP.get(db_type.lower())
        if not class_path:
            supported = ", ".join(ConnectorFactory._CONNECTOR_MAP.keys())
            raise ValueError(f"Unsupported database type: '{db_type}'. Supported types: {supported}")

        module_path, class_name = class_path.rsplit(".", 1)
        import importlib
        module = importlib.import_module(module_path)
        connector_class = getattr(module, class_name)
        return connector_class()

    @staticmethod
    def create_and_connect(connection_config: Dict[str, Any]) -> AbstractDatabaseConnector:
        """Create a connector and establish connection in one step."""
        db_type = connection_config.get("db_type", "")
        connector = ConnectorFactory.get_connector(db_type)
        connector.connect(connection_config)
        return connector

    @staticmethod
    def supported_types():
        """Return list of supported database types."""
        return list(ConnectorFactory._CONNECTOR_MAP.keys())
