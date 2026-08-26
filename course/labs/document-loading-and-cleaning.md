# 真实文档解析与错误边界实验

配套机制：[文档内容识别、解析路由、结构还原与来源保留](../mechanisms/document-loading-and-cleaning.md)。实验使用 `source/apps/review_assistant/fixtures/rag/ingestion/` 中的真实文件格式。

```bash
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py --verbose
uv run python source/demos/rag_ingestion_lab/inspect_ingestion.py --include-failures
```

先预测 TXT、Markdown、DOCX、文本型 PDF 与扫描 PDF 的表现。观察格式识别、元素、locator、warning 和结构化错误，区分“不支持”“文件损坏”和“解析成功但结构丢失”。

读码顺序：`inspect_ingestion.py` → `rag_core/ingestion/loader.py` → parsers、cleaning 与 errors。修改 fixture 后需要时运行 `build_binary_fixtures.py`，再执行 ingestion 测试。
