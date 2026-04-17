"""DatabaseService — reads DB_TYPE and provides typed repository accessors.

Usage in managers:
    db = self._service_managers["db"]
    user = db.users.get_by_id("user-123")
    docs = db.documents.find_by_user(user_id)
"""
import os
from typing import Optional, Dict

from abstractions.IServiceManagerBase import IServiceManagerBase
from database.repositories.user_repository import UserRepository
from database.repositories.document_repository import DocumentRepository
from database.repositories.model_repository import ModelRepository
from database.repositories.pipeline_repository import PipelineRepository
from database.repositories.output_repository import OutputRepository
from database.repositories.query_repository import QueryRepository
from database.repositories.config_repository import ConfigRepository
from database.repositories.connection_repository import ConnectionRepository
from database.repositories.source_repository import SourceRepository
from database.repositories.pipeline_source_repository import PipelineSourceRepository
from database.repositories.temp_data_table_repository import TempDataTableRepository


class DatabaseService(IServiceManagerBase):

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._db_type = os.getenv("DB_TYPE", "dynamodb")

        # Repositories (set during initialize)
        self.users = None
        self.organizations = None
        self.subscription_plans = None
        self.notifications = None
        self.audit_logs = None
        self.config = None
        # Document processing repositories
        self.documents = None
        self.document_chunks = None
        self.models = None
        self.pipelines = None
        self.pipeline_documents = None
        self.outputs = None
        self.queries = None
        self.usage_tracking = None
        self.plan_models = None
        # External database connections & sources
        self.connections = None
        self.sources = None
        self.pipeline_sources = None
        self.temp_data_tables = None

    def initialize(self):
        if self._db_type == "dynamodb":
            self._init_dynamodb()
        elif self._db_type == "postgres":
            self._init_postgres()
        else:
            raise ValueError(f"Unsupported DB_TYPE: {self._db_type}. Use 'dynamodb' or 'postgres'.")

    def _init_dynamodb(self):
        from database.repositories.connectors.DynamoDBConnector import DynamoDBConnector

        connector = DynamoDBConnector()
        connector.initialize()

        # Specialized repos
        self.users = UserRepository(connector.get_repository("users"))
        self.documents = DocumentRepository(connector.get_repository("documents", pk_field="user_id"))
        self.models = ModelRepository(connector.get_repository("models", pk_field="user_id"))
        self.pipelines = PipelineRepository(connector.get_repository("pipelines", pk_field="user_id"))
        self.outputs = OutputRepository(connector.get_repository("outputs", pk_field="pipeline_id"))
        self.queries = QueryRepository(connector.get_repository("queries", pk_field="user_id"))
        self.config = ConfigRepository(connector.get_repository("config", pk_field="pk"))

        # Generic repos
        self.organizations = connector.get_repository("organizations")
        self.subscription_plans = connector.get_repository("subscription_plans")
        self.notifications = connector.get_repository("notifications", pk_field="user_id")
        self.audit_logs = connector.get_repository("audit_log")
        self.document_chunks = connector.get_repository("document_chunks", pk_field="document_id")
        self.pipeline_documents = connector.get_repository("pipeline_documents", pk_field="pipeline_id")
        self.usage_tracking = connector.get_repository("usage_tracking", pk_field="user_id")
        self.plan_models = connector.get_repository("plan_models", pk_field="plan_id")

        # External database connections & sources
        self.connections = ConnectionRepository(connector.get_repository("database_connections", pk_field="user_id"))
        self.sources = SourceRepository(connector.get_repository("sources", pk_field="user_id"))
        self.pipeline_sources = PipelineSourceRepository(connector.get_repository("pipeline_sources", pk_field="pipeline_id"))
        self.temp_data_tables = TempDataTableRepository(connector.get_repository("temp_data_tables", pk_field="pipeline_id"))

    def _init_postgres(self):
        from database.repositories.connectors.SQLAlchemyConnector import SQLAlchemyConnector

        connector = SQLAlchemyConnector()
        connector.initialize()

        # Specialized repos
        self.users = UserRepository(connector.get_repository("users"))
        self.documents = DocumentRepository(connector.get_repository("documents"))
        self.models = ModelRepository(connector.get_repository("models"))
        self.pipelines = PipelineRepository(connector.get_repository("pipelines"))
        self.outputs = OutputRepository(connector.get_repository("outputs"))
        self.queries = QueryRepository(connector.get_repository("queries"))
        self.config = ConfigRepository(connector.get_repository("config", pk_field="pk"))

        # Generic repos
        self.organizations = connector.get_repository("organizations")
        self.subscription_plans = connector.get_repository("subscription_plans")
        self.notifications = connector.get_repository("notifications", pk_field="user_id")
        self.audit_logs = connector.get_repository("audit_log")
        self.document_chunks = connector.get_repository("document_chunks", pk_field="document_id")
        self.pipeline_documents = connector.get_repository("pipeline_documents", pk_field="pipeline_id")
        self.usage_tracking = connector.get_repository("usage_tracking", pk_field="user_id")
        self.plan_models = connector.get_repository("plan_models", pk_field="plan_id")

        # External database connections & sources
        self.connections = ConnectionRepository(connector.get_repository("database_connections"))
        self.sources = SourceRepository(connector.get_repository("sources"))
        self.pipeline_sources = PipelineSourceRepository(connector.get_repository("pipeline_sources", pk_field="pipeline_id"))
        self.temp_data_tables = TempDataTableRepository(connector.get_repository("temp_data_tables", pk_field="pipeline_id"))
