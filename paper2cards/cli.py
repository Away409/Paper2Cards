import argparse
from pathlib import Path
import sys

from .export import export, publish
from .review import read_deck, review_html
from .source import read_pdf
from .study import generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把 PDF 学习资料转换为带出处的笔记与卡片。")
    parser.add_argument("input", type=Path, help="PDF 讲义或已导出的 cards.json")
    parser.add_argument("-o", "--output", type=Path, help="新输出目录（默认 output/<文件名>）")
    args = parser.parse_args(argv)
    output = args.output or Path("output") / args.input.stem
    try:
        if args.input.suffix.lower() == ".json":
            publish(output, {"review.html": review_html(read_deck(args.input))})
            review_path = output / "review.html"
            try:
                print(f"自测页已生成：{review_path}")
            except UnicodeEncodeError:
                print(f"Review: {ascii(str(review_path))}")
            return 0
        study = generate(args.input.name, read_pdf(args.input))
        export(study, output)
    except (OSError, ValueError) as exc:
        print(f"Paper2Cards: {exc}", file=sys.stderr)
        return 1
    sections, cards = len(study.sections), len(study.cards)
    try:
        print(f"已生成 {sections} 节笔记、{cards} 张卡片：{output}")
    except UnicodeEncodeError:
        # Redirected stdout on Windows may use a legacy code page.
        print(f"Generated {sections} sections and {cards} cards in {ascii(str(output))}")
    if study.skipped_pages:
        print("未提取到文字的页码：" + "、".join(map(str, study.skipped_pages)), file=sys.stderr)
    return 0
