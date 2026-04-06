# 02. 多平台模型接入与统一抽象 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/02_llm/02_multi_provider.md) 一步步动手操作

---

## 核心原则

```text
读文档 -> 看 provider 差异 -> 看请求预览 -> 运行代码 -> 总结哪些差异该抽象、哪些不该
```

- 在 `source/02_llm/02_multi_provider/` 目录下操作
- 这一章的重点不是“平台百科”，而是理解如何把平台差异收敛到底层抽象
- 有真实 API Key 时优先用百炼 / 通义、DeepSeek、GLM 做真实实验
- 没有配置时，也能通过预览和 mock 走通学习链路

---

## 项目结构

```text
02_multi_provider/
├── README.md                  ← 你正在读的这个文件
├── .env.example               ← 多平台环境变量模板
├── provider_utils.py          ← 本章公共工具：注册表、能力矩阵、请求预览、统一客户端
├── 01_openai_compatible.py    ← 第 1 步：同一套 OpenAI SDK 切换不同平台（文档第 2、4 章）
├── 02_provider_config.py      ← 第 2 步：provider 配置层与能力矩阵（文档第 4-5 章）
└── 03_unified_client.py       ← 第 3 步：统一客户端设计（文档第 6 章）
```

---

## 前置准备

### 1. 安装依赖

```bash
pip install openai python-dotenv
```

### 2. 配置环境变量

把 `.env.example` 复制为 `.env` 后填写。

本章建议优先完成两类实验：

1. 用国内 OpenAI-compatible 平台做真实调用
2. 用 Claude / Gemini 的扩展位理解“并不是所有平台都长一样”

### 3. 运行方式

```bash
cd source/02_llm/02_multi_provider

python 01_openai_compatible.py
python 02_provider_config.py
python 03_unified_client.py
```

---

## 第 1 步：同一套 OpenAI SDK 切换平台（文档第 2、4 章）

**对应文件**：`01_openai_compatible.py`  
**对应文档**：第 2 章「为什么 OpenAI SDK 可以作为统一入口」+ 第 4 章「国内平台与 OpenAI-compatible 接入」

### 操作流程

1. 先读文档第 2 章，理解为什么课程里优先使用 OpenAI SDK 风格。
2. 再读文档第 4 章，理解 OpenAI-compatible 的工程意义。
3. 运行：

```bash
python 01_openai_compatible.py
```

### 重点看什么

- `build_demo_request()`：同一份 messages 请求
- `print_registered_providers()`：当前已注册 provider 概览
- `print_same_sdk_different_configs()`：同一调用形状如何随着 `base_url / model` 改变
- `run_default_provider_demo()`：默认 provider 的真实或 mock 调用

### 重点观察

- 为什么 request shape 几乎不变
- 为什么真正变化的是配置而不是业务逻辑
- 如果默认 provider 已就绪，真实 response_preview 长什么样

---

## 第 2 步：配置层与能力矩阵（文档第 4-5 章）

**对应文件**：`02_provider_config.py`  
**对应文档**：第 4 章「平台配置设计」+ 第 5 章「哪些差异该进配置层」

### 操作流程

1. 运行：

```bash
python 02_provider_config.py
```

2. 这个脚本不依赖真实 API，它的目标是让你真正看懂：
   - provider 能力矩阵
   - 环境变量和默认值映射
   - OpenAI / Claude / Gemini 的请求预览差异

### 重点观察

- `openai_compatible=True` 和 `False` 的差异意味着什么
- 哪些字段属于“平台能力”
- 为什么 system 的组织方式会影响抽象设计

### 建议主动修改

- 给 provider registry 新增一个平台
- 修改某个平台的能力矩阵
- 对比 preview 是否真的会变化

---

## 第 3 步：统一客户端（文档第 6 章）

**对应文件**：`03_unified_client.py`  
**对应文档**：第 6 章「从 provider 配置走向统一客户端」

### 操作流程

1. 运行：

```bash
python 03_unified_client.py
```

2. 重点看三段演示：
   - `demo_default_client()`：统一客户端的 request / response / debug 输出
   - `demo_switch_provider()`：切换 provider 的行为变化
   - `demo_messages_level_api()`：为什么统一抽象必须以 `messages` 为核心输入

### 重点观察

- `client.describe()` 输出了哪些关键信息
- `UnifiedLLMClient.chat()` 为什么接受 `ChatRequest` 而不是一个裸字符串
- retry、timeout、debug 为什么应该放在统一客户端层
- Claude 扩展位为什么现在只做 preview / placeholder

---

## 文档章节与文件对应表

| 文档章节 | 核心内容 | 对应文件 |
|---------|---------|---------|
| 第 2 章 | OpenAI SDK 作为统一入口 | `01_openai_compatible.py` |
| 第 3 章 | 平台差异具体落在哪里 | `02_provider_config.py` |
| 第 4-5 章 | OpenAI-compatible 平台与配置层 | `provider_utils.py`, `02_provider_config.py` |
| 第 6 章 | 统一客户端与抽象边界 | `03_unified_client.py`, `provider_utils.py` |

---

## 建议的学习顺序

1. 先看 `01_openai_compatible.py`
2. 再看 `02_provider_config.py`
3. 最后重点看 `03_unified_client.py`

这三步分别回答三个问题：

1. 我能不能切平台？
2. 平台差异到底落在哪里？
3. 我该把这些差异怎么收进一个统一客户端？

---

## 常见问题

### 1. 第二章一定要把 Claude / Gemini 真接进去吗？

不需要。第二章的重点是把接口差异讲明白，把抽象边界设计清楚，不是把所有平台都真正接完。

### 2. 为什么统一客户端不能只写成 `chat(prompt: str)`？

因为真正的聊天模型输入核心是 `messages`。如果你第二章就把抽象降级成字符串，后面做多轮、结构化输出、流式会很容易返工。

### 3. OpenAI-compatible 平台是不是就一定完全兼容？

不是。很多平台是“高相似度兼容”，但不一定 100% 一样。真正工程里仍然要留出差异处理空间，这正是第二章要学的重点。
