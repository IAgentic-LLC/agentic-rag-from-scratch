"""Model factory. Swapping providers is a change of environment variables, not code."""
import os
from functools import lru_cache

from langchain.chat_models import init_chat_model

from . import config

_provider_of: dict[int, str] = {}   # model object id -> provider name, used by structured()


@lru_cache
def chat_model(model_id: str):
    """'provider:model' -> a LangChain chat model. Native integrations first, then any OpenAI-compatible endpoint."""
    provider, name = model_id.split(":", 1)
    extra = config.PROVIDER_EXTRA.get(provider, {})
    if provider in config.OPENAI_COMPATIBLE:
        from langchain_openai import ChatOpenAI
        base_url, key_env = config.OPENAI_COMPATIBLE[provider]
        model = ChatOpenAI(model=name, base_url=base_url, api_key=os.getenv(key_env, "not-needed"), temperature=0, **extra)
    else:
        model = init_chat_model(model_id, temperature=0, **extra)
    _provider_of[id(model)] = provider
    return model


def structured(model, schema):
    """Ask a model for a Pydantic object, using the method that provider handles best."""
    provider = _provider_of.get(id(model), "default")
    method = config.STRUCTURED_METHOD.get(provider, config.STRUCTURED_METHOD["default"])
    return model.with_structured_output(schema, method=method)


@lru_cache
def embedder(model_id: str = config.EMBED_MODEL):
    provider, name = model_id.split(":", 1)
    if provider == "google":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model=f"models/{name}")
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=name)
    if provider in config.OPENAI_COMPATIBLE:            # e.g. Qwen or a local embedding model
        from langchain_openai import OpenAIEmbeddings
        base_url, key_env = config.OPENAI_COMPATIBLE[provider]
        return OpenAIEmbeddings(model=name, base_url=base_url, api_key=os.getenv(key_env, "not-needed"),
                                check_embedding_ctx_length=False)
    raise ValueError(f"Unknown embedding provider: {provider}")


def cost_usd(usage_by_model: dict) -> float:
    total = 0.0
    for model, usage in usage_by_model.items():
        price_in, price_out = next((p for k, p in config.PRICES.items() if k in model), (0.0, 0.0))
        total += usage.get("input_tokens", 0) / 1e6 * price_in + usage.get("output_tokens", 0) / 1e6 * price_out
    return total
