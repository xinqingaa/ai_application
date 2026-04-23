# 07. RAG 优化

> 本章目标：把第六章已经跑通的 `question -> answer + sources` 固定链路，推进成“可评估、可对比、可回归”的优化闭环，明确区分检索问题、生成问题、真实 LLM 观察点和坏案例回流。

---

## 1. 概述

### 学习目标

- 理解为什么第七章真正新增的是“评估闭环”，不是“再加几个调参按钮”
- 理解为什么第七章必须建立在固定 Golden Set 之上，而不是边改边凭感觉看回答
- 掌握检索评估、生成评估和端到端评估三层视角的分工
- 理解为什么第七章既保留 `policy mock`，又补上真实 LLM 路径
- 能说明一次改动到底改善了检索、生成，还是两者都没有改善
- 能把坏案例沉淀成下一轮优化输入，而不是零散截图
- 能解释为什么第七章只复用第五章和第六章的稳定对象，而不重写一套平行 RAG 系统

### 预计学习时间

- Golden Set 与实验基线：30-40 分钟
- 检索评估与配置对比：40-60 分钟
- 生成质量评估与引用边界：40-60 分钟
- 真实 LLM 观察与 fallback：30-40 分钟
- 坏案例回流：30-40 分钟

### 本章在 RAG 工程中的重要性

| 场景 | 第七章先解决什么 |
|------|------------------|
| 想改 Retriever | 先判断召回有没有真的变好 |
| 想改 Prompt | 先判断答案质量、引用和拒答有没有真的改善 |
| 想加 Rerank / Hybrid | 先用固定样本回归，而不是只看单个 Demo |
| 想接真实模型验证 | 先把同一条评估链路和 provider/fallback 接起来 |
| 想知道系统坏在哪 | 先把失败归因到 retrieval / citation / refusal / answer quality |
| 想继续进第八章 | 先把固定链路评估立住，才知道何时真的需要更复杂方案 |

> **没有评估，RAG 优化就很容易退化成“换个 Prompt 看感觉”。**

### 学习前提

- 建议先完成第五章，已经理解 `RetrievalResult[]`、`threshold / MMR / hybrid / rerank`
- 建议先完成第六章，已经理解 `context selection -> answer + sources -> refusal`
- 建议已经接受课程开头的最小评估集意识：优化一定需要固定样本

这一章不再重复讲：

- 如何切块
- 如何生成 embedding
- 如何实现底层向量数据库
- 如何重新设计一套生成链
- 如何建设完整 LLMOps 平台
- 如何系统讲 provider 多平台抽象

### 本章与前后章节的关系

第五章已经解决：

1. 检索器如何稳定返回 `RetrievalResult[]`
2. `similarity / threshold / mmr / hybrid / rerank` 的策略差异
3. 检索层有哪些最小可评估入口

第六章已经解决：

1. 如何把 `RetrievalResult[]` 收成可控上下文
2. 如何固定 `answer + sources`
3. 如何显式设计 refusal
4. 如何让 mock、真实 LLM、LCEL 都指向同一条生成主线

第七章接着解决：

1. 如何判断某次改动是不是变好
2. 如何把检索评估和生成评估拆开看
3. 如何把配置差异变成结构化实验结果
4. 如何把同一条评估链路接到真实 provider
5. 如何沉淀坏案例并驱动下一轮修改

第八章会继续建立在这里之上：

1. 当固定链路优化到一定程度后，什么时候值得升级到更复杂方案

### 第七章与第六章的连续性

第七章不会重新定义一套新的问答对象。

当前代码延续的是这条连续路径：

```text
chapter 5 SmartRetrievalConfig / SmartRetrievalEngine / retrieval metrics
-> chapter 6 RagService / answer + sources / provider fallback
-> chapter 7 Golden Set / experiment configs / reports / bad cases
```

也就是说，第七章真正新增的是：

- `GoldenSetCase`
- `ExperimentConfig`
- `LLMRuntimeConfig`
- `RagEvaluationReport`
- `compare_experiments()`
- `collect_bad_cases()`

而不是再次重写：

- Retriever 基础接口
- 向量 store
- `answer + sources`
- provider config
- 拒答主线

### 本章代码入口

本章对应的代码目录是：

