import time
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = "8162509137:AAEJE0QFu1EIovWpO4MMTdRh2zKC-n-_ZT4"
CHAT_ID = "1822483442"
ACCOUNT = "CxKFkAu8LngjYmcCjT2siKyAiMrKjbTB96NRXg8jqHH6"
CHECK_INTERVAL = 15  # секунд

RPC_URLS = [
    "https://api.mainnet-beta.solana.com",
    "https://rpc.ankr.com/solana",
    "https://solana-mainnet.g.alchemy.com/v2/demo",
    "https://free.rpcpool.com"
]

def send_telegram_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
        r = requests.post(url, data=data)
        print("📨 Telegram response:", r.text)
    except Exception as e:
        print("⚠️ Ошибка отправки Telegram:", e)

def get_latest_signature():
    for rpc in RPC_URLS:
        try:
            print(f"🔗 Проверяем RPC: {rpc}")
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [ACCOUNT, {"limit": 1}]
            }
            r = requests.post(rpc, json=payload, timeout=10)
            r.raise_for_status()
            sigs = r.json().get("result", [])
            if sigs:
                print("📦 Последняя сигнатура:", sigs[0]["signature"])
                return sigs[0]["signature"]
        except Exception as e:
            print(f"⚠️ RPC ошибка ({rpc}):", e)
    return None

def check_new_transfer(last_sig):
    for rpc in RPC_URLS:
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [ACCOUNT, {"limit": 1}]
            }
            r = requests.post(rpc, json=payload, timeout=10)
            r.raise_for_status()
            sigs = r.json().get("result", [])
            if not sigs:
                print("⏳ Нет новых трансферов на RPC:", rpc)
                continue

            latest_sig = sigs[0]["signature"]
            if latest_sig != last_sig:
                print(f"💸 Новый трансфер найден: {latest_sig}")
                send_telegram_message(
                    f"💸 <b>Новый трансфер!</b>\n"
                    f"<a href='https://solscan.io/tx/{latest_sig}'>Открыть в Solscan</a>"
                )
                return latest_sig
        except Exception as e:
            print(f"⚠️ RPC ошибка ({rpc}):", e)
    return last_sig

# Простой health сервер для Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    server = HTTPServer(("0.0.0.0", 10000), SimpleHandler)
    print("🌍 Health server запущен на порту 10000")
    server.serve_forever()

if __name__ == "__main__":
    send_telegram_message("✅ Бот запущен и отслеживает новые трансферы.")
    last_sig = get_latest_signature()
    if not last_sig:
        send_telegram_message("⚠️ Не удалось получить последнюю сигнатуру при запуске.")
    else:
        print("🚀 Отслеживаем трансферы для адреса:", ACCOUNT)

    import threading
    threading.Thread(target=run_server, daemon=True).start()

    while True:
        last_sig = check_new_transfer(last_sig)
        time.sleep(CHECK_INTERVAL)
