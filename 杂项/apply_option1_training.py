# -*- coding: utf-8 -*-
"""Apply the user-selected Option 1 revision (DEC-041).

- remove the false claim that B is frozen during Stage 1 (DEC-040)
- reframe the training schedule: Stage 0 = nominal one-step pretraining
  (optimization initialization), Stage 1 = scheduled-rollout fine-tuning of the
  joint parameter set with only C structurally fixed
- add the training-schedule ablation (strategies A/B/C/D, 3 seeds) to Section VII
- repair the forward references that pointed at a rank sweep / modulation claim
  not present in the paper
"""
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")
R = []

# ---- IV-A: separate structure from training strategy; re-point the ablation claim
R.append((
    "Context dependence is confined to $\\mA(\\vc)$, while $\\mB$ remains fixed so that the current input enters through a common affine channel. The resulting model is a history-conditioned parameter-varying lifted system that remains linear in $(\\vz_k,\\vu_k)$ for a fixed context, and the fixed projection \\eqref{eq:decoder_projection} recovers the physical state exactly. Ablations (Section~\\ref{sec:experiments}) show that the predictive benefit is concentrated in the $\\mA$-modulation and that $r=2$ is the minimal near-optimal rank.",
    "Context dependence is confined to $\\mA(\\vc)$; $\\mB$ is a single global matrix shared across all contexts, so the current input always enters through the same affine channel. The resulting model is a history-conditioned parameter-varying lifted system that remains linear in $(\\vz_k,\\vu_k)$ for a fixed context, and the fixed projection \\eqref{eq:decoder_projection} recovers the physical state exactly. Section~\\ref{subsec:schedule_ablation} shows that the modulation must be refined jointly with the temporal representation and the nominal transition, since training it alone degrades deployment accuracy by more than an order of magnitude."
))

# ---- IV-B: B is context-independent, not frozen
R.append((
    "The input matrix $\\mB$ is context-independent: it is learned during Stage~0 and then frozen during Stage~1.",
    "The input matrix $\\mB$ is context-independent: a single global matrix is shared across all contexts and is optimized jointly with the other parameters."
))

# ---- IV-B: two-stage schedule framed as an optimization schedule
R.append((
    "Training therefore proceeds in two stages. Stage~0 (\\emph{initialization}) learns the shared nominal backbone---the encoder and a time-invariant base operator---from encoder-consistent one-step transitions. Stage~1 (\\emph{rollout-aware scheduled training}) then refines the context-dependent correction, training the full history-conditioned family on the \\emph{propagated}-latent distribution that arises at deployment, by minimizing the rollout-aware scheduled objective $\\mathcal{L}_R$ of Definition~\\ref{def:rollout_aware}.",
    "Training therefore proceeds in two stages, which we treat as an optimization schedule rather than a requirement of the model: a nominal one-step pretraining stage that provides a well-scaled initialization, followed by scheduled-rollout fine-tuning that jointly refines the full history-conditioned family on the \\emph{propagated}-latent distribution that arises at deployment, by minimizing the rollout-aware scheduled objective $\\mathcal{L}_R$ of Definition~\\ref{def:rollout_aware}."
))

# ---- IV-B: Stage 0 renamed
R.append((
    "\\textbf{Stage~0 (initialization).}",
    "\\textbf{Stage~0 (nominal one-step pretraining).}"
))

# ---- IV-B: Stage 0 positioned as an initialization
R.append((
    "This stage provides a well-scaled lifted representation and a data-fitted nominal base operator; it is the only training stage optimized exclusively on the encoder-consistent one-step latent distribution, and it corresponds to the fixed (time-invariant) Transformer-Koopman baseline used in Section~\\ref{sec:experiments}.",
    "This stage provides a well-scaled lifted representation and a data-fitted nominal base operator; it is the only stage optimized exclusively on the encoder-consistent one-step latent distribution, and it corresponds to the fixed (time-invariant) Transformer-Koopman baseline. It serves as an optimization initialization: Section~\\ref{subsec:schedule_ablation} shows that omitting it does not degrade deployment accuracy."
))

