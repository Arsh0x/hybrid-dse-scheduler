#!/usr/bin/env python3
"""
extract_dataset.py — Combine run logs into a single dataset.

Usage:
    extract_dataset.py [--runs-dir DIR] [--out FILE]

Walks /workspace/runs/*/<compiler>-<opt>/rep-N/, joins candidates.csv
with solver_timing.csv, writes a single combined CSV.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

WORKSPACE = Path("/workspace")
DEFAULT_RUNS = WORKSPACE / "runs"
DEFAULT_OUT = WORKSPACE / "dataset" / "processed.csv"

FEATURE_COLS = [
    "constraint_count", "path_length", "symbolized_bytes",
    "branch_hit_count", "prev_sat", "prev_unsat", "prev_timeout",
    "rtn_offset", "rtn_size", "rtn_cmov",
    "insn_pos_in_rtn", "rtn_insn_count", "rtn_branch_count",
    "rtn_indirect_count", "rtn_simd_count", "rtn_mem_ops",
]

OUT_COLS = (
    ["run_id", "program", "compiler", "opt", "repetition",
     "candidate_id", "timestamp_us", "branch_id",
     "is_interesting", "taken"]
    + FEATURE_COLS
    + ["solver_result", "solver_time_us"]
)


def log(msg, level="INFO"):
    print("[{}] {}".format(level, msg), flush=True)


def load_solver_timing(path):
    """Return list of solver rows sorted by timestamp."""
    if not path.exists():
        return []
    rows = []
    with open(str(path)) as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    rows.sort(key=lambda x: int(x["timestamp_us"]))
    return rows


def find_solver_outcome(solver_rows, branch_id, cand_ts, window_us=100000):
    """Find solver outcome for this branch near the candidate timestamp."""
    best = None
    best_delta = None
    for s in solver_rows:
        if s["branch_id"] != branch_id:
            continue
        delta = abs(int(s["timestamp_us"]) - cand_ts)
        if delta <= window_us and (best_delta is None or delta < best_delta):
            best = s
            best_delta = delta
    return best


def extract_run(run_dir, program, compiler, opt, rep):
    """Yield combined rows for one run."""
    cand_path = run_dir / "candidates.csv"
    solver_path = run_dir / "solver_timing.csv"

    if not cand_path.exists():
        log("no candidates.csv in {}".format(run_dir), "WARN")
        return

    solver_rows = load_solver_timing(solver_path)
    run_id = "{}-{}-{}-rep{}".format(program, compiler, opt, rep)

    with open(str(cand_path)) as f:
        r = csv.DictReader(f)
        for c in r:
            row = {
                "run_id": run_id,
                "program": program,
                "compiler": compiler,
                "opt": opt,
                "repetition": rep,
                "candidate_id": c["candidate_id"],
                "timestamp_us": c["timestamp_us"],
                "branch_id": c["branch_id"],
                "is_interesting": c["is_interesting"],
                "taken": c["taken"],
            }
            for col in FEATURE_COLS:
                row[col] = c.get(col, "")

            # Attach solver outcome if interesting
            if c["is_interesting"] == "1":
                outcome = find_solver_outcome(
                    solver_rows, c["branch_id"], int(c["timestamp_us"]))
                if outcome:
                    row["solver_result"] = outcome["result"]
                    row["solver_time_us"] = outcome["elapsed_us"]
                else:
                    row["solver_result"] = ""
                    row["solver_time_us"] = ""
            else:
                row["solver_result"] = ""
                row["solver_time_us"] = ""

            yield row


def walk_runs(runs_dir):
    """Yield (run_dir, program, compiler, opt, rep) tuples."""
    if not runs_dir.exists():
        log("runs dir not found: {}".format(runs_dir), "ERROR")
        return
    for prog_dir in sorted(runs_dir.iterdir()):
        if not prog_dir.is_dir():
            continue
        for cfg_dir in sorted(prog_dir.iterdir()):
            if not cfg_dir.is_dir():
                continue
            # cfg_dir name is like gcc-O2
            parts = cfg_dir.name.rsplit("-", 1)
            if len(parts) != 2:
                continue
            compiler, opt = parts
            for rep_dir in sorted(cfg_dir.iterdir()):
                if not rep_dir.is_dir() or not rep_dir.name.startswith("rep-"):
                    continue
                try:
                    rep = int(rep_dir.name.split("-")[1])
                except Exception:
                    continue
                yield (rep_dir, prog_dir.name, compiler, opt, rep)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs-dir", default=str(DEFAULT_RUNS))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with open(str(out_path), "w") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()

        for run_dir, program, compiler, opt, rep in walk_runs(runs_dir):
            count = 0
            for row in extract_run(run_dir, program, compiler, opt, rep):
                w.writerow(row)
                count += 1
            if count > 0:
                log("{} rows from {}".format(count, run_dir))
            total += count

    log("=== DONE ===")
    log("total rows: {}".format(total))
    log("output: {}".format(out_path))


if __name__ == "__main__":
    main()
