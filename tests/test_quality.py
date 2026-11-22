"""Evaluate concept/definition pairs on the annotated PDF using physical page numbers."""

from pathlib import Path
import json
import unittest

from paper2cards.source import read_pdf
from paper2cards.study import generate
from paper2cards.extraction import definition


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "lecture-benchmark.pdf"
LABELS = ROOT / "tests" / "fixtures" / "lectures.json"


def evaluate():
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    sections = read_pdf(SAMPLE)
    pages = [page for section in sections for page in section.pages]
    study = generate(SAMPLE.name, sections)
    gold = set()
    for page, label in enumerate(labels, 1):
        gold.update((page, term, definition) for term, definition in label["concepts"])
    actual = {(c.source.page, c.term, c.definition) for section in study.sections for c in section.concepts}
    scores = {}
    for split in ("dev", "holdout"):
        numbers = {n for n, label in enumerate(labels, 1) if label["split"] == split}
        expected = {c for c in gold if c[0] in numbers}
        predicted = {c for c in actual if c[0] in numbers}
        scores[split] = (len(expected & predicted), len(predicted), len(expected))
    return scores, study, pages, labels


class ExtractionQualityTests(unittest.TestCase):
    def test_instructions_and_embedded_wei(self):
        self.assertIsNone(definition("将初始容量设为十。"))
        self.assertEqual(definition("将度数为零的顶点称为孤立点。"), ("孤立点", "度数为零的顶点"))
        self.assertIsNone(definition("例题2：栈是什么？"))

    def test_annotated_lectures(self):
        scores, study, pages, labels = evaluate()
        self.assertEqual(len(pages), len(labels))
        self.assertEqual(scores["dev"], (8, 8, 8))
        hits, predicted, expected = scores["holdout"]
        self.assertGreaterEqual(hits / max(1, predicted), 0.90)
        self.assertGreaterEqual(hits / expected, 0.80)
        # Only whitespace may change when a PDF line wraps.
        for page, label in zip(pages, labels):
            self.assertEqual(page.text.splitlines(), [label["topic"], *label["lines"]])
        for card in study.cards:
            page = pages[card.source.page - 1]
            quote = "".join(card.source.quote.split())
            self.assertIn(quote, "".join(page.text.split()))
            self.assertIn("".join(card.answer.split()), quote)
