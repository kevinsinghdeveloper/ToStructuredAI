"""Pipeline type controller — API routes for listing pipeline types."""
from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class PipelineTypeController(IController):
    def register_all_routes(self):
        self.register_route("/api/pipeline-types", "pipeline_types_list", self.list_pipeline_types, "GET")
        self.register_route("/api/pipeline-types/<type_id>", "pipeline_types_get", self.get_pipeline_type, "GET")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_pipeline_types(self):
        result = self._resource_manager.get(RequestResourceModel(data={}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_pipeline_type(self, type_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"type_id": type_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code
