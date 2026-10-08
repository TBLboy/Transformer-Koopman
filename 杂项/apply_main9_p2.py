# -*- coding: utf-8 -*-
"""Restore the core motivation clause in the Abstract so that the compressed
abstract lands inside the Main(9) recommended 190-210 word band (it had dropped
to 183 words, below the band).  The clause states the behavioural consequence of
using instantaneous-state observables with a fixed transition, which is the
paper's hook and was the only substantive content removed by the compression.
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")

REPLACE = [
    (r"Many conventional EDMD and learned-lifting approaches use instantaneous-state observables with a fixed lifted transition, neglecting short-term temporal correlations and the dependence of the evolution on recent history.",
     r"Many conventional EDMD and learned-lifting approaches use instantaneous-state observables with a fixed lifted transition, so they neglect short-term temporal correlations and cannot distinguish how the system evolves from different past trajectories."),
]


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    assert "\ufeff" not in text, "unexpected BOM"
    nl = "\r\n" if "\r\n" in text else "\n"

    for old, new in REPLACE:
        n = text.count(old)
        assert n == 1, "expected 1 occurrence, got %d for: %s" % (n, old[:80])
        text = text.replace(old, new)
    print("applied %d replacements" % len(REPLACE))

    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.replace("\r\n", "\n").split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
