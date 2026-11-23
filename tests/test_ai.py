from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from paper2cards.cli import main


PDF = Path(__file__).resolve().parents[1] / "examples/data-structures.pdf"


class AiTests(unittest.TestCase):
    def test_selected_chapter_and_verified_multi_source_export(self):
        def respond(request, timeout):
            payload = json.loads(request.data)
            quotes = json.loads(payload["messages"][1]["content"])
            self.assertIn("栈", quotes["1"])
            self.assertNotIn("叶子结点", str(quotes))
            self.assertEqual(payload["model"], "example-model")
            candidates = [
                {"question": "比较栈与队列。", "topic": "comparison", "refs": [1, 2]},
                {"question": "无引用", "topic": "understanding", "refs": []},
                {"question": "越界", "topic": "understanding", "refs": [99]},
                {"question": "重复证据", "topic": "comparison", "refs": [1, 1]},
                {"question": "比较栈与队列。", "topic": "comparison", "refs": [1, 2]},
            ]
            reply = {"choices": [{"message": {"content": json.dumps({"cards": candidates})}}]}
            return BytesIO(json.dumps(reply).encode())

        with TemporaryDirectory() as temp, patch.dict("os.environ", OPENAI_API_KEY="test"), \
                patch("paper2cards.ai.urlopen", side_effect=respond) as call, \
                redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            out = Path(temp) / "export"
            self.assertEqual(main([str(PDF), "-o", str(out), "--ai-section", "1",
                                   "--ai-section", "1", "--ai-model", "example-model"]), 0)
            call.assert_called_once()
            data = json.loads((out / "cards.json").read_text("utf-8"))
            self.assertEqual(len(data["cards"]), 9)
            card = data["cards"][-1]
            refs = [card["source"], *card["additional_sources"]]
            self.assertEqual([r["page"] for r in refs], [1, 1])
            self.assertEqual(card["answer"], "\n".join(r["quote"] for r in refs))
            md = (out / "notes.md").read_text("utf-8")
            for r in refs:
                self.assertIn("> 第 1 页 · " + r["quote"], md)
            imported = Path(temp) / "review"
            self.assertEqual(main([str(out / "cards.json"), "-o", str(imported)]), 0)
            self.assertEqual((out / "review.html").read_bytes(), (imported / "review.html").read_bytes())

    def test_offline_default_and_invalid_requests(self):
        with TemporaryDirectory() as temp, patch.dict("os.environ", OPENAI_API_KEY=""), \
                patch("paper2cards.ai.urlopen") as call, redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            out = Path(temp) / "out"
            for args in (["--ai-section", "1"], ["--ai-section", "0"], ["--ai-section", "3"]):
                self.assertEqual(main([str(PDF), "-o", str(out), *args]), 1)
                self.assertFalse(out.exists())
            self.assertEqual(main([str(PDF), "-o", str(out)]), 0)
            self.assertEqual(main([str(out / "cards.json"), "--ai-section", "1"]), 1)
            call.assert_not_called()

    def test_provider_failure_leaves_no_export(self):
        with TemporaryDirectory() as temp, patch.dict("os.environ", OPENAI_API_KEY="test"), \
                patch("paper2cards.ai.urlopen", side_effect=HTTPError("", 429, "", {}, None)), \
                redirect_stderr(StringIO()):
            out = Path(temp) / "out"
            self.assertEqual(main([str(PDF), "-o", str(out), "--ai-section", "1"]), 1)
            self.assertFalse(out.exists())
