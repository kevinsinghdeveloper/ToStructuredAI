"""Abstract base class for external database connectors.
Provides a standard interface for connecting to and querying user-provided databases.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AbstractDatabaseConnector(ABC):

    @abstractmethod
    def connect(self, connection_config: Dict[str, Any]) -> bool:
        """Establish a database connection.

        Args:
            connection_config: Dictionary with host, port, database_name,
                username, password, ssl_enabled, schema_name.

        Returns:
            True if connection was successful.

        Raises:
            ConnectionError: If connection fails.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the database connection and cleanup resources."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the current connection is alive."""
        pass

    @abstractmethod
    def get_tables(self) -> List[str]:
        """List all user tables in the connected database."""
        pass

    @abstractmethod
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get the schema definition for a specific table.

        Returns:
            {
                "table_name": "...",
                "columns": [{"name": ..., "type": ..., "nullable": ..., "primary_key": ...}],
                "row_count": N
            }
        """
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict] = None, row_limit: int = 1000) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results.

        Raises:
            ValueError: If query is not a SELECT statement.
            RuntimeError: If query execution fails.
        """
        pass

    @abstractmethod
    def get_sample_data(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sample rows from a table."""
        pass
