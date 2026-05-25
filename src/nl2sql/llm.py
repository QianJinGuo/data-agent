"""Configurable LLM wrapper supporting openai/anthropic/local endpoints."""
from typing import Literal
from langchain_openai import ChatOpenAI


def build_llm(
    provider: Literal["openai", "anthropic", "local"] = "openai",
    model: str = "gpt-4o",
    api_key: str = "not-set",
    base_url: str = "https://api.openai.com/v1",
    temperature: float = 0.0,
):
    """Build an LLM client based on provider.

    provider: "openai" (default), "anthropic", or "local" (Ollama-compatible)
    model: model name (default gpt-4o)
    api_key: API key (not-set for local providers)
    base_url: API base URL
    temperature: sampling temperature
    """
    if provider in ("openai", "anthropic"):
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
        )
    elif provider == "local":
        return ChatOpenAI(
            model=model,
            api_key="not-needed",
            base_url=f"{base_url}/v1",
            temperature=temperature,
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")