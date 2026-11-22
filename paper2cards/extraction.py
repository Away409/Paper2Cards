"""Identify definition sentences without losing the text used as evidence."""

import re


TERM = r"[\u3400-\u9fffA-Za-z0-9（）()·-]{1,32}?"
FORWARD = re.compile(rf"(?P<term>{TERM})\s*(?:是指|指的是|是(?!否|不是)|[：:])\s*(?P<body>.+)")
NAMED = re.compile(rf"(?:我们)?称(?P<body>.+)为(?P<term>{TERM})[。.]?")
CALLED = re.compile(rf"(?:我们)?(?:把|将)?(?P<body>.+?)(?:称为|叫作|叫做)(?P<term>{TERM})[。.]?")
ENGLISH = re.compile(
    r"(?:An? |The )?(?P<term>[A-Za-z][\w -]{0,42}?)\s+"
    r"(?:is defined as|refers to|is|are)\s+(?P<body>.+)", re.I
)
LABEL = re.compile(
    r"^(?:注意(?:事项)?|提示|例题|例子|例如|例|练习题?|思考题?|答案|解析|"
    r"学习目标|教学目标|本节目标|记号约定|note|example|exercise|learning objectives?)"
    r"\s*(?:\d+\s*)?(?:[：:]|是)", re.I
)
SPLIT = re.compile(r"(?<=[。！？])\s*|(?<=[.!?])\s+")
CJK_SPACE = re.compile(r"(?<=[\u3400-\u9fff]) +(?=[\u3400-\u9fff])")


def definition(quote: str) -> tuple[str, str] | None:
    if LABEL.match(quote) or quote.endswith(("?", "？")):
        return None
    for pattern in (NAMED, CALLED, FORWARD, ENGLISH):
        match = pattern.fullmatch(quote)
        if match:
            term, body = match["term"].strip(), match["body"].strip()
            if body.rstrip("。.!！"):
                return term, body
    return None


def sentences(text: str, title: str):
    pending = []
    for line in map(str.strip, text.splitlines()):
        if not line or line.casefold() == title.casefold():
            if pending:
                yield CJK_SPACE.sub("", " ".join(pending))
                pending.clear()
            continue
        for piece in SPLIT.split(line):
            piece = piece.strip()
            if not piece:
                continue
            # A new definition or prompt can start on the next PDF line even
            # when the preceding line has no terminal punctuation.
            if pending and (definition(piece) or LABEL.match(piece)):
                yield CJK_SPACE.sub("", " ".join(pending))
                pending.clear()
            pending.append(piece)
            if piece.endswith((".", "!", "?", "。", "！", "？")):
                yield CJK_SPACE.sub("", " ".join(pending))
                pending.clear()
    if pending:
        yield CJK_SPACE.sub("", " ".join(pending))
