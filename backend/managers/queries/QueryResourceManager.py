"""Query resource manager — RAG Q&A against pipeline documents + data_analyzer SQL."""
import json
import logging
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from database.schemas.query import QueryItem
from services.ai.LangChainServiceManager import LangChainServiceManager
from services.ai.EmbeddingsService import EmbeddingsService
from services.ai.SQLGenerationService import SQLGenerationService
from services.database.ConnectorFactory import ConnectorFactory
from config.model_registry import get_llm_config, get_embedding_config
from utils.encryption import decrypt_value

logger = logging.getLogger(__name__)


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
        """Ask a question — routes to RAG or data_analyzer based on pipeline type."""
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

            # Route by pipeline type
            pipeline_type = p.get("pipeline_type", "document_explore")
            if pipeline_type == "data_analyzer":
                return self._handle_data_analyzer_query(p, user_id, question, conversation_history)

            # --- document_explore flow (RAG) ---
            return self._handle_document_explore_query(p, user_id, pipeline_id, question, conversation_history)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to process query: {e}", status_code=500)

    def _handle_document_explore_query(self, p, user_id, pipeline_id, question, conversation_history):
        """RAG-based Q&A against pipeline documents."""
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

    def _handle_data_analyzer_query(self, pipeline, user_id, question, conversation_history):
        """Handle queries for data_analyzer pipelines using SQL generation."""
        try:
            pipeline_id = pipeline["id"]

            # Get pipeline sources
            pipeline_source_links = self._db.pipeline_sources.find_by_pipeline(pipeline_id)
            if not pipeline_source_links:
                return ResponseModel(
                    success=False,
                    error="Pipeline has no sources. Add queryable sources before querying.",
                    status_code=400,
                )

            # Gather table schemas and connection configs
            table_schemas = []
            table_connection_map = {}  # table_name -> connection config

            for ps_link in pipeline_source_links:
                source = self._db.sources.get_by_key({"user_id": user_id, "id": ps_link["source_id"]})
                if not source or not source.get("is_queryable"):
                    continue

                source_type = source.get("source_type", "document")

                if source_type == "database":
                    # DB source — get schema from source metadata, execution via connection
                    connection = self._db.connections.get_by_key({
                        "user_id": user_id,
                        "id": source.get("connection_id"),
                    })
                    if not connection or not source.get("table_name"):
                        continue

                    columns = []
                    if source.get("metadata_json"):
                        try:
                            metadata = json.loads(source["metadata_json"]) if isinstance(source["metadata_json"], str) else source["metadata_json"]
                            columns = metadata.get("columns", [])
                        except (json.JSONDecodeError, TypeError):
                            pass

                    table_schemas.append({
                        "table_name": source["table_name"],
                        "source_name": source.get("name", source["table_name"]),
                        "columns": columns,
                        "row_count": metadata.get("row_count", 0) if source.get("metadata_json") else 0,
                    })

                    table_connection_map[source["table_name"]] = {
                        "type": "db",
                        "connection_config": {
                            "db_type": connection.get("db_type", "postgresql"),
                            "host": connection.get("host", ""),
                            "port": int(connection.get("port", 5432)),
                            "database_name": connection.get("database_name", ""),
                            "username": connection.get("username", ""),
                            "password": connection.get("encrypted_password", ""),  # TODO: decrypt
                            "ssl_enabled": connection.get("ssl_enabled", False),
                            "schema_name": connection.get("schema_name", "public"),
                        },
                    }

                elif source_type == "document":
                    # CSV/Excel source — find temp data table
                    temp_tables = self._db.temp_data_tables.find_by_source(ps_link["source_id"])
                    pipeline_temps = [t for t in temp_tables if t.get("pipeline_id") == pipeline_id]
                    if not pipeline_temps:
                        continue

                    temp = pipeline_temps[0]
                    columns = []
                    if temp.get("schema_json"):
                        try:
                            schema_data = json.loads(temp["schema_json"]) if isinstance(temp["schema_json"], str) else temp["schema_json"]
                            columns = schema_data.get("columns", [])
                        except (json.JSONDecodeError, TypeError):
                            pass

                    table_schemas.append({
                        "table_name": temp["table_name"],
                        "source_name": source.get("name", temp["table_name"]),
                        "columns": columns,
                        "row_count": temp.get("row_count", 0),
                    })
                    table_connection_map[temp["table_name"]] = {"type": "temp"}

            if not table_schemas:
                return ResponseModel(
                    success=False,
                    error="No queryable data found for this pipeline.",
                    status_code=400,
                )

            # Use AIService for SQL generation
            ai_service = self._service_managers.get("ai")
            if not ai_service:
                return ResponseModel(success=False, error="AI service not available", status_code=500)

            sql_service = SQLGenerationService(ai_service)

            # Resolve model for the pipeline
            model_id = pipeline.get("model_id")

            sql_result = sql_service.generate_sql(
                question, table_schemas,
                model_id=model_id,
                conversation_history=conversation_history,
            )

            generated_sql = sql_result.get("sql", "")
            sql_explanation = sql_result.get("explanation", "")

            if not generated_sql:
                return ResponseModel(success=False, error="Could not generate SQL for this question.", status_code=400)

            # Execute SQL against the appropriate data source
            sql_results = None
            execution_error = None

            try:
                # Determine which connection to use
                external_config = None
                for table_name, info in table_connection_map.items():
                    if table_name.lower() in generated_sql.lower() and info["type"] == "db":
                        external_config = info
                        break

                if external_config:
                    connector = ConnectorFactory.create_and_connect(external_config["connection_config"])
                    try:
                        sql_results = connector.execute_query(generated_sql, row_limit=500)
                    finally:
                        connector.disconnect()
                else:
                    # No external DB — this would be for temp tables (future CSV/Excel support)
                    sql_results = []

            except Exception as e:
                execution_error = str(e)
                logger.error("SQL execution error: %s", execution_error)

            # Generate natural language answer
            if sql_results and not execution_error:
                answer = sql_service.generate_answer_from_results(
                    question, generated_sql, sql_results, model_id=model_id,
                )
            elif execution_error:
                answer = (
                    f"I generated the following SQL query but encountered an error executing it:\n\n"
                    f"```sql\n{generated_sql}\n```\n\n**Error:** {execution_error}\n\n"
                    "Please try rephrasing your question."
                )
            else:
                answer = f"I generated a SQL query but got no results:\n\n```sql\n{generated_sql}\n```\n\n{sql_explanation}"

            # Save query with SQL metadata
            query_metadata = json.dumps({
                "pipeline_type": "data_analyzer",
                "generated_sql": generated_sql,
                "sql_explanation": sql_explanation,
                "execution_error": execution_error,
                "result_row_count": len(sql_results) if sql_results else 0,
            })

            query = QueryItem(
                user_id=user_id, pipeline_id=pipeline_id,
                question=question, answer=answer,
                context=generated_sql, query_metadata=query_metadata,
            )
            self._db.queries.create(query.to_item())

            response_data = query.to_api_dict()
            response_data["sql"] = generated_sql
            response_data["sqlExplanation"] = sql_explanation
            response_data["sqlResults"] = sql_results
            response_data["confidence"] = 0.8 if not execution_error else 0.3

            return ResponseModel(success=True, data=response_data, status_code=200)

        except Exception as e:
            logger.error("Data analyzer query failed: %s", str(e))
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
