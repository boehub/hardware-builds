import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, fm_calc as C
N = np.linspace(1, 8, 50); v = [C.row(n)["v"] for n in N]; g = [C.row(n)["g_h"] for n in N]
fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=200)
ax.axvspan(3, 5, color="#C79A3B", alpha=0.18); ax.text(4, 0.5, "working window", ha="center", fontsize=9)
ax.plot(N, v, color="#2563C4", lw=2); ax.set_xlabel("Screw rpm"); ax.set_ylabel("Filament m/min", color="#A5001E"); ax.grid(alpha=.3)
ax2 = ax.twinx(); ax2.set_ylabel("Output g/h", color="#2563C4"); ax2.set_ylim(np.array(ax.get_ylim()) * g[-1] / v[-1])
ax.set_title("Screw speed vs output (estimate)"); fig.tight_layout(); fig.savefig("out/img/d_speed.png")
