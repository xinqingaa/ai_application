from __future__ import annotations

import argparse
from pathlib import Path

from optimization_basics import DEFAULT_GOLDEN_SET_PATH, load_golden_set, summarize_golden_set


def main() -> None:
    parser = argparse.ArgumentParser(description="查看第七章 Golden Set")
    parser.add_argument("--path", default=str(DEFAULT_GOLDEN_SET_PATH))
    args = parser.parse_args()

    cases = load_golden_set(Path(args.path))
    summary = summarize_golden_set(cases)

    print("Golden Set Summary")
    for key, value in summary.items():
        print(f"- {key}: {value}")

    for case in cases:
        print("=" * 72)
        print(f"case_id: {case.case_id}")
        print(f"question: {case.question}")
        print(f"should_refuse: {case.should_refuse}")
        print(f"retrieval_expected_chunk_ids: {list(case.retrieval_expected_chunk_ids)}")
        print(f"expected_sources: {list(case.expected_sources)}")
        print(f"expected_answer_points: {list(case.expected_answer_points)}")
        if case.tags:
            print(f"tags: {list(case.tags)}")
        if case.notes:
            print(f"notes: {case.notes}")


if __name__ == "__main__":
    main()