- [README.md](../../source/04_rag/07_rag_optimization/README.md)
- [requirements.txt](../../source/04_rag/07_rag_optimization/requirements.txt)
- [optimization_basics.py](../../source/04_rag/07_rag_optimization/optimization_basics.py)
- [01_inspect_golden_set.py](../../source/04_rag/07_rag_optimization/01_inspect_golden_set.py)
- [02_eval_retrieval.py](../../source/04_rag/07_rag_optimization/02_eval_retrieval.py)
- [03_eval_generation.py](../../source/04_rag/07_rag_optimization/03_eval_generation.py)
- [04_compare_configs.py](../../source/04_rag/07_rag_optimization/04_compare_configs.py)
- [05_review_bad_cases.py](../../source/04_rag/07_rag_optimization/05_review_bad_cases.py)
- [06_real_llm_eval.py](../../source/04_rag/07_rag_optimization/06_real_llm_eval.py)
- [evals/golden_set.json](../../source/04_rag/07_rag_optimization/evals/golden_set.json)
- [evals/experiment_configs.json](../../source/04_rag/07_rag_optimization/evals/experiment_configs.json)
- [tests/test_optimization.py](../../source/04_rag/07_rag_optimization/tests/test_optimization.py)

### 本章边界

本章重点解决：

1. 最小 Golden Set
2. 检索评估
3. 生成评估
4. 配置对比
5. 真实 LLM 路径
6. 坏案例回流

本章不要求：

- 完整企业级观测平台
- 自动化标注平台
- 线上 A/B 平台
- 大规模离线评测管线
- 自动事实核查系统
- 复杂多模型路由治理

第七章当前真正要立住的是：

> 同一条固定 RAG 链路，怎样从“能答”推进成“知道哪里变好了、哪里退化了、真实模型上又会怎样表现”。

---

## 2. 为什么第七章不是“再加一个评测脚本” 📌

### 2.1 真正难的不是写指标，而是固定实验尺子

很多人一说“我要优化 RAG”，会马上开始改：

- `top_k`
- `threshold`
- `mmr_lambda`
- Prompt
- `max_chunks`
- `min_context_score`

这些动作本身没错，但如果你没有固定样本，就很难回答：

- 变好的是检索还是生成
- 哪些 case 变好了，哪些 case 变差了
- 成本和风险是不是也一起上来了

所以第七章第一步不是“做一个评测器”，而是：

> 先固定 Golden Set，让后续每一次改动都能回到同一把尺子上。

### 2.2 最小 Golden Set 到底应该长什么样

本课程里，第七章的 Golden Set 至少包含：

- `question`
- `expected_answer`
- `expected_answer_points`
- `expected_sources`
- `retrieval_expected_chunk_ids`
- `should_refuse`

这里最容易被忽略的是：

- `expected_answer` 用来帮助你理解标准答案长什么样
- `expected_answer_points` 才是最适合最小回归的字段
- `expected_sources` 是最终回答应该至少覆盖到的来源
- `retrieval_expected_chunk_ids` 是检索层应该召回到的 chunk

也就是说：

> `retrieval_expected_chunk_ids` 和 `expected_sources` 不是一个概念。前者看的是“有没有召回证据”，后者看的是“最终回答有没有把证据带出来”。

### 2.3 为什么第七章一定要拆成三层评估

第七章如果只给一个总分，很快就会失真。

因为同样是“答错了”，实际可能有三种完全不同的原因：

1. 检索就没召回来
2. 检索召回了，但没有进 Prompt
3. Prompt 里已经有依据，但生成没引用、没拒答或没覆盖关键要点

所以第七章要强制拆成三层：

1. 检索评估
   - `Recall / MRR / Hit Rate`
2. 生成评估
   - answer point recall
   - source hit rate
   - citation support
   - refusal accuracy
3. 端到端对比
   - 哪个配置最终 pass rate 更高

### 2.4 为什么第七章不建设“万能分数”

现实里你当然会想要一个统一分数，但第七章只能给你一个**本地实验排序分数**，不能假装它是万能标准。

原因很简单：

- 不同业务的权重不一样
- 某些系统更看重 refusal
- 某些系统更看重引用稳定性
- 某些系统更看重检索召回

所以第七章会提供 `composite_score`，但它的角色只是：

> 方便你在当前样本、当前业务边界下做本地排序，不是取代人工判断。

---

