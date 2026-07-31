# 文档内容识别、解析路由、结构还原与来源保留

> 机制篇：理解一份文件怎样经过内容识别、解析路由和最小结构还原，成为可继续切片的知识文档。
>
> 课程位置：[标准学习路径](../learning-path.md) V0 第八步。必要前置是 [RAG 与外部知识的边界](../concepts/rag-and-external-knowledge.md)。本文用 PDF 建立复杂文档的完整心智模型，真实代码实现 TXT、Markdown、DOCX 和文本型 PDF；本文不产生 Chunk，不建立索引，也不实现 OCR/VLM。

## 先问文件里有什么，而不是先问用哪个库

需求评审助手收到一份 `after-sale-rules.pdf`。文件存在、大小正常，上传接口也返回成功，但这只能证明应用拿到了文件字节。

同一个 `.pdf` 后缀里可能装着完全不同的内容：

- 原生文本 PDF：文字有可提取文本层。
- 扫描 PDF：每页主要是一张图片，没有可用文本层。
- 图文混排 PDF：正文文字、截图、流程图、图表和扫描页同时存在。
- 复杂排版 PDF：虽然有文本层，但双栏、浮动文本框或表格使提取顺序失真。

如果不先识别内容形态，就无法选择正确的解析路线。直接调用文本提取库可能返回空字符串，也可能返回一段“看起来有字、实际顺序错误”的文本。

因此，文件进入 RAG 之前至少要经过两层知识生产：

```text
第一层：内容识别与解析路由
文件容器 → 内容形态 → 文本抽取 / OCR / 视觉理解

第二层：结构还原与统一表示
原始片段 → 阅读顺序、标题、段落、列表、表格、来源位置 → DocumentElement[]
```

本文只深入这两层，交付带结构和来源位置的 `DocumentElement[]`。Chunking 接收这组元素并建立检索单元，但不属于本文的文档解析责任。

## 第一层：识别内容形态并选择解析路线

### 格式识别只回答“容器是什么”

扩展名和文件头可以帮助确认输入是不是声明的格式。例如，文件名以 `.pdf` 结尾但文件头不是 PDF，应在格式检测阶段失败。

但格式识别不能回答：

- PDF 页面有没有文本层。
- DOCX 中是否包含图片、文本框或复杂图表。
- 一页文字能否按正确阅读顺序提取。
- 图片中的表格、箭头和关系是否需要视觉理解。

所以完整判断应是：

```text
识别文件容器
→ 检查容器内有什么可用内容
→ 按页或按区域选择解析路线
```

### PDF 是最完整的路由样例

PDF 不是“文字文档格式”，而是用于稳定呈现页面的容器。处理时至少需要下面的决策树：

```text
PDF
├─ 页面存在可靠文本层
│  └─ 提取文本、页码和可获得的位置
├─ 页面没有文本层
│  └─ 渲染页面 → OCR → 文字、坐标和置信度
└─ 文本、图片、图表或复杂版面混合
   └─ 文本抽取 + 版面分析 + 选择性 OCR/VLM → 按页面和区域合并
```

这个判断最好按页甚至按区域进行。一份 20 页 PDF 可能有 18 页原生文本和 2 页扫描附件；把整份文档简单标记为“文本 PDF”或“扫描 PDF”都会掩盖信息缺口。

### 原生文本路线：读取内容流，不是看懂页面

文本抽取库读取 PDF 内部的字符和内容流，再尝试生成页面文本。它适合文本层存在、阅读顺序相对简单的 PDF。

它并不等于视觉阅读。常见问题包括：

- 双栏内容左右交叉。
- 表格按单个字符或错误行序输出。
- 页眉页脚反复混入正文。
- 图表只提取标签，丢失箭头和空间关系。
- 字体编码异常导致字符乱码。

因此“提取到了非空文本”只是成功条件之一。系统还需要保留页码并报告阅读顺序风险，让后续实验或人工抽查能够发现结构问题。

### 扫描件路线：OCR 先识字，再恢复结构

扫描 PDF 没有可供文本库读取的字符层。典型 OCR 链路是：

```text
PDF 页面
→ 渲染为图像
→ 方向校正、去噪、裁边等预处理
→ 文字区域检测
→ 字符识别
→ 文本 + bounding box + confidence
→ 阅读顺序和段落重建
→ 来源定位与质量报告
```

