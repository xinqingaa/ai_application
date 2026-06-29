"""
02_prompt_compare — 02_llm/02 同一任务三版 Prompt 对比。

运行（无需命令行参数，改下方「实验配置」即可）：
    python prompt_compare.py
"""

from __future__ import annotations

from llm_core import LLMClient
from llm_core.config import LLMResponse
from llm_core.errors import LLMError, LLMErrorCode
from llm_core.observability import format_call_log
from llm_core.prompts import PromptTemplate, get_prompt, render_prompt

from _shared import (
    DEMO_DIR,
    find_and_load_env,
    load_evidence_block,
    load_sample,
    print_results_table,
    require_api_key,
)

# --- 实验配置（改这里，不用敲长命令；逐项说明见本目录 README 与 02 正文）---
# 样例 id：S1–S5，定义在 ../02_first_chat/samples.json；user_content → requirement_text
SAMPLE_ID = "S2"
# 逻辑名 → 必须等于某个 yaml 内的 prompt_id 字段（非文件名）；见 prompts/review/*.yaml
PROMPT_ID = "review.risk_review"
# 版本列表 → 每一项必须等于某个 yaml 内的 version 字段；与 risk_review_v1.yaml 等文件名无强制对应
PROMPT_VERSIONS = ("1.0.0", "2.0.0", "3.0.0")
# True：对比表之后打印完整 system/user、请求参数与 assistant 全文
VERBOSE = False
# 传给每次 client.chat；对比 Prompt 版本时建议固定 0
TEMPERATURE = 0
# JSON 文件，读取 evidence_block 字段；文件不存在时用「无检索证据」占位（见 _shared.load_evidence_block）
EVIDENCE_FILE = DEMO_DIR / "evidence_s2.json"
# 模型 config_ref 在各版 yaml 的 model_config_ref，不在此修改（默认 chat.dev_chat）
# -------------------------------------


def main() -> None:
    find_and_load_env()
    require_api_key()

    sample = load_sample(SAMPLE_ID)
    evidence_block = load_evidence_block(EVIDENCE_FILE)
    variables = {
        "requirement_text": sample["user_content"],
        "evidence_block": evidence_block,
    }

    client = LLMClient.from_default_config()
    chat_kwargs: dict = {"temperature": TEMPERATURE}

    print(f"sample: {sample['id']} ({sample['type']}) — {sample['summary']}")
    print(f"prompt: {PROMPT_ID}")
    print(f"versions: {', '.join(PROMPT_VERSIONS)}")
    print(f"temperature: {TEMPERATURE}")
    print(f"evidence: {EVIDENCE_FILE.name}")

    results: list[tuple[str, LLMResponse | LLMError]] = []
    rendered_by_version: dict[str, list[dict[str, str]]] = {}
    templates_by_version: dict[str, PromptTemplate] = {}

    for version in PROMPT_VERSIONS:
        label = f"v{version.split('.')[0]}"
        try:
            tpl = get_prompt(PROMPT_ID, version=version)
            messages = render_prompt(tpl, variables)
            rendered_by_version[version] = messages
            templates_by_version[version] = tpl
            response = client.chat(
                messages,
                tpl.model_config_ref,
                debug=False,
                **chat_kwargs,
            )
            results.append((label, response))
        except KeyError as exc:
            results.append((label, LLMError(LLMErrorCode.UNKNOWN, str(exc))))
        except ValueError as exc:
            results.append((label, LLMError(LLMErrorCode.UNKNOWN, str(exc))))
        except LLMError as exc:
            results.append((label, exc))

    print_results_table(results, header_label="version")

    if VERBOSE:
        print("\n【详细日志】")
        for label, item in results:
            if isinstance(item, LLMError):
                print(f"\n>>> verbose: {label} (ERROR)\n{item}")
                continue
            version = next(
                v for v in PROMPT_VERSIONS if f"v{v.split('.')[0]}" == label
            )
            tpl = templates_by_version[version]
            messages = rendered_by_version[version]
            config = client.get_config(tpl.model_config_ref)
            merged = {**config.default_params, **chat_kwargs, "model": config.model}
            print(f"\n>>> verbose: {label} ({tpl.ref})")
            print(format_call_log(messages, merged, item))

    print(
        "对比建议：固定 SAMPLE_ID 与 TEMPERATURE，只换 PROMPT_VERSIONS；"
        "在笔记中记录：是否更少编造、结构是否更稳、v3 JSON 是否可解析。"
    )


if __name__ == "__main__":
    main()
