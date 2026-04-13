"""
prompt_utils.py
第三章公共工具：provider 配置、Prompt 审计、模板变量校验、真实/Mock 调用

这个文件不是某个单独示例脚本的入口，而是第三章所有示例共享的“底层工具箱”。
它主要负责 6 类事情：

1. 尝试加载 `.env`，把环境准备动作集中到公共层
2. 把 provider 相关环境变量整理成统一的 `ProviderConfig`
3. 构造聊天请求预览，并根据配置决定走真实调用还是 Mock 回退
4. 审计 Prompt 结构，检查角色、任务、上下文、约束和输出格式是否齐全
5. 解析模板变量、校验变量缺失情况，并渲染最终 Prompt
6. 提供导出、打印和标签归一化等辅助能力

阅读顺序建议：
load_env_if_possible()
-> load_provider_config()
-> run_chat()
-> call_openai_compatible_chat() / mock_chat_response()
-> analyze_prompt()
-> extract_template_variables()
-> validate_template_variables()
-> render_template_text()

典型使用方式：
1. 示例脚本启动时，先调用 `load_env_if_possible()` 和 `load_provider_config()`
2. 构造 `messages` 后统一走 `run_chat()`，由它决定真实调用还是 Mock 回退
3. 如果当前脚本关注 Prompt 质量，可在调用前后配合 `analyze_prompt()` 做结构检查
4. 如果当前脚本关注模板工程化，则走 `extract_template_variables()`、
   `validate_template_variables()`、`render_template_text()` 这条模板链路
5. 如果需要保存调试结果，再使用 `write_json_export()`、`print_json()`、`print_lines()`
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any, Iterable


BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "exports"
DEFAULT_DEBUG = True


def load_env_if_possible() -> None:
    """作用：
    尝试加载 `.env` 环境变量，降低示例脚本的环境准备成本。

    参数：
    无。函数会尝试导入 `python-dotenv`；如果本地未安装，则直接跳过。
    """
    # 这里保持“可选加载”：
    # 装了 python-dotenv 就读 .env；没装也不影响第三章示例继续运行。
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _parse_float(value: str | None) -> float | None:
    """作用：
    把环境变量里的字符串价格配置安全转换成 `float`。

    参数：
    value: 可能来自环境变量的字符串；为空或格式非法时会返回 `None`。

    返回：
    转换成功时返回浮点数；否则返回 `None`。
    """
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


@dataclass
class ProviderConfig:
    """第三章运行时 provider 配置对象。

    上层示例代码统一依赖这个对象，不再直接散落读取环境变量，
    这样不同平台的鉴权和模型名差异都被收口到配置层。
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
        判断当前 provider 配置是否具备真实调用的最基本条件。

        参数：
        无。函数直接检查当前对象中的 `api_key` 是否存在。

        返回：
        `True` 表示可以尝试真实调用，`False` 表示更适合回退到 Mock 模式。
        """
        return bool(self.api_key)


@dataclass
class ChatUsage:
    """统一的 token 用量结构。

    这样上层脚本打印 token 消耗时，不需要直接依赖底层 SDK 的 usage 对象格式。
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatResult:
    """统一的聊天结果结构。

    无论是真实调用还是 Mock 回退，最终都整理成同一对象，
    这样第三章示例可以用一致方式读取内容、调试预览、错误信息和 token 信息。
    """

    provider: str
    model: str
    content: str
    usage: ChatUsage | None = None
    mocked: bool = False
    request_preview: dict[str, Any] | None = None
    raw_response_preview: dict[str, Any] | None = None
    elapsed_ms: float | None = None
    error: str | None = None
    debug_info: dict[str, Any] | None = None


@dataclass
class PromptAudit:
    """Prompt 结构审计结果。

    这层对象把各项检查布尔值、风险提示和整体分数统一收口，
    方便脚本同时打印结构分和可读的诊断结论。
    """

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
    """模板变量校验结果。

    用来区分模板里声明了哪些变量、哪些变量缺失、以及哪些输入变量没有被模板消费。
    """

    variables: list[str]
    missing_variables: list[str]
    unused_variables: list[str]


@dataclass
class EvaluationRow:
    """单条评测样本的标准化记录。

    这一层适合在批量评估场景里统一保存输入、期望输出、模型输出和命中情况。
    当前文件暂未直接消费，但保留为第三章扩展示例的公共结构。
    """

    case_id: str
    input_text: str
    expected: str
    predicted: str
    correct: bool
    raw_output: str


