"""Source resource manager — CRUD for unified sources (document + database)."""
import json
import logging
from datetime import datetime, timezone
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from database.schemas.source import SourceItem

logger = logging.getLogger(__name__)


class SourceResourceManager(IResourceManager):

    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            source_id = data.get("source_id")

            if source_id:
                source = self._db.sources.get_by_key({"user_id": user_id, "id": source_id})
                if not source:
                    return ResponseModel(success=False, error="Source not found", status_code=404)
                return ResponseModel(success=True, data=SourceItem.from_item(source).to_api_dict(), status_code=200)

            sources = self._db.sources.find_by_user(user_id)
            result = [SourceItem.from_item(s).to_api_dict() for s in sources]
            return ResponseModel(success=True, data=result, status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to get sources: {e}", status_code=500)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}

            source = SourceItem(
                user_id=user_id,
                name=data.get("name", ""),
                source_type=data.get("source_type", "document"),
                is_queryable=data.get("is_queryable", False),
                status=data.get("status", "pending"),
                document_id=data.get("document_id"),
                connection_id=data.get("connection_id"),
                table_name=data.get("table_name"),
                sql_view_query=data.get("sql_view_query"),
                metadata_json=json.dumps(data["metadata"]) if data.get("metadata") else None,
                delimiter=data.get("delimiter"),
            )

            self._db.sources.create(source.to_item())
            logger.info("Created source '%s' (type=%s)", source.name, source.source_type)
            return ResponseModel(success=True, data=source.to_api_dict(), message="Source created", status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to create source: {e}", status_code=500)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Update source metadata (column descriptions, name, sql_view_query)."""
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            source_id = data.get("source_id") or data.get("id")

            if not source_id:
                return ResponseModel(success=False, error="Source ID is required", status_code=400)

            source = self._db.sources.get_by_key({"user_id": user_id, "id": source_id})
            if not source:
                return ResponseModel(success=False, error="Source not found", status_code=404)

            updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
            if "metadata" in data:
                updates["metadata_json"] = json.dumps(data["metadata"])
            if "name" in data:
                updates["name"] = data["name"]
            if "sql_view_query" in data:
                updates["sql_view_query"] = data["sql_view_query"]

            self._db.sources.update(source_id, updates)
            updated = self._db.sources.get_by_key({"user_id": user_id, "id": source_id})
            return ResponseModel(success=True, data=SourceItem.from_item(updated).to_api_dict(), message="Source updated", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to update source: {e}", status_code=500)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Delete a source and cascade cleanup (pipeline_sources, temp_data_tables)."""
        try:
            user_id = request_resource_model.user_id
            source_id = (request_resource_model.data or {}).get("source_id")

            if not source_id:
                return ResponseModel(success=False, error="Source ID is required", status_code=400)

            source = self._db.sources.get_by_key({"user_id": user_id, "id": source_id})
            if not source:
                return ResponseModel(success=False, error="Source not found", status_code=404)

            # Cleanup pipeline_source links
            pipeline_links = self._db.pipeline_sources.find_by_source(source_id)
            for link in pipeline_links:
                self._db.pipeline_sources.delete_by_key({
                    "pipeline_id": link["pipeline_id"],
                    "source_id": source_id,
                })

            # Cleanup temp data tables
            temp_tables = self._db.temp_data_tables.find_by_source(source_id)
            for tt in temp_tables:
                self._db.temp_data_tables.delete_by_key({
                    "pipeline_id": tt["pipeline_id"],
                    "id": tt["id"],
                })

            self._db.sources.delete_by_key({"user_id": user_id, "id": source_id})
            return ResponseModel(success=True, message="Source deleted", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to delete source: {e}", status_code=500)
