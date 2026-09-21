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
