import torch, sys
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
p = r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\deploy\algorithms\tk_assets\model_assets\platform2_full_model.pth"
c = torch.load(p, map_location="cpu", weights_only=False)
cfg = c.get("config", {}) if isinstance(c, dict) else {}
print("top-level keys:", list(c.keys()) if isinstance(c, dict) else type(c))
print("config:", cfg)
print("model_info:", c.get("model_info"))
print("spectral_radius:", c.get("spectral_radius"))
for k, v in (c.items() if isinstance(c, dict) else []):
    if hasattr(v, "shape"):
        print("  tensor", k, tuple(v.shape))
