"""Tests for DynamoDB item schemas (database/schemas/).

Covers DocumentItem, DocumentChunkItem, ModelItem, PipelineItem,
OutputItem, and QueryItem.  Each schema is tested for:
  1. Construction with all fields
  2. to_item()   -- snake_case DynamoDB dict, None values stripped
  3. to_api_dict()  -- camelCase API dict
  4. from_item()  -- round-trip reconstruction
  5. from_item() with missing optional fields
"""
import json
import pytest

from database.schemas.document import DocumentItem
from database.schemas.document_chunk import DocumentChunkItem
from database.schemas.model import ModelItem
from database.schemas.pipeline import PipelineItem
from database.schemas.output import OutputItem
from database.schemas.query import QueryItem


# ====================================================================
# DocumentItem
# ====================================================================

class TestDocumentItem:
    """Tests for database.schemas.document.DocumentItem."""

    @pytest.fixture
    def full_doc(self) -> DocumentItem:
        return DocumentItem(
            user_id="user-1",
            id="doc-1",
            embedding_model_id="emb-1",
            filename="stored_abc.pdf",
            original_filename="report.pdf",
            file_path="s3://bucket/stored_abc.pdf",
            file_size=2048,
            mime_type="application/pdf",
            status="ready",
            extracted_text="Lorem ipsum",
            doc_metadata='{"pages": 5}',
            chunk_count=10,
            created_at="2024-06-01T00:00:00",
            updated_at="2024-06-02T00:00:00",
        )

    def test_construction(self, full_doc: DocumentItem):
        assert full_doc.user_id == "user-1"
        assert full_doc.id == "doc-1"
        assert full_doc.embedding_model_id == "emb-1"
        assert full_doc.filename == "stored_abc.pdf"
        assert full_doc.original_filename == "report.pdf"
        assert full_doc.file_path == "s3://bucket/stored_abc.pdf"
        assert full_doc.file_size == 2048
        assert full_doc.mime_type == "application/pdf"
        assert full_doc.status == "ready"
        assert full_doc.extracted_text == "Lorem ipsum"
        assert full_doc.doc_metadata == '{"pages": 5}'
        assert full_doc.chunk_count == 10
        assert full_doc.created_at == "2024-06-01T00:00:00"
        assert full_doc.updated_at == "2024-06-02T00:00:00"

    def test_default_values(self):
        doc = DocumentItem()
        assert doc.user_id == ""
        assert doc.id  # UUID auto-generated
        assert doc.status == "uploaded"
        assert doc.file_size == 0
        assert doc.chunk_count == 0
        assert doc.embedding_model_id is None
        assert doc.mime_type is None
        assert doc.extracted_text is None
        assert doc.doc_metadata is None

    def test_to_item(self, full_doc: DocumentItem):
        item = full_doc.to_item()
        assert item["user_id"] == "user-1"
        assert item["id"] == "doc-1"
        assert item["embedding_model_id"] == "emb-1"
        assert item["filename"] == "stored_abc.pdf"
        assert item["original_filename"] == "report.pdf"
        assert item["file_path"] == "s3://bucket/stored_abc.pdf"
        assert item["file_size"] == 2048
        assert item["mime_type"] == "application/pdf"
        assert item["status"] == "ready"
        assert item["extracted_text"] == "Lorem ipsum"
        assert item["doc_metadata"] == '{"pages": 5}'
        assert item["chunk_count"] == 10
        assert item["created_at"] == "2024-06-01T00:00:00"
        assert item["updated_at"] == "2024-06-02T00:00:00"

    def test_to_item_strips_none_values(self):
        doc = DocumentItem(user_id="u1", id="d1")
        item = doc.to_item()
        assert "embedding_model_id" not in item
        assert "mime_type" not in item
        assert "extracted_text" not in item
        assert "doc_metadata" not in item
        # Non-None defaults should still be present
        assert item["status"] == "uploaded"
        assert item["file_size"] == 0

    def test_to_api_dict(self, full_doc: DocumentItem):
        api = full_doc.to_api_dict()
        assert api["id"] == "doc-1"
        assert api["userId"] == "user-1"
        assert api["embeddingModelId"] == "emb-1"
        assert api["fileName"] == "report.pdf"  # prefers original_filename
        assert api["fileType"] == "application/pdf"
        assert api["fileSize"] == 2048
        assert api["status"] == "ready"
        assert api["chunkCount"] == 10
        assert api["uploadedAt"] == "2024-06-01T00:00:00"
        assert api["updatedAt"] == "2024-06-02T00:00:00"

    def test_to_api_dict_falls_back_to_filename(self):
        doc = DocumentItem(filename="stored.pdf", original_filename="")
        api = doc.to_api_dict()
        assert api["fileName"] == "stored.pdf"

    def test_to_api_dict_defaults_filetype_to_unknown(self):
        doc = DocumentItem()
        api = doc.to_api_dict()
        assert api["fileType"] == "Unknown"

    def test_from_item_roundtrip(self, full_doc: DocumentItem):
        item = full_doc.to_item()
        restored = DocumentItem.from_item(item)
        assert restored.user_id == full_doc.user_id
        assert restored.id == full_doc.id
        assert restored.embedding_model_id == full_doc.embedding_model_id
        assert restored.filename == full_doc.filename
        assert restored.original_filename == full_doc.original_filename
        assert restored.file_path == full_doc.file_path
        assert restored.file_size == full_doc.file_size
        assert restored.mime_type == full_doc.mime_type
        assert restored.status == full_doc.status
        assert restored.extracted_text == full_doc.extracted_text
        assert restored.doc_metadata == full_doc.doc_metadata
        assert restored.chunk_count == full_doc.chunk_count
        assert restored.created_at == full_doc.created_at
        assert restored.updated_at == full_doc.updated_at

    def test_from_item_missing_optional_fields(self):
        minimal = {"user_id": "u1", "id": "d1", "filename": "f.pdf"}
        doc = DocumentItem.from_item(minimal)
        assert doc.user_id == "u1"
        assert doc.id == "d1"
        assert doc.filename == "f.pdf"
        assert doc.embedding_model_id is None
        assert doc.mime_type is None
        assert doc.extracted_text is None
        assert doc.doc_metadata is None
        assert doc.status == "uploaded"

    def test_from_item_ignores_extra_keys(self):
        item = {"user_id": "u1", "id": "d1", "unknown_field": "ignored"}
        doc = DocumentItem.from_item(item)
        assert doc.user_id == "u1"
        assert not hasattr(doc, "unknown_field")


