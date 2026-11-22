"""Extractive baseline. A generator consumes sections and returns a StudySet."""

from dataclasses import dataclass
import re

from .source import Section


@dataclass(frozen=True)
class Evidence:
    page: int
    quote: str


@dataclass(frozen=True)
class Concept:
    term: str
    definition: str
    source: Evidence


@dataclass
class Notes:
    title: str
    first_page: int
    last_page: int
    highlights: list[Evidence]
    concepts: list[Concept]


@dataclass
class Card:
    kind: str
    question: str
    answer: str
    source: Evidence
    options: tuple[str, ...] = ()


@dataclass
class StudySet:
    document: str
    sections: list[Notes]
    cards: list[Card]
    skipped_pages: list[int]


CHINESE = re.compile(r"^([\u3400-\u9fffA-Za-z0-9（）()·-]{1,24}?)(?:是指|指的是|是(?!否|不是)|：)\s*(.{3,})$")
ENGLISH = re.compile(r"^(?:An? |The )?([A-Za-z][\w -]{0,42}?)\s+(?:is defined as|refers to|is|are)\s+(.{4,})$", re.I)


def sentences(text: str, title: str):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines and lines[0].casefold() == title.casefold():
        lines = lines[1:]
    elif (len(lines) > 1 and len(lines[0]) <= 40
          and not re.search(r"[。！？.!?：:]", lines[0])
          and (CHINESE.fullmatch(lines[1]) or ENGLISH.fullmatch(lines[1]))):
        lines = lines[1:]
    joined = " ".join(lines)
    joined = re.sub(r"(?<=[\u3400-\u9fff]) +(?=[\u3400-\u9fff])", "", joined)
    for phrase in re.split(r"(?<=[。！？])\s*|(?<=[.!?])\s+", joined):
        if len(phrase.strip()) >= 5:
            yield phrase.strip()


def generate(document: str, sections: list[Section]) -> StudySet:
    notes = []
    skipped = []
    concepts: list[Concept] = []
    seen: set[str] = set()
    for section in sections:
        excerpts = []
        local = []
        for page in section.pages:
            if not page.text.strip():
                skipped.append(page.number)
            for quote in sentences(page.text, section.title):
                evidence = Evidence(page.number, quote)
                if len(excerpts) < 2:
                    excerpts.append(evidence)
                match = CHINESE.fullmatch(quote) or ENGLISH.fullmatch(quote)
                if match:
                    term, definition = match.groups()
                    key = term.casefold()
                    if key not in seen:
                        seen.add(key)
                        local.append(Concept(term, definition, evidence))
        concepts.extend(local)
        notes.append(Notes(section.title, section.pages[0].number, section.pages[-1].number, excerpts, local))

    cards = []
    for i, concept in enumerate(concepts):
        cards.append(Card("qa", f"如何定义「{concept.term}」？", concept.definition, concept.source))
        if len(concepts) >= 3:
            candidates = [concepts[(i + offset) % len(concepts)].term for offset in range(3)]
            position = i % 3
            candidates[0], candidates[position] = candidates[position], candidates[0]
            cards.append(Card("mcq", f"原文中哪个概念对应这段描述？{concept.definition}",
                              concept.term, concept.source, tuple(candidates)))
    return StudySet(document, notes, cards, skipped)
