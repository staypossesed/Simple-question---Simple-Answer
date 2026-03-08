# RAG Portfolio App

Работает **без OpenAI кредитов**:
- **Embeddings** — локально (HuggingFace), бесплатно
- **LLM** — Groq (бесплатно) или OpenAI

## 1. Получи бесплатный Groq API ключ

1. Зайди на https://console.groq.com/keys
2. Зарегистрируйся (Google/GitHub)
3. Создай API ключ
4. Добавь в `../.env`:
   ```
   GROQ_API_KEY=gsk_твой_ключ
   ```

## 2. Запуск

```powershell
cd d:\Downloads\portfolio-rag-app\rag_simple
pip install -r requirements.txt
python -m streamlit run ui.py
```

Открой http://localhost:8501

При первом запуске скачается модель embeddings (~90 MB) — подожди 1–2 минуты.

## Документы

Клади `.txt` или `.pdf` в папку `../data/`
