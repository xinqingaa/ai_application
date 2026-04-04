# 10. 异步编程

> 本节目标：掌握 Python 异步编程，为 LLM API 并发调用和流式响应打基础

---

## 1. 概述

### 学习目标

- 理解同步 vs 异步、阻塞 vs 非阻塞的区别
- 掌握 async def / await / asyncio.run 基础语法
- 掌握 asyncio.gather / create_task / wait 并发模式
- 掌握 httpx.AsyncClient 异步 HTTP 请求
- 了解 aiofiles 异步文件操作
- 能实现并发 API 调用和竞速模式

### 预计学习时间

- 异步概念：30 分钟
- asyncio 基础：1 小时
- 并发执行：1 小时
- 异步 HTTP：30 分钟
- 异步文件操作：15 分钟
- 练习：1-2 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|------|---------|
| 并发调用多个 LLM API | asyncio.gather / create_task |
| 多模型竞速（返回最快） | asyncio.wait + FIRST_COMPLETED |
| 流式响应（SSE） | async for + httpx 流式 |
| 多用户并发（FastAPI） | async def 路由处理函数 |
| 控制 API 请求频率 | asyncio.Semaphore |
| 超时控制 | asyncio.wait_for |

> **异步是 AI 应用开发的核心技能**。LLM API 响应通常需要几秒到几十秒，同步调用会阻塞整个程序。异步让你在等待模型响应时可以同时处理其他请求。

---

## 2. 异步概念 📌

### 2.1 同步 vs 异步

**同步**：一个任务完成后才开始下一个，串行执行。

```
同步（串行）：
  调用 OpenAI  ────────→ 等 3 秒 → 拿到结果
                                            调用 Claude ────────→ 等 2 秒 → 拿到结果
                                                                                    总耗时：5 秒
```

**异步**：发起任务后不等待，继续做别的事，结果好了再回来处理。

```
异步（并发）：
  调用 OpenAI  ────────→ 等 3 秒 → 拿到结果
  调用 Claude  ────────→ 等 2 秒 → 拿到结果
                                            总耗时：3 秒（取决于最慢的）
```

**类比：餐厅点餐**

| 模式 | 行为 | 效率 |
|------|------|------|
| 同步 | 服务员给 A 点完餐，等 A 的菜上了，再去给 B 点餐 | 很低 |
| 异步 | 服务员给 A 点完餐，立刻去给 B 点餐，菜好了再分别端上来 | 很高 |

### 2.2 阻塞 vs 非阻塞

```python
import time
import asyncio

# 阻塞：time.sleep 会卡住整个程序
time.sleep(3)  # 什么都做不了，傻等 3 秒

# 非阻塞：asyncio.sleep 只暂停当前协程，其他协程可以继续执行
await asyncio.sleep(3)  # 当前协程暂停，事件循环可以处理其他任务
```

### 2.3 为什么 AI 应用需要异步

1. **LLM API 响应慢**：一次请求可能 3-30 秒，同步调用会阻塞服务器
2. **需要并发**：同时请求多个模型、处理多个用户请求
3. **流式输出**：LLM 逐字输出，需要异步迭代接收
4. **成本优化**：多模型竞速，选最快的结果

### 2.4 与 JavaScript 的异步对比

| 差异点 | JavaScript | Python |
|--------|-----------|--------|
| 异步模型 | 天然单线程异步（Event Loop 自动运行） | 需要显式启动事件循环（asyncio.run） |
| 语法 | `async function` / `await` | `async def` / `await` |
| 返回值 | `Promise` | `Coroutine`（协程对象） |
| 并发 | `Promise.all([...])` | `asyncio.gather(...)` |
| 竞速 | `Promise.race([...])` | `asyncio.wait(..., FIRST_COMPLETED)` |
| 事件循环 | 浏览器/Node.js 自动管理 | 需要 `asyncio.run()` 手动启动 |

> **关键区别**：JS 中调用 `async function` 会自动开始执行并返回 Promise。Python 中调用 `async def` 只返回一个协程对象，必须 `await` 或丢给事件循环才会真正执行。

---

## 3. asyncio 基础 📌

### 3.1 async def 定义协程

```python
import asyncio

# 普通函数
def hello_sync():
    return "hello"

# 协程函数（用 async def 定义）
async def hello_async():
    return "hello"

# 调用区别
result = hello_sync()       # 直接得到 "hello"
coro = hello_async()        # 得到 <coroutine object>，还没执行！
result = await hello_async() # await 后才真正执行，得到 "hello"
```

