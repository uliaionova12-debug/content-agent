import os
import requests
from dotenv import load_dotenv

load_dotenv()


def post(text: str) -> bool:
    token = os.getenv("VK_ACCESS_TOKEN")
    owner_id = os.getenv("VK_OWNER_ID")  # отрицательное число для группы, например -12345678
    if not token or not owner_id:
        return False
    resp = requests.post(
        "https://api.vk.com/method/wall.post",
        params={
            "access_token": token,
            "owner_id": owner_id,
            "message": text,
            "v": "5.199",
        },
        timeout=15,
    )
    data = resp.json()
    return resp.ok and "response" in data
