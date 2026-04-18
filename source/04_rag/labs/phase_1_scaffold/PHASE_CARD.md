# PHASE_CARD

## Phase

- 名称：`phase_1_scaffold`
- 对应章节：[01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)

## 本章目标

- 建立项目骨架
- 固定核心对象
- 露出最小 RAG 链路形状

## 输入契约

- 无上一章输入
- 当前只使用最小样例文本和占位链路

## 输出契约

- `SourceChunk`
- `RetrievalResult`
- `AnswerResult`
- 最小 `retriever -> prompt -> answer` 链路

## 本章新增

- `app/config.py`
- `app/schemas.py`
- `app/retrievers/base.py`
- `app/prompts/rag_prompt.py`
- `app/chains/rag_chain.py`
- `app/services/rag_service.py`
- `scripts/query_demo.py`
- `tests/test_scaffold.py`

## 本章可忽略

- `embeddings/` 真实实现
- `vectorstores/` 真实实现
- 真实 LLM 调用

## 第一命令

```bash
python3 scripts/query_demo.py
```

## 建议阅读顺序

1. `app/config.py`
2. `app/schemas.py`
3. `app/indexing/index_manager.py`
4. `app/prompts/rag_prompt.py`
5. `app/chains/rag_chain.py`
6. `app/services/rag_service.py`

## 完成标准

- 能解释为什么第一章先做骨架
- 能说明三个核心对象的职责
- 能看懂最小链路已经长出什么

## 下一章

- 把样例输入替换成真实 `.md / .txt` 文档
- 把 `SourceChunk[]` 生产链路做成真实实现
