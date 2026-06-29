"""需求评审助手的 LLM 调用底座（02_llm）。

01 起提供 LLMClient、models.yaml 与统一可观测日志。
02 起提供命名 Prompt 模板（YAML 真源）与 render 能力。
03 起提供 Pydantic Schema、结构化解析与 chat_structured。
"""

from llm_core.client import LLMClient
from llm_core.config import CapabilityTags, LLMResponse, ModelConfig, TokenUsage
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
from llm_core.structured import StructuredLLMResponse, build_response_format

__version__ = "0.3.0"

__all__ = [
    "LLMClient",
    "LLMResponse",
    "StructuredLLMResponse",
    "StructuredParseResult",
    "LLMError",
    "LLMErrorCode",
    "ModelConfig",
    "TokenUsage",
    "CapabilityTags",
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
    "DemoLog",
    "demo_log",
    "format_call_log",
    "print_call_log",
    "__version__",
]
