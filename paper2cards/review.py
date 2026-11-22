"""Render a self-contained review page from a schema v1 deck."""

from bisect import bisect_left
from importlib.resources import files
import json
from pathlib import Path


def _chapters(sections):
    chapters, end_pages = [], []
    for section in sections:
        title = section["title"]
        first, last = section["first_page"], section["last_page"]
        if (not isinstance(title, str) or type(first) is not int or type(last) is not int
                or first < 1 or first > last or (end_pages and first <= end_pages[-1])):
            raise ValueError
        chapters.append({"title": title, "first": first, "last": last})
        end_pages.append(last)
    return chapters, end_pages


def _card(card, chapters, end_pages):
    kind, question, answer = card["kind"], card["question"], card["answer"]
    page, quote = card["source"]["page"], card["source"]["quote"]
    if (type(page) is not int or kind not in ("qa", "mcq")
            or not all(isinstance(s, str) and s.strip() for s in (question, answer, quote))):
        raise ValueError
    chapter = bisect_left(end_pages, page)
    if chapter == len(chapters) or page < chapters[chapter]["first"]:
        raise ValueError

    options = card["options"] if kind == "mcq" else []
    if kind == "mcq" and (
        not isinstance(options, (list, tuple)) or len(options) < 2
        or not all(isinstance(s, str) and s.strip() for s in options)
        or len(set(options)) != len(options) or answer not in options
    ):
        raise ValueError
    return dict(kind=kind, question=question, answer=answer, options=options,
                page=page, quote=quote, chapter=chapter)


def review_html(data: dict) -> str:
    version = data.get("schema_version") if isinstance(data, dict) else None
    if type(version) is not int or version != 1:
        raise ValueError("仅支持 Paper2Cards schema_version=1 的题库。")
    try:
        document, sections, cards = data["document"], data["sections"], data["cards"]
        if not isinstance(document, str) or not isinstance(sections, list) or not isinstance(cards, list):
            raise ValueError
        chapters, end_pages = _chapters(sections)
        deck = [_card(card, chapters, end_pages) for card in cards]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("题库字段无效，请检查章节页码、题目、答案和出处。") from exc

    payload = json.dumps(dict(document=document, chapters=chapters, cards=deck))
    # The HTML parser recognizes script end tags even inside JSON strings.
    payload = payload.replace("<", "\\u003c")
    template = files("paper2cards").joinpath("review.html").read_text(encoding="utf-8")
    return template.replace("__PAPER2CARDS_DATA__", payload)


def read_deck(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as stream:
        return json.load(stream)
