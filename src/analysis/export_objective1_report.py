from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _fallback_html(out_html: Path) -> None:
    summary_md = Path("outputs/objective1/objective1_summary.md")
    assoc_csv = Path("outputs/objective1/parameter_association.csv")
    importance_csv = Path("outputs/objective1/logistic_feature_importance.csv")
    plot_path = Path("outputs/objective1/association_plot.png")

    assoc_tbl = ""
    imp_tbl = ""
    if assoc_csv.exists():
        assoc_tbl = pd.read_csv(assoc_csv).head(10).to_html(index=False)
    if importance_csv.exists():
        imp_tbl = pd.read_csv(importance_csv).head(10).to_html(index=False)

    summary_text = summary_md.read_text(encoding="utf-8") if summary_md.exists() else "Objective 1 summary not found."
    summary_html = "<br/>".join(summary_text.splitlines())

    img_html = f'<img src="../{plot_path.as_posix()}" style="max-width:780px;">' if plot_path.exists() else ""
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Objective 1 Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 28px; }}
    h1,h2 {{ color: #1d3b6f; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 13px; }}
    th {{ background: #f0f5ff; }}
    .box {{ background: #fafafa; border: 1px solid #eee; padding: 12px; }}
  </style>
</head>
<body>
  <h1>Objective 1 Statistical Report</h1>
  <p>Generated from unified CI/CD dataset.</p>
  <h2>Executive Summary</h2>
  <div class="box">{summary_html}</div>
  <h2>Association Plot</h2>
  {img_html}
  <h2>Top Parameter Associations</h2>
  {assoc_tbl}
  <h2>Logistic Feature Importance</h2>
  {imp_tbl}
</body>
</html>"""
    out_html.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Objective 1 report as HTML/PDF.")
    parser.add_argument("--notebook", default="notebooks/objective1_eda.ipynb")
    parser.add_argument("--html-out", default="outputs/objective1/objective1_report.html")
    parser.add_argument("--pdf-out", default="outputs/objective1/objective1_report.pdf")
    args = parser.parse_args()

    html_out = Path(args.html_out)
    pdf_out = Path(args.pdf_out)
    html_out.parent.mkdir(parents=True, exist_ok=True)

    jupyter = shutil.which("jupyter")
    if jupyter:
        try:
            _run(
                [
                    jupyter,
                    "nbconvert",
                    "--to",
                    "html",
                    "--execute",
                    "--output",
                    html_out.name,
                    "--output-dir",
                    str(html_out.parent),
                    args.notebook,
                ]
            )
            print(f"[OK] Notebook HTML report exported: {html_out}")
        except Exception as exc:
            print(f"[WARN] Jupyter export failed: {exc}")
            _fallback_html(html_out)
            print(f"[OK] Fallback HTML report exported: {html_out}")
    else:
        _fallback_html(html_out)
        print(f"[OK] Fallback HTML report exported: {html_out}")

    # Try PDF export if jupyter exists and has webpdf support; otherwise skip cleanly.
    if jupyter:
        try:
            _run(
                [
                    jupyter,
                    "nbconvert",
                    "--to",
                    "webpdf",
                    "--execute",
                    "--output",
                    pdf_out.name,
                    "--output-dir",
                    str(pdf_out.parent),
                    args.notebook,
                ]
            )
            print(f"[OK] PDF report exported: {pdf_out}")
        except Exception:
            print("[INFO] PDF export skipped (webpdf toolchain not available).")
    else:
        print("[INFO] PDF export skipped (jupyter not installed).")


if __name__ == "__main__":
    main()
