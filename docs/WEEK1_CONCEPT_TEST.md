# Week 1 Concept Test

## Instructions
Close all notes. Answer from memory. Then reopen notes and correct.

## Questions
1. State the one-sentence thesis.
2. What is the primary metric?
3. What is V(b)? What is C(b)? What is R(b)?
4. Name the four feature families.
5. Name three optimization-shaped binary proxies.
6. What is the candidate branch pool? Name two inclusion criteria.
7. Why is the raw log append-only?
8. What is the branch ID scheme?
9. Name the first-choice DSE backend and the fallback.
10. What is the biggest open question in the paper?

## Answers (write yours first, then check)
1. Optimization-aware branch features + predicted SMT cost improve DSE dispatch and per-branch budgeting in x86-64 binary hybrid fuzzing.
2. New edges per DSE CPU second.
3. V = predicted utility; C = predicted cost; R = V / max(C, ε).
4. Coverage value, fuzzing difficulty, solvability history, predicted symbolic cost. (Plus optimization-shaped proxies.)
5. Superblock structure, jump-table membership, reduced instrumentation sites / branch simplification.
6. Uncovered, low-frequency, nontrivial downstream reward, not recently attempted.
7. So previous runs cannot be overwritten; processed data is regenerable.
8. build_id (SHA256 of binary) + module-relative branch offset.
9. First choice: Sydr; fallback: QSYM or Triton-based lightweight concolic backend.
10. Whether optimization-shaped binary features improve allocation enough on diverse real-world programs to justify their overhead.
