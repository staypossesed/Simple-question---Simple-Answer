# 📖 Пошаговое объяснение: что здесь происходит

Этот файл объясняет **каждый шаг** проекта. Читай по порядку — к концу ты поймёшь, как всё устроено.

---

## Часть 1: Что такое RAG и зачем он нужен

### Проблема
Обычный ChatGPT не знает твои документы. Он обучен на общих данных и не имеет доступа к твоим PDF, контрактам, отчётам.

### Решение: RAG
**RAG = Retrieval-Augmented Generation** (генерация, усиленная поиском).

Идея простая:
1. **Retrieval** — ищем в твоих документах куски текста, релевантные вопросу
2. **Augmented** — подмешиваем эти куски в контекст для LLM
3. **Generation** — LLM генерирует ответ, опираясь на найденный контекст

Схема:
```
Твой вопрос → Поиск по векторной БД → Релевантные чанки → Промпт для LLM → Ответ
```

---

## Часть 2: Структура проекта

```
portfolio-rag-app/
├── app.py          # Точка входа — запускает RAG-пайплайн и REST API
├── app.yaml        # Конфиг: источники данных, LLM, embedder, парсер и т.д.
├── requirements.txt
├── data/           # Сюда кладёшь PDF, DOCX, TXT — они автоматически индексируются
├── ui/
│   ├── ui.py       # Streamlit-интерфейс для вопросов
│   └── ...
├── .env            # OPENAI_API_KEY (не коммить!)
└── STEP_BY_STEP.md # Этот файл
```

---

## Часть 3: Что делает каждый файл

### `app.py`

**Шаг 1.** Загружает конфиг из `app.yaml`:
```python
with open("app.yaml") as f:
    config = pw.load_yaml(f)
```
YAML описывает все компоненты: источники, LLM, embedder, парсер, retriever.

**Шаг 2.** Создаёт объект `App` с `question_answerer` (RAG-движок).

**Шаг 3.** Запускает `QASummaryRestServer` — HTTP-сервер с эндпоинтами:
- `/v2/answer` — ответ на вопрос (RAG)
- `/v2/summarize` — суммаризация текстов
- `/v1/retrieve` — поиск по векторной БД
- `/v2/list_documents` — список документов
- `/v1/statistics` — статистика индексера

**Шаг 4.** `pw.run()` — запускает Pathway в режиме стриминга. Всё работает инкрементально: новые файлы автоматически парсятся, чанкаются, эмбеддятся и попадают в индекс.

---

### `app.yaml`

Здесь описана **вся цепочка обработки**. Разберём по блокам.

#### 1. Источники данных (`$sources`)
```yaml
$sources:
  - !pw.io.fs.read
    path: data
    format: binary
    with_metadata: true
```
**Что это:** Pathway читает файлы из папки `data/`. При изменении или добавлении файлов — автоматически переиндексирует. Никакого отдельного ETL не нужно.

#### 2. LLM (`$llm`)
```yaml
$llm: !pw.xpacks.llm.llms.OpenAIChat
  model: "gpt-4.1-mini"
  temperature: 0
  ...
```
**Что это:** Модель для генерации ответов. Можно заменить на `gpt-4o`, `gpt-4`, или на локальную (Ollama/Mistral) через `LiteLLMChat`.

#### 3. Embedder (`$embedder`)
```yaml
$embedder: !pw.xpacks.llm.embedders.OpenAIEmbedder
  model: "text-embedding-3-small"
```
**Что это:** Превращает текст в вектор (embedding). По этим векторам ищутся похожие чанки. Размерность у `text-embedding-3-small` — 1536.

#### 4. Splitter (`$splitter`)
```yaml
$splitter: !pw.xpacks.llm.splitters.TokenCountSplitter
  max_tokens: 400
```
**Что это:** Режет документ на чанки по ~400 токенов. Так LLM получает куски разумного размера, а не целые книги.

#### 5. Parser (`$parser`)
```yaml
$parser: !pw.xpacks.llm.parsers.DoclingParser
  table_parsing_strategy: "llm"
```
**Что это:** Парсит PDF/DOCX в текст. Docling умеет таблицы, изображения (с LLM). Без парсера — бинарник, с парсером — читаемый текст.

