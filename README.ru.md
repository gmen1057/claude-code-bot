# Claude Code Telegram Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[English](README.md) | **Русский**

Управляйте Claude Code CLI через Telegram. Выполняйте команды, анализируйте файлы и управляйте сервером прямо с телефона.

## Возможности

- **Полный доступ к Claude Code** — выполнение любых команд через Telegram
- **Сохранение контекста** — история диалога сохраняется между сообщениями (PostgreSQL)
- **Работа с файлами** — загрузка и анализ файлов и изображений
- **Безопасность по умолчанию** — режим только чтения, пока явно не запросите изменения
- **Отмена команд** — отмена долгих операций через `/cancel`
- **Защита от зависания** — таймаут 5 минут на выполнение команд
- **Контроль доступа** — ограничение доступа по Telegram ID пользователя
- **Корректное завершение** — чистое завершение всех процессов

## Требования

- Python 3.9+
- PostgreSQL 12+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`)
- Telegram Bot Token (от [@BotFather](https://t.me/BotFather))

## Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/gmen1057/claude-code-bot.git
cd claude-code-bot
```

### 2. Создайте виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или: venv\Scripts\activate  # Windows
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Настройте конфигурацию

```bash
cp .env.example .env
# Отредактируйте .env
```

### 5. Создайте базу данных

```bash
sudo -u postgres psql -c "CREATE DATABASE claude_code_bot;"
sudo -u postgres psql -c "CREATE USER your_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE claude_code_bot TO your_user;"
```

### 6. Запустите бота

```bash
python -m bot.main
```

## Docker

```bash
# Настройте конфигурацию
cp .env.example .env
# Отредактируйте .env

# Запустите через Docker Compose
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot
```

## Конфигурация

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_TOKEN` | Токен бота от @BotFather | **Обязательно** |
| `ALLOWED_USER_ID` | Telegram ID пользователя (через запятую) | Нет (все пользователи) |
| `DB_NAME` | Имя базы данных PostgreSQL | `claude_code_bot` |
| `DB_USER` | Пользователь БД | `postgres` |
| `DB_PASSWORD` | Пароль БД | `postgres` |
| `DB_HOST` | Хост БД | `localhost` |
| `DB_PORT` | Порт БД | `5432` |
| `CLAUDE_CLI_PATH` | Путь к Claude CLI | `/root/.bun/bin/claude` |
| `CLAUDE_TIMEOUT` | Таймаут команд (сек) | `300` |
| `DEFAULT_WORKING_DIR` | Рабочая директория | `/root` |

### Как узнать свой Telegram ID

Отправьте `/start` боту [@userinfobot](https://t.me/userinfobot).

## Использование

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота и создание сессии |
| `/reset` | Новая сессия (очистка контекста) |
| `/status` | Статус текущей сессии |
| `/context` | Показать контекст диалога |
| `/history` | История команд |
| `/cancel` | Отменить выполняемую команду |
| `/cd <путь>` | Сменить рабочую директорию |
| `/help` | Справка |

### Ключевые слова для выполнения

Команды выполняются только при использовании триггерных слов:

**Русские:** `выполни`, `сделай`, `запусти`, `исправь`, `создай`, `удали`, `перезапусти`

**Английские:** `execute`, `run`, `do`, `fix`, `create`, `delete`, `restart`

### Примеры

**Только информация (без выполнения):**
```
Покажи список файлов
Что делает этот скрипт?
Проверь статус nginx
```

**С выполнением:**
```
Перезапусти nginx
Создай новый Python скрипт
Исправь ошибку в bot.py
```

### Загрузка файлов

Загрузите любой файл в чат — Claude его проанализирует:
- **Изображения** — визуальный анализ и описание
- **Код** — ревью кода и рекомендации
- **Логи** — анализ ошибок и диагностика
- **Документы** — извлечение содержимого и резюме

## Архитектура

```
claude-code-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Точка входа
│   ├── config.py            # Конфигурация
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py      # Обработчики команд
│   │   ├── messages.py      # Обработчик сообщений
│   │   └── files.py         # Обработчик файлов
│   ├── services/
│   │   ├── __init__.py
│   │   ├── claude.py        # Исполнитель Claude CLI
│   │   ├── session.py       # Управление сессиями
│   │   └── formatter.py     # HTML форматирование
│   └── database/
│       ├── __init__.py
│       └── pool.py          # Пул соединений PostgreSQL
├── user_files/              # Хранилище загруженных файлов
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── LICENSE
└── README.md
```

## Безопасность

### Контроль доступа
- Установите `ALLOWED_USER_ID` для ограничения доступа
- Несколько ID через запятую: `123456789,987654321`
- **Внимание:** Без этой настройки бот доступен всем!

### Безопасное выполнение
- По умолчанию команды в режиме только чтения
- Для изменений нужны триггерные слова
- Инструкции безопасности встроены в каждый запрос

### Защита от зависания
- Таймаут 5 минут на все операции
- Отмена в любой момент через `/cancel`

## Systemd сервис

Создайте `/etc/systemd/system/claude-code-bot.service`:

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

Включите и запустите:
```bash
systemctl daemon-reload
systemctl enable claude-code-bot
systemctl start claude-code-bot
```

Просмотр логов:
```bash
journalctl -u claude-code-bot -f
```

## Решение проблем

### Бот не отвечает
1. Проверьте логи: `journalctl -u claude-code-bot -f`
2. Убедитесь, что Claude CLI работает: `claude --version`
3. Проверьте подключение к БД: `psql -h localhost -U your_user -d claude_code_bot`

### Ошибки таймаута
1. Увеличьте `CLAUDE_TIMEOUT` в `.env`
2. Упростите запрос
3. Проверьте работу Claude CLI: `claude "Привет"`

### Ошибки доступа
1. Бот должен запускаться от пользователя с доступом к Claude CLI
2. Проверьте права на рабочую директорию
3. Директория для файлов должна быть доступна для записи

### Ошибки базы данных
1. PostgreSQL запущен: `systemctl status postgresql`
2. Проверьте учётные данные в `.env`
3. База существует: `psql -l | grep claude_code_bot`

## Схема базы данных

**sessions** — данные сессий пользователей
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

**command_logs** — история команд
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

## Участие в разработке

Приветствуются любые вклады! См. [CONTRIBUTING.md](CONTRIBUTING.md).

1. Сделайте форк репозитория
2. Создайте ветку: `git checkout -b feature/amazing-feature`
3. Закоммитьте изменения: `git commit -m 'Add amazing feature'`
4. Запушьте: `git push origin feature/amazing-feature`
5. Откройте Pull Request

## Лицензия

MIT License — см. [LICENSE](LICENSE).

## Благодарности

- [Anthropic](https://www.anthropic.com/) за Claude и Claude Code
- [python-telegram-bot](https://python-telegram-bot.org/) за отличную библиотеку

## Поддержка

- **Issues:** [GitHub Issues](https://github.com/gmen1057/claude-code-bot/issues)
- **Discussions:** [GitHub Discussions](https://github.com/gmen1057/claude-code-bot/discussions)
