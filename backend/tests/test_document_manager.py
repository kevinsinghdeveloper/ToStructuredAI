"""Unit tests for DocumentResourceManager."""
import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock, ANY

from tests.conftest import make_request, SAMPLE_USER_ITEM


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_DOCUMENT_ITEM = {
    "user_id": "user-123",
    "id": "doc-001",
    "embedding_model_id": "emb-model-001",
    "filename": "abc123.pdf",
    "original_filename": "research.pdf",
    "file_path": "user_user-123/abc123.pdf",
    "file_size": 102400,
    "mime_type": "application/pdf",
    "status": "ready",
    "extracted_text": "Sample extracted text",
    "doc_metadata": None,
    "chunk_count": 5,
    "created_at": "2024-06-01T00:00:00",
    "updated_at": "2024-06-01T00:00:00",
}

SAMPLE_DOCUMENT_ITEM_2 = {
    **SAMPLE_DOCUMENT_ITEM,
    "id": "doc-002",
    "filename": "def456.txt",
    "original_filename": "notes.txt",
    "file_path": "user_user-123/def456.txt",
    "file_size": 2048,
    "mime_type": "text/plain",
    "status": "ready",
    "embedding_model_id": "emb-model-002",
    "chunk_count": 2,
}

SAMPLE_UPLOADED_DOCUMENT_ITEM = {
    **SAMPLE_DOCUMENT_ITEM,
    "id": "doc-003",
    "status": "uploaded",
    "chunk_count": 0,
    "extracted_text": None,
}


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _build_manager(mock_db=None, mock_storage=None, mock_processor=None, mock_vector_db=None):
    """Instantiate DocumentResourceManager with mock services."""
    from managers.documents.DocumentResourceManager import DocumentResourceManager

    if mock_db is None:
        mock_db = MagicMock()
    service_managers = {
        "db": mock_db,
        "storage": mock_storage or MagicMock(),
        "processor": mock_processor or MagicMock(),
        "vector_db": mock_vector_db or MagicMock(),
    }
    return DocumentResourceManager(service_managers=service_managers)


# ===========================================================================
# GET -- list all documents for a user
# ===========================================================================

class TestGetDocuments:

    def test_get_all_documents_success(self):
        mock_db = MagicMock()
        mock_db.documents.find_by_user.return_value = [
            SAMPLE_DOCUMENT_ITEM.copy(),
            SAMPLE_DOCUMENT_ITEM_2.copy(),
        ]

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) == 2
        assert resp.data[0]["id"] == "doc-001"
        assert resp.data[1]["id"] == "doc-002"
        mock_db.documents.find_by_user.assert_called_once_with("user-123")

    def test_get_all_documents_empty(self):
        mock_db = MagicMock()
        mock_db.documents.find_by_user.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data == []


# ===========================================================================
# GET -- single document by ID
# ===========================================================================

class TestGetSingleDocument:

    def test_get_document_by_id_success(self):
        mock_db = MagicMock()
        mock_db.documents.get_by_key.return_value = SAMPLE_DOCUMENT_ITEM.copy()

        mgr = _build_manager(mock_db)
        req = make_request(data={"document_id": "doc-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["id"] == "doc-001"
        assert resp.data["fileName"] == "research.pdf"
        assert resp.data["status"] == "ready"
        mock_db.documents.get_by_key.assert_called_once_with({"user_id": "user-123", "id": "doc-001"})

    def test_get_document_not_found(self):
        mock_db = MagicMock()
        mock_db.documents.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"document_id": "nonexistent"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()


# ===========================================================================
# GET -- filter by embedding model
# ===========================================================================

class TestGetByEmbeddingModel:

    def test_get_by_embedding_model_success(self):
        mock_db = MagicMock()
        mock_db.documents.find_by_user.return_value = [
            SAMPLE_DOCUMENT_ITEM.copy(),       # emb-model-001, ready
            SAMPLE_DOCUMENT_ITEM_2.copy(),     # emb-model-002, ready
        ]

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"action": "by_embedding_model", "embedding_model_id": "emb-model-001"},
            user_id="user-123",
        )
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["id"] == "doc-001"

    def test_get_by_embedding_model_filters_non_ready(self):
        """Only documents with status='ready' are returned."""
        non_ready = {**SAMPLE_DOCUMENT_ITEM, "status": "extracting"}
        mock_db = MagicMock()
        mock_db.documents.find_by_user.return_value = [non_ready]

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"action": "by_embedding_model", "embedding_model_id": "emb-model-001"},
            user_id="user-123",
        )
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.data == []

    def test_get_by_embedding_model_missing_id(self):
        mock_db = MagicMock()

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"action": "by_embedding_model"},
            user_id="user-123",
        )
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "embedding_model_id" in resp.error.lower()


# ===========================================================================
# POST -- upload document
# ===========================================================================

