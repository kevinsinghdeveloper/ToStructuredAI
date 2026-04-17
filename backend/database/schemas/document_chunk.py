"""DynamoDB item schema for DocumentChunk records.

Stores chunk metadata in DynamoDB; actual vector embeddings live in
an external vector DB (e.g., Pinecone).
"""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DocumentChunkItem:
    document_id: str = ""
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chunk_index: int = 0
    content: str = ""
    chunk_metadata: Optional[str] = None  # JSON string
    vector_id: Optional[str] = None  # ID in external vector DB
    token_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "document_id": self.document_id, "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index, "content": self.content,
            "chunk_metadata": self.chunk_metadata,
            "vector_id": self.vector_id,
            "token_count": self.token_count,
            "created_at": self.created_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        return {
            "chunkId": self.chunk_id,
            "documentId": self.document_id,
            "chunkIndex": self.chunk_index,
            "content": self.content,
            "tokenCount": self.token_count,
            "createdAt": self.created_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "DocumentChunkItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
