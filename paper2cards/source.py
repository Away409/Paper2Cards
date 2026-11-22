"""Read text and top-level PDF bookmarks. Page numbers always start at one."""

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PyPdfError


@dataclass(frozen=True)
class Page:
    number: int
    text: str


@dataclass
class Section:
    title: str
    pages: list[Page]


def read_pdf(path: Path) -> list[Section]:
    sections: list[Section] = []
    with path.open("rb") as stream:
        try:
            reader = PdfReader(stream)
            if reader.is_encrypted:
                raise ValueError("请先解锁 PDF，再运行转换。")
            headings = {}
            for item in reader.outline:
                if isinstance(item, list):
                    continue
                index = reader.get_destination_page_number(item)
                if index is not None and index >= 0 and item.title:
                    headings.setdefault(index, str(item.title))
            for index, page in enumerate(reader.pages):
                number = index + 1
                if not headings or not sections or index in headings:
                    title = headings.get(index, f"第 {number} 页" if not headings else "正文开头")
                    sections.append(Section(title, []))
                sections[-1].pages.append(Page(number, page.extract_text() or ""))
        except PyPdfError as exc:
            raise ValueError(f"无法解析 PDF。{exc}") from exc
    if not any(p.text.strip() for section in sections for p in section.pages):
        raise ValueError("未提取到文字。扫描件请先进行 OCR。")
    return sections
