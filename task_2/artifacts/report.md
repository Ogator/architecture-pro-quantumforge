## Задание 2. Подготовка базы знаний

### Что сделано

| Шаг | Результат |
|---|---|
| Выбор источника | [Memory Alpha](https://memory-alpha.fandom.com) — канон Star Trek (сериалы и фильмы) |
| Скачивание | 41 страница через MediaWiki API (`action=query&prop=extracts&explaintext=1`) — без HTML и разметки |
| Очистка | удалены цитаты эпизодов `(TOS: "…")`, разделы «Appendices / Background information / Apocrypha / External links» |
| Замена терминов | 320+ терминов из `terms_map.json`, longest-first, с сохранением регистра |
| Проверка | `_masking_report.json` — 41 файл, 0 утечек оригинальных терминов |

### Структура

```
task_2/tools/
├── fetch_knowledge_base.py     # скачивание из Memory Alpha API
└── build_knowledge_base.py     # замена терминов + проверка утечек

task_2/artifacts/raw_knowledge_base/              # сырые тексты (41 .txt) + _manifest.json
task_2/artifacts/knowledge_base/                  # финальная замаскированная база
├── *.md                        # 41 документ
├── terms_map.json              # 321 замена (оригинал → вымышленный термин)
└── _masking_report.json        # отчёт проверки утечек
```

### Список документов

**Персонажи (17):** Velthar Deyn (James T. Kirk), Sareth (Spock), Brenic Halst (McCoy), Torren Quell (Scotty),
Adisa Maren (Uhura), Renn Takeda (Sulu), Yuri Vlasov (Chekov), Corvin Leysard (Picard), Eddan Rhys (Riker),
Vekta (Data), Gharun (Worf), Sienna Valar (Troi), Korel Aventi (Khan), Herald (Q), Zethra (Sybok), Thanev (Sarek), The Medician (The Doctor)

**Расы (7):** Syrithi (Vulcan), Draugs (Klingon), Ashen (Romulan), Hiveborn (Borg), Vaskari (Cardassian),
Orallin (Ferengi), Kestrin (Bajoran)

**Корабли (5):** MV Vaelor (Enterprise NCC-1701), MV Vaelor-D (Enterprise-D), MV Pharae (Voyager),
MV Kinrath (Defiant), Hiveborn Monolith (Borg cube)

**Места (5):** Tellura (Earth), Droganth (Qo'noS), Cindras (Romulus), Kestras (Bajor), Station Ninefold (DS9)

**Технологии (6):** slipstream core (warp drive), quantum translocator (transporter),
matter synthesizer (replicator), sensory amphitheatre (holodeck), ion lancet (phaser), veil engine (cloaking device)

**Организации (5):** Concordium of Worlds (Federation), Voidwatch (Starfleet), Voidwatch Institute (Academy),
Sanctity Edict (Prime Directive), Elder Silence (Star Trek — franchise name)

**События (1):** Engram of Harrow Reach (Battle of Wolf 359)

### Логика замены

1. Многословные термины обрабатываются **первыми** (`"James T. Kirk"` раньше `"Kirk"`).
2. Регистр сохраняется: `KIRK` → `VELTHAR`, `Kirk` → `Velthar`, `kirk` → `velthar`.
3. Два прохода + regex-добивка для остаточных упоминаний (`NCC-\d+`, коды сериалов `TOS/TNG/DS9/…`, `NBC`, `Paramount`).
4. Проверка: для каждого файла флаг `leaks=[]`; итог — **0 утечек** на 41 файле.

### Проверка качества

После маскировки выполнены два прогона проверки:
- **Автоматическая:** `check_leaks()` в `build_knowledge_base.py` + `_masking_report.json`.
- **Ручная эвристика:** top-300 самых частых capitalized-фраз — все относятся к вымышленному миру.

Пример «до/после» (`klingon.md`):

> **До:** «Klingons were a proud, tradition-bound people who valued honor and combat…»
> **После:** «Draugs were a proud, tradition-bound people who valued honor and combat…»

### Ответы на проверочные вопросы

| Вопрос | Что ожидается от бота |
|---|---|
| Какая раса с Droganth ценит честь? | Draugs |
| Как называется главный корабль Velthar Deyn? | MV Vaelor (VA-2201) |
| Что такое Sanctity Edict? | Запрет Voidwatch вмешиваться в дела развивающихся цивилизаций |
| Как звали Syrith, служившего первым помощником Sareth? | Неизвестно — данных в базе нет → **«Я не знаю»** |
| Кто победил в Engram of Harrow Reach? | Hiveborn — ожидаемый ответ |

### Команда сборки

```bash
python task_2/tools/fetch_knowledge_base.py     # скачать 41 страницу
python task_2/tools/build_knowledge_base.py     # применить terms_map + отчёт
```

---


