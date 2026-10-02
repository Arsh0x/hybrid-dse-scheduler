# Research Log

## Day 1 — Scoping and Setup
- Initialized repository skeleton `hybrid-dse-scheduler`.
- Defined primary metric: **New edges per DSE CPU second**.
- Froze research questions and hypotheses in `docs/RESEARCH_QUESTIONS.md`.
- Formalized ROI scoring and candidate branch pool logic in `docs/FORMULATION.md`.

## Day 2 — Novelty Matrix and Gap Formalization
- Built `docs/NOVELTY_MATRIX.md` comparing our work against 10 hybrid fuzzing papers (QSYM, SHFuzz, EPfuzzer, LeanSym, BSFuzz, HyperGo, SeedOrNot, PBFuzz, S2F, LOOL).
- Identified core gap: Per-branch budget control with compiler-optimization-shaped binary signals in binary-only hybrid fuzzing.

## Day 3 — DSE Backend Evaluation
- Evaluated candidate backends (Sydr, QSYM, LeanSym, Triton custom fallback) in `docs/BACKEND_DECISION.md`.
- Recorded build environment in `baseline/environment.md`.

## Day 4 — Instrumentation & Branch ID Protocol
- Selected static binary rewriting (RetroWrite-style) for x86-64 PIE binaries with qemu_mode fallback in `docs/INSTRUMENTATION_DECISION.md`.
- Scaffolded branch ID stability verification in `tests/test_branch_id.py`.

## Day 5 — Candidate Pool Specification
- Specified inclusion/exclusion rules and thresholds in `docs/CANDIDATE_POOL.md`.

## Day 6 — Schema & Append-Only Logger
- Designed v1 schema in `docs/LOG_SCHEMA.md`.
- Implemented append-only raw logger `src/feature_extraction/raw_logger.py`.
- Verified smoke tests in `tests/test_raw_logger.py`.

## Day 7 — Week 1 Retrospective & Tagging
- Created architecture diagram `paper/figures/architecture_v1.md`.
- Formulated concept test `docs/WEEK1_CONCEPT_TEST.md`.
- Verified all smoke tests and committed `phase-0-complete`.

## 2026-09-19 — QSYM Backend Verified (Milestones 1–3)

### Setup
- Container: zjuchenyuan/qsym (Ubuntu 16.04 base)
- Built libqsym.so from source inside container
- Installed QSYM via `pip install .` (Python 2.7)
- Volume mount: ~/qsym_workspace <-> /workspace

### Milestone 1: Hybrid Handoff
- AFL++ 2.52b + QSYM running simultaneously
- QSYM read seeds from AFL slave queue
- Generated testcase f2 00 flipped branch -> "Branch A"
- Evidence: baseline/qsym/milestone_01/

### Milestone 2: Magic Byte Solve
- Target: DE AD BE EF check
- QSYM generated id:000003 = DE AD BE EF -> "MAGIC FOUND"
- Solved via value-set pre-pass (Solver=0s)
- Evidence: baseline/qsym/milestone_02_magic_solve/

### Milestone 3: Non-Linear Solve
- Target: buf[0]*buf[1]==0x1234 AND (buf[2]^0xAA)==(buf[3]+5)
- QSYM generated e9 14 e8 3d -> "PRODUCT OK" + "XOR SUM OK"
- Both constraints satisfiable; non-linear multiplication solved
- Evidence: baseline/qsym/milestone_03_z3_nonlinear/

### Critical Finding
QSYM's stdout logging is too coarse for our scheduler paper:
- Per-seed, not per-branch granularity
- Solver time rounded to whole seconds
- Cannot distinguish value-set pre-pass from actual Z3 invocation
- PIN temp dirs (/tmp/tmp*/qsym-out-*) are deleted after each run

### Implication
Must instrument the PIN tool to emit:
- branch_id (build_id + module-relative offset)
- solver invocation timestamp + elapsed milliseconds
- solver result (SAT/UNSAT/TIMEOUT)
to a persistent append-only log.

This is the next milestone: solver timing hook.

### Next Action
Instrument /workdir/qsym/qsym/pintool/solver.cpp to write per-query
timing to a persistent CSV log.

## 2026-09-20 — Milestone 4a: Solver Timing Hook

Instrumented /workdir/qsym/qsym/pintool/solver.cpp to write one row
per Z3 solver invocation to /workspace/logs/solver_timing.csv.

