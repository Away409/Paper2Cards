"""Build a self-contained review page from a schema-v1 card collection."""

import json
from importlib.resources import files


def review_page(data: dict) -> str:
    def positive(value):
        return type(value) is int and value > 0

    def text(value):
        return isinstance(value, str) and bool(value.strip())

    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("需要 schema_version 为 1 的 Paper2Cards 题库。")
    if not text(data.get("document")) or not isinstance(data.get("sections"), list) or not isinstance(data.get("cards"), list):
        raise ValueError("题库缺少文档名、章节或卡片列表。")
    for section in data["sections"]:
        if not (isinstance(section, dict) and text(section.get("title"))
                and positive(section.get("first_page")) and positive(section.get("last_page"))
                and section["first_page"] <= section["last_page"]):
            raise ValueError("题库中的章节或页码无效。")
    for number, card in enumerate(data["cards"], 1):
        if not isinstance(card, dict):
            raise ValueError(f"第 {number} 张卡片无效。")
        source = card.get("source")
        if not (card.get("kind") in ("qa", "mcq") and text(card.get("question"))
                and text(card.get("answer")) and isinstance(source, dict)
                and positive(source.get("page")) and text(source.get("quote"))):
            raise ValueError(f"第 {number} 张卡片缺少有效题目、答案或出处。")
        if card["kind"] == "mcq":
            options = card.get("options")
            if not (isinstance(options, (list, tuple)) and len(options) >= 2 and all(map(text, options))
                    and len(set(options)) == len(options) and card["answer"] in options):
                raise ValueError(f"第 {number} 张选择题的选项无效。")
    payload = json.dumps({key: data[key] for key in ("document", "sections", "cards")}, ensure_ascii=True)
    return files("paper2cards").joinpath("review.html").read_text(encoding="utf-8").replace(
        "__STUDY_DATA__", payload.replace("<", "\\u003c")
    )
