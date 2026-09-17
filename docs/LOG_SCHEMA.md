# Raw Log Schema v1

## Design Rules
- Append-only. Never overwrite previous runs.
- Schema version included in every row.
- Raw logs immutable. Processed datasets are regenerable from raw logs.
- Separate predictors from outcomes explicitly.

## Schema

### `runs.csv`
| Field | Type | Description |
|:---|:---|:---|
| schema_version | string | e.g. "v1" |
| run_id | uuid | Unique per experiment run |
| program | string | Target program name |
| build_id | sha256 | SHA256 of binary |
| compiler | string | gcc/clang |
| optimization | string | -O0/-O1/-O2/-O3/-Os |
| seed_id | int | Fuzzer seed identifier |
| start_time | iso8601 | Run start |
| end_time | iso8601 | Run end |
| cpu_seconds | float | Total DSE CPU time |
| config_hash | sha256 | Hash of experiment config |

### `candidates.csv` (predictors + decision)
| Field | Type | Description |
|:---|:---|:---|
| schema_version | string | |
| run_id | uuid | FK to runs.csv |
| branch_id | string | build_id + module-relative offset |
| seed_id | int | |
| timestamp | iso8601 | Decision time |
| -- predictors -- | | |
| hit_count | int | Branch hit count before decision |
| taken_count | int | |
| not_taken_count | int | |
| prev_attempts | int | Previous DSE attempts on this branch |
| prev_sat | int | |
| prev_unsat | int | |
| prev_timeout | int | |
| path_length | int | |
| constraint_count | int | |
| target_depth | int | |
| sym_input_bytes | int | |
| ast_node_count | int | |
| ast_depth | int | |
| bb_size | int | |
| pred_count | int | |
| succ_count | int | |
| loop_member | bool | |
| branch_type | string | je/jne/jg/... |
| opt_level | string | |
| superblock_id | int | Optimization-shaped proxy |
| jump_table_member | bool | |
| -- decision -- | | |
| value_pred | float | Predicted utility |
| cost_pred | float | Predicted cost |
| roi_score | float | V/C |
| dispatched | bool | Was branch sent to DSE? |
| budget_ms | int | Allocated budget |

### `outcomes.csv` (post-decision)
| Field | Type | Description |
|:---|:---|:---|
| schema_version | string | |
| run_id | uuid | |
| branch_id | string | |
| timestamp | iso8601 | Solve completion time |
| solver_result | string | SAT/UNSAT/UNKNOWN/TIMEOUT |
| solver_time_ms | float | Actual solver time |
| testcase_generated | bool | |
| branch_flipped | bool | |
| old_edge_count | int | |
| new_edge_count | int | |
| new_edges | int | Difference |
| coverage_useful | bool | new_edges > 0 |

## Leakage Controls
- `outcomes.csv` fields are NEVER predictors.
- `value_pred`, `cost_pred`, `roi_score`, `dispatched`, `budget_ms` are decision-time fields, not predictors for the model being trained.
- For utility model training: predictors = candidates.csv predictor fields; label = outcomes.csv `coverage_useful`.
- For cost model training: predictors = candidates.csv predictor fields; label = outcomes.csv `solver_time_ms` or cost class.
