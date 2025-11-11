import requests
import time

# === Настройки ===
ADDRESS = "CxKFkAu8LngjYmcCjT2siKyAiMrKjbTB96NRXg8jqHH6"
TELEGRAM_BOT_TOKEN = "8162509137:AAEJE0QFu1EIovWpO4MMTdRh2zKC-n-_ZT4"
TELEGRAM_CHAT_ID = "1822483442"
CHECK_INTERVAL = 5  # секунд между проверками
SOLSCAN_API = f"https://public-api.solscan.io/account/tokens?address={ADDRESS}"

last_transfers = set()

# === Отправка уведомления в Telegram ===
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
            print(f"Ошибка Telegram: {r.status_code}, {r.text}")
    except Exception as e:
        print("Ошибка при отправке Telegram:", e)

# === Получаем последние трансферы с Solscan ===
def get_recent_transfers():
    try:
        url = f"https://public-api.solscan.io/account/transfer?address={ADDRESS}&limit=5"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
        print(f"⚠️ Ошибка при получении трансферов: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Ошибка Solscan API: {e}")
    return []

# === Основная функция ===
def main():
    global last_transfers

    print("🚀 Бот запущен и отслеживает трансферы!")
    print(f"📍 Адрес: {ADDRESS}\n")

    send_telegram_message("✅ Бот запущен и отслеживает *трансферы* на Solana!")

    while True:
        transfers = get_recent_transfers()
        new_items = []

        for t in transfers:
            sig = t.get("txHash")
            if sig and sig not in last_transfers:
                last_transfers.add(sig)
                new_items.append(sig)

        for sig in reversed(new_items):
            msg = (
                "💸 *Новый трансфер на Solana!*\n\n"
                f"🔗 [Посмотреть в Solscan](https://solscan.io/tx/{sig})\n"
                f"📄 [Страница кошелька](https://solscan.io/account/{ADDRESS}#transfers)"
            )
            send_telegram_message(msg)
            print(f"📩 Новое уведомление: {sig}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
