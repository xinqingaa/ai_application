# 文档加载、清洗与来源保留

> 机制篇：理解 TXT、Markdown、DOCX 和文本型 PDF 怎样进入统一知识文档契约，同时保留能够回到原文的位置。
>
> 课程位置：[标准学习路径](../learning-path.md) V0 第八步。必要前置是 [RAG 与外部知识的边界](../concepts/rag-and-external-knowledge.md)；本文交付可运行的 ingestion 机制、真实代码调用链、四格式对照和失败定位，不产生 Chunk，也不建立检索索引。

## 上传成功，为什么仍然没有知识

需求评审助手收到一份 `after-sale-rules.pdf`。文件存在、大小正常，上传接口也返回了成功，但系统检索不到其中的规则。

可能发生了几件完全不同的事：

- 这是文本型 PDF，但解析库没有按预期提取页面内容。
- 这是扫描 PDF，页面只有图片，本来就没有文本层。
- 文本已经提取，但双栏阅读顺序错乱，条件和结论被拼反。
- 清洗规则删掉了表头、换行或否定词。
- 内容存在，却没有保留页码，后续无法回到原文核对。

“拿到文件字节”只说明传输完成。知识生产还要回答：内容是否被正确读出，结构是否仍然可解释，来源能否定位，失败是否清晰可见。

## 本文有一条可以立即运行的机制链

本文不是只介绍解析库。共享实现位于 [`rag_core.ingestion`](../../source/packages/rag_core/ingestion/)，最小实验位于 [`rag_ingestion_lab`](../../source/demos/rag_ingestion_lab/)。

先在仓库根目录运行正常路径：

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py
```

此时先不用读完所有输出，只确认四件事：

1. TXT、Markdown、DOCX 和文本型 PDF 都得到 `loaded` 结果。
2. 每个结果都包含 `document_id@version`、元素和 locator。
3. 四种格式的元素数量和 locator 类型不同。
4. PDF 有页码和 reading-order warning，不是“没有结果”。

接下来正文会沿着实验调用的真实路径解释实现：

```text
inspect_ingestion.main
→ 读取 fixture manifest
→ 调用 load_document
→ 检测格式并选择 parser
→ 清洗 ParsedElement
→ 组装 KnowledgeDocument + LoadReport
→ demo 打印元素、位置、warning 或 error
```

完整命令、输出字段和修改实验的方法由 [demo README](../../source/demos/rag_ingestion_lab/README.md) 维护。正文关注这条链为什么这样实现。

## 从一个字符串递进到知识文档契约

最简单的文档加载方式，是读取文件后返回一个字符串。它只能回答“有没有文本”，不能回答：

- 这是哪个业务文档和哪个版本？
- 这段文字来自第几页、哪一段或哪个标题？
- 历史评审能否作为当前规则的证据？
- 内容是解析失败、清洗后为空，还是扫描 PDF 没有文本层？
- 文件或策略改变后，元素身份是否仍然可比较？

因此实现按问题逐层增加责任：

```text
读取文件字节
→ 识别并校验格式
→ 用格式 Parser 产生带位置的元素
→ 确定性清洗并记录动作
→ 生成稳定元素身份
→ 组装业务文档和加载诊断
```

这不是为了把 Loader 做复杂，而是让每一次转换都留下可验证结果。后面的 Chunking 和 Retrieval 只能使用这里已经存在的内容与来源，不能补救已经丢失的原文。

## 文件、文档、元素和 Chunk 是四个对象

真实数据契约定义在 [`ingestion/models.py`](../../source/packages/rag_core/ingestion/models.py)。四个对象分别回答不同问题：

| 对象 | 核心责任 | 当前实现中的关键字段 |
| --- | --- | --- |
| `FileArtifact` | 描述收到的物理文件 | `path`、`filename`、`size_bytes`、`content_hash`、`content` |
| `KnowledgeDocument` | 描述具有业务身份和来源角色的知识文档 | `document_id`、`document_version`、`source_role`、`evidence_eligibility`、`elements` |
| `DocumentElement` | 保存解析后的内容、结构类型和原始位置 | `element_id`、`kind`、`text`、`locator`、`cleaning_actions` |
| `Chunk` | 为后续检索策略创建单元 | 本文不产生 |

同一个业务文档可以有多个文件版本。`document_id` 回答“这是哪份业务文档”，`document_version` 回答“这是哪个内容版本”，文件名和内容哈希描述本次物理输入。数据库自增 ID、文件名和业务身份不能互相替代。

本阶段的完整输入输出是：

```text
path + document identity + source contract + LoaderConfig
→ FileArtifact
→ ParsedElement[]
→ DocumentElement[]
→ KnowledgeDocument + LoadReport
```

## 公共入口先冻结调用者必须提供的信息

公共入口是 [`load_document`](../../source/packages/rag_core/ingestion/loader.py)：

```python
def load_document(
    path: str | Path,
    *,
    document_id: str,
    document_version: str,
    source_role: SourceRole,
    evidence_eligibility: EvidenceEligibility,
    metadata: Mapping[str, str] | None = None,
    config: LoaderConfig | None = None,
) -> LoadResult:
```

这段签名把两类信息分开：

- Loader 可以从文件得到路径、字节、格式、大小和内容哈希。
- Loader 无法从字节可靠推断业务文档身份、版本、来源角色和证据资格，这些必须由调用者提供。

如果让 Parser 根据文件名猜 `document_id`，重命名文件就会改变业务身份；如果让模型判断历史材料能否成为当前证据，来源事实就会变成不稳定推测。

## 第一步：先执行应用约束，再解析文件

[`loader.py`](../../source/packages/rag_core/ingestion/loader.py) 在读取内容前先校验业务身份和来源边界：

```python
document_id = document_id.strip()
document_version = document_version.strip()
if not document_id or not document_version:
    raise ValueError("document_id 和 document_version 不能为空")
