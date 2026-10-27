"""
Page 4: Health Chat
Free-form AI chat grounded in Kenya MoH guidelines via Amazon Bedrock.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from rag.bedrock_client import ask_health_assistant
from i18n.translations import t


def render(lang: str = "en"):
    st.title(t("chat_title", lang))
    st.markdown(f"*{t('chat_desc', lang)}*")

    # Emergency disclaimer
    st.error(
        f"📞 {t('chat_disclaimer', lang)}",
        icon="⚠️",
    )
    st.divider()

    # ── Initialise chat history ───────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ── Clear chat button ─────────────────────────────────────────────────────
    if st.button(t("chat_clear", lang), type="secondary"):
        st.session_state.chat_history = []
        st.rerun()

    # ── Render chat history ───────────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        role = msg["role"]
        with st.chat_message(
            role,
            avatar="🧑" if role == "user" else "🩺",
        ):
            st.markdown(msg["content"])

    # ── Chat input ────────────────────────────────────────────────────────────
    user_input = st.chat_input(t("chat_placeholder", lang))

    if user_input:
        # Display user message
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)

        # Add to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
        })

        # Get AI response
        with st.chat_message("assistant", avatar="🩺"):
            with st.spinner(t("chat_thinking", lang)):
                response = ask_health_assistant(
                    user_message=user_input,
                    chat_history=st.session_state.chat_history[:-1],
                    lang=lang,
                )
            st.markdown(response)

        # Add AI response to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
        })


# ── Run standalone ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    lang = st.session_state.get("lang", "en")
    render(lang)
