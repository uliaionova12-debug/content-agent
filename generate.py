#!/usr/bin/env python3
"""
AI Content Agent — генератор контент-пакета для психолога-супервизора.

Использование:
  python generate.py "Тема или идея"
  python generate.py "Почему психологу трудно брать отпуск"
"""

import sys
import os
import re
import time
from datetime import date
from pathlib import Path

from agent import audience, content_b17, content_dzen, content_telegram, content_vk, content_plan, visual


OUTPUT_DIR = Path(__file__).parent / "output"
AUTHOR_PROFILE = Path(__file__).parent / "author" / "style_profile.md"


def load_style_profile() -> str:
    if AUTHOR_PROFILE.exists():
        return AUTHOR_PROFILE.read_text(encoding="utf-8")
    return "Стиль автора не задан. Пиши тёплым экспертным голосом, избегай штампов."


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:50]


def save(folder: Path, filename: str, content: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / filename).write_text(content, encoding="utf-8")


def run(topic: str) -> None:
    print(f"\n🎯 Тема: {topic}")
    print("=" * 60)

    style = load_style_profile()
    slug = slugify(topic)
    today = date.today().isoformat()
    out_dir = OUTPUT_DIR / f"{slug}_{today}"

    # 1. Анализ аудитории (нужен для всех генераторов)
    print("\n📊 Анализ целевой аудитории...")
    audience_text = audience.analyze(topic)
    save(out_dir, "audience.md", audience_text)
    print("  ✅ audience.md")

    # 2. Последовательная генерация текстов для 4 платформ
    print("\n✍️  Генерация контента...")

    text = content_b17.generate(topic, audience_text, style)
    save(out_dir, "b17.md", text)
    print("  ✅ b17.md")
    time.sleep(8)

    text = content_dzen.generate(topic, audience_text, style)
    save(out_dir, "dzen.md", text)
    print("  ✅ dzen.md")
    time.sleep(8)

    text = content_telegram.generate(topic, audience_text, style)
    save(out_dir, "telegram.md", text)
    print("  ✅ telegram.md")
    time.sleep(8)

    text = content_vk.generate(topic, audience_text, style)
    save(out_dir, "vk.md", text)
    print("  ✅ vk.md")
    time.sleep(8)

    # 3. Контент-план
    print("\n📅 Генерация контент-плана (30 тем)...")
    plan_text = content_plan.generate(topic)
    save(out_dir, "content_plan.md", plan_text)
    print("  ✅ content_plan.md")

    # 4. Визуальный блок
    print("\n🎨 Создание визуальной концепции...")
    visual_text = visual.generate(topic, audience_text)
    save(out_dir, "visual.md", visual_text)
    print("  ✅ visual.md")

    print(f"\n{'=' * 60}")
    print(f"✨ Готово! Контент-пакет сохранён в:\n   {out_dir}/")
    print("\nФайлы:")
    for f in sorted(out_dir.iterdir()):
        size = f.stat().st_size
        print(f"  {f.name:25s}  {size:>6,} байт")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python generate.py \"Тема статьи\"")
        sys.exit(1)

    topic_input = " ".join(sys.argv[1:])
    run(topic_input)
