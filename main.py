from __future__ import annotations

import logging
import os

from app.bot import build_application
from app.config import settings
from app.database import init_db
from app.logging_setup import configure_logging
from app.memory import MemoryStore
from app.services.ai_provider import (
    GeminiProvider,
    OpenAICompatibleProvider,
)


def main() -> None:
    configure_logging()
    init_db()

    provider_name = (settings.ai_provider or "gemini").lower()

    if provider_name == "gemini":
        logging.info("Using Gemini Provider")

        provider = GeminiProvider(
            api_key=settings.ai_api_key or os.getenv("AI_API_KEY", ""),
            model=settings.ai_model or os.getenv("AI_MODEL", "gemini-2.5-flash"),
        )

    else:
        logging.info("Using OpenAI Compatible Provider")

        provider = OpenAICompatibleProvider(
            api_key=settings.ai_api_key or os.getenv("OPENAI_API_KEY", ""),
            base_url=settings.ai_base_url
            or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model=settings.ai_model,
        )

    memory_store = MemoryStore()

    app = build_application(
        settings=settings,
        provider=provider,
        memory_store=memory_store,
    )

    logging.info("Starting Eva AI Bot...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
