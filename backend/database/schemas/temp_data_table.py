"""DynamoDB item schema for TempDataTable records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TempDataTableItem:
    pipeline_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    table_name: str = ""
    schema_json: Optional[str] = None  # JSON string of table schema
    row_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None

    def to_item(self) -> dict:
        item = {
            "pipeline_id": self.pipeline_id, "id": self.id,
            "source_id": self.source_id,
            "table_name": self.table_name,
            "schema_json": self.schema_json,
            "row_count": self.row_count,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }
        return {k: v for k, v in item.items() if v is not None}

    def to_api_dict(self) -> dict:
        return {
            "id": self.id,
            "pipelineId": self.pipeline_id,
            "sourceId": self.source_id,
            "tableName": self.table_name,
            "schemaJson": self.schema_json,
            "rowCount": self.row_count,
            "createdAt": self.created_at,
            "expiresAt": self.expires_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "TempDataTableItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
