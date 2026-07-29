from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..memory import MemoryStore
from ..services.ai_provider import AIProvider
from ..services.files import DocumentService
from ..services.ocr import OCRService
from ..services.vision import VisionService
from ..services.voice import VoiceService
from ..services.web_search import WebSearchService

logger = logging.getLogger(__name__)


class BasicHandler:
    def __init__(self, provider: AIProvider, memory_store: MemoryStore, settings: Settings) -> None:
        self.provider = provider
        self.memory_store = memory_store
        self.settings = settings
        self.web_search = WebSearchService()
        self.document_service = DocumentService()
        self.ocr_service = OCRService()
        self.vision_service = VisionService()
        self.voice_service = VoiceService()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Hello! I am Eva AI. Send me a message or a document and I will help.")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Commands: /start, /help, /search, /remind\n"
            "I support text, documents, photos, voice, reminders, and AI responses."
        )

    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = " ".join(context.args) if context.args else ""
        if not query:
            await update.message.reply_text("Usage: /search <query>")
            return
        try:
            if self.settings.web_search_enabled:
                answer = self.web_search.search(query, api_key=self.settings.web_search_api_key)
            else:
                answer = self.provider.generate(f"Search the web for: {query}")
        except Exception as exc:  # pragma: no cover - runtime safeguard
            logger.exception("search failed", exc_info=exc)
            answer = f"Search is unavailable right now: {exc}"
        await update.message.reply_text(answer)

    async def remind(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("Usage: /remind <minutes> <message>")
            return
        try:
            minutes = int(context.args[0])
            message = " ".join(context.args[1:]) or "Reminder"
            due_at = datetime.utcnow() + timedelta(minutes=minutes)
            reminder = self.memory_store.add_reminder(
                user_id=str(update.effective_user.id),
                chat_id=str(update.effective_chat.id),
                message=message,
                due_at=due_at,
            )
            await update.message.reply_text(f"Reminder saved for {minutes} minute(s): {message}")
        except ValueError:
            await update.message.reply_text("Minutes must be an integer.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = update.message.text or ""
        if not text:
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        try:
            self.memory_store.append_memory(str(update.effective_user.id), "user", text)
            history = [
                {"role": record.role, "content": record.content}
                for record in reversed(self.memory_store.get_recent_messages(str(update.effective_user.id), limit=10))
            ]
            answer = self.provider.generate(
                text,
                system_prompt="You are Eva AI, a helpful assistant.",
                history=history[:-1] if history else None,
            )
            self.memory_store.append_memory(str(update.effective_user.id), "assistant", answer)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            logger.exception("handle_message failed", exc_info=exc)
            answer = f"Sorry, I couldn't process that message right now: {exc}"

        await update.message.reply_text(answer)

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        document = update.message.document
        if not document:
            return

        file = await context.bot.get_file(document.file_id)
        suffix = Path(document.file_name or "document").suffix.lower() or ".txt"
        with NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_path = temp_file.name
            await file.download_to_drive(temp_path)

        try:
            extracted_text = self.document_service.extract_text_from_file(temp_path)
            preview = extracted_text[:4000] if extracted_text else "No readable text found."
            answer = self.provider.generate(
                f"Summarize the following document content:\n{preview}",
                system_prompt="You are Eva AI. Deliver a concise and helpful summary.",
            )
            await update.message.reply_text(answer)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            logger.exception("document processing failed", exc_info=exc)
            await update.message.reply_text(f"Document processing failed: {exc}")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        photo = update.message.photo[-1] if update.message.photo else None
        if not photo:
            return

        file = await context.bot.get_file(photo.file_id)
        with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_path = temp_file.name
            await file.download_to_drive(temp_path)

        try:
            text = self.ocr_service.extract_text(temp_path)
            if text.strip():
                answer = self.provider.generate(
                    f"Analyze the following image text:\n{text[:3000]}",
                    system_prompt="You are Eva AI. Describe the image content clearly.",
                )
            else:
                answer = self.vision_service.analyze_image(temp_path)
            await update.message.reply_text(answer)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            logger.exception("photo processing failed", exc_info=exc)
            await update.message.reply_text(f"Image analysis failed: {exc}")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        voice = update.message.voice
        if not voice:
            return

        file = await context.bot.get_file(voice.file_id)
        with NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
            temp_path = temp_file.name
            await file.download_to_drive(temp_path)

        try:
            transcript = self.voice_service.transcribe(temp_path)
            await update.message.reply_text(transcript)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            logger.exception("voice processing failed", exc_info=exc)
            await update.message.reply_text(f"Voice transcription failed: {exc}")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
