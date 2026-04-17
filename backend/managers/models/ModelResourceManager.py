"""Model resource manager — CRUD for AI model configurations."""
import json
import uuid
from datetime import datetime
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from database.schemas.model import ModelItem
from utils.encryption import encrypt_value


class ModelResourceManager(IResourceManager):

    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            model_id = data.get("model_id")
            model_type = data.get("model_type")

            if model_id:
                # Search global and user models
                model = self._db.models.get_by_key({"user_id": user_id, "id": model_id})
                if not model:
                    model = self._db.models.get_by_key({"user_id": "GLOBAL", "id": model_id})
                if not model:
                    return ResponseModel(success=False, error="Model not found", status_code=404)
                return ResponseModel(success=True, data=ModelItem.from_item(model).to_api_dict(), status_code=200)

            # List all accessible models
            global_models = self._db.models.find_global_models()
            user_models = self._db.models.find_by_user(user_id)
            all_models = global_models + user_models

            if model_type:
                all_models = [m for m in all_models if m.get("model_type") == model_type]

            result = [ModelItem.from_item(m).to_api_dict() for m in all_models if m.get("is_active", True)]
            return ResponseModel(success=True, data=result, status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to retrieve models: {e}", status_code=500)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}

            name = data.get("name")
            provider = data.get("provider")
            model_id_str = data.get("modelId") or data.get("model_id")
            model_type = data.get("modelType") or data.get("model_type", "chat")

            if not all([name, provider, model_id_str]):
                return ResponseModel(success=False, error="name, provider, and modelId are required", status_code=400)

            # Encrypt API key if provided
            api_key = data.get("apiKey") or data.get("api_key")
            encrypted_key = encrypt_value(api_key) if api_key else None

            config_data = {}
            if data.get("temperature") is not None:
                config_data["temperature"] = data["temperature"]
            if data.get("maxTokens") is not None:
                config_data["max_tokens"] = data["maxTokens"]

            is_global = data.get("isGlobal", False)
            owner = "GLOBAL" if is_global else user_id

            model = ModelItem(
                user_id=owner, name=name, provider=provider.lower(),
                model_id=model_id_str, model_type=model_type,
                description=data.get("description"),
                config=json.dumps(config_data) if config_data else None,
                encrypted_api_key=encrypted_key,
                temperature=str(data.get("temperature", 0.7)),
                max_tokens=str(data.get("maxTokens", 2000)),
                top_p=str(data["topP"]) if data.get("topP") is not None else None,
                frequency_penalty=str(data["frequencyPenalty"]) if data.get("frequencyPenalty") is not None else None,
                presence_penalty=str(data["presencePenalty"]) if data.get("presencePenalty") is not None else None,
                is_active=True, is_global=is_global,
            )
            self._db.models.create(model.to_item())
            return ResponseModel(success=True, data=model.to_api_dict(), status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to create model: {e}", status_code=500)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            model_id = data.get("model_id") or data.get("id")
            if not model_id:
                return ResponseModel(success=False, error="Model ID is required", status_code=400)

            model = self._db.models.get_by_key({"user_id": user_id, "id": model_id})
            if not model:
                model = self._db.models.get_by_key({"user_id": "GLOBAL", "id": model_id})
            if not model:
                return ResponseModel(success=False, error="Model not found", status_code=404)

            updates = {"updated_at": datetime.utcnow().isoformat()}
            for field in ["name", "description"]:
                if data.get(field) is not None:
                    updates[field] = data[field]
            if data.get("temperature") is not None:
                updates["temperature"] = str(data["temperature"])
            if data.get("maxTokens") is not None:
                updates["max_tokens"] = str(data["maxTokens"])
            if data.get("apiKey"):
                updates["encrypted_api_key"] = encrypt_value(data["apiKey"])
            if data.get("isActive") is not None:
                updates["is_active"] = data["isActive"]

            self._db.models.update(model_id, updates)
            updated = self._db.models.get_by_key({"user_id": model["user_id"], "id": model_id})
            return ResponseModel(success=True, data=ModelItem.from_item(updated).to_api_dict(), status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to update model: {e}", status_code=500)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            model_id = (request_resource_model.data or {}).get("model_id")
            if not model_id:
                return ResponseModel(success=False, error="Model ID is required", status_code=400)

            model = self._db.models.get_by_key({"user_id": user_id, "id": model_id})
            if not model:
                return ResponseModel(success=False, error="Model not found", status_code=404)

            self._db.models.delete_by_key({"user_id": user_id, "id": model_id})
            return ResponseModel(success=True, message="Model deleted successfully", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to delete model: {e}", status_code=500)
