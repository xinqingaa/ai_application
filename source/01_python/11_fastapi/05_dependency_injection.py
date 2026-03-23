"""
练习 5：依赖注入 — Depends 机制、公共参数、API Key 验证

启动方式：
    uvicorn 05_dependency_injection:app --reload --port 8000

测试方式：
    浏览器打开 http://localhost:8000/docs
    测试需要 API Key 的接口时，点击 "Authorize" 按钮或在 Header 中添加 x-api-key
"""

from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="练习5：依赖注入",
    description="演示 Depends 机制、公共参数提取、API Key 验证",
)


# ============================================================
# 1. 基础依赖 — 公共分页参数
# ============================================================

class PaginationParams(BaseModel):
    """分页参数模型"""
    limit: int
    offset: int


def common_pagination(
    limit: int = Query(default=10, ge=1, le=100, description="每页数量"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
) -> PaginationParams:
    """公共分页依赖 — 多个路由复用同一组参数"""
    return PaginationParams(limit=limit, offset=offset)


Pagination = Annotated[PaginationParams, Depends(common_pagination)]

FAKE_BOOKS = [
    {"id": i, "title": f"书籍 {i}", "author": f"作者 {i}"}
    for i in range(1, 21)
]

FAKE_USERS = [
    {"id": i, "name": f"用户 {i}", "email": f"user{i}@example.com"}
    for i in range(1, 16)
]


@app.get("/books")
async def list_books(pagination: Pagination):
    """书籍列表 — 使用公共分页"""
    items = FAKE_BOOKS[pagination.offset : pagination.offset + pagination.limit]
    return {"total": len(FAKE_BOOKS), "items": items, "pagination": pagination.model_dump()}


@app.get("/users")
async def list_users(pagination: Pagination):
    """用户列表 — 同样使用公共分页（参数定义只写一次）"""
    items = FAKE_USERS[pagination.offset : pagination.offset + pagination.limit]
    return {"total": len(FAKE_USERS), "items": items, "pagination": pagination.model_dump()}


# ============================================================
# 2. API Key 验证依赖
# ============================================================

VALID_API_KEYS = {
    "sk-test-key-001": {"user": "测试用户", "role": "admin"},
    "sk-test-key-002": {"user": "普通用户", "role": "user"},
}


class AuthInfo(BaseModel):
    api_key: str
    user: str
    role: str


async def verify_api_key(x_api_key: str = Header(description="API Key")) -> AuthInfo:
    """
    验证 API Key 的依赖函数。

    从请求头 x-api-key 中获取 key，验证是否有效。
    在 /docs 页面点击右上角 "Authorize" 按钮输入 key。
    """
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="无效的 API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    info = VALID_API_KEYS[x_api_key]
    return AuthInfo(api_key=x_api_key, **info)


Auth = Annotated[AuthInfo, Depends(verify_api_key)]


@app.get("/protected/profile")
async def get_profile(auth: Auth):
    """
    受保护的路由 — 需要有效的 API Key。

    测试：
    - 不传 x-api-key → 422
    - 传错误的 key → 401
    - 传 sk-test-key-001 → 成功（admin）
    - 传 sk-test-key-002 → 成功（user）
    """
    return {
        "message": f"你好，{auth.user}！",
        "role": auth.role,
        "key_prefix": auth.api_key[:10] + "...",
    }


# ============================================================
# 3. 依赖组合 — 多个依赖叠加
# ============================================================

def require_admin(auth: Auth) -> AuthInfo:
    """要求 admin 角色（依赖 verify_api_key 的结果）"""
    if auth.role != "admin":
        raise HTTPException(status_code=403, detail="需要 admin 权限")
    return auth


AdminAuth = Annotated[AuthInfo, Depends(require_admin)]


@app.get("/admin/dashboard")
async def admin_dashboard(auth: AdminAuth):
    """
    管理员专属路由 — 需要 admin 角色。

    测试：
    - sk-test-key-001（admin）→ 成功
    - sk-test-key-002（user）→ 403
    """
    return {
        "message": "管理员仪表盘",
        "admin": auth.user,
        "stats": {
            "total_books": len(FAKE_BOOKS),
            "total_users": len(FAKE_USERS),
        },
    }


# ============================================================
# 4. 带参数的依赖 — 工厂模式
# ============================================================

def rate_limiter(max_calls: int = 10):
    """
    依赖工厂 — 返回一个依赖函数。

    实际场景中会用 Redis 记录调用次数，这里简化为计数器演示。
    """
    call_count: dict[str, int] = {}

    async def check_rate_limit(x_api_key: str = Header(default="anonymous")) -> dict:
        current = call_count.get(x_api_key, 0) + 1
        call_count[x_api_key] = current

        if current > max_calls:
            raise HTTPException(
                status_code=429,
                detail=f"请求过于频繁，限制 {max_calls} 次/周期",
            )
        return {"current_calls": current, "max_calls": max_calls}

    return check_rate_limit


@app.get("/limited")
async def limited_endpoint(
    rate_info: dict = Depends(rate_limiter(max_calls=5)),
):
    """
    限流演示 — 超过 5 次返回 429。

    连续请求 6 次看效果（重启服务器重置计数）。
    """
    return {"message": "请求成功", **rate_info}


# ============================================================
# 5. 实战场景 — 模拟 AI 应用的请求处理链
# ============================================================

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    model: str = Field(default="gpt-4o-mini")


class ChatResponse(BaseModel):
    reply: str
    model: str
    user: str
    tokens_used: int


async def track_usage(auth: Auth) -> dict:
    """追踪 API 使用量（模拟）"""
    return {
        "user": auth.user,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/ai/chat", response_model=ChatResponse)
async def ai_chat(
    request: ChatRequest,
    auth: Auth,
    usage: dict = Depends(track_usage),
):
    """
    模拟 AI 聊天接口 — 串联多个依赖。

    依赖链：verify_api_key → track_usage → 路由处理

    测试（需要在 Header 中传 x-api-key）:
    Body: {"message": "你好", "model": "gpt-4o-mini"}
    """
    token_count = len(request.message) * 2 + 50

    return ChatResponse(
        reply=f"[{request.model}] 收到：{request.message}（模拟回复）",
        model=request.model,
        user=auth.user,
        tokens_used=token_count,
    )
