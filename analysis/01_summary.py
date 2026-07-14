from utils import *

df = load_runs()

summary = (
    df.groupby("algorithm")
      .agg(
          avg_cost=("best_cost","mean"),
          std_cost=("best_cost","std"),
          avg_time=("time","mean"),
          std_time=("time","std"),
          avg_iter=("best_iteration","mean"),
      )
)

print(summary)

summary.to_csv("figures/summary.csv")
