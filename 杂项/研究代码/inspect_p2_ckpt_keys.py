import torch, json
from pathlib import Path

p = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\deploy\algorithms\tk_assets\model_assets\platform2_full_model.pth")
o = torch.load(p, map_location="cpu", weights_only=False)
msd = o["model_state_dict"]
print("model_state_dict type:", type(msd).__name__, "n=", len(msd))
for k, v in msd.items():
    print(k, tuple(v.shape) if hasattr(v, "shape") else type(v).__name__)
print("---config---")
print(json.dumps(o["config"], indent=2, ensure_ascii=False)[:2000])
print("---model_info---")
print(json.dumps(o.get("model_info", {}), indent=2, ensure_ascii=False)[:1500])