OCR 的输出不应只有一个大字符串。坐标用于恢复阅读顺序和回到原图，置信度用于发现低质量区域，页码用于后续引用。

OCR 也不能自动保证理解正确。低分辨率、小字体、印章、手写内容和复杂表格都可能产生识别错误；“售后不可申请”中的“不”一旦丢失，结果会从格式问题变成业务事实错误。

当前 V0 不实现 OCR。当全部页面都没有可提取文本时，代码明确返回 `pdf_text_layer_missing`，而不是静默调用外部 OCR，也不返回空成功。

### 图文混排路线：组合确定性抽取和视觉理解

图文混排不应默认把整份文档交给 VLM 重写。更可控的方案是：

1. 先提取可靠的原生文本和页码。
2. 用版面分析识别文本块、图片、表格和区域坐标。
3. 只对缺少文本的图片区域执行 OCR。
4. 只对流程图、截图状态、图表关系等需要语义理解的区域调用 VLM。
5. 按页面、区域坐标和阅读顺序合并结果。
6. 为每个元素记录来源方式，例如 native text、OCR 或 VLM。
7. 保留模型、Prompt、置信度、成本和失败信息，以便复现。

VLM 适合回答“这张流程图表达了哪些分支”或“截图中按钮在哪种状态出现”，但输出具有模型不确定性，不能无记录地覆盖原生文字。涉及规则证据时，还需要让生成文本能够回到原始图片区域核对。

当前 V0 不实现版面分析、OCR、VLM 或多路结果合并。V1 的按需支撑课程会用固定样例观察这些机制，本节只建立选路原则和接口边界。

### 其他格式也遵循同一问题框架

PDF 的分支最多，但 TXT、Markdown 和 DOCX 仍要回答“容器里有什么、可以恢复什么结构”。

| 格式 | 主要解析依据 | 仍需警惕 |
| --- | --- | --- |
| TXT | 字符编码、行和空行 | 编码错误，没有可靠标题语义 |
| Markdown | 文本编码和语法 Token | 方言扩展、嵌入 HTML、外链图片 |
| DOCX | OOXML 段落、样式、表格顺序 | 图片、图形、文本框、复杂布局和视觉分页 |
| PDF | 页面文本层和内容流 | 扫描页、图文混排、阅读顺序和表格语义 |

DOCX 通常比 PDF 更容易读取逻辑段落，但并不天然等于纯文本。当前实现只处理段落、标题样式和表格，不读取图片文字、浮动文本框或图形关系。

## 第二层：从文本片段恢复可用结构

### 得到文字不等于得到知识结构

假设解析器返回下面的字符串：

```text
已支付 已完成
允许申请售后
虚拟商品除外
```

如果不知道它来自标题、表格还是连续段落，也不知道“虚拟商品除外”属于哪一节，后续切片很容易把条件与结论拆开。结构还原要把解析器能够可靠获得的关系保存下来：

```text
原始解析片段
→ 确定阅读顺序
→ 识别标题、段落、列表、代码和表格
→ 关联章节路径
→ 保存页码、行号、段落号或表格号
→ 形成统一 DocumentElement
```

“统一”不表示伪造所有格式都没有的信息。TXT 没有页码，就保存真实行号；PDF 没有可靠标题层级，就不能仅凭字号猜出一棵确定的章节树。

### 当前实现完成的是最小结构还原

真实数据契约位于 [`ingestion/models.py`](../../source/packages/rag_core/ingestion/models.py)。`DocumentElement` 保存：

- `kind`：标题、段落、列表项、表格、代码或页面。
- `text`：当前元素的规范化文本。
- `ordinal`：元素在统一序列中的顺序。
- `locator`：原格式真正拥有的位置和章节路径。
- `cleaning_actions`：文本经历过的确定性清洗。

四种格式的当前结构能力不同：

| 格式 | 当前保留 | 当前明确损失或不保证 |
| --- | --- | --- |
| TXT | 连续非空文本块、起止行号、原始顺序 | 标题层级、表格和视觉布局 |
| Markdown | 标题、段落、列表、代码、标题路径、行号 | 非 CommonMark 扩展和外链媒体语义 |
| DOCX | 标题样式、段落、表格、文档顺序、标题路径 | 图片文字、文本框、绘图、稳定视觉页码 |
| PDF | 页面文本、页码、页面顺序 | 可靠标题树、表格语义、区域坐标和复杂阅读顺序 |