if (
    source_role is SourceRole.HISTORICAL_MATERIAL
    and evidence_eligibility is EvidenceEligibility.CURRENT_EVIDENCE
):
    raise ValueError("Historical Material 不能直接标记为 current_evidence")
```

这里体现了一个不变量：历史材料可以进入知识系统，但不能自动获得“当前规则证据”资格。Parser 只负责读取内容，不负责修改来源角色。

当前待评审 PRD 是 Target Requirement，它通过 `ReviewRequest` 直接进入后续评审链路。本 Loader 服务 Reference Knowledge 和 Historical Material，不会为了复用文件解析就把 Target Requirement 混进外部证据候选池。

## 第二步：检测格式和解析格式是两层责任

公共流程接着读取文件、检查大小、检测格式，再把文件交给对应 Parser：

```python
loader_config = config or LoaderConfig()
artifact = _read_artifact(path)
if artifact.size_bytes > loader_config.max_file_bytes:
    raise IngestionError(
        code=IngestionErrorCode.FILE_TOO_LARGE,
        stage=IngestionStage.FORMAT_DETECTION,
        message=f"文件大小 {artifact.size_bytes} 超过上限 {loader_config.max_file_bytes}",
        filename=artifact.filename,
    )

file_format = _detect_format(artifact)
parsed = parse_artifact(artifact, file_format, loader_config)
```

`_detect_format` 先根据支持的扩展名选择格式，并对 PDF、DOCX 检查基础文件头。它回答“这是不是一种可交给对应 Parser 的输入”。

`parse_artifact` 再调用格式库读取内部结构。它回答“合法格式内部有哪些可用内容和位置”。因此：

- 扩展名是 `.pdf`，文件头却不是 PDF，属于 `format_detection/format_mismatch`。
- 文件头看起来像 DOCX，但内部 OOXML 已损坏，属于 `parse/document_parse_failed`。

把两层拆开后，使用者不会只得到一个无法行动的“加载失败”。

## 四种 Parser 保留各自真正拥有的位置

格式分派位于 [`ingestion/parsers.py`](../../source/packages/rag_core/ingestion/parsers.py)。统一契约不是把所有格式强行改造成相同结构，而是保证每个 `ParsedElement` 都带一个结构化 `SourceLocator`。

### TXT：连续文本块和行范围

TXT 没有天然标题结构。`_parse_txt` 按空行形成连续非空块，在 flush 时保存 `line_start` 和 `line_end`。

默认编码是 UTF-8 / UTF-8-SIG。GBK 等编码不会被静默猜测，因为自动猜测可能把错误字节解释成看似正常的文本。调用者需要显式设置 `LoaderConfig.text_encoding`，或者在进入系统前完成可追踪的编码转换。

### Markdown：语法 Token 和标题路径

`_parse_markdown` 不用正则删除 `#` 后返回大字符串。`markdown-it-py` 先生成 Token，Parser 再读取 Token 的 `map` 作为源行范围，并维护当前 `heading_path`。

