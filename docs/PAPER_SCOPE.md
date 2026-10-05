# Paper Scope: What Pre-Solve Binary Features Actually Generalize?

**Status:** Draft v1 (2026-10-01)
**Target venue:** TOSEM (fallback: ESE, JSS)
**Timeline:** 5–6 months from scope lock to submission

---

## 1. Thesis

> For ML-based DSE scheduling in binary hybrid fuzzing, structural and
> history features generalize across programs, compilers, and optimization
> levels; symbolic and optimization-shaped features do not. This paper
> establishes which feature families are usable for cross-program models
> and which are not, with an evidence-backed interpretation of failure
> modes and a reusable evaluation methodology.

---

## 1b. Novelty and Positioning

Independent literature review (Consensus, 2026-10-01) confirms the following.

**Preempted by prior work** (do NOT claim as novel):
- ML-guided scheduling for hybrid fuzzing (MEUZZ 2020)
- Transferable models across programs (MEUZZ, SyML)
- Binary hybrid fuzzing itself (QSYM, Driller)
- Feature engineering for DSE (FeatMaker, Cha et al.)

**Novel in this paper** (the defensible claim):
- First systematic feature-family generalization study for ML-guided
  DSE scheduling in binary hybrid fuzzing
- Across programs AND compilers AND optimization levels
- Separation of transferable vs non-transferable feature families
- Reusable evaluation methodology

**Near-neighbors requiring explicit differentiation in the paper:**
- MEUZZ (Chen et al., 2020): closest work. Claims transferable learned
  seed scheduler. No feature taxonomy, no compiler robustness analysis.
- SyML (Ruaro et al., 2021): transfer to unseen binaries via semantic
  features. No feature-family comparison.
- FeatMaker (Yoon & Cha, 2024): automated feature generation. Goal is
  new features, not characterizing which existing families transfer.
- Cha et al. (2019): per-program learned heuristics. Cuts against
  cross-program transfer, contrasting with our positive result.

**Risks:**
- "Apparent novelty" not "absolute novelty" — very recent niche work
  could overlap. Mitigate with careful literature review at submission.
- Reviewers may see the work as trend-following. Mitigate by emphasizing
  the methodology as the contribution, not just the findings.

---

## 2. Research Questions

### RQ1 (Cross-Program Generalization)
Which pre-solve binary feature families predict DSE utility when trained
on one program and tested on a structurally different program?

### RQ2 (Cross-Compiler Generalization)
Which feature families generalize when trained on GCC-compiled binaries
and tested on Clang-compiled binaries (and vice versa)?

### RQ3 (Cross-Optimization Generalization)
Which feature families generalize across optimization levels (-O0/-O1/
-O2/-O3/-Os)? Which features work only within a fixed optimization level?

### RQ4 (Upper Bound)
What is the achievable AUROC ceiling from all pre-solve features,
compared with an oracle that observes the actual solve outcome?

### RQ5 (Failure-Mode Taxonomy)
Why do certain feature families fail to generalize? Can we categorize
failures into types (label encoding, compiler-specific bias, distribution
shift, taint-domain mismatch)?

---

## 3. Feature Taxonomy (8 families, ~45 features)

### F1. Structural
- path_length (branches in current trace)
- target_depth (nesting depth of branch)
- **status:** both generalize (path_length 0.89/0.85 cross-program)

### F2. Frequency/History
- branch_hit_count (appearances in prior traces)
- prev_sat, prev_unsat, prev_timeout (per-branch outcome history)
- **status:** branch_hit_count generalizes (0.77/0.94). prev_* fail.

### F3. Symbolic
- symbolized_bytes (taint slice width)
- constraint_count (accumulated solver assertions, pre-solve)
- **status:** GENERALIZES (0.774 / 0.714) after milestone 5b pre-solve fix.
  Earlier "fails" verdict was based on contaminated data.

### F4. Optimization — Function Geometry
- rtn_offset (offset from function start)
- rtn_size (function size in bytes)
- rtn_cmov (CMOVcc count in function)
- rtn_calls (call instruction count)
- rtn_loops (natural loop count)
- **status:** all three tested fail (0.38–0.68 cross-program).

### F5. Optimization — CFG Structure
- superblock_id (basic block group)
- jump_table_member (is PC in a computed-goto dispatch)
- has_back_edge (is PC target of a loop back-edge)
- in_loop (is PC inside a natural loop)
- **status:** NOT YET TESTED

### F6. Optimization — Instruction Mix
- insn_mix_ratio (arith/logic/branch/mem ratio in function)
- has_avx_or_sse (SIMD instructions present in function)
- branch_density (branches / instructions in function)
- **status:** NOT YET TESTED

### F7. Binary Metadata
- opt_level (compile flag: -O0/-O1/-O2/-O3/-Os)
- compiler_id (GCC vs Clang version hash)
- build_id (SHA of binary)
- **status:** meta-features; useful for cross-validation splits

### F8. Coverage-Based
- is_new_edge (first time branch target was reached)
- local_coverage_gain (new edges from this seed)
- **status:** strong prior; already known in fuzzing literature

---

## 4. Benchmark Plan (~60 programs, 10 domains)

### Domain 1: Compression (6)
zlib, bzip2, xz, zstd, lz4, brotli

### Domain 2: Image (8)
libpng, libjpeg-turbo, libtiff, giflib, libwebp, openjpeg, jasper, libraw

### Domain 3: Parsing/Serialization (10)
libxml2, json-c, yaml, toml-c, expat, libcsv, re2, pcre2, libyaml, cJSON

