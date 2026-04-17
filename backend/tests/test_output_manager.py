"""Unit tests for OutputResourceManager."""
import pytest
from unittest.mock import MagicMock

from tests.conftest import make_request


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_OUTPUT_ITEM = {
    "pipeline_id": "pipe-001",
    "id": "out-001",
    "output_data": '{"result": "Extracted data here"}',
    "format": "json",
    "created_at": "2024-06-01T00:00:00",
}

SAMPLE_OUTPUT_ITEM_2 = {
    "pipeline_id": "pipe-001",
    "id": "out-002",
    "output_data": '{"result": "Second output"}',
    "format": "csv",
    "created_at": "2024-06-02T00:00:00",
}


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _build_manager(mock_db=None):
    """Instantiate OutputResourceManager with a mock db service."""
    from managers.outputs.OutputResourceManager import OutputResourceManager

    if mock_db is None:
        mock_db = MagicMock()
    service_managers = {"db": mock_db}
    return OutputResourceManager(service_managers=service_managers)


# ===========================================================================
# GET -- list outputs for a pipeline
# ===========================================================================

class TestGetOutputs:

    def test_get_outputs_success(self):
        mock_db = MagicMock()
        mock_db.outputs.find_by_pipeline.return_value = [
            SAMPLE_OUTPUT_ITEM.copy(),
            SAMPLE_OUTPUT_ITEM_2.copy(),
        ]

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"})
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) == 2
        assert resp.data[0]["id"] == "out-001"
        assert resp.data[0]["pipelineId"] == "pipe-001"
        assert resp.data[1]["id"] == "out-002"
        mock_db.outputs.find_by_pipeline.assert_called_once_with("pipe-001")

    def test_get_outputs_empty(self):
        mock_db = MagicMock()
        mock_db.outputs.find_by_pipeline.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"})
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data == []

    def test_get_outputs_missing_pipeline_id(self):
        mgr = _build_manager()
        req = make_request(data={})
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "pipeline_id" in resp.error.lower()

    def test_get_outputs_none_data(self):
        """Request with None data should still return 400 for missing pipeline_id."""
        mgr = _build_manager()
        req = make_request(data=None)
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 400

    def test_get_outputs_db_error(self):
        mock_db = MagicMock()
        mock_db.outputs.find_by_pipeline.side_effect = Exception("DynamoDB timeout")

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"})
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to retrieve outputs" in resp.error.lower()

    def test_get_outputs_api_dict_format(self):
        """Verify to_api_dict produces camelCase keys with parsed JSON output_data."""
        mock_db = MagicMock()
        mock_db.outputs.find_by_pipeline.return_value = [SAMPLE_OUTPUT_ITEM.copy()]

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"})
        resp = mgr.get(req)

        item = resp.data[0]
        assert "pipelineId" in item
        assert "outputData" in item
        assert "createdAt" in item
        # output_data should be parsed from JSON string to dict
        assert isinstance(item["outputData"], dict)
        assert item["outputData"]["result"] == "Extracted data here"


# ===========================================================================
# POST -- method not allowed
# ===========================================================================

class TestPostOutput:

    def test_post_not_allowed(self):
        mgr = _build_manager()
        req = make_request(data={"some": "data"})
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 405
        assert "pipeline execution" in resp.error.lower()


# ===========================================================================
# PUT -- method not allowed
# ===========================================================================

class TestPutOutput:

    def test_put_not_allowed(self):
        mgr = _build_manager()
        req = make_request(data={"some": "data"})
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 405
        assert "method not allowed" in resp.error.lower()


# ===========================================================================
# DELETE -- remove a single output
# ===========================================================================

class TestDeleteOutput:

    def test_delete_output_success(self):
        mock_db = MagicMock()
        mock_db.outputs.delete_by_key.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={"output_id": "out-001", "pipeline_id": "pipe-001"})
        resp = mgr.delete(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert "deleted" in resp.message.lower()
        mock_db.outputs.delete_by_key.assert_called_once_with(
            {"pipeline_id": "pipe-001", "id": "out-001"}
        )

    def test_delete_output_missing_output_id(self):
        mgr = _build_manager()
        req = make_request(data={"pipeline_id": "pipe-001"})
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "output_id" in resp.error.lower()

    def test_delete_output_missing_pipeline_id(self):
        mgr = _build_manager()
        req = make_request(data={"output_id": "out-001"})
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "pipeline_id" in resp.error.lower()

    def test_delete_output_missing_both_ids(self):
        mgr = _build_manager()
        req = make_request(data={})
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 400

    def test_delete_output_db_error(self):
        mock_db = MagicMock()
        mock_db.outputs.delete_by_key.side_effect = Exception("DynamoDB error")

        mgr = _build_manager(mock_db)
        req = make_request(data={"output_id": "out-001", "pipeline_id": "pipe-001"})
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to delete output" in resp.error.lower()


# ===========================================================================
# download_output
# ===========================================================================

class TestDownloadOutput:

    def test_download_output_success(self):
        mock_db = MagicMock()
        mock_db.outputs.get_by_key.return_value = SAMPLE_OUTPUT_ITEM.copy()

        mgr = _build_manager(mock_db)
        file_data, filename, mime = mgr.download_output("pipe-001", "out-001")

        assert file_data is not None
        assert isinstance(file_data, bytes)
        assert b"Extracted data here" in file_data
        assert filename == "output_out-001.json"
        assert mime == "application/json"
        mock_db.outputs.get_by_key.assert_called_once_with(
            {"pipeline_id": "pipe-001", "id": "out-001"}
        )

    def test_download_output_not_found(self):
        mock_db = MagicMock()
        mock_db.outputs.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        file_data, message, status = mgr.download_output("pipe-001", "nonexistent")

        assert file_data is None
        assert status == 404
        assert "not found" in message.lower()

    def test_download_output_empty_data(self):
        """Output with no output_data should default to empty JSON object."""
        mock_db = MagicMock()
        output_no_data = {
            "pipeline_id": "pipe-001",
            "id": "out-003",
        }
        mock_db.outputs.get_by_key.return_value = output_no_data

        mgr = _build_manager(mock_db)
        file_data, filename, mime = mgr.download_output("pipe-001", "out-003")

        assert file_data is not None
        assert file_data == b"{}"
        assert filename == "output_out-003.json"
