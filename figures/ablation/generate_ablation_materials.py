from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams


# ==============================
# Adjustable parameters
# ==============================
ROOT_DIR = Path(__file__).resolve().parents[2]
RESULTS_ROOT = ROOT_DIR / "results"
OUTPUT_DIR = ROOT_DIR / "figures" / "ablation"

FIGSIZE = (3.45, 2.4)
METRIC_FIGSIZE = (6.8, 3.2)
DPI = 300
AXIS_LABEL_SIZE = 8
TICK_LABEL_SIZE = 7
ANNOTATION_SIZE = 6.5
METRIC_ANNOTATION_SIZE = 6.0
METRIC_TOP_MARGIN_PT = 8.0
BAR_HEIGHT = 0.62
ZERO_LINE_WIDTH = 0.8
SPINE_WIDTH = 0.6
BAR_EDGE_WIDTH = 0.6
# Gap (pt) between bar tip and percent label.
ANNOTATION_GAP_PT = 4.0
# Target gap (pt) from axes spine to outermost bar / percent label inside the plot box.
FRAME_MARGIN_PT = 5.5
# Target gap (pt) from y-axis variant labels to the left axes spine.
YLABEL_MARGIN_PT = 4.0
XLIM_MARGIN_MAX_ITERS = 10
TABCOLSEP_PT = 3

DEGRADE_COLOR = "#7A7A7A"
IMPROVE_COLOR = "#C9C9C9"
BAR_EDGE_COLOR = "#333333"
IMPROVE_HATCH = "///"
BASELINE_COLOR = "#B8B8B8"
MODULE_COLOR = "#4C78A8"
PARAMETER_COLOR = "#F58518"

LATEX_NL = "\\\\"

# Top-to-bottom in the bar chart (module first, then hyperparameter sweeps).
GROUP_PLOT_ORDER = [
    "Module",
    "Patch Length",
    "History Length",
    "Transformer Depth",
    "Latent Dimension",
]
MODULE_VARIANT_ORDER = ["no_patch", "no_attention", "no_positional"]
PLOT_EXCLUDE_VARIANTS = {"full_model"}

LEGACY_OUTPUT_NAMES = (
    "fig_ablation_flexible.pdf",
    "fig_ablation_flexible.png",
    "fig_ablation_soft.pdf",
    "fig_ablation_soft.png",
    "table_ablation_flexible.tex",
    "table_ablation_soft.tex",
)


def platform_output_artifacts(platform_key: str) -> dict[str, str]:
    """Output filenames and LaTeX labels derived from platform1 / platform2."""
    return {
        "figure_pdf": f"fig_ablation_{platform_key}.pdf",
        "figure_png": f"fig_ablation_{platform_key}.png",
        "metric_figure_pdf": f"fig_ablation_metric_{platform_key}.pdf",
        "metric_figure_png": f"fig_ablation_metric_{platform_key}.png",
        "table_file": f"table_ablation_{platform_key}.tex",
        "figure_label": f"fig:ablation_{platform_key}",
        "metric_figure_label": f"fig:ablation_metric_{platform_key}",
        "table_label": f"tab:ablation_{platform_key}",
    }


@dataclass(frozen=True)
class VariantSpec:
    variant_id: str
    short_label: str
    full_label: str
    group: str


