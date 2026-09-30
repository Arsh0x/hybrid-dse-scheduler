# Milestone 5c: Cross-Program Generalization

## Date
2026-09-30

## Goal
Test whether pre-solve features generalize across structurally different binaries.

## Targets
- zlib 1.3.1 (minigzip -d, gzip decompression)
- libpng 1.6.43 (custom fuzz_stdin, PNG decode)

## Data

| Target | Candidates | Solver rows | Interesting % |
|:---|:---:|:---:|:---:|
| zlib | 351 | 351 | 25% |
| libpng | 640 | 14,804 | 43% |

## Feature Distributions

| Feature | zlib (min,max,mean) | libpng (min,max,mean) |
|:---|:---|:---|
| path_length | 1, 24, 7.7 | 1, 126, 28.0 |
| symbolized_bytes | 1, 6, 1.56 | 1, 40, 2.46 |
| constraint_count | 0, 46, 0.58 | 0, 63, 1.98 |

## Class Separation

### path_length (generalizes)
| Target | Interesting mean | Rejected mean | Ratio |
|:---|:---:|:---:|:---:|
| zlib | 13.14 | 5.97 | 2.20x |
| libpng | 45.41 | 14.60 | 3.11x |

### symbolized_bytes (does NOT generalize)
| Target | Interesting mean | Rejected mean | Direction |
|:---|:---:|:---:|:---|
| zlib | 2.29 | 1.32 | int > rej |
| libpng | 2.12 | 2.71 | rej > int (REVERSED) |

### constraint_count (QSYM artifact)
- All rejected rows have constraint_count = 0
- All interesting rows have constraint_count >= 0 (mostly > 0)
- Cross-program AUROC 1.000 (perfect separation = red flag)

## Cross-Program AUROC

| Feature set | zlib->libpng | libpng->zlib |
|:---|:---:|:---:|
| path_length | 0.892 | 0.899 |
| symbolized_bytes | 0.632 | N/A |
| path_length + symbolized_bytes | 0.887 | 0.821 |
| constraint_count | 1.000 | N/A |

## Findings

1. **path_length generalizes bidirectionally (AUROC ~0.89).**
   Real structural signal, not target-specific.

2. **symbolized_bytes does NOT generalize (AUROC 0.63, direction reverses).**
   Target-specific artifact: libpng's chunk-length checks correlate with high
   symbolized_bytes on rejected branches; zlib doesn't have this pattern.

3. **constraint_count is a QSYM structural artifact.**
   Constraint accumulation only happens after interesting branches, creating
   a label proxy. Not usable as a feature.

## Implications for Paper

- Positive result: pre-solve features can predict DSE utility cross-program.
- Negative result: not all "obvious" features generalize — motivates
  optimization-aware feature design.
- Methodological finding: QSYM's internal state has hidden biases that must
  be audited before feature engineering.

## What's Needed Next

At least 2 more features that generalize to defend the paper's ML story.
Candidates:
- branch_hit_count (history)
- prev_sat / prev_unsat / prev_timeout (history)
- superblock geometry (optimization-shaped)
- jump_table_member (optimization-shaped)

## Evidence
- milestone_5c_cross_program/*.csv
- milestone_5c_cross_program/cross_program.py

## Next
Milestone 5d: implement history + optimization features, re-run cross-program
generalization test on the full feature set.
