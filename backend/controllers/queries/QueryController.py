"""Query controller — API routes for RAG Q&A."""
from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class QueryController(IController):
    def register_all_routes(self):
        self.register_route("/api/queries", "queries_list", self.list_queries, "GET")
        self.register_route("/api/queries", "queries_ask", self.ask_question, "POST")
        self.register_route("/api/queries/<query_id>", "queries_delete", self.delete_query, "DELETE")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_queries(self):
        pipeline_id = request.args.get("pipeline_id")
        result = self._resource_manager.get(RequestResourceModel(
            data={"pipeline_id": pipeline_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def ask_question(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data=data, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_query(self, query_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"query_id": query_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code
