"""Extrae cada personaje de su lámina/render individual y guarda PNG transparente en sprites/.
Viper no tiene render nuevo: su sprite se mantiene tal cual (no está en JOBS)."""
import numpy as np
from PIL import Image, ImageFilter
import os, sys

SRC = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(SRC, "source")
OUT = os.path.join(SRC, "sprites")
os.makedirs(OUT, exist_ok=True)

# id -> (archivo en source/, caja [x0,y0,x1,y1] en fracciones, tolerancia, sujeto_claro)
JOBS = {
    "michiloco": ("White_cat_wearing_cape_standing_202608290101.jpeg", (0.05, 0.03, 0.97, 0.99), 26, True),
    "lupita":    ("Cat_dressed_as_sorceress_princess_202608290101.jpeg",(0.09, 0.02, 0.94, 0.99), 30, False),
    "kai":       ("Cat_warrior_wearing_tactical_armor_202608290101.jpeg",(0.24, 0.02, 0.83, 0.99), 30, False),
    "atlas":     ("Pink_axolotl_wearing_stone_armor_202608290101.jpeg",(0.03, 0.03, 0.98, 0.99), 32, False),
    "nocturna":  ("Cat_queen_standing_in_gown_202608290101.jpeg",     (0.12, 0.01, 0.95, 0.995), 32, False),
    "bruce":     ("bruce_new.jpeg",                                   (0.360, 0.03, 0.592, 0.945), 64, False),
    "yubari":    ("Cat_wearing_green_robe_standing_202608290101.jpeg", (0.245, 0.03, 0.725, 0.955), 46, True),
    "ratin":     ("Gray_ninja_mouse_standing_2K_202608290101.jpeg",   (0.23, 0.01, 0.69, 0.995), 30, False),
}

TARGET_H = 480
PAD = 8


def dilate(m):
    o = m.copy()
    o[1:, :] |= m[:-1, :]; o[:-1, :] |= m[1:, :]
    o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    return o


def reconstruct(seed, allowed, max_iter=6000):
    cur = seed & allowed
    for _ in range(max_iter):
        nxt = dilate(cur) & allowed
        if np.array_equal(nxt, cur):
            break
        cur = nxt
    return cur


def largest_components(opaque, keep_frac=0.10):
    rem = opaque.copy()
    comps = []
    while rem.any() and len(comps) < 60:
        ys, xs = np.nonzero(rem)
        s = np.zeros_like(rem); s[ys[0], xs[0]] = True
        c = reconstruct(s, rem)
        comps.append(c); rem &= ~c
    if not comps:
        return opaque
    comps.sort(key=lambda c: int(c.sum()), reverse=True)
    big = int(comps[0].sum())
    out = np.zeros_like(opaque)
    for c in comps:
        if int(c.sum()) >= keep_frac * big:
            out |= c
    return out


def erode(m, n):
    e = m.copy()
    for _ in range(n):
        f = e.copy()
        f[1:, :] &= e[:-1, :]; f[:-1, :] &= e[1:, :]
        f[:, 1:] &= e[:, :-1]; f[:, :-1] &= e[:, 1:]
        e = f
    return e


def process(cid, fname, box, tol, white=False):
    im = Image.open(os.path.join(SOURCE, fname)).convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = box
    crop = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    arr = np.asarray(crop).astype(np.int16)
    ch, cw, _ = arr.shape

    border = np.concatenate([
        arr[:8, :, :].reshape(-1, 3), arr[-8:, :, :].reshape(-1, 3),
        arr[:, :8, :].reshape(-1, 3), arr[:, -8:, :].reshape(-1, 3),
    ])
    bg = np.median(border, axis=0)
    dist = np.sqrt(((arr - bg) ** 2).sum(axis=2))
    mn = arr.min(axis=2)
    bg_like = dist < tol if white else ((dist < tol) | (mn > 232))

    seed = np.zeros((ch, cw), bool)
    seed[0, :] = seed[-1, :] = seed[:, 0] = seed[:, -1] = True
    background = reconstruct(seed, bg_like)
    fg = largest_components(~background, keep_frac=0.06 if white else 0.10)
    fg = ~reconstruct(seed, ~fg)                 # rellena huecos internos
    fg = erode(fg, 1 if white else 2)            # quita el halo del matte

    a_img = Image.fromarray((fg.astype(np.uint8) * 255), "L").filter(ImageFilter.GaussianBlur(0.6))
    out = crop.convert("RGBA")
    out.putalpha(a_img)
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
    print(f"{cid:10s} {fname:48s} -> {out.size}  opaco={op:4.1f}%")


if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv) > 1 else list(JOBS)
    for cid in only:
        f, box, tol, white = JOBS[cid]
        process(cid, f, box, tol, white)
    print("listo ->", OUT)