### Domain 4: Network (8)
tcpdump, tshark, nginx-mini, libcurl, openssl, wolfssl, libssh, mosquitto

### Domain 5: Media (6)
ffmpeg (h264, vp8, mp3, flac variants), libopus, libvorbis, libtheora

### Domain 6: Crypto (5)
openssl-crypto, libsodium, libgcrypt, mbedtls, libtomcrypt

### Domain 7: Archive (5)
tar, cpio, unzip, gzip, xz-utils

### Domain 8: Database (4)
sqlite, leveldb, lmdb, rocksdb

### Domain 9: Language Runtime (5)
lua, quickjs, duktape, mujs, micropython

### Domain 10: Text Processing (5)
jq, sed, grep, awk (busybox), coreutils

**Total:** 62 programs.

### Compiler configurations
- GCC 5.4 (Ubuntu 16.04 default, matches QSYM container)
- Clang 3.8 (available in container)
- Optimization levels: -O0, -O2, -Os (3 levels)

**Total configurations:** 62 × 2 × 3 = 372 build variants.

### Runtime protocol
- 10-minute runs per (program, compiler, opt-level)
- >=20 repetitions per configuration
- Warmup seeds from each program's test suite

**Total runs:** 372 × 20 = 7,440 runs
**Total compute:** ~1,240 CPU-hours (parallelizable)

---

## 5. Evaluation Protocol

### Splits
1. **Leave-one-program-out (LOPO):** for each program, train on the
   other 61, test on the held-out one.
2. **Leave-one-compiler-out (LOCO):** train on GCC, test on Clang and
   vice versa.
3. **Leave-one-opt-out (LOOO):** train on 2 optimization levels, test
   on the third.

### Models
- Logistic regression (interpretable baseline)
- Gradient-boosted trees (main result)
- Feature ablation: drop one family at a time

### Metrics
- AUROC (primary)
- AUPRC (class-imbalanced complement)
- Per-program AUROC distribution (not just mean)
- Bootstrap 95% confidence intervals (10,000 resamples)

### Statistical tests
- Wilcoxon signed-rank between feature families
- Cliff's delta for effect sizes
- Bonferroni correction for multiple comparisons

---

## 6. Contributions (ranked)

1. First systematic cross-program/cross-compiler/cross-optimization
   evaluation of pre-solve features for DSE scheduling.
2. Feature family taxonomy with empirical verdicts.
3. Upper-bound analysis: how much headroom remains.
4. Failure-mode taxonomy with examples.
5. Reusable infrastructure (instrumented QSYM, automated pipeline).
6. Methodological guidance for ML-in-fuzzing practitioners.

---

## 7. Threats to Validity

### Internal
- QSYM's internal biases (constraint accumulation artifact)
- Feature extraction timing (log ordering — fixed in milestone 5b)
- Data leakage (audited in milestone 5d)

### External
- Binary-only setting (source-based may differ)
- x86-64 Linux (ARM, Windows untested)
- QSYM specifically (other backends may differ)

### Construct
- "Utility" defined as new coverage, not crash discovery
- Pre-solve prediction, not real-time scheduling

### Statistical
- Class imbalance (mitigated by AUPRC + bootstrap CIs)
- Multiple comparisons (Bonferroni correction)
- Temporal split contamination (documented in milestone 5e2)

---

## 8. Timeline

| Week | Task |
|:---|:---|
| 1-2 | Lock scope (this document); set up build/run automation |
| 3-6 | Implement F4-F8 features; unit test each on zlib/libpng |
| 7-10 | Build automation pipeline; validate on 5 pilot programs |
| 11-16 | Full data collection (7,440 runs, parallelized) |
| 17-18 | Analysis: cross-program, cross-compiler, cross-optimization |
| 19-20 | Upper bound + failure-mode taxonomy |
| 21-24 | Paper writing |
| 25-26 | Internal revision, reproducibility artifact |
| 27 | Submission to TOSEM |

**Total: ~6 months.**

---

## 9. Success Criteria

The paper is submittable if:
- Clean data for >=50 programs x 2 compilers x 3 opt levels
- At least one feature family generalizes with statistical significance
- At least 3 feature families do not generalize with statistical significance
- Upper-bound analysis complete
- Reproducibility artifact public
- Paper draft 15-20 pages

The paper is a landmark if:
- Cross-compiler results reveal new findings
- Failure taxonomy explains 80%+ of observed failures
- Methodological guidelines adopted by follow-up work

---

## 10. Out of Scope

- Build the actual ROI scheduler (that's a follow-up systems paper)
- Extend QSYM's symbolic engine
- Target crash discovery (only coverage utility)
- Windows or ARM
- Deep learning models (logistic + GBT only)

---

## 11. Open Decisions

- [ ] Final venue: TOSEM vs ESE vs JSS
- [ ] Include -O1, -O3 in addition to -O0/-O2/-Os?
- [ ] Clang 3.8 only, or also Clang 6+?
- [ ] Add ARM cross-compilation study?
- [ ] Include live scheduler demo as appendix?

---

## 12. Next Immediate Action

**Phase B (Week 3-6):** Implement remaining feature families
(F5 CFG structure, F6 instruction mix), unit-test on zlib + libpng.

**Phase C (Week 7-10):** Build automation pipeline.

**Phase D (Week 11+):** Full data collection.

---

*This document is frozen at scope-lock. Changes require a written
amendment appended to this file with date and rationale.*
