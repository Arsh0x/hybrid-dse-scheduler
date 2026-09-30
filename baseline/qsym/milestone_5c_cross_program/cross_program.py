import csv, math, random

def load(path):
    rows = list(csv.DictReader(open(path)))
    return rows

zlib = load('/workspace/zlib_candidates.csv')
libpng = load('/workspace/logs/candidates.csv')

def to_xy(rows, features):
    X = [[int(c[f]) for f in features] for c in rows]
    y = [1 if c['is_interesting']=='1' else 0 for c in rows]
    return X, y

def sigmoid(z):
    if z < -500: return 0.0
    if z > 500: return 1.0
    return 1.0/(1.0+math.exp(-z))

def train(X, y, lr=0.05, epochs=3000):
    n = len(X)
    means = [sum(X[i][j] for i in range(n))/n for j in range(len(X[0]))]
    stds = [max(math.sqrt(sum((X[i][j]-means[j])**2 for i in range(n))/n), 1e-9)
            for j in range(len(X[0]))]
    Xn = [[(X[i][j]-means[j])/stds[j] for j in range(len(X[0]))] for i in range(n)]
    w = [0.0]*len(Xn[0]); b = 0.0
    for _ in range(epochs):
        gw = [0.0]*len(w); gb = 0.0
        for i in range(n):
            z = b + sum(w[j]*Xn[i][j] for j in range(len(w)))
            err = sigmoid(z) - y[i]
            for j in range(len(w)): gw[j] += err*Xn[i][j]
            gb += err
        for j in range(len(w)): w[j] -= lr*gw[j]/n
        b -= lr*gb/n
    return w, b, means, stds

def predict(X, w, b, means, stds):
    out = []
    for x in X:
        xn = [(x[j]-means[j])/stds[j] for j in range(len(x))]
        z = b + sum(w[j]*xn[j] for j in range(len(w)))
        out.append(sigmoid(z))
    return out

def auroc(scores, labels):
    pairs = sorted(zip(scores, labels), reverse=True)
    n_pos = sum(labels); n_neg = len(labels)-n_pos
    if n_pos==0 or n_neg==0: return 0.5
    auc = 0.0; tp = 0
    for s, l in pairs:
        if l == 1: tp += 1
        else: auc += tp
    return auc/(n_pos*n_neg)

def evaluate(features, name):
    Xz, yz = to_xy(zlib, features)
    Xp, yp = to_xy(libpng, features)
    # Train on zlib, test on libpng
    w, b, m, s = train(Xz, yz)
    preds = predict(Xp, w, b, m, s)
    auc = auroc(preds, yp)
    print("{}: cross-program AUROC (train zlib -> test libpng) = {:.3f}".format(name, auc))
    return auc

print("=== Cross-Program Generalization Test ===")
print("Training set: zlib ({} rows)".format(len(zlib)))
print("Test set:     libpng ({} rows)".format(len(libpng)))
print()

evaluate(['path_length'], 'path_length only')
evaluate(['symbolized_bytes'], 'symbolized_bytes only')
evaluate(['path_length', 'symbolized_bytes'], 'path_length + symbolized_bytes')
evaluate(['constraint_count'], 'constraint_count only (expected bad)')

# Reverse direction: train on libpng, test on zlib
print("\n=== Reverse Direction: train libpng -> test zlib ===")

def evaluate_reverse(features, name):
    Xz, yz = to_xy(zlib, features)
    Xp, yp = to_xy(libpng, features)
    w, b, m, s = train(Xp, yp)
    preds = predict(Xz, w, b, m, s)
    auc = auroc(preds, yz)
    print("{}: cross-program AUROC (train libpng -> test zlib) = {:.3f}".format(name, auc))

evaluate_reverse(['path_length'], 'path_length only')
evaluate_reverse(['path_length', 'symbolized_bytes'], 'path_length + symbolized_bytes')
