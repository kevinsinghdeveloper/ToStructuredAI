"""Unit tests for SourceResourceManager."""
import json
import pytest
from unittest.mock import MagicMock

from tests.conftest import make_request


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_SOURCE_ITEM = {
    "user_id": "user-123",
    "id": "src-001",
    "name": "Users Table",
    "source_type": "database",
    "is_queryable": True,
    "status": "metadata_extracted",
    "document_id": None,
    "connection_id": "conn-001",
    "table_name": "users",
    "sql_view_query": None,
    "metadata_json": json.dumps([
        {"column_name": "id", "data_type": "integer"},
        {"column_name": "name", "data_type": "varchar"},
    ]),
    "delimiter": None,
    "created_at": "2024-06-01T00:00:00",
    "updated_at": "2024-06-01T00:00:00",
}

SAMPLE_SOURCE_ITEM_2 = {
    **SAMPLE_SOURCE_ITEM,
    "id": "src-002",
    "name": "Uploaded CSV",
    "source_type": "document",
    "is_queryable": False,
    "status": "ready",
    "connection_id": None,
    "table_name": None,
    "document_id": "doc-001",
    "metadata_json": None,
    "delimiter": ",",
}


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _build_manager(mock_db=None):
    """Instantiate SourceResourceManager with mock services."""
    from managers.sources.SourceResourceManager import SourceResourceManager

    if mock_db is None:
        mock_db = MagicMock()
    service_managers = {"db": mock_db}
    return SourceResourceManager(service_managers=service_managers)


# ===========================================================================
# GET -- list all sources for a user
# ===========================================================================

class TestGetAllSources:

    def test_get_all_sources(self):
        mock_db = MagicMock()
        mock_db.sources.find_by_user.return_value = [
            SAMPLE_SOURCE_ITEM.copy(),
            SAMPLE_SOURCE_ITEM_2.copy(),
        ]

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) == 2
        assert resp.data[0]["id"] == "src-001"
        assert resp.data[0]["sourceType"] == "database"
        assert resp.data[0]["isQueryable"] is True
        assert resp.data[1]["id"] == "src-002"
        assert resp.data[1]["sourceType"] == "document"
        mock_db.sources.find_by_user.assert_called_once_with("user-123")

    def test_get_all_sources_empty(self):
        mock_db = MagicMock()
        mock_db.sources.find_by_user.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data == []


# ===========================================================================
# GET -- single source by ID
# ===========================================================================

