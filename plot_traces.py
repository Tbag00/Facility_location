#!/usr/bin/env python3
"""
plot_traces.py

Elabora i file di trace (log per-iterazione, colonne: iteration,current_cost,best_cost)
prodotti da Csv_logger e genera i grafici di convergenza per la relazione.

Assunzioni sul formato dei file, dedotte dai due esempi forniti:
  - Un trace file contiene la concatenazione di piu' "segmenti", uno per ogni
    dimensione n del problema testata con la STESSA configurazione di parametri
    (stesso algoritmo, stesso seed, stessi iperparametri). Ogni segmento inizia
    quando la colonna `iteration` torna a 0/1 (reset).
  - I segmenti compaiono in ordine di n crescente (5, 10, 20, 50, 100, ...),
    coerentemente con il ciclo del main OCaml.
  - Il nome del file segue lo schema:
        trace_ils_iter<max_iterations>_pmut<p_mut>_seed<seed>.csv
        trace_sa_t0<t0>_tend<t_end>_alpha<alpha>_newlow<new_low>_seed<seed>.csv
    con i numeri decimali scritti sostituendo il punto con underscore
    (es. pmut0_1 -> 0.1, t0100_0 -> 100.0).

Per associare ogni segmento al proprio n, il file di trace viene incrociato con
il CSV aggregato (runs.csv / tuning_results.csv): si filtrano le righe con
stesso algorithm/seed/iperparametri, si ordinano per n crescente e si abbinano
posizionalmente ai segmenti; il match viene poi verificato controllando che il
best_cost finale del segmento coincida con quello della riga di runs.csv
(altrimenti viene segnalato un warning e il segmento viene scartato).

Uso tipico:
    python3 plot_traces.py --trace-dir ./traces --runs-csv tuning_results.csv --outdir figs

Con molti file (centinaia+), l'elaborazione è in streaming: ogni file viene
processato singolarmente e il risultato appeso subito a master_trace_long.csv,
invece di accumulare tutto in RAM. Se lo script si interrompe (crash, Ctrl+C),
i file già processati restano salvati; rilanciando lo stesso comando, i file già
presenti in master_trace_long.csv vengono saltati automaticamente (resume). Le
righe consecutive a costo invariato vengono compresse di default (utile
soprattutto per SA, dove il costo resta identico per centinaia di iterazioni).

Opzioni utili per dataset grandi:
    --no-resume       riparte da zero ignorando l'output precedente
    --no-collapse     disattiva la compressione delle righe a costo invariato
    --skip-plots      genera solo master_trace_long.csv, utile per una prima
                       passata di parsing su moltissimi file, rimandando i
                       grafici a una chiamata successiva (basta rilanciare
                       senza --skip-plots: il resume evita di rifare il parsing)
    --progress-every  ogni quanti file stampare un avanzamento (default 20)

Output:
    figs/master_trace_long.csv         -> tabella unica (n, algorithm, seed, iteration, best_cost, ...)
    figs/convergence_n<N>.png          -> un grafico ILS vs SA per ogni n trovato
    figs/convergence_n<N>_variance.png -> banda di varianza multi-seed (se >=2 seed per config)
"""

import argparse
import glob
import os
import re
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["figure.dpi"] = 130
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3

ILS_RE = re.compile(
    r"trace_ils_iter(?P<max_iterations>\d+)_pmut(?P<p_mut>\d+(?:[._]\d+)?)_seed(?P<seed>\d+)"
)
SA_RE = re.compile(
    r"trace_sa_t0(?P<t0>\d+(?:[._]\d+)?)_tend(?P<t_end>\d+(?:[._]\d+)?)_alpha(?P<alpha>\d+(?:[._]\d+)?)"
    r"_newlow(?P<new_low>\d+(?:[._]\d+)?)_seed(?P<seed>\d+)"
)

def _num(s: str) -> float:
    """'0_1' -> 0.1, '100_0' -> 100.0, '50' -> 50.0"""
    return float(s.replace("_", "."))


