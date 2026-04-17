"""Output controller — API routes for pipeline outputs."""
from flask import request, jsonify, send_file
from io import BytesIO
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class OutputController(IController):
    def register_all_routes(self):
        self.register_route("/api/outputs", "outputs_list", self.list_outputs, "GET")
        self.register_route("/api/outputs/<output_id>/download", "outputs_download", self.download_output, "GET")
        self.register_route("/api/outputs/<output_id>", "outputs_delete", self.delete_output, "DELETE")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_outputs(self):
        pipeline_id = request.args.get("pipeline_id")
        result = self._resource_manager.get(RequestResourceModel(
            data={"pipeline_id": pipeline_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def download_output(self, output_id):
        pipeline_id = request.args.get("pipeline_id")
        file_data, filename, mime_type = self._resource_manager.download_output(pipeline_id, output_id)
        if file_data is None:
            return jsonify({"success": False, "error": filename}), mime_type
        return send_file(BytesIO(file_data), download_name=filename, mimetype=mime_type, as_attachment=True)

    @token_required
    def delete_output(self, output_id):
        pipeline_id = request.args.get("pipeline_id")
        result = self._resource_manager.delete(RequestResourceModel(
            data={"output_id": output_id, "pipeline_id": pipeline_id}, user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code