因此列表项可以表达自己属于“售后入口与订单状态 > 接口与客户端约束”。这仍然是原文结构，不是 Chunk 的父子关系。

### DOCX：按文档顺序处理段落和表格

`_parse_docx` 使用 `python-docx` 的 `iter_inner_content()` 按文档顺序读取 `Paragraph` 和 `Table`。标题样式更新 heading path，普通段落保存段落序号，表格保存表格序号和完整单元格内容。

DOCX 的视觉分页、浮动文本框、图形和图片文字不等于稳定逻辑结构。当前实现不根据排版坐标伪造页码，也不声称完整还原复杂 Office 文档。

### PDF：文本型成功，无文本层明确失败

`_parse_pdf` 使用 `pypdf` 逐页提取文本，并把真实 PDF 页码写入 locator。若某一页没有文本，Parser 记录 page warning；若所有页面都没有文本，才将整个文档判为失败：

```python
if not elements:
    raise IngestionError(
        code=IngestionErrorCode.PDF_TEXT_LAYER_MISSING,
        stage=IngestionStage.EMPTY_CONTENT,
        message="PDF 没有可提取文本层；V0 不会静默调用 OCR/VLM",
        filename=artifact.filename,
    )
```

文本型 PDF 正常产生页面元素。复杂分栏、表格和浮动元素的阅读顺序仍可能与视觉版面不同，所以成功结果还会携带 `pdf_reading_order_not_guaranteed` warning。warning 表示需要核对，不表示没有结果。

四种 locator 保留格式真实拥有的位置：

```text
TXT       → text_lines, lines=6-7
Markdown  → markdown_block, lines=10, heading=API and client constraints
DOCX      → docx_table, table=1, heading=After-sale entry and order status > API and client constraints
PDF       → pdf_page, page=2
```

下游只依赖 locator 可以展示和回查，不要求所有来源都有页码。

## 第三步：清洗每个元素，并保留清洗事实

格式 Parser 返回 `ParsedElement` 后，公共流程逐元素调用 [`clean_text`](../../source/packages/rag_core/ingestion/cleaning.py)：

```python
for parsed_element in parsed.elements:
    try:
        cleaned, actions = clean_text(parsed_element.text, loader_config)
    except Exception as exc:
        raise IngestionError(
            code=IngestionErrorCode.CLEANING_FAILED,
            stage=IngestionStage.CLEANING,
            message=f"文本清洗失败：{exc}",
            filename=artifact.filename,
            raw=exc,
        ) from exc
    if not cleaned:
        continue
```

当前清洗只做确定性规范化：统一换行、替换不换行空格、Unicode NFC、删除行尾和外层空白、收敛过多空行。它不会删除标点、代码标识、标题、表头、否定条件或段落内换行。