当前 `KnowledgeDocument.elements` 是一个扁平有序序列，`heading_path` 表达元素所属章节。它不是完整文档结构树。

尚未实现的结构能力包括：

- 显式父子元素 ID 和嵌套结构树。
- bounding box 和区域级阅读顺序。
- 跨页表格、合并单元格和表头语义。
- 原生文本、OCR 与 VLM 结果的合并契约。
- 结构恢复的置信度和逐项信息损失报告。

这些限制必须显式保留，不能把扁平元素序列描述成“完整还原了文档”。

### 原始结构与父子 Chunk 不是一回事

第 8 步的结构还原描述原文拥有什么：标题、段落、表格、页面以及它们的位置。

第 9 步的父子 Chunk 描述检索策略怎样组织内容：小块用于命中，大块用于补充上下文，父子关系可能由切片策略重新建立。

```text
原始文档结构                     检索结构
标题 > 段落 > 表格      →       Parent Chunk > Child Chunk
```

检索结构必须基于原始结构，但不能反过来冒充原文结构。若第 8 步已经丢失标题或表格关系，第 9 步无法可靠猜回。

## 清洗属于归一化，不负责修复语义

格式 Parser 产生 `ParsedElement` 后，公共流程调用 [`clean_text`](../../source/packages/rag_core/ingestion/cleaning.py)。当前清洗只做确定性规范化：

- 统一换行。
- 替换不换行空格。
- Unicode NFC 规范化。
- 删除行尾和元素外层空白。
- 收敛过多空行。

清洗不会删除标点、标题、表头、否定词、代码标识或段落内换行，也不会用模型改写原文。

每次实际发生的变化会写入 `cleaning_actions`，再汇总到 `LoadReport`。看到文本变化时，使用者可以判断变化来自 Parser 还是清洗规则。

实验中的 `cleaning_probe.md` 固定包含不换行空格、分解形式 Unicode、多余空行和外层空白。verbose 输出会同时展示清洗前对应的输入特征、规范化文本和 actions；测试还会确认业务文本与段内换行没有被破坏。这样“确定性”不只表示代码没有调用模型，也表示每一类变化都能被观察和回归。

下面这些操作看似让文本更整齐，实际会破坏知识：

| 操作 | 风险 |
| --- | --- |
| 把全部换行替换为空格 | 列表、表格行和条件边界消失 |
| 删除重复词或相似句 | 现行规则和历史规则可能被错误合并 |
| 用模型润色解析结果 | 来源事实变成不可复现的生成内容 |
| 解析异常后返回空字符串 | 下游无法区分空文档、扫描件和程序错误 |

清洗只能规范已经识别出的内容，不能修复错误阅读顺序，也不能补回漏掉的图片或表格语义。

## 统一表示还必须保留业务身份和来源

物理文件、业务文档、结构元素和检索 Chunk 是四个不同对象：

| 对象 | 回答的问题 |
| --- | --- |
| `FileArtifact` | 本次收到哪个物理文件，字节和哈希是什么？ |
| `KnowledgeDocument` | 这是哪份业务文档、哪个版本、什么来源角色？ |
| `DocumentElement` | 解析出了什么结构化内容，它位于原文哪里？ |
| `Chunk` | 后续检索策略要用什么单元建立索引？本节不产生它。 |

同一业务文档可以有多个文件版本。文件名和数据库自增 ID 都不能稳定表达业务身份。因此调用者必须提供 `document_id`、`document_version`、`source_role` 和 `evidence_eligibility`。

这里还有一个业务不变量：Historical Material 可以进入知识系统，但不能自动标记为当前有效证据。Parser 负责读取内容，不负责决定资料是否有资格支撑当前结论。

## 把两层机制映射到真实代码

### 公共入口冻结输入输出契约

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

Loader 可以从文件得到路径、字节、格式、大小和内容哈希，但不能从字节可靠推断业务身份、版本、来源角色和证据资格。这些信息必须由调用者提供。

最终 `LoadResult` 同时返回：

- `artifact`：物理文件事实。
- `document`：可进入后续知识生产的统一文档与元素。
- `report`：格式、元素数量、locator、清洗动作和 warning。

这使业务结果和诊断结果保持关联，又不会混成一个无约束字典。

### 主调用链怎样推进数据

真实调用链是：