### 3.2 await 等待协程

`await` 只能在 `async def` 函数内部使用。

```python
import asyncio

async def fetch_data():
    print("开始获取数据...")
    await asyncio.sleep(2)  # 模拟网络请求，暂停 2 秒
    print("数据获取完成")
    return {"name": "AI"}

async def main():
    # await 会暂停当前协程，等待结果
    data = await fetch_data()
    print(f"结果: {data}")

asyncio.run(main())
```

### 3.3 asyncio.run() 运行入口

`asyncio.run()` 是启动异步程序的入口，它会创建事件循环并运行协程。

```python
import asyncio

async def main():
    print("异步程序开始")
    await asyncio.sleep(1)
    print("异步程序结束")

# 程序入口：启动事件循环，运行 main 协程
asyncio.run(main())
```

> **注意**：`asyncio.run()` 只能在同步代码中调用（即最外层），不能在 `async def` 中嵌套使用。

### 3.4 asyncio.sleep() vs time.sleep()

```python
import asyncio
import time

async def demo_sleep():
    # ❌ time.sleep 会阻塞整个事件循环
    # 其他协程也无法执行
    time.sleep(1)  # 不要在 async 函数中用这个

    # ✅ asyncio.sleep 只暂停当前协程
    # 事件循环可以去执行其他协程
    await asyncio.sleep(1)  # 用这个
```

> **记住**：在 `async def` 中，所有"等待"操作都应该用异步版本（`asyncio.sleep` 而非 `time.sleep`，`httpx.AsyncClient` 而非 `httpx.get`）。

### 3.5 协程不是线程

Python 的 asyncio 是**单线程并发**——只有一个线程，通过事件循环切换不同协程。

```
事件循环（单线程）：
  ┌─ 协程A: 发请求 → 等待响应... → 收到响应 → 处理 ─┐
  │  协程B:            发请求 → 等待... → 收到 → 处理 │
  └─ 协程C:            发请求 → 等... → 收到 → 处理 ──┘
  
  等待期间，事件循环自动切换到其他协程
  所有协程共享同一个线程
```

---

## 4. 并发执行 📌

### 4.1 asyncio.gather() — 并发等待全部完成

```python
import asyncio

async def task(name: str, seconds: float) -> str:
    print(f"  {name}: 开始（需要 {seconds}s）")
    await asyncio.sleep(seconds)
    print(f"  {name}: 完成")
    return f"{name} 的结果"

async def main():
    # gather：并发执行，等待全部完成
    results = await asyncio.gather(
        task("任务A", 2),
        task("任务B", 1),
        task("任务C", 3),
    )
    print(f"  全部完成: {results}")
    # 总耗时约 3 秒（最慢的那个），不是 6 秒

asyncio.run(main())
```

> **对应 JS**：`asyncio.gather(a, b, c)` ≈ `Promise.all([a, b, c])`

### 4.2 asyncio.create_task() — 创建并调度任务

```python
import asyncio

async def background_job(name: str):
    await asyncio.sleep(2)
    print(f"  后台任务 {name} 完成")

async def main():
    # create_task：立即开始执行，不等待
    task1 = asyncio.create_task(background_job("A"))
    task2 = asyncio.create_task(background_job("B"))

    print("  任务已创建，继续做别的事...")
    await asyncio.sleep(1)
    print("  1 秒后：任务还在后台跑")

    # 等待任务完成
    await task1
    await task2
    print("  所有任务完成")

asyncio.run(main())
```

### 4.3 asyncio.wait() — 灵活等待策略

```python
import asyncio

async def api_call(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"{name} 响应（{delay}s）"

async def main():
    tasks = [
        asyncio.create_task(api_call("OpenAI", 3)),
        asyncio.create_task(api_call("Claude", 1)),
        asyncio.create_task(api_call("DeepSeek", 2)),
    ]

    # FIRST_COMPLETED：第一个完成就返回
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    for task in done:
        print(f"  最快完成: {task.result()}")

    # 取消剩余任务
    for task in pending:
        task.cancel()
    print(f"  已取消 {len(pending)} 个未完成任务")

asyncio.run(main())
```

> **对应 JS**：`asyncio.wait(tasks, FIRST_COMPLETED)` ≈ `Promise.race([...])`

