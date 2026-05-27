"""Render ablation results into a LaTeX table + printable summary.

Usage:
    python scripts/ablation/plot_ablation_results.py \\
        --results_dir results/ablation
"""
import argparse
import json
from pathlib import Path


VARIANT_ORDER = [
    "full_model",
    "no_patch",
    "no_attention",
    "no_positional",
    "patch_L1",
    "patch_L2",
    "patch_L4",
    "patch_L8",
    "patch_L16",
    "history_P2",
    "history_P4",
    "history_P8",
    "history_P16",
    "history_P32",
    "history_P128",
    "readout_max",
    "readout_last",
]


def load_results(results_dir):
    """Load the latest ``ablation_platform{1,2}_*.json`` files in the directory."""
    path = Path(results_dir)
    if not path.exists():
        raise FileNotFoundError(f"Results dir not found: {path}")

    platform1_files = sorted(path.glob("ablation_platform1_*.json"))
    platform2_files = sorted(path.glob("ablation_platform2_*.json"))
    if not platform1_files:
        raise FileNotFoundError("No ablation_platform1_*.json found")
    if not platform2_files:
        raise FileNotFoundError("No ablation_platform2_*.json found")

    with open(platform1_files[-1], "r", encoding="utf-8") as f:
        p1 = json.load(f)
    with open(platform2_files[-1], "r", encoding="utf-8") as f:
        p2 = json.load(f)

    print(f"Loaded platform 1 results: {platform1_files[-1].name}")
    print(f"Loaded platform 2 results: {platform2_files[-1].name}")
    return p1, p2


def generate_latex_table(p1, p2, save_path):
    p1_data = p1["results"]
    p2_data = p2["results"]
    baseline_p1 = p1_data.get("full_model", {}).get("rmse")
    baseline_p2 = p2_data.get("full_model", {}).get("rmse")

    latex = (
        "\\begin{table}[!t]\n"
        "\\renewcommand{\\arraystretch}{1.2}\n"
        "\\caption{Ablation Study Results (test RMSE on first trajectory)}\n"
        "\\label{tab:ablation}\n"
        "\\centering\n"
        "\\begin{tabular}{lcc}\n"
        "\\hline\\hline\n"
        "\\textbf{Variant} & \\textbf{Platform 1 RMSE} & \\textbf{Platform 2 RMSE} \\\\\n"
        "\\hline\n"
    )

    for vid in VARIANT_ORDER:
        if vid not in p1_data:
            continue
        v1 = p1_data[vid].get("rmse")
        v2 = p2_data.get(vid, {}).get("rmse")
        if v1 is None or v2 is None:
            continue
        name = p1_data[vid]["name"]
        if vid == "full_model":
            p1_str = f"\\textbf{{{v1:.6f}}}"
            p2_str = f"\\textbf{{{v2:.6f}}}"
        else:
            d1 = (v1 - baseline_p1) / baseline_p1 * 100 if baseline_p1 else None
            d2 = (v2 - baseline_p2) / baseline_p2 * 100 if baseline_p2 else None
            p1_str = f"{v1:.6f} (+{d1:.1f}\\%)" if d1 is not None else f"{v1:.6f}"
            p2_str = f"{v2:.6f} (+{d2:.1f}\\%)" if d2 is not None else f"{v2:.6f}"
        latex += f"{name:<35s} & {p1_str} & {p2_str} \\\\\n"

    latex += "\\hline\\hline\n\\end{tabular}\n\\end{table}\n"

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(latex)
    print(f"LaTeX table saved: {save_path}")


def print_summary(p1, p2):
    p1_data = p1["results"]
    p2_data = p2["results"]
    baseline_p1 = p1_data.get("full_model", {}).get("rmse")
    baseline_p2 = p2_data.get("full_model", {}).get("rmse")

    print("\n" + "=" * 80)
    print("Ablation summary (RMSE)")
    print("=" * 80)
    print(f"\n{'Variant':<35} | {'Platform 1':<20} | {'Platform 2':<20}")
    print("-" * 80)
    for vid in VARIANT_ORDER:
        if vid not in p1_data:
            continue
        v1 = p1_data[vid].get("rmse")
        v2 = p2_data.get(vid, {}).get("rmse")
        if v1 is None or v2 is None:
            continue
        name = p1_data[vid]["name"]
        if vid == "full_model":
            s1, s2 = f"{v1:.6f} (baseline)", f"{v2:.6f} (baseline)"
        else:
            d1 = (v1 - baseline_p1) / baseline_p1 * 100 if baseline_p1 else None
            d2 = (v2 - baseline_p2) / baseline_p2 * 100 if baseline_p2 else None
            s1 = f"{v1:.6f} (+{d1:.1f}%)" if d1 is not None else f"{v1:.6f}"
            s2 = f"{v2:.6f} (+{d2:.1f}%)" if d2 is not None else f"{v2:.6f}"
        print(f"{name:<35} | {s1:<20} | {s2:<20}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Render ablation results")
    parser.add_argument(
        "--results_dir",
        type=str,
        default="./results/ablation",
        help="Directory containing ablation_platform*.json",
    )
    parser.add_argument(
        "--save_latex",
        type=str,
        default=None,
        help="Path to write the LaTeX table (default: <results_dir>/ablation_table.tex)",
    )
    parser.add_argument("--no_table", action="store_true", help="Skip LaTeX export")
    args = parser.parse_args()

    p1, p2 = load_results(args.results_dir)
    print_summary(p1, p2)

    if not args.no_table:
        save_path = args.save_latex or str(Path(args.results_dir) / "ablation_table.tex")
        generate_latex_table(p1, p2, save_path)


if __name__ == "__main__":
    main()
