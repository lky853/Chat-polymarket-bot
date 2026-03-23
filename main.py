import requests
import time
import os

print("🔥 BOT STARTED")

# ✅ 從 Railway 環境變數讀取
TELEGRAM_TOKEN = os.environ.get("8674263944:AAGR0RuvKBI1eTyQwQwkAVtVD6Qs9IUfXV4")
CHAT_ID = os.environ.get("7803455800")

EDGE_THRESHOLD = 0.02  # 2%

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": msg
        }
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

def get_markets():
    all_markets = []
    page = 1

    while True:
        try:
            url = f"https://gamma-api.polymarket.com/markets?page={page}"
            res = requests.get(url, timeout=10)
            data = res.json()

            if not data:
                break

            all_markets.extend(data)
            page += 1
            time.sleep(0.5)

        except Exception as e:
            print("Fetch error:", e)
            break

    return all_markets

def check_arbitrage():
    markets = get_markets()

    for m in markets:
        try:
            yes_price = float(m["outcomes"][0]["price"])
            no_price = float(m["outcomes"][1]["price"])
            volume = float(m.get("volume", 0))

            edge = 1 - (yes_price + no_price)

            if edge > EDGE_THRESHOLD and volume < 20000:
                msg = f"""🚨 Arbitrage Alert

{m['question']}

YES: {yes_price}
NO: {no_price}
Edge: {round(edge*100,2)}%

https://polymarket.com/event/{m['slug']}
"""
                send_telegram(msg)

        except Exception:
            continue


# ✅ 啟動通知（超重要測試）
send_telegram("✅ Bot 已成功啟動")

# ✅ 主循環
while True:
    try:
        check_arbitrage()
        print("running...")
        time.sleep(60)  # 每60秒掃一次
    except Exception as e:
        print("Loop error:", e)
        time.sleep(10)
