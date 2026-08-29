from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest TravisTorrent CSV and map to project raw schema."
    )
    parser.add_argument(
        "--infile",
        required=True,
        help="Path to TravisTorrent CSV file downloaded manually.",
    )
    parser.add_argument(
        "--out",
        default="data/raw/travistorrent_raw.csv",
        help="Mapped output path.",
    )
    args = parser.parse_args()

    in_path = Path(args.infile)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(in_path, low_memory=False)

    # Common fields observed in TravisTorrent variants.
    col_candidates = {
        "repo": ["gh_project_name", "gh_repository_name", "repo", "project"],
        "build_id": ["tr_build_id", "build_id", "id_build"],
        "run_number": ["tr_build_number", "build_number"],
        "event": ["gh_event_type", "event_type", "event"],
        "status": ["tr_status", "status"],
        "conclusion": ["tr_status", "status"],
        "created_at": ["gh_build_started_at", "tr_started_at", "started_at"],
        "started_at": ["gh_build_started_at", "tr_started_at", "started_at"],
        "updated_at": ["tr_finished_at", "finished_at"],
        "duration_sec": ["tr_duration", "build_duration"],
        "head_sha": ["git_trigger_commit", "gh_commit", "sha"],
        "branch": ["git_branch", "branch"],
        "commit_timestamp": ["gh_build_started_at", "commit_time"],
        "additions": ["gh_diff_added", "diff_added", "additions"],
        "deletions": ["gh_diff_removed", "diff_removed", "deletions"],
        "total_changes": ["gh_diff_modified", "diff_modified", "total_changes"],
        "files_changed": ["gh_diff_files", "diff_files", "files_changed"],
        "run_attempt": [],
        "commit_message_len": [],
    }

    mapped = pd.DataFrame()
    for target, candidates in col_candidates.items():
        found = None
        for c in candidates:
            if c in df.columns:
                found = c
                break
        mapped[target] = df[found] if found else None

    mapped["source"] = "travistorrent"
    mapped["run_attempt"] = mapped["run_attempt"].fillna(1)
    mapped["commit_message_len"] = mapped["commit_message_len"].fillna(0)

    mapped.to_csv(out_path, index=False)
    print(f"[OK] TravisTorrent mapped raw dataset: {out_path} ({len(mapped)} rows)")


if __name__ == "__main__":
    main()
