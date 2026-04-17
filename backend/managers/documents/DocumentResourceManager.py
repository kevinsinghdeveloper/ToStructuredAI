"""Document resource manager — upload, process, list, delete documents."""
import json
import os
import uuid
import threading
from datetime import datetime
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from database.schemas.document import DocumentItem
from database.schemas.document_chunk import DocumentChunkItem
from services.ai.EmbeddingsService import EmbeddingsService
from config.model_registry import get_embedding_config
from utils.encryption import decrypt_value


class DocumentResourceManager(IResourceManager):

    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            document_id = data.get("document_id")
            action = data.get("action")

            if action == "by_embedding_model":
                return self._get_by_embedding_model(user_id, data)

            if document_id:
                doc = self._db.documents.get_by_key({"user_id": user_id, "id": document_id})
                if not doc:
                    return ResponseModel(success=False, error="Document not found", status_code=404)
                return ResponseModel(success=True, data=DocumentItem.from_item(doc).to_api_dict(), status_code=200)

            docs = self._db.documents.find_by_user(user_id)
            return ResponseModel(
                success=True,
                data=[DocumentItem.from_item(d).to_api_dict() for d in docs],
                status_code=200,
            )
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to retrieve documents: {e}", status_code=500)

    def _get_by_embedding_model(self, user_id: str, data: dict) -> ResponseModel:
        embedding_model_id = data.get("embedding_model_id")
        if not embedding_model_id:
            return ResponseModel(success=False, error="embedding_model_id is required", status_code=400)
        docs = self._db.documents.find_by_user(user_id)
        filtered = [
            DocumentItem.from_item(d).to_api_dict()
            for d in docs
            if d.get("embedding_model_id") == embedding_model_id and d.get("status") == "ready"
        ]
        return ResponseModel(success=True, data=filtered, status_code=200)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            file_obj = data.get("file")
            original_filename = data.get("filename")
            mime_type = data.get("mime_type")
            embedding_model_id = data.get("embedding_model_id")
            overwrite = data.get("overwrite", False)

            if not all([file_obj, original_filename, mime_type]):
                return ResponseModel(success=False, error="File, filename, and mime_type are required", status_code=400)
            if not embedding_model_id:
                return ResponseModel(success=False, error="embedding_model_id is required", status_code=400)

            # Check duplicate
            existing_docs = self._db.documents.find_by_user(user_id)
            existing = next((d for d in existing_docs if d.get("original_filename") == original_filename), None)
            if existing and not overwrite:
                return ResponseModel(
                    success=False, error=f"A document with filename '{original_filename}' already exists",
                    status_code=409, data={"existing_document": DocumentItem.from_item(existing).to_api_dict()},
                )
            if existing and overwrite:
                self._delete_document(user_id, existing["id"])

            # Upload file
            storage = self._service_managers.get("storage")
            ext = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4()}{ext}"

            file_obj.seek(0, os.SEEK_END)
            file_size = file_obj.tell()
            file_obj.seek(0)

            file_path = storage.upload_file(file_obj, unique_filename, subfolder=f"user_{user_id}")

            doc = DocumentItem(
                user_id=user_id, embedding_model_id=embedding_model_id,
                filename=unique_filename, original_filename=original_filename,
                file_path=file_path, file_size=file_size, mime_type=mime_type, status="uploaded",
            )
            self._db.documents.create(doc.to_item())

            # Process in background
            thread = threading.Thread(target=self._process_document_background, args=(doc.user_id, doc.id), daemon=True)
            thread.start()

            return ResponseModel(success=True, data=doc.to_api_dict(), message="Document uploaded. Processing in background.", status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to upload document: {e}", status_code=500)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            document_id = data.get("document_id")
            metadata = data.get("metadata")
            if not document_id:
                return ResponseModel(success=False, error="Document ID is required", status_code=400)

            doc = self._db.documents.get_by_key({"user_id": user_id, "id": document_id})
            if not doc:
                return ResponseModel(success=False, error="Document not found", status_code=404)

            updates = {"updated_at": datetime.utcnow().isoformat()}
            if metadata:
                updates["doc_metadata"] = json.dumps(metadata)
            self._db.documents.update(document_id, updates)

            updated = self._db.documents.get_by_key({"user_id": user_id, "id": document_id})
            return ResponseModel(success=True, data=DocumentItem.from_item(updated).to_api_dict(), status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to update document: {e}", status_code=500)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            document_id = (request_resource_model.data or {}).get("document_id")
            if not document_id:
                return ResponseModel(success=False, error="Document ID is required", status_code=400)

            doc = self._db.documents.get_by_key({"user_id": user_id, "id": document_id})
            if not doc:
                return ResponseModel(success=False, error="Document not found", status_code=404)

            self._delete_document(user_id, document_id)
            return ResponseModel(success=True, message="Document deleted successfully", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to delete document: {e}", status_code=500)

    def _delete_document(self, user_id: str, document_id: str):
        """Delete document, its chunks, pipeline links, and stored file."""
        # Remove from pipelines
        links = self._db.pipeline_documents.find_by("document_id", document_id)
        for link in links:
            self._db.pipeline_documents.delete_by_key({"pipeline_id": link["pipeline_id"], "document_id": document_id})

        # Delete chunks
        self._db.document_chunks.delete_where("document_id", document_id)

        # Delete vector embeddings
        vector_db = self._service_managers.get("vector_db")
        if vector_db:
            vector_db.delete_by_namespace(document_id)

        # Delete file from storage
        doc = self._db.documents.get_by_key({"user_id": user_id, "id": document_id})
        if doc and doc.get("file_path"):
            storage = self._service_managers.get("storage")
            if storage:
                try:
                    storage.delete_file(doc["file_path"])
                except Exception:
                    pass

        self._db.documents.delete_by_key({"user_id": user_id, "id": document_id})

    def _process_document_background(self, user_id: str, document_id: str):
        """Extract text, chunk, and create embeddings in a background thread."""
        try:
            doc = self._db.documents.get_by_key({"user_id": user_id, "id": document_id})
            if not doc:
                return

            # Get embedding model
            emb_model_id = doc.get("embedding_model_id")
            models = self._db.models.find_by("user_id", "GLOBAL") + self._db.models.find_by("user_id", user_id)
            model = next((m for m in models if m["id"] == emb_model_id), None)
            if not model:
                raise Exception(f"Embedding model {emb_model_id} not found")

            config = json.loads(model.get("config", "{}")) if model.get("config") else {}
            if model.get("encrypted_api_key"):
                decrypted = decrypt_value(model["encrypted_api_key"])
                if decrypted:
                    config["api_key"] = decrypted

            emb_config = get_embedding_config(model["model_id"], config)
            emb_service = EmbeddingsService({"config": emb_config})
            emb_service.configure()

            # Extract text
            self._db.documents.update(document_id, {"status": "extracting"})
            processor = self._service_managers.get("processor")
            text = processor.run_task({"task_type": "extract", "file_path": doc["file_path"], "mime_type": doc["mime_type"]})

            self._db.documents.update(document_id, {"extracted_text": text, "status": "embedding"})

            # Chunk text
            chunks = processor.run_task({"task_type": "chunk", "text": text})

            # Create embeddings and store chunks
            vector_db = self._service_managers.get("vector_db")
            vectors = []
            for idx, chunk_text in enumerate(chunks):
                embedding = emb_service.create_embedding(chunk_text)
                chunk_id = str(uuid.uuid4())
                chunk = DocumentChunkItem(
                    document_id=document_id, chunk_id=chunk_id,
                    chunk_index=idx, content=chunk_text,
                    vector_id=chunk_id, token_count=len(chunk_text.split()),
                )
                self._db.document_chunks.create(chunk.to_item())
                vectors.append({"id": chunk_id, "values": embedding, "metadata": {"document_id": document_id, "chunk_index": idx}})

            if vector_db and vectors:
                vector_db.upsert_vectors(vectors, namespace=document_id)

            self._db.documents.update(document_id, {"status": "ready", "chunk_count": len(chunks)})
        except Exception as e:
            try:
                self._db.documents.update(document_id, {"status": "error"})
            except Exception:
                pass
            print(f"Error processing document {document_id}: {e}")

    def download_document(self, document_id: str, user_id: str) -> tuple:
        doc = self._db.documents.get_by_key({"user_id": user_id, "id": document_id})
        if not doc:
            return None, "Document not found", 404
        storage = self._service_managers.get("storage")
        file_data = storage.download_file(doc["file_path"])
        return file_data, doc.get("original_filename", "download"), doc.get("mime_type", "application/octet-stream")
