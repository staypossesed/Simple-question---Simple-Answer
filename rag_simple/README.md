# RAG 2026 — Production-ready

**Hybrid Search** (FAISS + BM25) · **BGE Reranker** · **Groq/OpenAI**

## Возможности

- **Hybrid Retrieval** — семантика (FAISS) + ключевые слова (BM25), RRF
- **Reranking** — BGE v2-m3, локально
- **Улучшенный чанкинг** — 800 токенов, overlap 100
- **Источники** — показ документов, использованных для ответа
- **RAGAS** — скрипт оценки качества (`python eval_rag.py`)

## Запуск

```powershell
cd rag_simple
pip install -r requirements.txt
python -m streamlit run ui.py
```

Открой http://localhost:8501

## API ключи (.env)

- **GROQ_API_KEY** — бесплатно, https://console.groq.com/keys
- **OPENAI_API_KEY** — альтернатива

## Документы

Клади `.txt` или `.pdf` в папку `../data/`

При первом запуске скачаются модели (~90 MB embeddings, ~2.3 GB reranker).
