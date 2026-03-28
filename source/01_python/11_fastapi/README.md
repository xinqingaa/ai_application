# 11. FastAPI 基础 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/01_python/11_fastapi.md) 一步步动手操作

---

## 核心原则

```
读文档 → 看对应代码 → 启动服务 → /docs 页面测试
```

- 在 `source/01_python/11_fastapi/` 目录下操作
- 每个文件是独立可运行的 FastAPI 应用
- **每次只运行一个文件**（都用 8000 端口），Ctrl+C 停止后再启动下一个

---

## 项目结构

```
11_fastapi/
├── README.md                    ← 你正在读的这个文件
├── 01_hello.py                  ← 第 1 步：入门（文档第 2-3 章）
├── 02_pydantic_models.py        ← 第 2 步：Pydantic 模型（文档第 4 章）
├── 03_books_crud.py             ← 第 3 步：完整 CRUD（文档第 3-4 章综合）
├── 04_error_handling.py         ← 第 4 步：错误处理（文档第 5 章）
└── 05_dependency_injection.py   ← 第 5 步：依赖注入（文档第 6 章）
```

---

## 前置准备

### 安装依赖

```bash
pip install "fastapi[standard]"
```

### 运行方式

```bash
cd source/01_python/11_fastapi

# 启动练习 1
uvicorn 01_hello:app --reload --port 8000

# 启动练习 2
uvicorn 02_pydantic_models:app --reload --port 8000

# 启动练习 3
uvicorn 03_books_crud:app --reload --port 8000

# 启动练习 4
uvicorn 04_error_handling:app --reload --port 8000

# 启动练习 5
uvicorn 05_dependency_injection:app --reload --port 8000
```

### 测试 API 的三种方式

**方式一：Swagger UI（推荐）**

启动服务后，浏览器打开 `http://localhost:8000/docs`。这是 FastAPI 自动生成的交互式文档，可以直接填参数、发请求、看响应。**不需要 Postman。**

**方式二：curl**

```bash
curl http://localhost:8000/
curl http://localhost:8000/items/42
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "张三", "email": "test@example.com", "age": 25}'
```

**方式三：Python httpx（结合第 9 节所学）**

```python
import httpx
resp = httpx.get("http://localhost:8000/")
print(resp.json())
```

---

## 第 1 步：FastAPI 入门（文档第 2-3 章）

**对应文件**：`01_hello.py`
**对应文档**：第 2 章「FastAPI 入门」+ 第 3 章「路由与参数」

### 操作流程

1. 读文档 2.1-2.3 节，理解 FastAPI 和 Express/Flask 的区别

2. 打开 `01_hello.py`，看最简应用——三行核心代码就是一个 API 服务

3. 启动服务：

```bash
uvicorn 01_hello:app --reload --port 8000
```

4. 打开 `http://localhost:8000/docs`，看到自动生成的 API 文档

5. 读文档 3.1 节「路由装饰器」，看代码中的 `@app.get`、`@app.post`

6. 读文档 3.2 节「路径参数」，看 `/{item_id}` + 类型声明自动转换：
   - 声明 `item_id: int`，FastAPI 自动把 URL 字符串转为 int
   - 转换失败自动返回 422 错误（不需要手动写验证逻辑）

7. 读文档 3.3 节「查询参数」，看函数参数有默认值 = 查询参数：
   - `limit: int = 10` → 可选参数，默认 10
   - `search: str | None = None` → 可选参数，默认 None

8. 在 `/docs` 页面逐个测试每个接口，观察参数类型和响应格式

---

## 第 2 步：Pydantic 模型（文档第 4 章）

**对应文件**：`02_pydantic_models.py`
**对应文档**：第 4 章「Pydantic 模型与请求体」

### 操作流程

1. 读文档 4.1 节「定义请求模型」，理解 Pydantic = TypeScript interface + Zod 验证

2. Ctrl+C 停止上一个服务，启动练习 2：

```bash
uvicorn 02_pydantic_models:app --reload --port 8000
```

3. 打开 `02_pydantic_models.py`，看 `UserCreate` 模型：
   - `Field(min_length=1, max_length=50)` — 字符串长度约束
   - `Field(ge=0, le=150)` — 数值范围约束
   - 自动验证，失败返回 422 + 详细错误信息

4. 读文档 4.2 节「使用请求模型」—— `user: UserCreate` 自动解析和验证请求体

5. 读文档 4.3 节「响应模型」—— `response_model=UserResponse` 过滤响应字段

6. 读文档 4.4 节「嵌套模型」—— `ChatRequest` 包含 `list[Message]`，类似 OpenAI 的请求格式

