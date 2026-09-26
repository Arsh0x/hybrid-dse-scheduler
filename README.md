# Hybrid DSE Scheduler

Research project: **Optimization-Aware, Value-and-Cost-Sensitive Branch-Level DSE Scheduling for x86-64 Binary Hybrid Fuzzing**

## What This Is

A decision layer on top of AFL++ + QSYM that predicts branch utility and SMT cost, then allocates per-branch solver budget by expected return on investment (ROI).

## Repo Layout

    baseline/qsym/          # QSYM patches + evidence (milestones 1-4d)
    docs/                   # Research questions, formulation, novelty matrix
    src/                    # Future: feature extraction, models, scheduler
    scripts/                # Future: dataset builder, experiment runners
    data/                   # Future: raw logs, processed datasets
    paper/                  # Draft manuscript and figures

## Quick Start (Reproduce Baseline)

    # 1. Start QSYM container
    docker run --cap-add=SYS_PTRACE -it \
      -v ~/qsym_workspace:/workspace \
      zjuchenyuan/qsym /bin/bash

    # 2. Restore + rebuild patched QSYM
    /workspace/setup_qsym.sh

    # 3. Set environment
    export PATH=$PATH:/afl:/workdir/qsym/bin
    export AFL_SKIP_CPUFREQ=1 AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1
    export AFL_NO_AFFINITY=1 AFL_PATH=/afl

    # 4. Run hybrid fuzzing
    cd /workspace/<target>
    nohup afl-fuzz -M afl-master -i in -o out -- ./target &
    sleep 8
    nohup afl-fuzz -S afl-slave  -i in -o out -- ./target &
    sleep 8
    nohup run_qsym_afl.py -a afl-slave -o out -n qsym -- ./target &

    # 5. Inspect
    cat /workspace/logs/candidates.csv
    cat /workspace/logs/solver_timing.csv

## Status

| Phase | Description | Status |
|:---|:---|:---|
| 0 | Scoping, novelty, toolchain decisions | Complete |
| 1 | Baseline + measurement infrastructure | Complete |
| 2 | Dataset V1 (spike-first) | Next |
| 3 | Utility model | Pending |
| 4 | Cost model | Pending |
| 5 | ROI scheduler | Pending |
| 6 | Large benchmark campaign | Pending |
| 7 | Ablations + statistics | Pending |
| 8 | Manuscript + submission | Pending |

## Key Docs

- `docs/RESEARCH_QUESTIONS.md` — RQ1-RQ6, H1-H6, primary metric
- `docs/FORMULATION.md` — value, cost, ROI, budget
- `docs/NOVELTY_MATRIX.md` — vs 10 related works
- `docs/RELATED_WORK.md` — one-line summaries of relevant papers
- `docs/PHASE1_CHECKPOINT.md` — verification of Phase 1
- `docs/PHASE2_PLAN.md` — spike-first plan
- `RESEARCH_LOG.md` — chronological log

## Primary Metric

New edges per DSE CPU second.

## License

Research use only.
