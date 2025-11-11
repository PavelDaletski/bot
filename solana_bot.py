import requests
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# === Настройки ===
ADDRESS = "CxKFkAu8LngjYmcCjT2siKyAiMrKjbTB96NRXg8jqHH6"
RPC_URL = "https://api.mainnet-beta.solana.com"
CHECK_INTERVAL = 8  # Проверка каждые 30 секунд

BOT_TOKEN = "8162509137:AAEJE0QFu1EIovWpO4MMTdRh2zKC-n-_ZT4"
CHAT_ID = "1822483442"

last_signature = None


# === Отправка сообщений в Telegram ===
def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ Telegram не настроен, сообщение не отправлено:", text)
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print("⚠️ Ошибка Telegram:", r.text)
    except Exception as e:
        print("⚠️ Ошибка при отправке в Telegram:", e)


# === Получение последних транзакций ===
def get_recent_transfers():
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [ADDRESS, {"limit": 5}]
    }
    try:
        response = requests.post(RPC_URL, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json().get("result", [])
        return data
    except Exception as e:
        print(f"⚠️ RPC ошибка ({RPC_URL}): {e}")
        return []


# === Проверка новых трансферов ===
def check_new_transfers():
    global last_signature
    data = get_recent_transfers()

    if not data:
        print("⚠️ Нет данных от RPC.")
        return

    new_sigs = []
    for tx in data:
        sig = tx.get("signature")
        if not sig:
            continue
        if sig == last_signature:
            break
        new_sigs.append(sig)

    if not new_sigs:
        print("⏳ Нет новых трансферов...")
        return

    # Отправляем уведомления о новых трансферах
    for sig in reversed(new_sigs):
        solscan_url = f"https://solscan.io/account/{ADDRESS}#transfers"
        msg = (
            f"💸 *Новый трансфер обнаружен!*\n"
            f"🔗 [Открыть в Solscan]({solscan_url})\n"
            f"📍 Адрес: `{ADDRESS}`"
        )
        print(msg)
        send_telegram_message(msg)

    last_signature = data[0].get("signature")


# === HTTP сервер для Render (чтобы бот считался активным) ===
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running")


def start_server():
    server = HTTPServer(('0.0.0.0', 10000), HealthHandler)
    print("🌐 Health сервер запущен на порту 10000")
    server.serve_forever()


# === Главный цикл ===
def main():
    global last_signature
    print(f"🚀 Бот запущен! Отслеживаем кошелёк:\n{ADDRESS}\n")

    send_telegram_message("✅ Бот запущен и следит за новыми трансферами на Solana!")

    # Инициализация последней транзакции
    txs = get_recent_transfers()
    if txs:
        last_signature = txs[0].get("signature")
        print(f"🟢 Последняя сигнатура при запуске: {last_signature}")
    else:
        print("⚠️ Не удалось получить последние трансферы при запуске.")

    # Основной цикл
    while True:
        try:
            check_new_transfers()
        except Exception as e:
            print("⚠️ Ошибка в основном цикле:", e)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    main()
