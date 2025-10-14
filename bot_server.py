import os
import json
from flask import Flask, request
from datetime import datetime
import requests

app = Flask(__name__)

# === Налаштування ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SECRET_CODE = os.getenv("BOT_SECRET_CODE")  # захист від спаму

PRODUCTS_FILE = "products.json"
LAST_CHECK_FILE = "last_check.txt"

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"


# === Допоміжні функції ===
def send_message(chat_id, text):
    """Надсилає повідомлення у Telegram."""
    requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})


def load_products():
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)


def get_last_check():
    """Зчитує час останньої перевірки з last_check.txt."""
    if not os.path.exists(LAST_CHECK_FILE):
        return "Інформація про останню перевірку відсутня."
    with open(LAST_CHECK_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


# === Обробка повідомлень ===
@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" not in data:
        return "ok"

    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()

    if not text:
        return "ok"

    # --- /list ---
    if text.startswith("/list"):
        products = load_products()
        if not products:
            send_message(chat_id, "📭 Немає товарів для відстеження.")
        else:
            message = "📦 *Список товарів для відстеження:*\n\n"
            for p in products:
                status = "🔔" if p.get("notified") else "🔕"
                message += f"{status} {p['title']}\n{p['url']}\n\n"
            send_message(chat_id, message)

    # --- /add ---
    elif text.startswith("/add"):
        parts = text.split(" ", 3)
        if len(parts) < 4:
            send_message(chat_id, "❗ Формат команди:\n`/add Назва URL СЕКРЕТНИЙ_КОД`")
            return "ok"

        _, title, url, code = parts

        if code != SECRET_CODE:
            send_message(chat_id, "🚫 Невірний секретний код.")
            return "ok"

        products = load_products()
        if any(p["url"] == url for p in products):
            send_message(chat_id, "⚠️ Цей товар уже є в списку.")
            return "ok"

        products.append({
            "title": title,
            "url": url,
            "notified": False
        })
        save_products(products)
        send_message(chat_id, f"✅ Товар *{title}* додано до списку відстеження.")

    # --- /last ---
    elif text.startswith("/last"):
        last_check = get_last_check()
        send_message(chat_id, f"🕓 Остання перевірка виконана:\n{last_check}")

    # --- /help ---
    elif text.startswith("/help"):
        help_text = (
            "🤖 *Команди бота:*\n"
            "/list — показати список товарів\n"
            "/add Назва URL СЕКРЕТНИЙ_КОД — додати новий товар\n"
            "/last — показати коли була остання перевірка\n"
        )
        send_message(chat_id, help_text)

    else:
        send_message(chat_id, "❔ Невідома команда. Використай /help для списку команд.")

    return "ok"


@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is running."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
