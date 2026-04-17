"""Specialized repository interface for sources."""
from abc import abstractmethod
from typing import List
from abstractions.IRepository import IRepository


class ISourceRepository(IRepository):

    @abstractmethod
    def find_by_user(self, user_id: str) -> List[dict]:
        pass

    @abstractmethod
    def find_by_connection(self, connection_id: str) -> List[dict]:
        pass

    @abstractmethod
    def find_queryable(self, user_id: str) -> List[dict]:
        pass
