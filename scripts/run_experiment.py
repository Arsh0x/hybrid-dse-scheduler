#!/usr/bin/env python3
"""
run_experiment.py — Run a hybrid fuzzing experiment.
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/workspace")
BUILDS_DIR = WORKSPACE / "builds"
RUNS_DIR = WORKSPACE / "runs"
LOGS_DIR = WORKSPACE / "logs"
STATE_DIR = WORKSPACE / "state"


def log(msg, level="INFO"):
    print("[{}] {}".format(level, msg), flush=True)


def die(msg):
    log(msg, "ERROR")
    sys.exit(1)


def setup_environment():
    env = os.environ.copy()
    env["PATH"] = env.get("PATH", "") + ":/afl:/workdir/qsym/bin"
    env["AFL_SKIP_CPUFREQ"] = "1"
    env["AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES"] = "1"
    env["AFL_NO_AFFINITY"] = "1"
    env["AFL_PATH"] = "/afl"
    return env


def cleanup_previous_logs():
    for f in ["candidates.csv", "solver_timing.csv"]:
        p = LOGS_DIR / f
        if p.exists():
            p.unlink()
    h = STATE_DIR / "branch_history.csv"
    if h.exists():
        h.unlink()


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
    return run_dir, afl_out


def run_experiment(program, compiler, opt, rep, minutes, env):
    binary, args, uses_stdin = get_target_cmd(program, compiler, opt)
    if uses_stdin:
        target_cmd = [binary] + args
    else:
        target_cmd = [binary] + args + ["@@"]
    log("target: {}".format(" ".join(target_cmd)))

    run_dir, afl_out = prepare_run_dir(program, compiler, opt, rep)
    seeds_dir = get_build_dir(program, compiler, opt) / "seeds"
    if not seeds_dir.exists() or not any(seeds_dir.iterdir()):
        die("no seeds at {}".format(seeds_dir))

    cleanup_previous_logs()

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

    log("copying logs...")
    for f in ["candidates.csv", "solver_timing.csv"]:
        src = LOGS_DIR / f
        if src.exists():
            shutil.copy(str(src), str(run_dir / f))
        else:
            log("warning: {} not found".format(src), "WARN")
    h = STATE_DIR / "branch_history.csv"
    if h.exists():
        shutil.copy(str(h), str(run_dir / "branch_history.csv"))

    meta = {
        "program": program,
        "compiler": compiler,
        "opt": opt,
        "repetition": rep,
        "minutes": minutes,
        "finished_at": datetime.utcnow().isoformat() + "Z",
        "target_cmd": target_cmd,
    }
    with open(str(run_dir / "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    cand = run_dir / "candidates.csv"
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
    args = parser.parse_args()
    env = setup_environment()
    run_experiment(args.program, args.compiler, args.opt,
                   args.repetition, args.minutes, env)


if __name__ == "__main__":
    main()
