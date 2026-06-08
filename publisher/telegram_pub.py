import os
import requests
from dotenv import load_dotenv

load_dotenv()


def send(text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not channel:
        return False
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": channel, "text": text},
        timeout=15,
    )
    return resp.ok and "result" in resp.json()
