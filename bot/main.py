"""
Claude Code Telegram Bot - Main Entry Point
"""

import asyncio
import signal

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.config import TELEGRAM_TOKEN, logger, validate_config
from bot.database.pool import close_pool, init_database, init_pool
from bot.handlers.commands import (
    cmd_cancel,
    cmd_cd,
    cmd_context,
    cmd_help,
    cmd_history,
    cmd_reset,
    cmd_start,
    cmd_status,
)
from bot.handlers.files import handle_file
from bot.handlers.messages import handle_message
from bot.services.claude import terminate_all_processes
from bot.services.session import session_manager

# Flag for graceful shutdown
_shutdown_event = asyncio.Event()


async def post_init(application: Application):
    """Called after application initialization"""
    # Set bot commands
    await application.bot.set_my_commands(
        [
            ("start", "🚀 Запустить бота"),
            ("reset", "🔄 Начать новую сессию"),
            ("status", "📊 Статус текущей сессии"),
            ("context", "💬 Показать текущий контекст"),
            ("history", "📜 История всех команд"),
            ("cancel", "🛑 Отменить текущую команду"),
            ("cd", "📁 Сменить директорию"),
            ("help", "❓ Помощь по командам"),
        ]
    )
    logger.info("Bot commands registered")


async def post_shutdown(application: Application):
    """Called after application shutdown"""
    logger.info("Starting graceful shutdown...")

    # Terminate all active Claude processes
    await terminate_all_processes()

    # Clear session cache
    session_manager.clear_cache()

    # Close database pool
    close_pool()

    logger.info("Graceful shutdown complete")


def setup_signal_handlers(application: Application):
    """Setup signal handlers for graceful shutdown"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # If no loop is running yet, we'll set up handlers after start
        return

    def signal_handler(sig):
        logger.info(f"Received signal {sig}, initiating shutdown...")
        _shutdown_event.set()
        # Stop the application
        application.stop_running()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))


def create_application() -> Application:
    """Create and configure the bot application"""
    # Build application
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Register command handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("reset", cmd_reset))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("context", cmd_context))
    application.add_handler(CommandHandler("history", cmd_history))
    application.add_handler(CommandHandler("cancel", cmd_cancel))
    application.add_handler(CommandHandler("cd", cmd_cd))
    application.add_handler(CommandHandler("help", cmd_help))

    # Register message handler (text messages excluding commands)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Register file handler (documents and photos)
    application.add_handler(
        MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file)
    )

    return application


def main():
    """Main entry point"""
    # Validate configuration
    errors = validate_config()
    if errors:
        for error in errors:
            logger.error(error)
        return 1

    # Initialize database
    try:
        init_pool()
        init_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return 1

    # Create application
    application = create_application()

    # Setup signal handlers (only works on Unix)
    try:
        setup_signal_handlers(application)
    except NotImplementedError:
        # Windows doesn't support signal handlers in asyncio
        pass

    # Run the bot
    logger.info("Claude Code Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

    return 0


if __name__ == "__main__":
    exit(main())
