# Milestone 04b: Stable Branch IDs

## Date
2026-09-21

## Goal
Ensure branch IDs are stable across repeated runs (ASLR-safe).

## Scheme
branch_id = FNV1a64(binary_file) + ":" + "0x" + (pc - module_base)

Where module_base is from IMG_LowAddress(IMG_FindByAddress(pc)).

## Stability Test
Run 1 unique IDs:
  0e8fd84a25f0fbd0:0x7dd
  0e8fd84a25f0fbd0:0x93f

Run 2 unique IDs:
  0e8fd84a25f0fbd0:0x7dd
  0e8fd84a25f0fbd0:0x93f

Intersection: BOTH IDs identical across runs.

## Why This Matters
- Same branch -> same ID across ASLR, container restarts, and process respawns
- Prerequisite for training any ML model on branch features
- Enables cross-run aggregation without merging by fuzzy match

## CSV Schema v1 (updated)
schema_version,timestamp_us,result,elapsed_us,branch_id,cum_solving_time_us

## Known Limitations
- build_id is FNV-1a 64-bit (not SHA-256); good enough for uniqueness but
  switch to SHA-256 for paper artifact if reviewers ask
- Only main executable hashed; shared libraries get "unknown" suffix
- Requires PIN 2.14 API (IMG_FindByAddress, IMG_LowAddress)

## Next
Milestone 4c: candidate/outcome CSV loggers (feature extraction starts here)
