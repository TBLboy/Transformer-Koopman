import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

LOG = r"C:\Users\12187\AppData\Local\Temp\opencode\fullsuite.log"
lines = open(LOG, encoding="utf-16").read().splitlines()

TARGETS = (
    "test_existing_lockfile_is_restored_after_failed_update",
    "test_package_manager_failure_leaves_no_artifacts_or_dirs",
    "test_package_manager_failure_rolls_back_all_writes",
)

i = 0
while i < len(lines):
    if re.match(r"^(FAIL|ERROR): ", lines[i]):
        header, j = lines[i], i + 1
        while not header.rstrip().endswith(")") and j < len(lines):
            header += lines[j]; j += 1
        raw = [header]
        while j < len(lines) and not re.match(r"^={20,}$", lines[j]):
            raw.append(lines[j]); j += 1
        if any(t in header for t in TARGETS):
            print("=" * 78)
            for l in raw:
                print(re.sub(r"[^\x20-\x7e]", ".", l)[:200])
        i = j
    else:
        i += 1
