import hashlib
import sys

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

DOC = r"D:\Project\Transformer-Koopman\.project-log\docs\business-logic\clarification.yaml"

text = open(DOC, encoding="utf-8").read()

OLD = """      - 仅 platform2 缺: experiment.deterministic, experiment.amp, training.prefetch_factor,
        training.edmd.pretrain.multi_step.horizon, loss_weights.multi_step_physical, loss_weights.multi_step_latent
"""
NEW = """      - 仅 platform2 缺: [experiment.deterministic, experiment.amp, training.prefetch_factor,
          training.edmd.pretrain.multi_step.horizon, loss_weights.multi_step_physical,
          loss_weights.multi_step_latent]
"""

if OLD in text:
    text = text.replace(OLD, NEW)
    open(DOC, "w", encoding="utf-8", newline="\n").write(text)
    print("patched.")
else:
    print("PATTERN NOT FOUND - inspecting surrounding lines")

# re-validate, reporting every problem instead of stopping at the first
try:
    data = yaml.safe_load(text)
    print("YAML VALID")
    print("top keys:", list(data.keys()))
    print("alignment entries:", len(data["alignment"]))
except yaml.YAMLError as error:
    print("STILL INVALID:")
    mark = getattr(error, "problem_mark", None)
    if mark is not None:
        lines = text.splitlines()
        for i in range(max(0, mark.line - 4), min(len(lines), mark.line + 3)):
            flag = ">>" if i == mark.line else "  "
            print(f"{flag} {i+1:4d}: {lines[i]}")
    print(error)

print("bytes:", len(text.encode("utf-8")))
print("sha256:", hashlib.sha256(text.encode("utf-8")).hexdigest())
