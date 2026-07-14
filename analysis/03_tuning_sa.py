from utils import *

df = load_runs()

sa = df[df.algorithm=="sa"]
# boxplot alpha
plt.figure(figsize=(8,5))

sa.boxplot(column="best_cost", by="alpha")

plt.suptitle("")
plt.title("Effect of alpha")
plt.ylabel("Best cost")

savefig("sa_alpha_boxplot.png")

# boxplot T0
plt.figure(figsize=(8,5))

sa.boxplot(column="best_cost", by="t0")

plt.suptitle("")
plt.title("Effect of initial temperature")

savefig("sa_t0_boxplot.png")

# scatter temppo/costo
plt.figure(figsize=(7,5))

plt.scatter(sa.time, sa.best_cost)

plt.xlabel("Time")
plt.ylabel("Best cost")

savefig("sa_time_cost.png")
