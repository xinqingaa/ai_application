# 模型原理与 LangChain 基础 学习大纲

> 目标：以应用开发者视角理解 LLM 的基本工作原理，并系统掌握 LangChain 的核心抽象，为 RAG 和 Agent 工程打牢基础

---

## 课程定位

- 本课程是 `LLM -> RAG -> Agent` 之间的承上启下模块。
- 上半部分补足你需要的 **LLM 基本原理认知**，重点是“理解为什么能这样工作”，不是做研究型深入。
- 下半部分系统讲 **LangChain 核心抽象**，重点是“理解组件如何组合”，不是穷举所有类和 API。
- 课程风格遵循“代表性对象深讲 + 其余对象会查会用”，降低心智负担。

## 学习前提

- 已完成 [01_python/outline.md](/Users/linruiqiang/work/ai_application/docs/01_python/outline.md)
- 已完成 [02_llm/outline.md](/Users/linruiqiang/work/ai_application/docs/02_llm/outline.md)
- 已能独立调用至少一个 LLM API，并理解消息、结构化输出、流式输出这些基本概念

## 一、LLM 基本原理

### 1. 从“下一个 Token 预测”理解 LLM

#### 知识点

1. **LLM 本质**
   - 语言模型的目标：预测下一个 Token
   - 为什么“预测下一个 Token”能表现出问答、总结、翻译、代码生成能力
   - 预训练语料、模式学习与泛化

2. **从 Prompt 到输出的过程**
   - 文本先分词，再映射为 Token ID
   - Token ID 变成向量表示
   - 模型逐步生成下一个 Token
   - 采样参数如何影响最终输出

3. **应用开发者需要理解到什么程度**
   - 为什么 Prompt 改一点，结果会明显变化
   - 为什么上下文越长越贵
   - 为什么结构化输出、工具调用可以提升稳定性

#### 实践练习

```python
# 1. 画出一次 LLM 调用的最小数据流
# 用户文本 -> tokenizer -> token ids -> model -> next token -> decode

# 2. 用自己的话解释：
# “为什么大模型不是在数据库里查答案，而是在做概率预测？”

# 3. 将“文本生成”与“分类任务”统一成“下一个 token 预测”来理解
```

---

### 2. Transformer 与 Attention 直觉

#### 知识点

1. **为什么需要 Transformer**
   - RNN / LSTM 的局限
   - 并行训练的重要性
   - 长距离依赖问题

2. **Attention 的直觉**
   - 当前 Token 在看什么上下文
   - Query / Key / Value 的直观含义
   - 为什么 Attention 能处理“代词指代、长距离关联”

3. **Transformer 的基本结构**
   - Embedding
   - Multi-Head Attention
   - Feed Forward
   - Residual + LayerNorm
   - Decoder-only 架构为什么成为主流 LLM 方案

4. **应用开发视角的收获**
   - 为什么上下文顺序重要
   - 为什么检索片段的组织方式会影响回答
   - 为什么多余噪声上下文会污染输出

#### 实践练习

```python
# 1. 用一句话分别解释 Query / Key / Value

# 2. 找一个例子说明：
# “模型回答当前词时，会重点关注上下文里的哪些词？”

# 3. 结合 RAG 预习：
# 为什么把不相关文档塞进上下文可能让答案变差？
```

---

### 3. 模型训练生命周期

#### 知识点

1. **预训练（Pretraining）**
   - 大规模语料学习语言与知识模式
   - 形成通用能力的来源

2. **指令微调（SFT）**
   - 让模型更像助手而不是“纯续写器”
   - 常见数据形式：instruction / input / output

3. **对齐与偏好优化**
   - RLHF / DPO 的基本目的
   - 为什么模型会“更听话、更安全”

4. **推理阶段（Inference）**
   - Prompt 作为“临时任务注入”
   - 采样、上下文窗口、KV Cache 的基本直觉

#### 实践练习

```python
# 1. 用时间线画出：
# 预训练 -> 指令微调 -> 对齐 -> 推理

# 2. 思考：
# “为什么很多任务只靠 Prompt 就能做，不一定需要微调？”

# 3. 比较：
# 通用基座模型 vs 聊天模型，应用开发时你会怎么选？
```

---

### 4. 微调、RAG、长上下文如何选择

#### 知识点

1. **三种方案的本质区别**
   - 微调：改模型行为/风格
   - RAG：补外部知识
   - 长上下文：直接塞材料

2. **适用场景**
   - 高频固定格式输出
   - 私域知识问答
   - 低频但长材料分析

3. **企业常见决策逻辑**
   - 先 Prompt
   - 再 RAG
   - 再考虑工作流
   - 最后才考虑微调

