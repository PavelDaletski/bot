import requests
import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ========= НАСТРОЙКИ =========

TOKEN_MINT = "2tgZJ6N7buMDq9HZWbzXvSPFq6MYWbrAGCoDD22Ypump"

MIN_PRICE = 0.00001     # 🔽 цена падения
MAX_PRICE = 0.00003     # 🔼 цена пробоя вверх

CHECK_INTERVAL = 20     # секунд

TELEGRAM_BOT_TOKEN = "8162509137:AAEJE0QFu1EIovWpO4MMTdRh2zKC-n-_ZT4"
TELEGRAM_CHAT_ID = "1822483442"

# ========= СОСТОЯНИЕ =========

previous_price = None
alert_down_sent = False
alert_up_sent = False

# ========= TELEGRAM =========

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# ========= ЦЕНА С DexScreener =========

def get_price():
    url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_MINT}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()
        pairs = data.get("pairs", [])
        if not pairs:
            return None

        pair = max(
            pairs,
            key=lambda x: float(x.get("liquidity", {}).get("usd", 0))
        )
        return float(pair["priceUsd"])

    except Exception as e:
        print("Price error:", e)
        return None

# ========= ОСНОВНОЙ ЦИКЛ =========

def price_loop():
    global previous_price, alert_down_sent, alert_up_sent

    send_telegram(
        "✅ *Бот запущен*\n\n"
        f"Mint: `{TOKEN_MINT}`\n"
        f"📉 Падение ниже: `{MIN_PRICE}`\n"
        f"📈 Пробой выше: `{MAX_PRICE}`"
    )

    while True:
        price = get_price()
        if price is None:
            time.sleep(CHECK_INTERVAL)
            continue

        print("Цена:", price)

        # ---- ПРОБОЙ ВВЕРХ ----
        if (
            previous_price is not None
            and not alert_up_sent
            and previous_price < MAX_PRICE
            and price >= MAX_PRICE
        ):
            alert_up_sent = True
            send_telegram(
                "📈 *ПРОБОЙ ВВЕРХ!*\n\n"
                f"Цена: *{price:.10f} USD*\n"
                f"Уровень: `{MAX_PRICE}`\n\n"
                f"🔗 https://dexscreener.com/solana/{TOKEN_MINT}"
            )

        # ---- ПАДЕНИЕ ВНИЗ ----
        if (
            previous_price is not None
            and not alert_down_sent
            and previous_price > MIN_PRICE
            and price <= MIN_PRICE
        ):
            alert_down_sent = True
            send_telegram(
                "📉 *ПАДЕНИЕ ЦЕНЫ!*\n\n"
                f"Цена: *{price:.10f} USD*\n"
                f"Уровень: `{MIN_PRICE}`\n\n"
                f"🔗 https://dexscreener.com/solana/{TOKEN_MINT}"
            )

        previous_price = price
        time.sleep(CHECK_INTERVAL)

# ========= HEALTH SERVER (Render) =========

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

# ========= START =========

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    price_loop()
