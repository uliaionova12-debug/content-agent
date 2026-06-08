from __future__ import annotations

import base64
import os
import re
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY не задан в .env")
        _client = OpenAI(api_key=api_key)
    return _client


def extract_prompts(visual_text: str) -> list[str]:
    blocks = re.split(r"### Вариант \d+[^\n]*\n", visual_text)
    prompts = []
    for block in blocks[1:]:
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        prompt_lines = []
        for line in lines:
            if line.startswith("#"):
                break
            prompt_lines.append(line)
        if prompt_lines:
            prompts.append(" ".join(prompt_lines))
    return prompts[:3]


def analyze_photo(photo_bytes: bytes, topic: str) -> str:
    """GPT-4o смотрит на фото Юли и создаёт визуальную концепцию под эту статью."""
    client = get_client()
    b64 = base64.b64encode(photo_bytes).decode("utf-8")

    system = """Ты — арт-директор бренда Юлии Ионовой, клинического психолога и супервизора.

Визуальный стиль бренда: Kinfolk, Monocle, The Gentlewoman.
Ключевые слова: воздух, минимализм, интеллектуальная атмосфера, editorial, тихая роскошь,
северный свет, текстуры, нейтральные тона (кремовый, беж, серо-серебристый, тёплый белый).

Ты получаешь фотографию автора и тему статьи.
Твоя задача: создать конкретные рекомендации как использовать ИМЕННО ЭТО фото."""

    prompt = f"""Тема статьи: «{topic}»

Проанализируй это фото и создай:

## Анализ фотографии
Что на фото: поза, свет, выражение, фон, настроение. 3-4 предложения.

## Подходит ли это фото для статьи?
Да/нет и почему. Какое настроение фото передаёт.

## Рекомендации по обработке
Конкретные шаги в Lightroom или Canva:
— цветовая температура (теплее/холоднее)
— контраст и экспозиция
— цветовой фильтр (например: +10 teal, -5 orange)
— кадрирование

## Цветовая палитра фото
3 основных цвета с HEX-кодами, которые уже есть на фото.

## Промпт для DALL-E 3 — фон под это фото
Опиши фон/атмосферу которая будет гармонировать с этим конкретным фото.
Промпт на английском, 50-70 слов. БЕЗ людей, только окружение и свет.

## Как разместить на обложке
Конкретная рекомендация: слева/справа/по центру, с каким текстом рядом."""

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1500,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            },
        ],
    )
    return response.choices[0].message.content or ""


def generate_image(prompt: str, size: str = "1024x1024") -> bytes | None:
    """Генерирует изображение через DALL-E 3."""
    try:
        client = get_client()
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()
        return img_response.content
    except Exception as e:
        print(f"Image generation error: {e}")
        return None
