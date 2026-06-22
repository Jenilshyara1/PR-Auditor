from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from src.services.ai.config import MODEL_TIERS

# Reasoning-style models (e.g. the "strong" tier) only support the default
# temperature and reject an explicit override.
TIERS_WITHOUT_CUSTOM_TEMPERATURE = {"strong"}


def get_chat_model(tier: str) -> BaseChatModel:
    if tier in TIERS_WITHOUT_CUSTOM_TEMPERATURE:
        return ChatOpenAI(model=MODEL_TIERS[tier], temperature=1)
    return ChatOpenAI(model=MODEL_TIERS[tier], temperature=0)
