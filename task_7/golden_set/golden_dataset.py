"""Golden dataset for RAG evaluation.

This file contains reference questions and expected answers for evaluating
the RAG bot's coverage and quality.
"""
from __future__ import annotations

GOLDEN_DATASET = [
    # =======================================================================
    # CATEGORY 1: Characters (Персонажи)
    # =======================================================================
    {
        "id": "char_001",
        "category": "characters",
        "question": "Кто такой Velthar Deyn?",
        "expected_answer": "Velthar Deyn — капитан корабля MV Vaelor, аналог James T. Kirk",
        "expected_sources": ["james_t_kirk.md"],
        "difficulty": "easy",
    },
    {
        "id": "char_002",
        "category": "characters",
        "question": "Who is Sareth?",
        "expected_answer": "Sareth is a Syrithi officer, first officer on MV Vaelor, analog of Spock",
        "expected_sources": ["spock.md"],
        "difficulty": "easy",
    },
    {
        "id": "char_003",
        "category": "characters",
        "question": "Расскажи про Herald",
        "expected_answer": "Herald — всемогущее существо из континуума, аналог Q",
        "expected_sources": ["q.md"],
        "difficulty": "medium",
    },

    # =======================================================================
    # CATEGORY 2: Species (Расы)
    # =======================================================================
    {
        "id": "species_001",
        "category": "species",
        "question": "Кто такие Hiveborn?",
        "expected_answer": "Hiveborn — киборгическая раса коллективного разума, аналог Borg",
        "expected_sources": ["borg.md"],
        "difficulty": "easy",
    },
    {
        "id": "species_002",
        "category": "species",
        "question": "What are Draugs known for?",
        "expected_answer": "Draugs are warrior species from Droganth, known for honor and combat traditions, analog of Klingons",
        "expected_sources": ["klingon.md"],
        "difficulty": "easy",
    },
    {
        "id": "species_003",
        "category": "species",
        "question": "Какая родная планета Syrithi?",
        "expected_answer": "Syran — родная планета расы Syrithi (аналог Vulcan)",
        "expected_sources": ["vulcan.md"],
        "difficulty": "medium",
    },
    {
        "id": "species_004",
        "category": "species",
        "question": "Расскажи про Ashen",
        "expected_answer": "Ashen — милитаристская раса, аналог Romulan",
        "expected_sources": ["romulan.md"],
        "difficulty": "medium",
    },

    # =======================================================================
    # CATEGORY 3: Technology (Технологии)
    # =======================================================================
    {
        "id": "tech_001",
        "category": "technology",
        "question": "Что такое slipstream core?",
        "expected_answer": "Slipstream core — двигатель сверхсветовой скорости, аналог warp drive",
        "expected_sources": ["warp_drive.md"],
        "difficulty": "easy",
    },
    {
        "id": "tech_002",
        "category": "technology",
        "question": "What is a phase modulator?",
        "expected_answer": "Phase modulator is a defensive technology, analog of shields",
        "expected_sources": ["shields.md"],
        "difficulty": "medium",
    },
    {
        "id": "tech_003",
        "category": "technology",
        "question": "Как работает транспортер?",
        "expected_answer": "Transporter — технология материализации объектов",
        "expected_sources": ["transporter.md"],
        "difficulty": "medium",
    },

    # =======================================================================
    # CATEGORY 4: Organizations & Concepts (Организации и концепции)
    # =======================================================================
    {
        "id": "org_001",
        "category": "organizations",
        "question": "What is the Sanctity Edict?",
        "expected_answer": "Sanctity Edict is the prime directive of Voidwatch, prohibits interference with developing civilizations",
        "expected_sources": ["prime_directive.md"],
        "difficulty": "easy",
    },
    {
        "id": "org_002",
        "category": "organizations",
        "question": "Что такое Voidwatch?",
        "expected_answer": "Voidwatch — межзвёздная организация исследователей, аналог Starfleet",
        "expected_sources": ["starfleet.md"],
        "difficulty": "easy",
    },
    {
        "id": "org_003",
        "category": "organizations",
        "question": "Расскажи про United Dawnstar Coalition",
        "expected_answer": "United Dawnstar Coalition — объединение планет, аналог Federation",
        "expected_sources": ["united_federation_of_planets.md"],
        "difficulty": "medium",
    },

    # =======================================================================
    # CATEGORY 5: Ships & Locations (Корабли и локации)
    # =======================================================================
    {
        "id": "ship_001",
        "category": "ships",
        "question": "Расскажи про MV Vaelor",
        "expected_answer": "MV Vaelor — флагманский корабль Voidwatch класса Vertex, номер VA-2201, аналог USS Enterprise",
        "expected_sources": ["uss_enterprise.md"],
        "difficulty": "easy",
    },
    {
        "id": "ship_002",
        "category": "ships",
        "question": "What is the registry number of MV Vaelor?",
        "expected_answer": "VA-2201 (original: NCC-1701)",
        "expected_sources": ["uss_enterprise.md"],
        "difficulty": "medium",
    },
    {
        "id": "loc_001",
        "category": "locations",
        "question": "Какая планета является столицей Federation?",
        "expected_answer": "Dawnstar (Earth analog)",
        "expected_sources": ["earth.md"],
        "difficulty": "medium",
    },

    # =======================================================================
    # CATEGORY 6: Cross-topic & Complex (Межтематические и сложные)
    # =======================================================================
    {
        "id": "complex_001",
        "category": "complex",
        "question": "Кто служит первым офицером на MV Vaelor?",
        "expected_answer": "Sareth (Spock analog)",
        "expected_sources": ["spock.md", "uss_enterprise.md"],
        "difficulty": "medium",
    },
    {
        "id": "complex_002",
        "category": "complex",
        "question": "Какая раса с планеты Droganth ценит честь и боевые традиции?",
        "expected_answer": "Draugs (Klingons)",
        "expected_sources": ["klingon.md", "qo_nos.md"],
        "difficulty": "hard",
    },
    {
        "id": "complex_003",
        "category": "complex",
        "question": "Почему Voidwatch не может вмешиваться в дела развивающихся цивилизаций?",
        "expected_answer": "Из-за Sanctity Edict — главного принципа Voidwatch (Prime Directive)",
        "expected_sources": ["prime_directive.md", "starfleet.md"],
        "difficulty": "hard",
    },

    # =======================================================================
    # CATEGORY 7: Adversarial / Out-of-scope (Некорректные вопросы)
    # =======================================================================
    {
        "id": "oos_001",
        "category": "out_of_scope",
        "question": "Сколько стоит билет на MV Vaelor?",
        "expected_answer": "НЕТ В БАЗЕ - должен сказать 'не знаю'",
        "expected_sources": [],
        "difficulty": "easy",
    },
    {
        "id": "oos_002",
        "category": "out_of_scope",
        "question": "Какая любимая еда у Velthar Deyn?",
        "expected_answer": "НЕТ В БАЗЕ - должен сказать 'не знаю'",
        "expected_sources": [],
        "difficulty": "easy",
    },
    {
        "id": "oos_003",
        "category": "out_of_scope",
        "question": "Когда был основан Voidwatch Institute?",
        "expected_answer": "НЕТ В БАЗЕ - должен сказать 'не знаю'",
        "expected_sources": [],
        "difficulty": "medium",
    },
    {
        "id": "oos_004",
        "category": "out_of_scope",
        "question": "Что такое квантовая физика?",
        "expected_answer": "НЕ ИЗ ДОМЕНА - общий вопрос вне контекста базы знаний",
        "expected_sources": [],
        "difficulty": "medium",
    },
]


def get_golden_dataset() -> list[dict]:
    """Return the full golden dataset."""
    return GOLDEN_DATASET


def get_by_category(category: str) -> list[dict]:
    """Get all questions from a specific category."""
    return [q for q in GOLDEN_DATASET if q["category"] == category]


def get_by_difficulty(difficulty: str) -> list[dict]:
    """Get all questions of specific difficulty."""
    return [q for q in GOLDEN_DATASET if q["difficulty"] == difficulty]


def get_categories() -> list[str]:
    """Get list of all categories."""
    return sorted(set(q["category"] for q in GOLDEN_DATASET))


def get_statistics() -> dict:
    """Get dataset statistics."""
    return {
        "total": len(GOLDEN_DATASET),
        "by_category": {cat: len(get_by_category(cat)) for cat in get_categories()},
        "by_difficulty": {
            diff: len(get_by_difficulty(diff))
            for diff in ["easy", "medium", "hard"]
        },
    }


if __name__ == "__main__":
    import json
    stats = get_statistics()
    print("Golden Dataset Statistics:")
    print(json.dumps(stats, indent=2))
