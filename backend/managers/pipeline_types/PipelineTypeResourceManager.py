"""Pipeline type resource manager — list available pipeline types."""
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from services.pipeline_types.PipelineTypeService import PipelineTypeService


class PipelineTypeResourceManager(IResourceManager):

    def __init__(self, service_managers=None):
        super().__init__(service_managers)
        self._pipeline_type_service = PipelineTypeService()

    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            data = request_resource_model.data or {}
            type_id = data.get("type_id")

            if type_id:
                pt = self._pipeline_type_service.get_pipeline_type(type_id)
                if not pt:
                    return ResponseModel(success=False, error="Pipeline type not found", status_code=404)
                return ResponseModel(success=True, data=pt, status_code=200)

            types = self._pipeline_type_service.get_all_pipeline_types()
            return ResponseModel(success=True, data=types, status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to retrieve pipeline types: {e}", status_code=500)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Method not allowed", status_code=405)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Method not allowed", status_code=405)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Method not allowed", status_code=405)
