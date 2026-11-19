# Использование локальных моделей через Ollama

## Установка Ollama

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS
```bash
brew install ollama
```

### Windows
Скачайте установщик с https://ollama.com/download

## Запуск Ollama

```bash
# Запустите сервер (в отдельном терминале)
ollama serve
```

Сервер будет доступен на `http://localhost:11434`

## Установка моделей

### Рекомендуемые модели для RAG-бота

**Для начала (лёгкие, быстрые):**
```bash
ollama pull qwen2.5:3b        # Qwen 2.5, 3B параметров, ~2GB
ollama pull llama3.2:3b       # Llama 3.2, 3B параметров, ~2GB
```

**Для лучшего качества (требуют больше RAM):**
```bash
ollama pull mistral:7b        # Mistral, 7B параметров, ~4GB
ollama pull llama3.1:8b       # Llama 3.1, 8B параметров, ~4.7GB
```

## Проверка установленных моделей

```bash
# Список моделей
ollama list

# Информация о модели
ollama show qwen2.5:3b
```

## Тестирование модели

```bash
# Интерактивный чат с моделью
ollama run qwen2.5:3b

# Или одиночный запрос
ollama run qwen2.5:3b "Explain quantum computing in simple terms"
```

## Использование с RAG-ботом

```bash
# Убедитесь, что Ollama запущена
ollama serve

# Запустите RAG-бота (по умолчанию использует Ollama)
python task_4/tools/rag_bot.py

# Или явно укажите модель
python task_4/tools/rag_bot.py --llm-provider ollama --model mistral:7b
```

## Сравнение моделей

| Модель | Параметры | Размер | RAM | Качество | Скорость | Лучше для |
|--------|-----------|--------|-----|----------|----------|-----------|
| qwen2.5:3b | 3B | ~2GB | 4GB | ★★★☆☆ | Быстро | Быстрые ответы, тестирование |
| llama3.2:3b | 3B | ~2GB | 4GB | ★★★☆☆ | Быстро | Общие вопросы |
| mistral:7b | 7B | ~4GB | 8GB | ★★★★☆ | Средне | Качественные ответы |
| llama3.1:8b | 8B | ~4.7GB | 8GB | ★★★★☆ | Средне | Сложные рассуждения |

**Рекомендация:** Начните с `qwen2.5:3b` для быстрой проверки, затем попробуйте `mistral:7b` для лучшего качества.

## Системные требования

**Минимальные (для 3B моделей):**
- RAM: 4 GB
- Диск: 5 GB свободного места
- CPU: любой современный процессор

**Рекомендуемые (для 7-8B моделей):**
- RAM: 8 GB
- Диск: 10 GB свободного места
- CPU: многоядерный процессор

**Опционально (для ускорения):**
- GPU: NVIDIA с CUDA или AMD с ROCm
- Apple Silicon: использует Metal автоматически

## Устранение проблем

### Ошибка: "connection refused"
```bash
# Убедитес��, что Ollama запущена
ollama serve

# Проверьте статус
curl http://localhost:11434
```

### Модель загружается медленно
```bash
# Это нормально при первом запуске
# Модель загружается с https://ollama.com/library/
# Последующие запуски будут быстрыми
```

### Недостаточно памяти
```bash
# Используйте более лёгкую модель
ollama pull qwen2.5:3b

# Или квантизированную версию
ollama pull llama3.1:8b-q4_0  # 4-bit квантизация
```

## Дополнительные ресурсы

- Официальный сайт: https://ollama.com
- Библиотека моделей: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama
- Документация API: https://github.com/ollama/ollama/blob/main/docs/api.md

## Удаление модели

```bash
# Удалить модель
ollama rm qwen2.5:3b

# Посмотреть все модели
ollama list
```

## Python API

Ollama предоставляет Python SDK, который используется в RAG-боте:

```python
import ollama

# Простой запрос
response = ollama.chat(model='qwen2.5:3b', messages=[
    {'role': 'user', 'content': 'Why is the sky blue?'}
])
print(response['message']['content'])

# С системным промптом
response = ollama.chat(
    model='qwen2.5:3b',
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Explain RAG in simple terms'}
    ]
)
```

## Переключение между моделями

В RAG-боте можно легко переключаться между моделями:

```bash
# Qwen (быстро)
python task_4/tools/rag_bot.py --model qwen2.5:3b

# Mistral (качество)
python task_4/tools/rag_bot.py --model mistral:7b

# Llama (баланс)
python task_4/tools/rag_bot.py --model llama3.1:8b
```
