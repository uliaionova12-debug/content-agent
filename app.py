import time
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent import audience as aud_module
from agent import content_b17, content_dzen, content_telegram, content_vk, content_plan, visual
from agent import image_gen, compositor
from publisher import telegram_pub, b17_pub, vk_pub

AUTHOR_PROFILE = Path(__file__).parent / "author" / "style_profile.md"


def load_style() -> str:
    if AUTHOR_PROFILE.exists():
        return AUTHOR_PROFILE.read_text(encoding="utf-8")
    return ""


# ── Настройки страницы ──────────────────────────────────────────────
st.set_page_config(
    page_title="Контент-агент",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Контент-агент")
st.caption("Юлия Ионова — клинический психолог, супервизор")

# ── Форма ввода ─────────────────────────────────────────────────────
with st.form("generate_form"):
    topic = st.text_area(
        "Тема, идея, фрагмент кейса",
        placeholder="Почему психологу трудно брать отпуск",
        height=100,
    )
    submitted = st.form_submit_button("🚀 Генерировать контент", use_container_width=True)

# ── Генерация ────────────────────────────────────────────────────────
if submitted and topic.strip():
    st.session_state.topic = topic.strip()
    st.session_state.generated = {}
    style = load_style()

    with st.status("Генерирую контент...", expanded=True) as status:

        st.write("📊 Анализ целевой аудитории...")
        audience_text = aud_module.analyze(topic)
        st.session_state.generated["audience"] = audience_text
        st.write("✅ Анализ готов")
        time.sleep(4)

        st.write("✍️ Пишу статью для Б17...")
        st.session_state.generated["b17"] = content_b17.generate(topic, audience_text, style)
        st.write("✅ Б17 готова")
        time.sleep(4)

        st.write("✍️ Адаптирую для Яндекс Дзен...")
        st.session_state.generated["dzen"] = content_dzen.generate(topic, audience_text, style)
        st.write("✅ Дзен готов")
        time.sleep(4)

        st.write("✍️ Пишу посты для Telegram...")
        st.session_state.generated["telegram"] = content_telegram.generate(topic, audience_text, style)
        st.write("✅ Telegram готов")
        time.sleep(4)

        st.write("✍️ Пишу пост для ВКонтакте...")
        st.session_state.generated["vk"] = content_vk.generate(topic, audience_text, style)
        st.write("✅ ВКонтакте готов")
        time.sleep(4)

        st.write("📅 Создаю контент-план (30 тем)...")
        st.session_state.generated["plan"] = content_plan.generate(topic)
        st.write("✅ Контент-план готов")
        time.sleep(4)

        st.write("🎨 Создаю визуальную концепцию...")
        st.session_state.generated["visual"] = visual.generate(topic, audience_text)
        st.write("✅ Визуал готов")

        status.update(label="✨ Готово! Проверьте тексты и публикуйте.", state="complete")

# ── Просмотр и публикация ────────────────────────────────────────────
if "generated" in st.session_state and st.session_state.generated:
    g = st.session_state.generated
    topic_display = st.session_state.get("topic", "")
    st.markdown(f"---\n### Контент-пакет: «{topic_display}»")

    tab_b17, tab_dzen, tab_tg, tab_vk, tab_plan, tab_visual = st.tabs([
        "📝 Б17", "📰 Яндекс Дзен", "✈️ Telegram", "🔵 ВКонтакте", "📅 Контент-план", "🎨 Визуал + AI-фото"
    ])

    # ── Б17 ──
    with tab_b17:
        if "b17" in g:
            text = st.text_area("Статья", g["b17"], height=500, key="b17_edit")
            if st.button("📤 Опубликовать на Б17"):
                with st.spinner("Публикую..."):
                    url = b17_pub.publish(text)
                if url:
                    st.success(f"Опубликовано! {url}")
                else:
                    st.error("Ошибка публикации — проверь cookies в /tmp/b17_cookies.json")

    # ── Дзен ──
    with tab_dzen:
        if "dzen" in g:
            text = st.text_area("Статья", g["dzen"], height=500, key="dzen_edit")
            st.info("⚠️ Дзен блокирует автоматизацию. Скопируй текст и вставь вручную на dzen.ru")
            if st.button("📋 Показать текст для копирования"):
                st.code(text, language=None)

    # ── Telegram ──
    with tab_tg:
        if "telegram" in g:
            raw = g["telegram"]
            parts = raw.split("---")
            short = parts[0].strip() if parts else raw
            long_ = parts[1].strip() if len(parts) > 1 else ""

            st.subheader("Короткий пост")
            short_edit = st.text_area("", short, height=150, key="tg_short")
            if st.button("📤 Отправить короткий пост"):
                with st.spinner("Отправляю..."):
                    ok = telegram_pub.send(short_edit)
                if ok:
                    st.success("Отправлено в канал!")
                else:
                    st.error("Ошибка — добавь TELEGRAM_BOT_TOKEN и TELEGRAM_CHANNEL_ID в .env")

            st.divider()
            st.subheader("Длинный пост")
            long_edit = st.text_area("", long_, height=250, key="tg_long")
            if st.button("📤 Отправить длинный пост"):
                with st.spinner("Отправляю..."):
                    ok = telegram_pub.send(long_edit)
                if ok:
                    st.success("Отправлено в канал!")
                else:
                    st.error("Ошибка — добавь TELEGRAM_BOT_TOKEN и TELEGRAM_CHANNEL_ID в .env")

    # ── ВКонтакте ──
    with tab_vk:
        if "vk" in g:
            text = st.text_area("Пост", g["vk"], height=300, key="vk_edit")
            if st.button("📤 Опубликовать в ВКонтакте"):
                with st.spinner("Публикую..."):
                    ok = vk_pub.post(text)
                if ok:
                    st.success("Опубликовано в ВКонтакте!")
                else:
                    st.error("Ошибка — добавь VK_ACCESS_TOKEN и VK_OWNER_ID в .env")

    # ── Контент-план ──
    with tab_plan:
        if "plan" in g:
            st.markdown(g["plan"])

    # ── Визуал + DALL-E 3 ──
    with tab_visual:
        if "visual" in g:
            import re as _re

            st.subheader("📷 Шаг 1 — загрузи своё фото")
            uploaded = st.file_uploader(
                "JPG или PNG — агент сам вырежет фон и соберёт обложку",
                type=["jpg", "jpeg", "png", "webp"],
                key="photo_upload",
            )

            if uploaded is not None:
                photo_bytes = uploaded.read()
                st.image(photo_bytes, caption="Исходное фото", width=220)

                st.subheader("🎨 Шаг 2 — настройки обложки")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    size_option = st.selectbox(
                        "Формат:",
                        ["1024x1024 (квадрат)", "1792x1024 (широкий)", "1024x1792 (портрет)"],
                    )
                with col_b:
                    position = st.selectbox("Расположение фигуры:", ["справа", "слева", "по центру"])
                with col_c:
                    scale = st.slider("Размер фигуры:", 0.5, 1.0, 0.78, 0.05)

                size_map = {
                    "1024x1024 (квадрат)": "1024x1024",
                    "1792x1024 (широкий)": "1792x1024",
                    "1024x1792 (портрет)": "1024x1792",
                }
                pos_map = {"справа": "right", "слева": "left", "по центру": "center"}

                # Промпт для фона — агент предлагает, можно отредактировать
                prompts = image_gen.extract_prompts(g["visual"])
                default_prompt = prompts[0] if prompts else ""
                bg_prompt = st.text_area("Промпт фона (DALL-E 3):", value=default_prompt, height=90)

                # Автозаполнение заголовка из статьи
                auto_title = ""
                if "b17" in g:
                    for line in g["b17"].split("\n"):
                        if line.startswith("# "):
                            auto_title = line[2:].strip()
                            break

                st.subheader("✍️ Шаг 3 — текст обложки")
                cover_title    = st.text_input("Заголовок (Didot — как в Vogue):", value=auto_title)
                cover_subtitle = st.text_input("Подзаголовок (Futura — капслок):", value=topic_display[:60])
                cover_author   = st.text_input("Имя автора:", value="Юлия Ионова")
                text_color     = st.radio("Цвет текста:", ["dark", "light"], horizontal=True,
                                          format_func=lambda x: "Тёмный" if x == "dark" else "Светлый")

                if st.button("✨ Создать обложку", use_container_width=True, type="primary"):
                    with st.status("Создаю обложку...", expanded=True) as status:
                        st.write("✂️ Вырезаю фон с фото...")
                        person_png = compositor.remove_background(photo_bytes)
                        st.write("✅ Фон вырезан")

                        st.write("🎨 Генерирую фон через DALL-E 3...")
                        bg_bytes = image_gen.generate_image(
                            bg_prompt, size=size_map[size_option]
                        )
                        if not bg_bytes:
                            st.error("Ошибка генерации фона")
                            status.update(state="error")
                        else:
                            st.write("✅ Фон готов")
                            st.write("🖼 Верстаю журнальный разворот...")
                            cover = compositor.composite(
                                person_png, bg_bytes,
                                position=pos_map[position],
                                scale=scale,
                                title=cover_title,
                                subtitle=cover_subtitle,
                                author=cover_author,
                                text_color=text_color,
                            )
                            st.write("✅ Готово!")
                            status.update(label="✨ Обложка готова!", state="complete")

                            st.image(cover, use_container_width=True)
                            st.download_button(
                                "⬇️ Скачать обложку",
                                data=cover,
                                file_name=f"cover_{topic_display[:30].replace(' ', '_')}.jpg",
                                mime="image/jpeg",
                            )

            st.divider()
            st.subheader("💡 Визуальная концепция")
            st.markdown(g["visual"])
