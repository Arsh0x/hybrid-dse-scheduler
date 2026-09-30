import csv
rows = list(csv.DictReader(open('/workspace/zlib_5e2_candidates.csv')))
print("zlib: {} rows".format(len(rows)))
for f in ['path_length', 'branch_hit_count', 'rtn_cmov']:
    int_vals = [int(c[f]) for c in rows if c['is_interesting']=='1']
    rej_vals = [int(c[f]) for c in rows if c['is_interesting']=='0']
    im = sum(int_vals)/len(int_vals) if int_vals else 0
    rm = sum(rej_vals)/len(rej_vals) if rej_vals else 0
    print("  {}: interesting={:.2f}, rejected={:.2f}".format(f, im, rm))
