#!/usr/bin/env python3
"""
analyze.py — Cross-program AUROC analysis with bootstrap CIs.

Usage:
    analyze.py [--dataset FILE] [--out FILE]

Reads processed.csv, for each feature / family computes:
  - Within-program AUROC (random split)
  - Cross-program AUROC (train on one program, test on another)
  - Bootstrap 95% CI on each AUROC
Writes results to a CSV.
"""

import argparse
import csv
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

WORKSPACE = Path("/workspace")
DEFAULT_DATASET = WORKSPACE / "dataset" / "processed.csv"
DEFAULT_OUT = WORKSPACE / "dataset" / "analysis.csv"

# Feature families
FAMILIES = {
    "structural": ["path_length"],
    "history_freq": ["branch_hit_count"],
    "history_outcome": ["prev_sat", "prev_unsat", "prev_timeout"],
    "symbolic": ["constraint_count", "symbolized_bytes"],
    "opt_geometry": ["rtn_offset", "rtn_size", "rtn_cmov"],
    "opt_cfg": ["insn_pos_in_rtn", "rtn_insn_count", "rtn_branch_count",
                "rtn_indirect_count"],
    "opt_insn_mix": ["rtn_simd_count", "rtn_mem_ops"],
}

BASELINE = ["path_length", "branch_hit_count"]


def log(msg, level="INFO"):
    print("[{}] {}".format(level, msg), flush=True)


def load_dataset(path):
    rows = []
    with open(str(path)) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def to_xy(rows, features):
    X = []
    y = []
    for r in rows:
        try:
            x = [float(r[f]) for f in features]
            yv = 1 if r["is_interesting"] == "1" else 0
        except (KeyError, ValueError):
            continue
        X.append(x)
        y.append(yv)
    return X, y


def sigmoid(z):
    if z < -500: return 0.0
    if z > 500: return 1.0
    return 1.0 / (1.0 + math.exp(-z))


def train_lr(X, y, lr=0.05, epochs=3000):
    n = len(X)
    if n == 0 or len(X[0]) == 0:
        return None
    d = len(X[0])
    means = [sum(X[i][j] for i in range(n)) / n for j in range(d)]
    stds = []
    for j in range(d):
        v = sum((X[i][j] - means[j]) ** 2 for i in range(n)) / n
        stds.append(max(math.sqrt(v), 1e-9))
    Xn = [[(X[i][j] - means[j]) / stds[j] for j in range(d)] for i in range(n)]
    w = [0.0] * d
    b = 0.0
    for _ in range(epochs):
        gw = [0.0] * d
        gb = 0.0
        for i in range(n):
            z = b + sum(w[j] * Xn[i][j] for j in range(d))
            err = sigmoid(z) - y[i]
            for j in range(d):
                gw[j] += err * Xn[i][j]
            gb += err
        for j in range(d):
            w[j] -= lr * gw[j] / n
        b -= lr * gb / n
    return (w, b, means, stds)


def predict_lr(model, X):
    if model is None:
        return [0.5] * len(X)
    w, b, means, stds = model
    d = len(w)
    out = []
    for x in X:
        xn = [(x[j] - means[j]) / stds[j] for j in range(d)]
        z = b + sum(w[j] * xn[j] for j in range(d))
        out.append(sigmoid(z))
    return out


def auroc(scores, labels):
    pairs = sorted(zip(scores, labels), key=lambda p: -p[0])
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    n = len(pairs)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and pairs[j][0] == pairs[i][0]:
            j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg
        i = j
    sum_pos = sum(ranks[i] for i in range(n) if pairs[i][1] == 1)
    return 1.0 - (sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def bootstrap_ci(scores, labels, n_iter=500, alpha=0.05):
    """Bootstrap 95% CI on AUROC."""
    if len(scores) < 10:
        return (float("nan"), float("nan"))
    n = len(scores)
    aucs = []
    rng = random.Random(42)
    for _ in range(n_iter):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        s = [scores[i] for i in idx]
        l = [labels[i] for i in idx]
        if sum(l) == 0 or sum(l) == n:
            continue
        aucs.append(auroc(s, l))
    if not aucs:
        return (float("nan"), float("nan"))
    aucs.sort()
    lo = aucs[int(len(aucs) * alpha / 2)]
    hi = aucs[int(len(aucs) * (1 - alpha / 2))]
    return (lo, hi)


def cross_program_auroc(train_rows, test_rows, features):
    Xtr, ytr = to_xy(train_rows, features)
    Xte, yte = to_xy(test_rows, features)
    if not Xtr or not Xte:
        return (float("nan"), float("nan"), float("nan"))
    model = train_lr(Xtr, ytr)
    scores = predict_lr(model, Xte)
    auc = auroc(scores, yte)
    lo, hi = bootstrap_ci(scores, yte, n_iter=500)
    return (auc, lo, hi)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default=str(DEFAULT_DATASET))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    rows = load_dataset(args.dataset)
    log("loaded {} rows".format(len(rows)))

    # Group by program
    by_program = defaultdict(list)
    for r in rows:
        by_program[r["program"]].append(r)

    programs = sorted(by_program.keys())
    log("programs: {}".format(programs))

    if len(programs) < 2:
        log("need >= 2 programs for cross-program analysis", "ERROR")
        log("only 1 program present; run experiment on more targets", "WARN")
        # Still produce within-program results
        out_rows = []
        for prog in programs:
            prog_rows = by_program[prog]
            for fam_name, feats in list(FAMILIES.items()) + [("baseline", BASELINE)]:
                auc, lo, hi = cross_program_auroc(prog_rows, prog_rows, feats)
                out_rows.append({
                    "train_program": prog,
                    "test_program": prog,
                    "family": fam_name,
                    "features": "+".join(feats),
                    "auroc": "{:.4f}".format(auc),
                    "ci_lo": "{:.4f}".format(lo),
                    "ci_hi": "{:.4f}".format(hi),
                })
        with open(args.out, "w") as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            w.writeheader()
            for r in out_rows:
                w.writerow(r)
        log("wrote {} rows to {}".format(len(out_rows), args.out))
        return

    # Real cross-program analysis
    out_rows = []
    for train_prog in programs:
        for test_prog in programs:
            if train_prog == test_prog:
                continue
            train_rows = by_program[train_prog]
            test_rows = by_program[test_prog]
            for fam_name, feats in list(FAMILIES.items()) + [("baseline", BASELINE)]:
                auc, lo, hi = cross_program_auroc(train_rows, test_rows, feats)
                out_rows.append({
                    "train_program": train_prog,
                    "test_program": test_prog,
                    "family": fam_name,
                    "features": "+".join(feats),
                    "auroc": "{:.4f}".format(auc),
                    "ci_lo": "{:.4f}".format(lo),
                    "ci_hi": "{:.4f}".format(hi),
                })
                log("{:10s} -> {:10s} {:20s} AUC={:.3f} [{:.3f}, {:.3f}]".format(
                    train_prog, test_prog, fam_name, auc, lo, hi))

    with open(args.out, "w") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        for r in out_rows:
            w.writerow(r)
    log("wrote {} rows to {}".format(len(out_rows), args.out))


if __name__ == "__main__":
    main()
