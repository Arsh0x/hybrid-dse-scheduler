import csv
from collections import Counter

candidates = list(csv.DictReader(open('/workspace/logs/candidates.csv')))
solver = list(csv.DictReader(open('/workspace/logs/solver_timing.csv')))

print("=== Basic counts ===")
print("Candidates: {}".format(len(candidates)))
print("Solver rows: {}".format(len(solver)))

util_counts = Counter(c['is_interesting'] for c in candidates)
print("\nUtility labels: {}".format(dict(util_counts)))

print("\n=== Clean feature distributions ===")
for feature in ['path_length', 'symbolized_bytes']:
    vals = [int(c[feature]) for c in candidates]
    print("{}: min={}, max={}, mean={:.2f}".format(
        feature, min(vals), max(vals), sum(vals)/len(vals)))

print("\n=== Feature means by class ===")
for feature in ['path_length', 'symbolized_bytes']:
    interesting_vals = [int(c[feature]) for c in candidates if c['is_interesting'] == '1']
    rejected_vals = [int(c[feature]) for c in candidates if c['is_interesting'] == '0']
    int_mean = sum(interesting_vals)/len(interesting_vals) if interesting_vals else 0
    rej_mean = sum(rejected_vals)/len(rejected_vals) if rejected_vals else 0
    print("{}: interesting_mean={:.2f}, rejected_mean={:.2f}".format(
        feature, int_mean, rej_mean))

print("\n=== Solver cost for interesting branches ===")
solver_by_ts = sorted(solver, key=lambda s: int(s['timestamp_us']))
interesting_costs = []

for c in candidates:
    if c['is_interesting'] != '1':
        continue
    c_ts = int(c['timestamp_us'])
    closest = min(solver_by_ts, key=lambda s: abs(int(s['timestamp_us']) - c_ts))
    if abs(int(closest['timestamp_us']) - c_ts) < 1000:
        interesting_costs.append(int(closest['elapsed_us']))

if interesting_costs:
    print("Matched: {}, mean={:.0f}us, min={}us, max={}us".format(
        len(interesting_costs),
        sum(interesting_costs)/len(interesting_costs),
        min(interesting_costs),
        max(interesting_costs)))
else:
    print("No matches within 1ms window")