def parse_filename(path: str) -> dict:
    """Estrae algoritmo, seed e iperparametri dal nome del file."""
    name = os.path.basename(path)
    m = ILS_RE.search(name)
    if m:
        d = m.groupdict()
        return {
            "algorithm": "ils",
            "seed": int(d["seed"]),
            "params": {"max_iterations": _num(d["max_iterations"]), "p_mut": _num(d["p_mut"])},
        }
    m = SA_RE.search(name)
    if m:
        d = m.groupdict()
        return {
            "algorithm": "sa",
            "seed": int(d["seed"]),
            "params": {
                "t0": _num(d["t0"]),
                "t_end": _num(d["t_end"]),
                "alpha": _num(d["alpha"]),
                "new_low": _num(d["new_low"]),
            },
        }
    raise ValueError(f"Nome file non riconosciuto: {name}")


def split_into_segments(df: pd.DataFrame) -> list:
    """Divide il trace in segmenti ogni volta che 'iteration' non e' crescente
    (indica l'inizio di una nuova run, tipicamente per un nuovo n)."""
    it = df["iteration"].values
    reset_idx = [0] + [i for i in range(1, len(it)) if it[i] <= it[i - 1]] + [len(it)]
    segments = []
    for a, b in zip(reset_idx[:-1], reset_idx[1:]):
        segments.append(df.iloc[a:b].reset_index(drop=True))
    return segments


def match_segments_to_n(segments: list, runs_df: pd.DataFrame, algo: str, seed: int, params: dict, tol=1e-6):
    """Associa ad ogni segmento il valore di n corrispondente, incrociando con runs_df.
    Ritorna una lista di dict {n, m, segment} solo per i match verificati."""
    cand = runs_df[(runs_df["algorithm"] == algo) & (runs_df["seed"] == seed)].copy()
    for k, v in params.items():
        if k in cand.columns:
            cand = cand[np.isclose(cand[k], v, atol=tol, equal_nan=False) | cand[k].isna()]
    cand = cand.sort_values("n")

    matched = []
    n_pairs = min(len(cand), len(segments))
    if len(segments) > len(cand):
        # Caso tipico: run interrotta a meta' (es. Ctrl+C) mentre stava scrivendo
        # l'ultimo/gli ultimi segmenti -> quelle run non sono mai state loggate
        # in runs.csv, quindi restano segmenti "orfani" in coda al trace.
        n_orphans = len(segments) - len(cand)
        print(
            f"  [info] {algo} seed={seed} params={params}: "
            f"{n_orphans} segmento/i finale/i senza riscontro in runs.csv "
            f"(probabile esecuzione interrotta a meta', es. Ctrl+C) -> scartato/i",
            file=sys.stderr,
        )
    elif len(cand) > len(segments):
        print(
            f"  [warn] {algo} seed={seed} params={params}: "
            f"{len(cand)} righe candidate in runs.csv ma solo {len(segments)} segmenti nel trace "
            f"-> controlla se il trace file e' incompleto o troncato",
            file=sys.stderr,
        )
    for (_, row), seg in zip(cand.iloc[:n_pairs].iterrows(), segments[:n_pairs]):
        seg_final_cost = seg["best_cost"].iloc[-1]
        if seg_final_cost != row["best_cost"]:
            print(
                f"  [warn] mismatch inatteso: segmento finisce a best_cost={seg_final_cost} "
                f"ma runs.csv per n={row['n']} indica {row['best_cost']} -> segmento scartato "
                f"(possibile riga troncata a meta' scrittura: controlla con 'tail' il file trace)",
                file=sys.stderr,
            )
            continue
        matched.append({"n": int(row["n"]), "m": int(row["m"]), "segment": seg})
    return matched


def _segment_to_frame(seg: pd.DataFrame, n: int, m: int, algorithm: str, seed: int,
                       config_label: str, source_file: str, collapse_flat: bool) -> pd.DataFrame:
    """Costruisce il DataFrame finale per un segmento, in modo vettoriale (niente
    iterrows: per trace SA da migliaia di righe, iterrows e' l'origine principale
    del rallentamento/crash su molti file)."""
    out = seg[["iteration", "current_cost", "best_cost"]].copy()
    out["n"] = n
    out["m"] = m
    out["algorithm"] = algorithm
    out["seed"] = seed
    out["config"] = config_label
    out["source_file"] = source_file

    if collapse_flat and len(out) > 2:
        # tengo solo le righe in cui current_cost o best_cost cambiano rispetto alla
        # precedente (+ sempre la prima e l'ultima riga del segmento). Per SA, dove
        # il costo resta identico per centinaia di iterazioni di fila, questo riduce
        # il volume di dati anche di 10-100x senza perdere informazione per i grafici
        # di convergenza (che mostrano comunque un costo costante finche' non cambia).
        changed = (out["current_cost"].diff() != 0) | (out["best_cost"].diff() != 0)
        changed.iloc[0] = True
        changed.iloc[-1] = True
        out = out[changed]

    return out.reset_index(drop=True)


