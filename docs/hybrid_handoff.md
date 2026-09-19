# Hybrid Handoff: AFL++ + QSYM

## Status
Working as of 2026-09-19.

## Environment
- Container image: zjuchenyuan/qsym (Ubuntu 16.04 base)
- Container run: docker run --cap-add=SYS_PTRACE -it -v ~/qsym_workspace:/workspace zjuchenyuan/qsym /bin/bash
- ptrace_scope inside container: 0
- AFL version: 2.52b at /afl
- QSYM: built from source inside container, installed via pip

## Directory Layout Inside Container
- QSYM repo: /workdir/qsym
- PIN tool: /workdir/qsym/qsym/pintool/obj-intel64/libqsym.so
- Z3: /workdir/qsym/third_party/z3/build/z3
- AFL: /afl
- QSYM launcher: /workdir/qsym/bin/run_qsym_afl.py

## Required Environment Variables
export PATH=$PATH:/afl:/workdir/qsym/bin
export AFL_SKIP_CPUFREQ=1
export AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1
export AFL_NO_AFFINITY=1
export AFL_PATH=/afl

## Launch Commands
afl-fuzz -M afl-master -i in -o out -- ./target
afl-fuzz -S afl-slave  -i in -o out -- ./target
run_qsym_afl.py -a afl-slave -o out -n qsym -- ./target

Notes:
- stdin targets: -- ./target (no @@)
- file targets: -- ./target @@
- QSYM requires stdin or symbolized fd; fopen(argv[1]) does NOT work

## First Successful Run
Target: toy_stdin.c (reads 4 bytes from stdin)
Seed: 05 0F 41 00 (LEFT branch)
QSYM generated f2 00 which flips to RIGHT branch (prints "Branch A")

Evidence: baseline/qsym/milestone_01/

## Solver Time Note
Solver=0s because QSYM opportunistically flips trivial branches without Z3.
Need magic bytes/checksums to observe nonzero solver time.

## Next Steps
1. Harder target forcing Z3 to run
2. Instrument per-branch solver time logging
3. Record first nonzero solver-time measurement
4. Identify scheduler insertion point
