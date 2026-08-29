from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def recommend_action(stability_score: float, total_changes: float, files_changed: float) -> str:
    if stability_score < 0.35:
        return "BLOCK_AND_DIAGNOSE: trigger deep log triage and mandatory reviewer approval."
    if stability_score < 0.55:
        return "RUN_EXTENDED_TESTS: prioritize integration/regression suites."
    if total_changes > 300 or files_changed > 15:
        return "CAUTIONARY_RUN: run standard pipeline plus targeted tests."
    return "FAST_TRACK: standard CI run with normal monitoring."


def main() -> None:
    parser = argparse.ArgumentParser(description="POC for Objective 4: portable agentic orchestration stub.")
    parser.add_argument("--infile", default="outputs/objective3_metric_poc.csv")
    parser.add_argument("--out", default="outputs/objective4_agentic_actions.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.infile)
    # Join with extra fields if available from unified dataset.
    unified = Path("data/processed/unified_build_dataset.csv")
    if unified.exists():
        more = pd.read_csv(unified)[["build_id", "total_changes", "files_changed"]]
        df = df.merge(more, on="build_id", how="left")
    else:
        df["total_changes"] = 0
        df["files_changed"] = 0

    df["recommended_action"] = df.apply(
        lambda r: recommend_action(
            float(r.get("stability_score", 0.5)),
            float(r.get("total_changes", 0.0)),
            float(r.get("files_changed", 0.0)),
        ),
        axis=1,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df[["repo", "build_id", "stability_score", "recommended_action"]].to_csv(out_path, index=False)
    print(f"[OK] Objective 4 agentic POC output: {out_path}")


if __name__ == "__main__":
    main()
