"""DynamoDB item schema for Query (Q&A history) records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QueryItem:
    user_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: Optional[str] = None
    question: str = ""
    answer: Optional[str] = None
    context: Optional[str] = None  # Retrieved context used for answer
    query_metadata: Optional[str] = None  # JSON string
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "user_id": self.user_id, "id": self.id,
            "pipeline_id": self.pipeline_id,
            "question": self.question, "answer": self.answer,
            "context": self.context,
            "query_metadata": self.query_metadata,
            "created_at": self.created_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        return {
            "id": self.id, "userId": self.user_id,
            "pipelineId": self.pipeline_id,
            "question": self.question, "answer": self.answer,
            "context": self.context,
            "queryMetadata": self.query_metadata,
            "createdAt": self.created_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "QueryItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
