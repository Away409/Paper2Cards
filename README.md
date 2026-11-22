# Paper2Cards

把 PDF 讲义整理成能回到原文核对的复习卡片。输入一份带文字层的 PDF，可在本机得到章节目录、摘要摘录、概念表、问答卡和选择题。生成过程离线运行，无需 API 密钥。

例如，示例讲义第 1 页写着「栈是仅允许在同一端插入和删除元素的线性表。」Paper2Cards 会生成「如何定义『栈』？」这张卡，并保留答案、页码和这句原文。

## 快速体验

需要 Python 3.10 或更高版本。在项目根目录的 PowerShell 中运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install .
.\.venv\Scripts\python -m paper2cards examples/data-structures.pdf
```

Linux 和 macOS 可将上述解释器路径换成 `.venv/bin/python`。首次安装需要获取 pypdf。示例含两页原创中文讲义，会生成 4 张问答卡和 4 道选择题。

- `output/data-structures/notes.md` 是可直接阅读的复习笔记。每节摘录最前面的两条有效语句。
- `output/data-structures/cards.json` 是 UTF-8 题库。每张卡的 `source.page` 从 PDF 的第一页起按 1 编号，`source.quote` 保存对应原句并整理换行空白。
- 转换自己的资料可运行 `python -m paper2cards "课程讲义.pdf" -o "output/课程复习"`，使用安装过本项目的 Python。每次请选择新的输出目录。

## 适用范围

v0.1.0 采用抽取式规则。顶层 PDF 书签决定章节起始页，无书签时逐页整理。工具识别「栈是……」「术语：……」「A stack is ...」等定义句，每个概念保留首次出现的定义。至少识别到三个不同概念时，会用同一份资料里的术语组成选项。一般叙述可能只有笔记，规则也可能误识别定义。复习时可以用卡片中的原句核对。

图片扫描件需要先做 OCR，部分页面缺少文字时会列出页码。多栏排版和公式的阅读顺序取决于 PDF 文字层。

## 项目结构

| 模块 | 职责 |
| --- | --- |
| `paper2cards/source.py` | 读取 PDF 书签，保留物理页码与文本 |
| `paper2cards/study.py` | 从章节生成结构化笔记、概念和带出处的卡片 |
| `paper2cards/export.py` | 将同一份学习资料导出成 Markdown 和 JSON |
| `paper2cards/cli.py` | 命令行入口与错误提示 |
| `examples/data-structures.pdf` | 两页可复现的示例输入 |
| `tests/` | 转换、来源核验和异常输入测试 |

后续接入可选的大模型生成器时，可以复用 `Section` 与 `StudySet`，保留相同的页码与出处字段。运行测试使用 `python -m unittest discover -s tests -v`。
