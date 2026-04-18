# 06. RAG 生成

> 本节目标：把前五章的文档处理、向量化、向量库和检索策略真正接成一个最小可运行的问答链路，掌握 `context formatter -> RAG Prompt -> LLM -> answer + sources` 这条固定生成路径。

---

## 1. 概述

### 学习目标

- 理解为什么检索结果还需要经过上下文组织和 Prompt 设计
- 理解 RAG Prompt 和普通聊天 Prompt 的边界差异
- 掌握为什么最小返回结构应该是 `answer + sources`
- 理解为什么“我不知道”必须成为主线能力
- 能对着第六章代码快照看清生成问题和检索问题分别落在哪一层

### 预计学习时间

- context formatter 与 Prompt 设计：1 小时
- 生成客户端与服务链路：1 小时
- 引用和拒答边界：45 分钟
- 第六章代码快照阅读：1-1.5 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|------|---------|
| 文档问答 | context formatter、RAG Prompt |
| 引用回答 | `answer + sources` |
| 无答案处理 | 阈值、拒答、保守边界 |
| 线上服务链路 | `Retriever -> Prompt -> LLM -> Result` |
| 效果诊断 | 区分检索问题和生成问题 |

> **第六章是“检索系统”第一次真正变成“问答系统”的地方。**

### 本章与前后章节的关系

第五章已经解决：

1. 如何把 Chroma 查询收束成稳定 Retriever
2. 如何对比 `similarity / threshold / MMR / metadata filter`
3. 检索失败时应该先从哪里排查

第六章接着解决：

1. 如何把 `RetrievalResult[]` 翻译成模型可读上下文
2. 如何通过 RAG Prompt 把回答边界固定下来
3. 如何返回 `answer + sources`
4. 如何在没有足够依据时显式拒答

第七章会继续建立在这里之上：

1. 对问答链路建立最小评估闭环
2. 区分改动到底改善了检索、生成还是两者都没有改善

### 本章的学习边界

本章重点解决：

1. context formatter
2. RAG Prompt
3. 固定 RAG Chain
4. `answer + sources`
5. 无答案处理
6. 生成侧最小抽象

本章不系统展开：

- Golden Set 自动评估
- Rerank、HyDE、混合检索
- Agent loop
- 多工具动态决策
- 完整 API / 前后端交互系统

### 当前代码快照

本章对应的代码快照是：

- [phase_6_rag_generation/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/README.md)
- [app/prompts/rag_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/prompts/rag_prompt.py)
- [app/chains/rag_chain.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/chains/rag_chain.py)
- [app/llms/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/llms/providers.py)
- [app/services/rag_service.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/services/rag_service.py)
- [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/scripts/query_demo.py)
- [scripts/inspect_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/scripts/inspect_prompt.py)
- [tests/test_generation.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/tests/test_generation.py)

---

## 2. 为什么检索结果不能直接扔给模型 📌

### 2.1 检索结果本身还是程序对象

第五章拿到的通常还是结构化检索结果：

- chunk 文本
- 相似度分数
- metadata
- 来源身份

这还不是模型天然最适合消费的输入形式。

模型更适合的通常是：

- 明确格式化过的上下文片段
- 明确的回答任务
- 明确的引用约束
- 明确的拒答边界

所以第六章要新增的第一层能力，不是“模型接进来”，而是：

> 把检索对象翻译成受控上下文。

### 2.2 RAG Prompt 和普通聊天 Prompt 的区别

普通聊天 Prompt 的重点通常是：

- 角色
- 任务
- 风格

RAG Prompt 还必须额外回答：

1. 上下文从哪里来
2. 是否必须优先依据上下文回答
3. 如果上下文不够该怎么办
4. 来源要不要返回、怎么标

所以第六章的核心不是“再写一个 Prompt”，而是：

> 让模型在受控上下文里回答，而不是自由发挥。

### 2.3 为什么 context formatter 不是简单拼字符串

如果只是把多个 chunk 粘起来，你很快会遇到几个问题：

- 模型不知道哪些内容来自同一来源
- 用户无法核对答案依据
- 调试时很难知道是哪一段上下文出了问题
- 上下文越来越长，却没有长度边界

所以第六章里的 context formatter 至少要负责：

1. 给每个 chunk 一个稳定可见标签，例如 `[S1]`
2. 保留 `filename / chunk_index / score`
3. 控制进入上下文的 chunk 数量和每个 chunk 的长度
4. 让后面的答案和来源能对得上

---

## 3. 第六章要解决的几个关键问题 📌

### 3.1 context formatter

context formatter 负责的是：

- 把检索结果拼成清晰文本
- 保留最小可追溯 metadata
- 控制进入 Prompt 的上下文长度
- 让来源标签和最终答案能对应起来

它不是简单字符串拼接，而是：

> 检索层和生成层之间的翻译器。

### 3.2 RAG Prompt

一个稳的 RAG Prompt 至少要固定三件事：

1. 只能依据当前上下文回答
2. 没有依据时要显式回答“我不知道”
3. 有依据时要标来源标签

第六章当前的 [app/prompts/rag_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/prompts/rag_prompt.py) 正在锁这三个边界。

