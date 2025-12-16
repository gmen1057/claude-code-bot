"""
Claude CLI executor service with safe invocation
"""
import asyncio
import time
from typing import Optional, Tuple, Callable, Dict, List
from dataclasses import dataclass
from enum import Enum

from bot.config import (
    logger, CLAUDE_CLI_PATH, CLAUDE_TIMEOUT,
    CLAUDE_MAX_CONTEXT_MESSAGES, DEFAULT_WORKING_DIR
)


class ExecutionStatus(Enum):
    """Execution status codes"""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class ExecutionResult:
    """Result of Claude execution"""
    status: ExecutionStatus
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: int = 0


# Global storage for active processes (for cancellation)
_active_processes: Dict[int, asyncio.subprocess.Process] = {}


def get_active_process(user_id: int) -> Optional[asyncio.subprocess.Process]:
    """Get active process for user"""
    return _active_processes.get(user_id)


def has_active_process(user_id: int) -> bool:
    """Check if user has active process"""
    process = _active_processes.get(user_id)
    return process is not None and process.returncode is None


async def cancel_process(user_id: int) -> bool:
    """Cancel active process for user"""
    process = _active_processes.get(user_id)
    if process and process.returncode is None:
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except asyncio.TimeoutError:
            process.kill()
        logger.info(f"Process cancelled for user {user_id}")
        return True
    return False


def build_prompt(
    user_message: str,
    context: List[Dict] = None,
    needs_execution: bool = False
) -> str:
    """Build full prompt with context and safety instructions"""

    # Safety instructions
    safety_instructions = """IMPORTANT CONTEXT: You are being accessed through Telegram bot @ServerClaudeBot
The user is writing to you from their phone/computer via Telegram messenger.
Responses will be shown in Telegram chat, so keep them concise and well-formatted.

CRITICAL RULES - YOU MUST FOLLOW:
1. DO NOT execute ANY system commands unless the message explicitly says "выполни", "сделай", "запусти" or "restart"
2. If user just mentions something or asks about status - ONLY provide information
3. NEVER run systemctl, apt, rm, or any modifying commands without explicit request
4. For messages like "пока оставим так", "хм", "ладно" - just acknowledge, don't do anything
5. Default mode is READ-ONLY - only analyze and inform
6. Example: "swap используется" = explain, don't fix. "очисти swap" = then execute
7. Remember: The user is communicating via Telegram, not directly in terminal

"""

    if needs_execution:
        safety_instructions += "CURRENT MODE: Execution allowed (user explicitly requested action)\n"
    else:
        safety_instructions += "CURRENT MODE: Information only (no execution)\n"

    safety_instructions += "INTERFACE: Telegram Bot\n\n"

    # Build context from previous messages
    context_text = ""
    if context:
        recent_context = context[-CLAUDE_MAX_CONTEXT_MESSAGES:]
        context_messages = []

        for msg in recent_context:
            if msg.get('user'):
                context_messages.append(f"User: {msg['user']}")
            if msg.get('assistant'):
                # Truncate long assistant messages in context
                assistant_msg = msg['assistant']
                if len(assistant_msg) > 500:
                    assistant_msg = assistant_msg[:500] + "..."
                context_messages.append(f"Assistant: {assistant_msg}")

        if context_messages:
            context_text = "Previous context:\n" + "\n".join(context_messages) + "\n\n"

    return safety_instructions + context_text + f"Current request (from Telegram): {user_message}"


async def execute_claude(
    user_message: str,
    user_id: int,
    context: List[Dict] = None,
    working_dir: str = DEFAULT_WORKING_DIR,
    timeout: int = None,
    progress_callback: Callable[[str], None] = None
) -> ExecutionResult:
    """
    Execute Claude CLI safely with stdin input (no shell injection)

    Args:
        user_message: User's message
        user_id: Telegram user ID (for process tracking)
        context: Previous conversation context
        working_dir: Working directory for execution
        timeout: Timeout in seconds (default from config)
        progress_callback: Async callback for progress updates

    Returns:
        ExecutionResult with status, output, and timing
    """
    timeout = timeout or CLAUDE_TIMEOUT
    start_time = time.time()

    # Detect if execution is needed
    execute_keywords = ['выполни', 'сделай', 'запусти', 'исправь', 'создай', 'удали', 'restart', 'перезапусти']
    needs_execution = any(keyword in user_message.lower() for keyword in execute_keywords)

    # Add prefix for non-execution requests
    if not needs_execution:
        user_message = f"[ТОЛЬКО ИНФОРМАЦИЯ, НЕ ВЫПОЛНЯТЬ КОМАНДЫ] {user_message}"

    # Build full prompt
    full_prompt = build_prompt(user_message, context, needs_execution)
    logger.info(f"Executing Claude for user {user_id}, prompt length: {len(full_prompt)}")

    process = None
    progress_task = None

    try:
        # Create subprocess with stdin (SAFE - no shell injection)
        process = await asyncio.create_subprocess_exec(
            CLAUDE_CLI_PATH,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )

        # Track process for cancellation
        _active_processes[user_id] = process

        # Start progress updates
        if progress_callback:
            async def update_progress():
                statuses = [
                    "⏳ Claude думает...",
                    "⚙️ Обрабатываю запрос...",
                    "🔄 Анализирую...",
                    "📊 Готовлю ответ..."
                ]
                counter = 0
                while process.returncode is None:
                    await asyncio.sleep(3)
                    if counter < 20:  # First 60 seconds
                        try:
                            await progress_callback(statuses[counter % len(statuses)])
                            counter += 1
                        except Exception:
                            pass

            progress_task = asyncio.create_task(update_progress())

        # Execute with timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=full_prompt.encode('utf-8')),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()

            execution_time = int((time.time() - start_time) * 1000)
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                error=f"Превышено время ожидания ({timeout} секунд)",
                execution_time_ms=execution_time
            )

        execution_time = int((time.time() - start_time) * 1000)

        # Check return code
        if process.returncode == 0:
            output = stdout.decode('utf-8')
            logger.info(f"Claude response received: {len(output)} chars in {execution_time}ms")
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                output=output,
                execution_time_ms=execution_time
            )
        elif process.returncode == -15:  # SIGTERM
            return ExecutionResult(
                status=ExecutionStatus.CANCELLED,
                error="Выполнение отменено",
                execution_time_ms=execution_time
            )
        else:
            error = stderr.decode('utf-8')
            logger.error(f"Claude error (code {process.returncode}): {error}")
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error=error or f"Exit code: {process.returncode}",
                execution_time_ms=execution_time
            )

    except asyncio.CancelledError:
        if process and process.returncode is None:
            process.terminate()
        execution_time = int((time.time() - start_time) * 1000)
        return ExecutionResult(
            status=ExecutionStatus.CANCELLED,
            error="Выполнение отменено",
            execution_time_ms=execution_time
        )

    except Exception as e:
        logger.error(f"Claude execution error: {e}")
        execution_time = int((time.time() - start_time) * 1000)
        return ExecutionResult(
            status=ExecutionStatus.ERROR,
            error=str(e),
            execution_time_ms=execution_time
        )

    finally:
        # Cancel progress task
        if progress_task:
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

        # Remove from active processes
        if user_id in _active_processes:
            del _active_processes[user_id]


async def terminate_all_processes():
    """Terminate all active processes (for shutdown)"""
    for user_id, process in list(_active_processes.items()):
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
            logger.info(f"Terminated process for user {user_id}")

    _active_processes.clear()
