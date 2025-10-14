# 🏎️ Hot Wheels Stock Tracker

Цей проєкт автоматично відстежує наявність моделей Hot Wheels на сайті **bi.ua**  
і відправляє сповіщення у Telegram, коли товари знову з’являються у продажу.

## ⚙️ Функціонал
- Автоматична перевірка товарів (кожні 30 хв із 6:00 до 22:00)
- Відправлення повідомлень у Telegram
- Telegram-бот з командами:
  - `/list` — список товарів, за якими йде стеження
  - `/add <url>` — додати новий товар
  - `/last` — коли була остання перевірка

## 🚀 Деплой бота на Render
1. Зареєструйся на [render.com](https://render.com)
2. Створи новий "Web Service" із цього репозиторію
3. Вкажи:
   - **Start Command:** `python bot_server.py`
   - **Environment variables:**
     - `TELEGRAM_TOKEN`
     - `TELEGRAM_CHAT_ID`
4. Render автоматично збере й запустить Flask-сервер
