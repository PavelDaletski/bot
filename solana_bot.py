import os
import time
import threading
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "ТУТ_ТВОЙ_BOT_TOKEN"
CHAT_ID = 1822483442

TOKEN_MINT = "2tgZJ6N7buMDq9HZWbzXvSPFq6MYWbrAGCoDD22Ypump"
COINGECKO_URL = f"https://api.coingecko.com/api/v3/simple/token_price/solana?contract_addresses={TOKEN_MINT}&vs_currencies=usd"

check_interval = 30  # секунд
min_price = None
max_price = None
# =============================================


# ---------- HTTP сервер (для Render) ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


# ---------- Получение цены ----------
def get_price():
    r = requests.get(COINGECKO_URL, timeout=10)
    data = r.json()
    return data[TOKEN_MINT.lower()]["usd"]


# ---------- Проверка цены ----------
def price_watcher(app):
    global min_price, max_price

    while True:
        try:
            price = get_price()

            if min_price and price <= min_price:
                app.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"🔻 Цена УПАЛА\nЦена: ${price}\nМинимум: ${min_price}"
                )
                min_price = None

            if max_price and price >= max_price:
                app.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"🚀 Цена ВЫРОСЛА\nЦена: ${price}\nМаксимум: ${max_price}"
                )
                max_price = None

        except Exception as e:
            print("Ошибка:", e)

        time.sleep(check_interval)


# ---------- Команды ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Бот запущен\n"
        "/setmin ЦЕНА\n"
        "/setmax ЦЕНА\n"
        "/status"
    )

async def setmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global min_price
    min_price = float(context.args[0])
    await update.message.reply_text(f"🔻 Минимальная цена установлена: ${min_price}")

async def setmax(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global max_price
    max_price = float(context.args[0])
    await update.message.reply_text(f"🚀 Максимальная цена установлена: ${max_price}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 Статус:\n"
        f"Min: {min_price}\n"
        f"Max: {max_price}"
    )


# ---------- Запуск ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setmin", setmin))
    app.add_handler(CommandHandler("setmax", setmax))
    app.add_handler(CommandHandler("status", status))

    threading.Thread(target=price_watcher, args=(app,), daemon=True).start()
    threading.Thread(target=run_server, daemon=True).start()

    app.run_polling()


if __name__ == "__main__":
    main()
