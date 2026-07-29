# rag_ingestion_lab

> 课表位置：[标准学习路径](../../../course/learning-path.md) V0 步骤 8–9。步骤 8 先读 [文档内容识别、解析路由、结构还原与来源保留](../../../course/mechanisms/document-loading-and-cleaning.md)，步骤 9 再读 [Chunking、父子块与 Metadata](../../../course/mechanisms/chunking-and-metadata.md)。

本实验负责运行方式、输出解读和代码阅读路径。机制原理在课程正文，核心实现位于 [`rag_core.ingestion`](../../packages/rag_core/ingestion/) 和 [`rag_core.chunking`](../../packages/rag_core/chunking/)；demo 只读取 fixture、调用公共 API，并使用全仓共享的 [`app_log`](../../packages/app_log/) 呈现结果。

## 实验契约

fixtures 是人为编写的模拟业务内容，但使用真实 TXT、Markdown、DOCX 和文本型 PDF 文件，不使用 Mock Parser。

[`canonical_content.json`](../../../review_assistant/fixtures/v0/ingestion/canonical_content.json) 固定四种格式共同表达的业务事实。manifest 将四个文件定义为同一业务文档版本的互斥表示：每次独立观察一个格式，不能把四份内容同时入库。

因此本实验只验证格式解析、来源定位、确定性清洗和错误分层基线，不证明任意复杂生产文档都能正确解析。

## 默认运行：先看摘要

在仓库根目录运行：

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py
```

默认 compact 输出只展示：

- 文件和识别格式。
- `DocumentElement` 数量。
- 当前格式真实拥有的 locator。
- `SUCCESS` / `WARNING` 状态。
- warning 和最终汇总。

默认不逐条打印全部元素，避免格式对照被大段文本淹没。不要比较哪种格式的元素数量“更正确”；Markdown 标题、DOCX 表格和 PDF 页面天然会产生不同结构。

## Verbose：观察元素和清洗

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py --verbose
```

verbose 会增加：

- 每个元素的 `kind`、`element_id`、locator 和文本预览。
- 元素与报告中的 `cleaning_actions`。
- `cleaning_probe.md` 的确定性清洗对照。

清洗 probe 固定观察：

- 不换行空格替换。
- Unicode NFC 规范化。
- 多余空行收敛。
- 外层空白删除。

规范化后仍需保留业务文本和段内换行。清洗实验不能证明 Parser 的阅读顺序正确，也不能用来修复缺失图片或表格语义。

## 稳定边界与失败

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py --include-failures
```

输出先比较一个双栏 PDF：

- 视觉上左栏应先读。
- fixture 故意先把右栏写入 PDF 内容流。
- `pypdf` 因而先抽取右栏。
- Loader 必须保留 `pdf_reading_order_not_guaranteed`。

随后核对四个失败契约：

| 输入 | expected stage | expected code |
| --- | --- | --- |
| 真实栅格图片扫描 PDF | `empty_content` | `pdf_text_layer_missing` |
| 损坏 DOCX | `parse` | `document_parse_failed` |
| 非 UTF-8 TXT | `parse` | `text_decode_failed` |
| 无有效内容 Markdown | `empty_content` | `empty_document` |

manifest 同时冻结 stage 和 code。任意一项不匹配、或失败样例意外成功，结果为 `MISMATCH` 且命令返回非零退出码。

## JSON Lines

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py \
  --log-format json
```

每行是一个独立 JSON 事件，适合 CI、脚本处理和后续 Trace 接入。warning/error 写入 stderr；普通结果写入 stdout。`--no-color` 可强制关闭 ANSI 颜色。

## 第九步：为什么 Element 还不是检索 Chunk

第八步的 Markdown Parser 会把标题、列表项分别保存为 `DocumentElement`。这是原文结构，不保证每个元素都适合独立检索：

- 只有标题的 Element 没有业务事实。
- “允许申请售后”和“虚拟商品除外”位于两个列表项。
- DOCX 表格和 PDF 页面又可能比一次检索需要的内容更大。

运行策略对照：

```bash
uv run python source/demos/rag_ingestion_lab/inspect_chunking.py
```