4. **常见误区**
   - 把“知识更新”问题误交给微调
   - 把“行为不稳定”问题误交给 RAG
   - 过早投入训练与部署成本

#### 实践练习

```python
# 1. 判断以下场景更适合 Prompt / RAG / 微调 / 长上下文
# - 企业制度问答
# - 固定风格客服回复
# - 50页合同分析
# - 表格字段抽取

# 2. 为一个“公司内部知识助手”写技术选型说明
```

---

### 5. 开源模型、私有化部署与本地推理认知

#### 知识点

1. **开源模型生态概览**
   - Qwen、Llama、DeepSeek、Mistral 等
   - 基座模型 vs 指令模型
   - 通用模型 vs 代码模型 vs Embedding / Rerank 模型

2. **本地推理与私有化部署**
   - Ollama / vLLM / LM Studio 的定位
   - 单机本地体验 vs 企业私有化部署
   - GPU、显存、量化的基本概念

3. **何时需要私有化**
   - 数据合规
   - 成本模型
   - 时延与可控性

4. **应用开发者需要具备的认知边界**
   - 知道如何选方案
   - 知道该和训练/平台团队讨论什么
   - 不要求在这一阶段重投入自训与大规模部署

#### 实践练习

```python
# 1. 比较：
# API 调用闭源模型 vs 本地运行开源模型

# 2. 为以下场景做部署建议：
# - 个人学习 Demo
# - 公司内部敏感知识问答
# - 高并发在线客服
```

---

### 6. 微调认知入门

#### 知识点

1. **微调的目标**
   - 调整输出风格
   - 强化任务模式
   - 学习领域格式

2. **主流方法**
   - Full Fine-tuning
   - LoRA
   - QLoRA

3. **成本与收益**
   - 数据准备成本
   - 训练资源成本
   - 上线维护成本

4. **你当前阶段的学习目标**
   - 理解概念和适用边界
   - 看得懂 LoRA / QLoRA 相关文章
   - 能判断当前需求是否值得做微调

#### 实践练习

```python
# 1. 解释：
# 为什么很多应用场景优先做 RAG，而不是直接微调？

# 2. 对比：
# LoRA 和 Full Fine-tuning 的优缺点
```

---

## 二、LangChain 核心抽象

### 7. 为什么要学 LangChain

#### 知识点

1. **LangChain 的价值**
   - 把模型、Prompt、输出解析、检索、工具等能力组件化
   - 降低“从 demo 到工程”的重复胶水代码
   - 统一抽象，便于扩展和替换

2. **正确预期**
   - LangChain 不是“必须用”的
   - 也不是“学会几个类就等于掌握了框架”
   - 真正要掌握的是：它抽象了哪些对象、这些对象如何组合

3. **学习策略**
   - 深讲代表性对象：`ChatModel`、`PromptTemplate`、`Runnable`、`Retriever`、`Tool`
   - 其余同类对象通过文档与迁移能力掌握

#### 实践练习

```python
# 1. 总结：
# 如果不用 LangChain，你在项目里通常要自己写哪些胶水代码？

# 2. 思考：
# “框架熟练掌握”和“死记 API”有什么区别？
```

---

### 8. 代表性对象一：Model / Prompt / OutputParser

#### 知识点

1. **ChatModel**
   - 统一不同模型提供方的调用接口
   - 参数透传与 provider 差异

2. **PromptTemplate**
   - 模板化 Prompt
   - 变量注入
   - Prompt 作为可组合组件，而不是纯字符串

3. **OutputParser**
   - 字符串输出
   - 结构化输出
   - 解析失败时的修复思路

4. **这一组抽象解决的问题**
   - 输入组织
   - 模型调用
   - 输出消费

#### 实战案例

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个严谨的技术助理"),
    ("human", "请用三点总结以下主题：{topic}")
])

chain = prompt | llm | StrOutputParser()
result = chain.invoke({"topic": "RAG 的核心组成"})
print(result)
```

---

### 9. 代表性对象二：Runnable 与 LCEL

#### 知识点

1. **Runnable 是什么**
   - LangChain 的统一执行抽象
   - 支持 `invoke / batch / stream`
   - 让不同组件可组合

2. **LCEL（LangChain Expression Language）**
   - 使用 `|` 连接组件
   - 并行与映射组合
   - 将数据流显式表达出来

3. **为什么这是核心**
   - RAG Chain 基本都建立在 Runnable / LCEL 思维上
   - Agent 前的很多业务，其实是更稳定的 Chain 问题

#### 实践练习

```python
# 1. 用 LCEL 组一个：
# prompt -> llm -> parser

# 2. 再加一个预处理函数：
# input -> preprocess -> prompt -> llm -> parser

