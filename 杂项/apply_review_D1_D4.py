"""Apply reviewer wording items D1-D4 to Main.tex (section VII-A).

Exact-match replacements only; every edit must match exactly once or the
script aborts without writing.  Byte-preserving (keeps a BOM if one exists).
"""
import hashlib
import pathlib
import sys

P = pathlib.Path(
    "D:/Project/Transformer-Koopman/Transformer-Koopman/"
    "\u8bba\u6587/\u65b0\u7248\u672c/Main.tex"
)

EDITS = [
    # D2a: "differ only in" is too strong, and the shared budget is Stage-1 only.
    (
        "and epoch budget, and differ only in which parameters the scheduled-rollout "
        "stage optimizes. Strategy~A optimizes only the low-rank modulation",
        "and scheduled-rollout-stage epoch budget. They differ in which parameters the "
        "scheduled-rollout stage optimizes: strategy~A optimizes only the low-rank modulation",
        "D2a",
    ),
    # D2b: make strategy D's extra difference explicit at the point of enumeration.
    (
        "strategy~C optimizes all parameters; strategy~D omits the nominal one-step "
        "pretraining stage",
        "strategy~C optimizes all parameters; strategy~D additionally omits the nominal "
        "one-step pretraining stage",
        "D2b",
    ),
    # D3: all four variants use the scheduled-rollout objective, so A-vs-C isolates
    # which parameters it is allowed to adapt, not the objective itself.
    (
        "First, the scheduled-rollout objective is the essential ingredient: "
        "optimizing only the low-rank modulation",
        "First, what matters is which parameters the scheduled-rollout objective is "
        "allowed to adapt: optimizing only the low-rank modulation",
        "D3",
    ),
    # D1: name the two metric definitions explicitly (endpoint RMSE vs whole-rollout MSE).
    (
        "with a $5.9\\%$ higher rollout RMSE and a $24\\%$ higher rollout MSE at $H=20$.",
        "with a $5.9\\%$ higher $H=20$ rollout RMSE and a $24\\%$ higher rollout MSE "
        "accumulated over the whole $20$-step rollout.",
        "D1",
    ),
    # D4: avoid reading "A variant ..." as variant A; tag both single-seed values.
    (
        "A variant trained on the one-step objective with an explicit spectral constraint "
        "$\\rho(\\mA(\\vc))\\le0.99$ attains an $H=20$ rollout RMSE of $1.5681$ (single seed), "
        "whereas the same constrained model trained under the scheduled-rollout objective "
        "attains $0.0412$.",
        "Training with an explicit spectral constraint $\\rho(\\mA(\\vc))\\le0.99$ under the "
        "one-step objective attains an $H=20$ rollout RMSE of $1.5681$, whereas the same "
        "constrained model trained under the scheduled-rollout objective attains $0.0412$ "
        "(both single-seed comparisons).",
        "D4",
    ),
]

raw = P.read_bytes()
print(
    "before: sha256=%s size=%d bom=%s"
    % (hashlib.sha256(raw).hexdigest()[:12].upper(), len(raw), raw[:3] == b"\xef\xbb\xbf")
)

text = raw.decode("utf-8")
ok = True
for old, new, tag in EDITS:
    n = text.count(old)
    print("%s occurrences=%d" % (tag, n))
    if n != 1:
        ok = False
    else:
        text = text.replace(old, new)

if not ok:
    print("ABORT: an edit did not match exactly once; nothing written")
    sys.exit(1)

out = text.encode("utf-8")  # preserves a leading BOM if the source had one
P.write_bytes(out)
print("after:  sha256=%s size=%d" % (hashlib.sha256(out).hexdigest()[:12].upper(), len(out)))
