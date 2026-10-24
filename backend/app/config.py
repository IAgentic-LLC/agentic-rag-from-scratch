"""All settings in one place. Override any of them with environment variables (see .env.example)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = Path(os.getenv("DOCS_DIR", ROOT / "data" / "docs"))
INDEX_PATH = Path(os.getenv("INDEX_PATH", ROOT / "data" / "index.json"))

# Models are "provider:model". Two kinds of provider:
#   Native LangChain integrations (best feature coverage):
#     google_genai:gemini-3.8-flash    GOOGLE_API_KEY
#     openai:gpt-5.4-mini              OPENAI_API_KEY
#     anthropic:claude-sonnet-5-5      ANTHROPIC_API_KEY
#     deepseek:deepseek-flash          DEEPSEEK_API_KEY   (the old name deepseek-v4-flash still works but is retired)
#   OpenAI-compatible endpoints (one client for many providers, see OPENAI_COMPATIBLE below):
#     qwen:qwen3.8-flash               DASHSCOPE_API_KEY
#     gemini_compat:gemini-3.8-flash   GOOGLE_API_KEY
#     local:qwen3.8-27b                (Ollama, vLLM or LM Studio on your machine)
CHAT_MODEL = os.getenv("CHAT_MODEL", "google_genai:gemini-3.8-flash")       # writes the answer
FAST_MODEL = os.getenv("FAST_MODEL", "google_genai:gemini-3.5-flash-lite")  # routes, grades, rewrites, checks

# Embeddings: "google:gemini-embedding-001" or "openai:text-embedding-3-small".
# Claude and DeepSeek have no embedding API, so keep Gemini or OpenAI embeddings when you swap chat models.
EMBED_MODEL = os.getenv("EMBED_MODEL", "google:gemini-embedding-001")

# Endpoints that speak the OpenAI Chat Completions API: name -> (base_url, api key env var)
OPENAI_COMPATIBLE = {
    "qwen": (os.getenv("QWEN_BASE_URL", "https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1"), "DASHSCOPE_API_KEY"),
    "deepseek_compat": ("https://api.deepseek.com", "DEEPSEEK_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),   # hosts qwen/qwen3.8-27b (preview) and others
    "gemini_compat": ("https://generativelanguage.googleapis.com/v1beta/openai/", "GOOGLE_API_KEY"),
    "local": (os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1"), "LOCAL_API_KEY"),
}

# Extra constructor arguments per provider. DeepSeek V4 runs in thinking mode by default and that mode rejects the forced
# tool choice the graders use ("Thinking mode does not support this tool_choice"), so it is switched off for the small decisions.
PROVIDER_EXTRA = {
    "deepseek": {"extra_body": {"thinking": {"type": "disabled"}}},
    "deepseek_compat": {"extra_body": {"thinking": {"type": "disabled"}}},
}

# How graders ask for structured output. "function_calling" works on every provider that supports tools.
# "json_schema" is stricter where supported (OpenAI, Gemini, Qwen). Override per provider here.
STRUCTURED_METHOD = {"default": "function_calling", "openai": "json_schema"}

# The eval judge. Ideally a different provider from CHAT_MODEL, so the model doesn't grade itself.
JUDGE_MODEL = os.getenv("JUDGE_MODEL", CHAT_MODEL)

TOP_K = 6              # chunks handed to the grader
RRF_K = 60             # reciprocal rank fusion constant (Cormack et al., 2009)
MAX_REWRITES = 2       # how many times the agent may rewrite its search query
MAX_REGENERATIONS = 1  # how many times it may retry an answer that failed the grounding check

# USD per 1M tokens (input, output). Only used for the live cost counter. Check your provider's current prices.
PRICES = {
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gpt-5.4-mini": (0.25, 2.00),
    # DeepSeek list price at PEAK hours (01-04 and 06-10 UTC, Mon-Fri); off-peak is half: (0.15, 0.60). Source: api-docs.deepseek.com/quick_start/pricing, 2026-10-22.
    "deepseek-flash": (0.30, 1.20),
    "deepseek-v4-flash": (0.30, 1.20),
}