# ====================================================================
# DocumentChunkItem
# ====================================================================

class TestDocumentChunkItem:
    """Tests for database.schemas.document_chunk.DocumentChunkItem."""

    @pytest.fixture
    def full_chunk(self) -> DocumentChunkItem:
        return DocumentChunkItem(
            document_id="doc-1",
            chunk_id="chunk-1",
            chunk_index=3,
            content="Some text content from the document.",
            chunk_metadata='{"page": 2}',
            vector_id="vec-abc",
            token_count=42,
            created_at="2024-06-01T12:00:00",
        )

    def test_construction(self, full_chunk: DocumentChunkItem):
        assert full_chunk.document_id == "doc-1"
        assert full_chunk.chunk_id == "chunk-1"
        assert full_chunk.chunk_index == 3
        assert full_chunk.content == "Some text content from the document."
        assert full_chunk.chunk_metadata == '{"page": 2}'
        assert full_chunk.vector_id == "vec-abc"
        assert full_chunk.token_count == 42
        assert full_chunk.created_at == "2024-06-01T12:00:00"

    def test_default_values(self):
        chunk = DocumentChunkItem()
        assert chunk.document_id == ""
        assert chunk.chunk_id  # UUID auto-generated
        assert chunk.chunk_index == 0
        assert chunk.content == ""
        assert chunk.chunk_metadata is None
        assert chunk.vector_id is None
        assert chunk.token_count == 0

    def test_to_item(self, full_chunk: DocumentChunkItem):
        item = full_chunk.to_item()
        assert item["document_id"] == "doc-1"
        assert item["chunk_id"] == "chunk-1"
        assert item["chunk_index"] == 3
        assert item["content"] == "Some text content from the document."
        assert item["chunk_metadata"] == '{"page": 2}'
        assert item["vector_id"] == "vec-abc"
        assert item["token_count"] == 42
        assert item["created_at"] == "2024-06-01T12:00:00"

    def test_to_item_strips_none_values(self):
        chunk = DocumentChunkItem(document_id="d1", chunk_id="c1")
        item = chunk.to_item()
        assert "chunk_metadata" not in item
        assert "vector_id" not in item
        assert item["chunk_index"] == 0
        assert item["token_count"] == 0

    def test_to_api_dict(self, full_chunk: DocumentChunkItem):
        api = full_chunk.to_api_dict()
        assert api["chunkId"] == "chunk-1"
        assert api["documentId"] == "doc-1"
        assert api["chunkIndex"] == 3
        assert api["content"] == "Some text content from the document."
        assert api["tokenCount"] == 42
        assert api["createdAt"] == "2024-06-01T12:00:00"
        # chunk_metadata and vector_id are NOT in api_dict
        assert "chunkMetadata" not in api
        assert "vectorId" not in api

    def test_from_item_roundtrip(self, full_chunk: DocumentChunkItem):
        item = full_chunk.to_item()
        restored = DocumentChunkItem.from_item(item)
        assert restored.document_id == full_chunk.document_id
        assert restored.chunk_id == full_chunk.chunk_id
        assert restored.chunk_index == full_chunk.chunk_index
        assert restored.content == full_chunk.content
        assert restored.chunk_metadata == full_chunk.chunk_metadata
        assert restored.vector_id == full_chunk.vector_id
        assert restored.token_count == full_chunk.token_count
        assert restored.created_at == full_chunk.created_at

    def test_from_item_missing_optional_fields(self):
        minimal = {"document_id": "d1", "chunk_id": "c1", "content": "hi"}
        chunk = DocumentChunkItem.from_item(minimal)
        assert chunk.document_id == "d1"
        assert chunk.chunk_id == "c1"
        assert chunk.content == "hi"
        assert chunk.chunk_metadata is None
        assert chunk.vector_id is None
        assert chunk.chunk_index == 0
        assert chunk.token_count == 0

    def test_from_item_ignores_extra_keys(self):
        item = {"document_id": "d1", "chunk_id": "c1", "extra": "nope"}
        chunk = DocumentChunkItem.from_item(item)
        assert chunk.document_id == "d1"
        assert not hasattr(chunk, "extra")


