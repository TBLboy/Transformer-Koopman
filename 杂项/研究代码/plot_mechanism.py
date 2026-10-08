import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TMP = Path(r"C:\Users\12187\AppData\Local\Temp\opencode")
d = json.loads((TMP / "gate16_diag_fix.json").read_text(encoding="utf-8"))

H = [1, 5, 10, 20]
prod = [d["prod"][str(h)] for h in H]
dM = [d["d_norm"][str(h)] for h in H]
ex = [d["corollary1_bound_LF"][str(h)]["actual_phys_rmse"] for h in H]

n = lambda a: [v / a[0] for v in a]
prod_n, dM_n, ex_n = n(prod), n(dM), n(ex)

print("H          :", H)
print("prod   raw :", [round(v, 4) for v in prod], " norm:", [round(v, 3) for v in prod_n])
print("d_M    raw :", [round(v, 4) for v in dM], " norm:", [round(v, 3) for v in dM_n])
print("e_x    raw :", [round(v, 4) for v in ex], " norm:", [round(v, 3) for v in ex_n])

plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "legend.fontsize": 7,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "font.family": "serif", "mathtext.fontset": "dejavuserif",
    "axes.linewidth": 0.6, "lines.linewidth": 1.2, "lines.markersize": 4,
})
fig, ax = plt.subplots(figsize=(3.45, 2.5))

ax.plot(H, prod_n, "-o", color="#1f4e9c", label=r"$\|\mathbf{A}_{k+H-1}\cdots\mathbf{A}_k\|_2$")
ax.plot(H, dM_n, "-s", color="#c0392b", label=r"$d_{\mathcal{M}}(H)$")
ax.plot(H, ex_n, "-^", color="#1e8449", label=r"$e_x(H)$ (physical RMSE)")

for xv, yv in zip(H, prod_n):
    ax.annotate(f"{yv:.2f}", (xv, yv), textcoords="offset points", xytext=(0, -11), ha="center", fontsize=6.5, color="#1f4e9c")
for xv, yv in zip(H, dM_n):
    ax.annotate(f"{yv:.2f}", (xv, yv), textcoords="offset points", xytext=(0, 5), ha="center", fontsize=6.5, color="#c0392b")
for xv, yv in zip(H, ex_n):
    ax.annotate(f"{yv:.2f}", (xv, yv), textcoords="offset points", xytext=(0, 5), ha="center", fontsize=6.5, color="#1e8449")

ax.set_xlabel(r"Prediction horizon $H$")
ax.set_ylabel(r"Normalized value (divided by value at $H{=}1$)")
ax.set_xticks(H)
ax.set_xticklabels(["1", "5", "10", "20"])
ax.set_ylim(0.5, 8.6)
ax.grid(True, which="both", linestyle=":", linewidth=0.4, alpha=0.6)
ax.legend(loc="upper left", frameon=False, handlelength=1.6)
fig.tight_layout(pad=0.3)

pic = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\pictures")
pic.mkdir(parents=True, exist_ok=True)
fig.savefig(pic / "Figure_mechanism.pdf")
fig.savefig(pic / "Figure_mechanism.png", dpi=300)
print("saved:", pic / "Figure_mechanism.pdf")
print("saved:", pic / "Figure_mechanism.png")
