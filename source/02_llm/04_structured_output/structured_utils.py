"""
structured_utils.py
第四章公共工具：provider 配置、结构化输出解析、Pydantic 校验、导出工具
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

try:
    from pydantic import ValidationError
except ImportError:  # pragma: no cover - 运行时环境可能未安装
    ValidationError = Exception  # type: ignore[misc,assignment]


BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "exports"

T = TypeVar("T")


def load_env_if_possible() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _parse_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


@dataclass
class ProviderConfig:
    provider: str
    api_key: str | None
    base_url: str | None
    model: str
    input_price_per_million: float | None = None
    output_price_per_million: float | None = None

    @property
    def is_ready(self) -> bool:
        return bool(self.api_key)


@dataclass
class ChatUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class RawChatResult:
    provider: str
    model: str
    content: str
    usage: ChatUsage | None
    mocked: bool
    request_preview: dict[str, Any]
    raw_response_preview: dict[str, Any]


@dataclass
class JsonParseResult:
    ok: bool
    candidate_text: str | None
    data: Any | None
    error: str | None


def load_provider_config(provider: str | None = None) -> ProviderConfig:
    provider_name = (provider or os.getenv("DEFAULT_PROVIDER", "bailian")).strip().lower()
    mapping = {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "input_price_per_million": _parse_float(os.getenv("OPENAI_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("OPENAI_OUTPUT_PRICE_PER_MILLION")),
        },
        "deepseek": {
            "api_key": os.getenv("DEEPSEEK_API_KEY"),
            "base_url": os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com",
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "input_price_per_million": _parse_float(os.getenv("DEEPSEEK_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("DEEPSEEK_OUTPUT_PRICE_PER_MILLION")),
        },
        "bailian": {
            "api_key": os.getenv("BAILIAN_API_KEY"),
            "base_url": os.getenv("BAILIAN_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": os.getenv("BAILIAN_MODEL", "qwen-plus"),
            "input_price_per_million": _parse_float(os.getenv("BAILIAN_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("BAILIAN_OUTPUT_PRICE_PER_MILLION")),
        },
        "glm": {
            "api_key": os.getenv("GLM_API_KEY"),
            "base_url": os.getenv("GLM_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4/",
            "model": os.getenv("GLM_MODEL", "glm-4.5-air"),
            "input_price_per_million": _parse_float(os.getenv("GLM_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("GLM_OUTPUT_PRICE_PER_MILLION")),
        },
    }
    data = mapping.get(provider_name, mapping["bailian"])
    return ProviderConfig(provider=provider_name, **data)


def preview_chat_request(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    extra_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if extra_options:
        payload.update(extra_options)
    return payload


def call_openai_compatible_chat(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 400,
    extra_options: dict[str, Any] | None = None,
) -> RawChatResult:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("未安装 openai SDK，请先执行：pip install openai") from exc

    request_preview = preview_chat_request(
        config,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        extra_options=extra_options,
    )
    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    request_kwargs = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if extra_options:
        request_kwargs.update(extra_options)

    response = client.chat.completions.create(**request_kwargs)

    usage = None
    if response.usage:
        usage = ChatUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

    message = response.choices[0].message
    raw_response_preview = {
        "id": response.id,
        "model": response.model,
        "choices": [
            {
                "index": 0,
                "finish_reason": response.choices[0].finish_reason,
                "message": {
                    "role": message.role,
                    "content": message.content,
                },
            }
        ],
        "usage": asdict(usage) if usage else None,
    }
    return RawChatResult(
        provider=config.provider,
        model=config.model,
        content=message.content or "",
        usage=usage,
        mocked=False,
        request_preview=request_preview,
        raw_response_preview=raw_response_preview,
    )


def _mock_json_from_prompt(user_prompt: str) -> str:
    normalized = user_prompt.lower()
    if "销售线索结构化提取助手" in user_prompt or ("need_demo" in normalized and "contact" in normalized):
        payload = {
            "name": "王敏",
            "company": "华星零售",
            "city": "杭州",
            "team_size": 30,
            "budget": 50000,
            "intent_level": "high",
            "requested_features": ["权限管理", "多轮问答"],
            "need_demo": True,
            "contact": {
                "email": None,
                "wecom": True,
            },
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if "销售跟进记录" in user_prompt or ("intent_level" in normalized and "next_action" in normalized):
        city = "北京"
        for item in ["杭州", "深圳", "成都", "北京"]:
            if item in user_prompt:
                city = item
                break
        if "王敏" in user_prompt:
            payload = {
                "name": "王敏",
                "company": "华星零售",
                "city": "杭州",
                "intent_level": "high",
                "budget": 50000,
                "next_action": "安排线上演示并确认采购周期",
            }
        elif "李涛" in user_prompt:
            payload = {
                "name": "李涛",
                "company": "云展科技",
                "city": "深圳",
                "intent_level": "medium",
                "budget": None,
                "next_action": "发送试用资料并确认试用时间",
            }
        elif "陈雪" in user_prompt:
            payload = {
                "name": "陈雪",
                "company": "远山教育",
                "city": "成都",
                "intent_level": "high",
                "budget": 80000,
                "next_action": "安排产品评估并跟进季度采购计划",
            }
        else:
            payload = {
                "name": "周凯",
                "company": "连锁餐饮系统项目",
                "city": city,
                "intent_level": "medium",
                "budget": None,
                "next_action": "发送产品资料并确认后续需求细节",
            }
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if "ticket_title" in normalized or "工单" in user_prompt:
        return json.dumps(
            {
                "ticket_title": "支付成功但订单状态未更新",
                "issue_type": "支付",
                "priority": "中",
                "need_human_follow_up": True,
                "summary": "用户已完成付款，但订单状态未更新，需要人工核查。",
            },
            ensure_ascii=False,
            indent=2,
        )
    if "intent_level" in normalized or "lead" in normalized or "销售线索" in user_prompt:
        return json.dumps(
            {
                "name": "王敏",
                "company": "华星零售",
                "city": "杭州",
                "intent_level": "high",
                "budget": 50000,
                "next_action": "安排产品演示并确认采购周期",
            },
            ensure_ascii=False,
            indent=2,
        )
    if "age" in normalized or "job" in normalized or "提取" in user_prompt:
        return json.dumps(
            {
                "name": "张三",
                "gender": "男",
                "age": 28,
                "city": "北京",
                "job": "软件工程师",
            },
            ensure_ascii=False,
            indent=2,
        )
    return json.dumps(
        {
            "summary": "这是一个 mock 结构化输出示例。",
            "confidence": "medium",
        },
        ensure_ascii=False,
        indent=2,
    )


def mock_chat_response(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 400,
    extra_options: dict[str, Any] | None = None,
) -> RawChatResult:
    user_message = next((item["content"] for item in reversed(messages) if item["role"] == "user"), "")
    wants_json = "json" in user_message.lower() or "输出格式" in user_message or "schema" in user_message.lower()
    content = _mock_json_from_prompt(user_message) if wants_json else "[MOCK] 当前请求未包含明显结构化输出要求。"
    return RawChatResult(
        provider=config.provider,
        model=config.model,
        content=content,
        usage=None,
        mocked=True,
        request_preview=preview_chat_request(config, messages, temperature, max_tokens, extra_options),
        raw_response_preview={
            "id": "mock-chatcmpl-structured",
            "model": config.model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                }
            ],
            "usage": None,
        },
    )


def run_chat(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 400,
    extra_options: dict[str, Any] | None = None,
) -> RawChatResult:
    if not config.is_ready:
        return mock_chat_response(
            config,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_options=extra_options,
        )
    return call_openai_compatible_chat(
        config,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        extra_options=extra_options,
    )


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def find_json_candidate(text: str) -> str | None:
    cleaned = strip_code_fence(text)
    if not cleaned:
        return None

    if cleaned.startswith("{") or cleaned.startswith("["):
        return cleaned

    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = cleaned.find(start_char)
        if start == -1:
            continue
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(cleaned)):
            char = cleaned[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == start_char:
                depth += 1
            elif char == end_char:
                depth -= 1
                if depth == 0:
                    return cleaned[start : index + 1]
    return None


def parse_json_output(text: str) -> JsonParseResult:
    candidate = find_json_candidate(text)
    if not candidate:
        return JsonParseResult(
            ok=False,
            candidate_text=None,
            data=None,
            error="未找到可解析的 JSON 片段",
        )
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return JsonParseResult(
            ok=False,
            candidate_text=candidate,
            data=None,
            error=f"JSON 解析失败: {exc}",
        )
    return JsonParseResult(ok=True, candidate_text=candidate, data=data, error=None)


def is_pydantic_available() -> bool:
    try:
        import pydantic  # noqa: F401
    except ImportError:
        return False
    return True


def get_model_json_schema(model_cls: type[Any]) -> dict[str, Any]:
    if hasattr(model_cls, "model_json_schema"):
        return model_cls.model_json_schema()
    if hasattr(model_cls, "schema"):
        return model_cls.schema()
    raise TypeError("当前对象不支持导出 JSON Schema")


def model_validate(model_cls: type[T], data: Any) -> T:
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)
    if hasattr(model_cls, "parse_obj"):
        return model_cls.parse_obj(data)
    raise TypeError("当前对象不支持 Pydantic 验证")


def model_dump(instance: Any) -> dict[str, Any]:
    if hasattr(instance, "model_dump"):
        return instance.model_dump()
    if hasattr(instance, "dict"):
        return instance.dict()
    raise TypeError("当前实例不支持导出字典")


def format_validation_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError) and hasattr(exc, "errors"):
        parts: list[str] = []
        for item in exc.errors():  # type: ignore[union-attr]
            location = ".".join(str(x) for x in item.get("loc", [])) or "<root>"
            parts.append(f"{location}: {item.get('msg', 'invalid')}")
        return "; ".join(parts)
    return str(exc)


def _render_schema_properties(
    properties: dict[str, Any],
    required: set[str],
    defs: dict[str, Any],
    indent: int = 0,
) -> list[str]:
    lines: list[str] = []
    prefix = "  " * indent
    for name, meta in properties.items():
        type_name, nested_properties, nested_required = _resolve_schema_meta(meta, defs)
        description = meta.get("description", "")
        enum_values = meta.get("enum")
        optional = "required" if name in required else "optional"
        detail = f"{prefix}- {name}: {type_name}, {optional}"
        if description:
            detail += f", {description}"
        if enum_values:
            detail += f", allowed={enum_values}"
        lines.append(detail)
        if nested_properties:
            lines.extend(_render_schema_properties(nested_properties, nested_required, defs, indent + 1))
        item_meta = meta.get("items", {})
        if item_meta:
            _, item_properties, item_required = _resolve_schema_meta(item_meta, defs)
        else:
            item_properties, item_required = None, set()
        if item_properties:
            lines.append(f"{prefix}  - items:")
            lines.extend(_render_schema_properties(item_properties, item_required, defs, indent + 2))
    return lines


def schema_to_prompt_description(model_cls: type[Any]) -> str:
    schema = get_model_json_schema(model_cls)
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    defs = schema.get("$defs", {})
    lines = _render_schema_properties(properties, required, defs)
    return "\n".join(lines)


def _resolve_schema_meta(meta: dict[str, Any], defs: dict[str, Any]) -> tuple[str, dict[str, Any] | None, set[str]]:
    if "$ref" in meta:
        ref = meta["$ref"]
        if ref.startswith("#/$defs/"):
            def_name = ref.split("/")[-1]
            resolved = defs.get(def_name, {})
            type_name = resolved.get("type", "object")
            return type_name, resolved.get("properties"), set(resolved.get("required", []))

    if "anyOf" in meta:
        type_names: list[str] = []
        nested_properties: dict[str, Any] | None = None
        nested_required: set[str] = set()
        for item in meta["anyOf"]:
            if "$ref" in item and item["$ref"].startswith("#/$defs/"):
                def_name = item["$ref"].split("/")[-1]
                resolved = defs.get(def_name, {})
                nested_properties = resolved.get("properties")
                nested_required = set(resolved.get("required", []))
                type_name = resolved.get("type")
            else:
                type_name = item.get("type")
            if type_name:
                type_names.append(type_name)
        if type_names:
            return "|".join(type_names), nested_properties, nested_required

    type_name = meta.get("type", "object")
    return type_name, meta.get("properties"), set(meta.get("required", []))


def build_json_fix_prompt(bad_output: str, error_message: str, schema_description: str | None = None) -> str:
    prompt = [
        "上一次结构化输出校验失败，请只返回修正后的 JSON。",
        "",
        "错误信息：",
        error_message,
        "",
        "上一次输出：",
        bad_output,
    ]
    if schema_description:
        prompt.extend(
            [
                "",
                "目标 Schema：",
                schema_description,
            ]
        )
    prompt.extend(
        [
            "",
            "要求：",
            "1. 只输出一个合法 JSON 对象。",
            "2. 保留已有正确字段，修复缺失字段、类型错误和非法取值。",
            "3. 如果信息不足，用 null 或空数组，不要编造新事实。",
        ]
    )
    return "\n".join(prompt)


def estimate_cost(config: ProviderConfig, prompt_tokens: int, completion_tokens: int) -> float | None:
    if config.input_price_per_million is None or config.output_price_per_million is None:
        return None
    input_cost = prompt_tokens / 1_000_000 * config.input_price_per_million
    output_cost = completion_tokens / 1_000_000 * config.output_price_per_million
    return input_cost + output_cost


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def print_json(title: str, payload: Any) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)
    print(json_dumps(payload))


def write_json_export(filename: str, payload: Any) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / filename
    path.write_text(json_dumps(payload), encoding="utf-8")
    return path


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
