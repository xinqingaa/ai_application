"""
prompt_utils.py
第三章公共工具：provider 配置、Prompt 审计、模板变量校验、真实/Mock 调用
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any, Iterable


BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "exports"


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
class ChatResult:
    provider: str
    model: str
    content: str
    usage: ChatUsage | None
    mocked: bool
    request_preview: dict[str, Any]
    raw_response_preview: dict[str, Any]


@dataclass
class PromptAudit:
    score: int
    has_role: bool
    has_task: bool
    has_context: bool
    has_constraints: bool
    has_output_format: bool
    has_negative_constraints: bool
    has_examples: bool
    estimated_tokens: int
    strengths: list[str]
    risks: list[str]


@dataclass
class TemplateCheck:
    variables: list[str]
    missing_variables: list[str]
    unused_variables: list[str]


@dataclass
class EvaluationRow:
    case_id: str
    input_text: str
    expected: str
    predicted: str
    correct: bool
    raw_output: str


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
) -> dict[str, Any]:
    return {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def call_openai_compatible_chat(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 400,
) -> ChatResult:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("未安装 openai SDK，请先执行：pip install openai") from exc

    request_preview = preview_chat_request(config, messages, temperature, max_tokens)
    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    response = client.chat.completions.create(
        model=config.model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
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
    return ChatResult(
        provider=config.provider,
        model=config.model,
        content=message.content or "",
        usage=usage,
        mocked=False,
        request_preview=request_preview,
        raw_response_preview=raw_response_preview,
    )


def mock_chat_response(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 400,
) -> ChatResult:
    user_message = next((item["content"] for item in reversed(messages) if item["role"] == "user"), "")
    system_message = next((item["content"] for item in messages if item["role"] == "system"), "")
    audit = analyze_prompt(user_message)
    content = (
        f"[MOCK:{config.provider}] 结构分={audit.score}/7\n"
        f"最后一条用户提示词长度约 {audit.estimated_tokens} tokens\n"
        f"已检测到字段：角色={audit.has_role} / 任务={audit.has_task} / 输出格式={audit.has_output_format}\n"
        f"system 摘要：{system_message[:40] or '（无）'}"
    )
    return ChatResult(
        provider=config.provider,
        model=config.model,
        content=content,
        usage=None,
        mocked=True,
        request_preview=preview_chat_request(config, messages, temperature, max_tokens),
        raw_response_preview={
            "id": "mock-chatcmpl-prompt",
            "model": config.model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
            "usage": None,
        },
    )


def run_chat(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 400,
) -> ChatResult:
    if not config.is_ready:
        return mock_chat_response(config, messages, temperature=temperature, max_tokens=max_tokens)
    return call_openai_compatible_chat(config, messages, temperature=temperature, max_tokens=max_tokens)


def estimate_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    try:
        import tiktoken
    except ImportError:
        ascii_chars = sum(1 for char in text if ord(char) < 128)
        non_ascii_chars = len(text) - ascii_chars
        english_est = max(1, ascii_chars // 4) if ascii_chars else 0
        chinese_est = max(1, int(non_ascii_chars / 1.5)) if non_ascii_chars else 0
        return english_est + chinese_est

    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def analyze_prompt(prompt: str) -> PromptAudit:
    has_role = bool(re.search(r"你是|你的角色|角色[:：]|扮演", prompt))
    has_task = bool(re.search(r"任务[:：]|请你|请根据|目标[:：]|请完成", prompt))
    has_context = bool(re.search(r"背景[:：]|上下文[:：]|输入[:：]|材料[:：]|需求[:：]|用户反馈[:：]", prompt))
    has_constraints = bool(re.search(r"要求[:：]|限制[:：]|约束[:：]|控制在|不要超过|必须", prompt))
    has_output_format = bool(re.search(r"输出格式[:：]|按以下格式|JSON|Markdown|分点输出|表格", prompt))
    has_negative_constraints = bool(re.search(r"不要|禁止|不得|不要输出|不要编造", prompt))
    has_examples = bool(re.search(r"示例|例子|few-shot|输入：.+输出：", prompt, re.DOTALL))

    strengths: list[str] = []
    risks: list[str] = []

    if has_role:
        strengths.append("指定了角色，有助于限制回答视角。")
    else:
        risks.append("没有角色信息，模型容易自行选择表达风格。")

    if has_task:
        strengths.append("任务目标相对明确。")
    else:
        risks.append("缺少清晰任务描述，模型需要自行猜测目标。")

    if has_context:
        strengths.append("包含输入材料或业务背景。")
    else:
        risks.append("缺少上下文，模型可能把常识当成你的真实场景。")

    if has_constraints:
        strengths.append("给出了约束条件。")
    else:
        risks.append("缺少约束，输出长度、粒度和边界会飘。")

    if has_output_format:
        strengths.append("输出格式明确，便于人工阅读或程序消费。")
    else:
        risks.append("没有固定输出格式，后续程序接入会更脆弱。")

    if has_negative_constraints:
        strengths.append("包含负向限制，能减少跑题或臆造。")
    else:
        risks.append("没有负向限制，模型可能补充你没有要求的内容。")

    if has_examples:
        strengths.append("包含示例，有利于对齐分类或格式任务。")
    else:
        risks.append("没有示例时，边界任务更依赖模型自己理解。")

    score = sum(
        [
            has_role,
            has_task,
            has_context,
            has_constraints,
            has_output_format,
            has_negative_constraints,
            has_examples,
        ]
    )
    return PromptAudit(
        score=score,
        has_role=has_role,
        has_task=has_task,
        has_context=has_context,
        has_constraints=has_constraints,
        has_output_format=has_output_format,
        has_negative_constraints=has_negative_constraints,
        has_examples=has_examples,
        estimated_tokens=estimate_tokens(prompt),
        strengths=strengths,
        risks=risks,
    )


def extract_template_variables(template_text: str) -> list[str]:
    variables = re.findall(r"\$\{?([a-zA-Z_][a-zA-Z0-9_]*)\}?", template_text)
    return sorted(set(variables))


def validate_template_variables(template_text: str, variables: dict[str, Any]) -> TemplateCheck:
    declared = extract_template_variables(template_text)
    provided = sorted(variables.keys())
    missing = sorted(name for name in declared if name not in variables)
    unused = sorted(name for name in provided if name not in declared)
    return TemplateCheck(
        variables=declared,
        missing_variables=missing,
        unused_variables=unused,
    )


def render_template_text(template_text: str, variables: dict[str, Any]) -> tuple[str, TemplateCheck]:
    check = validate_template_variables(template_text, variables)
    rendered = Template(template_text).safe_substitute(**variables)
    return rendered, check


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json_export(filename: str, payload: dict[str, Any]) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def print_json(title: str, payload: dict[str, Any]) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_lines(title: str, lines: Iterable[str]) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)
    for line in lines:
        print(line)


def normalize_label(text: str, allowed_labels: list[str]) -> str:
    compact = re.sub(r"\s+", "", text)
    for label in allowed_labels:
        if label in compact:
            return label
    return compact[:20] or "EMPTY"