class TestPostDocument:

    def test_upload_document_success(self):
        mock_db = MagicMock()
        mock_db.documents.find_by_user.return_value = []
        mock_db.documents.create.return_value = {}

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "user_user-123/somefile.pdf"

        mgr = _build_manager(mock_db, mock_storage=mock_storage)

        file_content = b"PDF file content here"
        fake_file = BytesIO(file_content)

        req = make_request(
            data={
                "file": fake_file,
                "filename": "report.pdf",
                "mime_type": "application/pdf",
                "embedding_model_id": "emb-model-001",
            },
            user_id="user-123",
        )

        with patch("managers.documents.DocumentResourceManager.threading") as mock_threading:
            resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["fileName"] == "report.pdf"
        assert resp.data["status"] == "uploaded"
        mock_db.documents.create.assert_called_once()
        mock_storage.upload_file.assert_called_once()
        mock_threading.Thread.assert_called_once()

    def test_upload_document_missing_file(self):
        mgr = _build_manager()

        req = make_request(
            data={"filename": "report.pdf", "mime_type": "application/pdf", "embedding_model_id": "emb-model-001"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "required" in resp.error.lower()

    def test_upload_document_missing_filename(self):
        mgr = _build_manager()

        req = make_request(
            data={"file": BytesIO(b"data"), "mime_type": "application/pdf", "embedding_model_id": "emb-model-001"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400

    def test_upload_document_missing_mime_type(self):
        mgr = _build_manager()

        req = make_request(
            data={"file": BytesIO(b"data"), "filename": "report.pdf", "embedding_model_id": "emb-model-001"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400

    def test_upload_document_missing_embedding_model_id(self):
        mgr = _build_manager()

        req = make_request(
            data={"file": BytesIO(b"data"), "filename": "report.pdf", "mime_type": "application/pdf"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "embedding_model_id" in resp.error.lower()

    def test_upload_document_duplicate_no_overwrite(self):
        mock_db = MagicMock()
        mock_db.documents.find_by_user.return_value = [SAMPLE_DOCUMENT_ITEM.copy()]

        mgr = _build_manager(mock_db)

        req = make_request(
            data={
                "file": BytesIO(b"data"),
                "filename": "research.pdf",  # same as SAMPLE_DOCUMENT_ITEM.original_filename
                "mime_type": "application/pdf",
                "embedding_model_id": "emb-model-001",
                "overwrite": False,
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 409
        assert "already exists" in resp.error.lower()
        assert resp.data["existing_document"]["id"] == "doc-001"

    def test_upload_document_duplicate_with_overwrite(self):
        existing = SAMPLE_DOCUMENT_ITEM.copy()
        mock_db = MagicMock()
        mock_db.documents.find_by_user.return_value = [existing]
        mock_db.documents.create.return_value = {}
        mock_db.documents.get_by_key.return_value = existing
        mock_db.pipeline_documents.find_by.return_value = []

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "user_user-123/newfile.pdf"

        mock_vector_db = MagicMock()

        mgr = _build_manager(mock_db, mock_storage=mock_storage, mock_vector_db=mock_vector_db)

        req = make_request(
            data={
                "file": BytesIO(b"new content"),
                "filename": "research.pdf",
                "mime_type": "application/pdf",
                "embedding_model_id": "emb-model-001",
                "overwrite": True,
            },
            user_id="user-123",
        )

        with patch("managers.documents.DocumentResourceManager.threading"):
            resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        # Old document should have been deleted
        mock_db.document_chunks.delete_where.assert_called_once_with("document_id", "doc-001")
        mock_vector_db.delete_by_namespace.assert_called_once_with("doc-001")


# ===========================================================================
# PUT -- update document metadata
# ===========================================================================

class TestPutDocument:

    def test_update_document_metadata_success(self):
        mock_db = MagicMock()
        updated_item = {**SAMPLE_DOCUMENT_ITEM, "doc_metadata": '{"tags": ["important"]}'}
        mock_db.documents.get_by_key.side_effect = [
            SAMPLE_DOCUMENT_ITEM.copy(),  # initial lookup
            updated_item.copy(),          # after update
        ]
        mock_db.documents.update.return_value = {}

        mgr = _build_manager(mock_db)

        req = make_request(
            data={"document_id": "doc-001", "metadata": {"tags": ["important"]}},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert resp.status_code == 200
        mock_db.documents.update.assert_called_once()

    def test_update_document_missing_id(self):
        mgr = _build_manager()

        req = make_request(data={"metadata": {"tags": ["test"]}}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "document id" in resp.error.lower()

    def test_update_document_not_found(self):
        mock_db = MagicMock()
        mock_db.documents.get_by_key.return_value = None

        mgr = _build_manager(mock_db)

        req = make_request(data={"document_id": "nonexistent"}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()


# ===========================================================================
# DELETE -- remove document (cascading to chunks, vectors, storage)
# ===========================================================================

class TestDeleteDocument:

    def test_delete_document_success(self):
        mock_db = MagicMock()
        mock_db.documents.get_by_key.return_value = SAMPLE_DOCUMENT_ITEM.copy()
        mock_db.pipeline_documents.find_by.return_value = []
        mock_db.documents.delete_by_key.return_value = {}
        mock_db.document_chunks.delete_where.return_value = {}

        mock_vector_db = MagicMock()
        mock_storage = MagicMock()

        mgr = _build_manager(mock_db, mock_storage=mock_storage, mock_vector_db=mock_vector_db)

        req = make_request(data={"document_id": "doc-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert "deleted" in resp.message.lower()

        # Verify cascading deletes
        mock_db.document_chunks.delete_where.assert_called_once_with("document_id", "doc-001")
        mock_vector_db.delete_by_namespace.assert_called_once_with("doc-001")
        mock_storage.delete_file.assert_called_once_with(SAMPLE_DOCUMENT_ITEM["file_path"])
        mock_db.documents.delete_by_key.assert_called_once_with({"user_id": "user-123", "id": "doc-001"})

    def test_delete_document_removes_pipeline_links(self):
        pipeline_link = {"pipeline_id": "pipe-001", "document_id": "doc-001"}
        mock_db = MagicMock()
        mock_db.documents.get_by_key.return_value = SAMPLE_DOCUMENT_ITEM.copy()
        mock_db.pipeline_documents.find_by.return_value = [pipeline_link]
        mock_db.documents.delete_by_key.return_value = {}
        mock_db.document_chunks.delete_where.return_value = {}

        mock_vector_db = MagicMock()

        mgr = _build_manager(mock_db, mock_vector_db=mock_vector_db)

        req = make_request(data={"document_id": "doc-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is True
        mock_db.pipeline_documents.delete_by_key.assert_called_once_with(
            {"pipeline_id": "pipe-001", "document_id": "doc-001"}
        )

    def test_delete_document_missing_id(self):
        mgr = _build_manager()

        req = make_request(data={}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "document id" in resp.error.lower()

    def test_delete_document_not_found(self):
        mock_db = MagicMock()
        mock_db.documents.get_by_key.return_value = None

        mgr = _build_manager(mock_db)

        req = make_request(data={"document_id": "nonexistent"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()

    def test_delete_document_no_vector_db(self):
        """Deletion works even when vector_db service is not configured."""
        mock_db = MagicMock()
        mock_db.documents.get_by_key.return_value = SAMPLE_DOCUMENT_ITEM.copy()
        mock_db.pipeline_documents.find_by.return_value = []
        mock_db.documents.delete_by_key.return_value = {}
        mock_db.document_chunks.delete_where.return_value = {}

        service_managers = {"db": mock_db, "storage": MagicMock(), "vector_db": None}
        from managers.documents.DocumentResourceManager import DocumentResourceManager
        mgr = DocumentResourceManager(service_managers=service_managers)

        req = make_request(data={"document_id": "doc-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is True
        assert resp.status_code == 200


# ===========================================================================
# GET -- error handling
# ===========================================================================

class TestGetDocumentErrors:

    def test_get_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.documents.find_by_user.side_effect = Exception("DynamoDB connection timeout")

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to retrieve" in resp.error.lower()

    def test_get_single_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.documents.get_by_key.side_effect = Exception("DynamoDB error")

        mgr = _build_manager(mock_db)
        req = make_request(data={"document_id": "doc-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500


# ===========================================================================
# POST -- error handling
# ===========================================================================

class TestPostDocumentErrors:

    def test_post_handles_storage_exception(self):
        mock_db = MagicMock()
        mock_db.documents.find_by_user.return_value = []

        mock_storage = MagicMock()
        mock_storage.upload_file.side_effect = Exception("S3 upload failed")

        mgr = _build_manager(mock_db, mock_storage=mock_storage)

        req = make_request(
            data={
                "file": BytesIO(b"data"),
                "filename": "test.pdf",
                "mime_type": "application/pdf",
                "embedding_model_id": "emb-model-001",
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to upload" in resp.error.lower()


# ===========================================================================
# DELETE -- error handling
# ===========================================================================

class TestDeleteDocumentErrors:

    def test_delete_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.documents.get_by_key.side_effect = Exception("DynamoDB error")

        mgr = _build_manager(mock_db)
        req = make_request(data={"document_id": "doc-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to delete" in resp.error.lower()


# ===========================================================================
# download_document
# ===========================================================================

class TestDownloadDocument:

    def test_download_success(self):
        mock_db = MagicMock()
        mock_db.documents.get_by_key.return_value = SAMPLE_DOCUMENT_ITEM.copy()

        mock_storage = MagicMock()
        mock_storage.download_file.return_value = b"file bytes"

        mgr = _build_manager(mock_db, mock_storage=mock_storage)
        file_data, filename, mime = mgr.download_document("doc-001", "user-123")

        assert file_data == b"file bytes"
        assert filename == "research.pdf"
        assert mime == "application/pdf"

    def test_download_not_found(self):
        mock_db = MagicMock()
        mock_db.documents.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        file_data, message, status = mgr.download_document("nonexistent", "user-123")

        assert file_data is None
        assert status == 404
        assert "not found" in message.lower()
