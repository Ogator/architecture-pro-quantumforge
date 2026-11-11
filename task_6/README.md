# Задание 6: Автоматическое обновление базы знаний

## Описание

Полностью автоматизированный процесс мониторинга директории с документами, обновления векторного индекса и логирования изменений.

## Архитектура

**Источник данных:** локальная директория `task_6/watch_dir/`

**Поток данных:**
1. Скрипт `update_index.py` сканирует `watch_dir/`
2. Для каждого `.md` файла вычисляется SHA256 хеш
3. Новые/изменённые файлы → `add_to_index.py` → векторный индекс
4. Состояние сохраняется в `update_state.json`
5. Лог операций записывается в `logs/update.log`

**Планировщик:** cron (Linux/macOS) или Task Scheduler (Windows)

## Структура

```
task_6/
├── tools/
│   └── update_index.py         # Основной скрипт обновления
├── artifacts/
│   ├── update_state.json       # Состояние (хеши файлов)
��   ├── logs/
│   │   └── update.log          # JSON-логи обновлений
│   └── diagrams/
│       └── architecture.puml   # PlantUML диаграмма
├── watch_dir/                  # Директория для м��ниторинга
│   └── (положите сюда .md файлы)
├── crontab.example             # Пример настройки cron
└── README.md
```

## Установка

### 1. Запуск вручную (тест)

```bash
# Создайте тестовый документ
echo "# Test Document\n\nThis is a test." > task_6/watch_dir/test.md

# Запустите обновление
python task_6/tools/update_index.py

# Проверьте лог
cat task_6/artifacts/logs/update.log
```

### 2. Настройка автоматического запуска

#### Linux/macOS (cron)

```bash
# Откройте crontab
crontab -e

# Добавьте строку для ежедневного запуска в 03:00
0 3 * * * /usr/bin/python3 /home/ogator/Projects/Yandex_Practicum/architecture-pro-quantumforge/task_6/tools/update_index.py >> /home/ogator/Projects/Yandex_Practicum/architecture-pro-quantumforge/task_6/artifacts/logs/cron.log 2>&1

# Или каждый час
0 * * * * /usr/bin/python3 /path/to/task_6/tools/update_index.py >> /path/to/task_6/artifacts/logs/cron.log 2>&1

# Сохраните и выйдите
```

**Важно:** используйте абсолютные пути в cron!

#### Windows (Task Scheduler)

1. Откройте Task Scheduler
2. Create Basic Task → Name: "RAG Index Update"
3. Trigger: Daily at 03:00
4. Action: Start a program
   - Program: `C:\Python39\python.exe`
   - Arguments: `C:\path\to\task_6\tools\update_index.py`
   - Start in: `C:\path\to\architecture-pro-quantumforge`
5. Finish

### 3. Проверка работы

```bash
# Посмотреть задачи cron
crontab -l

# Проверить последний лог
tail -f task_6/artifacts/logs/update.log

# Проверить состояние
cat task_6/artifacts/update_state.json
```

## Параметры

```
--watch-dir PATH      Директория для мониторинга (по умолчанию: task_6/watch_dir)
--index PATH          Путь к векторному индексу (по умолчанию: task_3/artifacts/index)
--state-file PATH     Файл состояния (по умолчанию: task_6/artifacts/update_state.json)
--log-file PATH       Файл лога (по умолчанию: task_6/artifacts/logs/update.log)
--dry-run             Показать изменения без применения
```

## Примеры использования

```bash
# Базовый запуск
python task_6/tools/update_index.py

# С кастомной директорией
python task_6/tools/update_index.py --watch-dir /path/to/docs

# Dry-run (показать что будет обновлено)
python task_6/tools/update_index.py --dry-run
```

## Формат логов

```json
{
  "timestamp": "2025-01-17T03:00:15.123456",
  "watch_dir": "/path/to/watch_dir",
  "index_path": "/path/to/index",
  "files_added": ["new_doc.md"],
  "files_updated": ["changed_doc.md"],
  "files_removed": [],
  "errors": []
}
```

## Диаграмма архитектуры

См. `artifacts/diagrams/architecture.puml` — PlantUML диаграмма потока данных.

Для генерации изображения:
```bash
# Установите PlantUML
sudo apt install plantuml  # Linux
brew install plantuml      # macOS

# Сгенерируйте PNG
plantuml task_6/artifacts/diagrams/architecture.puml
```

## Мониторинг и отладка

### Проверка логов

```bash
# Последние обновления
tail -20 task_6/artifacts/logs/update.log | jq

# Статистика за всё время
cat task_6/artifacts/logs/update.log | jq '.files_added | length' | awk '{s+=$1} END {print "Total files added:", s}'

# Найти ошибки
cat task_6/artifacts/logs/update.log | jq 'select(.errors | length > 0)'
```

### Ручной тригер обновления

```bash
# Запустить сейчас (не дожидаясь cron)
python task_6/tools/update_index.py
```

## Расширения

### Добавление внешних источников

Для интеграции с S3, Git, RSS или API:

1. Создайте скрипт `fetch_from_source.py`
2. Скачайте документы в `watch_dir/`
3. `update_index.py` автоматически их подхватит

Пример:
```bash
#!/bin/bash
# fetch_and_update.sh
cd /path/to/architecture-pro-quantumforge

# Скачать из S3
aws s3 sync s3://my-bucket/docs/ task_6/watch_dir/

# Обновить индекс
python task_6/tools/update_index.py
```

Настройте cron на запуск этого скрипта.

## Производительность

- **Инкрементальность:** обрабатываются только новые/изменённые файлы
- **Идемпотентность:** повторный запуск безопасен
- **Хеширование:** SHA256 для детекции изменений
- **Логирование:** все операции записываются

## Безопасность

- Скрипт читает только `.md` файлы
- Не удаляет файлы из индекса автоматически (требует ручного вмешательства)
- Логи содержат полную историю изменений для аудита
