import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

P = Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\scripts\train_lstm_platforms.py")
text = P.read_text(encoding="utf-8")

OLD = '''    # Run training
    start_time = time.time()
    
    with open(log_file, "w", encoding="utf-8") as f:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        
        for line in process.stdout:
            print(line, end="")
            f.write(line)
            f.flush()
        
        process.wait()
    
    elapsed = time.time() - start_time
    
    if process.returncode == 0:
'''

NEW = '''    # Run training (cwd pinned to the project root so relative data_dir resolves)
    returncode, elapsed = run_streaming(cmd, PROJECT_DIR, log_path=log_file)

    if returncode == 0:
'''

if OLD not in text:
    print("OLD block not found; aborting")
    sys.exit(1)

text = text.replace(OLD, NEW, 1)
with open(P, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("replaced OK")
