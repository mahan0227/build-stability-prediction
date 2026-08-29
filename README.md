# Agentic AI Driven Continuous Build Stability Prediction in the SDLC

Replication artifact for the manuscript *Predicting Build Stability* and the
accompanying PhD thesis work. This repository is the reviewer-facing companion:
the analysis pipeline, the frozen public GitHub Actions corpus, and the tables
and figures needed to regenerate the empirical numbers.

The work is organised around four objectives. **Objective 1** is fully
implemented and is the source of the empirical results. Objectives 2–4 are
proof-of-concept implementations of the model, metric, and agentic
orchestration designs.

## Data provenance

The analysis snapshot in `data/processed/unified_build_dataset.csv` is **3,000
completed GitHub Actions workflow runs** collected on 28 August 2026 from 15
public open-source repositories. Every row has `source = github_actions`. Labels
(`success` / `failure`) are GitHub's own conclusions. There is no silent
synthetic fallback in the live collector: if the API is unreachable, collection
fails.

| Item | Value |
|---|---|
| Repositories | 15 public OSS projects |
| Records | 3,000 completed runs |
| Success / failure | 2,611 / 389 |
| Failure rate | 0.1297 |
| Window (`created_at`) | 2026-06-15 to 2026-08-28 |
| Platform | GitHub Actions public REST API |

Per-repository counts, URLs, and failure rates:
[`data/DATA_SOURCES_CATALOG.md`](data/DATA_SOURCES_CATALOG.md),
[`data/processed/real_corpus_profile.md`](data/processed/real_corpus_profile.md),
and `data/raw/real/collection_manifest.json`.

A previous 300-row synthetic generator run is kept only as
`data/processed/unified_build_dataset_synthetic_archive.csv`. It is **not** used
in the reported analyses.

## Repository layout

```text
src/
  collect/     GitHub Actions multi-repo collector plus optional TravisTorrent / GHArchive connectors
  schema/      harmonization into one canonical schema
  analysis/    Objective 1 statistics, temporal split, robustness, and report builders
  poc/         Objective 2, 3, and 4 proof-of-concept implementations
data/
  raw/real/    per-repository GitHub Actions CSVs and collection manifest
  processed/   frozen harmonized corpus used by the analyses
outputs/       Objective 1 results on the frozen snapshot
assets/        figures used in the manuscript
visualization/ interactive pipeline demo (empirical KPIs match the frozen snapshot)
```

## Setup

Requires Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The `Makefile` invokes `.venv/bin/python` by default. Override with
`make PYTHON=python3 ...` if you use a different environment.

## Reproducing the reported results

The bundled corpus is the exact input behind the numbers below. No network
access is required:

```bash
make objective1-snapshot
```

This rewrites `outputs/objective1_real/`, `outputs/objective1_temporal_real/`,
and `outputs/objective1_robustness_real/`. Compare against the committed copies.

Equivalent commands:

```bash
.venv/bin/python src/analysis/objective1_parameter_analysis.py \
  --infile data/processed/unified_build_dataset.csv \
  --outdir outputs/objective1_real
.venv/bin/python src/analysis/association_pvalue_correction.py
.venv/bin/python src/analysis/objective1_temporal_analysis.py \
  --infile data/processed/unified_build_dataset.csv \
  --outdir outputs/objective1_temporal_real
.venv/bin/python src/analysis/objective1_robustness_analysis.py \
  --infile data/processed/unified_build_dataset.csv \
  --outdir outputs/objective1_robustness_real
```

### Expected values (frozen snapshot)

From `outputs/objective1_real/objective1_summary.md` (stratified random holdout,
seed 42, 900 test builds):

| Quantity | Value |
|---|---|
| Records | 3,000 |
| Failure rate | 0.1297 |
| `duration_sec` point-biserial r | 0.2475 (p = 4.16e-43; Holm-significant) |
| `run_attempt` point-biserial r | 0.1413 (p = 7.58e-15; Holm-significant) |
| Other five associations | not significant after Holm correction |
| Logistic ROC-AUC | 0.6160 |
| Failure-class precision / recall / F1 | 0.7333 / 0.0940 / 0.1667 |
| Accuracy | 0.8778 |

Chronological split (oldest 70% train, newest 30% test) and bootstrap /
multi-seed intervals are in
`outputs/objective1_temporal_real/temporal_vs_random_summary.md` and
`outputs/objective1_robustness_real/robustness_summary.md`.

On this snapshot, `duration_sec` and `run_attempt` are the only parameters with
a significant association after Holm correction. Change-scope fields
(`files_changed`, `additions`, `deletions`) are not. Pre-outcome features alone
yield ROC-AUC ≈ 0.52 (random split), which is reported as a leakage check:
duration and retry count are only fully observed after the run.

`total_changes` equals `additions + deletions` on every row. Association tables
keep all seven fields; interpret logistic coefficients with that collinearity in
mind.

### Objectives 2 to 4

```bash
make all-pocs
```

Runs the baseline model, stability metric, and agentic action-selection
prototypes. These are design POCs, not the frozen Objective 1 snapshot.

## Re-collecting live GitHub Actions data

Re-collection replaces the frozen snapshot, so figures will differ.

```bash
cp .env.example .env          # set GITHUB_TOKEN; required for the multi-repo collector
make collect-real-corpus
make objective1-snapshot
```

`src/collect/collect_real_multirepo.py` queries only public repositories and
exits if the token is missing or the API fails. Optional extra sources:

```bash
make objective1-travis TRAVIS_FILE=/absolute/path/to/travistorrent.csv
make objective1-gharchive GH_HOUR=2025-01-01-0
```

## Key outputs

| Artifact | Path |
|---|---|
| Analysis summary | `outputs/objective1_real/objective1_summary.md` |
| Parameter associations | `outputs/objective1_real/parameter_association.csv` |
| Holm / BH-corrected p-values | `outputs/objective1_real/parameter_association_corrected.csv` |
| Logistic coefficients | `outputs/objective1_real/logistic_feature_importance.csv` |
| Association figure | `outputs/objective1_real/association_plot.png` |
| Chronological vs random split | `outputs/objective1_temporal_real/temporal_vs_random_summary.md` |
| Leakage ablation, CIs, 30 seeds | `outputs/objective1_robustness_real/robustness_summary.md` |
| Source catalog | `data/DATA_SOURCES_CATALOG.md` |

## Interactive demo

Open `visualization/index.html` in a browser, or serve it locally:

```bash
python3 -m http.server 8000 --directory visualization
```

It is self-contained. Hero KPIs and Objective 1 charts follow the frozen
3,000-run snapshot. The agentic loop (Objectives 3–4) remains a live
calculator over the prototype formulae in `src/poc/`.

## License

Released under the MIT License. See [LICENSE](LICENSE).
