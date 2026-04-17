"""Unit tests for ModelResourceManager."""
import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import make_request


# ---------------------------------------------------------------------------
# Patch targets
# ---------------------------------------------------------------------------

_PATCH_ENCRYPT = "managers.models.ModelResourceManager.encrypt_value"


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_GLOBAL_MODEL_ITEM = {
    "user_id": "GLOBAL",
    "id": "model-global-001",
    "name": "GPT-4",
    "provider": "openai",
    "model_id": "gpt-4",
    "model_type": "chat",
    "description": "OpenAI GPT-4 chat model",
    "config": None,
    "encrypted_api_key": None,
    "temperature": "0.7",
    "max_tokens": "2000",
    "top_p": None,
    "frequency_penalty": None,
    "presence_penalty": None,
    "is_active": True,
    "is_global": True,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}

SAMPLE_USER_MODEL_ITEM = {
    "user_id": "user-123",
    "id": "model-user-001",
    "name": "My Custom Claude",
    "provider": "anthropic",
    "model_id": "claude-3-sonnet",
    "model_type": "chat",
    "description": "Custom Claude configuration",
    "config": '{"temperature": 0.5}',
    "encrypted_api_key": "encrypted-key-abc",
    "temperature": "0.5",
    "max_tokens": "4000",
    "top_p": "0.9",
    "frequency_penalty": None,
    "presence_penalty": None,
    "is_active": True,
    "is_global": False,
    "created_at": "2024-03-15T00:00:00",
    "updated_at": "2024-03-15T00:00:00",
}

SAMPLE_EMBEDDING_MODEL_ITEM = {
    "user_id": "GLOBAL",
    "id": "model-emb-001",
    "name": "Ada Embedding",
    "provider": "openai",
    "model_id": "text-embedding-ada-002",
    "model_type": "embedding",
    "description": "OpenAI embedding model",
    "config": None,
    "encrypted_api_key": None,
    "temperature": None,
    "max_tokens": None,
    "top_p": None,
    "frequency_penalty": None,
    "presence_penalty": None,
    "is_active": True,
    "is_global": True,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}

SAMPLE_INACTIVE_MODEL_ITEM = {
    **SAMPLE_USER_MODEL_ITEM,
    "id": "model-inactive-001",
    "name": "Disabled Model",
    "is_active": False,
}


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _build_manager(mock_db=None):
    """Instantiate ModelResourceManager with a mock db."""
    from managers.models.ModelResourceManager import ModelResourceManager

    if mock_db is None:
        mock_db = MagicMock()
    return ModelResourceManager(service_managers={"db": mock_db})


# ===========================================================================
# GET -- list all models (global + user)
# ===========================================================================

class TestGetModels:

    def test_get_all_models_success(self):
        mock_db = MagicMock()
        mock_db.models.find_global_models.return_value = [
            SAMPLE_GLOBAL_MODEL_ITEM.copy(),
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
        ]
        mock_db.models.find_by_user.return_value = [
            SAMPLE_USER_MODEL_ITEM.copy(),
        ]

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) == 3
        mock_db.models.find_global_models.assert_called_once()
        mock_db.models.find_by_user.assert_called_once_with("user-123")

    def test_get_all_models_filters_inactive(self):
        mock_db = MagicMock()
        mock_db.models.find_global_models.return_value = [SAMPLE_GLOBAL_MODEL_ITEM.copy()]
        mock_db.models.find_by_user.return_value = [
            SAMPLE_USER_MODEL_ITEM.copy(),
            SAMPLE_INACTIVE_MODEL_ITEM.copy(),
        ]

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert len(resp.data) == 2  # global + active user model (inactive filtered)
        model_ids = [m["id"] for m in resp.data]
        assert "model-inactive-001" not in model_ids

    def test_get_models_filter_by_type_chat(self):
        mock_db = MagicMock()
        mock_db.models.find_global_models.return_value = [
            SAMPLE_GLOBAL_MODEL_ITEM.copy(),
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
        ]
        mock_db.models.find_by_user.return_value = [SAMPLE_USER_MODEL_ITEM.copy()]

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_type": "chat"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        for m in resp.data:
            assert m["modelType"] == "chat"

    def test_get_models_filter_by_type_embedding(self):
        mock_db = MagicMock()
        mock_db.models.find_global_models.return_value = [
            SAMPLE_GLOBAL_MODEL_ITEM.copy(),
            SAMPLE_EMBEDDING_MODEL_ITEM.copy(),
        ]
        mock_db.models.find_by_user.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_type": "embedding"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert len(resp.data) == 1
        assert resp.data[0]["modelType"] == "embedding"

    def test_get_models_empty(self):
        mock_db = MagicMock()
        mock_db.models.find_global_models.return_value = []
        mock_db.models.find_by_user.return_value = []

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.data == []


# ===========================================================================
# GET -- single model by ID
# ===========================================================================

