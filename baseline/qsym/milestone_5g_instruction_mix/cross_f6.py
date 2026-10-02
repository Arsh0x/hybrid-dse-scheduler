import csv, math

def load(path):
    return list(csv.DictReader(open(path)))

zlib = load('/workspace/zlib_f6_candidates.csv')
libpng = load('/workspace/libpng_f6_candidates.csv')

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
    return [sigmoid(b + sum(w[j]*((x[j]-means[j])/stds[j]) for j in range(len(x))))
            for x in X]

def auroc(scores, labels):
    pairs = sorted(zip(scores, labels), key=lambda p: -p[0])
    n_pos = sum(labels); n_neg = len(labels)-n_pos
    if n_pos==0 or n_neg==0: return 0.5
    n = len(pairs); ranks = [0.0]*n
    i = 0
    while i < n:
        j = i
        while j < n and pairs[j][0] == pairs[i][0]: j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j): ranks[k] = avg
        i = j
    sum_pos = sum(ranks[i] for i in range(n) if pairs[i][1] == 1)
    return 1.0 - (sum_pos - n_pos*(n_pos+1)/2.0) / (n_pos * n_neg)

def cross(features, name):
    Xz, yz = to_xy(zlib, features)
    Xp, yp = to_xy(libpng, features)
    w, b, m, s = train(Xz, yz)
    auc_fwd = auroc(predict(Xp, w, b, m, s), yp)
    w2, b2, m2, s2 = train(Xp, yp)
    auc_rev = auroc(predict(Xz, w2, b2, m2, s2), yz)
    print("{:55s} z->l: {:.3f}   l->z: {:.3f}".format(name, auc_fwd, auc_rev))

print("zlib: {} rows, libpng: {} rows".format(len(zlib), len(libpng)))
print()
print("=== F6 Individual Features ===")
for f in ['rtn_simd_count', 'rtn_mem_ops']:
    cross([f], f)

print()
print("=== F6 family ===")
cross(['rtn_simd_count', 'rtn_mem_ops'], 'F6 (both features)')

print()
print("=== All optimization features combined ===")
cross(['rtn_cmov', 'insn_pos_in_rtn', 'rtn_insn_count', 'rtn_branch_count',
       'rtn_indirect_count', 'rtn_simd_count', 'rtn_mem_ops'],
      'F4+F5+F6 (all opt features)')

print()
print("=== Reference: Baseline ===")
cross(['path_length', 'branch_hit_count'], 'Baseline (path + hit)')
cross(['path_length', 'branch_hit_count', 'rtn_mem_ops'], 'Baseline + mem_ops')
cross(['path_length', 'branch_hit_count', 'rtn_simd_count'], 'Baseline + simd_count')