# 3. 对比：
# 原生 SDK 写法 vs LCEL 写法
```

---

### 10. 代表性对象三：Document / Retriever

#### 知识点

1. **Document 抽象**
   - `page_content`
   - `metadata`
   - 为什么 RAG 工程离不开这两个字段

2. **Retriever 抽象**
   - 检索器是“给定 query，返回相关文档”
   - 向量库只是 retriever 的一个实现来源
   - 混合检索、重排序、本质上都可以挂在检索链路上

3. **这组抽象与 RAG 的关系**
   - `Document` 是知识单元
   - `Retriever` 是知识入口
   - 后续 RAG 课将围绕它们展开

#### 实践练习

```python
# 1. 用自己的话定义 Document 和 Retriever

# 2. 说明：
# 为什么“向量数据库”不等于“完整 RAG”？
```

---

### 11. 代表性对象四：Tool

#### 知识点

1. **Tool 的本质**
   - 给模型一个“可调用能力”
   - 可以是搜索、数据库、HTTP API、文件系统

2. **Tool 与 Retriever 的区别**
   - Retriever 是为知识查询设计的标准接口
   - Tool 更泛化，强调“动作能力”

3. **为什么 Tool 是 Agent 主线的入口**
   - Agent 不是先学“会说话”
   - Agent 是先学“能做事”

#### 实践练习

```python
# 1. 判断以下能力更适合建模为 Retriever 还是 Tool
# - 搜索产品手册
# - 查询天气 API
# - 执行 SQL
# - 读取本地文件
```

---

## 三、LangChain 工程化基础

### 12. 从原生 SDK 迁移到 LangChain 的思维方式

#### 知识点

1. **原生 SDK 的优点**
   - 透明
   - 控制力强
   - 适合入门与定位问题

2. **LangChain 的优点**
   - 组件化
   - 易于复用
   - 便于扩展到 RAG / Agent

3. **迁移原则**
   - 先理解原生调用
   - 再抽象成组件
   - 不为用框架而用框架

#### 实践练习

```python
# 1. 将一个原生 OpenAI SDK 调用，改写为 LangChain 版本

# 2. 列出改写前后：
# 输入、输出、错误处理、扩展性分别有什么变化
```

---

### 13. 可观测性、配置与项目结构

#### 知识点

1. **配置管理**
   - 模型配置
   - 环境变量
   - 开发/测试/生产环境区分

2. **可观测性**
   - 日志
   - Trace
   - Callback
   - LangSmith 的定位

3. **项目结构**
   - prompts/
   - chains/
   - retrievers/
   - tools/
   - services/

4. **面向企业工程的意识**
   - 不把所有逻辑塞进一个脚本
   - 可替换、可测试、可追踪

#### 实践练习

```python
# 1. 为一个小型 LLM 服务设计目录结构

# 2. 设计一个配置类，统一管理模型、温度、超时、重试等参数
```

---

### 综合案例：组件化问答服务雏形

```python
# 实现一个最小但工程化的问答服务雏形
#
# 功能要求：
# 1. 使用 LangChain 封装模型调用
# 2. 使用 PromptTemplate 管理提示词
# 3. 使用 OutputParser 处理输出
# 4. 支持流式输出
# 5. 预留 Retriever / Tool 接口，方便后续扩展到 RAG 和 Agent
#
# 使用示例：
# service = QAServer(model="gpt-4o-mini")
# answer = service.ask("什么是 Transformer？")
#
# 技术要点：
# - ChatModel
# - PromptTemplate
# - Runnable / LCEL
# - 配置管理
# - 日志与错误处理
#
# 学习目标：
# - 看懂 LangChain 的组件组合方式
# - 为后续 RAG 和 Agent 课程建立统一心智模型
```

---

## 学习资源

### 官方文档

- [LangChain Overview](https://python.langchain.com/docs/introduction/)
- [LCEL](https://python.langchain.com/docs/concepts/lcel/)
- [LangChain Expression Language Cheatsheet](https://python.langchain.com/docs/how_to/#langchain-expression-language-lcel)
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)

### 推荐理解材料

- Transformer / Attention 图解类文章
- LoRA / QLoRA 入门文章
- 开源模型推理与部署对比文章

---

## 验收标准

1. **解释** LLM 从输入到输出的大致工作过程
2. **说明** Transformer / Attention 在做什么，以及这对 Prompt / RAG 有什么影响
3. **判断** 什么时候用 Prompt、RAG、长上下文、微调
4. **理解** 开源模型、本地推理、私有化部署、LoRA 的基本概念
5. **掌握** LangChain 的核心抽象：Model、Prompt、Parser、Runnable、Retriever、Tool
6. **能够** 使用 LCEL 组合一个可扩展的小型 LLM 服务
7. **为后续 RAG / Agent 课程建立统一工程心智模型**