CSV schema v1:
  schema_version,timestamp_us,result,elapsed_us,pc,cum_solving_time_us

Sample:
  v1,1789918987610639,SAT,2906,4196317,2906
  v1,1789918988518217,SAT,541,4196671,3447

Key change: inserted logSolverRow() inside Solver::check() — captures
every Z3 query with microsecond timing and PC address.

Next: Milestone 4b (stable branch IDs).

## 2026-09-21 — Milestone 4b: Stable Branch IDs

### Achievement
Branch IDs now stable across runs (ASLR-safe).

Scheme: branch_id = FNV1a64(binary) + ":" + "0x" + (pc - module_base)

### Verification
Two independent runs produced identical branch IDs:
  0e8fd84a25f0fbd0:0x7dd
  0e8fd84a25f0fbd0:0x93f

### CSV Schema v1 (updated)
schema_version,timestamp_us,result,elapsed_us,branch_id,cum_solving_time_us

### Implementation
- Patched solver.cpp with getBranchId() and computeBuildIdForPc()
- Rebuilt libqsym.so, installed to Python package path

### Evidence
- baseline/qsym/milestone_04b_branch_ids/

### Next
Milestone 4c: candidate/outcome CSV loggers (feature extraction begins)

## 2026-09-21 — Milestone 4c: Candidate + Outcome Loggers

Two CSV logs now produced by QSYM:
- candidates.csv     -- every branch decision (with is_interesting flag)
- solver_timing.csv  -- every Z3 solve (result + elapsed_us)

Join verified: 3 interesting candidates = 3 solver invocations.
Both logs use stable branch_id format (build_id:0xoffset).

Known issue: candidate logged AFTER solve (order will be fixed in 4d).

Evidence: baseline/qsym/milestone_04c_candidate_logging/

## 2026-09-24 — Milestone 4d: Measurement Audit + Pre-Solve Features

### Achievements
- Fixed log ordering: candidate timestamp now captured BEFORE solving
- Added constraint_count feature (solver_.assertions().size())
- Verified on z3_target: is_interesting=1 rows have constraint_count=1

### New CSV schema (candidates.csv)
schema_version,candidate_id,timestamp_us,branch_id,is_interesting,taken,constraint_count

### Sample verified pattern
v1,1,...,0x7dd,1,1,1   <- interesting, constraint_count=1
v1,1,...,0x7dd,0,1,0   <- rejected, constraint_count=0

### Reproducibility
Added /workspace/setup_qsym.sh -- one-command restore + rebuild after
container restart. Points at /workspace/solver.cpp.4d snapshot.

### Evidence
- baseline/qsym/milestone_04d_features/
- baseline/qsym/setup_qsym.sh
- baseline/qsym/solver.cpp.latest

### Next
Milestone 4e: Phase 1 checkpoint -- formal verification of complete
measurement pipeline

## 2026-09-29 — Milestone 5a: Phase 2a Spike (AUROC Validation)

### Goal
Test whether pre-solve binary features predict DSE utility.

### Result: GO
- Random-split AUROC: 0.863 (both features)
- path_length alone: 0.867
- symbolized_bytes alone: 0.838
- Random baseline: 0.528

### Data (zlib minigzip -d, 3 min)
- 344 candidates (83 interesting, 261 rejected)
- 345 solver invocations (256 SAT, 89 UNSAT)

### Class separation
| Feature | Interesting | Rejected | Ratio |
| path_length | 13.14 | 5.97 | 2.20x |
| symbolized_bytes | 2.29 | 1.32 | 1.73x |

### Issues Found
- constraint_count is leaky (read after addConstraint, always 0 for rejected)
- Single target only
- Small test set

### Decision
GO to Phase 2b. Paper's thesis is empirically grounded.

### Evidence
- baseline/qsym/milestone_5a_spike/

## 2026-09-30 — Milestones 5b + 5c: Leakage Fix + Cross-Program Validation

### 5b: Fixed constraint_count leakage
- Moved read of solver_.assertions().size() to BEFORE addConstraint
- Discovered deeper issue: constraint accumulation only happens after
  interesting branches, so constraint_count>0 still perfectly encodes
  the label (AUROC 1.000 cross-program). Not usable as a feature.
- Documented as QSYM structural artifact.

