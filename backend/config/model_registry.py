"""Model configuration registry for LLM and embedding models."""
from typing import Dict, Any, Optional


LLM_MODELS = {
    "gpt-4": {
        "provider": "openai", "model_name": "gpt-4", "display_name": "GPT-4",
        "default_config": {"temperature": 0.7, "max_tokens": 2000, "top_p": 1.0},
    },
    "gpt-4-turbo": {
        "provider": "openai", "model_name": "gpt-4-turbo-preview", "display_name": "GPT-4 Turbo",
        "default_config": {"temperature": 0.7, "max_tokens": 4096, "top_p": 1.0},
    },
    "gpt-4-turbo-preview": {
        "provider": "openai", "model_name": "gpt-4-turbo-preview", "display_name": "GPT-4 Turbo Preview",
        "default_config": {"temperature": 0.7, "max_tokens": 4096, "top_p": 1.0},
    },
    "gpt-3.5-turbo": {
        "provider": "openai", "model_name": "gpt-3.5-turbo", "display_name": "GPT-3.5 Turbo",
        "default_config": {"temperature": 0.7, "max_tokens": 2000, "top_p": 1.0},
    },
    "claude-3-opus-20240229": {
        "provider": "anthropic", "model_name": "claude-3-opus-20240229", "display_name": "Claude 3 Opus",
        "default_config": {"temperature": 0.7, "max_tokens": 4000, "top_p": 1.0},
    },
    "claude-3-sonnet-20240229": {
        "provider": "anthropic", "model_name": "claude-3-sonnet-20240229", "display_name": "Claude 3 Sonnet",
        "default_config": {"temperature": 0.7, "max_tokens": 4000, "top_p": 1.0},
    },
    "claude-3-haiku-20240307": {
        "provider": "anthropic", "model_name": "claude-3-haiku-20240307", "display_name": "Claude 3 Haiku",
        "default_config": {"temperature": 0.7, "max_tokens": 4000, "top_p": 1.0},
    },
}

EMBEDDING_MODELS = {
    "text-embedding-ada-002": {
        "provider": "openai", "model_name": "text-embedding-ada-002",
        "display_name": "OpenAI Ada 002", "dimensions": 1536, "default_config": {},
    },
    "text-embedding-3-small": {
        "provider": "openai", "model_name": "text-embedding-3-small",
        "display_name": "OpenAI Embedding 3 Small", "dimensions": 1536, "default_config": {},
    },
    "text-embedding-3-large": {
        "provider": "openai", "model_name": "text-embedding-3-large",
        "display_name": "OpenAI Embedding 3 Large", "dimensions": 3072, "default_config": {},
    },
}


def get_llm_config(model_id: str, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    normalized = model_id.lower().replace("_", "-")
    if normalized not in LLM_MODELS:
        raise ValueError(f"Unknown LLM model: {model_id}. Available: {list(LLM_MODELS.keys())}")
    cfg = LLM_MODELS[normalized].copy()
    gen = cfg["default_config"].copy()
    if custom_config:
        gen.update(custom_config)
    return {"provider": cfg["provider"], "model_name": cfg["model_name"], "gen_config": gen}


def get_embedding_config(model_id: str, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    normalized = model_id.lower().replace("_", "-")
    if normalized not in EMBEDDING_MODELS:
        raise ValueError(f"Unknown embedding model: {model_id}. Available: {list(EMBEDDING_MODELS.keys())}")
    cfg = EMBEDDING_MODELS[normalized].copy()
    config = cfg["default_config"].copy()
    if custom_config:
        config.update(custom_config)
    return {"provider": cfg["provider"], "model_name": cfg["model_name"], **config}


def get_model_info(model_id: str, model_type: str = "llm") -> Optional[Dict[str, Any]]:
    normalized = model_id.lower().replace("_", "-")
    if model_type == "llm":
        return LLM_MODELS.get(normalized)
    elif model_type == "embedding":
        return EMBEDDING_MODELS.get(normalized)
    return None


def list_available_models(model_type: str = "llm") -> list:
    if model_type == "llm":
        return list(LLM_MODELS.keys())
    elif model_type == "embedding":
        return list(EMBEDDING_MODELS.keys())
    return []


def get_provider_for_model(model_id: str) -> Optional[str]:
    normalized = model_id.lower().replace("_", "-")
    if normalized in LLM_MODELS:
        return LLM_MODELS[normalized]["provider"]
    if normalized in EMBEDDING_MODELS:
        return EMBEDDING_MODELS[normalized]["provider"]
    return None
