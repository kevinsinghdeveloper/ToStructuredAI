"""Unified ModelRepository — wraps any IRepository, backend-agnostic."""
from typing import List, Optional
from abstractions.IRepository import IRepository
from abstractions.IModelRepository import IModelRepository


class ModelRepository(IModelRepository):

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

    # -- Model-specific methods --
    def find_global_models(self) -> List[dict]:
        return self._repo.find_by("user_id", "GLOBAL")

    def find_by_user(self, user_id: str) -> List[dict]:
        return self._repo.find_by("user_id", user_id)

    def find_by_type(self, user_id: str, model_type: str) -> List[dict]:
        models = self._repo.find_by("user_id", user_id)
        return [m for m in models if m.get("model_type") == model_type]
