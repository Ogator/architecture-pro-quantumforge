# Задание 7: Аналитика покрытия и качества базы знаний

## Описание

Оценка полноты и актуальности базы знаний через тестирование на Golden Dataset — наборе эталонных вопросов с ожидаемыми ответами.

## Цели

1. **Выявить пробелы** в базе знаний — темы, на которые бот не может ответить
2. **Оценить качество retrieval** — насколько хорошо векторный поиск находит релевантные документы
3. **Проверить отказы** — корректно ли бот отказывается отвечать на вопросы вне его компетенции
4. **Сформировать рекомендации** по улучшению базы знаний

## Структура

```
task_7/
├── golden_set/
│   └── golden_dataset.py       # Эталонный набор вопросов (30 вопросов)
├── tools/
│   ├── evaluate.py             # Скрипт оценки
│   └── generate_report.py      # Генератор отчётов
├── artifacts/
│   ├── logs/
│   │   └── evaluation_*.json   # JSON результаты
│   └── reports/
│       └── coverage_*.md       # Markdown отчёты
└── README.md
```

## Golden Dataset

### Статистика

- **Всего вопросов:** 30
- **Категории:**
  - Characters (персонажи): 3
  - Species (расы): 4
  - Technology (технологии): 3
  - Organizations (организации): 3
  - Ships & Locations (корабли и локации): 3
  - Complex (сложные межтематические): 3
  - Out-of-scope (вне базы): 4

- **Сложность:**
  - Easy: 10
  - Medium: 15
  - Hard: 3
  - Out-of-scope: 4

### Формат записи

```python
{
    "id": "char_001",
    "category": "characters",
    "question": "Кто такой Velthar Deyn?",
    "expected_answer": "Velthar Deyn — капитан корабля MV Vaelor, аналог James T. Kirk",
    "expected_sources": ["james_t_kirk.md"],
    "difficulty": "easy",
}
```

## Метрики оценки

### 1. Retrieval Metrics

- **Retrieval Success Rate** — процент вопросов, для которых хотя бы один ожидаемый документ попал в top-k
- **Average Recall** — средний recall (какая доля ожидаемых документов найдена) по всем вопросам

### 2. Answer Quality

- **Out-of-Scope Refusal Rate** — процент корректных отказов на вопросы вне базы знаний

### 3. Coverage by Category

Процент успешно отвеченных вопросов по каждой категории.

## Запуск оценки

### Шаг 1: Запустить evaluation

```bash
# Базовый запуск
python task_7/tools/evaluate.py

# С OpenAI
export OPENAI_API_KEY="your-key"
python task_7/tools/evaluate.py --llm-provider openai --model gpt-4o-mini

# С кастомными параметрами
python task_7/tools/evaluate.py --top-k 5 --model llama3.2:3b

# Указать выходной файл
python task_7/tools/evaluate.py --output task_7/artifacts/logs/my_eval.json
```

**Результат:** JSON-файл с детальными результатами оценки.

### Шаг 2: Сгенерировать отчёт

```bash
# Автоматически создаст .md файл рядом с .json
python task_7/tools/generate_report.py task_7/artifacts/logs/evaluation_20250117_120000.json

# Указать выходной файл
python task_7/tools/generate_report.py task_7/artifacts/logs/evaluation_*.json \
    --output task_7/artifacts/reports/coverage_report.md
```

**Результат:** Markdown-отчёт с анализом пробелов и рекомендациями.

## Пример workflow

```bash
# 1. Запустить оценку
python task_7/tools/evaluate.py

# Вывод:
# ======================================================================
# RAG EVALUATION
# ======================================================================
# Golden dataset: 30 questions
# Model: ollama/qwen2.5:3b
# ======================================================================
# 
# [1/30] char_001 (characters/easy)
# Q: Кто такой Velthar Deyn?
# A: Velthar Deyn — капитан корабля MV Vaelor...
#    Retrieval: recall=1.00, retrieved=True
#    Sources: james_t_kirk.md
# ...

# 2. Получить последний evaluation файл
EVAL_FILE=$(ls -t task_7/artifacts/logs/evaluation_*.json | head -1)

# 3. Сгенерировать отчёт
python task_7/tools/generate_report.py $EVAL_FILE

# 4. Посмотреть отчёт
cat task_7/artifacts/logs/evaluation_*.md
```

