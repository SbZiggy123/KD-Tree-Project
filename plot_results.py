import csv
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ── Style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor":  "#fafaf8",
    "axes.facecolor":    "#f1efe8",
    "axes.edgecolor":    "#b4b2a9",
    "axes.labelcolor":   "#3d3d3a",
    "axes.titlesize":    13,
    "axes.titleweight":  "medium",
    "axes.labelsize":    11,
    "axes.grid":         True,
    "grid.color":        "#d3d1c7",
    "grid.linewidth":    0.6,
    "xtick.color":       "#5f5e5a",
    "ytick.color":       "#5f5e5a",
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "legend.fontsize":   9,
    "legend.framealpha": 0.85,
    "legend.edgecolor":  "#b4b2a9",
    "lines.linewidth":   2,
    "lines.markersize":  6,
    "figure.dpi":        150,
})

COL = {
    "nn1":    "#378ADD",
    "nn2":    "#1D9E75",
    "bf":     "#D85A30",
    "kd":     "#378ADD",
    "speed1": "#378ADD",
    "speed2": "#1D9E75",
    "unbal":  "#D85A30",
    "bal":    "#1D9E75",
}

OUT = "plots"
os.makedirs(OUT, exist_ok=True)

def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def savefig(name):
    path = f"{OUT}/{name}.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {path}")

def us(s):
    """seconds → microseconds"""
    return float(s) * 1e6

def ms(s):
    """seconds → milliseconds"""
    return float(s) * 1e3


# ══════════════════════════════════════════════════════════════════════════════
#  PLOT 1  —  Curse of Dimensionality: KD vs Brute Force speedup over k
# ══════════════════════════════════════════════════════════════════════════════
def plot_curse_of_dimensionality():
    rows = read_csv("results/exp1_k_sweep_nn.csv")
    ks        = [int(r["k"])            for r in rows]
    sp_nn1    = [float(r["nn1_speedup"]) for r in rows]
    sp_nn2    = [float(r["nn2_speedup"]) for r in rows]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ks, sp_nn1, "o-", color=COL["nn1"], label="NN1 (split-plane)")
    ax.plot(ks, sp_nn2, "s-", color=COL["nn2"], label="NN2 (bounding-box)")
    ax.axhline(1, color="#888", linewidth=1, linestyle="--", label="Brute-force baseline (1×)")

    ax.set_xlabel("Dimensions (k)")
    ax.set_ylabel("Speedup over brute force (×)")
    ax.set_title("Curse of Dimensionality: KD-tree speedup collapses as k grows\n"
                 f"N = 50,000 points")
    ax.set_xticks(ks)
    ax.legend()
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:g}×"))

    # annotate crossover
    for i, (k, s1, s2) in enumerate(zip(ks, sp_nn1, sp_nn2)):
        if s1 < 1 and i > 0 and sp_nn1[i-1] >= 1:
            ax.annotate("NN1 slower\nthan brute force",
                        xy=(k, s1), xytext=(k-1.5, s1*0.3),
                        arrowprops=dict(arrowstyle="->", color="#888"),
                        fontsize=8, color="#5f5e5a")

    fig.tight_layout()
    savefig("01_curse_of_dimensionality")


# ══════════════════════════════════════════════════════════════════════════════
#  PLOT 2  —  Raw query times across k (log scale) — NN1, NN2, BF
# ══════════════════════════════════════════════════════════════════════════════
def plot_raw_times_vs_k():
    rows = read_csv("results/exp1_k_sweep_nn.csv")
    ks      = [int(r["k"])          for r in rows]
    nn1_ms  = [ms(r["nn1_avg_s"])   for r in rows]
    nn2_ms  = [ms(r["nn2_avg_s"])   for r in rows]
    bf_ms   = [ms(r["bf_avg_s"])    for r in rows]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ks, nn1_ms, "o-", color=COL["nn1"], label="NN1 (split-plane)")
    ax.plot(ks, nn2_ms, "s-", color=COL["nn2"], label="NN2 (bounding-box)")
    ax.plot(ks, bf_ms,  "^-", color=COL["bf"],  label="Brute force")

    ax.set_xlabel("Dimensions (k)")
    ax.set_ylabel("Average query time (ms, log scale)")
    ax.set_title("Query time vs dimensionality\n"
                 "N = 50,000 points")
    ax.set_xticks(ks)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:g} ms"))
    ax.legend()

    fig.tight_layout()
    savefig("02_raw_times_vs_k")


# ══════════════════════════════════════════════════════════════════════════════
#  PLOT 3  —  NN1 vs NN2 crossover detail
# ══════════════════════════════════════════════════════════════════════════════
def plot_nn_crossover():
    rows = read_csv("results/exp4_nn_crossover.csv")
    ks      = [int(r["k"])          for r in rows]
    nn1_us  = [us(r["nn1_avg_s"])   for r in rows]
    nn2_us  = [us(r["nn2_avg_s"])   for r in rows]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ks, nn1_us, "o-", color=COL["nn1"], label="NN1 (split-plane)")
    ax.plot(ks, nn2_us, "s-", color=COL["nn2"], label="NN2 (bounding-box)")

    # shade regions
    crossover_k = None
    for i in range(1, len(ks)):
        if nn1_us[i] < nn2_us[i] and nn1_us[i-1] >= nn2_us[i-1]:
            crossover_k = ks[i]
        if nn1_us[i] > nn2_us[i] and nn1_us[i-1] <= nn2_us[i-1]:
            crossover_k = ks[i]

    # find where NN2 first wins
    nn2_wins_at = next((ks[i] for i in range(len(ks)) if nn2_us[i] < nn1_us[i]), None)
    if nn2_wins_at:
        ax.axvline(nn2_wins_at, color="#888", linewidth=1, linestyle="--")
        ax.annotate(f"NN2 wins\nfrom k={nn2_wins_at}",
                    xy=(nn2_wins_at, max(nn1_us)*0.5),
                    xytext=(nn2_wins_at+0.5, max(nn1_us)*0.6),
                    fontsize=8, color="#5f5e5a",
                    arrowprops=dict(arrowstyle="->", color="#888"))

    ax.set_xlabel("Dimensions (k)")
    ax.set_ylabel("Average query time (µs, log scale)")
    ax.set_title("NN1 vs NN2: where does bounding-box pruning start paying off?\n"
                 "N = 50,000 points")
    ax.set_xticks(ks)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:g} µs"))
    ax.legend()

    fig.tight_layout()
    savefig("03_nn1_vs_nn2_crossover")


