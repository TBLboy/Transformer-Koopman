import json

CFG = r"C:\Users\12187\.config\opencode\opencode.json"
BAK = r"C:\Users\12187\.config\opencode\backups\opencode.json.bak-20260928-113716"

cur = open(CFG, encoding="utf-8", newline="").read()
print("current newlines: CRLF=%d, bare LF=%d" % (cur.count("\r\n"), cur.count("\n") - cur.count("\r\n")))

# restore the original CRLF convention; the only intended change is the 8 removed lines
crlf = cur.replace("\r\n", "\n").replace("\n", "\r\n")
with open(CFG, "w", encoding="utf-8", newline="") as fh:
    fh.write(crlf)

after = open(CFG, encoding="utf-8", newline="").read()
print("after rewrite: CRLF=%d, bytes=%d" % (after.count("\r\n"), len(after.encode("utf-8"))))
print("JSON valid:", bool(json.loads(after)))

old = open(BAK, encoding="utf-8", newline="").read()
old_lines = old.split("\r\n")
new_lines = after.split("\r\n")
print("lines before/after:", len(old_lines), "/", len(new_lines))
removed = [i for i, l in enumerate(old_lines) if l.strip() == '"enabled": true,']
expected = [l for i, l in enumerate(old_lines) if i not in set(removed)]
print("exactly the 8 'enabled' lines removed and nothing else changed:",
      expected == new_lines)
if expected != new_lines:
    for i, (a, b) in enumerate(zip(expected, new_lines)):
        if a != b:
            print("  first diff at line", i + 1)
            print("   expected:", repr(a))
            print("   actual  :", repr(b))
            break
