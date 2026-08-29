"""Redimensiona los fondos de escenario y los deja en assets/stages/<id>.jpg."""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source", "stages")
OUT = os.path.join(HERE, "stages")
os.makedirs(OUT, exist_ok=True)

# id -> archivo fuente
JOBS = {
    "dojo":          "Dojo.jpeg",
    "hechiceria":    "Escuela de hechiceria.jpeg",
    "laberinto":     "Laberinto Michiloco.jpeg",
    "espejos":       "Laberinto de Espejos.jpeg",
    "muelle":        "Muelle.jpeg",
    "oceano":        "Oceano.jpeg",
    "sparta":        "Sparta.jpeg",
    "flotante":      "Casa Flotante.jpeg",
}

W = 1600
for sid, fn in JOBS.items():
    p = os.path.join(SRC, fn)
    if not os.path.exists(p):
        print("FALTA", fn)
        continue
    im = Image.open(p).convert("RGB")
    h = round(W * im.height / im.width)
    im = im.resize((W, h), Image.LANCZOS)
    out = os.path.join(OUT, sid + ".jpg")
    im.save(out, quality=82, optimize=True)
    print(f"{sid:12s} {im.size}  {os.path.getsize(out)//1024} KB")
