"""Connection resource manager — CRUD + introspection for external database connections."""
import json
import logging
from datetime import datetime, timezone
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from database.schemas.database_connection import DatabaseConnectionItem
from database.schemas.source import SourceItem
from services.database.ConnectorFactory import ConnectorFactory

logger = logging.getLogger(__name__)


class ConnectionResourceManager(IResourceManager):

    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            connection_id = data.get("connection_id")

            if connection_id:
                conn = self._db.connections.get_by_key({"user_id": user_id, "id": connection_id})
                if not conn:
                    return ResponseModel(success=False, error="Connection not found", status_code=404)
                return ResponseModel(success=True, data=DatabaseConnectionItem.from_item(conn).to_api_dict(), status_code=200)

            connections = self._db.connections.find_by_user(user_id)
            result = [DatabaseConnectionItem.from_item(c).to_api_dict() for c in connections]
            return ResponseModel(success=True, data=result, status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to get connections: {e}", status_code=500)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}

            name = data.get("name")
            if not name:
                return ResponseModel(success=False, error="Connection name is required", status_code=400)

            conn = DatabaseConnectionItem(
                user_id=user_id,
                name=name,
                db_type=data.get("dbType", "postgresql"),
                host=data.get("host", ""),
                port=int(data.get("port", 5432)),
                database_name=data.get("databaseName", ""),
                username=data.get("username", ""),
                encrypted_password=data.get("password", ""),  # TODO: encrypt with EncryptionService
                ssl_enabled=data.get("sslEnabled", False),
                schema_name=data.get("schemaName", "public"),
                status="untested",
            )

            self._db.connections.create(conn.to_item())
            return ResponseModel(success=True, data=conn.to_api_dict(), message="Connection created", status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to create connection: {e}", status_code=500)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            connection_id = data.get("connection_id") or data.get("id")

            if not connection_id:
                return ResponseModel(success=False, error="Connection ID is required", status_code=400)

            conn = self._db.connections.get_by_key({"user_id": user_id, "id": connection_id})
            if not conn:
                return ResponseModel(success=False, error="Connection not found", status_code=404)

            updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
            field_map = {
                "name": "name", "dbType": "db_type", "host": "host",
                "port": "port", "databaseName": "database_name",
                "username": "username", "sslEnabled": "ssl_enabled",
                "schemaName": "schema_name",
            }
            for api_key, db_key in field_map.items():
                if data.get(api_key) is not None:
                    updates[db_key] = data[api_key]

            if data.get("password"):
                updates["encrypted_password"] = data["password"]  # TODO: encrypt

            self._db.connections.update(connection_id, updates)
            updated = self._db.connections.get_by_key({"user_id": user_id, "id": connection_id})
            return ResponseModel(success=True, data=DatabaseConnectionItem.from_item(updated).to_api_dict(), message="Connection updated", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to update connection: {e}", status_code=500)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            user_id = request_resource_model.user_id
            connection_id = (request_resource_model.data or {}).get("connection_id")

            if not connection_id:
                return ResponseModel(success=False, error="Connection ID is required", status_code=400)

            conn = self._db.connections.get_by_key({"user_id": user_id, "id": connection_id})
            if not conn:
                return ResponseModel(success=False, error="Connection not found", status_code=404)

            self._db.connections.delete_by_key({"user_id": user_id, "id": connection_id})
            return ResponseModel(success=True, message="Connection deleted", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to delete connection: {e}", status_code=500)

    def _get_connection_config(self, conn_item: dict) -> dict:
        """Build connection config dict from a DynamoDB item."""
        return {
            "db_type": conn_item.get("db_type", "postgresql"),
            "host": conn_item.get("host", ""),
            "port": int(conn_item.get("port", 5432)),
            "database_name": conn_item.get("database_name", ""),
            "username": conn_item.get("username", ""),
            "password": conn_item.get("encrypted_password", ""),  # TODO: decrypt
            "ssl_enabled": conn_item.get("ssl_enabled", False),
            "schema_name": conn_item.get("schema_name", "public"),
        }

    def test_connection(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Test a database connection."""
        try:
            user_id = request_resource_model.user_id
            connection_id = (request_resource_model.data or {}).get("connection_id")

            conn = self._db.connections.get_by_key({"user_id": user_id, "id": connection_id})
            if not conn:
                return ResponseModel(success=False, error="Connection not found", status_code=404)

            try:
                connector = ConnectorFactory.create_and_connect(self._get_connection_config(conn))
                is_connected = connector.test_connection()
                connector.disconnect()
                status = "connected" if is_connected else "failed"
            except Exception as e:
                self._db.connections.update(connection_id, {"status": "failed"})
                return ResponseModel(success=False, error=f"Connection test failed: {e}", status_code=400)

            self._db.connections.update(connection_id, {"status": status})
            updated = self._db.connections.get_by_key({"user_id": user_id, "id": connection_id})
            return ResponseModel(success=True, data=DatabaseConnectionItem.from_item(updated).to_api_dict(), message="Connection test successful", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to test connection: {e}", status_code=500)

    def get_tables(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """List tables for a database connection."""
        try:
            user_id = request_resource_model.user_id
            connection_id = (request_resource_model.data or {}).get("connection_id")

            conn = self._db.connections.get_by_key({"user_id": user_id, "id": connection_id})
            if not conn:
                return ResponseModel(success=False, error="Connection not found", status_code=404)

            config = self._get_connection_config(conn)
            connector = ConnectorFactory.create_and_connect(config)
            table_names = connector.get_tables()
            connector.disconnect()

            schema = config.get("schema_name", "public")
            tables = [{"name": t, "schema": schema} for t in table_names]
            return ResponseModel(success=True, data=tables, status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to get tables: {e}", status_code=500)

    def get_table_schema(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Get schema for a specific table."""
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            connection_id = data.get("connection_id")
            table_name = data.get("table_name")

            conn = self._db.connections.get_by_key({"user_id": user_id, "id": connection_id})
            if not conn:
                return ResponseModel(success=False, error="Connection not found", status_code=404)

            connector = ConnectorFactory.create_and_connect(self._get_connection_config(conn))
            schema = connector.get_table_schema(table_name)
            sample_data = connector.get_sample_data(table_name, limit=5)
            connector.disconnect()

            return ResponseModel(success=True, data={"schema": schema, "sampleData": sample_data}, status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to get table schema: {e}", status_code=500)

    def create_source_from_table(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Create a Source record from a database table."""
        try:
            user_id = request_resource_model.user_id
            data = request_resource_model.data or {}
            connection_id = data.get("connection_id")
            table_name = data.get("table_name")
            source_name = data.get("name", table_name)

            conn = self._db.connections.get_by_key({"user_id": user_id, "id": connection_id})
            if not conn:
                return ResponseModel(success=False, error="Connection not found", status_code=404)

            # Get schema for metadata
            connector = ConnectorFactory.create_and_connect(self._get_connection_config(conn))
            schema = connector.get_table_schema(table_name)
            connector.disconnect()

            source = SourceItem(
                user_id=user_id,
                name=source_name,
                source_type="database",
                is_queryable=True,
                connection_id=connection_id,
                table_name=table_name,
                sql_view_query=data.get("sql_view_query"),
                metadata_json=json.dumps(schema),
                status="metadata_extracted",
            )

            self._db.sources.create(source.to_item())
            logger.info("Created DB source '%s' from table '%s'", source_name, table_name)
            return ResponseModel(success=True, data=source.to_api_dict(), message="Source created from database table", status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=f"Failed to create source: {e}", status_code=500)
