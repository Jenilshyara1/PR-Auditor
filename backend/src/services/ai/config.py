import os

MODEL_TIERS: dict[str, str] = {
    "small": "gpt-5.4-nano",
    "mid": "gpt-5.4-mini",
    "strong": "gpt-5.5",
}

NODE_TIER: dict[str, str] = {
    "planner": "small",
    "style": "small",
    "test_coverage": "small",
    "perf": "mid",
    "security": "strong",
    "critic": "strong",
}

NODE_TIMEOUT_SECONDS: dict[str, int] = {
    "security": 30,
    "style": 30,
    "test_coverage": 30,
    "perf": 30,
}

SPECIALIST_RETRY_COUNT = 1


def langfuse_enabled() -> bool:
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY")) and bool(os.environ.get("LANGFUSE_SECRET_KEY"))


def get_langfuse_callbacks() -> list[object]:
    if not langfuse_enabled():
        return []

    from langfuse.langchain import CallbackHandler

    return [CallbackHandler()]