# ---- IV-B: Stage 1 renamed and described as joint refinement; only C fixed
R.append((
    "\\textbf{Stage~1 (rollout-aware scheduled training).} We then activate the low-rank context modulation $\\mA(\\vc_k)=\\mA_0+\\mU\\,\\mathrm{diag}(\\gamma_\\psi(\\vc_k))\\,\\mV^\\top$ and train $\\theta$, $\\phi$, $\\mA_0$, $\\mU$, $\\mV$, and $\\gamma_\\psi$ jointly by minimizing the rollout-aware scheduled objective $\\mathcal{L}_R$ of Definition~\\ref{def:rollout_aware} \\eqref{eq:loss_rollout}, in which the latent is propagated through $\\mA(\\vc_{k+i-1})$ while the context is \\emph{re-scheduled} from the history that the predictor itself has rolled out, $\\vc_{k+i-1}=C_\\phi(\\hat{\\mX}_{k+i-1},\\mU^{\\mathrm{in}}_{k+i-1})$ (Section~\\ref{subsec:rollout}). The input matrix $\\mB$ (learned in Stage~0) and the projection $\\mC$ are held fixed. We use horizon $H_R=20$ with uniform weights $w_i$.",
    "\\textbf{Stage~1 (scheduled-rollout fine-tuning).} We then activate the low-rank context modulation $\\mA(\\vc_k)=\\mA_0+\\mU\\,\\mathrm{diag}(\\gamma_\\psi(\\vc_k))\\,\\mV^\\top$ and jointly refine $\\theta$, $\\phi$, $\\mA_0$, $\\mU$, $\\mV$, $\\gamma_\\psi$, and the shared input matrix $\\mB$ by minimizing the rollout-aware scheduled objective $\\mathcal{L}_R$ of Definition~\\ref{def:rollout_aware} \\eqref{eq:loss_rollout}, in which the latent is propagated through $\\mA(\\vc_{k+i-1})$ while the context is \\emph{re-scheduled} from the history that the predictor itself has rolled out, $\\vc_{k+i-1}=C_\\phi(\\hat{\\mX}_{k+i-1},\\mU^{\\mathrm{in}}_{k+i-1})$ (Section~\\ref{subsec:rollout}). Only the projection $\\mC$ is structurally fixed. We use horizon $H_R=20$ with uniform weights $w_i$."
))

# ---- IV-B: drop the unsupported rank-sweep forward reference
R.append((
    "Throughout, $r=2$; the rank sweep in Section~\\ref{sec:experiments} shows this to be the minimal near-optimal choice.",
    "Throughout, $r=2$, a small rank chosen so that the modulation remains a bounded low-rank correction of the nominal transition."
))

# ---- Algorithm 1
R.append((
    "\\STATE Rollout weights $w_1,\\ldots,w_{H_R}$; epochs $E_0$ (initialization), $E_1$ (scheduled training)",
    "\\STATE Rollout weights $w_1,\\ldots,w_{H_R}$; epochs $E_0$ (nominal pretraining), $E_1$ (scheduled-rollout fine-tuning)"
))
R.append((
    "\\STATE \\textbf{Output:} Lifting encoder $\\theta^{*}$; context $\\phi^{*}$; transition parameters $\\mA_0^{*},\\mU^{*},\\mV^{*},\\gamma_\\psi^{*}$",
    "\\STATE \\textbf{Output:} Lifting encoder $\\theta^{*}$; context $\\phi^{*}$; transition parameters $\\mA_0^{*},\\mU^{*},\\mV^{*},\\gamma_\\psi^{*}$; input matrix $\\mB^{*}$"
))
R.append((
    "\\STATE \\textbf{Stage~0 (initialization):}",
    "\\STATE \\textbf{Stage~0 (nominal one-step pretraining):}"
))
R.append((
    "\\STATE \\textbf{Stage~1 (rollout-aware scheduled training):}",
    "\\STATE \\textbf{Stage~1 (scheduled-rollout fine-tuning):}"
))
R.append((
    "Activate $\\mA(\\vc)=\\mA_0+\\mU\\,\\mathrm{diag}(\\gamma_\\psi(\\vc))\\,\\mV^\\top$; fix $\\mB$ and $\\mC$.",
    "Activate $\\mA(\\vc)=\\mA_0+\\mU\\,\\mathrm{diag}(\\gamma_\\psi(\\vc))\\,\\mV^\\top$; keep only $\\mC$ structurally fixed."
))
R.append((
    "\\STATE Update $(\\theta,\\phi,\\mA_0,\\mU,\\mV,\\gamma_\\psi)$ via gradient descent.",
    "\\STATE Update $(\\theta,\\phi,\\mA_0,\\mU,\\mV,\\gamma_\\psi,\\mB)$ via gradient descent."
))
R.append((
    "\\RETURN $\\theta^{*},\\phi^{*},\\mA_0^{*},\\mU^{*},\\mV^{*},\\gamma_\\psi^{*}$",
    "\\RETURN $\\theta^{*},\\phi^{*},\\mA_0^{*},\\mU^{*},\\mV^{*},\\gamma_\\psi^{*},\\mB^{*}$"
))

