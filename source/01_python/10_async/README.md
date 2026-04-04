# 10. 异步编程 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/01_python/10_async.md) 一步步动手操作

---

## 核心原则

```
读文档 → 看对应代码 → 运行验证 → 理解原理
```

- 在 `source/01_python/10_async/` 目录下操作
- 每个练习文件独立可运行，无包依赖关系
- 练习 1-2 纯本地，练习 3、5 需要联网

---

## 项目结构

```
10_async/
├── README.md                ← 你正在读的这个文件
├── async_basics.py          ← 第 1 步：asyncio 基础（文档第 2-3 章）
├── async_concurrency.py     ← 第 2 步：并发执行（文档第 4 章）
├── async_http.py            ← 第 3 步：异步 HTTP（文档第 5 章）
├── async_file.py            ← 第 4 步：异步文件操作（文档第 6 章）
└── async_llm_race.py        ← 第 5 步：多模型竞速（文档第 7 章）
```

---

## 前置准备

### 安装依赖

```bash
pip install httpx aiofiles
```

### 运行方式

```bash
cd source/01_python/10_async

python async_basics.py          # 无需联网
python async_concurrency.py     # 无需联网
python async_http.py            # 需要联网
python async_file.py            # 需要 aiofiles
python async_llm_race.py        # 需要联网
```

---

## 第 1 步：asyncio 基础（文档第 2-3 章）

**对应文件**：`async_basics.py`
**对应文档**：第 2 章「异步概念」+ 第 3 章「asyncio 基础」

不需要联网。

### 操作流程

1. 读文档 2.1-2.4 节，理解同步 vs 异步、阻塞 vs 非阻塞

2. 读文档 3.1 节「async def 定义协程」，理解关键区别：
   - 调用普通函数 `hello_sync()` → 直接拿到结果
   - 调用协程函数 `hello_async()` → 只拿到协程对象，**还没执行**
   - 必须 `await hello_async()` 才会真正执行

3. 读文档 3.2-3.3 节「await 和 asyncio.run()」

4. 读文档 3.4 节「asyncio.sleep() vs time.sleep()」，这是最常踩的坑：
   - `time.sleep()` 在 async 函数中会**阻塞整个事件循环**
   - `asyncio.sleep()` 只暂停当前协程，其他协程可以继续

5. 运行 `async_basics.py`，看 sleep 对比的耗时输出

6. 读文档 3.5 节「协程不是线程」，理解单线程并发模型

### JS 对照速查

| Python | JavaScript |
|--------|-----------|
| `async def fn()` | `async function fn()` |
| `await coro` | `await promise` |
| `asyncio.run(main())` | 自动运行（浏览器/Node.js） |
| `asyncio.sleep(1)` | `new Promise(r => setTimeout(r, 1000))` |

---

## 第 2 步：并发执行（文档第 4 章）

**对应文件**：`async_concurrency.py`
**对应文档**：第 4 章「并发执行」

不需要联网。

### 操作流程

1. 读文档 4.1 节「asyncio.gather()」—— 并发等待全部完成

2. 打开 `async_concurrency.py`，看 gather 演示：3 个任务分别需要 2s/1s/3s，并发执行总耗时约 3s 而非 6s

3. 读文档 4.2 节「asyncio.create_task()」—— 创建并调度任务，不等待

4. 读文档 4.3 节「asyncio.wait()」—— 灵活等待策略：
   - `FIRST_COMPLETED`：第一个完成就返回（对应 JS 的 `Promise.race`）
   - 可以取消未完成的任务

5. 读文档 4.4 节「asyncio.wait_for()」—— 单任务超时控制

6. 读文档 4.5 节「asyncio.as_completed()」—— 按完成顺序处理

7. 读文档 4.6 节「错误处理」—— `return_exceptions=True` 收集所有结果（包括异常）

8. 运行验证：

```bash
python async_concurrency.py
```

### 关键 API 选择

| 场景 | 用什么 |
|-----|-------|
| 等所有任务完成，拿全部结果 | `asyncio.gather()` |
| 后台跑任务，稍后再等 | `asyncio.create_task()` |
| 谁先完成先处理谁 | `asyncio.wait(FIRST_COMPLETED)` |
| 单任务超时 | `asyncio.wait_for()` |
| 按完成顺序逐个处理 | `asyncio.as_completed()` |

---

## 第 3 步：异步 HTTP（文档第 5 章）

**对应文件**：`async_http.py`
**对应文档**：第 5 章「异步 HTTP（httpx.AsyncClient）」

需要联网。

### 操作流程

