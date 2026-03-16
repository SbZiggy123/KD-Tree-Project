from kdtree import KDtree, node
from bruteforce import BruteForce
import time
import random


#TESTING
# ==============================
# CONFIGURATION
# ==============================

K        = 8        # number of dimensions
N        = 100000   # number of nodes in the tree
REPEATS  = 1000     # number of times each test is repeated for timing
VALRANGE = 10000    # range of numbers for values

BF_REPEATS = 10     # brute force is much slower so use far fewer repeats


# ==============================
# TREE SETUP
# ==============================

points = [[random.randint(0, VALRANGE) for _ in range(K)] for _ in range(N)]

tree = KDtree(K)
for p in points:
    tree.insert(node(p))

bf = BruteForce()
for p in points:
    bf.insert(p)

print(f"Tree built. ({N} nodes, {K} dimensions)\n")

start = time.perf_counter()
tree.optimise()
end = time.perf_counter()
print(f"KD tree optimised in {(end - start):.6f} seconds\n")


# ==============================
# EXACT SEARCH
# ==============================

print("--- Exact Search ---")

exact_targets = [node(random.choice(points)) for _ in range(5)]
exact_keys    = [t.key for t in exact_targets]             # raw keys for brute force

start = time.perf_counter()
for _ in range(REPEATS):
    for t in exact_targets:
        tree.exactSearch(t)
end = time.perf_counter()
kd_time = end - start
print(f"KD  total: {kd_time:.6f}s  |  avg: {kd_time / (REPEATS * len(exact_targets)):.9f}s")

start = time.perf_counter()
for _ in range(BF_REPEATS):
    for key in exact_keys:
        bf.exactSearch(key)
end = time.perf_counter()
bf_time = end - start
print(f"BF  total: {bf_time:.6f}s  |  avg: {bf_time / (BF_REPEATS * len(exact_keys)):.9f}s")
print(f"KD is {bf_time / BF_REPEATS * REPEATS / kd_time:.1f}x faster than brute force\n")


# ==============================
# PARTIAL SEARCH
# ==============================

print("--- Partial Search ---")

partial_tests = [
    {i: random.randint(0, VALRANGE) for i in range(K // 2 + 1)}
    for _ in range(5)
]

start = time.perf_counter()
for _ in range(REPEATS):
    for constraints in partial_tests:
        tree.partialSearch(constraints)
end = time.perf_counter()
kd_time = end - start
print(f"KD  total: {kd_time:.6f}s  |  avg: {kd_time / (REPEATS * len(partial_tests)):.9f}s")

start = time.perf_counter()
for _ in range(BF_REPEATS):
    for constraints in partial_tests:
        bf.partialSearch(constraints)
end = time.perf_counter()
bf_time = end - start
print(f"BF  total: {bf_time:.6f}s  |  avg: {bf_time / (BF_REPEATS * len(partial_tests)):.9f}s")
print(f"KD is {bf_time / BF_REPEATS * REPEATS / kd_time:.1f}x faster than brute force\n")


# ==============================
# REGION QUERY
# ==============================

print("--- Region Query ---")

region_size = VALRANGE // 10
region_tests = []
for _ in range(5):
    lower = [random.randint(0, VALRANGE - region_size) for _ in range(K)]
    upper = [l + region_size for l in lower]
    region_tests.append((upper, lower))

start = time.perf_counter()
for _ in range(REPEATS):
    for upper, lower in region_tests:
        tree.regionQuery(upper, lower)
end = time.perf_counter()
kd_time = end - start
print(f"KD  total: {kd_time:.6f}s  |  avg: {kd_time / (REPEATS * len(region_tests)):.9f}s")

start = time.perf_counter()
for _ in range(BF_REPEATS):
    for upper, lower in region_tests:
        bf.regionQuery(lower, upper)                        # brute force takes lower then upper
end = time.perf_counter()
bf_time = end - start
print(f"BF  total: {bf_time:.6f}s  |  avg: {bf_time / (BF_REPEATS * len(region_tests)):.9f}s")
print(f"KD is {bf_time / BF_REPEATS * REPEATS / kd_time:.1f}x faster than brute force\n")


# ==============================
# NEAREST NEIGHBOUR
# ==============================

print("--- Nearest Neighbour ---")

nn_tests = [[random.randint(0, VALRANGE) for _ in range(K)] for _ in range(5)]

start = time.perf_counter()
for _ in range(REPEATS):
    for target in nn_tests:
        tree.nearestNeighbour1(target)
end = time.perf_counter()
nn1_time = end - start
print(f"NN1 total: {nn1_time:.6f}s  |  avg: {nn1_time / (REPEATS * len(nn_tests)):.9f}s")

start = time.perf_counter()
for _ in range(REPEATS):
    for target in nn_tests:
        tree.nearestNeighbour2(target)
end = time.perf_counter()
nn2_time = end - start
print(f"NN2 total: {nn2_time:.6f}s  |  avg: {nn2_time / (REPEATS * len(nn_tests)):.9f}s")

start = time.perf_counter()
for _ in range(BF_REPEATS):
    for target in nn_tests:
        bf.nearestNeighbour(target)
end = time.perf_counter()
bf_time = end - start
print(f"BF  total: {bf_time:.6f}s  |  avg: {bf_time / (BF_REPEATS * len(nn_tests)):.9f}s")

print()
if nn2_time < nn1_time:
    print(f"NN2 was faster than NN1 by {((nn1_time - nn2_time) / nn1_time * 100):.1f}%")
else:
    print(f"NN1 was faster than NN2 by {((nn2_time - nn1_time) / nn2_time * 100):.1f}% — NN2 overhead not yet paying off at K={K}")

best_kd = min(nn1_time, nn2_time)
print(f"Best KD is {bf_time / BF_REPEATS * REPEATS / best_kd:.1f}x faster than brute force")
