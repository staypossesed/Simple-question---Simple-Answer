"""
RAG 2026 — Attractive UI with sources, history, loading states
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from app import build_rag, DATA_DIR

st.set_page_config(
    page_title="RAG 2026 | Portfolio",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%); }
    h1 { color: #e0e7ff !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
    .stCaptionContainer { color: #94a3b8 !important; }
    [data-testid="stChatMessage"] { 
        background: rgba(30, 41, 59, 0.8) !important; 
        border-radius: 12px !important; 
        padding: 1rem !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
    }
    [data-testid="stChatInput"] { background: rgba(30, 41, 59, 0.6) !important; }
    .source-card { 
        background: rgba(15, 23, 42, 0.9); 
        border-radius: 8px; 
        padding: 12px; 
        margin: 8px 0;
        border-left: 4px solid #6366f1;
        font-size: 0.9em;
    }
    .badge { 
        display: inline-block; 
        background: #6366f1; 
        color: white; 
        padding: 2px 8px; 
        border-radius: 4px; 
        font-size: 0.75em;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Init session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sources" not in st.session_state:
    st.session_state.sources = {}

# Header
st.markdown("# RAG 2026")
st.caption("Hybrid Search (FAISS + BM25) · BGE Reranker · Groq/OpenAI")

# Build RAG
rag_result, err = build_rag()

if err:
    st.error(err)
    st.info(f"Добавь файлы в папку: `{DATA_DIR}`")
    st.stop()

chain = rag_result["chain"]
retriever = rag_result["retriever"]

# Sidebar
with st.sidebar:
    st.markdown("### Настройки")
    st.caption("RAG 2026 · Production-ready")
    st.divider()
    st.markdown("**Возможности:**")
    st.markdown("- Hybrid Search (семантика + ключевые слова)")
    st.markdown("- BGE Reranker")
    st.markdown("- Источники в ответах")
    st.divider()
    if st.button("Очистить историю"):
        st.session_state.messages = []
        st.session_state.sources = {}
        st.rerun()

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📄 Источники"):
                for i, src in enumerate(msg["sources"], 1):
                    st.markdown(f"**{i}.** {src[:300]}..." if len(src) > 300 else f"**{i}.** {src}")

# Input
question = st.chat_input("Задай любой вопрос...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        step = st.empty()
        step.caption("🔍 Ищу в документах...")
        sources = retriever(question) if retriever else []
        step.caption("✍️ Генерирую ответ...")

        try:
            answer = chain.invoke(question)
            step.empty()
            st.markdown(answer)

            source_texts = [doc.page_content for doc in sources]
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": source_texts
            })

            with st.expander("📄 Источники (документы, использованные для ответа)"):
                if sources:
                    for i, doc in enumerate(sources, 1):
                        source = doc.page_content
                        meta = doc.metadata.get("source", "?")
                        st.markdown(f"**{i}. {Path(meta).name if meta else 'Документ'}**")
                        st.code(source[:400] + "..." if len(source) > 400 else source, language=None)
                else:
                    st.caption("Ответ на основе общих знаний (релевантных документов не найдено)")

        except Exception as e:
            step.empty()
            st.error(f"Ошибка: {e}")
            st.caption("Проверь GROQ_API_KEY или OPENAI_API_KEY в .env")
