"""
Streamlit UI для простого RAG (LangChain)
Запуск: streamlit run ui.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from app import build_rag, DATA_DIR

st.set_page_config(page_title="RAG Portfolio (LangChain)", page_icon="📚", layout="centered")

st.markdown("# 📚 RAG Portfolio App")
st.caption("LangChain + FAISS — Groq/OpenAI. Embeddings локально (без API).")

chain, err = build_rag()

if err:
    st.error(err)
    st.info(f"Добавь файлы в папку: `{DATA_DIR}`")
    st.stop()

question = st.chat_input("Задай вопрос по документам...")

if question:
    with st.chat_message("user"):
        st.write(question)
    
    with st.chat_message("assistant"):
        with st.spinner("Ищу и генерирую..."):
            try:
                answer = chain.invoke(question)
                st.markdown(answer)
            except Exception as e:
                st.error(f"Ошибка: {e}")
                st.caption("Проверь OPENAI_API_KEY в .env")
