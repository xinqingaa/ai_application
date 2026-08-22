-- 调试用：强制展开（每字段一行），对照原文 / 拆词 / 词袋。不修改数据。
-- \pset pager off
-- \x on

SELECT
    chunk_id,
    content,
    lexical_text,
    search_vector
FROM review_assistant.rag_chunks
ORDER BY chunk_id;
