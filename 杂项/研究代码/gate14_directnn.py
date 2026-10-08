"""Gate-14: direct Transformer/NN predictor baseline  x_{k+1} = NN(H_k, u_k).

Fair comparison: same PatchTSTEncoder backbone + MLP head on [z; u], similar params.
Evaluated with the same autoregressive re-encoding rollout as A-only.
"""
import sys, os, json
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F

sys.path.insert(0, r"C:\Users\12187\AppData\Local\Temp\opencode")
from gate_context_koopman import CtxKoopman, build_split, eval_rollout, H_EVAL, REPO
from patchtst_koopman.models.patchtst_encoder import PatchTSTEncoder
from patchtst_koopman.utils.config_loader import load_config

DEV = "cuda" if torch.cuda.is_available() else "cpu"
STATE = r"C:\Users\12187\AppData\Local\Temp\opencode\gate_states"
OUT = r"C:\Users\12187\AppData\Local\Temp\opencode\gate14_directnn_result.json"
CFG = load_config(os.path.join(REPO, "configs", "platform2.yaml"))
DATA_DIR = os.path.abspath(os.path.join(REPO, CFG["data"]["data_dir"]))


class DirectNN(nn.Module):
    def __init__(self, cfg, hidden=48):
        super().__init__()
        self.encoder = PatchTSTEncoder(cfg)
        d = cfg["encoder"]["latent_dim"]; m = cfg["data"]["control_dim"]; n = cfg["data"]["state_dim"]
        self.head = nn.Sequential(nn.Linear(d + m, hidden), nn.Tanh(),
                                  nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, n))

    def forward(self, xh, uh, ut):
        z = self.encoder(xh)
        return self.head(torch.cat([z, ut], dim=1))


def train(trXH, trUH, trUT, trXN, epochs=100, lr=1e-3, bs=256, seed=0):
    torch.manual_seed(seed)
    model = DirectNN(CFG).to(DEV)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    n = len(trXH); best = (1e9, None)
    for ep in range(epochs):
        model.train(); perm = torch.randperm(n)
        for s in range(0, n, bs):
            b = perm[s:s + bs]; opt.zero_grad()
            loss = F.mse_loss(model(trXH[b].to(DEV), trUH[b].to(DEV), trUT[b].to(DEV)), trXN[b].to(DEV))
            loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            vl = F.mse_loss(model(trXH.to(DEV), trUH.to(DEV), trUT.to(DEV)), trXN.to(DEV)).item()
        if vl < best[0]:
            best = (vl, {k: v.clone() for k, v in model.state_dict().items()})
    model.load_state_dict(best[1]); return model, best[0]


if __name__ == "__main__":
    trXH, trUH, trUT, trXN, NORM = build_split(DATA_DIR, "train", CFG)
    m, v = train(trXH, trUH, trUT, trXN, epochs=100)
    rv = eval_rollout(m, CFG, DATA_DIR, "val", NORM)
    rt = eval_rollout(m, CFG, DATA_DIR, "test", NORM)
    params = sum(p.numel() for p in m.parameters())
    print("DirectNN val:", {k: round(x, 4) for k, x in rv.items()}, "params:", params)
    print("DirectNN test:", {k: round(x, 4) for k, x in rt.items()})
    # references
    base = CtxKoopman(CFG, "A", r=2).to(DEV)
    base.load_state_dict(torch.load(os.path.join(STATE, "A_r2.pt"), map_location=DEV)); base.eval()
    out = {"direct_nn": {"val": rv, "test": rt, "params": params},
           "A_only_r2": {"val": eval_rollout(base, CFG, DATA_DIR, "val", NORM),
                         "test": eval_rollout(base, CFG, DATA_DIR, "test", NORM),
                         "params": sum(p.numel() for p in base.parameters())}}
    print("A_only_r2 params:", out["A_only_r2"]["params"])
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved", OUT)
