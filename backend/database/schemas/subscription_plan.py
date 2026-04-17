"""DynamoDB item schema for SubscriptionPlan records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SubscriptionPlanItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""  # "Free", "Basic", "Power", "Enterprise"
    tier: str = "free"  # free | basic | power | enterprise
    stripe_price_id: Optional[str] = None
    stripe_product_id: Optional[str] = None
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    # Document processing limits
    custom_models_limit: int = 0
    monthly_token_limit: int = 0  # 0 = unlimited
    max_file_size_mb: int = 10
    requests_per_day: int = 0  # 0 = unlimited
    # Feature flags
    can_use_metadata: bool = False
    can_use_custom_models: bool = False
    priority_support: bool = False
    # Metadata
    description: Optional[str] = None
    features: Optional[str] = None  # JSON array of feature strings
    is_active: bool = True
    is_default: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "id": self.id, "name": self.name, "tier": self.tier,
            "stripe_price_id": self.stripe_price_id,
            "stripe_product_id": self.stripe_product_id,
            "price_monthly": str(self.price_monthly),
            "price_yearly": str(self.price_yearly),
            "custom_models_limit": self.custom_models_limit,
            "monthly_token_limit": self.monthly_token_limit,
            "max_file_size_mb": self.max_file_size_mb,
            "requests_per_day": self.requests_per_day,
            "can_use_metadata": self.can_use_metadata,
            "can_use_custom_models": self.can_use_custom_models,
            "priority_support": self.priority_support,
            "description": self.description,
            "features": self.features,
            "is_active": self.is_active, "is_default": self.is_default,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        import json
        feature_list = None
        if self.features:
            try:
                feature_list = json.loads(self.features)
            except (json.JSONDecodeError, TypeError):
                feature_list = self.features
        return {
            "id": self.id, "name": self.name, "tier": self.tier,
            "stripePriceId": self.stripe_price_id,
            "stripeProductId": self.stripe_product_id,
            "priceMonthly": self.price_monthly, "priceYearly": self.price_yearly,
            "customModelsLimit": self.custom_models_limit,
            "monthlyTokenLimit": self.monthly_token_limit,
            "maxFileSizeMb": self.max_file_size_mb,
            "requestsPerDay": self.requests_per_day,
            "canUseMetadata": self.can_use_metadata,
            "canUseCustomModels": self.can_use_custom_models,
            "prioritySupport": self.priority_support,
            "description": self.description,
            "features": feature_list, "isActive": self.is_active,
            "isDefault": self.is_default,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "SubscriptionPlanItem":
        data = {k: v for k, v in item.items() if k in cls.__dataclass_fields__}
        if "price_monthly" in data and isinstance(data["price_monthly"], str):
            data["price_monthly"] = float(data["price_monthly"])
        if "price_yearly" in data and isinstance(data["price_yearly"], str):
            data["price_yearly"] = float(data["price_yearly"])
        return cls(**data)
