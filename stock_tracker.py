import aiohttp
import asyncio
import json
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from telegram import Bot
import os

# ---- Налаштування логування ----
logging.basicConfig(
    filename='stock_tracker.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---- Робота з файлами ----
def load_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"{filename} не знайдено")
        return None
    except Exception as e:
        logging.error(f"Помилка при зчитуванні {filename}: {e}")
        return None


def save_json(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Помилка при збереженні {filename}: {e}")


# ---- HTTP-запит ----
async def fetch_page(session, url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status == 200:
                return await resp.text()
            else:
                logging.warning(f"Статус {resp.status} при отриманні {url}")
    except Exception as e:
        logging.error(f"Помилка при отриманні {url}: {e}")
    return None


# ---- Перевірка наявності ----
def check_availability(html, url, product, config):
    domain = urlparse(url).netloc
    store_config = next((s for s in config['stores'].values() if domain in s['base_url']), None)
    if not store_config:
        logging.warning(f"Конфігурація для {domain} не знайдена")
        return None

    soup = BeautifulSoup(html, 'html.parser')
    title_elem = soup.select_one(store_config['title_selector'])
    title = title_elem.text.strip() if title_elem else product.get('title', 'Без назви')

    buy_btn = soup.select_one(store_config['buy_button_selector'])
    status = "Немає в наявності"
    if buy_btn and buy_btn.text.strip() == store_config['buy_button_text']:
        status = "В наявності"

    return {"url": url, "title": title, "status": status}


# ---- Telegram ----
def load_telegram_config():
    """Повертає Telegram-конфіг з файлу або з environment."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if token and chat_id:
        logging.info("Telegram-конфіг завантажено з environment")
        return {"token": token, "chat_id": chat_id}

    # fallback: локальний файл
    cfg = load_json("telegram_config.json")
    if cfg and "token" in cfg and "chat_id" in cfg:
        logging.info("Telegram-конфіг завантажено з telegram_config.json")
        return cfg

    logging.error("Telegram-конфіг не знайдено")
    return None


async def send_telegram(product, telegram_config):
    try:
        bot = Bot(token=telegram_config['token'])
        message = f"🟢 Товар в наявності!\n{product['title']}\n{product['url']}"
        await bot.send_message(chat_id=telegram_config['chat_id'], text=message)
        logging.info(f"Відправлено Telegram для {product['title']}")
        return True
    except Exception as e:
        logging.error(f"Помилка Telegram для {product['title']}: {e}")
        return False


# ---- Основна логіка ----
async def check_products_once(config, products, telegram_config):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, p['url']) for p in products]
        pages = await asyncio.gather(*tasks)

    updated = False
    for product, html in zip(products, pages):
        if not html:
            continue
        result = check_availability(html, product['url'], product, config)
        if not result:
            continue

        if result['status'] == "В наявності":
            if not product.get('notified', False):
                if await send_telegram(product, telegram_config):
                    product['notified'] = True
                    updated = True
        else:
            if product.get('notified', False):
                product['notified'] = False
                updated = True

    if updated:
        save_json('products.json', products)
        logging.info("Оновлено products.json")


# ---- Головна функція ----
async def main():
    config = load_json('config.json')
    products = load_json('products.json')
    telegram_config = load_telegram_config()

    if not all([config, products, telegram_config]):
        logging.error("Не вдалося завантажити необхідні конфігурації. Завершення роботи.")
        return

    check_interval = config.get('check_interval', 1200)  # 20 хв за замовчуванням
    run_once = os.getenv("RUN_ONCE", "false").lower() == "true"

    while True:
        logging.info("🔍 Початок перевірки товарів")
        await check_products_once(config, products, telegram_config)
        logging.info("✅ Перевірка завершена")

        if run_once:
            break  # GitHub режим — один прохід

        logging.info(f"Очікування {check_interval} секунд перед наступною перевіркою...")
        await asyncio.sleep(check_interval)


if __name__ == "__main__":
    asyncio.run(main())
