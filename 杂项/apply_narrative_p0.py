# -*- coding: utf-8 -*-
"""Apply the P0 items of the problem-driven narrative review (option A).

1. Introduction gap paragraph: add the missing layer -- history-aware lifting
   still requires all history-dependent regimes to share one global lifted
   transition.
2. Introduction contribution paragraph: drop the flawed "same instantaneous
   state" argument for A(c).
3. Section III-A ending: add the III-A -> III-B bridge.
4. Section III-B: rename to "Prediction Problem and Design Requirements" and
   state three requirements R1/R2/R3 before the abstract predictor.
5. Section IV opening: add the requirement-to-component map.
6. Section IV-A: rewrite the motivation for A(c) in terms of global-transition
   rigidity, and add the shared-vs-corrective reading of the decomposition.
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")

REPL = []

# --- 1. Introduction gap paragraph -----------------------------------------
REPL.append((
    "These approaches differ from the formulation considered here, where history selectively modulates a low-rank deviation around a nominal lifted transition learned jointly with the lifting map, and such limitations can become more pronounced under recursive multi-step prediction.",
    "Enriching the observables with history supplies temporal information that the current measurement alone does not, but it leaves a second question open: a single time-invariant lifted transition still requires every history-dependent operating regime to share one global linear evolution in the learned coordinates, which can place a strong burden on the lifting map when the effective dynamics vary with recent trajectory context. We therefore separate history dependence into two roles---history is encoded into the lifted state, and a structured low-rank correction selectively adjusts a shared nominal transition. Such distinctions can matter more under recursive multi-step prediction."
))

# --- 2. Introduction contribution paragraph --------------------------------
REPL.append((
    "rather than fitting a single time-invariant operator, we let the history modulate the lifted transition through a low-rank term, so that the same instantaneous state can evolve differently depending on the recent trajectory.",
    "rather than requiring all history-dependent regimes to share a single time-invariant operator, we let the history modulate the lifted transition through a low-rank term, so that the transition can adapt to the recent trajectory while the propagation remains linear in the lifted state for a given context."
))

# --- 3. Section III-A -> III-B bridge --------------------------------------
REPL.append((
    "where $\\vw_k$ denotes the lifted-space approximation residual. In this work, $g_\\theta$ is implemented using a Transformer encoder, while Section~\\ref{sec:methodology} develops the history-conditioned transition used in the proposed model.",
    "where $\\vw_k$ denotes the lifted-space approximation residual. In this work, $g_\\theta$ is implemented using a Transformer encoder. Temporal lifting makes recent trajectory information available in the latent state, but it does not by itself remove the restriction imposed by a single global lifted transition: a fixed $\\mA$ requires every history-dependent latent state to evolve under the same linear operator, which may be unnecessarily restrictive when the effective dynamics vary with recent trajectory context. Replacing the lifted dynamics by a fully nonlinear black-box predictor would remove that restriction but would discard the conditional-linear structure that makes the model usable for predictive control. These considerations motivate the prediction problem formulated next."
))

# --- 4. Section III-B rename ----------------------------------------------
REPL.append((
    "\\subsection{Learning Problem}",
    "\\subsection{Prediction Problem and Design Requirements}"
))

# --- 5. Section III-B: requirements R1/R2/R3 ------------------------------
REPL.append((
    "A length-$H$ training segment therefore contains the tuple $(\\mX_k,\\allowbreak \\mU_k^{\\mathrm{in}},\\allowbreak \\vu_{k:k+H-1},\\allowbreak \\vx_{k+1:k+H})$ and is extracted without crossing trajectory boundaries.",
    "A length-$H$ training segment therefore contains the tuple $(\\mX_k,\\allowbreak \\mU_k^{\\mathrm{in}},\\allowbreak \\vu_{k:k+H-1},\\allowbreak \\vx_{k+1:k+H})$ and is extracted without crossing trajectory boundaries.\n\n"
    "Because the measured state need not form a complete Markov state, the predictor must exploit finite history. However, using history only in the lifting map does not by itself remove the restriction imposed by a single global lifted transition: all history-dependent latent states would still be required to evolve under the same linear operator. Conversely, replacing the lifted dynamics with an unstructured nonlinear predictor would weaken the linear structure that makes Koopman models attractive for predictive control.\n\n"
    "These considerations lead to three requirements for a control-oriented predictor. \\emph{R1:} the lifted representation should incorporate recent trajectory information while preserving the current measured state. \\emph{R2:} the lifted transition should be allowed to adapt to trajectory context, while remaining linear in the lifted state and the current input for a given context. \\emph{R3:} because future contexts are generated from the model's own predicted histories during recursive deployment, the predictor should remain accurate under this scheduled rollout rather than only on encoder-consistent one-step transitions."
))

# --- 6. Section III-B: predictor framing ----------------------------------
REPL.append((
    "The learning objective is to construct a state-preserving temporal lifting",
    "A predictor satisfying these requirements takes the form of a state-preserving temporal lifting"
))

# --- 7. Section III-B: closing forward reference --------------------------
REPL.append((
    "where the current control input enters through a context-independent linear channel. We seek a predictor that maintains small finite-horizon recursive prediction error when the history is updated from its own predicted outputs, while retaining a conditional-linear structure suitable for predictive control. Section~\\ref{sec:methodology} instantiates $\\mathcal{A}_{\\psi}$ using the proposed history-conditioned low-rank transition and specifies the Transformer lifting map.",
    "where the current control input enters through a context-independent linear channel. Section~\\ref{sec:methodology} realizes these requirements through a patch-based Transformer lifting map, a low-rank history-conditioned modulation of a shared nominal transition, and deployment-consistent scheduled training."
))

# --- 8. Section IV opening: requirement-to-component map ------------------
REPL.append((
    "In this section, we present the proposed Transformer-Koopman framework\nfor temporal lifting and model identification. We first introduce the\nlifting architecture based on Transformer encoding, and then describe\nthe associated training procedure and modeling error characterization.",
    "Section~\\ref{sec:problem} identifies three requirements: history-aware representation, context-adaptive conditional-linear propagation, and consistency under recursively scheduled deployment. The proposed framework addresses them in three corresponding steps. A patch-based Transformer first constructs a state-preserving temporal lifting; a low-rank history-conditioned modulation then adapts a shared nominal lifted transition; finally, the model is trained under the same scheduled rollout used at deployment. We describe the lifting architecture, the training procedure, and the modeling error characterization in turn."
))

# --- 9. Section IV-A: motivation for A(c) ---------------------------------
REPL.append((
    "Given the lifted state \\eqref{eq:lifted_state_form}, a \\emph{single time-invariant} operator $\\mA$ is generally insufficient: the same instantaneous state can evolve differently depending on the recent trajectory (a flexible body has memory). We therefore condition the lifted transition on the history through a low-rank modulation.",
    "Although the temporal lifting provides different latent representations for different histories, a fixed transition $\\mA$ still requires all such history-dependent latent states to evolve under one global linear operator. To relax this additional restriction without discarding the conditional-linear structure, we decompose the transition into a shared nominal component and a structured history-dependent correction."
))

# --- 10. Section IV-A: shared-vs-corrective reading -----------------------
REPL.append((
    "Throughout, $r=2$.",
    "Throughout, $r=2$. The decomposition separates shared dynamics from context-dependent variation: $\\mA_0$ captures the nominal lifted evolution common across histories, while the low-rank correction restricts history-dependent adaptation to a small learned transition subspace, so that history selectively adjusts the nominal transition rather than regenerating the entire operator."
))


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    assert "\ufeff" not in raw, "unexpected BOM"
    nl = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")

    for i, (old, new) in enumerate(REPL, 1):
        c = text.count(old)
        assert c == 1, "item %d: expected 1 occurrence, found %d\n--- %s" % (i, c, old[:90])
        text = text.replace(old, new)
        print("applied item %d" % i)

    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
