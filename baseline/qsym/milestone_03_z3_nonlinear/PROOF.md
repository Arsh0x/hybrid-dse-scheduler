# Milestone 03: QSYM Solves Non-Linear Constraints

## Date
2026-09-19

## Target
z3_target.c
  - Constraint 1: buf[0] * buf[1] == 0x1234   (non-linear)
  - Constraint 2: (buf[2] ^ 0xAA) == (buf[3] + 5)   (XOR + arithmetic)

## Seeds
- seed: 00 00 00 00
- seed2: 01 02 03 04
- seed3: FF FF FF FF

## Result — QSYM generated 3 inputs
| File | Bytes | Output |
|:---|:---|:---|
| id:000000 | 73 b7 ff 50 | (none) |
| id:000001 | e9 14 aa 7b | PRODUCT OK |
| id:000002 | e9 14 e8 3d | PRODUCT OK + XOR SUM OK |

## Proof
- id:000001 (e9 14 aa 7b) solves buf[0]*buf[1] == 0x1234
  (0xE9 * 0x14 = 233 * 20 = 4660 = 0x1234)
- id:000002 (e9 14 e8 3d) solves BOTH constraints
  (0xE8 ^ 0xAA = 0x42, 0x3D + 5 = 0x42)

## Solver Timing Issue
QSYM's stdout logs "Solver=0s" — but this is rounded to whole seconds
AND does not distinguish value-set pre-pass from Z3 invocation.

QSYM's PIN temp dirs are deleted after each run, so we cannot recover
per-branch timing post-hoc.

## Implication for Our Scheduler Paper
We MUST instrument QSYM's PIN tool to log:
- branch_id
- solver invocation timestamp
- solver result (SAT/UNSAT/TIMEOUT)
- actual solver time in milliseconds

This is Day 25-27 of the execution plan (solver timing hook).

## Next Step
Instrument the PIN tool to emit per-branch solver timing to a persistent log.