## 3. 检索效果优化：先判断证据有没有被召回 📌

### 3.1 检索层常见失败是什么

在真正进入生成之前，检索层最常见的问题通常是：

- 根本没召回预期 chunk
- 召回到了，但排位太靠后
- 候选里有很多噪声
- 上下文候选过多，后面会挤占 Prompt 空间

如果这里没拆开看，后面很容易误以为：

- “是 Prompt 不够好”
- “是模型不够强”

其实问题可能只是：

- `top_k` 太小
- `threshold` 太高
- 没有 `MMR`
- 没有混合检索
- 没有对重复 chunk 做 rerank

### 3.2 第七章怎样承接第五章

第七章不会重新发明新的检索器，而是直接复用第五章的：

- `SmartRetrievalConfig`
- `SmartRetrievalEngine`
- `Recall / MRR / Hit Rate`

区别只在于：

- 第五章主要看“检索策略本身怎样工作”
- 第七章开始看“同一条检索策略，在 Golden Set 上到底表现怎样”

当前代码里，这个承接点在：

- [optimization_basics.py](../../source/04_rag/07_rag_optimization/optimization_basics.py) 的 `evaluate_retrieval_from_golden_set()`
- [02_eval_retrieval.py](../../source/04_rag/07_rag_optimization/02_eval_retrieval.py)

### 3.3 检索优化的默认顺序

本课程建议的默认顺序仍然是：

1. 先固定评估样本
2. 先看 `top_k / candidate_k`
3. 再看 `threshold / MMR`
4. 语义和关键词各有短板时，再上 hybrid
5. 候选池足够大但排序不稳时，再上 rerank

这个顺序很重要，因为：

- 你可以更容易定位变化来源
- 不会一开始就把多个变量一起改掉
- 回归结果更容易解释

### 3.4 为什么第七章代码没有先展开 `chunk_size`

大纲里“检索优化”当然包括切分策略和 embedding 模型选择。

但第七章当前代码没有先把这些变量做成主轴，而是先聚焦：

- retrieval strategy
- context filter
- prompt variant
- llm runtime

原因不是这些变量不重要，而是：

1. 切分和 embedding 已经在前几章系统讲过
2. 第七章当前更需要先把“可重复评估框架”立住
3. 有了这套框架，后续你完全可以把 `chunk_size / overlap / embedding model` 也作为实验配置继续加入

也就是说：

> 第七章当前代码先解决“怎样评”，而不是假装“一次性把所有变量都演完”。

---

## 4. 生成质量优化：重点不是模型更会说，而是回答更可控 📌

### 4.1 生成层常见失败是什么

在第六章里，你已经把生成主线跑通了。

第七章开始，你更应该关注这些失败：

- 答案没有覆盖关键要点
- 答案没有带来源标签
- `sources` 返回了，但 answer 里没有引用
- 本来应该拒答，却被硬答
- 检索结果没问题，但上下文裁剪让回答丢掉了重要信息

这几个问题不能简单归结成“模型太弱”。

它们通常对应的是：

- Prompt 约束不够清晰
- `max_chunks` 或 `max_chars_per_chunk` 太激进
- `min_context_score` 过滤边界不合理
- `sources` 和 answer labels 没有对齐

### 4.2 第七章怎样承接第六章

第七章不会复制一套新的生成链，而是直接复用第六章的：

- `RagService`
- `answer + sources`
- `NO_ANSWER_TEXT`
- refusal 边界

唯一新增的共享接缝是：

- 允许 `RagService` 接收可选 Prompt 模板

这样做的目的不是“让 Prompt 花活变多”，而是：

> 让第七章可以合法比较“同一条链路下，Prompt 约束变强或变弱，会怎样影响 citation 和 refusal”。

### 4.3 生成质量优化到底看什么

第七章当前把生成质量拆成四个最小指标：

1. `answer_point_recall`
   - 关键要点覆盖了多少
2. `source_hit_rate`
   - 预期来源是否至少被回答带出来
3. `citation_support_rate`
   - answer 里是否真的有标签，并且来源没丢
4. `refusal_accuracy`
   - 无答案问题是否稳住了“我不知道”

这些指标都不是完整真理，但它们足够支持第七章的核心目标：

> 让你能区分“检索差”“回答差”“引用差”“拒答差”。

