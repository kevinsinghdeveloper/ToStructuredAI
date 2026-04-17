"""Unit tests for PipelineResourceManager."""
import json
import pytest
from unittest.mock import patch, MagicMock, ANY, call

from tests.conftest import make_request, SAMPLE_USER_ITEM


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_PIPELINE_ITEM = {
    "user_id": "user-123",
    "id": "pipe-001",
    "model_id": "model-001",
    "embedding_model_id": "emb-model-001",
    "name": "Test Pipeline",
    "description": "A test pipeline",
    "pipeline_type": "extraction",
    "config": '{"field_values": {"key": "value"}}',
    "prompt_template": "Extract data from: {context}",
    "output_schema": None,
    "status": "pending",
    "created_at": "2024-06-01T00:00:00",
    "updated_at": "2024-06-01T00:00:00",
}

SAMPLE_PIPELINE_ITEM_2 = {
    **SAMPLE_PIPELINE_ITEM,
    "id": "pipe-002",
    "name": "Second Pipeline",
    "description": "Another pipeline",
    "pipeline_type": "summarization",
    "config": None,
    "prompt_template": None,
}

SAMPLE_PIPELINE_DOC_LINK = {
    "pipeline_id": "pipe-001",
    "document_id": "doc-001",
    "id": "link-001",
    "created_at": "2024-06-01T00:00:00",
}

SAMPLE_PIPELINE_DOC_LINK_2 = {
    "pipeline_id": "pipe-001",
    "document_id": "doc-002",
    "id": "link-002",
    "created_at": "2024-06-01T00:00:00",
}

SAMPLE_MODEL_DATA = {
    "user_id": "user-123",
    "id": "model-001",
    "model_id": "gpt-4",
    "name": "GPT-4",
    "config": '{"temperature": 0.7}',
    "encrypted_api_key": "enc_key_abc123",
}

SAMPLE_CHUNK = {
    "id": "chunk-001",
    "document_id": "doc-001",
    "content": "This is sample chunk content for testing.",
}

SAMPLE_CHUNK_2 = {
    "id": "chunk-002",
    "document_id": "doc-001",
    "content": "This is another chunk of text.",
}


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _build_manager(mock_db=None):
    """Instantiate PipelineResourceManager with mock db and patched PipelineTypeService."""
    if mock_db is None:
        mock_db = MagicMock()
    service_managers = {"db": mock_db}

    with patch(
        "managers.pipelines.PipelineResourceManager.PipelineTypeService"
    ) as MockPTS:
        mock_pts_instance = MagicMock()
        MockPTS.return_value = mock_pts_instance

        from managers.pipelines.PipelineResourceManager import PipelineResourceManager
        mgr = PipelineResourceManager(service_managers=service_managers)

    return mgr


# ===========================================================================
# GET -- list all pipelines for a user
# ===========================================================================

class TestGetPipelines:

    def test_get_all_pipelines_success(self):
        mock_db = MagicMock()
        mock_db.pipelines.find_by_user.return_value = [
            SAMPLE_PIPELINE_ITEM.copy(),
            SAMPLE_PIPELINE_ITEM_2.copy(),
        ]
        mock_db.pipeline_documents.find_by.return_value = [SAMPLE_PIPELINE_DOC_LINK.copy()]

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) == 2
        assert resp.data[0]["id"] == "pipe-001"
        assert resp.data[0]["name"] == "Test Pipeline"
        assert resp.data[1]["id"] == "pipe-002"
        mock_db.pipelines.find_by_user.assert_called_once_with("user-123")

    def test_get_all_pipelines_empty(self):
        mock_db = MagicMock()
        mock_db.pipelines.find_by_user.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data == []

    def test_get_all_pipelines_includes_document_ids(self):
        mock_db = MagicMock()
        mock_db.pipelines.find_by_user.return_value = [SAMPLE_PIPELINE_ITEM.copy()]
        mock_db.pipeline_documents.find_by.return_value = [
            SAMPLE_PIPELINE_DOC_LINK.copy(),
            SAMPLE_PIPELINE_DOC_LINK_2.copy(),
        ]

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.data[0]["documentIds"] == ["doc-001", "doc-002"]


