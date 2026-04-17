"""Output resource manager — retrieve and download pipeline outputs."""
import json
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from database.schemas.output import OutputItem


class OutputResourceManager(IResourceManager):

    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            data = request_resource_model.data or {}
            pipeline_id = data.get("pipeline_id")
            if not pipeline_id:
                return ResponseModel(success=False, error="pipeline_id is required", status_code=400)

            outputs = self._db.outputs.find_by_pipeline(pipeline_id)
            result = [OutputItem.from_item(o).to_api_dict() for o in outputs]
            return ResponseModel(success=True, data=result, status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to retrieve outputs: {e}", status_code=500)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Outputs are created via pipeline execution", status_code=405)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Method not allowed", status_code=405)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            data = request_resource_model.data or {}
            output_id = data.get("output_id")
            pipeline_id = data.get("pipeline_id")
            if not output_id or not pipeline_id:
                return ResponseModel(success=False, error="output_id and pipeline_id are required", status_code=400)
            self._db.outputs.delete_by_key({"pipeline_id": pipeline_id, "id": output_id})
            return ResponseModel(success=True, message="Output deleted", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to delete output: {e}", status_code=500)

    def download_output(self, pipeline_id: str, output_id: str) -> tuple:
        output = self._db.outputs.get_by_key({"pipeline_id": pipeline_id, "id": output_id})
        if not output:
            return None, "Output not found", 404
        data = output.get("output_data", "{}")
        return data.encode("utf-8"), f"output_{output_id}.json", "application/json"