PLATFORM_VARIANTS = {
    "platform1": {
        "name": "platform1 (Flexible Manipulator)",
        "figure_caption": (
            "Relative RMSE changes of ablation variants on platform1 (flexible manipulator). "
            "Attention removal and excessive latent lifting cause the most severe degradation, "
            "while positional encoding has only a marginal effect."
        ),
        "table_caption": "Ablation results for platform1.",
        "variants": [
            VariantSpec("full_model", "Full Model", "Full Model (Baseline)", "Baseline"),
            VariantSpec("no_patch", "w/o Patch", "Without Patching", "Module"),
            VariantSpec("no_attention", "w/o Attention", "Without Attention", "Module"),
            VariantSpec("no_positional", "w/o Positional Enc.", "Without Positional Encoding", "Module"),
            VariantSpec("patch_L2", "Patch L=2", "Patch Length L=2", "Patch Length"),
            VariantSpec("patch_L4", "Patch L=4", "Patch Length L=4", "Patch Length"),
            VariantSpec("patch_L8", "Patch L=8", "Patch Length L=8", "Patch Length"),
            VariantSpec("patch_L16", "Patch L=16", "Patch Length L=16", "Patch Length"),
            VariantSpec("history_P4", "P=4", "History P=4", "History Length"),
            VariantSpec("history_P8", "P=8", "History P=8", "History Length"),
            VariantSpec("history_P16", "P=16", "History P=16", "History Length"),
            VariantSpec("history_P32", "P=32", "History P=32", "History Length"),
            VariantSpec("history_P64", "P=64", "History P=64", "History Length"),
            VariantSpec("n_layers_L1", "L=1", "Transformer L=1 layers", "Transformer Depth"),
            VariantSpec("n_layers_L2", "L=2", "Transformer L=2 layers", "Transformer Depth"),
            VariantSpec("n_layers_L3", "L=3", "Transformer L=3 layers", "Transformer Depth"),
            VariantSpec("n_layers_L4", "L=4", "Transformer L=4 layers", "Transformer Depth"),
            VariantSpec("n_layers_L6", "L=6", "Transformer L=6 layers", "Transformer Depth"),
            VariantSpec("latent_dim_d12", "d=12", "Latent dim d=12", "Latent Dimension"),
            VariantSpec("latent_dim_d32", "d=32", "Latent dim d=32", "Latent Dimension"),
            VariantSpec("latent_dim_d64", "d=64", "Latent dim d=64", "Latent Dimension"),
            VariantSpec("latent_dim_d128", "d=128", "Latent dim d=128", "Latent Dimension"),
            VariantSpec("latent_dim_d256", "d=256", "Latent dim d=256", "Latent Dimension"),
        ],
    },
    "platform2": {
        "name": "platform2 (Soft Robot)",
        "figure_caption": (
            "Relative RMSE changes of ablation variants on platform2 (soft robot). "
            "Unlike platform1, platform2 is highly sensitive to positional encoding and history length, "
            "indicating stronger dependence on temporal ordering and longer memory."
        ),
        "table_caption": "Ablation results for platform2.",
        "variants": [
            VariantSpec("full_model", "Full Model", "Full Model (Baseline)", "Baseline"),
            VariantSpec("no_patch", "w/o Patch", "Without Patching", "Module"),
            VariantSpec("no_attention", "w/o Attention", "Without Attention", "Module"),
            VariantSpec("no_positional", "w/o Positional Enc.", "Without Positional Encoding", "Module"),
            VariantSpec("patch_L1", "Patch L=1", "Patch Length L=1", "Patch Length"),
            VariantSpec("patch_L4", "Patch L=4", "Patch Length L=4", "Patch Length"),
            VariantSpec("history_P2", "P=2", "History P=2", "History Length"),
            VariantSpec("history_P4", "P=4", "History P=4", "History Length"),
            VariantSpec("history_P6", "P=6", "History P=6", "History Length"),
            VariantSpec("history_P8", "P=8", "History P=8", "History Length"),
            VariantSpec("history_P12", "P=12", "History P=12", "History Length"),
            VariantSpec("history_P16", "P=16", "History P=16", "History Length"),
            VariantSpec("n_layers_L1", "L=1", "Transformer L=1 layers", "Transformer Depth"),
            VariantSpec("n_layers_L2", "L=2", "Transformer L=2 layers", "Transformer Depth"),
            VariantSpec("n_layers_L3", "L=3", "Transformer L=3 layers", "Transformer Depth"),
            VariantSpec("n_layers_L4", "L=4", "Transformer L=4 layers", "Transformer Depth"),
            VariantSpec("latent_dim_d4", "d=4", "Latent dim d=4", "Latent Dimension"),
            VariantSpec("latent_dim_d8", "d=8", "Latent dim d=8", "Latent Dimension"),
            VariantSpec("latent_dim_d16", "d=16", "Latent dim d=16", "Latent Dimension"),
            VariantSpec("latent_dim_d32", "d=32", "Latent dim d=32", "Latent Dimension"),
            VariantSpec("latent_dim_d64", "d=64", "Latent dim d=64", "Latent Dimension"),
        ],
    },
}


