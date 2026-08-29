"""Leakage-aware ablation and uncertainty quantification for the logistic baseline.

Addresses two reviewer concerns in one protocol:

1. Leakage analysis: features are classified by availability time relative to
   the outcome. Change-scope fields (additions, deletions, total_changes,
   files_changed, commit_message_len) are fixed at commit time, before any
   build starts. duration_sec is only observable once the run completes, and
   run_attempt increments through retries that may themselves be triggered by
   failure; both are therefore excluded from the pre-outcome feature set.
   The model is evaluated with the full set and the pre-outcome-only set.

2. Uncertainty: for each configuration we report (a) a percentile bootstrap
   95% CI on the held-out test set for ROC-AUC and failure-class F1, and
   (b) mean +/- SD over repeated random stratified splits with 30 seeds.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(".mplconfig").resolve()))

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ALL_FEATURES = [
    "duration_sec",
    "commit_message_len",
    "additions",
    "deletions",
    "total_changes",
    "files_changed",
    "run_attempt",
]

# Available at commit/trigger time, strictly before the build outcome exists.
PRE_OUTCOME_FEATURES = [
    "commit_message_len",
    "additions",
    "deletions",
    "total_changes",
    "files_changed",
]

TIME_COLUMNS = ["run_started_at", "created_at", "started_at", "commit_timestamp", "timestamp"]

N_BOOTSTRAP = 2000
N_SEEDS = 30
RNG = np.random.default_rng(12345)


def make_model() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000)),
    ])


def evaluate(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    y_pred = (y_prob >= 0.5).astype(int)
    return {
        "auc": roc_auc_score(y_true, y_prob),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }


def bootstrap_ci(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    aucs, f1s = [], []
    n = len(y_true)
    for _ in range(N_BOOTSTRAP):
        idx = RNG.integers(0, n, n)
        yt, yp = y_true[idx], y_prob[idx]
        if yt.min() == yt.max():
            continue
        aucs.append(roc_auc_score(yt, yp))
        f1s.append(f1_score(yt, (yp >= 0.5).astype(int), zero_division=0))
    return {
        "auc_ci": (float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))),
        "f1_ci": (float(np.percentile(f1s, 2.5)), float(np.percentile(f1s, 97.5))),
    }


def run_config(df: pd.DataFrame, features: list[str], time_col: str, test_size: float) -> dict:
    X_all = df[features]
    y_all = df["is_failed"].astype(int)

    out: dict = {}

    # Single random stratified holdout (seed 42, as published).
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_all, y_all, test_size=test_size, random_state=42, stratify=y_all
    )
    model = make_model().fit(X_tr, y_tr)
    prob = model.predict_proba(X_te)[:, 1]
    out["random"] = evaluate(y_te.to_numpy(), prob) | bootstrap_ci(y_te.to_numpy(), prob)

    # Chronological split.
    s = df.sort_values(time_col).reset_index(drop=True)
    k = int(round(len(s) * (1 - test_size)))
    model = make_model().fit(s[features].iloc[:k], s["is_failed"].iloc[:k].astype(int))
    y_te_c = s["is_failed"].iloc[k:].astype(int).to_numpy()
    prob_c = model.predict_proba(s[features].iloc[k:])[:, 1]
    out["chronological"] = evaluate(y_te_c, prob_c) | bootstrap_ci(y_te_c, prob_c)

    # Multi-seed random splits: mean +/- SD.
    metrics = {m: [] for m in ("auc", "precision", "recall", "f1")}
    for seed in range(N_SEEDS):
        X_tr, X_te, y_tr, y_te = train_test_split(
            X_all, y_all, test_size=test_size, random_state=seed, stratify=y_all
        )
        model = make_model().fit(X_tr, y_tr)
        res = evaluate(y_te.to_numpy(), model.predict_proba(X_te)[:, 1])
        for m in metrics:
            metrics[m].append(res[m])
    out["multiseed"] = {
        m: (float(np.mean(v)), float(np.std(v))) for m, v in metrics.items()
    }
    return out


def fmt_block(name: str, r: dict) -> str:
    lines = [f"## {name}\n"]
    for split in ("random", "chronological"):
        d = r[split]
        lines.append(
            f"**{split.capitalize()} split (seed-42 holdout / fixed 70-30 boundary):** "
            f"AUC {d['auc']:.4f} (95% CI {d['auc_ci'][0]:.4f}-{d['auc_ci'][1]:.4f}), "
            f"failure precision {d['precision']:.4f}, recall {d['recall']:.4f}, "
            f"F1 {d['f1']:.4f} (95% CI {d['f1_ci'][0]:.4f}-{d['f1_ci'][1]:.4f})\n"
        )
    ms = r["multiseed"]
    lines.append(
        f"**Random splits over {N_SEEDS} seeds (mean +/- SD):** "
        f"AUC {ms['auc'][0]:.4f} +/- {ms['auc'][1]:.4f}, "
        f"failure precision {ms['precision'][0]:.4f} +/- {ms['precision'][1]:.4f}, "
        f"recall {ms['recall'][0]:.4f} +/- {ms['recall'][1]:.4f}, "
        f"F1 {ms['f1'][0]:.4f} +/- {ms['f1'][1]:.4f}\n"
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Leakage ablation and uncertainty analysis.")
    parser.add_argument("--infile", default="data/processed/unified_build_dataset.csv")
    parser.add_argument("--outdir", default="outputs/objective1_robustness")
    parser.add_argument("--test-size", type=float, default=0.30)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.infile)
    time_col = next(c for c in TIME_COLUMNS if c in df.columns)
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce", utc=True)
    df = df[ALL_FEATURES + ["is_failed", time_col]].dropna().copy()

    full = run_config(df, ALL_FEATURES, time_col, args.test_size)
    pre = run_config(df, PRE_OUTCOME_FEATURES, time_col, args.test_size)

    summary = (
        "# Leakage-Aware Ablation and Uncertainty Analysis\n\n"
        f"- Records: {len(df)}, overall failure rate {df['is_failed'].mean():.4f}\n"
        f"- Full feature set: {ALL_FEATURES}\n"
        f"- Pre-outcome feature set (excludes duration_sec, run_attempt): {PRE_OUTCOME_FEATURES}\n"
        f"- Bootstrap reps: {N_BOOTSTRAP}, multi-seed repeats: {N_SEEDS}\n\n"
        + fmt_block("Full feature set (includes post-outcome-ambiguous fields)", full)
        + "\n"
        + fmt_block("Pre-outcome features only (decision-time safe)", pre)
    )
    (outdir / "robustness_summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    print(f"[OK] Written to: {outdir / 'robustness_summary.md'}")


if __name__ == "__main__":
    main()
