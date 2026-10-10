"""Gate-13B: rank sweep r in {1,2,3,5} for A-only, seed 0, same budget."""
import sys, os, json
import numpy as np, torch
sys.path.insert(0, r"C:\Users\12187\AppData\Local\Temp\opencode")
from gate_context_koopman import build_split, train_model, eval_rollout, H_EVAL, REPO
from patchtst_koopman.utils.config_loader import load_config

STATE = r"C:\Users\12187\AppData\Local\Temp\opencode\gate_states"
OUT = r"C:\Users\12187\AppData\Local\Temp\opencode\gate13b_result.json"
cfg = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
data_dir = os.path.abspath(os.path.join(REPO, cfg["data"]["data_dir"]))
trXH, trUH, trUT, trXN, norm = build_split(data_dir, "train", cfg)
print("train", trXH.shape)
fixed, fixed_val = train_model("fixed", cfg, (trXH, trUH, trUT, trXN), epochs=100, seed=0)
init = {k: v.clone() for k, v in fixed.state_dict().items()}
res = {}
for r in (1, 2, 3, 5):
    m, v = train_model("A", cfg, (trXH, trUH, trUT, trXN), epochs=100, lr=5e-4, init_state=init, seed=0, r=r)
    torch.save({k: t.clone() for k, t in m.state_dict().items()}, os.path.join(STATE, f"A_r{r}.pt"))
    rv = eval_rollout(m, cfg, data_dir, "val", norm)
    rt = eval_rollout(m, cfg, data_dir, "test", norm)
    S = 0.5 * rv[10] + 0.5 * rv[20]
    res[r] = {"val_rollout": rv, "test_rollout": rt, "S_r": S, "params": sum(p.numel() for p in m.parameters())}
    print(f"r={r} val={ {k: round(x,4) for k,x in rv.items()} } S_r={S:.5f}")
best = min(res, key=lambda r: res[r]["S_r"])
thresh = res[best]["S_r"] * 1.03
chosen = min([r for r in res if res[r]["S_r"] <= thresh])
print("best r:", best, "chosen (<=3% of best):", chosen)
res["_summary"] = {"best_r": best, "chosen_r": chosen, "threshold_3pct": thresh,
                   "S_r": {str(r): res[r]["S_r"] for r in (1, 2, 3, 5)}}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2, default=str)
print("saved", OUT)
