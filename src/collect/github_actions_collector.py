from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv


DEFAULT_REPOS = [
    "pallets/flask",
    "psf/requests",
    "numpy/numpy",
]


def _to_dt(ts: str | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _duration_seconds(started_at: str | None, updated_at: str | None) -> float | None:
    s = _to_dt(started_at)
    u = _to_dt(updated_at)
    if not s or not u:
        return None
    return max((u - s).total_seconds(), 0.0)


def _github_get(url: str, headers: dict[str, str], timeout: int = 30) -> dict[str, Any]:
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _collect_github_actions(
    repos: list[str],
    max_runs_per_repo: int,
    token: str | None,
) -> pd.DataFrame:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "thesis-poc-cicd-stability",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    rows: list[dict[str, Any]] = []
    for repo in repos:
        runs_url = f"https://api.github.com/repos/{repo}/actions/runs?per_page={max_runs_per_repo}"
        runs_payload = _github_get(runs_url, headers=headers)
        runs = runs_payload.get("workflow_runs", [])
        for run in runs:
            sha = run.get("head_sha")
            commit_url = f"https://api.github.com/repos/{repo}/commits/{sha}" if sha else None
            commit_payload: dict[str, Any] = {}
            if commit_url:
                try:
                    commit_payload = _github_get(commit_url, headers=headers)
                except Exception:
                    commit_payload = {}

            stats = commit_payload.get("stats", {}) if isinstance(commit_payload, dict) else {}
            files = commit_payload.get("files", []) if isinstance(commit_payload, dict) else []
            commit_meta = commit_payload.get("commit", {}) if isinstance(commit_payload, dict) else {}
            commit_msg = (commit_meta.get("message") or "") if isinstance(commit_meta, dict) else ""
            committer = commit_meta.get("committer", {}) if isinstance(commit_meta, dict) else {}
            commit_ts = committer.get("date")

            rows.append(
                {
                    "source": "github_actions",
                    "repo": repo,
                    "build_id": run.get("id"),
                    "run_number": run.get("run_number"),
                    "event": run.get("event"),
                    "status": run.get("status"),
                    "conclusion": run.get("conclusion"),
                    "created_at": run.get("created_at"),
                    "started_at": run.get("run_started_at"),
                    "updated_at": run.get("updated_at"),
                    "duration_sec": _duration_seconds(run.get("run_started_at"), run.get("updated_at")),
                    "head_sha": sha,
                    "branch": run.get("head_branch"),
                    "commit_timestamp": commit_ts,
                    "commit_message_len": len(commit_msg),
                    "additions": stats.get("additions"),
                    "deletions": stats.get("deletions"),
                    "total_changes": stats.get("total"),
                    "files_changed": len(files) if isinstance(files, list) else None,
                    "run_attempt": run.get("run_attempt"),
                }
            )

    if not rows:
        raise RuntimeError("No records were collected from GitHub Actions.")
    return pd.DataFrame(rows)


def _build_synthetic_dataset(rows: int = 300) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    out: list[dict[str, Any]] = []
    for i in range(rows):
        additions = (i * 7) % 320 + 3
        deletions = (i * 5) % 180 + 2
        files_changed = (i % 15) + 1
        duration_sec = 80 + (i * 13) % 1800
        run_attempt = 1 if i % 10 else 2
        commit_message_len = 20 + (i * 3) % 140
        # Synthetic but realistic-ish failure relationship.
        risk_score = (
            0.0008 * additions
            + 0.001 * deletions
            + 0.06 * files_changed
            + 0.0004 * duration_sec
            + 0.35 * (run_attempt - 1)
            - 0.002 * commit_message_len
        )
        failed = risk_score > 1.1
        ts = now - timedelta(hours=i)
        out.append(
            {
                "source": "synthetic",
                "repo": f"synthetic/repo-{(i % 4) + 1}",
                "build_id": 100000 + i,
                "run_number": i + 1,
                "event": "push",
                "status": "completed",
                "conclusion": "failure" if failed else "success",
                "created_at": ts.isoformat(),
                "started_at": ts.isoformat(),
                "updated_at": (ts + timedelta(seconds=duration_sec)).isoformat(),
                "duration_sec": float(duration_sec),
                "head_sha": f"sha{i:08d}",
                "branch": "main",
                "commit_timestamp": ts.isoformat(),
                "commit_message_len": commit_message_len,
                "additions": additions,
                "deletions": deletions,
                "total_changes": additions + deletions,
                "files_changed": files_changed,
                "run_attempt": run_attempt,
            }
        )
    return pd.DataFrame(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect CI/CD build data from public GitHub Actions.")
    parser.add_argument("--repos", nargs="*", default=DEFAULT_REPOS, help="owner/repo list.")
    parser.add_argument("--max-runs-per-repo", type=int, default=60)
    parser.add_argument("--use-synthetic", action="store_true", help="Generate synthetic data for offline/demo use.")
    parser.add_argument("--out", default="data/raw/github_actions_raw.csv")
    args = parser.parse_args()

    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.use_synthetic:
        df = _build_synthetic_dataset()
    else:
        # No silent synthetic fallback: if live collection fails, fail loudly
        # so real and synthetic corpora can never be conflated.
        df = _collect_github_actions(args.repos, args.max_runs_per_repo, token)

    df.to_csv(out_path, index=False)
    metadata = {
        "rows": int(len(df)),
        "repos": sorted(df["repo"].dropna().unique().tolist()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (out_path.parent / "collection_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"[OK] Raw dataset written: {out_path} ({len(df)} rows)")


if __name__ == "__main__":
    main()
