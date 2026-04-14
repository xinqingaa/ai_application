"""
structured_utils.py
第四章公共工具：provider 配置、结构化输出解析、Pydantic 校验、导出工具

这个文件不是某个单独示例脚本的入口，而是第四章所有示例共享的“结构化输出工具箱”。
它主要负责 5 类事情：

1. 尝试加载 `.env`，并整理 provider 配置
2. 统一真实调用 / Mock 回退 / 调试日志输出
3. 解析模型返回文本中的 JSON 片段
4. 导出 Pydantic 模型对应的 JSON Schema，并把它转换成 Prompt 可读描述
5. 提供 Pydantic 校验、错误格式化、导出和打印等辅助能力

阅读顺序建议：
load_env_if_possible()
-> load_provider_config()
-> preview_chat_request()
-> run_chat()
-> parse_json_output()
-> get_model_json_schema()
-> schema_to_prompt_description()
-> model_validate()

如果你在看第四章脚本时有两个疑问：
1. “模型调用前的请求参数是在哪里统一打印的？”
2. “LeadRecord 这种 Pydantic 类是怎么变成 JSON Schema 和 Prompt 描述的？”

答案基本都在这个文件里。
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
DEFAULT_DEBUG = True

T = TypeVar("T")


def load_env_if_possible() -> None:
    """作用：
    尝试加载 `.env` 环境变量，降低第四章示例脚本的启动门槛。

    参数：
    无。函数会优先尝试导入 `python-dotenv`；如果本地未安装，则静默跳过。
    """
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
    """第四章运行时 provider 配置对象。

    各个示例脚本统一依赖这个对象，不再自己零散读取环境变量。
    这样无论你切换百炼、DeepSeek、GLM 还是 OpenAI-compatible 平台，
    上层脚本拿到的接口形态都保持一致。
    """

    provider: str
    api_key: str | None
    base_url: str | None
    model: str
    input_price_per_million: float | None = None
    output_price_per_million: float | None = None

    @property
    def is_ready(self) -> bool:
        """作用：
        判断当前配置是否满足真实调用模型的基本条件。

        返回：
        `True` 表示具备 API Key，可以尝试真实请求；
        `False` 表示更适合回退到 Mock 模式。
        """
        return bool(self.api_key)


@dataclass
class ChatUsage:
    """统一的 token 用量结构。

    上层脚本只依赖这个简单对象，不需要直接理解底层 SDK 的 usage 细节。
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class RawChatResult:
    """统一的聊天结果对象。

    无论是真实调用还是 Mock 回退，最终都收口成这份结构。
    这样第四章脚本既能拿到 `content` 做 JSON 解析，
    也能拿到 `request_preview` / `raw_response_preview` 做调试对照。
    """

    provider: str
    model: str
    content: str
    usage: ChatUsage | None
    mocked: bool
    request_preview: dict[str, Any]
    raw_response_preview: dict[str, Any]


@dataclass
class JsonParseResult:
    """模型文本解析为 JSON 后的标准化结果。"""

    ok: bool
    candidate_text: str | None
    data: Any | None
    error: str | None


def load_provider_config(provider: str | None = None) -> ProviderConfig:
    """作用：
    按 provider 名称从环境变量中整理出统一配置。

    参数：
    provider: 可选的平台名称；不传时读取 `DEFAULT_PROVIDER`，默认回退到 `bailian`。

    返回：
    一个 `ProviderConfig`，里面包含模型名、鉴权信息、base_url 和价格配置。

    使用位置：
    第四章脚本通常在 `main()` 开头先拿到这份配置，再交给 `run_chat()`。
    """
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
    """作用：
    生成一次聊天调用的请求预览对象。

    这份对象不会直接发给模型，它主要用于：
    1. 调试日志打印
    2. Mock 结果里保留“原始入参视角”
    3. 教学时观察 JSON Mode 等额外参数到底长什么样
    """
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if extra_options:
        payload.update(extra_options)
    return payload


