#!/usr/bin/env python3
"""
run_experiment.py — Run a hybrid fuzzing experiment with QSYM watchdog.

Usage:
    run_experiment.py <program> <compiler> <opt> <rep> [--minutes N]
                       [--checkpoint-hours 1,6,12] [--watchdog-stale 180]
                       [--no-watchdog]
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
    ts = datetime.utcnow().strftime("%H:%M:%S")
    print("[{}][{}] {}".format(ts, level, msg), flush=True)


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


def checkpoint_worker(run_dir, logs_dir, total_minutes, checkpoint_hours, stop_flag):
    start = time.time()
    for hour in sorted(checkpoint_hours):
        target_sec = hour * 3600
        if target_sec > total_minutes * 60:
            continue
        while not stop_flag.is_set():
            elapsed = time.time() - start
            if elapsed >= target_sec:
                break
            time.sleep(min(30, target_sec - elapsed))
        if stop_flag.is_set():
            return
        cp_dir = run_dir / "checkpoints" / "{}h".format(hour)
        cp_dir.mkdir(parents=True, exist_ok=True)
        for f in ["candidates.csv", "solver_timing.csv", "branch_history.csv"]:
            src = logs_dir / f
            if src.exists():
                try:
                    shutil.copy(str(src), str(cp_dir / f))
                except Exception as e:
                    log("checkpoint copy failed: {}".format(e), "WARN")
        log("checkpoint {}h saved".format(hour))


class QSYMWatchdog(threading.Thread):
    """
    Watchdog that restarts QSYM if:
      - its log file hasn't been modified for `stale_seconds`
      - its process exits unexpectedly
    Uses setsid to give QSYM its own process group so killpg works.
    """

    def __init__(self, run_dir, afl_out, target_cmd, env,
                 stale_seconds=180, check_interval=30):
        super().__init__()
        self.daemon = True
        self.run_dir = run_dir
        self.afl_out = afl_out
        self.target_cmd = target_cmd
        self.env = env
        self.stale_seconds = stale_seconds
        self.check_interval = check_interval
        self.stop_flag = threading.Event()
        self.qsym_proc = None
        self.restart_count = 0
        self.log_fh = None
        self.restart_log = run_dir / "qsym_restarts.log"

    def _open_log(self):
        qsym_log = self.run_dir / "qsym.log"
        self.log_fh = open(str(qsym_log), "a")
        self.log_fh.write("\n=== QSYM START #{} at {} ===\n".format(
            self.restart_count, datetime.utcnow().isoformat()))
        self.log_fh.flush()

    def start_qsym(self):
        self._open_log()
        try:
            self.qsym_proc = subprocess.Popen(
                ["run_qsym_afl.py", "-a", "afl-slave",
                 "-o", str(self.afl_out), "-n", "qsym", "--"] + self.target_cmd,
                env=self.env,
                stdout=self.log_fh,
                stderr=subprocess.STDOUT,
                start_new_session=True)
        except Exception as e:
            log("watchdog: failed to start QSYM: {}".format(e), "ERROR")
            self.qsym_proc = None
        return self.qsym_proc

    def kill_qsym_tree(self):
        if self.qsym_proc is None:
            return
        try:
            pgid = os.getpgid(self.qsym_proc.pid)
            os.killpg(pgid, signal.SIGKILL)
            log("watchdog: sent SIGKILL to pgid {}".format(pgid), "WARN")
        except Exception as e:
            log("watchdog: killpg failed: {}".format(e), "WARN")
        try:
            self.qsym_proc.wait(timeout=5)
        except Exception:
            pass
        self.qsym_proc = None

    def _log_restart(self, reason):
        with open(str(self.restart_log), "a") as f:
            f.write("{}\trestart#\t{}\t{}\n".format(
                datetime.utcnow().isoformat(), self.restart_count, reason))

    def run(self):
        time.sleep(5)
        while not self.stop_flag.is_set():
            self.stop_flag.wait(self.check_interval)
            if self.stop_flag.is_set():
                return
            if self.qsym_proc is None:
                continue
            # Check process alive
            ret = self.qsym_proc.poll()
            if ret is not None:
                log("watchdog: QSYM exited with code {}".format(ret), "WARN")
                self.restart_count += 1
                self._log_restart("exited_{}".format(ret))
                self.start_qsym()
                continue
            # Check log staleness
            qsym_log = self.run_dir / "qsym.log"
            try:
                age = time.time() - qsym_log.stat().st_mtime
            except Exception:
                age = 0
            if age > self.stale_seconds:
                log("watchdog: QSYM log stale {:.0f}s (threshold {}s) — restarting".format(
                    age, self.stale_seconds), "WARN")
                self.restart_count += 1
                self._log_restart("stale_{}s".format(int(age)))
                self.kill_qsym_tree()
                self.start_qsym()

    def stop(self):
        self.stop_flag.set()


def run_experiment(program, compiler, opt, rep, minutes, checkpoint_hours,
                   watchdog_stale, use_watchdog):
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

    start_sec = time.time()
    with open(str(run_dir / "start_time.txt"), "w") as f:
        f.write("{}\n".format(start_sec))

    stop_flag = threading.Event()

    # Checkpoint thread
    if checkpoint_hours:
        t = threading.Thread(target=checkpoint_worker,
                             args=(run_dir, logs_dir, minutes, checkpoint_hours, stop_flag))
        t.daemon = True
        t.start()
        log("checkpoint hours: {}".format(sorted(checkpoint_hours)))

    # Start AFL master
    master_log = run_dir / "afl_master.log"
    log("starting afl master...")
    master_proc = subprocess.Popen(
        ["afl-fuzz", "-M", "afl-master",
         "-i", str(seeds_dir), "-o", str(afl_out), "--"] + target_cmd,
        env=env,
        stdout=open(str(master_log), "w"),
        stderr=subprocess.STDOUT)
    time.sleep(8)

    # Start AFL slave
    slave_log = run_dir / "afl_slave.log"
    log("starting afl slave...")
    slave_proc = subprocess.Popen(
        ["afl-fuzz", "-S", "afl-slave",
         "-i", str(seeds_dir), "-o", str(afl_out), "--"] + target_cmd,
        env=env,
        stdout=open(str(slave_log), "w"),
        stderr=subprocess.STDOUT)
    time.sleep(8)

    # Start QSYM (either with or without watchdog)
    qsym_proc = None
    watchdog = None
    if use_watchdog:
        log("starting qsym (with watchdog, stale={}s)...".format(watchdog_stale))
        watchdog = QSYMWatchdog(run_dir, afl_out, target_cmd, env,
                                stale_seconds=watchdog_stale)
        watchdog.start()
        watchdog.start_qsym()
    else:
        log("starting qsym (no watchdog)...")
        qsym_log = run_dir / "qsym.log"
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
    stop_flag.set()

    if watchdog is not None:
        watchdog.stop()
        watchdog.kill_qsym_tree()
    if qsym_proc is not None:
        try:
            qsym_proc.send_signal(signal.SIGTERM)
        except Exception:
            pass

    for p in [slave_proc, master_proc]:
        try:
            p.send_signal(signal.SIGTERM)
        except Exception:
            pass
    time.sleep(3)
    for p in [slave_proc, master_proc]:
        try:
            p.kill()
        except Exception:
            pass

    # Summary
    restart_count = watchdog.restart_count if watchdog else 0

    meta = {
        "program": program,
        "compiler": compiler,
        "opt": opt,
        "repetition": rep,
        "minutes": minutes,
        "checkpoint_hours": sorted(checkpoint_hours),
        "watchdog_enabled": use_watchdog,
        "watchdog_stale_seconds": watchdog_stale,
        "watchdog_restarts": restart_count,
        "start_time": start_sec,
        "finished_at": datetime.utcnow().isoformat() + "Z",
        "target_cmd": target_cmd,
    }
    with open(str(run_dir / "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    cand = logs_dir / "candidates.csv"
    if cand.exists():
        with open(str(cand)) as f:
            n_cand = sum(1 for _ in f) - 1
        log("=== COMPLETE ===")
        log("candidates: {}".format(n_cand))
        log("watchdog restarts: {}".format(restart_count))
        log("run dir: {}".format(run_dir))
    else:
        log("=== COMPLETE (no candidates.csv) ===", "WARN")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("program")
    ap.add_argument("compiler")
    ap.add_argument("opt")
    ap.add_argument("repetition", type=int)
    ap.add_argument("--minutes", type=int, default=10)
    ap.add_argument("--checkpoint-hours", default="")
    ap.add_argument("--watchdog-stale", type=int, default=180,
                    help="Restart QSYM if log stale for N seconds (default: 180)")
    ap.add_argument("--no-watchdog", action="store_true",
                    help="Disable QSYM watchdog (for debugging)")
    args = ap.parse_args()

    ckpts = []
    if args.checkpoint_hours:
        ckpts = [int(h.strip()) for h in args.checkpoint_hours.split(",") if h.strip()]

    run_experiment(args.program, args.compiler, args.opt,
                   args.repetition, args.minutes, ckpts,
                   args.watchdog_stale, not args.no_watchdog)


if __name__ == "__main__":
    main()
