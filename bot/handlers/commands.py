"""
Command handlers for Telegram bot
"""

import os

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.config import ALLOWED_USER_ID, logger
from bot.services.claude import cancel_process, has_active_process
from bot.services.formatter import escape_html, format_history, format_status
from bot.services.session import get_command_history, session_manager


def check_access(user_id: int) -> bool:
    """Check if user has access to the bot"""
    if not ALLOWED_USER_ID:
        return True  # No restriction if not configured
    return user_id == ALLOWED_USER_ID


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id

    if not check_access(user_id):
        await update.message.reply_text("❌ Доступ запрещён")
        return

    session = session_manager.get_session(user_id)

    await update.message.reply_text(
        "🤖 <b>Claude Code Bot активирован!</b>\n\n"
        "Я - ваш Claude Code на сервере. Отправьте любую команду, и я выполню её.\n\n"
        "<b>Команды управления:</b>\n"
        "• /reset - Начать новую сессию\n"
        "• /status - Текущий статус сессии\n"
        "• /context - Показать контекст\n"
        "• /cd &lt;path&gt; - Сменить директорию\n"
        "• /history - История команд\n"
        "• /cancel - Отменить выполняемую команду\n"
        "• /help - Помощь\n\n"
        f"📁 Рабочая директория: <code>{escape_html(session.working_dir)}</code>",
        parse_mode=ParseMode.HTML,
    )


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reset command"""
    user_id = update.effective_user.id

    if not check_access(user_id):
        return

    # Cancel any active process first
    if has_active_process(user_id):
        await cancel_process(user_id)

    session_manager.reset_session(user_id)
    await update.message.reply_text("✅ Сессия сброшена. Начинаем с чистого листа.")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user_id = update.effective_user.id

    if not check_access(user_id):
        return

    session = session_manager.get_session(user_id)
    status_text = format_status(session.to_dict())

    # Add active process indicator
    if has_active_process(user_id):
        status_text += (
            "\n\n⚙️ <b>Выполняется команда...</b> (используйте /cancel для отмены)"
        )

    await update.message.reply_text(status_text, parse_mode=ParseMode.HTML)


async def cmd_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /context command"""
    user_id = update.effective_user.id

    if not check_access(user_id):
        return

    session = session_manager.get_session(user_id)
    context_data = session.context

    if not context_data:
        await update.message.reply_text("📝 Контекст пуст")
        return

    # Show last 5 messages
    recent = context_data[-5:]

    parts = ["<b>Последние сообщения:</b>\n"]
    for msg in recent:
        user_msg = msg.get("user", "")
        if len(user_msg) > 100:
            user_msg = user_msg[:100] + "..."

        assistant_msg = msg.get("assistant", "")
        if len(assistant_msg) > 100:
            assistant_msg = assistant_msg[:100] + "..."

        parts.append(f"👤 {escape_html(user_msg)}")
        parts.append(f"🤖 {escape_html(assistant_msg)}\n")

    await update.message.reply_text("\n".join(parts), parse_mode=ParseMode.HTML)


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command"""
    user_id = update.effective_user.id

    if not check_access(user_id):
        return

    logs = get_command_history(user_id, limit=20)
    history_text = format_history(logs)

    # Split if too long
    if len(history_text) > 4096:
        parts = [history_text[i : i + 4096] for i in range(0, len(history_text), 4096)]
        await update.message.reply_text(parts[0], parse_mode=ParseMode.HTML)
        for part in parts[1:]:
            await update.message.reply_text(part, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(history_text, parse_mode=ParseMode.HTML)


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command"""
    user_id = update.effective_user.id

    if not check_access(user_id):
        return

    if await cancel_process(user_id):
        await update.message.reply_text("🛑 Выполнение команды отменено")
    else:
        await update.message.reply_text("ℹ️ Нет активных команд для отмены")


async def cmd_cd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cd command"""
    user_id = update.effective_user.id

    if not check_access(user_id):
        return

    # Get path from command
    text = update.message.text
    parts = text.split(maxsplit=1)

    if len(parts) < 2:
        await update.message.reply_text(
            "Использование: /cd &lt;путь&gt;", parse_mode=ParseMode.HTML
        )
        return

    new_dir = parts[1].strip()

    # Validate directory
    if os.path.exists(new_dir) and os.path.isdir(new_dir):
        session_manager.update_session(user_id, working_dir=new_dir)
        await update.message.reply_text(
            f"✅ Рабочая директория изменена на: <code>{escape_html(new_dir)}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            f"❌ Директория не существует: {escape_html(new_dir)}"
        )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """🤖 <b>Claude Code Bot - Помощь</b>

<b>Основные возможности:</b>
• Отправьте любое текстовое сообщение, и я выполню его через Claude Code
• Я помню контекст нашей беседы
• Могу работать с файлами, выполнять команды, писать код

<b>Команды управления:</b>
• /start - Активировать бота
• /reset - Начать новую сессию (сбросить контекст)
• /status - Показать статус текущей сессии
• /context - Показать текущий контекст (последние сообщения)
• /history - История ВСЕХ команд (сохраняется после /reset)
• /cancel - Отменить выполняющуюся команду
• /cd &lt;path&gt; - Сменить рабочую директорию
• /help - Эта справка

<b>Примеры использования:</b>
• "Покажи список файлов в текущей директории"
• "Исправь баг в файле bot.py на строке 45"
• "Создай новый Python скрипт для парсинга данных"
• "Проанализируй логи и найди ошибки"

<b>Ключевые слова для выполнения команд:</b>
выполни, сделай, запусти, исправь, создай, удали, restart, перезапусти

<b>Особенности:</b>
• Сессия сохраняется между сообщениями
• Timeout: 5 минут на выполнение команды
• Все команды логируются в базу данных"""

    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
