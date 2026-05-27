"""Produce a Markdown summary of the latest ablation runs for both platforms."""
import argparse
import json
from datetime import datetime
from pathlib import Path


def load_latest_results(results_dir):
    path = Path(results_dir)
    if not path.exists():
        raise FileNotFoundError(f"Results dir does not exist: {path}")

    platform1_files = sorted(path.glob("ablation_platform1_*.json"))
    platform2_files = sorted(path.glob("ablation_platform2_*.json"))
    if not platform1_files or not platform2_files:
        raise FileNotFoundError("Missing ablation_platform{1,2}_*.json in results dir")

    with open(platform1_files[-1], "r", encoding="utf-8") as f:
        p1 = json.load(f)
    with open(platform2_files[-1], "r", encoding="utf-8") as f:
        p2 = json.load(f)

    print(f"Loaded platform 1: {platform1_files[-1].name}")
    print(f"Loaded platform 2: {platform2_files[-1].name}")
    return p1, p2


def render_platform_section(name, results, baseline_key="rmse"):
    section = [f"\n## {name}\n", f"| Variant | RMSE | Degradation |", "|---|---|---|"]
    baseline = results.get("full_model", {}).get(baseline_key)
    for variant_id, result in results.items():
        score = result.get(baseline_key)
        if score is None:
            row = f"| {result['name']} | FAILED | - |"
        elif baseline is not None and variant_id != "full_model":
            delta = (score - baseline) / baseline * 100
            row = f"| {result['name']} | {score:.6f} | +{delta:.1f}% |"
        else:
            row = f"| {result['name']} | {score:.6f} | baseline |"
        section.append(row)
    return "\n".join(section)


def main():
    parser = argparse.ArgumentParser(description="Generate Markdown ablation report")
    parser.add_argument(
        "--results_dir",
        type=str,
        default="./results/ablation",
        help="Directory containing ablation_platform*.json files",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output Markdown path (default: <results_dir>/ablation_report.md)",
    )
    args = parser.parse_args()

    p1, p2 = load_latest_results(args.results_dir)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = [
        "# Ablation Study Report",
        f"\n*Generated: {timestamp}*",
        render_platform_section("Platform 1 — Flexible Manipulator", p1["results"]),
        render_platform_section("Platform 2 — Soft Robot", p2["results"]),
    ]
    markdown = "\n".join(report)

    out_path = args.out or str(Path(args.results_dir) / "ablation_report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"\nReport saved: {out_path}")


if __name__ == "__main__":
    main()
