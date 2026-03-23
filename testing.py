from kdtree import KDtree, node
from bruteforce import BruteForce
import time
import random
import csv
import os
 
# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
 
VALRANGE   = 10000   # range of random values per dimension
REPEATS    = 200     # repeats per KD-tree timing measurement
BF_REPEATS = 10      # brute force is much slower — fewer repeats
 
# Sweeps
K_SWEEP = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20]   # dimensions to test (curse of dimensionality)
N_SWEEP = [1_000, 5_000, 10_000]  # dataset sizes to test (scaling)
 
N_FIXED = 50_000   # N held constant during the k-sweep
K_FIXED = 4        # k held constant during the N-sweep
 
CSV_DIR = "results"
os.makedirs(CSV_DIR, exist_ok=True)
 
 
# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
 
def sep(char="═", width=72):
    print(char * width)
 
def header(title):
    sep()
    print(f"  {title}")
    sep()
 
def subheader(title):
    print(f"\n  ── {title} ──")
 
def fmt_s(seconds):
    """Human-readable time."""
    if seconds < 0.000_001:
        return f"{seconds * 1e9:.2f} ns"
    if seconds < 0.001:
        return f"{seconds * 1e6:.2f} µs"
    if seconds < 1:
        return f"{seconds * 1e3:.3f} ms"
    return f"{seconds:.4f} s"
 
def fmt_speedup(kd_time, bf_time, kd_reps, bf_reps):
    """Return a ×N speedup string, normalising for different repeat counts."""
    kd_avg = kd_time / kd_reps
    bf_avg = bf_time / bf_reps
    x = bf_avg / kd_avg if kd_avg > 0 else float("inf")
    return f"{x:.1f}×"
 
def build_tree(k, n):
    points = [[random.randint(0, VALRANGE) for _ in range(k)] for _ in range(n)]
    tree = KDtree(k)
    for p in points:
        tree.insert(node(p))
    tree.optimise()
    bf = BruteForce()
    for p in points:
        bf.insert(p)
    return tree, bf, points
 
def time_fn(fn, repeats):
    """Run fn() `repeats` times and return total elapsed seconds."""
    start = time.perf_counter()
    for _ in range(repeats):
        fn()
    return time.perf_counter() - start
 
def nn_targets(k, points, n=5):
    return [[random.randint(0, VALRANGE) for _ in range(k)] for _ in range(n)]
 
def region_tests(k, n=5):
    size = VALRANGE // 10
    tests = []
    for _ in range(n):
        lower = [random.randint(0, VALRANGE - size) for _ in range(k)]
        upper = [l + size for l in lower]
        tests.append((upper, lower))
    return tests
 
 
# ══════════════════════════════════════════════════════════════════════════════
#  EXPERIMENT 1: K-SWEEP  (curse of dimensionality)
#  Fixed N, sweep k — measuring NN1, NN2, and brute force
# ══════════════════════════════════════════════════════════════════════════════
 
def experiment_k_sweep():
    header("EXPERIMENT 1: Curse of Dimensionality  (N fixed, k varies)")
    print(f"  N = {N_FIXED:,}  |  k ∈ {K_SWEEP}  |  {REPEATS} KD repeats, {BF_REPEATS} BF repeats\n")
 
    rows = []
    col_w = 6
 
    # Table header
    print(f"  {'k':>{col_w}}  {'NN1 avg':>12}  {'NN2 avg':>12}  {'BF avg':>12}  "
          f"{'NN1 speed':>10}  {'NN2 speed':>10}  {'NN1 vs NN2':>12}")
    print(f"  {'-'*col_w}  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*12}")
 
    for k in K_SWEEP:
        tree, bf, points = build_tree(k, N_FIXED)
        targets = nn_targets(k, points)
 
        nn1_t = time_fn(lambda: [tree.nearestNeighbour1(t) for t in targets], REPEATS)
        nn2_t = time_fn(lambda: [tree.nearestNeighbour2(t) for t in targets], REPEATS)
        bf_t  = time_fn(lambda: [bf.nearestNeighbour(t)   for t in targets], BF_REPEATS)
 
        nn1_avg = nn1_t / (REPEATS    * len(targets))
        nn2_avg = nn2_t / (REPEATS    * len(targets))
        bf_avg  = bf_t  / (BF_REPEATS * len(targets))
 
        sp1     = bf_avg / nn1_avg if nn1_avg > 0 else float("inf")
        sp2     = bf_avg / nn2_avg if nn2_avg > 0 else float("inf")
        winner  = f"NN1 +{((nn2_avg-nn1_avg)/nn2_avg*100):.0f}%" if nn1_avg < nn2_avg \
                  else f"NN2 +{((nn1_avg-nn2_avg)/nn1_avg*100):.0f}%"
 
        print(f"  {k:>{col_w}}  {fmt_s(nn1_avg):>12}  {fmt_s(nn2_avg):>12}  {fmt_s(bf_avg):>12}  "
              f"{sp1:>9.1f}×  {sp2:>9.1f}×  {winner:>12}")
 
        rows.append({
            "k": k, "N": N_FIXED,
            "nn1_avg_s": nn1_avg, "nn2_avg_s": nn2_avg, "bf_avg_s": bf_avg,
            "nn1_speedup": sp1, "nn2_speedup": sp2,
        })
 
    path = f"{CSV_DIR}/exp1_k_sweep_nn.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"\n  Results saved → {path}")
 
 
