"""
Message handler for processing text messages
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.config import ALLOWED_USER_ID, logger
from bot.services.session import session_manager, log_command
from bot.services.claude import execute_claude, ExecutionStatus
from bot.services.formatter import format_for_telegram, format_error


def check_access(user_id: int) -> bool:
    """Check if user has access to the bot"""
    if not ALLOWED_USER_ID:
        return True
    return user_id == ALLOWED_USER_ID


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    user_id = update.effective_user.id

    if not check_access(user_id):
        return

    user_message = update.message.text
    session = session_manager.get_session(user_id)

    # Send processing indicator
    processing_msg = await update.message.reply_text("⏳ Обрабатываю запрос...")

    # Progress callback for status updates
    async def update_status(text: str):
        try:
            await processing_msg.edit_text(text)
        except Exception:
            pass  # Ignore if message was already edited

    try:
        # Execute through Claude
        result = await execute_claude(
            user_message=user_message,
            user_id=user_id,
            context=session.context,
            working_dir=session.working_dir,
            progress_callback=update_status
        )

        # Log the command
        log_command(
            user_id=user_id,
            command=user_message,
            response=result.output if result.status == ExecutionStatus.SUCCESS else None,
            execution_time_ms=result.execution_time_ms,
            error=result.error if result.status != ExecutionStatus.SUCCESS else None
        )

        # Handle different statuses
        if result.status == ExecutionStatus.SUCCESS:
            # Add to session context
            session_manager.add_message(user_id, user_message, result.output)

            # Format and send response
            formatted_parts = format_for_telegram(result.output)

            # Edit first message
            try:
                await processing_msg.edit_text(formatted_parts[0], parse_mode=ParseMode.HTML)
            except Exception as e:
                # Fallback without HTML if formatting fails
                logger.warning(f"HTML formatting failed: {e}")
                await processing_msg.edit_text(result.output[:4096])

            # Send additional parts if needed
            for part in formatted_parts[1:]:
                try:
                    await update.message.reply_text(part, parse_mode=ParseMode.HTML)
                except Exception:
                    await update.message.reply_text(part[:4096])

        elif result.status == ExecutionStatus.TIMEOUT:
            await processing_msg.edit_text(
                f"⏱️ Превышено время ожидания ({result.execution_time_ms // 1000} сек)\n"
                "Попробуйте более простой запрос или используйте /cancel для отмены."
            )

        elif result.status == ExecutionStatus.CANCELLED:
            await processing_msg.edit_text("🛑 Выполнение отменено")

        else:  # ERROR
            error_msg = format_error(result.error or "Неизвестная ошибка")
            try:
                await processing_msg.edit_text(error_msg, parse_mode=ParseMode.HTML)
            except Exception:
                await processing_msg.edit_text(f"❌ Ошибка: {result.error}")

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await processing_msg.edit_text(f"❌ Произошла ошибка: {str(e)}")
