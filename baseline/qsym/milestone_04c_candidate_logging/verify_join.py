import csv

solver_rows = list(csv.DictReader(open('/workspace/logs/solver_timing.csv')))
cand_rows = list(csv.DictReader(open('/workspace/logs/candidates.csv')))

print("Joined pairs (candidate -> outcome):")
print("branch_id                      is_interested  result   elapsed_us   delta_us")
print("-" * 80)

interesting = [r for r in cand_rows if r['is_interesting'] == '1']
for c in interesting:
    c_ts = int(c['timestamp_us'])
    best = min(solver_rows, key=lambda s: abs(int(s['timestamp_us']) - c_ts))
    delta = int(best['timestamp_us']) - c_ts
    print("%-30s %-15s %-8s %-12s %d" % (
        c['branch_id'], c['is_interesting'],
        best['result'], best['elapsed_us'], delta))

print()
print("Total interesting candidates: %d" % len(interesting))
print("Total solver invocations:     %d" % len(solver_rows))
print("Match: %s" % ("YES" if len(interesting) == len(solver_rows) else "NO"))
