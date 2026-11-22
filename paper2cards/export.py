"""Publish both UTF-8 outputs together in a new directory."""

from dataclasses import asdict
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .study import StudySet


def markdown(study: StudySet) -> str:
    lines = [f"# {study.document}", "", "## 目录", ""]
    for section in study.sections:
        lines.append(f"- {section.title}（第 {section.first_page}–{section.last_page} 页）")
    for section in study.sections:
        lines.extend(["", f"## {section.title}", "", "### 摘要摘录", ""])
        for excerpt in section.highlights:
            lines.append(f"- {excerpt.quote}（第 {excerpt.page} 页）")
        if not section.highlights:
            lines.append("本节未提取到可用语句。")
        if section.concepts:
            lines.extend(["", "### 重要概念", ""])
            for item in section.concepts:
                lines.append(f"- **{item.term}**　{item.definition}（第 {item.source.page} 页）")
    lines.extend(["", "## 自测", ""])
    if not study.cards:
        lines.append("未识别到可制卡的定义句。")
    for i, card in enumerate(study.cards, 1):
        lines.extend([f"### {i}. {card.question}", ""])
        for j, option in enumerate(card.options):
            lines.append(f"- {chr(65 + j)}. {option}")
        lines.extend(["", f"答案：{card.answer}", "", f"> 第 {card.source.page} 页 · {card.source.quote}", ""])
    if study.skipped_pages:
        lines.append("未提取到文字的页码：" + "、".join(map(str, study.skipped_pages)))
    return "\n".join(lines).rstrip() + "\n"


def export(study: StudySet, output: Path) -> None:
    if output.exists():
        raise ValueError(f"输出目录已存在，请选择新目录：{output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as staging:
        bundle = Path(staging) / "bundle"
        bundle.mkdir()
        (bundle / "notes.md").write_text(markdown(study), encoding="utf-8")
        data = {"schema_version": 1, **asdict(study)}
        (bundle / "cards.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        bundle.rename(output)
