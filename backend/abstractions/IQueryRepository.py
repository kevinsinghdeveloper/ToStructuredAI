"""Specialized repository interface for Q&A queries."""
from abc import abstractmethod
from typing import List
from abstractions.IRepository import IRepository


class IQueryRepository(IRepository):

    @abstractmethod
    def find_by_user(self, user_id: str) -> List[dict]:
        pass

    @abstractmethod
    def find_by_pipeline(self, pipeline_id: str) -> List[dict]:
        pass
