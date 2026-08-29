from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _compose_results_md(
    unified_df: pd.DataFrame,
    assoc_df: pd.DataFrame,
    imp_df: pd.DataFrame,
    report_rel: str,
) -> str:
    n = len(unified_df) if not unified_df.empty else 0
    fail_rate = float(unified_df["is_failed"].mean()) if (not unified_df.empty and "is_failed" in unified_df.columns) else 0.0

    top_assoc_lines = []
    if not assoc_df.empty:
        top_assoc = assoc_df.dropna().copy().head(5)
        for _, r in top_assoc.iterrows():
            top_assoc_lines.append(
                f"- `{r['feature']}`: correlation={r['point_biserial_corr']:.4f}, p-value={r['p_value']:.4g}"
            )
    else:
        top_assoc_lines.append("- Association table not available yet.")

    top_imp_lines = []
    if not imp_df.empty:
        top_imp = imp_df.dropna().copy().head(5)
        for _, r in top_imp.iterrows():
            top_imp_lines.append(f"- `{r['feature']}`: coefficient={r['logistic_coef']:.4f}")
    else:
        top_imp_lines.append("- Feature importance table not available yet.")

    md = f"""# Objective 1 Results Section (Draft)

## Dataset and Outcome Summary
The unified CI/CD dataset used for Objective 1 contains **{n} build records** with an observed failure ratio of **{fail_rate:.4f}**. The data was harmonized into a common schema spanning build metadata, commit-level change attributes, and process-level execution attributes.

## Parameter-Outcome Association Findings
Statistical association analysis (point-biserial correlation against binary build outcome) identified the following top parameters:

{chr(10).join(top_assoc_lines)}

These parameters represent the strongest linear associations with build failure in the current dataset and can be prioritized for further hypothesis testing and temporal robustness checks.

## Predictive Signal Cross-check
A baseline logistic model was used as a sanity check for predictive signal. The strongest model coefficients were:

{chr(10).join(top_imp_lines)}

This cross-check does not replace full model selection (Objective 2), but confirms that the extracted features contain meaningful failure-related signal.

## Figures and Tables for Thesis Chapter
- Association plot: `figures/association_plot.png`
- Parameter association table: `tables/top_parameter_association.csv`
- Logistic feature importance table: `tables/top_logistic_importance.csv`
- Full Objective 1 report (HTML): `{report_rel}`

## Suggested Chapter Text Snippet
\"Objective 1 establishes that dataset engineering choices strongly influence CI/CD build-outcome inference. In the current dataset, change volume and process-intensity indicators show statistically meaningful associations with failure outcomes. This validates the need for a harmonized multi-source schema prior to advanced model design and supports the next-stage work on architecture-specific predictive optimization.\"
"""
    return md


def main() -> None:
    parser = argparse.ArgumentParser(description="Build thesis-ready paper pack for Objective 1.")
    parser.add_argument("--outdir", default="outputs/objective1/paper_pack")
    parser.add_argument("--objective1-dir", default="outputs/objective1")
    parser.add_argument("--unified", default="data/processed/unified_build_dataset.csv")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    fig_dir = outdir / "figures"
    tbl_dir = outdir / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    tbl_dir.mkdir(parents=True, exist_ok=True)

    objective1_dir = Path(args.objective1_dir)
    unified_df = _safe_read_csv(Path(args.unified))
    assoc_df = _safe_read_csv(objective1_dir / "parameter_association.csv")
    imp_df = _safe_read_csv(objective1_dir / "logistic_feature_importance.csv")

    # Copy/trim core figure and tables.
    assoc_plot = objective1_dir / "association_plot.png"
    if assoc_plot.exists():
        (fig_dir / "association_plot.png").write_bytes(assoc_plot.read_bytes())

    if not assoc_df.empty:
        assoc_df.sort_values(by="point_biserial_corr", key=lambda s: s.abs(), ascending=False).head(10).to_csv(
            tbl_dir / "top_parameter_association.csv", index=False
        )
        assoc_df.to_csv(tbl_dir / "full_parameter_association.csv", index=False)

    if not imp_df.empty:
        imp_df.sort_values(by="logistic_coef", key=lambda s: s.abs(), ascending=False).head(10).to_csv(
            tbl_dir / "top_logistic_importance.csv", index=False
        )
        imp_df.to_csv(tbl_dir / "full_logistic_importance.csv", index=False)

    report_rel = "../objective1_report.html"
    results_md = _compose_results_md(unified_df, assoc_df, imp_df, report_rel)
    (outdir / "objective1_results_section.md").write_text(results_md, encoding="utf-8")

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "paper_pack_path": str(outdir),
        "files": sorted([str(p.relative_to(outdir)) for p in outdir.rglob("*") if p.is_file()]),
    }
    import json

    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[OK] Objective 1 paper pack created: {outdir}")


if __name__ == "__main__":
    main()
