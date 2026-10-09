import csv, math
from collections import defaultdict

def load(path):
    return list(csv.DictReader(open(path)))

def to_xy(rows, features):
    X, y = [], []
    for r in rows:
        try:
            x = [float(r[f]) for f in features]
            yv = 1 if r['is_interesting'] == '1' else 0
        except (KeyError, ValueError):
            continue
        X.append(x)
        y.append(yv)
    return X, y

def sigmoid(z):
    if z < -500: return 0.0
    if z > 500: return 1.0
    return 1.0 / (1.0 + math.exp(-z))

def has_variance(X):
    """True if any column has non-zero variance."""
    if not X:
        return False
    n = len(X)
    d = len(X[0])
    for j in range(d):
        col = [X[i][j] for i in range(n)]
        m = sum(col) / n
        var = sum((v - m) ** 2 for v in col) / n
        if var > 1e-9:
            return True
    return False

def train_lr(X, y, lr=0.05, epochs=2000):
    if not X:
        return None
    n = len(X)
    d = len(X[0])
    means = [sum(X[i][j] for i in range(n)) / n for j in range(d)]
    stds = []
    for j in range(d):
        v = sum((X[i][j] - means[j]) ** 2 for i in range(n)) / n
        s = math.sqrt(v)
        stds.append(s if s > 1e-9 else 1.0)
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

def predict(model, X):
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

FAMILIES = {
    'structural': ['path_length'],
    'history_freq': ['branch_hit_count'],
    'symbolic': ['constraint_count', 'symbolized_bytes'],
    'history_outcome': ['prev_sat', 'prev_unsat', 'prev_timeout'],
    'opt_geometry': ['rtn_offset', 'rtn_size', 'rtn_cmov'],
    'opt_cfg': ['insn_pos_in_rtn', 'rtn_insn_count', 'rtn_branch_count', 'rtn_indirect_count'],
    'opt_insn_mix': ['rtn_simd_count', 'rtn_mem_ops'],
    'baseline': ['path_length', 'branch_hit_count'],
}

rows = load('/workspace/dataset/processed_mainonly.csv')

by_prog_rep = defaultdict(lambda: defaultdict(list))
for r in rows:
    by_prog_rep[r['program']][int(r['repetition'])].append(r)

print('=== Per-rep candidate counts (main-module only) ===')
for prog in ['zlib', 'libpng']:
    for rep in sorted(by_prog_rep[prog].keys()):
        print('  {:8s} rep-{}: {}'.format(prog, rep, len(by_prog_rep[prog][rep])))

print()
print('=== Per-rep AUROC (libpng -> zlib) ===')
header = '{:20s}'.format('family')
for rep in [1,2,3,4,5]:
    header += '{:>8s}'.format('r'+str(rep))
header += '{:>10s}{:>8s}'.format('mean','std')
print(header)

for fam, feats in FAMILIES.items():
    aurocs = []
    for rep in [1,2,3,4,5]:
        train = by_prog_rep['libpng'].get(rep, [])
        test = by_prog_rep['zlib'].get(rep, [])
        Xtr, ytr = to_xy(train, feats)
        Xte, yte = to_xy(test, feats)
        if not Xtr or not Xte:
            aurocs.append(None)
            continue
        if not has_variance(Xtr):
            aurocs.append(None)
            continue
        if len(set(ytr)) < 2 or len(set(yte)) < 2:
            aurocs.append(None)
            continue
        model = train_lr(Xtr, ytr)
        scores = predict(model, Xte)
        aurocs.append(auroc(scores, yte))

    valid = [a for a in aurocs if a is not None]
    if valid:
        m = sum(valid) / len(valid)
        s = math.sqrt(sum((a-m)**2 for a in valid) / len(valid))
    else:
        m = float('nan')
        s = float('nan')

    line = '{:20s}'.format(fam)
    for a in aurocs:
        line += '{:>8s}'.format('{:.3f}'.format(a) if a is not None else 'NaN')
    line += '{:>10s}{:>8s}'.format(
        '{:.3f}'.format(m) if not math.isnan(m) else 'NaN',
        '{:.3f}'.format(s) if not math.isnan(s) else 'NaN')
    print(line)

# Diagnostic - show Xtr sizes
print()
print('=== Diagnostic: Xtr sizes per family (libpng rep-1) ===')
for fam, feats in FAMILIES.items():
    train = by_prog_rep['libpng'].get(1, [])
    Xtr, ytr = to_xy(train, feats)
    has_var = has_variance(Xtr) if Xtr else False
    n_pos = sum(ytr) if ytr else 0
    print('  {:20s}: Xtr={} ytr_pos={} has_var={}'.format(
        fam, len(Xtr), n_pos, has_var))
