"""DynamoDB item schema for Pipeline records."""
import uuid
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PipelineItem:
    user_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_id: str = ""
    embedding_model_id: str = ""
    name: str = ""
    description: Optional[str] = None
    pipeline_type: Optional[str] = None  # e.g., "document_explore"
    config: Optional[str] = None  # JSON string for pipeline configuration
    prompt_template: Optional[str] = None
    output_schema: Optional[str] = None  # JSON schema for structured output
    status: str = "pending"  # pending | processing | completed | failed
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "user_id": self.user_id, "id": self.id,
            "model_id": self.model_id,
            "embedding_model_id": self.embedding_model_id,
            "name": self.name, "description": self.description,
            "pipeline_type": self.pipeline_type,
            "config": self.config,
            "prompt_template": self.prompt_template,
            "output_schema": self.output_schema,
            "status": self.status,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self, document_ids: list = None) -> dict:
        field_values = {}
        if self.config:
            try:
                config_dict = json.loads(self.config)
                field_values = config_dict.get("field_values", {})
            except (json.JSONDecodeError, TypeError):
                pass
        return {
            "id": self.id, "userId": self.user_id,
            "modelId": self.model_id,
            "embeddingModelId": self.embedding_model_id,
            "name": self.name, "description": self.description,
            "pipelineType": self.pipeline_type,
            "fieldValues": field_values,
            "documentIds": document_ids or [],
            "config": self.config,
            "promptTemplate": self.prompt_template,
            "outputSchema": self.output_schema,
            "status": self.status,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "PipelineItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
