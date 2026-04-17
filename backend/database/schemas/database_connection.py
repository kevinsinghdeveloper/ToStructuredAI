"""DynamoDB item schema for DatabaseConnection records."""
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DatabaseConnectionItem:
    user_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    db_type: str = ""  # postgresql, mysql, mssql
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    encrypted_password: Optional[str] = None
    ssl_enabled: bool = False
    schema_name: str = "public"
    status: str = "untested"  # untested | connected | failed
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_item(self) -> dict:
        item = {
            "user_id": self.user_id, "id": self.id,
            "name": self.name, "db_type": self.db_type,
            "host": self.host, "port": self.port,
            "database_name": self.database_name,
            "username": self.username,
            "encrypted_password": self.encrypted_password,
            "ssl_enabled": self.ssl_enabled,
            "schema_name": self.schema_name,
            "status": self.status,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }
        return {k: v for k, v in item.items() if v is not None}

    def to_api_dict(self) -> dict:
        return {
            "id": self.id, "userId": self.user_id,
            "name": self.name, "dbType": self.db_type,
            "host": self.host, "port": self.port,
            "databaseName": self.database_name,
            "username": self.username,
            "sslEnabled": self.ssl_enabled,
            "schemaName": self.schema_name,
            "status": self.status,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "DatabaseConnectionItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
