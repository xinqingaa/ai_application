"""
03_structured_risk — 02_llm/03 结构化风险列表：固定 Prompt + config，只换 structured_mode。

运行（改下方「实验配置」）：
    python structured_risk.py
"""

from __future__ import annotations

from typing import Literal

from llm_core import BuiltContext, ContextSource, LLMClient, build_review_context
from llm_core.errors import LLMError
from llm_core.observability import demo_log, render_experiment_messages_once
from llm_core.prompts import get_prompt, render_prompt
from llm_core.schemas.review import ReviewRiskList
from llm_core.structured import StructuredMode, build_response_format, merge_chat_request_params

from _shared import (
    DEMO_DIR,
    find_and_load_env,
    load_evidence_block,
    load_sample,
    log_experiment_header,
    log_structured_mode_result,
    require_api_key,
)

StructuredRiskMode = Literal["prompt_only", "json_mode", "json_schema"]

# --- 实验配置（逐项说明见 README 与 course/02_llm/03 正文）---
SAMPLE_ID = "S2"
PROMPT_ID = "review.risk_review"
PROMPT_VERSION = "4.0.0"
CONFIG_REF = "chat.dev_chat"
MODES: tuple[StructuredRiskMode, ...] = ("prompt_only", "json_mode", "json_schema")
VERBOSE = False
TEMPERATURE = 0
EVIDENCE_FILE = DEMO_DIR / "evidence_s2.json"
CONTEXT_TOKEN_BUDGET = 900
# -----------------------------------------------------------

_MODE_TO_STRUCTURED: dict[StructuredRiskMode, StructuredMode] = {
    "prompt_only": "none",
    "json_mode": "json_object",
    "json_schema": "json_schema",
}


def _structured_mode(mode: StructuredRiskMode) -> StructuredMode:
    return _MODE_TO_STRUCTURED[mode]


def _request_params_for_mode(
    client: LLMClient,
    structured_mode: StructuredMode,
    chat_kwargs: dict,
) -> dict:
    config = client.get_config(CONFIG_REF)
    call_params = dict(chat_kwargs)
    response_format = build_response_format(
        ReviewRiskList,
        structured_mode,
        schema_name="review_risk_list",
    )
    if response_format is not None:
        call_params["response_format"] = response_format
    return merge_chat_request_params(config, call_params)


def _log_context(context: BuiltContext) -> None:
    demo_log.section("context")
    demo_log.field("token_budget", context.token_budget, indent=1)
    demo_log.field("estimated_tokens", context.estimated_tokens, indent=1)
    demo_log.field(
        "included_sources",
        ", ".join(context.included_source_ids) or "—",
        indent=1,
    )
    demo_log.field(
        "dropped_sources",
        ", ".join(context.dropped_source_ids) or "—",
        indent=1,
    )
    demo_log.blank()


def main() -> None:
    find_and_load_env()
    require_api_key(demo_log)

    sample = load_sample(SAMPLE_ID, demo_log)
    client = LLMClient.from_default_config()
    config = client.get_config(CONFIG_REF)
    chat_kwargs = {"temperature": TEMPERATURE}

    evidence_sources: list[ContextSource] = []
    if EVIDENCE_FILE.is_file():
        evidence_sources.append(
            ContextSource(
                source_id=f"{SAMPLE_ID}.evidence.after_sale_api_v2",
                source_type="evidence",
                title="内部接口说明摘录",
                content=load_evidence_block(EVIDENCE_FILE),
                priority=80,
                metadata={"sample_id": SAMPLE_ID},
            )
        )
    context = build_review_context(
        requirement_text=sample["user_content"],
        sources=evidence_sources,
        token_budget=CONTEXT_TOKEN_BUDGET,
        model=config.model,
    )
    variables = context.to_prompt_variables()

    tpl = get_prompt(PROMPT_ID, version=PROMPT_VERSION)
    messages = render_prompt(tpl, variables)

    log_experiment_header(
        demo_log,
        sample=sample,
        prompt=f"{PROMPT_ID}@{PROMPT_VERSION}",
        config_ref=CONFIG_REF,
        model=config.model,
        modes=", ".join(MODES),
        temperature=TEMPERATURE,
        evidence_file=EVIDENCE_FILE,
    )
    _log_context(context)

    if VERBOSE:
        render_experiment_messages_once(demo_log, messages)

    for mode in MODES:
        structured_mode = _structured_mode(mode)
        request_params = _request_params_for_mode(client, structured_mode, chat_kwargs)
        try:
            result = client.chat_structured(
                messages,
                CONFIG_REF,
                structured_mode=structured_mode,
                debug=False,
                **chat_kwargs,
            )
        except LLMError as exc:
            log_structured_mode_result(
                demo_log,
                mode,
                structured_mode=structured_mode,
                error=exc,
                verbose=VERBOSE,
                request_params=request_params,
            )
            continue

        log_structured_mode_result(
            demo_log,
            mode,
            structured_mode=structured_mode,
            result=result,
            verbose=VERBOSE,
            request_params=request_params,
        )

if __name__ == "__main__":
    main()
