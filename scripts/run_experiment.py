#!/usr/bin/env python3
"""
run_experiment.py — Run a hybrid fuzzing experiment.

Usage:
    run_experiment.py <program> <compiler> <opt> <repetition> [--minutes N] [--checkpoint-hours 1,6,12]
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/workspace")
BUILDS_DIR = WORKSPACE / "builds"
RUNS_DIR = WORKSPACE / "runs"


def log(msg, level="INFO"):
    print("[{}] {}".format(level, msg), flush=True)


def die(msg):
    log(msg, "ERROR")
    sys.exit(1)


def setup_environment(run_logs_dir):
    env = os.environ.copy()
    env["PATH"] = env.get("PATH", "") + ":/afl:/workdir/qsym/bin"
    env["AFL_SKIP_CPUFREQ"] = "1"
    env["AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES"] = "1"
    env["AFL_NO_AFFINITY"] = "1"
    env["AFL_PATH"] = "/afl"
    # Per-run QSYM log paths (avoids collisions between parallel runs)
    env["QSYM_LOG_FILE"] = str(run_logs_dir / "solver_timing.csv")
    env["QSYM_CANDIDATE_LOG"] = str(run_logs_dir / "candidates.csv")
    env["QSYM_HISTORY_FILE"] = str(run_logs_dir / "branch_history.csv")
    return env


def get_build_dir(program, compiler, opt):
    d = BUILDS_DIR / program / "{}-{}".format(compiler, opt)
    if not d.exists():
        die("build dir not found: {}".format(d))
    return d


def get_target_cmd(program, compiler, opt):
    build_dir = get_build_dir(program, compiler, opt)
    src = build_dir / "src"
    import yaml
    meta_path = WORKSPACE / "benchmarks" / program / "metadata.yaml"
    with open(str(meta_path)) as f:
        meta = yaml.safe_load(f)
    binary = src / meta["target"]["binary"]
    if not binary.exists():
        die("target binary not found: {}".format(binary))
    args = meta["target"].get("args", [])
    uses_stdin = meta["target"].get("stdin_mode", True)
    return str(binary), args, uses_stdin


def prepare_run_dir(program, compiler, opt, rep):
    run_dir = RUNS_DIR / program / "{}-{}".format(compiler, opt) / "rep-{}".format(rep)
    if run_dir.exists():
        log("removing previous run dir {}".format(run_dir))
        shutil.rmtree(str(run_dir))
    run_dir.mkdir(parents=True)
    afl_out = run_dir / "afl-out"
    afl_out.mkdir()
    logs_dir = run_dir / "logs"
    logs_dir.mkdir()
    return run_dir, afl_out, logs_dir


def checkpoint_worker(run_dir, logs_dir, total_minutes, checkpoint_hours):
    """Background thread that snapshots logs at specified hour marks."""
    start = time.time()
    for hour in sorted(checkpoint_hours):
        target_sec = hour * 3600
        if target_sec > total_minutes * 60:
            continue
        sleep_secs = target_sec - (time.time() - start)
        if sleep_secs > 0:
            time.sleep(sleep_secs)
        cp_dir = run_dir / "checkpoints" / "{}h".format(hour)
        cp_dir.mkdir(parents=True, exist_ok=True)
        for f in ["candidates.csv", "solver_timing.csv", "branch_history.csv"]:
            src = logs_dir / f
            if src.exists():
                try:
                    shutil.copy(str(src), str(cp_dir / f))
                except Exception as e:
                    log("checkpoint copy failed: {}".format(e), "WARN")
        with open(str(cp_dir / "checkpoint.txt"), "w") as f:
            f.write("hour={} wall_time={}\n".format(hour, time.time()))
        log("checkpoint {}h saved to {}".format(hour, cp_dir))


def run_experiment(program, compiler, opt, rep, minutes, checkpoint_hours):
    binary, args, uses_stdin = get_target_cmd(program, compiler, opt)
    if uses_stdin:
        target_cmd = [binary] + args
    else:
        target_cmd = [binary] + args + ["@@"]
    log("target: {}".format(" ".join(target_cmd)))

    run_dir, afl_out, logs_dir = prepare_run_dir(program, compiler, opt, rep)
    env = setup_environment(logs_dir)
    seeds_dir = get_build_dir(program, compiler, opt) / "seeds"
    if not seeds_dir.exists() or not any(seeds_dir.iterdir()):
        die("no seeds at {}".format(seeds_dir))

    # Write start_time.txt for later filtering
    start_sec = time.time()
    with open(str(run_dir / "start_time.txt"), "w") as f:
        f.write("{}\n".format(start_sec))

    # Start checkpoint thread
    if checkpoint_hours:
        t = threading.Thread(target=checkpoint_worker,
                             args=(run_dir, logs_dir, minutes, checkpoint_hours))
        t.daemon = True
        t.start()
        log("checkpoint hours: {}".format(sorted(checkpoint_hours)))

    master_log = run_dir / "afl_master.log"
    log("starting afl master...")
    master_proc = subprocess.Popen(
        ["afl-fuzz", "-M", "afl-master",
         "-i", str(seeds_dir), "-o", str(afl_out), "--"] + target_cmd,
        env=env,
        stdout=open(str(master_log), "w"),
        stderr=subprocess.STDOUT)
    time.sleep(8)

    slave_log = run_dir / "afl_slave.log"
    log("starting afl slave...")
    slave_proc = subprocess.Popen(
        ["afl-fuzz", "-S", "afl-slave",
         "-i", str(seeds_dir), "-o", str(afl_out), "--"] + target_cmd,
        env=env,
        stdout=open(str(slave_log), "w"),
        stderr=subprocess.STDOUT)
    time.sleep(8)

    qsym_log = run_dir / "qsym.log"
    log("starting qsym...")
    qsym_proc = subprocess.Popen(
        ["run_qsym_afl.py", "-a", "afl-slave",
         "-o", str(afl_out), "-n", "qsym", "--"] + target_cmd,
        env=env,
        stdout=open(str(qsym_log), "w"),
        stderr=subprocess.STDOUT)

    log("running for {} minutes...".format(minutes))
    try:
        time.sleep(minutes * 60)
    except KeyboardInterrupt:
        log("interrupted by user")

    log("stopping processes...")
    for p in [qsym_proc, slave_proc, master_proc]:
        try:
            p.send_signal(signal.SIGTERM)
        except Exception:
            pass
    time.sleep(3)
    for p in [qsym_proc, slave_proc, master_proc]:
        try:
            p.kill()
        except Exception:
            pass

    # Write metadata
    meta = {
        "program": program,
        "compiler": compiler,
        "opt": opt,
        "repetition": rep,
        "minutes": minutes,
        "checkpoint_hours": sorted(checkpoint_hours),
        "start_time": start_sec,
        "finished_at": datetime.utcnow().isoformat() + "Z",
        "target_cmd": target_cmd,
    }
    with open(str(run_dir / "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    # Summary
    cand = logs_dir / "candidates.csv"
    if cand.exists():
        with open(str(cand)) as f:
            n_cand = sum(1 for _ in f) - 1
        log("=== COMPLETE ===")
        log("candidates: {}".format(n_cand))
        log("run dir: {}".format(run_dir))
    else:
        log("=== COMPLETE (no candidates.csv) ===", "WARN")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program")
    parser.add_argument("compiler")
    parser.add_argument("opt")
    parser.add_argument("repetition", type=int)
    parser.add_argument("--minutes", type=int, default=10)
    parser.add_argument("--checkpoint-hours", default="",
                        help="Comma-separated hour marks for log snapshots, e.g. 1,6,12")
    args = parser.parse_args()

    ckpts = []
    if args.checkpoint_hours:
        ckpts = [int(h.strip()) for h in args.checkpoint_hours.split(",") if h.strip()]

    run_experiment(args.program, args.compiler, args.opt,
                   args.repetition, args.minutes, ckpts)


if __name__ == "__main__":
    main()
