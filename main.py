import os
import time
import logging
import requests
from typing import List, Dict, Any

# =========================
# CONFIG
# =========================
POLYMARKET_API = "https://gamma-api.polymarket.com/markets"
SCAN_INTERVAL = 60  # seconds
MIN_VOLUME = 20000
ARBITRAGE_THRESHOLD = 1.0

TELEGRAM_TOKEN = os.getenv("8674263944:AAGR0RuvKBI1eTyQwQwkAVtVD6Qs9IUfXV4")
TELEGRAM_CHAT_ID = os.getenv("7803455800")

REQUEST_TIMEOUT = 10
MAX_RETRIES = 5
RETRY_DELAY = 2

# =========================
# LOGGING SETUP
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)

# =========================
# TELEGRAM
# =========================
def send_telegram(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram config missing")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            res = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)

            if res.status_code == 200:
                logger.info("Telegram sent successfully")
                return
            else:
                logger.warning(f"Telegram failed (status {res.status_code}): {res.text}")

        except Exception as e:
            logger.error(f"Telegram error: {e}")

        time.sleep(RETRY_DELAY * attempt)

    logger.error("Telegram send FAILED after retries")


# =========================
# FETCH MARKETS
# =========================
def fetch_markets() -> List[Dict[str, Any]]:
    try:
        response = requests.get(POLYMARKET_API, timeout=REQUEST_TIMEOUT)

        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}")
            return []

        data = response.json()

        if not isinstance(data, list):
            logger.error("Unexpected API format")
            return []

        return data

    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return []


# =========================
# ARBITRAGE LOGIC
# =========================
def find_arbitrage(markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    opportunities = []

    for market in markets:
        try:
            if not market.get("active", False):
                continue

            volume = float(market.get("volume", 0))
            if volume < MIN_VOLUME:
                continue

            outcomes = market.get("outcomes", [])
            prices = market.get("outcomePrices", [])

            if len(outcomes) != 2 or len(prices) != 2:
                continue

            yes_price = float(prices[0])
            no_price = float(prices[1])

            total = yes_price + no_price

            if total < ARBITRAGE_THRESHOLD:
                profit = round((1 - total) * 100, 2)

                opportunities.append({
                    "question": market.get("question", "N/A"),
                    "yes": yes_price,
                    "no": no_price,
                    "total": total,
                    "profit": profit,
                    "volume": volume,
                    "url": f"https://polymarket.com/market/{market.get('slug', '')}"
                })

        except Exception as e:
            logger.warning(f"Parse error: {e}")
            continue

    return opportunities


# =========================
# FORMAT MESSAGE
# =========================
def format_message(opps: List[Dict[str, Any]]) -> str:
    lines = ["🚨 <b>Arbitrage Opportunity Found</b>\n"]

    for opp in opps:
        line = (
            f"<b>{opp['question']}</b>\n"
            f"YES: {opp['yes']:.3f} | NO: {opp['no']:.3f}\n"
            f"SUM: {opp['total']:.3f}\n"
            f"PROFIT: {opp['profit']}%\n"
            f"VOL: {int(opp['volume'])}\n"
            f"<a href='{opp['url']}'>View Market</a>\n"
        )
        lines.append(line)

    return "\n".join(lines)


# =========================
# MAIN LOOP
# =========================
def main():
    send_telegram("✅ Bot started successfully")
    logger.info("🔥 Polymarket Arbitrage Bot Started")

    seen = set()

    while True:
        try:
            logger.info("Scanning markets...")

            markets = fetch_markets()

            if not markets:
                logger.warning("No markets fetched")
                time.sleep(SCAN_INTERVAL)
                continue

            opps = find_arbitrage(markets)

            logger.info(f"Found {len(opps)} opportunities")

            new_opps = []
            for opp in opps:
                key = opp["url"]

                if key not in seen:
                    seen.add(key)
                    new_opps.append(opp)

            if new_opps:
                msg = format_message(new_opps)
                send_telegram(msg)

            time.sleep(SCAN_INTERVAL)

        except Exception as e:
            logger.critical(f"MAIN LOOP CRASH: {e}", exc_info=True)
            time.sleep(10)


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    main()