#### 6. Retriever (`$retriever_factory`)
```yaml
$retriever_factory: !pw.indexing.UsearchKnnFactory
  embedder: $embedder
  metric: !pw.indexing.USearchMetricKind.COS
```
**Что это:** Векторный индекс (USearch). Хранит эмбеддинги и ищет ближайшие по косинусной близости (COS).

#### 7. Document Store (`$document_store`)
```yaml
$document_store: !pw.xpacks.llm.document_store.DocumentStore
  docs: $sources
  parser: $parser
  splitter: $splitter
  retriever_factory: $retriever_factory
```
**Что это:** Связывает всё в один пайплайн: источники → парсер → сплиттер → эмбеддер → индекс.

#### 8. Question Answerer (`question_answerer`)
```yaml
question_answerer: !pw.xpacks.llm.question_answering.SummaryQuestionAnswerer
  llm: $llm
  indexer: $document_store
```
**Что это:** RAG-движок. При вопросе: ищет чанки в индексе, собирает контекст, отправляет в LLM, возвращает ответ. `SummaryQuestionAnswerer` ещё умеет суммаризировать списки текстов.

---

## Часть 4: Поток данных (как всё связано)

```
[data/*.pdf, *.docx]
        ↓
   $sources (pw.io.fs.read)
        ↓
   $parser (Docling) → текст из PDF/DOCX
        ↓
   $splitter (TokenCountSplitter) → чанки по 400 токенов
        ↓
   $embedder (OpenAI) → векторы
        ↓
   $retriever_factory (USearch) → векторный индекс
        ↓
   [Пользователь задаёт вопрос]
        ↓
   Вопрос → embedder → поиск в индексе → топ-K чанков
        ↓
   Промпт: "Контекст: {чанки}. Вопрос: {вопрос}"
        ↓
   $llm (GPT) → ответ
```

---

## Часть 5: Как запустить

### Шаг 1. Установка зависимостей
```bash
cd portfolio-rag-app
pip install -r requirements.txt
```
> **Windows:** Pathway лучше работает в Docker. Если локальный запуск падает — используй `docker compose up`.

### Шаг 2. API-ключ OpenAI
В `.env` пропиши:
```
OPENAI_API_KEY=sk-твой-ключ
```

### Шаг 3. Запуск бэкенда
```bash
python app.py
```
Сервер поднимется на `http://localhost:8000`. Подожди, пока в логах появится что-то вроде `0 entries (x minibatch(es)) have been...` — значит индексация завершена.

### Шаг 4. Запуск UI
В другом терминале:
```bash
cd ui
pip install -r requirements.txt
streamlit run ui.py
```
Открой `http://localhost:8501` и задавай вопросы.

### Альтернатива: Docker
```bash
docker compose build
docker compose up
```
Бэкенд: 8000, UI: 8501.

---

## Часть 6: Примеры запросов (curl)

**Статистика:**
```bash
curl -X POST http://localhost:8000/v1/statistics -H "Content-Type: application/json"
```

**Поиск:**
```bash
curl -X POST http://localhost:8000/v1/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?", "k": 5}'
```

**Вопрос (RAG):**
```bash
curl -X POST http://localhost:8000/v2/answer \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is RAG and how does it work?"}'
```

---

## Часть 7: Что можно улучшить для портфолио

1. **Добавить README** с скриншотами и описанием стека.
2. **Поменять LLM** — попробуй Ollama (локально) или другую модель в `app.yaml`.
3. **Кастомный промпт** — в `question_answerer` задай `prompt_template`.
4. **Гибридный поиск** — BM25 + векторный (см. документацию Pathway).
5. **Деплой** — Render, Railway, или GCP по гайду Pathway.

---

## Резюме

| Компонент | Роль |
|-----------|------|
| Pathway | Стриминговая платформа: инкрементальная обработка, без отдельного ETL |
| Docling | Парсинг PDF/DOCX в текст |
| TokenCountSplitter | Разбиение на чанки |
| OpenAI Embedder | Текст → вектор |
| USearch | Векторный индекс, поиск похожих чанков |
| OpenAI Chat | Генерация ответа по контексту |
| Streamlit | Простой UI для демо |

Всё вместе = **RAG с живой индексацией**. Добавил файл — он автоматически попал в индекс. Спросил — получил ответ на основе твоих документов.
