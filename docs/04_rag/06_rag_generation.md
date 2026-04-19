# 06. RAG 生成

> 本节目标：把第五章稳定的 `RetrievalResult[]` 真正接成一个最小可运行的问答闭环，掌握 `retriever candidates -> context selection -> context formatter -> RAG Prompt -> answer + sources` 这条固定生成路径。

---

## 1. 概述

### 学习目标

- 理解为什么第六章的输入应该是第五章产出的稳定 `RetrievalResult[]`
- 理解为什么生成前还要再做一次 context selection，而不是把全部召回结果直接塞进 Prompt
- 掌握 `answer + sources` 为什么是 RAG 系统的最小返回结构
- 理解为什么“我不知道”必须在生成链路里被显式设计
- 能独立运行第六章脚本，并区分问题究竟出在检索候选、上下文筛选还是生成组织

### 预计学习时间

- 输入输出契约与章节连续性：30-40 分钟
- context selection 与 formatter：40-60 分钟
- Prompt、引用与拒答边界：40-60 分钟

### 本章在 RAG 工程中的重要性

| 场景 | 第六章先解决什么 |
|------|------------------|
| 检索已经有结果 | 哪些结果真的值得进入 Prompt |
| 结果太多太杂 | 为什么需要 context selection 和 `max_chunks` |
| 回答需要可追溯 | 为什么返回值必须是 `answer + sources` |
| 无答案问题 | 为什么拒答应该发生在生成前 |
| 调参定位 | 如何拆开“检索候选问题”和“生成组织问题” |

### 本章与前后章节的关系

第五章已经解决：

1. 如何把底层查询收束成稳定 Retriever
2. 如何让 Retriever 输出统一的 `RetrievalResult[]`
3. 如何比较 `similarity / threshold / MMR / filename filter`
4. 检索失败时应该先从哪里排查

第六章接着解决：

1. 如何从 `RetrievalResult[]` 里挑出适合进入 Prompt 的上下文
2. 如何把这些结果格式化成模型可读上下文
3. 如何通过 RAG Prompt 固定回答边界
4. 如何返回真正可追溯的 `answer + sources`

第七章会继续建立在这里之上：

1. 对问答链路建立最小评估闭环
2. 判断一次改动到底改善了检索、生成还是两者都没有改善

### 第六章与第五章的连续性

第六章不应该重新定义一套新的 `SourceChunk / RetrievalResult / Retriever` 数据模型。

当前代码改成了下面这条连续路径：

```text
chapter 4 SourceChunk / metadata / store
-> chapter 5 SimpleRetriever / RetrievalResult[]
-> chapter 6 context selection / prompt / answer + sources
```

也就是说，第六章真正新增的是：

- `min_context_score`
- `max_chunks`
- `format_context()`
- `build_messages()`
- `RagService.ask()`

而不是再次重写：

- `SourceChunk`
- `RetrievalResult`
- 向量 store
- 检索基础接口

需要注意一件事：

> 第六章会保留自己的教学语料，但它底层仍然复用第五章的 Retriever 契约和第四章的 metadata 契约。

### 本章代码入口

本章对应的代码目录是：

- [../../source/04_rag/06_rag_generation/README.md](../../source/04_rag/06_rag_generation/README.md)
- [../../source/04_rag/06_rag_generation/generation_basics.py](../../source/04_rag/06_rag_generation/generation_basics.py)
- [../../source/04_rag/06_rag_generation/01_inspect_prompt.py](../../source/04_rag/06_rag_generation/01_inspect_prompt.py)
- [../../source/04_rag/06_rag_generation/02_query_demo.py](../../source/04_rag/06_rag_generation/02_query_demo.py)
- [../../source/04_rag/06_rag_generation/03_refusal_demo.py](../../source/04_rag/06_rag_generation/03_refusal_demo.py)
- [../../source/04_rag/06_rag_generation/tests/test_generation.py](../../source/04_rag/06_rag_generation/tests/test_generation.py)

### 本章边界

本章重点解决：

1. `RetrievalResult[]` 的输入契约
2. context selection
3. context formatter
4. RAG Prompt
5. `answer + sources`
6. 无答案处理

本章不要求：

- 接真实模型 SDK
- 设计多提供方抽象
- 展开完整线上服务工程
- 进入复杂 Agent 或多工具路由

这一章的核心目标不是“把模型接起来”，而是把下面这条生成主线固定住：

> 第六章解决的是“哪些检索结果值得进入回答”，不是“重新做一遍检索工程”。

---

## 2. 本章的输入和输出到底是什么 📌

