# rag_core

需求评审助手的共享 RAG package。课程正文解释机制；本 README 维护代码职责、阅读入口和运行边界。

当前实现标准学习路径 V0 步骤 8 的文档加载、确定性清洗和来源定位，步骤 9 的可回查 Chunking，以及步骤 10 的 Embedding 表示与成对相似度观察。知识库匹配、排名、持久化向量索引和固定 RAG Pipeline 尚未实现，不能从目录名推断它们已经可用。

## 当前数据流

```text
FileArtifact + LoaderConfig
→ format detection
→ TXT / Markdown / DOCX / PDF parser
→ deterministic cleaning
→ KnowledgeDocument + DocumentElement[] + LoadReport
→ ChunkPolicy
→ element / fixed-window / structure-aware / parent-child
→ Chunk[] + ChunkReport
→ embed_texts / pairwise_similarity
→ EmbeddingRecord[] + SimilarityObservation[]
```

## 代码入口

| 文件 | 职责 |
| --- | --- |
| `ingestion/models.py` | 文件、文档、元素、locator、来源角色和加载报告契约 |
| `ingestion/errors.py` | format detection、parse、cleaning、empty content 错误分层 |
| `ingestion/parsers.py` | 四种格式的结构化解析和原生位置保留 |
| `ingestion/cleaning.py` | 可说明、可测试的确定性文本规范化 |
| `ingestion/loader.py` | 文件检查、解析调度、清洗和结果组装 |
| `tests/test_ingestion.py` | 正常格式、稳定身份、来源边界和明确错误契约测试 |
| `chunking/models.py` | Chunk、来源跨度、策略和报告契约 |
| `chunking/tokenization.py` | 固定 tokenizer 下的 token 计数和字符边界切分 |
| `chunking/identity.py` | 根据文档、有效策略和来源跨度生成稳定 Chunk ID |
| `chunking/service.py` | element、fixed、structure-aware 与 parent-child 策略 |
| `tests/test_chunking.py` | 来源回查、父子关系、Metadata 与稳定身份不变量 |
| `embedding/models.py` | EmbeddingRecord、相似度度量与成对观察契约 |
| `tests/test_embedding.py` | 表示顺序、度量方向和 Embedding 空间一致性边界 |

建议按上表顺序阅读。步骤 8–9 运行 [`rag_ingestion_lab`](../../demos/rag_ingestion_lab/)；步骤 10 运行 [`rag_retrieval_lab`](../../demos/rag_retrieval_lab/)。

## 公共入口

```python
from rag_core import EvidenceEligibility, SourceRole, load_document

result = load_document(
    "rules.md",
    document_id="KR-ORDER-STATE",
    document_version="1.0.0",
    source_role=SourceRole.REFERENCE_KNOWLEDGE,
    evidence_eligibility=EvidenceEligibility.CURRENT_EVIDENCE,
)
print(result.document.elements)
print(result.report.warnings)
```

调用者提供稳定的业务 `document_id` 和 `document_version`；Loader 计算物理文件内容哈希。数据库自增 ID 和文件名都不能替代业务身份。

Loader 在读取完整字节前先通过文件状态检查 `max_file_bytes`，避免超限文件已经占用内存后才失败；读取后仍保留一次大小校验以防文件在检查与读取之间变化。

Chunking 公共入口接收完整 `KnowledgeDocument`，不重复接收一份可能与 `document.elements` 不一致的元素列表：

```python
from rag_core import ChunkPolicy, ChunkStrategy, chunk_document

result = chunk_document(
    document,
    ChunkPolicy(
        name="structure_aware",
        version="1.0.0",
        strategy=ChunkStrategy.STRUCTURE_AWARE,
        max_tokens=96,
    ),
)
```

`ChunkSourceSpan` 保存原始 `element_id`、locator 和元素内字符范围。Chunk 可以合并、截取或重复原文，但每个来源片段必须能够回到真实 `DocumentElement`。

