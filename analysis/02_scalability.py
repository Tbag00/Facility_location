from utils import *

import matplotlib.pyplot as plt
import pandas as pd

# ==========================
# Load data
# ==========================

df = load_runs()

df["size"] = df["n"] * df["m"]

# ==========================
# Aggregate statistics
# ==========================

stats = (
    df.groupby(["algorithm", "size"])
      .agg(
          mean_time=("time", "mean"),
          std_time=("time", "std"),

          mean_cost=("best_cost", "mean"),
          std_cost=("best_cost", "std"),

          mean_iter=("best_iteration", "mean"),
          std_iter=("best_iteration", "std"),
      )
      .reset_index()
)

# Colori coerenti
colors = {
    "sa": "tab:blue",
    "ils": "tab:orange"
}

# ==========================
# Execution time
# ==========================

plt.figure(figsize=(8,5))

for alg in stats.algorithm.unique():

    d = stats[stats.algorithm == alg]

    plt.errorbar(
        d["size"],
        d["mean_time"],
        yerr=d["std_time"],
        marker="o",
        capsize=4,
        linewidth=2,
        label=alg.upper(),
        color=colors[alg]
    )

plt.grid(True, alpha=0.3)

plt.xlabel("Problem size (n × m)")
plt.ylabel("Execution time (s)")
plt.title("Execution time vs problem size")

plt.legend()

savefig("time_scalability.png")

# ==========================
# Best cost
# ==========================

plt.figure(figsize=(8,5))

for alg in stats.algorithm.unique():

    d = stats[stats.algorithm == alg]

    plt.errorbar(
        d["size"],
        d["mean_cost"],
        yerr=d["std_cost"],
        marker="o",
        capsize=4,
        linewidth=2,
        label=alg.upper(),
        color=colors[alg]
    )

plt.grid(True, alpha=0.3)

plt.xlabel("Problem size (n × m)")
plt.ylabel("Average best cost")
plt.title("Solution quality vs problem size")

plt.legend()

savefig("cost_scalability.png")

# ==========================
# Best iteration
# ==========================

plt.figure(figsize=(8,5))

for alg in stats.algorithm.unique():

    d = stats[stats.algorithm == alg]

    plt.errorbar(
        d["size"],
        d["mean_iter"],
        yerr=d["std_iter"],
        marker="o",
        capsize=4,
        linewidth=2,
        label=alg.upper(),
        color=colors[alg]
    )

plt.grid(True, alpha=0.3)

plt.xlabel("Problem size (n × m)")
plt.ylabel("Iteration of best solution")
plt.title("Convergence speed")

plt.legend()

savefig("iteration_scalability.png")
