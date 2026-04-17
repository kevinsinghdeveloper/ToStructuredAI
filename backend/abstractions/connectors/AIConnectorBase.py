"""Base class for AI connectors."""
from abc import ABC
from typing import Dict, Any


class AIConnectorBase(ABC):
    """Base class for all AI connectors (chat, embeddings, etc.)."""

    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._model = None
        self._provider = config.get("provider") if config else None
        self._model_name = config.get("model_name") if config else None

    def get_config(self) -> Dict[str, Any]:
        return self._config
