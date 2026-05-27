from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams


# ==============================
# Adjustable parameters — paths default to the new project layout.
# Override ROOT_DIR / OUTPUT_DIR to point at a different code-projectv2 checkout.
# ==============================
ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT_DIR / "figures" / "ablation"

FIGSIZE = (3.45, 2.4)
DPI = 300
AXIS_LABEL_SIZE = 8
TICK_LABEL_SIZE = 7
ANNOTATION_SIZE = 6.5
BAR_HEIGHT = 0.62
ZERO_LINE_WIDTH = 0.8
SPINE_WIDTH = 0.6
BAR_EDGE_WIDTH = 0.6
ANNOTATION_OFFSET = 5.0
TABCOLSEP_PT = 3

DEGRADE_COLOR = "#7A7A7A"
IMPROVE_COLOR = "#C9C9C9"
BAR_EDGE_COLOR = "#333333"
IMPROVE_HATCH = "///"

FLEX_XLIM = (-35, 290)
SOFT_XLIM = (-60, 360)
LATEX_NL = "\\\\"


@dataclass(frozen=True)
class VariantSpec:
    variant_id: str
    short_label: str
    full_label: str
    group: str


PLATFORMS = {
    "platform1": {
        "baseline_rmse": 0.19248,
        "json_path": ROOT_DIR / "results" / "models" / "ablation_platform1" / "20260512_230907" / "test_results.json",
        "table_caption": "Ablation results on the flexible manipulator platform.",
        "table_label": "tab:ablation_flexible",
        "table_file": "table_ablation_flexible.tex",
        "figure_label": "fig:ablation_flexible",
        "figure_pdf": "fig_ablation_flexible.pdf",
        "figure_png": "fig_ablation_flexible.png",
        "figure_caption": (
            "Relative RMSE changes of representative ablation variants on the flexible manipulator platform. "
            "The results show that attention removal and excessive latent lifting cause the most severe degradation, "
            "while positional encoding has only a marginal effect."
        ),
        "xlim": FLEX_XLIM,
        "plot_order": [
            "latent_dim_d128",
            "no_attention",
            "n_layers_L1",
            "history_P8",
            "no_patch",
            "latent_dim_d32",
            "no_positional",
            "n_layers_L4",
        ],
        "variants": [
            VariantSpec("full_model", "Full Model", "Full Model (Baseline)", "Baseline"),
            VariantSpec("no_patch", "w/o Patch", "Without Patching", "Module"),
            VariantSpec("no_attention", "w/o Attention", "Without Attention", "Module"),
            VariantSpec("no_positional", "w/o Positional Enc.", "Without Positional Encoding", "Module"),
            VariantSpec("patch_L2", "Patch L=2", "Patch Length L=2", "Patch Length"),
            VariantSpec("patch_L8", "Patch L=8", "Patch Length L=8", "Patch Length"),
            VariantSpec("history_P8", "History P=8", "History P=8", "History Length"),
            VariantSpec("history_P32", "History P=32", "History P=32", "History Length"),
            VariantSpec("n_layers_L1", "Layers=1", "Transformer L=1 layers", "Transformer Depth"),
            VariantSpec("n_layers_L2", "Layers=2", "Transformer L=2 layers", "Transformer Depth"),
            VariantSpec("n_layers_L4", "Layers=4", "Transformer L=4 layers", "Transformer Depth"),
            VariantSpec("latent_dim_d32", "d=32", "Latent dim d=32", "Latent Dimension"),
            VariantSpec("latent_dim_d128", "d=128", "Latent dim d=128", "Latent Dimension"),
        ],
    },
    "platform2": {
        "baseline_rmse": 0.78149,
        "json_path": ROOT_DIR / "results" / "models" / "ablation_platform2" / "20260514_084213" / "test_results.json",
        "table_caption": "Ablation results on the soft robot platform.",
        "table_label": "tab:ablation_soft",
        "table_file": "table_ablation_soft.tex",
        "figure_label": "fig:ablation_soft",
        "figure_pdf": "fig_ablation_soft.pdf",
        "figure_png": "fig_ablation_soft.png",
        "figure_caption": (
            "Relative RMSE changes of representative ablation variants on the soft robot platform. "
            "Unlike the flexible manipulator, the soft robot is highly sensitive to positional encoding and history length, "
            "indicating stronger dependence on temporal ordering and longer memory."
        ),
        "xlim": SOFT_XLIM,
        "plot_order": [
            "n_layers_L2",
            "latent_dim_d32",
            "no_positional",
            "patch_L1",
            "no_patch",
            "patch_L4",
            "latent_dim_d4",
            "no_attention",
            "history_P2",
            "n_layers_L1",
            "history_P8",
        ],
        "variants": [
            VariantSpec("full_model", "Full Model", "Full Model (Baseline)", "Baseline"),
            VariantSpec("no_patch", "w/o Patch", "Without Patching", "Module"),
            VariantSpec("no_attention", "w/o Attention", "Without Attention", "Module"),
            VariantSpec("no_positional", "w/o Positional Enc.", "Without Positional Encoding", "Module"),
            VariantSpec("patch_L1", "Patch L=1", "Patch Length L=1", "Patch Length"),
            VariantSpec("patch_L4", "Patch L=4", "Patch Length L=4", "Patch Length"),
            VariantSpec("history_P2", "History P=2", "History P=2", "History Length"),
            VariantSpec("history_P8", "History P=8", "History P=8", "History Length"),
            VariantSpec("n_layers_L1", "Layers=1", "Transformer L=1 layers", "Transformer Depth"),
            VariantSpec("n_layers_L2", "Layers=2", "Transformer L=2 layers", "Transformer Depth"),
            VariantSpec("latent_dim_d4", "d=4", "Latent dim d=4", "Latent Dimension"),
            VariantSpec("latent_dim_d32", "d=32", "Latent dim d=32", "Latent Dimension"),
        ],
    },
}


