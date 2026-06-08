from __future__ import annotations

import io
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

_FONTS_DIR = Path(__file__).parent.parent / "fonts"
FONT_TITLE    = str(_FONTS_DIR / "title.ttf")
FONT_SUBTITLE = str(_FONTS_DIR / "subtitle.ttf")
FONT_BODY     = str(_FONTS_DIR / "body.ttf")


def remove_background(photo_bytes: bytes) -> bytes:
    from rembg import remove
    return remove(photo_bytes)


def composite(
    person_png: bytes,
    background_png: bytes,
    position: str = "right",
    scale: float = 0.78,
    title: str = "",
    subtitle: str = "",
    author: str = "Юлия Ионова",
    text_color: str = "dark",
) -> bytes:
    """
    Собирает журнальную обложку:
    - накладывает вырезанную фигуру на фон
    - добавляет заголовок (Didot), подзаголовок (Futura), имя автора
    text_color: 'dark' | 'light'
    """
    bg = Image.open(io.BytesIO(background_png)).convert("RGBA")
    person = Image.open(io.BytesIO(person_png)).convert("RGBA")

    bg_w, bg_h = bg.size

    # ── Фигура ────────────────────────────────────────────────────────
    target_h = int(bg_h * scale)
    ratio = target_h / person.height
    target_w = int(person.width * ratio)
    person = person.resize((target_w, target_h), Image.LANCZOS)

    margin = int(bg_w * 0.04)
    if position == "left":
        person_x = margin
        text_side = "right"
    elif position == "right":
        person_x = bg_w - target_w - margin
        text_side = "left"
    else:
        person_x = (bg_w - target_w) // 2
        text_side = "left"

    person_y = bg_h - target_h
    bg.paste(person, (person_x, person_y), person)

    # ── Текстовая зона ────────────────────────────────────────────────
    if not title and not subtitle:
        out = io.BytesIO()
        bg.convert("RGB").save(out, format="JPEG", quality=93)
        return out.getvalue()

    draw = ImageDraw.Draw(bg)

    # Цвет текста
    ink      = (15, 15, 15, 255)   if text_color == "dark" else (245, 240, 235, 255)
    ink_sub  = (60, 55, 50, 220)   if text_color == "dark" else (210, 205, 200, 200)
    ink_auth = (120, 110, 100, 180) if text_color == "dark" else (180, 175, 170, 180)

    # Текстовая колонка
    if text_side == "left":
        col_x = int(bg_w * 0.05)
        col_w = person_x - int(bg_w * 0.08)
    else:
        col_x = person_x + target_w + int(bg_w * 0.04)
        col_w = bg_w - col_x - int(bg_w * 0.05)

    col_w = max(col_w, int(bg_w * 0.3))

    # ── Тонкая линия-акцент сверху ───────────────────────────────────
    line_y = int(bg_h * 0.12)
    draw.line([(col_x, line_y), (col_x + min(60, col_w // 3), line_y)],
              fill=ink, width=2)

    # ── Заголовок — Didot ─────────────────────────────────────────────
    title_size = _fit_font(FONT_TITLE, title, col_w, max_size=90, min_size=32)
    font_title = ImageFont.truetype(FONT_TITLE, title_size)
    wrapped_title = _wrap(title, font_title, col_w)

    title_y = line_y + 18
    for line in wrapped_title:
        _draw_text_shadow(draw, col_x, title_y, line, font_title, ink, text_color)
        title_y += int(title_size * 1.15)

    # ── Разделитель ───────────────────────────────────────────────────
    sep_y = title_y + 16
    draw.line([(col_x, sep_y), (col_x + min(40, col_w // 4), sep_y)],
              fill=ink_sub, width=1)

    # ── Подзаголовок — Futura ─────────────────────────────────────────
    if subtitle:
        sub_size = _fit_font(FONT_SUBTITLE, subtitle, col_w, max_size=28, min_size=14)
        font_sub = ImageFont.truetype(FONT_SUBTITLE, sub_size)
        wrapped_sub = _wrap(subtitle.upper(), font_sub, col_w)

        sub_y = sep_y + 20
        for line in wrapped_sub:
            _draw_text_shadow(draw, col_x, sub_y, line, font_sub, ink_sub, text_color)
            sub_y += int(sub_size * 1.5)

    # ── Имя автора внизу — GillSans ──────────────────────────────────
    if author:
        auth_size = 18
        font_auth = ImageFont.truetype(FONT_BODY, auth_size)
        auth_y = int(bg_h * 0.88)
        draw.text((col_x, auth_y), author.upper(), font=font_auth, fill=ink_auth)
        # тонкая линия под именем
        draw.line([(col_x, auth_y + auth_size + 4),
                   (col_x + col_w // 2, auth_y + auth_size + 4)],
                  fill=ink_auth, width=1)

    out = io.BytesIO()
    bg.convert("RGB").save(out, format="JPEG", quality=93)
    return out.getvalue()


def _fit_font(path: str, text: str, max_width: int, max_size: int, min_size: int) -> int:
    """Подбирает максимальный размер шрифта, при котором слово влезает в колонку."""
    for size in range(max_size, min_size - 1, -2):
        font = ImageFont.truetype(path, size)
        word = max(text.split(), key=len) if text.split() else text
        w = font.getlength(word)
        if w <= max_width:
            return size
    return min_size


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Разбивает текст на строки по ширине колонки."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if font.getlength(test) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def _draw_text_shadow(draw, x, y, text, font, color, mode):
    """Рисует текст с тонкой тенью для читаемости."""
    if mode == "light":
        # На светлом фоне — тёмная тень
        draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, 60))
    else:
        # На тёмном фоне — светлое свечение
        draw.text((x + 1, y + 1), text, font=font, fill=(255, 255, 255, 40))
    draw.text((x, y), text, font=font, fill=color)
