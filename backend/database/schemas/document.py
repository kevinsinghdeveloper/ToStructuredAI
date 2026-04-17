"""DynamoDB item schema for Document records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DocumentItem:
    user_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    embedding_model_id: Optional[str] = None
    filename: str = ""
    original_filename: str = ""
    file_path: str = ""
    file_size: int = 0
    mime_type: Optional[str] = None
    status: str = "uploaded"  # uploaded | extracting | embedding | ready | error
    extracted_text: Optional[str] = None
    doc_metadata: Optional[str] = None  # JSON string
    chunk_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "user_id": self.user_id, "id": self.id,
            "embedding_model_id": self.embedding_model_id,
            "filename": self.filename, "original_filename": self.original_filename,
            "file_path": self.file_path, "file_size": self.file_size,
            "mime_type": self.mime_type, "status": self.status,
            "extracted_text": self.extracted_text,
            "doc_metadata": self.doc_metadata,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        return {
            "id": self.id, "userId": self.user_id,
            "embeddingModelId": self.embedding_model_id,
            "fileName": self.original_filename or self.filename,
            "fileType": self.mime_type or "Unknown",
            "fileSize": self.file_size,
            "status": self.status,
            "chunkCount": self.chunk_count,
            "uploadedAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "DocumentItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
