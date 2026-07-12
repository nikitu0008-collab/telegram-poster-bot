import asyncio
import json
import logging
import random
import time
import feedparser
import requests
import threading
import os
from bs4 import BeautifulSoup
from telethon import TelegramClient
from telegram import Bot
from telegram.error import TelegramError
import schedule

#SETTINGS
TELEGRAM_BOT_TOKEN = #TELEGRAM BOT TOKEN
CHANNEL_ID = #"@CHANEL_ID"

TELEGRAM_API_ID = #TELEGRAM API IP 
TELEGRAM_API_HASH = #"TELEGRAM API HASH"

#Интервал сбора контента (минуты) — 6 дней
POST_INTERVAL_MINUTES = 8640
#Интервал публикации (минуты)
PUBLISH_INTERVAL_MINUTES = 30
#Максимальное количество постов за один сбор
MAX_POSTS_PER_COLLECT = 20

#FILES
HISTORY_FILE = "posted_history.json"
QUEUE_FILE = "queue.json"

# ========== ИСТОЧНИКИ ==========
SOURCE_CHANNELS = [
    #"@CHANNELS"
]

RSS_FEEDS = [
    #"https://..."
]

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = Bot(token=TELEGRAM_BOT_TOKEN)
client = TelegramClient("user_session", TELEGRAM_API_ID, TELEGRAM_API_HASH)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# Подавляем технические сообщения Telethon
logging.getLogger('telethon').setLevel(logging.WARNING)

# История опубликованных постов
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return set(json.loads(content)) if content else set()
        except (json.JSONDecodeError, ValueError):
            logging.warning("Файл истории повреждён, создаём новый")
            if os.path.exists(HISTORY_FILE):
                os.rename(HISTORY_FILE, HISTORY_FILE + ".bak")
            return set()
    return set()

def save_history():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(posted_texts), f, ensure_ascii=False)

posted_texts = load_history()

# Очередь постов (хранит кортежи: ("text", текст) или ("photo", подпись, url))
def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except (json.JSONDecodeError, ValueError):
            return []
    return []

def save_queue():
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False)

queue = load_queue()

# ========== ФУНКЦИИ ПОЛУЧЕНИЯ КОНТЕНТА ==========
async def fetch_last_messages_from_channel(channel_username, limit=1):
    try:
        entity = await client.get_entity(channel_username)
        messages = []
        async for msg in client.iter_messages(entity, limit=limit):
            if msg.text and not msg.text.startswith("/") and msg.text.strip():
                messages.append(msg.text)
        return messages
    except Exception as e:
        logging.error(f"Ошибка {channel_username}: {e}")
        return []

def fetch_rss_articles(feed_url, limit=1):
    articles = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:limit]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")
            img_url = None
            summary_text = ""
            if summary:
                soup = BeautifulSoup(summary, 'html.parser')
                img_tag = soup.find('img')
                if img_tag and img_tag.get('src'):
                    img_url = img_tag['src']
                summary_text = soup.get_text(separator=' ').strip()
                if len(summary_text) > 500:
                    summary_text = summary_text[:500] + "..."
            caption = f"📰 <b>{title}</b>\n\n{summary_text}\n\n🔗 <a href='{link}'>Читать далее</a>"
            articles.append((caption, img_url))
        return articles
    except Exception as e:
        logging.error(f"Ошибка RSS {feed_url}: {e}")
        return []

def fetch_meme_with_image():
    try:
        response = requests.get("https://meme-api.com/gimme", timeout=10)
        data = response.json()
        if data and "url" in data:
            title = data.get("title", "Мем")
            url = data["url"]
            caption = f"😂 <b>{title}</b>\n\n#мем #программирование"
            return caption, url
    except Exception as e:
        logging.error(f"Ошибка мема: {e}")
    return None

# ========== УПРАВЛЕНИЕ ОЧЕРЕДЬЮ ==========
def is_duplicate(item):
    """Проверяет, есть ли такой пост уже в истории или в очереди."""
    if item[0] == "text":
        text = item[1]
        if text in posted_texts:
            return True
        for qitem in queue:
            if qitem[0] == "text" and qitem[1] == text:
                return True
    elif item[0] == "photo":
        caption = item[1]
        if caption in posted_texts:
            return True
        for qitem in queue:
            if qitem[0] == "photo" and qitem[1] == caption:
                return True
    return False

