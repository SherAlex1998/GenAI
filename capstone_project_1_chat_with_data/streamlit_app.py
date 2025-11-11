from __future__ import annotations

import os
from pathlib import Path

import openai
import streamlit as st

from llm_agent import LLMAgent, LOG_BUFFER


def _init_agent() -> LLMAgent | None:
    default_db_path = Path(__file__).resolve().parent / "steam.sqlite"
    db_path = Path(os.environ.get("STEAM_DB_PATH", default_db_path))

    try:
        return LLMAgent(str(db_path))
    except Exception as error:  # noqa: BLE001
        st.error(f"Failed to initialize agent: {error}")
        return None


def _get_history() -> list[dict[str, str]]:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    return st.session_state.chat_history


def _render_sidebar() -> None:
    st.sidebar.header("Log")
    if LOG_BUFFER:
        st.sidebar.code("\n".join(LOG_BUFFER[-200:]), language="text")
    else:
        st.sidebar.write("Log is empty.")


def main() -> None:
    st.set_page_config(page_title="Steam LLM Chat", page_icon="💬")
    st.title("Steam LLM Chat")
    st.caption("Chat with the agent that uses the Steam database.")

    if "agent" not in st.session_state:
        agent = _init_agent()
        if agent is None:
            return
        st.session_state.agent = agent

    agent: LLMAgent = st.session_state.agent

    history = _get_history()

    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    try:
        prompt = st.chat_input("Type your message")
        if prompt:
            history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Generating response..."):
                    result = agent.generate([dict(item) for item in history])
                answer = result.get("content") or "Sorry, I couldn't produce a response."
                st.markdown(answer)
            history.append({"role": "assistant", "content": answer})
    except openai.BadRequestError as ex:
        _render_sidebar()
        raise ex

    _render_sidebar()


if __name__ == "__main__":
    main()

