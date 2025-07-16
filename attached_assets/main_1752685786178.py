import requests
import time
import os
import datetime
import telegram
from telegram.error import TelegramError

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID").replace("@", "")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")

bot = telegram.Bot(token=TELEGRAM_TOKEN)

last_price = None
last_news_time = ""

def get_eth_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    response = requests.get(url)
    return response.json()["ethereum"]["usd"]

def get_news():
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&currencies=ETH&filter=important"
    response = requests.get(url)
    data = response.json()
    if "results" in data and data["results"]:
        return data["results"]
    return []

def send_message(msg):
    try:
        bot.send_message(chat_id=f"@{TELEGRAM_USER_ID}", text=msg)
    except TelegramError as e:
        print("Błąd wysyłania:", e)

def check():
    global last_price, last_news_time
    try:
        price = get_eth_price()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if last_price:
            diff_percent = ((price - last_price) / last_price) * 100
            if abs(diff_percent) >= 3:
                send_message(f"⚠️ ETH zmieniło się o {diff_percent:.2f}% i wynosi {price}$")
        last_price = price
        print(f"[{now}] Cena ETH: {price}$")
    except Exception as e:
        print("Błąd ceny:", e)

    try:
        news = get_news()
        for article in news:
            if article["published_at"] != last_news_time:
                title = article["title"]
                url = article["url"]
                send_message(f"📰 Nowy news: {title}\n{url}")
                last_news_time = article["published_at"]
    except Exception as e:
        print("Błąd newsów:", e)

def main():
    while True:
        now = datetime.datetime.now()
        if now.hour in [8, 12, 16, 20] and now.minute == 0:
            check()
            time.sleep(60)
        time.sleep(30)

if __name__ == "__main__":
    send_message("✅ Bot ETH uruchomiony.")
    main()
