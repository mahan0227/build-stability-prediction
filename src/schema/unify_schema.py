from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


UNIFIED_COLUMNS = [
    "source",
    "repo",
    "build_id",
    "run_number",
    "event",
    "status",
    "conclusion",
    "created_at",
    "started_at",
    "updated_at",
    "duration_sec",
    "head_sha",
    "branch",
    "commit_timestamp",
    "commit_message_len",
    "additions",
    "deletions",
    "total_changes",
    "files_changed",
    "run_attempt",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Harmonize CI/CD data into unified schema.")
    parser.add_argument(
        "--infile",
        default="data/raw/github_actions_raw.csv",
        help="Single input CSV path (legacy option).",
    )
    parser.add_argument(
        "--inputs",
        nargs="*",
        default=None,
        help="Multiple input CSVs to combine before harmonization.",
    )
    parser.add_argument("--out", default="data/processed/unified_build_dataset.csv")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.inputs:
        frames: list[pd.DataFrame] = []
        for p in args.inputs:
            path = Path(p)
            if path.exists():
                frames.append(pd.read_csv(path))
        if not frames:
            raise FileNotFoundError("No valid input files found in --inputs.")
        df = pd.concat(frames, ignore_index=True)
    else:
        in_path = Path(args.infile)
        df = pd.read_csv(in_path)

    for col in UNIFIED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    unified = df[UNIFIED_COLUMNS].copy()
    numeric_cols = ["duration_sec", "commit_message_len", "additions", "deletions", "total_changes", "files_changed", "run_attempt"]
    for col in numeric_cols:
        unified[col] = pd.to_numeric(unified[col], errors="coerce")

    # Unified binary label for Objective 1 analysis.
    failure_labels = {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}
    unified["is_failed"] = unified["conclusion"].fillna("").str.lower().isin(failure_labels).astype(int)

    unified.to_csv(out_path, index=False)
    print(f"[OK] Unified schema dataset written: {out_path} ({len(unified)} rows)")


if __name__ == "__main__":
    main()
