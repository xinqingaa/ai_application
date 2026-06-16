# 11. FastAPI 基础

> 本节目标：掌握 FastAPI 框架基础，为构建 AI 应用后端做好准备

---

## 1. 概述

### 学习目标

- 掌握 FastAPI 的安装、启动和基本路由
- 掌握路径参数、查询参数
- 掌握 Pydantic 模型定义请求体和响应
- 掌握错误处理和自定义异常
- 了解依赖注入机制
- 能构建完整的 CRUD API

### 预计学习时间

- FastAPI 入门 + 路由：1 小时
- Pydantic 模型：1 小时
- CRUD 练习：1 小时
- 错误处理 + 依赖注入：1 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|------|---------|
| AI 聊天后端 API | 路由、POST 请求处理 |
| LLM 请求/响应验证 | Pydantic 模型 |
| 流式响应（SSE） | FastAPI StreamingResponse |
| API Key 鉴权 | 依赖注入 |
| 错误降级 | HTTPException、自定义异常处理器 |
| 自动 API 文档 | Swagger UI（`/docs`） |

> **FastAPI 是 AI 应用后端首选框架**。它原生支持 async、自带 Pydantic 验证、自动生成 API 文档，和 LLM API 开发完美契合。

---

## 2. FastAPI 入门 📌

### 2.1 为什么选 FastAPI

| 特性 | Express (Node.js) | Flask (Python) | FastAPI (Python) |
|------|-------------------|----------------|-----------------|
| 异步支持 | 天然 | 需要扩展 | 原生 async |
| 类型验证 | 需要 Joi/Zod | 需要 Marshmallow | Pydantic 内置 |
| API 文档 | 需要 Swagger 插件 | 需要插件 | 自动生成 |
| 性能 | 高 | 一般 | 高（Starlette 驱动） |
| AI 生态 | 一般 | 丰富 | 最丰富 |

### 2.2 安装

```bash
pip install "fastapi[standard]"
# 包含：fastapi + uvicorn + pydantic + 其他常用依赖
```

### 2.3 最小应用

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

三行核心代码，就是一个完整的 API 服务。

### 2.4 启动方式

```bash
# 方式一：uvicorn（推荐，更多控制）
uvicorn main:app --reload --port 8000

# 方式二：fastapi CLI（快捷开发）
fastapi dev main.py

# 参数说明：
# main:app  → main.py 文件中的 app 变量
# --reload  → 代码修改后自动重启（开发模式）
# --port    → 端口号，默认 8000
```

### 2.5 自动文档（杀手锏）

启动后访问：
- **Swagger UI**：`http://localhost:8000/docs` — 交互式 API 文档，可直接测试
- **ReDoc**：`http://localhost:8000/redoc` — 更美观的文档

> **不需要 Postman！** 在 `/docs` 页面可以直接填参数、发请求、看响应。这是 FastAPI 相比 Express/Flask 最大的优势之一。

---

## 3. 路由与参数 📌

### 3.1 路由装饰器

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")           # GET 请求
async def read_root():
    return {"method": "GET"}

@app.post("/items")     # POST 请求
async def create_item():
    return {"method": "POST"}

@app.put("/items/{id}") # PUT 请求
async def update_item(id: int):
    return {"method": "PUT", "id": id}

@app.delete("/items/{id}")  # DELETE 请求
async def delete_item(id: int):
    return {"method": "DELETE", "id": id}
```

> **sync 和 async 都可以**：FastAPI 同时支持 `def` 和 `async def`。有 I/O 操作（如调用 LLM API）时用 `async def`。

### 3.2 路径参数

```python
@app.get("/items/{item_id}")
async def get_item(item_id: int):  # 自动转换为 int
    return {"item_id": item_id}

# 访问：GET /items/42
# 返回：{"item_id": 42}

# 访问：GET /items/abc
# 返回：422 错误（自动验证失败）
```

> **类型自动转换和验证**：声明 `item_id: int`，FastAPI 自动把 URL 中的字符串转为 int。如果转换失败（如 `"abc"`），自动返回 422 错误。这在 Express 中需要手动处理。

### 3.3 查询参数

```python
@app.get("/users")
async def get_users(
    limit: int = 10,          # 有默认值 → 可选
    offset: int = 0,          # 有默认值 → 可选
    search: str | None = None # None 默认 → 可选
):
    return {"limit": limit, "offset": offset, "search": search}