### 4.4 为什么第七章还保留 `pass_rate`

很多时候局部指标看起来都不错，但系统仍然没法交付。

例如：

- 检索召回到了
- answer 也覆盖了要点
- 但没有 citation

对课程当前目标来说，这个 case 依然不能算通过。

因此第七章还保留了一个更直接的判断：

- `pass_rate`

它不是替代各项指标，而是告诉你：

> 在当前课程定义的最小质量边界下，真正通过的 case 有多少。

---

## 5. 为什么第七章既要 `policy mock` 又要真实 LLM 📌

### 5.1 如果只保留 mock，会留下什么断层

如果第七章永远不接真实模型，你会失去这些观察点：

- 真实 provider 的 answer 风格
- usage / finish_reason
- request preview / response preview
- 不同 provider 环境变量是否真的接通
- provider 未就绪时 fallback 的可观察信息

这会让第七章停在“本地模拟优化”，无法自然衔接真实应用。

### 5.2 如果只保留真实模型，又会出现什么问题

但如果第七章从第一步就只依赖真实模型，也会马上遇到这些噪声：

- 随机性
- provider 差异
- 调用成本
- SDK、认证、base_url 配置问题

这样你很容易分不清：

- 是评估逻辑没讲清
- 还是模型输出本来就有波动
- 还是环境根本没配好

### 5.3 `policy mock` 在本章到底保什么

第七章当前新增的 `PolicyAwareMockLLMClient` 不是为了假装模型很强，而是为了稳定放大两个教学现象：

1. citation 约束变强时，answer 更容易保留来源标签
2. citation 约束变弱时，answer 更容易丢掉标签

也就是说：

> `policy mock` 保的是稳定可重复的教学基线，不是替代真实模型。

### 5.4 真实 LLM 路径在本章补什么

真实 LLM 路径在第七章补的是：

- 真实 answer 的观察
- provider/fallback 行为
- usage 和 finish_reason
- request/response preview
- 同一份 Golden Set 在真实 provider 上的最小验证

所以第七章现在的角色分工是：

1. `policy mock`
   用来稳定做本地回归和配置对比
2. `real provider`
   用来验证这套评估链路怎样接到真实模型

### 5.5 为什么真实 LLM 仍然只抽最小 client 接缝

第七章不会重新展开：

- provider registry
- 各家鉴权差异
- 多平台抽象设计

这里只继续复用第六章已经讲清楚的最小接缝：

- provider config
- OpenAI-compatible client
- normalized generation result
- mock fallback

因为第七章真正要学的是：

> 同一条评估链路怎样稳稳接到真实 provider，而不是在这一章重新做一套多模型接入课程。

---

## 6. 配置对比：优化不是单点观察，而是同一组实验回归 📌

### 6.1 为什么第七章一定要有实验配置文件

只要优化是持续发生的，你迟早会遇到这些问题：

- 这次到底改了什么
- 为什么上周看起来更好，这周又退化了
- Prompt 和 Retriever 是一起改的，还是只改了一层
- 这轮实验到底是 `policy mock` 还是 real provider

所以第七章不把实验配置写死在脚本里，而是单独放到：

- [evals/experiment_configs.json](../../source/04_rag/07_rag_optimization/evals/experiment_configs.json)

当前配置里至少覆盖了：

- baseline similarity
- strict threshold
- MMR balanced
- hybrid + rerank + strict prompt
- loose prompt similarity

这样你就能在一份 Golden Set 上直接比较：

- 策略变化
- Prompt 变化
- 上下文过滤变化

### 6.2 为什么“变好”必须先回答具体改善了哪一层

一次配置变化可能出现三种典型情况：

1. retrieval 更好了，generation 没变
2. retrieval 没变，但 citation 和 refusal 更稳了
3. retrieval 看起来更强了，但上下文过长，反而让 answer point recall 下降

所以第七章的配置对比不会只输出一个分数，而是必须一起看：

- retrieval recall / mrr
- answer point recall
- source hit rate
- citation support
- refusal accuracy
- pass rate

### 6.3 为什么真实 provider 上的配置对比要更谨慎

第七章允许你把同一份配置对比接到真实 provider，但这里要非常明确：

- 成本会上升
- 结果会更慢
- 输出可能有轻微随机性

所以真实 provider 上的对比更适合：

