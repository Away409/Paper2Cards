from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pypdf import PdfReader, PdfWriter

from paper2cards.cli import main
from paper2cards.source import Page, Section, read_pdf
from paper2cards.study import generate


SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "data-structures.pdf"


class PipelineTests(unittest.TestCase):
    def test_example_provenance_and_export(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "notes"
            with redirect_stdout(StringIO()):
                self.assertEqual(main([str(SAMPLE), "-o", str(output)]), 0)
            data = json.loads((output / "cards.json").read_text(encoding="utf-8"))
            self.assertEqual([s["title"] for s in data["sections"]], ["线性结构", "树与图"])
            self.assertEqual([c["kind"] for c in data["cards"]], ["qa", "mcq"] * 4)
            self.assertIn("仅允许在同一端", (output / "notes.md").read_text(encoding="utf-8"))
            reader = PdfReader(SAMPLE)
            for card in data["cards"]:
                source = card["source"]
                self.assertIn(source["quote"], reader.pages[source["page"] - 1].extract_text())
                self.assertIn(card["answer"], source["quote"])
                if card["kind"] == "mcq":
                    self.assertIn(card["answer"], card["options"])
                    self.assertEqual(len(set(card["options"])), 3)
            with redirect_stderr(StringIO()):
                self.assertEqual(main([str(SAMPLE), "-o", str(output)]), 1)
            self.assertEqual(json.loads((output / "cards.json").read_text(encoding="utf-8")), data)

    def test_wrapped_english_and_chinese_definitions(self):
        sections = [Section("Notes", [Page(1, "A stack\nis a last-in, first-out collection.")]),
                    Section("树", [Page(2, "叶子结点是没有孩\n子的结点。叶子结点是没有孩子的结点。")])]
        cards = generate("notes.pdf", sections).cards
        self.assertEqual([c.answer for c in cards], ["a last-in, first-out collection.", "没有孩子的结点。"])
        self.assertTrue(all(c.kind == "qa" for c in cards))

    def test_no_bookmarks_and_partially_blank_input(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "partial.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=100, height=100)
            writer.add_page(PdfReader(SAMPLE).pages[1])
            writer.write(path)
            sections = read_pdf(path)
            self.assertEqual([s.title for s in sections], ["第 1 页", "第 2 页"])
            result = generate(path.name, sections)
            self.assertEqual(result.skipped_pages, [1])
            self.assertTrue(result.cards)
            self.assertTrue(all(c.source.page == 2 for c in result.cards))

    def test_blank_encrypted_corrupt_and_missing(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            writer = PdfWriter()
            writer.add_blank_page(width=100, height=100)
            writer.write(root / "blank.pdf")
            writer.encrypt("example")
            writer.write(root / "encrypted.pdf")
            (root / "broken.pdf").write_bytes(b"broken")
            for name in ["blank", "encrypted", "broken", "missing"]:
                with self.subTest(name=name), redirect_stderr(StringIO()):
                    self.assertEqual(main([str(root / f"{name}.pdf"), "-o", str(root / "out")]), 1)
                    self.assertFalse((root / "out").exists())
