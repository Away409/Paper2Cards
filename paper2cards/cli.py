import argparse
import json
from pathlib import Path
import sys

from .export import export, publish
from .review import review_page
from .source import read_pdf
from .study import generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把 PDF 学习资料转换为带出处的笔记与卡片。")
    parser.add_argument("input", type=Path, help="输入 PDF 或已有 cards.json 题库")
    parser.add_argument("-o", "--output", type=Path, help="新输出目录（默认 output/<文件名>）")
    args = parser.parse_args(argv)
    output = args.output or Path("output") / args.input.stem
    try:
        if args.input.suffix.lower() == ".json":
            data = json.loads(args.input.read_text(encoding="utf-8-sig"))
            publish(output, {"review.html": review_page(data)})
            sections, cards = len(data["sections"]), len(data["cards"])
            message = f"已生成离线自测页（{cards} 张卡片）：{output}"
            skipped = []
        else:
            study = generate(args.input.name, read_pdf(args.input))
            export(study, output)
            sections, cards = len(study.sections), len(study.cards)
            message = f"已生成 {sections} 节笔记、{cards} 张卡片：{output}"
            skipped = study.skipped_pages
    except (OSError, ValueError) as exc:
        print(f"Paper2Cards: {exc}", file=sys.stderr)
        return 1
    try:
        print(message)
    except UnicodeEncodeError:
        # Redirected stdout on Windows may use a legacy code page.
        print(f"Generated {sections} sections and {cards} cards in {ascii(str(output))}")
    if skipped:
        print("未提取到文字的页码：" + "、".join(map(str, skipped)), file=sys.stderr)
    return 0