```text
load_document
→ 校验业务身份和来源资格
→ _read_artifact：path 变为 FileArtifact
→ _detect_format：确认受支持容器和基础文件头
→ parse_artifact：选择格式 Parser
→ ParsedElement[] + warning[]
→ clean_text：规范文本并记录 action
→ DocumentElement[]：增加稳定 ID、顺序和来源位置
→ KnowledgeDocument + LoadReport
→ LoadResult
```

这条源码链实现前两层机制，但两者不是按函数一一分开的：

- `_detect_format` 和格式 Parser 共同承担内容识别与解析路由。
- 每个 Parser 同时抽取内容并保存它能可靠获得的原生结构。
- Loader 负责清洗、稳定身份、业务来源约束和统一结果组装。

### 四个 Parser 怎样完成最小结构还原

格式分派位于 [`ingestion/parsers.py`](../../source/packages/rag_core/ingestion/parsers.py)。

TXT Parser 按空行形成连续文本块，在 flush 时记录 `line_start` 和 `line_end`。默认编码是 UTF-8 / UTF-8-SIG；其他编码必须显式指定或在入库前完成可追踪转换，不能靠猜测把错误字节变成看似正常的文字。

Markdown Parser 使用 `markdown-it-py` 生成语法 Token。标题 Token 更新 `heading_path`，段落、列表和代码块保存各自的行号与章节路径。这里使用语法结构，而不是用正则删掉 `#` 后返回一个大字符串。

DOCX Parser 使用 `python-docx` 的 `iter_inner_content()` 按文档顺序读取段落和表格。标题样式更新章节路径，普通段落保存段落序号，表格保存表格序号和单元格文字。它没有根据视觉排版伪造页码。

PDF Parser 使用 `pypdf` 逐页提取文本并保存真实页码。它有三种可观察结果：

```text
页面有文本
→ 产生 PAGE element

部分页面无文本
→ 跳过空页并产生 pdf_page_without_text warning

全部页面无文本
→ 抛出 empty_content / pdf_text_layer_missing
```

只要得到文本，结果还会包含 `pdf_reading_order_not_guaranteed`。warning 表示内容可以继续处理但必须核对；error 表示当前 V0 路线没有产生可继续处理的内容。

### 清洗后再生成稳定元素身份

Loader 根据以下信息生成 `element_id`：

```text
document_id
+ document_version
+ element ordinal
+ locator
+ cleaned text
```

同一文件以相同身份和策略重复加载时，元素 ID 可预测；版本、位置或文本变化时，旧元素和新元素能够区分。它不是数据库自增 ID，也不是后续 Chunk ID。

## 用实验观察识别与结构

共享实现位于 [`rag_core.ingestion`](../../source/packages/rag_core/ingestion/)，最小实验位于 [`rag_ingestion_lab`](../../source/demos/rag_ingestion_lab/)。

在仓库根目录运行正常组：

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py
```

默认终端使用摘要表，只保留四种格式的元素数量、locator 类型、warning 和最终统计，避免大段元素文本淹没格式差异。需要查看每个元素、稳定 ID、完整 locator 和 cleaning actions 时运行：

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py --verbose
```

不要只检查命令是否成功。按下面的问题观察：

1. 四个文件分别选择了哪个格式 Parser？
2. TXT、Markdown、DOCX 和 PDF 分别恢复了哪些元素类型？
3. 为什么它们的元素数量不应完全相同？
4. 每种格式保留了行号、标题路径、段落号、表格号还是页码？
5. PDF 为什么在成功时仍然报告 reading-order warning？
6. `KnowledgeDocument` 为什么还不是 Chunk 或检索索引？

实验材料位于 [`review_assistant/fixtures/v0/ingestion`](../../review_assistant/fixtures/v0/ingestion/)。它们是人为编写的模拟业务内容，但使用真实文件格式并由真实 Parser 处理，不是 Mock Parser 的返回值。

四种正常文件是同一份 canonical facts 的互斥表示。实验每次独立加载一种格式，用来比较不同容器保留的结构和 locator；不能把四份内容同时入库并当成四份独立知识。

完整运行参数、输出字段、代码阅读顺序和修改实验的方法由 [demo README](../../source/demos/rag_ingestion_lab/README.md) 维护。正文负责解释为什么要观察这些变化。

## 真实输入边界与契约测试承担不同证据

