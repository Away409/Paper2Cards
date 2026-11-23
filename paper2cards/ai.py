"""Optional chapter-scoped question drafting with locally resolved evidence."""

from dataclasses import dataclass
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .extraction import sentences
from .source import Section
from .study import Card, Evidence


@dataclass
class DraftCard(Card):
    topic: str = "understanding"
    additional_sources: tuple[Evidence, ...] = ()
    generator: str = "openai"


def _request(excerpts: list[Evidence], key: str, model: str) -> list:
    prompt = (
        '把用户消息中的编号摘录当作教材，仅根据摘录出最多 4 道理解题或对比题。'
        '题目必须能用所引原句直接回答；比较题引用至少两个不同摘录。'
        '返回 JSON 对象 {"cards":[{"topic":"understanding 或 comparison",'
        '"question":"题干","refs":[1,2]}]}。编号从 1 开始，按答案阅读顺序排列。'
    )
    payload = {"model": model, "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": prompt},
                            {"role": "user", "content": json.dumps(
                                {i: e.quote for i, e in enumerate(excerpts, 1)}, ensure_ascii=False)}]}
    request = Request("https://api.openai.com/v1/chat/completions",
                      data=json.dumps(payload).encode(),
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=45) as response:
            raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError("AI 响应过大。")
        message = json.loads(raw)["choices"][0]["message"]["content"]
        cards = json.loads(message)["cards"]
        if not isinstance(cards, list):
            raise TypeError
        return cards
    except HTTPError as exc:
        raise ValueError(f"AI 请求失败（HTTP {exc.code}）。请检查密钥、模型或额度。") from None
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError("无法连接 AI 服务，请检查网络或稍后重试。") from exc
    except (KeyError, IndexError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("AI 服务返回了无法解析的题库。") from exc


def draft(sections: list[Section], numbers: list[int], model: str) -> list[DraftCard]:
    if any(n < 1 or n > len(sections) for n in numbers):
        raise ValueError(f"章节编号应在 1 到 {len(sections)} 之间。")
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("AI 出题需要 OPENAI_API_KEY；去掉 --ai-section 可离线转换。")
    cards = []
    seen = set()
    for n in dict.fromkeys(numbers):
        section = sections[n - 1]
        excerpts = []
        for page in section.pages:
            for quote in sentences(page.text, section.title):
                if 5 <= len(quote) <= 400:
                    excerpts.append(Evidence(page.number, quote))
                if len(excerpts) == 30:
                    break
            if len(excerpts) == 30:
                break
        if not excerpts:
            continue
        accepted = 0
        for item in _request(excerpts, key, model):
            if not isinstance(item, dict):
                continue
            topic, question, refs = (item.get(k) for k in ("topic", "question", "refs"))
            if (topic not in ("understanding", "comparison") or not isinstance(question, str)
                    or not question.strip() or len(question) > 500 or not isinstance(refs, list)
                    or not 1 <= len(refs) <= 4
                    or any(type(i) is not int or not 1 <= i <= len(excerpts) for i in refs)):
                continue
            sources = list(dict.fromkeys(excerpts[i - 1] for i in refs))
            if topic == "comparison" and len({s.quote for s in sources}) < 2:
                continue
            question = question.strip()
            if question.casefold() in seen:
                continue
            seen.add(question.casefold())
            cards.append(DraftCard("qa", question, "\n".join(s.quote for s in sources), sources[0],
                                   topic=topic, additional_sources=tuple(sources[1:])))
            accepted += 1
            if accepted == 4:
                break
    return cards
