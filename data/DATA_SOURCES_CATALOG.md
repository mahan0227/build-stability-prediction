# Real CI/CD Data Sources Catalog

This file documents the publicly available repositories used to collect genuine GitHub Actions workflow-run traces for Objective 1 (and reusable for later thesis objectives). All records are retrieved from the public GitHub REST API (`/repos/{owner}/{repo}/actions/runs` and `/repos/{owner}/{repo}/commits/{sha}`). No synthetic rows are included in this corpus.

**Publisher of the API and hosting platform:** GitHub, Inc. (Microsoft).  
**License of traces:** public workflow metadata and public commit stats from each project's open-source repository, used for non-commercial academic research under GitHub's terms of service and each project's open-source license.

---

## How this corpus is genuine

1. Each row corresponds to a real completed GitHub Actions workflow run that can be opened at the recorded `html_url`.
2. Outcome labels (`success` / `failure`) are assigned by GitHub Actions, not by this project.
3. Change-scope fields (`additions`, `deletions`, `files_changed`, commit message length) come from the triggering commit via the GitHub Commits API.
4. Collection is authenticated with a personal access token for rate-limit purposes only; no private repositories are queried.
5. There is no silent synthetic fallback. If the API is unreachable, collection fails rather than fabricating rows.

## How the data can be used in the thesis

| Thesis use | How this corpus supports it |
|---|---|
| Objective 1 — dataset suitability and parameter–outcome analysis | Harmonized schema, class balance, chronological vs random splits, leakage ablation |
| Objective 2 — comparative modeling | Same frozen snapshot as a public, multi-project, time-ordered benchmark |
| Objective 3 — stability / evaluation metrics | Per-split failure rates, drift over time, failure-class precision/recall/F1 |
| Objective 4 — agentic orchestration (future) | Workflow names, event types, retry counts, and URLs as operational context |

---

## Repository list

**Collection completed 28 August 2026.** Combined snapshot: **3,000** completed success/failure runs; overall failure rate **0.1297**. Machine-readable per-repo stats: `data/raw/real/collection_manifest.json`.

| # | Repository | Publisher / maintainer | Public URL | Ecosystem | Why it is a genuine research source |
|---|---|---|---|---|---|
| 1 | `pallets/flask` | Pallets (PSF-adjacent Python web project) | https://github.com/pallets/flask | Python | Canonical micro-framework with long public CI history |
| 2 | `psf/requests` | Python Software Foundation | https://github.com/psf/requests | Python | Widely used HTTP library; PSF-maintained; public Actions workflows |
| 3 | `numpy/numpy` | NumPy / NumFOCUS | https://github.com/numpy/numpy | Python / scientific | Core scientific-computing library with production-grade CI |
| 4 | `pandas-dev/pandas` | pandas / NumFOCUS | https://github.com/pandas-dev/pandas | Python / scientific | High-volume data library; frequent CI runs across PRs |
| 5 | `scikit-learn/scikit-learn` | scikit-learn / INRIA / community | https://github.com/scikit-learn/scikit-learn | Python / ML | Standard ML library; public test-heavy GitHub Actions |
| 6 | `fastapi/fastapi` | Sebastián Ramírez / FastAPI org | https://github.com/fastapi/fastapi | Python | High-velocity web framework with public CI |
| 7 | `apache/airflow` | Apache Software Foundation | https://github.com/apache/airflow | Python / data | ASF project; complex multi-job CI typical of industrial pipelines |
| 8 | `facebook/react` | Meta (Facebook) Open Source | https://github.com/facebook/react | JavaScript | Major frontend library; public Actions traces |
| 9 | `vuejs/core` | Vue.js / Evan You and core team | https://github.com/vuejs/core | JavaScript / TypeScript | Major frontend framework; public CI |
| 10 | `axios/axios` | axios organization | https://github.com/axios/axios | JavaScript | Widely used HTTP client; public workflow runs |
| 11 | `microsoft/TypeScript` | Microsoft | https://github.com/microsoft/TypeScript | TypeScript | Large compiler project; dense public CI |
| 12 | `spring-projects/spring-boot` | VMware / Spring | https://github.com/spring-projects/spring-boot | Java | Enterprise Java framework; public GitHub Actions |
| 13 | `grafana/grafana` | Grafana Labs | https://github.com/grafana/grafana | Go / TypeScript | Observability product with open-source CI |
| 14 | `tokio-rs/tokio` | Tokio project | https://github.com/tokio-rs/tokio | Rust | Standard async runtime; public Actions |
| 15 | `opencv/opencv` | OpenCV.org | https://github.com/opencv/opencv | C++ | Computer-vision library; public multi-platform CI |

**API endpoints used for every repository**

- Workflow runs: `https://api.github.com/repos/{owner}/{repo}/actions/runs`
- Commit enrichment: `https://api.github.com/repos/{owner}/{repo}/commits/{sha}`
- Human-readable run page: stored per row in `html_url` (example pattern `https://github.com/{owner}/{repo}/actions/runs/{id}`)

---

## Collection parameters

- Filter: completed runs with `conclusion` in `{success, failure}` (cancelled / skipped / in-progress excluded so the binary label is unambiguous).
- Target: up to 200 recent completed success/failure runs per repository.
- Fields retained: run identifiers, timestamps, duration, conclusion, event, branch, SHA, commit message length, additions, deletions, total changes, files changed, run attempt, HTML URL.
- Output layout:
  - per-repo CSVs: `data/raw/real/<owner>__<repo>.csv`
  - machine-readable manifest: `data/raw/real/collection_manifest.json`
  - harmonized analysis table: `data/processed/unified_build_dataset.csv` (written after collection; previous synthetic file is replaced)

---

## Provenance after collection

## Collected statistics (this run)

| Repository | Rows | Failure rate | Time window (created_at) |
|---|---:|---:|---|
| pallets/flask | 200 | 0.470 | 2026-07-02 → 2026-08-28 |
| psf/requests | 200 | 0.245 | 2026-06-15 → 2026-08-26 |
| numpy/numpy | 200 | 0.005 | 2026-08-27 → 2026-08-28 |
| pandas-dev/pandas | 200 | 0.085 | 2026-08-27 → 2026-08-28 |
| scikit-learn/scikit-learn | 200 | 0.045 | 2026-08-28 → 2026-08-28 |
| fastapi/fastapi | 200 | 0.085 | 2026-08-26 → 2026-08-28 |
| apache/airflow | 200 | 0.085 | 2026-08-21 → 2026-08-28 |
| facebook/react | 200 | 0.025 | 2026-08-26 → 2026-08-28 |
| vuejs/core | 200 | 0.080 | 2026-08-26 → 2026-08-28 |
| axios/axios | 200 | 0.040 | 2026-08-13 → 2026-08-28 |
| microsoft/TypeScript | 200 | 0.095 | 2026-08-26 → 2026-08-28 |
| spring-projects/spring-boot | 200 | 0.070 | 2026-08-25 → 2026-08-28 |
| grafana/grafana | 200 | 0.025 | 2026-07-18 → 2026-07-19 |
| tokio-rs/tokio | 200 | 0.080 | 2026-08-15 → 2026-08-28 |
| opencv/opencv | 200 | 0.510 | 2026-08-13 → 2026-08-28 |
| **Total** | **3,000** | **0.1297** | 2026-06-15 → 2026-08-28 |

See also `data/processed/real_corpus_profile.md`.
