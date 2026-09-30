# Milestone 5e2: rtn_cmov Feature + Cross-Program Validation

## Date
2026-10-01

## Goal
Test optimization-shaped `rtn_cmov` feature (count of CMOVcc instructions
in enclosing function) for cross-program generalization.

## Engineering Work

### Fixed PIN crash
Runtime `RTN_InsHead`/`INS_Next`/`INS_Mnemonic` calls crash PIN 2.14.
Replaced with instrumentation-time caching:
- Registered `RTN_AddInstrumentFunction` callback
- Counts cmovs once per RTN at instrument time
- Runtime `getRtnCmovCount()` does only a map lookup

### Fixed QSYM Python race condition
QSYM's `afl.py get_score()` stat'd AFL queue files that could be
deleted mid-iteration (OSError). Wrapped `os.path.getsize()` in
try/except, returning 0 for missing files.

### Added QSYM restart wrapper
`/workspace/run_qsym_loop.sh` restarts QSYM on crash. NOTE: this
corrupted the data regime (repeated seed processing). Use only as
fallback — do not use during experiments.

## Data (3-minute runs per target)

| Target | Candidates | Interesting % |
|:---|:---:|:---:|
| zlib minigzip -d | 335 | 24% |
| libpng fuzz_stdin | 723 | 43% |

## Class Means

| Feature | zlib int/rej | libpng int/rej |
|:---|:---|:---|
| path_length | 12.71 / 6.05 | 57.25 / 15.90 |
| branch_hit_count | 1.37 / 11.58 | 3.97 / 8.38 |
| rtn_cmov | 9.52 / 7.70 | 0.52 / 1.20 |

## Cross-Program AUROC

| Model | z->l | l->z |
|:---|:---:|:---:|
| path_length | 0.891 | 0.846 |
| branch_hit_count | 0.770 | 0.941 |
| rtn_cmov | 0.381 | 0.409 |
| Baseline (path+hit) | 0.909 | 0.941 |
| Baseline + rtn_cmov | 0.910 | 0.936 |

## Verdict

**rtn_cmov fails to generalize.** AUROC 0.381/0.409 is below random.
Adding it to the baseline slightly HURTS performance.

This is the THIRD optimization-shaped feature tested (rtn_offset,
rtn_size, rtn_cmov) — all three fail to generalize.

## Paper Impact

The paper's original thesis ("optimization-aware features improve
DSE scheduling") is empirically falsified at the binary-only cross-
program level. Three independent feature families tested.

## Positive Result Retained

Baseline (path_length + branch_hit_count) achieves cross-program AUROC
0.909/0.941 — strong, bidirectional, competitive with MEUZZ.

## Next
Decide paper scope: pivot to empirical study of which features generalize.

## Evidence
- milestone_5e2_rtn_cmov/*.csv
- milestone_5e2_rtn_cmov/solver.cpp.patched (final instrumented version)
- milestone_5e2_rtn_cmov/cross_5e2_clean.py
