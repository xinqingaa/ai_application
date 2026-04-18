# PHASE_CARD

## Phase

- 名称：`phase_2_document_processing`
- 对应章节：[02_document_processing.md](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md)

## 本章目标

- 让文件真正进入系统
- 把文本稳定整理成 `SourceChunk[]`
- 固定 metadata 和 stable id

## 上一章输入契约

- 第一章已定义 `SourceChunk`
- 第一章已定义 `ingestion / indexing` 目录位

## 输出契约

- `SourceChunk[]`
- `document_id`
- `chunk_id`
- `base metadata + chunk metadata`

## 本章新增

- 真实 `.md / .txt` 加载
- `discover_documents()`
- `normalize_text()`
- `TextChunk`
- 更完整的 metadata
- 稳定 ID 规则
- 文档处理测试

## 本章关键文件

- `app/ingestion/loaders.py`
- `app/ingestion/splitters.py`
- `app/ingestion/metadata.py`
- `app/indexing/id_generator.py`
- `app/indexing/index_manager.py`

## 第一命令

```bash
python3 scripts/build_index.py
```

## 建议阅读顺序

1. `data/product_overview.md`
2. `data/faq.txt`
3. `app/config.py`
4. `app/ingestion/loaders.py`
5. `app/ingestion/splitters.py`
6. `app/indexing/index_manager.py`

## 完成标准

- 能解释 `loader / splitter / metadata / stable id` 各自职责
- 能说明为什么 `SourceChunk[]` 是第三章的真实输入
- 能看懂 `chunk_id` 和字符范围

## 下一章

- 在 `SourceChunk[]` 外再加一层向量表示
- 引入 `EmbeddingProvider`
- 产出 `EmbeddedChunk[]`
