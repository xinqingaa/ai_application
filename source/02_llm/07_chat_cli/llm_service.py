"""
llm_service.py
第七章综合项目服务层：多轮会话、普通聊天、流式输出、JSON 模式、成本统计、导出、缓存、重试与安全防护
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import uuid
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterator, TypeVar

from chat_schemas import (
    CLIState,
    CostStats,
    ErrorInfo,
    MessageRecord,
    ProjectSession,
    RetryLog,
    SafetyAssessment,
    TurnResult,
    UsageStats,
)


BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "exports"
DEFAULT_SYSTEM_PROMPT = "你是一个严谨、简洁、对开发者友好的 AI 助手。"
DEFAULT_DEBUG = True
T = TypeVar("T")


def load_env_if_possible() -> None:
    """尽量加载 `.env`，但不强制依赖 `python-dotenv`。"""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _parse_float(value: str | None) -> float | None:
    """把环境变量里的浮点数字符串转成 `float`，失败时返回 `None`。"""
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _now() -> str:
    """统一生成当前时间字符串，便于会话更新时间写回。"""
    return datetime.now().isoformat()


def _new_session_id() -> str:
    """生成一个短一些的会话 id，方便 CLI 和导出文件阅读。"""
    return uuid.uuid4().hex[:12]


class ProviderConfig:
    """把 provider 的环境变量配置收敛成一个可传递的对象。"""

    def __init__(
        self,
        provider: str,
        api_key: str | None,
        base_url: str | None,
        model: str,
        backup_provider: str | None = None,
        input_price_per_million: float | None = None,
        output_price_per_million: float | None = None,
    ) -> None:
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.backup_provider = backup_provider
        self.input_price_per_million = input_price_per_million
        self.output_price_per_million = output_price_per_million

    @property
    def is_ready(self) -> bool:
        """只要 API Key 存在，就认为可以走真实调用。"""
        return bool(self.api_key)


class CacheEntry:
    """缓存中的单条记录，保存值和过期时间。"""

    def __init__(self, value: TurnResult, expires_at: float) -> None:
        self.value = value
        self.expires_at = expires_at

    @property
    def is_expired(self) -> bool:
        """判断当前缓存项是否已经过期。"""
        return time.time() >= self.expires_at


class TTLCache:
    """一个很轻量的内存 TTL 缓存，用于复用相同请求的结果。"""

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, CacheEntry] = {}

    def _cleanup(self) -> None:
        """清掉已经过期的条目，避免内存里堆积陈旧数据。"""
        for key in list(self._store):
            if self._store[key].is_expired:
                self._store.pop(key, None)

    def get(self, key: str) -> TurnResult | None:
        """读取一个缓存结果，命中则直接返回。"""
        self._cleanup()
        entry = self._store.get(key)
        return entry.value if entry else None

    def set(self, key: str, value: TurnResult) -> None:
        """写入一个带过期时间的缓存结果。"""
        self._store[key] = CacheEntry(value=value, expires_at=time.time() + self.ttl_seconds)

    def size(self) -> int:
        """返回当前还有效的缓存条目数量。"""
        self._cleanup()
        return len(self._store)


class DailyQuotaManager:
    """按 subject 统计每日 token 配额，避免无限制调用。"""

    def __init__(self, daily_limit_tokens: int = 100_000) -> None:
        self.daily_limit_tokens = daily_limit_tokens
        self._usage: dict[tuple[str, str], int] = {}

    def snapshot(self, subject: str, on_date: date | None = None) -> dict[str, Any]:
        """返回某个 subject 在某一天的配额视图。"""
        today = (on_date or date.today()).isoformat()
        used = self._usage.get((subject, today), 0)
        return {
            "subject": subject,
            "date": today,
            "used_tokens": used,
            "limit_tokens": self.daily_limit_tokens,
            "remaining_tokens": max(0, self.daily_limit_tokens - used),
            "exceeded": used >= self.daily_limit_tokens,
        }

    def ensure_available(self, subject: str, estimated_tokens: int) -> bool:
        """在执行前先判断预计 token 是否会超额。"""
        snapshot = self.snapshot(subject)
        return snapshot["used_tokens"] + estimated_tokens <= self.daily_limit_tokens

    def consume(self, subject: str, tokens: int) -> dict[str, Any]:
        """把本轮实际消耗记入当天配额。"""
        today = date.today().isoformat()
        key = (subject, today)
        self._usage[key] = self._usage.get(key, 0) + max(0, tokens)
        return self.snapshot(subject)


class InMemorySessionStore:
    """保存项目运行时的会话对象，CLI 和 API 都依赖它。"""

    def __init__(self) -> None:
        self._store: dict[str, ProjectSession] = {}

    def get_or_create(
        self,
        session_id: str | None = None,
        provider: str = "bailian",
        model: str = "qwen-plus",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> ProjectSession:
        """获取已有 session，或者按默认配置创建一个新的 session。"""
        sid = session_id or _new_session_id()
        if sid not in self._store:
            self._store[sid] = ProjectSession(
                session_id=sid,
                provider=provider,
                model=model,
                system_prompt=system_prompt,
                debug_mode=DEFAULT_DEBUG,
            )
        return self._store[sid]

    def get(self, session_id: str) -> ProjectSession | None:
        """只查询，不创建。"""
        return self._store.get(session_id)

    def reset_messages(self, session_id: str) -> ProjectSession:
        """清空当前 session 的对话历史和累计统计。"""
        session = self.get_or_create(session_id)
        session.messages = []
        session.turn_count = 0
        session.accumulated_prompt_tokens = 0
        session.accumulated_completion_tokens = 0
        session.accumulated_total_tokens = 0
        session.accumulated_estimated_cost = 0.0
        session.updated_at = _now()
        return session


def load_provider_config(provider: str | None = None, model_override: str | None = None) -> ProviderConfig:
    """从环境变量加载 provider 配置，并转成统一 `ProviderConfig`。"""
    provider_name = (provider or os.getenv("DEFAULT_PROVIDER", "bailian")).strip().lower()
    mapping = {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "backup_provider": os.getenv("OPENAI_BACKUP_PROVIDER"),
            "input_price_per_million": _parse_float(os.getenv("OPENAI_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("OPENAI_OUTPUT_PRICE_PER_MILLION")),
        },
        "deepseek": {
            "api_key": os.getenv("DEEPSEEK_API_KEY"),
            "base_url": os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com",
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "backup_provider": os.getenv("DEEPSEEK_BACKUP_PROVIDER") or "bailian",
            "input_price_per_million": _parse_float(os.getenv("DEEPSEEK_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("DEEPSEEK_OUTPUT_PRICE_PER_MILLION")),
        },
        "bailian": {
            "api_key": os.getenv("BAILIAN_API_KEY"),
            "base_url": os.getenv("BAILIAN_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": os.getenv("BAILIAN_MODEL", "qwen-plus"),
            "backup_provider": os.getenv("BAILIAN_BACKUP_PROVIDER") or "deepseek",
            "input_price_per_million": _parse_float(os.getenv("BAILIAN_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("BAILIAN_OUTPUT_PRICE_PER_MILLION")),
        },
        "glm": {
            "api_key": os.getenv("GLM_API_KEY"),
            "base_url": os.getenv("GLM_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4/",
            "model": os.getenv("GLM_MODEL", "glm-4.5-air"),
            "backup_provider": os.getenv("GLM_BACKUP_PROVIDER") or "bailian",
            "input_price_per_million": _parse_float(os.getenv("GLM_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("GLM_OUTPUT_PRICE_PER_MILLION")),
        },
    }
    data = mapping.get(provider_name, mapping["bailian"])
    return ProviderConfig(
        provider=provider_name,
        api_key=data["api_key"],
        base_url=data["base_url"],
        model=model_override or data["model"],
        backup_provider=data["backup_provider"],
        input_price_per_million=data["input_price_per_million"],
        output_price_per_million=data["output_price_per_million"],
    )


def estimate_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """估算单段文本的 token 数；没有 `tiktoken` 时走一个近似算法。"""
    try:
        import tiktoken
    except ImportError:
        # 没装 `tiktoken` 时仍然要让教学代码可跑，所以退化到粗略估算。
        ascii_chars = sum(1 for char in text if ord(char) < 128)
        non_ascii_chars = len(text) - ascii_chars
        english_est = max(1, ascii_chars // 4) if ascii_chars else 0
        chinese_est = max(1, int(non_ascii_chars / 1.5)) if non_ascii_chars else 0
        return english_est + chinese_est

    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def estimate_messages_tokens(messages: list[dict[str, str]]) -> int:
    """按 OpenAI 风格消息结构粗估整段 messages 的 token 消耗。"""
    total = 0
    for item in messages:
        total += estimate_tokens(item["role"])
        total += estimate_tokens(item["content"])
        total += 4
    return total + 2


def stable_cache_key(
    provider: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    """把一次请求的关键入参稳定序列化后生成缓存键。"""
    payload = json.dumps(
        {
            "provider": provider,
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "json_mode": json_mode,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    import hashlib

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def classify_exception(exc: Exception) -> ErrorInfo:
    """把原始异常归类成项目内部更稳定的错误对象。"""
    name = exc.__class__.__name__.lower()
    text = str(exc).lower()
    combined = f"{name} {text}"
    if "authentication" in combined or "api key" in combined or "invalid_api_key" in combined or "unauthorized" in combined:
        return ErrorInfo("auth_error", False, str(exc), "API Key 无效或没有权限，请检查 Key、provider 和模型配置。")
    if "rate limit" in combined or "429" in combined or "too many requests" in combined:
        return ErrorInfo("rate_limit", True, str(exc), "请求过于频繁，建议指数退避重试或切换备用模型。")
    if "timeout" in combined:
        return ErrorInfo("timeout", True, str(exc), "请求超时，建议缩短上下文、降低 max_tokens 或稍后重试。")
    if "network" in combined or "connection" in combined or "temporarily unavailable" in combined:
        return ErrorInfo("network_error", True, str(exc), "网络或上游服务临时异常，适合有限次重试。")
    if "badrequest" in combined or "invalid request" in combined or "400" in combined:
        return ErrorInfo("request_error", False, str(exc), "请求参数错误，应修正 messages、model 或输出格式。")
    if "content policy" in combined or "moderation" in combined or "safety" in combined:
        return ErrorInfo("safety_block", False, str(exc), "内容安全策略拦截，应调整输入或转人工处理。")
    return ErrorInfo("unknown_error", False, str(exc), "未知异常，应记录日志并人工排查。")


def retry_call(
    func: Callable[[], T],
    max_retries: int = 2,
    base_delay: float = 0.4,
    max_delay: float = 3.0,
) -> tuple[T | None, list[RetryLog], ErrorInfo | None]:
    """执行一次带指数退避的重试，并把过程记录成 `RetryLog`。"""
    retries: list[RetryLog] = []
    for attempt in range(1, max_retries + 2):
        try:
            return func(), retries, None
        except Exception as exc:
            error = classify_exception(exc)
            if not error.retryable or attempt > max_retries:
                return None, retries, error
            wait_seconds = min(base_delay * (2 ** (attempt - 1)), max_delay)
            retries.append(RetryLog(attempt, wait_seconds, error.category, error.message))
            time.sleep(wait_seconds)
    return None, retries, ErrorInfo("unknown_error", False, "未知异常", "请检查日志。")


def redact_sensitive(text: str) -> str:
    """在导出或展示前，对常见敏感信息做脱敏。"""
    redacted = text
    patterns = [
        (r"(?i)(api[_-]?key\s*[:=]\s*)([A-Za-z0-9_\-]+)", r"\1***REDACTED***"),
        (r"sk-[A-Za-z0-9_\-]{10,}", "sk-***REDACTED***"),
        (r"\b1[3-9]\d{9}\b", "***PHONE***"),
        (r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "***EMAIL***"),
    ]
    for pattern, repl in patterns:
        redacted = re.sub(pattern, repl, redacted)
    return redacted


def detect_prompt_injection(text: str) -> SafetyAssessment:
    """用简单规则做 prompt injection 风险初筛。"""
    normalized = text.strip().lower()
    patterns = [
        ("试图覆盖系统提示", r"忽略.*指令|ignore previous instructions|forget previous instructions"),
        ("试图获取敏感信息", r"隐藏提示词|system prompt|api[_ -]?key|show your hidden prompt"),
        ("试图越权执行", r"开发者模式|系统管理员|pretend to be system|切换为系统角色"),
        ("疑似注入标签结构", r"<system>|</system>|```system|begin_system_prompt"),
    ]
    reasons: list[str] = []
    score = 0
    for reason, pattern in patterns:
        if re.search(pattern, normalized):
            reasons.append(reason)
            score += 2
    if any(token in normalized for token in ["password", "secret", "token", "api_key"]):
        reasons.append("包含敏感词")
        score += 1
    return SafetyAssessment(
        risk_score=score,
        blocked=score >= 3,
        reasons=reasons,
        normalized_text=normalized,
    )


def ensure_system_message(messages: list[dict[str, str]], system_prompt: str) -> list[dict[str, str]]:
    """无论历史如何，始终把 system message 放在最前面。"""
    others = [item for item in messages if item["role"] != "system"]
    return [{"role": "system", "content": system_prompt}] + others


def trim_messages(messages: list[dict[str, str]], keep_last_messages: int) -> list[dict[str, str]]:
    """保留 system 消息，再截断最近 N 条非 system 历史。"""
    systems = [item for item in messages if item["role"] == "system"]
    others = [item for item in messages if item["role"] != "system"]
    return systems + others[-keep_last_messages:]


def build_user_message_content(user_text: str, json_mode: bool) -> str:
    """在 JSON 模式下，把“只返回 JSON”的要求拼进用户消息。"""
    if not json_mode:
        return user_text
    return (
        f"{user_text}\n\n"
        "输出要求：\n"
        "1. 只返回一个 JSON 对象。\n"
        "2. 不要输出 Markdown 代码块。\n"
        "3. 如果缺少信息，用 null 或空数组，不要编造。"
    )


def split_mock_chunks(text: str) -> list[str]:
    """把完整文本拆成小块，用来模拟流式输出的视觉效果。"""
    sizes = [4, 5, 3, 6]
    parts: list[str] = []
    cursor = 0
    index = 0
    while cursor < len(text):
        size = sizes[index % len(sizes)]
        parts.append(text[cursor : cursor + size])
        cursor += size
        index += 1
    return parts


def encode_sse_event(event: str, data: Any, event_id: str | None = None) -> str:
    """把事件名和数据编码成 SSE 协议需要的文本格式。"""
    lines: list[str] = []
    if event_id:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    for line in payload.splitlines():
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"


def _debug_print_start(
    config: ProviderConfig,
    request_preview: dict[str, Any],
    stream: bool,
) -> None:
    mode_name = "stream_chat" if stream else "chat"
    print(f"\n{'=' * 72}")
    print(f"[DEBUG] {mode_name} -> 请求开始")
    print("=" * 72)
    print(
        f"[DEBUG] {mode_name}.start "
        f"provider={config.provider} "
        f"model={config.model} "
        f"ready={config.is_ready}"
    )
    print("[DEBUG] request_preview:")
    print(json.dumps(request_preview, ensure_ascii=False, indent=2))


def _debug_print_cache_hit(config: ProviderConfig, cache_key: str, stream: bool) -> None:
    mode_name = "stream_chat" if stream else "chat"
    print(
        f"[DEBUG] {mode_name}.cache_hit "
        f"provider={config.provider} "
        f"model={config.model} "
        f"cache_key={cache_key[:12]}..."
    )


def _debug_print_retry(retries: list[RetryLog], stream: bool) -> None:
    if not retries:
        return
    mode_name = "stream_chat" if stream else "chat"
    print(f"[DEBUG] {mode_name}.retry:")
    for item in retries:
        print(
            f"- attempt={item.attempt} "
            f"wait_seconds={item.wait_seconds} "
            f"category={item.category} "
            f"message={item.message}"
        )


def _debug_print_error(error: ErrorInfo, request_preview: dict[str, Any], stream: bool) -> None:
    mode_name = "stream_chat" if stream else "chat"
    print(f"\n{'=' * 72}")
    print(f"[DEBUG] {mode_name} -> 异常返回")
    print("=" * 72)
    print(
        f"[DEBUG] {mode_name}.error "
        f"category={error.category} "
        f"retryable={error.retryable}"
    )
    print(f"[DEBUG] error_message: {error.message}")
    print(f"[DEBUG] user_hint: {error.user_hint}")
    print("[DEBUG] request_preview:")
    print(json.dumps(request_preview, ensure_ascii=False, indent=2))


def _debug_print_result(result: TurnResult, stream: bool) -> None:
    mode_name = "stream_chat" if stream else "chat"
    print(f"\n{'=' * 72}")
    print(f"[DEBUG] {mode_name} -> 返回结果")
    print("=" * 72)
    print(
        f"[DEBUG] {mode_name}.result "
        f"provider={result.provider} "
        f"model={result.model} "
        f"mocked={result.mocked} "
        f"from_cache={result.from_cache} "
        f"elapsed_ms={result.elapsed_ms:.2f}"
    )
    if result.usage:
        print(
            "[DEBUG] usage "
            f"prompt_tokens={result.usage.prompt_tokens} "
            f"completion_tokens={result.usage.completion_tokens} "
            f"total_tokens={result.usage.total_tokens}"
        )
    if result.cost and result.cost.estimated_cost is not None:
        print(f"[DEBUG] estimated_cost={result.cost.estimated_cost:.6f}")
    if result.retries:
        _debug_print_retry(result.retries, stream=stream)
    print(
        "[DEBUG] safety "
        f"blocked={result.safety.blocked} "
        f"risk_score={result.safety.risk_score} "
        f"reasons={result.safety.reasons}"
    )
    print("[DEBUG] request_preview:")
    print(json.dumps(result.request_preview or {}, ensure_ascii=False, indent=2))
    print("[DEBUG] raw_content:")
    print(result.reply or "")


def write_json_export(filename: str, data: Any) -> Path:
    """把导出数据写到 `exports/` 目录。"""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / filename
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def timestamp_slug() -> str:
    """生成适合文件名的时间戳后缀。"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class ProjectLLMService:
    """统一服务层，负责把聊天项目里的横切能力收拢到一处。"""

    def __init__(
        self,
        provider: str | None = None,
        cache_ttl_seconds: float = 300.0,
        daily_limit_tokens: int = 100_000,
    ) -> None:
        """初始化 provider、session store、cache 和 quota 管理器。"""
        load_env_if_possible()
        self.provider_name = provider or os.getenv("DEFAULT_PROVIDER", "bailian")
        self.store = InMemorySessionStore()
        self.cache = TTLCache(ttl_seconds=cache_ttl_seconds)
        self.quota = DailyQuotaManager(daily_limit_tokens=daily_limit_tokens)

    def resolve_config(self, provider: str | None = None, model_override: str | None = None) -> ProviderConfig:
        """解析当前应使用的 provider 配置。"""
        return load_provider_config(provider or self.provider_name, model_override=model_override)

    def get_or_create_session(self, session_id: str | None = None) -> ProjectSession:
        """拿到一个可继续使用的会话对象。"""
        config = self.resolve_config()
        session = self.store.get_or_create(
            session_id=session_id,
            provider=config.provider,
            model=config.model,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
        )
        return session

    def get_cli_state(self, session_id: str) -> CLIState:
        """提取 CLI 真正关心的会话配置视图。"""
        session = self.get_or_create_session(session_id)
        return CLIState(
            session_id=session.session_id,
            provider=session.provider,
            model=session.model,
            system_prompt=session.system_prompt,
            json_mode=session.json_mode,
            stream_mode=session.stream_mode,
            debug_mode=session.debug_mode,
            temperature=session.temperature,
            max_tokens=session.max_tokens,
            keep_last_messages=session.keep_last_messages,
        )

    def update_session_settings(self, session_id: str, **kwargs: Any) -> ProjectSession:
        """统一更新 session 配置，供 CLI 命令和 API 请求复用。"""
        session = self.get_or_create_session(session_id)
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        session.updated_at = _now()
        return session

    def clear_session(self, session_id: str) -> ProjectSession:
        """清空会话历史，但保留当前 session 的配置。"""
        return self.store.reset_messages(session_id)

    def _message_dicts(self, session: ProjectSession) -> list[dict[str, str]]:
        """把 dataclass 形式的消息转换成模型 SDK 更熟悉的 dict 结构。"""
        return [{"role": item.role, "content": item.content} for item in session.messages]

    def _build_messages(self, session: ProjectSession, user_text: str) -> list[dict[str, str]]:
        """组装真正要发给模型的 messages。"""
        history = self._message_dicts(session)
        base = ensure_system_message(history, session.system_prompt)
        base = trim_messages(base, session.keep_last_messages)
        return base + [{"role": "user", "content": build_user_message_content(user_text, session.json_mode)}]

    def _preview_request(self, config: ProviderConfig, messages: list[dict[str, str]], session: ProjectSession, stream: bool) -> dict[str, Any]:
        """生成请求预览，便于调试和导出时回看本轮入参。"""
        payload: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "temperature": session.temperature,
            "max_tokens": session.max_tokens,
        }
        if session.json_mode:
            payload["json_mode"] = "prompt_json"
            if config.provider == "openai":
                payload["response_format"] = {"type": "json_object"}
        if stream:
            payload["stream"] = True
        return payload

    def _compute_cost(self, usage: UsageStats | None, config: ProviderConfig) -> CostStats | None:
        """根据 usage 和配置价格估算本轮成本。"""
        if not usage:
            return None
        estimated_cost = None
        if config.input_price_per_million is not None and config.output_price_per_million is not None:
            estimated_cost = (
                usage.prompt_tokens / 1_000_000 * config.input_price_per_million
                + usage.completion_tokens / 1_000_000 * config.output_price_per_million
            )
        return CostStats(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            input_price_per_million=config.input_price_per_million,
            output_price_per_million=config.output_price_per_million,
            estimated_cost=estimated_cost,
        )

    def _mock_response_text(self, user_text: str, session: ProjectSession, config: ProviderConfig) -> str:
        """在没有真实 API Key 时，生成一个仍然可练习流程的 mock 响应。"""
        if session.json_mode:
            return json.dumps(
                {
                    "summary": "这是第七章综合项目的 mock JSON 返回。",
                    "provider": config.provider,
                    "model": config.model,
                    "question_preview": user_text[:60],
                    "tips": ["当前未配置真实 API Key", "你仍可练习命令流、导出、统计和状态管理"],
                },
                ensure_ascii=False,
                indent=2,
            )
        return (
            f"[MOCK:{config.provider}] 这是第七章综合项目的模拟回复。\n"
            f"本轮问题预览：{user_text[:80]}\n"
            f"当前模式：json_mode={session.json_mode}, stream_mode={session.stream_mode}\n"
            "你可以继续练习 provider 切换、导出会话、查看统计和流式输出。"
        )

    def _real_chat_once(self, config: ProviderConfig, messages: list[dict[str, str]], session: ProjectSession) -> tuple[str, UsageStats | None, float]:
        """执行一次真实的非流式模型调用。"""
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("未安装 openai SDK，请先执行：pip install openai") from exc

        client = OpenAI(api_key=config.api_key, base_url=config.base_url, timeout=30.0)
        kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "temperature": session.temperature,
            "max_tokens": session.max_tokens,
        }
        if session.json_mode and config.provider == "openai":
            kwargs["response_format"] = {"type": "json_object"}

        started = time.perf_counter()
        response = client.chat.completions.create(**kwargs)
        elapsed_ms = (time.perf_counter() - started) * 1000
        usage = None
        if response.usage:
            usage = UsageStats(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        return response.choices[0].message.content or "", usage, elapsed_ms

    def _chat_once(self, config: ProviderConfig, messages: list[dict[str, str]], session: ProjectSession, raw_user_text: str) -> tuple[str, UsageStats | None, float, bool]:
        """统一封装“本轮到底走 mock 还是真实模型”的分支。"""
        if not config.is_ready:
            content = self._mock_response_text(raw_user_text, session, config)
            prompt_tokens = estimate_messages_tokens(messages)
            completion_tokens = estimate_tokens(content)
            usage = UsageStats(prompt_tokens, completion_tokens, prompt_tokens + completion_tokens)
            return content, usage, 120.0, True
        content, usage, elapsed_ms = self._real_chat_once(config, messages, session)
        return content, usage, elapsed_ms, False

    def _append_turn(self, session: ProjectSession, user_text: str, assistant_text: str, cost: CostStats | None, usage: UsageStats | None, request_preview: dict[str, Any], billable: bool) -> None:
        """把本轮对话结果和统计写回 session，作为后续轮次的上下文基础。"""
        session.messages.append(MessageRecord(role="user", content=user_text))
        session.messages.append(MessageRecord(role="assistant", content=assistant_text))
        # session 里保留最近一段历史即可，避免上下文无限增长。
        session.messages = session.messages[-(session.keep_last_messages + 2) :]
        session.turn_count += 1
        session.updated_at = _now()
        session.latest_request_preview = request_preview
        if billable and usage:
            session.accumulated_prompt_tokens += usage.prompt_tokens
            session.accumulated_completion_tokens += usage.completion_tokens
            session.accumulated_total_tokens += usage.total_tokens
        if billable and cost and cost.estimated_cost is not None:
            session.accumulated_estimated_cost += cost.estimated_cost

    def _session_estimated_tokens(self, session: ProjectSession) -> int:
        """粗估当前会话历史大约占用了多少 token。"""
        return estimate_messages_tokens(self._message_dicts(session)) if session.messages else 0

    def _build_turn_result(
        self,
        session: ProjectSession,
        config: ProviderConfig,
        reply: str | None,
        usage: UsageStats | None,
        cost: CostStats | None,
        retries: list[RetryLog],
        safety: SafetyAssessment,
        request_preview: dict[str, Any],
        elapsed_ms: float,
        mocked: bool,
        from_cache: bool,
        error: ErrorInfo | None = None,
    ) -> TurnResult:
        """统一构造服务层对外返回的结果对象。"""
        return TurnResult(
            ok=error is None,
            session_id=session.session_id,
            provider=config.provider,
            model=config.model,
            reply=reply,
            mocked=mocked,
            from_cache=from_cache,
            json_mode=session.json_mode,
            stream_mode=session.stream_mode,
            elapsed_ms=elapsed_ms,
            usage=usage,
            cost=cost,
            retries=retries,
            safety=safety,
            request_preview=request_preview,
            session_estimated_tokens=self._session_estimated_tokens(session),
            error=error,
        )

    def chat(self, session_id: str | None, user_text: str, quota_subject: str = "cli-user") -> TurnResult:
        """执行一轮普通聊天请求。"""
        session = self.get_or_create_session(session_id)
        config = self.resolve_config(session.provider, model_override=session.model)
        safety = detect_prompt_injection(user_text)
        messages = self._build_messages(session, user_text)
        request_preview = self._preview_request(config, messages, session, stream=False)
        if session.debug_mode:
            _debug_print_start(config, request_preview, stream=False)
        estimated_tokens = estimate_messages_tokens(messages) + session.max_tokens
        # 先做额度检查，避免已经超额时还继续占用上游资源。
        if not self.quota.ensure_available(quota_subject, estimated_tokens):
            result = self._build_turn_result(
                session,
                config,
                reply=None,
                usage=None,
                cost=None,
                retries=[],
                safety=safety,
                request_preview=request_preview,
                elapsed_ms=0.0,
                mocked=not config.is_ready,
                from_cache=False,
                error=ErrorInfo("quota_exceeded", False, "用户今日 Token 配额不足", "请降低上下文长度、切换更便宜模型或明日再试。"),
            )
            if session.debug_mode and result.error:
                _debug_print_error(result.error, request_preview, stream=False)
            return result

        cache_key = stable_cache_key(config.provider, config.model, messages, session.temperature, session.max_tokens, session.json_mode)
        cached = self.cache.get(cache_key)
        if cached:
            if session.debug_mode:
                _debug_print_cache_hit(config, cache_key, stream=False)
            # 命中缓存也要把 user/assistant 重新落回 session，这样当前会话历史仍然完整。
            self._append_turn(session, user_text, cached.reply or "", cached.cost, cached.usage, cached.request_preview, billable=False)
            result = self._build_turn_result(
                session,
                config,
                reply=cached.reply,
                usage=cached.usage,
                cost=cached.cost,
                retries=[],
                safety=safety,
                request_preview=cached.request_preview,
                elapsed_ms=0.0,
                mocked=cached.mocked,
                from_cache=True,
                error=None,
            )
            if session.debug_mode:
                _debug_print_result(result, stream=False)
            return result

        def _call() -> tuple[str, UsageStats | None, float, bool]:
            return self._chat_once(config, messages, session, user_text)

        outcome, retries, error = retry_call(_call, max_retries=2)
        if error or not outcome:
            result = self._build_turn_result(
                session,
                config,
                reply=None,
                usage=None,
                cost=None,
                retries=retries,
                safety=safety,
                request_preview=request_preview,
                elapsed_ms=0.0,
                mocked=not config.is_ready,
                from_cache=False,
                error=error,
            )
            if session.debug_mode:
                _debug_print_retry(retries, stream=False)
                if result.error:
                    _debug_print_error(result.error, request_preview, stream=False)
            return result

        reply, usage, elapsed_ms, mocked = outcome
        cost = self._compute_cost(usage, config)
        # 只有真实执行成功后，才把这轮结果作为新的上下文写回。
        self._append_turn(session, user_text, reply, cost, usage, request_preview, billable=True)
        if usage:
            self.quota.consume(quota_subject, usage.total_tokens)
        result = self._build_turn_result(
            session,
            config,
            reply=reply,
            usage=usage,
            cost=cost,
            retries=retries,
            safety=safety,
            request_preview=request_preview,
            elapsed_ms=elapsed_ms,
            mocked=mocked,
            from_cache=False,
        )
        self.cache.set(cache_key, result)
        if session.debug_mode:
            _debug_print_result(result, stream=False)
        return result

    def _real_stream(self, config: ProviderConfig, messages: list[dict[str, str]], session: ProjectSession) -> Iterator[str]:
        """执行真实模型的流式调用，并把增量文本逐段吐出。"""
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("未安装 openai SDK，请先执行：pip install openai") from exc

        client = OpenAI(api_key=config.api_key, base_url=config.base_url, timeout=30.0)
        kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "temperature": session.temperature,
            "max_tokens": session.max_tokens,
            "stream": True,
        }
        if session.json_mode and config.provider == "openai":
            kwargs["response_format"] = {"type": "json_object"}
        stream = client.chat.completions.create(**kwargs)
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta

    def stream_chat(self, session_id: str | None, user_text: str, quota_subject: str = "cli-user") -> Iterator[dict[str, Any]]:
        """执行一轮流式聊天，按事件流的形式把过程暴露给上层。"""
        session = self.get_or_create_session(session_id)
        config = self.resolve_config(session.provider, model_override=session.model)
        safety = detect_prompt_injection(user_text)
        messages = self._build_messages(session, user_text)
        request_preview = self._preview_request(config, messages, session, stream=True)
        if session.debug_mode:
            _debug_print_start(config, request_preview, stream=True)
        estimated_tokens = estimate_messages_tokens(messages) + session.max_tokens

        if not self.quota.ensure_available(quota_subject, estimated_tokens):
            error = ErrorInfo("quota_exceeded", False, "用户今日 Token 配额不足", "请缩短上下文或稍后再试。")
            if session.debug_mode:
                _debug_print_error(error, request_preview, stream=True)
            yield {
                "type": "error",
                "error": asdict(error),
                "request_preview": request_preview,
            }
            return

        cache_key = stable_cache_key(config.provider, config.model, messages, session.temperature, session.max_tokens, session.json_mode)
        cached = self.cache.get(cache_key)
        if cached and cached.reply:
            if session.debug_mode:
                _debug_print_cache_hit(config, cache_key, stream=True)
            # 流式模式命中缓存时，仍然用 chunk 形式重放，保持调用方体验一致。
            yield {
                "type": "start",
                "session_id": session.session_id,
                "provider": config.provider,
                "model": config.model,
                "from_cache": True,
            }
            for chunk in split_mock_chunks(cached.reply):
                yield {"type": "token", "delta": chunk}
            self._append_turn(session, user_text, cached.reply, cached.cost, cached.usage, cached.request_preview, billable=False)
            result = self._build_turn_result(
                session,
                config,
                reply=cached.reply,
                usage=cached.usage,
                cost=cached.cost,
                retries=[],
                safety=safety,
                request_preview=cached.request_preview,
                elapsed_ms=0.0,
                mocked=cached.mocked,
                from_cache=True,
            )
            yield {
                "type": "done",
                "result": asdict(result),
            }
            if session.debug_mode:
                _debug_print_result(result, stream=True)
            return

        started = time.perf_counter()
        # start 事件告诉调用方：本轮流式输出已经开始，可以准备消费 token。
        yield {
            "type": "start",
            "session_id": session.session_id,
            "provider": config.provider,
            "model": config.model,
            "from_cache": False,
        }

        collected: list[str] = []
        mocked = not config.is_ready
        try:
            if mocked:
                reply_text = self._mock_response_text(user_text, session, config)
                for chunk in split_mock_chunks(reply_text):
                    time.sleep(0.05)
                    collected.append(chunk)
                    yield {"type": "token", "delta": chunk}
            else:
                for delta in self._real_stream(config, messages, session):
                    collected.append(delta)
                    yield {"type": "token", "delta": delta}
        except Exception as exc:
            error = classify_exception(exc)
            if session.debug_mode:
                _debug_print_error(error, request_preview, stream=True)
            yield {
                "type": "error",
                "error": asdict(error),
                "request_preview": request_preview,
            }
            return

        reply = "".join(collected)
        # 流式输出结束后，仍然要补齐 usage / cost / session 等项目级信息。
        elapsed_ms = (time.perf_counter() - started) * 1000
        usage = UsageStats(
            prompt_tokens=estimate_messages_tokens(messages),
            completion_tokens=estimate_tokens(reply),
            total_tokens=estimate_messages_tokens(messages) + estimate_tokens(reply),
        )
        cost = self._compute_cost(usage, config)
        self._append_turn(session, user_text, reply, cost, usage, request_preview, billable=True)
        self.quota.consume(quota_subject, usage.total_tokens)
        result = self._build_turn_result(
            session,
            config,
            reply=reply,
            usage=usage,
            cost=cost,
            retries=[],
            safety=safety,
            request_preview=request_preview,
            elapsed_ms=elapsed_ms,
            mocked=mocked,
            from_cache=False,
        )
        self.cache.set(cache_key, result)
        if session.debug_mode:
            _debug_print_result(result, stream=True)
        yield {"type": "done", "result": asdict(result)}

    def export_session(self, session_id: str) -> Path:
        """导出当前 session 和 CLI 状态，便于回放与排查。"""
        session = self.get_or_create_session(session_id)
        payload = {
            "session": asdict(session),
            "state": asdict(self.get_cli_state(session_id)),
        }
        return write_json_export(f"chat_session_{session_id}_{timestamp_slug()}.json", payload)

    def session_snapshot(self, session_id: str) -> dict[str, Any]:
        """返回 API 更适合直接消费的会话快照。"""
        session = self.get_or_create_session(session_id)
        return {
            "session": asdict(session),
            "estimated_tokens_current_history": self._session_estimated_tokens(session),
            "cache_size": self.cache.size(),
            "quota_snapshot": self.quota.snapshot(session_id),
        }

    def format_stats_text(self, session_id: str) -> str:
        """把当前会话统计格式化成 CLI 友好的纯文本。"""
        session = self.get_or_create_session(session_id)
        lines = [
            f"session_id={session.session_id}",
            f"provider={session.provider}",
            f"model={session.model}",
            f"json_mode={session.json_mode}",
            f"stream_mode={session.stream_mode}",
            f"debug_mode={session.debug_mode}",
            f"turn_count={session.turn_count}",
            f"accumulated_prompt_tokens={session.accumulated_prompt_tokens}",
            f"accumulated_completion_tokens={session.accumulated_completion_tokens}",
            f"accumulated_total_tokens={session.accumulated_total_tokens}",
            f"accumulated_estimated_cost={session.accumulated_estimated_cost:.6f}",
            f"estimated_tokens_current_history={self._session_estimated_tokens(session)}",
            f"cache_size={self.cache.size()}",
        ]
        return "\n".join(lines)


def _print_turn_result(result: TurnResult) -> None:
    """示例运行时，把结果按 JSON 形式打印出来。"""
    print(f"\n{'=' * 72}")
    print(f"运行示例，完整的返回结果")
    print("=" * 72)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


def main() -> None:
    """允许直接运行服务文件，快速验证服务层是否能独立工作。"""
    load_env_if_possible()
    service = ProjectLLMService()
    session = service.get_or_create_session()
    result = service.chat(session.session_id, "请给出第七章项目的 3 条学习建议。", quota_subject="demo")
    _print_turn_result(result)


if __name__ == "__main__":
    main()
