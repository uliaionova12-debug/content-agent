import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client = None
MODEL_NAME = "llama-3.3-70b-versatile"


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY не задан в .env")
        _client = Groq(api_key=api_key)
    return _client


def generate(system: str, user: str, max_tokens: int = 2048) -> str:
    """Генерация текста — для коротких форматов."""
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""


def generate_streaming(system: str, user: str, max_tokens: int = 8192, label: str = "") -> str:
    """Генерация длинного текста — для статей Б17 и Дзен."""
    client = get_client()
    if label:
        print(f"  ✍️  {label}...", flush=True)
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        stream=True,
    )
    parts = []
    for chunk in stream:
        text = chunk.choices[0].delta.content or ""
        parts.append(text)
    return "".join(parts)
