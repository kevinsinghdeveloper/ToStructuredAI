"""Unified PipelineSourceRepository — wraps any IRepository, backend-agnostic."""
from typing import List, Optional
from abstractions.IRepository import IRepository
from abstractions.IPipelineSourceRepository import IPipelineSourceRepository


class PipelineSourceRepository(IPipelineSourceRepository):

    def __init__(self, repo: IRepository):
        self._repo = repo

    def __getattr__(self, name):
        return getattr(self._repo, name)

    # -- IRepository delegation --
    def get_by_id(self, id: str) -> Optional[dict]:
        return self._repo.get_by_id(id)

    def get_by_key(self, key: dict) -> Optional[dict]:
        return self._repo.get_by_key(key)

    def create(self, item: dict) -> dict:
        return self._repo.create(item)

    def upsert(self, item: dict) -> dict:
        return self._repo.upsert(item)

    def update(self, id: str, fields: dict) -> Optional[dict]:
        return self._repo.update(id, fields)

    def update_if(self, id: str, fields: dict, conditions: dict) -> bool:
        return self._repo.update_if(id, fields, conditions)

    def delete(self, id: str) -> bool:
        return self._repo.delete(id)

    def delete_by_key(self, key: dict) -> bool:
        return self._repo.delete_by_key(key)

    def delete_where(self, field: str, value) -> int:
        return self._repo.delete_where(field, value)

    def list_all(self, **filters) -> list:
        return self._repo.list_all(**filters)

    def find_by(self, field: str, value) -> list:
        return self._repo.find_by(field, value)

    def count(self, **filters) -> int:
        return self._repo.count(**filters)

    # -- PipelineSource-specific methods --
    def find_by_pipeline(self, pipeline_id: str) -> List[dict]:
        return self._repo.find_by("pipeline_id", pipeline_id)

    def find_by_source(self, source_id: str) -> List[dict]:
        return self._repo.find_by("source_id", source_id)
