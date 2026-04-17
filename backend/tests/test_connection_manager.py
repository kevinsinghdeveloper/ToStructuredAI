"""Unit tests for ConnectionResourceManager."""
import json
import pytest
from unittest.mock import patch, MagicMock, ANY

from tests.conftest import make_request


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_CONNECTION_ITEM = {
    "user_id": "user-123",
    "id": "conn-001",
    "name": "Production DB",
    "db_type": "postgresql",
    "host": "db.example.com",
    "port": 5432,
    "database_name": "myapp",
    "username": "admin",
    "encrypted_password": "s3cret",
    "ssl_enabled": True,
    "schema_name": "public",
    "status": "connected",
    "created_at": "2024-06-01T00:00:00",
    "updated_at": "2024-06-01T00:00:00",
}

SAMPLE_CONNECTION_ITEM_2 = {
    **SAMPLE_CONNECTION_ITEM,
    "id": "conn-002",
    "name": "Staging DB",
    "host": "staging-db.example.com",
    "database_name": "staging",
    "status": "untested",
}


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _build_manager(mock_db=None):
    """Instantiate ConnectionResourceManager with mock services."""
    from managers.connections.ConnectionResourceManager import ConnectionResourceManager

    if mock_db is None:
        mock_db = MagicMock()
    service_managers = {"db": mock_db}
    return ConnectionResourceManager(service_managers=service_managers)


# ===========================================================================
# GET -- list all connections for a user
# ===========================================================================

class TestGetAllConnections:

    def test_get_all_connections(self):
        mock_db = MagicMock()
        mock_db.connections.find_by_user.return_value = [
            SAMPLE_CONNECTION_ITEM.copy(),
            SAMPLE_CONNECTION_ITEM_2.copy(),
        ]

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) == 2
        assert resp.data[0]["id"] == "conn-001"
        assert resp.data[0]["name"] == "Production DB"
        assert resp.data[1]["id"] == "conn-002"
        mock_db.connections.find_by_user.assert_called_once_with("user-123")

    def test_get_all_connections_empty(self):
        mock_db = MagicMock()
        mock_db.connections.find_by_user.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data == []


# ===========================================================================
# GET -- single connection by ID
# ===========================================================================

class TestGetSingleConnection:

    def test_get_single_connection(self):
        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = SAMPLE_CONNECTION_ITEM.copy()

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "conn-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["id"] == "conn-001"
        assert resp.data["name"] == "Production DB"
        assert resp.data["dbType"] == "postgresql"
        assert resp.data["host"] == "db.example.com"
        assert resp.data["port"] == 5432
        assert resp.data["databaseName"] == "myapp"
        assert resp.data["sslEnabled"] is True
        assert resp.data["status"] == "connected"
        mock_db.connections.get_by_key.assert_called_once_with(
            {"user_id": "user-123", "id": "conn-001"}
        )

    def test_get_connection_not_found(self):
        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "nonexistent"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()


# ===========================================================================
# POST -- create connection
# ===========================================================================

