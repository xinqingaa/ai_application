# 第 11 节：FastAPI 基础 — 参考实现

> 对应文档：[docs/01_python/11_fastapi.md](../../../docs/01_python/11_fastapi.md)

## 环境准备

### 安装依赖

```bash
pip install "fastapi[standard]"
# 包含 fastapi + uvicorn + pydantic + httptools + uvloop 等
```

### 验证安装

```bash
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
python -c "import pydantic; print(f'Pydantic {pydantic.__version__}')"
```

## 文件说明

| 文件 | 内容 | 核心知识点 |
|------|------|-----------|
| `01_hello.py` | 最简 FastAPI 应用 | 路由、路径参数、查询参数、类型自动转换 |
| `02_pydantic_models.py` | Pydantic 模型 | 请求体验证、响应模型、嵌套模型、Field 约束 |
| `03_books_crud.py` | 完整 CRUD API | 增删改查、分页、搜索、内存存储 |
| `04_error_handling.py` | 错误处理 | HTTPException、自定义异常、异常处理器、统一错误格式 |
| `05_dependency_injection.py` | 依赖注入 | Depends、公共参数、API Key 验证、依赖组合 |

## 启动方式

每个文件都是独立可运行的 FastAPI 应用：

```bash
# 进入目录
cd source/01_python/11_fastapi

# 启动练习 1
uvicorn 01_hello:app --reload --port 8000

# 启动练习 2
uvicorn 02_pydantic_models:app --reload --port 8000

# 启动练习 3
uvicorn 03_books_crud:app --reload --port 8000

# 以此类推...
```

> **每次只运行一个**，因为都使用 8000 端口。`Ctrl+C` 停止后再启动下一个。

## 测试 API

### 方式一：Swagger UI（强烈推荐）

启动服务后，浏览器打开：

```
http://localhost:8000/docs
```

这是 FastAPI 自动生成的交互式文档，可以：
- 查看所有接口和参数说明
- 直接在页面上填写参数并发送请求
- 查看请求和响应的完整内容

> 不需要 Postman！`/docs` 是最快的 API 测试方式。

### 方式二：curl

```bash
# GET 请求
curl http://localhost:8000/

# 带路径参数
curl http://localhost:8000/items/42

# 带查询参数
curl "http://localhost:8000/search?keyword=python&limit=5"

# POST 请求（JSON 请求体）
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "张三", "email": "test@example.com", "age": 25}'

# 带 Header（API Key）
curl http://localhost:8000/protected/profile \
  -H "x-api-key: sk-test-key-001"
```

### 方式三：Python httpx（结合第 9 节所学）

```python
import httpx

# GET
resp = httpx.get("http://localhost:8000/books")
print(resp.json())

# POST
resp = httpx.post(
    "http://localhost:8000/users",
    json={"name": "李四", "email": "lisi@test.com", "age": 30},
)
print(resp.json())
```

## 推荐学习顺序

```
01_hello.py          入门：路由 + 参数
    ↓
02_pydantic_models   进阶：请求体验证
    ↓
03_books_crud        综合：完整 CRUD
    ↓
04_error_handling    健壮：错误处理
    ↓
05_dependency_injection  工程化：依赖注入
```

## 练习 5 测试用 API Key

| Key | 用户 | 角色 |
|-----|------|------|
| `sk-test-key-001` | 测试用户 | admin |
| `sk-test-key-002` | 普通用户 | user |

在 `/docs` 页面点击右上角 **Authorize** 按钮，输入 `sk-test-key-001` 即可测试受保护的接口。

## 与 JS 框架对比

| 对比项 | Express (Node.js) | FastAPI (Python) |
|--------|-------------------|-----------------|
| 启动 | `node app.js` | `uvicorn app:app` |
| 热重载 | `nodemon` | `--reload` 参数 |
| API 文档 | 需 swagger 插件 | 自动生成 `/docs` |
| 类型验证 | Joi / Zod | Pydantic 内置 |
| 中间件 | `app.use()` | `Depends()` |

## 下一步

完成本节后，进入第 12 节"综合练习：AI 聊天 API"，将本节学到的 FastAPI 知识接入 LLM API，构建完整的 AI 聊天后端。
