# Optimization-Aware Dynamic Symbolic Execution (DSE) Scheduler

An optimization-aware, ROI-driven DSE branch scheduling and per-branch cost budgeting controller for x86-64 binary hybrid fuzzing.

## Overview
This repository contains the prototype implementation of the decision layer positioned between coverage-guided fuzzers (e.g., AFL++) and concolic execution backends (e.g., Sydr/QSYM). It ranks candidate branches using predicted return-on-investment (ROI = predicted coverage value / predicted SMT cost) and allocates dynamic per-branch timeouts.

## Quick Start
- See `docs/RESEARCH_QUESTIONS.md` for project scope, metrics, and core hypotheses.
- See `docs/FORMULATION.md` for problem formulation and ROI scoring rules.
- See `docs/NOVELTY_MATRIX.md` for comparison against state-of-the-art hybrid fuzzers.