- 小规模配置验证
- 重点 case 复盘
- 最终确认某个优化方向是否合理

而不是一开始就拿来当唯一基线。

---

## 7. 坏案例为什么比“成功案例展示”更重要 📌

### 7.1 好案例只能证明“系统有时候会成功”

如果你只看成功案例，你只能得出一个很弱的结论：

- 这个系统不是完全坏的

但这对优化没什么帮助。

因为你真正需要知道的是：

- 哪类问题更容易失败
- 失败发生在 retrieval、citation、refusal 还是 answer quality
- 下一轮到底先改哪一层

### 7.2 第七章当前怎么分类坏案例

当前实现把失败样本先粗分成：

- `retrieval`
- `citation_alignment`
- `citation_format`
- `refusal_boundary`
- `answer_quality`

这几个分类不是最终工业标准，但已经足够支持教学主线：

- 先判断问题在哪一层
- 再决定下一轮优先级

### 7.3 一条坏案例最少应该沉淀什么

第七章当前坏案例至少会沉淀：

- `case_id`
- `question`
- `failure_stage`
- `summary`
- `retrieved_chunk_ids`
- `prompt_chunk_ids`
- `answer`

这样你回头看时，不只是看到“FAIL”，而是能继续问：

- 证据有没有召回
- 哪些候选真正进了 Prompt
- answer 为什么失败
- 下一轮应该先改什么

### 7.4 坏案例回流的真实意义

第七章最后要建立的不是“做一份报告”的习惯，而是：

> 每次坏案例都能推动下一轮更有针对性的修改。

这是 RAG 优化和“换 Prompt 看感觉”之间最本质的区别。

---

## 8. 第七章代码是怎么落地的 📌

### 8.1 `optimization_basics.py`

这个文件承载了本章全部核心对象：

- `PromptVariant`
- `GoldenSetCase`
- `ExperimentConfig`
- `LLMRuntimeConfig`
- `PolicyAwareMockLLMClient`
- `RagCaseMetrics`
- `RagEvaluationReport`
- `ExperimentComparisonRow`
- `BadCaseRecord`

同时也放了本章所有核心动作：

- `load_golden_set()`
- `load_experiment_configs()`
- `build_llm_client()`
- `build_generation_smart_engine()`
- `build_rag_service()`
- `evaluate_retrieval_from_golden_set()`
- `evaluate_rag_cases()`
- `compare_experiments()`
- `collect_bad_cases()`

这里最重要的边界是：

> 第七章不是再做一套 RAG 系统，而是在第五章和第六章的稳定对象之上加“评估层”和“实验层”。

### 8.2 `LLMRuntimeConfig` 真正在补什么

这个对象的意义很大，因为它把第七章以前容易散落的运行时选择统一了：

- 当前走 `policy_mock` 还是 `provider`
- provider 是谁
- `temperature`
- `max_tokens`
- `timeout`
- `max_retries`

这样第七章的脚本不会各自乱拼 provider 参数，而是共享同一套 runtime 语义。

### 8.3 `PolicyAwareMockLLMClient` 真正在补什么

这个对象不是为了模仿真实大模型全部能力，而是专门为第七章保留一个**稳定可重复的教学基线**。

它做的最关键两件事是：

- 在宽松 Prompt 下更容易丢 citation
- 在严格 Prompt 下更容易保留 citation

这让你可以在不依赖真实 API 的情况下稳定观察 Prompt 优化带来的差异。

### 8.4 脚本各自的职责

各脚本不是随机分散的，它们分别锁定不同观察点：

- [01_inspect_golden_set.py](../../source/04_rag/07_rag_optimization/01_inspect_golden_set.py)
  看样本结构和覆盖范围
- [02_eval_retrieval.py](../../source/04_rag/07_rag_optimization/02_eval_retrieval.py)
  只评 retrieval
- [03_eval_generation.py](../../source/04_rag/07_rag_optimization/03_eval_generation.py)
  评 generation；既可跑 `policy_mock`，也可跑 `provider`
- [04_compare_configs.py](../../source/04_rag/07_rag_optimization/04_compare_configs.py)
  统一比较多组实验配置
- [05_review_bad_cases.py](../../source/04_rag/07_rag_optimization/05_review_bad_cases.py)
  汇总失败样本并归因