# ══════════════════════════════════════════════════════════════════════════════
#  PLOT 4  —  Scaling with N: KD vs BF for all three operations
# ══════════════════════════════════════════════════════════════════════════════
def plot_scaling_with_n():
    rows = read_csv("results/exp2_n_sweep.csv")
    ops  = list(dict.fromkeys(r["operation"] for r in rows))

    fig, axes = plt.subplots(1, len(ops), figsize=(5 * len(ops), 5), sharey=False)
    if len(ops) == 1:
        axes = [axes]

    for ax, op in zip(axes, ops):
        op_rows = [r for r in rows if r["operation"] == op]
        ns      = [int(r["N"])        for r in op_rows]
        kd_us   = [us(r["kd_avg_s"])  for r in op_rows]
        bf_us   = [us(r["bf_avg_s"])  for r in op_rows]

        ax.plot(ns, kd_us, "o-", color=COL["kd"], label="KD-tree")
        ax.plot(ns, bf_us, "^-", color=COL["bf"], label="Brute force")
        ax.set_xlabel("Dataset size (N)")
        ax.set_ylabel("Average query time (µs)" if ax == axes[0] else "")
        ax.set_title(op)
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:g} µs"))
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
        ax.legend()

    fig.suptitle(f"KD-tree vs Brute Force scaling with N  (k = 4)", fontsize=13, y=1.02)
    fig.tight_layout()
    savefig("04_scaling_with_n")


# ══════════════════════════════════════════════════════════════════════════════
#  PLOT 5  —  Speedup ratios vs N (one line per operation)
# ══════════════════════════════════════════════════════════════════════════════
def plot_speedup_vs_n():
    rows = read_csv("results/exp2_n_sweep.csv")
    ops  = list(dict.fromkeys(r["operation"] for r in rows))
    colours = [COL["nn1"], COL["nn2"], COL["bf"]]

    fig, ax = plt.subplots(figsize=(8, 5))
    for op, col in zip(ops, colours):
        op_rows = [r for r in rows if r["operation"] == op]
        ns      = [int(r["N"])          for r in op_rows]
        speeds  = [float(r["speedup"])  for r in op_rows]
        ax.plot(ns, speeds, "o-", color=col, label=op)

    ax.set_xlabel("Dataset size (N)")
    ax.set_ylabel("Speedup over brute force (×)")
    ax.set_title(f"KD-tree speedup grows with N  (k = 4)")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:g}×"))
    ax.legend()

    fig.tight_layout()
    savefig("05_speedup_vs_n")


# ══════════════════════════════════════════════════════════════════════════════
#  PLOT 6  —  Balance experiment: before vs after optimise()
# ══════════════════════════════════════════════════════════════════════════════
def plot_balance():
    rows   = read_csv("results/exp3_balance.csv")
    states = [r["state"]            for r in rows]
    nn1_us = [us(r["nn1_avg_s"])    for r in rows]
    nn2_us = [us(r["nn2_avg_s"])    for r in rows]

    x      = range(len(states))
    width  = 0.35

    fig, ax = plt.subplots(figsize=(7, 5))
    bars1 = ax.bar([i - width/2 for i in x], nn1_us, width,
                   label="NN1 (split-plane)", color=COL["nn1"], alpha=0.85)
    bars2 = ax.bar([i + width/2 for i in x], nn2_us, width,
                   label="NN2 (bounding-box)", color=COL["nn2"], alpha=0.85)

    # value labels on bars
    for bar in list(bars1) + list(bars2):
        h = bar.get_height()
        label = f"{h:.0f} µs" if h >= 1 else f"{h*1000:.1f} ns"
        ax.text(bar.get_x() + bar.get_width()/2, h * 1.02, label,
                ha="center", va="bottom", fontsize=8, color="#3d3d3a")

    short_labels = [s.split("(")[0].strip() for s in states]
    ax.set_xticks(list(x))
    ax.set_xticklabels(short_labels)
    ax.set_ylabel("Average query time (µs)")
    ax.set_title("Effect of tree balance on query performance\n"
                 "Sorted insert (worst case) vs optimise()  —  N = 20,000, k = 4")
    ax.legend()

    fig.tight_layout()
    savefig("06_balance_effect")


# ══════════════════════════════════════════════════════════════════════════════
#  RUN ALL
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating plots...\n")
    plot_curse_of_dimensionality()
    plot_raw_times_vs_k()
    plot_nn_crossover()
    plot_scaling_with_n()
    plot_speedup_vs_n()
    plot_balance()
    print(f"\nAll plots saved to ./{OUT}/")
