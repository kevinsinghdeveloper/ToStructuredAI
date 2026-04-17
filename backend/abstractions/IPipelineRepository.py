"""Specialized repository interface for pipelines."""
from abc import abstractmethod
from typing import List
from abstractions.IRepository import IRepository


class IPipelineRepository(IRepository):

    @abstractmethod
    def find_by_user(self, user_id: str) -> List[dict]:
        pass

    @abstractmethod
    def find_by_status(self, user_id: str, status: str) -> List[dict]:
        pass