- [06_real_llm_eval.py](../../source/04_rag/07_rag_optimization/06_real_llm_eval.py)
  用单条 case 观察真实 LLM 的请求、响应和 sources 对齐

---

## 9. 第七章最小治理锚点 📌

### 9.1 为什么第七章就要带治理视角

如果这一章只讲“调几个参数看看效果”，后面很快会失控：

- 今天换了 Prompt，答案变好了还是碰巧了？
- 今天调了 `threshold`，是检索更稳了还是只是更爱拒答了？
- 今天换了 provider，是模型强了还是 citation 反而不稳了？

所以第七章要开始建立最小治理视角。

### 9.2 第七章最重要的治理锚点是什么

这一章当前最重要的治理锚点有五类：

1. 样本锚点
   `GoldenSetCase` 必须固定
2. 配置锚点
   `ExperimentConfig` 必须可记录
3. 检索锚点
   `Recall / MRR / Hit Rate` 必须可复现
4. 生成锚点
   `answer + sources + refusal` 必须可判断
5. 运行时锚点
   `policy_mock / provider / fallback` 必须可观察

### 9.3 第七章最值得反复观察的 case

当前最值得反复观察的几条 case：

1. `refund_policy`
   看 retrieval 和 answer points 是否一起过
2. `citation_rules`
   看 citation label 和 `sources` 是否对齐
3. `prompt_boundary`
   看拒答边界相关的 Prompt 要求是否被保留
4. `no_answer`
   看系统是否稳定拒答
5. `loose_prompt_similarity`
   看坏案例是否集中在 `citation_format`

### 9.4 第七章最关键的三类错误定位

你应该刻意区分三类错误：

1. 检索候选错误
   第五章根本没把对的候选找出来
2. 上下文/配置错误
   候选有了，但 `threshold / max_chunks / min_context_score` 让它没变成可用回答
3. 生成组织错误
   上下文已经对了，但 Prompt、引用或拒答组织方式有问题

真实 provider 路径再额外补一层：

4. 运行时观察错误
   provider、usage、finish_reason、fallback 信息没有被正确保留

---

## 10. 如何阅读第七章代码

### 10.1 第一遍只看对象

先打开 [optimization_basics.py](../../source/04_rag/07_rag_optimization/optimization_basics.py)，只看这些对象：

- `PromptVariant`
- `GoldenSetCase`
- `ExperimentConfig`
- `LLMRuntimeConfig`
- `PolicyAwareMockLLMClient`
- `RagCaseMetrics`
- `RagEvaluationReport`
- `ExperimentComparisonRow`

然后再补看：

- `GenerationResult`
- `SmartRetrievalConfig`
- `RagService`

这一遍的目标不是理解所有逻辑，而是先知道：

- 第七章有哪些最小运行时对象
- 哪些对象属于教学主线，哪些对象属于真实调用接缝
- 为什么第七章不是只多了一个统计脚本

### 10.2 第二遍只看主流程

然后再看这些函数和方法：

- `load_golden_set()`
- `load_experiment_configs()`
- `build_llm_client()`
- `build_rag_service()`
- `evaluate_retrieval_from_golden_set()`
- `evaluate_rag_cases()`
- `compare_experiments()`
- `collect_bad_cases()`

这一遍只回答一个问题：

```text
同一条 question 进入第七章以后，到底按什么顺序变成可比较、可回归、可复盘的评估结果？
```

### 10.3 第三遍再看脚本和 tests

最后再看：

- `01_inspect_golden_set.py`
- `02_eval_retrieval.py`
- `03_eval_generation.py`
- `04_compare_configs.py`
- `05_review_bad_cases.py`
- `06_real_llm_eval.py`
- `tests/test_optimization.py`

这样读会比一开始从头到尾顺着扫更容易建立结构感。

---

## 11. 第七章实践：建议运行顺序

### 11.1 安装依赖

在 `source/04_rag/07_rag_optimization/` 目录下运行：

```bash
python -m pip install -r requirements.txt
```

### 11.2 先看 Golden Set

```bash
python 01_inspect_golden_set.py
```

重点观察：

- case 结构长什么样
- answerable 和 refusal 怎么区分
- 为什么 `expected_answer_points` 比整段标准答案更适合回归

### 11.3 再看检索评估

