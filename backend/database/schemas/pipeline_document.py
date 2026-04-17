"""DynamoDB item schema for PipelineDocument (many-to-many link) records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class PipelineDocumentItem:
    pipeline_id: str = ""
    document_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "document_id": self.document_id,
            "id": self.id,
            "created_at": self.created_at,
        }

    def to_api_dict(self) -> dict:
        return {
            "id": self.id,
            "pipelineId": self.pipeline_id,
            "documentId": self.document_id,
            "createdAt": self.created_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "PipelineDocumentItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
