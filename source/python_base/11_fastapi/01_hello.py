"""
练习 1：FastAPI 入门 — 最简应用 + 路由 + 参数

启动方式：
    uvicorn 01_hello:app --reload --port 8000
    
测试方式：
    浏览器打开 http://localhost:8000/docs
"""

from fastapi import FastAPI

app = FastAPI(
    title="练习1：FastAPI 入门",
    description="最简 FastAPI 应用，演示路由和参数",
)


# ============================================================
# 1. 最简路由
# ============================================================

@app.get("/")
async def root():
    return {"message": "Hello FastAPI! "}


# ============================================================
# 2. 路径参数 — 自动类型转换
# ============================================================

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """
    路径参数示例。

    - item_id 声明为 int → FastAPI 自动把 URL 中的字符串转成 int
    - 传 /items/abc → 自动返回 422 验证错误
    """
    return {"item_id": item_id, "type": type(item_id).__name__}


@app.get("/users/{username}")
async def get_user(username: str):
    """路径参数为 str 类型，不做转换"""
    return {"username": username, "greeting": f"你好，{username}！"}


# ============================================================
# 3. 查询参数 — 默认值、可选
# ============================================================

@app.get("/search")
async def search(
    keyword: str,                     # 无默认值 → 必填
    limit: int = 10,                  # 有默认值 → 可选
    offset: int = 0,                  # 有默认值 → 可选
    category: str | None = None,      # None 默认 → 可选
):
    """
    查询参数示例。

    测试：GET /search?keyword=python&limit=5&category=教程
    """
    return {
        "keyword": keyword,
        "limit": limit,
        "offset": offset,
        "category": category,
    }


# ============================================================
# 4. 路径参数 + 查询参数 混合使用
# ============================================================

FAKE_BOOKS = {
    1: {"id": 1, "title": "Python 入门", "tags": ["python", "入门"]},
    2: {"id": 2, "title": "FastAPI 实战", "tags": ["python", "fastapi", "web"]},
    3: {"id": 3, "title": "LLM 应用开发", "tags": ["ai", "llm", "python"]},
}


@app.get("/books")
async def list_books(
    limit: int = 10,
    offset: int = 0,
    tag: str | None = None,
):
    """
    列出书籍（带分页和标签过滤）。

    测试：
    - GET /books → 所有书
    - GET /books?tag=python → 只返回包含 python 标签的书
    - GET /books?limit=1&offset=1 → 分页
    """
    books = list(FAKE_BOOKS.values())

    if tag:
        books = [b for b in books if tag in b["tags"]]

    return {
        "total": len(books),
        "books": books[offset : offset + limit],
    }


@app.get("/books/{book_id}")
async def get_book(book_id: int):
    """
    路径参数获取单本书。

    测试：GET /books/1 → 返回 id=1 的书
    """
    if book_id not in FAKE_BOOKS:
        return {"error": f"书籍 {book_id} 不存在"}
    return FAKE_BOOKS[book_id]


# ============================================================
# 5. 多种 HTTP 方法
# ============================================================

@app.post("/echo")
async def echo_post(data: dict):
    """POST 回显 — 把请求体原样返回"""
    return {"received": data}


@app.get("/health")
def health_check():
    """健康检查（同步函数也可以）"""
    return {"status": "ok"}
