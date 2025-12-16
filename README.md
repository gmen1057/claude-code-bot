# Claude Code Telegram Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**English** | [Русский](README.ru.md)

Control Claude Code CLI through Telegram. Execute commands, analyze files, and manage your server directly from your phone.

## ✨ Features

- **Full Claude Code Access** — Execute any Claude Code command via Telegram
- **Session Persistence** — Context preserved between messages (stored in PostgreSQL)
- **File Support** — Upload and analyze files and images
- **Safe by Default** — Read-only mode unless you explicitly request changes
- **Command Cancellation** — Cancel long-running operations with `/cancel`
- **Timeout Protection** — 5-minute timeout prevents hanging processes
- **Access Control** — Restrict bot access to specific Telegram user IDs
- **Graceful Shutdown** — Clean termination of all processes

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 12+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed (`npm install -g @anthropic-ai/claude-code`)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/gmen1057/claude-code-bot.git
cd claude-code-bot
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Create database

```bash
sudo -u postgres psql -c "CREATE DATABASE claude_code_bot;"
sudo -u postgres psql -c "CREATE USER your_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE claude_code_bot TO your_user;"
```

### 6. Run the bot

```bash
python -m bot.main
```

## 🐳 Docker Installation

```bash
# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f bot
```

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_TOKEN` | Bot token from @BotFather | **Required** |
| `ALLOWED_USER_ID` | Comma-separated Telegram user IDs | None (all users) |
| `DB_NAME` | PostgreSQL database name | `claude_code_bot` |
| `DB_USER` | Database username | `postgres` |
| `DB_PASSWORD` | Database password | `postgres` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `CLAUDE_CLI_PATH` | Path to Claude CLI binary | `/root/.bun/bin/claude` |
| `CLAUDE_TIMEOUT` | Command timeout in seconds | `300` |
| `DEFAULT_WORKING_DIR` | Default working directory | `/root` |

### Getting Your Telegram User ID

Send `/start` to [@userinfobot](https://t.me/userinfobot) to get your user ID.

## 📖 Usage

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and create session |
| `/reset` | Start new session (clear context) |
| `/status` | Show current session status |
| `/context` | Show recent conversation context |
| `/history` | Show command history |
| `/cancel` | Cancel running command |
| `/cd <path>` | Change working directory |
| `/help` | Show help message |

### Execution Keywords

Commands are executed only when you use trigger keywords:

**Russian:** `выполни`, `сделай`, `запусти`, `исправь`, `создай`, `удали`, `перезапусти`

**English:** `execute`, `run`, `do`, `fix`, `create`, `delete`, `restart`

### Examples

**Information only (no execution):**
```
Show me the list of files
What does this script do?
Check nginx status
```

**With execution:**
```
Restart nginx service
Create a new Python script
Fix the error in bot.py
```

### File Uploads

Upload any file to the chat and Claude will analyze it:
- **Images** — Visual analysis and description
- **Code files** — Code review and suggestions
- **Logs** — Error analysis and troubleshooting
- **Documents** — Content extraction and summary

## 🏗️ Architecture

```
claude-code-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point, application setup
│   ├── config.py            # Configuration from environment
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py      # Bot command handlers
│   │   ├── messages.py      # Text message handler
│   │   └── files.py         # File upload handler
│   ├── services/
│   │   ├── __init__.py
│   │   ├── claude.py        # Claude CLI executor
│   │   ├── session.py       # Session management
│   │   └── formatter.py     # Telegram HTML formatter
│   └── database/
│       ├── __init__.py
│       └── pool.py          # PostgreSQL connection pool
├── user_files/              # Uploaded files storage
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── LICENSE
└── README.md
```

## 🔐 Security

### Access Control
- Set `ALLOWED_USER_ID` to restrict access to specific Telegram user IDs
- Multiple IDs can be comma-separated: `123456789,987654321`
- **Warning:** Without this setting, anyone can use your bot!

### Safe Execution
- Commands run in read-only mode by default
- Explicit trigger keywords required for modifications
- Safety instructions embedded in every prompt

### Timeout Protection
- 5-minute timeout on all Claude operations
- Cancel any time with `/cancel`

## 🖥️ Systemd Service

Create `/etc/systemd/system/claude-code-bot.service`:

```ini
[Unit]
Description=Claude Code Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/claude-code-bot
Environment=PATH=/root/.bun/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/path/to/claude-code-bot/venv/bin/python -m bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable claude-code-bot
systemctl start claude-code-bot
```

View logs:
```bash
journalctl -u claude-code-bot -f
```

## 🔧 Troubleshooting

### Bot not responding
1. Check logs: `journalctl -u claude-code-bot -f`
2. Verify Claude CLI works: `claude --version`
3. Check database connection: `psql -h localhost -U your_user -d claude_code_bot`

### Timeout errors
1. Increase `CLAUDE_TIMEOUT` in `.env`
2. Simplify your request
3. Check if Claude CLI is responding: `claude "Hello"`

### Permission errors
1. Ensure bot runs as user with Claude CLI access
2. Check working directory permissions
3. Verify file upload directory is writable

### Database errors
1. Check PostgreSQL is running: `systemctl status postgresql`
2. Verify credentials in `.env`
3. Check database exists: `psql -l | grep claude_code_bot`

## 📝 Database Schema

The bot uses two tables:

**sessions** — User session data
```sql
CREATE TABLE sessions (
    user_id BIGINT PRIMARY KEY,
    context TEXT,
    working_dir TEXT,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**command_logs** — Command history
```sql
CREATE TABLE command_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    command TEXT NOT NULL,
    response TEXT,
    execution_time_ms INTEGER DEFAULT 0,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Anthropic](https://www.anthropic.com/) for Claude and Claude Code
- [python-telegram-bot](https://python-telegram-bot.org/) for the excellent Telegram library

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/gmen1057/claude-code-bot/issues)
- **Discussions:** [GitHub Discussions](https://github.com/gmen1057/claude-code-bot/discussions)
