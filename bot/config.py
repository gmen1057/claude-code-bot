"""
Configuration module for Claude Code Bot
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger('claude-code-bot')

# Telegram configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
_allowed_user_id = os.getenv('ALLOWED_USER_ID', '').strip()
ALLOWED_USER_ID = int(_allowed_user_id) if _allowed_user_id.isdigit() else None

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'claude_code_bot'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

# Connection pool settings
DB_POOL_MIN = int(os.getenv('DB_POOL_MIN', '1'))
DB_POOL_MAX = int(os.getenv('DB_POOL_MAX', '10'))

# Claude CLI configuration
CLAUDE_CLI_PATH = os.getenv('CLAUDE_CLI_PATH', '/root/.bun/bin/claude')
CLAUDE_TIMEOUT = int(os.getenv('CLAUDE_TIMEOUT', '300'))  # 5 minutes default
CLAUDE_MAX_CONTEXT_MESSAGES = int(os.getenv('CLAUDE_MAX_CONTEXT_MESSAGES', '10'))

# File handling
USER_FILES_DIR = Path(os.getenv('USER_FILES_DIR', '/root/claude-code-bot/user_files'))
USER_FILES_DIR.mkdir(parents=True, exist_ok=True)

# Default working directory
DEFAULT_WORKING_DIR = os.getenv('DEFAULT_WORKING_DIR', '/root')

# Rate limiting
RATE_LIMIT_MESSAGES = int(os.getenv('RATE_LIMIT_MESSAGES', '30'))  # per minute
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))  # seconds

# Validate required configuration
def validate_config():
    """Validate that all required configuration is present"""
    errors = []

    if not TELEGRAM_TOKEN:
        errors.append("TELEGRAM_TOKEN is not set")

    if not ALLOWED_USER_ID:
        logger.warning("ALLOWED_USER_ID not set - bot will be accessible to everyone!")

    if not Path(CLAUDE_CLI_PATH).exists():
        errors.append(f"Claude CLI not found at {CLAUDE_CLI_PATH}")

    return errors
