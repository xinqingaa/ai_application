# 第 10 节练习：异步编程

> 异步是 AI 应用开发的核心技能。LLM API 响应慢，异步让你在等待时可以同时处理其他请求。

## 目录结构

```
10_async/
├── README.md
├── async_basics.py           # 练习1：asyncio 基础（async/await/run/sleep）
├── async_concurrency.py      # 练习2：并发（gather/create_task/wait/as_completed）
├── async_http.py             # 练习3：异步 HTTP（httpx.AsyncClient + 并发）
├── async_file.py             # 练习4：异步文件操作（aiofiles）
└── async_llm_race.py         # 练习5：实战 — 多模型竞速
```

每个文件独立可运行。

## 安装依赖

```bash
# httpx 在第 9 节已安装，aiofiles 是新增
pip install httpx aiofiles
```

## 运行方式

```bash
cd source/01_python/10_async

# 练习1-2：纯 asyncio，无网络依赖
python async_basics.py
python async_concurrency.py

# 练习3、5：需要联网（httpbin.org）
python async_http.py
python async_llm_race.py

# 练习4：需要 aiofiles
python async_file.py
```

## 建议学习顺序

| 顺序 | 文件 | 内容 | 依赖 |
|------|------|------|------|
| 1 | `async_basics.py` | async/await 基础、sleep 对比 | 无 |
| 2 | `async_concurrency.py` | gather/wait/create_task 并发模式 | 无 |
| 3 | `async_http.py` | 异步 HTTP 请求、串行 vs 并发 | httpx + 联网 |
| 4 | `async_file.py` | 异步文件读写 | aiofiles |
| 5 | `async_llm_race.py` | 多模型竞速实战 | httpx + 联网 |

## 知识点覆盖

- **基础**：async def / await / asyncio.run / asyncio.sleep
- **并发**：gather / create_task / wait(FIRST_COMPLETED) / as_completed / wait_for
- **错误处理**：return_exceptions / TimeoutError
- **异步 HTTP**：httpx.AsyncClient / 并发请求 / Semaphore 限速
- **异步文件**：aiofiles 读写
- **实战**：多模型竞速、批量请求限速、超时 fallback

## 与 JS 对照速查

| Python | JavaScript |
|--------|-----------|
| `async def fn()` | `async function fn()` |
| `await coro` | `await promise` |
| `asyncio.run(main())` | 自动（或 Node.js 顶层 await） |
| `asyncio.gather(a, b)` | `Promise.all([a, b])` |
| `asyncio.wait(FIRST_COMPLETED)` | `Promise.race([a, b])` |
| `asyncio.sleep(1)` | `new Promise(r => setTimeout(r, 1000))` |

## 注意事项

- 练习 1-2 不需要网络，可以离线学习
- 练习 3、5 需要联网访问 httpbin.org
- 练习 4 需要安装 aiofiles，未安装时会有提示
- `time.sleep()` 在 async 函数中会阻塞事件循环，要用 `asyncio.sleep()`
