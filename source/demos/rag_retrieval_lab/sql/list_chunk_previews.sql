-- 调试用：窄表预览，避免终端折行。不修改数据。
-- \pset pager off
-- \pset format aligned
-- \pset tuples_only off

SELECT
    chunk_id,
    regexp_replace(btrim(content), E'\\s+', ' ', 'g') AS content_preview
FROM review_assistant.rag_chunks
ORDER BY chunk_id;
