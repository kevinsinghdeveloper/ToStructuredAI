"""Specialized repository interface for AI models."""
from abc import abstractmethod
from typing import List
from abstractions.IRepository import IRepository


class IModelRepository(IRepository):

    @abstractmethod
    def find_global_models(self) -> List[dict]:
        pass

    @abstractmethod
    def find_by_user(self, user_id: str) -> List[dict]:
        pass

    @abstractmethod
    def find_by_type(self, user_id: str, model_type: str) -> List[dict]:
        pass
