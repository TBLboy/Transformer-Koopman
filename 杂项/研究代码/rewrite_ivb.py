# -*- coding: utf-8 -*-
"""Rewrite Section IV-B (Training Procedure) + Algorithm 1 + Fig.2 caption to the
actual new-route implementation (one-step init -> rollout-aware scheduled training),
and repoint the single external eq:loss_x reference."""
import io, sys, os

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PATH = r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex"

with io.open(PATH, "r", encoding="utf-8", newline="") as f:
    text = f.read()

nl = "\r\n" if "\r\n" in text else "\n"
lines = text.split(nl)


def find(pred, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    raise RuntimeError("anchor not found")


# ---- anchors ----
i_body = find(lambda l: l.strip() == r"\subsection{Training Procedure}")
i_body_end = find(lambda l: l.strip().startswith("The complete training procedure is summarized"))
i_alg_s = find(lambda l: l.strip() == r"\begin{algorithm}[!t]", i_body_end)
i_alg_e = find(lambda l: l.strip() == r"\end{algorithm}", i_alg_s)
i_fig_s = find(lambda l: l.strip() == r"\begin{figure*}[!t]", i_alg_e)
i_fig_e = find(lambda l: l.strip() == r"\end{figure*}", i_fig_s)

print("anchors:", i_body + 1, i_body_end + 1, i_alg_s + 1, i_alg_e + 1, i_fig_s + 1, i_fig_e + 1)

new_body = r"""\subsection{Training Procedure}
\label{sec:training}
% ---------------------------------------------------------

The model of Definition~\ref{def:hcltk} has three trainable parts: the encoder parameters $\theta$ that produce the lifted state $\vz_k$, the context parameters $\phi$ that produce $\vc_k=C_\phi(\mX_k)$, and the dynamics parameters $\mA_0$, $\mU$, $\mV$, and $g$. The input matrix $\mB$ and the fixed projection $\mC$ are structural and are not trained, as in Definition~\ref{def:hcltk}.

Training proceeds in two stages. Stage~0 (\emph{initialization}) fits a time-invariant base operator to the encoder-generated one-step latent distribution. Stage~1 (\emph{rollout-aware scheduled training}) then trains the full history-conditioned family on the \emph{propagated}-latent distribution that arises at deployment, by minimizing the rollout-aware scheduled objective $\mathcal{L}_R$ of Definition~\ref{def:rollout_aware}.

\textbf{Stage~0 (initialization).} We initialize the encoder $g_\theta$ and a time-invariant base operator $(\mA_0,\mB)$ by minimizing the one-step physical prediction error over the encoder-generated latent distribution,
\begin{equation}
    \mathcal{L}_{1}
    =
    \sum_{k}
    \big\|\mC\big(\mA_0\,\vz_k+\mB\,\vu_k\big)-\vx_{k+1}\big\|_2^2,
    \qquad
    \vz_k=g_\theta(\mX_k).
    \label{eq:loss_one_step}
\end{equation}
This stage provides a well-scaled lifted representation and a stable base operator; it is the only stage that uses the encoder-consistent one-step latent distribution, and it corresponds to the fixed (time-invariant) Transformer-Koopman baseline used in Section~\ref{sec:experiments}.

\textbf{Stage~1 (rollout-aware scheduled training).} We then activate the low-rank context modulation $\mA(\vc_k)=\mA_0+\mU\,\mathrm{diag}(g(\vc_k))\,\mV^\top$ and train $\theta$, $\phi$, $\mA_0$, $\mU$, $\mV$, and $g$ jointly by minimizing the rollout-aware scheduled objective $\mathcal{L}_R$ of Definition~\ref{def:rollout_aware} \eqref{eq:loss_rollout}, in which the latent is propagated through $\mA(\vc_{k+i-1})$ while the context is \emph{re-scheduled} from the history that the predictor itself has rolled out, $\vc_{k+i-1}=C_\phi(\hat{\mX}_{k+i-1})$ (Section~\ref{subsec:rollout_aware}). The input matrix $\mB$ and the projection $\mC$ are held fixed. We use horizon $H_R=20$ with uniform weights $w_i$.

Minimizing $\mathcal{L}_R$ trains the operator on the propagated-latent distribution that arises at deployment, rather than on the encoder-generated one-step distribution---precisely the distribution shift analyzed in Section~\ref{subsec:rollout_aware}. We deliberately do \emph{not} apply a closed-form EDMD refit: once the transition is history-conditioned, the regression target is no longer a single operator $(\mA,\mB)$ shared across all contexts, and the scheduled objective already constrains the propagated distribution. We also do not rely on spectral stabilization; Remark~\ref{rem:spectral} and Section~\ref{sec:experiments} show that constraining $\rho(\mA(\vc))<1$ does not restore scheduled-rollout accuracy, whereas changing the training objective does.

The modulation is parameterized with a bounded budget so that the lifted dynamics remain well-conditioned: the columns of $\mU$ and $\mV$ are unit-norm and $g$ is bounded elementwise, so $\|\mA(\vc)-\mA_0\|_2$ is bounded uniformly in $\vc$. Throughout, $r=2$; the rank sweep in Section~\ref{sec:experiments} shows this to be the minimal near-optimal choice.

The complete procedure is summarized in Algorithm~\ref{alg:training}."""

new_alg = r"""\begin{algorithm}[!t]
\caption{Transformer-Koopman Training Algorithm}
\label{alg:training}
\begin{algorithmic}[1]

\STATE \textbf{Input:} Dataset $\mathcal{D}$ \eqref{eq:dataset}
\STATE History length $P$; patch length $p$; lifted dimension $d$; rank $r$; rollout horizon $H_R$
\STATE Rollout weights $w_1,\ldots,w_{H_R}$; epochs $E_0$ (initialization), $E_1$ (scheduled training)

\STATE \textbf{Output:} Encoder $\theta^{*}$; context $\phi^{*}$; transition parameters $\mA_0^{*},\mU^{*},\mV^{*},g^{*}$

\STATE \textbf{Stage~0 (initialization):}
Initialize $\theta$ and $(\mA_0,\mB)$; for $E_0$ epochs, minimize the one-step loss \eqref{eq:loss_one_step} over $(\theta,\mA_0,\mB)$.

\vspace{2pt}

\STATE \textbf{Stage~1 (rollout-aware scheduled training):}
Activate $\mA(\vc)=\mA_0+\mU\,\mathrm{diag}(g(\vc))\,\mV^\top$; fix $\mB$ and $\mC$.
\FOR{epoch $\ell = 1$ \TO $E_1$}
    \FOR{each mini-batch $\mathcal{B} \subset \mathcal{D}$}
        \STATE Roll out the latent over $H_R$ steps, re-scheduling the context $\vc_{k+i}=C_\phi(\hat{\mX}_{k+i})$ from the rolled-out history.
        \STATE Form the scheduled objective $\mathcal{L}_R$ \eqref{eq:loss_rollout}.
        \STATE Update $(\theta,\phi,\mA_0,\mU,\mV,g)$ via gradient descent.
    \ENDFOR
\ENDFOR

\RETURN $\theta^{*},\phi^{*},\mA_0^{*},\mU^{*},\mV^{*},g^{*}$

\end{algorithmic}
\end{algorithm}"""

new_fig = r"""\begin{figure*}[!t]
    \centering
    \includegraphics[width=0.95\textwidth]{pictures/Figure2.pdf}
    \caption{One-step lifting and prediction (initialization, Stage~0). The
    history window $\mX_k$ and its shift $\mX_k^{+}$ are each encoded by
    $g_\theta$ to produce $\vz_k$ and $\vz_k^{+}$. The time-invariant base
    operator $(\mA_0,\mB)$ produces the one-step prediction
    $\hat{\vz}_{k+1}=\mA_0\vz_k+\mB\vu_k$, from which $\hat{\vx}_{k+1}$ is
    recovered via $\mC$. This one-step coupling is used to initialize the
    encoder and base operator, supervised by the one-step loss
    \eqref{eq:loss_one_step}. Stage~1 replaces $\mA_0$ by the
    history-conditioned $\mA(\vc)$ and trains on the rollout-aware scheduled
    objective (Algorithm~\ref{alg:training}).}
    \label{fig:training_procedure}
\end{figure*}"""

# splice from bottom up
lines[i_fig_s:i_fig_e + 1] = new_fig.split("\n")
lines[i_alg_s:i_alg_e + 1] = new_alg.split("\n")
lines[i_body:i_body_end + 1] = new_body.split("\n")

text = nl.join(lines)

# repoint the single external eq:loss_x reference in Section IV-C
old_ref = r"enforced approximately by the state-consistency loss \eqref{eq:loss_x} rather than structurally."
new_ref = r"enforced approximately by the one-step prediction loss \eqref{eq:loss_one_step} rather than structurally."
assert text.count(old_ref) == 1, "eq:loss_x ref not found uniquely"
text = text.replace(old_ref, new_ref)

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(text)

# sanity: no dangling labels
for lab in ["eq:loss_x", "eq:loss_z", "eq:loss_c", "eq:loss_multi_x", "eq:loss_multi_z",
            "eq:pretraining_loss", "eq:edmd_solution", "eq:multi_step_lifted_rollout",
            "eq:multi_step_state_rollout"]:
    assert lab not in text, "dangling label: " + lab
print("OK; eq:loss_one_step present:", text.count("eq:loss_one_step"))
