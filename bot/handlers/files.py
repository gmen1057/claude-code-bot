"""
File handler for processing uploaded files and images
"""
import os
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.config import ALLOWED_USER_ID, USER_FILES_DIR, logger
from bot.services.session import session_manager, log_command
from bot.services.claude import execute_claude, ExecutionStatus
from bot.services.formatter import format_for_telegram, format_error


def check_access(user_id: int) -> bool:
    """Check if user has access to the bot"""
    if not ALLOWED_USER_ID:
        return True
    return user_id == ALLOWED_USER_ID


def get_file_type_hint(filename: str) -> str:
    """Get file type and suggested action"""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''

    image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
    text_exts = {'txt', 'py', 'js', 'ts', 'json', 'md', 'log', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'sh', 'bash'}
    code_exts = {'py', 'js', 'ts', 'java', 'cpp', 'c', 'h', 'go', 'rs', 'rb', 'php'}

    if ext in image_exts:
        return 'image', 'Посмотри изображение и'
    elif ext in code_exts:
        return 'code', 'Прочитай код и'
    elif ext in text_exts:
        return 'text', 'Прочитай файл и'
    else:
        return 'unknown', 'Проанализируй файл и'


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded files and images"""
    user_id = update.effective_user.id

    if not check_access(user_id):
        return

    # Determine file info
    if update.message.photo:
        # For photos, get the largest size
        file_obj = update.message.photo[-1]
        file_name = f"photo_{file_obj.file_id[:10]}.jpg"
    elif update.message.document:
        file_obj = update.message.document
        file_name = file_obj.file_name or f"document_{file_obj.file_id[:10]}"
    else:
        await update.message.reply_text("❌ Неподдерживаемый тип файла")
        return

    # Send processing message
    processing_msg = await update.message.reply_text("📥 Загружаю файл...")

    try:
        # Download file
        file = await context.bot.get_file(file_obj.file_id)
        file_path = os.path.join(USER_FILES_DIR, file_name)
        await file.download_to_drive(file_path)

        logger.info(f"File downloaded: {file_path}")

        # Get caption or default action
        caption = update.message.caption or "проанализируй этот файл"

        # Build request based on file type
        file_type, action_prefix = get_file_type_hint(file_name)

        if file_type == 'image':
            request_text = f"[РАЗРЕШЕНО ЧИТАТЬ ФАЙЛЫ] {action_prefix} {caption}. Файл: {file_path}"
        else:
            request_text = f"[РАЗРЕШЕНО ЧИТАТЬ ФАЙЛЫ] {action_prefix} {caption}. Файл: {file_path}"

        await processing_msg.edit_text("🔄 Обрабатываю файл...")

        # Get session
        session = session_manager.get_session(user_id)

        # Progress callback
        async def update_status(text: str):
            try:
                await processing_msg.edit_text(text)
            except Exception:
                pass

        # Execute through Claude
        result = await execute_claude(
            user_message=request_text,
            user_id=user_id,
            context=session.context,
            working_dir=session.working_dir,
            progress_callback=update_status
        )

        # Log the command
        log_command(
            user_id=user_id,
            command=f"[Файл: {file_name}] {caption}",
            response=result.output if result.status == ExecutionStatus.SUCCESS else None,
            execution_time_ms=result.execution_time_ms,
            error=result.error if result.status != ExecutionStatus.SUCCESS else None
        )

        if result.status == ExecutionStatus.SUCCESS:
            # Add to session context
            session_manager.add_message(
                user_id,
                f"[Файл: {file_name}] {caption}",
                result.output
            )

            # Format and send response
            formatted_parts = format_for_telegram(result.output)

            try:
                await processing_msg.edit_text(formatted_parts[0], parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.warning(f"HTML formatting failed: {e}")
                await processing_msg.edit_text(result.output[:4096])

            for part in formatted_parts[1:]:
                try:
                    await update.message.reply_text(part, parse_mode=ParseMode.HTML)
                except Exception:
                    await update.message.reply_text(part[:4096])

        elif result.status == ExecutionStatus.TIMEOUT:
            await processing_msg.edit_text(
                f"⏱️ Превышено время ожидания при обработке файла"
            )

        elif result.status == ExecutionStatus.CANCELLED:
            await processing_msg.edit_text("🛑 Обработка отменена")

        else:  # ERROR
            error_msg = format_error(result.error or "Неизвестная ошибка")
            try:
                await processing_msg.edit_text(error_msg, parse_mode=ParseMode.HTML)
            except Exception:
                await processing_msg.edit_text(f"❌ Ошибка: {result.error}")

    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await processing_msg.edit_text(f"❌ Ошибка обработки файла: {str(e)}")
