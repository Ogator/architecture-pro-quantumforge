"""Demo script for RAG bot - runs predefined queries and saves results."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from rag_bot import RAGBot, ROOT


# Successful queries - bot should provide useful answers
SUCCESSFUL_QUERIES = [
    "Кто такие борги?",
    "What is the Prime Directive?",
    "Какая родная планета клингонов?",
    "Расскажи про USS Enterprise",
    "Что такое варп-двигатель?",
]

# Queries with no answer or filtered - bot should say "I don't know"
NO_ANSWER_QUERIES = [
    "Сколько стоит билет на Enterprise?",
    "Какая любимая еда у капитана Пикарда?",
    "Когда был основан Звездный Флот?",
    "Что такое квантовая физика в Star Trek?",
    "Расскажи про эпизод, которого нет в базе",
]


def run_demo(
    index_path: Path,
    llm_provider: str = "openai",
    model_name: str = "gpt-4o-mini",
    api_key: str | None = None,
    top_k: int = 3,
    enable_few_shot: bool = True,
    enable_cot: bool = True,
    output_dir: Path | None = None,
):
    """
    Run demo with predefined queries.

    Args:
        index_path: Path to vector index
        llm_provider: LLM provider
        model_name: Model name
        api_key: API key
        top_k: Number of chunks to retrieve
        enable_few_shot: Enable few-shot prompting
        enable_cot: Enable Chain-of-Thought
        output_dir: Directory to save results (optional)
    """
    print("="*80)
    print("RAG Bot Demo")
    print("="*80)
    print(f"\nКонфигурация:")
    print(f"  LLM: {llm_provider}/{model_name}")
    print(f"  Few-shot: {'✓' if enable_few_shot else '✗'}")
    print(f"  Chain-of-Thought: {'✓' if enable_cot else '✗'}")
    print(f"  Top-K: {top_k}")
    print()

    # Initialize bot
    print("Инициализация бота...")
    bot = RAGBot(
        index_path=index_path,
        llm_provider=llm_provider,
        model_name=model_name,
        api_key=api_key,
        top_k=top_k,
        enable_few_shot=enable_few_shot,
        enable_cot=enable_cot
    )
    print("✓ Бот готов\n")

    results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "llm_provider": llm_provider,
            "model": model_name,
            "top_k": top_k,
            "few_shot": enable_few_shot,
            "cot": enable_cot,
        },
        "successful": [],
        "no_answer": [],
        "total_tokens": 0,
    }

    # Run successful queries
    print("="*80)
    print("ЧАСТЬ 1: Запросы с полезными ответами")
    print("="*80)
    print()

    for i, query in enumerate(SUCCESSFUL_QUERIES, 1):
        print(f"[{i}/{len(SUCCESSFUL_QUERIES)}] Вопрос: {query}")
        print("-" * 80)

        try:
            result = bot.generate_answer(query)

            print(f"Ответ:\n{result['answer']}\n")
            print(f"Источники: {', '.join(c['source'].split('/')[-1] for c in result['chunks'])}")
            print(f"Токенов: {result['metadata']['usage']['total_tokens']}")
            print()

            results["successful"].append(result)
            results["total_tokens"] += result["metadata"]["usage"]["total_tokens"]

        except Exception as e:
            print(f"ОШИБКА: {e}\n")
            results["successful"].append({
                "query": query,
                "error": str(e)
            })

    # Run no-answer queries
    print("="*80)
    print("ЧАСТЬ 2: Запросы без ответа или с фильтрацией")
    print("="*80)
    print()

    for i, query in enumerate(NO_ANSWER_QUERIES, 1):
        print(f"[{i}/{len(NO_ANSWER_QUERIES)}] Вопрос: {query}")
        print("-" * 80)

        try:
            result = bot.generate_answer(query)

            print(f"Ответ:\n{result['answer']}\n")

            # Check if bot correctly said "I don't know"
            answer_lower = result['answer'].lower()
            said_dont_know = any(phrase in answer_lower for phrase in [
                "не знаю", "don't know", "нет информации", "no information",
                "not found", "не найдено", "недостаточно", "insufficient"
            ])

            if said_dont_know:
                print("✓ Бот корректно указал на отсутствие информации")
            else:
                print("⚠ Бот дал ответ, хотя информации может не быть")

            print(f"Источники: {', '.join(c['source'].split('/')[-1] for c in result['chunks']) if result['chunks'] else 'нет'}")
            print(f"Токенов: {result['metadata']['usage']['total_tokens']}")
            print()

            results["no_answer"].append({
                **result,
                "said_dont_know": said_dont_know
            })
            results["total_tokens"] += result["metadata"]["usage"]["total_tokens"]

        except Exception as e:
            print(f"ОШИБКА: {e}\n")
            results["no_answer"].append({
                "query": query,
                "error": str(e)
            })

    # Summary
    print("="*80)
    print("ИТОГИ")
    print("="*80)
    print(f"Успешных ответов: {len(results['successful'])}")
    print(f"Запросов без ответа: {len(results['no_answer'])}")
    print(f"Всего токенов использовано: {results['total_tokens']}")

    # Count correct "don't know" responses
    correct_dont_know = sum(
        1 for r in results["no_answer"]
        if not isinstance(r, dict) or r.get("said_dont_know", False)
    )
    print(f"Корректных 'не знаю': {correct_dont_know}/{len(results['no_answer'])}")
    print()

    # Save results
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"demo_results_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Результаты сохранены: {output_file}")

    bot.close()


def main():
    parser = argparse.ArgumentParser(description="Demo script for RAG bot")
    parser.add_argument(
        '--index',
        type=Path,
        default=ROOT / 'task_3' / 'artifacts' / 'index',
        help='Path to vector index'
    )
    parser.add_argument(
        '--llm-provider',
        choices=['openai', 'ollama', 'yandex'],
        default='ollama',
        help='LLM provider'
    )
    parser.add_argument(
        '--model',
        default='qwen2.5:3b',
        help='Model name'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=3,
        help='Number of chunks to retrieve'
    )
    parser.add_argument(
        '--no-few-shot',
        action='store_true',
        help='Disable few-shot prompting'
    )
    parser.add_argument(
        '--no-cot',
        action='store_true',
        help='Disable Chain-of-Thought'
    )
    parser.add_argument(
        '--api-key',
        help='API key for LLM provider'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=ROOT / 'task_4' / 'artifacts' / 'examples',
        help='Output directory for results'
    )

    args = parser.parse_args()

    try:
        run_demo(
            index_path=args.index,
            llm_provider=args.llm_provider,
            model_name=args.model,
            api_key=args.api_key,
            top_k=args.top_k,
            enable_few_shot=not args.no_few_shot,
            enable_cot=not args.no_cot,
            output_dir=args.output
        )
        return 0
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