def _debug_print_start(
    config: ProviderConfig,
    request_preview: dict[str, Any],
    debug_label: str | None = None,
) -> None:
    if debug_label:
        print(f"\n{'=' * 72}")
        print(f"[DEBUG] {debug_label} -> 请求开始")
        print("=" * 72)
    print(
        "[DEBUG] chat.start "
        f"provider={config.provider} "
        f"model={config.model} "
        f"ready={config.is_ready}"
    )
    print("[DEBUG] request_preview:")
    print(json.dumps(request_preview, ensure_ascii=False, indent=2))


def _debug_print_result(result: RawChatResult, debug_label: str | None = None) -> None:
    finish_reason = None
    choices = result.raw_response_preview.get("choices") or []
    if choices:
        finish_reason = choices[0].get("finish_reason")

    if debug_label:
        print(f"\n{'=' * 72}")
        print(f"[DEBUG] {debug_label} -> 返回结果")
        print("=" * 72)
    print(
        "[DEBUG] chat.result "
        f"provider={result.provider} "
        f"model={result.model} "
        f"mocked={result.mocked} "
        f"finish_reason={finish_reason or '（未返回）'}"
    )
    print("[DEBUG] raw_response_preview:")
    print(json.dumps(result.raw_response_preview or {}, ensure_ascii=False, indent=2))
    print("[DEBUG] raw_content:")
    print(result.content)


def call_openai_compatible_chat(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 400,
    extra_options: dict[str, Any] | None = None,
) -> RawChatResult:
    """作用：
    发起一次真实的 OpenAI-compatible 聊天调用，并收口为统一结果结构。

    参数：
    config: 统一 provider 配置。
    messages: 标准聊天消息列表。
    temperature: 采样温度。
    max_tokens: 最大输出 token 数。
    extra_options: 附加请求参数，例如 `response_format`。

    返回：
    一个 `RawChatResult`，包含原始文本、请求预览和响应预览。
    """
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
    """作用：
    在缺少真实 API Key 时生成可教学、可调试的 Mock 结构化输出。

    这样第四章很多脚本即使在离线或未配置鉴权时，也能继续演示：
    Prompt 长什么样、JSON 怎么解析、Schema 怎么校验。
    """
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
    debug: bool = DEFAULT_DEBUG,
    debug_label: str | None = None,
) -> RawChatResult:
    """作用：
    统一第四章脚本的聊天调用入口。

    它负责三件核心事情：
    1. 在调用前打印请求预览和运行配置
    2. 根据 `config.is_ready` 决定走真实调用还是 Mock 回退
    3. 在调用后打印响应预览和原始返回文本

    这也是第四章调试日志最重要的收口点。
    如果你在脚本里看到 `[DEBUG] request_preview` 和 `[DEBUG] raw_content`，
    基本就是从这里打出来的。
    """
    request_preview = preview_chat_request(config, messages, temperature, max_tokens, extra_options)
    if debug:
        _debug_print_start(config, request_preview, debug_label)

    if not config.is_ready:
        if debug:
            print(
                "[DEBUG] mock_fallback "
                f"provider={config.provider} "
                "reason=missing_api_key"
            )
        result = mock_chat_response(
            config,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_options=extra_options,
        )
        if debug:
            _debug_print_result(result, debug_label)
        return result

    try:
        result = call_openai_compatible_chat(
            config,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_options=extra_options,
        )
    except Exception as exc:
        if debug:
            print(
                "[DEBUG] request_failed "
                f"provider={config.provider} "
                f"error={type(exc).__name__}: {exc}"
            )
        raise

    if debug:
        _debug_print_result(result, debug_label)
    return result


def strip_code_fence(text: str) -> str:
    """去掉包裹在最外层的 Markdown 代码块。"""
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def find_json_candidate(text: str) -> str | None:
    """作用：
    从一段模型原始文本里尽量提取出最可能的 JSON 片段。

    这一步主要解决两类常见问题：
    1. 模型在 JSON 前后额外夹带解释文字
    2. 模型把 JSON 放在 Markdown 代码块里
    """
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
    """作用：
    尝试把模型输出文本解析成 JSON，并返回标准化结果。

    返回：
    `ok=True` 时，`data` 是解析后的 Python 对象；
    `ok=False` 时，`error` 会说明失败发生在“没找到 JSON”还是“JSON 语法错误”。

    使用位置：
    第四章脚本通常先 `run_chat()`，再 `parse_json_output()`，
    最后才进入 Pydantic 校验。
    """
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
    """检查运行环境是否安装了 Pydantic。"""
    try:
        import pydantic  # noqa: F401
    except ImportError:
        return False
    return True


