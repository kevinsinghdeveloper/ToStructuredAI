"""Base class for embeddings AI connectors."""
from abc import abstractmethod
from typing import List, Optional
from abstractions.connectors.AIConnectorBase import AIConnectorBase


class EmbeddingsConnectorBase(AIConnectorBase):

    def __init__(self, config=None):
        super().__init__(config)
        self._dimensions = None

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def get_dimensions(self) -> Optional[int]:
        pass

    @abstractmethod
    def create_embedding(self, text: str) -> List[float]:
        pass

    def get_embeddings(self, text: str) -> List[float]:
        return self.embed_query(text)

    def create_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self.embed_documents(texts)
