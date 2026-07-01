"""需求评审助手的 LLM 调用底座（02_llm）。

01 起提供 LLMClient、models.yaml 与统一可观测日志。
02 起提供命名 Prompt 模板（YAML 真源）与 render 能力。
03 起提供 Pydantic Schema、结构化解析与 chat_structured。
04 起提供流式事件、SSE 编码与最小 Conversation Buffer。
05 起提供上下文构造、证据编号与预算诊断。
"""

from llm_core.client import LLMClient
from llm_core.config import CapabilityTags, LLMResponse, ModelConfig, TokenUsage
from llm_core.context import (
    BuiltContext,
    ContextSource,
    DroppedContextSource,
    build_review_context,
    estimate_tokens,
    format_context_source,
    format_evidence_block,
)
from llm_core.conversation import ConversationBuffer, ConversationMessage
from llm_core.errors import LLMError, LLMErrorCode
from llm_core.observability import DemoLog, demo_log, format_call_log, print_call_log
from llm_core.prompts import PromptTemplate, get_prompt, list_prompt_versions, render_prompt
from llm_core.schemas import (
    Citation,
    ClarificationQuestion,
    ReviewRisk,
    ReviewRiskList,
    RiskCategory,
    RiskLevel,
    StructuredParseResult,
    parse_risk_list,
)
from llm_core.streaming import LLMStreamEvent, StreamEventBuilder, encode_sse
from llm_core.structured import StructuredLLMResponse, build_response_format

__version__ = "0.5.0"

__all__ = [
    "LLMClient",
    "LLMResponse",
    "StructuredLLMResponse",
    "StructuredParseResult",
    "LLMStreamEvent",
    "StreamEventBuilder",
    "LLMError",
    "LLMErrorCode",
    "ModelConfig",
    "TokenUsage",
    "CapabilityTags",
    "BuiltContext",
    "ContextSource",
    "DroppedContextSource",
    "build_review_context",
    "estimate_tokens",
    "format_context_source",
    "format_evidence_block",
    "PromptTemplate",
    "get_prompt",
    "list_prompt_versions",
    "render_prompt",
    "ReviewRisk",
    "ReviewRiskList",
    "Citation",
    "ClarificationQuestion",
    "RiskCategory",
    "RiskLevel",
    "parse_risk_list",
    "build_response_format",
    "encode_sse",
    "ConversationBuffer",
    "ConversationMessage",
    "DemoLog",
    "demo_log",
    "format_call_log",
    "print_call_log",
    "__version__",
]