# ===========================================================================
# GET -- single pipeline by ID
# ===========================================================================

class TestGetSinglePipeline:

    def test_get_pipeline_by_id_success(self):
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.pipeline_documents.find_by.return_value = [SAMPLE_PIPELINE_DOC_LINK.copy()]

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["id"] == "pipe-001"
        assert resp.data["name"] == "Test Pipeline"
        assert resp.data["modelId"] == "model-001"
        assert resp.data["embeddingModelId"] == "emb-model-001"
        assert resp.data["pipelineType"] == "extraction"
        assert resp.data["status"] == "pending"
        assert resp.data["documentIds"] == ["doc-001"]
        mock_db.pipelines.get_by_key.assert_called_once_with(
            {"user_id": "user-123", "id": "pipe-001"}
        )

    def test_get_pipeline_returns_field_values_from_config(self):
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.pipeline_documents.find_by.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.data["fieldValues"] == {"key": "value"}

    def test_get_pipeline_not_found(self):
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "nonexistent"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()


# ===========================================================================
# POST -- create pipeline
# ===========================================================================

class TestPostPipeline:

    def test_create_pipeline_success_with_documents(self):
        mock_db = MagicMock()
        mock_db.pipelines.create.return_value = {}
        mock_db.pipeline_documents.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "New Pipeline",
                "modelId": "model-001",
                "embeddingModelId": "emb-model-001",
                "description": "A new pipeline",
                "pipelineType": "extraction",
                "documentIds": ["doc-001", "doc-002"],
                "promptTemplate": "Extract: {context}",
                "outputSchema": '{"type": "object"}',
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["name"] == "New Pipeline"
        assert resp.data["modelId"] == "model-001"
        assert resp.data["embeddingModelId"] == "emb-model-001"
        assert resp.data["pipelineType"] == "extraction"
        assert resp.data["status"] == "pending"
        assert resp.data["documentIds"] == ["doc-001", "doc-002"]
        mock_db.pipelines.create.assert_called_once()
        assert mock_db.pipeline_documents.create.call_count == 2

    def test_create_pipeline_success_no_documents(self):
        mock_db = MagicMock()
        mock_db.pipelines.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "Simple Pipeline",
                "modelId": "model-001",
                "embeddingModelId": "emb-model-001",
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["name"] == "Simple Pipeline"
        assert resp.data["documentIds"] == []
        mock_db.pipelines.create.assert_called_once()
        mock_db.pipeline_documents.create.assert_not_called()

    def test_create_pipeline_with_field_values(self):
        mock_db = MagicMock()
        mock_db.pipelines.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "Extraction Pipeline",
                "modelId": "model-001",
                "embeddingModelId": "emb-model-001",
                "fieldValues": {"company_name": "text", "revenue": "number"},
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["fieldValues"] == {"company_name": "text", "revenue": "number"}
        # Verify config was stored as JSON with field_values
        created_item = mock_db.pipelines.create.call_args[0][0]
        config = json.loads(created_item["config"])
        assert config["field_values"] == {"company_name": "text", "revenue": "number"}

    def test_create_pipeline_accepts_snake_case_keys(self):
        """Manager accepts both camelCase and snake_case field names."""
        mock_db = MagicMock()
        mock_db.pipelines.create.return_value = {}
        mock_db.pipeline_documents.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "Snake Case Pipeline",
                "model_id": "model-001",
                "embedding_model_id": "emb-model-001",
                "document_ids": ["doc-001"],
                "pipeline_type": "summarization",
                "field_values": {"field1": "value1"},
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["modelId"] == "model-001"
        assert resp.data["documentIds"] == ["doc-001"]

    def test_create_pipeline_missing_name(self):
        mgr = _build_manager()

        req = make_request(
            data={"modelId": "model-001", "embeddingModelId": "emb-model-001"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "name" in resp.error.lower()

    def test_create_pipeline_missing_model_id(self):
        mgr = _build_manager()

        req = make_request(
            data={"name": "Test", "embeddingModelId": "emb-model-001"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "model id" in resp.error.lower()

    def test_create_pipeline_missing_embedding_model_id(self):
        mgr = _build_manager()

        req = make_request(
            data={"name": "Test", "modelId": "model-001"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "embedding model id" in resp.error.lower()


# ===========================================================================
# PUT -- update pipeline
# ===========================================================================

class TestPutPipeline:

    def test_update_pipeline_success(self):
        mock_db = MagicMock()
        updated_item = {**SAMPLE_PIPELINE_ITEM, "name": "Updated Pipeline", "description": "Updated desc"}
        mock_db.pipelines.get_by_key.side_effect = [
            SAMPLE_PIPELINE_ITEM.copy(),  # initial lookup
            updated_item.copy(),           # after update
        ]
        mock_db.pipelines.update.return_value = {}
        mock_db.pipeline_documents.find_by.return_value = [SAMPLE_PIPELINE_DOC_LINK.copy()]

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"pipeline_id": "pipe-001", "name": "Updated Pipeline", "description": "Updated desc"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["name"] == "Updated Pipeline"
        mock_db.pipelines.update.assert_called_once()
        update_args = mock_db.pipelines.update.call_args
        assert update_args[0][0] == "pipe-001"
        updates = update_args[0][1]
        assert updates["name"] == "Updated Pipeline"
        assert updates["description"] == "Updated desc"
        assert "updated_at" in updates

    def test_update_pipeline_via_id_key(self):
        """put() also accepts 'id' instead of 'pipeline_id'."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.side_effect = [
            SAMPLE_PIPELINE_ITEM.copy(),
            SAMPLE_PIPELINE_ITEM.copy(),
        ]
        mock_db.pipelines.update.return_value = {}
        mock_db.pipeline_documents.find_by.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"id": "pipe-001", "name": "Via ID Key"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert resp.status_code == 200
        mock_db.pipelines.get_by_key.assert_called_with({"user_id": "user-123", "id": "pipe-001"})

    def test_update_pipeline_document_links(self):
        """Updating documentIds replaces old links with new ones."""
        old_link_1 = {"pipeline_id": "pipe-001", "document_id": "doc-old-1"}
        old_link_2 = {"pipeline_id": "pipe-001", "document_id": "doc-old-2"}

        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.side_effect = [
            SAMPLE_PIPELINE_ITEM.copy(),
            SAMPLE_PIPELINE_ITEM.copy(),
        ]
        mock_db.pipelines.update.return_value = {}
        # First call to find_by for old links deletion, second for _get_document_ids at end
        mock_db.pipeline_documents.find_by.side_effect = [
            [old_link_1, old_link_2],           # old links to delete
            [{"document_id": "doc-new-1"}],     # final _get_document_ids
        ]
        mock_db.pipeline_documents.delete_by_key.return_value = {}
        mock_db.pipeline_documents.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"pipeline_id": "pipe-001", "documentIds": ["doc-new-1"]},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert resp.status_code == 200

        # Old links deleted
        assert mock_db.pipeline_documents.delete_by_key.call_count == 2
        mock_db.pipeline_documents.delete_by_key.assert_any_call(
            {"pipeline_id": "pipe-001", "document_id": "doc-old-1"}
        )
        mock_db.pipeline_documents.delete_by_key.assert_any_call(
            {"pipeline_id": "pipe-001", "document_id": "doc-old-2"}
        )

        # New link created
        mock_db.pipeline_documents.create.assert_called_once()

    def test_update_pipeline_empty_document_ids_clears_links(self):
        """Passing an empty document_ids list via snake_case clears all links.

        Note: The manager uses ``data.get("documentIds") or data.get("document_ids")``
        which means an empty list ``[]`` for "documentIds" is falsy and falls through
        to the ``document_ids`` key.  To actually clear links, use the snake_case key.
        """
        old_link = {"pipeline_id": "pipe-001", "document_id": "doc-old-1"}

        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.side_effect = [
            SAMPLE_PIPELINE_ITEM.copy(),
            SAMPLE_PIPELINE_ITEM.copy(),
        ]
        mock_db.pipelines.update.return_value = {}
        mock_db.pipeline_documents.find_by.side_effect = [
            [old_link],  # old links
            [],          # final _get_document_ids
        ]
        mock_db.pipeline_documents.delete_by_key.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"pipeline_id": "pipe-001", "document_ids": []},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        mock_db.pipeline_documents.delete_by_key.assert_called_once()
        mock_db.pipeline_documents.create.assert_not_called()

    def test_update_pipeline_missing_id(self):
        mgr = _build_manager()

        req = make_request(data={"name": "No ID"}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "pipeline id" in resp.error.lower()

    def test_update_pipeline_not_found(self):
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "nonexistent"}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()


# ===========================================================================
# DELETE -- remove pipeline with cascade
# ===========================================================================

class TestDeletePipeline:

    def test_delete_pipeline_success(self):
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.pipeline_documents.find_by.return_value = [
            SAMPLE_PIPELINE_DOC_LINK.copy(),
            SAMPLE_PIPELINE_DOC_LINK_2.copy(),
        ]
        mock_db.pipeline_documents.delete_by_key.return_value = {}
        mock_db.outputs.delete_where.return_value = {}
        mock_db.queries.delete_where.return_value = {}
        mock_db.pipelines.delete_by_key.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert "deleted" in resp.message.lower()

        # Verify cascading deletes
        assert mock_db.pipeline_documents.delete_by_key.call_count == 2
        mock_db.pipeline_documents.delete_by_key.assert_any_call(
            {"pipeline_id": "pipe-001", "document_id": "doc-001"}
        )
        mock_db.pipeline_documents.delete_by_key.assert_any_call(
            {"pipeline_id": "pipe-001", "document_id": "doc-002"}
        )
        mock_db.outputs.delete_where.assert_called_once_with("pipeline_id", "pipe-001")
        mock_db.queries.delete_where.assert_called_once_with("pipeline_id", "pipe-001")
        mock_db.pipelines.delete_by_key.assert_called_once_with(
            {"user_id": "user-123", "id": "pipe-001"}
        )

    def test_delete_pipeline_no_linked_documents(self):
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.pipeline_documents.find_by.return_value = []
        mock_db.outputs.delete_where.return_value = {}
        mock_db.queries.delete_where.return_value = {}
        mock_db.pipelines.delete_by_key.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is True
        assert resp.status_code == 200
        mock_db.pipeline_documents.delete_by_key.assert_not_called()

    def test_delete_pipeline_missing_id(self):
        mgr = _build_manager()

        req = make_request(data={}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "pipeline id" in resp.error.lower()

    def test_delete_pipeline_not_found(self):
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "nonexistent"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()


# ===========================================================================
# run_pipeline -- execute pipeline
# ===========================================================================

class TestRunPipeline:

    def _setup_run_mocks(self, mock_db, pipeline_item=None, doc_links=None,
                         chunks=None, model_data=None):
        """Set up common mock_db returns for run_pipeline tests."""
        mock_db.pipelines.get_by_key.return_value = (
            pipeline_item or SAMPLE_PIPELINE_ITEM.copy()
        )
        mock_db.pipelines.update.return_value = {}
        mock_db.pipeline_documents.find_by.return_value = (
            doc_links if doc_links is not None else [SAMPLE_PIPELINE_DOC_LINK.copy()]
        )
        mock_db.document_chunks.find_by.return_value = (
            chunks if chunks is not None else [SAMPLE_CHUNK.copy(), SAMPLE_CHUNK_2.copy()]
        )
        if model_data is not None:
            mock_db.models.get_by_key.return_value = model_data
        else:
            mock_db.models.get_by_key.return_value = SAMPLE_MODEL_DATA.copy()
        mock_db.outputs.create.return_value = {}

    @patch("utils.encryption.decrypt_value", return_value="decrypted_key")
    @patch("config.model_registry.get_llm_config", return_value={"model": "gpt-4"})
    @patch("services.ai.LangChainServiceManager.LangChainServiceManager")
    def test_run_pipeline_success(self, MockLLMClass, mock_get_config, mock_decrypt):
        mock_db = MagicMock()
        self._setup_run_mocks(mock_db)

        mock_llm_instance = MagicMock()
        mock_llm_instance.run_task.return_value = "Extracted: company=Acme, revenue=1M"
        MockLLMClass.return_value = mock_llm_instance

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert "pipelineId" in resp.data
        assert "outputData" in resp.data

        # Verify status transitions
        calls = mock_db.pipelines.update.call_args_list
        assert calls[0] == call("pipe-001", {"status": "processing"})
        assert calls[-1] == call("pipe-001", {"status": "completed"})

        # Verify LLM was configured and called
        MockLLMClass.assert_called_once()
        mock_llm_instance.configure.assert_called_once()
        mock_llm_instance.run_task.assert_called_once()

        # Verify output was saved
        mock_db.outputs.create.assert_called_once()

    @patch("utils.encryption.decrypt_value", return_value="decrypted_key")
    @patch("config.model_registry.get_llm_config", return_value={"model": "gpt-4"})
    @patch("services.ai.LangChainServiceManager.LangChainServiceManager")
    def test_run_pipeline_uses_prompt_template(self, MockLLMClass, mock_get_config, mock_decrypt):
        mock_db = MagicMock()
        pipeline_with_template = {
            **SAMPLE_PIPELINE_ITEM,
            "prompt_template": "Custom prompt: {context}",
        }
        self._setup_run_mocks(mock_db, pipeline_item=pipeline_with_template)

        mock_llm_instance = MagicMock()
        mock_llm_instance.run_task.return_value = "LLM result"
        MockLLMClass.return_value = mock_llm_instance

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is True
        # Verify prompt was built from the template
        task_arg = mock_llm_instance.run_task.call_args[0][0]
        assert "Custom prompt:" in task_arg["prompt"]
        assert "sample chunk content" in task_arg["prompt"].lower()

    @patch("utils.encryption.decrypt_value", return_value="decrypted_key")
    @patch("config.model_registry.get_llm_config", return_value={"model": "gpt-4"})
    @patch("services.ai.LangChainServiceManager.LangChainServiceManager")
    def test_run_pipeline_falls_back_to_pipeline_type_template(self, MockLLMClass, mock_get_config, mock_decrypt):
        """When no prompt_template is set, use PipelineTypeService to build one."""
        mock_db = MagicMock()
        pipeline_no_template = {
            **SAMPLE_PIPELINE_ITEM,
            "prompt_template": None,
            "pipeline_type": "extraction",
        }
        self._setup_run_mocks(mock_db, pipeline_item=pipeline_no_template)

        mock_llm_instance = MagicMock()
        mock_llm_instance.run_task.return_value = "Result from type template"
        MockLLMClass.return_value = mock_llm_instance

        mgr = _build_manager(mock_db)
        mgr._pipeline_type_service.build_prompt_template.return_value = "Type template: {context}"

        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is True
        mgr._pipeline_type_service.build_prompt_template.assert_called_once_with("extraction")
        task_arg = mock_llm_instance.run_task.call_args[0][0]
        assert "Type template:" in task_arg["prompt"]

    @patch("utils.encryption.decrypt_value", return_value="decrypted_key")
    @patch("config.model_registry.get_llm_config", return_value={"model": "gpt-4"})
    @patch("services.ai.LangChainServiceManager.LangChainServiceManager")
    def test_run_pipeline_uses_default_prompt_when_no_template(self, MockLLMClass, mock_get_config, mock_decrypt):
        """When neither prompt_template nor pipeline_type is set, uses default prompt."""
        mock_db = MagicMock()
        pipeline_no_template = {
            **SAMPLE_PIPELINE_ITEM,
            "prompt_template": None,
            "pipeline_type": None,
        }
        self._setup_run_mocks(mock_db, pipeline_item=pipeline_no_template)

        mock_llm_instance = MagicMock()
        mock_llm_instance.run_task.return_value = "Default result"
        MockLLMClass.return_value = mock_llm_instance

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is True
        task_arg = mock_llm_instance.run_task.call_args[0][0]
        assert "structured summary" in task_arg["prompt"].lower()

    @patch("utils.encryption.decrypt_value", return_value="decrypted_key")
    @patch("config.model_registry.get_llm_config", return_value={"model": "gpt-4"})
    @patch("services.ai.LangChainServiceManager.LangChainServiceManager")
    def test_run_pipeline_falls_back_to_global_model(self, MockLLMClass, mock_get_config, mock_decrypt):
        """When user model not found, falls back to GLOBAL model."""
        mock_db = MagicMock()
        self._setup_run_mocks(mock_db)
        # First call returns None (user model), second returns the global model
        mock_db.models.get_by_key.side_effect = [None, SAMPLE_MODEL_DATA.copy()]

        mock_llm_instance = MagicMock()
        mock_llm_instance.run_task.return_value = "Global model result"
        MockLLMClass.return_value = mock_llm_instance

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is True
        # Verify both lookups happened
        assert mock_db.models.get_by_key.call_count == 2
        mock_db.models.get_by_key.assert_any_call({"user_id": "user-123", "id": "model-001"})
        mock_db.models.get_by_key.assert_any_call({"user_id": "GLOBAL", "id": "model-001"})

    @patch("utils.encryption.decrypt_value", return_value=None)
    @patch("config.model_registry.get_llm_config", return_value={"model": "gpt-4"})
    @patch("services.ai.LangChainServiceManager.LangChainServiceManager")
    def test_run_pipeline_no_api_key_when_decrypt_returns_none(self, MockLLMClass, mock_get_config, mock_decrypt):
        """When decrypt_value returns None, api_key is not set in config."""
        mock_db = MagicMock()
        self._setup_run_mocks(mock_db)

        mock_llm_instance = MagicMock()
        mock_llm_instance.run_task.return_value = "Result"
        MockLLMClass.return_value = mock_llm_instance

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is True
        # get_llm_config should be called with config without api_key
        config_arg = mock_get_config.call_args[0][1]
        assert "api_key" not in config_arg

    def test_run_pipeline_missing_pipeline_id(self):
        mgr = _build_manager()

        req = make_request(data={}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "pipeline id" in resp.error.lower()

    def test_run_pipeline_not_found(self):
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "nonexistent"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()

    def test_run_pipeline_model_not_found(self):
        """When neither user nor global model is found, status set to failed."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.pipelines.update.return_value = {}
        mock_db.pipeline_documents.find_by.return_value = [SAMPLE_PIPELINE_DOC_LINK.copy()]
        mock_db.document_chunks.find_by.return_value = [SAMPLE_CHUNK.copy()]
        mock_db.models.get_by_key.return_value = None  # neither user nor global

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "model not found" in resp.error.lower()
        # Verify status was set to failed
        mock_db.pipelines.update.assert_any_call("pipe-001", {"status": "failed"})

    @patch("utils.encryption.decrypt_value", return_value="key")
    @patch("config.model_registry.get_llm_config", return_value={"model": "gpt-4"})
    @patch("services.ai.LangChainServiceManager.LangChainServiceManager")
    def test_run_pipeline_error_sets_status_to_failed(self, MockLLMClass, mock_get_config, mock_decrypt):
        """When LLM execution raises, pipeline status is set to failed."""
        mock_db = MagicMock()
        self._setup_run_mocks(mock_db)

        mock_llm_instance = MagicMock()
        mock_llm_instance.run_task.side_effect = Exception("LLM inference failed")
        MockLLMClass.return_value = mock_llm_instance

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to run pipeline" in resp.error.lower()
        # Verify status was set to failed in the error handler
        mock_db.pipelines.update.assert_any_call("pipe-001", {"status": "failed"})

    @patch("utils.encryption.decrypt_value", return_value="key")
    @patch("config.model_registry.get_llm_config", return_value={"model": "gpt-4"})
    @patch("services.ai.LangChainServiceManager.LangChainServiceManager")
    def test_run_pipeline_with_no_document_chunks(self, MockLLMClass, mock_get_config, mock_decrypt):
        """Pipeline runs with empty context when no chunks are found."""
        mock_db = MagicMock()
        self._setup_run_mocks(mock_db, doc_links=[], chunks=[])

        mock_llm_instance = MagicMock()
        mock_llm_instance.run_task.return_value = "Empty context result"
        MockLLMClass.return_value = mock_llm_instance

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is True
        assert resp.status_code == 200

    @patch("utils.encryption.decrypt_value", return_value="key")
    @patch("config.model_registry.get_llm_config", return_value={"model": "gpt-4"})
    @patch("services.ai.LangChainServiceManager.LangChainServiceManager")
    def test_run_pipeline_model_without_encrypted_key(self, MockLLMClass, mock_get_config, mock_decrypt):
        """Model data with no encrypted_api_key skips decryption."""
        mock_db = MagicMock()
        model_no_key = {**SAMPLE_MODEL_DATA, "encrypted_api_key": None}
        del model_no_key["encrypted_api_key"]
        self._setup_run_mocks(mock_db, model_data=model_no_key)

        mock_llm_instance = MagicMock()
        mock_llm_instance.run_task.return_value = "No key result"
        MockLLMClass.return_value = mock_llm_instance

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is True
        mock_decrypt.assert_not_called()

    @patch("utils.encryption.decrypt_value", return_value="key")
    @patch("config.model_registry.get_llm_config", return_value={"model": "gpt-4"})
    @patch("services.ai.LangChainServiceManager.LangChainServiceManager")
    def test_run_pipeline_model_without_config(self, MockLLMClass, mock_get_config, mock_decrypt):
        """Model data with no config field uses empty dict."""
        mock_db = MagicMock()
        model_no_config = {**SAMPLE_MODEL_DATA, "config": None}
        self._setup_run_mocks(mock_db, model_data=model_no_config)

        mock_llm_instance = MagicMock()
        mock_llm_instance.run_task.return_value = "Result"
        MockLLMClass.return_value = mock_llm_instance

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.run_pipeline(req)

        assert resp.success is True
        config_arg = mock_get_config.call_args[0][1]
        assert "api_key" in config_arg


# ===========================================================================
# GET -- error handling
# ===========================================================================

class TestGetPipelineErrors:

    def test_get_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.pipelines.find_by_user.side_effect = Exception("DynamoDB connection timeout")

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to retrieve" in resp.error.lower()

    def test_get_single_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.side_effect = Exception("DynamoDB error")

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to retrieve" in resp.error.lower()


# ===========================================================================
# POST -- error handling
# ===========================================================================

class TestPostPipelineErrors:

    def test_post_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.pipelines.create.side_effect = Exception("DynamoDB write error")

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "Failing Pipeline",
                "modelId": "model-001",
                "embeddingModelId": "emb-model-001",
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to create" in resp.error.lower()


# ===========================================================================
# PUT -- error handling
# ===========================================================================

class TestPutPipelineErrors:

    def test_put_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.side_effect = Exception("DynamoDB error")

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to update" in resp.error.lower()


# ===========================================================================
# DELETE -- error handling
# ===========================================================================

class TestDeletePipelineErrors:

    def test_delete_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.side_effect = Exception("DynamoDB error")

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to delete" in resp.error.lower()
