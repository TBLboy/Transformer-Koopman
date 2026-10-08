# -*- coding: utf-8 -*-
"""Apply the user-ruled remaining Main(9) items to Main.tex.

P1-8  delete the Informer/Linformer/Performer/Autoformer/Fedformer citation cluster
      AND the five now-orphaned bibliography entries (55 -> 50 bibitems).
P1-9  compress the RTI / quasi-LPV tutorial background in Related Work.
P2-10 compress the Abstract by ~7-10% and align its closing sentence with the
      Section VIII statement that hardware validation remains future work.
Every replacement is asserted to occur exactly once.
"""
import re
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")

DELETE_KEYS = [
    "zhou2021informer",
    "wang2020linformer",
    "choromanski2021performer",
    "wu2021autoformer",
    "zhou2022fedformer",
]

REPLACE = [
    # --- P2-10 + closing-sentence alignment: Abstract -----------------------------
    (r"Koopman modeling represents nonlinear dynamics as linear evolution in a lifted space, but its accuracy depends critically on the lifting map and on how the linear operator is identified. Many conventional EDMD and learned-lifting approaches use instantaneous-state observables together with a fixed lifted transition, so they neglect short-term temporal correlations and cannot distinguish how the system evolves from different past trajectories. We propose Transformer-Koopman, a temporal lifting framework in which a patch-based Transformer encoder maps a finite history window to a structured lifted state, and the lifted transition is history-conditioned by a low-rank modulation of a full-rank nominal operator. We show that a one-step-trained history-conditioned operator develops a training--deployment inconsistency under recursive scheduled propagation that spectral stabilization does not repair, and that training under the same scheduled rollout used at deployment restores long-horizon accuracy. The predictor is integrated into a one-iteration real-time-iteration (RTI) MPC that avoids re-running the full Transformer lifting encoder at every prediction stage, achieving a $p95$ controller latency of 120\,ms under a 200-ms sampling period, while tracking a matched exact scheduled NMPC oracle within $1\%$. A finite-horizon theory characterizes the rollout-error propagation and the local RTI approximation, and empirical diagnostics assess its assumptions. Experiments on a 6-state manipulator and a 2-state soft robotic platform support the modeling and real-time control claims.",
     r"Koopman modeling represents nonlinear dynamics as linear evolution in a lifted space whose accuracy depends critically on the lifting map and the identified operator. Many conventional EDMD and learned-lifting approaches use instantaneous-state observables with a fixed lifted transition, neglecting short-term temporal correlations and the dependence of the evolution on recent history. We propose Transformer-Koopman, where a patch-based Transformer encoder maps a finite history window to a structured lifted state and a low-rank history-dependent term modulates a full-rank nominal transition. We show that a one-step-trained history-conditioned operator develops a training--deployment inconsistency under recursive scheduled propagation that spectral stabilization does not repair, whereas training under the same scheduled rollout used at deployment restores long-horizon accuracy. The predictor is integrated into a one-iteration real-time-iteration (RTI) MPC that avoids re-running the full Transformer lifting encoder at every stage, achieving a $p95$ latency of 120\,ms under a 200-ms sampling period and tracking a matched exact scheduled NMPC oracle within $1\%$. A finite-horizon theory characterizes the rollout-error propagation and the local RTI approximation, supported by empirical diagnostics. Modeling and real-time control results on a 6-state manipulator and a 2-state soft robotic platform support the reported claims; hardware validation on the soft robot is left for future work."),

    # --- P1-8: remove the Transformer architecture catalogue ----------------------
    (r"Transformers \cite{vaswani2017attention} model temporal dependencies via self-attention, capturing dependencies across all time steps simultaneously and parallelizing better than recurrent networks. Efficient attention variants and decomposition-based models \cite{zhou2021informer, wang2020linformer, choromanski2021performer, wu2021autoformer, zhou2022fedformer} reduce the cost of long-sequence modeling, while patch-based tokenization \cite{nie2023time} aggregates local temporal structure before global attention. In Koopman lifting, where the relevant temporal context is unknown a priori, Transformers can incorporate short-term information from past trajectories.",
     r"Transformers model temporal dependencies through self-attention \cite{vaswani2017attention}, while patch-based tokenization provides an efficient representation of local temporal structure \cite{nie2023time}. In Koopman lifting, where the relevant temporal context is unknown a priori, Transformers can incorporate short-term information from past trajectories."),

    # --- P1-9: compress the RTI / quasi-LPV tutorial background -------------------
    (r"Two established strategies reduce the online cost of predictive control. The real-time iteration (RTI) performs a single sequential quadratic programming step per sampling instant around the current nominal trajectory, replacing the nonlinear program by a quadratic program \cite{diehl2005realtime, gros2020rti}; its nominal stability and suboptimality have been analyzed \cite{diehl2005rtistability}, and sensitivity-based schemes reduce delay by separating an offline nonlinear program from a fast online update \cite{zavala2009advancedstep}. Scheduled, or quasi-linear parameter-varying (quasi-LPV), control instead embeds a nonlinear model into a family of linear models indexed by a scheduling variable, so freezing or iterating the scheduling trajectory turns the problem into a sequence of QPs \cite{rugh2000gain, leith1998velocity, cisneros2016qlmpc, cisneros2020qlpv}.",
     r"Two established strategies reduce the online cost of predictive control. The real-time iteration (RTI) performs a single sequential quadratic programming update per sampling instant around the current nominal trajectory \cite{diehl2005realtime, gros2020rti}, and its nominal stability, suboptimality, and sensitivity-based delay reduction have been analyzed \cite{diehl2005rtistability, zavala2009advancedstep}. Quasi-linear parameter-varying (quasi-LPV) control instead embeds the nonlinear model into a family of linear models indexed by a scheduling variable, so that freezing or iterating the scheduling trajectory yields a sequence of tractable quadratic programs \cite{rugh2000gain, leith1998velocity, cisneros2016qlmpc, cisneros2020qlpv}."),
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

    before = text.count(r"\bibitem")
    for key in DELETE_KEYS:
        pat = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{" + re.escape(key)
                         + r"\}.*?(?=\\bibitem|\\end\{thebibliography\})", re.S)
        text, n = pat.subn("", text)
        assert n == 1, "could not delete %s (n=%d)" % (key, n)
    after = text.count(r"\bibitem")
    print("bibitems: %d -> %d (deleted %d)" % (before, after, before - after))

    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.replace("\r\n", "\n").split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