def add_to_queue(item):
    if is_duplicate(item):
        logging.info("Дубликат, не добавлен")
        return
    queue.append(item)
    save_queue()
    logging.info(f"Добавлен в очередь: {item[0]}")

# ========== СБОР КОНТЕНТА ==========
async def collect_and_post():
    logging.info("🔍 Начинаем сбор контента...")
    added = 0

    # 1. Мем
    if added < MAX_POSTS_PER_COLLECT and random.random() < 0.4:
        meme = fetch_meme_with_image()
        if meme:
            caption, url = meme
            add_to_queue(("photo", caption, url))
            added += 1
            await asyncio.sleep(1)

    # 2. RSS
    shuffled_feeds = RSS_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    for feed in shuffled_feeds:
        if added >= MAX_POSTS_PER_COLLECT:
            break
        articles = fetch_rss_articles(feed, limit=1)
        for caption, img_url in articles:
            if added >= MAX_POSTS_PER_COLLECT:
                break
            if img_url:
                add_to_queue(("photo", caption, img_url))
            else:
                add_to_queue(("text", caption))
            added += 1
            await asyncio.sleep(1)

    # 3. Telegram-каналы
    if added < MAX_POSTS_PER_COLLECT:
        shuffled_channels = SOURCE_CHANNELS.copy()
        random.shuffle(shuffled_channels)
        for channel in shuffled_channels:
            if added >= MAX_POSTS_PER_COLLECT:
                break
            msgs = await fetch_last_messages_from_channel(channel, limit=1)
            for msg in msgs:
                if added >= MAX_POSTS_PER_COLLECT:
                    break
                final_msg = f"📎 <b>Репост из {channel}</b>\n\n{msg}"
                add_to_queue(("text", final_msg))
                added += 1
                await asyncio.sleep(1)

    logging.info(f"✅ Сбор завершён. Добавлено {added} постов. В очереди {len(queue)}")

# ========== ПУБЛИКАЦИЯ ==========
async def publish_one():
    if not queue:
        logging.info("Очередь пуста, нечего публиковать")
        return

    item = queue.pop(0)
    save_queue()

    try:
        if item[0] == "text":
            text = item[1]
            if text in posted_texts:
                logging.info("Дубликат, пропускаем")
                return
            await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
            posted_texts.add(text)
            save_history()
            logging.info("✅ Опубликован текст")
        elif item[0] == "photo":
            caption, url = item[1], item[2]
            if caption in posted_texts:
                logging.info("Дубликат, пропускаем")
                return
            await bot.send_photo(chat_id=CHANNEL_ID, photo=url, caption=caption, parse_mode="HTML")
            posted_texts.add(caption)
            save_history()
            logging.info("✅ Опубликовано фото")
    except TelegramError as e:
        logging.error(f"Ошибка публикации: {e}")
        # Возвращаем в начало очереди
        queue.insert(0, item)
        save_queue()

# ========== ПЛАНИРОВЩИКИ ==========
def schedule_collect(loop):
    schedule.every(POST_INTERVAL_MINUTES).minutes.do(
        lambda: asyncio.run_coroutine_threadsafe(collect_and_post(), loop)
    )
    logging.info(f"⏰ Сбор контента запланирован каждые {POST_INTERVAL_MINUTES} минут")

def schedule_publish(loop):
    schedule.every(PUBLISH_INTERVAL_MINUTES).minutes.do(
        lambda: asyncio.run_coroutine_threadsafe(publish_one(), loop)
    )
    logging.info(f"⏰ Публикация запланирована каждые {PUBLISH_INTERVAL_MINUTES} минут")

def run_scheduler(loop):
    schedule_collect(loop)
    schedule_publish(loop)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ========== ТОЧКА ВХОДА ==========
async def main():
    await client.start()
    logging.info("🚀 Telethon клиент запущен")

    # Если очередь пуста, наполняем
    if not queue:
        logging.info("Очередь пуста, запускаем сбор контента...")
        await collect_and_post()

    # Сразу публикуем первый пост
    await publish_one()

    # Получаем текущий event loop
    loop = asyncio.get_running_loop()

    # Запускаем планировщик в отдельном потоке, передаём loop
    threading.Thread(target=run_scheduler, args=(loop,), daemon=True).start()

    # Держим асинхронный цикл активным
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Остановлено пользователем")
