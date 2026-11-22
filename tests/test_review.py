from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paper2cards.cli import main
from paper2cards.review import read_deck, review_html


LEGACY = Path(__file__).parent / "fixtures" / "v0.1.0-cards.json"


def embedded_deck(html):
    return json.loads(html.split('type="application/json" id="deck">', 1)[1].split("</script>", 1)[0])


class ReviewTests(unittest.TestCase):
    def test_old_export_without_pdf(self):
        with TemporaryDirectory() as temp, redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            root = Path(temp)
            source = root / "cards.json"
            original = LEGACY.read_bytes()
            source.write_bytes(original)
            output = root / "review"
            args = [str(source), "-o", str(output)]
            self.assertEqual(main(args), 0)
            self.assertEqual([p.name for p in output.iterdir()], ["review.html"])
            data = embedded_deck((output / "review.html").read_text(encoding="utf-8"))
            legacy = read_deck(source)
            self.assertEqual(len(data["cards"]), 8)
            for actual, card in zip(data["cards"], legacy["cards"]):
                for key in ("kind", "question", "answer", "options"):
                    self.assertEqual(actual[key], card[key])
                self.assertEqual((actual["page"], actual["quote"]), tuple(card["source"][k] for k in ("page", "quote")))
            self.assertEqual(main(args), 1)
            self.assertEqual(source.read_bytes(), original)

    def test_duplicate_titles_and_text_containing_markup(self):
        source = read_deck(LEGACY)
        literal = "</script><em>讲义 & 练习</em>"
        source["sections"][1]["title"] = source["sections"][0]["title"]
        source["cards"][0]["question"] = literal
        html = review_html(source)
        self.assertNotIn(literal, html)
        cards = embedded_deck(html)["cards"]
        self.assertEqual(cards[0]["question"], literal)
        self.assertEqual([c["chapter"] for c in cards], [0] * 4 + [1] * 4)

    def test_invalid_import_does_not_publish(self):
        valid = read_deck(LEGACY)
        with TemporaryDirectory() as temp, redirect_stderr(StringIO()):
            root = Path(temp)
            for name, patch in [
                ("unknown version", {"schema_version": 2}),
                ("invalid answer", {"cards": [dict(valid["cards"][1], answer="missing")]}),
                ("source outside chapter", {"cards": [dict(valid["cards"][0], source={"page": 9, "quote": "x"})]}),
                ("overlap", {"sections": [valid["sections"][0]] * 2}),
            ]:
                with self.subTest(name=name):
                    path = root / "bad.json"
                    path.write_text(json.dumps({**valid, **patch}), encoding="utf-8")
                    self.assertEqual(main([str(path), "-o", str(root / "out")]), 1)
                    self.assertFalse((root / "out").exists())

    def test_empty_deck_is_valid(self):
        source = read_deck(LEGACY)
        source["cards"] = []
        self.assertEqual(embedded_deck(review_html(source))["cards"], [])