需要检查不支持输入和错误契约时运行：

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py --include-failures
```

实验会先展示一个可重复的双栏 PDF 阅读顺序对照：视觉左栏应先读，但 fixture 的 PDF 内容流先记录右栏，抽取结果因此先出现右栏。这是用于隔离 Parser 行为的受控对照，只能证明内容流与视觉阅读顺序可能不一致，不能冒充真实业务文档分布或 V0 产品质量证据。

随后检查一项真实支持边界和三项确定性契约：

| 输入 | 证据性质 | stage | code | 优先判断 |
| --- | --- | --- | --- | --- |
| 无文本层 PDF | 有效输入下的当前支持边界 | `empty_content` | `pdf_text_layer_missing` | 当前文本路线不适用，应评估 OCR/VLM 路线 |
| 损坏 DOCX | 确定性契约测试 | `parse` | `document_parse_failed` | 容器内部 OOXML 无法解析 |
| 非 UTF-8 TXT | 确定性契约测试 | `parse` | `text_decode_failed` | 编码契约不匹配 |
| 无有效内容 Markdown | 确定性契约测试 | `empty_content` | `empty_document` | 文件存在但没有可继续处理的元素 |

manifest 同时冻结 expected stage 和 expected code。任意一项不匹配，或负向样例意外成功，实验都会返回非零退出码，不能用“打印了错误信息”代替错误契约成立。这些结果用于验证应用分层，不证明 Parser 对真实资料的总体质量。

错误类型定义在 [`ingestion/errors.py`](../../source/packages/rag_core/ingestion/errors.py)。建议按数据流定位：

1. `format_detection`：文件是否存在、大小是否超限、扩展名与文件头是否一致？
2. `parse`：编码是否正确、文件是否损坏或加密、解析库是否支持当前结构？
3. `empty_content`：是原文为空、清洗后为空，还是当前路线无法取得文字？
4. warning：结果能否继续使用，但存在哪些页、结构或阅读顺序风险？

无文本层 PDF 的失败不是“PDF 没有结果”，而是一个有行动含义的路由结果：当前文本抽取路线已经证明不适用。由于 V0 没有配置真实 OCR/VLM 服务，系统在这里停止并暴露边界。

## 解析库封装了什么，没有解决什么

`pypdf`、`python-docx` 和 `markdown-it-py` 封装了对应格式的底层读取，但没有替应用解决：

- 应该选择文本抽取、OCR 还是 VLM。
- 哪些结构恢复结果足够可信。
- 文档业务身份、版本和证据资格是什么。
- 清洗能否改变业务语义。
- 元素与原文如何稳定关联。
- 失败如何进入日志、重试、人工处理或产品状态。
- 后续怎样 Chunk、索引、检索和评估。

框架只能提供能力，应用仍要建立路由、数据契约、诊断和业务边界。

## 本节交付与下一层输入

本节真实交付是：

```text
KnowledgeDocument
+ DocumentElement[]
+ SourceLocator
+ LoadReport
```

下一层接收本文结果：

```text
DocumentElement[] → Chunk[] + Parent/Child + Metadata
```

本文只保证后续 Chunking 能获得有序文本元素、最小结构、来源位置、业务身份和加载诊断，不替后续策略决定怎样切片或建立索引。

V0 明确不做：

- 扫描 PDF 的 OCR 产品链路。
- 图片、流程图和截图的 VLM 理解。
- 完整版面结构树和 bounding box。
- Chunk、Embedding、FTS、向量索引和 Retrieval。

这些边界不会阻止本节建立完整心智模型，但不能把未实现设计写成当前能力。

## 判断是否已经掌握

1. 为什么识别 PDF 文件头后仍然不能立即选择文本抽取路线？
2. 原生文本 PDF、扫描 PDF 和图文混排 PDF 分别应该怎样处理？
3. OCR 为什么需要坐标和置信度，而不应只返回大字符串？
4. VLM 适合补充什么信息，为什么不应无记录地覆盖原生文本？
5. 内容抽取和结构还原分别解决什么问题？
6. 当前四种 Parser 分别保留了哪些结构，又明确损失了什么？
7. 原始标题层级和父子 Chunk 为什么不是同一种关系？
8. `load_document` 从文件路径到 `LoadResult` 经历了哪些数据转换？
9. 文本型 PDF 的 warning 与无文本层 PDF 的 error 分别代表什么？

完成后回到 [标准学习路径](../learning-path.md)，由唯一课表决定后续内容。
