"""Source controller — API routes for unified sources."""
from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class SourceController(IController):
    def register_all_routes(self):
        self.register_route("/api/sources", "sources_list", self.list_sources, "GET")
        self.register_route("/api/sources/<source_id>", "sources_get", self.get_source, "GET")
        self.register_route("/api/sources", "sources_create", self.create_source, "POST")
        self.register_route("/api/sources/<source_id>", "sources_update", self.update_source, "PUT")
        self.register_route("/api/sources/<source_id>", "sources_delete", self.delete_source, "DELETE")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_sources(self):
        result = self._resource_manager.get(RequestResourceModel(data={}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_source(self, source_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"source_id": source_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_source(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data=data, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_source(self, source_id):
        data = request.get_json(force=True, silent=True) or {}
        data["source_id"] = source_id
        result = self._resource_manager.put(RequestResourceModel(data=data, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_source(self, source_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"source_id": source_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code