默认比较：

- `element_baseline`
- `fixed_window`
- `structure_aware`
- `parent_child`

输出只描述块数量、token 分布、重复量、来源跨度，以及两组相关事实位于同一 retrieval chunk、同一 parent 或不同 chunk。它不把某种组织方式标记为通过或失败，也不能代替后续真实 Retriever 评估。

只观察一种策略或修改窗口：

```bash
uv run python source/demos/rag_ingestion_lab/inspect_chunking.py \
  --policy fixed \
  --max-tokens 32 \
  --overlap-tokens 6
```

查看 `chunk_id`、Parent/child、文本和逐项来源跨度：

```bash
uv run python source/demos/rag_ingestion_lab/inspect_chunking.py \
  --policy parent-child \
  --verbose
```

JSON Lines：

```bash
uv run python source/demos/rag_ingestion_lab/inspect_chunking.py \
  --log-format json
```

Chunking 对照使用第八步已经加载成功的真实 Markdown fixture，不增加故意损坏的 Chunk 或专门报错样例。参数不合法仍由公共契约明确拒绝，但不作为课程实验主线。

## Demo 的调用路径

```text
main
→ 读取 manifest.json
→ load_document
→ 读取 KnowledgeDocument / LoadReport
→ compact / verbose / json 呈现
→ 检查 warning 和失败契约
→ 最终汇总与退出码
```

demo 不实现格式检测、Parser、清洗或稳定 ID。修改核心机制应进入 package，不应写进终端渲染代码。

## 从 Demo 进入核心代码

建议按一次真实调用的顺序阅读：

1. [`inspect_ingestion.py`](inspect_ingestion.py)：看调用者传入什么、读取什么结果。
2. [`ingestion/loader.py`](../../packages/rag_core/ingestion/loader.py)：看公共入口、大小预检、调用顺序、结果组装和错误转换。
3. [`ingestion/models.py`](../../packages/rag_core/ingestion/models.py)：看文件、文档、元素、locator 与报告契约。
4. [`ingestion/parsers.py`](../../packages/rag_core/ingestion/parsers.py)：选择一个格式，追踪它如何产生 `ParsedElement`。
5. [`ingestion/cleaning.py`](../../packages/rag_core/ingestion/cleaning.py)：看文本和 `cleaning_actions` 如何同时返回。
6. [`tests/test_ingestion.py`](../../packages/rag_core/tests/test_ingestion.py)：看哪些行为被固定为回归契约。

第一次阅读不需要同时理解四种 Parser。可以先追踪 Markdown 正常路径，再用 PDF 观察成功、warning 与 error 的区别。

## 修改实验材料

### 修改 canonical facts

1. 修改 `review_assistant/fixtures/v0/ingestion/canonical_content.json`。
2. 同步修改 TXT 和 Markdown 表示。
3. 重新生成 DOCX、正常 PDF、扫描 PDF 和错序 PDF：

```bash
uv run python review_assistant/fixtures/v0/ingestion/build_binary_fixtures.py
```

4. 运行测试，确认四种格式仍保留全部 canonical facts。

### 增加失败样例

先在 manifest 登记 `expected_stage` 和 `expected_error`，再让实验验证实际错误层。不能看到实现返回什么后再把 expected 值改成相同结果。

## 运行测试

```bash
uv run pytest source/packages/rag_core/tests -q
```

测试覆盖 canonical facts、稳定身份、四格式 locator、清洗 actions、文本型 PDF、部分无文本页、真实扫描 PDF、双栏阅读顺序、编码、格式检测、文件大小预检和历史证据边界。

## 当前实验不观察什么

- `inspect_ingestion.py` 不产生 Chunk；`inspect_chunking.py` 只比较 Chunk 组织，不建立索引。
- 不建立 Embedding、FTS 或向量索引。
- 不运行 Retriever，不宣称某个策略召回质量更好。
- 不对扫描 PDF 静默调用 OCR/VLM。
- 不用模型推测缺失结构或来源位置。
- 不用受控 fixtures 证明复杂真实文档的整体解析质量。

这些边界让实验只回答“资料能否可靠进入知识文档契约”。
