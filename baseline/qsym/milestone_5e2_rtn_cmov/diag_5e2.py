import csv
from collections import Counter

def summarize(path, name):
    rows = list(csv.DictReader(open(path)))
    print("\n=== {} ({} rows) ===".format(name, len(rows)))
    
    # Class balance
    labels = Counter(c['is_interesting'] for c in rows)
    print("Class balance: {}".format(dict(labels)))
    
    # Feature means by class
    for f in ['path_length', 'branch_hit_count', 'rtn_cmov']:
        int_vals = [int(c[f]) for c in rows if c['is_interesting']=='1']
        rej_vals = [int(c[f]) for c in rows if c['is_interesting']=='0']
        if int_vals and rej_vals:
            im = sum(int_vals)/len(int_vals)
            rm = sum(rej_vals)/len(rej_vals)
            print("  {}: interesting_mean={:.2f}, rejected_mean={:.2f}".format(f, im, rm))
        else:
            print("  {}: EMPTY class".format(f))
    
    # Header sanity
    print("  Header: {}".format(list(rows[0].keys())))
    print("  First row: {}".format(list(rows[0].values())))

summarize('/workspace/zlib_5e2_candidates.csv', 'zlib_5e2')
summarize('/workspace/libpng_5e2_candidates.csv', 'libpng_5e2')

# Also compare against 5d
print("\n=== For comparison: 5d zlib ===")
try:
    rows_5d = list(csv.DictReader(open('/workspace/zlib_5d_candidates.csv')))
    print("5d zlib rows: {}".format(len(rows_5d)))
    for f in ['path_length', 'branch_hit_count']:
        int_vals = [int(c[f]) for c in rows_5d if c['is_interesting']=='1']
        rej_vals = [int(c[f]) for c in rows_5d if c['is_interesting']=='0']
        im = sum(int_vals)/len(int_vals)
        rm = sum(rej_vals)/len(rej_vals)
        print("  {}: interesting={:.2f}, rejected={:.2f}".format(f, im, rm))
except Exception as e:
    print("Could not load 5d: {}".format(e))