class TestGetSingleSource:

    def test_get_single_source(self):
        mock_db = MagicMock()
        mock_db.sources.get_by_key.return_value = SAMPLE_SOURCE_ITEM.copy()

        mgr = _build_manager(mock_db)
        req = make_request(data={"source_id": "src-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["id"] == "src-001"
        assert resp.data["name"] == "Users Table"
        assert resp.data["sourceType"] == "database"
        assert resp.data["isQueryable"] is True
        assert resp.data["connectionId"] == "conn-001"
        assert resp.data["tableName"] == "users"
        assert resp.data["status"] == "metadata_extracted"
        mock_db.sources.get_by_key.assert_called_once_with(
            {"user_id": "user-123", "id": "src-001"}
        )

    def test_get_source_not_found(self):
        mock_db = MagicMock()
        mock_db.sources.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"source_id": "nonexistent"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()


# ===========================================================================
# POST -- create source
# ===========================================================================

class TestCreateSource:

    def test_create_source(self):
        mock_db = MagicMock()
        mock_db.sources.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "New Source",
                "source_type": "database",
                "is_queryable": True,
                "status": "pending",
                "connection_id": "conn-001",
                "table_name": "orders",
                "metadata": [{"column_name": "id", "data_type": "integer"}],
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["name"] == "New Source"
        assert resp.data["sourceType"] == "database"
        assert resp.data["isQueryable"] is True
        assert resp.data["connectionId"] == "conn-001"
        assert resp.data["tableName"] == "orders"
        assert resp.data["metadataJson"] == json.dumps(
            [{"column_name": "id", "data_type": "integer"}]
        )
        assert resp.data["userId"] == "user-123"
        assert "created" in resp.message.lower()
        mock_db.sources.create.assert_called_once()

    def test_create_source_document_type(self):
        mock_db = MagicMock()
        mock_db.sources.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "CSV Upload",
                "source_type": "document",
                "is_queryable": False,
                "document_id": "doc-001",
                "delimiter": ",",
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["sourceType"] == "document"
        assert resp.data["documentId"] == "doc-001"
        assert resp.data["delimiter"] == ","
        assert resp.data["isQueryable"] is False

    def test_create_source_defaults(self):
        """Fields not provided should fall back to defaults."""
        mock_db = MagicMock()
        mock_db.sources.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={}, user_id="user-123")
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["name"] == ""
        assert resp.data["sourceType"] == "document"
        assert resp.data["isQueryable"] is False
        assert resp.data["status"] == "pending"

    def test_create_source_no_metadata(self):
        """When metadata is not provided, metadataJson should be None."""
        mock_db = MagicMock()
        mock_db.sources.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"name": "No Metadata Source"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.data["metadataJson"] is None


# ===========================================================================
# PUT -- update source metadata
# ===========================================================================

class TestUpdateSource:

    def test_update_source_metadata(self):
        new_metadata = [
            {"column_name": "id", "data_type": "integer", "description": "Primary key"},
            {"column_name": "name", "data_type": "varchar", "description": "User name"},
        ]
        updated_item = {
            **SAMPLE_SOURCE_ITEM,
            "metadata_json": json.dumps(new_metadata),
            "name": "Renamed Source",
        }
        mock_db = MagicMock()
        mock_db.sources.get_by_key.side_effect = [
            SAMPLE_SOURCE_ITEM.copy(),  # initial lookup
            updated_item.copy(),        # after update
        ]
        mock_db.sources.update.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "source_id": "src-001",
                "name": "Renamed Source",
                "metadata": new_metadata,
            },
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["name"] == "Renamed Source"
        assert resp.data["metadataJson"] == json.dumps(new_metadata)
        assert "updated" in resp.message.lower()
        mock_db.sources.update.assert_called_once()

        # Verify the update dict contains expected keys
        call_args = mock_db.sources.update.call_args
        updates = call_args[0][1]
        assert "metadata_json" in updates
        assert "name" in updates
        assert "updated_at" in updates

    def test_update_source_sql_view_query(self):
        updated_item = {
            **SAMPLE_SOURCE_ITEM,
            "sql_view_query": "SELECT * FROM users WHERE active = true",
        }
        mock_db = MagicMock()
        mock_db.sources.get_by_key.side_effect = [
            SAMPLE_SOURCE_ITEM.copy(),
            updated_item.copy(),
        ]
        mock_db.sources.update.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "source_id": "src-001",
                "sql_view_query": "SELECT * FROM users WHERE active = true",
            },
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert resp.data["sqlViewQuery"] == "SELECT * FROM users WHERE active = true"
        call_args = mock_db.sources.update.call_args
        updates = call_args[0][1]
        assert updates["sql_view_query"] == "SELECT * FROM users WHERE active = true"

    def test_update_source_not_found(self):
        mock_db = MagicMock()
        mock_db.sources.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"source_id": "nonexistent", "name": "Updated"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()

    def test_update_source_missing_id(self):
        mgr = _build_manager()
        req = make_request(data={"name": "No ID"}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "id" in resp.error.lower()


# ===========================================================================
# DELETE -- remove source with cascade cleanup
# ===========================================================================

class TestDeleteSource:

    def test_delete_source(self):
        pipeline_link_1 = {"pipeline_id": "pipe-001", "source_id": "src-001"}
        pipeline_link_2 = {"pipeline_id": "pipe-002", "source_id": "src-001"}
        temp_table_1 = {"pipeline_id": "pipe-001", "id": "tmp-001"}
        temp_table_2 = {"pipeline_id": "pipe-001", "id": "tmp-002"}

        mock_db = MagicMock()
        mock_db.sources.get_by_key.return_value = SAMPLE_SOURCE_ITEM.copy()
        mock_db.pipeline_sources.find_by_source.return_value = [pipeline_link_1, pipeline_link_2]
        mock_db.temp_data_tables.find_by_source.return_value = [temp_table_1, temp_table_2]
        mock_db.sources.delete_by_key.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={"source_id": "src-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert "deleted" in resp.message.lower()

        # Verify pipeline_sources cascade cleanup
        mock_db.pipeline_sources.find_by_source.assert_called_once_with("src-001")
        assert mock_db.pipeline_sources.delete_by_key.call_count == 2
        mock_db.pipeline_sources.delete_by_key.assert_any_call(
            {"pipeline_id": "pipe-001", "source_id": "src-001"}
        )
        mock_db.pipeline_sources.delete_by_key.assert_any_call(
            {"pipeline_id": "pipe-002", "source_id": "src-001"}
        )

        # Verify temp_data_tables cascade cleanup
        mock_db.temp_data_tables.find_by_source.assert_called_once_with("src-001")
        assert mock_db.temp_data_tables.delete_by_key.call_count == 2
        mock_db.temp_data_tables.delete_by_key.assert_any_call(
            {"pipeline_id": "pipe-001", "id": "tmp-001"}
        )
        mock_db.temp_data_tables.delete_by_key.assert_any_call(
            {"pipeline_id": "pipe-001", "id": "tmp-002"}
        )

        # Verify source itself is deleted
        mock_db.sources.delete_by_key.assert_called_once_with(
            {"user_id": "user-123", "id": "src-001"}
        )

    def test_delete_source_no_cascades(self):
        """Source with no pipeline links or temp tables deletes cleanly."""
        mock_db = MagicMock()
        mock_db.sources.get_by_key.return_value = SAMPLE_SOURCE_ITEM.copy()
        mock_db.pipeline_sources.find_by_source.return_value = []
        mock_db.temp_data_tables.find_by_source.return_value = []
        mock_db.sources.delete_by_key.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={"source_id": "src-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is True
        assert resp.status_code == 200
        mock_db.pipeline_sources.delete_by_key.assert_not_called()
        mock_db.temp_data_tables.delete_by_key.assert_not_called()
        mock_db.sources.delete_by_key.assert_called_once()

    def test_delete_source_not_found(self):
        mock_db = MagicMock()
        mock_db.sources.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"source_id": "nonexistent"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()

    def test_delete_source_missing_id(self):
        mgr = _build_manager()
        req = make_request(data={}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "id" in resp.error.lower()


# ===========================================================================
# Error handling
# ===========================================================================

class TestSourceManagerErrors:

    def test_get_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.sources.find_by_user.side_effect = Exception("DynamoDB timeout")

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to get sources" in resp.error.lower()

    def test_post_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.sources.create.side_effect = Exception("DynamoDB write error")

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"name": "Test Source"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to create source" in resp.error.lower()

    def test_put_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.sources.get_by_key.side_effect = Exception("DynamoDB error")

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"source_id": "src-001", "name": "Updated"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to update source" in resp.error.lower()

    def test_delete_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.sources.get_by_key.side_effect = Exception("DynamoDB error")

        mgr = _build_manager(mock_db)
        req = make_request(data={"source_id": "src-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to delete source" in resp.error.lower()
