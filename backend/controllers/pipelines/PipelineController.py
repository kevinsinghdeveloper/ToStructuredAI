"""Pipeline controller — API routes for pipeline management and execution."""
from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class PipelineController(IController):
    def register_all_routes(self):
        self.register_route("/api/pipelines", "pipelines_list", self.list_pipelines, "GET")
        self.register_route("/api/pipelines/<pipeline_id>", "pipelines_get", self.get_pipeline, "GET")
        self.register_route("/api/pipelines", "pipelines_create", self.create_pipeline, "POST")
        self.register_route("/api/pipelines/<pipeline_id>", "pipelines_update", self.update_pipeline, "PUT")
        self.register_route("/api/pipelines/<pipeline_id>", "pipelines_delete", self.delete_pipeline, "DELETE")
        self.register_route("/api/pipelines/<pipeline_id>/run", "pipelines_run", self.run_pipeline, "POST")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_pipelines(self):
        result = self._resource_manager.get(RequestResourceModel(data={}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_pipeline(self, pipeline_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"pipeline_id": pipeline_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_pipeline(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data=data, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_pipeline(self, pipeline_id):
        data = request.get_json(force=True, silent=True) or {}
        data["pipeline_id"] = pipeline_id
        result = self._resource_manager.put(RequestResourceModel(data=data, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_pipeline(self, pipeline_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"pipeline_id": pipeline_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def run_pipeline(self, pipeline_id):
        data = request.get_json(force=True, silent=True) or {}
        data["pipeline_id"] = pipeline_id
        result = self._resource_manager.run_pipeline(RequestResourceModel(data=data, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code
