"""LangChain-based embeddings service supporting multiple providers."""
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from abstractions.IServiceManagerBase import IServiceManagerBase
from abstractions.connectors.EmbeddingsConnectorBase import EmbeddingsConnectorBase


class EmbeddingsService(IServiceManagerBase, EmbeddingsConnectorBase):
    """
    Embeddings service supporting OpenAI and HuggingFace providers.
    Generates vector embeddings for text chunks used in RAG retrieval.
    """

    def __init__(self, service_manager_config: Dict[str, Any]):
        IServiceManagerBase.__init__(self, service_manager_config)
        EmbeddingsConnectorBase.__init__(self, service_manager_config.get("config", {}))
        self._batch_size = service_manager_config.get("config", {}).get("batch_size", 32)

    def configure(self):
        config = self.get_config()
        provider = config.get("provider")
        model_name = config.get("model_name")
        api_key = config.get("api_key")

        if not provider:
            raise ValueError("Embedding provider must be specified")
        if not model_name:
            raise ValueError("Embedding model name must be specified")

        provider = provider.lower()
        if provider == "openai":
            if not api_key:
                raise ValueError("Embedding provider requires api_key")
            self._configure_openai(model_name, api_key)
        else:
            raise ValueError(f"Unsupported embeddings provider: {provider}")

    def _configure_openai(self, model_name: str, api_key: str):
        from langchain_openai import OpenAIEmbeddings
        self._model = OpenAIEmbeddings(model=model_name, openai_api_key=api_key)
        if "ada-002" in model_name or "3-small" in model_name:
            self._dimensions = 1536
        elif "3-large" in model_name:
            self._dimensions = 3072
        else:
            self._dimensions = 1536

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def _embed_with_retry(self, text: str) -> List[float]:
        return self._model.embed_query(text)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def _embed_batch_with_retry(self, texts: List[str]) -> List[List[float]]:
        return self._model.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._embed_with_retry(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed_batch_with_retry(texts)

    def get_dimensions(self) -> Optional[int]:
        return self._dimensions

    def create_embedding(self, text: str) -> List[float]:
        return self.embed_query(text)

    def create_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self.embed_documents(texts)

    def run_task(self, request: Dict[str, Any]) -> Any:
        task_type = request.get("task_type")
        if task_type == "embedding":
            return self.embed_query(request.get("text", ""))
        elif task_type == "batch_embedding":
            return self.embed_documents(request.get("texts", []))
        else:
            raise ValueError(f"Unknown task type: {task_type}")