def build_master_dataframe(
    trace_dir: str,
    runs_csv_path: str,
    outdir: str,
    collapse_flat: bool = True,
    resume: bool = True,
    progress_every: int = 20,
) -> str:
    """Processa i file trace_*.csv UNO ALLA VOLTA e appende subito il risultato su
    disco (master_trace_long.csv), invece di accumulare tutto in una lista Python
    in RAM. Cosi':
      - la memoria di picco resta legata alla dimensione di un solo file per volta,
        non alla somma di tutti i file;
      - se lo script si interrompe (crash, Ctrl+C) a meta', i file gia' processati
        restano salvati su disco;
      - rilanciando lo script, i file gia' presenti in master_trace_long.csv
        (colonna source_file) vengono saltati automaticamente (resume).
    Ritorna il path del CSV prodotto.
    """
    runs_df = pd.read_csv(runs_csv_path)
    files = sorted(glob.glob(os.path.join(trace_dir, "trace_*.csv")))
    if not files:
        raise FileNotFoundError(f"Nessun file 'trace_*.csv' trovato in {trace_dir}")

    out_path = os.path.join(outdir, "master_trace_long.csv")
    already_done = set()
    if resume and os.path.exists(out_path):
        try:
            already_done = set(pd.read_csv(out_path, usecols=["source_file"])["source_file"].unique())
            print(f"Resume attivo: {len(already_done)} file gia' presenti in {out_path}, verranno saltati.")
        except Exception:
            already_done = set()

    file_exists = os.path.exists(out_path) and len(already_done) > 0
    total = len(files)
    n_written = 0
    n_skipped = 0
    n_errors = 0

    for i, path in enumerate(files, 1):
        fname = os.path.basename(path)
        if fname in already_done:
            n_skipped += 1
            continue

        try:
            info = parse_filename(path)
            df = pd.read_csv(path)
            segments = split_into_segments(df)
            matches = match_segments_to_n(segments, runs_df, info["algorithm"], info["seed"], info["params"])

            config_label = "_".join(f"{k}={v}" for k, v in info["params"].items())
            frames = [
                _segment_to_frame(
                    m["segment"], m["n"], m["m"], info["algorithm"], info["seed"],
                    config_label, fname, collapse_flat,
                )
                for m in matches
            ]
        except Exception as e:
            print(f"  [error] {fname}: {type(e).__name__}: {e} -> file saltato", file=sys.stderr)
            n_errors += 1
            continue

        if frames:
            out_df = pd.concat(frames, ignore_index=True)
            out_df.to_csv(out_path, mode="a" if file_exists else "w", header=not file_exists, index=False)
            file_exists = True
            n_written += len(out_df)

        # libero esplicitamente la memoria del file appena processato prima di passare al prossimo
        del df, segments, matches, frames

        if i % progress_every == 0 or i == total:
            print(f"[{i}/{total}] file processati (scartati per resume: {n_skipped}, errori: {n_errors})")

    if n_written == 0 and not already_done:
        raise RuntimeError("Nessun segmento e' stato abbinato correttamente a runs.csv.")

    print(f"Completato: {n_written} righe scritte in questa esecuzione, {n_errors} file con errori, {n_skipped} saltati (resume).")
    return out_path