def configure_fonts() -> None:
    candidates = ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"]
    installed = {font.name for font in font_manager.fontManager.ttflist}
    selected = next((name for name in candidates if name in installed), "DejaVu Serif")
    rcParams.update(
        {
            "font.family": selected,
            "font.size": TICK_LABEL_SIZE,
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def compact_params(value: int) -> str:
    return f"{value / 1000:.1f}K" if value >= 1000 else str(value)


def escape_latex(text: str) -> str:
    return text.replace("%", "\\%").replace("_", "\\_")


def load_metrics(json_path: Path) -> dict:
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)["test_metrics"]


def build_rows(platform_key: str) -> list[dict]:
    cfg = PLATFORMS[platform_key]
    metrics = load_metrics(cfg["json_path"])
    baseline = cfg["baseline_rmse"]
    best_variant_id = min(metrics.items(), key=lambda item: item[1]["rmse"])[0]
    rows: list[dict] = []

    for spec in cfg["variants"]:
        metric = metrics[spec.variant_id]
        rmse = round(float(metric["rmse"]), 5)
        mae = round(float(metric["mae"]), 5)
        delta = round((rmse - baseline) / baseline * 100.0, 1)
        rows.append(
            {
                "platform": platform_key,
                "group": spec.group,
                "variant": spec.full_label,
                "variant_id": spec.variant_id,
                "short_label": spec.short_label,
                "rmse": rmse,
                "mae": mae,
                "params": int(metric["params"]),
                "delta_rmse_percent": delta,
                "is_baseline": spec.variant_id == "full_model",
                "is_best": spec.variant_id == best_variant_id,
                "is_best_non_baseline": spec.variant_id == best_variant_id and spec.variant_id != "full_model",
            }
        )
    return rows


def write_csv(rows: list[dict], output_path: Path) -> None:
    fieldnames = [
        "platform",
        "group",
        "variant",
        "variant_id",
        "short_label",
        "rmse",
        "mae",
        "params",
        "delta_rmse_percent",
        "is_baseline",
        "is_best",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fieldnames})


def rmse_text(row: dict) -> str:
    text = f"{row['rmse']:.5f}"
    if row["is_best"]:
        text = f"\\textbf{{{text}}}"
        if row["is_best_non_baseline"]:
            text += "$^\\dagger$"
    return text


def delta_text(row: dict) -> str:
    if row["is_baseline"]:
        return "--"
    sign = "+" if row["delta_rmse_percent"] > 0 else ""
    return f"{sign}{row['delta_rmse_percent']:.1f}\\%"


