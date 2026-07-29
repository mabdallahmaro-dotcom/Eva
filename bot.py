import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .handlers.basic import BasicHandler
from .memory import MemoryStore
from .services.ai_provider import AIProvider
from .config import Settings

logger = logging.getLogger(__name__)


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled exception while processing update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Sorry, something went wrong on my end. Please try again."
            )
        except Exception:  # pragma: no cover - best effort notification
            logger.exception("Failed to notify user about the error")


def build_application(settings: Settings, provider: AIProvider, memory_store: MemoryStore) -> Application:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required to start Eva AI.")

    application = Application.builder().token(settings.bot_token).build()
    handler = BasicHandler(provider=provider, memory_store=memory_store, settings=settings)

    application.add_handler(CommandHandler("start", handler.start))
    application.add_handler(CommandHandler("help", handler.help))
    application.add_handler(CommandHandler("search", handler.search))
    application.add_handler(CommandHandler("remind", handler.remind))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handler.handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, handler.handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handler.handle_voice))
    application.add_error_handler(_on_error)

    return application