`chunk_id` 同时包含文档身份、版本、有效策略 fingerprint、Chunk 类型、文本和来源跨度。同一输入与策略重复运行可预测；内容、版本或有效策略改变后不会复用旧 ID。数据库清理、索引迁移和 Citation 失效属于后续知识治理，不由当前模块执行。

## Embedding 表示边界

真实 Embedding HTTP 调用位于 [`llm_core.LLMClient.embed`](../llm_core/client/service.py)。`rag_core.embedding` 只负责：

- 把文本整理成带 Provider、配置、模型、维度、预处理版本和可选 `text_id` 的 `EmbeddingRecord`
- 在同一 Embedding 空间内计算 cosine / dot / Euclidean
- 产出成对 `SimilarityObservation`

它只做表示记录与成对相似度观察，不对知识库候选做匹配排名，也不持久化向量。当前 Embedding 空间身份由 Provider、配置引用、模型、维度和预处理版本共同表达；任一项变化后不得与旧记录直接比较。

```python
from rag_core import SimilarityMetric, embed_texts, pairwise_similarity

batch = embed_texts(
    ["申请售后", "发起逆向服务", "售前活动规则"],
    text_ids=["synonym_a", "synonym_b", "noise"],
    preprocessing_version="raw-v1",
)
for item in pairwise_similarity(batch.records, metric=SimilarityMetric.COSINE):
    print(item.left_id, item.right_id, round(item.score, 4))
```

## Chunking 策略边界

| 策略 | 当前行为 | 不应推断 |
| --- | --- | --- |
| `element` | 将解析元素作为基线单元，超长元素仍按 token 上限切分 | Element 天然适合检索 |
| `fixed_window` | 在文档文本上按 token 窗口和 overlap 切分 | overlap 能理解业务关系 |
| `structure_aware` | 优先按标题节、元素和表格边界组织，必要时重复标题上下文 | 已恢复 Parser 没有提供的结构 |
| `parent_child` | section 形成 parent，较小 child 作为 retrieval unit | 父子块一定优于普通 Chunk |

当前 token 边界使用显式 `tiktoken` encoding，不在 tokenizer 不可用时静默改成字符估算。具体参数是策略配置和实验输入，不是课程固定答案。

来源事实、业务过滤字段、策略信息和运行诊断分开保存：文档身份、来源角色和证据资格是 Chunk 强类型字段；`knowledge_scope` 等进入 `business_metadata`；token 分布、重复量和来源跨度数量进入 `ChunkReport`。

## 支持边界

| 格式 | 当前保留的位置 | 明确边界 |
| --- | --- | --- |
| TXT | 连续文本块的行范围 | 默认只接受 UTF-8/UTF-8-SIG；其他编码需显式配置或转换 |
| Markdown | 源行范围、标题路径 | 当前解析标题、段落、列表和代码块；不推测渲染后页码 |
| DOCX | 段落序号、表格序号、标题路径 | 不还原复杂浮动布局、图片文字和视觉分页 |
| 文本型 PDF | 页码 | 内容流顺序可能不同于复杂版面的视觉阅读顺序 |
| 扫描 PDF | 不支持 | 返回 `pdf_text_layer_missing`，不静默调用 OCR/VLM |

清洗只规范换行、Unicode、行尾空白、外层空白和过多空行，不删除业务符号、标题、表头或否定条件。

## 错误定位

| stage | 先检查什么 |
| --- | --- |
| `format_detection` | 扩展名、文件头、大小和文件是否存在 |
| `parse` | 编码、文件损坏、加密和格式解析库 |
| `cleaning` | 确定性清洗配置与异常输入 |
| `empty_content` | 空文档、图片页或扫描 PDF 的文本层 |

主路径不返回 fake 文档，也不把失败格式当成空成功结果。

终端颜色、表格、JSON Lines 和日志级别由全仓共享的 [`app_log`](../app_log/) 负责。`rag_core` 只返回领域结果、报告和错误，不直接决定终端布局。
