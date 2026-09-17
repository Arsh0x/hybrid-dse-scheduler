# Novelty Matrix

| Work | Branch Ranking | Seed Scheduling | Budget Control | Cost Model | Optimization Cues | Binary-Only | Real Binaries |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| QSYM (2018) | ❌ | ❌ | ⚠️ fixed timeout | ❌ | ❌ | ✅ | ✅ |
| SHFuzz (2020) | ✅ hit/solvability/complexity | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| EPfuzzer (2020) | ✅ hardest-to-reach | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| LeanSym (2021) | ✅ conservative selection | ❌ | ❌ | ⚠️ constraint debloating | ❌ | ✅ | ✅ |
| BSFuzz (2023) | ✅ branch-state | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| HyperGo (2023) | ✅ probability-based | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| SeedOrNot (2025) | ❌ | ✅ classifier | ❌ | ❌ | ❌ | ❌ | ✅ |
| PBFuzz (2024) | ✅ potential-aware | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| S2F (2026) | ✅ | ✅ | ⚠️ sampling | ⚠️ selective symbolization | ❌ | ❌ | ✅ |
| LOOL (2026) | ❌ | ❌ | ❌ | ❌ | ✅ optimization logs | ❌ | ✅ |
| **This work** | ✅ value model | ⚠️ not primary | ✅ per-branch ROI | ✅ cost model | ✅ optimization-shaped proxies | ✅ | ✅ |

## The Gap

Current hybrid fuzzers improve either:
- branch selection (SHFuzz, EPfuzzer, BSFuzz, PBFuzz), OR
- seed scheduling (SeedOrNot), OR
- constraint reduction (LeanSym), OR
- solver efficiency (Wen et al., Chen et al.).

None unify all four around **explicit cost-effectiveness** with **per-branch budget control** in **binary-only** settings using **optimization-aware signals**.

## Our Unique Contribution

1. **Per-branch budget control** — allocate solver time proportional to predicted ROI, not a constant timeout.
2. **Optimization-shaped binary proxies** — use compiler-optimization artifacts (superblock structure, jump tables, reduced instrumentation sites, branch simplification) as branch features, which is underused in binary hybrid DSE scheduling.
3. **Unified value + cost decision layer** — treat DSE as a scarce resource allocated by predicted return, not a heuristic to trigger.

---

## One-Line Contribution Claims

- QSYM: fast concolic execution tailored for hybrid fuzzing; identifies concolic executor as bottleneck.
- SHFuzz: select hard-to-reach branches using binary instrumentation.
- EPfuzzer: prioritize hardest-to-reach branches.
- LeanSym: conservative constraint debloating for efficient hybrid fuzzing.
- BSFuzz: branch-state guided redundancy reduction.
- HyperGo: probability-based directed hybrid fuzzing.
- SeedOrNot: classification-based seed scheduling.
- PBFuzz: potential-aware branch-oriented hybrid fuzzing.
- S2F: principled hybrid testing with fuzzing, symbolic execution, and sampling.
- LOOL: low-overhead, optimization-log-guided compiler fuzzing.

## Our Claim
A unified decision layer that predicts branch utility and SMT cost, then allocates per-branch budget by ROI, improves new edges per DSE CPU second on real x86-64 binaries.
