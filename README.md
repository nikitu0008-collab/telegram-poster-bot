# Telegram Auto-Poster Bot

Бот для автоматического сбора контента из различных источников (RSS-ленты, Telegram-каналы, генерация мемов) и публикации его в ваш Telegram-канал с управляемой очередью и защитой от дубликатов.

## Возможности

- Сбор постов из RSS/Atom-лент (заголовок, описание, картинка, ссылка).
- Репост последних сообщений из Telegram-каналов с указанием источника.
- Генерация мемов через Meme-API (вероятность настраивается).
- Умная очередь публикаций — посты не дублируются, история сохраняется.
- Отложенная публикация: при ошибке Telegram пост возвращается в начало очереди.
- Гибкие интервалы сбора и публикации.
- Поддержка HTML-разметки в тексте постов.
- Полностью асинхронная работа: Telethon + python-telegram-bot, планировщик в отдельном потоке.

## Требования

- Python 3.8+
- Аккаунт Telegram (`api_id` и `api_hash` с <https://my.telegram.org>)
- Бот-токен от [@BotFather](https://t.me/BotFather)
- ID канала, в который публикуем (например, `@my_channel`)

## Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/nikitu0008-collab/telegram-poster-bot.git
cd telegram-poster-bot
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
```

```bash
venv\Scripts\activate         # Windows
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить переменные окружения

Скопируйте пример конфигурации и отредактируйте:

```bash
cp .env.example .env
```

```bash
copy .env.example .env        # Windows
```

Заполните `.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:AA...
CHANNEL_ID=@my_channel
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=0123456789abcdef...
```

Полный список настроек с комментариями — в [.env.example](.env.example).

### 5. Задать источники контента

Тот же `.env`, списки через запятую:

```env
SOURCE_CHANNELS=@news_channel,@tech_updates
RSS_FEEDS=https://example.com/rss,https://another-feed.xml
```

Интервалы в минутах:

```env
POST_INTERVAL_MINUTES=60       # сбор раз в час
PUBLISH_INTERVAL_MINUTES=30    # публикация раз в полчаса
MAX_POSTS_PER_COLLECT=20       # максимум постов за один сбор
MEME_PROBABILITY=0.4           # вероятность мема при сборе
```

## Запуск

```bash
python src/main.py
```

При первом запуске Telethon запросит подтверждение входа — понадобится номер телефона и код из Telegram. Сессия сохранится в `src/user_session.session`, при следующих запусках вход не потребуется.

Бот сразу проверит очередь: если она пуста, выполнит сбор контента и опубликует первый пост, затем перейдёт в режим ожидания по расписанию.

## Файлы состояния

| Файл | Назначение |
|---|---|
| `src/posted_history.json` | хэши текстов уже опубликованных постов |
| `src/queue.json` | очередь постов, ожидающих публикации |
| `src/user_session.session` | сессия Telethon |

Все три файла в `.gitignore` — это runtime-состояние, а не часть кода.

## Управление очередью и историей

История хранится в `posted_history.json`: она не даёт опубликовать один и тот же пост дважды (сравнивается текст или подпись фото). Очередь лежит в `queue.json` — бот публикует посты последовательно и удаляет их из очереди. Если публикация не удалась (ошибка Telegram), пост возвращается в начало очереди.

## Возможные проблемы

| Проблема | Решение |
|---|---|
| `TelegramError` при публикации | Проверьте токен бота, права на публикацию в канале и доступность URL для фото. |
| Бот не видит канал | Бот должен быть добавлен в канал как администратор. |
| Ошибка импорта модулей | `pip install -r requirements.txt`. |
| Telethon запрашивает код каждый раз | Проверьте, что сохраняется `src/user_session.session`. |
| `Не заданы переменные окружения` | Скопируйте `.env.example` в `.env` и заполните значения. |

## Структура проекта

```
telegram-poster-bot/
├── src/
│   ├── main.py        # основная логика: сбор, очередь, публикация, планировщик
│   └── config.py      # конфигурация из переменных окружения
├── .env.example
├── requirements.txt
└── README.md
```

## Лицензия

MIT — файл [LICENSE](LICENSE).

## Благодарности

- [Telethon](https://docs.telethon.dev) — асинхронный клиент Telegram.
- [python-telegram-bot](https://python-telegram-bot.org) — обёртка над Bot API.
- [feedparser](https://pypi.org/project/feedparser/) — парсинг RSS/Atom.
- [Meme-API](https://github.com/MemeAPI) — генерация мемов.
