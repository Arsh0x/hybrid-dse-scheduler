# Milestone 04d: Measurement Audit + Pre-Solve Features

## Date
2026-09-24

## Goal
Add first pre-solve features to candidates.csv, fix logging order,
perform sanity audit.

## Changes vs 4c

### 4d.1: Fixed logging order
- Candidate timestamp captured BEFORE solving (pre-solve)
- Candidate row written AFTER addConstraint
- Ensures timestamp is honest while feature reflects full constraint state

### 4d.2: Added constraint_count feature
- Value = solver_.assertions().size() after addConstraint
- Reflects number of accumulated Z3 assertions at decision time

### 4d.3: Combined fix
- logCandidate(pc, taken, is_interesting, ts_pre, constraint_count_post)

## CSV Schema v1 (updated)
schema_version,candidate_id,timestamp_us,branch_id,is_interesting,taken,constraint_count

## Sample Data
v1,1,...,0x7dd,1,1,1   <- interesting, constraint_count=1
v1,1,...,0x7dd,0,1,0   <- rejected, constraint_count=0

## Sanity Observations
- constraint_count=1 for all is_interesting=1 rows (toy target)
- constraint_count=0 for all is_interesting=0 rows
- Toy target only 2 branches; richer distribution expected on real targets
- No duplicate (branch_id, timestamp_us) pairs
- Timestamps in candidates.csv consistently EARLIER than matched
  solver_timing.csv row (pre-solve)

## What This Enables
- Cost model can now train on constraint_count
- Utility model can distinguish rejected from accepted branches
- Ready for Milestone 4e (Phase 1 checkpoint)

## Next Features (Phase 2)
- path_length, target_depth (trace-level)
- symbolized_bytes (taint)
- branch_hit_count, prev_attempts, prev_sat/unsat (history)
