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
