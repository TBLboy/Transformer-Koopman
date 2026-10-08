# -*- coding: utf-8 -*-
"""Verify the v3 compression pass: removed phrases gone, new phrases present, citation integrity."""
import re
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")
t = TEX.read_text(encoding="utf-8")

gone = [
    r"\subsection{Recursive Multi-Step Deployment}",
    r"eq:edmd_regression",
    r"\emph{R1:}",
    r"\emph{R2:}",
    r"\emph{R3:}",
    r"A length-$H$ training segment",
    r"not a fixed linear time-invariant (LTI) model",
    r"we do not claim that minimizing it implies any bound",
    r"deliberately use different information",
    r"represent the current dynamical condition",
    r"The proposed framework addresses them in three corresponding steps",
    r"\subsection{Representation: Instantaneous versus History-Based Lifting}",
    r"\subsection{Transition Adaptation: Context-Aware and Time-Varying Operators}",
    r"\subsection{Real-Time and Scheduled Predictive Control}",
    r"\subsection{Patch-Based Temporal Lifting Architecture}",
    r"must constitute a complete Markov state",
    r"We also do not rely on spectral stabilization",
]
gone_ok = True
for g in gone:
    c = t.count(g)
    if c:
        gone_ok = False
        print("STILL PRESENT (%d): %s" % (c, g))
print("removed-phrase check:", "PASS" if gone_ok else "FAIL")

added = [
    r"\subsection{History-Based Koopman Representation}",
    r"\subsection{Context-Dependent Koopman Dynamics and Recursive Prediction}",
    r"\subsection{Real-Time Predictive Control}",
    r"\subsection{Temporal Lifting and History-Conditioned Transition}",
    r"We instantiate the predictor of Section~\ref{sec:problem}",
    r"Training operates on length-$H_R$ segments",
    r"The rollout objective is an algorithmic training mechanism",
    r"minimizing it is not claimed to imply any bound on $\epsilon_k$, $d_{\mathcal M}(H)$, or $\mLf$",
    r"the context map additionally uses the past inputs",
    r"history-conditioned parameter-varying lifted system that remains linear",
    r"is standard in neural system identification more broadly \cite{forgione2021dynonet}",
]
add_ok = True
for a in added:
    c = t.count(a)
    if c != 1:
        add_ok = False
        print("EXPECTED 1, found %d: %s" % (c, a))
print("added-phrase check:", "PASS" if add_ok else "FAIL")

subs = re.findall(r"\\subsection\{([^}]*)\}", t)
print("\nsubsections (%d):" % len(subs))
for s in subs:
    print("  -", s)

# citation integrity
bib = set(re.findall(r"\\bibitem\{([^}]*)\}", t))
cited = set()
for m in re.findall(r"\\cite\{([^}]*)\}", t):
    for k in m.split(","):
        cited.add(k.strip())
print("\nbibitems: %d | cited: %d | uncited: %s | undefined: %s"
      % (len(bib), len(cited), sorted(bib - cited), sorted(cited - bib)))

labels = set(re.findall(r"\\label\{([^}]*)\}", t))
refs = set()
for m in re.findall(r"\\(?:eq|fig|tab|sec|subsec|prop|thm|cor|def|ass|rem|app)ref\{([^}]*)\}", t):
    refs.add(m.strip())
print("labels: %d | referenced: %d | never-referenced: %d | DANGLING: %s"
      % (len(labels), len(refs), len(labels - refs), sorted(refs - labels)))

print("\nbytes: %d | words: %d" % (len(t.encode("utf-8")), len(t.split())))