# 访问：GET /users?limit=5&search=张
# 返回：{"limit": 5, "offset": 0, "search": "张"}
```

### 3.4 路径参数 vs 查询参数

| 类型 | 语法 | 场景 | 示例 |
|------|------|------|------|
| 路径参数 | `/items/{id}` | 标识特定资源 | `GET /books/42` |
| 查询参数 | `?key=value` | 过滤、分页、搜索 | `GET /books?page=2&limit=10` |

---

## 4. Pydantic 模型与请求体 📌

### 4.1 定义请求模型

```python
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    email: str
    age: int = Field(ge=0, le=150)  # 大于等于 0，小于等于 150
```

> **与 TypeScript 对比**：
> ```typescript
> // TypeScript（只有类型，没有运行时验证）
> interface UserCreate {
>   name: string;
>   email: string;
>   age: number;
> }
>
> // Zod（TypeScript 运行时验证）
> const UserCreate = z.object({
>   name: z.string().min(1).max(50),
>   email: z.string().email(),
>   age: z.number().min(0).max(150),
> });
> ```
> Pydantic = TypeScript interface + Zod 验证，合为一体。

### 4.2 使用请求模型

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    email: str
    age: int = Field(ge=0, le=150)

@app.post("/users")
async def create_user(user: UserCreate):  # 自动解析和验证请求体
    return {"message": f"用户 {user.name} 创建成功", "user": user}

# POST /users
# Body: {"name": "张三", "email": "test@example.com", "age": 25}
# → 自动验证，通过后执行函数
# → 验证失败自动返回 422 + 详细错误信息
```

### 4.3 响应模型

```python
from datetime import datetime

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    # response_model 会过滤掉不在模型中的字段
    return UserResponse(
        id=1,
        name=user.name,
        email=user.email,
        created_at=datetime.now(),
    )
```

### 4.4 嵌套模型

```python
class Message(BaseModel):
    role: str        # "user" / "assistant" / "system"
    content: str

class ChatRequest(BaseModel):
    model: str = "gpt-4o-mini"
    messages: list[Message]
    temperature: float = Field(default=0.7, ge=0, le=2)

# POST /chat
# Body: {
#   "model": "gpt-4o-mini",
#   "messages": [
#     {"role": "system", "content": "你是助手"},
#     {"role": "user", "content": "你好"}
#   ]
# }
```

---

## 5. 错误处理 📌

### 5.1 HTTPException

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {"1": "书本", "2": "笔记本"}

@app.get("/items/{item_id}")
async def get_item(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail=f"物品 {item_id} 不存在"
        )
    return {"item_id": item_id, "name": items[item_id]}
```

### 5.2 自定义异常 + 异常处理器

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# 自定义异常
class BookNotFoundError(Exception):
    def __init__(self, book_id: int):
        self.book_id = book_id

# 注册异常处理器
@app.exception_handler(BookNotFoundError)
async def book_not_found_handler(request: Request, exc: BookNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": "NOT_FOUND",
            "message": f"书籍 ID {exc.book_id} 不存在",
        }
    )

@app.get("/books/{book_id}")
async def get_book(book_id: int):
    # 业务代码只需要 raise，不需要构造 HTTP 响应
    raise BookNotFoundError(book_id)
```

---

## 6. 依赖注入 ⚡

### 6.1 什么是依赖注入

把公共逻辑（验证、参数提取、数据库连接）提取成独立函数，通过 `Depends` 注入到路由中。

```python
from fastapi import FastAPI, Depends, Query

app = FastAPI()

# 依赖函数：提取公共分页参数
def common_pagination(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    return {"limit": limit, "offset": offset}

@app.get("/books")
async def get_books(pagination: dict = Depends(common_pagination)):
    return {"books": [], **pagination}

@app.get("/users")
async def get_users(pagination: dict = Depends(common_pagination)):
    return {"users": [], **pagination}
```

### 6.2 API Key 验证

```python
from fastapi import FastAPI, Depends, Header, HTTPException

app = FastAPI()

async def verify_api_key(x_api_key: str = Header()):
    """验证 API Key（依赖注入）"""
    if x_api_key != "my-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.get("/protected")
async def protected_route(api_key: str = Depends(verify_api_key)):
    return {"message": "验证通过", "api_key": api_key[:8] + "..."}
```

> **AI 应用场景**：用依赖注入验证用户的 API Key，确保只有授权用户可以调用 LLM 接口。

---

## 7. 部署基础 📌