# ══════════════════════════════════════════════════════════════════════════════
#  EXPERIMENT 2: N-SWEEP  (scaling)
#  Fixed k, sweep N — measuring all four operations vs brute force
# ══════════════════════════════════════════════════════════════════════════════
 
def experiment_n_sweep():
    header("EXPERIMENT 2: Scaling with Dataset Size  (k fixed, N varies)")
    print(f"  k = {K_FIXED}  |  N ∈ {[f'{n:,}' for n in N_SWEEP]}  |  {REPEATS} KD / {BF_REPEATS} BF repeats\n")
 
    rows = []
 
    for op in ["Exact Search", "Region Query", "Nearest Neighbour (NN2)"]:
        subheader(op)
        col_w = 10
        print(f"  {'N':>{col_w}}  {'KD avg':>12}  {'BF avg':>12}  {'Speedup':>10}")
        print(f"  {'-'*col_w}  {'-'*12}  {'-'*12}  {'-'*10}")
 
        for n in N_SWEEP:
            tree, bf, points = build_tree(K_FIXED, n)
 
            if op == "Exact Search":
                targets     = [node(random.choice(points)) for _ in range(5)]
                target_keys = [t.key for t in targets]
                kd_t = time_fn(lambda: [tree.exactSearch(t) for t in targets],     REPEATS)
                bf_t = time_fn(lambda: [bf.exactSearch(k)   for k in target_keys], BF_REPEATS)
 
            elif op == "Region Query":
                tests = region_tests(K_FIXED)
                kd_t = time_fn(lambda: [tree.regionQuery(u, l) for u, l in tests], REPEATS)
                bf_t = time_fn(lambda: [bf.regionQuery(l, u)   for u, l in tests], BF_REPEATS)
 
            else:  # NN2
                targets = nn_targets(K_FIXED, points)
                kd_t = time_fn(lambda: [tree.nearestNeighbour2(t) for t in targets], REPEATS)
                bf_t = time_fn(lambda: [bf.nearestNeighbour(t)    for t in targets], BF_REPEATS)
 
            n_ops   = 5
            kd_avg  = kd_t / (REPEATS    * n_ops)
            bf_avg  = bf_t / (BF_REPEATS * n_ops)
            speedup = bf_avg / kd_avg if kd_avg > 0 else float("inf")
 
            print(f"  {n:>{col_w},}  {fmt_s(kd_avg):>12}  {fmt_s(bf_avg):>12}  {speedup:>9.1f}×")
 
            rows.append({
                "operation": op, "k": K_FIXED, "N": n,
                "kd_avg_s": kd_avg, "bf_avg_s": bf_avg, "speedup": speedup,
            })
 
    path = f"{CSV_DIR}/exp2_n_sweep.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"\n  Results saved → {path}")
 
 
# ══════════════════════════════════════════════════════════════════════════════
#  EXPERIMENT 3: BALANCE  (unbalanced vs optimised tree)
#  Insert in sorted order (worst case), then call optimise()
# ══════════════════════════════════════════════════════════════════════════════
 