7. 在 `/docs` 页面测试：
   - 发送合法 JSON → 200 成功
   - 发送非法 JSON（如 age 传 "abc"）→ 422 详细错误

---

## 第 3 步：完整 CRUD（文档第 3-4 章综合）

**对应文件**：`03_books_crud.py`

### 操作流程

1. Ctrl+C 停止上一个服务，启动练习 3：

```bash
uvicorn 03_books_crud:app --reload --port 8000
```

2. 打开 `03_books_crud.py`，看完整的 CRUD API：
   - `GET /books` — 列表（支持分页和搜索）
   - `POST /books` — 创建
   - `GET /books/{id}` — 获取单条
   - `PUT /books/{id}` — 更新
   - `DELETE /books/{id}` — 删除

3. 在 `/docs` 页面按顺序测试完整流程：
   - 先 POST 创建几本书
   - 再 GET 查看列表
   - PUT 修改某本
   - DELETE 删除某本

4. 这就是 REST API 的标准模式，后续 AI 聊天 API 也是同样的结构

---

## 第 4 步：错误处理（文档第 5 章）

**对应文件**：`04_error_handling.py`
**对应文档**：第 5 章「错误处理」

### 操作流程

1. 读文档 5.1 节「HTTPException」

2. Ctrl+C 停止上一个服务，启动练习 4：

```bash
uvicorn 04_error_handling:app --reload --port 8000
```

3. 看 `04_error_handling.py` 中的两种方式：
   - `HTTPException`：简单场景，直接 raise
   - 自定义异常 + `@app.exception_handler`：复杂场景，统一错误格式

4. 在 `/docs` 页面测试：
   - 访问不存在的资源 → 自定义错误格式
   - 触发业务错误 → 统一的 JSON 错误响应

---

## 第 5 步：依赖注入（文档第 6 章）

**对应文件**：`05_dependency_injection.py`
**对应文档**：第 6 章「依赖注入」

### 操作流程

1. 读文档 6.1 节「什么是依赖注入」—— 把公共逻辑提取成独立函数，通过 `Depends` 注入

2. Ctrl+C 停止上一个服务，启动练习 5：

```bash
uvicorn 05_dependency_injection:app --reload --port 8000
```

3. 看 `05_dependency_injection.py` 中的两个核心场景：
   - 公共分页参数：`Depends(common_pagination)` 提取公共逻辑
   - API Key 验证：`Depends(verify_api_key)` 鉴权

4. 在 `/docs` 页面测试：
   - 不带 API Key 访问受保护接口 → 401 错误
   - 点击右上角 **Authorize**，输入 `sk-test-key-001` → 测试通过

5. 测试用 API Key：

| Key | 用户 | 角色 |
|-----|------|------|
| `sk-test-key-001` | 测试用户 | admin |
| `sk-test-key-002` | 普通用户 | user |

---

## 文档章节与文件对应表

| 文档章节 | 核心内容 | 对应文件 |
|---------|---------|---------|
| 第 2-3 章 | 入门、路由装饰器、路径参数、查询参数 | `01_hello.py` |
| 第 4 章 | Pydantic 模型、请求体验证、响应模型、嵌套模型 | `02_pydantic_models.py` |
| 第 3-4 章综合 | 完整 CRUD API（增删改查 + 分页搜索） | `03_books_crud.py` |
| 第 5 章 | HTTPException、自定义异常、异常处理器 | `04_error_handling.py` |
| 第 6 章 | Depends、公共参数、API Key 验证 | `05_dependency_injection.py` |

---

## 学习顺序总结

| 顺序 | 文件 | 核心内容 | 启动命令 |
|-----|------|---------|---------|
| 1 | `01_hello.py` | 路由 + 参数（入门） | `uvicorn 01_hello:app --reload` |
| 2 | `02_pydantic_models.py` | Pydantic 验证（请求体） | `uvicorn 02_pydantic_models:app --reload` |
| 3 | `03_books_crud.py` | 完整 CRUD（综合） | `uvicorn 03_books_crud:app --reload` |
| 4 | `04_error_handling.py` | 错误处理（健壮性） | `uvicorn 04_error_handling:app --reload` |
| 5 | `05_dependency_injection.py` | 依赖注入（工程化） | `uvicorn 05_dependency_injection:app --reload` |

---

## 注意事项

- **每次只运行一个服务**，都用 8000 端口，Ctrl+C 停止后再启动下一个
- **`/docs` 页面是最好的测试工具**，不需要 Postman
- **Pydantic 验证失败返回 422**，看响应中的 `detail` 字段定位问题
- **`def` 和 `async def` 都可以**，有 I/O 操作（如调用 LLM API）时用 `async def`
- 修改代码后 `--reload` 会自动重启服务，不需要手动重启
