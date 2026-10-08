# -*- coding: utf-8 -*-
"""Fix the subsection order in Related Work: the Transformer-Koopman paragraph
belongs to 'Transition Adaptation', not to 'Recursive Multi-Step Deployment'."""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")

MULTI = ("Multi-step training is also used in learned Koopman models to mitigate error accumulation under "
         "recursive prediction \\cite{lusch2018deep, otto2019linearly, azencot2020forecasting, wu2026multistep}, "
         "and is standard in neural system identification more broadly \\cite{forgione2021dynonet}; we therefore "
         "do not claim multi-step loss itself as novel. The issue is specific to history-conditioned dynamics: "
         "during recursive deployment the transition is repeatedly rescheduled from the predicted history, so the "
         "propagated latent state and conditioning context can depart from the encoder-consistent one-step "
         "distribution. Our rollout-aware procedure reproduces that scheduled propagation during training rather "
         "than merely extending a one-step objective over several horizons.")

TRANSK = ("Recent work has explored Transformer encoders with Koopman-style latent dynamics for forecasting "
          "\\cite{forootani2025deepkoopformer, forootani2026spectral}. In particular, \\cite{forootani2026spectral} "
          "parameterizes the transition as a single low-rank operator with a spectrally constrained diagonal factor "
          "on a patch-based Transformer backbone; unlike our full-rank nominal transition modulated by history, it "
          "uses a static low-rank transition for forecasting. In contrast, our Transformer is used only for history "
          "encoding, while prediction inside the controller is performed by the structured Koopman model. Relatedly, "
          "low-rank space-varying transitions have been learned for continuum-robot control, conditioned on the "
          "instantaneous state and paired with an infinite-horizon linear-quadratic controller \\cite{feizi2025deepkoopman}.")

OLD = "\\subsection{Recursive Multi-Step Deployment}\n\n" + MULTI + "\n\n" + TRANSK
NEW = TRANSK + "\n\n\\subsection{Recursive Multi-Step Deployment}\n\n" + MULTI


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    assert text.count(OLD) == 1, "block not found (count=%d)" % text.count(OLD)
    text = text.replace(OLD, NEW)
    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.split("\n")))
    print("OK: subsection order fixed")


if __name__ == "__main__":
    main()
