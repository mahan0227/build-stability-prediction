# Leakage-Aware Ablation and Uncertainty Analysis

- Records: 3000, overall failure rate 0.1297
- Full feature set: ['duration_sec', 'commit_message_len', 'additions', 'deletions', 'total_changes', 'files_changed', 'run_attempt']
- Pre-outcome feature set (excludes duration_sec, run_attempt): ['commit_message_len', 'additions', 'deletions', 'total_changes', 'files_changed']
- Bootstrap reps: 2000, multi-seed repeats: 30

## Full feature set (includes post-outcome-ambiguous fields)

**Random split (seed-42 holdout / fixed 70-30 boundary):** AUC 0.6160 (95% CI 0.5526-0.6777), failure precision 0.7333, recall 0.0940, F1 0.1667 (95% CI 0.0840-0.2520)

**Chronological split (seed-42 holdout / fixed 70-30 boundary):** AUC 0.6886 (95% CI 0.6114-0.7598), failure precision 0.0000, recall 0.0000, F1 0.0000 (95% CI 0.0000-0.0000)

**Random splits over 30 seeds (mean +/- SD):** AUC 0.6274 +/- 0.0292, failure precision 0.6079 +/- 0.1180, recall 0.0587 +/- 0.0183, F1 0.1062 +/- 0.0307

## Pre-outcome features only (decision-time safe)

**Random split (seed-42 holdout / fixed 70-30 boundary):** AUC 0.5197 (95% CI 0.4620-0.5751), failure precision 0.0000, recall 0.0000, F1 0.0000 (95% CI 0.0000-0.0000)

**Chronological split (seed-42 holdout / fixed 70-30 boundary):** AUC 0.4684 (95% CI 0.3809-0.5587), failure precision 0.0000, recall 0.0000, F1 0.0000 (95% CI 0.0000-0.0000)

**Random splits over 30 seeds (mean +/- SD):** AUC 0.5146 +/- 0.0272, failure precision 0.0000 +/- 0.0000, recall 0.0000 +/- 0.0000, F1 0.0000 +/- 0.0000
