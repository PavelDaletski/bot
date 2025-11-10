import requests
import time

# ================== НАСТРОЙКА ==================
ADDRESS = "CxKFkAu8LngjYmcCjT2siKyAiMrKjbTB96NRXg8jqHH6"

# Рабочие публичные RPC
RPC_URLS = [
    "https://api.mainnet-beta.solana.com",
    "https://rpc.ankr.com/solana",
    "https://solana-rpc.com",
    "https://api.rpcpool.com/solana"
]

CHECK_INTERVAL = 30  # секунд между проверками

# Telegram
TELEGRAM_BOT_TOKEN = "8162509137:AAEJE0QFu1EIovWpO4MMTdRh2zKC-n-_ZT4"
TELEGRAM_CHAT_ID = "1822483442"
last_signature = None

# ================== ФУНКЦИИ ==================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Ошибка Telegram: {e}")

def rpc_request(method, params=None):
    for rpc in RPC_URLS:
        try:
            response = requests.post(
                rpc,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []},
                timeout=20
            )
            if response.status_code == 200:
                return response.json().get("result")
        except Exception as e:
            print(f"⚠️ RPC ошибка ({rpc}): {e}")
    return None

def get_latest_transactions(limit=10):
    return rpc_request("getSignaturesForAddress", [ADDRESS, {"limit": limit}]) or []

def parse_swaps(tx_sig):
    tx_info = rpc_request("getTransaction", [tx_sig, {"encoding": "jsonParsed"}])
    if not tx_info:
        return []

    swaps = []
    instructions = tx_info.get("transaction", {}).get("message", {}).get("instructions", [])

    for instr in instructions:
        program = instr.get("program")
        parsed = instr.get("parsed", {})

        # Проверка swap на DEX (Raydium, Serum, Jupiter)
        if program in ["spl-token", "serum", "raydium", "jupiter"] and parsed.get("type") in ["swap", "transferChecked"]:
            info = parsed.get("info", {})
            from_token = info.get("source")
            to_token = info.get("destination")
            amount_in = info.get("amount")
            amount_out = info.get("amountOut") or info.get("amount")
            swaps.append(
                f"🔄 Swap\nОт: {from_token}\nКому: {to_token}\nПродано: {amount_in}\nКуплено: {amount_out}"
            )

    return swaps

# ================== ОСНОВНОЙ ЦИКЛ ==================
def main():
    global last_signature
    print("🚀 Бот запущен! Отслеживаем покупки/продажи токенов на Solana.")
    send_telegram_message("✅ Бот запущен и отслеживает swap транзакции!")

    # --- Инициализация: показываем последнюю транзакцию при старте ---
    latest = get_latest_transactions(limit=1)
    if latest:
        last_sig = latest[0]["signature"]
        swaps = parse_swaps(last_sig)
        if swaps:
            message = "\n\n".join(swaps) + f"\n🔗 [Посмотреть все трансферы](https://solscan.io/account/{ADDRESS}#transfers)"
            print(message)
            send_telegram_message(message)
        last_signature = last_sig
        print(f"🟢 Начинаем с последней сигнатуры: {last_signature}")
    else:
        print("⚠️ Не удалось получить последнюю транзакцию при запуске.")

    # --- Основной цикл ---
    while True:
        time.sleep(CHECK_INTERVAL)
        txs = get_latest_transactions(limit=5)

        for tx in reversed(txs):
            sig = tx["signature"]
            if sig == last_signature:
                break

            swaps = parse_swaps(sig)
            if swaps:
                message = "\n\n".join(swaps) + f"\n🔗 [Посмотреть все трансферы](https://solscan.io/account/{ADDRESS}#transfers)"
                print(message)
                send_telegram_message(message)

        if txs:
            last_signature = txs[0]["signature"]

if __name__ == "__main__":
    main()