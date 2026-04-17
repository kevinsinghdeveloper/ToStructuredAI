"""DynamoDB item schema for PipelineSource records (many-to-many link)."""
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class PipelineSourceItem:
    pipeline_id: str = ""
    source_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "source_id": self.source_id,
            "created_at": self.created_at,
        }

    def to_api_dict(self) -> dict:
        return {
            "pipelineId": self.pipeline_id,
            "sourceId": self.source_id,
            "createdAt": self.created_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "PipelineSourceItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