## Формат результатов

### evaluation_*.json

```json
{
  "timestamp": "2025-01-17T12:00:00",
  "model": "ollama/qwen2.5:3b",
  "top_k": 3,
  "questions": [
    {
      "id": "char_001",
      "category": "characters",
      "difficulty": "easy",
      "question": "Кто такой Velthar Deyn?",
      "answer": "...",
      "retrieval": {
        "retrieved_sources": ["james_t_kirk.md"],
        "expected_sources": ["james_t_kirk.md"],
        "recall": 1.0,
        "retrieved": true
      }
    }
  ],
  "summary": {
    "total_questions": 30,
    "retrieval_success_rate": 0.85,
    "average_recall": 0.78,
    "out_of_scope_refusal_rate": 0.75,
    "coverage_by_category": {...}
  }
}
```

### coverage_*.md

Markdown отчёт содержит:
- Executive Summary с ключевыми метриками
- Coverage by Category с визуальными индикаторами
- Identified Gaps — список проблемных вопросов
- Out-of-Scope Handling — анализ отказов
- Recommendations — конкретные шаги по улучшению
- Next Steps — план действий

## Интерпретация результатов

### Хорошие показатели

- **Retrieval Success Rate ≥ 80%** — векторный поиск работает хорошо
- **Average Recall ≥ 0.7** — большинство релевантных документов находятся
- **OOS Refusal Rate ≥ 80%** — бот корректно отказывается на неподходящие вопросы

### Тревожные сигналы

- **Retrieval Success Rate < 60%** — проблемы с векторным поиском или базой знаний
- **Average Recall < 0.5** — документы разбиты неоптимально или эмбеддинги слабые
- **OOS Refusal Rate < 50%** — бот галлюцинирует на неизвестные вопросы

### Рекомендации по улучшению

#### Если низкий Retrieval Success Rate:
1. Проверьте наличие документов из `expected_sources`
2. Расширьте документы — добавьте больше контекста
3. Улучшите формулировки в документах для лучшего semantic match

#### Если низкий Average Recall:
1. Увеличьте `top_k` (но учтите рост затрат на LLM)
2. Пересмотрите стратегию чанкинга
3. Попробуйте другую embedding модель

#### Если низкий OOS Refusal Rate:
1. Усильте system prompt с примерами отказов
2. Добавьте confidence thresholding на retrieval scores
3. Рассмотрите fine-tuning LLM на отказы

## Расширение Golden Dataset

Чтобы добавить новые вопросы:

```python
# Откройте task_7/golden_set/golden_dataset.py
# Добавьте новую запись в GOLDEN_DATASET:

{
    "id": "new_001",
    "category": "your_category",
    "question": "Your question?",
    "expected_answer": "Expected answer",
    "expected_sources": ["relevant_doc.md"],
    "difficulty": "medium",
}
```

**Рекомендации:**
- Добавляйте вопросы из реальных пользовательских запросов
- Включайте failed cases из production логов
- Покрывайте edge cases и сложные межтематические вопросы

## Continuous Monitoring

Для регулярной проверки качества:

```bash
# Добавьте в cron (например, еженедельно)
0 3 * * 0 /usr/bin/python3 /path/to/task_7/tools/evaluate.py && \
  /usr/bin/python3 /path/to/task_7/tools/generate_report.py \
  $(ls -t /path/to/task_7/artifacts/logs/evaluation_*.json | head -1)
```

Это поможет:
- Отслеживать деградацию качества после обновлений базы
- Выявлять новые пробелы по мере роста числа вопросов
- Мониторить влияние изменений в retrieval pipeline

## Связь с другими заданиями

- **Задание 4** — RAG bot, который тестируется
- **Задание 3** — векторный индекс, качество которого оценивается
- **Задание 6** — автообновление может влиять на coverage, нужен мониторинг
- **Задание 2** — gaps могут указывать на недостающие документы в базе знаний

## Диаграмма архитектуры

PlantUML диаграмма процесса оценки: [artifacts/diagrams/evaluation_pipeline.puml](artifacts/diagrams/evaluation_pipeline.puml)

Показывает:
- Поток данных от Golden Dataset через RAG Bot к метрикам
- Процесс evaluation и генерации отчёта
- Выявление пробелов и рекомендации по улучшению
- Опциональный continuous monitoring