### 3.3 来源引用

很多业务场景里，最终返回值不能只有答案。

还需要：

- 引用来源
- 帮助用户复核
- 帮助后续调试
- 帮助后面评估“答对了，但引用错了”这类问题

所以一个更稳的返回结构通常不是：

```text
"一段答案"
```

而是：

```text
answer + sources
```

### 3.4 无答案处理

RAG 系统不是“永远给个答案”。

真正稳的系统还要能处理：

- 没召回到依据
- 召回结果明显不相关
- 问题超出知识库范围

第六章当前实现把这一层放在生成前：

```text
retrieved results
-> min_source_score 过滤
-> 没有可接受上下文
-> 直接返回“我不知道”
```

这比“先让模型乱答，再靠 Prompt 勉强限制”要稳得多。

### 3.5 固定 RAG Chain 的边界

第六章默认做的是固定 RAG Chain：

```text
question
-> retriever
-> context formatter
-> prompt
-> llm
-> answer + sources
```

它的价值在于：

- 数据流稳定
- 易于调试
- 易于测试
- 易于评估
- 容易分清问题到底在检索还是在生成

这也是为什么本课程把复杂动态决策留到 Agent 阶段，而不是在这里提前混进来。

---

## 4. 第六章当前代码是怎么落地的 📌

### 4.1 `rag_chain.py` 负责把检索结果翻译成消息

[app/chains/rag_chain.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/chains/rag_chain.py) 当前做了三件关键事：

1. `format_context()`
   把检索结果渲染成 `[S1] filename=... chunk=... score=...` 的上下文块
2. `_truncate_content()`
   限制单个 chunk 进入 Prompt 的字符数
3. `build_messages()`
   输出固定 `system + user` 两段消息

这说明第六章不是把 Prompt 写在脚本里，而是把“如何组织上下文”收束成一层可单独调试的链路。

### 4.2 `providers.py` 负责把真实模型调用和 mock 路径统一

[app/llms/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/llms/providers.py) 当前不是直接把 OpenAI SDK 调用塞进服务层，而是先建立：

- `GenerationProviderConfig`
- `GenerationResult`
- `LLMClient`
- `OpenAICompatibleLLMClient`
- `MockLLMClient`

这样做的好处是：

1. 没有 API Key 时课程仍可完整运行
2. 切换到真实模型时，服务层不用改
3. 后面如果引入更多 provider，当前服务接口可以保持稳定

### 4.3 `RagService.ask()` 负责固定问答路径

[app/services/rag_service.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/services/rag_service.py) 当前流程是：

```text
retrieve(question)
-> filter_retrieval_results(min_source_score)
-> build_messages()
-> llm.generate()
-> AnswerResult(answer, sources)
```

这里最重要的不是“调用模型成功”，而是三件事：

1. `min_source_score` 在生成前先做边界控制
2. 最终固定返回 `answer + sources`
3. 保留 `last_messages / last_generation_result / last_retrieval_results` 方便调试

### 4.4 第六章当前的拒答阈值为什么是 `0.60`

这一章当前课程数据里，相关问题的高分结果大约落在 `0.71-0.78`，明显越界的问题大约在 `0.56` 左右。

所以当前代码把 `default_generation_min_score` 先设成 `0.60`，它的意义是：

- 作为课程样例的起步基线
- 让“明显越界”的问题更容易直接拒答
- 不是通用最佳值，只是当前数据上的合理起点

这一点很重要，因为你需要建立的不是“背住 0.60”，而是：

> 拒答阈值要由当前语料和实验结果驱动，而不是拍脑袋。

### 4.5 `query_demo.py` 和 `inspect_prompt.py` 分别解决什么

[scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/scripts/query_demo.py) 现在负责：

- 跑完整问答链路
- 切换检索策略
- 切换 mock / openai-compatible 生成路径
- 打印最终答案和来源

[scripts/inspect_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/scripts/inspect_prompt.py) 现在负责：

- 先看原始召回结果
- 再看哪些 chunk 真正进入上下文
- 最后直接打印消息内容

这两个脚本分开非常重要，因为很多第六章问题不是“答案不好”，而是：

- 上下文进错了
- 进得太多
- 进得太少
- 引用标签和 chunk 对不上

---

## 5. 回答效果不好时应该先看什么 📌

第六章建议建立这个排查顺序：

1. similarity 基线里是否有正确来源
2. `min_source_score` 是否过松或过严
3. Prompt 里是否明确要求“只能依据上下文回答”
4. 上下文里是否保留了足够 metadata 让来源可以对齐
5. 单个 chunk 是否被截断得过短
6. 最后才看模型本身是否需要替换

也就是说，第六章开始你要形成一个很重要的习惯：

> 先看上下文和 Prompt，再看最终答案。

这也是为什么本章额外补了 [scripts/inspect_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/scripts/inspect_prompt.py)。

---

## 6. 第六章应该怎么学

### 6.1 推荐顺序

建议按这个顺序进入：

