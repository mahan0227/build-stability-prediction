from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split


FEATURES = ["duration_sec", "additions", "deletions", "total_changes", "files_changed", "run_attempt", "commit_message_len"]


def main() -> None:
    parser = argparse.ArgumentParser(description="POC for Objective 2: baseline model design.")
    parser.add_argument("--infile", default="data/processed/unified_build_dataset.csv")
    parser.add_argument("--out", default="outputs/objective2_model_poc.md")
    args = parser.parse_args()

    df = pd.read_csv(args.infile)
    df = df[FEATURES + ["is_failed"]].dropna()
    X = df[FEATURES]
    y = df["is_failed"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    clf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    clf.fit(X_train, y_train)
    prob = clf.predict_proba(X_test)[:, 1]
    pred = (prob >= 0.5).astype(int)

    f1 = f1_score(y_test, pred)
    auc = roc_auc_score(y_test, prob)
    importances = pd.DataFrame({"feature": FEATURES, "importance": clf.feature_importances_}).sort_values(
        "importance", ascending=False
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_text = (
        "# Objective 2 POC (Baseline Model)\n\n"
        f"- Records used: {len(df)}\n"
        f"- F1 score: {f1:.4f}\n"
        f"- ROC-AUC: {auc:.4f}\n\n"
        "## Feature importances\n\n"
        + importances.to_markdown(index=False)
        + "\n"
    )
    out_path.write_text(out_text, encoding="utf-8")
    print(f"[OK] Objective 2 POC output: {out_path}")


if __name__ == "__main__":
    main()