def _load_latest_metrics(platform):
    """Find the latest run for a platform and load metrics."""
    base = RESULTS_ROOT / "ablation" / platform / f"ablation_{platform}"
    if not base.exists():
        return None, None
    dirs = sorted([d for d in base.iterdir() if d.is_dir()], reverse=True)
    if not dirs:
        return None, None
    for name in ("test_results.json", "ablation_results.json"):
        p = dirs[0] / name
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            metrics = data.get("test_metrics", data.get("results", None))
            if metrics is None:
                metrics = data
            return metrics, p
    return None, None


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


def _variant_numeric_key(variant_id: str) -> int:
    match = re.search(r"(\d+)$", variant_id)
    return int(match.group(1)) if match else 0


def _variant_sort_key(spec: VariantSpec) -> tuple:
    try:
        group_idx = GROUP_PLOT_ORDER.index(spec.group)
    except ValueError:
        group_idx = len(GROUP_PLOT_ORDER)
    if spec.group == "Module":
        try:
            module_idx = MODULE_VARIANT_ORDER.index(spec.variant_id)
        except ValueError:
            module_idx = len(MODULE_VARIANT_ORDER)
        return (group_idx, module_idx, spec.variant_id)
    return (group_idx, _variant_numeric_key(spec.variant_id), spec.variant_id)


def build_plot_order(platform_key: str, available_ids: set[str] | None = None) -> list[str]:
    """Module ablations first, then parameter sweeps in a fixed group order."""
    cfg = PLATFORM_VARIANTS[platform_key]
    specs = [s for s in cfg["variants"] if s.variant_id not in PLOT_EXCLUDE_VARIANTS]
    if available_ids is not None:
        specs = [s for s in specs if s.variant_id in available_ids]
    specs.sort(key=_variant_sort_key)
    return [spec.variant_id for spec in specs]


def order_rows_for_display(rows: list[dict], platform_key: str) -> list[dict]:
    """Baseline row first, then module and parameter ablations in plot order."""
    row_map = {row["variant_id"]: row for row in rows}
    ordered: list[dict] = []
    if "full_model" in row_map:
        ordered.append(row_map["full_model"])
    for variant_id in build_plot_order(platform_key, set(row_map)):
        ordered.append(row_map[variant_id])
    return ordered


