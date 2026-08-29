"""Genera dist/salmon-perdido-fighter.html: un solo archivo con los sprites incrustados.
Uso:  python build.py
"""
import base64, os, mimetypes

ROOT = os.path.dirname(os.path.abspath(__file__))
SPRITES = os.path.join(ROOT, "assets", "sprites")
DIST = os.path.join(ROOT, "dist")
os.makedirs(DIST, exist_ok=True)

IDS = ["michiloco", "lupita", "bruce", "kai", "atlas", "nocturna", "viper", "yubari", "ratin"]

def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")

parts = []
for cid in IDS:
    p = os.path.join(SPRITES, cid + ".png")
    if os.path.exists(p):
        parts.append(f'"{cid}":"{data_uri(p)}"')
inject = "<script>window.SPRITE_DATA={" + ",".join(parts) + "};</script>\n"

with open(os.path.join(ROOT, "index.html"), "r", encoding="utf-8") as f:
    html = f.read()

marker = "<script>\n(() => {"
if marker not in html:
    raise SystemExit("no se encontró el <script> principal en index.html")
html = html.replace(marker, inject + marker, 1)

out = os.path.join(DIST, "salmon-perdido-fighter.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

kb = os.path.getsize(out) / 1024
print(f"OK  {out}  ({kb:.0f} KB, {len(parts)} sprites incrustados)")
