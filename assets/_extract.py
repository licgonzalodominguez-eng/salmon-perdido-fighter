"""Recorta cada personaje de su render y guarda PNG transparente en sprites/.
La mayoría vienen con fondo verde (chroma key); Viper viene con fondo gris."""
import numpy as np
from PIL import Image, ImageFilter
import os, sys

SRC = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(SRC, "source")
OUT = os.path.join(SRC, "sprites")
os.makedirs(OUT, exist_ok=True)

B2 = "_2K_202608290413.jpeg"
# id -> (archivo en source/, caja [x0,y0,x1,y1], tolerancia, modo: ""|"green")
JOBS = {
    "michiloco": (f"Michiloco_character_sheet_2K_202608290103_(1).jpeg{B2}", (0.02, 0.02, 0.98, 0.99), 70, "green"),
    "ratin":     (f"Michiloco_character_sheet_2K_202608290103_(2).jpeg{B2}", (0.02, 0.02, 0.98, 0.99), 70, "green"),
    "bruce":     (f"Michiloco_character_sheet_2K_202608290103_(3).jpeg{B2}", (0.02, 0.02, 0.98, 0.99), 70, "green"),
    "lupita":    (f"Michiloco_character_sheet_2K_202608290103_(4).jpeg{B2}", (0.02, 0.02, 0.98, 0.99), 70, "green"),
    "nocturna":  (f"Michiloco_character_sheet_2K_202608290103_(5).jpeg{B2}", (0.02, 0.02, 0.98, 0.99), 70, "green"),
    "kai":       (f"Michiloco_character_sheet_2K_202608290103_(6).jpeg{B2}", (0.02, 0.02, 0.98, 0.99), 70, "green"),
    "yubari":    (f"Michiloco_character_sheet_2K_202608290103_(7).jpeg{B2}", (0.02, 0.02, 0.98, 0.99), 70, "green"),
    "atlas":     (f"Michiloco_character_sheet_2K_202608290103_(9).jpeg{B2}", (0.02, 0.02, 0.98, 0.99), 70, "green"),
    "viper":     ("viper_character_sheet.jpg_2K_202608290416.jpeg",          (0.09, 0.02, 0.95, 0.90), 40, ""),
}

TARGET_H = 520
PAD = 10


def dilate(m):
    o = m.copy()
    o[1:, :] |= m[:-1, :]; o[:-1, :] |= m[1:, :]
    o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    return o


def erode(m, n):
    e = m.copy()
    for _ in range(n):
        f = e.copy()
        f[1:, :] &= e[:-1, :]; f[:-1, :] &= e[1:, :]
        f[:, 1:] &= e[:, :-1]; f[:, :-1] &= e[:, 1:]
        e = f
    return e


def reconstruct(seed, allowed, max_iter=8000):
    cur = seed & allowed
    for _ in range(max_iter):
        nxt = dilate(cur) & allowed
        if np.array_equal(nxt, cur):
            break
        cur = nxt
    return cur


def components(mask):
    rem = mask.copy()
    out = []
    while rem.any() and len(out) < 200:
        ys, xs = np.nonzero(rem)
        s = np.zeros_like(rem); s[ys[0], xs[0]] = True
        c = reconstruct(s, rem)
        out.append(c); rem &= ~c
    return out


def largest_components(opaque, bg_like, keep_frac=0.08):
    comps = components(opaque)
    if not comps:
        return opaque
    comps.sort(key=lambda c: int(c.sum()), reverse=True)
    big = int(comps[0].sum())
    out = np.zeros_like(opaque)
    for i, c in enumerate(comps):
        n = int(c.sum())
        if n < keep_frac * big:
            continue
        if i > 0 and int((c & bg_like).sum()) > 0.55 * n:   # blob que es casi todo fondo -> descartar
            continue
        out |= c
    return out


def process(cid, fname, box, tol, mode=""):
    im = Image.open(os.path.join(SOURCE, fname)).convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = box
    crop = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    arr = np.asarray(crop).astype(np.int16)
    R, Gc, Bc = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    ch, cw, _ = arr.shape

    border = np.concatenate([
        arr[:8].reshape(-1, 3), arr[-8:].reshape(-1, 3),
        arr[:, :8].reshape(-1, 3), arr[:, -8:].reshape(-1, 3),
    ])
    bg = np.median(border, axis=0)
    dist = np.sqrt(((arr - bg) ** 2).sum(axis=2))

    seed = np.zeros((ch, cw), bool)
    seed[0, :] = seed[-1, :] = seed[:, 0] = seed[:, -1] = True

    if mode == "green":
        gdom = (Gc > R + 16) & (Gc > Bc + 8) & (Gc > 70)          # verde chroma
        bg_like = gdom | (dist < tol)
    else:
        bg_like = (dist < tol) | (arr.min(axis=2) > 232)

    background = reconstruct(seed, bg_like)
    fg = largest_components(~background, bg_like, keep_frac=0.08)

    if mode == "green":
        fg &= ~gdom                                               # nada de verde, esté donde esté
    else:
        fg &= ~bg_like
        neutral = (np.abs(R - Gc) < 18) & (np.abs(Gc - Bc) < 18) & (dist < 62)   # gris (sombra del piso)
        fg &= ~neutral

    # tapar SOLO huecos internos chicos que NO sean color de fondo (cuentas, hebillas)
    holes = (~reconstruct(seed, ~fg)) & ~fg
    lim = 0.012 * ch * cw
    for hc in components(holes):
        n = int(hc.sum())
        if n < lim and int((hc & bg_like).sum()) < 0.5 * n:
            fg |= hc
    fg = largest_components(fg, bg_like, keep_frac=0.05)          # descarta esquirlas sueltas
    inner = erode(fg, 2)                                          # borde hacia adentro (mata el fleco)

    a_img = Image.fromarray((inner.astype(np.uint8) * 255), "L").filter(ImageFilter.GaussianBlur(1.0))
    out = crop.convert("RGBA")
    out.putalpha(a_img)

    if mode == "green":                                           # quitar tinte verde del borde
        px = np.asarray(out).copy()
        r, g, b, a = px[:, :, 0].astype(int), px[:, :, 1].astype(int), px[:, :, 2].astype(int), px[:, :, 3]
        spill = (a > 0) & (g > np.maximum(r, b) + 12)
        px[:, :, 1] = np.where(spill, (np.maximum(r, b) + 12), g).astype(np.uint8)
        out = Image.fromarray(px, "RGBA")

    bb = out.getbbox()
    if bb:
        out = out.crop(bb)
    pad = Image.new("RGBA", (out.width + 2 * PAD, out.height + 2 * PAD), (0, 0, 0, 0))
    pad.paste(out, (PAD, PAD), out)
    out = pad
    sc = TARGET_H / out.height
    out = out.resize((max(1, round(out.width * sc)), TARGET_H), Image.LANCZOS)
    out.save(os.path.join(OUT, cid + ".png"))
    op = (np.asarray(out)[:, :, 3] > 16).mean() * 100
    print(f"{cid:10s} -> {out.size}  opaco={op:4.1f}%")


if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv) > 1 else list(JOBS)
    for cid in only:
        f, box, tol, mode = JOBS[cid]
        process(cid, f, box, tol, mode)
    print("listo ->", OUT)
