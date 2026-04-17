"""DynamoDB item schema for Output (pipeline execution result) records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OutputItem:
    pipeline_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    output_data: str = ""  # JSON string of structured output
    file_path: Optional[str] = None
    format: Optional[str] = None  # json | csv | excel
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "pipeline_id": self.pipeline_id, "id": self.id,
            "output_data": self.output_data,
            "file_path": self.file_path,
            "format": self.format,
            "created_at": self.created_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        import json
        data = self.output_data
        try:
            data = json.loads(self.output_data)
        except (json.JSONDecodeError, TypeError):
            pass
        return {
            "id": self.id,
            "pipelineId": self.pipeline_id,
            "outputData": data,
            "filePath": self.file_path,
            "format": self.format,
            "createdAt": self.created_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "OutputItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
