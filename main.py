import requests
import time
import os

TELEGRAM_TOKEN = os.environ.get("8663329966:AAE5GeFrd1J5lvwqg8iHaVlaxRbsMn9NMck")
CHAT_ID = os.environ.get("7803455800")

EDGE_THRESHOLD = 0.02

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    requests.post(url, data=data)

def get_markets():
    all_markets = []
    page = 1

    while True:
        url = f"https://gamma-api.polymarket.com/markets?page={page}"
        res = requests.get(url)
        data = res.json()

        if not data:
            break

        all_markets.extend(data)
        page += 1
        time.sleep(0.5)

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

        except:
            continue

while True:
    check_arbitrage()
    time.sleep(60)
