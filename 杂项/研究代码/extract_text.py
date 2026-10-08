# -*- coding: utf-8 -*-
import fitz, os
pdf = r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\build\Main.pdf"
out = r"C:\Users\12187\AppData\Local\Temp\opencode\pdf_text_p8_p9.txt"
doc = fitz.open(pdf)
with open(out, "w", encoding="utf-8") as f:
    for i in (7, 8):
        f.write(f"===== PAGE {i+1} =====\n")
        f.write(doc[i].get_text())
        f.write("\n")
print("written", out)
