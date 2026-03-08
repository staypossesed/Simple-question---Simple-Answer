# 📚 RAG Portfolio App

Real-time Question-Answering RAG приложение на базе [Pathway](https://pathway.com).  
Документы индексируются автоматически, ответы строятся на основе твоей базы знаний.

## Стек

- **Pathway** — стриминговая платформа, инкрементальная индексация
- **OpenAI** — GPT для ответов, text-embedding для векторов
- **Docling** — парсинг PDF/DOCX
- **USearch** — векторный поиск
- **Streamlit** — UI

## Быстрый старт

**Вариант 1: Docker (рекомендуется на Windows)**
```bash
# Пропиши OPENAI_API_KEY в .env, затем:
docker compose build
docker compose up
```
Бэкенд: http://localhost:8000, UI: http://localhost:8501

**Вариант 2: Локально**
```bash
pip install -r requirements.txt
# OPENAI_API_KEY в .env
python app.py
# В другом терминале:
cd ui && pip install -r requirements.txt && streamlit run ui.py
```
Открой http://localhost:8501

## Документация

**[STEP_BY_STEP.md](./STEP_BY_STEP.md)** — пошаговое объяснение каждого компонента (на русском).

## Структура

```
├── app.py, app.yaml   # RAG-пайплайн и REST API
├── data/              # PDF, DOCX, TXT — автоматически индексируются
├── ui/                # Streamlit-интерфейс
└── STEP_BY_STEP.md    # Подробное объяснение
```

## API эндпоинты

| Эндпоинт | Описание |
|----------|----------|
| `POST /v2/answer` | Вопрос-ответ (RAG) |
| `POST /v2/summarize` | Суммаризация текстов |
| `POST /v1/retrieve` | Поиск по векторной БД |
| `POST /v2/list_documents` | Список документов |
| `POST /v1/statistics` | Статистика индексера |

## Docker

```bash
docker compose build
docker compose up
```

Бэкенд: 8000, UI: 8501.

---

Based on [Pathway llm-app](https://github.com/pathwaycom/llm-app) template.