1. 读文档 5.1 节「基础用法」，理解 `httpx.AsyncClient` 的用法：
   - `async with httpx.AsyncClient() as client:` 是异步版上下文管理器
   - `as client` 的意思是把客户端对象绑定给变量 `client`
   - 代码块结束后会自动执行异步清理，相当于 `try/finally + await client.aclose()`
   - `await client.get(url)` 异步请求

2. 看 `async_http.py` 中的串行 vs 并发对比——5 个请求：
   - 串行：逐个 await，总耗时 = 所有请求时间之和
   - 并发：`asyncio.gather()` 同时发，总耗时 ≈ 最慢的那个

3. 读文档 5.4 节「Semaphore 控制并发数」—— LLM API 有速率限制，不能同时发太多：
   ```python
   semaphore = asyncio.Semaphore(3)  # 最多同时 3 个请求
   async with semaphore:
       response = await client.get(url)
   ```

4. 运行验证：

```bash
python async_http.py
# 输入 a 运行全部
```

---

## 第 4 步：异步文件操作（文档第 6 章）

**对应文件**：`async_file.py`
**对应文档**：第 6 章「异步文件操作（aiofiles）」

需要安装 aiofiles。

### 操作流程

1. 读文档 6.1-6.2 节，理解 aiofiles 的用法

2. 打开 `async_file.py`，对比同步 open() 和异步 aiofiles.open() 的区别：
   - `with open(...) as f:` 是同步版资源管理
   - `async with aiofiles.open(...) as f:` 是异步版资源管理
   - `async for line in f:` 是异步版逐行迭代

3. 理解什么时候用 aiofiles：

| 场景 | 推荐 |
|-----|------|
| 普通脚本读写文件 | 同步 `open()` |
| FastAPI 请求中读写大文件 | `aiofiles` |
| 读取配置文件 | 同步 `open()` |

4. 运行验证：

```bash
python async_file.py
```

---

## 第 5 步：多模型竞速实战（文档第 7 章）

**对应文件**：`async_llm_race.py`
**对应文档**：第 7 章「实战：模拟 LLM API 并发竞速」

需要联网。这是本节最重要的练习。

### 操作流程

1. 读文档第 7 章，理解「多模型竞速」的概念：同时请求多个 LLM，谁先返回用谁的结果

2. 打开 `async_llm_race.py`，看核心逻辑：
   - 同时请求 3 个模型（OpenAI/Claude/DeepSeek），模拟不同延迟
   - `asyncio.wait(FIRST_COMPLETED)` 拿最快的结果
   - `task.cancel()` 取消剩余请求（省钱）

3. 看 Semaphore 限速的批量请求——防止触发 API 限速

4. 运行验证：

```bash
python async_llm_race.py
# 输入 a 运行全部
```

---

## 文档章节与文件对应表

| 文档章节 | 核心内容 | 对应文件 | 联网 |
|---------|---------|---------|------|
| 第 2-3 章 | async/await 基础、asyncio.run、sleep 对比 | `async_basics.py` | 否 |
| 第 4 章 | gather/create_task/wait/as_completed 并发模式 | `async_concurrency.py` | 否 |
| 第 5 章 | httpx.AsyncClient、串行 vs 并发、Semaphore | `async_http.py` | 是 |
| 第 6 章 | aiofiles 异步文件读写 | `async_file.py` | 否 |
| 第 7 章 | 多模型竞速、批量限速、超时 fallback | `async_llm_race.py` | 是 |

---

## 学习顺序总结

| 顺序 | 文件 | 核心内容 | 联网 | 运行命令 |
|-----|------|---------|------|---------|
| 1 | `async_basics.py` | async/await/sleep 对比 | 否 | `python async_basics.py` |
| 2 | `async_concurrency.py` | gather/wait/create_task | 否 | `python async_concurrency.py` |
| 3 | `async_http.py` | 异步 HTTP、串行 vs 并发 | 是 | `python async_http.py` |
| 4 | `async_file.py` | aiofiles 异步文件 | 否 | `python async_file.py` |
| 5 | `async_llm_race.py` | 多模型竞速实战 | 是 | `python async_llm_race.py` |

---

## 注意事项

- **练习 1-2 可以离线完成**，优先从这两个开始
- `time.sleep()` 在 async 函数中会阻塞事件循环，**永远用 `asyncio.sleep()`**
- 调用 `async def` 函数不加 `await`，协程不会执行，会有 RuntimeWarning
- `asyncio.run()` 只能在最外层调用，不能在 `async def` 中嵌套使用
- Jupyter Notebook 中自带事件循环，直接 `await` 即可，不需要 `asyncio.run()`
