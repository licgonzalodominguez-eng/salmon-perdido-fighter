"""Extrae la figura de cuerpo entero de cada hoja de personaje y guarda PNG transparente."""
import numpy as np
from PIL import Image, ImageFilter
import os, sys

SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SRC, "sprites")
os.makedirs(OUT, exist_ok=True)

# id -> (archivo, caja de recorte en fracciones [x0,y0,x1,y1], tolerancia de fondo, sujeto_claro)
JOBS = {
    "michiloco": ("Michiloco_Character_Reference.jpg",              (0.752, 0.132, 0.958, 0.535), 20, True),
    "lupita":    ("sorceress_princess_lupita_reference_sheet_5.jpg",(0.072, 0.142, 0.268, 0.468), 20, True),
    "bruce":     ("bruce_cat_turnaround_sheet.jpg",                 (0.058, 0.185, 0.225, 0.560), 36, False),
    "kai":       ("kai_character_design_sheet.jpg",                 (0.705, 0.545, 0.975, 0.950), 40, False),
    "atlas":     ("atlas_character_sheet.jpg",                      (0.045, 0.115, 0.345, 0.575), 34, False),
    "nocturna":  ("nocturna_shadow_queen_sheet.jpg",               (0.105, 0.075, 0.315, 0.580), 34, False),
    "viper":     ("viper_character_sheet.jpg",                      (0.118, 0.050, 0.285, 0.535), 36, False),
    "yubari":    ("master_yubari_buddhist_reference_sheet.jpg",     (0.095, 0.115, 0.315, 0.625), 34, False),
    "ratin":     ("ratin_ninja_reference_sheet_1.jpg",             (0.055, 0.055, 0.245, 0.625), 36, False),
}

TARGET_H = 460
PAD = 8


def dilate(mask):
    out = mask.copy()
    out[1:, :] |= mask[:-1, :]
    out[:-1, :] |= mask[1:, :]
    out[:, 1:] |= mask[:, :-1]
    out[:, :-1] |= mask[:, 1:]
    return out


def reconstruct(seed, allowed, max_iter=4000):
    """Reconstrucción morfológica: expande seed dentro de allowed hasta estabilizar."""
    cur = seed & allowed
    for _ in range(max_iter):
        nxt = dilate(cur) & allowed
        if np.array_equal(nxt, cur):
            break
        cur = nxt
    return cur


def largest_components(opaque, keep_frac=0.12):
    """Devuelve máscara con el componente opaco mayor + los que superen keep_frac de su área."""
    remaining = opaque.copy()
    comps = []
    h, w = opaque.shape
    while remaining.any():
        ys, xs = np.nonzero(remaining)
        seed = np.zeros_like(remaining)
        seed[ys[0], xs[0]] = True
        comp = reconstruct(seed, remaining)
        comps.append(comp)
        remaining &= ~comp
        if len(comps) > 40:
            break
    comps.sort(key=lambda c: int(c.sum()), reverse=True)
    if not comps:
        return opaque
    biggest = int(comps[0].sum())
    out = np.zeros_like(opaque)
    for c in comps:
        if int(c.sum()) >= keep_frac * biggest:
            out |= c
    return out


def process(cid, fname, box, tol, white=False):
    im = Image.open(os.path.join(SRC, fname)).convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = box
    crop = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    arr = np.asarray(crop).astype(np.int16)
    ch, cw, _ = arr.shape

    # color de fondo = mediana de un marco fino en el borde
    border = np.concatenate([
        arr[:6, :, :].reshape(-1, 3), arr[-6:, :, :].reshape(-1, 3),
        arr[:, :6, :].reshape(-1, 3), arr[:, -6:, :].reshape(-1, 3),
    ])
    bg = np.median(border, axis=0)

    dist = np.sqrt(((arr - bg) ** 2).sum(axis=2))
    mn = arr.min(axis=2)
    if white:
        # sujeto claro (gato blanco/crema): NO tratar "brillante" como fondo,
        # solo lo muy parecido al color exacto del borde
        bg_like = dist < tol
    else:
        bg_like = (dist < tol) | (mn > 232)

    seed = np.zeros((ch, cw), bool)
    seed[0, :] = seed[-1, :] = seed[:, 0] = seed[:, -1] = True
    background = reconstruct(seed, bg_like)

    fg = ~background
    fg = largest_components(fg, keep_frac=0.05 if white else 0.12)

    # limpiar: rellenar huecos internos, erosionar y suavizar
    fg_filled = ~reconstruct(seed, ~fg)          # fondo real = lo conectado al borde
    er = fg_filled.copy()
    for _ in range(1 if white else 2):
        e = er.copy()
        e[1:, :] &= er[:-1, :]; e[:-1, :] &= er[1:, :]
        e[:, 1:] &= er[:, :-1]; e[:, :-1] &= er[:, 1:]
        er = e
    alpha = (er.astype(np.uint8)) * 255
    a_img = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(0.6))

    out = crop.convert("RGBA")
    out.putalpha(a_img)

    # recortar a contenido
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    out = out.crop((-PAD, -PAD, out.width + PAD, out.height + PAD)) if False else out
    # padding manual transparente
    padded = Image.new("RGBA", (out.width + 2 * PAD, out.height + 2 * PAD), (0, 0, 0, 0))
    padded.paste(out, (PAD, PAD), out)
    out = padded

    scale = TARGET_H / out.height
    out = out.resize((max(1, round(out.width * scale)), TARGET_H), Image.LANCZOS)

    dst = os.path.join(OUT, cid + ".png")
    out.save(dst)
    op = (np.asarray(out)[:, :, 3] > 16).mean()
    print(f"{cid:10s} {fname:42s} -> {out.size}  opaco={op*100:4.1f}%")


if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv) > 1 else list(JOBS)
    for cid in only:
        f, box, tol, white = JOBS[cid]
        process(cid, f, box, tol, white)
    print("listo ->", OUT)
