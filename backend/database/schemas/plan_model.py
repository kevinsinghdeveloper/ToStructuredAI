"""DynamoDB item schema for PlanModel (plan-to-model mapping) records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class PlanModelItem:
    plan_id: str = ""
    model_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "model_id": self.model_id,
            "id": self.id,
            "created_at": self.created_at,
        }

    def to_api_dict(self) -> dict:
        return {
            "id": self.id,
            "planId": self.plan_id,
            "modelId": self.model_id,
            "createdAt": self.created_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "PlanModelItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
