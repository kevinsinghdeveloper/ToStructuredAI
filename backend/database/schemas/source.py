"""DynamoDB item schema for Source records."""
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SourceItem:
    user_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    source_type: str = "document"  # document | database
    is_queryable: bool = False
    status: str = "pending"  # pending | ready | metadata_extracted | error
    document_id: Optional[str] = None
    connection_id: Optional[str] = None
    table_name: Optional[str] = None
    sql_view_query: Optional[str] = None
    metadata_json: Optional[str] = None  # JSON string of column metadata
    delimiter: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_item(self) -> dict:
        item = {
            "user_id": self.user_id, "id": self.id,
            "name": self.name, "source_type": self.source_type,
            "is_queryable": self.is_queryable, "status": self.status,
            "document_id": self.document_id,
            "connection_id": self.connection_id,
            "table_name": self.table_name,
            "sql_view_query": self.sql_view_query,
            "metadata_json": self.metadata_json,
            "delimiter": self.delimiter,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }
        return {k: v for k, v in item.items() if v is not None}

    def to_api_dict(self) -> dict:
        return {
            "id": self.id, "userId": self.user_id,
            "name": self.name, "sourceType": self.source_type,
            "isQueryable": self.is_queryable, "status": self.status,
            "documentId": self.document_id,
            "connectionId": self.connection_id,
            "tableName": self.table_name,
            "sqlViewQuery": self.sql_view_query,
            "metadataJson": self.metadata_json,
            "delimiter": self.delimiter,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "SourceItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
