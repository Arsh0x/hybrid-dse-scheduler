# Candidate Branch Pool Definition

## Motivation
Do not solve every branch in a trace. Even LeanSym notes that more advanced branch selection is still open and can amplify efficiency. Solving all branches wastes symbolic effort on already-covered, low-yield, or unsolvable branches.

## Inclusion Criteria (all must hold)

1. **Uncovered:** branch target edge has not been hit by the fuzzer.
2. **Low-frequency:** branch hit count below a program-relative threshold (e.g., below q25 of observed hit counts).
3. **Nontrivial downstream reward:** branch leads to a path with at least one basic block not yet covered.
4. **Not recently attempted:** branch not solved or timed out in the last N DSE attempts on this program.
5. **In scope:** branch is reachable from the current seed's trace.

## Exclusion Criteria (any is sufficient)

- Already covered edge.
- Repeatedly timed out with no state change (unless history features say retry is worthwhile).
- Branch is in a known-uninteresting region (e.g., error handling that does not unlock new code).
- Branch constraint is trivially satisfiable by mutation (predicted by fuzzing-difficulty features).

## Operationalization

```python
pool = []
for branch in trace.branches:
    if branch.edge in covered_edges: continue
    if branch.hit_count > q25(hit_counts): continue
    if not has_downstream_uncovered(branch): continue
    if recently_attempted(branch, window=N): continue
    if not reachable_from(seed, branch): continue
    pool.append(branch)
```

## Parameters to Freeze

| Parameter | Default | Rationale |
|:---|:---:|:---|
| hit_count threshold | q25 | Program-relative, not absolute |
| recently_attempted window N | 5 | Avoid repeated waste |
| downstream_uncovered depth | 1 basic block | Conservative |

## Open Questions
- Should the pool be per-seed or per-program?
- How to handle branches that become reachable only after partial solving?
- Should pool size be capped to avoid combinatorial explosion?
