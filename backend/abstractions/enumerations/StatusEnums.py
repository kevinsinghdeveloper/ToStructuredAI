from enum import Enum


class OrgRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class OrgPlanTier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    POWER = "power"
    ENTERPRISE = "enterprise"


class ProcessingStatusEnum(str, Enum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    EMBEDDING = "embedding"
    READY = "ready"
    ERROR = "error"


class JobStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelTypeEnum(str, Enum):
    CHAT = "chat"
    EMBEDDING = "embedding"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class NotificationType(str, Enum):
    DOCUMENT_PROCESSED = "document_processed"
    DOCUMENT_FAILED = "document_failed"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    USAGE_WARNING = "usage_warning"
    SUBSCRIPTION_UPDATE = "subscription_update"
    SYSTEM = "system"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
