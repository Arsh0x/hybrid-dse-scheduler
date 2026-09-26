# Phase 2 Plan: Dataset V1 (Spike-First)

**Date:** 2026-09-27
**Status:** Ready to start
**Duration:** ~3 weeks (adjusted from original 4)

## Why Spike-First

Original plan: add all ~10 features, then train models.

New plan: **validate 3 features predict signal before investing in 7 more.**

Rationale from literature review (Consensus report, 2026-09-26):
- Generalization is the biggest risk (Jiang et al. ICSE 2023)
- No paper has validated which binary-only features predict DSE utility/cost
- Rebuild-and-test cycle for QSYM patches is ~10 min each
- Adding 10 features blindly = ~2 hours of churn before knowing if any work

**Spike-first hedge:** 4 days to get an AUROC signal, then decide.

## Phase 2a: Spike (Days 1-4)

### Goal
Answer one question: **do 3 pre-solve features predict DSE utility and cost on a real binary?**

### Features to Add
1. `constraint_count` — done in Milestone 4d
2. `path_length` — number of branches in current trace
3. `symbolized_bytes` — taint slice width for this PC

### Data Collection
- Target: `zlib` (small, fast, real-world, has magic bytes + checksums)
- Runtime: 30-60 minutes of hybrid fuzzing
- Expected: 10k-100k candidate rows, 1k-5k solver_timing rows

### Models to Train
- **Utility model:** logistic regression on `[constraint_count, path_length, symbolized_bytes]` predicting `is_interesting`
- **Cost model:** linear regression predicting `elapsed_us` from same features

### Decision Gate (Day 4)
- **If AUROC > 0.65** on held-out split: features work, proceed to Phase 2b
- **If AUROC 0.60-0.65:** borderline, investigate which feature has signal
- **If AUROC < 0.60:** stop and rethink (different features? different labels?)

## Phase 2b: Full Feature Set (Weeks 2-3)

Only executed if spike passes.

### Additional Features
- `branch_hit_count` — how often this branch has appeared
- `prev_attempts` — prior DSE attempts on this branch
- `prev_sat`, `prev_unsat`, `prev_timeout` — historical outcomes
- `target_depth` — nesting depth at branch PC
- `superblock_id` — CFG superblock grouping
- `jump_table_member` — boolean: is this PC in a jump table
- `opt_level` — from build metadata (-O0/-O1/-O2/-O3/-Os)

### Candidate Pool Filtering
Filter `addJcc` before logging:
- Exclude already-covered edges
- Exclude branches with hit_count > threshold
- Exclude branches without downstream uncovered blocks
- Exclude branches not recently attempted

### Leakage Audit
For every feature, ask: **was this known before the solve decision?**
- Remove `elapsed_us`, `result`, `testcase_generated` from predictors
- Keep them as labels only

### Dataset V1 Freeze
- Write `scripts/build_dataset.py` to regenerate from raw logs
- Write `docs/dataset_card.md` with:
  - Source programs and compiler versions
  - Feature definitions
  - Label definitions
  - Limitations
  - Leakage controls
- Tag `dataset-v1`

## Success Criteria for Phase 2

| Criterion | Threshold | Why |
|:---|:---|:---|
| Utility model AUROC | > 0.70 | Predictive enough to matter |
| Cost model MAE | < 20% of median solver time | Cheap to compute, useful signal |
| Feature extraction overhead | < 1% of runtime | MEUZZ benchmark |
| Cross-program split | Both models hold up on unseen program | Generalization requirement |
| No leakage | Manual audit of 20 random rows | Q1 reviewer requirement |

## Tooling to Build in Phase 2

### `scripts/build_dataset.py`
Reads raw logs, applies leakage filtering, joins candidates with outcomes, writes processed parquet.

### `src/feature_extraction/` modules
One file per feature family. Each module exposes `extract(state) -> dict`.

### `src/models/` modules
One file per model type. Each exposes `train(X, y) -> model`, `predict(model, X)`.

### `tests/` for each new module
Every feature and model gets unit tests.

## Risks in Phase 2

| Risk | Probability | Mitigation |
|:---|:---|:---|
| 3 features have no signal | Medium | Spike detects this early |
| QSYM's taint data hard to access | Medium | Alternative: use constraint AST size |
| Real binary too slow | Low | Fall back to libpng or toy |
| Session length too short for real data | Low | Run overnight |
| Rebuild churn kills productivity | Medium | Use setup_qsym.sh, add feature in one patch |

## Timeline

| Day | Work |
|:---|:---|
| 1 | Add path_length + symbolized_bytes patches to solver.cpp, rebuild |
| 2 | Run 30-60 min fuzzing on zlib, collect dataset |
| 3 | Build build_dataset.py, train baseline models |
| 4 | Decision gate: AUROC analysis, go/no-go on Phase 2b |
| 5-7 | If GO: design full feature schema, add history features |
| 8-14 | Add remaining features, run second collection |
| 15-21 | Leakage audit, dataset card, freeze Dataset V1 |

## Handoff to Phase 3

Phase 3 (Utility Model) will:
- Train logistic regression, decision tree, random forest, gradient boosting
- Cross-program split: leave-one-program-out
- Report PR-AUC (not ROC-AUC, because class imbalance)
- Model card with limitations

Phase 4 (Cost Model) will:
- Decide regression vs classification target
- If regression: log-transform solver time
- If classification: cost classes (cheap/medium/expensive/timeout)
- Cross-program split

Phase 5 (Scheduler) will combine them into ROI dispatch.

## Sign-off

- [ ] Spike runs end-to-end
- [ ] Decision gate outcome documented
- [ ] Dataset V1 frozen (if GO)
- [ ] All scripts committed and tested
