# -*- coding: utf-8 -*-
"""Main(9) P0-3 completion: unify ambiguous "encoder" occurrences in the body.

The review asks for paper-wide disambiguation between the Transformer lifting
encoder E_theta and the context map C_phi.  The front matter was fixed by
apply_main9_p0.py; these are the remaining ambiguous occurrences inside
Sections IV-VI and Algorithm 1.
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")

REPLACE = [
    # RTI-SP description (Section VI)
    (r"structure (RTI-SP) never re-runs the full Transformer encoder inside the horizon.",
     r"structure (RTI-SP) never re-runs the full Transformer lifting encoder inside the horizon."),
    # runtime comparison (Section VI)
    (r"Second, RTI-SP is roughly $1.6\times$ faster than RTI-RE because it avoids a full encoder evaluation per stage,",
     r"Second, RTI-SP is roughly $1.6\times$ faster than RTI-RE because it avoids a full Transformer lifting-encoder evaluation per stage,"),
    # trainable-parts sentence (Section IV)
    (r"The model of Definition~\ref{def:hcltk} has three trainable parts: the encoder parameters $\theta$ that produce the lifted state $\vz_k$,",
     r"The model of Definition~\ref{def:hcltk} has three trainable parts: the lifting-encoder parameters $\theta$ that produce the lifted state $\vz_k$,"),
    # Algorithm 1 output line
    (r"\STATE \textbf{Output:} Encoder $\theta^{*}$; context $\phi^{*}$;",
     r"\STATE \textbf{Output:} Lifting encoder $\theta^{*}$; context $\phi^{*}$;"),
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
