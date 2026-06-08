from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

COOKIES_FILE = Path("/tmp/b17_cookies.json")


def extract_title_and_body(text: str) -> tuple[str, str]:
    lines = text.strip().split("\n")
    title = ""
    body_lines = []
    for line in lines:
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        else:
            body_lines.append(line)
    body = "\n".join(body_lines).strip()
    if not title:
        title = body_lines[0][:80] if body_lines else "Без заголовка"
    return title, body


async def _publish(text: str) -> str | None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None

    title, body = extract_title_and_body(text)
    html_body = body.replace("\n\n", "</p><p>").replace("\n", "<br>")
    html_body = f"<p>{html_body}</p>"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        if COOKIES_FILE.exists():
            cookies = json.loads(COOKIES_FILE.read_text())
            await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto("https://www.b17.ru/article/add/", wait_until="networkidle", timeout=30000)

        # Заголовок
        await page.fill('input[name="title"]', title)

        # Тело статьи — Б17 использует TinyMCE
        try:
            await page.evaluate(f"""
                var ed = tinymce.get(tinymce.editors[0] ? tinymce.editors[0].id : null);
                if (ed) {{ ed.setContent({json.dumps(html_body)}); }}
            """)
        except Exception:
            # Запасной вариант: прямой textarea
            await page.fill('textarea[name="text"]', body)

        # Сохранить как черновик
        try:
            await page.click('button:has-text("Сохранить черновик")', timeout=3000)
        except Exception:
            try:
                await page.click('input[value="Сохранить"]', timeout=3000)
            except Exception:
                await page.click('button[type="submit"]', timeout=3000)

        await page.wait_for_timeout(3000)
        return page.url


def publish(text: str) -> str | None:
    try:
        return asyncio.run(_publish(text))
    except Exception as e:
        print(f"B17 publish error: {e}")
        return None