def load_provider_config(provider: str | None = None) -> ProviderConfig:
    """作用：
    按 provider 名称从环境变量中整理出统一的运行时配置对象。

    参数：
    provider: 可选的 provider 名称；不传时会读取 `DEFAULT_PROVIDER`，默认回退到 `bailian`。

    返回：
    一个 `ProviderConfig` 对象，包含模型、鉴权、base_url 和价格信息。

    使用位置：
    第三章所有示例脚本都会先拿到这份配置，再把它交给 `run_chat()`。
    """
    provider_name = (provider or os.getenv("DEFAULT_PROVIDER", "bailian")).strip().lower()
    # 第三章只覆盖课程里常用的 OpenAI-compatible 平台；
    # 配置层先统一成一个映射，再由下游统一消费。
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
    """作用：
    生成一份便于调试和教学展示的请求预览结构。

    参数：
    config: 当前 provider 的运行时配置。
    messages: 准备发送给模型的消息列表。
    temperature: 本次生成温度。
    max_tokens: 本次输出 token 上限。

    返回：
    一个与真实请求核心字段对齐的字典，用于打印或导出调试信息。

    流程位置：
    这个函数只负责生成“请求快照”，不会真正发请求；
    真实调用和 Mock 调用都会复用它，保证调试输出口径一致。
    """
    return {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def _build_debug_info(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    request_preview: dict[str, Any],
    *,
    mocked: bool,
    raw_response_preview: dict[str, Any] | None = None,
    usage: ChatUsage | None = None,
    elapsed_ms: float | None = None,
    error: str | None = None,
    fallback_reason: str | None = None,
) -> dict[str, Any]:
    """作用：
    构造一份统一的调试信息快照，口径尽量对齐第二章的“摘要 + 请求预览 + 响应预览”模式。

    参数：
    config: 当前 provider 的运行时配置。
    messages: 本轮请求的消息列表。
    temperature: 本轮生成温度。
    max_tokens: 本轮输出 token 上限。
    request_preview: 已整理好的请求预览。
    mocked: 当前结果是否为 Mock 回退。
    raw_response_preview: 精简后的响应预览。
    usage: 本轮 token 用量。
    elapsed_ms: 本轮调用耗时，毫秒。
    error: 可选错误信息。
    fallback_reason: 可选回退原因，用于解释为何进入 Mock。

    返回：
    一个包含调用摘要、请求预览、Prompt 审计和响应预览的调试字典。
    """
    user_message = next((item["content"] for item in reversed(messages) if item["role"] == "user"), "")
    audit = analyze_prompt(user_message) if user_message else None
    return {
        "chat": {
            "mode": "mock" if mocked else "real",
            "provider": config.provider,
            "model": config.model,
            "base_url": config.base_url,
            "ready": config.is_ready,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "message_count": len(messages),
            "elapsed_ms": elapsed_ms,
            "usage": asdict(usage) if usage else None,
            "error": error,
            "fallback_reason": fallback_reason,
        },
        "prompt_audit": asdict(audit) if audit else None,
        "raw_response_preview": raw_response_preview,
    }


def call_openai_compatible_chat(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 400,
    debug: bool = DEFAULT_DEBUG,
) -> ChatResult:
    """作用：
    使用 OpenAI SDK 按 OpenAI-compatible 协议发起一次真实聊天调用。

    参数：
    config: 当前 provider 的运行时配置，包含 API Key、base_url 和模型名。
    messages: 发给模型的消息列表。
    temperature: 生成温度，默认值适合课程演示里的稳定输出场景。
    max_tokens: 最大输出 token 数。
    debug: 是否附带完整调试快照；默认开启。

    返回：
    一个标准化后的 `ChatResult`，同时保留请求预览和精简响应预览，便于调试。

    流程位置：
    这是 `run_chat()` 在“环境已就绪”分支下调用的真实请求实现。
    """
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("未安装 openai SDK，请先执行：pip install openai") from exc

    request_preview = preview_chat_request(config, messages, temperature, max_tokens)
    start = time.time()
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
    # 这里只保留课堂演示需要的关键字段，避免直接打印完整 SDK 对象带来噪音。
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
    elapsed_ms = (time.time() - start) * 1000
    return ChatResult(
        provider=config.provider,
        model=config.model,
        content=message.content or "",
        usage=usage,
        mocked=False,
        request_preview=request_preview,
        raw_response_preview=raw_response_preview,
        elapsed_ms=elapsed_ms,
        debug_info=(
            _build_debug_info(
                config,
                messages,
                temperature,
                max_tokens,
                request_preview,
                mocked=False,
                raw_response_preview=raw_response_preview,
                usage=usage,
                elapsed_ms=elapsed_ms,
            )
            if debug
            else None
        ),
    )


def mock_chat_response(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 400,
    error: str | None = None,
    fallback_reason: str | None = None,
    debug: bool = DEFAULT_DEBUG,
) -> ChatResult:
    """作用：
    在没有可用 API Key 时，生成一份可读的 Mock 结果，保证示例脚本仍可演示流程。

    参数：
    config: 当前 provider 的运行时配置。
    messages: 原本准备发送给模型的消息列表。
    temperature: 生成温度；这里主要用于保留请求预览的一致性。
    max_tokens: 最大输出 token 数；这里主要用于保留请求预览的一致性。
    error: 可选错误说明，常用于解释为什么发生了 Mock 回退。
    fallback_reason: 可选回退原因代码，便于上层脚本做分类展示。
    debug: 是否附带完整调试快照；默认开启。

    返回：
    一个 `mocked=True` 的 `ChatResult`，内容以 Prompt 审计摘要为主。

    流程位置：
    这是 `run_chat()` 在“环境未就绪”分支下调用的兜底实现，
    目标不是模拟真实模型能力，而是让教学脚本能继续展示流程。
    """
    user_message = next((item["content"] for item in reversed(messages) if item["role"] == "user"), "")
    system_message = next((item["content"] for item in messages if item["role"] == "system"), "")
    audit = analyze_prompt(user_message)
    request_preview = preview_chat_request(config, messages, temperature, max_tokens)
    content = (
        f"[MOCK:{config.provider}] 结构分={audit.score}/7\n"
        f"最后一条用户提示词长度约 {audit.estimated_tokens} tokens\n"
        f"已检测到字段：角色={audit.has_role} / 任务={audit.has_task} / 输出格式={audit.has_output_format}\n"
        f"system 摘要：{system_message[:40] or '（无）'}"
    )
    if error:
        content += f"\n回退原因：{error}"

    raw_response_preview = {
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
    }
    return ChatResult(
        provider=config.provider,
        model=config.model,
        content=content,
        usage=None,
        mocked=True,
        request_preview=request_preview,
        raw_response_preview=raw_response_preview,
        elapsed_ms=0.0,
        error=error,
        debug_info=(
            _build_debug_info(
                config,
                messages,
                temperature,
                max_tokens,
                request_preview,
                mocked=True,
                raw_response_preview=raw_response_preview,
                elapsed_ms=0.0,
                error=error,
                fallback_reason=fallback_reason,
            )
            if debug
            else None
        ),
    )


def run_chat(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 400,
    debug: bool = DEFAULT_DEBUG,
) -> ChatResult:
    """作用：
    统一封装第三章里的聊天调用入口，自动在真实调用和 Mock 之间切换。

    参数：
    config: 当前 provider 的运行时配置。
    messages: 要发送给模型的消息列表。
    temperature: 生成温度。
    max_tokens: 最大输出 token 数。
    debug: 是否附带完整调试信息；默认开启。

    返回：
    一个标准化后的 `ChatResult`。

    流程位置：
    第三章脚本不直接区分真实调用函数和 Mock 函数，而是统一依赖这里。
    """
    # 第三章示例统一走这里：
    # 环境就绪时真实调用；环境未就绪时返回 Mock，保证课程脚本可直接跑通。
    if not config.is_ready:
        return mock_chat_response(
            config,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            error="未检测到可用 API Key，自动进入 Mock 模式。",
            fallback_reason="missing_api_key",
            debug=debug,
        )

    try:
        return call_openai_compatible_chat(
            config,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            debug=debug,
        )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        return mock_chat_response(
            config,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            error=f"真实调用失败，自动进入 Mock 模式。{error}",
            fallback_reason="request_failed",
            debug=debug,
        )


def estimate_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """作用：
    估算一段文本大致会消耗多少 token。

    参数：
    text: 要估算的文本。
    encoding_name: `tiktoken` 的编码名称，默认使用常见的 `cl100k_base`。

    返回：
    文本的大致 token 数；如果本地没有 `tiktoken`，则回退到启发式估算。

    使用位置：
    主要用于 Prompt 审计、Few-shot 成本对比，以及课堂里观察上下文长度变化。
    """
    try:
        import tiktoken
    except ImportError:
        ascii_chars = sum(1 for char in text if ord(char) < 128)
        non_ascii_chars = len(text) - ascii_chars
        # 没装 tiktoken 时，用较粗略但足够教学演示的方式估算：
        # 英文按约 4 个字符 1 token，中文按约 1.5 个字符 1 token。
        english_est = max(1, ascii_chars // 4) if ascii_chars else 0
        chinese_est = max(1, int(non_ascii_chars / 1.5)) if non_ascii_chars else 0
        return english_est + chinese_est

    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def analyze_prompt(prompt: str) -> PromptAudit:
    """作用：
    对 Prompt 做一轮基于规则的结构审计，判断其关键组成是否齐全。

    参数：
    prompt: 待分析的提示词文本。

    返回：
    一个 `PromptAudit` 对象，包含布尔检查项、总分、token 估算以及优点和风险提示。

    流程位置：
    这个函数不负责改写 Prompt，只负责把 Prompt 结构问题显式化，
    方便示例脚本比较“模糊 Prompt / 结构化 Prompt / Few-shot Prompt”的差异。
    """
    # 这里是课程里使用的启发式规则，不追求严格 NLP 解析，
    # 重点是帮助学习者快速定位 Prompt 结构缺口。
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
    """作用：
    从模板文本中提取 `${name}` 或 `$name` 形式的变量名。

    参数：
    template_text: 原始模板文本。

    返回：
    去重并排序后的变量名列表。

    流程位置：
    这是模板链路的第一步，先知道模板“声明了什么变量”，
    后面 `validate_template_variables()` 和 `render_template_text()` 都会复用它。
    """
    variables = re.findall(r"\$\{?([a-zA-Z_][a-zA-Z0-9_]*)\}?", template_text)
    return sorted(set(variables))


def validate_template_variables(template_text: str, variables: dict[str, Any]) -> TemplateCheck:
    """作用：
    校验模板里声明的变量与调用方传入变量是否匹配。

    参数：
    template_text: 原始模板文本。
    variables: 调用方准备传入模板的变量字典。

    返回：
    一个 `TemplateCheck`，包含声明变量、缺失变量和未使用变量三部分信息。

    流程位置：
    这个函数只做“校验”，不直接渲染字符串；
    它的输出会被 `render_template_text()` 一并返回给上层脚本。
    """
    declared = extract_template_variables(template_text)
    provided = sorted(variables.keys())
    # missing 表示模板需要但调用方没提供；unused 表示调用方传了但模板没有消费。
    missing = sorted(name for name in declared if name not in variables)
    unused = sorted(name for name in provided if name not in declared)
    return TemplateCheck(
        variables=declared,
        missing_variables=missing,
        unused_variables=unused,
    )


def render_template_text(template_text: str, variables: dict[str, Any]) -> tuple[str, TemplateCheck]:
    """作用：
    渲染模板文本，并同步返回变量校验结果，方便上层一起展示。

    参数：
    template_text: 原始模板文本。
    variables: 用于替换模板占位符的变量字典。

    返回：
    一个二元组：`(渲染后的文本, TemplateCheck 校验结果)`。

    流程位置：
    这是模板工程化链路的最终入口。上层脚本通常不会手动分开调
    “提变量 -> 校验 -> 渲染”，而是直接调用这里拿到最终结果。
    """
    check = validate_template_variables(template_text, variables)
    rendered = Template(template_text).safe_substitute(**variables)
    return rendered, check


def read_text(path: Path) -> str:
    """作用：
    用统一的 UTF-8 编码读取文本文件。

    参数：
    path: 待读取文件路径。

    返回：
    文件内容字符串。
    """
    return path.read_text(encoding="utf-8")


def write_json_export(filename: str, payload: dict[str, Any]) -> Path:
    """作用：
    把调试结果或模板预览导出到 `exports` 目录下的 JSON 文件。

    参数：
    filename: 导出文件名。
    payload: 要写入 JSON 的字典内容。

    返回：
    实际写入的文件路径。
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def timestamp_slug() -> str:
    """作用：
    生成适合拼到导出文件名里的时间戳字符串。

    参数：
    无。函数直接读取当前本地时间。

    返回：
    格式为 `YYYYMMDD_HHMMSS` 的字符串。
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def print_json(title: str, payload: dict[str, Any]) -> None:
    """作用：
    以带标题分隔线的形式打印 JSON 数据，便于课堂演示阅读。

    参数：
    title: 当前输出块标题。
    payload: 要打印的字典内容。
    """
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_lines(title: str, lines: Iterable[str]) -> None:
    """作用：
    以带标题的多行文本形式打印列表内容。

    参数：
    title: 当前输出块标题。
    lines: 要逐行打印的文本序列。
    """
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)
    for line in lines:
        print(line)


def normalize_label(text: str, allowed_labels: list[str]) -> str:
    """作用：
    把模型输出归一化成可比较的标签，减少空格和附带说明带来的干扰。

    参数：
    text: 模型原始输出文本。
    allowed_labels: 允许命中的标准标签列表。

    返回：
    如果命中标准标签则返回该标签；否则返回裁剪后的紧凑文本，用于调试异常输出。
    """
    compact = re.sub(r"\s+", "", text)
    for label in allowed_labels:
        if label in compact:
            return label
    return compact[:20] or "EMPTY"
