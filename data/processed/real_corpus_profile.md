# Real corpus profile (analysis-ready snapshot)

**File:** `data/processed/unified_build_dataset.csv`  
**Frozen copy:** `data/processed/unified_build_dataset_real.csv`  
**Synthetic archive (previous run, not used):** `data/processed/unified_build_dataset_synthetic_archive.csv`  
**Collected:** 28 August 2026 via GitHub REST API (authenticated, public repos only)  
**Source column:** `github_actions` on all 3,000 rows (no synthetic records)

## Snapshot size

| Item | Value |
|---|---|
| Repositories | 15 public OSS projects |
| Records | 3,000 completed workflow runs |
| Success | 2,611 (87.03%) |
| Failure | 389 (12.97%) |
| Missing values on analysis fields | 0 |
| Time span (`created_at`) | 2026-06-15 to 2026-08-28 |
| Publisher / platform | GitHub, Inc. (public Actions API) |

Per-repository counts, URLs, publishers, and failure rates: `data/DATA_SOURCES_CATALOG.md` and `data/raw/real/collection_manifest.json`.

## Modeling notes

- Binary label `is_failed` = 1 iff GitHub `conclusion` is `failure` (cancelled/skipped excluded at collection).
- `total_changes` equals `additions + deletions` on every row (collinear). Association tests may keep all seven fields; logistic models should drop `total_changes` when interpreting coefficients.
- GitHub's commit API truncates the files list at 300 entries; `files_changed` is therefore a lower bound on very large commits.

## Analysis outputs (this snapshot)

| Analysis | Path |
|---|---|
| Associations | `outputs/objective1_real/parameter_association.csv` |
| Holm / BH | `outputs/objective1_real/parameter_association_corrected.csv` |
| Random-holdout logistic | `outputs/objective1_real/objective1_summary.md` |
| Chronological vs random | `outputs/objective1_temporal_real/temporal_vs_random_summary.md` |
| Leakage ablation + CIs + 30 seeds | `outputs/objective1_robustness_real/robustness_summary.md` |
