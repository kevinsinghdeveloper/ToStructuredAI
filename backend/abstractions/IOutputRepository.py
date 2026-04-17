"""Specialized repository interface for pipeline outputs."""
from abc import abstractmethod
from typing import List
from abstractions.IRepository import IRepository


class IOutputRepository(IRepository):

    @abstractmethod
    def find_by_pipeline(self, pipeline_id: str) -> List[dict]:
        pass
