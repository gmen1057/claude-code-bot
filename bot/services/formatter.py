"""
Message formatter for Telegram
Converts Claude output to Telegram-compatible HTML
"""
import re
from typing import List, Tuple


def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


def format_code_blocks(text: str) -> Tuple[str, List[str]]:
    """
    Extract and replace code blocks with placeholders
    Returns: (text_with_placeholders, list_of_code_blocks)
    """
    code_blocks = []
    placeholder_template = "<<<CODE_BLOCK_{0}>>>"

    # Match triple backtick code blocks with optional language
    pattern = r'```(\w*)\n?(.*?)```'

    def replacer(match):
        lang = match.group(1) or ''
        code = match.group(2).strip()
        idx = len(code_blocks)
        code_blocks.append((lang, code))
        return placeholder_template.format(idx)

    text = re.sub(pattern, replacer, text, flags=re.DOTALL)
    return text, code_blocks


def restore_code_blocks(text: str, code_blocks: List[Tuple[str, str]]) -> str:
    """Restore code blocks from placeholders"""
    for idx, (lang, code) in enumerate(code_blocks):
        placeholder = f"<<<CODE_BLOCK_{idx}>>>"
        # For Telegram, we use <pre> for code blocks
        # Language hint is added as a comment if present
        if lang:
            formatted = f"<pre>{escape_html(code)}</pre>"
        else:
            formatted = f"<pre>{escape_html(code)}</pre>"
        text = text.replace(placeholder, formatted)
    return text


def format_inline_code(text: str) -> str:
    """Convert `code` to <code>code</code>"""
    # Don't match inside our placeholders
    pattern = r'`([^`\n]+)`'

    def replacer(match):
        code = match.group(1)
        return f"<code>{escape_html(code)}</code>"

    return re.sub(pattern, replacer, text)


def format_bold(text: str) -> str:
    """Convert **bold** and *bold* to <b>bold</b>"""
    # Double asterisks first
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    # Single asterisks (but not if inside a tag)
    text = re.sub(r'(?<![<>])\*([^*<>]+)\*(?![<>])', r'<b>\1</b>', text)
    return text


def format_italic(text: str) -> str:
    """Convert _italic_ to <i>italic</i>"""
    # Underscores for italic (but not multiple underscores like __name__)
    text = re.sub(r'(?<![_\w])_([^_]+)_(?![_\w])', r'<i>\1</i>', text)
    return text


def format_strikethrough(text: str) -> str:
    """Convert ~~strikethrough~~ to <s>strikethrough</s>"""
    text = re.sub(r'~~([^~]+)~~', r'<s>\1</s>', text)
    return text


def format_links(text: str) -> str:
    """Convert [text](url) to <a href="url">text</a>"""
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    text = re.sub(pattern, r'<a href="\2">\1</a>', text)
    return text


def clean_claude_output(text: str) -> str:
    """Clean up Claude CLI output artifacts"""
    # Remove ANSI color codes
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)

    # Remove box-drawing characters and decorations
    text = re.sub(r'[─│┌┐└┘├┤┬┴┼╭╮╯╰]+', '', text)

    # Remove multiple empty lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove leading/trailing whitespace from lines while preserving code indentation
    lines = text.split('\n')
    cleaned_lines = []
    in_code_block = False

    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            cleaned_lines.append(line)
        elif in_code_block:
            cleaned_lines.append(line)  # Preserve indentation in code
        else:
            cleaned_lines.append(line.strip())

    text = '\n'.join(cleaned_lines)

    return text.strip()


def format_for_telegram(text: str, max_length: int = 4096) -> List[str]:
    """
    Convert Claude output to Telegram-compatible HTML

    Args:
        text: Raw Claude output
        max_length: Maximum message length (Telegram limit is 4096)

    Returns:
        List of formatted message parts
    """
    # Clean up Claude artifacts
    text = clean_claude_output(text)

    # Extract code blocks (to protect them from other formatting)
    text, code_blocks = format_code_blocks(text)

    # Escape HTML in non-code parts
    text = escape_html(text)

    # Apply formatting (order matters!)
    text = format_bold(text)
    text = format_italic(text)
    text = format_strikethrough(text)
    text = format_inline_code(text)
    text = format_links(text)

    # Restore code blocks
    text = restore_code_blocks(text, code_blocks)

    # Split into parts if too long
    if len(text) <= max_length:
        return [text]

    return split_message(text, max_length)


def split_message(text: str, max_length: int = 4096) -> List[str]:
    """
    Split long message into parts while preserving HTML tags

    Args:
        text: Formatted text
        max_length: Maximum length per part

    Returns:
        List of message parts
    """
    parts = []

    while len(text) > max_length:
        # Find a good split point
        split_idx = max_length

        # Try to split at paragraph
        para_idx = text.rfind('\n\n', 0, max_length)
        if para_idx > max_length // 2:
            split_idx = para_idx

        # Or at newline
        elif (newline_idx := text.rfind('\n', 0, max_length)) > max_length // 2:
            split_idx = newline_idx

        # Or at space
        elif (space_idx := text.rfind(' ', 0, max_length)) > max_length // 2:
            split_idx = space_idx

        # Check if we're splitting inside a tag
        part = text[:split_idx]

        # Simple check for unclosed tags
        open_tags = re.findall(r'<(b|i|code|pre|s|a)[^>]*>', part)
        close_tags = re.findall(r'</(b|i|code|pre|s|a)>', part)

        # Close unclosed tags at end of part
        for tag in reversed(open_tags):
            if open_tags.count(tag) > close_tags.count(tag):
                part += f"</{tag.split()[0]}>"

        parts.append(part.strip())
        text = text[split_idx:].strip()

        # Reopen tags that were closed
        for tag in open_tags:
            if open_tags.count(tag) > close_tags.count(tag):
                text = f"<{tag}>" + text

    if text:
        parts.append(text)

    return parts


def format_error(error: str) -> str:
    """Format error message"""
    return f"❌ Ошибка:\n<pre>{escape_html(error)}</pre>"


def format_status(status: dict) -> str:
    """Format session status message"""
    return f"""📊 <b>Статус сессии</b>

📁 Рабочая директория: <code>{escape_html(status.get('working_dir', '/root'))}</code>
🎯 Активный проект: {escape_html(status.get('active_project', 'Не выбран') or 'Не выбран')}
💬 Сообщений: {status.get('message_count', 0)}
🕐 Создана: {status.get('created_at', 'Неизвестно')}
🔄 Последняя активность: {status.get('last_activity', 'Неизвестно')}"""


def format_history(logs: List[dict]) -> str:
    """Format command history"""
    if not logs:
        return "📜 История команд пуста"

    parts = ["📜 <b>Последние команды:</b>\n"]

    for log in reversed(logs):  # Show oldest first
        timestamp = log['created_at'].strftime('%d.%m %H:%M') if log.get('created_at') else 'N/A'
        command = log.get('command', '')[:50]
        if len(log.get('command', '')) > 50:
            command += '...'

        response_preview = log.get('response', '') or 'Нет ответа'
        if len(response_preview) > 100:
            response_preview = response_preview[:100] + '...'

        exec_time = f" ({log['execution_time_ms']}ms)" if log.get('execution_time_ms') else ""

        parts.append(f"🕐 {timestamp}{exec_time}\n"
                     f"👤 {escape_html(command)}\n"
                     f"🤖 {escape_html(response_preview)}\n")

    return '\n'.join(parts)