# ---- Fig. 2 caption
R.append((
    "\\caption{One-step lifting and prediction (initialization, Stage~0). The",
    "\\caption{One-step lifting and prediction (nominal pretraining, Stage~0). The"
))
R.append((
    "Stage~1 replaces $\\mA_0$ by the\n    history-conditioned $\\mA(\\vc)$ and trains on the rollout-aware scheduled\n    objective (Algorithm~\\ref{alg:training}).}",
    "Stage~1 replaces $\\mA_0$ by the\n    history-conditioned $\\mA(\\vc)$ and jointly refines the full model on the\n    rollout-aware scheduled objective (Algorithm~\\ref{alg:training}).}"
))

# ---- Section VII intro
R.append((
    "This section reports the empirical diagnostics that assess the assumptions and quantities of the consistency analysis of Section~\\ref{sec:theory}.",
    "This section reports a training-schedule ablation of the history-conditioned predictor, followed by the empirical diagnostics that assess the assumptions and quantities of the consistency analysis of Section~\\ref{sec:theory}."
))

# ---- Section VII: insert the ablation subsection before the diagnostics subsection
ABL = r"""\subsection{Training Schedule Ablation}
\label{subsec:schedule_ablation}

We assess how the training schedule affects the deployment accuracy of the history-conditioned predictor. All variants share the same architecture, data, optimizer, rollout horizon ($H_R=20$), learning rate, batch size, and epoch budget, and differ only in which parameters the scheduled-rollout stage optimizes. Strategy~A optimizes only the low-rank modulation $(\phi,\mU,\mV,\gamma_\psi)$ while freezing the temporal lifting $\theta$, the nominal transition $\mA_0$, and the input matrix $\mB$; strategy~B freezes only $\mB$; strategy~C optimizes all parameters; strategy~D omits the nominal one-step pretraining stage and optimizes all parameters from a random initialization. Table~\ref{tab:schedule_ablation} reports the validation rollout RMSE under the deployment-consistent scheduled propagation, averaged over three seeds.

\begin{table}[!t]
\centering
\caption{Training-schedule ablation: validation rollout RMSE under scheduled propagation, averaged over three seeds ($H_R=20$ during training). The seed spread at $H=20$ is at most $0.0011$ for B--D.}
\label{tab:schedule_ablation}
\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}llcccc@{}}
\toprule
 & Scheduled-rollout stage & $H=1$ & $H=5$ & $H=10$ & $H=20$ \\
\midrule
A & modulation only & $0.0276$ & $0.1787$ & $0.4300$ & $1.1533$ \\
B & all but $\mB$ & $0.0173$ & $0.0271$ & $0.0337$ & $0.0440$ \\
C & all parameters & $0.0115$ & $0.0228$ & $0.0301$ & $0.0415$ \\
D & all, no pretraining & $0.0112$ & $0.0217$ & $0.0289$ & $0.0401$ \\
\bottomrule
\end{tabular}
\end{table}

Three observations follow. First, the scheduled-rollout objective is the essential ingredient: optimizing only the low-rank modulation while freezing the temporal lifting and the nominal transition (A) degrades the $H=20$ rollout error by more than an order of magnitude ($1.1533$ versus $0.0415$), so the representation and the nominal transition must adapt together with the modulation. Second, freezing the input matrix brings no benefit: variant~B is worse than variant~C at every horizon and in every seed, by $5.6\%$ at $H=20$, with a $24\%$ higher rollout MSE. Third, the nominal pretraining stage is not required: optimizing all parameters directly under the scheduled-rollout objective (D) matches or slightly exceeds C while removing one training stage and reducing the total training time ($311$~s versus $338$~s). We therefore treat the two-stage schedule of Section~\ref{sec:methodology} as an optimization initialization rather than a necessity of the model, and all remaining results use the predictor of strategy~C, whose training schedule is the one described there. The separation of B from C and D exceeds the seed spread, whereas C and D are statistically indistinguishable.

\subsection{Mechanism and Theory Diagnostics}
\label{subsec:diagnostics}"""
R.append((
    "\\subsection{Mechanism and Theory Diagnostics}\n\\label{subsec:diagnostics}",
    ABL
))


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    assert "\ufeff" not in raw, "unexpected BOM"
    nl = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    for i, (old, new) in enumerate(R, 1):
        c = text.count(old)
        assert c == 1, "item %d: expected 1, found %d\n--- %s" % (i, c, old[:120])
        text = text.replace(old, new)
        print("applied %d" % i)
    with open(TEX, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(text.split("\n")))
    print("OK")


if __name__ == "__main__":
    main()
