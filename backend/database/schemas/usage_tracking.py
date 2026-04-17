"""DynamoDB item schema for UsageTracking records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UsageTrackingItem:
    user_id: str = ""
    period: str = ""  # Format: "YYYY-MM" for monthly tracking
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_id: Optional[str] = None
    usage_type: str = ""  # tokens | api_request | file_upload
    tokens_used: int = 0
    file_size_mb: Optional[str] = None  # Decimal as string
    endpoint: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "user_id": self.user_id, "period": self.period,
            "id": self.id, "model_id": self.model_id,
            "usage_type": self.usage_type,
            "tokens_used": self.tokens_used,
            "file_size_mb": self.file_size_mb,
            "endpoint": self.endpoint,
            "timestamp": self.timestamp,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        return {
            "id": self.id, "userId": self.user_id,
            "period": self.period,
            "modelId": self.model_id,
            "usageType": self.usage_type,
            "tokensUsed": self.tokens_used,
            "fileSizeMb": float(self.file_size_mb) if self.file_size_mb else 0.0,
            "endpoint": self.endpoint,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_item(cls, item: dict) -> "UsageTrackingItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