# ====================================================================
# ModelItem
# ====================================================================

class TestModelItem:
    """Tests for database.schemas.model.ModelItem."""

    @pytest.fixture
    def full_model(self) -> ModelItem:
        return ModelItem(
            user_id="user-1",
            id="model-1",
            name="GPT-4o",
            provider="openai",
            model_id="gpt-4o",
            model_type="chat",
            description="OpenAI GPT-4o chat model",
            config='{"stream": true}',
            encrypted_api_key="enc_key_abc",
            temperature="0.7",
            max_tokens="4096",
            top_p="0.9",
            frequency_penalty="0.5",
            presence_penalty="0.3",
            is_active=True,
            is_global=False,
            created_at="2024-06-01T00:00:00",
            updated_at="2024-06-02T00:00:00",
        )

    def test_construction(self, full_model: ModelItem):
        assert full_model.user_id == "user-1"
        assert full_model.id == "model-1"
        assert full_model.name == "GPT-4o"
        assert full_model.provider == "openai"
        assert full_model.model_id == "gpt-4o"
        assert full_model.model_type == "chat"
        assert full_model.description == "OpenAI GPT-4o chat model"
        assert full_model.config == '{"stream": true}'
        assert full_model.encrypted_api_key == "enc_key_abc"
        assert full_model.temperature == "0.7"
        assert full_model.max_tokens == "4096"
        assert full_model.top_p == "0.9"
        assert full_model.frequency_penalty == "0.5"
        assert full_model.presence_penalty == "0.3"
        assert full_model.is_active is True
        assert full_model.is_global is False

    def test_default_values(self):
        model = ModelItem()
        assert model.user_id == ""
        assert model.id  # UUID auto-generated
        assert model.name == ""
        assert model.provider == ""
        assert model.model_type == "chat"
        assert model.description is None
        assert model.config is None
        assert model.encrypted_api_key is None
        assert model.temperature is None
        assert model.max_tokens is None
        assert model.top_p is None
        assert model.frequency_penalty is None
        assert model.presence_penalty is None
        assert model.is_active is True
        assert model.is_global is False

    def test_to_item(self, full_model: ModelItem):
        item = full_model.to_item()
        assert item["user_id"] == "user-1"
        assert item["id"] == "model-1"
        assert item["name"] == "GPT-4o"
        assert item["provider"] == "openai"
        assert item["model_id"] == "gpt-4o"
        assert item["model_type"] == "chat"
        assert item["description"] == "OpenAI GPT-4o chat model"
        assert item["config"] == '{"stream": true}'
        assert item["encrypted_api_key"] == "enc_key_abc"
        assert item["temperature"] == "0.7"
        assert item["max_tokens"] == "4096"
        assert item["top_p"] == "0.9"
        assert item["frequency_penalty"] == "0.5"
        assert item["presence_penalty"] == "0.3"
        assert item["is_active"] is True
        assert item["is_global"] is False
        assert item["created_at"] == "2024-06-01T00:00:00"
        assert item["updated_at"] == "2024-06-02T00:00:00"

    def test_to_item_strips_none_values(self):
        model = ModelItem(user_id="u1", id="m1", name="Test")
        item = model.to_item()
        assert "description" not in item
        assert "config" not in item
        assert "encrypted_api_key" not in item
        assert "temperature" not in item
        assert "max_tokens" not in item
        assert "top_p" not in item
        assert "frequency_penalty" not in item
        assert "presence_penalty" not in item
        # Booleans are not None, so they should be present
        assert item["is_active"] is True
        assert item["is_global"] is False

    def test_to_api_dict(self, full_model: ModelItem):
        api = full_model.to_api_dict()
        assert api["id"] == "model-1"
        assert api["name"] == "GPT-4o"
        assert api["provider"] == "OPENAI"  # uppercased
        assert api["modelId"] == "gpt-4o"
        assert api["modelType"] == "chat"
        assert api["description"] == "OpenAI GPT-4o chat model"
        assert api["userId"] == "user-1"
        assert api["temperature"] == 0.7
        assert api["maxTokens"] == 4096
        assert api["topP"] == 0.9
        assert api["frequencyPenalty"] == 0.5
        assert api["presencePenalty"] == 0.3
        assert api["isActive"] is True
        assert api["isGlobal"] is False
        assert api["createdAt"] == "2024-06-01T00:00:00"
        assert api["updatedAt"] == "2024-06-02T00:00:00"
        # config not included by default
        assert "config" not in api

    def test_to_api_dict_global_user_id_is_none(self):
        model = ModelItem(user_id="GLOBAL", is_global=True)
        api = model.to_api_dict()
        assert api["userId"] is None
        assert api["isGlobal"] is True

    def test_to_api_dict_provider_uppercased(self):
        model = ModelItem(provider="anthropic")
        api = model.to_api_dict()
        assert api["provider"] == "ANTHROPIC"

    def test_to_api_dict_empty_provider(self):
        model = ModelItem(provider="")
        api = model.to_api_dict()
        assert api["provider"] == ""

    def test_to_api_dict_none_numerics(self):
        model = ModelItem()
        api = model.to_api_dict()
        assert api["temperature"] is None
        assert api["maxTokens"] is None
        assert api["topP"] is None
        assert api["frequencyPenalty"] is None
        assert api["presencePenalty"] is None

    def test_to_api_dict_include_config_valid_json(self, full_model: ModelItem):
        api = full_model.to_api_dict(include_config=True)
        assert api["config"] == {"stream": True}

    def test_to_api_dict_include_config_invalid_json(self):
        model = ModelItem(config="not-json{")
        api = model.to_api_dict(include_config=True)
        assert api["config"] == "not-json{"

    def test_to_api_dict_include_config_none(self):
        model = ModelItem(config=None)
        api = model.to_api_dict(include_config=True)
        assert "config" not in api

    def test_from_item_roundtrip(self, full_model: ModelItem):
        item = full_model.to_item()
        restored = ModelItem.from_item(item)
        assert restored.user_id == full_model.user_id
        assert restored.id == full_model.id
        assert restored.name == full_model.name
        assert restored.provider == full_model.provider
        assert restored.model_id == full_model.model_id
        assert restored.model_type == full_model.model_type
        assert restored.description == full_model.description
        assert restored.config == full_model.config
        assert restored.encrypted_api_key == full_model.encrypted_api_key
        assert restored.temperature == full_model.temperature
        assert restored.max_tokens == full_model.max_tokens
        assert restored.top_p == full_model.top_p
        assert restored.frequency_penalty == full_model.frequency_penalty
        assert restored.presence_penalty == full_model.presence_penalty
        assert restored.is_active == full_model.is_active
        assert restored.is_global == full_model.is_global
        assert restored.created_at == full_model.created_at
        assert restored.updated_at == full_model.updated_at

    def test_from_item_missing_optional_fields(self):
        minimal = {"user_id": "u1", "id": "m1", "name": "Tiny"}
        model = ModelItem.from_item(minimal)
        assert model.user_id == "u1"
        assert model.id == "m1"
        assert model.name == "Tiny"
        assert model.description is None
        assert model.config is None
        assert model.encrypted_api_key is None
        assert model.temperature is None
        assert model.max_tokens is None
        assert model.is_active is True
        assert model.is_global is False

    def test_from_item_ignores_extra_keys(self):
        item = {"user_id": "u1", "id": "m1", "bogus": "value"}
        model = ModelItem.from_item(item)
        assert model.user_id == "u1"
        assert not hasattr(model, "bogus")


