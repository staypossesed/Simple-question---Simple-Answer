"""
RAG 2026 — Hybrid Search + Reranking + Production-ready
Embeddings: HuggingFace (локально)
LLM: Groq / OpenAI
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.retrievers import BM25Retriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

load_dotenv(Path(__file__).parent.parent / ".env")

DATA_DIR = Path(__file__).parent.parent / "data"

# Конфиг
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
RETRIEVE_K = 12
RERANK_TOP_N = 5


def _load_docs():
    """Загрузка документов из data/"""
    all_docs = []
    if not DATA_DIR.exists():
        return all_docs

    try:
        loader = DirectoryLoader(str(DATA_DIR), glob="*.txt", loader_cls=TextLoader)
        all_docs.extend(loader.load())
    except Exception:
        pass

    try:
        from langchain_community.document_loaders import PyPDFLoader
        loader = DirectoryLoader(str(DATA_DIR), glob="*.pdf", loader_cls=PyPDFLoader)
        all_docs.extend(loader.load())
    except Exception:
        pass

    return all_docs


def _get_embeddings():
    """Локальные embeddings"""
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def _get_llm():
    """Groq или OpenAI"""
    if os.getenv("GROQ_API_KEY"):
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        except ImportError:
            pass
    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model="gpt-4o-mini", temperature=0)
        except Exception:
            pass
    return None


def _rerank_docs(query: str, docs: list[Document], top_n: int = RERANK_TOP_N) -> list[Document]:
    """BGE Reranker — локально, бесплатно"""
    if not docs or len(docs) <= top_n:
        return docs[:top_n]
    try:
        from FlagEmbedding import FlagReranker
        reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)
        pairs = [[query, doc.page_content] for doc in docs]
        scores = reranker.compute_score(pairs)
        if isinstance(scores, float):
            scores = [scores]
        scored = list(zip(docs, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [d for d, _ in scored[:top_n]]
    except Exception:
        return docs[:top_n]


def build_rag():
    """RAG + fallback: если в документах нет ответа — отвечай из общих знаний"""
    llm = _get_llm()
    if not llm:
        return {"chain": None, "retriever": None}, (
            "Добавь в .env один из ключей:\n"
            "• GROQ_API_KEY (бесплатно: console.groq.com)\n"
            "• OPENAI_API_KEY"
        )

    all_docs = _load_docs()
    has_docs = bool(all_docs)

    retriever_with_rerank = None

    if has_docs:
        embeddings = _get_embeddings()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_documents(all_docs)

        vectorstore = FAISS.from_documents(chunks, embeddings)
        faiss_retriever = vectorstore.as_retriever(k=RETRIEVE_K)
        bm25_retriever = BM25Retriever.from_documents(chunks, k=RETRIEVE_K)

        def _hybrid_retrieve(query: str, k: int = RETRIEVE_K) -> list[Document]:
            faiss_docs = faiss_retriever.invoke(query)
            bm25_docs = bm25_retriever.invoke(query)
            rrf_k = 60
            scores = {}
            for rank, doc in enumerate(faiss_docs):
                key = hash(doc.page_content)
                scores[key] = scores.get(key, 0) + 1 / (rrf_k + rank)
            for rank, doc in enumerate(bm25_docs):
                key = hash(doc.page_content)
                scores[key] = scores.get(key, 0) + 1 / (rrf_k + rank)
            seen = set()
            merged = []
            for doc in faiss_docs + bm25_docs:
                key = hash(doc.page_content)
                if key not in seen:
                    seen.add(key)
                    merged.append((doc, scores.get(key, 0)))
            merged.sort(key=lambda x: x[1], reverse=True)
            return [d for d, _ in merged[:k]]

        def retriever_with_rerank_fn(query: str) -> list[Document]:
            docs = _hybrid_retrieve(query)
            return _rerank_docs(query, docs, RERANK_TOP_N)

        retriever_with_rerank = retriever_with_rerank_fn

    # Промпт: если есть контекст — используй его; если нет — отвечай из общих знаний
    prompt = ChatPromptTemplate.from_template("""Ты — полезный помощник. Отвечай на любой вопрос.

Правила:
- Если в контексте ниже есть релевантная информация — используй её в первую очередь.
- Если контекст пуст или не содержит ответа — ответь на основе своих общих знаний.
- Всегда давай полезный, структурированный ответ. Не отказывайся отвечать.
- Используй нумерацию или списки, если это уместно.

Контекст из документов пользователя:
{context}

Вопрос: {question}

Ответ:""")

    def get_context(query: str) -> str:
        if not has_docs or not retriever_with_rerank:
            return "(пусто — документы не загружены)"
        docs = retriever_with_rerank(query)
        if not docs:
            return "(пусто)"
        return "\n\n---\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": RunnableLambda(get_context), "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return {"chain": chain, "retriever": retriever_with_rerank or (lambda q: [])}, None


if __name__ == "__main__":
    result, err = build_rag()
    if err:
        print(err)
        exit(1)
    print("RAG готов. Запуск: python -m streamlit run ui.py")
