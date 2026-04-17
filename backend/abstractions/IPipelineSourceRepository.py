"""Specialized repository interface for pipeline-source links."""
from abc import abstractmethod
from typing import List
from abstractions.IRepository import IRepository


class IPipelineSourceRepository(IRepository):

    @abstractmethod
    def find_by_pipeline(self, pipeline_id: str) -> List[dict]:
        pass

    @abstractmethod
    def find_by_source(self, source_id: str) -> List[dict]:
        pass
