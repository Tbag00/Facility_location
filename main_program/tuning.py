"""
Script di parameter tuning per il solver FLP (ILS / SA).

Cosa fa:
1. (opzionale) genera istanze sintetiche del problema, oppure usa istanze
   già esistenti sul disco (via USE_GENERATED_INSTANCES).
2. costruisce la griglia di combinazioni di metaparametri per ILS e SA.
3. lancia il binario OCaml una volta per ogni combinazione (x ogni istanza
   x ogni seed), scrivendo tutti i risultati in un unico runs.csv tramite
   Csv_logger.runs_logger (append_row già gestisce l'accodamento).
4. a fine run, carica il CSV con pandas e mostra un'anteprima/tabella
   riassuntiva grezza —

"""

import itertools
import subprocess
import sys
import random
from pathlib import Path
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# CONFIGURAZIONE — modifica qui
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent / "main_program"  # adatta se serve
EXECUTABLE = PROJECT_ROOT / "_build/default/bin/main.exe"

INSTANCES_DIR = PROJECT_ROOT / "data" / "tuning_instances"
RESULTS_CSV = PROJECT_ROOT / "tuning_results.csv"

SEEDS = [111, 222, 333]  # più seed per run = stima meno rumorosa del best_cost

# scegli True per generare istanze sintetiche al volo, False per usare
# istanze già presenti (elenca i path in MANUAL_INSTANCES)
USE_GENERATED_INSTANCES = True

# usata solo se USE_GENERATED_INSTANCES = True
GENERATED_INSTANCE_SIZES = [
    # (n facilities, m customers)
    (10, 20),
    (20, 40),
]

# usata solo se USE_GENERATED_INSTANCES = False
MANUAL_INSTANCES = [
    PROJECT_ROOT / "data" / "input1.txt",
    PROJECT_ROOT / "data" / "input_medium.txt",
]

# griglia metaparametri ILS
ILS_GRID = {
    "iterations": [10, 100, 1000, 10000],
    "p_mut":      [0.1, 0.05, 0.01],
}

# griglia metaparametri SA
SA_GRID = {
    "t0":      [10.0, 50.0, 100.0, 300.0, 600.0],
    "t_end":   [0.01, 0.1, 1.0],
    "alpha":   [0.85, 0.90, 0.95, 0.99],
    "new_low": [10, 50, 100],
}

RUN_TIMEOUT_SECONDS = 300  # kill una run che si impalla, non l'intera campagna


# ---------------------------------------------------------------------------
# GENERAZIONE ISTANZE 
# ---------------------------------------------------------------------------

def generate_instance(n: int, m: int, seed: int, out_path: Path) -> None:
    """Genera un'istanza sintetica UFLP nel formato atteso da Reader.

    Costi di apertura nella stessa scala di (costo_medio * domanda_media),
    cosi' aprire/chiudere una facility resta una scelta non banale (vedi
    discussione precedente sull'istanza n=5 "degenere").
    """
    rng = random.Random(seed)
    shipment = [[rng.randint(1, 100) for _ in range(m)] for _ in range(n)]
    demand = [rng.randint(5, 50) for _ in range(m)]
    opening = [rng.randint(300, 1500) for _ in range(n)]

    lines = [
        f"NUMBER_FACILITIES={n}",
        f"NUMBER_COSTUMERS={m}",
        "SHIPMENT_COSTS_MATRIX=" + ";".join(",".join(map(str, row)) for row in shipment),
        "DEMAND=" + ",".join(map(str, demand)),
        "COST_TO_OPEN=" + ",".join(map(str, opening)),
    ]
    out_path.write_text("\n".join(lines) + "\n")


def prepare_instances() -> list[Path]:
    if not USE_GENERATED_INSTANCES:
        missing = [p for p in MANUAL_INSTANCES if not p.exists()]
        if missing:
            sys.exit(f"Istanze mancanti su disco: {missing}")
        return MANUAL_INSTANCES

    INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for (n, m) in GENERATED_INSTANCE_SIZES:
        path = INSTANCES_DIR / f"instance_n{n}_m{m}.txt"
        # rigenera solo se non esiste già, cosi' le run restano riproducibili
        # anche rilanciando lo script più volte
        if not path.exists():
            generate_instance(n, m, seed=n * 1000 + m, out_path=path)
        paths.append(path)
    return paths


