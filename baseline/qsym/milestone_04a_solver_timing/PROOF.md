# Milestone 04a: Per-Branch Solver Timing Hook

## Date
2026-09-20

## Goal
Instrument QSYM's PIN tool to write one row per Z3 solver invocation
to a persistent CSV.

## Implementation
Modified /workdir/qsym/qsym/pintool/solver.cpp:

1. Added includes: <cstdio>, <cstdlib>, <unistd.h>
2. Added helper functions in anonymous namespace:
   - initSolverLogIfNeeded()  -- lazy init of CSV file
   - logSolverRow()           -- writes one row per solve
3. Inserted single call inside Solver::check():
   logSolverRow(res, elapsed, last_pc_, solving_time_);

Output path: /workspace/logs/solver_timing.csv
Override via env var: QSYM_LOG_FILE

Rebuilt libqsym.so and installed to:
  /usr/local/lib/python2.7/dist-packages/qsym/pintool/obj-intel64/libqsym.so

## CSV Schema v1
schema_version,timestamp_us,result,elapsed_us,pc,cum_solving_time_us

## Sample Data (from z3_target run)
v1,1789918987610639,SAT,2906,4196317,2906
v1,1789918988518217,SAT,541,4196671,3447
v1,1789918993023208,SAT,924,4196671,924

## What This Proves
1. Every Z3 query is captured with microsecond-precision timing
2. Result (SAT/UNSAT/UNKNOWN) is logged
3. PC address of the branch is captured
4. Data persists to host via /workspace volume mount

## Known Limitations
- PC is decimal; will convert to hex and combine with build_id for
  stable branch IDs
- cum_solving_time_us resets per PIN process (QSYM spawns fresh process
  per seed)
- Only 3 rows in 60 seconds -- QSYM invokes Z3 sparingly
- All results SAT; need harder targets for UNSAT/UNKNOWN samples

## Next Steps
- Milestone 4b: stable branch IDs (build_id + module-relative offset)
- Milestone 4c: candidate/outcome CSV loggers
- Milestone 4d: measurement audit
- Milestone 4e: full hybrid test with hard target
