"""Unit tests for QueryResourceManager."""
import pytest
from unittest.mock import patch, MagicMock, ANY

from tests.conftest import make_request


# ---------------------------------------------------------------------------
# Patch targets (patched at the module where they are imported)
# ---------------------------------------------------------------------------

_PATCH_LANGCHAIN = "managers.queries.QueryResourceManager.LangChainServiceManager"
_PATCH_EMBEDDINGS = "managers.queries.QueryResourceManager.EmbeddingsService"
_PATCH_GET_LLM_CONFIG = "managers.queries.QueryResourceManager.get_llm_config"
_PATCH_GET_EMBEDDING_CONFIG = "managers.queries.QueryResourceManager.get_embedding_config"
_PATCH_DECRYPT = "managers.queries.QueryResourceManager.decrypt_value"


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_QUERY_ITEM = {
    "user_id": "user-123",
    "id": "query-001",
    "pipeline_id": "pipe-001",
    "question": "What is the main topic?",
    "answer": "The main topic is AI document processing.",
    "context": "Sample context from documents...",
    "created_at": "2024-06-01T00:00:00",
}

SAMPLE_QUERY_ITEM_2 = {
    **SAMPLE_QUERY_ITEM,
    "id": "query-002",
    "question": "What are the key findings?",
    "answer": "The key findings include improved accuracy.",
}

SAMPLE_PIPELINE_ITEM = {
    "user_id": "user-123",
    "id": "pipe-001",
    "model_id": "model-001",
    "embedding_model_id": "emb-model-001",
    "prompt_template": None,
}

SAMPLE_MODEL_ITEM = {
    "user_id": "user-123",
    "id": "model-001",
    "model_id": "gpt-4",
    "config": '{"temperature": 0.7}',
    "encrypted_api_key": None,
}

SAMPLE_EMBEDDING_MODEL_ITEM = {
    "user_id": "user-123",
    "id": "emb-model-001",
    "model_id": "text-embedding-ada-002",
    "config": '{"dimensions": 1536}',
    "encrypted_api_key": None,
}

SAMPLE_DOC_LINK = {"pipeline_id": "pipe-001", "document_id": "doc-001"}
SAMPLE_DOC_LINK_2 = {"pipeline_id": "pipe-001", "document_id": "doc-002"}

SAMPLE_CHUNK = {
    "document_id": "doc-001",
    "chunk_id": "chunk-001",
    "content": "This document discusses AI document processing.",
}

SAMPLE_CHUNK_2 = {
    "document_id": "doc-001",
    "chunk_id": "chunk-002",
    "content": "Machine learning techniques are applied.",
}


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _build_manager(mock_db=None, mock_vector_db=None):
    """Instantiate QueryResourceManager with mock services."""
    from managers.queries.QueryResourceManager import QueryResourceManager

    if mock_db is None:
        mock_db = MagicMock()
    service_managers = {"db": mock_db, "vector_db": mock_vector_db}
    return QueryResourceManager(service_managers=service_managers)


# ===========================================================================
# GET -- list queries
# ===========================================================================

