#!/usr/bin/env python3
"""
analyze_tuning.py

Genera i grafici di sensitivity analysis per la relazione, a partire dal CSV
aggregato prodotto dal solver OCaml (runs.csv / tuning_results.csv).

Colonne attese:
n, m, algorithm, seed, best_cost, best_iteration, total_iteration, time,
facilities, max_iterations, p_mut, t0, t_end, alpha, new_low

Uso:
    python3 analyze_tuning.py tuning_results.csv [output_dir]
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["figure.dpi"] = 130
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # costo ottimo (o migliore trovato) per ciascuna dimensione n
    opt = df.groupby("n")["best_cost"].min().to_dict()
    df["optimal_cost"] = df["n"].map(opt)
    df["is_opt"] = df["best_cost"] == df["optimal_cost"]
    df["gap_pct"] = (df["best_cost"] - df["optimal_cost"]) / df["optimal_cost"] * 100
    return df


# ----------------------------------------------------------------------
# 1. ILS: hit-rate e tempo in funzione di max_iterations e p_mut
# ----------------------------------------------------------------------
def plot_ils_sensitivity(df: pd.DataFrame, outdir: str):
    ils = df[df["algorithm"] == "ils"]
    if ils.empty:
        return

    g = (
        ils.groupby(["max_iterations", "p_mut"])
        .agg(hit_rate=("is_opt", "mean"), mean_time=("time", "mean"))
        .reset_index()
    )

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    for p in sorted(g["p_mut"].unique()):
        sub = g[g["p_mut"] == p].sort_values("max_iterations")
        axes[0].plot(sub["max_iterations"], sub["hit_rate"], marker="o", label=f"p_mut={p}")
        axes[1].plot(sub["max_iterations"], sub["mean_time"], marker="o", label=f"p_mut={p}")

    axes[0].set_xscale("log")
    axes[0].set_xlabel("max_iterations")
    axes[0].set_ylabel("frazione di run che raggiungono l'ottimo")
    axes[0].set_title("ILS - qualità della soluzione")
    axes[0].set_ylim(-0.05, 1.05)
    axes[0].legend()

    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("max_iterations")
    axes[1].set_ylabel("tempo medio (s)")
    axes[1].set_title("ILS - costo computazionale")
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "ils_sensitivity.png"))
    plt.close(fig)


# ----------------------------------------------------------------------
# 2. SA: heatmap hit-rate / tempo su alpha x new_low (aggregato su t0)
# ----------------------------------------------------------------------
def plot_sa_sensitivity(df: pd.DataFrame, outdir: str):
    sa = df[df["algorithm"] == "sa"]
    if sa.empty:
        return

    g = (
        sa.groupby(["alpha", "new_low"])
        .agg(hit_rate=("is_opt", "mean"), mean_time=("time", "mean"))
        .reset_index()
    )

    alphas = sorted(g["alpha"].unique())
    new_lows = sorted(g["new_low"].unique())

    hit_matrix = np.zeros((len(alphas), len(new_lows)))
    time_matrix = np.zeros((len(alphas), len(new_lows)))
    for i, a in enumerate(alphas):
        for j, nl in enumerate(new_lows):
            row = g[(g["alpha"] == a) & (g["new_low"] == nl)]
            hit_matrix[i, j] = row["hit_rate"].values[0] if len(row) else np.nan
            time_matrix[i, j] = row["mean_time"].values[0] if len(row) else np.nan

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    im0 = axes[0].imshow(hit_matrix, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    axes[0].set_xticks(range(len(new_lows)))
    axes[0].set_xticklabels(new_lows)
    axes[0].set_yticks(range(len(alphas)))
    axes[0].set_yticklabels(alphas)
    axes[0].set_xlabel("new_low (lunghezza catena)")
    axes[0].set_ylabel("alpha (raffreddamento)")
    axes[0].set_title("SA - frazione run ottimi")
    for i in range(len(alphas)):
        for j in range(len(new_lows)):
            axes[0].text(j, i, f"{hit_matrix[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im0, ax=axes[0], fraction=0.046)

    im1 = axes[1].imshow(time_matrix, cmap="viridis", aspect="auto")
    axes[1].set_xticks(range(len(new_lows)))
    axes[1].set_xticklabels(new_lows)
    axes[1].set_yticks(range(len(alphas)))
    axes[1].set_yticklabels(alphas)
    axes[1].set_xlabel("new_low (lunghezza catena)")
    axes[1].set_ylabel("alpha (raffreddamento)")
    axes[1].set_title("SA - tempo medio (s)")
    for i in range(len(alphas)):
        for j in range(len(new_lows)):
            axes[1].text(j, i, f"{time_matrix[i, j]:.2f}", ha="center", va="center", fontsize=8, color="white")
    fig.colorbar(im1, ax=axes[1], fraction=0.046)

    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "sa_sensitivity.png"))
    plt.close(fig)


# ----------------------------------------------------------------------
# 3. Trade-off qualita'/tempo, per dimensione del problema
# ----------------------------------------------------------------------
def plot_quality_vs_time(df: pd.DataFrame, outdir: str):
    ns = sorted(df["n"].unique())
    fig, axes = plt.subplots(1, len(ns), figsize=(4 * len(ns), 4), sharey=False)
    if len(ns) == 1:
        axes = [axes]

    for ax, n in zip(axes, ns):
        sub = df[df["n"] == n]
        for algo, color in [("ils", "tab:blue"), ("sa", "tab:orange")]:
            s = sub[sub["algorithm"] == algo]
            if s.empty:
                continue
            ax.scatter(s["time"], s["gap_pct"], s=14, alpha=0.5, color=color, label=algo.upper())
        ax.set_xscale("log")
        ax.set_xlabel("tempo (s)")
        ax.set_ylabel("gap dall'ottimo (%)")
        ax.set_title(f"n={n}")
        ax.legend()

    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "quality_vs_time.png"))
    plt.close(fig)


# ----------------------------------------------------------------------
# 4. Tabella riassuntiva delle configurazioni consigliate
# ----------------------------------------------------------------------
def best_configs_table(df: pd.DataFrame, outdir: str):
    rows = []
    for n in sorted(df["n"].unique()):
        for algo in ["ils", "sa"]:
            sub = df[(df["n"] == n) & (df["algorithm"] == algo) & (df["is_opt"])]
            if sub.empty:
                continue
            best = sub.loc[sub["time"].idxmin()]
            row = {"n": n, "algorithm": algo, "time": round(best["time"], 4)}
            if algo == "ils":
                row["max_iterations"] = best["max_iterations"]
                row["p_mut"] = best["p_mut"]
            else:
                row["t0"] = best["t0"]
                row["alpha"] = best["alpha"]
                row["new_low"] = best["new_low"]
            rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(os.path.join(outdir, "best_configs_summary.csv"), index=False)
    print(table.to_string(index=False))


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 analyze_tuning.py <csv_path> [output_dir]")
        sys.exit(1)

    csv_path = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else "figs"
    os.makedirs(outdir, exist_ok=True)

    df = load_data(csv_path)

    plot_ils_sensitivity(df, outdir)
    plot_sa_sensitivity(df, outdir)
    plot_quality_vs_time(df, outdir)
    best_configs_table(df, outdir)

    print(f"\nGrafici salvati in: {outdir}/")


if __name__ == "__main__":
    main()
