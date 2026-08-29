"""Genera dist/salmon-perdido-fighter.html: un solo archivo con los sprites incrustados.
Uso:  python build.py
"""
import base64, os, mimetypes

ROOT = os.path.dirname(os.path.abspath(__file__))
SPRITES = os.path.join(ROOT, "assets", "sprites")
STAGES_DIR = os.path.join(ROOT, "assets", "stages")
DIST = os.path.join(ROOT, "dist")
os.makedirs(DIST, exist_ok=True)

IDS = ["michiloco", "lupita", "bruce", "kai", "atlas", "nocturna", "viper", "yubari", "ratin"]
STAGE_IDS = ["dojo", "hechiceria", "laberinto", "espejos", "muelle", "oceano", "sparta", "flotante"]

def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")

def mapfor(ids, folder, ext):
    out = []
    for i in ids:
        p = os.path.join(folder, i + ext)
        if os.path.exists(p):
            out.append(f'"{i}":"{data_uri(p)}"')
    return out

parts = mapfor(IDS, SPRITES, ".png")
stage_parts = mapfor(STAGE_IDS, STAGES_DIR, ".jpg")
inject = ("<script>window.SPRITE_DATA={" + ",".join(parts) + "};"
          + "window.STAGE_DATA={" + ",".join(stage_parts) + "};</script>\n")

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
print(f"OK  {out}  ({kb:.0f} KB, {len(parts)} sprites + {len(stage_parts)} escenarios)")
