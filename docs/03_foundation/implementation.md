# 03 Foundation 实施方案

> 目标：把 `03_foundation` 做成一个独立、轻量、可运行的基础实验项目，用最小代码验证 LLM 原理理解与 LangChain 核心抽象，为 `04_rag` 和 `05_agent` 建立统一工程心智模型

---

## 一、项目定位

- 项目名称：`foundation_lab`
- 项目类型：独立学习项目，不是业务产品
- 项目目的：
  - 理解 LLM 应用开发者需要掌握的原理边界
  - 理解 LangChain 的核心抽象与组合方式
  - 用最小工程骨架验证 `Model / Prompt / Parser / Runnable / Retriever / Tool`
  - 为后续 `04_rag` 和 `05_agent` 提供结构迁移经验

### 不做什么

- 不做完整 RAG 项目
- 不做完整 Agent 项目
- 不接真实向量数据库
- 不做复杂前端
- 不做重部署和复杂基础设施

---

## 二、交付物

### 必须交付

1. 一个最小可运行的问答服务
2. 一个原生 SDK 与 LangChain 的对照实现
3. 一个最小 LCEL Chain
4. 一个 `mock_retriever`
5. 一个 `mock_tool`
6. 一个最小 FastAPI 接口
7. 一份短 README，说明项目定位、结构和运行方式

### 可选交付

- 一个简单的分类 Chain
- 一个结构化输出示例
- 一个简单的日志与配置封装

---

## 三、目录规划

代码放在：

```plain
source/03_foundation/foundation_lab/
```

建议结构：

```plain
foundation_lab/
├── app/
│   ├── config.py
│   ├── main.py
│   ├── schemas.py
│   ├── llm/
│   │   ├── client_native.py
│   │   └── client_langchain.py
│   ├── prompts/
│   │   ├── qa_prompt.py
│   │   └── classify_prompt.py
│   ├── chains/
│   │   ├── qa_chain.py
│   │   └── classify_chain.py
│   ├── retrievers/
│   │   └── mock_retriever.py
│   ├── tools/
│   │   └── mock_tools.py
│   ├── services/
│   │   └── qa_service.py
│   └── observability/
│       └── logger.py
├── scripts/
│   ├── demo_native.py
│   ├── demo_langchain.py
│   └── compare_native_vs_lc.py
├── tests/
│   ├── test_prompt_format.py
│   ├── test_mock_retriever.py
│   └── test_mock_tools.py
└── README.md
```

---

## 四、学习与实施边界

### 4.1 原理部分：重理解，轻代码

对应：

- `1. 从下一个 Token 预测理解 LLM`
- `2. Transformer 与 Attention 直觉`
- `3. 模型训练生命周期`
- `4. 微调、RAG、长上下文如何选择`
- `5. 开源模型、私有化部署与本地推理认知`
- `6. 微调认知入门`

实施方式：

- 以文档理解和笔记为主
- 用自己的话总结关键判断
- 不做底层算法实现
- 不尝试训练或复现模型结构

这一部分的产出：

- 一页到两页判断笔记
- 能口头说明：
  - 为什么 Prompt 会影响输出
  - 为什么上下文组织影响结果
  - 为什么知识更新优先考虑 RAG
  - 为什么 Agent 不是普通聊天接口

### 4.2 LangChain 抽象部分：必须动手

对应：

- `7. 为什么要学 LangChain`
- `8. Model / Prompt / OutputParser`
- `9. Runnable 与 LCEL`
- `10. Document / Retriever`
- `11. Tool`
- `12. 从原生 SDK 迁移到 LangChain`
- `13. 可观测性、配置与项目结构`

实施方式：

- 每一个代表性抽象都至少写一个最小示例
- 所有示例尽量围绕同一套小项目骨架组织
- 重点理解：
  - 输入如何组织
  - 输出如何消费
  - 组件如何组合
  - 原生 SDK 与 LangChain 的差异是什么

---

## 五、实施阶段

### Phase 1：原理判断与短笔记

目标：

- 完成原理部分的学习
- 输出自己的判断，而不是摘抄概念

任务：

1. 总结 LLM 从输入到输出的最小数据流
2. 写一页“Prompt / RAG / 长上下文 / 微调”的选型说明
3. 写一页“开源模型 / API 模型 / 私有化部署”的认知边界说明

