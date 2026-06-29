"""
02_prompt_compare — 02_llm/02 同一任务三版 Prompt 对比。

运行（无需命令行参数，改下方「实验配置」即可）：
    python prompt_compare.py
"""

from __future__ import annotations

from llm_core import LLMClient
from llm_core.errors import LLMError, LLMErrorCode
from llm_core.observability import demo_log
from llm_core.prompts import get_prompt, render_prompt

from _shared import (
    DEMO_DIR,
    find_and_load_env,
    load_evidence_block,
    load_sample,
    log_chat_result,
    log_experiment_header,
    require_api_key,
)

# --- 实验配置（改这里，不用敲长命令；逐项说明见本目录 README 与 02 正文）---
SAMPLE_ID = "S2"
PROMPT_ID = "review.risk_review"
PROMPT_VERSIONS = ("1.0.0", "2.0.0", "3.0.0")
VERBOSE = False
TEMPERATURE = 0
EVIDENCE_FILE = DEMO_DIR / "evidence_s2.json"
# -------------------------------------


def main() -> None:
    find_and_load_env()
    require_api_key(demo_log)

    sample = load_sample(SAMPLE_ID, demo_log)
    evidence_block = load_evidence_block(EVIDENCE_FILE)
    variables = {
        "requirement_text": sample["user_content"],
        "evidence_block": evidence_block,
    }

    client = LLMClient.from_default_config()
    chat_kwargs: dict = {"temperature": TEMPERATURE}

    log_experiment_header(
        demo_log,
        sample=sample,
        prompt=PROMPT_ID,
        versions=", ".join(PROMPT_VERSIONS),
        temperature=TEMPERATURE,
        evidence_file=EVIDENCE_FILE,
    )

    for version in PROMPT_VERSIONS:
        label = f"v{version.split('.')[0]}"
        try:
            tpl = get_prompt(PROMPT_ID, version=version)
            messages = render_prompt(tpl, variables)
            response = client.chat(
                messages,
                tpl.model_config_ref,
                debug=False,
                **chat_kwargs,
            )
            config = client.get_config(tpl.model_config_ref)
            merged = {**config.default_params, **chat_kwargs, "model": config.model}
            log_chat_result(
                demo_log,
                label,
                response,
                verbose=VERBOSE,
                messages=messages if VERBOSE else None,
                params=merged if VERBOSE else None,
            )
        except KeyError as exc:
            log_chat_result(demo_log, label, LLMError(LLMErrorCode.UNKNOWN, str(exc)))
        except ValueError as exc:
            log_chat_result(demo_log, label, LLMError(LLMErrorCode.UNKNOWN, str(exc)))
        except LLMError as exc:
            log_chat_result(demo_log, label, exc)

    demo_log.hint(
        "固定 SAMPLE_ID 与 TEMPERATURE，只换 PROMPT_VERSIONS；"
        "在笔记中记录：是否更少编造、结构是否更稳、v3 JSON 是否可解析。"
    )


if __name__ == "__main__":
    main()
