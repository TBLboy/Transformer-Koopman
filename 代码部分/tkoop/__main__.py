"""命令行入口。在 代码部分/ 下运行：uv run python -m tkoop <命令> ...

    train   训练一个变体（--variant all 表示全部九个）
    eval    评测一次训练的结果；测试集只评测一次
    tune    在验证集上做超参数选型
    freeze  把当前配置冻结到 configs/final/
    report  汇总测试结果，生成对比表和消融表
"""
from __future__ import annotations

import argparse

from .config import CONFIG_DIR, RUNS_DIR, VARIANTS, freeze, load_final, parse_overrides, resolve


def _variants(name: str) -> list[str]:
    return VARIANTS if name == "all" else [name]


def _config(args, variant: str) -> tuple[dict, str]:
    if args.final:
        if args.set:
            raise SystemExit("--final 只读 configs/final/ 的冻结配置，不能再用 --set 覆盖")
        return load_final(variant), "final"
    return resolve(variant, parse_overrides(args.set)), args.tag


def _seeds(args, cfg: dict) -> list[int]:
    return cfg["seeds"] if args.seed is None else [args.seed]


def cmd_train(args) -> None:
    from .data import load_train_data
    from .train import is_deterministic, train_variant
    for variant in _variants(args.variant):
        cfg, tag = _config(args, variant)
        seeds = _seeds(args, cfg)
        if args.seed is None and is_deterministic(cfg, load_train_data(cfg).n):
            seeds = seeds[:1]
        for seed in seeds:
            out = train_variant(cfg, seed, tag)
            print(f"[train] {variant} seed {seed} -> {out}")


def cmd_eval(args) -> None:
    from .evaluate import evaluate_run
    from .train import run_dir
    for variant in _variants(args.variant):
        cfg, tag = _config(args, variant)
        for seed in _seeds(args, cfg):
            out = run_dir(RUNS_DIR, tag, variant, seed)
            if not (out / "done.json").is_file():
                print(f"[eval] 跳过 {variant} seed {seed}：没有已完成的训练 {out}")
                continue
            res = evaluate_run(out, args.split, per_horizon=args.per_horizon, select=args.select, force=args.force)
            line = "  ".join(f"H{h}={m['rmse_cm']:.4f}" for h, m in res["horizons"].items())
            print(f"[eval] {variant} seed {seed} {args.split} ({res['selection']}) cm: {line}")


def cmd_tune(args) -> None:
    from .train import tune
    path = tune(args.variant, seed=args.seed, max_trials=args.max_trials,
                keys=args.keys.split(",") if args.keys else None, overrides=parse_overrides(args.set))
    print(f"[tune] {args.variant} -> {path}")


def cmd_freeze(args) -> None:
    for path in freeze(CONFIG_DIR):
        print(f"[freeze] {path}")


def cmd_report(args) -> None:
    from .report import report
    for stem in report(args.tag, args.split):
        print(f"[report] {stem}.csv  {stem}.tex")


def _horizon(text: str):
    return text if text == "full" else int(text)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="python -m tkoop", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p, tag_default="dev"):
        p.add_argument("--variant", required=True, choices=[*VARIANTS, "all"])
        p.add_argument("--seed", type=int, default=None, help="不给时用 base.yaml 里的全部种子")
        p.add_argument("--tag", default=tag_default, help="运行目录的命名空间：runs/<tag>/<variant>/seed<k>")
        p.add_argument("--final", action="store_true", help="读 configs/final/ 的冻结配置，写入 runs/final/")
        p.add_argument("--set", action="append", metavar="KEY=VALUE", help="覆盖配置项，可重复，例如 stage2.lr=1e-3")

    p = sub.add_parser("train", help="训练")
    common(p)
    p.set_defaults(func=cmd_train)

    p = sub.add_parser("eval", help="评测")
    common(p)
    p.add_argument("--split", required=True, choices=["val", "test"])
    p.add_argument("--select", type=_horizon, default=None, help="所有视野都用该视野上验证最优的参数（默认取配置）")
    p.add_argument("--per-horizon", action="store_true", help="每个视野用它自己验证最优的参数")
    p.add_argument("--force", action="store_true", help="允许重写已有的测试结果，旧文件改名保留")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("tune", help="选型")
    p.add_argument("--variant", required=True, choices=VARIANTS)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max-trials", type=int, default=12)
    p.add_argument("--keys", default=None, help="只搜索以这些前缀开头的键，逗号分隔，例如 stage2,dynamics")
    p.add_argument("--set", action="append", metavar="KEY=VALUE")
    p.set_defaults(func=cmd_tune)

    p = sub.add_parser("freeze", help="冻结配置")
    p.set_defaults(func=cmd_freeze)

    p = sub.add_parser("report", help="汇总")
    p.add_argument("--tag", default="final")
    p.add_argument("--split", default="test", choices=["val", "test"])
    p.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
