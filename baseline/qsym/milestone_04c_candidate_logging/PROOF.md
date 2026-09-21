# Milestone 04c: Candidate + Outcome Loggers

## Date
2026-09-21

## Goal
Log every branch decision (candidate) plus every solve outcome,
joined on (branch_id, timestamp) to produce an ML-ready dataset.

## Implementation
Patched solver.cpp:
1. Added global FILE* g_candidate_log
2. Added initCandidateLogIfNeeded() -- lazy init, writes header
3. Added logCandidate(pc, taken, is_interesting) -- one row per decision
4. Hooked into Solver::addJcc() right after addConstraint()

## CSV Schemas

candidates.csv:
  schema_version,candidate_id,timestamp_us,branch_id,is_interesting,taken

solver_timing.csv:
  schema_version,timestamp_us,result,elapsed_us,branch_id,cum_solving_time_us

## Verification
Row counts match:
  - interesting candidates: 3
  - solver invocations:     3
Join script confirms 1:1 mapping.

## Known Limitations

1. candidate_id is process-local (QSYM spawns fresh PIN per seed).
   Use (branch_id, timestamp_us) as the join key.

2. Logging happens AFTER negatePath(), so the candidate timestamp is
   technically post-solve. Non-blocking for now (no features logged yet),
   but must be moved BEFORE negatePath when we add pre-solve features
   in Milestone 4d.

## What This Enables
- Utility model: predict (is_interesting AND SAT) from features
- Cost model: predict elapsed_us from pre-solve features
- Scheduler: rank candidates by predicted utility / predicted cost

## Evidence
- candidates.csv (7 rows)
- solver_timing.csv (3 rows)
- verify_join.py (join script)

## Next
Milestone 4d: measurement audit + fix logging order
