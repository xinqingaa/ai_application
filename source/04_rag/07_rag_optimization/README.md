# 07. RAG 优化 - 实践指南

> 这份 README 只负责一件事：带你按正确顺序跑完第七章，先固定 Golden Set，再拆开看检索评估和生成评估，然后比较配置、回看坏案例，最后把同一条评估链路接到真实 LLM。

---

## 核心原则

```text
先固定样本 -> 再拆开检索和生成 -> 再比较配置 -> 最后回看坏案例与真实 LLM
```

- 在 `source/04_rag/07_rag_optimization/` 目录下操作
- 第七章不重新发明 Retriever 或 RAG Service，而是直接复用第五章和第六章的稳定契约
- 第七章当前有两条生成评估路径：
  - `policy mock` 路径：稳定观察 Prompt、citation、refusal 和配置差异
  - `real LLM` 路径：把同一条评估链路接到真实 provider，并保留 mock fallback
- 检索评估继续沿用第五章的 `Recall / MRR / Hit Rate`
- 生成评估继续沿用第六章的 `answer + sources`、拒答边界和来源标签
- 真实调用继续参考第六章的最小 OpenAI-compatible 接缝，不在这里重新讲一遍多平台接入课程

---

## 项目结构

```text
07_rag_optimization/
├── README.md
├── requirements.txt
├── optimization_basics.py
├── 01_inspect_golden_set.py
├── 02_eval_retrieval.py
├── 03_eval_generation.py
├── 04_compare_configs.py
├── 05_review_bad_cases.py
├── 06_real_llm_eval.py
├── evals/
│   ├── golden_set.json
│   └── experiment_configs.json
├── store/
│   └── .gitignore
└── tests/
    └── test_optimization.py
```

- `optimization_basics.py`
  第七章共享主线：Golden Set、实验配置、Prompt 变体、LLM runtime、检索评估、生成评估、配置对比、坏案例分类
- `01_inspect_golden_set.py`
  先看 Golden Set 的字段和覆盖范围
- `02_eval_retrieval.py`
  只看检索层是否召回了正确 chunk
- `03_eval_generation.py`
  看答案要点、来源命中、citation 和拒答边界；可切 `policy_mock / provider`
- `04_compare_configs.py`
  在同一份 Golden Set 上比较不同策略和 Prompt 组合；默认跑 `policy mock`
- `05_review_bad_cases.py`
  把失败样本按阶段归类，决定下一轮该改哪里
- `06_real_llm_eval.py`
  用单条 Golden Set case 观察真实 provider 或 mock fallback 的请求、响应和 usage
- `tests/test_optimization.py`
  锁定 Golden Set、基线指标、Prompt 差异和 real-provider fallback 路径

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/07_rag_optimization
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 3. 当前命令

```bash
python 01_inspect_golden_set.py
python 02_eval_retrieval.py --config baseline_similarity
python 03_eval_generation.py --config baseline_similarity
python 04_compare_configs.py
python 05_review_bad_cases.py --config loose_prompt_similarity
python 06_real_llm_eval.py --config baseline_similarity --case-id citation_rules --provider openai
python -m unittest discover -s tests
```

### 4. 环境变量

真实调用沿用第六章同一套 provider 约定：

- `OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL`
- `BAILIAN_API_KEY / BAILIAN_BASE_URL / BAILIAN_MODEL`
- `DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL`
- `GLM_API_KEY / GLM_BASE_URL / GLM_MODEL`

如果环境未配置完整，第七章的 provider 路径会自动回退到 mock，不会直接打断评估主线。

---

## 先怎么读代码

### 1. 第一遍只看对象

先打开 [optimization_basics.py](./optimization_basics.py)，只看这些对象：

- `GoldenSetCase`
- `ExperimentConfig`
- `PromptVariant`
- `LLMRuntimeConfig`
- `PolicyAwareMockLLMClient`
- `RagCaseMetrics`
- `RagEvaluationReport`
- `ExperimentComparisonRow`

这一遍的目标不是理解所有逻辑，而是先知道：

- 第七章的评估样本长什么样
- 一次实验到底固定了哪些检索、生成和 LLM 变量
- 哪些对象属于稳定教学路径，哪些属于真实调用接缝

### 2. 第二遍只看主流程

然后再看这些函数：

- `load_golden_set()`
- `load_experiment_configs()`
- `build_generation_smart_engine()`
- `build_llm_client()`
- `build_rag_service()`
- `evaluate_retrieval_from_golden_set()`
- `evaluate_rag_cases()`
- `compare_experiments()`
- `collect_bad_cases()`

这一遍只回答一个问题：

```text
同一条 question 进入第七章以后，怎样先经过固定检索链路，再变成可比较、可回归、可复盘的评估结果？
```

### 3. 第三遍再看脚本和 tests

最后再看：

- `01_inspect_golden_set.py`
- `02_eval_retrieval.py`
- `03_eval_generation.py`
- `04_compare_configs.py`
- `05_review_bad_cases.py`
- `06_real_llm_eval.py`
- `tests/test_optimization.py`

这样读会比一开始顺着扫更容易建立结构感。

---

## 为什么第七章既要 `policy mock` 又要 `real LLM`

### 1. `policy mock` 在保什么

如果第七章从第一步就全部依赖真实模型，你很快会被这些噪声干扰：

