from llm_core import ContextSource, build_review_context, estimate_tokens, format_context_source, get_context_policy


def test_build_review_context_keeps_traceable_evidence():
    source = ContextSource(
        source_id="EV-1",
        title="接口说明",
        content="售后接口 v2 需要 order_id。",
        priority=80,
    )

    context = build_review_context(
        requirement_text="订单详情页新增申请售后按钮。",
        sources=[source],
        token_budget=500,
    )

    assert context.included_source_ids == ["EV-1"]
    assert context.dropped_source_ids == []
    assert "[EV-1] 接口说明" in context.evidence_block
    assert "售后接口 v2" in context.to_prompt_variables()["evidence_block"]
    assert context.estimated_tokens > 0


def test_build_review_context_drops_low_priority_source_when_budget_is_limited():
    high = ContextSource(source_id="high", content="must keep", priority=90)
    low = ContextSource(source_id="low", content="word " * 200, priority=10)
    budget = (
        estimate_tokens("short requirement")
        + estimate_tokens(format_context_source(high))
        + 1
    )

    context = build_review_context(
        requirement_text="short requirement",
        sources=[low, high],
        token_budget=budget,
    )

    assert context.included_source_ids == ["high"]
    assert context.dropped_source_ids == ["low"]
    assert context.dropped_sources[0].reason == "token_budget_exceeded"


def test_build_review_context_deduplicates_sources_by_priority():
    older = ContextSource(source_id="EV-1", content="old content", priority=10)
    newer = ContextSource(source_id="EV-1", content="new content", priority=90)

    context = build_review_context(
        requirement_text="requirement",
        sources=[older, newer],
        token_budget=500,
    )

    assert context.included_source_ids == ["EV-1"]
    assert "new content" in context.evidence_block
    assert "old content" not in context.evidence_block


def test_duplicate_source_id_replaces_content_index():
    old = ContextSource(source_id="A", content="old content", priority=10)
    updated = ContextSource(source_id="A", content="new content", priority=90)
    independent = ContextSource(source_id="B", content="old content", priority=80)

    context = build_review_context(
        requirement_text="requirement",
        sources=[old, updated, independent],
        policy=get_context_policy("full_context"),
    )

    assert context.included_source_ids == ["A", "B"]
    assert "new content" in context.evidence_block
    assert "old content" in context.evidence_block
    assert context.dropped_source_ids == ["A"]
    assert context.dropped_sources[0].reason == "duplicate_source_id"


def test_build_review_context_uses_no_evidence_placeholder():
    context = build_review_context(
        requirement_text="只有一句需求。",
        sources=[],
        token_budget=100,
    )

    assert context.included_sources == []
    assert "无可用证据" in context.evidence_block
    assert context.report is not None
    assert "no_evidence_included" in {warning.code for warning in context.report.warnings}


def test_context_policy_can_disable_evidence_section():
    evidence = ContextSource(source_id="EV-1", content="接口说明", source_type="api_doc")
    agent_summary = ContextSource(
        source_id="AG-1",
        content="上游 Agent 判断接口参数存在风险。",
        source_type="agent_summary",
        priority=80,
    )

    context = build_review_context(
        requirement_text="订单详情页新增售后入口。",
        sources=[evidence, agent_summary],
        policy=get_context_policy("agent_summary_only"),
    )

    assert context.included_source_ids == ["AG-1"]
    assert "EV-1" in context.dropped_source_ids
    assert context.citation_candidates == []
    assert context.section_content("agent_summary")


def test_citation_candidates_only_come_from_included_evidence_sources():
    evidence = ContextSource(source_id="API-1", content="售后接口 v2 参数说明", source_type="api_doc")
    history = ContextSource(source_id="HIS-1", content="历史评审曾提到售后入口。", source_type="history_review")

    context = build_review_context(
        requirement_text="订单详情页新增售后入口。",
        sources=[history, evidence],
        policy=get_context_policy("full_context"),
    )

    assert set(context.included_source_ids) == {"API-1", "HIS-1"}
    assert [candidate.source_id for candidate in context.citation_candidates] == ["API-1"]


def test_context_builder_compresses_assumed_expanded_order_rules_with_stable_id():
    # Deterministic mechanism assumption: the real order_rules.md facts are
    # repeated inside a longer same-topic document only to exercise compression.
    expanded_order_rules = "\n".join(
        [
            "仅已支付且已完成的订单可申请售后。",
            "【确定性机制假设：同主题扩展段落】" + "售后流程背景说明。" * 40,
            "虚拟商品不进入售后流程。",
            "售后接口 v2 必须提供 source_channel。",
            "Flutter 客户端必须使用相同的入口可见性规则。",
        ]
    )
    source = ContextSource(
        source_id="ASSUMED-EXPANDED-ORDER-RULES",
        content=expanded_order_rules,
        source_type="evidence",
        priority=90,
    )

    context = build_review_context(
        requirement_text="申请售后",
        sources=[source],
        policy=get_context_policy("tight_budget"),
    )

    assert "ASSUMED-EXPANDED-ORDER-RULES" in context.included_source_ids
    assert context.report is not None
    assert "ASSUMED-EXPANDED-ORDER-RULES" in context.report.compressed_source_ids
    assert "ASSUMED-EXPANDED-ORDER-RULES" in context.evidence_block
    assert "compressed=true" in context.evidence_block


def test_context_builder_deduplicates_normalized_content():
    first = ContextSource(source_id="A", content="售后接口 v2 需要 order_id。", priority=20)
    better = ContextSource(source_id="B", content=" 售后接口 v2 需要 order_id。 ", priority=90)

    context = build_review_context(
        requirement_text="订单详情页新增售后入口。",
        sources=[first, better],
        policy=get_context_policy("full_context"),
    )

    assert context.included_source_ids == ["B"]
    assert context.dropped_source_ids == ["A"]
    assert context.dropped_sources[0].reason == "duplicate_content"


def test_context_report_exposes_section_tokens_and_warnings():
    context = build_review_context(
        requirement_text="订单详情页新增售后入口。",
        sources=[],
        policy=get_context_policy("balanced"),
    )

    assert context.report is not None
    assert "requirement" in context.report.section_tokens
    assert context.report.estimated_tokens == context.estimated_tokens
    assert context.context_block().startswith("## Requirement")