def build_rows(platform_key: str) -> list[dict]:
    cfg = PLATFORM_VARIANTS[platform_key]
    metrics, src_path = _load_latest_metrics(platform_key)
    if metrics is None:
        raise FileNotFoundError(
            f"No ablation results found for {platform_key} under {RESULTS_ROOT}"
        )

    baseline_entry = metrics.get("full_model")
    baseline = float(baseline_entry["rmse"]) if baseline_entry else None
    if baseline is None:
        raise ValueError(f"No full_model (baseline) found for {platform_key}")

    best_variant_id = min(metrics.items(), key=lambda item: float(item[1]["rmse"]))[0]
    rows: list[dict] = []

    for spec in cfg["variants"]:
        metric = metrics.get(spec.variant_id)
        if metric is None or metric.get("rmse") is None:
            print(f"  WARNING: {spec.variant_id} not found or failed in {src_path}, skipping")
            continue
        import math
        raw_rmse = float(metric["rmse"])
        if math.isnan(raw_rmse):
            print(f"  WARNING: {spec.variant_id} RMSE is NaN, skipping")
            continue
        rmse = round(raw_rmse, 5)
        mae = round(float(metric["mae"]), 5)
        delta = round((rmse - baseline) / baseline * 100.0, 1)
        raw_params = metric.get("params")
        params_val = int(raw_params) if raw_params is not None else 0
        rows.append(
            {
                "platform": platform_key,
                "group": spec.group,
                "variant": spec.full_label,
                "variant_id": spec.variant_id,
                "short_label": spec.short_label,
                "rmse": rmse,
                "mae": mae,
                "params": params_val,
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


def _annotation_label(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


def _bar_x_bounds(values: list[float]) -> tuple[float, float]:
    return min(0.0, min(values)), max(0.0, max(values))


def _initial_xlim(values: list[float]) -> tuple[float, float]:
    left, right = _bar_x_bounds(values)
    inner = max(right - left, 1.0)
    pad = 0.25 * inner + 10.0
    return left - pad, right + pad


def _content_xlim_px(ax, values: list[float], texts: list, renderer) -> tuple[float, float]:
    """Outermost content edges in display pixels (x only)."""
    left_px = float("inf")
    right_px = float("-inf")

    for value in values:
        bar_x = max(0.0, value) if value >= 0 else min(0.0, value)
        tip_px = ax.transData.transform((bar_x, 0.0))[0]
        left_px = min(left_px, tip_px)
        right_px = max(right_px, tip_px)

    for text in texts:
        bb = text.get_window_extent(renderer)
        left_px = min(left_px, bb.x0)
        right_px = max(right_px, bb.x1)

    return left_px, right_px


def _fit_xlim_to_frame_margin(
    ax,
    values: list[float],
    texts: list,
    renderer,
    margin_pt: float,
) -> tuple[float, float]:
    """
    Adjust xlim until bar tips and labels sit margin_pt inside the spines.

    Uses display-space measurements so the gap stays constant in points.
    Expands when content overflows; shrinks when the plot is unnecessarily wide.
    """
    x_min, x_max = ax.get_xlim()
    tolerance_pt = 0.35

    for _ in range(XLIM_MARGIN_MAX_ITERS):
        content_left_px, content_right_px = _content_xlim_px(ax, values, texts, renderer)
        ax_bbox = ax.get_window_extent(renderer)
        data_per_px = (x_max - x_min) / max(ax_bbox.width, 1.0)

        delta_left_pt = margin_pt - (content_left_px - ax_bbox.x0)
        delta_right_pt = margin_pt - (ax_bbox.x1 - content_right_px)

        if abs(delta_left_pt) <= tolerance_pt and abs(delta_right_pt) <= tolerance_pt:
            break

        if abs(delta_left_pt) > tolerance_pt:
            x_min -= delta_left_pt * data_per_px
        if abs(delta_right_pt) > tolerance_pt:
            x_max += delta_right_pt * data_per_px

        ax.set_xlim(x_min, x_max)
        ax.figure.canvas.draw()
        renderer = ax.figure.canvas.get_renderer()

    return x_min, x_max


def _add_bar_annotations(ax, positions: list[int], values: list[float]) -> list:
    """Place percent labels in offset points so spacing is independent of xlim."""
    artists = []
    for pos, value in zip(positions, values):
        offset = ANNOTATION_GAP_PT if value >= 0 else -ANNOTATION_GAP_PT
        artists.append(
            ax.annotate(
                _annotation_label(value),
                xy=(value, pos),
                xytext=(offset, 0),
                textcoords="offset points",
                va="center",
                ha="left" if value >= 0 else "right",
                fontsize=ANNOTATION_SIZE,
            )
        )
    return artists


def _adjust_left_margin_for_ylabels(fig, ax, renderer, margin_pt: float) -> None:
    """Shift axes right if y tick labels intrude on the left spine."""
    ax_bbox = ax.get_window_extent(renderer)
    label_right = ax_bbox.x0
    for label in ax.get_yticklabels():
        if not label.get_visible():
            continue
        bb = label.get_window_extent(renderer)
        label_right = max(label_right, bb.x1)

    deficit_pt = label_right + margin_pt - ax_bbox.x0
    if deficit_pt <= 0:
        return

    fig_bbox = fig.get_window_extent(renderer)
    shift_frac = deficit_pt / max(fig_bbox.width, 1.0)
    subplot = fig.subplotpars
    new_left = min(subplot.left + shift_frac, 0.62)
    fig.subplots_adjust(
        left=new_left,
        right=subplot.right,
        top=subplot.top,
        bottom=subplot.bottom,
    )


def _finalize_plot_layout(fig, ax, values: list[float], texts: list, labels: list[str]) -> None:
    max_label_chars = max(len(label) for label in labels)
    fig.subplots_adjust(
        left=min(0.48, 0.30 + max_label_chars * 0.012),
        right=0.94,
        top=0.98,
        bottom=0.16,
    )

    ax.set_xlim(_initial_xlim(values))
    fig.canvas.draw()

    _fit_xlim_to_frame_margin(
        ax, values, texts, fig.canvas.get_renderer(), FRAME_MARGIN_PT
    )
    _adjust_left_margin_for_ylabels(fig, ax, fig.canvas.get_renderer(), YLABEL_MARGIN_PT)
    fig.canvas.draw()
    _fit_xlim_to_frame_margin(
        ax, values, texts, fig.canvas.get_renderer(), FRAME_MARGIN_PT
    )


def write_table(platform_key: str, rows: list[dict], output_path: Path) -> None:
    cfg = PLATFORM_VARIANTS[platform_key]
    artifacts = platform_output_artifacts(platform_key)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        f"\\caption{{{cfg['table_caption']}}}",
        f"\\label{{{artifacts['table_label']}}}",
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
    row_map = {row["variant_id"]: row for row in rows}
    plot_order = build_plot_order(platform_key, set(row_map))
    selected = [row_map[variant_id] for variant_id in plot_order]

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
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=TICK_LABEL_SIZE)
    ax.tick_params(axis="x", labelsize=TICK_LABEL_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_LABEL_SIZE)
    ax.set_xlabel(r"$\Delta$RMSE (\%)", fontsize=AXIS_LABEL_SIZE)
    ax.grid(axis="x", linestyle=":", linewidth=0.5, color="#CFCFCF")
    ax.set_axisbelow(True)
    ax.invert_yaxis()

    annotations = _add_bar_annotations(ax, positions, values)
    _finalize_plot_layout(fig, ax, values, annotations, labels)
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(png_path, dpi=DPI, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def _metric_bar_color(row: dict) -> str:
    if row["is_baseline"]:
        return BASELINE_COLOR
    if row["group"] == "Module":
        return MODULE_COLOR
    return PARAMETER_COLOR


def _metric_group_boundaries(rows: list[dict]) -> list[int]:
    boundaries: list[int] = []
    previous_group = rows[0]["group"] if rows else ""
    for idx, row in enumerate(rows[1:], start=1):
        if row["group"] != previous_group:
            boundaries.append(idx)
            previous_group = row["group"]
    return boundaries


def write_metric_plot(platform_key: str, rows: list[dict], pdf_path: Path, png_path: Path) -> None:
    ordered_rows = order_rows_for_display(rows, platform_key)
    labels = [row["short_label"] for row in ordered_rows]
    values = [row["rmse"] for row in ordered_rows]
    positions = list(range(len(ordered_rows)))
    colors = [_metric_bar_color(row) for row in ordered_rows]

    fig, ax = plt.subplots(figsize=METRIC_FIGSIZE)
    bars = ax.bar(
        positions,
        values,
        color=colors,
        edgecolor=BAR_EDGE_COLOR,
        linewidth=BAR_EDGE_WIDTH,
        width=0.72,
    )


    for boundary_idx in _metric_group_boundaries(ordered_rows):
        ax.axvline(boundary_idx - 0.5, color="#D0D0D0", linewidth=0.6, linestyle=":")

    ymax = max(values)
    ax.set_ylim(0.0, ymax * 1.06)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=TICK_LABEL_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_LABEL_SIZE)
    ax.set_ylabel("RMSE", fontsize=AXIS_LABEL_SIZE)
    ax.set_xlabel("Ablation Variant", fontsize=AXIS_LABEL_SIZE)
    ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#CFCFCF")
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_linewidth(SPINE_WIDTH)

    annotations = []
    for bar, row in zip(bars, ordered_rows):
        annotations.append(
            ax.annotate(
                f"{row['rmse']:.3f}",
                xy=(bar.get_x() + bar.get_width() / 2.0, bar.get_height()),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=METRIC_ANNOTATION_SIZE,
                rotation=90,
            )
        )

    fig.subplots_adjust(left=0.10, right=0.98, top=0.95, bottom=0.36)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    ax_bbox = ax.get_window_extent(renderer)
    top_text_y = max(text.get_window_extent(renderer).y1 for text in annotations)
    top_gap_pt = ax_bbox.y1 - top_text_y
    if top_gap_pt < METRIC_TOP_MARGIN_PT:
        y_min, y_max = ax.get_ylim()
        data_per_px = (y_max - y_min) / max(ax_bbox.height, 1.0)
        ax.set_ylim(y_min, y_max + (METRIC_TOP_MARGIN_PT - top_gap_pt) * data_per_px)

    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(png_path, dpi=DPI, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def write_section_draft(output_path: Path) -> None:
    p1 = platform_output_artifacts("platform1")
    p2 = platform_output_artifacts("platform2")
    text = rf"""\subsection{{Ablation Studies}}

\subsubsection{{Results on platform1}}

\input{{{p1['table_file']}}}

\begin{{figure}}[t]
    \centering
    \includegraphics[width=\columnwidth]{{{p1['figure_pdf']}}}
    \caption{{Relative RMSE changes of ablation variants on platform1 (flexible manipulator). Attention removal and excessive latent lifting cause the most severe degradation, while positional encoding has only a marginal effect.}}
    \label{{{p1['figure_label']}}}
\end{{figure}}

Table~\ref{{{p1['table_label']}}} and Fig.~\ref{{{p1['figure_label']}}} show that platform1 mainly benefits from attention-based temporal interaction modeling. Removing attention produces the largest module-level degradation, increasing the rollout RMSE from 0.19248 to 0.51161 (+165.8\%), while removing patching also causes a substantial degradation of +62.6\%. By contrast, removing positional encoding only changes the RMSE by +3.0\%, which suggests that this platform is comparatively insensitive to absolute temporal order once local temporal aggregation is retained.

The hyperparameter ablations further indicate that the default configuration is already close to a strong operating point on platform1. Reducing the Transformer depth to one or two layers clearly harms performance, whereas increasing the depth to four layers yields only a marginal improvement to \textbf{{0.18968}}$^\dagger$. This small gain suggests that the baseline depth of three layers already captures most of the useful temporal interaction structure. Similarly, moderate changes to patch length and latent dimension only produce limited degradation, but over-expanding the latent dimension to $d=128$ severely worsens the RMSE by +229.5\%, indicating over-parameterized lifting and less stable latent dynamics.

The per-dimension errors are also consistent with this interpretation. For platform1, the error is mainly concentrated in dimensions 1, 3, and 5. Removing attention increases the RMSE of dim1 from 0.2895 to 0.8256 and dim3 from 0.2588 to 0.7427, suggesting that attention is essential for capturing coupled temporal interactions across the multivariate state trajectory.

\subsubsection{{Results on platform2}}

\input{{{p2['table_file']}}}

\begin{{figure}}[t]
    \centering
    \includegraphics[width=\columnwidth]{{{p2['figure_pdf']}}}
    \caption{{Relative RMSE changes of ablation variants on platform2 (soft robot). Unlike platform1, platform2 is highly sensitive to positional encoding and history length, indicating stronger dependence on temporal ordering and longer memory.}}
    \label{{{p2['figure_label']}}}
\end{{figure}}

platform2 exhibits a different ablation pattern. As shown in Table~\ref{{{p2['table_label']}}} and Fig.~\ref{{{p2['figure_label']}}}, removing positional encoding causes the largest module-level degradation, increasing the RMSE from 0.78149 to 1.82345 (+133.3\%). Removing patching also produces a large degradation (+85.1\%), while removing attention causes a smaller but still substantial increase of +48.5\%. These results indicate that platform2 depends more strongly on temporal ordering information than platform1.

The parameter sweep shows that longer temporal memory is beneficial on platform2. Increasing the history length from the default $P=4$ to $P=8$ reduces the RMSE by 37.1\%, and even the shorter setting $P=2$ still improves over the default baseline by 17.4\%. In addition, reducing the Transformer depth to one layer improves the RMSE by 22.2\%, whereas using two layers causes a dramatic failure case with +279.7\% degradation. A similarly strong deterioration appears when the latent dimension is expanded to $d=32$ (+185.4\%), which indicates that this lower-dimensional system is more vulnerable to over-parameterized temporal lifting.

The per-dimension statistics highlight the source of these failures. Removing positional encoding dramatically increases the RMSE of dim1 from 0.3321 to 2.4798, which suggests that temporal ordering is crucial for platform2. The unstable Layers=2 case mainly comes from dim0, whose RMSE increases from 1.0541 to 4.1818, implying that the deeper temporal encoder can become unstable even when the second state component remains relatively well behaved.

\subsubsection{{Cross-Platform Discussion}}

The ablation results reveal platform-dependent temporal modeling requirements rather than inconsistency of the proposed framework. On platform1, the dominant factor is attention-based global temporal interaction, while positional encoding has only a marginal effect. On platform2, by contrast, positional encoding and history length are far more important, indicating stronger reliance on temporal ordering and longer effective memory. These results suggest that PatchTST-Koopman adapts to different temporal structures across dynamical systems: platform1 benefits more from global temporal interaction modeling, whereas platform2 depends more strongly on explicit ordering cues and memory length. Therefore, the optimal temporal configuration should be understood as platform-dependent, even though the full PatchTST-Koopman design provides a consistent and effective temporal lifting framework across both systems.
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
        display_rows = order_rows_for_display(rows, platform_key)
        artifacts = platform_output_artifacts(platform_key)
        write_table(platform_key, display_rows, OUTPUT_DIR / artifacts["table_file"])
        write_plot(
            platform_key,
            display_rows,
            OUTPUT_DIR / artifacts["figure_pdf"],
            OUTPUT_DIR / artifacts["figure_png"],
        )
        write_metric_plot(
            platform_key,
            display_rows,
            OUTPUT_DIR / artifacts["metric_figure_pdf"],
            OUTPUT_DIR / artifacts["metric_figure_png"],
        )

    write_section_draft(OUTPUT_DIR / "ablation_section_draft.tex")

    for legacy_name in LEGACY_OUTPUT_NAMES:
        legacy_path = OUTPUT_DIR / legacy_name
        if legacy_path.exists():
            legacy_path.unlink()

    print("Generated files:")
    for path in sorted(OUTPUT_DIR.iterdir()):
        if path.is_file():
            print(path.name)


if __name__ == "__main__":
    main()





