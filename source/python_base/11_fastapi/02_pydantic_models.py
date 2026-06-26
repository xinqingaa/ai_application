"""
练习 2：Pydantic 模型 — 请求体验证 + 响应模型

启动方式：
    uvicorn 02_pydantic_models:app --reload --port 8000

测试方式：
    浏览器打开 http://localhost:8000/docs
"""

from datetime import datetime
from enum import StrEnum

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="练习2：Pydantic 模型",
    description="演示请求体验证、响应模型、嵌套模型",
)


# ============================================================
# 1. 基础请求/响应模型
# ============================================================

class UserCreate(BaseModel):
    """用户创建请求体（相当于 TS 中 interface + Zod 验证合体）"""
    name: str = Field(min_length=1, max_length=50, description="用户名")
    email: str = Field(description="邮箱地址")
    age: int = Field(ge=0, le=150, description="年龄")
    bio: str | None = Field(default=None, max_length=200, description="个人简介")


class UserResponse(BaseModel):
    """用户响应模型 — 控制返回哪些字段"""
    id: int
    name: str
    email: str
    age: int
    created_at: datetime


users_db: dict[int, dict] = {}
next_id = 1


# response_model 会过滤掉不在模型中的字段
@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """
    创建用户。

    - 请求体自动按 UserCreate 验证
    - 响应自动按 UserResponse 过滤字段（bio 不在 response 中）

    测试 Body:
    {"name": "张三", "email": "zhangsan@example.com", "age": 25, "bio": "测试用户"}
    """
    global next_id
    user_data = {
        "id": next_id,
        **user.model_dump(),
        "created_at": datetime.now(),
    }
    users_db[next_id] = user_data
    next_id += 1
    return user_data


@app.get("/users", response_model=list[UserResponse])
async def list_users():
    """列出所有用户"""
    return list(users_db.values())


# ============================================================
# 2. 字段验证（Field）
# ============================================================

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="价格必须大于 0")
    quantity: int = Field(ge=0, default=0, description="库存数量")
    description: str = Field(default="", max_length=500)


@app.post("/products")
async def create_product(product: ProductCreate):
    """
    创建商品 — 演示更多 Field 验证。

    试试传入不合法数据，比如 price=-1，看 422 错误的详细信息。
    """
    return {"message": "商品创建成功", "product": product.model_dump()}


# ============================================================
# 3. 嵌套模型 — 模拟 LLM 聊天请求
# ============================================================

class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: Role
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    """模拟 LLM API 请求结构（和 OpenAI 格式类似）"""
    model: str = Field(default="gpt-4o-mini", description="模型名称")
    messages: list[Message] = Field(min_length=1, description="至少包含一条消息")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=1024, ge=1, le=4096)


class ChatResponse(BaseModel):
    id: str
    model: str
    message: Message
    usage: dict


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    模拟聊天接口 — 感受嵌套模型验证。

    测试 Body:
    {
        "messages": [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "你好"}
        ]
    }
    """
    last_user_msg = ""
    for msg in reversed(request.messages):
        print(f"msg: {msg.role == Role.USER} ")
        if msg.role == Role.USER:
            last_user_msg = msg.content
            break

    return ChatResponse(
        id="chatcmpl-demo-001",
        model=request.model,
        message=Message(
            role=Role.ASSISTANT,
            content=f"你发送了：{last_user_msg}（这是模拟回复）",
        ),
        usage={
            "prompt_tokens": len(last_user_msg) * 2,
            "completion_tokens": 20,
            "total_tokens": len(last_user_msg) * 2 + 20,
        },
    )


# ============================================================
# 4. model_dump / model_validate — Pydantic v2 常用方法
# ============================================================

@app.get("/demo/pydantic-methods")
async def pydantic_methods_demo():
    """
    演示 Pydantic v2 常用方法。

    - model_dump(): 模型 → dict
    - model_validate(): dict → 模型（带验证）
    - model_json_schema(): 获取 JSON Schema
    """
    user = UserCreate(name="李四", email="lisi@example.com", age=30)

    raw_dict = {"name": "王五", "email": "wangwu@test.com", "age": 28}
    validated_user = UserCreate.model_validate(raw_dict)

    return {
        "model_dump": user.model_dump(),
        "model_dump_exclude": user.model_dump(exclude={"bio"}),
        "model_validate_from_dict": validated_user.model_dump(),
        "json_schema": UserCreate.model_json_schema(),
    }
