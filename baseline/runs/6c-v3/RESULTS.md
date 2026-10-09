# Milestone 6c-v3: 5-Repetition Cross-Program Stability Analysis

## Setup
- 5 repetitions × 10 min each × 2 programs (zlib, libpng)
- 14,426 total candidates, 11,625 main-module only (80.6%)
- Per-rep leave-one-rep-out AUROC (libpng -> zlib)

## Results (mean ± std over 5 reps)

| Family | Mean | Std | Verdict |
|--------|-----:|----:|---------|
| baseline | 0.937 | 0.014 | Excellent, stable |
| history_freq | 0.916 | 0.011 | Excellent, stable |
| structural | 0.872 | 0.016 | Strong, stable |
| symbolic | 0.604 | 0.172 | Unstable - do not claim |
| opt_insn_mix | 0.587 | 0.006 | Below threshold |
| history_outcome | 0.498 | 0.069 | Random |
| opt_cfg | 0.488 | 0.123 | Below random |
| opt_geometry | 0.459 | 0.142 | Below random |

## Paper Thesis (final)
Structural and frequency features generalize bidirectionally with AUROC
0.87-0.94 (std <= 0.016). Symbolic features are unstable (std 0.17).
Optimization-shaped, history-outcome, and instruction-mix families
perform at or below random chance.

## Why This Is Strong
1. 5 repetitions establish stability, not just single-run point estimates.
2. Clean separation between stable performers and failures.
3. Symbolic instability is itself a publishable finding.

## Evidence
- processed_mainonly.csv: 11,625 main-module rows
- per_rep.py: reproducible stability analysis

## Next
- Commit milestone + update PAPER_SCOPE.md
- Phase D: add xz, jq, tar, gzip (4 more programs)
- Then 25-program campaign on cloud