第六章最重要的一步，是把注意力从“接一个模型”改成“固定一条受控生成链路”。

它的最小数据流应该长这样：

```text
question
-> RetrievalResult[] candidates
-> context selection
-> formatted context
-> RAG Prompt
-> answer + sources
```

这里最关键的是两端：

- 输入不是原始文档，而是第五章已经整理好的 `RetrievalResult[]`
- 输出不是一段随意文本，而是最小可追溯的 `answer + sources`

### 2.1 输入为什么不是“文档”

真正送进生成层的，不是整份 PDF，也不是原始文件内容，而是更小、更稳定的一组检索结果：

- chunk 文本
- 检索分数
- stable chunk 身份
- richer metadata

这说明生成层的前提是：

> 检索层已经把候选依据缩小到一批可以继续筛选和组织的结果。

所以第六章真正吃的是第五章的输出契约，不是重新做一次检索。

### 2.2 输出为什么不能只是“一段答案”

如果最终只返回一段文本，你很快会遇到三个问题：

- 用户无法核对依据
- 你无法判断答对是不是碰巧
- 第七章开始做评估时很难区分“答对了但引用错了”

所以第六章推荐的最小返回结构是：

```text
answer + sources
```

### 2.3 为什么 `sources` 不能只是“所有召回结果”

这也是本章一个很关键的边界。

真正应该返回的 `sources`，至少要和下面两件事对齐：

1. 真正进入 Prompt 的上下文
2. 最终答案里实际使用的来源标签

如果 `sources` 只是把所有低质量候选都原样返回，你会失去引用链路的可解释性。

---

## 3. 为什么检索结果还要过一次 context selection 📌

### 3.1 Retriever 候选池不等于 Prompt 上下文

第五章解决的是：

- 从 store 里召回候选
- 返回稳定 `RetrievalResult[]`

第六章还要额外解决：

- 候选里哪些结果值得进 Prompt
- 候选过多时先裁掉谁
- 无答案时在哪里停下来

所以当前第六章的最小链路是：

```text
chapter 5 retriever candidates
-> chapter 6 min_context_score filter
-> chapter 6 max_chunks cap
-> formatted context
```

这一步的意义非常大，因为它把“检索能查到一些东西”和“这些东西真的值得成为回答依据”拆开了。

### 3.2 `min_context_score` 在解决什么问题

当前实现会对 Retriever 返回的候选再做一次问题相关性筛选。

它的职责不是替代第五章的 Retriever，而是：

- 在进入 Prompt 之前挡掉弱相关上下文
- 让“我不知道”可以在生成前发生
- 让第六章可以更清楚地演示 context selection 的存在价值

你可以把它理解成：

> 第五章负责“把候选找出来”，第六章负责“把候选收缩成可回答上下文”。

### 3.3 `max_chunks` 为什么不是小参数

就算已经有一批可接受结果，也不代表应该全部塞进 Prompt。

`max_chunks` 解决的是：

- 控制上下文长度
- 控制引用标签数量
- 保证 `sources` 和实际回答更容易对齐

这也是为什么现在要明确区分三类结果：

1. `retrieved_results`
2. `accepted_results`
3. `prompt_results`

---

## 4. context formatter 到底在做什么 📌

很多初学者会把 formatter 理解成“把字符串拼起来”，但这不够。

一个最小可用的 context formatter 至少要负责：

1. 给每个 prompt chunk 一个稳定标签，例如 `[S1]`
2. 显式保留 `filename / chunk_index`
3. 让调试时能看到 `retrieval_score / context_score`
4. 控制每段内容长度
5. 让最终答案和 `sources` 能对得上

当前代码里的 [format_context()](../../source/04_rag/06_rag_generation/generation_basics.py) 正在做这件事。

---

## 5. RAG Prompt 和普通聊天 Prompt 的区别 📌

普通聊天 Prompt 常见的重点是：

- 角色
- 任务
- 风格

RAG Prompt 还必须额外固定三件事：

1. 回答依据从哪里来
2. 如果上下文不够该怎么办
3. 如果用了上下文，答案要怎么标来源

当前本章的 [RAG_SYSTEM_PROMPT](../../source/04_rag/06_rag_generation/generation_basics.py) 和 [RAG_USER_TEMPLATE](../../source/04_rag/06_rag_generation/generation_basics.py) 固定了三个边界：

- 只能依据当前上下文回答
- 没有依据时直接说“我不知道”
- 使用了上下文就要带 `[S1]` 这样的来源标签

从这里开始，Prompt 的任务不再只是“让模型说得更像人”，而是“让模型在边界里说话”。

