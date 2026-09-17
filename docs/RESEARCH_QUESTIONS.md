# Research Questions

## One-Sentence Thesis
Compiler-optimization-aware branch features plus predicted SMT cost improve DSE dispatch and per-branch budgeting in x86-64 binary hybrid fuzzing.

## Primary Research Question
Can a value-and-cost-sensitive scheduler, using optimization-aware branch features and predicted SMT solver cost, improve new-edge-per-DSE-CPU-second over fixed-timeout and heuristic hybrid fuzzing baselines on real x86-64 binaries?

## Sub-Questions

- **RQ1 (Cost Prediction):** Can pre-solve branch features predict SMT solver time or timeout risk with useful accuracy on unseen programs?
- **RQ2 (Utility Prediction):** Can pre-solve branch features predict whether a DSE attempt will yield new coverage?
- **RQ3 (Scheduling):** Does ranking candidate branches by predicted value/cost ratio improve DSE efficiency over baseline dispatch policies?
- **RQ4 (Optimization-Aware Features):** Do compiler-optimization-shaped binary features (O-level proxies, CFG superblock structure, reduced instrumentation sites, jump-table structure, branch simplification) add unique predictive value beyond conventional coverage and history features?
- **RQ5 (Overhead):** Does feature extraction and model inference overhead remain small enough that end-to-end gains are not erased?
- **RQ6 (Generalization):** Do the utility and cost models generalize across programs, compilers, and optimization levels?

## Hypotheses

- **H1:** Solver time is heavy-tailed; a small fraction of queries dominates total symbolic time.
- **H2:** Pre-solve features (constraint size, AST depth, taint slice width, branch type) carry measurable signal about solver cost.
- **H3:** Pre-solve features carry measurable signal about whether a DSE attempt yields new coverage.
- **H4:** Value/cost scheduling increases new edges per DSE CPU second over fixed-timeout and value-only policies.
- **H5:** Optimization-shaped features add unique predictive value beyond conventional features, especially under cross-optimization generalization.
- **H6:** Utility and cost models generalize to unseen programs and unseen optimization levels better than random-split estimates suggest.

## Primary Metric
**New edges per DSE CPU second.**

## Secondary Metrics
- Useful seeds per DSE invocation
- Solved branches per CPU hour
- Timeout rate
- Median solver time
- Coverage gain per DSE second
- Feature extraction time
- Scheduler CPU fraction

## Scope Boundary
- No new fuzzer.
- No new SMT solver.
- No deep learning by default.
- Optimization awareness is a secondary RQ, not a dependency that can kill the paper.