class TestCreateConnection:

    def test_create_connection(self):
        mock_db = MagicMock()
        mock_db.connections.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "New Connection",
                "dbType": "postgresql",
                "host": "localhost",
                "port": 5432,
                "databaseName": "testdb",
                "username": "testuser",
                "password": "testpass",
                "sslEnabled": False,
                "schemaName": "public",
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["name"] == "New Connection"
        assert resp.data["dbType"] == "postgresql"
        assert resp.data["host"] == "localhost"
        assert resp.data["port"] == 5432
        assert resp.data["databaseName"] == "testdb"
        assert resp.data["username"] == "testuser"
        assert resp.data["sslEnabled"] is False
        assert resp.data["status"] == "untested"
        assert resp.data["userId"] == "user-123"
        assert "created" in resp.message.lower()
        mock_db.connections.create.assert_called_once()

    def test_create_connection_defaults(self):
        """Fields not provided should fall back to defaults."""
        mock_db = MagicMock()
        mock_db.connections.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"name": "Minimal Connection"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["dbType"] == "postgresql"
        assert resp.data["host"] == ""
        assert resp.data["port"] == 5432
        assert resp.data["schemaName"] == "public"

    def test_create_connection_missing_name(self):
        mgr = _build_manager()
        req = make_request(
            data={"dbType": "postgresql", "host": "localhost"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "name" in resp.error.lower()


# ===========================================================================
# PUT -- update connection
# ===========================================================================

class TestUpdateConnection:

    def test_update_connection(self):
        mock_db = MagicMock()
        updated_item = {
            **SAMPLE_CONNECTION_ITEM,
            "name": "Renamed DB",
            "host": "new-host.example.com",
        }
        mock_db.connections.get_by_key.side_effect = [
            SAMPLE_CONNECTION_ITEM.copy(),  # initial lookup
            updated_item.copy(),            # after update
        ]
        mock_db.connections.update.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "connection_id": "conn-001",
                "name": "Renamed DB",
                "host": "new-host.example.com",
            },
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["name"] == "Renamed DB"
        assert resp.data["host"] == "new-host.example.com"
        assert "updated" in resp.message.lower()
        mock_db.connections.update.assert_called_once()

    def test_update_connection_password(self):
        """Password field is mapped to encrypted_password in update dict."""
        mock_db = MagicMock()
        mock_db.connections.get_by_key.side_effect = [
            SAMPLE_CONNECTION_ITEM.copy(),
            SAMPLE_CONNECTION_ITEM.copy(),
        ]
        mock_db.connections.update.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"connection_id": "conn-001", "password": "newpass"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        call_args = mock_db.connections.update.call_args
        updates = call_args[0][1]
        assert updates["encrypted_password"] == "newpass"

    def test_update_connection_not_found(self):
        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"connection_id": "nonexistent", "name": "Updated"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()

    def test_update_connection_missing_id(self):
        mgr = _build_manager()
        req = make_request(data={"name": "No ID"}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "id" in resp.error.lower()


# ===========================================================================
# DELETE -- remove connection
# ===========================================================================

class TestDeleteConnection:

    def test_delete_connection(self):
        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = SAMPLE_CONNECTION_ITEM.copy()
        mock_db.connections.delete_by_key.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "conn-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert "deleted" in resp.message.lower()
        mock_db.connections.delete_by_key.assert_called_once_with(
            {"user_id": "user-123", "id": "conn-001"}
        )

    def test_delete_connection_not_found(self):
        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "nonexistent"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()

    def test_delete_connection_missing_id(self):
        mgr = _build_manager()
        req = make_request(data={}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "id" in resp.error.lower()


# ===========================================================================
# test_connection -- test database connectivity
# ===========================================================================

class TestTestConnection:

    @patch("managers.connections.ConnectionResourceManager.ConnectorFactory")
    def test_test_connection_success(self, mock_factory_cls):
        mock_connector = MagicMock()
        mock_connector.test_connection.return_value = True
        mock_factory_cls.create_and_connect.return_value = mock_connector

        mock_db = MagicMock()
        mock_db.connections.get_by_key.side_effect = [
            SAMPLE_CONNECTION_ITEM.copy(),                            # initial lookup
            {**SAMPLE_CONNECTION_ITEM, "status": "connected"},        # after update
        ]
        mock_db.connections.update.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "conn-001"}, user_id="user-123")
        resp = mgr.test_connection(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["status"] == "connected"
        assert "successful" in resp.message.lower()
        mock_factory_cls.create_and_connect.assert_called_once()
        mock_connector.test_connection.assert_called_once()
        mock_connector.disconnect.assert_called_once()
        mock_db.connections.update.assert_called_with("conn-001", {"status": "connected"})

    @patch("managers.connections.ConnectionResourceManager.ConnectorFactory")
    def test_test_connection_failure(self, mock_factory_cls):
        mock_factory_cls.create_and_connect.side_effect = Exception("Connection refused")

        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = SAMPLE_CONNECTION_ITEM.copy()
        mock_db.connections.update.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "conn-001"}, user_id="user-123")
        resp = mgr.test_connection(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "failed" in resp.error.lower()
        mock_db.connections.update.assert_called_with("conn-001", {"status": "failed"})

    @patch("managers.connections.ConnectionResourceManager.ConnectorFactory")
    def test_test_connection_returns_false(self, mock_factory_cls):
        """When test_connection returns False, status should be 'failed'."""
        mock_connector = MagicMock()
        mock_connector.test_connection.return_value = False
        mock_factory_cls.create_and_connect.return_value = mock_connector

        mock_db = MagicMock()
        mock_db.connections.get_by_key.side_effect = [
            SAMPLE_CONNECTION_ITEM.copy(),
            {**SAMPLE_CONNECTION_ITEM, "status": "failed"},
        ]
        mock_db.connections.update.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "conn-001"}, user_id="user-123")
        resp = mgr.test_connection(req)

        assert resp.success is True
        assert resp.data["status"] == "failed"
        mock_db.connections.update.assert_called_with("conn-001", {"status": "failed"})

    def test_test_connection_not_found(self):
        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "nonexistent"}, user_id="user-123")
        resp = mgr.test_connection(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()


# ===========================================================================
# get_tables -- list tables in the connected database
# ===========================================================================

class TestGetTables:

    @patch("managers.connections.ConnectionResourceManager.ConnectorFactory")
    def test_get_tables(self, mock_factory_cls):
        mock_connector = MagicMock()
        mock_connector.get_tables.return_value = ["users", "orders", "products"]
        mock_factory_cls.create_and_connect.return_value = mock_connector

        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = SAMPLE_CONNECTION_ITEM.copy()

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "conn-001"}, user_id="user-123")
        resp = mgr.get_tables(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) == 3
        assert resp.data[0] == {"name": "users", "schema": "public"}
        assert resp.data[1] == {"name": "orders", "schema": "public"}
        assert resp.data[2] == {"name": "products", "schema": "public"}
        mock_factory_cls.create_and_connect.assert_called_once()
        mock_connector.get_tables.assert_called_once()
        mock_connector.disconnect.assert_called_once()

    def test_get_tables_not_found(self):
        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "nonexistent"}, user_id="user-123")
        resp = mgr.get_tables(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()

    @patch("managers.connections.ConnectionResourceManager.ConnectorFactory")
    def test_get_tables_connector_error(self, mock_factory_cls):
        mock_factory_cls.create_and_connect.side_effect = Exception("Auth failed")

        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = SAMPLE_CONNECTION_ITEM.copy()

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "conn-001"}, user_id="user-123")
        resp = mgr.get_tables(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to get tables" in resp.error.lower()


# ===========================================================================
# get_table_schema -- get column info and sample data
# ===========================================================================

class TestGetTableSchema:

    @patch("managers.connections.ConnectionResourceManager.ConnectorFactory")
    def test_get_table_schema(self, mock_factory_cls):
        schema_info = [
            {"column_name": "id", "data_type": "integer", "is_nullable": False},
            {"column_name": "name", "data_type": "varchar", "is_nullable": True},
        ]
        sample_rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        mock_connector = MagicMock()
        mock_connector.get_table_schema.return_value = schema_info
        mock_connector.get_sample_data.return_value = sample_rows
        mock_factory_cls.create_and_connect.return_value = mock_connector

        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = SAMPLE_CONNECTION_ITEM.copy()

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"connection_id": "conn-001", "table_name": "users"},
            user_id="user-123",
        )
        resp = mgr.get_table_schema(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["schema"] == schema_info
        assert resp.data["sampleData"] == sample_rows
        mock_connector.get_table_schema.assert_called_once_with("users")
        mock_connector.get_sample_data.assert_called_once_with("users", limit=5)
        mock_connector.disconnect.assert_called_once()

    def test_get_table_schema_connection_not_found(self):
        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"connection_id": "nonexistent", "table_name": "users"},
            user_id="user-123",
        )
        resp = mgr.get_table_schema(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()


# ===========================================================================
# create_source_from_table -- create a Source from a database table
# ===========================================================================

class TestCreateSourceFromTable:

    @patch("managers.connections.ConnectionResourceManager.ConnectorFactory")
    def test_create_source_from_table(self, mock_factory_cls):
        schema_info = [
            {"column_name": "id", "data_type": "integer"},
            {"column_name": "email", "data_type": "varchar"},
        ]
        mock_connector = MagicMock()
        mock_connector.get_table_schema.return_value = schema_info
        mock_factory_cls.create_and_connect.return_value = mock_connector

        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = SAMPLE_CONNECTION_ITEM.copy()
        mock_db.sources.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "connection_id": "conn-001",
                "table_name": "users",
                "name": "Users Source",
            },
            user_id="user-123",
        )
        resp = mgr.create_source_from_table(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["name"] == "Users Source"
        assert resp.data["sourceType"] == "database"
        assert resp.data["isQueryable"] is True
        assert resp.data["connectionId"] == "conn-001"
        assert resp.data["tableName"] == "users"
        assert resp.data["status"] == "metadata_extracted"
        assert resp.data["metadataJson"] == json.dumps(schema_info)
        assert "created" in resp.message.lower()
        mock_db.sources.create.assert_called_once()
        mock_connector.get_table_schema.assert_called_once_with("users")
        mock_connector.disconnect.assert_called_once()

    @patch("managers.connections.ConnectionResourceManager.ConnectorFactory")
    def test_create_source_from_table_default_name(self, mock_factory_cls):
        """When no name is provided, table_name is used as the source name."""
        mock_connector = MagicMock()
        mock_connector.get_table_schema.return_value = []
        mock_factory_cls.create_and_connect.return_value = mock_connector

        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = SAMPLE_CONNECTION_ITEM.copy()
        mock_db.sources.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"connection_id": "conn-001", "table_name": "orders"},
            user_id="user-123",
        )
        resp = mgr.create_source_from_table(req)

        assert resp.success is True
        assert resp.data["name"] == "orders"

    def test_create_source_from_table_connection_not_found(self):
        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"connection_id": "nonexistent", "table_name": "users"},
            user_id="user-123",
        )
        resp = mgr.create_source_from_table(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()

    @patch("managers.connections.ConnectionResourceManager.ConnectorFactory")
    def test_create_source_from_table_with_sql_view_query(self, mock_factory_cls):
        """sql_view_query should be passed through to the SourceItem."""
        mock_connector = MagicMock()
        mock_connector.get_table_schema.return_value = []
        mock_factory_cls.create_and_connect.return_value = mock_connector

        mock_db = MagicMock()
        mock_db.connections.get_by_key.return_value = SAMPLE_CONNECTION_ITEM.copy()
        mock_db.sources.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "connection_id": "conn-001",
                "table_name": "users",
                "sql_view_query": "SELECT id, name FROM users WHERE active = true",
            },
            user_id="user-123",
        )
        resp = mgr.create_source_from_table(req)

        assert resp.success is True
        assert resp.data["sqlViewQuery"] == "SELECT id, name FROM users WHERE active = true"


# ===========================================================================
# Error handling
# ===========================================================================

class TestConnectionManagerErrors:

    def test_get_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.connections.find_by_user.side_effect = Exception("DynamoDB timeout")

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to get connections" in resp.error.lower()

    def test_post_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.connections.create.side_effect = Exception("DynamoDB write error")

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"name": "Test", "dbType": "postgresql"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to create connection" in resp.error.lower()

    def test_delete_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.connections.get_by_key.side_effect = Exception("DynamoDB error")

        mgr = _build_manager(mock_db)
        req = make_request(data={"connection_id": "conn-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to delete connection" in resp.error.lower()
