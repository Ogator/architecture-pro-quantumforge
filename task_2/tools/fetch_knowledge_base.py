#!/usr/bin/env python3
"""
Скачивает чистый текст страниц Memory Alpha (канон Star Trek) и сохраняет
его в task_2/artifacts/raw_knowledge_base/<slug>.txt — по одному файлу на сущность.

Использование:
    python task_2/tools/fetch_knowledge_base.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import time

import requests

# Точка входа MediaWiki API Memory Alpha
API = "https://memory-alpha.fandom.com/api.php"
USER_AGENT = "QuantumForge-RAG-Research/1.0 (educational project)"
# Папка для сырых текстов: <корень репозитория>/task_2/artifacts/raw_knowledge_base
OUT_DIR = pathlib.Path(__file__).resolve().parents[2] / "task_2" / "artifacts" / "raw_knowledge_base"

# 41 ключевая сущность: персонажи, расы, корабли, планеты, технологии, события
PAGES = [
    # --- Персонажи ---
    ("James T. Kirk", "character"),
    ("Spock", "character"),
    ("Leonard McCoy", "character"),
    ("Montgomery Scott", "character"),
    ("Nyota Uhura", "character"),
    ("Hikaru Sulu", "character"),
    ("Pavel Chekov", "character"),
    ("Jean-Luc Picard", "character"),
    ("William T. Riker", "character"),
    ("Data", "character"),
    ("Worf", "character"),
    ("Deanna Troi", "character"),
    ("Khan Noonien Singh", "character"),
    ("Q", "character"),
    # --- Расы ---
    ("Vulcan", "species"),
    ("Klingon", "species"),
    ("Romulan", "species"),
    ("Borg", "species"),
    ("Cardassian", "species"),
    ("Ferengi", "species"),
    ("Bajoran", "species"),
    # --- Корабли ---
    ("USS Enterprise (NCC-1701)", "ship"),
    ("USS Enterprise (NCC-1701-D)", "ship"),
    ("USS Voyager", "ship"),
    ("USS Defiant (2375)", "ship"),
    ("Borg cube", "ship"),
    # --- Планеты и места ---
    ("Earth", "planet"),
    ("Qo'noS", "planet"),
    ("Romulus", "planet"),
    ("Bajor", "planet"),
    ("Deep Space 9", "station"),
    # --- Технологии ---
    ("Warp drive", "technology"),
    ("Transporter", "technology"),
    ("Replicator", "technology"),
    ("Holodeck", "technology"),
    ("Phaser", "technology"),
    ("Cloaking device", "technology"),
    # --- События и организации ---
    ("United Federation of Planets", "organisation"),
    ("Starfleet", "organisation"),
    ("Battle of Wolf 359", "event"),
    ("Prime Directive", "concept"),
]


def slugify(title: str) -> str:
    """Превращает название страницы в имя файла: 'Warp drive' -> 'warp_drive'."""
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def clean(text: str) -> str:
    """Убирает из текста разметку, которая выдаёт вселенную."""
    # Вырезаем ссылки на эпизоды вида "(TOS: ...)", "(TNG: ...)" — они содержат названия серий
    text = re.sub(r"\((?:TOS|TNG|DS9|VOY|ENT|SNW|PIC|LD|PRO|DIS|film)[^)]*\)", "", text, flags=re.I)
    text = re.sub(r"\(\s*\)", "", text)
    # Схлопываем тройные и более пустые строки до двойных
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Удаляем остатки разметки файлов/категорий: [[File:...]], [[Category:...]]
    text = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", "", text, flags=re.I)
    return text.strip()


def fetch(title: str) -> str:
    """Запрашивает у MediaWiki API чистый текст страницы (без вики-разметки)."""
    r = requests.get(
        API,
        params={
            "action": "query",
            "prop": "extracts",   # хотим «извлечения», а не сырой wikitext
            "explaintext": 1,     # отдать уже очищенный текст
            "titles": title,
            "format": "json",
            "formatversion": 2,   # упрощённая структура ответа
        },
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    pages = data.get("query", {}).get("pages", [])
    if not pages or "missing" in pages[0]:
        raise RuntimeError(f"страница не найдена: {title}")
    return pages[0].get("extract", "")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []   # сводка: slug, название, тип, размер
    errors = 0
    for i, (title, kind) in enumerate(PAGES, 1):
        slug = slugify(title)
        try:
            raw = fetch(title)
            body = clean(raw)
            (OUT_DIR / f"{slug}.txt").write_text(body, encoding="utf-8")
            manifest.append({"slug": slug, "title": title, "kind": kind, "chars": len(body)})
            print(f"[{i:02d}/{len(PAGES)}] {title:<40} -> {len(body):>6} символов")
        except Exception as e:  # noqa: BLE001
            # Ошибка на одной странице не должна ронять весь прогон
            errors += 1
            print(f"[{i:02d}/{len(PAGES)}] ОШИБКА {title}: {e}", file=sys.stderr)
        # Небольшая пауза, чтобы не упираться в rate-limit фандома
        time.sleep(0.5)

    # Сохраняем manifest — пригодится на этапе замены терминов
    (OUT_DIR / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nЗаписано {len(manifest)} страниц в {OUT_DIR}, ошибок: {errors}.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())