清洗函数同时返回 `actions`。动作写入对应 `DocumentElement`，再由 `LoadReport` 汇总。这样看到文本变化时，可以区分是 Parser 原始输出还是清洗策略造成的结果。

下面几类操作不属于当前清洗：

| 操作 | 为什么危险 |
| --- | --- |
| 把所有换行替换为空格 | 表格行、列表项和条件边界消失 |
| 删除重复词或相似句 | 现行规则与历史规则可能被错误合并 |
| 用模型改写原文 | 来源事实变成不可复现的模型输出 |
| 解析失败后返回空字符串 | 下游无法区分空文档、扫描件和程序错误 |

清洗不是“让文本看起来漂亮”，而是在不破坏业务含义的前提下建立可重复输入。

## 第四步：稳定元素身份，再同时返回业务结果和诊断

清洗成功后，Loader 根据业务文档身份、版本、元素顺序、locator 和清洗后文本生成 `element_id`：

```python
element_id = _element_id(
    document_id,
    document_version,
    ordinal,
    parsed_element.locator.describe(),
    cleaned,
)
```

这意味着同一文件以相同身份和策略重复加载时，元素 ID 可预测；文档版本、位置或内容变化时，旧元素与新元素能够区分。它不是数据库自增主键，也不是后续 Chunk ID。

流程最后返回 `LoadResult`，其中包含三部分：

- `artifact`：本次物理文件事实。
- `document`：可以进入后续知识生产的业务文档和元素。
- `report`：格式、元素数量、locator 类型、清洗动作和 warning。

业务结果与诊断同时返回，但不混成一个无约束字典。后续代码消费 `KnowledgeDocument`，学习和排错入口读取 `LoadReport`。

如果解析和清洗后没有任何有效元素，Loader 不返回“空成功”，而是抛出 `empty_content/empty_document`。这保证“loaded”始终意味着至少存在一个可继续处理的元素。

## Fixtures 是受控模拟材料，不是生产资料

实验资料位于 [`review_assistant/fixtures/v0/ingestion`](../../review_assistant/fixtures/v0/ingestion/)。它们是人为编写的模拟业务内容，但使用真实 TXT、Markdown、DOCX 和 PDF 文件格式，由真实 Parser 处理。

四种正常文件共享同一份 canonical facts，用于观察格式怎样改变结构元素和 locator。它们是同一业务文档版本的四种互斥表示：实验每次独立加载一个文件，不把四份内容同时写入同一个知识库。

因此这个实验能够证明：

- 四种受支持格式能进入统一契约。
- 核心业务事实没有因格式解析丢失。
- 格式原生 locator 和结构化失败可观察。

它不能证明：

- 任意复杂 DOCX 或 PDF 都能正确解析。
- 双栏、复杂表格、图片和扫描件已经被可靠理解。
- 当前 Loader 已经达到真实生产资料的完整覆盖率。

失败 fixtures 也是人为构造的，只用于稳定复现无文本层 PDF、损坏 DOCX、错误编码和空文档路径。它们不是 Mock Parser 返回值。

## 用失败组验证错误分层

