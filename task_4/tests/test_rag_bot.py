"""Tests for RAG bot."""
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

from rag_bot import RAGBot, ROOT


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "This is a test answer about Borg."
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    return mock_response


@pytest.fixture
def index_path():
    """Get path to the test index."""
    path = ROOT / 'task_3' / 'artifacts' / 'index'
    if not path.exists():
        pytest.skip(f"Index not found at {path}")
    return path


@pytest.fixture
def mock_api_key():
    """Provide a mock API key."""
    return "sk-test-key-mock"


def test_rag_bot_initialization(index_path, mock_api_key):
    """Test RAG bot can be initialized."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': mock_api_key}):
        with patch('openai.OpenAI'):
            bot = RAGBot(
                index_path=index_path,
                llm_provider="openai",
                model_name="gpt-4o-mini",
                api_key=mock_api_key,
                top_k=3,
                enable_few_shot=True,
                enable_cot=True
            )

            assert bot.index_path == index_path
            assert bot.llm_provider == "openai"
            assert bot.model_name == "gpt-4o-mini"
            assert bot.top_k == 3
            assert bot.enable_few_shot is True
            assert bot.enable_cot is True

            bot.close()


def test_rag_bot_retrieve(index_path, mock_api_key):
    """Test retrieval functionality."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': mock_api_key}):
        with patch('openai.OpenAI'):
            bot = RAGBot(
                index_path=index_path,
                llm_provider="openai",
                api_key=mock_api_key
            )

            # Test retrieval
            results = bot.retrieve("What are the Borg?")

            assert isinstance(results, list)
            assert len(results) <= bot.top_k

            if results:
                # Check structure of first result
                assert 'score' in results[0]
                assert 'text' in results[0]
                assert 'source' in results[0]
                assert 0 <= results[0]['score'] <= 1

            bot.close()


def test_rag_bot_prompts(index_path, mock_api_key):
    """Test prompt building methods."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': mock_api_key}):
        with patch('openai.OpenAI'):
            bot = RAGBot(
                index_path=index_path,
                llm_provider="openai",
                api_key=mock_api_key,
                enable_few_shot=True,
                enable_cot=True
            )

            # Test system prompt
            system_prompt = bot._build_system_prompt()
            assert "помощник" in system_prompt.lower()
            assert "шаги" in system_prompt.lower()  # CoT enabled

            # Test few-shot examples
            examples = bot._build_few_shot_examples()
            assert "Q:" in examples
            assert "A:" in examples
            assert "клингон" in examples.lower() or "klingon" in examples.lower()

            # Test context formatting
            mock_chunks = [
                {"score": 0.95, "source": "borg.md", "text": "The Borg are cyborgs..."},
                {"score": 0.87, "source": "federation.md", "text": "Federation fights Borg..."}
            ]
            context = bot._format_context(mock_chunks)
            assert "Источник 1" in context
            assert "borg.md" in context
            assert "The Borg are cyborgs" in context

            # Test empty context
            empty_context = bot._format_context([])
            assert "не найдена" in empty_context.lower()

            bot.close()


def test_rag_bot_generate_answer(index_path, mock_api_key, mock_openai_response):
    """Test answer generation."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': mock_api_key}):
        with patch('openai.OpenAI') as mock_openai:
            # Setup mock
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai.return_value = mock_client

            bot = RAGBot(
                index_path=index_path,
                llm_provider="openai",
                api_key=mock_api_key,
                top_k=3,
                enable_few_shot=True,
                enable_cot=True
            )

            # Generate answer
            result = bot.generate_answer("Who are the Borg?")

            # Check result structure
            assert isinstance(result, dict)
            assert 'query' in result
            assert 'answer' in result
            assert 'chunks' in result
            assert 'metadata' in result

            assert result['query'] == "Who are the Borg?"
            assert result['answer'] == "This is a test answer about Borg."
            assert isinstance(result['chunks'], list)

            # Check metadata
            metadata = result['metadata']
            assert metadata['top_k'] == 3
            assert metadata['few_shot_enabled'] is True
            assert metadata['cot_enabled'] is True
            assert metadata['llm_provider'] == "openai"
            assert 'usage' in metadata
            assert metadata['usage']['total_tokens'] == 150

            bot.close()


def test_rag_bot_chat_simple(index_path, mock_api_key, mock_openai_response):
    """Test simple chat interface."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': mock_api_key}):
        with patch('openai.OpenAI') as mock_openai:
            # Setup mock
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai.return_value = mock_client

            bot = RAGBot(
                index_path=index_path,
                llm_provider="openai",
                api_key=mock_api_key
            )

            # Test simple chat
            answer = bot.chat("Who are the Borg?")

            assert isinstance(answer, str)
            assert answer == "This is a test answer about Borg."

            bot.close()


def test_rag_bot_disable_features(index_path, mock_api_key):
    """Test disabling Few-shot and CoT."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': mock_api_key}):
        with patch('openai.OpenAI'):
            bot = RAGBot(
                index_path=index_path,
                llm_provider="openai",
                api_key=mock_api_key,
                enable_few_shot=False,
                enable_cot=False
            )

            # System prompt should not mention CoT
            system_prompt = bot._build_system_prompt()
            assert "шаги" not in system_prompt.lower()

            # User prompt should not contain few-shot examples
            mock_chunks = [{"score": 0.95, "source": "test.md", "text": "Test text"}]
            user_prompt = bot._build_user_prompt("Test query", mock_chunks)
            assert "Примеры вопросов" not in user_prompt
            assert "Q:" not in user_prompt or "A:" not in user_prompt

            bot.close()


def test_invalid_index_path(mock_api_key):
    """Test initialization with invalid index path."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': mock_api_key}):
        with patch('openai.OpenAI'):
            with pytest.raises(ValueError, match="Index manifest not found"):
                RAGBot(
                    index_path=Path("/nonexistent/path"),
                    llm_provider="openai",
                    api_key=mock_api_key
                )


def test_unsupported_llm_provider(index_path, mock_api_key):
    """Test initialization with unsupported LLM provider."""
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        RAGBot(
            index_path=index_path,
            llm_provider="unsupported",
            api_key=mock_api_key
        )