# ====================================================================
# PipelineItem
# ====================================================================

class TestPipelineItem:
    """Tests for database.schemas.pipeline.PipelineItem."""

    @pytest.fixture
    def full_pipeline(self) -> PipelineItem:
        return PipelineItem(
            user_id="user-1",
            id="pipe-1",
            model_id="model-1",
            embedding_model_id="emb-1",
            name="Invoice Extractor",
            description="Extracts fields from invoices",
            pipeline_type="document_explore",
            config='{"field_values": {"vendor": "Acme"}}',
            prompt_template="Extract the following: {{fields}}",
            output_schema='{"type": "object"}',
            status="completed",
            created_at="2024-06-01T00:00:00",
            updated_at="2024-06-02T00:00:00",
        )

    def test_construction(self, full_pipeline: PipelineItem):
        assert full_pipeline.user_id == "user-1"
        assert full_pipeline.id == "pipe-1"
        assert full_pipeline.model_id == "model-1"
        assert full_pipeline.embedding_model_id == "emb-1"
        assert full_pipeline.name == "Invoice Extractor"
        assert full_pipeline.description == "Extracts fields from invoices"
        assert full_pipeline.pipeline_type == "document_explore"
        assert full_pipeline.config == '{"field_values": {"vendor": "Acme"}}'
        assert full_pipeline.prompt_template == "Extract the following: {{fields}}"
        assert full_pipeline.output_schema == '{"type": "object"}'
        assert full_pipeline.status == "completed"

    def test_default_values(self):
        pipeline = PipelineItem()
        assert pipeline.user_id == ""
        assert pipeline.id  # UUID auto-generated
        assert pipeline.model_id == ""
        assert pipeline.embedding_model_id == ""
        assert pipeline.name == ""
        assert pipeline.description is None
        assert pipeline.pipeline_type is None
        assert pipeline.config is None
        assert pipeline.prompt_template is None
        assert pipeline.output_schema is None
        assert pipeline.status == "pending"

    def test_to_item(self, full_pipeline: PipelineItem):
        item = full_pipeline.to_item()
        assert item["user_id"] == "user-1"
        assert item["id"] == "pipe-1"
        assert item["model_id"] == "model-1"
        assert item["embedding_model_id"] == "emb-1"
        assert item["name"] == "Invoice Extractor"
        assert item["description"] == "Extracts fields from invoices"
        assert item["pipeline_type"] == "document_explore"
        assert item["config"] == '{"field_values": {"vendor": "Acme"}}'
        assert item["prompt_template"] == "Extract the following: {{fields}}"
        assert item["output_schema"] == '{"type": "object"}'
        assert item["status"] == "completed"
        assert item["created_at"] == "2024-06-01T00:00:00"
        assert item["updated_at"] == "2024-06-02T00:00:00"

    def test_to_item_strips_none_values(self):
        pipeline = PipelineItem(user_id="u1", id="p1", name="Test")
        item = pipeline.to_item()
        assert "description" not in item
        assert "pipeline_type" not in item
        assert "config" not in item
        assert "prompt_template" not in item
        assert "output_schema" not in item
        assert item["status"] == "pending"

    def test_to_api_dict(self, full_pipeline: PipelineItem):
        api = full_pipeline.to_api_dict(document_ids=["doc-1", "doc-2"])
        assert api["id"] == "pipe-1"
        assert api["userId"] == "user-1"
        assert api["modelId"] == "model-1"
        assert api["embeddingModelId"] == "emb-1"
        assert api["name"] == "Invoice Extractor"
        assert api["description"] == "Extracts fields from invoices"
        assert api["pipelineType"] == "document_explore"
        assert api["fieldValues"] == {"vendor": "Acme"}
        assert api["documentIds"] == ["doc-1", "doc-2"]
        assert api["config"] == '{"field_values": {"vendor": "Acme"}}'
        assert api["promptTemplate"] == "Extract the following: {{fields}}"
        assert api["outputSchema"] == '{"type": "object"}'
        assert api["status"] == "completed"
        assert api["createdAt"] == "2024-06-01T00:00:00"
        assert api["updatedAt"] == "2024-06-02T00:00:00"

    def test_to_api_dict_no_document_ids(self, full_pipeline: PipelineItem):
        api = full_pipeline.to_api_dict()
        assert api["documentIds"] == []

    def test_to_api_dict_field_values_from_config(self):
        config = json.dumps({"field_values": {"name": "Alice", "age": "30"}})
        pipeline = PipelineItem(config=config)
        api = pipeline.to_api_dict()
        assert api["fieldValues"] == {"name": "Alice", "age": "30"}

    def test_to_api_dict_no_config(self):
        pipeline = PipelineItem()
        api = pipeline.to_api_dict()
        assert api["fieldValues"] == {}
        assert api["config"] is None

    def test_to_api_dict_invalid_config_json(self):
        pipeline = PipelineItem(config="not-json{")
        api = pipeline.to_api_dict()
        assert api["fieldValues"] == {}
        assert api["config"] == "not-json{"

    def test_to_api_dict_config_without_field_values_key(self):
        pipeline = PipelineItem(config='{"other_key": "val"}')
        api = pipeline.to_api_dict()
        assert api["fieldValues"] == {}

    def test_from_item_roundtrip(self, full_pipeline: PipelineItem):
        item = full_pipeline.to_item()
        restored = PipelineItem.from_item(item)
        assert restored.user_id == full_pipeline.user_id
        assert restored.id == full_pipeline.id
        assert restored.model_id == full_pipeline.model_id
        assert restored.embedding_model_id == full_pipeline.embedding_model_id
        assert restored.name == full_pipeline.name
        assert restored.description == full_pipeline.description
        assert restored.pipeline_type == full_pipeline.pipeline_type
        assert restored.config == full_pipeline.config
        assert restored.prompt_template == full_pipeline.prompt_template
        assert restored.output_schema == full_pipeline.output_schema
        assert restored.status == full_pipeline.status
        assert restored.created_at == full_pipeline.created_at
        assert restored.updated_at == full_pipeline.updated_at

    def test_from_item_missing_optional_fields(self):
        minimal = {"user_id": "u1", "id": "p1", "name": "Bare"}
        pipeline = PipelineItem.from_item(minimal)
        assert pipeline.user_id == "u1"
        assert pipeline.id == "p1"
        assert pipeline.name == "Bare"
        assert pipeline.description is None
        assert pipeline.pipeline_type is None
        assert pipeline.config is None
        assert pipeline.prompt_template is None
        assert pipeline.output_schema is None
        assert pipeline.status == "pending"

    def test_from_item_ignores_extra_keys(self):
        item = {"user_id": "u1", "id": "p1", "random_key": "value"}
        pipeline = PipelineItem.from_item(item)
        assert pipeline.user_id == "u1"
        assert not hasattr(pipeline, "random_key")


