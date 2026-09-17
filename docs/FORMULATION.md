# Problem Formulation

## Notation

- `b` : candidate branch
- `V(b)` : predicted utility of running DSE on branch `b`
- `C(b)` : predicted cost (solver time or timeout risk) of running DSE on `b`
- `R(b)` : return on investment score

## Utility Definition (frozen before training)

Primary binary label:
  V_label(b) = 1 if DSE on b produces ≥1 previously unseen edge, else 0.

Secondary outcomes preserved separately:
  - branch inversion success (binary)
  - new_edge_count (integer)

## Cost Definition

Operational cost classes derived from empirical quantiles of solver time:
  - cheap      : solver_time < q50
  - medium     : q50 ≤ solver_time < q90
  - expensive  : q90 ≤ solver_time < timeout
  - timeout-risk : solver_time ≥ timeout OR result == UNKNOWN

Continuous alternative: log(solver_time_ms + 1).

## Return / ROI Score

  R(b) = V(b) / max(C(b), ε)

Dispatch rule: rank candidates by R(b), solve top-k under per-branch budget.

## Budget Allocator

Minimal: 3-tier timeout bins mapped from predicted cost class.
Stronger: continuous budget B(b) = B_total * R(b) / Σ R(b).

## Decision Boundary

A branch is dispatched to DSE iff:
  - it is in the candidate pool (uncovered, low-frequency, nontrivial downstream reward), AND
  - R(b) ≥ threshold, AND
  - remaining global DSE budget > 0.
