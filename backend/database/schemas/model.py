"""DynamoDB item schema for Model (AI model configuration) records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelItem:
    user_id: str = ""  # "GLOBAL" for global models, user UUID for user-specific
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    provider: str = ""  # openai, anthropic, etc.
    model_id: str = ""  # gpt-4, claude-3, text-embedding-ada-002, etc.
    model_type: str = "chat"  # chat | embedding
    description: Optional[str] = None
    config: Optional[str] = None  # JSON string for model-specific config
    encrypted_api_key: Optional[str] = None
    temperature: Optional[str] = None  # Stored as string for DynamoDB
    max_tokens: Optional[str] = None
    top_p: Optional[str] = None
    frequency_penalty: Optional[str] = None
    presence_penalty: Optional[str] = None
    is_active: bool = True
    is_global: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "user_id": self.user_id, "id": self.id,
            "name": self.name, "provider": self.provider,
            "model_id": self.model_id, "model_type": self.model_type,
            "description": self.description, "config": self.config,
            "encrypted_api_key": self.encrypted_api_key,
            "temperature": self.temperature, "max_tokens": self.max_tokens,
            "top_p": self.top_p, "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "is_active": self.is_active, "is_global": self.is_global,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self, include_config: bool = False) -> dict:
        import json
        result = {
            "id": self.id, "name": self.name,
            "provider": self.provider.upper() if self.provider else "",
            "modelId": self.model_id,
            "modelType": self.model_type,
            "description": self.description,
            "userId": self.user_id if self.user_id != "GLOBAL" else None,
            "temperature": float(self.temperature) if self.temperature else None,
            "maxTokens": int(self.max_tokens) if self.max_tokens else None,
            "topP": float(self.top_p) if self.top_p else None,
            "frequencyPenalty": float(self.frequency_penalty) if self.frequency_penalty else None,
            "presencePenalty": float(self.presence_penalty) if self.presence_penalty else None,
            "isActive": self.is_active, "isGlobal": self.is_global,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }
        if include_config and self.config:
            try:
                result["config"] = json.loads(self.config)
            except (json.JSONDecodeError, TypeError):
                result["config"] = self.config
        return result

    @classmethod
    def from_item(cls, item: dict) -> "ModelItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
