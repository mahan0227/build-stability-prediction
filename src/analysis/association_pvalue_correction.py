"""Holm and Benjamini-Hochberg corrections for Objective 1 association tests."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def holm_bh(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    m = len(p)
    order = np.argsort(p)
    holm = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        holm[i] = min(running, 1.0)

    bh = np.empty(m)
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        prev = min(prev, p[i] * m / (rank + 1))
        bh[i] = prev
    return holm, bh


def main() -> None:
    parser = argparse.ArgumentParser(description="Multiple-testing correction for association p-values.")
    parser.add_argument("--infile", default="outputs/objective1_real/parameter_association.csv")
    parser.add_argument("--outfile", default="outputs/objective1_real/parameter_association_corrected.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.infile)
    p = df["p_value"].to_numpy(dtype=float)
    holm, bh = holm_bh(p)
    out = df.copy()
    out["holm"] = holm
    out["bh"] = bh
    Path(args.outfile).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.outfile, index=False)

    print(f"{'feature':<20}{'raw p':>12}{'Holm':>12}{'BH (FDR)':>12}  sig@0.05(Holm)")
    for row in out.itertuples(index=False):
        flag = "yes" if row.holm < 0.05 else "no"
        print(f"{row.feature:<20}{row.p_value:>12.4g}{row.holm:>12.4g}{row.bh:>12.4g}  {flag}")
    print(f"[OK] Written {args.outfile}")


if __name__ == "__main__":
    main()
