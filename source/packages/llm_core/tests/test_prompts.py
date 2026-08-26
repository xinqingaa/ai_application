import pytest

from llm_core import PromptTemplate, get_prompt, list_prompt_versions, render_prompt


def test_prompt_versions_are_loaded_by_identity() -> None:
    assert list_prompt_versions("review.risk_review") == [
        "1.0.0",
        "2.0.0",
        "3.0.0",
        "4.0.0",
        "5.0.0",
    ]
    assert get_prompt("review.risk_review", "2").ref == "review.risk_review@2.0.0"


def test_render_prompt_rejects_missing_variables() -> None:
    template = PromptTemplate(
        prompt_id="review.test",
        version="1.0.0",
        model_config_ref="chat.dev_chat",
        system="只依据 {{evidence_block}}",
        user="评审 {{requirement_text}}",
    )

    with pytest.raises(ValueError, match="evidence_block"):
        render_prompt(template, {"requirement_text": "售后入口需求"})


def test_render_prompt_allows_explicit_empty_value() -> None:
    template = PromptTemplate(
        prompt_id="review.test",
        version="1.0.0",
        model_config_ref="chat.dev_chat",
        system="只依据 {{evidence_block}}",
        user="评审 {{requirement_text}}",
    )

    messages = render_prompt(
        template,
        {"requirement_text": "售后入口需求", "evidence_block": ""},
    )

    assert messages == [
        {"role": "system", "content": "只依据"},
        {"role": "user", "content": "评审 售后入口需求"},
    ]
