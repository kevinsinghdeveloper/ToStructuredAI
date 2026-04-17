"""Specialized repository interface for temp data tables."""
from abc import abstractmethod
from typing import List
from abstractions.IRepository import IRepository


class ITempDataTableRepository(IRepository):

    @abstractmethod
    def find_by_pipeline(self, pipeline_id: str) -> List[dict]:
        pass

    @abstractmethod
    def find_by_source(self, source_id: str) -> List[dict]:
        pass