- 模型随机性
- provider 差异
- usage 成本
- 环境配置问题

所以 `policy mock` 的角色不是“偷懒”，而是：

- 稳定放大 citation 约束变强或变弱后的结果差异
- 让 Prompt 优化、坏案例和基线回归在本地可重复

### 2. `real LLM` 在补什么

但第七章如果永远不接真实模型，也会留下明显断层：

- 你无法观察真实 answer 的引用风格
- 你看不到 usage、finish_reason、request preview
- 你无法验证固定样本在真实 provider 上会不会表现不同

所以第七章现在保留真实路径，但角色很明确：

> `policy mock` 用来稳定教学，`real LLM` 用来验证这套评估链路怎样接到真实 provider。

### 3. 为什么 provider 路径仍然只抽最小接缝

这一章不会重新讲第二章的 provider registry、多平台抽象和认证差异。

第七章只复用第六章已经讲清楚的最小接缝：

- provider config
- OpenAI-compatible client
- normalized generation result
- mock fallback

因为第七章的主线始终还是：

- 固定样本
- 稳定对比
- 定位坏案例

不是重新做一章“多模型接入”。

---

## 建议学习顺序

### 第 1 步：先确认 Golden Set 不是随便记几个问题

```bash
python 01_inspect_golden_set.py
```

重点观察：

- 哪些 case 是 answerable，哪些是 refusal
- `retrieval_expected_chunk_ids` 和 `expected_sources` 为什么不是一个概念
- `expected_answer_points` 为什么比整段标准答案更适合做最小回归

### 第 2 步：只看检索层

```bash
python 02_eval_retrieval.py --config baseline_similarity
python 02_eval_retrieval.py --config hybrid_rerank_strict
```

重点观察：

- 检索是否把正确 chunk 召回了
- `Recall / MRR / Hit Rate` 是否一起变化
- 为什么 retrieval 变好不等于最终 answer 一定变好

### 第 3 步：先用 `policy mock` 看生成层

```bash
python 03_eval_generation.py --config baseline_similarity
python 03_eval_generation.py --config loose_prompt_similarity
python 03_eval_generation.py --config strict_threshold
```

重点观察：

- answer 是否覆盖了 `expected_answer_points`
- `sources` 是否命中 `expected_sources`
- citation 是否真的出现在 answer 里
- refusal case 是否稳住了“我不知道”边界

### 第 4 步：统一比较配置

```bash
python 04_compare_configs.py
```

重点观察：

- Prompt 变化和 Retriever 变化分别影响了什么
- 为什么第七章只给出一个本地 `composite_score`，而不是假装它是万能指标
- 如果某个配置 retrieval 变好但 citation 变差，应该怎么解读

### 第 5 步：最后回看坏案例

```bash
python 05_review_bad_cases.py --config loose_prompt_similarity
python 05_review_bad_cases.py --config strict_threshold
```

重点观察：

- failure_stage 是 `retrieval / citation_alignment / citation_format / refusal_boundary / answer_quality` 的哪一种
- 每种失败类型下一轮应该优先调哪一层
- 为什么坏案例是优化输入，而不是附属报告

### 第 6 步：再把同一条链路接到真实 LLM

```bash
python 03_eval_generation.py --config baseline_similarity --provider openai
python 06_real_llm_eval.py --config baseline_similarity --case-id citation_rules --provider openai
python 04_compare_configs.py --config baseline_similarity --config strict_threshold --provider openai
```

重点观察：

- 没有真实环境时，为什么 provider 路径仍然能回退到 mock
- 真实 provider 的 answer、usage、finish_reason 和 request preview 长什么样
- 为什么真实模型上的配置对比更贵、更慢，也更容易受随机性影响

---

## 本章与第六章如何衔接

- 第六章已经把问答链路固定成了 `answer + sources`
- 第七章不会重写新的问答对象，而是直接消费第六章的 `RagService` 运行时状态
- 第七章如果比较 Prompt，只通过第六章新增的可选 Prompt 接缝完成，不复制一套平行生成链路
- 第七章如果接真实 LLM，也只复用第六章的最小 provider/fallback 接缝

---

## 本章复用了哪些已有逻辑

- 复用第五章的检索策略抽象和评估指标：
  - `SmartRetrievalConfig`
  - `SmartRetrievalEngine`
  - `Recall / MRR / Hit Rate`
- 复用第六章的生成主线：
  - `build_generation_demo_store()`
  - `generation_demo_source_chunks()`
  - `RagService`
  - `answer + sources`
  - `NO_ANSWER_TEXT`
  - `create_generation_client()`

本章新增的不是新的检索器或新的生成链，而是：

- Golden Set 结构
- 实验配置结构
- Prompt 变体
- LLM runtime 配置
- 评估报告
- 坏案例分类

---

## 你应该产出的学习结论

学完第七章，至少要能明确说出：

1. 某次修改到底改善了检索、生成，还是两者都没有改善
2. 哪些问题是 retrieval miss，哪些是 citation 没对齐，哪些是 refusal 边界坏了
3. 为什么 `policy mock` 更适合做稳定基线，而真实 LLM 更适合做最后验证
4. 下一轮应该先改 `Retriever / Prompt / context filter / max_chunks` 的哪一个
