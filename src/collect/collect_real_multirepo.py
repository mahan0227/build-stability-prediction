"""Collect real CI/CD build records from public GitHub Actions APIs.

Collects completed workflow runs with definitive outcomes (success/failure)
from a curated list of well-known, actively maintained open-source
repositories, and enriches each run with change-scope statistics from the
associated commit. There is intentionally NO synthetic fallback: if the API
is unreachable the script fails loudly, so the resulting corpus can never
silently contain fabricated records.

Outputs:
  data/raw/real/<owner>__<repo>.csv     one CSV per repository (resumable)
  data/raw/real/collection_manifest.json  provenance metadata per repository
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

# Curated corpus: high-profile, actively maintained OSS projects that run CI
# on GitHub Actions, spanning ecosystems (Python, JS/TS, Java, Go, Rust, C++)
# and publishers (PSF, NumFOCUS, Meta, Microsoft, ASF, VMware, ...).
DEFAULT_REPOS = [
    "pallets/flask",
    "psf/requests",
    "numpy/numpy",
    "pandas-dev/pandas",
    "scikit-learn/scikit-learn",
    "fastapi/fastapi",
    "apache/airflow",
    "facebook/react",
    "vuejs/core",
    "axios/axios",
    "microsoft/TypeScript",
    "spring-projects/spring-boot",
    "grafana/grafana",
    "tokio-rs/tokio",
    "opencv/opencv",
]

API = "https://api.github.com"
KEEP_CONCLUSIONS = {"success", "failure"}
MAX_PAGES = 10  # GitHub caps this listing at 1000 results (10 x 100).


def _to_dt(ts: str | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _duration_seconds(started_at: str | None, updated_at: str | None) -> float | None:
    s, u = _to_dt(started_at), _to_dt(updated_at)
    if not s or not u:
        return None
    return max((u - s).total_seconds(), 0.0)


def gh_get(session: requests.Session, url: str, params: dict | None = None) -> requests.Response:
    """GET with rate-limit-aware retries. Raises after persistent failure."""
    for attempt in range(10):
        try:
            resp = session.get(url, params=params, timeout=45)
        except requests.RequestException as exc:
            print(f"[RETRY] network error ({exc}); attempt {attempt + 1}")
            time.sleep(15)
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code in (403, 429):
            if resp.headers.get("X-RateLimit-Remaining") == "0":
                reset = int(resp.headers.get("X-RateLimit-Reset", "0"))
                wait = max(reset - time.time(), 0) + 5
                print(f"[RATE] quota exhausted; sleeping {wait:.0f}s until reset")
                time.sleep(wait)
                continue
            retry_after = int(resp.headers.get("Retry-After", "30"))
            print(f"[RATE] secondary limit; sleeping {retry_after}s")
            time.sleep(retry_after)
            continue
        if resp.status_code in (500, 502, 503, 504):
            time.sleep(10)
            continue
        resp.raise_for_status()
    raise RuntimeError(f"Persistent failure fetching {url}")


def collect_repo(
    session: requests.Session,
    repo: str,
    max_runs: int,
    commit_cache: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    kept_runs: list[dict[str, Any]] = []
    for page in range(1, MAX_PAGES + 1):
        resp = gh_get(
            session,
            f"{API}/repos/{repo}/actions/runs",
            params={"per_page": 100, "page": page, "status": "completed"},
        )
        runs = resp.json().get("workflow_runs", [])
        if not runs:
            break
        for run in runs:
            if run.get("conclusion") in KEEP_CONCLUSIONS:
                kept_runs.append(run)
        print(f"[{repo}] page {page}: kept so far {len(kept_runs)}")
        if len(kept_runs) >= max_runs:
            break
    kept_runs = kept_runs[:max_runs]

    rows: list[dict[str, Any]] = []
    for i, run in enumerate(kept_runs, 1):
        sha = run.get("head_sha")
        commit_payload = commit_cache.get(f"{repo}@{sha}")
        if commit_payload is None and sha:
            try:
                commit_payload = gh_get(session, f"{API}/repos/{repo}/commits/{sha}").json()
            except Exception as exc:
                print(f"[{repo}] commit {sha[:8]} lookup failed: {exc}")
                commit_payload = {}
            commit_cache[f"{repo}@{sha}"] = commit_payload
        commit_payload = commit_payload or {}

        stats = commit_payload.get("stats", {}) or {}
        files = commit_payload.get("files", []) or []
        commit_meta = commit_payload.get("commit", {}) or {}
        commit_msg = commit_meta.get("message") or ""
        commit_ts = (commit_meta.get("committer") or {}).get("date")

        rows.append(
            {
                "source": "github_actions",
                "repo": repo,
                "build_id": run.get("id"),
                "run_number": run.get("run_number"),
                "workflow_name": run.get("name"),
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
                "html_url": run.get("html_url"),
            }
        )
        if i % 50 == 0:
            print(f"[{repo}] enriched {i}/{len(kept_runs)} runs")
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect real GitHub Actions build data (no synthetic fallback).")
    parser.add_argument("--repos", nargs="*", default=DEFAULT_REPOS, help="owner/repo list.")
    parser.add_argument("--max-runs-per-repo", type=int, default=400)
    parser.add_argument("--outdir", default="data/raw/real")
    parser.add_argument("--force", action="store_true", help="Re-collect repos that already have a CSV.")
    args = parser.parse_args()

    load_dotenv()
    import os

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN missing in environment/.env; refusing to run unauthenticated.")

    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "thesis-poc-cicd-stability-research",
            "Authorization": f"Bearer {token}",
        }
    )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    manifest_path = outdir / "collection_manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    commit_cache: dict[str, dict[str, Any]] = {}
    for repo in args.repos:
        out_csv = outdir / f"{repo.replace('/', '__')}.csv"
        if out_csv.exists() and not args.force:
            print(f"[SKIP] {repo} already collected ({out_csv})")
            continue
        print(f"[START] {repo}")
        df = collect_repo(session, repo, args.max_runs_per_repo, commit_cache)
        if df.empty:
            print(f"[WARN] {repo} yielded 0 usable runs; skipping save.")
            continue
        df.to_csv(out_csv, index=False)
        manifest[repo] = {
            "url": f"https://github.com/{repo}",
            "api_endpoint": f"{API}/repos/{repo}/actions/runs",
            "rows": int(len(df)),
            "failure_rate": float((df["conclusion"] == "failure").mean()),
            "window_start": str(pd.to_datetime(df["created_at"]).min()),
            "window_end": str(pd.to_datetime(df["created_at"]).max()),
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"[OK] {repo}: {len(df)} rows -> {out_csv}")

    print(f"[DONE] manifest: {manifest_path}")


if __name__ == "__main__":
    main()