```bash
python 02_eval_retrieval.py --config baseline_similarity
python 02_eval_retrieval.py --config hybrid_rerank_strict
```

重点观察：

- 正确 chunk 有没有召回
- rank 有没有变好
- 哪个策略对当前样本更稳

### 11.4 先用 `policy mock` 看生成评估

```bash
python 03_eval_generation.py --config baseline_similarity
python 03_eval_generation.py --config loose_prompt_similarity
python 03_eval_generation.py --config strict_threshold
```

重点观察：

- answer point recall
- source hit rate
- citation support
- refusal accuracy

### 11.5 再做配置对比

```bash
python 04_compare_configs.py
```

这一遍重点不是背排名，而是理解：

- 为什么某些配置 retrieval 更强
- 为什么某些配置 citation 更稳
- 为什么某些配置虽然 answer 还能看，但 pass rate 反而下降

### 11.6 最后回看坏案例

```bash
python 05_review_bad_cases.py --config loose_prompt_similarity
python 05_review_bad_cases.py --config strict_threshold
```

这一遍要练的是：

- 从 failure_stage 反推该改哪一层
- 不把所有失败都归结成“换更强模型”

### 11.7 再把同一条链路接到真实 LLM

```bash
python 03_eval_generation.py --config baseline_similarity --provider openai
python 06_real_llm_eval.py --config baseline_similarity --case-id citation_rules --provider openai
python 04_compare_configs.py --config baseline_similarity --config strict_threshold --provider openai
```

重点观察：

- 没有真实环境时，为什么仍然能看到 provider 和 fallback 信息
- 真实 provider 的 usage、finish_reason、request preview、response preview 长什么样
- 为什么真实 provider 上的配置对比更贵、更慢，也更容易受随机性影响

### 11.8 测试在锁定什么

```bash
python -m unittest discover -s tests
```

这组测试当前锁定的不是“脚本能跑”，而是：

1. Golden Set 的规模和结构稳定
2. baseline 配置在 retrieval 和 generation 上都有非零指标
3. strict Prompt 在 citation 上不会比 loose Prompt 更差
4. provider runtime 在环境不完整时仍会回退到 mock

### 11.9 建议你主动改的地方

如果你想真正吃透第七章，建议你主动做这些小改动：

1. 把 `min_context_score` 分别改成 `0.2 / 0.35 / 0.5`，看系统何时更爱拒答
2. 把 `max_chunks` 分别改成 `1 / 2 / 3`，观察 Prompt 和 `answer_point_recall` 怎么变化
3. 把配置从 `similarity` 改成 `threshold / mmr / hybrid + rerank`，看 retrieval 与 generation 指标怎样联动
4. 在 `policy_mock` 和真实 provider 间切换，观察 citation 和 usage 信息有什么差别
5. 主动新增一个 Golden Set case，判断它属于检索错误、配置错误还是生成组织错误

---

## 12. 本章学完后你应该能回答

- 为什么 RAG 优化不能只靠主观感觉
- 为什么 `retrieval_expected_chunk_ids` 和 `expected_sources` 必须拆开
- 为什么 `policy mock` 更适合做稳定基线，而真实 LLM 更适合做最终验证
- 为什么真实 LLM 接入只应该继续复用第六章的最小 provider/fallback 接缝
- 为什么坏案例比漂亮答案展示更能推动下一轮优化

---

## 综合案例：一次优化为什么不能只看主观感觉

```python
# 你把配置从 baseline_similarity 改成 hybrid_rerank_strict，
# 又把 generation runtime 从 policy_mock 换成 openai。
#
# 请回答：
# 1. 为什么这还不能直接说明优化成功？
# 2. 至少要同时看哪些 retrieval 指标、generation 指标和 runtime 观察点？
# 3. 如果 citation support 提高了，但 answer point recall 下降了，应该怎么解释？
# 4. 如果 loose_prompt_similarity 的坏案例集中在 citation_format，下一轮应该先改 Prompt、Retriever，还是 max_chunks？
# 5. 如果真实 provider 和 policy_mock 的结论不完全一致，应该优先怎样定位？
```

第七章真正希望你建立的判断方式是：

> 优化不是“改完以后感觉更顺眼”，而是“能明确指出哪一层变好了、哪一层变差了、真实模型上又出现了什么额外信息，以及下一轮应该先改哪里”。
