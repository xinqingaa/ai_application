"""
练习 3：完整 CRUD — 书籍管理 API

启动方式：
    uvicorn 03_books_crud:app --reload --port 8000

测试方式：
    浏览器打开 http://localhost:8000/docs
    按顺序测试：POST 创建 → GET 列表 → GET 详情 → PUT 更新 → DELETE 删除
"""

from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="练习3：书籍管理 CRUD",
    description="完整的增删改查 API，使用内存存储",
)


# ============================================================
# 模型定义
# ============================================================

class BookCreate(BaseModel):
    """创建书籍请求体"""
    title: str = Field(min_length=1, max_length=200, description="书名")
    author: str = Field(min_length=1, max_length=100, description="作者")
    price: float = Field(gt=0, description="价格")
    tags: list[str] = Field(default=[], description="标签列表")
    description: str = Field(default="", max_length=1000, description="简介")


class BookUpdate(BaseModel):
    """更新书籍请求体 — 所有字段可选"""
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=100)
    price: float | None = Field(default=None, gt=0)
    tags: list[str] | None = None
    description: str | None = Field(default=None, max_length=1000)


class BookResponse(BaseModel):
    """书籍响应模型"""
    id: int
    title: str
    author: str
    price: float
    tags: list[str]
    description: str
    created_at: datetime
    updated_at: datetime


class BookListResponse(BaseModel):
    """书籍列表响应"""
    total: int
    books: list[BookResponse]


# ============================================================
# 内存数据库
# ============================================================

books_db: dict[int, dict] = {}
next_id = 1


def _init_sample_data():
    """初始化示例数据"""
    global next_id
    samples = [
        BookCreate(title="Python 编程", author="Guido", price=59.9, tags=["python", "入门"]),
        BookCreate(title="FastAPI 实战", author="Sebastián", price=79.0, tags=["python", "web", "fastapi"]),
        BookCreate(title="LLM 应用开发", author="AI Team", price=99.0, tags=["ai", "llm", "python"]),
    ]
    for book in samples:
        now = datetime.now()
        books_db[next_id] = {"id": next_id, **book.model_dump(), "created_at": now, "updated_at": now}
        next_id += 1


_init_sample_data()


# ============================================================
# CREATE — 创建书籍
# ============================================================

@app.post("/books", response_model=BookResponse, status_code=201)
async def create_book(book: BookCreate):
    """
    创建新书籍。

    测试 Body:
    {"title": "新书", "author": "作者", "price": 39.9, "tags": ["test"]}
    """
    global next_id
    now = datetime.now()
    book_data = {
        "id": next_id,
        **book.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    books_db[next_id] = book_data
    next_id += 1
    return book_data


# ============================================================
# READ — 查询书籍
# ============================================================

@app.get("/books", response_model=BookListResponse)
async def list_books(
    limit: int = Query(default=10, ge=1, le=100, description="每页数量"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    tag: str | None = Query(default=None, description="按标签过滤"),
    search: str | None = Query(default=None, description="搜索书名/作者"),
):
    """
    查询书籍列表（支持分页、标签过滤、搜索）。

    测试：
    - GET /books → 全部
    - GET /books?tag=python → 包含 python 标签的
    - GET /books?search=FastAPI → 书名或作者包含 FastAPI 的
    """
    books = list(books_db.values())

    if tag:
        books = [b for b in books if tag in b["tags"]]

    if search:
        search_lower = search.lower()
        books = [
            b for b in books
            if search_lower in b["title"].lower() or search_lower in b["author"].lower()
        ]

    total = len(books)
    books = books[offset : offset + limit]

    return BookListResponse(total=total, books=books)


@app.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: int):
    """
    获取单本书详情。

    测试：GET /books/1
    """
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail=f"书籍 ID {book_id} 不存在")
    return books_db[book_id]


# ============================================================
# UPDATE — 更新书籍
# ============================================================

@app.put("/books/{book_id}", response_model=BookResponse)
async def update_book(book_id: int, book_update: BookUpdate):
    """
    更新书籍信息（只更新传入的字段）。

    测试 Body:
    {"title": "更新后的书名", "price": 49.9}
    """
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail=f"书籍 ID {book_id} 不存在")

    existing = books_db[book_id]
    update_data = book_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        existing[field] = value
    existing["updated_at"] = datetime.now()

    return existing


# ============================================================
# DELETE — 删除书籍
# ============================================================

@app.delete("/books/{book_id}")
async def delete_book(book_id: int):
    """
    删除书籍。

    测试：DELETE /books/1
    """
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail=f"书籍 ID {book_id} 不存在")

    deleted = books_db.pop(book_id)
    return {"message": f"书籍《{deleted['title']}》已删除", "id": book_id}


# ============================================================
# 额外：统计接口
# ============================================================

@app.get("/books/stats/summary")
async def books_stats():
    """书籍统计信息"""
    if not books_db:
        return {"total": 0, "avg_price": 0, "tags": []}

    prices = [b["price"] for b in books_db.values()]
    all_tags = set()
    for b in books_db.values():
        all_tags.update(b["tags"])

    return {
        "total": len(books_db),
        "avg_price": round(sum(prices) / len(prices), 2),
        "min_price": min(prices),
        "max_price": max(prices),
        "tags": sorted(all_tags),
    }
