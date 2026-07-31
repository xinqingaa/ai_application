"""Observe real embedding vectors and pairwise similarity scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app_log import add_log_arguments, configure_from_args, console, get_logger
from dotenv import load_dotenv
from llm_core import LLMClient, LLMError, LLMErrorCode
from rag_core import SimilarityMetric, embed_texts, pairwise_similarity

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
PROBES_PATH = (
    REPO_ROOT / "review_assistant" / "fixtures" / "v0" / "retrieval" / "embedding_probes.json"
)
log = get_logger("rag_retrieval_lab.embedding")


def main() -> int:
    parser = argparse.ArgumentParser(description="Embedding 表示与成对相似度观察")
    parser.add_argument(
        "--config-ref",
        default="embedding.default_embed",
        help="llm_core 中的 embedding config_ref",
    )
    parser.add_argument(
        "--metric",
        choices=("cosine", "dot", "euclidean"),
        default="cosine",
        help="成对相似度度量；默认 cosine（越大越近）",
    )
    parser.add_argument(
        "--probes",
        type=Path,
        default=PROBES_PATH,
        help="探针 JSON 路径",
    )
    parser.add_argument(
        "--preprocessing-version",
        default="raw-v1",
        help="记录本轮文本预处理契约版本；改变文本组装方式时必须升级",
    )
    add_log_arguments(parser)
    args = parser.parse_args()
    configure_from_args(args)
    json_mode = args.log_format == "json" and not args.verbose

    _load_env()
    payload = json.loads(args.probes.read_text(encoding="utf-8"))
    probes = payload["probes"]
    groups = {item["id"]: item.get("group", "") for item in probes}
    metric = SimilarityMetric(args.metric)

    if not json_mode:
        console.title(
            "RAG Retrieval Lab · Embedding",
            "真实 Embedding 成对相似度观察\n"
            f"config={args.config_ref} · metric={metric.value}\n"
            "本实验比较探针句对，不把结果当成知识库检索结论",
        )

    try:
        batch = embed_texts(
            [item["text"] for item in probes],
            client=LLMClient.from_default_config(),
            config_ref=args.config_ref,
            text_ids=[item["id"] for item in probes],
            preprocessing_version=args.preprocessing_version,
            debug=args.verbose,
        )
    except LLMError as exc:
        if json_mode:
            log.error(
                "embedding.failed",
                "Embedding 调用失败",
                code=exc.code.value,
                error_message=exc.message,
                config_ref=exc.config_ref,
            )
        else:
            console.error(f"{exc.code.value} [{exc.config_ref}]: {exc.message}")
            if exc.code is LLMErrorCode.PROVIDER_ERROR and "404" in exc.message:
                console.hint(
                    "chat 若走 DeepSeek，请为 Embedding 单独配置 "
                    "OPENAI_EMBEDDING_BASE_URL / OPENAI_EMBEDDING_API_KEY"
                )
        return 1

    observations = pairwise_similarity(batch.records, metric=metric)
    focus = _focus_rows(observations, payload.get("focus_pairs", []))

    if json_mode:
        log.success(
            "embedding.completed",
            "Embedding 成对观察完成",
            model=batch.response.model,
            dimensions=batch.response.dimensions,
            preprocessing_version=batch.records[0].preprocessing_version,
            latency_ms=round(batch.response.latency_ms, 1),
            probe_count=len(batch.records),
            pair_count=len(observations),
            usage=batch.response.usage,
            focus=focus,
        )
        if args.verbose:
            for item in observations:
                log.info(
                    "embedding.pair",
                    "成对相似度",
                    left=item.left_id,
                    right=item.right_id,
                    score=round(item.score, 6),
                    metric=item.metric.value,
                    higher_is_closer=item.higher_is_closer,
                )
    else:
        _render_summary(batch, metric, groups)
        _render_focus(focus, metric)
        if args.verbose:
            _render_all_pairs(observations)
        console.success(
            f"{len(batch.records)} probes · {len(observations)} pairs · "
            f"dim={batch.response.dimensions} · "
            f"{batch.response.latency_ms:.0f} ms"
        )
        if not args.verbose:
            console.hint("使用 --verbose 查看全部成对分数")
    return 0


def _load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()


def _focus_rows(observations, focus_pairs: list[dict]) -> list[dict]:
    by_ids = {
        frozenset({item.left_id, item.right_id}): item
        for item in observations
    }
    rows: list[dict] = []
    for pair in focus_pairs:
        key = frozenset({pair["left"], pair["right"]})
        item = by_ids.get(key)
        rows.append(
            {
                "left": pair["left"],
                "right": pair["right"],
                "expect": pair.get("expect", ""),
                "score": None if item is None else round(item.score, 6),
                "found": item is not None,
            }
        )
    return rows


def _render_summary(batch, metric: SimilarityMetric, groups: dict[str, str]) -> None:
    usage = batch.response.usage
    console.info(
        f"model={batch.response.model} · provider={batch.response.provider} · "
        f"preprocessing={batch.records[0].preprocessing_version} · "
        f"metric={metric.value} · higher_is_closer="
        f"{metric is not SimilarityMetric.EUCLIDEAN}"
    )
    if usage is not None:
        console.info(
            f"usage prompt={usage.prompt_tokens} total={usage.total_tokens}"
        )
    console.table(
        ["ID", "Group", "Text"],
        [
            [
                probe.text_id or "",
                groups.get(probe.text_id or "", ""),
                _preview(probe.text),
            ]
            for probe in batch.records
        ],
        title="Probes",
    )


def _render_focus(focus: list[dict], metric: SimilarityMetric) -> None:
    direction = "越大越近" if metric is not SimilarityMetric.EUCLIDEAN else "越小越近"
    console.table(
        ["Left", "Right", "Score", "Expect"],
        [
            [
                row["left"],
                row["right"],
                "—" if row["score"] is None else f"{row['score']:.4f}",
                row["expect"],
            ]
            for row in focus
        ],
        title=f"Focus pairs（{direction}）",
    )
    console.info("这些分数只描述表示空间距离，不代表检索命中或证据充分。")


def _render_all_pairs(observations) -> None:
    console.table(
        ["Left", "Right", "Score"],
        [
            [
                item.left_id or _preview(item.left_text),
                item.right_id or _preview(item.right_text),
                f"{item.score:.4f}",
            ]
            for item in sorted(
                observations,
                key=lambda row: row.score,
                reverse=observations[0].higher_is_closer,
            )
        ],
        title="All pairs",
    )


def _preview(text: str, limit: int = 28) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


if __name__ == "__main__":
    raise SystemExit(main())