def write_table(platform_key: str, rows: list[dict], output_path: Path) -> None:
    cfg = PLATFORMS[platform_key]
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        f"\\caption{{{cfg['table_caption']}}}",
        f"\\label{{{cfg['table_label']}}}",
        "\\scriptsize",
        f"\\setlength{{\\tabcolsep}}{{{TABCOLSEP_PT}pt}}",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        f"Variant & RMSE$\\downarrow$ & $\\Delta$RMSE & Params {LATEX_NL}",
        "\\midrule",
    ]

    previous_group = None
    for row in rows:
        if previous_group is not None and row["group"] != previous_group:
            lines.append("\\addlinespace[1pt]")
        previous_group = row["group"]
        lines.append(
            f"{escape_latex(row['short_label'])} & {rmse_text(row)} & {delta_text(row)} & {compact_params(row['params'])} {LATEX_NL}"
        )

    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\vspace{2pt}",
            "\\raggedright\\footnotesize $^\\dagger$ Best non-baseline configuration.",
            "\\end{table}",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_plot(platform_key: str, rows: list[dict], pdf_path: Path, png_path: Path) -> None:
    cfg = PLATFORMS[platform_key]
    row_map = {row["variant_id"]: row for row in rows}
    selected = [row_map[variant_id] for variant_id in cfg["plot_order"]]

    labels = [row["short_label"] for row in selected]
    values = [row["delta_rmse_percent"] for row in selected]
    positions = list(range(len(selected)))

    fig, ax = plt.subplots(figsize=FIGSIZE)
    for spine in ax.spines.values():
        spine.set_linewidth(SPINE_WIDTH)

    for pos, value in zip(positions, values):
        common = {
            "height": BAR_HEIGHT,
            "edgecolor": BAR_EDGE_COLOR,
            "linewidth": BAR_EDGE_WIDTH,
        }
        if value >= 0:
            ax.barh(pos, value, color=DEGRADE_COLOR, **common)
        else:
            ax.barh(pos, value, color=IMPROVE_COLOR, hatch=IMPROVE_HATCH, **common)

    ax.axvline(0, linestyle="--", linewidth=ZERO_LINE_WIDTH, color="#444444")
    ax.set_xlim(cfg["xlim"])
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=TICK_LABEL_SIZE)
    ax.tick_params(axis="x", labelsize=TICK_LABEL_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_LABEL_SIZE)
    ax.set_xlabel(r"$\Delta$RMSE (\%)", fontsize=AXIS_LABEL_SIZE)
    ax.grid(axis="x", linestyle=":", linewidth=0.5, color="#CFCFCF")
    ax.set_axisbelow(True)
    ax.invert_yaxis()

    for pos, value in zip(positions, values):
        if value >= 0:
            x = value + ANNOTATION_OFFSET
            ha = "left"
        else:
            x = value - ANNOTATION_OFFSET
            ha = "right"
        sign = "+" if value > 0 else ""
        ax.text(
            x,
            pos,
            f"{sign}{value:.1f}%",
            va="center",
            ha=ha,
            fontsize=ANNOTATION_SIZE,
        )

    fig.tight_layout(pad=0.4)
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(png_path, dpi=DPI, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def write_section_draft(output_path: Path) -> None:
    text = r"""\subsection{Ablation Studies}

\subsubsection{Results on the Flexible Manipulator}

\input{table_ablation_flexible.tex}

\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{fig_ablation_flexible.pdf}
    \caption{Relative RMSE changes of representative ablation variants on the flexible manipulator platform. The results show that attention removal and excessive latent lifting cause the most severe degradation, while positional encoding has only a marginal effect.}
    \label{fig:ablation_flexible}
\end{figure}

Table~\ref{tab:ablation_flexible} and Fig.~\ref{fig:ablation_flexible} show that the flexible manipulator mainly benefits from attention-based temporal interaction modeling. Removing attention produces the largest module-level degradation, increasing the rollout RMSE from 0.19248 to 0.51161 (+165.8\%), while removing patching also causes a substantial degradation of +62.6\%. By contrast, removing positional encoding only changes the RMSE by +3.0\%, which suggests that this platform is comparatively insensitive to absolute temporal order once local temporal aggregation is retained.

The hyperparameter ablations further indicate that the default configuration is already close to a strong operating point on this platform. Reducing the Transformer depth to one or two layers clearly harms performance, whereas increasing the depth to four layers yields only a marginal improvement to \textbf{0.18968}$^\dagger$. This small gain suggests that the baseline depth of three layers already captures most of the useful temporal interaction structure. Similarly, moderate changes to patch length and latent dimension only produce limited degradation, but over-expanding the latent dimension to $d=128$ severely worsens the RMSE by +229.5\%, indicating over-parameterized lifting and less stable latent dynamics.

The per-dimension errors are also consistent with this interpretation. For the flexible manipulator, the error is mainly concentrated in dimensions 1, 3, and 5. Removing attention increases the RMSE of dim1 from 0.2895 to 0.8256 and dim3 from 0.2588 to 0.7427, suggesting that attention is essential for capturing coupled temporal interactions across the multivariate state trajectory.

\subsubsection{Results on the Soft Robot}

\input{table_ablation_soft.tex}

\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{fig_ablation_soft.pdf}
    \caption{Relative RMSE changes of representative ablation variants on the soft robot platform. Unlike the flexible manipulator, the soft robot is highly sensitive to positional encoding and history length, indicating stronger dependence on temporal ordering and longer memory.}
    \label{fig:ablation_soft}
\end{figure}

The soft robot exhibits a different ablation pattern. As shown in Table~\ref{tab:ablation_soft} and Fig.~\ref{fig:ablation_soft}, removing positional encoding causes the largest module-level degradation, increasing the RMSE from 0.78149 to 1.82345 (+133.3\%). Removing patching also produces a large degradation (+85.1\%), while removing attention causes a smaller but still substantial increase of +48.5\%. These results indicate that the soft robot depends more strongly on temporal ordering information than the flexible manipulator.

The parameter sweep shows that longer temporal memory is beneficial on this platform. Increasing the history length from the default $P=4$ to $P=8$ reduces the RMSE by 37.1\%, and even the shorter setting $P=2$ still improves over the default baseline by 17.4\%. In addition, reducing the Transformer depth to one layer improves the RMSE by 22.2\%, whereas using two layers causes a dramatic failure case with +279.7\% degradation. A similarly strong deterioration appears when the latent dimension is expanded to $d=32$ (+185.4\%), which indicates that this lower-dimensional system is more vulnerable to over-parameterized temporal lifting.

The per-dimension statistics highlight the source of these failures. Removing positional encoding dramatically increases the RMSE of dim1 from 0.3321 to 2.4798, which suggests that temporal ordering is crucial for this platform. The unstable Layers=2 case mainly comes from dim0, whose RMSE increases from 1.0541 to 4.1818, implying that the deeper temporal encoder can become unstable even when the second state component remains relatively well behaved.

\subsubsection{Cross-Platform Discussion}

The ablation results reveal platform-dependent temporal modeling requirements rather than inconsistency of the proposed framework. On the flexible manipulator, the dominant factor is attention-based global temporal interaction, while positional encoding has only a marginal effect. On the soft robot, by contrast, positional encoding and history length are far more important, indicating stronger reliance on temporal ordering and longer effective memory. These results suggest that PatchTST-Koopman adapts to different temporal structures across dynamical systems: the flexible manipulator benefits more from global temporal interaction modeling, whereas the soft robot depends more strongly on explicit ordering cues and memory length. Therefore, the optimal temporal configuration should be understood as platform-dependent, even though the full PatchTST-Koopman design provides a consistent and effective temporal lifting framework across both systems.
"""
    output_path.write_text(text, encoding="utf-8")


def main() -> None:
    configure_fonts()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows_by_platform: dict[str, list[dict]] = {}
    all_rows: list[dict] = []
    for platform_key in ("platform1", "platform2"):
        rows = build_rows(platform_key)
        rows_by_platform[platform_key] = rows
        all_rows.extend(rows)

    write_csv(all_rows, OUTPUT_DIR / "ablation_data_clean.csv")

    for platform_key, rows in rows_by_platform.items():
        cfg = PLATFORMS[platform_key]
        write_table(platform_key, rows, OUTPUT_DIR / cfg["table_file"])
        write_plot(platform_key, rows, OUTPUT_DIR / cfg["figure_pdf"], OUTPUT_DIR / cfg["figure_png"])

    write_section_draft(OUTPUT_DIR / "ablation_section_draft.tex")

    print("Generated files:")
    for path in sorted(OUTPUT_DIR.iterdir()):
        if path.is_file():
            print(path.name)


if __name__ == "__main__":
    main()