### 7.1 uvicorn 参数

```bash
uvicorn main:app \
  --host 0.0.0.0 \      # 监听所有网卡（允许外部访问）
  --port 8000 \          # 端口
  --reload \             # 热重载（开发模式）
  --workers 4            # 多进程（生产模式，不能和 --reload 同时用）
```

### 7.2 开发 vs 生产

| 模式 | 命令 | 特点 |
|------|------|------|
| 开发 | `uvicorn main:app --reload` | 热重载、详细错误 |
| 开发 | `fastapi dev main.py` | 同上，更简短 |
| 生产 | `uvicorn main:app --workers 4` | 多进程、无热重载 |

---

## 8. 小结

### 核心知识

| 知识点 | 优先级 | 一句话总结 |
|--------|-------|-----------|
| 最小应用 | 📌 | `FastAPI()` + `@app.get("/")` + `uvicorn` |
| 路径参数 | 📌 | `/{id}` + 类型声明自动转换验证 |
| 查询参数 | 📌 | 函数参数有默认值 = 查询参数 |
| Pydantic 模型 | 📌 | `BaseModel` 定义请求/响应，自动验证 |
| response_model | 📌 | 控制响应字段，过滤敏感信息 |
| HTTPException | 📌 | `raise HTTPException(404, detail="...")` |
| 自定义异常 | 📌 | `exception_handler` 注册处理器 |
| 依赖注入 | ⚡ | `Depends(func)` 提取公共逻辑 |
| 自动文档 | 📌 | `/docs`（Swagger）可直接测试 API |

### 与 JavaScript 关键差异

| 差异点 | Express (Node.js) | FastAPI (Python) |
|--------|-------------------|-----------------|
| 路由定义 | `app.get("/", (req, res) => ...)` | `@app.get("/") async def ...` |
| 参数获取 | `req.params.id`、`req.query.limit` | 函数参数自动注入 |
| 请求体 | `req.body`（需中间件） | Pydantic 模型自动解析验证 |
| 类型验证 | Joi / Zod / 手动 | Pydantic 内置 |
| 错误处理 | `res.status(404).json(...)` | `raise HTTPException(404)` |
| 中间件 | `app.use(middleware)` | `@app.middleware` / Depends |
| API 文档 | Swagger 插件 | 自动生成 |
| 异步 | 天然 | `async def`（也支持 `def`） |

### 下一节预告

下一节 **综合练习：AI 聊天 API**（第 12 节）将在本节基础上接入 LLM API，构建一个完整的 AI 聊天后端。

---

## 9. 常见问题

### Q: def 和 async def 有什么区别？什么时候用哪个？

```python
# 有 I/O 操作（网络请求、数据库查询）→ async def
@app.post("/chat")
async def chat():
    response = await call_llm_api()  # 需要 await
    return response

# 纯计算、无 I/O → def 也可以
@app.get("/health")
def health_check():
    return {"status": "ok"}
```

FastAPI 对两者都能正确处理。`async def` 在事件循环中执行，`def` 会放到线程池中执行。

### Q: Pydantic 验证失败返回什么？

自动返回 422 + 详细错误信息：

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["body", "age"],
      "msg": "Input should be a valid integer",
      "input": "abc"
    }
  ]
}
```

不需要手动写验证逻辑。

### Q: 怎么测试 API？

1. **`/docs` 页面**（推荐）：浏览器打开 `http://localhost:8000/docs`
2. **curl**：`curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d '{"name":"test"}'`
3. **httpx / requests**：用 Python 代码调用
4. **Postman**：也可以，但 `/docs` 更方便

### Q: FastAPI 和 Flask 怎么选？

| 场景 | 推荐 |
|------|------|
| AI 应用后端 | FastAPI（原生 async、Pydantic、自动文档） |
| 简单 Web 应用 | Flask（更简单、生态更广） |
| 追求性能 | FastAPI |
| 团队已有 Flask 经验 | Flask 也行 |

AI 应用开发推荐 FastAPI，因为 LLM API 调用需要异步、请求/响应需要 Pydantic 验证。

### Q: 为什么我的请求返回 422？

422 是 Pydantic 验证失败。常见原因：
- 请求体不是合法 JSON
- 字段类型不匹配（如传了字符串给 int 字段）
- 缺少必填字段
- 字段值不符合约束（如 age < 0）

看响应中的 `detail` 字段，会告诉你哪个字段有问题。
