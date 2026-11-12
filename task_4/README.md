# Задание 4: RAG-бот с техниками промптинга

## Описание

Реализация RAG-бота для базы знаний Star Trek с поддержкой:
- **Few-shot prompting** — примеры вопросов-ответов
- **Chain-of-Thought (CoT)** — явное рассуждение модели

Поддерживаются LLM:
- **Ollama** (локальные модели, по умолчанию) — не требует API ключа
- **OpenAI** (GPT-4o-mini, GPT-4o) — требует API ключ

## Установка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Вариант A: Локальные модели через Ollama (рекомендуется для локальной проверки)
# 1. Установите Ollama: https://ollama.com/download
# 2. Запустите Ollama
ollama serve

# 3. Скачайте модель (в отдельном терминале)
ollama pull qwen2.5:3b        # Лёгкая модель, 3B параметров, ~2GB
# или
ollama pull llama3.2:3b       # Альтернатива от Meta

# Вариант B: OpenAI GPT (требует API ключ)
export OPENAI_API_KEY="your-api-key-here"
```

**Требования для Ollama:**
- Python 3.9+
- RAM: 4GB минимум (для qwen2.5:3b)
- Ollama Desktop или Server установлены и запущены

## Быстрый старт

```bash
# С локальной моделью (по умолчанию)
python task_4/tools/rag_bot.py

# С OpenAI
python task_4/tools/rag_bot.py --llm-provider openai --model gpt-4o-mini

# Демонстрация с тестами (5 успешных + 5 "не знаю")
python task_4/tools/demo.py
python task_4/tools/demo.py --llm-provider openai --model gpt-4o-mini
```

## Опции запуска

- `--llm-provider NAME` — провайдер LLM: `ollama` (по умолчанию) | `openai`
- `--model NAME` — модель:
  - Ollama: `qwen2.5:3b` (по умолчанию), `llama3.2:3b`, `mistral:7b`
  - OpenAI: `gpt-4o-mini`, `gpt-4o`
- `--top-k N` — количество чанков (по умолчанию: 3)
- `--no-few-shot` — отключить Few-shot prompting
- `--no-cot` — отключить Chain-of-Thought

## Рекомендуемые локальные модели

| Модель | Размер | RAM | Качество | Скорость | Команда установки |
|--------|--------|-----|----------|----------|-------------------|
| qwen2.5:3b | ~2 GB | 4 GB | Хорошее | Быстро | `ollama pull qwen2.5:3b` |
| llama3.2:3b | ~2 GB | 4 GB | Хорошее | Быстро | `ollama pull llama3.2:3b` |
| mistral:7b | ~4 GB | 8 GB | Отличное | Средне | `ollama pull mistral:7b` |
| llama3.1:8b | ~4.7 GB | 8 GB | Отличное | Средне | `ollama pull llama3.1:8b` |

**Рекомендация:** Начните с `qwen2.5:3b` — хороший баланс качества и скорости.

## Программное использование

```python
from pathlib import Path
from task_4.tools.rag_bot import RAGBot

# Локальная модель через Ollama
bot = RAGBot(
    index_path=Path("task_3/artifacts/index"),
    llm_provider="ollama",
    model_name="qwen2.5:3b"
)

# Или OpenAI
bot = RAGBot(
    index_path=Path("task_3/artifacts/index"),
    llm_provider="openai",
    model_name="gpt-4o-mini",
    api_key="your-key"  # или через env OPENAI_API_KEY
)

answer = bot.chat("Кто такие борги?")
print(answer)

bot.close()
```

## Тестирование

```bash
pytest task_4/tests/
```

## Устранение проблем

### Ошибка: "Cannot connect to Ollama"
**Решение:**
```bash
# Запустите Ollama в отдельном терминале
ollama serve

# Проверьте, что модель скачана
ollama list

# Скачайте модель, если её нет
ollama pull qwen2.5:3b
```

### Ошибка: "Model not found"
**Решение:**
```bash
# Посмотрите доступные модели
ollama list

# Скачайте нужную модель
ollama pull <model-name>
```

## Структура

- `tools/rag_bot.py` — основной модуль RAG-бота
- `tools/demo.py` — демонстрация с 10 тестовыми запросами
- `tools/api_example.py` — примеры использования
- `tests/test_rag_bot.py` — unit-тесты
- `artifacts/REPORT.md` — детальный отчет

## Результат задания

✅ Модуль RAG с загрузкой индекса, поиском, Few-shot и CoT  
✅ Запускаемый REPL-интерфейс  
✅ Поддержка локальных моделей (Ollama) и OpenAI  
✅ 5 примеров успешных диалогов в `demo.py`  
✅ 5 примеров ситуаций "я не знаю" в `demo.py`
