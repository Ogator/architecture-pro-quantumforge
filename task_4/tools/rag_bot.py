"""RAG bot with Few-shot and Chain-of-Thought prompting techniques."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
MODEL = "BAAI/bge-m3"
COLLECTION = "quantumforge"
DIMENSION = 1024


class RAGBot:
    """RAG bot that retrieves relevant context and generates answers using LLM."""

    def __init__(
        self,
        index_path: Path,
        llm_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        top_k: int = 3,
        enable_few_shot: bool = True,
        enable_cot: bool = True,
    ):
        """
        Initialize RAG bot.

        Args:
            index_path: Path to the vector index directory
            llm_provider: LLM provider ("openai" or "yandex")
            model_name: Model name to use
            api_key: API key for the LLM provider
            top_k: Number of top chunks to retrieve
            enable_few_shot: Enable Few-shot prompting
            enable_cot: Enable Chain-of-Thought prompting
        """
        self.index_path = index_path
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.top_k = top_k
        self.enable_few_shot = enable_few_shot
        self.enable_cot = enable_cot

        # Load manifest and validate
        manifest_path = index_path / 'manifest.json'
        if not manifest_path.exists():
            raise ValueError(f"Index manifest not found: {manifest_path}")

        self.manifest = json.loads(manifest_path.read_text())
        if self.manifest['model'] != MODEL or self.manifest['dimension'] != DIMENSION:
            raise ValueError('Incompatible embedding model')

        # Initialize embedding model
        self._load_embedding_model()

        # Initialize Qdrant client
        self._init_qdrant_client()

        # Initialize LLM
        self._init_llm(api_key)

    def _load_embedding_model(self):
        """Load the sentence transformer model for embeddings."""
        from sentence_transformers import SentenceTransformer
        self.embedding_model = SentenceTransformer(
            MODEL,
            revision=self.manifest.get('revision'),
            device="cpu"
        )

    def _init_qdrant_client(self):
        """Initialize Qdrant client."""
        from qdrant_client import QdrantClient
        qdrant_path = self.index_path / 'qdrant'
        if not qdrant_path.exists():
            raise ValueError(f"Qdrant storage not found: {qdrant_path}")
        self.qdrant_client = QdrantClient(path=str(qdrant_path))

    def _init_llm(self, api_key: Optional[str]):
        """Initialize LLM client."""
        if self.llm_provider == "openai":
            import openai
            self.llm_client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        elif self.llm_provider == "ollama":
            try:
                import ollama
            except ImportError:
                raise ImportError(
                    "Ollama package not installed.\n"
                    "Install with: pip install ollama\n"
                    "Then start Ollama server: ollama serve\n"
                    "And download a model: ollama pull qwen2.5:3b"
                )
            try:
                self.llm_client = ollama.Client()
                # Проверка доступности Ollama
                try:
                    self.llm_client.list()
                except Exception as e:
                    raise ConnectionError(
                        f"Cannot connect to Ollama at http://localhost:11434\n"
                        f"Make sure Ollama is running: ollama serve\n"
                        f"Error: {e}"
                    )
            except ConnectionError:
                raise
            except Exception as e:
                raise RuntimeError(f"Error initializing Ollama client: {e}")
        elif self.llm_provider == "yandex":
            raise NotImplementedError("YandexGPT support coming soon")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    def retrieve(self, query: str) -> list[dict]:
        """
        Retrieve relevant chunks for the query.

        Args:
            query: User query

        Returns:
            List of relevant chunks with scores
        """
        # Encode query
        vector = self.embedding_model.encode(query, normalize_embeddings=True).tolist()

        # Search in Qdrant
        results = self.qdrant_client.query_points(
            COLLECTION,
            query=vector,
            limit=self.top_k,
            with_payload=True
        )

        return [
            dict(score=point.score, **point.payload)
            for point in results.points
        ]

    def _build_few_shot_examples(self) -> str:
        """
        Build few-shot examples from the knowledge base.

        Returns examples in Q&A format from the Star Trek domain.
        """
        examples = [
            {
                "question": "Как называется родная планета клингонов?",
                "answer": "Родная планета клингонов называется Droganth (Кроносъ в оригинале)."
            },
            {
                "question": "What is the Prime Directive?",
                "answer": "The Prime Directive (known as the Sanctity Edict) is Starfleet's fundamental principle that forbids interference with the internal development of alien civilizations, especially pre-warp societies."
            }
        ]

        return "\n\n".join([
            f"Q: {ex['question']}\nA: {ex['answer']}"
            for ex in examples
        ])

    def _build_system_prompt(self) -> str:
        """
        Build system prompt with optional CoT instructions.

        Returns:
            System prompt string
        """
        base_prompt = """Ты — помощник по вселенной Star Trek. Твоя задача — отвечать на вопросы пользователей, используя предоставленную информацию из базы знаний.

Правила:
1. Отвечай только на основе предоставленного контекста
2. Если информации недостаточно или её нет, честно скажи "Я не знаю"
3. Не придумывай факты, которых нет в контексте
4. Отвечай на том же языке, что и вопрос пользователя"""

        if self.enable_cot:
            base_prompt += """
