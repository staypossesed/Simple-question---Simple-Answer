"""
RAG на LangChain — работает на Windows без OpenAI кредитов
Embeddings: HuggingFace (локально, бесплатно)
LLM: Groq (бесплатно) или OpenAI
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv(Path(__file__).parent.parent / ".env")

DATA_DIR = Path(__file__).parent.parent / "data"


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
    """Локальные embeddings — без API, без кредитов"""
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def _get_llm():
    """Groq (бесплатно) или OpenAI"""
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


def build_rag():
    """Собирает RAG-цепочку"""
    all_docs = _load_docs()
    if not all_docs:
        return None, "Нет документов в data/. Добавь .txt или .pdf файлы."

    embeddings = _get_embeddings()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(all_docs)

    vectorstore = FAISS.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever(k=4)

    llm = _get_llm()
    if not llm:
        return None, (
            "Добавь в .env один из ключей:\n"
            "• GROQ_API_KEY (бесплатно: console.groq.com)\n"
            "• OPENAI_API_KEY"
        )

    prompt = ChatPromptTemplate.from_template("""
Ответь на вопрос, опираясь только на контекст ниже.
Если в контексте нет ответа — скажи об этом.

Контекст:
{context}

Вопрос: {question}

Ответ:""")

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, None


if __name__ == "__main__":
    chain, err = build_rag()
    if err:
        print(err)
        exit(1)
    print("RAG готов. Запуск: python -m streamlit run ui.py")