---

## 6. 为什么“我不知道”必须成为主线能力 📌

很多初学者会把拒答看成异常分支，但对 RAG 来说，它其实是主线能力。

因为真实问题里一定会出现：

- 没有召回到真正相关的依据
- 候选结果虽然有分数，但仍然不值得进 Prompt
- 问题超出知识库范围

所以当前更稳的顺序应该是：

```text
retrieved results
-> context selection
-> no acceptable context
-> 直接返回“我不知道”
```

这比“先让模型回答，再希望 Prompt 限制住它”更稳。

本章的 [RagService.ask()](../../source/04_rag/06_rag_generation/generation_basics.py) 就是在做这件事。

---

## 7. 第六章代码是怎么落地的 📌

### 7.1 `generation_basics.py`

这个文件承载了本章全部核心对象：

- `Chapter5DemoRetriever`
- `PromptInspection`
- `MockLLMClient`
- `RagService`

同时也放了本章所有核心动作：

- `build_generation_demo_store()`
- `filter_retrieval_results()`
- `format_context()`
- `build_messages()`
- `inspect_prompt()`

这里最重要的变化是：

> 第六章不再自己重写 `SourceChunk / RetrievalResult`，而是直接复用第五章链路和第四章 metadata。

### 7.2 `01_inspect_prompt.py`

这个脚本不负责给答案，它只负责帮你看清：

- Retriever 实际召回了什么候选
- 每个候选的 `retrieval_score / context_score`
- 哪些结果真的通过了 `min_context_score`
- 哪些结果最终进入了 Prompt

所以它是本章最重要的调试入口。

### 7.3 `02_query_demo.py`

这个脚本负责跑最小问答闭环：

```text
question
-> retrieve candidates
-> context selection
-> prompt
-> mock generate
-> answer + sources
```

它的重点不是炫耀“已经能回答问题”，而是让你看到：

- 哪些结果真的进入了生成环节
- 最终答案里的来源标签和 `sources` 是否一致
- `sources` 是否只返回实际使用到的来源

### 7.4 `03_refusal_demo.py`

这个脚本把两类问题放在一起看：

- 有依据的问题
- 没依据的问题

只有把这两类问题摆在一起，你才会真正感受到：

> RAG 的稳定，不是“总能回答”，而是“该答时答，不该答时停”。

---

## 8. 学这一章时应该重点观察什么 📌

建议按这个顺序观察：

1. 原始 `RetrievalResult[]` 长什么样
2. 哪些结果因为 `min_context_score` 太低被挡在上下文外
3. 进入 Prompt 的结果是否有稳定标签 `[S1] / [S2]`
4. Prompt 是否明确写了“只能依据上下文回答”
5. 最终答案是否带来源标签
6. 最终 `sources` 是否和答案中的来源标签一致
7. 无答案问题是否真的直接拒答

你应该刻意区分三类错误：

- 检索候选错误：第五章根本没把对的候选找出来
- 上下文筛选错误：候选有了，但第六章没挑对
- 生成组织错误：上下文已经对了，但 Prompt 或答案组织方式有问题

这就是第六章最大的学习价值。

---

## 9. 建议学习顺序

1. 先读 [../../source/04_rag/06_rag_generation/README.md](../../source/04_rag/06_rag_generation/README.md)
2. 跑 `python 01_inspect_prompt.py`
3. 跑 `python 02_query_demo.py`
4. 跑 `python 03_refusal_demo.py`
5. 最后跑 `python -m unittest discover -s tests`

推荐你至少主动改三处参数：

- `top_k`
- `min_context_score`
- `max_chunks`

这样你会很直观地看到：

- 候选拉多了不等于真的都该进 Prompt
- 过滤太严会不会让系统更容易拒答
- Prompt 只吃前几个 chunk 时，`sources` 应该怎么对齐

---

## 10. 学完这一章后你应该能回答

- 为什么第五章的 `RetrievalResult[]` 还不能直接等于模型输入
- 为什么第六章必须显式增加 context selection
- 为什么 context formatter 是生成链路里的独立职责
- 为什么最小结果应该是 `answer + sources`
- 为什么“我不知道”必须被当成正确输出之一

---

## 11. 小结

第六章真正教你的，不是“接了一个模型”。

它教的是：

- 第五章的候选结果如何继续收缩成可回答上下文
- 回答边界如何被 Prompt 固定下来
- 为什么答案和来源必须一起返回
- 为什么拒答能力要在链路里被明确设计

从这里开始，RAG 才第一次真正从“检索实验”变成“问答系统”。
