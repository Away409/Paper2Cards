import argparse
from pathlib import Path
import sys

from .ai import draft
from .export import export, publish
from .review import read_deck, review_html
from .source import read_pdf
from .study import generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把 PDF 学习资料转换为带出处的笔记与卡片。")
    parser.add_argument("input", type=Path, help="PDF 讲义或已导出的 cards.json")
    parser.add_argument("-o", "--output", type=Path, help="新输出目录（默认 output/<文件名>）")
    parser.add_argument("--ai-section", type=int, action="append", metavar="N",
                        help="向 OpenAI 发送第 N 章的摘录并出题（从 1 开始，可重复）")
    parser.add_argument("--ai-model", default="gpt-4o-mini", help="AI 出题使用的 OpenAI 模型")
    args = parser.parse_args(argv)
    output = args.output or Path("output") / args.input.stem
    try:
        if args.input.suffix.lower() == ".json":
            if args.ai_section:
                raise ValueError("AI 出题需要 PDF 原文；请选择 PDF 作为输入。")
            publish(output, {"review.html": review_html(read_deck(args.input))})
            review_path = output / "review.html"
            try:
                print(f"自测页已生成：{review_path}")
            except UnicodeEncodeError:
                print(f"Review: {ascii(str(review_path))}")
            return 0
        source = read_pdf(args.input)
        study = generate(args.input.name, source)
        if args.ai_section:
            if output.exists():
                raise ValueError(f"输出目录已存在，请选择新目录：{output}")
            generated = draft(source, args.ai_section, args.ai_model)
            study.cards.extend(generated)
            print(f"AI 出题：收录 {len(generated)} 张。", file=sys.stderr)
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
