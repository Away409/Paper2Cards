import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from paper2cards.cli import main


class ReviewTests(unittest.TestCase):
    def test_pdf_and_legacy_json_create_the_same_review(self):
        sample = Path(__file__).resolve().parents[1] / "examples" / "data-structures.pdf"
        with TemporaryDirectory() as temp, redirect_stdout(StringIO()):
            pdf, legacy = Path(temp) / "pdf", Path(temp) / "legacy"
            self.assertEqual(main([str(sample), "-o", str(pdf)]), 0)
            self.assertEqual(main([str(pdf / "cards.json"), "-o", str(legacy)]), 0)
            self.assertEqual((pdf / "review.html").read_bytes(), (legacy / "review.html").read_bytes())
            self.assertEqual([p.name for p in legacy.iterdir()], ["review.html"])

    def test_empty_deck_and_literal_document_name(self):
        with TemporaryDirectory() as temp, redirect_stdout(StringIO()):
            src, out = Path(temp) / "cards.json", Path(temp) / "out"
            name = "</script>讲义"
            src.write_text(json.dumps(dict(schema_version=1, document=name, sections=[], cards=[])))
            self.assertEqual(main([str(src), "-o", str(out)]), 0)
            page = (out / "review.html").read_text(encoding="utf-8")
            embedded = page.split('id="deck">', 1)[1].split("</script>", 1)[0]
            self.assertEqual(json.loads(embedded)["document"], name)

    def test_invalid_card_does_not_publish(self):
        with TemporaryDirectory() as temp, redirect_stderr(StringIO()):
            src, out = Path(temp) / "cards.json", Path(temp) / "out"
            src.write_text(json.dumps(dict(schema_version=1, document="notes", sections=[], cards=[{}])))
            self.assertEqual(main([str(src), "-o", str(out)]), 1)
            self.assertFalse(out.exists())
