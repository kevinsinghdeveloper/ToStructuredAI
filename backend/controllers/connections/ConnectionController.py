"""Connection controller — API routes for external database connections."""
from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class ConnectionController(IController):
    def register_all_routes(self):
        self.register_route("/api/connections", "connections_list", self.list_connections, "GET")
        self.register_route("/api/connections/<connection_id>", "connections_get", self.get_connection, "GET")
        self.register_route("/api/connections", "connections_create", self.create_connection, "POST")
        self.register_route("/api/connections/<connection_id>", "connections_update", self.update_connection, "PUT")
        self.register_route("/api/connections/<connection_id>", "connections_delete", self.delete_connection, "DELETE")
        self.register_route("/api/connections/<connection_id>/test", "connections_test", self.test_connection, "POST")
        self.register_route("/api/connections/<connection_id>/tables", "connections_tables", self.get_tables, "GET")
        self.register_route("/api/connections/<connection_id>/tables/<table_name>/schema", "connections_table_schema", self.get_table_schema, "GET")
        self.register_route("/api/connections/<connection_id>/tables/<table_name>/create-source", "connections_create_source", self.create_source_from_table, "POST")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_connections(self):
        result = self._resource_manager.get(RequestResourceModel(data={}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_connection(self, connection_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"connection_id": connection_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_connection(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data=data, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_connection(self, connection_id):
        data = request.get_json(force=True, silent=True) or {}
        data["connection_id"] = connection_id
        result = self._resource_manager.put(RequestResourceModel(data=data, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_connection(self, connection_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"connection_id": connection_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def test_connection(self, connection_id):
        result = self._resource_manager.test_connection(RequestResourceModel(
            data={"connection_id": connection_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_tables(self, connection_id):
        result = self._resource_manager.get_tables(RequestResourceModel(
            data={"connection_id": connection_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_table_schema(self, connection_id, table_name):
        result = self._resource_manager.get_table_schema(RequestResourceModel(
            data={"connection_id": connection_id, "table_name": table_name}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_source_from_table(self, connection_id, table_name):
        data = request.get_json(force=True, silent=True) or {}
        data["connection_id"] = connection_id
        data["table_name"] = table_name
        result = self._resource_manager.create_source_from_table(RequestResourceModel(
            data=data, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code
