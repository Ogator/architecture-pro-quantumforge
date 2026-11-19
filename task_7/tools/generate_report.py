"""Генератор отчёта по анализу покрытия и качества базы знаний."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def generate_report(evaluation_file: Path, output_file: Path):
    """Генерирует markdown отчёт из результатов оценки."""

    with open(evaluation_file, encoding='utf-8') as f:
        results = json.load(f)

    summary = results['summary']
    questions = results['questions']

    # Выявление пробелов
    failed_questions = [
        q for q in questions
        if q['category'] != 'out_of_scope' and not q['retrieval']['retrieved']
    ]

    # Группировка по категориям
    gaps_by_category = {}
    for q in failed_questions:
        cat = q['category']
        if cat not in gaps_by_category:
            gaps_by_category[cat] = []
        gaps_by_category[cat].append(q)

    # Анализ вопросов вне компетенции
    oos_failed = [
        q for q in questions
        if q['category'] == 'out_of_scope' and not q.get('out_of_scope', {}).get('refused', False)
    ]

    # Генерация markdown отчёта
    report = f"""# Отчёт по анализу покрытия RAG-системы

Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Краткие итоги

- **Всего вопросов:** {summary['total_questions']}
- **В области компетенции:** {summary['in_scope_questions']}
- **Вне области компетенции:** {summary['out_of_scope_questions']}

### Ключевые метрики

| Метрика | Значение |
|---------|----------|
| Успешность поиска (Retrieval Success Rate) | {summary['retrieval_success_rate']:.1%} |
| Средняя полнота (Average Recall) | {summary['average_recall']:.2f} |
| Корректность отказов (Out-of-scope Refusal Rate) | {summary['out_of_scope_refusal_rate']:.1%} |

## Покрытие по категориям

"""

    for cat, stats in summary['coverage_by_category'].items():
        coverage = stats['coverage']
        status = "✅" if coverage >= 0.8 else "⚠️" if coverage >= 0.5 else "❌"
        report += f"- **{cat}**: {stats['retrieved']}/{stats['total']} ({coverage:.1%}) {status}\n"

    report += "\n## Выявленные пробелы\n\n"

    if not failed_questions:
        report += "🎉 Пробелов не обнаружено! Все вопросы в области компетенции успешно обработаны.\n\n"
    else:
        report += f"Обнаружено **{len(failed_questions)} пробелов**, где бот не смог найти релевантные документы.\n\n"

        for cat, gaps in gaps_by_category.items():
            report += f"### {cat.title()} ({len(gaps)} пробелов)\n\n"
            for gap in gaps:
                report += f"**{gap['id']}**: {gap['question']}\n"
                report += f"- Ожидаемые источники: {', '.join(gap['retrieval']['expected_sources'])}\n"
                report += f"- Найдено: {', '.join(gap['retrieval']['retrieved_sources'][:3])}\n"
                report += f"- Сложность: {gap['difficulty']}\n\n"

    report += "## Обработка вопросов вне компетенции\n\n"

    if oos_failed:
        report += f"⚠️ **{len(oos_failed)} вопросов вне компетенции** были обработаны вместо корректного отказа:\n\n"
        for q in oos_failed:
            report += f"**{q['id']}**: {q['question']}\n"
            report += f"- Ответ: {q['answer'][:150]}...\n\n"
    else:
        report += "✅ Все вопросы вне компетенции были корректно отклонены.\n\n"

    report += "## Рекомендации\n\n"

    # Генерация рекомендаций
    if failed_questions:
        report += "### 1. Расширение базы знаний\n\n"
        report += "Добавьте или расширьте следующие темы:\n\n"

        for cat, gaps in gaps_by_category.items():
            if gaps:
                report += f"**{cat.title()}:**\n"
                unique_sources = set()
                for gap in gaps:
                    unique_sources.update(gap['retrieval']['expected_sources'])
                for src in sorted(unique_sources):
                    report += f"- Проверьте и расширьте `{src}`\n"
                report += "\n"

    if summary['retrieval_success_rate'] < 0.8:
        report += "### 2. Улучшение качества поиска\n\n"
        report += "- Рассмотрите увеличение параметра `top_k`\n"
        report += "- Проверьте стратегию разбиения документов — некоторые могут быть разбиты неоптимально\n"
        report += "- Попробуйте другие модели эмбеддингов для лучшего семантического соответствия\n\n"

    if summary['out_of_scope_refusal_rate'] < 0.8:
        report += "### 3. Усиление детектирования вопросов вне компетенции\n\n"
        report += "- Улучшите system prompt для лучшей обработки нерелевантных вопросов\n"
        report += "- Добавьте пороговое значение уверенности для оценок поиска\n"
        report += "- Рассмотрите fine-tuning промпта с отрицательными примерами\n\n"

    if summary['average_recall'] < 0.5:
        report += "### 4. Связи между документами\n\n"
        report += "- Добавьте перекрёстные ссылки между связанными документами\n"
        report += "- Рассмотрите иерархическую стратегию чанкинга\n"
        report += "- Реализуйте фильтрацию по метаданным для лучшего выбора контекста\n\n"

    report += """## Следующие шаги

1. **Немедленные действия:**
   - Устраните пробелы в категориях с низким покрытием
   - Добавьте недостающие документы или расширьте существующие
   - Протестируйте с обновлённой базой знаний

2. **Среднесрочные улучшения:**
   - Внедрите непрерывный мониторинг с помощью этого скрипта оценки
   - Настройте оповещения при падении покрытия ниже порога
   - Расширьте golden dataset запросами пользователей из production логов

3. **Долгосрочная стратегия:**
   - Интегрируйте цикл обратной связи от пользователей
   - Проведите A/B тестирование различных конфигураций поиска
   - Рассмотрите гибридный поиск (dense + keyword)

## Приложение: Детальные результаты

Полные результаты оценки см. в файле: `{evaluation_file.name}`

---

*Этот отчёт был автоматически сгенерирован инструментом оценки RAG.*
"""

    # Запись отчёта
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding='utf-8')

    print(f"✓ Отчёт сгенерирован: {output_file}")

    # Вывод ключевых находок в консоль
    print("\n" + "=" * 70)
    print("КЛЮЧЕВЫЕ НАХОДКИ")
    print("=" * 70)
    print(f"Выявлено пробелов: {len(failed_questions)}")
    print(f"Успешность поиска: {summary['retrieval_success_rate']:.1%}")
    print(f"Корректность отказов: {summary['out_of_scope_refusal_rate']:.1%}")

    if gaps_by_category:
        print("\nПробелы по категориям:")
        for cat, gaps in gaps_by_category.items():
            print(f"  {cat}: {len(gaps)}")

    print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Генератор отчёта по покрытию")
    parser.add_argument(
        'evaluation_file',
        type=Path,
        help='Путь к JSON файлу с результатами оценки'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Выходной markdown файл (по умолчанию: рядом с входным, .md расширение)'
    )

    args = parser.parse_args()

    if not args.evaluation_file.exists():
        print(f"Ошибка: файл оценки не найден: {args.evaluation_file}")
        return 1

    if args.output is None:
        args.output = args.evaluation_file.with_suffix('.md')

    try:
        generate_report(args.evaluation_file, args.output)
        return 0
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
