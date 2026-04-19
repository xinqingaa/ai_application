# 06. RAG 生成 - 实践指南

> 本文档说明如何跟着 [学习文档](/Users/linruiqiang/work/ai_application/docs/04_rag/06_rag_generation.md) 学完第六章，并在不依赖第七章以后的前提下，看懂检索结果如何被组织成上下文、Prompt、答案和来源。

---

## 核心原则

```text
先看检索结果长什么样 -> 再看这些结果如何被格式化成上下文 -> 最后看答案、来源和拒答怎么一起返回
```

- 在 `source/04_rag/06_rag_generation/` 目录下操作
- 本章只讲生成闭环，不重新展开检索策略
- 为了保持章节独立，代码自带一个最小 `DemoRetriever` 和 `MockLLMClient`
- 本章重点不是接真实 SDK，而是把回答边界固定下来
- 旧的 `labs/phase_6_rag_generation/` 只作为迁移期备份，不再是当前学习入口

---

## 项目结构

```text
06_rag_generation/
├── README.md
├── generation_basics.py
├── 01_inspect_prompt.py
├── 02_query_demo.py
├── 03_refusal_demo.py
└── tests/
    └── test_generation.py
```

- `generation_basics.py`
  放本章所有最小对象、样例检索结果、上下文格式化、Prompt、mock 生成器和 `RagService`
- `01_inspect_prompt.py`
  看检索结果如何变成最终 Prompt
- `02_query_demo.py`
  跑一次完整的 `question -> answer + sources`
- `03_refusal_demo.py`
  对比“可回答”和“应拒答”两类问题

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/06_rag_generation
```

### 2. 当前命令

```bash
python 01_inspect_prompt.py
python 01_inspect_prompt.py "为什么回答里要带来源标签？"
python 02_query_demo.py
python 02_query_demo.py "火星首都是什么？"
python 03_refusal_demo.py
python -m unittest discover -s tests
```

### 3. 先跑哪个

建议先跑：

```bash
python 01_inspect_prompt.py
```

你现在最该先建立的直觉是：

- 检索结果不是直接塞给模型，而是先要被翻译成上下文
- 第六章的最小输出不是一段文本，而是 `answer + sources`
- “我不知道”是主线能力，不是兜底异常

---

## 第 1 步：先看输入和输出契约

**对应文件**：[generation_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/generation_basics.py)

重点观察：

- 输入为什么是稳定 `RetrievalResult[]`
- 输出为什么是稳定 `AnswerResult`
- `RagService.ask()` 为什么要先过滤、再生成、再返回来源

---

## 第 2 步：看检索结果如何变成上下文

**对应文件**：[generation_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/generation_basics.py)、[01_inspect_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/01_inspect_prompt.py)

重点观察：

- `format_context()` 如何生成 `[S1] / [S2]`
- 为什么 `filename / chunk_index / score` 要显式保留
- 为什么 `max_chunks / max_chars_per_chunk` 是上下文边界，不是细节参数

---

## 第 3 步：看 Prompt 如何固定回答边界

**对应文件**：[generation_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/generation_basics.py)

重点观察：

- `RAG_SYSTEM_PROMPT`
- `RAG_USER_TEMPLATE`
- `build_messages()`

你要明确看到三件事：

1. 模型只能依据当前上下文回答
2. 没有依据时必须明确说“我不知道”
3. 使用了上下文就要带来源标签

---

## 第 4 步：看最小生成器如何返回答案和来源

**对应文件**：[generation_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/generation_basics.py)、[02_query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/02_query_demo.py)

重点观察：

- `MockLLMClient.generate()`
- `_build_mock_answer()`
- `RagService.ask()`

运行后重点看：

- 回答里是否出现 `[S1]`
- `sources` 是否和进入 Prompt 的 chunk 对齐
- 低分结果是否在生成前就被过滤掉

---

## 第 5 步：看拒答为什么必须先于生成

**对应文件**：[03_refusal_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/03_refusal_demo.py)、[tests/test_generation.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/tests/test_generation.py)

重点观察：

- `min_source_score` 如何控制“哪些检索结果值得进入上下文”
- 为什么“火星首都是什么？”应该直接返回拒答
- 为什么比起“先生成再限制”，先过滤上下文更稳

---

## 建议学习顺序

1. 先读 [06_rag_generation.md](/Users/linruiqiang/work/ai_application/docs/04_rag/06_rag_generation.md)
2. 再跑 `python 01_inspect_prompt.py`
3. 再跑 `python 02_query_demo.py`
4. 最后跑 `python 03_refusal_demo.py`

---

## 学完这一章后你应该能回答

- 为什么 `RetrievalResult[]` 还不能直接等于模型输入
- 为什么 RAG Prompt 和普通聊天 Prompt 的边界不同
- 为什么一个稳的最小返回结构应该是 `answer + sources`
- 为什么“我不知道”必须成为默认能力的一部分

---

## 当前真实进度和下一章

- 当前真实进度：第六章已经改成独立学习单元
- 完成标准：能解释上下文格式化、Prompt、答案引用和拒答边界
- 下一章：继续做效果评估，判断一次改动到底改善了检索、生成还是两者都没有改善
