"""Unit tests for PipelineTypeResourceManager."""
import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import make_request


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_PIPELINE_TYPE = {
    "id": "document_extraction",
    "name": "Document Extraction",
    "description": "Extract structured data from documents",
    "icon": "description",
    "category": "extraction",
    "supports_chat": False,
    "supports_extraction": True,
    "output_schema": {"type": "object"},
    "prompt_template": "Extract the following fields from the document: {fields}",
}

SAMPLE_PIPELINE_TYPE_2 = {
    "id": "chat_analysis",
    "name": "Chat Analysis",
    "description": "Analyze documents via conversational AI",
    "icon": "chat",
    "category": "analysis",
    "supports_chat": True,
    "supports_extraction": False,
}

SAMPLE_ALL_TYPES_SUMMARY = [
    {
        "id": "document_extraction",
        "name": "Document Extraction",
        "description": "Extract structured data from documents",
        "icon": "description",
        "category": "extraction",
        "supports_chat": False,
        "supports_extraction": True,
    },
    {
        "id": "chat_analysis",
        "name": "Chat Analysis",
        "description": "Analyze documents via conversational AI",
        "icon": "chat",
        "category": "analysis",
        "supports_chat": True,
        "supports_extraction": False,
    },
]


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _build_manager(mock_db=None, mock_pipeline_type_service=None):
    """Instantiate PipelineTypeResourceManager with optional mock services.

    PipelineTypeService is instantiated inside __init__, so we patch the
    class at the import location used by the manager module.
    """
    from managers.pipeline_types.PipelineTypeResourceManager import PipelineTypeResourceManager

    if mock_db is None:
        mock_db = MagicMock()

    service_managers = {"db": mock_db}

    if mock_pipeline_type_service is not None:
        with patch(
            "managers.pipeline_types.PipelineTypeResourceManager.PipelineTypeService",
            return_value=mock_pipeline_type_service,
        ):
            mgr = PipelineTypeResourceManager(service_managers=service_managers)
    else:
        mgr = PipelineTypeResourceManager(service_managers=service_managers)

    return mgr


# ===========================================================================
# GET -- list all pipeline types
# ===========================================================================

class TestGetPipelineTypes:

    def test_get_all_pipeline_types_success(self):
        mock_service = MagicMock()
        mock_service.get_all_pipeline_types.return_value = SAMPLE_ALL_TYPES_SUMMARY.copy()

        mgr = _build_manager(mock_pipeline_type_service=mock_service)
        req = make_request(data={})
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) == 2
        assert resp.data[0]["id"] == "document_extraction"
        assert resp.data[1]["id"] == "chat_analysis"
        mock_service.get_all_pipeline_types.assert_called_once()

    def test_get_all_pipeline_types_empty(self):
        mock_service = MagicMock()
        mock_service.get_all_pipeline_types.return_value = []

        mgr = _build_manager(mock_pipeline_type_service=mock_service)
        req = make_request(data={})
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data == []

    def test_get_single_pipeline_type_success(self):
        mock_service = MagicMock()
        mock_service.get_pipeline_type.return_value = SAMPLE_PIPELINE_TYPE.copy()

        mgr = _build_manager(mock_pipeline_type_service=mock_service)
        req = make_request(data={"type_id": "document_extraction"})
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["id"] == "document_extraction"
        assert resp.data["name"] == "Document Extraction"
        assert resp.data["supports_extraction"] is True
        mock_service.get_pipeline_type.assert_called_once_with("document_extraction")

    def test_get_single_pipeline_type_not_found(self):
        mock_service = MagicMock()
        mock_service.get_pipeline_type.return_value = None

        mgr = _build_manager(mock_pipeline_type_service=mock_service)
        req = make_request(data={"type_id": "nonexistent_type"})
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()
        mock_service.get_pipeline_type.assert_called_once_with("nonexistent_type")

    def test_get_pipeline_types_service_exception(self):
        mock_service = MagicMock()
        mock_service.get_all_pipeline_types.side_effect = Exception("Service unavailable")

        mgr = _build_manager(mock_pipeline_type_service=mock_service)
        req = make_request(data={})
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to retrieve pipeline types" in resp.error.lower()

    def test_get_single_pipeline_type_exception(self):
        mock_service = MagicMock()
        mock_service.get_pipeline_type.side_effect = Exception("Unexpected error")

        mgr = _build_manager(mock_pipeline_type_service=mock_service)
        req = make_request(data={"type_id": "document_extraction"})
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to retrieve pipeline types" in resp.error.lower()

    def test_get_with_none_data(self):
        """Request with None data should list all types (no type_id)."""
        mock_service = MagicMock()
        mock_service.get_all_pipeline_types.return_value = SAMPLE_ALL_TYPES_SUMMARY.copy()

        mgr = _build_manager(mock_pipeline_type_service=mock_service)
        req = make_request(data=None)
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert len(resp.data) == 2
        mock_service.get_all_pipeline_types.assert_called_once()


# ===========================================================================
# POST -- method not allowed
# ===========================================================================

class TestPostPipelineType:

    def test_post_not_allowed(self):
        mgr = _build_manager()
        req = make_request(data={"name": "New Type"})
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 405
        assert "method not allowed" in resp.error.lower()


# ===========================================================================
# PUT -- method not allowed
# ===========================================================================

class TestPutPipelineType:

    def test_put_not_allowed(self):
        mgr = _build_manager()
        req = make_request(data={"id": "some_type", "name": "Updated"})
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 405
        assert "method not allowed" in resp.error.lower()


# ===========================================================================
# DELETE -- method not allowed
# ===========================================================================

class TestDeletePipelineType:

    def test_delete_not_allowed(self):
        mgr = _build_manager()
        req = make_request(data={"type_id": "document_extraction"})
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 405
        assert "method not allowed" in resp.error.lower()
