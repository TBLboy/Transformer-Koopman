# -*- coding: utf-8 -*-
"""P2-12: rename the low-rank modulation network g(c) to gamma_psi(c).

Motivation (review P2-12): g_theta(X_k) is the lifting map and g(c) is the
transition-modulation coefficient network; the two g's are visually confusable.
Pure symbol rename -- no mathematical content changes.  The generic EDMD lifting
map g(x_k) in Section III-A and the bibliography initials are left untouched.
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")

REPLACE = [
    # Definition 1 -- transition and function signature
    (r"\mA(\vc) = \mA_0 + \mU\,\mathrm{diag}\big(g(\vc)\big)\,\mV^\top,",
     r"\mA(\vc) = \mA_0 + \mU\,\mathrm{diag}\big(\gamma_\psi(\vc)\big)\,\mV^\top,"),
    (r"$g:\mathbb{R}^{d_c}\to\mathbb{R}^r$", r"$\gamma_\psi:\mathbb{R}^{d_c}\to\mathbb{R}^r$"),

    # Section IV-B trainable parts
    (r"the dynamics parameters $\mA_0$, $\mU$, $\mV$, and $g$.",
     r"the dynamics parameters $\mA_0$, $\mU$, $\mV$, and $\gamma_\psi$."),

    # Stage 1 description
    (r"$\mA(\vc_k)=\mA_0+\mU\,\mathrm{diag}(g(\vc_k))\,\mV^\top$ and train $\theta$, $\phi$, $\mA_0$, $\mU$, $\mV$, and $g$ jointly",
     r"$\mA(\vc_k)=\mA_0+\mU\,\mathrm{diag}(\gamma_\psi(\vc_k))\,\mV^\top$ and train $\theta$, $\phi$, $\mA_0$, $\mU$, $\mV$, and $\gamma_\psi$ jointly"),

    # bounded-budget sentence
    (r"and $g$ is bounded elementwise", r"and $\gamma_\psi$ is bounded elementwise"),

    # Algorithm 1
    (r"transition parameters $\mA_0^{*},\mU^{*},\mV^{*},g^{*}$",
     r"transition parameters $\mA_0^{*},\mU^{*},\mV^{*},\gamma_\psi^{*}$"),
    (r"Activate $\mA(\vc)=\mA_0+\mU\,\mathrm{diag}(g(\vc))\,\mV^\top$;",
     r"Activate $\mA(\vc)=\mA_0+\mU\,\mathrm{diag}(\gamma_\psi(\vc))\,\mV^\top$;"),
    (r"Update $(\theta,\phi,\mA_0,\mU,\mV,g)$ via gradient descent.",
     r"Update $(\theta,\phi,\mA_0,\mU,\mV,\gamma_\psi)$ via gradient descent."),
    (r"\RETURN $\theta^{*},\phi^{*},\mA_0^{*},\mU^{*},\mV^{*},g^{*}$",
     r"\RETURN $\theta^{*},\phi^{*},\mA_0^{*},\mU^{*},\mV^{*},\gamma_\psi^{*}$"),

    # Lipschitz regularity sentence in Section V
    (r"the modulation $g$", r"the modulation $\gamma_\psi$"),

    # Definition display in Section V and the Conclusion (2 occurrences)
    (r"$\mA(\vc)=\mA_0+\mU\,\mathrm{diag}(g(\vc))\mV^\top$",
     r"$\mA(\vc)=\mA_0+\mU\,\mathrm{diag}(\gamma_\psi(\vc))\mV^\top$", 2),
]


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    assert "\ufeff" not in text, "unexpected BOM"
    nl = "\r\n" if "\r\n" in text else "\n"

    total = 0
    for item in REPLACE:
        old, new = item[0], item[1]
        expect = item[2] if len(item) > 2 else 1
        n = text.count(old)
        assert n == expect, "expected %d, got %d for: %s" % (expect, n, old[:70])
        text = text.replace(old, new)
        total += n
    print("renamed %d occurrences" % total)

    assert r"\mathrm{diag}(g(" not in text
    assert r"\mathrm{diag}\big(g(" not in text
    assert r"and $g$" not in text

    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.replace("\r\n", "\n").split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