1. 先看 [app/prompts/rag_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/prompts/rag_prompt.py)
2. 再看 [app/chains/rag_chain.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/chains/rag_chain.py)
3. 再看 [app/llms/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/llms/providers.py)
4. 再看 [app/services/rag_service.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/services/rag_service.py)
5. 再跑 [scripts/inspect_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/scripts/inspect_prompt.py)
6. 最后跑 [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/scripts/query_demo.py) 和 [tests/test_generation.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/tests/test_generation.py)

### 6.2 建议先跑的命令

```bash
cd source/04_rag/labs/phase_6_rag_generation
python scripts/query_demo.py
python scripts/inspect_prompt.py
python scripts/query_demo.py "What is the capital of Mars?" --strategy threshold --threshold 0.70
python -m unittest discover -s tests
```

如果要切到真实模型，再跑：

```bash
export OPENAI_API_KEY=...
python scripts/query_demo.py --llm-provider openai_compatible --llm-model gpt-4o-mini
```

### 6.3 跑完后重点观察什么

- 回答里是否带有 `[S1] / [S2]`
- `sources` 是否和 Prompt 中进入的 chunk 对齐
- 无答案问题时是否直接拒答
- `threshold` 和 `min_source_score` 是否在一起把噪声压下来了
- mock 和真实模型在同一上下文下有没有明显风格差异

### 6.4 测试在锁定什么

[tests/test_generation.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/tests/test_generation.py) 当前锁定的是：

1. 上下文格式包含标签、metadata 和分数
2. Prompt 消息里同时有系统约束、上下文和问题
3. 没有结果时服务层直接返回拒答
4. 低分结果不会进入生成上下文
5. mock 生成也能稳定返回 `answer + sources`
6. 没配 API Key 时会回退到 mock

这说明第六章测试的重心已经变成：

> 生成链路是不是可控、可解释、可回归。

---

## 7. 综合案例：为什么明明检索到了还答不好

```python
# 你发现一个问题：
# Retriever 已经召回了正确 chunk，
# 但最终答案还是很散，来源也不清楚。
#
# 请回答：
# 1. 这更像检索问题还是生成问题？
# 2. context formatter 可能应该检查什么？
# 3. RAG Prompt 里至少应加入哪些约束？
# 4. min_source_score 应该在生成前处理，还是等模型回答后再决定？
# 5. 为什么最终返回结构最好是 answer + sources，而不是单一字符串？
```

你在这一章应该能给出这样的判断路径：

1. 先用 `inspect_prompt.py` 看正确 chunk 是否真的进入了上下文
2. 如果进入了，再看 Prompt 是否明确限制“只能依据上下文”
3. 如果答案里没有来源，再看 formatter 和 Prompt 是否保留了 `[S1]`
4. 如果越界问题仍被回答，再看 `threshold` 和 `min_source_score`

---

## 8. 代码映射表

| 目标 | 当前文件 | 作用 |
|------|----------|------|
| 固定回答边界 | [app/prompts/rag_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/prompts/rag_prompt.py) | 定义 system / user prompt 与拒答文本 |
| 格式化上下文 | [app/chains/rag_chain.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/chains/rag_chain.py) | 把检索结果翻译成模型消息 |
| 抽象生成客户端 | [app/llms/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/llms/providers.py) | 统一 mock 与真实 provider |
| 串起问答链路 | [app/services/rag_service.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/app/services/rag_service.py) | 检索、过滤、生成、返回结果 |
| 跑端到端问答 | [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/scripts/query_demo.py) | 观察最终答案与来源 |
| 检查 Prompt | [scripts/inspect_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/scripts/inspect_prompt.py) | 观察原始召回和最终上下文 |
| 锁定生成行为 | [tests/test_generation.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_6_rag_generation/tests/test_generation.py) | 回归 formatter、拒答和 mock 路径 |

---

## 9. 实践任务

1. 把 `default_generation_min_score` 从 `0.60` 改成 `0.70`，重新跑无答案问题，观察拒答是否更激进。
2. 把 `default_context_max_chunks` 改成 `2`，再跑 `inspect_prompt.py`，观察上下文压缩是否开始丢信息。
3. 给 `RAG_USER_TEMPLATE` 增加“先给一句结论，再给一句依据”的要求，再看真实模型和 mock 的输出差异。
4. 切到 `--llm-provider openai_compatible`，比较真实模型是否比 mock 更容易整合多条来源。

## 10. 学完这一章后你应该能回答

- 为什么检索结果不能直接等于生成输入
- 为什么 RAG Prompt 必须显式规定引用和拒答
- 为什么 `answer + sources` 比单字符串更稳
- 为什么“无答案处理”应该放在服务主流程里
- 为什么第六章依然坚持固定链路，而不是提前做 Agentic RAG

## 11. 小结

第六章真正交付的不是“模型接上了”，而是：

1. 检索结果被格式化成受控上下文
2. Prompt 明确了依据、引用和拒答边界
3. 服务层固定返回 `answer + sources`
4. 无答案被当成主线能力处理

只有这四件事立住了，第七章的评估和优化才有意义。否则你后面看到的所有好坏变化，都会混杂检索、Prompt 和生成三个层次的问题，根本无法判断改动是否真的有效。
