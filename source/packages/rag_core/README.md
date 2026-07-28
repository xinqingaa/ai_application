# rag_core

需求评审助手的共享 RAG package。课程正文解释机制；本 README 维护代码职责、阅读入口和运行边界。

当前只实现标准学习路径 V0 步骤 8 的文档加载、确定性清洗和来源定位。Chunk、Embedding、Retriever、RRF 和固定 RAG Pipeline 尚未实现，不能从目录名推断它们已经可用。

## 当前数据流

```text
FileArtifact + LoaderConfig
→ format detection
→ TXT / Markdown / DOCX / PDF parser
→ deterministic cleaning
→ KnowledgeDocument + DocumentElement[] + LoadReport
```

## 代码入口

| 文件 | 职责 |
| --- | --- |
| `ingestion/models.py` | 文件、文档、元素、locator、来源角色和加载报告契约 |
| `ingestion/errors.py` | format detection、parse、cleaning、empty content 错误分层 |
| `ingestion/parsers.py` | 四种格式的结构化解析和原生位置保留 |
| `ingestion/cleaning.py` | 可说明、可测试的确定性文本规范化 |
| `ingestion/loader.py` | 文件检查、解析调度、清洗和结果组装 |
| `tests/test_ingestion.py` | 正常格式、稳定身份、来源边界和主动失败测试 |

建议按上表顺序阅读，再运行 [`rag_ingestion_lab`](../../demos/rag_ingestion_lab/)。

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
