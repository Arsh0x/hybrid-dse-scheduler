# Milestone 02: QSYM Solves 4-Byte Magic

## Date
2026-09-19

## Target
magic.c: checks for bytes DE AD BE EF

## Result
QSYM generated `id:000003` = bytes DE AD BE EF
Running it prints "MAGIC FOUND"

## Solver Time
Solver=0s. QSYM value-set pre-pass solved it without Z3.
This is expected for direct byte-equal comparisons.

## Notes
- Second branch (sum == 0x3E8) is unsatisfiable: DE+AD+BE+EF = 0x338, not 0x3E8
- For future experiments, need a target with satisfiable arithmetic constraints
  that force Z3 to actually run

## Next Steps
- Build an arithmetic-constraint target (e.g., buf[0] * buf[1] == 0x1234)
- Instrument QSYM's solver invocation for per-branch timing
