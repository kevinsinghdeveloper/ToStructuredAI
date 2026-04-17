"""Document controller — API routes for document management."""
from flask import request, jsonify, send_file
from io import BytesIO
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class DocumentController(IController):
    def register_all_routes(self):
        self.register_route("/api/documents", "documents_list", self.list_documents, "GET")
        self.register_route("/api/documents/<document_id>", "documents_get", self.get_document, "GET")
        self.register_route("/api/documents/by-embedding-model", "documents_by_embedding", self.get_by_embedding_model, "GET")
        self.register_route("/api/documents", "documents_upload", self.upload_document, "POST")
        self.register_route("/api/documents/<document_id>", "documents_update", self.update_document, "PUT")
        self.register_route("/api/documents/<document_id>", "documents_delete", self.delete_document, "DELETE")
        self.register_route("/api/documents/<document_id>/download", "documents_download", self.download_document, "GET")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_documents(self):
        result = self._resource_manager.get(RequestResourceModel(data={}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_document(self, document_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"document_id": document_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_by_embedding_model(self):
        embedding_model_id = request.args.get("embedding_model_id")
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "by_embedding_model", "embedding_model_id": embedding_model_id},
            user_id=request.user_id,
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def upload_document(self):
        file = request.files.get("file")
        if not file:
            return jsonify({"success": False, "error": "No file provided"}), 400
        result = self._resource_manager.post(RequestResourceModel(
            data={
                "file": file.stream, "filename": file.filename,
                "mime_type": file.content_type,
                "embedding_model_id": request.form.get("embedding_model_id"),
                "overwrite": request.form.get("overwrite", "false").lower() == "true",
            },
            user_id=request.user_id,
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_document(self, document_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.put(RequestResourceModel(
            data={"document_id": document_id, **data}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_document(self, document_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"document_id": document_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def download_document(self, document_id):
        file_data, filename, mime_type = self._resource_manager.download_document(document_id, request.user_id)
        if file_data is None:
            return jsonify({"success": False, "error": filename}), mime_type
        return send_file(BytesIO(file_data), download_name=filename, mimetype=mime_type, as_attachment=True)