# ====================================================================
# OutputItem
# ====================================================================

class TestOutputItem:
    """Tests for database.schemas.output.OutputItem."""

    @pytest.fixture
    def full_output(self) -> OutputItem:
        return OutputItem(
            pipeline_id="pipe-1",
            id="out-1",
            output_data='{"results": [{"name": "Alice"}]}',
            file_path="s3://bucket/outputs/out-1.json",
            format="json",
            created_at="2024-06-01T00:00:00",
        )

    def test_construction(self, full_output: OutputItem):
        assert full_output.pipeline_id == "pipe-1"
        assert full_output.id == "out-1"
        assert full_output.output_data == '{"results": [{"name": "Alice"}]}'
        assert full_output.file_path == "s3://bucket/outputs/out-1.json"
        assert full_output.format == "json"
        assert full_output.created_at == "2024-06-01T00:00:00"

    def test_default_values(self):
        output = OutputItem()
        assert output.pipeline_id == ""
        assert output.id  # UUID auto-generated
        assert output.output_data == ""
        assert output.file_path is None
        assert output.format is None

    def test_to_item(self, full_output: OutputItem):
        item = full_output.to_item()
        assert item["pipeline_id"] == "pipe-1"
        assert item["id"] == "out-1"
        assert item["output_data"] == '{"results": [{"name": "Alice"}]}'
        assert item["file_path"] == "s3://bucket/outputs/out-1.json"
        assert item["format"] == "json"
        assert item["created_at"] == "2024-06-01T00:00:00"

    def test_to_item_strips_none_values(self):
        output = OutputItem(pipeline_id="p1", id="o1")
        item = output.to_item()
        assert "file_path" not in item
        assert "format" not in item
        assert item["output_data"] == ""

    def test_to_api_dict_parses_json_output(self, full_output: OutputItem):
        api = full_output.to_api_dict()
        assert api["id"] == "out-1"
        assert api["pipelineId"] == "pipe-1"
        assert api["outputData"] == {"results": [{"name": "Alice"}]}
        assert api["filePath"] == "s3://bucket/outputs/out-1.json"
        assert api["format"] == "json"
        assert api["createdAt"] == "2024-06-01T00:00:00"

    def test_to_api_dict_invalid_json_returns_raw_string(self):
        output = OutputItem(output_data="not-json{")
        api = output.to_api_dict()
        assert api["outputData"] == "not-json{"

    def test_to_api_dict_empty_string_output(self):
        output = OutputItem(output_data="")
        api = output.to_api_dict()
        assert api["outputData"] == ""

    def test_to_api_dict_plain_text_output(self):
        output = OutputItem(output_data="plain text result")
        api = output.to_api_dict()
        assert api["outputData"] == "plain text result"

    def test_from_item_roundtrip(self, full_output: OutputItem):
        item = full_output.to_item()
        restored = OutputItem.from_item(item)
        assert restored.pipeline_id == full_output.pipeline_id
        assert restored.id == full_output.id
        assert restored.output_data == full_output.output_data
        assert restored.file_path == full_output.file_path
        assert restored.format == full_output.format
        assert restored.created_at == full_output.created_at

    def test_from_item_missing_optional_fields(self):
        minimal = {"pipeline_id": "p1", "id": "o1"}
        output = OutputItem.from_item(minimal)
        assert output.pipeline_id == "p1"
        assert output.id == "o1"
        assert output.file_path is None
        assert output.format is None
        assert output.output_data == ""

    def test_from_item_ignores_extra_keys(self):
        item = {"pipeline_id": "p1", "id": "o1", "extra_field": "val"}
        output = OutputItem.from_item(item)
        assert output.pipeline_id == "p1"
        assert not hasattr(output, "extra_field")


