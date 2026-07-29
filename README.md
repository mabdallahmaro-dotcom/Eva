# Eva AI

Eva AI is a production-ready Telegram assistant built with Python 3.12. It provides a modular architecture with SQLite-backed memory, an AI provider abstraction, support for OpenAI-compatible APIs, document and image handling helpers, reminders, logging, Docker packaging, and deployment targets for Render and Railway.

## Features
- Telegram bot experience with commands and message handling
- SQLite-powered memory and reminder storage
- AI provider abstraction with OpenAI-compatible support and graceful offline fallbacks
- Document helpers for PDF, Word, and Excel read/write workflows
- OCR and image analysis support for photos and screenshots
- Voice-message transcription hooks for audio uploads
- Structured logging and environment-based configuration
- Docker, GitHub Actions, Render, and Railway deployment files

## Project structure
- app/config.py: environment and settings management
- app/database.py: SQLite schema and initialization
- app/memory.py: memory and reminder persistence
- app/bot.py: Telegram application wiring
- app/handlers/basic.py: user command and message handlers
- app/services: provider, file, OCR, vision, voice, and web search services

## Quick start
1. Create a virtual environment with Python 3.12.
2. Install dependencies: pip install -r requirements.txt
3. Copy .env.example to .env and fill in your Telegram and AI settings.
4. Run the bot: python main.py

## Environment variables
- BOT_TOKEN: Telegram bot token
- OPENAI_API_KEY: API key for OpenAI-compatible providers
- OPENAI_BASE_URL: Base URL for an OpenAI-compatible endpoint
- AI_MODEL: Model name to use
- SQLITE_PATH: Optional SQLite database path

## Deployment
- Docker: docker build -t eva-ai .
- Render: use render.yaml
- Railway: use railway.toml