### 4.4 asyncio.wait_for() — 单任务超时

```python
import asyncio

async def slow_task():
    await asyncio.sleep(10)
    return "完成"

async def main():
    try:
        result = await asyncio.wait_for(slow_task(), timeout=3.0)
        print(f"结果: {result}")
    except asyncio.TimeoutError:
        print("任务超时（3 秒内未完成）")

asyncio.run(main())
```

### 4.5 asyncio.as_completed() — 按完成顺序处理

```python
import asyncio

async def fetch(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"{name}（{delay}s）"

async def main():
    coros = [fetch("A", 3), fetch("B", 1), fetch("C", 2)]

    # 按完成顺序逐个处理
    for coro in asyncio.as_completed(coros):
        result = await coro
        print(f"  完成: {result}")
    # 输出顺序：B（1s）→ C（2s）→ A（3s）

asyncio.run(main())
```

### 4.6 错误处理

```python
import asyncio

async def might_fail(name: str, fail: bool) -> str:
    await asyncio.sleep(0.5)
    if fail:
        raise ValueError(f"{name} 失败了")
    return f"{name} 成功"

async def main():
    # return_exceptions=True：异常作为返回值，不会中断其他任务
    results = await asyncio.gather(
        might_fail("A", fail=False),
        might_fail("B", fail=True),
        might_fail("C", fail=False),
        return_exceptions=True,
    )

    for r in results:
        if isinstance(r, Exception):
            print(f"  异常: {r}")
        else:
            print(f"  成功: {r}")

asyncio.run(main())
```

---

## 5. 异步 HTTP（httpx.AsyncClient） 📌

> 承接第 9 节的 httpx 异步预览，这里深入讲解。

### 5.1 基础用法

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://httpbin.org/get")
        print(response.json())

asyncio.run(main())
```

`async with` 是 **异步版的上下文管理器**。

如果你已经学过第 3 章的 `with open(...) as file:`，可以直接这样类比：

- `with`：进入代码块前打开普通资源，退出时自动清理
- `async with`：进入代码块前打开**异步资源**，退出时用 `await` 自动清理

先看语法骨架：

```python
async with 表达式 as 变量:
    代码块
```

放到 `httpx` 里就是：

```python
async with httpx.AsyncClient() as client:
    response = await client.get("https://httpbin.org/get")
```

你可以先这样理解：

- `httpx.AsyncClient()`：创建异步 HTTP 客户端
- `as client`：把客户端对象绑定给变量 `client`
- 缩进代码块：在客户端可用期间发送请求
- 代码块结束后：自动关闭客户端和连接池

它本质上很像下面这段手写版：

```python
client = httpx.AsyncClient()
try:
    response = await client.get("https://httpbin.org/get")
finally:
    await client.aclose()
```

也就是说，`async with` 可以先理解成：

- 异步版的 `try/finally`
- 重点是自动资源清理
- 和 `asyncio.gather()` 的“并发”不是一回事

更底层一点说：

- `with` 背后依赖 `__enter__()` / `__exit__()`
- `async with` 背后依赖 `__aenter__()` / `__aexit__()`

> **为什么这里必须写 `async with`，不能写普通 `with`？**
>
> 因为 `AsyncClient` 的关闭动作本身是异步的，需要 `await client.aclose()`。普通 `with` 处理不了这种异步清理逻辑。

### 5.2 并发请求多个 URL

```python
import httpx
import asyncio
import time

async def fetch_url(client: httpx.AsyncClient, url: str) -> dict:
    response = await client.get(url, timeout=10.0)
    return {"url": url, "status": response.status_code}

async def main():
    urls = [
        "https://httpbin.org/get?id=1",
        "https://httpbin.org/get?id=2",
        "https://httpbin.org/get?id=3",
        "https://httpbin.org/get?id=4",
        "https://httpbin.org/get?id=5",
    ]

    async with httpx.AsyncClient() as client:
        # 并发请求
        start = time.time()
        tasks = [fetch_url(client, url) for url in urls]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

    for r in results:
        print(f"  {r['url']} → {r['status']}")
    print(f"  并发耗时: {elapsed:.2f}s")

asyncio.run(main())
```

### 5.3 串行 vs 并发对比

```python
import httpx
import asyncio
import time

