"""Model controller — API routes for AI model configuration."""
from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class ModelController(IController):
    def register_all_routes(self):
        self.register_route("/api/models", "models_list", self.list_models, "GET")
        self.register_route("/api/models/<model_id>", "models_get", self.get_model, "GET")
        self.register_route("/api/models", "models_create", self.create_model, "POST")
        self.register_route("/api/models/<model_id>", "models_update", self.update_model, "PUT")
        self.register_route("/api/models/<model_id>", "models_delete", self.delete_model, "DELETE")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_models(self):
        model_type = request.args.get("model_type")
        result = self._resource_manager.get(RequestResourceModel(
            data={"model_type": model_type}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_model(self, model_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"model_id": model_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_model(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data=data, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_model(self, model_id):
        data = request.get_json(force=True, silent=True) or {}
        data["model_id"] = model_id
        result = self._resource_manager.put(RequestResourceModel(data=data, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_model(self, model_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"model_id": model_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code