# ---------------------------------------------------------------------------
# ESECUZIONE DELLE RUN
# ---------------------------------------------------------------------------

def build_project() -> None:
    print("Compilazione del progetto (dune build)...")
    result = subprocess.run(["dune", "build"], cwd=PROJECT_ROOT)
    if result.returncode != 0:
        sys.exit("dune build fallito, correggi gli errori prima di lanciare il tuning.")


def param_combinations(grid: dict) -> list[dict]:
    keys = list(grid.keys())
    values_product = itertools.product(*grid.values())
    return [dict(zip(keys, values)) for values in values_product]


def run_once(instance_path: Path, algorithm: str, seed: int, params: dict) -> bool:
    """Lancia una singola run del binario. Ritorna True se completata senza errori."""
    cmd = [
        str(EXECUTABLE),
        str(instance_path),
        "-a", algorithm,
        "-s", str(seed),
        "-o", str(RESULTS_CSV.with_suffix("")),  # main.ml aggiunge ".csv" da solo
    ]
    for key, value in params.items():
        cmd += ["-p", f"{key}={value}"]

    try:
        result = subprocess.run(
            cmd, cwd=PROJECT_ROOT, capture_output=True, text=True,
            timeout=RUN_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {instance_path.name} {algorithm} seed={seed} {params}")
        return False

    if result.returncode != 0:
        print(f"  [ERRORE] {instance_path.name} {algorithm} seed={seed} {params}")
        print("  stderr:", result.stderr.strip()[:300])
        return False
    return True


def run_campaign(instances: list[Path]) -> None:
    ils_combos = param_combinations(ILS_GRID)
    sa_combos = param_combinations(SA_GRID)

    total_runs = len(instances) * len(SEEDS) * (len(ils_combos) + len(sa_combos))
    print(f"Totale run pianificate: {total_runs}")

    done = 0
    failed = 0
    for instance_path in instances:
        for seed in SEEDS:
            for params in ils_combos:
                ok = run_once(instance_path, "ils", seed, params)
                done += 1
                failed += 0 if ok else 1
                print(f"[{done}/{total_runs}] ILS  {instance_path.name} seed={seed} {params}"
                      + ("" if ok else "  <-- fallita"))
            for params in sa_combos:
                ok = run_once(instance_path, "sa", seed, params)
                done += 1
                failed += 0 if ok else 1
                print(f"[{done}/{total_runs}] SA   {instance_path.name} seed={seed} {params}"
                      + ("" if ok else "  <-- fallita"))

    print(f"\nCampagna completata: {done - failed}/{done} run riuscite ({failed} fallite).")


# ---------------------------------------------------------------------------
# CARICAMENTO E ANTEPRIMA RISULTATI (analisi vera e propria: prossimo step)
# ---------------------------------------------------------------------------

def load_results() -> pd.DataFrame:
    if not RESULTS_CSV.exists():
        sys.exit(f"Nessun file di risultati trovato in {RESULTS_CSV}")
    df = pd.read_csv(RESULTS_CSV)
    return df


def preview_results(df: pd.DataFrame) -> None:
    print("\n--- Anteprima risultati ---")
    print(f"Righe totali: {len(df)}")
    print(df.head(10))

    print("\n--- Best cost medio per algoritmo ---")
    print(df.groupby("algorithm")["best_cost"].agg(["mean", "min", "count"]))


# ---------------------------------------------------------------------------

def main() -> None:
    build_project()
    instances = prepare_instances()
    print(f"Istanze usate: {[p.name for p in instances]}")

    start = datetime.now()
    run_campaign(instances)
    print(f"Tempo totale campagna: {datetime.now() - start}")

    df = load_results()
    preview_results(df)


if __name__ == "__main__":
    main()
