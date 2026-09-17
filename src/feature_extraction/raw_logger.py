"""
Append-only raw logger for DSE scheduler experiments.
Schema version: v1
"""
import csv
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "v1"
RAW_DIR = Path("data/raw")

RUNS_FIELDS = [
    "schema_version", "run_id", "program", "build_id", "compiler",
    "optimization", "seed_id", "start_time", "end_time",
    "cpu_seconds", "config_hash",
]

CANDIDATE_FIELDS = [
    "schema_version", "run_id", "branch_id", "seed_id", "timestamp",
    # predictors
    "hit_count", "taken_count", "not_taken_count",
    "prev_attempts", "prev_sat", "prev_unsat", "prev_timeout",
    "path_length", "constraint_count", "target_depth",
    "sym_input_bytes", "ast_node_count", "ast_depth",
    "bb_size", "pred_count", "succ_count", "loop_member", "branch_type",
    "opt_level", "superblock_id", "jump_table_member",
    # decision
    "value_pred", "cost_pred", "roi_score", "dispatched", "budget_ms",
]

OUTCOME_FIELDS = [
    "schema_version", "run_id", "branch_id", "timestamp",
    "solver_result", "solver_time_ms", "testcase_generated",
    "branch_flipped", "old_edge_count", "new_edge_count",
    "new_edges", "coverage_useful",
]


def _append_row(path: Path, fields, row: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in fields})


def new_run_id() -> str:
    return str(uuid.uuid4())


def log_run(run_id, program, build_id, compiler, optimization, seed_id,
            start_time, end_time, cpu_seconds, config_hash):
    _append_row(RAW_DIR / "runs.csv", RUNS_FIELDS, {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "program": program,
        "build_id": build_id,
        "compiler": compiler,
        "optimization": optimization,
        "seed_id": seed_id,
        "start_time": start_time,
        "end_time": end_time,
        "cpu_seconds": cpu_seconds,
        "config_hash": config_hash,
    })


def log_candidate(run_id, branch_id, seed_id, **kwargs):
    row = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "branch_id": branch_id,
        "seed_id": seed_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    row.update(kwargs)
    _append_row(RAW_DIR / "candidates.csv", CANDIDATE_FIELDS, row)


def log_outcome(run_id, branch_id, solver_result, solver_time_ms,
                testcase_generated, branch_flipped, old_edge_count,
                new_edge_count):
    _append_row(RAW_DIR / "outcomes.csv", OUTCOME_FIELDS, {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "branch_id": branch_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "solver_result": solver_result,
        "solver_time_ms": solver_time_ms,
        "testcase_generated": testcase_generated,
        "branch_flipped": branch_flipped,
        "old_edge_count": old_edge_count,
        "new_edge_count": new_edge_count,
        "new_edges": new_edge_count - old_edge_count,
        "coverage_useful": new_edge_count > old_edge_count,
    })