class TestGetSingleModel:

    def test_get_user_model_by_id(self):
        mock_db = MagicMock()
        mock_db.models.get_by_key.return_value = SAMPLE_USER_MODEL_ITEM.copy()

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_id": "model-user-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["id"] == "model-user-001"
        assert resp.data["name"] == "My Custom Claude"
        assert resp.data["provider"] == "ANTHROPIC"
        assert resp.data["modelId"] == "claude-3-sonnet"

    def test_get_global_model_by_id_fallback(self):
        """When model not found under user_id, falls back to GLOBAL."""
        mock_db = MagicMock()
        mock_db.models.get_by_key.side_effect = [
            None,                              # not found under user_id
            SAMPLE_GLOBAL_MODEL_ITEM.copy(),   # found under GLOBAL
        ]

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_id": "model-global-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.data["id"] == "model-global-001"
        assert resp.data["isGlobal"] is True
        # Verify both lookups were made
        assert mock_db.models.get_by_key.call_count == 2
        mock_db.models.get_by_key.assert_any_call({"user_id": "user-123", "id": "model-global-001"})
        mock_db.models.get_by_key.assert_any_call({"user_id": "GLOBAL", "id": "model-global-001"})

    def test_get_model_not_found(self):
        mock_db = MagicMock()
        mock_db.models.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_id": "nonexistent"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()


# ===========================================================================
# POST -- create model
# ===========================================================================

