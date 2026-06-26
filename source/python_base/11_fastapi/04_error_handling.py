"""
练习 4：错误处理 — HTTPException + 自定义异常 + 统一错误格式

启动方式：
    uvicorn 04_error_handling:app --reload --port 8000

测试方式：
    浏览器打开 http://localhost:8000/docs
    故意触发各种错误，观察不同的错误响应格式
"""

from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="练习4：错误处理",
    description="演示 HTTPException、自定义异常、统一错误响应",
)


# ============================================================
# 1. 自定义异常类
# ============================================================

class AppError(Exception):
    """应用基础异常"""
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.error_code = error_code


class NotFoundError(AppError):
    """资源不存在"""
    def __init__(self, resource: str, resource_id: int | str):
        super().__init__(
            message=f"{resource} (ID: {resource_id}) 不存在",
            error_code="NOT_FOUND",
        )
        self.resource = resource
        self.resource_id = resource_id


class DuplicateError(AppError):
    """资源重复"""
    def __init__(self, resource: str, field: str, value: str):
        super().__init__(
            message=f"{resource} 的 {field} '{value}' 已存在",
            error_code="DUPLICATE",
        )


class PermissionError_(AppError):
    """权限不足（避免和内置 PermissionError 冲突）"""
    def __init__(self, action: str):
        super().__init__(
            message=f"没有权限执行操作：{action}",
            error_code="FORBIDDEN",
        )


# ============================================================
# 2. 注册异常处理器 — 统一错误响应格式
# ============================================================

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """处理所有 AppError 及其子类"""
    status_map = {
        "NOT_FOUND": 404,
        "DUPLICATE": 409,
        "FORBIDDEN": 403,
        "INTERNAL_ERROR": 500,
    }
    return JSONResponse(
        status_code=status_map.get(exc.error_code, 500),
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url),
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """覆盖默认的 422 验证错误格式，统一为自定义格式"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "details": errors,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url),
            },
        },
    )


# ============================================================
# 3. 模型和数据
# ============================================================

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    priority: int = Field(ge=1, le=5, description="优先级 1-5")


class TaskResponse(BaseModel):
    id: int
    title: str
    priority: int
    done: bool


tasks_db: dict[int, dict] = {
    1: {"id": 1, "title": "学习 FastAPI", "priority": 3, "done": False},
    2: {"id": 2, "title": "写练习代码", "priority": 2, "done": True},
}
next_id = 3


# ============================================================
# 4. API 路由 — 演示不同的错误场景
# ============================================================

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """
    获取任务 — 触发 NotFoundError。

    测试：GET /tasks/999 → 自定义 404 错误格式
    """
    if task_id not in tasks_db:
        raise NotFoundError("任务", task_id)
    return tasks_db[task_id]


@app.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    """
    创建任务 — 触发 DuplicateError。

    测试：创建两个同名任务 → 第二次返回 409
    """
    global next_id
    for existing in tasks_db.values():
        if existing["title"] == task.title:
            raise DuplicateError("任务", "title", task.title)

    task_data = {"id": next_id, **task.model_dump(), "done": False}
    tasks_db[next_id] = task_data
    next_id += 1
    return task_data


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, role: str = "viewer"):
    """
    删除任务 — 触发 PermissionError_。

    测试：
    - DELETE /tasks/1?role=viewer → 403 权限不足
    - DELETE /tasks/1?role=admin → 删除成功
    """
    if task_id not in tasks_db:
        raise NotFoundError("任务", task_id)

    if role != "admin":
        raise PermissionError_("删除任务")

    deleted = tasks_db.pop(task_id)
    return {"success": True, "message": f"任务 '{deleted['title']}' 已删除"}


# ============================================================
# 5. HTTPException 也可以直接用
# ============================================================

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """
    直接使用 HTTPException — 简单场景。

    两种错误处理方式都有用：
    - HTTPException：简单、快速
    - 自定义异常 + handler：统一格式、可复用
    """
    items = {1: "书", 2: "笔"}
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail=f"物品 {item_id} 不存在",
            headers={"X-Error": "Item not found"},
        )
    return {"id": item_id, "name": items[item_id]}


# ============================================================
# 6. 错误测试入口
# ============================================================

@app.get("/test-errors/{error_type}")
async def test_errors(error_type: str):
    """
    集中测试各种错误类型。

    测试：
    - GET /test-errors/not_found
    - GET /test-errors/duplicate
    - GET /test-errors/forbidden
    - GET /test-errors/http_exception
    - GET /test-errors/unknown → 未捕获异常
    """
    match error_type:
        case "not_found":
            raise NotFoundError("测试资源", 42)
        case "duplicate":
            raise DuplicateError("测试资源", "name", "重复值")
        case "forbidden":
            raise PermissionError_("测试操作")
        case "http_exception":
            raise HTTPException(status_code=400, detail="这是一个 HTTPException")
        case _:
            return {"message": f"未知错误类型: {error_type}，试试 not_found / duplicate / forbidden"}
