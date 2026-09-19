# Milestone 01: Hybrid Handoff and Branch Flip Proof

## Date
2026-09-19

## Environment
- Container image: zjuchenyuan/qsym
- AFL version: 2.52b (at /afl)
- QSYM: built from source, installed via pip
- ptrace_scope: 0
- Target: toy_stdin.c (reads 4 bytes from stdin)

## Target Logic
    read(0, buf, 4);
    if (buf[0] > 10 && buf[1] < 20) {
        printf("Branch A\n");
        if (buf[2] == 0x42) {
            printf("Branch B\n");
        }
    }

## Seed
- in/seed: bytes 05 0F 41 00 -> LEFT branch (buf[0]=5, not > 10)
- in/right_seed: bytes 0B 0F 42 00 -> RIGHT branch

## Hybrid Setup
- AFL master: afl-fuzz -M afl-master -i in -o out -- ./toy_stdin
- AFL slave:  afl-fuzz -S afl-slave  -i in -o out -- ./toy_stdin
- QSYM: run_qsym_afl.py -a afl-slave -o out -n qsym -- ./toy_stdin

## Result
QSYM read seeds from AFL slave queue and generated 3 testcases:

| File | Bytes | Output | Interpretation |
|:---|:---|:---|:---|
| id:000000 | 00 | (none) | Trivial |
| id:000001 | f2 00 | Branch A | FLIP: buf[0]=242 > 10 |
| id:000002 | 0b 80 42 00 | (none) | buf[1]=0x80 fails <20 |

## Proof of Branch Flip
id:000001 = bytes f2 00:
- Original seed buf[0]=5 (<=10) -> left branch
- QSYM-generated buf[0]=0xf2=242 (>10) -> right branch -> "Branch A"

## Notes on Solver=0s
Expected. QSYM uses opportunistic concrete-trace branch flipping before
invoking Z3. Z3 will run on targets requiring true symbolic reasoning
(magic bytes, checksums).

## What This Proves
1. AFL++ and QSYM can run simultaneously
2. QSYM reads seeds from AFL slave queue
3. QSYM runs target under Intel PIN
4. QSYM generates testcases and writes to its own queue
5. At least one generated testcase flips a branch

## Next Steps
- Record in hybrid-dse-scheduler repo
- Move to harder targets where Z3 actually runs
- Begin scheduler insertion point work
