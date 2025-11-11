# solana_bot.py — версия с health endpoint для Render
import requests
import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# === Настройки ===
ADDRESS = "CxKFkAu8LngjYmcCjT2siKyAiMrKjbTB96NRXg8jqHH6"
TELEGRAM_BOT_TOKEN = "8162509137:AAEJE0QFu1EIovWpO4MMTdRh2zKC-n-_ZT4"
TELEGRAM_CHAT_ID = "1822483442"
CHECK_INTERVAL = 30  # секунд между проверками
SOLSCAN_TRANSFER_URL = f"https://public-api.solscan.io/account/transfer?address={ADDRESS}&limit=5"

last_transfers = set()

# === Telegram ===
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if not r.ok:
            print(f"Ошибка Telegram: {r.status_code} {r.text}")
    except Exception as e:
        print("Ошибка при отправке Telegram:", e)

# === Получаем последние трансферы с Solscan ===
def get_recent_transfers():
    try:
        url = SOLSCAN_TRANSFER_URL
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return data
            # иногда Solscan возвращает объект с key 'data'
            if isinstance(data, dict) and 'data' in data:
                return data['data']
        else:
            print(f"⚠️ Solscan returned HTTP {r.status_code}: {r.text}")
    except Exception as e:
        print("⚠️ Ошибка Solscan API:", e)
    return []

# === Основная логика ===
def poll_loop():
    global last_transfers
    print("🚀 Запущен poll loop — отслеживаем трансферы для", ADDRESS)
    send_telegram_message("✅ Бот запущен и отслеживает трансферы (Solscan).")
    while True:
        try:
            transfers = get_recent_transfers()
            new_hashes = []
            for t in transfers:
                # ключи в ответе Solscan: 'txHash' или 'txhash' — проверяем оба
                sig = t.get("txHash") or t.get("txhash") or t.get("tx")
                if not sig:
                    continue
                if sig not in last_transfers:
                    new_hashes.append(sig)
                    last_transfers.add(sig)
            # отправляем уведомления от старых к новым
            for sig in reversed(new_hashes):
                msg = (
                    "💸 *Новый трансфер на Solana!*\n\n"
                    f"🔗 [Посмотреть в Solscan](https://solscan.io/tx/{sig})\n"
                    f"📄 [Страница трансферов кошелька](https://solscan.io/account/{ADDRESS}#transfers)"
                )
                send_telegram_message(msg)
                print("📩 Уведомление отправлено для:", sig)
        except Exception as e:
            print("⚠️ Ошибка в poll_loop:", e)
        time.sleep(CHECK_INTERVAL)

# === Минимальный HTTP health сервер (GET + HEAD) ===
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        body = f"OK - bot alive for {ADDRESS}\n"
        self.wfile.write(body.encode("utf-8"))

    def do_HEAD(self):
        # чтобы Render не получал 501 на HEAD
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"🌐 Health server started on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    # Запускаем health-server в фоне
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()

    # Запускаем основной polling loop
    poll_loop()
