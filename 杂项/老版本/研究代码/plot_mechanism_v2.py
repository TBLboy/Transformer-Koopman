# -*- coding: utf-8 -*-
"""Rebuild Figure 3 (mechanism / normalized growth) with a short y-axis label
and collision-free data labels."""
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

print("prod norm:", [round(v, 3) for v in prod_n])
print("d_M  norm:", [round(v, 3) for v in dM_n])
print("e_x  norm:", [round(v, 3) for v in ex_n])

plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "legend.fontsize": 7,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "font.family": "serif", "mathtext.fontset": "dejavuserif",
    "axes.linewidth": 0.6, "lines.linewidth": 1.2, "lines.markersize": 4,
})

fig, ax = plt.subplots(figsize=(3.45, 2.7))

C_PROD, C_DM, C_EX = "#1f4e9c", "#c0392b", "#1e8449"
ax.plot(H, prod_n, "-o", color=C_PROD, label=r"$\|\mathbf{A}_{k+H-1}\cdots\mathbf{A}_k\|_2$")
ax.plot(H, dM_n, "-s", color=C_DM, label=r"$d_{\mathcal{M}}(H)$")
ax.plot(H, ex_n, "-^", color=C_EX, label=r"$e_x(H)$ (physical RMSE)")

# H = 1: all three curves coincide at 1.00 -> one shared label (no stacking)
ax.annotate("1.00", (1, 1.0), textcoords="offset points", xytext=(0, 7),
            ha="center", va="bottom", fontsize=6.5, color="#333333")

# H >= 5: per-curve labels, placed on the outside of each curve
for xv, yv in zip(H[1:], prod_n[1:]):
    ax.annotate(f"{yv:.2f}", (xv, yv), textcoords="offset points", xytext=(0, -12),
                ha="center", va="top", fontsize=6.5, color=C_PROD)
for xv, yv in zip(H[1:], dM_n[1:]):
    ax.annotate(f"{yv:.2f}", (xv, yv), textcoords="offset points", xytext=(0, 6),
                ha="center", va="bottom", fontsize=6.5, color=C_DM)
for xv, yv in zip(H[1:], ex_n[1:]):
    ax.annotate(f"{yv:.2f}", (xv, yv), textcoords="offset points", xytext=(0, 6),
                ha="center", va="bottom", fontsize=6.5, color=C_EX)

ax.set_xlabel(r"Prediction horizon $H$")
ax.set_ylabel("Normalized value")           # short label: no clipping
ax.set_xticks(H)
ax.set_xticklabels(["1", "5", "10", "20"])
ax.set_xlim(0.3, 20.9)
ax.set_ylim(0.15, 8.9)
ax.grid(True, which="both", linestyle=":", linewidth=0.4, alpha=0.6)
ax.legend(loc="upper left", frameon=False, handlelength=1.6, borderaxespad=0.3)

fig.tight_layout(pad=0.3)

pic = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\pictures")
pic.mkdir(parents=True, exist_ok=True)
fig.savefig(pic / "Figure_mechanism.pdf", bbox_inches="tight", pad_inches=0.02)
fig.savefig(pic / "Figure_mechanism.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
print("saved:", pic / "Figure_mechanism.pdf")
print("saved:", pic / "Figure_mechanism.png")