class TestGetQueries:

    def test_get_all_queries_by_user(self):
        """When no pipeline_id is provided, returns all queries for the user."""
        mock_db = MagicMock()
        mock_db.queries.find_by_user.return_value = [
            SAMPLE_QUERY_ITEM.copy(),
            SAMPLE_QUERY_ITEM_2.copy(),
        ]

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) == 2
        assert resp.data[0]["id"] == "query-001"
        assert resp.data[1]["id"] == "query-002"
        mock_db.queries.find_by_user.assert_called_once_with("user-123")

    def test_get_queries_by_pipeline_id(self):
        """When pipeline_id is provided, returns queries filtered by pipeline."""
        mock_db = MagicMock()
        mock_db.queries.find_by_pipeline.return_value = [SAMPLE_QUERY_ITEM.copy()]

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["pipelineId"] == "pipe-001"
        mock_db.queries.find_by_pipeline.assert_called_once_with("pipe-001")

    def test_get_queries_empty_results(self):
        """Returns empty list when no queries exist."""
        mock_db = MagicMock()
        mock_db.queries.find_by_user.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data == []

    def test_get_queries_empty_by_pipeline(self):
        """Returns empty list when pipeline has no queries."""
        mock_db = MagicMock()
        mock_db.queries.find_by_pipeline.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-no-queries"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data == []

    def test_get_queries_returns_camel_case_keys(self):
        """Verifies to_api_dict produces camelCase keys for the frontend."""
        mock_db = MagicMock()
        mock_db.queries.find_by_user.return_value = [SAMPLE_QUERY_ITEM.copy()]

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        item = resp.data[0]
        expected_keys = {"id", "userId", "pipelineId", "question", "answer", "context", "queryMetadata", "createdAt"}
        assert expected_keys.issubset(set(item.keys()))

    def test_get_queries_handles_db_exception(self):
        """Database errors are caught and return 500."""
        mock_db = MagicMock()
        mock_db.queries.find_by_user.side_effect = Exception("DynamoDB connection timeout")

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to retrieve" in resp.error.lower()

    def test_get_queries_by_pipeline_handles_db_exception(self):
        """Database error on pipeline query returns 500."""
        mock_db = MagicMock()
        mock_db.queries.find_by_pipeline.side_effect = Exception("DynamoDB throttle")

        mgr = _build_manager(mock_db)
        req = make_request(data={"pipeline_id": "pipe-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to retrieve" in resp.error.lower()

    def test_get_queries_with_none_data(self):
        """When data is None, defaults to empty dict and fetches by user."""
        mock_db = MagicMock()
        mock_db.queries.find_by_user.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(data=None, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.data == []
        mock_db.queries.find_by_user.assert_called_once_with("user-123")


# ===========================================================================
# POST -- RAG Q&A
# ===========================================================================

class TestPostQuery:

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4", "temperature": 0.7})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_success_with_vector_db(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """Full RAG flow with vector_db: embed -> search -> LLM -> save."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.models.get_by_key.side_effect = [
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),  # _resolve_model for embedding (user scope)
            SAMPLE_MODEL_ITEM.copy(),             # _resolve_model for chat (user scope)
        ]
        mock_db.pipeline_documents.find_by.return_value = [SAMPLE_DOC_LINK.copy()]
        mock_db.document_chunks.get_by_key.return_value = SAMPLE_CHUNK.copy()
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1, 0.2, 0.3]
        MockEmbeddings.return_value = mock_emb_instance

        mock_vector_db = MagicMock()
        mock_vector_db.query.return_value = [{"id": "chunk-001", "score": 0.95}]

        mock_llm_instance = MagicMock()
        mock_llm_instance.create_chat_completion.return_value = "The main topic is AI document processing."
        MockLangChain.return_value = mock_llm_instance

        mgr = _build_manager(mock_db, mock_vector_db=mock_vector_db)
        req = make_request(
            data={"pipeline_id": "pipe-001", "question": "What is the main topic?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["question"] == "What is the main topic?"
        assert resp.data["answer"] == "The main topic is AI document processing."
        assert resp.data["pipelineId"] == "pipe-001"
        assert resp.data["userId"] == "user-123"

        # Verify embedding service was configured and called
        MockEmbeddings.assert_called_once()
        mock_emb_instance.configure.assert_called_once()
        mock_emb_instance.embed_query.assert_called_once_with("What is the main topic?")

        # Verify vector_db was queried
        mock_vector_db.query.assert_called_once_with([0.1, 0.2, 0.3], top_k=3, namespace="doc-001")

        # Verify LLM was configured and called
        MockLangChain.assert_called_once()
        mock_llm_instance.configure.assert_called_once()
        mock_llm_instance.create_chat_completion.assert_called_once()

        # Verify query was saved
        mock_db.queries.create.assert_called_once()

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4"})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_fallback_without_vector_db(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """When vector_db is None, falls back to direct chunk retrieval."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.models.get_by_key.side_effect = [
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
            SAMPLE_MODEL_ITEM.copy(),
        ]
        mock_db.pipeline_documents.find_by.return_value = [SAMPLE_DOC_LINK.copy()]
        mock_db.document_chunks.find_by.return_value = [
            {"content": "Chunk 1 content"},
            {"content": "Chunk 2 content"},
        ]
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1, 0.2]
        MockEmbeddings.return_value = mock_emb_instance

        mock_llm_instance = MagicMock()
        mock_llm_instance.create_chat_completion.return_value = "Fallback answer."
        MockLangChain.return_value = mock_llm_instance

        mgr = _build_manager(mock_db, mock_vector_db=None)
        req = make_request(
            data={"pipeline_id": "pipe-001", "question": "Summarize the document."},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["answer"] == "Fallback answer."

        # Verify fallback: direct chunk retrieval used instead of vector_db
        mock_db.document_chunks.find_by.assert_called_once_with("document_id", "doc-001")

    def test_post_query_missing_pipeline_id(self):
        """Returns 400 when pipeline_id is not provided."""
        mgr = _build_manager()
        req = make_request(
            data={"question": "What is this about?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "pipeline_id is required" in resp.error

    def test_post_query_missing_question(self):
        """Returns 400 when question is not provided."""
        mgr = _build_manager()
        req = make_request(
            data={"pipeline_id": "pipe-001"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "question is required" in resp.error

    def test_post_query_missing_both_fields(self):
        """Returns 400 when both pipeline_id and question are missing."""
        mgr = _build_manager()
        req = make_request(data={}, user_id="user-123")
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400

    def test_post_query_pipeline_not_found(self):
        """Returns 404 when the pipeline does not exist."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"pipeline_id": "nonexistent", "question": "What?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "pipeline not found" in resp.error.lower()
        mock_db.pipelines.get_by_key.assert_called_once_with({"user_id": "user-123", "id": "nonexistent"})

    def test_post_query_embedding_model_not_found(self):
        """Returns 404 when the embedding model cannot be resolved."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        # _resolve_model: not found under user_id, not found under GLOBAL
        mock_db.models.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"pipeline_id": "pipe-001", "question": "What?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "embedding model not found" in resp.error.lower()

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4"})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_chat_model_not_found(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """Returns 404 when the chat model cannot be resolved."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        # First two calls: _resolve_model for embedding (user -> found)
        # Next two calls: _resolve_model for chat (user -> None, GLOBAL -> None)
        mock_db.models.get_by_key.side_effect = [
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),  # embedding model found (user scope)
            None,                                  # chat model not found (user scope)
            None,                                  # chat model not found (GLOBAL scope)
        ]
        mock_db.pipeline_documents.find_by.return_value = []
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1]
        MockEmbeddings.return_value = mock_emb_instance

        mgr = _build_manager(mock_db, mock_vector_db=None)
        req = make_request(
            data={"pipeline_id": "pipe-001", "question": "What?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "chat model not found" in resp.error.lower()

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4"})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_with_conversation_history(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """Conversation history is included in messages sent to the LLM."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.models.get_by_key.side_effect = [
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
            SAMPLE_MODEL_ITEM.copy(),
        ]
        mock_db.pipeline_documents.find_by.return_value = []
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1]
        MockEmbeddings.return_value = mock_emb_instance

        mock_llm_instance = MagicMock()
        mock_llm_instance.create_chat_completion.return_value = "Follow-up answer."
        MockLangChain.return_value = mock_llm_instance

        conversation = [
            {"role": "user", "content": "What is the topic?"},
            {"role": "assistant", "content": "The topic is AI."},
        ]

        mgr = _build_manager(mock_db, mock_vector_db=None)
        req = make_request(
            data={
                "pipeline_id": "pipe-001",
                "question": "Can you elaborate?",
                "conversation_history": conversation,
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.data["answer"] == "Follow-up answer."

        # Verify messages include system + history + user question
        call_args = mock_llm_instance.create_chat_completion.call_args[0][0]
        assert call_args[0]["role"] == "system"
        assert call_args[1]["role"] == "user"
        assert call_args[1]["content"] == "What is the topic?"
        assert call_args[2]["role"] == "assistant"
        assert call_args[2]["content"] == "The topic is AI."
        assert call_args[3]["role"] == "user"
        assert "Can you elaborate?" in call_args[3]["content"]

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4"})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_conversation_history_limited_to_10(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """Only the last 10 conversation history entries are included."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.models.get_by_key.side_effect = [
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
            SAMPLE_MODEL_ITEM.copy(),
        ]
        mock_db.pipeline_documents.find_by.return_value = []
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1]
        MockEmbeddings.return_value = mock_emb_instance

        mock_llm_instance = MagicMock()
        mock_llm_instance.create_chat_completion.return_value = "Answer."
        MockLangChain.return_value = mock_llm_instance

        # Create 15 history entries; only last 10 should be included
        conversation = [{"role": "user", "content": f"Message {i}"} for i in range(15)]

        mgr = _build_manager(mock_db, mock_vector_db=None)
        req = make_request(
            data={
                "pipeline_id": "pipe-001",
                "question": "Latest question?",
                "conversation_history": conversation,
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        # messages = system (1) + history (10) + user prompt (1) = 12
        call_args = mock_llm_instance.create_chat_completion.call_args[0][0]
        assert len(call_args) == 12
        # First history message should be "Message 5" (index 5 of 0-14 -> last 10 = 5-14)
        assert call_args[1]["content"] == "Message 5"

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4"})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_with_custom_prompt_template(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """When pipeline has a custom prompt_template, it is used instead of the default."""
        pipeline_with_template = {
            **SAMPLE_PIPELINE_ITEM,
            "prompt_template": "Custom template. Context: {context}. Question: {question}",
        }
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = pipeline_with_template
        mock_db.models.get_by_key.side_effect = [
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
            SAMPLE_MODEL_ITEM.copy(),
        ]
        mock_db.pipeline_documents.find_by.return_value = []
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1]
        MockEmbeddings.return_value = mock_emb_instance

        mock_llm_instance = MagicMock()
        mock_llm_instance.create_chat_completion.return_value = "Custom answer."
        MockLangChain.return_value = mock_llm_instance

        mgr = _build_manager(mock_db, mock_vector_db=None)
        req = make_request(
            data={"pipeline_id": "pipe-001", "question": "Custom question?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        # Verify the custom template was used in the prompt
        call_args = mock_llm_instance.create_chat_completion.call_args[0][0]
        user_message = call_args[-1]["content"]
        assert user_message.startswith("Custom template.")
        assert "Custom question?" in user_message

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4"})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_multiple_documents_with_vector_db(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """Vector search is performed across multiple documents linked to the pipeline."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.models.get_by_key.side_effect = [
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
            SAMPLE_MODEL_ITEM.copy(),
        ]
        mock_db.pipeline_documents.find_by.return_value = [
            SAMPLE_DOC_LINK.copy(),
            SAMPLE_DOC_LINK_2.copy(),
        ]
        mock_db.document_chunks.get_by_key.side_effect = [
            SAMPLE_CHUNK.copy(),
            SAMPLE_CHUNK_2.copy(),
        ]
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1, 0.2]
        MockEmbeddings.return_value = mock_emb_instance

        mock_vector_db = MagicMock()
        mock_vector_db.query.side_effect = [
            [{"id": "chunk-001", "score": 0.95}],  # doc-001 results
            [{"id": "chunk-002", "score": 0.88}],  # doc-002 results
        ]

        mock_llm_instance = MagicMock()
        mock_llm_instance.create_chat_completion.return_value = "Multi-doc answer."
        MockLangChain.return_value = mock_llm_instance

        mgr = _build_manager(mock_db, mock_vector_db=mock_vector_db)
        req = make_request(
            data={"pipeline_id": "pipe-001", "question": "Cross-document question?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.data["answer"] == "Multi-doc answer."
        # Verify vector_db was queried for each document
        assert mock_vector_db.query.call_count == 2
        mock_vector_db.query.assert_any_call([0.1, 0.2], top_k=3, namespace="doc-001")
        mock_vector_db.query.assert_any_call([0.1, 0.2], top_k=3, namespace="doc-002")

    @patch(_PATCH_DECRYPT, return_value="decrypted-api-key-123")
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4", "api_key": "decrypted-api-key-123"})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002", "api_key": "decrypted-api-key-123"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_with_encrypted_api_key(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """When model has an encrypted_api_key, it is decrypted and included in config."""
        emb_model_with_key = {**SAMPLE_EMBEDDING_MODEL_ITEM, "encrypted_api_key": "enc-key-abc"}
        chat_model_with_key = {**SAMPLE_MODEL_ITEM, "encrypted_api_key": "enc-key-xyz"}

        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.models.get_by_key.side_effect = [
            emb_model_with_key,
            chat_model_with_key,
        ]
        mock_db.pipeline_documents.find_by.return_value = []
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1]
        MockEmbeddings.return_value = mock_emb_instance

        mock_llm_instance = MagicMock()
        mock_llm_instance.create_chat_completion.return_value = "Answer with key."
        MockLangChain.return_value = mock_llm_instance

        mgr = _build_manager(mock_db, mock_vector_db=None)
        req = make_request(
            data={"pipeline_id": "pipe-001", "question": "Test with key?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        # decrypt_value should have been called for both models
        assert mock_decrypt.call_count == 2
        mock_decrypt.assert_any_call("enc-key-abc")
        mock_decrypt.assert_any_call("enc-key-xyz")

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4"})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_model_resolved_from_global(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """When model not found under user_id, falls back to GLOBAL."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        # _resolve_model for embedding: user -> None, GLOBAL -> found
        # _resolve_model for chat: user -> None, GLOBAL -> found
        mock_db.models.get_by_key.side_effect = [
            None,                                       # emb not found (user)
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),         # emb found (GLOBAL)
            None,                                       # chat not found (user)
            SAMPLE_MODEL_ITEM.copy(),                   # chat found (GLOBAL)
        ]
        mock_db.pipeline_documents.find_by.return_value = []
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1]
        MockEmbeddings.return_value = mock_emb_instance

        mock_llm_instance = MagicMock()
        mock_llm_instance.create_chat_completion.return_value = "Global model answer."
        MockLangChain.return_value = mock_llm_instance

        mgr = _build_manager(mock_db, mock_vector_db=None)
        req = make_request(
            data={"pipeline_id": "pipe-001", "question": "Global model?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.data["answer"] == "Global model answer."
        # 4 get_by_key calls: user + GLOBAL for each model
        assert mock_db.models.get_by_key.call_count == 4
        mock_db.models.get_by_key.assert_any_call({"user_id": "GLOBAL", "id": "emb-model-001"})
        mock_db.models.get_by_key.assert_any_call({"user_id": "GLOBAL", "id": "model-001"})

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4"})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_context_truncated_to_5000(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """Context saved in the query item is truncated to 5000 characters."""
        long_content = "A" * 6000

        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.models.get_by_key.side_effect = [
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
            SAMPLE_MODEL_ITEM.copy(),
        ]
        mock_db.pipeline_documents.find_by.return_value = [SAMPLE_DOC_LINK.copy()]
        mock_db.document_chunks.find_by.return_value = [{"content": long_content}]
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1]
        MockEmbeddings.return_value = mock_emb_instance

        mock_llm_instance = MagicMock()
        mock_llm_instance.create_chat_completion.return_value = "Answer."
        MockLangChain.return_value = mock_llm_instance

        mgr = _build_manager(mock_db, mock_vector_db=None)
        req = make_request(
            data={"pipeline_id": "pipe-001", "question": "Long context?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        # Verify that the context saved is at most 5000 chars
        create_call_args = mock_db.queries.create.call_args[0][0]
        assert len(create_call_args.get("context", "")) <= 5000

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_handles_llm_exception(
        self, MockEmbeddings, mock_get_emb_cfg, mock_decrypt
    ):
        """Exceptions during LLM call are caught and return 500."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.models.get_by_key.side_effect = [
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
            SAMPLE_MODEL_ITEM.copy(),
        ]
        mock_db.pipeline_documents.find_by.return_value = []

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1]
        MockEmbeddings.return_value = mock_emb_instance

        with patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4"}):
            with patch(_PATCH_LANGCHAIN) as MockLangChain:
                mock_llm_instance = MagicMock()
                mock_llm_instance.create_chat_completion.side_effect = Exception("OpenAI rate limit")
                MockLangChain.return_value = mock_llm_instance

                mgr = _build_manager(mock_db, mock_vector_db=None)
                req = make_request(
                    data={"pipeline_id": "pipe-001", "question": "Will fail?"},
                    user_id="user-123",
                )
                resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to process query" in resp.error.lower()

    def test_post_query_with_none_data(self):
        """When data is None, both validations fail with pipeline_id error first."""
        mgr = _build_manager()
        req = make_request(data=None, user_id="user-123")
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "pipeline_id is required" in resp.error

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4"})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_vector_db_chunk_not_found(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """When vector_db returns matches but chunks are not in DB, they are skipped."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.models.get_by_key.side_effect = [
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
            SAMPLE_MODEL_ITEM.copy(),
        ]
        mock_db.pipeline_documents.find_by.return_value = [SAMPLE_DOC_LINK.copy()]
        # Vector DB returns a match, but the chunk is not in the database
        mock_db.document_chunks.get_by_key.return_value = None
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1]
        MockEmbeddings.return_value = mock_emb_instance

        mock_vector_db = MagicMock()
        mock_vector_db.query.return_value = [{"id": "missing-chunk", "score": 0.9}]

        mock_llm_instance = MagicMock()
        mock_llm_instance.create_chat_completion.return_value = "No context answer."
        MockLangChain.return_value = mock_llm_instance

        mgr = _build_manager(mock_db, mock_vector_db=mock_vector_db)
        req = make_request(
            data={"pipeline_id": "pipe-001", "question": "Missing chunks?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.data["answer"] == "No context answer."

    @patch(_PATCH_DECRYPT, return_value=None)
    @patch(_PATCH_GET_LLM_CONFIG, return_value={"model": "gpt-4"})
    @patch(_PATCH_GET_EMBEDDING_CONFIG, return_value={"model": "text-embedding-ada-002"})
    @patch(_PATCH_LANGCHAIN)
    @patch(_PATCH_EMBEDDINGS)
    def test_post_query_no_documents_linked(
        self, MockEmbeddings, MockLangChain, mock_get_emb_cfg, mock_get_llm_cfg, mock_decrypt
    ):
        """Pipeline with no linked documents still works (empty context)."""
        mock_db = MagicMock()
        mock_db.pipelines.get_by_key.return_value = SAMPLE_PIPELINE_ITEM.copy()
        mock_db.models.get_by_key.side_effect = [
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
            SAMPLE_MODEL_ITEM.copy(),
        ]
        mock_db.pipeline_documents.find_by.return_value = []
        mock_db.queries.create.return_value = {}

        mock_emb_instance = MagicMock()
        mock_emb_instance.embed_query.return_value = [0.1]
        MockEmbeddings.return_value = mock_emb_instance

        mock_llm_instance = MagicMock()
        mock_llm_instance.create_chat_completion.return_value = "No docs answer."
        MockLangChain.return_value = mock_llm_instance

        mgr = _build_manager(mock_db, mock_vector_db=MagicMock())
        req = make_request(
            data={"pipeline_id": "pipe-001", "question": "No docs?"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.data["answer"] == "No docs answer."


# ===========================================================================
# PUT -- method not allowed
# ===========================================================================

class TestPutQuery:

    def test_put_returns_method_not_allowed(self):
        """PUT always returns 405."""
        mgr = _build_manager()
        req = make_request(data={"query_id": "query-001"}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 405
        assert "method not allowed" in resp.error.lower()

    def test_put_returns_405_with_empty_data(self):
        """PUT returns 405 regardless of payload."""
        mgr = _build_manager()
        req = make_request(data={}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 405


# ===========================================================================
# DELETE -- remove query
# ===========================================================================

class TestDeleteQuery:

    def test_delete_query_success(self):
        mock_db = MagicMock()
        mock_db.queries.delete_by_key.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={"query_id": "query-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert "deleted" in resp.message.lower()
        mock_db.queries.delete_by_key.assert_called_once_with({"user_id": "user-123", "id": "query-001"})

    def test_delete_query_missing_query_id(self):
        """Returns 400 when query_id is not provided."""
        mgr = _build_manager()
        req = make_request(data={}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "query id is required" in resp.error.lower()

    def test_delete_query_with_none_data(self):
        """Returns 400 when data is None."""
        mgr = _build_manager()
        req = make_request(data=None, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "query id is required" in resp.error.lower()

    def test_delete_query_handles_db_exception(self):
        """Database errors during delete are caught and return 500."""
        mock_db = MagicMock()
        mock_db.queries.delete_by_key.side_effect = Exception("DynamoDB throttle")

        mgr = _build_manager(mock_db)
        req = make_request(data={"query_id": "query-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to delete" in resp.error.lower()