# ----------------------------------------------------------------------
# Plot 1: convergenza ILS vs SA per una data dimensione n
# ----------------------------------------------------------------------
def plot_convergence_by_n(df_long: pd.DataFrame, n: int, outdir: str):
    sub = df_long[df_long["n"] == n]
    if sub.empty:
        return

    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = {"ils": "tab:blue", "sa": "tab:orange"}

    for algo in ["ils", "sa"]:

        s = sub[sub["algorithm"] == algo]
        if s.empty:
            continue

        # pivot: righe = iterazioni, colonne = run
        pivot = s.pivot_table(
            index="iteration",
            columns=["seed", "config"],
            values="best_cost",
            aggfunc="last",
        ).sort_index()

        # ogni run mantiene l'ultimo valore noto
        pivot = pivot.ffill()

        median = pivot.median(axis=1)
        q25 = pivot.quantile(0.25, axis=1)
        q75 = pivot.quantile(0.75, axis=1)

        ax.plot(
            median.index,
            median.values,
            color=colors[algo],
            lw=2.5,
            label=algo.upper(),
        )

        ax.fill_between(
            median.index,
            q25,
            q75,
            color=colors[algo],
            alpha=0.20,
        )

        # al massimo tre run di esempio
        for col in pivot.columns[:3]:
            ax.plot(
                pivot.index,
                pivot[col],
                color=colors[algo],
                alpha=0.12,
                lw=0.8,
            )

    ax.set_xscale("log")
    ax.set_xlabel("Iterazione")
    ax.set_ylabel("Costo della migliore soluzione")
    ax.set_title(f"Convergenza ILS vs SA (n={n})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, f"convergence_n{n}.png"))
    plt.close(fig)

# ----------------------------------------------------------------------
# Plot 2: banda di varianza multi-seed, per algoritmo e n fissati
# ----------------------------------------------------------------------
def plot_variance_band(df_long: pd.DataFrame, n: int, algorithm: str, outdir: str):
    sub = df_long[(df_long["n"] == n) & (df_long["algorithm"] == algorithm)]
    if sub.empty:
        return

    # prendo la configurazione con piu' seed disponibili
    counts = sub.groupby("config")["seed"].nunique()
    if counts.empty or counts.max() < 2:
        return  # non ho abbastanza seed per una banda di varianza
    best_config = counts.idxmax()
    s = sub[sub["config"] == best_config]

    pivot = s.pivot_table(index="iteration", columns="seed", values="best_cost", aggfunc="last")
    pivot = pivot.ffill()  # per allineare run di lunghezza leggermente diversa
    mean = pivot.mean(axis=1)
    std = pivot.std(axis=1)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(mean.index, mean.values, color="tab:green", linewidth=2, label=f"{algorithm.upper()} media")
    ax.fill_between(mean.index, mean - std, mean + std, color="tab:green", alpha=0.25, label="±1 std")
    ax.set_xscale("log")
    ax.set_xlabel("iterazione")
    ax.set_ylabel("costo della migliore soluzione trovata")
    ax.set_title(f"{algorithm.upper()} - varianza multi-seed (n={n}, {best_config})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, f"convergence_n{n}_{algorithm}_variance.png"))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trace-dir", required=True, help="cartella con i file trace_*.csv")
    ap.add_argument("--runs-csv", required=True, help="CSV aggregato (tuning_results.csv)")
    ap.add_argument("--outdir", default="figs_traces", help="cartella di output")
    ap.add_argument(
        "--no-resume", action="store_true",
        help="ignora master_trace_long.csv esistente e riparte da zero invece di saltare i file gia' processati",
    )
    ap.add_argument(
        "--no-collapse", action="store_true",
        help="non comprimere le righe consecutive a costo invariato (file piu' grande, usa piu' RAM per SA)",
    )
    ap.add_argument("--progress-every", type=int, default=20, help="ogni quanti file stampare un avanzamento")
    ap.add_argument(
        "--skip-plots", action="store_true",
        help="genera solo master_trace_long.csv, salta i grafici (utile per una prima passata su moltissimi file)",
    )
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    print("Parsing dei trace file e matching con runs.csv (streaming su disco, un file alla volta)...")
    master_path = build_master_dataframe(
        args.trace_dir, args.runs_csv, args.outdir,
        collapse_flat=not args.no_collapse,
        resume=not args.no_resume,
        progress_every=args.progress_every,
    )

    if args.skip_plots:
        print(f"--skip-plots attivo: {master_path} pronto, grafici saltati.")
        return

    print("Carico la tabella lunga per generare i grafici...")
    df_long = pd.read_csv(
        master_path,
        dtype={
            "n": "int32", "m": "int32", "iteration": "int64",
            "current_cost": "int64", "best_cost": "int64",
            "seed": "int32", "algorithm": "category", "config": "category",
        },
    )

    for n in sorted(df_long["n"].unique()):
        plot_convergence_by_n(df_long, n, args.outdir)
        for algo in ["ils", "sa"]:
            plot_variance_band(df_long, n, algo, args.outdir)

    print(f"Grafici salvati in: {args.outdir}/")


if __name__ == "__main__":
    main()
