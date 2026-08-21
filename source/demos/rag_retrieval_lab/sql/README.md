# 第 11 步调试 SQL

这些文件**只用于本地观察** `review_assistant.rag_chunks`，方便对照词面检索实验。它们不是 migration，不会改表结构，也不写入产品代码路径。

在 GUI 里把很长的 `content`、`lexical_text`、`search_vector` 挤在一张宽表里，终端会折成一团。请用这里的脚本，不要把 `SELECT ...` 存成临时文件名。

## 怎么跑

在仓库根目录（已 `source .env`，且 `psql` 在 `PATH` 中）：

```bash
set -a && source .env && set +a

# 先看两行摘要（窄表，终端可读）
psql "$DATABASE_URL" -f source/demos/rag_retrieval_lab/sql/list_chunk_previews.sql

# 再看原文 / 拆词 / 词袋（每列单独一行）
psql "$DATABASE_URL" -f source/demos/rag_retrieval_lab/sql/inspect_rag_chunks.sql
```

Cursor 的 PostgreSQL 插件若仍用宽表预览，改在终端执行上面两条，或在插件查询里只用 `list_chunk_previews.sql` 的 `SELECT`。

## 文件

| 文件 | 用途 |
| --- | --- |
| `list_chunk_previews.sql` | 只列出 `chunk_id` 和单行原文摘要 |
| `inspect_rag_chunks.sql` | 展开显示 `content`、`lexical_text`、`search_vector` |

第 11 步操作顺序见 [实验准备](../docs/11-lexical-retrieval.md)；词面机制见 [课程正文](../../../course/mechanisms/lexical-retrieval.md)。
