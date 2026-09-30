import csv
from collections import Counter

candidates = list(csv.DictReader(open('/workspace/logs/candidates.csv')))
solver = list(csv.DictReader(open('/workspace/logs/solver_timing.csv')))

print("=== Basic counts ===")
print("Candidates: {}".format(len(candidates)))
print("Solver rows: {}".format(len(solver)))

# Class balance
labels = Counter(c['is_interesting'] for c in candidates)
print("\nUtility labels: {}".format(dict(labels)))

# Feature distributions
print("\n=== Feature distributions (min, max, mean) ===")
for feature in ['path_length', 'symbolized_bytes', 'constraint_count']:
    vals = [int(c[feature]) for c in candidates]
    print("{}: min={}, max={}, mean={:.2f}".format(
        feature, min(vals), max(vals), sum(vals)/len(vals)))

# THE KEY TEST: does constraint_count still show the "cliff"?
print("\n=== constraint_count by class ===")
for label in ['0', '1']:
    rows = [c for c in candidates if c['is_interesting'] == label]
    counts = Counter(int(c['constraint_count']) for c in rows)
    print("\nis_interesting={} (n={}):".format(label, len(rows)))
    for val in sorted(counts.keys())[:10]:
        print("  constraint_count={}: {} rows".format(val, counts[val]))
    if len(counts) > 10:
        print("  ... ({} distinct values)".format(len(counts)))

# Feature means by class
print("\n=== Feature means by class ===")
for feature in ['path_length', 'symbolized_bytes', 'constraint_count']:
    int_vals = [int(c[feature]) for c in candidates if c['is_interesting'] == '1']
    rej_vals = [int(c[feature]) for c in candidates if c['is_interesting'] == '0']
    int_mean = sum(int_vals)/len(int_vals) if int_vals else 0
    rej_mean = sum(rej_vals)/len(rej_vals) if rej_vals else 0
    print("{}: interesting_mean={:.2f}, rejected_mean={:.2f}".format(
        feature, int_mean, rej_mean))

# Solver results
results = Counter(s['result'] for s in solver)
print("\n=== Solver result distribution ===")
print(dict(results))

# Solver time range
times = [int(s['elapsed_us']) for s in solver]
print("Solver time: min={}us, max={}us, mean={:.0f}us".format(
    min(times), max(times), sum(times)/len(times)))
