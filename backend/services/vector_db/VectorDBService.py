"""Abstract vector database service for storing and querying embeddings."""
import os
from typing import List, Dict, Any, Optional
from abstractions.IServiceManagerBase import IServiceManagerBase


class VectorDBService(IServiceManagerBase):
    """
    Vector DB service wrapping Pinecone (or another provider).
    Handles upsert, query, and delete operations for document embeddings.
    """

    def __init__(self, config: dict = None):
        super().__init__(config or {})
        self._index = None
        self._provider = (config or {}).get("provider", "pinecone")

    def configure(self, **kwargs) -> None:
        pass

    def initialize(self):
        if self._provider == "pinecone":
            self._init_pinecone()

    def _init_pinecone(self):
        try:
            from pinecone import Pinecone
            api_key = os.getenv("PINECONE_API_KEY", "")
            index_name = os.getenv("PINECONE_INDEX_NAME", "tostructured")

            if not api_key:
                return  # Skip in local dev

            pc = Pinecone(api_key=api_key)
            self._index = pc.Index(index_name)
        except ImportError:
            pass  # pinecone not installed

    def upsert_vectors(
        self, vectors: List[Dict[str, Any]], namespace: str = ""
    ) -> int:
        """
        Upsert vectors into the vector DB.

        Args:
            vectors: List of dicts with 'id', 'values' (embedding), 'metadata'
            namespace: Namespace/partition key (e.g., document_id)

        Returns:
            Number of vectors upserted
        """
        if not self._index:
            return 0

        batch_size = 100
        total = 0
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            self._index.upsert(vectors=batch, namespace=namespace)
            total += len(batch)
        return total

    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        namespace: str = "",
        filter: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query for similar vectors.

        Returns:
            List of matches with 'id', 'score', 'metadata'
        """
        if not self._index:
            return []

        results = self._index.query(
            vector=vector, top_k=top_k, namespace=namespace,
            filter=filter, include_metadata=True,
        )
        return [
            {"id": m.id, "score": m.score, "metadata": m.metadata or {}}
            for m in results.matches
        ]

    def delete_by_namespace(self, namespace: str) -> bool:
        """Delete all vectors in a namespace (e.g., for a document)."""
        if not self._index:
            return False
        self._index.delete(delete_all=True, namespace=namespace)
        return True

    def delete_by_ids(self, ids: List[str], namespace: str = "") -> bool:
        """Delete specific vectors by ID."""
        if not self._index:
            return False
        self._index.delete(ids=ids, namespace=namespace)
        return True

    def run_task(self, request: Dict[str, Any]) -> Any:
        task_type = request.get("task_type")
        if task_type == "upsert":
            return self.upsert_vectors(request.get("vectors", []), request.get("namespace", ""))
        elif task_type == "query":
            return self.query(
                request.get("vector", []), request.get("top_k", 5),
                request.get("namespace", ""), request.get("filter"),
            )
        elif task_type == "delete":
            return self.delete_by_namespace(request.get("namespace", ""))
        raise ValueError(f"Unknown task type: {task_type}")
