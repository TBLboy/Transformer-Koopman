import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PY = r"D:\conda\envs\vibe-coding\python.exe"
VIBE = r"C:\Users\12187\.config\opencode\vibe-workflow\scripts\vibe.py"
ROOT = r"D:\Project\Transformer-Koopman"
TMP = r"C:\Users\12187\AppData\Local\Temp\opencode"
DOC_REL = ".project-log/docs/business-logic/clarification.yaml"
DOC_ABS = Path(ROOT) / DOC_REL

text = DOC_ABS.read_text(encoding="utf-8")

# --- R1: stability switches are platform x method divergent, not uniformly off
R1_OLD = """    stability_switches_actually_set:
      platform1: enforce_stability=false, svd_clipping=false
      platform2: enforce_stability=false, svd_clipping=false
"""
R1_NEW = """    stability_switches_actually_set:
      note: 稳定机制按平台与方法分叉，不存在统一关闭
      platform1_edmd_M1: enforce_stability=false, svd_clipping=false -> 无保护
      platform1_end_to_end_M5: svd_projection.enabled=true, frequency=1 -> 每 epoch 调用 ensure_stability()，有保护
      platform2_edmd_M1: enforce_stability=false, svd_clipping=false -> 无保护
      platform2_end_to_end_M5: svd_projection.enabled=false -> 无保护
      baselines_MLP_LSTM_traditional: 无稳定性保证，代码仅打印谱半径
"""

# --- R2: rewrite the whole ALN-015 block
R2_NEW = """  - id: ALN-015
    class: constraint-conflict
    subject: 稳定性不变量 INV1 的实际状态按平台与方法分叉，且 6 份产物日志出现 rho > 1
    should: 谱半径 <= 1，以保证控制器稳定性（论文的稳定性前提）
    actual_matrix:
      platform1_edmd_M1: enforce_stability=false, svd_clipping=false -> 无保护
      platform1_end_to_end_M5: svd_projection.enabled=true, frequency=1 -> 每 epoch 调用 ensure_stability()，有保护
      platform2_edmd_M1: enforce_stability=false, svd_clipping=false -> 无保护
      platform2_end_to_end_M5: svd_projection.enabled=false -> 无保护
      baselines_MLP_LSTM_traditional: 无稳定性保证，代码仅打印谱半径
    artifacts_with_rho_gt_1:
      - results/logs/Platform_1_LSTM-Koopman_20260529_173639.log (rho=1.0842, line 791)
      - results/logs/Platform_2_LSTM-Koopman_20260529_160545.log (rho=1.0033, line 41)
      - results/logs/Platform_2_LSTM-Koopman_20260529_173345.log (rho=1.2351, line 1573)
      - results/logs/p2_mlp_koopman.log (rho=1.0138, line 356)
      - results/logs/p2_patchtst_koopman.log (rho=1.0005, lines 58 and 3022)
      - results/logs/p2_traditional_edmd.log (rho=1.0023, line 51)
    note_main_method_breaches: p2_patchtst_koopman.log 表明主方法 PatchTST-Koopman 的产物也超过 1（1.0005），不限于基线
    evidence:
      - configs/platform1.yaml（enforce_stability、edmd.compute.svd_clipping、end_to_end.svd_projection）
      - configs/platform2.yaml（同上三项）
      - src/patchtst_koopman/training/edmd_trainer.py:174-176（end-to-end 路径每 epoch 调 ensure_stability）
      - src/patchtst_koopman/training/edmd_trainer.py:446-447（只打印谱半径，无警告）
      - 上列 6 份 results/logs/*.log
    impact: 结论级 —— 对控制论文而言稳定性前提被削弱，且不触发任何警告
    provenance_caveat: 这些日志来自外部树（论文4\\code-projectv2 与 D:\\Project\\code-projectv2），属历史运行证据，非同树重跑
    status: open
    verification: 每次训练后断言 spectral_radius <= 1，或按平台与方法分叉显式记录并解释超限；阶段② 决定是否统一恢复稳定机制
"""