def experiment_balance():
    header("EXPERIMENT 3: Balance vs Unbalanced Tree  (sorted insert = worst case)")
    k, n = K_FIXED, 20_000
    print(f"  k = {k}  |  N = {n:,}  |  {REPEATS} repeats\n")
 
    # Build worst-case unbalanced tree: sorted on first dimension
    points = [[i] + [random.randint(0, VALRANGE) for _ in range(k - 1)] for i in range(n)]
    unbal  = KDtree(k)
    for p in points:
        unbal.insert(node(p))
 
    targets = nn_targets(k, points)
 
    rows = []
    for label, tree_obj in [("Unbalanced (sorted insert)", unbal)]:
        nn1_t = time_fn(lambda: [tree_obj.nearestNeighbour1(t) for t in targets], REPEATS)
        nn2_t = time_fn(lambda: [tree_obj.nearestNeighbour2(t) for t in targets], REPEATS)
        nn1_avg = nn1_t / (REPEATS * len(targets))
        nn2_avg = nn2_t / (REPEATS * len(targets))
        rows.append({"state": label, "nn1_avg_s": nn1_avg, "nn2_avg_s": nn2_avg})
        print(f"  {label}")
        print(f"    NN1 avg: {fmt_s(nn1_avg)}    NN2 avg: {fmt_s(nn2_avg)}")
        print(f"    Tree depth: {unbal.depth() if hasattr(unbal, 'depth') else 'n/a'}\n")
 
    # Now optimise and re-test
    unbal.optimise()
    nn1_t = time_fn(lambda: [unbal.nearestNeighbour1(t) for t in targets], REPEATS)
    nn2_t = time_fn(lambda: [unbal.nearestNeighbour2(t) for t in targets], REPEATS)
    nn1_avg_b = nn1_t / (REPEATS * len(targets))
    nn2_avg_b = nn2_t / (REPEATS * len(targets))
    rows.append({"state": "Balanced (after optimise())", "nn1_avg_s": nn1_avg_b, "nn2_avg_s": nn2_avg_b})
 
    improvement_nn1 = rows[0]["nn1_avg_s"] / nn1_avg_b
    improvement_nn2 = rows[0]["nn2_avg_s"] / nn2_avg_b
 
    print(f"  Balanced (after optimise())")
    print(f"    NN1 avg: {fmt_s(nn1_avg_b)}    NN2 avg: {fmt_s(nn2_avg_b)}")
    print(f"\n  Speedup from balancing:")
    print(f"    NN1: {improvement_nn1:.1f}×  faster after optimise()")
    print(f"    NN2: {improvement_nn2:.1f}×  faster after optimise()")
 
    path = f"{CSV_DIR}/exp3_balance.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"\n  Results saved → {path}")
 
 
# ══════════════════════════════════════════════════════════════════════════════
#  EXPERIMENT 4: NN1 vs NN2 CROSSOVER
#  Find the exact k where NN2's overhead stops being worth it
# ══════════════════════════════════════════════════════════════════════════════
 
def experiment_nn_crossover():
    header("EXPERIMENT 4: NN1 vs NN2 Crossover  (where does NN2 overhead stop paying off?)")
    print(f"  N = {N_FIXED:,}  |  k ∈ {K_SWEEP}  |  {REPEATS} repeats\n")
 
    col_w = 6
    print(f"  {'k':>{col_w}}  {'NN1 avg':>12}  {'NN2 avg':>12}  {'Winner':>14}  {'Margin':>10}")
    print(f"  {'-'*col_w}  {'-'*12}  {'-'*12}  {'-'*14}  {'-'*10}")
 
    rows      = []
    crossover = None
 
    for k in K_SWEEP:
        tree, _, points = build_tree(k, N_FIXED)
        targets = nn_targets(k, points)
 
        nn1_t = time_fn(lambda: [tree.nearestNeighbour1(t) for t in targets], REPEATS)
        nn2_t = time_fn(lambda: [tree.nearestNeighbour2(t) for t in targets], REPEATS)
 
        nn1_avg = nn1_t / (REPEATS * len(targets))
        nn2_avg = nn2_t / (REPEATS * len(targets))
 
        if nn1_avg < nn2_avg:
            winner = "NN1"
            margin = f"{((nn2_avg - nn1_avg) / nn2_avg * 100):.1f}%"
            if crossover is None:
                crossover = k
        else:
            winner = "NN2"
            margin = f"{((nn1_avg - nn2_avg) / nn1_avg * 100):.1f}%"
 
        print(f"  {k:>{col_w}}  {fmt_s(nn1_avg):>12}  {fmt_s(nn2_avg):>12}  {winner:>14}  {margin:>10}")
        rows.append({"k": k, "N": N_FIXED, "nn1_avg_s": nn1_avg, "nn2_avg_s": nn2_avg, "winner": winner})
 
    if crossover:
        print(f"\n  Crossover point: NN1 becomes faster at k = {crossover}")
    else:
        print(f"\n  NN2 was faster across all tested k values")
 
    path = f"{CSV_DIR}/exp4_nn_crossover.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"\n  Results saved → {path}")
 
 
# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
 
if __name__ == "__main__":
    sep("═")
    print("  KD-TREE BENCHMARK SUITE")
    print(f"  Results will be saved to ./{CSV_DIR}/")
    sep("═")
    print()
 
    experiment_k_sweep()
    print()
    experiment_n_sweep()
    print()
    experiment_balance()
    print()
    experiment_nn_crossover()
 
    print()
    sep()
    print("  All experiments complete.")
    sep()