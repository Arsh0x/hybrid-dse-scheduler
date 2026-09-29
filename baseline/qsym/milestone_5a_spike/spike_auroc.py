import csv
import math

# Load
candidates = list(csv.DictReader(open('/workspace/logs/candidates.csv')))

# Build X, y
X = []
y = []
for c in candidates:
    X.append([int(c['path_length']), int(c['symbolized_bytes'])])
    y.append(1 if c['is_interesting'] == '1' else 0)

# Simple logistic regression (gradient descent, pure python)
def sigmoid(z):
    if z < -500: return 0.0
    if z > 500: return 1.0
    return 1.0 / (1.0 + math.exp(-z))

def train_lr(X, y, lr=0.01, epochs=2000):
    n = len(X)
    # Standardize features
    means = [sum(X[i][j] for i in range(n))/n for j in range(len(X[0]))]
    stds = []
    for j in range(len(X[0])):
        var = sum((X[i][j] - means[j])**2 for i in range(n))/n
        stds.append(math.sqrt(var) if var > 0 else 1.0)
    
    Xn = [[(X[i][j]-means[j])/stds[j] for j in range(len(X[0]))] for i in range(n)]
    
    # Weights
    w = [0.0] * len(Xn[0])
    b = 0.0
    
    for epoch in range(epochs):
        grad_w = [0.0] * len(w)
        grad_b = 0.0
        for i in range(n):
            z = b + sum(w[j] * Xn[i][j] for j in range(len(w)))
            pred = sigmoid(z)
            err = pred - y[i]
            for j in range(len(w)):
                grad_w[j] += err * Xn[i][j]
            grad_b += err
        for j in range(len(w)):
            w[j] -= lr * grad_w[j] / n
        b -= lr * grad_b / n
    
    return w, b, means, stds

def predict(X, w, b, means, stds):
    preds = []
    for x in X:
        xn = [(x[j]-means[j])/stds[j] for j in range(len(x))]
        z = b + sum(w[j] * xn[j] for j in range(len(w)))
        preds.append(sigmoid(z))
    return preds

# AUROC
def auroc(scores, labels):
    pairs = sorted(zip(scores, labels), reverse=True)
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    auc = 0.0
    tp = 0
    fp = 0
    prev_fp = 0
    prev_tp = 0
    for score, label in pairs:
        if label == 1:
            tp += 1
        else:
            fp += 1
            auc += tp
    return auc / (n_pos * n_neg)

# Split: first 70% train, last 30% test
n = len(X)
split = int(n * 0.7)
X_tr, X_te = X[:split], X[split:]
y_tr, y_te = y[:split], y[split:]

w, b, means, stds = train_lr(X_tr, y_tr)
preds = predict(X_te, w, b, means, stds)

auc_path = auroc([p for p in preds], y_te)
print("AUROC (both features, last 30%): {:.3f}".format(auc_path))

# Individual features
for j, name in enumerate(['path_length', 'symbolized_bytes']):
    Xj_tr = [[X_tr[i][j]] for i in range(len(X_tr))]
    Xj_te = [[X_te[i][j]] for i in range(len(X_te))]
    w2, b2, m2, s2 = train_lr(Xj_tr, y_tr)
    p2 = predict(Xj_te, w2, b2, m2, s2)
    auc = auroc(p2, y_te)
    print("AUROC ({} only): {:.3f}".format(name, auc))

# Random baseline for reference
import random
random.seed(42)
rand_preds = [random.random() for _ in y_te]
print("AUROC (random baseline): {:.3f}".format(auroc(rand_preds, y_te)))

# Class balance in test
print("\nTest set: {} pos, {} neg".format(sum(y_te), len(y_te)-sum(y_te)))
print("Train set: {} pos, {} neg".format(sum(y_tr), len(y_tr)-sum(y_tr)))
