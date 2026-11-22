import argparse
from pathlib import Path
import sys

from .export import export
from .source import read_pdf
from .study import generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把 PDF 学习资料转换为带出处的笔记与卡片。")
    parser.add_argument("pdf", type=Path, help="输入 PDF")
    parser.add_argument("-o", "--output", type=Path, help="新输出目录（默认 output/<文件名>）")
    args = parser.parse_args(argv)
    output = args.output or Path("output") / args.pdf.stem
    try:
        study = generate(args.pdf.name, read_pdf(args.pdf))
        export(study, output)
    except (OSError, ValueError) as exc:
        print(f"Paper2Cards: {exc}", file=sys.stderr)
        return 1
    print(f"已生成 {len(study.sections)} 节笔记、{len(study.cards)} 张卡片：{output}")
    if study.skipped_pages:
        print("未提取到文字的页码：" + "、".join(map(str, study.skipped_pages)), file=sys.stderr)
    return 0
