"""Chronological-split evaluation for the logistic baseline.

Executes the time-aware protocol specified in the manuscript (Figure 5):
records are ordered by event time, the oldest 70% form the training window,
and the most recent 30% form the test window. The random stratified holdout
is re-run on the same modeling frame so both results can be reported side
by side (random vs chronological) with per-split class ratios.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(".mplconfig").resolve()))

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = [
    "duration_sec",
    "commit_message_len",
    "additions",
    "deletions",
    "total_changes",
    "files_changed",
    "run_attempt",
]

# Candidate event-time columns, in order of preference.
TIME_COLUMNS = [
    "run_started_at",
    "created_at",
    "started_at",
    "commit_timestamp",
    "timestamp",
    "run_created_at",
]


def find_time_column(df: pd.DataFrame) -> str:
    for col in TIME_COLUMNS:
        if col in df.columns:
            return col
    raise ValueError(
        f"No event-time column found. Looked for {TIME_COLUMNS}. "
        f"Available columns: {list(df.columns)}"
    )


def fit_and_evaluate(X_train, y_train, X_test, y_test) -> dict:
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    model.fit(X_train, y_train)
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    return {
        "auc": roc_auc_score(y_test, y_prob),
        "report": classification_report(y_test, y_pred, digits=4),
        "train_failure_rate": float(y_train.mean()),
        "test_failure_rate": float(y_test.mean()),
        "n_train": len(y_train),
        "n_test": len(y_test),
    }


def format_block(name: str, res: dict) -> str:
    return (
        f"## {name}\n\n"
        f"- Train records: {res['n_train']} (failure rate {res['train_failure_rate']:.4f})\n"
        f"- Test records: {res['n_test']} (failure rate {res['test_failure_rate']:.4f})\n"
        f"- ROC-AUC: {res['auc']:.4f}\n\n"
        f"```\n{res['report']}\n```\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Chronological vs random split evaluation.")
    parser.add_argument("--infile", default="data/processed/unified_build_dataset.csv")
    parser.add_argument("--outdir", default="outputs/objective1_temporal")
    parser.add_argument("--test-size", type=float, default=0.30)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.infile)
    if "is_failed" not in df.columns:
        raise ValueError("Expected 'is_failed' column in unified dataset.")

    time_col = find_time_column(df)
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce", utc=True)

    modeling_df = df[FEATURES + ["is_failed", time_col]].dropna().copy()

    # Random stratified holdout in original row order, exactly reproducing
    # the published baseline (train_test_split, seed 42, stratified).
    X_orig = modeling_df[FEATURES]
    y_orig = modeling_df["is_failed"].astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_orig, y_orig, test_size=args.test_size, random_state=42, stratify=y_orig
    )
    random_res = fit_and_evaluate(X_tr, y_tr, X_te, y_te)

    # Chronological split: oldest records train, newest records test.
    sorted_df = modeling_df.sort_values(time_col).reset_index(drop=True)
    X = sorted_df[FEATURES]
    y = sorted_df["is_failed"].astype(int)
    split_idx = int(round(len(sorted_df) * (1 - args.test_size)))
    chrono = fit_and_evaluate(
        X.iloc[:split_idx], y.iloc[:split_idx],
        X.iloc[split_idx:], y.iloc[split_idx:],
    )
    boundary_time = sorted_df[time_col].iloc[split_idx]

    summary = (
        "# Temporal vs Random Split Evaluation\n\n"
        f"- Modeling records: {len(sorted_df)}\n"
        f"- Event-time column: `{time_col}`\n"
        f"- Chronological boundary: {boundary_time}\n"
        f"- Overall failure rate: {y.mean():.4f}\n\n"
        + format_block("Chronological split (oldest 70% train, newest 30% test)", chrono)
        + "\n"
        + format_block("Random stratified holdout (seed 42)", random_res)
    )
    (outdir / "temporal_vs_random_summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    print(f"[OK] Written to: {outdir / 'temporal_vs_random_summary.md'}")


if __name__ == "__main__":
    main()
