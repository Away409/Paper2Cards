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
- `output/data-structures/review.html` 是离线自测页。双击即可开始，单独复制给同学也能使用。
- 转换自己的资料可运行 `python -m paper2cards "课程讲义.pdf" -o "output/课程复习"`，使用安装过本项目的 Python。每次请选择新的输出目录。

## v0.3.0 离线自测

在快速体验的示例中，打开 `review.html`，选择「线性结构」，就能练习关于栈和队列的 4 道题。问答卡先自己作答，点「查看答案」后选「已掌握」或「需重练」。选择题点击选项后立即判分。展开「查看原文」可核对引文和 PDF 物理页码。完成一轮后，点「重练错题」可只练本轮答错和标记需重练的题。进度仅保留在当前页面，刷新会重新开始。

用 v0.1.0 或 v0.2.0 导出的 `cards.json` 也能直接生成自测页。将下面的输入路径换成已有题库，输出指定一个新目录：

```powershell
.\.venv\Scripts\python -m paper2cards "旧版题库/cards.json" -o "output/旧题自测"
Start-Process ".\output\旧题自测\review.html"
```

导入沿用原题、选项与出处，无需原 PDF。生成后的 HTML 内含题库和页面所需资源，可以离线打开。可用仓库中的 `tests/fixtures/v0.1.0-cards.json` 体验旧题导入。

## v0.2.0 制卡质量

用同一份[六页原创讲义](examples/lecture-benchmark.pdf)运行两个版本。第 1 页连续写了「栈是后进先出的线性表」和队列的定义，第一行没有句号。v0.1.0 把两行拼成了一个答案，还把「注意」当作术语。v0.2.0 将两行分别制卡，另从「称没有孩子的结点为叶子结点。」中提取术语「叶子结点」和释义「没有孩子的结点」，三张问答卡均引用第 1 页。

前 3 页用于开发，后 3 页用于验收，均覆盖数据结构、离散数学和英文算法。每个概念的术语、释义、物理页码都与[固定标注](tests/fixtures/lectures.json)一致才算命中。选择题和问答卡共享概念，计分时每个概念只计一次。

| 预留 3 页，共 11 个标注概念 | 提取数 | 命中数 | 准确率（命中 / 提取） | 召回率（命中 / 标注） |
| --- | ---: | ---: | ---: | ---: |
| v0.1.0 | 8 | 5 | 62.5% | 45.5% |
| v0.2.0 | 10 | 10 | 100% | 90.9% |

本次漏掉的是第 6 页用英文「We call … a forest」表达的定义。以上指标仅描述这份小样本。完整六页的 CLI 输出从 28 张变为 36 张，可用 `python -m paper2cards examples/lecture-benchmark.pdf` 复现。运行 `python -m unittest discover -s tests -p test_quality.py -v` 可检查预留样本门槛（准确率 90%、召回率 80%）以及每张卡的引文和页码。

## 适用范围

顶层 PDF 书签决定章节起始页，无书签时逐页整理。工具识别「栈是……」「术语：……」「称……为……」「……称为……」和「A stack is ...」等定义句，每个概念保留首次出现的定义。至少识别到三个不同概念时，会用同一份资料里的术语组成选项。一般叙述可能只有笔记，规则也可能误识别定义。复习时可以用卡片中的原句核对。

图片扫描件需要先做 OCR，部分页面缺少文字时会列出页码。多栏排版和公式的阅读顺序取决于 PDF 文字层。

## 项目结构

| 模块 | 职责 |
| --- | --- |
| `paper2cards/source.py` | 读取 PDF 书签，保留物理页码与文本 |
| `paper2cards/extraction.py` | 处理断行，识别正向与反向定义句，过滤教学提示 |
| `paper2cards/study.py` | 从章节生成结构化笔记、概念和带出处的卡片 |
| `paper2cards/export.py` | 将笔记、题库和自测页一起写入新目录 |
| `paper2cards/review.py`、`review.html` | 校验题库，生成可离线使用的单文件自测页 |
| `paper2cards/cli.py` | 命令行入口与错误提示 |
| `examples/data-structures.pdf` | 两页可复现的示例输入 |
| `tests/` | 转换、来源核验和异常输入测试 |

后续接入可选的大模型生成器时，可以复用 `Section` 与 `StudySet`，保留相同的页码与出处字段。运行测试使用 `python -m unittest discover -s tests -v`。
