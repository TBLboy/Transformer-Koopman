import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
import fitz  # PyMuPDF

pdf = r"D:\Project\Transformer-Koopman\Transformer-Koopman\论文\新版本\build\Main.pdf"
out = r"C:\Users\12187\AppData\Local\Temp\opencode\pdf_pages"
os.makedirs(out, exist_ok=True)
doc = fitz.open(pdf)
print("pages:", doc.page_count)
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=110)
    p = os.path.join(out, f"page_{i+1:02d}.png")
    pix.save(p)
    print("saved", p, pix.width, "x", pix.height)
