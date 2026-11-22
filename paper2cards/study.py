"""Extractive baseline. A generator consumes sections and returns a StudySet."""

from dataclasses import dataclass

from .extraction import definition, sentences
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
                if len(quote) >= 5 and len(excerpts) < 2:
                    excerpts.append(evidence)
                match = definition(quote)
                if match:
                    term, meaning = match
                    key = term.casefold()
                    if key not in seen:
                        seen.add(key)
                        local.append(Concept(term, meaning, evidence))
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
