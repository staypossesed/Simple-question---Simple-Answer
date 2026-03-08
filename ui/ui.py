# Portfolio RAG App — Modern UI
# Streamlit интерфейс для Question-Answering RAG

import logging
import os

import streamlit as st
from dotenv import load_dotenv
from pathway.xpacks.llm.document_store import IndexingStatus
from pathway.xpacks.llm.question_answering import RAGClient

load_dotenv()

PATHWAY_HOST = os.environ.get("PATHWAY_HOST", "localhost")
PATHWAY_PORT = int(os.environ.get("PATHWAY_PORT", 8000))

st.set_page_config(
    page_title="RAG Portfolio App",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)
logger = logging.getLogger("streamlit")
logger.setLevel(logging.INFO)

# Подключаемся к Pathway RAG API
conn = RAGClient(url=f"http://{PATHWAY_HOST}:{PATHWAY_PORT}")

# === HEADER ===
st.markdown("""
# 📚 RAG Portfolio App
**Retrieval-Augmented Generation** — задавай вопросы по своим документам.  
Данные индексируются в реальном времени, ответы строятся на основе твоей базы знаний.
""")

# === SIDEBAR: документы ===
with st.sidebar:
    st.markdown("### 📁 Документы в индексе")
    st.caption("Файлы из папки `data/`")

    try:
        document_meta_list = conn.list_documents(keys=[])
        st.session_state["document_meta_list"] = document_meta_list

        indexed = [
            f for f in document_meta_list
            if f.get("_indexing_status") == IndexingStatus.INDEXED
        ]
        ingested = [
            f for f in document_meta_list
            if f.get("_indexing_status") == IndexingStatus.INGESTED
        ]

        if indexed:
            st.success(f"✅ Проиндексировано: {len(indexed)}")
            for f in indexed:
                name = f.get("path", "?").split("/")[-1]
                st.code(name, language=None)
        else:
            st.info("Пока нет документов. Добавь PDF/DOCX в папку `data/`.")

        if ingested:
            st.warning(f"⏳ Обрабатывается: {len(ingested)}")

    except Exception as e:
        st.error(f"Не удалось подключиться к API: {e}")
        st.caption("Запусти бэкенд: `python app.py`")

    st.divider()
    st.markdown("### 🔗 Ссылки")
    st.page_link("https://github.com/pathwaycom/llm-app", label="Pathway llm-app", icon="📦")

# === MAIN: вопрос-ответ ===
question = st.chat_input("Задай вопрос по документам...")

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Ищу в документах и генерирую ответ..."):
            try:
                api_response = conn.answer(question, return_context_docs=True)
                response = api_response["response"]
                context_docs = api_response.get("context_docs", [])

                st.markdown(response)

                if context_docs:
                    with st.expander("📄 Контекст (документы, отправленные в LLM)"):
                        for i, doc in enumerate(context_docs):
                            path = doc.get("metadata", {}).get("path", "?")
                            text = doc.get("text", "")[:500] + "..." if len(doc.get("text", "")) > 500 else doc.get("text", "")
                            st.markdown(f"**{i+1}. {path.split('/')[-1]}**")
                            st.code(text, language=None)
            except Exception as e:
                st.error(f"Ошибка: {e}")
