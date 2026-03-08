"""
RAGAS Evaluation — метрики качества RAG
Запуск: python eval_rag.py
Требует: pip install ragas
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

def run_eval():
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        from datasets import Dataset
    except ImportError:
        print("Установи: pip install ragas datasets")
        return

    from app import build_rag

    rag_result, err = build_rag()
    if err:
        print(err)
        return

    chain = rag_result["chain"]
    retriever = rag_result["retriever"]

    # Тестовые пары (вопрос, эталонный ответ) — добавь свои из документов
    test_data = [
        {"question": "What is RAG?", "ground_truth": "RAG stands for Retrieval-Augmented Generation. It combines a vector database, an LLM, and real-time indexing."},
        {"question": "How do I use this app?", "ground_truth": "Add documents to the data folder, wait for indexing, then ask questions in natural language."},
    ]

    questions = [d["question"] for d in test_data]
    ground_truths = [d["ground_truth"] for d in test_data]

    answers = []
    contexts = []
    for q in questions:
        ctx = retriever(q)
        contexts.append([c.page_content for c in ctx])
        answers.append(chain.invoke(q))

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )
    print("\n=== RAGAS Metrics ===")
    print(result)

if __name__ == "__main__":
    run_eval()
