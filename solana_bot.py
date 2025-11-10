import requests
import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================== Настройки ==================
ADDRESS = "CxKFkAu8LngjYmcCjT2siKyAiMrKjbTB96NRXg8jqHH6"  # твой кошелек
CHECK_INTERVAL = 30  # секунд между проверками
BOT_TOKEN = "8162509137:AAEJE0QFu1EIovWpO4MMTdRh2zKC-n-_ZT4"
CHAT_ID = "1822483442"
RPC_URLS = [
    "https://api.mainnet-beta.solana.com",  # рабочий официальный RPC Solana
    "https://rpc.ankr.com/solana"          # запасной RPC
]

last_signatures = set()

# ================== Telegram ==================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True}
    try:
        r = requests.post(url, data=payload, timeout=10)
        if not r.ok:
            print("Ошибка Telegram:", r.status_code, r.text)
    except Exception as e:
        print("Ошибка Telegram:", e)

# ================== HTTP health server для Render ==================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_http_server():
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("", port), HealthHandler)
    print(f"🌐 HTTP health server запущен на порту {port}")
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

# ================== RPC запрос ==================
def rpc_request(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or []
    }
    for rpc in RPC_URLS:
        try:
            r = requests.post(rpc, json=payload, timeout=10)
            r.raise_for_status()
            return r.json().get("result")
        except Exception as e:
            print(f"⚠️ RPC ошибка ({rpc}): {e}")
    return None

# ================== Получение новых транзакций ==================
def get_new_transfers():
    global last_signatures
    sigs = rpc_request("getSignaturesForAddress", [ADDRESS, {"limit": 20}])
    if not sigs:
        return []

    new_sigs = []
    for tx in sigs:
        sig = tx.get("signature")
        if sig and sig not in last_signatures:
            new_sigs.append(sig)

    for sig in new_sigs:
        last_signatures.add(sig)

    return list(reversed(new_sigs))  # старые -> новые

# ================== Основной цикл ==================
def main():
    print("🚀 Бот запущен! Отслеживаем трансферы...")

    # Тестовое уведомление при старте
    send_telegram_message(
        f"✅ Бот успешно запущен и отслеживает новые трансферы на кошельке {ADDRESS}!\n"
        f"🔗 https://solscan.io/account/{ADDRESS}#transfers"
    )

    # Инициализация последних транзакций
    init_sigs = rpc_request("getSignaturesForAddress", [ADDRESS, {"limit": 20}])
    if init_sigs:
        for tx in init_sigs:
            last_signatures.add(tx.get("signature"))

    while True:
        time.sleep(CHECK_INTERVAL)
        new_txs = get_new_transfers()
        if new_txs:
            for sig in new_txs:
                # Теперь всегда ведём на страницу всех трансферов кошелька
                url = f"https://solscan.io/account/{ADDRESS}#transfers"
                print(f"💸 Новая транзакция: {url}")
                msg = f"💸 Обнаружен новый трансфер на кошельке!\n🔗 {url}\n📍 Адрес: {ADDRESS}"
                send_telegram_message(msg)
        else:
            print("⏳ Нет новых трансферов...")

if __name__ == "__main__":
    main()
