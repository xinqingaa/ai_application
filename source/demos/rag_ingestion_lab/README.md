# rag_ingestion_lab

> 课表位置：[标准学习路径](../../../course/learning-path.md) V0 步骤 8。必要前置是 [RAG 与外部知识的边界](../../../course/concepts/rag-and-external-knowledge.md)，实现思路先读 [文档内容识别、解析路由、结构还原与来源保留](../../../course/mechanisms/document-loading-and-cleaning.md)。

本实验负责运行方式、输出解读和代码阅读路径。机制原理在课程正文，核心实现位于 [`rag_core.ingestion`](../../packages/rag_core/ingestion/)；demo 只读取 fixture manifest、调用公共 API 并打印诊断。

## 实验契约

fixtures 是人为编写的模拟业务内容，但使用真实 TXT、Markdown、DOCX 和文本型 PDF 文件，不使用 Mock Parser。

[`canonical_content.json`](../../../review_assistant/fixtures/v0/ingestion/canonical_content.json) 固定四种格式共同表达的业务事实。manifest 将四个文件定义为同一业务文档版本的互斥表示：每次独立观察一个格式，不能把四份内容同时入库。

因此本实验只验证格式解析、来源定位和错误分层基线，不证明任意复杂生产文档都能正确解析。

## 先运行正常路径

在仓库根目录运行：

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py
```

输出首先显示实验契约：

```text
[fixture_contract] kind=synthetic_controlled_format_comparison mode=mutually_exclusive_representations canonical=canonical_content.json
```

随后分别加载四种格式。建议按以下顺序读每个 `[loaded]` 块：

1. `file` 与 `format`：当前物理输入是什么。
2. `document@version`：四种表示是否共享业务身份。
3. `role` 与 `eligibility`：资料能以什么角色进入后续证据链。
4. `elements` 与 `hash`：解析结果数量和物理文件身份。
5. 每个元素的 `kind`、`id`、`locator` 和文本预览。
6. `[warning]`：成功结果仍然存在的格式边界。

不要比较哪种格式的元素数量“更正确”。Markdown 标题、DOCX 表格和 PDF 页面天然会产生不同结构。应检查 canonical facts 是否存在，以及 locator 是否忠实表达原格式。

## Demo 的调用路径

主脚本 [`inspect_ingestion.py`](inspect_ingestion.py) 的调用链是：

```text
main
→ 读取 manifest.json
→ 遍历 documents
→ _inspect_document
→ load_document
→ 读取 result.document / result.report
→ 打印 element 与 warning
```

关键位置：

- `main` 决定运行正常组还是同时运行失败组。
- `_inspect_document` 将 manifest 中的业务身份、来源角色和证据资格传给 `load_document`。
- `_inspect_failure` 捕获 `IngestionError`，并核对实际错误码是否符合 fixture 的 `expected_error`。

demo 不实现格式检测、Parser、清洗或稳定 ID。修改核心机制应进入 package，不应把逻辑写进打印脚本。

## 从 Demo 进入核心代码

建议按一次真实调用的顺序阅读：

1. [`inspect_ingestion.py`](inspect_ingestion.py)：看调用者传入什么、读取什么结果。
2. [`ingestion/loader.py`](../../packages/rag_core/ingestion/loader.py)：看公共入口、调用顺序、结果组装和错误转换。
3. [`ingestion/models.py`](../../packages/rag_core/ingestion/models.py)：看文件、文档、元素、locator 与报告契约。
4. [`ingestion/parsers.py`](../../packages/rag_core/ingestion/parsers.py)：选择一个格式，追踪它如何产生 `ParsedElement`。
5. [`ingestion/cleaning.py`](../../packages/rag_core/ingestion/cleaning.py)：看文本和 `cleaning_actions` 如何同时返回。
6. [`tests/test_ingestion.py`](../../packages/rag_core/tests/test_ingestion.py)：看哪些行为被固定为回归契约。

第一次阅读不需要同时理解四种 Parser。可以先追踪 Markdown 正常路径，再用 PDF 观察 warning 与 error 的区别。

## 运行稳定失败组

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py --include-failures
```

预期看到：

```text
[expected_failure] file=image_only_scan.pdf stage=empty_content code=pdf_text_layer_missing ... matched=True
[expected_failure] file=damaged.docx stage=parse code=document_parse_failed ... matched=True
[expected_failure] file=invalid_encoding.txt stage=parse code=text_decode_failed ... matched=True
[expected_failure] file=empty.md stage=empty_content code=empty_document ... matched=True
```

`matched=True` 只说明失败进入了预先登记的错误路径，不表示该格式主路径成功。

## 修改一个实验变量

### 修改业务事实

1. 修改 `review_assistant/fixtures/v0/ingestion/canonical_content.json`。
2. 同步修改 TXT 和 Markdown 表示。
3. 重新生成 DOCX 和 PDF：

```bash
uv run python review_assistant/fixtures/v0/ingestion/build_binary_fixtures.py
```

4. 运行测试，确认四种格式仍保留全部 canonical facts。

### 增加一个正常格式样例

先判断它是新的格式能力，还是同一格式的复杂结构 bad case。只有前者才应扩展公共格式契约；后者优先增加 fixture 和 Parser 回归测试。新增 manifest 项时必须给出业务身份、来源角色和证据资格。

### 增加一个失败样例

先在 manifest 登记 `expected_error`，再让 `--include-failures` 验证实际错误层。不能看到实现返回什么后再把 expected 值改成相同结果。

## 运行测试

定向测试：

```bash
uv run pytest source/packages/rag_core/tests -q
```

测试覆盖 canonical facts、稳定身份、四格式 locator、文本型 PDF、无文本层 PDF、编码、格式检测和历史证据边界。

## 本实验不观察什么

- 不产生 Chunk，不比较 Chunk 策略。
- 不建立 Embedding、FTS 或向量索引。
- 不对扫描 PDF 静默调用 OCR/VLM。
- 不用模型推测缺失结构或来源位置。
- 不用受控 fixtures 证明复杂真实文档的整体解析质量。

这些边界让实验只回答“资料能否可靠进入知识文档契约”。