运行：

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py --include-failures
```

实验固定了四类失败：

| 输入 | 期望 stage | 期望 code | 说明 |
| --- | --- | --- | --- |
| 无文本层 PDF | `empty_content` | `pdf_text_layer_missing` | 不静默 OCR，不返回空成功 |
| 损坏 DOCX | `parse` | `document_parse_failed` | 文件头通过后，OOXML 结构解析失败 |
| 非 UTF-8 TXT | `parse` | `text_decode_failed` | 默认编码契约没有被猜测绕过 |
| 无知识内容的 Markdown | `empty_content` | `empty_document` | 文件存在不代表具有可用内容 |

错误类型定义在 [`ingestion/errors.py`](../../source/packages/rag_core/ingestion/errors.py)。建议按数据流顺序定位：

1. `format_detection`：文件存在吗，大小是否超限，扩展名与文件头一致吗？
2. `parse`：编码正确吗，文件是否损坏或加密，解析库是否支持当前结构？
3. `cleaning`：清洗策略是否异常，关键内容是否在这里消失？
4. `empty_content`：文件本来为空，还是 PDF 没有文本层？
5. source contract：业务身份、来源角色、证据资格和 locator 是否正确？

如果 `KnowledgeDocument` 中已经没有某条关键规则，后续 Retriever 无论怎样调参都无法召回它。此时应修复 Loader 或清洗，而不是调整 Embedding、top-k 或 Prompt。

## 测试把哪些不变量固定下来

实现测试位于 [`test_ingestion.py`](../../source/packages/rag_core/tests/test_ingestion.py)。运行：

```bash
uv run pytest source/packages/rag_core/tests -q
```

测试分别证明：

- 相同输入重复加载得到相同文件哈希和元素 ID。
- Markdown 标题路径、DOCX 段落/表格位置和 PDF 页码得到保留。
- 四种格式都包含 canonical facts。
- 文本型 PDF 成功，无文本层 PDF 明确失败。
- format mismatch、parse failure 和 empty content 不会混成同一种错误。
- Historical Material 不能被标成 Current Evidence。

测试通过不能替代机制解释，但可以防止这些不变量在后续 Chunking、索引和产品组合时悄悄退化。

## 解析库封装了什么，没有解决什么

三个解析库分别封装 Markdown 语法 Token、OOXML 文档结构和 PDF 内容流读取。它们减少了手写格式解析的错误，但没有替应用决定：

- 哪个文件属于哪个业务文档和版本。
- Reference Knowledge 与 Historical Material 的证据资格。
- 哪种结构损失可以接受。
- 清洗是否改变了业务语义。
- PDF 阅读顺序是否符合视觉版面。
- 扫描件是否值得进入 OCR/VLM 流程。
- DocumentElement 应怎样切成 Chunk。

因此，解析库返回了字符串，不等于知识生产已经完成。应用仍需建立身份、来源、诊断和失败契约。

## 在 V0 中的边界

本步骤已经实现：

- TXT、Markdown、DOCX 和文本型 PDF 的真实解析。
- 稳定文档身份、来源角色、证据资格和内容哈希。
- 格式原生 locator、确定性清洗和加载报告。
- 文本型 PDF 正常路径，以及无文本层 PDF 等可重复失败路径。

本步骤明确不做：

- Chunk、父子块、overlap 和 Chunk ID。
- Embedding、PostgreSQL FTS、pgvector 和 RRF。
- OCR/VLM、复杂版面恢复和图片语义抽取。
- 对象存储、后台入库任务和通用知识库管理后台。
- 文档更新、删除一致性和 Citation 失效治理。

后续 Chunking 机制会以这里产生的 `DocumentElement` 为输入；具体阅读位置仍以标准学习路径为准。

## 判断是否已经掌握

读完并运行实验后，应能回答：

1. 文件上传成功为什么不能证明知识已经可检索？
2. `FileArtifact`、`KnowledgeDocument`、`DocumentElement` 和 Chunk 分别承担什么责任？
3. `load_document` 从文件路径到 `LoadResult` 经历了哪些转换？
4. 为什么格式检测、格式解析和空内容要分成不同失败层？
5. 为什么 TXT、Markdown、DOCX 和 PDF 不应该统一伪装成页码定位？
6. 清洗动作为什么必须确定、可测试并记录？
7. `element_id` 为什么不能使用数据库自增 ID？
8. 文本型 PDF 的 warning 与无文本层 PDF 的 error 分别代表什么？
9. 为什么 Historical Material 的证据资格必须由应用控制？
10. 将 fixture 中一条规则改为相反含义后，哪些输出、哈希和测试应该变化？

完成后回到 [标准学习路径](../learning-path.md)，由唯一课表决定后续内容。
