# -*- coding: utf-8 -*-
"""Apply the full citation-support audit fixes to Main.tex.

- Removes 8 bibliography entries: 2 nonexistent (yuan2022variational, rank2019recurrent)
  and 6 never-cited entries.
- Corrects verified metadata errors (pages, author list, subtitle, missing vol/issue,
  superseded arXiv entry -> published CDC version).
- Fixes one claim-support mismatch and one citation-key year inconsistency.
Every replacement is asserted to occur exactly once.
"""
import re
from pathlib import Path

TEX = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\Main.tex")

DELETE_KEYS = [
    "yuan2022variational",        # FAIL: fabricated / nonexistent
    "rank2019recurrent",          # FAIL: nonexistent
    "brunton2016sindy",           # never cited
    "zeng2023transformers",       # never cited
    "liu2024itransformer",        # never cited
    "forootani2026compact",       # never cited
    "forootani2025synthetic",     # never cited
    "katharopoulos2020transformers",  # never cited
]

REPLACE = [
    # --- claim-support fix: split efficiency variants from patch tokenization -------
    (r'Efficient variants and patch-based tokenization \cite{zhou2021informer, wang2020linformer, choromanski2021performer, wu2021autoformer, zhou2022fedformer, nie2023time} further improve efficiency by aggregating local temporal structure before global attention.',
     r'Efficient attention variants and decomposition-based models \cite{zhou2021informer, wang2020linformer, choromanski2021performer, wu2021autoformer, zhou2022fedformer} reduce the cost of long-sequence modeling, while patch-based tokenization \cite{nie2023time} aggregates local temporal structure before global attention.'),
    # --- remove fabricated entry from its citation cluster -------------------------
    (r'\cite{takeishi2017koopman, lusch2018deep, yeung2019learning, morton2019deep, yuan2022variational}',
     r'\cite{takeishi2017koopman, lusch2018deep, yeung2019learning, morton2019deep}'),
    # --- citation-key year consistency --------------------------------------------
    (r'\cite{forootani2026deepkoopformer, forootani2026spectral}',
     r'\cite{forootani2025deepkoopformer, forootani2026spectral}'),
    (r'\bibitem{forootani2026deepkoopformer}', r'\bibitem{forootani2025deepkoopformer}'),
    # --- metadata corrections ------------------------------------------------------
    (r'in \emph{Proc. IJCAI}, 2019, pp. 5113--5119.',
     r'in \emph{Proc. IJCAI}, 2019, pp. 3173--3179.'),
    (r'S. Klus, P. Koltai, and C. Sch\"utte,',
     r'S. Klus, F. N\"uske, P. Koltai, H. Wu, I. Kevrekidis, C. Sch\"utte, and F. No\'e,'),
    (r'vol. 35, no. 4, pp. 612--629, 2021.', r'vol. 35, no. 4, pp. 612--626, 2021.'),
    (r'Neural Networks and Fuzzy Models}, 2nd ed.',
     r'Neural Networks, Fuzzy Models, and Gaussian Processes}, 2nd ed.'),
    (r'\emph{SIAM J. Appl. Dyn. Syst.}, 2020, arXiv:1810.01479.',
     r'\emph{SIAM J. Appl. Dyn. Syst.}, vol. 19, no. 2, pp. 886--917, 2020.'),
    (r"Y. Han, W. Hao, and U. Vaidya, ``Deep learning of Koopman representation for control,'' arXiv:2010.07546, 2020.",
     r"Y. Han, W. Hao, and U. Vaidya, ``Deep learning of Koopman representation for control,'' in \emph{Proc. IEEE Conf. Decision Control (CDC)}, 2020, pp. 1890--1895."),
    (r'\emph{Nonlinear Dyn.}, vol. 41, pp. 309--325, 2005.',
     r'\emph{Nonlinear Dyn.}, vol. 41, no. 1--3, pp. 309--325, 2005.'),
    (r'Auton. Syst.}, vol. 4, pp. 59--87, 2021.',
     r'Auton. Syst.}, vol. 4, no. 1, pp. 59--87, 2021.'),
    (r'\emph{J. Stat. Phys.}, vol. 175, pp. 1107--1145, 2019.',
     r'\emph{J. Stat. Phys.}, vol. 175, no. 6, pp. 1107--1145, 2019.'),
    (r'Prentice Hall, 1999.', r'Prentice Hall PTR, 1999.'),
]


def main():
    with open(TEX, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    assert "\ufeff" not in text, "unexpected BOM"
    nl = "\r\n" if "\r\n" in text else "\n"

    # 1) textual replacements
    for old, new in REPLACE:
        n = text.count(old)
        assert n == 1, "expected 1 occurrence, got %d for: %s" % (n, old[:70])
        text = text.replace(old, new)
    print("applied %d replacements" % len(REPLACE))

    # 2) drop dead / fabricated bibliography entries
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
