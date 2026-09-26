# Phase 1 Checkpoint: Baseline & Measurement Infrastructure

**Date:** 2026-09-27
**Status:** COMPLETE
**Tag:** `phase-1-complete`

## Phase 1 Goal

Build a working hybrid fuzzing baseline (AFL++ + QSYM) with custom
instrumentation that produces an ML-ready dataset of branch-level DSE
decisions.

## Verification Matrix

| Goal | Evidence | Status |
|:---|:---|:---|
| Working DSE backend (QSYM) | `baseline/qsym/milestone_01/` | OK |
| Hybrid AFL++ + QSYM handoff | `baseline/qsym/milestone_01/PROOF.md` | OK |
| Branch inversion proven | `baseline/qsym/milestone_01/` (f2 00 flips buf[0]>10) | OK |
| Magic byte solve | `baseline/qsym/milestone_02_magic_solve/` | OK |
| Non-linear constraint solve | `baseline/qsym/milestone_03_z3_nonlinear/` | OK |
| Per-query solver timing (us) | `baseline/qsym/milestone_04a_solver_timing/` | OK |
| Stable branch IDs (ASLR-safe) | `baseline/qsym/milestone_04b_branch_ids/` (2-run match) | OK |
| Candidate + outcome loggers | `baseline/qsym/milestone_04c_candidate_logging/` | OK |
| Pre-solve features | `baseline/qsym/milestone_04d_features/` | OK |
| Reproducible rebuild | `baseline/qsym/setup_qsym.sh` | OK |

## What "Trustworthy" Means Here

Phase 1 is not about results. It is about whether we can trust
measurements before building models on them:

1. **Same branch -> same ID.** Verified across two independent runs:
   `0e8fd84a25f0fbd0:0x7dd` and `0e8fd84a25f0fbd0:0x93f` appeared in both.
2. **Same solve -> same timing.** Solver timing captured with
   `getTimeStamp()` (us precision) before/after `solver_.check()`.
3. **Same decision -> same log row.** `Solver::addJcc()` is the single
   choke point; every branch decision is captured.
4. **Append-only logs.** All CSV files opened with `fopen(path, "a")`;
   header written once.
5. **Reproducible environment.** Container + setup script restore the
   patched binary in 2-3 min.

## Architecture






## What "Trustworthy" Means Here

Phase 1 is not about results. It is about whether we can trust
measurements before building models on them:

1. Same branch -> same ID. Verified across two independent runs.
2. Same solve -> same timing. us-precision getTimeStamp().
3. Same decision -> same log row. Solver::addJcc() is the choke point.
4. Append-only logs. fopen(path, "a").
5. Reproducible environment. Container + setup_qsym.sh.

## Architecture

AFL++ master  --+
                +--> fuzzer queue
AFL++ slave   --+         |
                          v
                    QSYM (PIN tool)
                          |
                +---------+---------+
                v         v         v
          addJcc()   check()   addConstraint()
                |         |
                v         v
        candidates.csv  solver_timing.csv
                |         |
                +----+----+
                     v
           join on (branch_id, timestamp)
                     |
                     v
               Dataset V1 (Phase 2)

## CSV Schemas

candidates.csv:
  schema_version,candidate_id,timestamp_us,branch_id,is_interesting,taken,constraint_count

solver_timing.csv:
  schema_version,timestamp_us,result,elapsed_us,branch_id,cum_solving_time_us

## Known Issues Carried into Phase 2

1. candidate_id is process-local. QSYM spawns a fresh PIN process per seed.
   Join on (branch_id, timestamp_us) instead.
2. Only 1 feature so far (constraint_count). Phase 2 adds path length,
   symbolized bytes, history, and optimization-shaped features.
3. build_id is FNV-1a 64-bit. Switch to SHA-256 for paper artifact if needed.
4. Shared library branches get :unknown suffix. Main executable only.
5. Solver time dominated by QSYM's value-set pre-pass on toy targets.
   Real binaries will exercise Z3 more.

## Reproducibility Recipe

    # 1. Start container
    docker run --cap-add=SYS_PTRACE -it \
      -v ~/qsym_workspace:/workspace \
      zjuchenyuan/qsym /bin/bash

    # 2. Restore + rebuild patched QSYM
    /workspace/setup_qsym.sh

    # 3. Set environment
    export PATH=$PATH:/afl:/workdir/qsym/bin
    export AFL_SKIP_CPUFREQ=1 AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1
    export AFL_NO_AFFINITY=1 AFL_PATH=/afl

    # 4. Run hybrid on any target
    cd /workspace/<target>
    nohup afl-fuzz -M afl-master -i in -o out -- ./target &
    sleep 8
    nohup afl-fuzz -S afl-slave  -i in -o out -- ./target &
    sleep 8
    nohup run_qsym_afl.py -a afl-slave -o out -n qsym -- ./target &

    # 5. Inspect
    cat /workspace/logs/candidates.csv
    cat /workspace/logs/solver_timing.csv

## Phase 2 Handoff

Phase 2 will:
1. Add pre-solve features: path_length, symbolized_bytes, branch_hit_count,
   prev_attempts, prev_sat, prev_unsat, prev_timeout
2. Add optimization-shaped features: superblock_id, jump_table_member, opt_level
3. Build candidate pool filtering (uncovered, low-frequency, nontrivial
   downstream)
4. Run leakage audit (no post-decision signals as predictors)
5. Freeze Dataset V1 with schema version + dataset card
6. Spike-first: validate 3 features predict before adding all 10
   (see docs/PHASE2_PLAN.md)

## Sign-off

- [x] Backend builds and runs
- [x] Branch inversion end-to-end
- [x] Stable branch IDs verified across runs
- [x] Solver timing captured (us precision)
- [x] Candidate and outcome logs produce matching rows
- [x] Reproducible rebuild script working
- [x] All evidence committed and tagged

**Phase 1 complete. Proceed to Phase 2.**
