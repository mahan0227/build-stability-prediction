from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(".mplconfig").resolve()))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pointbiserialr
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


def _safe_point_biserial(x: pd.Series, y: pd.Series) -> tuple[float, float]:
    xx = pd.to_numeric(x, errors="coerce")
    yy = pd.to_numeric(y, errors="coerce")
    mask = xx.notna() & yy.notna()
    if mask.sum() < 10 or yy[mask].nunique() < 2:
        return np.nan, np.nan
    corr, pvalue = pointbiserialr(xx[mask], yy[mask])
    return float(corr), float(pvalue)


def main() -> None:
    parser = argparse.ArgumentParser(description="Objective 1: Parameter-outcome relationship analysis.")
    parser.add_argument("--infile", default="data/processed/unified_build_dataset.csv")
    parser.add_argument("--outdir", default="outputs/objective1")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.infile)
    if "is_failed" not in df.columns:
        raise ValueError("Expected 'is_failed' column in unified dataset.")

    stats_rows: list[dict[str, float | str]] = []
    for feature in FEATURES:
        corr, pvalue = _safe_point_biserial(df[feature], df["is_failed"])
        stats_rows.append({"feature": feature, "point_biserial_corr": corr, "p_value": pvalue})

    assoc = pd.DataFrame(stats_rows).sort_values(by="point_biserial_corr", key=lambda s: s.abs(), ascending=False)
    assoc.to_csv(outdir / "parameter_association.csv", index=False)

    modeling_df = df[FEATURES + ["is_failed"]].dropna().copy()
    if len(modeling_df) < 40:
        raise ValueError("Not enough rows after cleaning for modeling. Collect more data.")

    X = modeling_df[FEATURES]
    y = modeling_df["is_failed"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=42, stratify=y)
    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )
    model.fit(X_train, y_train)
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    auc = roc_auc_score(y_test, y_prob)
    report = classification_report(y_test, y_pred, digits=4)

    coefs = model.named_steps["clf"].coef_[0]
    coef_df = pd.DataFrame({"feature": FEATURES, "logistic_coef": coefs}).sort_values(
        by="logistic_coef", key=lambda s: s.abs(), ascending=False
    )
    coef_df.to_csv(outdir / "logistic_feature_importance.csv", index=False)

    # Simple visualization for thesis report.
    plt.figure(figsize=(9, 4.8))
    ordered = assoc.dropna().copy()
    plt.bar(ordered["feature"], ordered["point_biserial_corr"])
    plt.axhline(0, color="black", linewidth=0.8)
    plt.title("Objective 1: Parameter association with CI/CD build failures")
    plt.ylabel("Point-biserial correlation")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(outdir / "association_plot.png", dpi=200)

    summary = (
        "# Objective 1 Analysis Summary\n\n"
        f"- Total records: {len(df)}\n"
        f"- Modeling records after cleaning: {len(modeling_df)}\n"
        f"- Failure rate: {df['is_failed'].mean():.4f}\n"
        f"- Logistic ROC-AUC: {auc:.4f}\n\n"
        "## Top associated parameters (absolute point-biserial)\n\n"
        + assoc.head(5).to_markdown(index=False)
        + "\n\n## Classification report\n\n```\n"
        + report
        + "\n```\n"
    )
    (outdir / "objective1_summary.md").write_text(summary, encoding="utf-8")
    print(f"[OK] Objective 1 outputs written in: {outdir}")


if __name__ == "__main__":
    main()