async def compare():
    urls = [f"https://httpbin.org/delay/1?id={i}" for i in range(3)]

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 串行
        start = time.time()
        for url in urls:
            await client.get(url)
        serial_time = time.time() - start

        # 并发
        start = time.time()
        await asyncio.gather(*[client.get(url) for url in urls])
        concurrent_time = time.time() - start

    print(f"  串行: {serial_time:.2f}s")
    print(f"  并发: {concurrent_time:.2f}s")
    print(f"  提速: {serial_time / concurrent_time:.1f}x")

asyncio.run(compare())
```

### 5.4 Semaphore 控制并发数

LLM API 通常有速率限制，不能同时发太多请求。

```python
import httpx
import asyncio

async def fetch_with_limit(
    client: httpx.AsyncClient,
    url: str,
    semaphore: asyncio.Semaphore,
) -> dict:
    async with semaphore:  # 限制同时执行的数量
        response = await client.get(url, timeout=10.0)
        return response.json()

async def main():
    semaphore = asyncio.Semaphore(3)  # 最多同时 3 个请求
    urls = [f"https://httpbin.org/get?id={i}" for i in range(10)]

    async with httpx.AsyncClient() as client:
        tasks = [fetch_with_limit(client, url, semaphore) for url in urls]
        results = await asyncio.gather(*tasks)

    print(f"  完成 {len(results)} 个请求（最多同时 3 个）")

asyncio.run(main())
```

---

## 6. 异步文件操作（aiofiles） ⚡

> 大多数场景同步文件操作就够用。只有在异步上下文中（如 FastAPI 请求处理）需要读写大文件时，才需要 aiofiles。

### 6.1 安装

```bash
pip install aiofiles
```

### 6.2 基础用法

```python
import aiofiles
import asyncio

async def main():
    # 异步写入
    async with aiofiles.open("test.txt", "w", encoding="utf-8") as f:
        await f.write("Hello, 异步文件操作！\n")
        await f.write("第二行\n")

    # 异步读取
    async with aiofiles.open("test.txt", "r", encoding="utf-8") as f:
        content = await f.read()
        print(content)

    # 异步逐行读取
    async with aiofiles.open("test.txt", "r", encoding="utf-8") as f:
        async for line in f:
            print(f"  行: {line.strip()}")

asyncio.run(main())
```

这里顺便注意两种异步语法：

- `async with aiofiles.open(...) as f`
  异步版资源管理，代码块结束后自动关闭文件
- `async for line in f`
  异步版 `for`，逐个等待异步迭代结果

可以先把它们类比成：

- `with` -> `async with`
- `for` -> `async for`

只是后者都是给“异步对象”用的。

### 6.3 什么时候用 aiofiles

| 场景 | 推荐 |
|------|------|
| 脚本中读写文件 | 同步 `open()` 就够了 |
| FastAPI 中保存上传文件 | aiofiles（避免阻塞事件循环） |
| 异步上下文中读写大文件 | aiofiles |
| 读取配置文件 | 同步 `open()` |

---

## 7. 实战：模拟 LLM API 并发竞速 📌 🔗

多模型竞速：同时请求多个 LLM，谁先返回用谁的结果。

```python
import httpx
import asyncio

async def call_model(
    client: httpx.AsyncClient,
    model: str,
    delay: float,
) -> dict:
    """模拟调用 LLM API（用 httpbin.org/delay 模拟延迟）"""
    response = await client.get(
        f"https://httpbin.org/delay/{delay}",
        params={"model": model},
    )
    return {"model": model, "delay": delay, "status": response.status_code}