### 5c: Cross-program generalization
- Added libpng 1.6.43 as second target with custom stdin fuzz driver
- Data: zlib 351 candidates, libpng 640 candidates
- Result:
  - path_length: AUROC 0.892 (zlib->libpng), 0.899 (libpng->zlib)
  - symbolized_bytes: AUROC 0.632, direction reverses
  - constraint_count: AUROC 1.000 (artifact)

### Key Finding
Only path_length generalizes bidirectionally. Need 2+ more generalizing
features to defend the paper's ML story.

### Next
Milestone 5d: implement history and optimization-shaped features, retest.

### Evidence
- baseline/qsym/milestone_5c_cross_program/

## 2026-10-01 — Milestone 5e2: rtn_cmov + QSYM Stability

### Engineering
- Fixed PIN crash: RTN_InsHead now called at instrumentation time
  (RTN_AddInstrumentFunction callback), not runtime
- Fixed QSYM Python race condition (afl.py get_score OSError)
- Added QSYM restart wrapper as fallback (documented as corrupting regime)

### Result
rtn_cmov FAILS cross-program generalization (AUROC 0.381/0.409).
Adding it to baseline slightly hurts (0.909→0.910, 0.941→0.936).

This is the THIRD optimization-shaped feature to fail:
- rtn_offset: 0.52/0.47
- rtn_size: 0.45/0.41
- rtn_cmov: 0.38/0.41

### Positive Result Retained
Baseline (path_length + branch_hit_count) achieves AUROC 0.909/0.941.

### Paper Decision
Thesis must pivot: "Which pre-solve features generalize?" is a strong
empirical study. Original "optimization-aware features improve
scheduling" claim is falsified at binary-only cross-program level.

### Next
Phase A: write PAPER_SCOPE.md and lock the empirical study design.

### Evidence
- baseline/qsym/milestone_5e2_rtn_cmov/

## 2026-10-03 — Milestones 5f + 5g: F5 + F6 Complete

### F5 (CFG structure, 4 features)
insn_pos_in_rtn, rtn_insn_count, rtn_branch_count, rtn_indirect_count
Result: all fail. Family AUROC 0.478/0.353.

### F6 (instruction mix, 2 features)
rtn_simd_count, rtn_mem_ops
Result: both fail. Family AUROC 0.533/0.596.

### Combined F4+F5+F6
AUROC 0.527/0.264 — worse than random.

### Baseline
path_length + branch_hit_count: AUROC 0.885/0.950 (unchanged by
adding any optimization feature).

### Final Tally
17 features tested across 7 families.
2 generalize (path_length, branch_hit_count).
15 fail (symbolic, history-outcome, opt-geometry, opt-CFG, opt-instruction-mix).

### Verdict
The empirical thesis is airtight. Optimization-shaped features do not
generalize for binary hybrid fuzzing. Structural and history-frequency
features do.

### Next
Phase C: automation pipeline. Then full 62-program data collection
for the paper's final numbers with 10-min runs + bootstrap CIs.

### Evidence
- baseline/qsym/milestone_5f_cfg_features/
- baseline/qsym/milestone_5g_instruction_mix/

## 2026-10-03 — Milestone 6a: Build Automation Pipeline

### Achievement
`build_program.py` builds zlib and libpng end-to-end with one command:
- Downloads and extracts source tarballs
- Handles dependencies (zlib for libpng)
- Applies version overrides (PNG_ZLIB_VERNUM)
- Copies custom driver files from metadata dir
- Runs custom build steps
- Manages seeds (once populated)

### Validated Builds
- `python3 /workspace/scripts/build_program.py zlib gcc O2` → binary + seeds
- `python3 /workspace/scripts/build_program.py libpng gcc O2` → binary + seeds

### Python 3.5 Compatibility Fixes
- open(str(path)) for Path objects
- universal_newlines=True instead of text=True
- stdout=PIPE, stderr=PIPE instead of capture_output=True

### Next
- Regenerate seed corpora for zlib and libpng
- Write run_experiment.py (config-driven AFL+QSYM runs)
- Write extract_dataset.py (raw logs to Parquet)
- Write analyze.py (cross-program AUROC with bootstrap CIs)

### Evidence
- scripts/build_program.py (243 lines, working)
- benchmarks/zlib/metadata.yaml
- benchmarks/libpng/metadata.yaml
- benchmarks/libpng/fuzz_stdin.c
