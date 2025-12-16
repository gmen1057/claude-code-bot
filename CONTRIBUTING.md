# Contributing to Claude Code Telegram Bot

First off, thank you for considering contributing to Claude Code Telegram Bot! It's people like you that make this project better.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:
- Be respectful and inclusive
- Be patient with newcomers
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

When creating a bug report, include:
- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs **actual behavior**
- **Environment details**: Python version, OS, PostgreSQL version
- **Logs** if available (use `journalctl -u claude-code-bot`)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:
- Use a **clear and descriptive title**
- Provide a **detailed description** of the suggested enhancement
- Explain **why this enhancement would be useful**
- List **any alternatives** you've considered

### Pull Requests

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```
4. **Make your changes**
5. **Test** your changes thoroughly
6. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add amazing new feature"
   # or
   git commit -m "fix: resolve issue with session handling"
   ```
7. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
8. Open a **Pull Request**

## Development Setup

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Claude Code CLI installed
- A Telegram Bot Token (for testing)

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/claude-code-bot.git
   cd claude-code-bot
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # if available
   ```

4. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env with your test credentials
   ```

5. Create test database:
   ```bash
   sudo -u postgres psql -c "CREATE DATABASE claude_code_bot_test;"
   ```

6. Run the bot:
   ```bash
   python -m bot.main
   ```

## Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://github.com/psf/black) for formatting
- Maximum line length: 100 characters
- Use type hints where possible

### Code Formatting

Before committing, format your code:
```bash
# Install black if not already installed
pip install black

# Format all Python files
black bot/
```

### Docstrings

Use Google-style docstrings:
```python
def function_name(param1: str, param2: int) -> bool:
    """Short description of function.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When something is wrong.
    """
    pass
```

## Project Structure

```
bot/
├── __init__.py
├── main.py           # Entry point
├── config.py         # Configuration
├── handlers/         # Telegram handlers
│   ├── commands.py   # /start, /reset, etc.
│   ├── messages.py   # Text messages
│   └── files.py      # File uploads
├── services/         # Business logic
│   ├── claude.py     # Claude CLI interaction
│   ├── session.py    # Session management
│   └── formatter.py  # HTML formatting
└── database/         # Database layer
    └── pool.py       # Connection pool
```

### Adding New Features

1. **New Command**: Add handler in `bot/handlers/commands.py`, register in `bot/main.py`
2. **New Service**: Create file in `bot/services/`, import where needed
3. **Database Changes**: Modify `bot/database/pool.py` schema

## Commit Messages

Use conventional commits format:

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation only
- `style:` — Formatting, no code change
- `refactor:` — Code change without feature/fix
- `test:` — Adding tests
- `chore:` — Maintenance tasks

Examples:
```
feat: add /stats command for usage statistics
fix: handle timeout gracefully in Claude executor
docs: update installation instructions
refactor: extract message formatting to separate module
```

## Testing

### Manual Testing

1. Create a test Telegram bot via @BotFather
2. Set up test environment with `.env.test`
3. Test all commands: `/start`, `/reset`, `/status`, etc.
4. Test file uploads with various file types
5. Test error handling with invalid inputs

### Automated Testing (Future)

We plan to add pytest-based tests. Contributions welcome!

```bash
# Future: run tests
pytest tests/
```

## Questions?

Feel free to open an issue with the "question" label if you have any questions about contributing.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
