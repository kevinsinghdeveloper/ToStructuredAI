"""Query resource manager — RAG Q&A against pipeline documents."""
import json
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from database.schemas.query import QueryItem
from services.ai.LangChainServiceManager import LangChainServiceManager
from services.ai.EmbeddingsService import EmbeddingsService
from config.model_registry import get_llm_config, get_embedding_config
from utils.encryption import decrypt_value


class QueryResourceManager(IResourceManager):

    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            pipeline_id = data.get("pipeline_id")

            if pipeline_id:
                queries = self._db.queries.find_by_pipeline(pipeline_id)
            else:
                queries = self._db.queries.find_by_user(user_id)

            result = [QueryItem.from_item(q).to_api_dict() for q in queries]
            return ResponseModel(success=True, data=result, status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to retrieve queries: {e}", status_code=500)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Ask a question against pipeline documents using RAG."""
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            pipeline_id = data.get("pipeline_id")
            question = data.get("question")
            conversation_history = data.get("conversation_history", [])

            if not pipeline_id:
                return ResponseModel(success=False, error="pipeline_id is required", status_code=400)
            if not question:
                return ResponseModel(success=False, error="question is required", status_code=400)

            # Get pipeline
            p = self._db.pipelines.get_by_key({"user_id": user_id, "id": pipeline_id})
            if not p:
                return ResponseModel(success=False, error="Pipeline not found", status_code=404)

            # Initialize embedding service for query
            emb_model = self._resolve_model(p.get("embedding_model_id"), user_id)
            if not emb_model:
                return ResponseModel(success=False, error="Embedding model not found", status_code=404)

            emb_config = self._get_model_config(emb_model, "embedding")
            emb_service = EmbeddingsService({"config": emb_config})
            emb_service.configure()

            # Embed the question
            query_embedding = emb_service.embed_query(question)

            # Search for relevant chunks
            vector_db = self._service_managers.get("vector_db")
            doc_links = self._db.pipeline_documents.find_by("pipeline_id", pipeline_id)
            doc_ids = [link["document_id"] for link in doc_links]

            context_chunks = []
            if vector_db:
                for doc_id in doc_ids:
                    matches = vector_db.query(query_embedding, top_k=3, namespace=doc_id)
                    for match in matches:
                        chunk = self._db.document_chunks.get_by_key({"document_id": doc_id, "chunk_id": match["id"]})
                        if chunk:
                            context_chunks.append(chunk.get("content", ""))
            else:
                # Fallback: get all chunks directly
                for doc_id in doc_ids:
                    chunks = self._db.document_chunks.find_by("document_id", doc_id)
                    context_chunks.extend([c.get("content", "") for c in chunks[:5]])

            context = "\n\n---\n\n".join(context_chunks[:10])

            # Build prompt
            prompt_template = p.get("prompt_template") or (
                "You are a helpful AI assistant. Answer the user's question based on the provided document context.\n\n"
                "Context from documents:\n{context}\n\nQuestion: {question}\n\n"
                "Please provide a clear, accurate answer based solely on the information in the context above."
            )
            prompt = prompt_template.replace("{context}", context).replace("{question}", question)

            # Build messages with conversation history
            messages = [{"role": "system", "content": "You are a document analysis assistant."}]
            for entry in conversation_history[-10:]:
                messages.append({"role": entry["role"], "content": entry["content"]})
            messages.append({"role": "user", "content": prompt})

            # Initialize LLM
            chat_model = self._resolve_model(p.get("model_id"), user_id)
            if not chat_model:
                return ResponseModel(success=False, error="Chat model not found", status_code=404)

            llm_config = self._get_model_config(chat_model, "llm")
            llm = LangChainServiceManager({"config": llm_config})
            llm.configure()

            answer = llm.create_chat_completion(messages)

            # Save query
            query = QueryItem(
                user_id=user_id, pipeline_id=pipeline_id,
                question=question, answer=answer, context=context[:5000],
            )
            self._db.queries.create(query.to_item())

            return ResponseModel(success=True, data=query.to_api_dict(), status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to process query: {e}", status_code=500)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Method not allowed", status_code=405)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            query_id = (request_resource_model.data or {}).get("query_id")
            if not query_id:
                return ResponseModel(success=False, error="Query ID is required", status_code=400)
            self._db.queries.delete_by_key({"user_id": user_id, "id": query_id})
            return ResponseModel(success=True, message="Query deleted", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to delete query: {e}", status_code=500)

    def _resolve_model(self, model_id: str, user_id: str) -> dict:
        model = self._db.models.get_by_key({"user_id": user_id, "id": model_id})
        if not model:
            model = self._db.models.get_by_key({"user_id": "GLOBAL", "id": model_id})
        return model

    def _get_model_config(self, model: dict, model_type: str) -> dict:
        config = json.loads(model.get("config", "{}")) if model.get("config") else {}
        if model.get("encrypted_api_key"):
            decrypted = decrypt_value(model["encrypted_api_key"])
            if decrypted:
                config["api_key"] = decrypted
        if model_type == "llm":
            return get_llm_config(model["model_id"], config)
        return get_embedding_config(model["model_id"], config)
