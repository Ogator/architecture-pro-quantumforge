#!/usr/bin/env python3
"""
Собирает замаскированную базу знаний из сырых текстов Memory Alpha.

Пайплайн:
  task_2/artifacts/raw_knowledge_base/*.txt   (чистый текст страниц Memory Alpha)
        │  1. отсекаем «внешнее» окончание страницы (раздел Appendices и всё после)
        │  2. применяем словарь замен TERMS (длинные термины первыми, с сохранением регистра)
        │  3. добиваем оставшиеся следы франшизы регулярными выражениями
        │  4. проверяем, что ни один оригинальный термин не остался
        ▼
  task_2/artifacts/knowledge_base/*.md
  task_2/artifacts/knowledge_base/terms_map.json
  task_2/artifacts/knowledge_base/_masking_report.json
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "task_2" / "artifacts" / "raw_knowledge_base"
OUT_DIR = ROOT / "task_2" / "artifacts" / "knowledge_base"

# --------------------------------------------------------------------------
# Словарь замен: оригинальный термин -> вымышленный.
# Длинные ключи применяются первыми ("James T. Kirk" раньше, чем "Kirk"),
# иначе псевдоним разобьётся на части, которые заменятся по отдельности.
# --------------------------------------------------------------------------
TERMS: dict[str, str] = {
    # ---- Персонажи ----
    "Q": "Herald",
    "James Tiberius Kirk": "Velthar Deyn",
    "James T. Kirk": "Velthar Deyn",
    "James Kirk": "Velthar Deyn",
    "Jim Kirk": "Velthar Deyn",
    "Kirk": "Velthar",
    "Spock": "Sareth",
    "Leonard H. McCoy": "Brenic Halst",
    "Leonard McCoy": "Brenic Halst",
    "McCoy": "Halst",
    "Montgomery Scott": "Torren Quell",
    "Scotty": "Torren",
    "Nyota Uhura": "Adisa Maren",
    "Uhura": "Adisa",
    "Hikaru Sulu": "Renn Takeda",
    "Sulu": "Renn",
    "Pavel Chekov": "Yuri Vlasov",
    "Chekov": "Yuri",
    "Jean-Luc Picard": "Corvin Leysard",
    "Jean Luc Picard": "Corvin Leysard",
    "Picard": "Leysard",
    "William T. Riker": "Eddan Rhys",
    "William Riker": "Eddan Rhys",
    "Riker": "Eddan",
    "Data": "Vekta",
    "Daystrom": "Corvallis",
    "Worf": "Gharun",
    # Экипаж ТНГ: только фамилии — имена вроде Beverly или Wesley не выдают вселенную
    "Crusher": "Marrow",
    "Beverly Crusher": "Beverly Marrow",
    "Geordi La Forge": "Geori Vane",
    "La Forge": "Vane",
    "Guinan": "Elyria",
    "Wesley Crusher": "Wesley Marrow",
    "Tasha Yar": "Tessa Varn",
    "Miles O'Brien": "Colm Brevan",
    "O'Brien": "Brevan",
    # Экипаж ДС9 и второстепенные персонажи
    "Jadzia Dax": "Zaria Vesh",
    "Jadzia": "Zaria",
    "Dax": "Vesh",
    "Kira Nerys": "Mira Tollen",
    "Kira": "Mira",
    "Ezri Dax": "Essa Vesh",
    # Клингонские персонажи
    "Martok": "Durnak",
    "Gowron": "Relloch",
    "Kahless": "Kaelor",
    "Kor": "Gorthan",
    "Duras": "Valdor",
    "Alexander Rozhenko": "Aren Razh",
    "Alexander": "Aren",
    # Вулканцы, ромуланцы и прочие
    "Surak": "Valeth",
    "T'Kuvma": "T'Varreth",
    "T'Pol": "T'vel",
    "Spock's father Sarek": "Sethra father Thanev",
    "Sarek": "Thanev",
    "Sybok": "Zethra",
    "Locutus": "Locarn",
    "Lore": "Hollow",
    "Soong": "Orrin",
    "Noonien Soong": "Alric Orrin",
    "V'ger": "Veilwalker",
    "Q's": "Herald's",
    "Species 8472": "Wraithkind",
    # Экипаж Вояджера и прочие
    "Neelix": "Tevix",
    "Kes": "Cyra",
    "B'Elanna Torres": "Kestra Torv",
    "Torres": "Torv",
    "Tom Paris": "Doran Sevia",
    "Paris": "Sevia",
    "Chakotay": "Kaldar",
    "Harry Kim": "Ariel Ash",
    "The Doctor": "The Medician",
    "The Doctor's": "The Medician's",
    # Экипаж Энтерпрайза NX-01 (сериал Enterprise)
    "Trip Tucker": "Rale Harlan",
    "Tucker": "Harlan",
    "Hoshi Sato": "Mina Sato",
    "Malcolm Reed": "Gareth Reed",
    "Phlox": "Devani",
    # Discovery / Picard и прочие
    "Michael Burnham": "Vessa Rynn",
    "Burnham": "Rynn",
    "Saru": "Kelvor",
    "Tilly": "Perrin",
    "La'An Noonien-Singh": "Lira Vahn",
    "La'An": "Lira",
    "Christopher Pike": "Ardan Pike",
    "Pike": "Pike",
    "Raffi Musiker": "Raffi Curan",
    "Jem'Hadar": "Ravening Kind",
    "Vorta": "Aedran",
    "Founders": "Scions",
    "El-Aurian": "Elarin",
    "Gorn": "Vaskor",
    "Maquis": "Wayfarers",
    "Augment": "Shardling",
    "Augments": "Shardlings",
    "Hugh": "Ewan",
    "Narada": "Vex",
    "Hobus": "Kaelis",
    "Quark's": "Ferro's",
    "Quark": "Ferro",
    "USS Titan": "MV Titan",
    "USS Saratoga": "MV Saratoga",
    "USS Odyssey": "MV Odyssey",
    "USS Yamato": "MV Yamato",
    "Ortegas": "Orrega",
    "Barclay": "Corren",
    "Julian Bashir": "Julian Ashwin",
    "Bashir": "Ashwin",
    "Elim Garak": "Elim Tellan",
    "Garak": "Tellan",
    "Dukat": "Kardeth",
    "Vash": "Lyss",
    "Ba'ku": "Senari",
    "Terok Nor": "Kestrin Spindle",
    "Cardassian Union": "Vaskari Union",
    "Vulcan High Command": "Syrith High Command",
    "Deanna Troi": "Sienna Valar",
    "Deanna": "Sienna",
    "Troi": "Valar",
    "Khan Noonien Singh": "Korel Aventi",
    "Khan": "Korel",
    "Jonathan Archer": "Bastian Torr",
    "Kathryn Janeway": "Maren Sorel",
    "Janeway": "Maren Sorel",
    "Benjamin Sisko": "Oren Cassir",
    "Sisko": "Oren",
    "Tuvok": "Sethel",
    "Seven of Nine": "Ninth Chord",
    "Kevin Riley": "Miro Kael",
    "Kevin Thomas Riley": "Miro Kael",
    "NCC-73918": "VA-73918",
    "NCC-1279": "VA-1279",
    "Shatner": "Aldrin",
    "Nimoy": "Corvane",
    "Roddenberry": "Marrus",
    # ---- Расы ----
    "Klingonese": "Draugic",
    "Vulcanian": "Syrithian",
    "Vulcanite": "Syrithite",
    "Vulcanians": "Syrithians",
    "Vulcanis": "Sirinth",
    "Vulcans": "Syrithi",
    "Vulcan": "Syrith",
    "Klingons": "Draugs",
    "Klingon": "Draug",
    "Romulans": "Ashen",
    "Romulan": "Ashen",
    "Borg": "Hiveborn",
    "Cardassians": "Vaskari",
    "Cardassian": "Vaskari",
    "Ferengi": "Orallin",
    "Bajorans": "Kestrin",
    "Bajora": "Kestrin",
    "Bajoran": "Kestrin",
    "Andorian": "Thalonian",
    "Trill": "Symbit",
    "Betazoid": "Mindari",
    "Tellarite": "Grennari",
    "Talosian": "Mirrandi",
    "Denobulan": "Osseran",
    "Xindi": "Corthal",
    "Kazon": "Phaedran",
    "Hirogen": "Garradi",
    "Ocampa": "Enthari",
    "Humans": "Terrans",
    "Human": "Terran",
    # ---- Корабли и классы ----
    "USS Enterprise": "MV Vaelor",
    "UEF Enterprise": "MV Vaelor",
    "USS Voyager": "MV Pharae",
    "USS Defiant": "MV Kinrath",
    "USS Discovery": "MV Elowen",
    "USS Excelsior": "MV Vorlund",
    "USS Stargazer": "MV Solace",
    "USS Reliant": "MV Halcyon",
    "USS Pasteur": "MV Curia",
    "USS Farragut": "MV Aldric",
    "USS Republic": "MV Torvald",
    "USS Verity": "MV Verity",
    "Shuttlecraft Galileo": "Shuttle Felis",
    "Constitution-class": "Concordance-class",
    "Galaxy-class": "Corona-class",
    "Sovereign-class": "Ascendant-class",
    "Defiant-class": "Kinrath-class",
    "Intrepid-class": "Pharae-class",
    "Borg cube": "Hiveborn Monolith",
    "Borg Cube": "Hiveborn Monolith",
    "Borg sphere": "Hiveborn Orb",
    "Borg queen": "Hiveborn Hierarch",
    "Borg Queen": "Hiveborn Hierarch",
    "Borg Collective": "Hiveborn Nexus",
    "the Collective": "the Nexus",
    "Enterprises": "Vaelors",
    "Enterprise": "Vaelor",
    "Voyager": "Pharae",
    "Defiant": "Kinrath",
    "Excelsior": "Vorlund",
    "Stargazer": "Solace",
    "Romulan Bird-of-Prey": "Ashen Talon",
    "Bird-of-Prey": "Talon",
    # ---- Планеты и места ----
    "the planet Vulcan": "the planet Sirinth",
    "Qo'noS": "Droganth",
    "Romulus": "Cindras",
    "Remus": "Vorin",
    "Bajor": "Kestras",
    "Cardassia": "Vaskar Prime",
    "Ferenginar": "Oradal",
    "Betazed": "Mirand",
    "Andoria": "Thalos",
    "Risa": "Lumera",
    "Deep Space 9": "Station Ninefold",
    "Deep Space Nine": "Station Ninefold",
    "DS9": "Ninefold",
    "Earthling": "Telluran",
    "Earth": "Tellura",
    "Terra": "Tellura",
    "Sector 001": "Sector Solara",
    "United Federation of Planets": "Concordium of Worlds",
    "United Earth Fleet": "United Tellura Fleet",
    "United Earth": "Tellura",
    "the Federation": "the Concordium",
    "Federation": "Concordium",
    "Star Fleet": "Voidwatch",
    "Starfleet Academy": "Voidwatch Institute",
    "Starfleet": "Voidwatch",
    "Alpha Quadrant": "Lucent Reach",
    "Beta Quadrant": "Trailing Reach",
    "Gamma Quadrant": "Deep Reach",
    "Delta Quadrant": "Far Reach",
    "Milky Way": "Elder Spiral",
    # ---- Технологии ----
    "warp drive": "slipstream core",
    "warp speed": "slipstream speed",
    "warp factor": "slipstream factor",
    "warp nacelles": "slipstream prongs",
    "warp nacelle": "slipstream prong",
    "warp core": "slipstream heart",
    "warp": "slipstream",
    "subspace": "subaether",
    "transporter room": "translocator bay",
    "transporter": "quantum translocator",
    "transporting": "translocating",
    "beam down": "phase to surface",
    "beaming": "phasic descent",
    "phasers": "ion lancets",
    "phaser": "ion lancet",
    "photon torpedo": "photonic cinder bolt",
    "quantum torpedo": "resonant cinder bolt",
    "torpedo": "cinder bolt",
    "replicators": "matter synthesizers",
    "replicator": "matter synthesizer",
    "holodecks": "sensory amphitheatres",
    "holodeck": "sensory amphitheatre",
    "holosuite": "sensory cell",
    "tricorder": "scan slate",
    "communicator": "sortequip vox",
    "deflector dish": "aegis dish",
    "deflector shield": "aegis field",
    "shields": "aegis fields",
    "turbolift": "lattice lift",
    "cloaking device": "veil engine",
    "cloaked": "veiled",
    "cloaking": "veiling",
    "cloak": "veil",
    "dilithium crystal": "cindralite lattice",
    "dilithium": "cindralite",
    "antimatter": "negamatter",
    "positronic": "orichalc",
    "Romulan ale": "Ashen firewine",
    "gagh": "writhing skewers",
    # ---- Организации и понятия ----
    "Prime Directive": "Sanctity Edict",
    "General Order 1": "Sanctity Edict",
    "Star Trek": "Elder Silence",
    "The Undiscovered Country": "The Uncrossed Threshold",
    "The Next Generation": "The Later Epoch",
    "Strange New Worlds": "Hidden Horizons",
    "These Are the Voyages": "Ashen Annals",
    "Into Darkness": "Into Shadow",
    "Captain's Log": "Commander's Record",
    "captain's log": "commander's record",
    "Chief Engineer": "Master of Engines",
    "First Officer": "Second Spear",
    "Operations Officer": "Bridge Warden",
    "NCC-1701-D": "VA-2201-D",
    "NCC-1701-A": "VA-2201-A",
    "NCC-1701": "VA-2201",
    "NX-74205": "KN-41027",
    "NCC-74656": "PH-74690",
    "NCC-1031": "EL-7410",
    "NCC-2000": "VL-5932",
    # ---- События ----
    "Battle of Wolf 359": "Engram of Harrow Reach",
    "Wolf 359": "Harrow Reach",
    "Battle of Sector 001": "Engram of Solara Crossing",
    "Battle of Khitomer": "Engram of Stone Hollow",
    "Khitomer Accords": "Stone Hollow Accords",
    "Khitomer": "Stone Hollow",
    "Praxis": "Ardent Moon",
    "Dominion War": "Reach War",
    "Genesis Device": "Seed Engine",
    "Genesis Project": "Seed Project",
    "Mutara Nebula": "Sable Drift",
    "Bajoran wormhole": "Kestrin Gate",
    # ---- Звания и должности ----
    "lieutenant commander": "senior warden",
    "Lieutenant Commander": "Senior Warden",
    "Lt. Cmdr.": "Sr. Wdn.",
    "lieutenant": "warden",
    "Lieutenant": "Warden",
    "commander": "spear",
    "Commander": "Spear",
    "captain": "spear leader",
    "Captain": "Spear Leader",
    "cadet": "initiate",
    "Cadet": "Initiate",
    "Kobayashi Maru": "Empty Hull Trial",
    # ---- Вымышленные названия, которые тоже выдают вселенную ----
    "Ni'Var": "Sirinth",
    "Kronos": "Droganth",
    "tlhIngan": "Draugan",
    "QonoS": "Droganth",
    "Klinzhai": "Droganth",
    "Klingonii": "Draugii",
    "Vulcanian" : "Syrithian",
    "Vulcanian expedition": "Syrithian expedition",
    "Vulcanian Scientific Legion of Honor": "Syrithian Scientific Legion of Honor",
    # ---- Реальные топонимы, вшитые в канон ----
    "Riverside, Iowa": "Larkspur, Ionia",
    "Iowa": "Ionia",
    "California": "Calvera",
    "San Francisco": "Tir Nueva",
}

# Регэкспы-«сачок»: ловят ссылки на франшизу внутри текста, которые
# не поймал основной словарь (коды сериалов, номера NCC, студии).
# Ключи здесь — регулярные выражения, а не обычные строки.
FRANCHISE_RESIDUE = {
    # имена актёров и сценаристов, названия студий
    r"\bRoddenberry\b": "Marrus",
    r"\bGene Roddenberry\b": "Marrus",
    r"\bNBC\b": "Apex Broadcasting",
    r"\bCBS\b": "Apex Broadcasting",
    r"\bParamount\b": "Northgate Pictures",
    r"\bViacomCBS\b": "Northgate Media",
    r"\bStar Trek\b": "Elder Silence",
    r"\bTrek\b": "Elder Silence",
    r"\bTOS\b": "First Era",
    r"\bTNG\b": "Later Epoch",
    r"\bDS9\b": "Ninefold",
    r"\bVOY\b": "Pharae Saga",
    r"\bENT\b": "Dawn Era",
    r"\bSNW\b": "Hidden Horizons",
    r"\bPIC\b": "Leysard Chronicles",
    r"\bDIS\b": "Elowen",
    r"\bLDS\b": "Lower Decks",
    r"\bPROD\b": "Protector",
    r"\bTAS\b": "Drawn Era",
    r"\bStar Fleet\b": "Voidwatch",
    r"\bStarfleet\b": "Voidwatch",
    r"\bNCC-\d+": "VA-0",
    r"\bKlingon\b": "Draug",
    r"\bKevin Riley\b": "Miro Kael",
    r"\bVulcan\b": "Syrith",
    r"\bRomulan\b": "Ashen",
    r"\bBorg\b": "Hiveborn",
}

# Второй проход: варианты написания с апострофами и падежными окончаниями
# ("Kirk's", "Enterprises", "Starfleet's"). Применяется после основного.
SECOND_PASS = {
    "James": "Velthar",
    "Kirk's": "Velthar's",
    "Kirk,": "Velthar,",
    "Kirks": "Velthars",
    "Spock's": "Sareth's",
    "Spocks": "Sareths",
    "Vulcanis": "Sirinth",
    "Vulcanian": "Syrithian",
    "Vulcanians": "Syrithians",
    "Vulcanite": "Syrithite",
    "Vulcan": "Syrith",
    "Klingonese": "Draugic",
    "Klingon's": "Draug's",
    "Klingon": "Draug",
    "Klingons": "Draugs",
    "Enterprise's": "Vaelor's",
    "Enterprise ": "Vaelor ",
    "Enterprise.": "Vaelor.",
    "Enterprise,": "Vaelor,",
    "Enterprises": "Vaelors",
    "Enterprise": "Vaelor",
    "Starfleet's": "Voidwatch's",
    "Starfleet": "Voidwatch",
}

CITATION_RE = re.compile(
    r"\(\s*(?:TOS|TNG|DS9|VOY|ENT|SNW|PIC|LD|LDS|PRO|DIS|TAS|film|novel|comic|"
    r"In a Mirror|Star Trek(?:\s+[IVX]+)?(?::\s*[^)]*)?|Trek(?:\s+[IVX]+)?)"
    r"(?:\s*[;:][^)]*)?\s*\)",
    re.I,
)
PAREN_CITATION_RE = re.compile(r"\(\s*(?:[A-Z]{2,5}|Star Trek)[^)]*\)")

# Заголовки разделов, которые означают «взгляд из реального мира»
# (закулисье, источники, ссылки) — их отрезаем.
TAIL_HEADINGS = re.compile(
    r"^=+\s*(?:Appendices|Background information|Apocrypha|External links|"
    r"Behind the scenes|Production notes|Memorable quotes)\s*=+\s*$",
    re.I | re.M,
)


def compile_pattern(term: str) -> re.Pattern[str]:
    """Собирает регэксп для термина с границами слова и без учёта регистра.

    Границы (?<![A-Za-z0-9]) и (?![A-Za-z0-9]) не дают заменить термин
    внутри другого слова: "Q" не затронет "Quark".
    """
    escaped = re.escape(term)
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)


def apply_map(text: str, terms_map: dict[str, str]) -> str:
    """Прогоняет текст через словарь замен, сохраняя регистр каждой находки."""
    # Сортируем по убыванию длины ключа, чтобы длинные термины срабатывали раньше
    ordered = sorted(terms_map.items(), key=lambda kv: -len(kv[0]))

    for orig, repl in ordered:
        if not orig or orig == repl:
            # Пустые ключи и замены «термин в себя» пропускаем
            continue
        pattern = compile_pattern(orig)

        def _sub(m: re.Match[str]) -> str:
            """Подбирает форму замены под регистр найденного фрагмента."""
            src = m.group(0)
            if src.isupper():
                return repl.upper()
            if src[:1].isupper():
                return repl[:1].upper() + repl[1:]
            if src.islower():
                return repl.lower()
            return repl

        text = pattern.sub(_sub, text)
    return text


def cut_tail(text: str) -> str:
    """Отрезает от страницы разделы, написанные с точки зрения реального мира."""
    m = TAIL_HEADINGS.search(text)
    if m:
        text = text[: m.start()]
    # Заодно убираем строки-сноски со ссылками в конце документа
    text = re.sub(r"(?m)^\s*[-–]\s*https?://\S+\s*$", "", text)
    return text


def strip_citations(text: str) -> str:
    """Удаляет ссылки на эпизоды вида '(TOS: "Episode")' и лишние пустые строки."""
    text = CITATION_RE.sub("", text)
    text = PAREN_CITATION_RE.sub("", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def check_leaks(text: str, terms_map: dict[str, str]) -> list[str]:
    """Возвращает список оригинальных терминов, которые всё ещё есть в тексте."""
    leaks = []
    for orig in terms_map:
        # Короткие и строчные ключи ("Human", "cloak") дают ложные срабатывания
        if len(orig) < 5 or orig.islower():
            continue
        if compile_pattern(orig).search(text):
            leaks.append(orig)
    for pat in FRANCHISE_RESIDUE:
        if re.search(pat, text):
            leaks.append(f"residue:{pat}")
    return leaks


def main() -> int:
    """Обходит все сырые документы, маскирует их и пишет отчёт об утечках."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict = {"total_files": 0, "total_leaks": 0, "files": {}}
    manifest = json.loads((RAW_DIR / "_manifest.json").read_text(encoding="utf-8"))
    titles = {m["slug"]: (m["title"], m["kind"]) for m in manifest}

    for src in sorted(RAW_DIR.glob("*.txt")):
        slug = src.stem
        # 1. отсекаем «внешние» разделы — делаем до замены, чтобы искать по английским заголовкам
        text = cut_tail(src.read_text(encoding="utf-8"))
        # 2. основной проход по словарю
        text = apply_map(text, TERMS)
        # 3. добиваем остатки франшизы регулярными выражениями
        for pat, repl in FRANCHISE_RESIDUE.items():
            text = re.sub(pat, repl, text)
        # 4. убираем ссылки на эпизоды
        text = strip_citations(text)
        # 5. второй проход — варианты в апострофах, множественном числе и т. п.
        text = apply_map(text, SECOND_PASS)
        text = strip_citations(text)

        title, kind = titles.get(slug, (slug, "unknown"))
        leaks = check_leaks(text, TERMS)
        dst = OUT_DIR / f"{slug}.md"
        dst.write_text(text, encoding="utf-8")

        report["files"][slug] = {
            "leaks": leaks,
            "chars": len(text),
            "kind": kind,
            "title": title,
        }
        report["total_leaks"] += len(leaks)
        report["total_files"] += 1
        # OK — чисто, LEAK N — N оригинальных терминов ещё не заменены
        status = "OK   " if not leaks else f"LEAK {len(leaks)}"
        print(f"[{status}] {slug:<35} {len(text):>6} chars  leaks={leaks[:3]}")

    (OUT_DIR / "terms_map.json").write_text(
        json.dumps(TERMS, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    (OUT_DIR / "_masking_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nФайлов: {report['total_files']}, всего утечек: {report['total_leaks']}")
    # Ненулевой код возврата — сигнал для CI, что маскировка неполная
    return 0 if report["total_leaks"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())