# 06. RAG 生成

> 本节目标：把第五章的检索结果真正接成一个最小可运行的问答闭环，掌握 `RetrievalResult[] -> context formatter -> RAG Prompt -> answer + sources` 这条固定生成路径。

---

## 1. 概述

### 学习目标

- 理解为什么检索结果还需要经过上下文格式化
- 理解 RAG Prompt 和普通聊天 Prompt 的边界差异
- 掌握为什么最小返回结构应该是 `answer + sources`
- 理解为什么“我不知道”必须成为主线能力
- 能独立运行第六章脚本，并看出生成问题和检索问题分别落在哪一层

### 预计学习时间

- 上下文格式化与 Prompt：40-60 分钟
- 答案结构与来源引用：30-45 分钟
- 拒答边界与脚本实验：30-45 分钟

### 本章与前后章节的关系

第五章已经解决：

1. 如何把底层查询收束成稳定 Retriever
2. 如何对比 `similarity / threshold / MMR / metadata filter`
3. 检索失败时应该先从哪里排查

第六章接着解决：

1. 如何把 `RetrievalResult[]` 翻译成模型可读上下文
2. 如何通过 RAG Prompt 固定回答边界
3. 如何返回 `answer + sources`
4. 如何在没有足够依据时显式拒答

第七章会继续建立在这里之上：

1. 对问答链路建立最小评估闭环
2. 区分改动到底改善了检索、生成还是两者都没有改善

### 本章代码入口

本章对应的代码目录是：

- [source/04_rag/06_rag_generation/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/README.md)
- [generation_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/generation_basics.py)
- [01_inspect_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/01_inspect_prompt.py)
- [02_query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/02_query_demo.py)
- [03_refusal_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/03_refusal_demo.py)
- [tests/test_generation.py](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/tests/test_generation.py)

### 本章边界

本章重点解决：

1. `RetrievalResult[]` 的输入契约
2. context formatter
3. RAG Prompt
4. `answer + sources`
5. 无答案处理

本章不要求：

- 接真实模型 SDK
- 设计多提供方抽象
- 进入复杂 Agent 或多工具路由
- 展开完整线上服务工程

为了保持章节独立，本章代码使用一个最小 `DemoRetriever` 和 `MockLLMClient`。

目的不是绕开真实工程，而是避免你为了理解生成环节，又被目录结构、SDK 配置和项目抽象分散注意力。

---

## 2. 本章的输入和输出到底是什么 📌

第六章最重要的一步，是把注意力从“接一个模型”改成“固定一条受控生成链路”。

它的最小数据流应该长这样：

```text
question
-> RetrievalResult[]
-> context formatter
-> RAG Prompt
-> answer + sources
```

这里最关键的是两端：

- 输入不是原始文档，而是检索层已经整理好的 `RetrievalResult[]`
- 输出不是一段随意文本，而是最小可追溯的 `answer + sources`

如果你把这两端弄清楚，第六章就已经学对了一半。

### 2.1 输入为什么不是“文档”

真正送进生成层的，不是整份 PDF，也不是原始文件内容，而是更小、更稳定的一组检索结果：

- chunk 文本
- score
- metadata
- 来源身份

这说明生成层的前提是：

> 检索层已经把候选依据缩小到一批可以被进一步筛选和组织的结果。

所以第六章真正吃的是第五章的输出契约，不是重新做一次检索工程。

### 2.2 输出为什么不能只是“一段答案”

如果最终只返回一段文本，你很快会遇到三个问题：

- 用户无法核对依据
- 你无法判断答对了是不是碰巧
- 第七章开始做评估时很难区分“答对了但引用错了”

所以第六章推荐的最小返回结构是：

```text
answer + sources
```

这不是“为了看起来更完整”，而是因为从这里开始，RAG 系统和普通聊天系统已经有了明显边界。

---

## 3. 为什么检索结果不能直接扔给模型 📌

### 3.1 检索结果还是程序对象，不是模型最适合的输入

第五章的结果通常长这样：

- chunk 内容
- 相似度分数
- filename / source / chunk_index

这对程序很友好，但对模型不够友好。

模型更适合消费的是：

- 有边界的上下文片段
- 清楚的回答任务
- 清楚的引用要求
- 清楚的拒答要求

所以第六章的第一层工作不是“连模型”，而是：

> 把检索结果翻译成受控上下文。

### 3.2 context formatter 的职责不是简单拼字符串

如果只是把几个 chunk 直接拼起来，你会马上遇到几个问题：

- 模型不知道哪些内容来自同一来源
- 用户无法核对答案依据
- 调试时很难知道是哪一段上下文出了问题
- 上下文越来越长，却没有明确边界

所以一个最小可用的 context formatter 至少要负责：

1. 给每个 chunk 一个稳定标签，例如 `[S1]`
2. 保留 `filename / chunk_index / score`
3. 控制进入上下文的 chunk 数量和每段长度
4. 让最终答案和来源能对得上

这也是为什么本章代码里专门保留了 [format_context()](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/generation_basics.py) 这一层。

---

## 4. RAG Prompt 和普通聊天 Prompt 的区别 📌

