"""Pipeline resource manager — CRUD, execute pipelines."""
import json
import uuid
from datetime import datetime
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from database.schemas.pipeline import PipelineItem
from database.schemas.pipeline_document import PipelineDocumentItem
from database.schemas.pipeline_source import PipelineSourceItem
from database.schemas.output import OutputItem
from services.pipeline_types.PipelineTypeService import PipelineTypeService


class PipelineResourceManager(IResourceManager):

    def __init__(self, service_managers=None):
        super().__init__(service_managers)
        self._pipeline_type_service = PipelineTypeService()

    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            pipeline_id = data.get("pipeline_id")

            if pipeline_id:
                p = self._db.pipelines.get_by_key({"user_id": user_id, "id": pipeline_id})
                if not p:
                    return ResponseModel(success=False, error="Pipeline not found", status_code=404)
                doc_ids = self._get_document_ids(pipeline_id)
                api_dict = PipelineItem.from_item(p).to_api_dict(doc_ids)
                api_dict["sourceIds"] = self._get_source_ids(pipeline_id)
                return ResponseModel(success=True, data=api_dict, status_code=200)

            pipelines = self._db.pipelines.find_by_user(user_id)
            result = []
            for p in pipelines:
                doc_ids = self._get_document_ids(p["id"])
                api_dict = PipelineItem.from_item(p).to_api_dict(doc_ids)
                api_dict["sourceIds"] = self._get_source_ids(p["id"])
                result.append(api_dict)
            return ResponseModel(success=True, data=result, status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to retrieve pipelines: {e}", status_code=500)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}

            name = data.get("name")
            model_id = data.get("modelId") or data.get("model_id")
            embedding_model_id = data.get("embeddingModelId") or data.get("embedding_model_id", "")
            document_ids = data.get("documentIds") or data.get("document_ids", [])
            source_ids = data.get("sourceIds") or data.get("source_ids", [])
            pipeline_type = data.get("pipelineType") or data.get("pipeline_type")

            if not name:
                return ResponseModel(success=False, error="Pipeline name is required", status_code=400)
            if not model_id:
                return ResponseModel(success=False, error="Model ID is required", status_code=400)

            # data_analyzer pipelines don't require embedding model
            pt_config = self._pipeline_type_service.get_pipeline_type(pipeline_type) if pipeline_type else None
            requires_embedding = pt_config.get("requires_embedding", True) if pt_config else True
            if requires_embedding and not embedding_model_id:
                return ResponseModel(success=False, error="Embedding model ID is required", status_code=400)

            config = {}
            field_values = data.get("fieldValues") or data.get("field_values", {})
            if field_values:
                config["field_values"] = field_values

            pipeline = PipelineItem(
                user_id=user_id, model_id=model_id, embedding_model_id=embedding_model_id,
                name=name, description=data.get("description"),
                pipeline_type=pipeline_type,
                config=json.dumps(config) if config else None,
                prompt_template=data.get("promptTemplate"),
                output_schema=data.get("outputSchema"),
                status="pending",
            )
            self._db.pipelines.create(pipeline.to_item())

            # Link documents
            for doc_id in document_ids:
                link = PipelineDocumentItem(pipeline_id=pipeline.id, document_id=doc_id)
                self._db.pipeline_documents.create(link.to_item())

            # Link sources
            for source_id in source_ids:
                link = PipelineSourceItem(pipeline_id=pipeline.id, source_id=source_id)
                self._db.pipeline_sources.create(link.to_item())

            api_dict = pipeline.to_api_dict(document_ids)
            api_dict["sourceIds"] = source_ids
            return ResponseModel(success=True, data=api_dict, status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to create pipeline: {e}", status_code=500)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            pipeline_id = data.get("pipeline_id") or data.get("id")
            if not pipeline_id:
                return ResponseModel(success=False, error="Pipeline ID is required", status_code=400)

            p = self._db.pipelines.get_by_key({"user_id": user_id, "id": pipeline_id})
            if not p:
                return ResponseModel(success=False, error="Pipeline not found", status_code=404)

            updates = {"updated_at": datetime.utcnow().isoformat()}
            for field in ["name", "description", "pipeline_type"]:
                val = data.get(field)
                if val is not None:
                    updates[field] = val

            # Update document links if provided
            new_doc_ids = data.get("documentIds") or data.get("document_ids")
            if new_doc_ids is not None:
                old_links = self._db.pipeline_documents.find_by("pipeline_id", pipeline_id)
                for link in old_links:
                    self._db.pipeline_documents.delete_by_key({"pipeline_id": pipeline_id, "document_id": link["document_id"]})
                for doc_id in new_doc_ids:
                    self._db.pipeline_documents.create(PipelineDocumentItem(pipeline_id=pipeline_id, document_id=doc_id).to_item())

            # Update source links if provided
            new_source_ids = data.get("sourceIds") or data.get("source_ids")
            if new_source_ids is not None:
                old_source_links = self._db.pipeline_sources.find_by_pipeline(pipeline_id)
                for link in old_source_links:
                    self._db.pipeline_sources.delete_by_key({"pipeline_id": pipeline_id, "source_id": link["source_id"]})
                for source_id in new_source_ids:
                    self._db.pipeline_sources.create(PipelineSourceItem(pipeline_id=pipeline_id, source_id=source_id).to_item())

            self._db.pipelines.update(pipeline_id, updates)
            updated = self._db.pipelines.get_by_key({"user_id": user_id, "id": pipeline_id})
            doc_ids = self._get_document_ids(pipeline_id)
            api_dict = PipelineItem.from_item(updated).to_api_dict(doc_ids)
            api_dict["sourceIds"] = self._get_source_ids(pipeline_id)
            return ResponseModel(success=True, data=api_dict, status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to update pipeline: {e}", status_code=500)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            pipeline_id = (request_resource_model.data or {}).get("pipeline_id")
            if not pipeline_id:
                return ResponseModel(success=False, error="Pipeline ID is required", status_code=400)

            p = self._db.pipelines.get_by_key({"user_id": user_id, "id": pipeline_id})
            if not p:
                return ResponseModel(success=False, error="Pipeline not found", status_code=404)

            # Delete related data
            links = self._db.pipeline_documents.find_by("pipeline_id", pipeline_id)
            for link in links:
                self._db.pipeline_documents.delete_by_key({"pipeline_id": pipeline_id, "document_id": link["document_id"]})

            source_links = self._db.pipeline_sources.find_by_pipeline(pipeline_id)
            for link in source_links:
                self._db.pipeline_sources.delete_by_key({"pipeline_id": pipeline_id, "source_id": link["source_id"]})

            self._db.outputs.delete_where("pipeline_id", pipeline_id)
            self._db.queries.delete_where("pipeline_id", pipeline_id)
            self._db.pipelines.delete_by_key({"user_id": user_id, "id": pipeline_id})

            return ResponseModel(success=True, message="Pipeline deleted successfully", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to delete pipeline: {e}", status_code=500)

    def run_pipeline(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Execute a pipeline to generate structured output."""
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            pipeline_id = data.get("pipeline_id")
            if not pipeline_id:
                return ResponseModel(success=False, error="Pipeline ID is required", status_code=400)

            p = self._db.pipelines.get_by_key({"user_id": user_id, "id": pipeline_id})
            if not p:
                return ResponseModel(success=False, error="Pipeline not found", status_code=404)

            pipeline = PipelineItem.from_item(p)
            self._db.pipelines.update(pipeline_id, {"status": "processing"})

            # Gather document chunks
            doc_ids = self._get_document_ids(pipeline_id)
            all_chunks = []
            for doc_id in doc_ids:
                chunks = self._db.document_chunks.find_by("document_id", doc_id)
                all_chunks.extend([c.get("content", "") for c in chunks])

            context = "\n\n---\n\n".join(all_chunks[:20])  # Limit context size

            # Get prompt template
            prompt_template = pipeline.prompt_template
            if not prompt_template and pipeline.pipeline_type:
                prompt_template = self._pipeline_type_service.build_prompt_template(pipeline.pipeline_type)

            if not prompt_template:
                prompt_template = "Based on the following context, provide a structured summary.\n\nContext:\n{context}"

            prompt = prompt_template.replace("{context}", context)

            # Create LLM and generate
            from services.ai.LangChainServiceManager import LangChainServiceManager
            model_data = self._db.models.get_by_key({"user_id": user_id, "id": pipeline.model_id})
            if not model_data:
                model_data = self._db.models.get_by_key({"user_id": "GLOBAL", "id": pipeline.model_id})
            if not model_data:
                self._db.pipelines.update(pipeline_id, {"status": "failed"})
                return ResponseModel(success=False, error="Model not found", status_code=404)

            from config.model_registry import get_llm_config
            from utils.encryption import decrypt_value
            config = json.loads(model_data.get("config", "{}")) if model_data.get("config") else {}
            if model_data.get("encrypted_api_key"):
                decrypted = decrypt_value(model_data["encrypted_api_key"])
                if decrypted:
                    config["api_key"] = decrypted

            llm_config = get_llm_config(model_data["model_id"], config)
            llm = LangChainServiceManager({"config": llm_config})
            llm.configure()

            result = llm.run_task({"task_type": "prompt", "prompt": prompt, "instructions": "You are a document analysis assistant."})

            output = OutputItem(pipeline_id=pipeline_id, output_data=json.dumps({"result": result}), format="json")
            self._db.outputs.create(output.to_item())
            self._db.pipelines.update(pipeline_id, {"status": "completed"})

            return ResponseModel(success=True, data=output.to_api_dict(), status_code=200)
        except Exception as e:
            try:
                self._db.pipelines.update(pipeline_id, {"status": "failed"})
            except Exception:
                pass
            return ResponseModel(success=False, error=f"Failed to run pipeline: {e}", status_code=500)

    def _get_document_ids(self, pipeline_id: str) -> list:
        links = self._db.pipeline_documents.find_by("pipeline_id", pipeline_id)
        return [link["document_id"] for link in links]

    def _get_source_ids(self, pipeline_id: str) -> list:
        links = self._db.pipeline_sources.find_by_pipeline(pipeline_id)
        return [link["source_id"] for link in links]