完成标准：

- 能脱离文档复述关键概念
- 能判断一个需求更适合 Prompt、RAG 还是微调

### Phase 2：原生 SDK 最小实现

目标：

- 用原生 SDK 做一个最小问答服务

任务：

1. 实现一个最小 `chat()` 调用
2. 实现一个结构化输出示例
3. 实现一个流式输出示例
4. 暴露一个最小 FastAPI `/ask` 接口

完成标准：

- 知道“不用 LangChain 时自己要写哪些胶水代码”

### Phase 3：LangChain 等价重写

目标：

- 用 LangChain 重写同类能力

任务：

1. 使用 `ChatModel`
2. 使用 `PromptTemplate`
3. 使用 `OutputParser`
4. 使用 `LCEL` 组装一个最小 Chain
5. 支持 `invoke` 与 `stream`

完成标准：

- 能明确说明 LangChain 在工程复用上的价值

### Phase 4：抽象边界验证

目标：

- 区分 `Retriever` 和 `Tool`
- 建立统一 service 层思维

任务：

1. 实现 `mock_retriever`
2. 实现 `mock_tool`
3. 实现一个统一的 `qa_service`
4. 用脚本对比普通问答、检索问答、工具调用三种路径

完成标准：

- 能清楚解释：
  - `Retriever` 是知识入口
  - `Tool` 是动作能力
  - `Service` 是业务编排层

### Phase 5：工程化收口

目标：

- 把项目收成一个可复用的小骨架

任务：

1. 增加配置管理
2. 增加最小日志
3. 增加轻量测试
4. 写 README
5. 清理脚本和目录

完成标准：

- 项目能独立运行
- 目录职责清晰
- 为 `04` 和 `05` 提供结构参考

---

## 六、文件级任务清单

### app/config.py

- 管理模型名、base URL、超时、重试、是否开启流式

### app/llm/client_native.py

- 原生 OpenAI SDK 风格调用
- 提供普通调用与流式调用

### app/llm/client_langchain.py

- LangChain `ChatModel` 调用封装

### app/prompts/qa_prompt.py

- 最小问答 Prompt

### app/chains/qa_chain.py

- `prompt -> llm -> parser`

### app/retrievers/mock_retriever.py

- 从预置文档中按关键词或简单规则返回结果

### app/tools/mock_tools.py

- 至少提供一个简单工具：
  - 计算器
  - 当前时间
  - 模拟规则查询

### app/services/qa_service.py

- 统一接收问题
- 决定走普通问答、检索增强还是工具能力

### app/main.py

- 暴露最小 API：
  - `POST /ask`
  - `POST /ask/stream`

### scripts/compare_native_vs_lc.py

- 对同一输入分别走原生 SDK 和 LangChain
- 对比输入组织、输出处理、扩展性

---

## 七、时间建议

建议控制在 `5-7` 天有效学习量内完成。

### 第 1-2 天

- 学完原理部分
- 写判断笔记

### 第 3 天

- 原生 SDK 最小问答服务

### 第 4 天

- LangChain 重写
- 完成 LCEL Chain

### 第 5 天

- `mock_retriever`
- `mock_tool`
- `qa_service`

### 第 6 天

- FastAPI 接口
- 配置与日志
- README

### 第 7 天

- 复盘
- 整理遗留问题
- 准备切到 `04_rag`

---

## 八、验收标准

1. 能解释 LLM 从输入到输出的大致过程
2. 能判断 Prompt、RAG、长上下文、微调的适用边界
3. 能用原生 SDK 写一个最小问答服务
4. 能用 LangChain 写出等价版本
5. 能用 LCEL 组一个最小可扩展 Chain
6. 能清楚区分 `Prompt / Chain / Retriever / Tool / Service`
7. 能把 `foundation_lab` 当作独立项目讲清楚

---

## 九、和 04、05 的关系

- `03`、`04`、`05` 是三个独立项目
- 不要求直接复制代码
- 允许迁移的是：
  - 命名习惯
  - 分层方式
  - 配置管理方式
  - Prompt 管理方式
  - 可观测性意识

一句话总结：

- `03` 解决“抽象和工程骨架”
- `04` 解决“RAG 真正落地”
- `05` 解决“Agent 与工作流真正落地”
