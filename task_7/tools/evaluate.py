"""RAG evaluation tool — coverage and quality analysis.

Evaluates the RAG bot against golden dataset to identify gaps in knowledge base.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'task_4' / 'tools'))
sys.path.insert(0, str(ROOT / 'task_7' / 'golden_set'))

from rag_bot import RAGBot
from golden_dataset import get_golden_dataset, get_statistics, get_categories


def evaluate_retrieval(bot: RAGBot, question: str, expected_sources: list[str], top_k: int = 3) -> dict:
    """
    Evaluate retrieval quality.

    Returns:
        {
            "retrieved_sources": [...],
            "expected_sources": [...],
            "recall": float,  # how many expected sources were retrieved
            "retrieved": bool  # at least one expected source in top-k
        }
    """
    chunks = bot.retrieve(question)
    retrieved_sources = [c['source'].split('/')[-1] for c in chunks[:top_k]]

    if not expected_sources:
        # Out-of-scope question
        return {
            "retrieved_sources": retrieved_sources,
            "expected_sources": [],
            "recall": None,
            "retrieved": None,
        }

    # Check recall
    expected_set = set(expected_sources)
    retrieved_set = set(retrieved_sources)

    intersection = expected_set & retrieved_set
    recall = len(intersection) / len(expected_set) if expected_set else 0.0
    retrieved = len(intersection) > 0

    return {
        "retrieved_sources": retrieved_sources,
        "expected_sources": expected_sources,
        "recall": recall,
        "retrieved": retrieved,
    }


def evaluate_answer_relevance(answer: str, expected_keywords: list[str]) -> dict:
    """
    Simple keyword-based relevance check.

    Returns:
        {
            "keywords_found": int,
            "keywords_total": int,
            "score": float
        }
    """
    answer_lower = answer.lower()
    found = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)

    return {
        "keywords_found": found,
        "keywords_total": len(expected_keywords),
        "score": found / len(expected_keywords) if expected_keywords else 0.0,
    }


def evaluate_out_of_scope(answer: str) -> dict:
    """
    Check if bot correctly refuses to answer out-of-scope questions.

    Returns:
        {
            "refused": bool,  # detected "не знаю" / "I don't know"
            "confidence": float
        }
    """
    answer_lower = answer.lower()

    refusal_patterns = [
        "не знаю",
        "не могу ответить",
        "нет информации",
        "i don't know",
        "i cannot answer",
        "no information",
        "not found",
        "недостаточно информации",
    ]

    refused = any(pattern in answer_lower for pattern in refusal_patterns)

    return {
        "refused": refused,
        "confidence": 1.0 if refused else 0.0,
    }


def run_evaluation(
    bot: RAGBot,
    golden_dataset: list[dict],
    output_file: Path,
) -> dict:
    """Run full evaluation on golden dataset."""

    results = {
        "timestamp": datetime.now().isoformat(),
        "model": f"{bot.llm_provider}/{bot.model_name}",
        "top_k": bot.top_k,
        "questions": [],
        "summary": {},
    }

    print("=" * 70)
    print("RAG EVALUATION")
    print("=" * 70)
    print(f"Golden dataset: {len(golden_dataset)} questions")
    print(f"Model: {bot.llm_provider}/{bot.model_name}")
    print("=" * 70)

    for i, item in enumerate(golden_dataset, 1):
        qid = item["id"]
        question = item["question"]
        category = item["category"]
        difficulty = item["difficulty"]
        expected_sources = item.get("expected_sources", [])

        print(f"\n[{i}/{len(golden_dataset)}] {qid} ({category}/{difficulty})")
        print(f"Q: {question}")

        # Retrieval evaluation
        retrieval_result = evaluate_retrieval(bot, question, expected_sources, bot.top_k)

        # Generate answer
        answer_result = bot.generate_answer(question)
        answer = answer_result["answer"]

        print(f"A: {answer[:100]}{'...' if len(answer) > 100 else ''}")

        # Evaluate answer
        if category == "out_of_scope":
            oos_result = evaluate_out_of_scope(answer)
            print(f"   Out-of-scope: refused={oos_result['refused']}")
        else:
            print(f"   Retrieval: recall={retrieval_result['recall']:.2f}, retrieved={retrieval_result['retrieved']}")
            print(f"   Sources: {', '.join(retrieval_result['retrieved_sources'][:3])}")

        # Store result
        question_result = {
            "id": qid,
            "category": category,
            "difficulty": difficulty,
            "question": question,
            "answer": answer,
            "retrieval": retrieval_result,
        }

        if category == "out_of_scope":
            question_result["out_of_scope"] = oos_result

        results["questions"].append(question_result)

    # Calculate summary statistics
    in_scope_questions = [q for q in results["questions"] if q["category"] != "out_of_scope"]
    oos_questions = [q for q in results["questions"] if q["category"] == "out_of_scope"]

    # Retrieval metrics
    retrieval_success = sum(1 for q in in_scope_questions if q["retrieval"]["retrieved"])
    avg_recall = sum(q["retrieval"]["recall"] for q in in_scope_questions) / len(in_scope_questions) if in_scope_questions else 0

    # Out-of-scope metrics
    oos_refusal_rate = sum(1 for q in oos_questions if q.get("out_of_scope", {}).get("refused", False)) / len(oos_questions) if oos_questions else 0

    # Coverage by category
    coverage_by_category = {}
    for cat in get_categories():
        cat_questions = [q for q in in_scope_questions if q["category"] == cat]
        if cat_questions:
            cat_retrieved = sum(1 for q in cat_questions if q["retrieval"]["retrieved"])
            coverage_by_category[cat] = {
                "total": len(cat_questions),
                "retrieved": cat_retrieved,
                "coverage": cat_retrieved / len(cat_questions),
            }

    results["summary"] = {
        "total_questions": len(golden_dataset),
        "in_scope_questions": len(in_scope_questions),
        "out_of_scope_questions": len(oos_questions),
        "retrieval_success_rate": retrieval_success / len(in_scope_questions) if in_scope_questions else 0,
        "average_recall": avg_recall,
        "out_of_scope_refusal_rate": oos_refusal_rate,
        "coverage_by_category": coverage_by_category,
    }

    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total questions: {results['summary']['total_questions']}")
    print(f"In-scope: {results['summary']['in_scope_questions']}")
    print(f"Out-of-scope: {results['summary']['out_of_scope_questions']}")
    print(f"\nRetrieval success rate: {results['summary']['retrieval_success_rate']:.1%}")
    print(f"Average recall: {results['summary']['average_recall']:.2f}")
    print(f"Out-of-scope refusal rate: {results['summary']['out_of_scope_refusal_rate']:.1%}")

    print("\nCoverage by category:")
    for cat, stats in results['summary']['coverage_by_category'].items():
        print(f"  {cat:15} {stats['retrieved']}/{stats['total']} ({stats['coverage']:.1%})")

    print(f"\nResults saved: {output_file}")
    print("=" * 70)

    return results


def main():
    parser = argparse.ArgumentParser(description="RAG evaluation tool")
    parser.add_argument(
        '--index',
        type=Path,
        default=ROOT / 'task_3' / 'artifacts' / 'index',
    )
    parser.add_argument(
        '--llm-provider', choices=['openai', 'ollama'], default='ollama',
    )
    parser.add_argument('--model', default='qwen2.5:3b')
    parser.add_argument('--top-k', type=int, default=3)
    parser.add_argument(
        '--output',
        type=Path,
        default=ROOT / 'task_7' / 'artifacts' / 'logs' / f'evaluation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
    )
    parser.add_argument('--api-key', help='API key for OpenAI')

    args = parser.parse_args()

    try:
        # Initialize bot
        print("Initializing RAG bot...")
        bot = RAGBot(
            index_path=args.index,
            llm_provider=args.llm_provider,
            model_name=args.model,
            api_key=args.api_key,
            top_k=args.top_k,
            enable_few_shot=True,
            enable_cot=True,
        )

        # Load golden dataset
        golden_dataset = get_golden_dataset()
        stats = get_statistics()
        print(f"Loaded golden dataset: {stats}")

        # Run evaluation
        results = run_evaluation(bot, golden_dataset, args.output)

        bot.close()
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