# --- R3: source the 10.0 to the user decision, not to artifacts
R3_OLD = "  - 多步损失的 lambda 数值（含 multi_step_physical=10.0）与 N_L 取值\n"
R3_NEW = "  - 多步损失的 lambda 数值与 N_L 取值（multi_step_physical=10.0 来自用户决策 DEC-003，非产物证据；当前配置中该值为 1.0）\n"

rep = {"R1": (R1_OLD, R1_NEW), "R3": (R3_OLD, R3_NEW)}
for tag, (old, new) in rep.items():
    if old in text:
        text = text.replace(old, new)
        print(f"  {tag}: applied")
    else:
        print(f"  {tag}: PATTERN NOT FOUND")

# R2 by regex span
m = re.search(r"  - id: ALN-015\n.*?(?=  - id: ALN-016\n)", text, re.DOTALL)
if m:
    text = text[:m.start()] + R2_NEW + text[m.end():]
    print("  R2: ALN-015 block replaced")
else:
    print("  R2: ALN-015 block NOT FOUND")

DOC_ABS.write_text(text, encoding="utf-8", newline="\n")

raw = DOC_ABS.read_bytes()
NEW_SHA = hashlib.sha256(raw).hexdigest()
data = yaml.safe_load(raw.decode("utf-8"))
ids = [a["id"] for a in data["alignment"]]
print(f"\nYAML VALID  bytes={len(raw)}  sha256={NEW_SHA}")
print(f"alignments={len(ids)}  unique={len(set(ids))}  duplicates={[i for i in ids if ids.count(i) > 1]}")

DB = next(Path(ROOT, ".project-log", ".state").rglob("state.sqlite3"))
conn = sqlite3.connect(DB)


def revision() -> int:
    r = subprocess.run([PY, VIBE, "--root", ROOT, "status"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8", "replace"))["revision"]


def apply(action, payload, tag, label):
    env = {"schema_version": 1, "command_id": tag, "expected_revision": revision(),
           "action": action, "payload": payload}
    p = f"{TMP}/env_{tag}.json"
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(env, ensure_ascii=False, indent=2))
    r = subprocess.run([PY, VIBE, "--root", ROOT, "state-apply", "--file", p], capture_output=True)
    ok = r.returncode == 0
    note = "" if ok else r.stderr.decode("utf-8", "replace").strip()[:150]
    print(f"  {'OK ' if ok else 'FAIL'} {label} {note}")


print("\n== refresh doc_ref hashes ==")
carriers = [(k, i, rev) for k, i, rev, pl in conn.execute(
    "SELECT kind, id, revision, payload FROM records ORDER BY kind, id") if "doc_ref" in (pl or "")]
print(f"  carriers: {len(carriers)}")
for kind, rid, rev in carriers:
    apply("record.update",
          {"kind": kind, "id": rid, "expected_record_revision": rev,
           "payload": {"doc_ref": {"path": DOC_REL, "sha256": NEW_SHA}}},
          f"t3-ref-{kind}-{rid}".lower().replace("_", "-"), f"{kind}/{rid}")

# BA-LOSS-NUM payload should source 10.0 to DEC-003
row = conn.execute("SELECT revision FROM records WHERE kind='business-atom' AND id='BA-LOSS-NUM'").fetchone()
if row:
    apply("record.update",
          {"kind": "business-atom", "id": "BA-LOSS-NUM", "expected_record_revision": row[0],
           "payload": {"rule": "lambda 数值与 horizon N_L 尚未冻结，属阶段② 理论方法讨论议题；其中 multi_step_physical=10.0 来自用户决策 DEC-003，不是产物证据（当前配置中为 1.0）"}},
          "t3-fix-ba-loss-num", "business-atom/BA-LOSS-NUM")

print("\nfinal revision:", revision())