# ====================================================================
# QueryItem
# ====================================================================

class TestQueryItem:
    """Tests for database.schemas.query.QueryItem."""

    @pytest.fixture
    def full_query(self) -> QueryItem:
        return QueryItem(
            user_id="user-1",
            id="query-1",
            pipeline_id="pipe-1",
            question="What is the vendor name?",
            answer="The vendor name is Acme Corp.",
            context="Extracted from page 2: Vendor: Acme Corp.",
            query_metadata='{"tokens_used": 150}',
            created_at="2024-06-01T00:00:00",
        )

    def test_construction(self, full_query: QueryItem):
        assert full_query.user_id == "user-1"
        assert full_query.id == "query-1"
        assert full_query.pipeline_id == "pipe-1"
        assert full_query.question == "What is the vendor name?"
        assert full_query.answer == "The vendor name is Acme Corp."
        assert full_query.context == "Extracted from page 2: Vendor: Acme Corp."
        assert full_query.query_metadata == '{"tokens_used": 150}'
        assert full_query.created_at == "2024-06-01T00:00:00"

    def test_default_values(self):
        query = QueryItem()
        assert query.user_id == ""
        assert query.id  # UUID auto-generated
        assert query.pipeline_id is None
        assert query.question == ""
        assert query.answer is None
        assert query.context is None
        assert query.query_metadata is None

    def test_to_item(self, full_query: QueryItem):
        item = full_query.to_item()
        assert item["user_id"] == "user-1"
        assert item["id"] == "query-1"
        assert item["pipeline_id"] == "pipe-1"
        assert item["question"] == "What is the vendor name?"
        assert item["answer"] == "The vendor name is Acme Corp."
        assert item["context"] == "Extracted from page 2: Vendor: Acme Corp."
        assert item["query_metadata"] == '{"tokens_used": 150}'
        assert item["created_at"] == "2024-06-01T00:00:00"

    def test_to_item_strips_none_values(self):
        query = QueryItem(user_id="u1", id="q1", question="Why?")
        item = query.to_item()
        assert "pipeline_id" not in item
        assert "answer" not in item
        assert "context" not in item
        assert "query_metadata" not in item
        assert item["question"] == "Why?"

    def test_to_api_dict(self, full_query: QueryItem):
        api = full_query.to_api_dict()
        assert api["id"] == "query-1"
        assert api["userId"] == "user-1"
        assert api["pipelineId"] == "pipe-1"
        assert api["question"] == "What is the vendor name?"
        assert api["answer"] == "The vendor name is Acme Corp."
        assert api["context"] == "Extracted from page 2: Vendor: Acme Corp."
        assert api["queryMetadata"] == '{"tokens_used": 150}'
        assert api["createdAt"] == "2024-06-01T00:00:00"

    def test_to_api_dict_with_none_optionals(self):
        query = QueryItem(user_id="u1", question="Hi?")
        api = query.to_api_dict()
        assert api["pipelineId"] is None
        assert api["answer"] is None
        assert api["context"] is None
        assert api["queryMetadata"] is None

    def test_from_item_roundtrip(self, full_query: QueryItem):
        item = full_query.to_item()
        restored = QueryItem.from_item(item)
        assert restored.user_id == full_query.user_id
        assert restored.id == full_query.id
        assert restored.pipeline_id == full_query.pipeline_id
        assert restored.question == full_query.question
        assert restored.answer == full_query.answer
        assert restored.context == full_query.context
        assert restored.query_metadata == full_query.query_metadata
        assert restored.created_at == full_query.created_at

    def test_from_item_missing_optional_fields(self):
        minimal = {"user_id": "u1", "id": "q1", "question": "Hello?"}
        query = QueryItem.from_item(minimal)
        assert query.user_id == "u1"
        assert query.id == "q1"
        assert query.question == "Hello?"
        assert query.pipeline_id is None
        assert query.answer is None
        assert query.context is None
        assert query.query_metadata is None

    def test_from_item_ignores_extra_keys(self):
        item = {"user_id": "u1", "id": "q1", "mystery": "data"}
        query = QueryItem.from_item(item)
        assert query.user_id == "u1"
        assert not hasattr(query, "mystery")