def get_model_json_schema(model_cls: type[Any]) -> dict[str, Any]:
    """作用：
    把 Pydantic 模型导出成 JSON Schema 字典。

    这就是 `02_pydantic_schema.py` 里打印出来那份 `LeadRecord JSON Schema` 的来源。
    在第四章里，它的意义不是让你手写 JSON Schema，
    而是让你看到：同一份 Python 结构定义可以自动变成程序可读的标准结构描述。
    """
    if hasattr(model_cls, "model_json_schema"):
        return model_cls.model_json_schema()
    if hasattr(model_cls, "schema"):
        return model_cls.schema()
    raise TypeError("当前对象不支持导出 JSON Schema")


def model_validate(model_cls: type[T], data: Any) -> T:
    """作用：
    用 Pydantic 模型校验解析后的 JSON 数据是否符合业务结构。

    这一步解决的不是“是不是合法 JSON”，
    而是“字段、类型、枚举、嵌套结构是否符合 Schema”。
    """
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)
    if hasattr(model_cls, "parse_obj"):
        return model_cls.parse_obj(data)
    raise TypeError("当前对象不支持 Pydantic 验证")


def model_dump(instance: Any) -> dict[str, Any]:
    """把 Pydantic 实例统一导出为普通字典。"""
    if hasattr(instance, "model_dump"):
        return instance.model_dump()
    if hasattr(instance, "dict"):
        return instance.dict()
    raise TypeError("当前实例不支持导出字典")


def format_validation_error(exc: Exception) -> str:
    """把 Pydantic 校验错误整理成更适合打印和重试提示的短文本。"""
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
    """递归把 JSON Schema 的字段定义转成更适合 Prompt 的行文本。"""
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
    """作用：
    把 Pydantic 模型转换成 Prompt 可读的字段说明列表。

    例如 `LeadRecord` 最终会变成：
    `- name: string, required, 客户姓名`
    这种更适合喂给模型的描述格式。

    这说明 Schema 不只服务程序校验，也能反向服务 Prompt 约束。
    """
    schema = get_model_json_schema(model_cls)
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    defs = schema.get("$defs", {})
    lines = _render_schema_properties(properties, required, defs)
    return "\n".join(lines)


def _resolve_schema_meta(meta: dict[str, Any], defs: dict[str, Any]) -> tuple[str, dict[str, Any] | None, set[str]]:
    """解析单个 JSON Schema 字段的类型、嵌套属性和必填信息。"""
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
    """作用：
    在结构化输出失败后，构造“带错误反馈”的修复 Prompt。

    这是第四章重试策略的关键辅助函数：
    不只是重跑原请求，而是把错误信息和目标 Schema 一起回喂给模型。
    """
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
    """按每百万 token 单价粗略估算一次请求成本。"""
    if config.input_price_per_million is None or config.output_price_per_million is None:
        return None
    input_cost = prompt_tokens / 1_000_000 * config.input_price_per_million
    output_cost = completion_tokens / 1_000_000 * config.output_price_per_million
    return input_cost + output_cost


def json_dumps(payload: Any) -> str:
    """统一使用中文友好的 JSON pretty print。"""
    return json.dumps(payload, ensure_ascii=False, indent=2)


def print_json(title: str, payload: Any) -> None:
    """打印带标题和分隔线的 JSON 内容。"""
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)
    print(json_dumps(payload))


def write_json_export(filename: str, payload: Any) -> Path:
    """把 JSON 内容导出到第四章 `exports/` 目录。"""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / filename
    path.write_text(json_dumps(payload), encoding="utf-8")
    return path


def timestamp_slug() -> str:
    """生成适合导出文件名的时间戳片段。"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
