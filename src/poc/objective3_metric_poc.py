from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def compute_build_stability_metric(df: pd.DataFrame) -> pd.Series:
    # Lightweight POC metric. Formal metric design comes in Objective 3 paper.
    # Higher score => more stable.
    risk = (
        0.20 * (df["duration_sec"].fillna(df["duration_sec"].median()) / 3600.0).clip(0, 1)
        + 0.25 * (df["total_changes"].fillna(0) / 500.0).clip(0, 1)
        + 0.25 * (df["files_changed"].fillna(0) / 25.0).clip(0, 1)
        + 0.20 * (df["run_attempt"].fillna(1) - 1).clip(0, 1)
        + 0.10 * (df["is_failed"].fillna(0))
    )
    return (1.0 - risk).clip(0, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="POC for Objective 3: build stability metric.")
    parser.add_argument("--infile", default="data/processed/unified_build_dataset.csv")
    parser.add_argument("--out", default="outputs/objective3_metric_poc.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.infile)
    df["stability_score"] = compute_build_stability_metric(df)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df[["repo", "build_id", "conclusion", "is_failed", "stability_score"]].to_csv(out_path, index=False)
    print(f"[OK] Objective 3 metric POC output: {out_path}")


if __name__ == "__main__":
    main()