class TestPostModel:

    @patch(_PATCH_ENCRYPT, return_value="encrypted-key-xyz")
    def test_create_model_success(self, mock_encrypt):
        mock_db = MagicMock()
        mock_db.models.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "My GPT-4",
                "provider": "openai",
                "modelId": "gpt-4-turbo",
                "model_type": "chat",
                "apiKey": "sk-test-key-123",
                "temperature": 0.8,
                "maxTokens": 4096,
                "description": "Custom GPT-4 config",
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["name"] == "My GPT-4"
        assert resp.data["provider"] == "OPENAI"
        assert resp.data["modelId"] == "gpt-4-turbo"
        assert resp.data["modelType"] == "chat"
        assert resp.data["isGlobal"] is False
        mock_db.models.create.assert_called_once()
        mock_encrypt.assert_called_once_with("sk-test-key-123")

    @patch(_PATCH_ENCRYPT, return_value="encrypted-key-xyz")
    def test_create_global_model(self, mock_encrypt):
        mock_db = MagicMock()
        mock_db.models.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "Global GPT-4",
                "provider": "openai",
                "modelId": "gpt-4",
                "isGlobal": True,
                "apiKey": "sk-global-key",
            },
            user_id="admin-789",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["isGlobal"] is True
        # When isGlobal, userId in API dict is None
        assert resp.data["userId"] is None

    def test_create_model_without_api_key(self):
        mock_db = MagicMock()
        mock_db.models.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "No-Key Model",
                "provider": "openai",
                "modelId": "gpt-3.5-turbo",
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201

    def test_create_model_missing_name(self):
        mgr = _build_manager()
        req = make_request(
            data={"provider": "openai", "modelId": "gpt-4"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "required" in resp.error.lower()

    def test_create_model_missing_provider(self):
        mgr = _build_manager()
        req = make_request(
            data={"name": "My Model", "modelId": "gpt-4"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400

    def test_create_model_missing_model_id(self):
        mgr = _build_manager()
        req = make_request(
            data={"name": "My Model", "provider": "openai"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400

    @patch(_PATCH_ENCRYPT, return_value="enc")
    def test_create_model_with_optional_params(self, mock_encrypt):
        mock_db = MagicMock()
        mock_db.models.create.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "name": "Tuned Model",
                "provider": "openai",
                "modelId": "gpt-4",
                "apiKey": "sk-key",
                "temperature": 0.3,
                "maxTokens": 1000,
                "topP": 0.95,
                "frequencyPenalty": 0.5,
                "presencePenalty": 0.2,
            },
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.data["temperature"] == 0.3
        assert resp.data["maxTokens"] == 1000
        assert resp.data["topP"] == 0.95
        assert resp.data["frequencyPenalty"] == 0.5
        assert resp.data["presencePenalty"] == 0.2


# ===========================================================================
# PUT -- update model
# ===========================================================================

class TestPutModel:

    @patch(_PATCH_ENCRYPT, return_value="new-encrypted-key")
    def test_update_model_success(self, mock_encrypt):
        mock_db = MagicMock()
        original = SAMPLE_USER_MODEL_ITEM.copy()
        updated_item = {**original, "name": "Renamed Model", "temperature": "0.9"}
        mock_db.models.get_by_key.side_effect = [
            original,       # initial lookup (user scope)
            updated_item,   # after update
        ]
        mock_db.models.update.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={
                "model_id": "model-user-001",
                "name": "Renamed Model",
                "temperature": 0.9,
                "apiKey": "new-key",
            },
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["name"] == "Renamed Model"
        assert resp.data["temperature"] == 0.9
        mock_db.models.update.assert_called_once()
        mock_encrypt.assert_called_once_with("new-key")

    def test_update_model_fallback_to_global(self):
        """When model not found under user_id, falls back to GLOBAL lookup."""
        mock_db = MagicMock()
        global_model = SAMPLE_GLOBAL_MODEL_ITEM.copy()
        updated = {**global_model, "description": "Updated desc"}
        mock_db.models.get_by_key.side_effect = [
            None,           # not found under user_id
            global_model,   # found under GLOBAL
            updated,        # after update
        ]
        mock_db.models.update.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"model_id": "model-global-001", "description": "Updated desc"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert resp.data["description"] == "Updated desc"

    def test_update_model_missing_id(self):
        mgr = _build_manager()
        req = make_request(data={"name": "No ID"}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "model id" in resp.error.lower()

    def test_update_model_not_found(self):
        mock_db = MagicMock()
        mock_db.models.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_id": "nonexistent"}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()

    def test_update_model_partial_fields(self):
        """Only provided fields should be updated."""
        mock_db = MagicMock()
        original = SAMPLE_USER_MODEL_ITEM.copy()
        updated_item = {**original, "max_tokens": "8000"}
        mock_db.models.get_by_key.side_effect = [original, updated_item]
        mock_db.models.update.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"model_id": "model-user-001", "maxTokens": 8000},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        # Verify update was called with maxTokens mapped to max_tokens
        call_args = mock_db.models.update.call_args
        updates = call_args[0][1]
        assert "max_tokens" in updates
        assert updates["max_tokens"] == "8000"

    def test_update_model_toggle_active(self):
        mock_db = MagicMock()
        original = SAMPLE_USER_MODEL_ITEM.copy()
        deactivated = {**original, "is_active": False}
        mock_db.models.get_by_key.side_effect = [original, deactivated]
        mock_db.models.update.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"model_id": "model-user-001", "isActive": False},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert resp.data["isActive"] is False


# ===========================================================================
# DELETE -- remove model
# ===========================================================================

class TestDeleteModel:

    def test_delete_model_success(self):
        mock_db = MagicMock()
        mock_db.models.get_by_key.return_value = SAMPLE_USER_MODEL_ITEM.copy()
        mock_db.models.delete_by_key.return_value = {}

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_id": "model-user-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert "deleted" in resp.message.lower()
        mock_db.models.delete_by_key.assert_called_once_with({"user_id": "user-123", "id": "model-user-001"})

    def test_delete_model_missing_id(self):
        mgr = _build_manager()
        req = make_request(data={}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "model id" in resp.error.lower()

    def test_delete_model_not_found(self):
        mock_db = MagicMock()
        mock_db.models.get_by_key.return_value = None

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_id": "nonexistent"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 404
        assert "not found" in resp.error.lower()


# ===========================================================================
# Error handling
# ===========================================================================

class TestModelErrorHandling:

    def test_get_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.models.find_global_models.side_effect = Exception("Connection refused")

        mgr = _build_manager(mock_db)
        req = make_request(user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to retrieve" in resp.error.lower()

    @patch(_PATCH_ENCRYPT, side_effect=Exception("KMS key error"))
    def test_post_handles_encryption_exception(self, mock_encrypt):
        mock_db = MagicMock()

        mgr = _build_manager(mock_db)
        req = make_request(
            data={"name": "Model", "provider": "openai", "modelId": "gpt-4", "apiKey": "sk-key"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to create" in resp.error.lower()

    def test_put_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.models.get_by_key.side_effect = Exception("DynamoDB throttle")

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_id": "model-001"}, user_id="user-123")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to update" in resp.error.lower()

    def test_delete_handles_db_exception(self):
        mock_db = MagicMock()
        mock_db.models.get_by_key.side_effect = Exception("DynamoDB error")

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_id": "model-001"}, user_id="user-123")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 500
        assert "failed to delete" in resp.error.lower()


# ===========================================================================
# Response format validation
# ===========================================================================

class TestModelResponseFormat:

    def test_model_api_dict_has_expected_keys(self):
        mock_db = MagicMock()
        mock_db.models.get_by_key.return_value = SAMPLE_USER_MODEL_ITEM.copy()

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_id": "model-user-001"}, user_id="user-123")
        resp = mgr.get(req)

        expected_keys = {
            "id", "name", "provider", "modelId", "modelType", "description",
            "userId", "temperature", "maxTokens", "topP", "frequencyPenalty",
            "presencePenalty", "isActive", "isGlobal", "createdAt", "updatedAt",
        }
        assert expected_keys.issubset(set(resp.data.keys()))

    def test_global_model_user_id_is_none(self):
        mock_db = MagicMock()
        mock_db.models.get_by_key.return_value = SAMPLE_GLOBAL_MODEL_ITEM.copy()

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_id": "model-global-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.data["userId"] is None
        assert resp.data["isGlobal"] is True

    def test_provider_is_uppercased(self):
        mock_db = MagicMock()
        mock_db.models.get_by_key.return_value = SAMPLE_USER_MODEL_ITEM.copy()

        mgr = _build_manager(mock_db)
        req = make_request(data={"model_id": "model-user-001"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.data["provider"] == "ANTHROPIC"
