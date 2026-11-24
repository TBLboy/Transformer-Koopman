"""配置解析：base.yaml + 提升配置 + 变体配置，合成一份完整配置。

d、P_h、H_R、评测视野、种子只在 base.yaml 定义；提升配置和变体配置里出现这些键时报错。
"""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "configs"
RUNS_DIR = ROOT / "runs"
RESULTS_DIR = ROOT / "results"

BASE_ONLY = ("data", "shared", "eval", "seeds")
COMPARISON = ["edmdc", "delay_edmdc", "deep_koopman", "lstm_koopman", "full"]
ABLATION = ["full", "abl_no_sched", "abl_no_hist_lift", "abl_no_input_ctx", "abl_ctx_once"]
VARIANTS = COMPARISON + [v for v in ABLATION if v not in COMPARISON]
CLOSED_FORM_LIFTS = ("rbf", "delay_pca")
LEARNED_LIFTS = ("mlp", "lstm", "transformer")


def _load(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"配置文件不存在：{path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _merge(a: dict, b: dict) -> dict:
    out = copy.deepcopy(a)
    for key, value in b.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _forbid_base_keys(cfg: dict, path: Path) -> None:
    bad = [k for k in BASE_ONLY if k in cfg]
    if bad:
        raise ValueError(f"{path} 不允许定义 {bad}：这些键只能出现在 base.yaml")


def _set(cfg: dict, dotted: str, value) -> None:
    node = cfg
    *parents, leaf = dotted.split(".")
    for p in parents:
        if not isinstance(node.get(p), dict):
            raise KeyError(f"覆盖项 {dotted!r} 的路径不存在")
        node = node[p]
    if leaf not in node:
        raise KeyError(f"覆盖项 {dotted!r} 不是已有的配置键")
    node[leaf] = value


def parse_overrides(items: list[str] | None) -> dict:
    """把命令行的 key=value 列表解析成字典；1e-3 这类写法按浮点数处理。"""
    out = {}
    for item in items or []:
        key, sep, text = item.partition("=")
        if not sep:
            raise ValueError(f"覆盖项应写成 key=value：{item!r}")
        value = yaml.safe_load(text)
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                pass
        out[key.strip()] = value
    return out


def _lifting_cfg(name: str, config_dir: Path) -> dict:
    path = config_dir / "lifting" / f"{name}.yaml"
    cfg = _load(path)
    _forbid_base_keys(cfg, path)
    return cfg


def _variant_raw(name: str, config_dir: Path) -> dict:
    path = config_dir / "variants" / f"{name}.yaml"
    raw = _load(path)
    _forbid_base_keys(raw, path)
    raw.pop("search", None)
    parent = raw.pop("inherit", None)
    if parent:
        raw = _merge(_variant_raw(parent, config_dir), raw)
    return raw


def resolve(variant: str, overrides: dict | None = None, config_dir: Path = CONFIG_DIR) -> dict:
    """返回变体的完整配置。overrides 的键是点分路径，例如 {"stage2.lr": 1e-3}。"""
    config_dir = Path(config_dir)
    base = _load(config_dir / "base.yaml")
    raw = _variant_raw(variant, config_dir)
    cfg = {k: copy.deepcopy(base[k]) for k in BASE_ONLY}
    cfg["device"] = base.get("device", "cpu")
    cfg["variant"] = variant
    defaults = base.get("train", {})

    lift = raw["lifting"]
    if isinstance(lift, str):
        lcfg = _lifting_cfg(lift, config_dir)
        cfg["lifting"] = copy.deepcopy(lcfg["lifting"])
        cfg["stage1"] = _merge(defaults, lcfg["stage1"])
        cfg["stage2"] = _merge(defaults, raw["stage2"])
    else:
        cfg["lifting"] = copy.deepcopy(lift)
        cfg["closed_form"] = copy.deepcopy(raw["closed_form"])

    dyn = copy.deepcopy(raw["dynamics"])
    if isinstance(dyn.get("encoder"), str):
        enc = _lifting_cfg(dyn["encoder"], config_dir)["lifting"]
        if enc["kind"] != "transformer":
            raise ValueError("dynamics.encoder 只能引用 transformer 提升配置")
        dyn["encoder"] = {k: v for k, v in enc.items() if k != "kind"}
    cfg["dynamics"] = dyn

    for key, value in (overrides or {}).items():
        _set(cfg, key, value)
    validate(cfg)
    return cfg


def validate(cfg: dict) -> None:
    sh = cfg["shared"]
    d, P_h, H_R = sh["d"], sh["P_h"], sh["H_R"]
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (d, P_h, H_R)):
        raise ValueError("shared.d、shared.P_h、shared.H_R 必须是整数")
    if d < 1 or P_h < 2 or H_R < 1:
        raise ValueError("要求 d >= 1、P_h >= 2 且 H_R >= 1")
    ev = cfg["eval"]
    horizons = ev["horizons"]
    if not horizons or len(set(horizons)) != len(horizons):
        raise ValueError("eval.horizons 必须是非空且不重复的视野列表")
    if any(h != "full" and (not isinstance(h, int) or isinstance(h, bool) or h < 1) for h in horizons):
        raise ValueError("eval.horizons 中的整数视野必须为正，或使用 full")
    if ev["select_horizon"] not in horizons:
        raise ValueError("eval.select_horizon 必须是 eval.horizons 中的一项")

    kind = cfg["lifting"]["kind"]
    closed = "closed_form" in cfg
    if closed and kind not in CLOSED_FORM_LIFTS:
        raise ValueError(f"闭式解变体的提升只能是 {CLOSED_FORM_LIFTS}")
    if not closed and kind not in LEARNED_LIFTS:
        raise ValueError(f"学习型变体的提升只能是 {LEARNED_LIFTS}")

    patches = [cfg["lifting"]] if kind == "transformer" else []
    dyn = cfg["dynamics"]
    if dyn["kind"] not in ("fixed", "scheduled"):
        raise ValueError("dynamics.kind 只能是 fixed 或 scheduled")
    if dyn["kind"] == "scheduled":
        if closed:
            raise ValueError("闭式解变体不能使用调度矩阵")
        if dyn.get("encoder"):
            patches.append(dyn["encoder"])
        elif kind != "transformer":
            raise ValueError("调度上下文需要历史编码器：提升不是 transformer 时必须设置 dynamics.encoder")
        if not isinstance(dyn["r_A"], int) or isinstance(dyn["r_A"], bool) or not 1 <= dyn["r_A"] <= d:
            raise ValueError("要求 1 <= r_A <= d")
        if not isinstance(dyn["r_B"], int) or isinstance(dyn["r_B"], bool) or not 1 <= dyn["r_B"] <= d:
            raise ValueError("要求 1 <= r_B <= d；r_B 还必须不超过输入维数 m")
        if dyn["g_A"] < 0 or dyn["g_B"] < 0:
            raise ValueError("增益 g_A、g_B 必须非负")
        if dyn["ctx_update"] not in ("every_step", "once"):
            raise ValueError("dynamics.ctx_update 只能是 every_step 或 once")
    for p in patches:
        if P_h % p["patch"] != 0:
            raise ValueError(f"patch 长度 {p['patch']} 必须整除 P_h = {P_h}")

    if not closed:
        scope = cfg["stage2"]["trainable"]
        if scope not in ("all", "scheduling"):
            raise ValueError("stage2.trainable 只能是 all 或 scheduling")
        if scope == "scheduling" and dyn["kind"] != "scheduled":
            raise ValueError("stage2.trainable = scheduling 要求调度矩阵")


