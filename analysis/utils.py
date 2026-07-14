from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR = Path("../data")
FIG_DIR = Path("figures")

FIG_DIR.mkdir(exist_ok=True)

def load_runs():
    return pd.read_csv(DATA_DIR / "runs.csv")

def savefig(name):
    plt.tight_layout()
    plt.savefig(FIG_DIR / name, dpi=300)
    plt.close()
