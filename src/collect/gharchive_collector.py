from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


def _download_hour(hour_str: str, out_dir: Path) -> Path:
    # hour_str format: YYYY-MM-DD-H
    url = f"https://data.gharchive.org/{hour_str}.json.gz"
    out_path = out_dir / f"{hour_str}.json.gz"
    out_dir.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    out_path.write_bytes(response.content)
    return out_path


def _parse_push_events(gz_path: Path, repo_filter: set[str] | None = None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    df = pd.read_json(gz_path, lines=True, compression="gzip")
    push_df = df[df["type"] == "PushEvent"].copy()
    for _, r in push_df.iterrows():
        repo_name = (r.get("repo") or {}).get("name") if isinstance(r.get("repo"), dict) else None
        if repo_filter and repo_name not in repo_filter:
            continue
        payload = r.get("payload") if isinstance(r.get("payload"), dict) else {}
        commits = payload.get("commits", []) if isinstance(payload, dict) else []
        size = payload.get("size", 0) if isinstance(payload, dict) else 0
        distinct_size = payload.get("distinct_size", 0) if isinstance(payload, dict) else 0
        head = payload.get("head") if isinstance(payload, dict) else None
        ref = payload.get("ref") if isinstance(payload, dict) else None
        rows.append(
            {
                "source": "gharchive",
                "repo": repo_name,
                "build_id": None,
                "run_number": None,
                "event": "push",
                "status": "event_only",
                "conclusion": None,
                "created_at": r.get("created_at"),
                "started_at": r.get("created_at"),
                "updated_at": r.get("created_at"),
                "duration_sec": None,
                "head_sha": head,
                "branch": ref,
                "commit_timestamp": r.get("created_at"),
                "commit_message_len": None,
                "additions": None,
                "deletions": None,
                "total_changes": size,
                "files_changed": distinct_size,
                "run_attempt": 1,
                "gh_event_id": r.get("id"),
                "commit_count": len(commits) if isinstance(commits, list) else 0,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect GHArchive PushEvent data for process/context signals.")
    parser.add_argument("--hour", required=True, help="Hour slice format: YYYY-MM-DD-H")
    parser.add_argument("--repos", nargs="*", default=None, help="Optional repo filters, e.g. owner/repo")
    parser.add_argument("--out", default="data/raw/gharchive_raw.csv")
    args = parser.parse_args()

    temp_dir = Path("data/raw/gharchive_downloads")
    gz_path = _download_hour(args.hour, temp_dir)
    repo_filter = set(args.repos) if args.repos else None
    df = _parse_push_events(gz_path, repo_filter=repo_filter)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(
        f"[OK] GHArchive raw dataset written: {out_path} ({len(df)} rows) at {datetime.now(timezone.utc).isoformat()}"
    )


if __name__ == "__main__":
    main()
