"""需求评审助手共享的 LLM 模型交互底座。

模块覆盖 Provider、Prompt、Structured Output、Reliability、Context、
Calling Harness、Streaming、Conversation、成本与缓存。模块存在不代表
产品自动启用；demo、app 和产品 Pipeline 通过显式调用选择所需能力。
课程阅读顺序以 course/learning-path.md 为准。
"""

from llm_core.cache import CacheEvent, CacheKeyParts, CacheStats, InMemoryLLMCache, build_cache_key
from llm_core.client import LLMClient
from llm_core.config import CapabilityTags, EmbeddingResponse, LLMResponse, ModelConfig, TokenUsage
from llm_core.context import (
    BuiltContext,
    CitationCandidate,
    CompressedContextSource,
    ContextBuildPolicy,
    ContextBuildReport,
    ContextSection,
    ContextSource,
    ContextWarning,
    DroppedContextSource,
    build_review_context,
    estimate_tokens,
    format_context_source,
    format_evidence_block,
    get_context_policy,
    list_context_policy_names,
)
from llm_core.conversation import ConversationBuffer, ConversationMessage
from llm_core.costing import CostEstimate, ModelPrice, estimate_token_cost, estimate_usage_cost
from llm_core.errors import LLMError, LLMErrorCode
from llm_core.harness import (
    HarnessCase,
    HarnessRunConfig,
    HarnessRunRecord,
    HarnessSummary,
    LLMCallingHarness,
    format_records_table,
    format_summary,
)
from llm_core.prompts import PromptTemplate, get_prompt, list_prompt_versions, render_prompt
from llm_core.reliability import (
    DegradationPolicy,
    ReliableCallAttempt,
    ReliableCallReport,
    ReliableCallResult,
    ReliableLLMService,
    RetryPolicy,
)
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

__version__ = "0.7.0"

__all__ = [
    "LLMClient",
    "CacheEvent",
    "CacheKeyParts",
    "CacheStats",
    "InMemoryLLMCache",
    "build_cache_key",
    "LLMResponse",
    "EmbeddingResponse",
    "StructuredLLMResponse",
    "StructuredParseResult",
    "LLMStreamEvent",
    "StreamEventBuilder",
    "LLMError",
    "LLMErrorCode",
    "HarnessCase",
    "HarnessRunConfig",
    "HarnessRunRecord",
    "HarnessSummary",
    "LLMCallingHarness",
    "format_records_table",
    "format_summary",
    "RetryPolicy",
    "DegradationPolicy",
    "ReliableCallAttempt",
    "ReliableCallReport",
    "ReliableCallResult",
    "ReliableLLMService",
    "ModelConfig",
    "TokenUsage",
    "CapabilityTags",
    "CostEstimate",
    "ModelPrice",
    "estimate_token_cost",
    "estimate_usage_cost",
    "BuiltContext",
    "CitationCandidate",
    "CompressedContextSource",
    "ContextBuildPolicy",
    "ContextBuildReport",
    "ContextSection",
    "ContextSource",
    "ContextWarning",
    "DroppedContextSource",
    "build_review_context",
    "estimate_tokens",
    "format_context_source",
    "format_evidence_block",
    "get_context_policy",
    "list_context_policy_names",
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
    "__version__",
]