普通聊天 Prompt 常见的重点是：

- 角色
- 任务
- 风格

RAG Prompt 还必须额外固定三件事：

1. 回答依据从哪里来
2. 如果上下文不够该怎么办
3. 如果用了上下文，答案要怎么标来源

所以第六章不是“再写一个 Prompt”，而是：

> 让模型在受控上下文里回答，而不是自由发挥。

本章的 [RAG_SYSTEM_PROMPT](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/generation_basics.py) 和 [RAG_USER_TEMPLATE](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/generation_basics.py) 固定了三个边界：

- 只能依据当前上下文回答
- 没有依据时直接说“我不知道”
- 使用了上下文就要带 `[S1]` 这样的来源标签

这也是为什么第六章开始，Prompt 不再只是“让模型回答得更像人”，而是“让模型在边界内回答”。

---

## 5. 为什么“我不知道”必须成为主线能力 📌

很多初学者会把拒答看成异常分支，但对 RAG 来说，它其实是主线能力。

因为真实问题里一定会出现：

- 没召回到依据
- 召回结果明显不相关
- 问题超出知识库范围

如果系统在这些情况下仍然勉强回答，只会把弱相关内容包装成看起来合理的答案。

所以第六章应该建立一个更稳的顺序：

```text
retrieved results
-> score filter
-> 没有可接受上下文
-> 直接返回“我不知道”
```

这比“先让模型回答，再希望 Prompt 限制住它”更稳。

本章的 [RagService.ask()](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/generation_basics.py) 就是在做这件事。

---

## 6. 第六章代码是怎么落地的 📌

### 6.1 `generation_basics.py`

这个文件承载了本章全部核心对象：

- `SourceChunk`
- `RetrievalResult`
- `PromptInspection`
- `MockLLMClient`
- `RagService`

同时也放了本章所有核心动作：

- `format_context()`
- `build_messages()`
- `filter_retrieval_results()`
- `inspect_prompt()`

这样做的目的只有一个：

> 让你在一个文件里就能看清“输入结果 -> Prompt -> 输出答案”的完整路径。

### 6.2 `01_inspect_prompt.py`

这个脚本不负责给答案，它只负责帮你看清：

- 原始检索结果是什么
- 哪些结果通过了 `min_score`
- 最终进入 Prompt 的上下文长什么样

所以它是本章最重要的调试入口。

如果你跳过这一步，直接看最终答案，很容易把问题都误判成“模型没答好”。

### 6.3 `02_query_demo.py`

这个脚本负责跑最小问答闭环：

```text
question
-> retrieve
-> filter
-> prompt
-> mock generate
-> answer + sources
```

它的重点不是炫耀“已经能回答问题”，而是让你看到：

- 哪些结果真的进入了生成环节
- 最终答案里的来源标签和 `sources` 是否一致
- 拒答是发生在生成前，还是生成后

### 6.4 `03_refusal_demo.py`

这个脚本的价值在于把两类问题摆在一起看：

- 有依据的问题
- 没依据的问题

只有把这两类问题放在同一个演示里，你才会真正感受到：

> RAG 的稳定，不是“总能回答”，而是“该答时答，不该答时停”。

---

## 7. 学这一章时应该重点观察什么 📌

建议按这个顺序观察：

1. 原始 `RetrievalResult[]` 长什么样
2. 哪些结果因为分数太低被挡在上下文外
3. 进入上下文的结果是否有稳定标签 `[S1] / [S2]`
4. Prompt 是否明确写了“只能依据上下文回答”
5. 最终答案是否带来源标签
6. 无答案问题是否真的直接拒答

你应该刻意区分两类错误：

- 检索错误：根本没有正确依据，或者正确依据分数太低
- 生成错误：依据已经有了，但 Prompt 或回答组织方式有问题

第六章最大的学习价值，就是把这两类错误拆开。

---

## 8. 建议学习顺序

1. 先读 [source/04_rag/06_rag_generation/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/06_rag_generation/README.md)
2. 跑 `python 01_inspect_prompt.py`
3. 跑 `python 02_query_demo.py`
4. 跑 `python 03_refusal_demo.py`
5. 最后跑 `python -m unittest discover -s tests`

推荐你至少主动改两处参数：

- `min_source_score`
- `max_chars_per_chunk`

这样你会很直观地看到：

- 过滤太严会不会让系统更容易拒答
- 上下文太长或太短会不会影响最终答案形态

---

## 9. 学完这一章后你应该能回答

- 为什么 `RetrievalResult[]` 还不能直接等于模型输入
- 为什么 context formatter 是生成链路里的独立职责
- 为什么 RAG Prompt 必须固定回答边界
- 为什么最小结果应该是 `answer + sources`
- 为什么“我不知道”必须被当成正确输出之一

---

## 10. 小结

第六章真正教你的，不是“接了一个模型”。

它教的是：

- 检索结果如何变成模型可读上下文
- 回答边界如何被 Prompt 固定下来
- 为什么答案和来源必须一起返回
- 为什么拒答能力要在链路里被明确设计

从这里开始，RAG 才第一次真正从“检索实验”变成“问答系统”。