5. Сначала размышляй над вопросом, а потом давай ответ
6. Показывай свои шаги рассуждения:
   - Какую информацию ты нашел в контексте
   - Как она связана с вопросом
   - Какой вывод ты делаешь"""

        return base_prompt

    def _format_context(self, chunks: list[dict]) -> str:
        """
        Format retrieved chunks as context.

        Args:
            chunks: Retrieved chunks

        Returns:
            Formatted context string
        """
        if not chunks:
            return "Контекст: информация не найдена."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Источник {i}: {chunk['source']}, релевантность: {chunk['score']:.3f}]\n{chunk['text']}"
            )

        return "Контекст из базы знаний:\n\n" + "\n\n".join(context_parts)

    def _build_user_prompt(self, query: str, chunks: list[dict]) -> str:
        """
        Build user prompt with context and optional few-shot examples.

        Args:
            query: User query
            chunks: Retrieved chunks

        Returns:
            User prompt string
        """
        parts = []

        # Add few-shot examples if enabled
        if self.enable_few_shot:
            parts.append("Примеры вопросов и ответов:\n\n" + self._build_few_shot_examples())

        # Add context
        parts.append(self._format_context(chunks))

        # Add query
        parts.append(f"\nВопрос: {query}")

        if self.enable_cot:
            parts.append("\nПожалуйста, сначала опиши свои шаги рассуждения, а затем дай финальный ответ.")
        else:
            parts.append("\nОтвет:")

        return "\n\n".join(parts)

    def generate_answer(self, query: str) -> dict:
        """
        Generate answer for the user query.

        Args:
            query: User query

        Returns:
            Dictionary with answer, retrieved chunks, and metadata
        """
        # Retrieve relevant chunks
        chunks = self.retrieve(query)

        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, chunks)

        # Generate response using LLM
        if self.llm_provider == "openai":
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            answer = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        elif self.llm_provider == "ollama":
            response = self.llm_client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.7,
                    "num_predict": 1000
                }
            )
            answer = response['message']['content']
            usage = {
                "prompt_tokens": response.get('prompt_eval_count', 0),
                "completion_tokens": response.get('eval_count', 0),
                "total_tokens": response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
            }
        else:
            raise NotImplementedError(f"LLM provider {self.llm_provider} not implemented")

        return {
            "query": query,
            "answer": answer,
            "chunks": chunks,
            "metadata": {
                "top_k": self.top_k,
                "few_shot_enabled": self.enable_few_shot,
                "cot_enabled": self.enable_cot,
                "llm_provider": self.llm_provider,
                "model": self.model_name,
                "usage": usage
            }
        }

    def chat(self, query: str) -> str:
        """
        Simple chat interface that returns just the answer text.

        Args:
            query: User query

        Returns:
            Answer text
        """
        result = self.generate_answer(query)
        return result["answer"]

    def close(self):
        """Close connections."""
        if hasattr(self, 'qdrant_client'):
            self.qdrant_client.close()


def main():
    """Interactive REPL for the RAG bot."""
    import argparse

    parser = argparse.ArgumentParser(description="RAG Bot with Few-shot and CoT")
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
        help='LLM provider to use'
    )
    parser.add_argument(
        '--model',
        default='qwen2.5:3b',
        help='Model name to use'
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
        help='Disable Chain-of-Thought prompting'
    )
    parser.add_argument(
        '--api-key',
        help='API key for LLM provider (or set OPENAI_API_KEY env var)'
    )

    args = parser.parse_args()

    # Initialize bot
    print("Инициализация RAG бота...")
    try:
        bot = RAGBot(
            index_path=args.index,
            llm_provider=args.llm_provider,
            model_name=args.model,
            api_key=args.api_key,
            top_k=args.top_k,
            enable_few_shot=not args.no_few_shot,
            enable_cot=not args.no_cot
        )
    except ImportError as e:
        print(f"❌ Ошибка зависимостей:\n{e}")
        if "ollama" in str(e).lower():
            print("\n💡 Решение:")
            print("  1. Установите ollama: pip install -U ollama")
            print("  2. Запустите Ollama: ollama serve")
            print("  3. Скачайте модель: ollama pull qwen2.5:3b")
            print("  4. Попробуйте снова")
        return 1
    except ConnectionError as e:
        print(f"❌ Ошибка подключения:\n{e}")
        if "ollama" in str(e).lower():
            print("\n💡 Решение:")
            print("  1. Убедитесь, что Ollama запущена: ollama serve")
            print("  2. Убедитесь, что модель загружена: ollama pull qwen2.5:3b")
            print("  3. Проверьте, что Ollama доступна на http://localhost:11434")
        return 1
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return 1

    print(f"\nRAG бот готов!")
    print(f"Модель: {args.model}")
    print(f"Few-shot: {'✓' if not args.no_few_shot else '✗'}")
    print(f"Chain-of-Thought: {'✓' if not args.no_cot else '✗'}")
    print(f"Top-K: {args.top_k}")
    print("\nВведите ваш вопрос (или 'exit' для выхода, 'help' для справки)\n")

    try:
        while True:
            try:
                query = input("Вопрос: ").strip()

                if not query:
                    continue

                if query.lower() in ('exit', 'quit', 'q'):
                    print("До свидания!")
                    break

                if query.lower() == 'help':
                    print("""
Команды:
  exit, quit, q - выход из программы
  help          - показать эту справку

Примеры вопросов:
  - Кто такие борги?
  - Что такое Prime Directive?
  - Какая родная планета клингонов?
  - Расскажи про USS Enterprise
                    """)
                    continue

                print("\nГенерация ответа...")
                result = bot.generate_answer(query)

                print("\n" + "="*80)
                print(f"Ответ:\n{result['answer']}")
                print("="*80)

                # Show retrieved sources
                if result['chunks']:
                    print(f"\nИсточники ({len(result['chunks'])}):")
                    for i, chunk in enumerate(result['chunks'], 1):
                        print(f"  {i}. {chunk['source']} (релевантность: {chunk['score']:.3f})")

                print()

            except KeyboardInterrupt:
                print("\n\nПрервано пользователем. До свидания!")
                break
            except Exception as e:
                print(f"\nОшибка при обработке запроса: {e}")
                print("Попробуйте снова.\n")

    finally:
        bot.close()

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

