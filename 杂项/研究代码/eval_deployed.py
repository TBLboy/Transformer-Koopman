import os, sys, json
import numpy as np, torch
REPO = r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码"
sys.path.insert(0, os.path.join(REPO, "src"))
from patchtst_koopman.models.patchtst_encoder import PatchTSTEncoder
from patchtst_koopman.models.linear_decoder import LinearDecoder
from patchtst_koopman.utils.config_loader import load_config
import torch.nn as nn

DEV = "cuda" if torch.cuda.is_available() else "cpu"
CKPT = os.path.join(REPO, "deploy", "algorithms", "tk_assets", "model_assets", "platform2_full_model.pth")
sd = torch.load(CKPT, map_location="cpu", weights_only=False)
dcfg = sd["config"]; norm = sd["normalization"]; ms = sd["model_state_dict"]
P = int(dcfg["encoder"]["history_length"]); d = int(dcfg["encoder"]["latent_dim"]); m = int(dcfg["data"]["control_dim"]); n = int(dcfg["data"]["state_dim"])
data_dir = os.path.abspath(os.path.join(REPO, "..", "数据备份", "软体平台数据", "处理后的数据"))
print("P", P, "d", d, "data_dir", data_dir, "device", DEV)

class Fixed(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = PatchTSTEncoder(dcfg); self.decoder = LinearDecoder(dcfg)
        self.A = nn.Parameter(torch.eye(d)); self.B = nn.Parameter(torch.zeros(d, m))
    def forward(self, xh, uh, ut):
        z = self.encoder(xh)
        z2 = z @ self.A.t() + ut @ self.B.t()
        return self.decoder(z2)

mdl = Fixed().to(DEV)
A = torch.tensor(sd["koopman_A"], dtype=torch.float32); B = torch.tensor(sd["koopman_B"], dtype=torch.float32)
missing, unexpected = mdl.load_state_dict({**{k: v for k, v in ms.items()}}, strict=False)
print("missing:", [k for k in missing if "A" not in k and "B" not in k][:6], "... unexpected:", unexpected[:6])
with torch.no_grad():
    mdl.A.copy_(A); mdl.B.copy_(B)
mdl.eval()

xm, xs = torch.tensor(norm["x_mean"]), torch.tensor(norm["x_std"])
um, us = torch.tensor(norm["u_mean"]), torch.tensor(norm["u_std"])
H_MAX = 20; H_EVAL = [1, 5, 10, 20]
res = {}
for split in ("val", "test"):
    d2 = np.load(os.path.join(data_dir, f"{split}.npz"))
    x = (d2["x"] - norm["x_mean"]) / norm["x_std"]; u = (d2["u"] - norm["u_mean"]) / norm["u_std"]
    tid = d2["trajectory_id"]; errs = {h: [] for h in H_EVAL}
    with torch.no_grad():
        for t in np.unique(tid):
            idx = np.where(tid == t)[0]; xx, uu = x[idx], u[idx]
            for k in range(P - 1, len(xx) - H_MAX - 1, 8):
                xh = torch.tensor(xx[k - P + 1:k + 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                uh = torch.tensor(uu[k - P + 1:k], dtype=torch.float32).unsqueeze(0).to(DEV)
                for h in range(1, H_MAX + 1):
                    ut = torch.tensor(uu[k + h - 1], dtype=torch.float32).unsqueeze(0).to(DEV)
                    xn = mdl(xh, uh, ut)
                    xh = torch.cat([xh[:, 1:, :], xn.unsqueeze(1)], dim=1)
                    uh = torch.cat([uh[:, 1:, :], ut.unsqueeze(1)], dim=1)
                    if h in errs:
                        gt = torch.tensor(xx[k + h], dtype=torch.float32).to(DEV)
                        errs[h].append(torch.linalg.norm(xn.squeeze(0) - gt).item())
    res[split] = {h: round(float(np.sqrt(np.mean(np.square(v)))), 4) for h, v in errs.items()}
print(json.dumps(res, indent=2))