async def race_models():
    """并发调用多个模型，返回最快的结果"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = {
            asyncio.create_task(call_model(client, "OpenAI", 3)): "OpenAI",
            asyncio.create_task(call_model(client, "Claude", 1)): "Claude",
            asyncio.create_task(call_model(client, "DeepSeek", 2)): "DeepSeek",
        }

        done, pending = await asyncio.wait(
            tasks.keys(),
            return_when=asyncio.FIRST_COMPLETED,
        )

        # 拿到最快的结果
        winner = done.pop()
        result = winner.result()
        print(f"  最快: {result['model']}（{result['delay']}s）")

        # 取消剩余请求（省钱）
        for task in pending:
            task.cancel()
        print(f"  已取消 {len(pending)} 个慢请求")

asyncio.run(race_models())
```

---

## 8. 小结

### 核心知识

| 知识点 | 优先级 | 一句话总结 |
|--------|-------|-----------|
| async def / await | 📌 | 定义协程函数、等待协程结果 |
| asyncio.run() | 📌 | 异步程序的入口，启动事件循环 |
| asyncio.sleep() | 📌 | 异步等待，不阻塞事件循环（替代 time.sleep） |
| asyncio.gather() | 📌 | 并发执行多个协程，等待全部完成 |
| asyncio.create_task() | 📌 | 创建任务并立即调度执行 |
| asyncio.wait() | 📌 | 灵活等待策略，FIRST_COMPLETED 实现竞速 |
| asyncio.wait_for() | 📌 | 单任务超时控制 |
| asyncio.Semaphore | 📌 | 限制并发数，防止触发 API 限速 |
| httpx.AsyncClient | 📌 | 异步 HTTP 客户端，AI 应用必备 |
| aiofiles | ⚡ | 异步文件读写，FastAPI 场景使用 |

### 与 JavaScript 关键差异

| 差异点 | JavaScript | Python |
|--------|-----------|--------|
| 定义异步函数 | `async function fn()` | `async def fn()` |
| 等待结果 | `await promise` | `await coroutine` |
| 返回类型 | `Promise` | `Coroutine` |
| 并发全部 | `Promise.all([a, b])` | `asyncio.gather(a, b)` |
| 竞速 | `Promise.race([a, b])` | `asyncio.wait(tasks, FIRST_COMPLETED)` |
| 任意一个成功 | `Promise.any([a, b])` | 无直接对应，用 wait + 手动处理 |
| 事件循环 | 自动运行 | 需要 `asyncio.run()` 启动 |
| 调用但不等待 | 返回 Promise 自动执行 | 协程不自动执行，需 `create_task` |
| 顶层 await | Node.js ESM 支持 | Python 3.10+ 仅 REPL 支持 |

### 下一节预告

下一节 **FastAPI 基础**（第 11 节）将用今天学到的异步技能构建 API 服务器。FastAPI 的路由处理函数就是 `async def`。

---

## 9. 常见问题

### Q: 忘记写 await 会怎样？

协程不会执行，Python 会给出警告：

```python
async def fetch():
    return "data"

async def main():
    fetch()  # ❌ RuntimeWarning: coroutine 'fetch' was never awaited
    result = await fetch()  # ✅
```

### Q: 可以在普通函数中用 await 吗？

不行。`await` 只能在 `async def` 函数中使用：

```python
def sync_function():
    await asyncio.sleep(1)  # ❌ SyntaxError

async def async_function():
    await asyncio.sleep(1)  # ✅
```

### Q: asyncio.gather 中一个任务失败了怎么办？

默认会抛出异常，中断其他任务。加 `return_exceptions=True` 可以收集所有结果（包括异常）：

```python
results = await asyncio.gather(
    task_a(),
    task_b(),  # 这个可能失败
    task_c(),
    return_exceptions=True,
)
# results 中失败的项是 Exception 对象，成功的是正常返回值
```

### Q: 什么时候用 gather，什么时候用 create_task + wait？

- **gather**：简单场景，等所有任务完成，拿全部结果
- **create_task + wait**：需要灵活控制——谁先完成先处理谁、取消未完成的任务

```python
# 全要 → gather
results = await asyncio.gather(call_a(), call_b(), call_c())

# 只要最快的 → wait
tasks = [asyncio.create_task(c) for c in [call_a(), call_b(), call_c()]]
done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
```

### Q: 为什么不用多线程 / 多进程？

对于 **I/O 密集型**任务（网络请求、文件读写），asyncio 更轻量：

| 方案 | 适用场景 | 开销 |
|------|---------|------|
| asyncio | I/O 密集（API 调用、文件读写） | 极小（单线程） |
| threading | I/O 密集 + 少量 CPU | 中等（线程切换） |
| multiprocessing | CPU 密集（数据处理、计算） | 较大（进程创建） |

AI 应用主要是 I/O 密集（等待 LLM API 响应），所以 asyncio 是最佳选择。

### Q: 在 Jupyter Notebook 中怎么用？

Jupyter 自带事件循环，不能用 `asyncio.run()`，直接 `await` 即可：

```python
# Jupyter 中
result = await fetch_data()  # 直接 await，不需要 asyncio.run()

# 普通 .py 脚本中
asyncio.run(fetch_data())  # 需要 asyncio.run()
```
