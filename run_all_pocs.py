from __future__ import annotations

import os
import subprocess
import sys


def run(cmd: list[str]) -> None:
    print(f"[RUN] {' '.join(cmd)}")
    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", str((os.getcwd() + "/.mplconfig")))
    subprocess.run(cmd, check=True, env=env)


def main() -> None:
    py = sys.executable
    run([py, "src/collect/github_actions_collector.py", "--max-runs-per-repo", "50"])
    run([py, "src/schema/unify_schema.py"])
    run([py, "src/analysis/objective1_parameter_analysis.py"])
    run([py, "src/poc/objective2_model_poc.py"])
    run([py, "src/poc/objective3_metric_poc.py"])
    run([py, "src/poc/objective4_agentic_framework_poc.py"])
    print("[OK] All POCs completed. Check outputs/ directory.")


if __name__ == "__main__":
    main()