def digest(obj) -> str:
    text = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def stage1_config(cfg: dict) -> dict:
    """阶段一实际依赖的配置：数据、共用维数、评测视野、设备、提升结构和阶段一训练设置。

    不含调度、阶段二和选模视野，所以与共用它的各变体无关。
    """
    return {
        "variant": "_stage1",
        "data": cfg["data"],
        "shared": cfg["shared"],
        "eval": {"horizons": cfg["eval"]["horizons"]},
        "device": cfg["device"],
        "lifting": cfg["lifting"],
        "stage1": cfg["stage1"],
        "dynamics": {"kind": "fixed"},
    }


def stage1_key(cfg: dict) -> str:
    """阶段一的身份。键相同的变体共用同一份阶段一结果。"""
    return f"{cfg['lifting']['kind']}-{digest(stage1_config(cfg))}"


def search_space(variant: str, config_dir: Path = CONFIG_DIR) -> dict:
    """变体的超参数候选：提升配置的 search 加变体自己的 search（不继承父变体的）。"""
    config_dir = Path(config_dir)
    own = _load(config_dir / "variants" / f"{variant}.yaml")
    space = {}
    lift = _variant_raw(variant, config_dir)["lifting"]
    if isinstance(lift, str):
        space.update(_lifting_cfg(lift, config_dir).get("search", {}))
    space.update(own.get("search", {}))
    return space


def grid(space: dict) -> list[dict]:
    keys = list(space)
    return [dict(zip(keys, combo)) for combo in itertools.product(*(space[k] for k in keys))]


def check_consistency(cfgs: dict[str, dict]) -> None:
    """R3 与 R8：所有变体共用 data/shared/eval；同一种提升的学习型变体共用同一份阶段一。"""
    names = list(cfgs)
    for key in BASE_ONLY:
        ref = cfgs[names[0]][key]
        for name in names[1:]:
            if cfgs[name][key] != ref:
                raise ValueError(f"{name} 与 {names[0]} 的 {key} 配置不一致")
    keys: dict[str, tuple[str, str]] = {}
    for name, cfg in cfgs.items():
        if "stage1" not in cfg:
            continue
        kind, key = cfg["lifting"]["kind"], stage1_key(cfg)
        if kind in keys and keys[kind][1] != key:
            raise ValueError(f"{name} 与 {keys[kind][0]} 的阶段一配置不一致，无法共用阶段一参数")
        keys.setdefault(kind, (name, key))


def freeze(config_dir: Path = CONFIG_DIR) -> list[Path]:
    """把全部变体当前的完整配置写入 configs/final/；最终训练只读这里。"""
    config_dir = Path(config_dir)
    cfgs = {v: resolve(v, config_dir=config_dir) for v in VARIANTS}
    check_consistency(cfgs)
    out_dir = config_dir / "final"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, cfg in cfgs.items():
        path = out_dir / f"{name}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
        paths.append(path)
    return paths


def load_final(variant: str, config_dir: Path = CONFIG_DIR) -> dict:
    final_dir = Path(config_dir) / "final"
    cfg = _load(final_dir / f"{variant}.yaml")
    validate(cfg)
    others = {p.stem: _load(p) for p in sorted(final_dir.glob("*.yaml"))}
    for other in others.values():
        validate(other)
    check_consistency(others)
    return cfg
