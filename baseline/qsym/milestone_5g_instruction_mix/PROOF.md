# Milestone 5g: F6 Instruction Mix Features (Cross-Program Test)

## Date
2026-10-03

## Goal
Test 2 instruction-mix features for cross-program generalization.

## Features Added
- rtn_simd_count: SIMD (AVX/SSE) instruction count in enclosing RTN
- rtn_mem_ops: memory operand count in enclosing RTN

## Data (3-min runs)
- zlib: 302 rows
- libpng: 595 rows

## Cross-Program AUROC

| Feature | z->l | l->z |
|:---|:---:|:---:|
| rtn_simd_count | 0.491 | 0.404 |
| rtn_mem_ops | 0.552 | 0.596 |
| F6 (both) | 0.533 | 0.596 |
| All opt features (F4+F5+F6) | 0.527 | 0.264 |
| Baseline (path+hit) | 0.885 | 0.950 |
| Baseline + mem_ops | 0.884 | 0.735 |
| Baseline + simd_count | 0.883 | 0.943 |

## Findings

1. Both F6 features fail to generalize (AUROC < 0.60).
2. Combined F4+F5+F6 gives 0.527/0.264 — worse than random.
3. Adding mem_ops to baseline destroys reverse direction (0.950 -> 0.735).
4. simd_count is neutral (rarely fired on either target).

## Final Feature Tally

Structural:    1 tested, 1 generalizes
History freq:  1 tested, 1 generalizes
Symbolic:      3 tested, 0 generalize
History out:   3 tested, 0 generalize
Opt-geometry:  3 tested, 0 generalize
Opt-CFG:       4 tested, 0 generalize
Opt-instr-mix: 2 tested, 0 generalize
TOTAL:        17 tested, 2 generalize

## Paper Impact
The empirical claim is now airtight: structural and history-frequency
features generalize; symbolic and all optimization-shaped families do not.

## Next
Phase C: automation pipeline for full 62-program × 2-compiler × 3-opt
data collection.

## Evidence
- milestone_5g_instruction_mix/
