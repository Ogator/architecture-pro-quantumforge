"""Пример работы RAG бота"""
from pathlib import Path
from rag_bot import RAGBot

# Configuration
INDEX_PATH = Path(__file__).resolve().parents[2] / 'task_3' / 'artifacts' / 'index'

# Выберите провайдер:
# Вариант A: Локальная модель через Ollama (по умолчанию, не требует API ключа)
LLM_PROVIDER = "ollama"
MODEL_NAME = "qwen2.5:3b"
API_KEY = None

# Вариант B: OpenAI (требует API ключ)
# LLM_PROVIDER = "openai"
# MODEL_NAME = "gpt-4o-mini"
# API_KEY = "your-openai-api-key-here"  # Или установите OPENAI_API_KEY env var


def main():
    """Demonstrate programmatic usage of RAG bot."""

    # Initialize bot
    print("Initializing RAG bot...")
    bot = RAGBot(
        index_path=INDEX_PATH,
        llm_provider=LLM_PROVIDER,
        model_name=MODEL_NAME,
        api_key=API_KEY,
        top_k=3,
        enable_few_shot=True,
        enable_cot=True
    )
    print("✓ Bot initialized\n")

    # Example 1: Simple chat interface
    print("="*80)
    print("Example 1: Simple chat")
    print("="*80)
    query = "Кто такие борги?"
    print(f"Query: {query}\n")

    answer = bot.chat(query)
    print(f"Answer: {answer}\n")

    # Example 2: Full result with metadata
    print("="*80)
    print("Example 2: Full result with metadata")
    print("="*80)
    query = "What is the Prime Directive?"
    print(f"Query: {query}\n")

    result = bot.generate_answer(query)

    print(f"Answer:\n{result['answer']}\n")
    print(f"Retrieved chunks: {len(result['chunks'])}")
    for i, chunk in enumerate(result['chunks'], 1):
        print(f"  {i}. {chunk['source']} (score: {chunk['score']:.3f})")

    print(f"\nTokens used: {result['metadata']['usage']['total_tokens']}")
    print(f"  - Prompt: {result['metadata']['usage']['prompt_tokens']}")
    print(f"  - Completion: {result['metadata']['usage']['completion_tokens']}")

    # Example 3: Query with no answer
    print("\n" + "="*80)
    print("Example 3: Query with no answer in knowledge base")
    print("="*80)
    query = "Сколько стоит билет на Enterprise?"
    print(f"Query: {query}\n")

    result = bot.generate_answer(query)
    print(f"Answer:\n{result['answer']}\n")

    # Example 4: Retrieval only (no LLM generation)
    print("="*80)
    print("Example 4: Retrieval only")
    print("="*80)
    query = "USS Enterprise"
    print(f"Query: {query}\n")

    chunks = bot.retrieve(query)
    print(f"Retrieved {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n{i}. {chunk['source']} (score: {chunk['score']:.3f})")
        print(f"   {chunk['text'][:200]}...")

    # Cleanup
    print("\n" + "="*80)
    bot.close()
    print("✓ Bot closed")


if __name__ == '__main__':
    main()
