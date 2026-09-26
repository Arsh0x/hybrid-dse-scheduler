# Related Work

One-line summaries of papers most relevant to this project, organized by thematic role. This file feeds the manuscript's Related Work section (Phase 8).

## Direct Competitors (Must Differentiate Against)

- **OptSE** (Zhu et al., IEEE TSE 2025) — path-level reward/cost selection under knapsack budget. Not binary-only. Uses observed (not predicted) cost. *Differentiator: we schedule branches, use pre-solve prediction, and target x86-64 binaries.*
- **DigFuzz** (Zhao et al., IEEE TDSC 2022) — Monte Carlo path prioritization; difficulty-driven dispatch. Requires execution to normalize cost. *Differentiator: pre-solve prediction.*
- **MEUZZ** (Chen et al., RAID 2020) — learned seed scheduling; 27.1% coverage gain over QSYM; microsecond-level feature overhead. *Our overhead benchmark.*
- **Triereme** (Geretto et al., ACSAC 2023) — query scheduling in hybrid fuzzing. *Complementary; combine with branch-level dispatch.*
- **HyperGo** (Lin et al., Computers & Security 2024) — probability-based directed hybrid fuzzing. *Baseline for fuzzing-difficulty features.*

## Foundational (Build Directly On)

- **QSYM** (Yun et al., USENIX Security 2018) — fast binary concolic engine; the canonical hybrid-fuzzing backend. *Our DSE backend.*
- **Driller** (Stephens et al., NDSS 2016) — first major hybrid fuzzer. *Establishes the pattern we improve.*
- **Sydr** (Vishnyakov et al., ISPRAS 2020) — dynamic symbolic execution for binaries. *Alternative backend.*
- **SymQEMU** (Poeplau & Francillon, NDSS 2021) — compilation-based symbolic execution for binaries. *IR-shape evidence for optimization-aware features.*

## Branch Selection Baselines (Direct Comparison)

- **SHFuzz** (Mi et al., Applied Sciences 2020) — selective hybrid fuzzing; branch scheduling by hit/solvability/complexity.
- **EPfuzzer** (Wang et al., KSII TIIS 2020) — hardest-to-reach branch prioritization.
- **BSFuzz** (Hu et al., Electronics 2023) — branch-state guided redundancy reduction.
- **SILK** (Li & Zhang, COMPSAC 2023) — constraint-guided hybrid fuzzing.
- **BSP** (Qian et al., Electronics 2024) — branch splitting for unsolvable paths.
- **LeanSym** (Mi et al., RAID 2021) — conservative constraint debloating; symbolizes only target-relevant bytes. *Orthogonal — we keep debloating, add scheduling.*

## Constraint/Solver Cost

- **Luo et al.** (ISSTA 2021) — constraint solving time prediction; F1 0.743-0.800. *Closest cost-prediction precedent.*
- **Chen et al.** (ISSTA 2021) — synthesize solving strategy for symbolic execution.
- **Chen et al.** (JSS 2023) — adaptive solving strategy synthesis.
- **Wen et al.** (BAR 2019) — ML-based solver selection; 2-10% prediction overhead.
- **Palikareva & Cadar** (CAV 2013) — multi-solver support; no single solver dominates.
- **Malyshev et al.** (ISPRAS 2019) — SMT solvers in static and dynamic SE.
- **Shuai et al.** (TOSEM 2026) — unsatisfiable core guided constraint solving.
- **Mikkel & Zhang** (ESEC/FSE 2023) — speeding up SMT via compiler optimization.

## Optimization-Aware Evidence (Core Novelty)

- **Zhang et al.** (CCS 2024) — "When Compiler Optimizations Meet Symbolic Execution" — empirical study; most optimizations slow DSE. *Direct predecessor for optimization-aware features.*
- **Dong et al.** (ISSRE 2015) — standard optimization pipelines can slow symbolic execution on Coreutils targets.
- **Shen** (CSAIEE 2021) — impact of compiler optimizations on symbolic execution.
- **Hong et al.** (FITEE 2020) — MC/DC-oriented compiler optimization for symbolic execution.
- **Daniel et al.** (TOPS 2022) — Binsec/Rel: symbolic binary analyzer.
- **LOOL** (Berlakovich et al., TOSEM 2026) — optimization-log-guided compiler fuzzing. *Source-based, not binary-only — that is our differentiator.*

## Learned Scheduling (Methodological Precedent)

- **SeedOrNot** (Yan et al., APSEC 2025) — classification-based seed scheduling; negligible overhead.
- **Graphuzz** (Xu et al., TOSEM 2024) — data-driven seed scheduling.
- **Lin & Ye** (BDEE 2025) — random-forest hybrid-fuzzing optimization.
- **Cha et al.** (IEEE TSE 2019) — automatically learning search heuristics for DSE.
- **BELIEFFUZZ** (Huang et al., IEEE TDSC 2024) — Monte Carlo planning for seed scheduling with benefits and costs.

## Generalization Warning (Critical for Review)

- **Jiang et al.** (ICSE 2023) — "Evaluating and Improving Hybrid Fuzzing" — hybrid fuzzers often fail to generalize across setups. *Pre-register cross-program and cross-optimization splits; report negative results honestly.*
- **Zhang et al.** (CCS 2024) — "On Understanding and Forecasting Fuzzers Performance with Static Analysis."
- **Qiu et al.** (IST 2025) — survey of coverage-guided greybox fuzzing with deep neural models.

## Incremental / Constraint Reuse

- **Pangolin** (Huang et al., IEEE S&P 2020) — polyhedral path abstraction; incremental hybrid fuzzing.
- **Liu et al.** (Haifa 2014) — comparative study of incremental constraint solving in SE.
- **Parygina et al.** (IVMEM 2022) — strong optimistic solving for DSE.

## S2F (Most Recent, To Position Against)

- **S2F** (Wang et al., arXiv 2026) — principled hybrid testing with fuzzing, SE, and sampling. *2026 SOTA; positional benchmark.*

## The Gap We Fill

No paper in this list combines:
1. Branch-level dispatch (not path- or seed-level)
2. Pre-solve SMT cost prediction (not post-hoc)
3. Optimization-shaped binary features (not source-based, not logs)
4. Binary-only x86-64 setting
5. Continuous per-branch budget allocation under ROI

OptSE gets closest on (4) but not (1)(2)(3). MEUZZ gets closest on (2) but not (1)(3)(4). Zhang et al. 2024 gets closest on (3) but not (1)(2)(4).
