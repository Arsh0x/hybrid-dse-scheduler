#!/usr/bin/env python3
"""
extract_dataset.py — Combine run logs into a single dataset.

Usage:
    extract_dataset.py [--runs-dir DIR] [--out FILE] [--minutes N]

--minutes N: only include candidates within the first N minutes of each run.
             If omitted, include everything.
"""

import argparse
import csv
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


def read_start_time(run_dir):
    p = run_dir / "start_time.txt"
    if not p.exists():
        return None
    try:
        with open(str(p)) as f:
            return float(f.read().strip())
    except Exception:
        return None


def load_solver_timing(path):
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


def extract_run(run_dir, program, compiler, opt, rep, cutoff_us):
    """Yield combined rows for one run."""
    logs_dir = run_dir / "logs"
    cand_path = logs_dir / "candidates.csv"
    solver_path = logs_dir / "solver_timing.csv"

    if not cand_path.exists():
        log("no candidates.csv in {}".format(logs_dir), "WARN")
        return

    solver_rows = load_solver_timing(solver_path)
    run_id = "{}-{}-{}-rep{}".format(program, compiler, opt, rep)

    with open(str(cand_path)) as f:
        r = csv.DictReader(f)
        for c in r:
            ts = int(c["timestamp_us"])
            if cutoff_us is not None and ts > cutoff_us:
                continue

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

            if c["is_interesting"] == "1":
                outcome = find_solver_outcome(solver_rows, c["branch_id"], ts)
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
    if not runs_dir.exists():
        log("runs dir not found: {}".format(runs_dir), "ERROR")
        return
    for prog_dir in sorted(runs_dir.iterdir()):
        if not prog_dir.is_dir():
            continue
        for cfg_dir in sorted(prog_dir.iterdir()):
            if not cfg_dir.is_dir():
                continue
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
    ap.add_argument("--minutes", type=int, default=None,
                    help="Only include first N minutes of each run")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with open(str(out_path), "w") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()

        for run_dir, program, compiler, opt, rep in walk_runs(runs_dir):
            start = read_start_time(run_dir)
            if args.minutes is not None and start is not None:
                cutoff_us = int((start + args.minutes * 60) * 1e6)
            else:
                cutoff_us = None

            count = 0
            for row in extract_run(run_dir, program, compiler, opt, rep, cutoff_us):
                w.writerow(row)
                count += 1
            if count > 0:
                label = "{} (cutoff {}min)".format(run_dir, args.minutes) \
                    if args.minutes else str(run_dir)
                log("{} rows from {}".format(count, label))
            total += count

    log("=== DONE ===")
    log("total rows: {}".format(total))
    log("output: {}".format(out_path))


if __name__ == "__main__":
    main()
