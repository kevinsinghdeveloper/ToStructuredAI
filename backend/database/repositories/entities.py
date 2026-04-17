"""Single source of truth for entity registration.

Each entity references its schema dataclass (from database/schemas/) and adds
DB-specific metadata. Connectors introspect the schema to derive field names,
types, and defaults — no duplication.

SQLAlchemyConnector: builds ORM models from schema fields + entity metadata
DynamoDBConnector: derives table name map from dynamo_suffix
"""
from dataclasses import dataclass, field
from typing import Type, List

from database.schemas.user import UserItem
from database.schemas.organization import OrganizationItem
from database.schemas.subscription_plan import SubscriptionPlanItem
from database.schemas.notification import NotificationItem
from database.schemas.audit_log import AuditLogItem
from database.schemas.document import DocumentItem
from database.schemas.document_chunk import DocumentChunkItem
from database.schemas.model import ModelItem
from database.schemas.pipeline import PipelineItem
from database.schemas.pipeline_document import PipelineDocumentItem
from database.schemas.output import OutputItem
from database.schemas.query import QueryItem
from database.schemas.usage_tracking import UsageTrackingItem
from database.schemas.plan_model import PlanModelItem
from database.schemas.database_connection import DatabaseConnectionItem
from database.schemas.source import SourceItem
from database.schemas.pipeline_source import PipelineSourceItem
from database.schemas.temp_data_table import TempDataTableItem


@dataclass
class ConfigItem:
    """Minimal schema for the config table (no dedicated schema file)."""
    pk: str = ""
    sk: str = ""
    data: str = ""
    updated_at: str = ""


@dataclass
class Entity:
    schema: Type
    dynamo_suffix: str
    pk: List[str]
    indexes: List[str] = field(default_factory=list)
    unique: List[str] = field(default_factory=list)
    text_fields: List[str] = field(default_factory=list)
    non_nullable: List[str] = field(default_factory=list)


ENTITIES = {
    "users": Entity(
        schema=UserItem,
        dynamo_suffix="users",
        pk=["id"],
        indexes=["email", "org_id"],
        unique=["email"],
        text_fields=["avatar_url", "notification_preferences", "oauth_providers"],
        non_nullable=["email"],
    ),
    "config": Entity(
        schema=ConfigItem,
        dynamo_suffix="config",
        pk=["pk", "sk"],
        text_fields=["data"],
    ),
    "organizations": Entity(
        schema=OrganizationItem,
        dynamo_suffix="organizations",
        pk=["id"],
        text_fields=["logo_url", "settings"],
        non_nullable=["name", "slug", "owner_id"],
    ),
    "subscription_plans": Entity(
        schema=SubscriptionPlanItem,
        dynamo_suffix="subscription-plans",
        pk=["id"],
        text_fields=["features", "description"],
        non_nullable=["name"],
    ),
    "notifications": Entity(
        schema=NotificationItem,
        dynamo_suffix="notifications",
        pk=["user_id", "timestamp_id"],
        text_fields=["message", "action_url", "metadata"],
    ),
    "audit_log": Entity(
        schema=AuditLogItem,
        dynamo_suffix="audit-log",
        pk=["id", "timestamp"],
        indexes=["user_id", "org_id"],
        text_fields=["details"],
        non_nullable=["user_id", "action"],
    ),
    # Document processing entities
    "documents": Entity(
        schema=DocumentItem,
        dynamo_suffix="documents",
        pk=["user_id", "id"],
        indexes=["status"],
        text_fields=["extracted_text", "doc_metadata"],
        non_nullable=["user_id", "filename"],
    ),
    "document_chunks": Entity(
        schema=DocumentChunkItem,
        dynamo_suffix="document-chunks",
        pk=["document_id", "chunk_id"],
        text_fields=["content", "chunk_metadata"],
        non_nullable=["document_id", "content"],
    ),
    "models": Entity(
        schema=ModelItem,
        dynamo_suffix="models",
        pk=["user_id", "id"],
        indexes=["model_type"],
        text_fields=["description", "config", "encrypted_api_key"],
        non_nullable=["name", "provider", "model_id"],
    ),
    "pipelines": Entity(
        schema=PipelineItem,
        dynamo_suffix="pipelines",
        pk=["user_id", "id"],
        indexes=["status"],
        text_fields=["description", "config", "prompt_template", "output_schema"],
        non_nullable=["user_id", "name"],
    ),
    "pipeline_documents": Entity(
        schema=PipelineDocumentItem,
        dynamo_suffix="pipeline-documents",
        pk=["pipeline_id", "document_id"],
        indexes=[],
    ),
    "outputs": Entity(
        schema=OutputItem,
        dynamo_suffix="outputs",
        pk=["pipeline_id", "id"],
        text_fields=["output_data"],
        non_nullable=["pipeline_id", "output_data"],
    ),
    "queries": Entity(
        schema=QueryItem,
        dynamo_suffix="queries",
        pk=["user_id", "id"],
        indexes=["pipeline_id"],
        text_fields=["question", "answer", "context", "query_metadata"],
        non_nullable=["user_id", "question"],
    ),
    "usage_tracking": Entity(
        schema=UsageTrackingItem,
        dynamo_suffix="usage-tracking",
        pk=["user_id", "period"],
        indexes=["usage_type"],
        non_nullable=["user_id", "usage_type"],
    ),
    "plan_models": Entity(
        schema=PlanModelItem,
        dynamo_suffix="plan-models",
        pk=["plan_id", "model_id"],
    ),
    # External database connections & sources
    "database_connections": Entity(
        schema=DatabaseConnectionItem,
        dynamo_suffix="database-connections",
        pk=["user_id", "id"],
        indexes=["db_type", "status"],
        text_fields=["encrypted_password"],
        non_nullable=["user_id", "name", "db_type"],
    ),
    "sources": Entity(
        schema=SourceItem,
        dynamo_suffix="sources",
        pk=["user_id", "id"],
        indexes=["source_type", "connection_id"],
        text_fields=["metadata_json", "sql_view_query"],
        non_nullable=["user_id", "name"],
    ),
    "pipeline_sources": Entity(
        schema=PipelineSourceItem,
        dynamo_suffix="pipeline-sources",
        pk=["pipeline_id", "source_id"],
    ),
    "temp_data_tables": Entity(
        schema=TempDataTableItem,
        dynamo_suffix="temp-data-tables",
        pk=["pipeline_id", "id"],
        indexes=["source_id"],
        text_fields=["schema_json"],
    ),
}
