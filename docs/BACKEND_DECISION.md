# DSE Backend Decision

## Criteria (weight)

| Criterion | Weight | Why it matters |
|:---|:---:|:---|
| x86-64 binary support | 5 | Must analyze stripped real-world binaries |
| Buildability on Linux | 5 | Must build reproducibly in this environment |
| Solver visibility | 4 | Need to hook solver queries and time them |
| Branch-level access | 5 | Need to intercept per-branch solve decisions |
| Hybrid integration (AFL++) | 4 | Must accept fuzzer seeds and return testcases |
| Maintenance / activity | 2 | Prefer maintained projects |
| License compatibility | 2 | Must allow research use and artifact release |

## Candidates

### Candidate A: QSYM
| Criterion | Score | Notes |
|:---|:---:|:---|
| x86-64 binary support | 5 | Built for x86-64 binaries |
| Buildability | 3 | Legacy dependencies (old LLVM, Z3) |
| Solver visibility | 5 | Explicit Z3 integration |
| Branch-level access | 5 | Branch-level trace and constraint |
| Hybrid integration | 5 | Designed for AFL/AFL++ |
| Maintenance | 2 | Unmaintained since ~2019 |
| License | 5 | Open source |
| **Total** | **30/35** | |

### Candidate B: Sydr (from OSS-Sydr-Fuzz)
| Criterion | Score | Notes |
|:---|:---:|:---|
| x86-64 binary support | 5 | Designed for binaries |
| Buildability | 4 | Actively maintained, CMake |
| Solver visibility | 4 | Uses several SMT solvers |
| Branch-level access | 4 | Trace-based, some access |
| Hybrid integration | 5 | OSS-Sydr-Fuzz integration |
| Maintenance | 5 | Active |
| License | 5 | Open source |
| **Total** | **32/35** | |

### Candidate C: LeanSym
| Criterion | Score | Notes |
|:---|:---:|:---|
| x86-64 binary support | 5 | Binary-focused |
| Buildability | 3 | Research prototype, sparse docs |
| Solver visibility | 3 | Constraint debloating may hide solver calls |
| Branch-level access | 4 | Conservative selection is branch-level |
| Hybrid integration | 3 | Custom integration likely required |
| Maintenance | 1 | Research artifact |
| License | 4 | Check |
| **Total** | **23/35** | |

### Candidate D: Custom lightweight concolic backend on top of Triton / Miasm / Angr
| Criterion | Score | Notes |
|:---|:---:|:---|
| x86-64 binary support | 4–5 | Depends on framework |
| Buildability | 3 | Python overhead |
| Solver visibility | 5 | Full control |
| Branch-level access | 5 | Full control |
| Hybrid integration | 3 | Must build from scratch |
| Maintenance | 3 | Self-maintained |
| License | 4–5 | Varies |
| **Total** | **27–30/35** | |

## Decision

**First choice:** Candidate B (Sydr) if buildable in this environment; otherwise Candidate A (QSYM) with pinned legacy Docker image.

**Fallback:** Candidate D (Triton-based lightweight concolic backend) if both A and B fail to build within 3 days.

**Rationale:** Sydr offers active maintenance, multi-solver support (useful for RQ1's solver portfolio extension), and native OSS-Sydr-Fuzz integration. QSYM is the reference fast concolic backend but has legacy build issues.

## Go/No-Go
Build the first-choice backend and run one toy binary by end of Week 1. If it fails after 3 focused days, switch to fallback and document the failure.
