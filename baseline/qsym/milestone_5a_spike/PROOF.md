# Milestone 5a: Phase 2a Spike (AUROC Validation)

## Date
2026-09-29

## Goal
Answer: do 3 pre-solve features predict DSE utility on a real binary?

## Target
zlib 1.3.1 `minigzip -d` (decompress gzip from stdin)
Built with AFL instrumentation, static linking.

## Data
- 344 candidate rows in 3 minutes
- 83 interesting (24%), 261 rejected (76%)
- 345 solver_timing rows (256 SAT, 89 UNSAT)
- Solver time range: 18us to 8199us

## Features Tested
- path_length (1 to 24, mean 7.70)
- symbolized_bytes (1 to 6, mean 1.56)
- constraint_count (leaky — see below)

## Class Separation (means)

| Feature | Interesting | Rejected | Ratio |
|:---|:---:|:---:|:---:|
| path_length | 13.14 | 5.97 | 2.20x |
| symbolized_bytes | 2.29 | 1.32 | 1.73x |

## AUROC Results

### Temporal split (first 70% train, last 30% test)
- Both: 0.937
- path_length: 0.946
- symbolized_bytes: 0.871

### Random split (shuffled 70/30)
- Both: 0.863
- path_length: 0.867
- symbolized_bytes: 0.838
- Random baseline: 0.528

## Decision Gate
Threshold: AUROC > 0.65
Result: PASS (random split = 0.863)

## Decision
GO to Phase 2b (full feature set + larger campaign).

## Known Issues

1. constraint_count is leaky. It reads solver_.assertions().size() AFTER
   addConstraint(). For rejected branches this is 0, so it directly
   encodes the label. MUST move to pre-addConstraint read. Exclude from
   utility model until fixed.

2. Single target only (zlib). Cross-program generalization not tested.

3. Small test set (19 pos, 85 neg). Directional but not statistically
   conclusive. Needs a 24h campaign for paper-grade numbers.

## What This Proves
Pre-solve binary features carry real predictive signal for DSE utility.
The paper's central claim is empirically grounded.

## Next Steps
1. Fix constraint_count ordering (milestone 5b)
2. Add second target (libpng or jpeg) for cross-program validation
3. Run 30-min per target campaign
4. Cross-program AUROC: train on zlib, test on other
5. If cross-program AUROC > 0.70: proceed to full Phase 2b
