#!/usr/bin/python3
"""Apple hardware: classic Winamp 2.x skins in the style of the iMac G3 (1998-2001) and the
unibody MacBook Pro (2008-2012), from one procedural generator with themes.

Every bitmap is drawn here from code (shapes, gradients, noise, hand-made pixel fonts), apart
from two Apple logos rasterised from source/ at build time: the six-colour logo (iMac themes'
About spot) and the plain Apple logo (the MacBook Pro's glowing lid logo).

    /usr/bin/python3 -I gen_skin.py                     # every theme
    /usr/bin/python3 -I gen_skin.py imac-bondi macbook-pro
    /usr/bin/python3 -I gen_skin.py --list

Each theme writes its sheets into out/<theme>/, zips them flat into <name>.wsz beside this
script, and draws preview-<theme>.png (the windows assembled from the sprites at their real
positions, as the app does, 2x). Based on the structure of skins/ember/gen_skin.py.
"""

import os
import subprocess
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.join(HERE, "out")
SCRATCH = os.path.join(OUT_ROOT, "scratch")
RAINBOW_SVG = os.path.join(HERE, "source", "logo-rainbow", "apple-rainbow.svg")
APPLE_SVG = os.path.join(HERE, "source", "logo-apple", "apple-logo.svg")
SEP = (255, 0, 255)  # gen.bmp letter separators (never shown)
WHITE = (255, 255, 255)

# ------------------------------------------------------------------------------------------
# Colour helpers
# ------------------------------------------------------------------------------------------


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def tint(c, t):
    return lerp(c, WHITE, t)


def shade(c, t):
    return lerp(c, (0, 0, 0), t)


def hexc(c):
    return "#%02X%02X%02X" % tuple(c)


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

# iMac G3 plastic tones, read off product photos (Apple published no colour values). Bondi Blue
# is the 1998 original (the paint-chip "Bondi blue" is #0095B6; the plastic reads a touch deeper
# and greener over white); the five 1999 "flavours"; Graphite from the late-1999 iMac DV SE.
IMAC = {
    "bondi": ("Bondi-Blue", (0, 142, 170)),
    "blueberry": ("Blueberry", (30, 96, 192)),
    "strawberry": ("Strawberry", (218, 52, 98)),
    "lime": ("Lime", (106, 186, 44)),
    "grape": ("Grape", (104, 62, 156)),
    "tangerine": ("Tangerine", (246, 132, 30)),
    "graphite": ("Graphite", (98, 102, 110)),
}

THEME_KEYS = [f"imac-{k}" for k in IMAC] + ["macbook-pro"]
LED_GREEN = (96, 236, 72)


def make_theme(key):
    if key.startswith("imac-"):
        name, C = IMAC[key[5:]]
        face = lerp(WHITE, C, 0.86)
        ice = lerp((238, 242, 245), C, 0.10)
        disp = lerp((10, 13, 16), C, 0.07)
        ink = tint(C, 0.55)
        if luma(ink) < 165:
            ink = tint(C, 0.65)
        bezel = lerp((26, 30, 34), C, 0.18)
        t = dict(
            model="imac", C=C, face=face, ice=ice,
            body=face, body_hi=tint(C, 0.55), body_lo=shade(C, 0.45),
            rim=shade(C, 0.42), rim_hi=tint(C, 0.5),
            disp=disp, bezel=bezel, bezel_hi=lerp(bezel, C, 0.35),
            ink=ink, ink_mid=lerp(disp, ink, 0.55), ink_dim=lerp(disp, ink, 0.22),
            key_top=(253, 254, 255), key_bot=lerp((214, 222, 227), C, 0.14),
            key_edge=lerp((128, 138, 146), C, 0.40), key_ink=shade(C, 0.55),
            key_ink_on=shade(C, 0.72),
            plate=ice, plate_ink=shade(C, 0.52), plate_ink_dim=lerp(ice, (120, 126, 132), 0.55),
            label=shade(C, 0.6), label_dim=lerp(shade(C, 0.3), ice, 0.35),
            groove=lerp(disp, C, 0.18), fill=tint(C, 0.12), fill_hi=tint(C, 0.5),
            led_on=LED_GREEN, led_off=lerp((150, 158, 160), C, 0.1),
            pl_normal=ink, pl_current=(255, 255, 255), pl_sel=lerp(disp, C, 0.45),
            vis_spec=[tint(C, 0.8), tint(C, 0.45), C, shade(C, 0.25), shade(C, 0.5)],
            vis_osc=[tint(C, 0.75), tint(C, 0.55), tint(C, 0.35), C, shade(C, 0.2)],
            vis_peak=(255, 255, 255),
            title_word="iMac", name=name, wsz=f"iMac-G3-{name}.wsz",
            subject=f"the iMac G3 ({name.replace('-', ' ')})",
        )
    else:
        bezel = (14, 14, 16)
        disp = (6, 7, 9)
        ink = (228, 234, 242)
        aqua = (94, 166, 255)
        t = dict(
            model="mbp", C=(196, 199, 204),
            alu_top=(214, 217, 221), alu_bot=(184, 187, 193),
            body=(199, 202, 207), body_hi=(240, 241, 244), body_lo=(118, 121, 127),
            rim=(116, 119, 125), rim_hi=(244, 245, 247),
            disp=disp, bezel=bezel, bezel_hi=(54, 55, 60),
            ink=ink, ink_mid=lerp(disp, ink, 0.55), ink_dim=lerp(disp, ink, 0.2),
            key_top=(44, 44, 47), key_bot=(22, 22, 24), key_edge=(8, 8, 9),
            key_ink=(236, 237, 240), key_ink_on=(255, 255, 255),
            well=(146, 149, 155),
            plate=(181, 184, 190), plate_ink=(72, 74, 80), plate_ink_dim=(132, 135, 141),
            label=(74, 76, 82), label_dim=(130, 133, 139),
            groove=(40, 41, 45), fill=(238, 241, 246), fill_hi=(255, 255, 255),
            led_on=LED_GREEN, led_off=(52, 53, 56),
            pl_normal=(212, 217, 224), pl_current=(126, 190, 255), pl_sel=(40, 66, 106),
            vis_spec=[(214, 234, 255), (140, 194, 255), aqua, (40, 104, 210), (24, 62, 150)],
            vis_osc=[(220, 236, 255), (170, 208, 255), (120, 178, 255), aqua, (50, 116, 220)],
            vis_peak=(255, 255, 255),
            title_word="MacBook Pro", name="Unibody", wsz="MacBook-Pro-Unibody.wsz",
            subject="the unibody MacBook Pro (2008-2012)",
        )
    t.update(key=key, preview=f"preview-{key}.png")
    return t


T = None
OUT = None
_rng = None


def imac():
    return T["model"] == "imac"


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3)
# ------------------------------------------------------------------------------------------


def new(w, h, col=None):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = T["body"] if col is None else col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):y + h, max(0, x):x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def blend_px(a, x, y, col, t):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = lerp(tuple(int(v) for v in a[y, x]), col, t)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def _grid(w, h, ss):
    xs = (np.arange(w * ss) + 0.5) / ss
    ys = (np.arange(h * ss) + 0.5) / ss
    return np.meshgrid(xs, ys)


def rr_alpha(w, h, r, inset=0.0, ss=4):
    """Rounded rectangle w x h with corner radius r, shrunk by inset (antialiased coverage)."""
    X, Y = _grid(w, h, ss)
    x0, y0, x1, y1 = inset, inset, w - inset, h - inset
    rr = max(0.0, min(r - inset, (x1 - x0) / 2, (y1 - y0) / 2))
    dx = np.maximum(np.maximum(x0 + rr - X, X - (x1 - rr)), 0)
    dy = np.maximum(np.maximum(y0 + rr - Y, Y - (y1 - rr)), 0)
    inside = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1) & (dx * dx + dy * dy <= rr * rr + 1e-9)
    return inside.reshape(h, ss, w, ss).mean(axis=(1, 3))


def disc_alpha(w, h, cx, cy, rad, ss=4):
    X, Y = _grid(w, h, ss)
    inside = (X - cx) ** 2 + (Y - cy) ** 2 <= rad * rad
    return inside.reshape(h, ss, w, ss).mean(axis=(1, 3))


def ellipse_alpha(w, h, cx, cy, rx, ry, ss=4):
    X, Y = _grid(w, h, ss)
    inside = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1
    return inside.reshape(h, ss, w, ss).mean(axis=(1, 3))


def composite(a, x, y, al, col):
    """Paints col (a colour, a column of row colours, or an H x W x 3 layer) through alpha al."""
    h, w = al.shape
    reg = a[y:y + h, x:x + w].astype(np.float64)
    c = np.asarray(col, dtype=np.float64)
    if c.ndim == 1:
        c = c[None, None, :]
    elif c.ndim == 2:
        c = c[:, None, :]
    out = reg * (1 - al[..., None]) + c * al[..., None]
    a[y:y + h, x:x + w] = np.round(out).astype(np.int32)


def vgrad(h, stops):
    return np.array([ramp(stops, r / max(1, h - 1)) for r in range(h)], dtype=np.float64)


def shape(a, x, y, w, h, r, stops, edge):
    """A rounded shape: a 1px ring of the edge colour round a gradient face."""
    composite(a, x, y, rr_alpha(w, h, r), edge)
    composite(a, x, y, rr_alpha(w, h, r, 1.0), vgrad(h, stops))


def gloss_rows(a, x, y, w, h, strength, power=1.6):
    """A highlight fading down over h rows: the light on a glossy curved top."""
    for r in range(h):
        al = strength * (1 - r / h) ** power
        reg = a[y + r, x:x + w].astype(np.float64)
        a[y + r, x:x + w] = np.round(reg + (255 - reg) * al).astype(np.int32)


# ------------------------------------------------------------------------------------------
# Materials: translucent iMac plastic (coloured over a white inner shell, "ice" white) and
# bead-blasted aluminium. All tile-safe along whatever axis the app tiles a piece.
# ------------------------------------------------------------------------------------------


def surface(w, h, wy=0, wh=None, mat="body", struct=None, stripes=True, noise=True, glow=()):
    """A w x h float layer of the window's material. wy: the layer's first row within its
    window (pinstripe parity, gradient); wh: the window's height (None: no vertical gradient,
    for vertically tiled pieces); struct: an h x w 0..1 map of the inner parts seen through the
    plastic (iMac only)."""
    if imac():
        inner = np.full((h, w), 1.0)
        if struct is not None:
            inner = inner - 0.42 * struct
        if wh:
            rows = (wy + np.arange(h)) / wh
            inner = inner * (1 - 0.05 * rows)[:, None]
        col = np.asarray(T["ice"] if mat == "ice" else T["face"], dtype=np.float64)
        lay = inner[..., None] * col[None, None, :]
        if glow:
            # light passing through the thinner parts of the shell: broad soft bright patches
            X, Y = np.meshgrid(np.arange(w) + 0.5, wy + np.arange(h) + 0.5)
            g = np.zeros((h, w))
            for cx, cy, rx, ry, k in glow:
                g += k * np.exp(-(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2))
            g = np.clip(g, -0.5, 0.6)[..., None]
            lit = np.asarray(tint(T["C"], 0.45), dtype=np.float64)
            deep = np.asarray(shade(T["C"], 0.2), dtype=np.float64)
            lay = np.where(g > 0, lay + (lit - lay) * g, lay + (deep - lay) * (-g))
        if stripes:
            # the plastic's fine horizontal pinstripes
            k = 0.94 if mat == "body" else 0.965
            odd = ((wy + np.arange(h)) % 2 == 1)
            lay[odd] *= k
        return lay
    if wh:
        rows = vgrad(wh, [T["alu_top"], T["alu_bot"]])[wy:wy + h]
        lay = np.repeat(rows[:, None, :], w, axis=1)
    else:
        lay = np.empty((h, w, 3))
        lay[:] = lerp(T["alu_top"], T["alu_bot"], 0.45)
    if mat == "deep":
        lay = lay * 0.9
    if noise:
        # bead blasting: fine isotropic grain plus a faint mottle
        n = _rng.normal(0, 2.1, (h, w))
        m = _rng.normal(0, 1, (h, w))
        acc = np.zeros_like(m)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                acc += np.roll(np.roll(m, dy, 0), dx, 1)
        lay = lay + (n + acc * 0.35)[..., None]
    return lay


def put(a, x, y, lay, al=None):
    if al is None:
        a[y:y + lay.shape[0], x:x + lay.shape[1]] = np.round(lay).astype(np.int32)
    else:
        composite(a, x, y, al, lay)


def fill(a, x, y, w, h, wy=None, wh=None, mat="body", struct=None, stripes=True, glow=()):
    put(a, x, y, surface(w, h, y if wy is None else wy, wh, mat, struct, stripes, glow=glow))


def desat(a, x, y, w, h, t):
    reg = a[y:y + h, x:x + w].astype(np.float64)
    l = (0.299 * reg[..., 0] + 0.587 * reg[..., 1] + 0.114 * reg[..., 2])[..., None]
    a[y:y + h, x:x + w] = np.round(reg + (l - reg) * t).astype(np.int32)


def edge(a, x, y, w, h):
    """The window's outer rim: plastic's saturated edge / aluminium's diamond-cut chamfer."""
    rect(a, x, y, w, 1, T["rim_hi"])
    rect(a, x, y, 1, h, T["rim_hi"])
    rect(a, x, y + h - 1, w, 1, T["rim"])
    rect(a, x + w - 1, y, 1, h, T["rim"])


def struct_map(w, h, seed, items):
    """Inner parts seen through the plastic, drawn at 4x and softened: a 0..1 map."""
    S = 4
    im = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(im)
    for it in items:
        kind = it[0]
        if kind == "rect":
            _, x, y, rw, rh, v = it
            d.rectangle((x * S, y * S, (x + rw) * S - 1, (y + rh) * S - 1), outline=v, width=S)
        elif kind == "box":
            _, x, y, rw, rh, v = it
            d.rectangle((x * S, y * S, (x + rw) * S - 1, (y + rh) * S - 1), fill=v)
        elif kind == "ring":
            _, cx, cy, r, v = it
            d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), outline=v, width=S + 2)
        elif kind == "line":
            _, pts, v = it
            d.line([(px_ * S, py_ * S) for px_, py_ in pts], fill=v, width=S + 1)
    im = im.resize((w, h), Image.BOX)
    m = np.asarray(im, dtype=np.float64) / 255
    soft = m.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        soft += 0.5 * np.roll(np.roll(m, dy, 0), dx, 1)
    return np.clip(soft / 2.6, 0, 1)


# ------------------------------------------------------------------------------------------
# Pixel fonts
# ------------------------------------------------------------------------------------------

def G(*rows):
    return list(rows)


FONT5 = {
    "A": G(".##.", "#..#", "####", "#..#", "#..#"),
    "B": G("###.", "#..#", "###.", "#..#", "###."),
    "C": G(".###", "#...", "#...", "#...", ".###"),
    "D": G("###.", "#..#", "#..#", "#..#", "###."),
    "E": G("####", "#...", "###.", "#...", "####"),
    "F": G("####", "#...", "###.", "#...", "#..."),
    "G": G(".###", "#...", "#.##", "#..#", ".###"),
    "H": G("#..#", "#..#", "####", "#..#", "#..#"),
    "I": G("###", ".#.", ".#.", ".#.", "###"),
    "J": G("...#", "...#", "...#", "#..#", ".##."),
    "K": G("#..#", "#.#.", "##..", "#.#.", "#..#"),
    "L": G("#...", "#...", "#...", "#...", "####"),
    "M": G("#...#", "##.##", "#.#.#", "#...#", "#...#"),
    "N": G("#..#", "##.#", "#.##", "#..#", "#..#"),
    "O": G(".##.", "#..#", "#..#", "#..#", ".##."),
    "P": G("###.", "#..#", "###.", "#...", "#..."),
    "Q": G(".##.", "#..#", "#..#", "#.#.", ".#.#"),
    "R": G("###.", "#..#", "###.", "#.#.", "#..#"),
    "S": G(".###", "#...", ".##.", "...#", "###."),
    "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#..#", "#..#", "#..#", "#..#", ".##."),
    "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#...#", "#...#", "#.#.#", "##.##", "#...#"),
    "X": G("#..#", "#..#", ".##.", "#..#", "#..#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": G("####", "...#", ".##.", "#...", "####"),
    "0": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "1": G(".#.", "##.", ".#.", ".#.", "###"),
    "2": G("##.", "..#", ".#.", "#..", "###"),
    "3": G("##.", "..#", ".#.", "..#", "##."),
    "4": G("#.#", "#.#", "###", "..#", "..#"),
    "5": G("###", "#..", "##.", "..#", "##."),
    "6": G(".##", "#..", "##.", "#.#", ".#."),
    "7": G("###", "..#", ".#.", ".#.", ".#."),
    "8": G(".#.", "#.#", ".#.", "#.#", ".#."),
    "9": G(".#.", "#.#", ".##", "..#", "##."),
    '"': G("#.#", "#.#", "...", "...", "..."),
    "@": G(".##.", "#.##", "#.##", "#...", ".###"),
    "…": G(".....", ".....", ".....", ".....", "#.#.#"),
    ".": G(".", ".", ".", ".", "#"),
    ":": G(".", "#", ".", "#", "."),
    "(": G(".#", "#.", "#.", "#.", ".#"),
    ")": G("#.", ".#", ".#", ".#", "#."),
    "-": G("...", "...", "###", "...", "..."),
    "'": G("#", "#", ".", ".", "."),
    "!": G("#", "#", "#", ".", "#"),
    "_": G("....", "....", "....", "....", "####"),
    "+": G("...", ".#.", "###", ".#.", "..."),
    "\\": G("#..", "#..", ".#.", "..#", "..#"),
    "/": G("..#", "..#", ".#.", "#..", "#.."),
    "[": G("##", "#.", "#.", "#.", "##"),
    "]": G("##", ".#", ".#", ".#", "##"),
    "^": G(".#.", "#.#", "...", "...", "..."),
    "&": G(".#..", "#.#.", ".#..", "#.#.", ".#.#"),
    "%": G("#.#", "..#", ".#.", "#..", "#.#"),
    ",": G("..", "..", "..", ".#", "#."),
    "=": G("...", "###", "...", "###", "..."),
    "$": G(".###", "#.#.", ".##.", ".#.#", "###."),
    "#": G(".#.#", "####", ".#.#", "####", ".#.#"),
    "å": G(".##.", ".##.", "#..#", "####", "#..#"),
    "ö": G("#..#", ".##.", "#..#", "#..#", ".##."),
    "ä": G("#..#", ".##.", "#..#", "####", "#..#"),
    "?": G("###.", "...#", ".##.", "....", ".#.."),
    "*": G("#.#", ".#.", "###", ".#.", "#.#"),
    " ": G("...", "...", "...", "...", "..."),
}

TINY = {
    "A": G(".#.", "#.#", "###", "#.#", "#.#"),
    "B": G("##.", "#.#", "##.", "#.#", "##."),
    "C": G(".##", "#..", "#..", "#..", ".##"),
    "D": G("##.", "#.#", "#.#", "#.#", "##."),
    "E": G("###", "#..", "##.", "#..", "###"),
    "F": G("###", "#..", "##.", "#..", "#.."),
    "G": G(".##", "#..", "#.#", "#.#", ".##"),
    "H": G("#.#", "#.#", "###", "#.#", "#.#"),
    "I": G("###", ".#.", ".#.", ".#.", "###"),
    "K": G("#.#", "#.#", "##.", "#.#", "#.#"),
    "L": G("#..", "#..", "#..", "#..", "###"),
    "M": G("#.#", "###", "###", "#.#", "#.#"),
    "N": G("##.", "#.#", "#.#", "#.#", "#.#"),
    "O": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "P": G("##.", "#.#", "##.", "#..", "#.."),
    "Q": G(".#.", "#.#", "#.#", "##.", ".##"),
    "R": G("##.", "#.#", "##.", "#.#", "#.#"),
    "S": G(".##", "#..", ".#.", "..#", "##."),
    "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#.#", "#.#", "#.#", "#.#", "###"),
    "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#.#", "#.#", "###", "###", "#.#"),
    "X": G("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": G("###", "..#", ".#.", "#..", "###"),
    " ": G("..", "..", "..", "..", ".."),
}
for _c in "0123456789+-.":
    TINY[_c] = FONT5[_c]

# 7-row wordmark letters (cap height 7, x-height 5) for "iMac" and "MacBook Pro".
WORD = {
    "i": G("#", ".", "#", "#", "#", "#", "#"),
    "M": G("#.....#", "##...##", "#.#.#.#", "#..#..#", "#.....#", "#.....#", "#.....#"),
    "a": G(".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "c": G("....", "....", ".###", "#...", "#...", "#...", ".###"),
    "B": G("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "o": G(".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "k": G("#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#"),
    "P": G("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "r": G("...", "...", "#.#", "##.", "#..", "#..", "#.."),
    " ": G("..", "..", "..", "..", "..", "..", ".."),
}

# Clock digits: a bold rounded sans (2px strokes), 7 x 11 in the 9 x 13 cell.
DIGITS = {
    0: G(".#####.", "##...##", "##...##", "##..###", "##.#.##", "###..##", "##...##", "##...##", "##...##",
         "##...##", ".#####."),
    1: G("...##..", "..###..", ".####..", "...##..", "...##..", "...##..", "...##..", "...##..", "...##..",
         "...##..", ".######"),
    2: G(".#####.", "##...##", ".....##", ".....##", "....##.", "...##..", "..##...", ".##....", "##.....",
         "##.....", "#######"),
    3: G(".#####.", "##...##", ".....##", ".....##", "..####.", ".....##", ".....##", ".....##", ".....##",
         "##...##", ".#####."),
    4: G("....##.", "...###.", "..####.", ".##.##.", "##..##.", "##..##.", "#######", "....##.", "....##.",
         "....##.", "....##."),
    5: G("#######", "##.....", "##.....", "##.....", "######.", ".....##", ".....##", ".....##", ".....##",
         "##...##", ".#####."),
    6: G(".#####.", "##...##", "##.....", "##.....", "######.", "##...##", "##...##", "##...##", "##...##",
         "##...##", ".#####."),
    7: G("#######", ".....##", ".....##", "....##.", "....##.", "...##..", "...##..", "..##...", "..##...",
         "..##...", "..##..."),
    8: G(".#####.", "##...##", "##...##", "##...##", ".#####.", "##...##", "##...##", "##...##", "##...##",
         "##...##", ".#####."),
    9: G(".#####.", "##...##", "##...##", "##...##", "##...##", ".######", ".....##", ".....##", ".....##",
         "##...##", ".#####."),
}


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1, shadow=None, sh=(1, 1)):
    for c in s:
        if c not in font:
            continue
        g = font[c]
        if shadow is not None:
            for r, row in enumerate(g):
                for k, ch in enumerate(row):
                    if ch == "#":
                        px(a, x + k + sh[0], y + r + sh[1], shadow)
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col(r) if callable(col) else col)
        x += len(g[0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1, shadow=None, sh=(1, 1)):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow, sh)


def engraved(a, font, s, x, y, ink, gap=1, centre=False):
    """Text pressed into the surface: a light lip under the dark letters (aluminium), or a soft
    white sheen under them (plastic)."""
    lip = T["body_hi"] if not imac() else (255, 255, 255)
    if centre:
        x = x - text_w(font, s, gap) // 2
    draw_text(a, font, s, x, y, ink, gap, shadow=lip, sh=(0, 1))


# ------------------------------------------------------------------------------------------
# Logos
# ------------------------------------------------------------------------------------------

_RASTERS = {}


def raster(svg, name):
    if name not in _RASTERS:
        png = os.path.join(SCRATCH, name + "-400.png")
        if not os.path.exists(png):
            subprocess.run(["/usr/bin/rsvg-convert", "-h", "400", svg, "-o", png], check=True)
        _RASTERS[name] = Image.open(png).convert("RGBA")
    return _RASTERS[name]


def logo_alpha(svg, name, h):
    im = raster(svg, name).getchannel("A")
    w = max(1, round(im.width * h / im.height))
    al = np.asarray(im.resize((w, h), Image.BOX), dtype=np.float64) / 255
    return np.clip((al - 0.1) / 0.75, 0, 1)


def rainbow_logo(a, x, y, h=15):
    """The six-colour Apple logo: the shape's coverage at h rows, each row in the stripe colour
    found at its centre in the 400px raster (so the bands stay crisp at this size)."""
    src = raster(RAINBOW_SVG, "rainbow")
    al = logo_alpha(RAINBOW_SVG, "rainbow", h)
    arr = np.asarray(src, dtype=np.float64)
    rows = []
    for r in range(h):
        sy = int((r + 0.5) * src.height / h)
        band = arr[max(0, sy - 3):sy + 4]
        m = band[..., 3] > 200
        rows.append(tuple(int(v) for v in band[..., :3][m].mean(axis=0)) if m.any() else (117, 189, 33))
    # the logo's own six colours, a touch richer than the SVG's at this size
    composite(a, x, y, al, np.array(rows, dtype=np.float64))
    return al.shape[1]


def apple_alpha(h):
    return logo_alpha(APPLE_SVG, "apple", h)


# ------------------------------------------------------------------------------------------
# Shared pieces: keys, glass, plates, buttons
# ------------------------------------------------------------------------------------------


def key(a, x, y, w, h, pressed=False, r=None):
    """A key face over whatever is at (x, y): an ice-white translucent key (iMac) or a black
    chiclet key sunk into the aluminium (MacBook Pro). Returns the glyph's offset."""
    if imac():
        r = 4.0 if r is None else r
        # soft shadow under the key
        composite(a, x, y, rr_alpha(w, h, r) * 0.35, T["body_lo"])
        kh = h - 1
        top, bot = (T["key_top"], T["key_bot"]) if not pressed else (shade(T["key_bot"], 0.06), T["key_top"])
        shape(a, x, y + (1 if pressed else 0), w, kh, r, [top, bot], T["key_edge"])
        if not pressed:
            # glossy top sheen and a faint pinstripe through the ice
            al = rr_alpha(w - 4, max(1, kh // 2 - 1), r - 1.5)
            composite(a, x + 2, y + 1, al * 0.55, WHITE)
        o = 1 if pressed else 0
        for rr in range(2 + o, kh - 1 + o, 2):
            for cx in range(x + 2, x + w - 2):
                blend_px(a, cx, y + rr, T["key_bot"], 0.18)
        return o
    r = 2.6 if r is None else r
    # the well cut into the aluminium round the key
    composite(a, x, y, rr_alpha(w, h, r + 0.6), T["well"])
    composite(a, x, y, rr_alpha(w, h, r + 0.6, 0.8), shade(T["well"], 0.35))
    if pressed:
        shape(a, x + 1, y + 1, w - 2, h - 2, r, [(12, 12, 13), (20, 20, 22)], T["key_edge"])
        return 1
    shape(a, x + 1, y + 1, w - 2, h - 2, r, [T["key_top"], T["key_bot"]], T["key_edge"])
    rect(a, x + 1 + int(r), y + 2, w - 2 - 2 * int(r), 1, (66, 66, 70))
    return 0


def key_ink(pressed):
    return T["key_ink_on"] if pressed else T["key_ink"]


def led(a, x, y, on):
    """A 2x2 status light: the iMac's green power light / the caps-lock key's green LED."""
    c = T["led_on"] if on else T["led_off"]
    rect(a, x, y, 2, 2, c)
    if on:
        for dx, dy in ((-1, 0), (2, 0), (-1, 1), (2, 1), (0, -1), (1, -1), (0, 2), (1, 2)):
            blend_px(a, x + dx, y + dy, c, 0.35)
        px(a, x, y, tint(c, 0.6))


def glass(a, x, y, w, h, frame=3, r=3):
    """A display: a flat screen inside a frame (the iMac's CRT surround, darker than the plastic;
    the MacBook Pro's glossy black glass bezel)."""
    fx, fy, fw, fh = x - frame, y - frame, w + 2 * frame, h + 2 * frame
    if imac():
        composite(a, fx, fy, rr_alpha(fw, fh, r + frame), T["bezel"])
        composite(a, fx, fy, rr_alpha(fw, fh, r + frame) - rr_alpha(fw, fh, r + frame, 1.0), T["bezel_hi"])
    else:
        composite(a, fx, fy, rr_alpha(fw, fh, r + frame), T["bezel"])
        composite(a, fx, fy, rr_alpha(fw, fh, r + frame) - rr_alpha(fw, fh, r + frame, 1.0), (60, 62, 66))
    rect(a, x, y, w, h, T["disp"])
    rect(a, x, y, w, 1, lerp(T["disp"], T["bezel"], 0.5))


def bezel_gloss(a, x, y, w, h, frame=3):
    """The bezel's glossy reflection: a soft diagonal sheen over the frame band only."""
    fx, fy, fw, fh = x - frame, y - frame, w + 2 * frame, h + 2 * frame
    for yy in range(fy, fy + fh):
        for xx in range(fx, fx + fw):
            if x <= xx < x + w and y <= yy < y + h:
                continue
            d = (xx - fx) + 2.2 * (yy - fy)
            if 18 < d < 70:
                t = 0.10 * (1 - abs(d - 44) / 26)
                blend_px(a, xx, yy, (200, 205, 214), t)


def plate_col(i, h, lit):
    """Row i of an h-row title plate (rows 0 and h-1 are its edges)."""
    if imac():
        base = T["ice"] if lit else lerp(T["ice"], (200, 204, 208), 0.5)
        if i == 0:
            return lerp(base, T["rim"], 0.45)
        if i == h - 1:
            return lerp(base, WHITE, 0.6)
        c = lerp(WHITE, base, min(1.0, 0.45 + i / (h - 1)))
        return shade(c, 0.03) if i % 2 == 0 else c
    base = T["plate"] if lit else lerp(T["plate"], T["body"], 0.5)
    if i == 0:
        return shade(base, 0.22)
    if i == h - 1:
        return T["body_hi"]
    return base


def plate(a, x, y, w, lit, h=9):
    for i in range(h):
        rect(a, x, y + i, w, 1, plate_col(i, h, lit))


def plate_cap_left(a, x, y, lit, h=9):
    """4 columns: gap, rounded end, plate."""
    for i in range(h):
        c = plate_col(i, h, lit)
        edge_c = plate_col(0, h, lit)
        if i in (0, h - 1):
            continue
        rect(a, x + 2, y + i, 2, 1, c)
        px(a, x + 1, y + i, edge_c if 1 < i < h - 2 else lerp(edge_c, c, 0.5))
    rect(a, x + 2, y, 2, 1, plate_col(0, h, lit))
    rect(a, x + 2, y + h - 1, 2, 1, plate_col(h - 1, h, lit))
    px(a, x + 2, y, lerp(plate_col(0, h, lit), plate_col(1, h, lit), 0.5))


def plate_cap_right(a, x, y, lit, h=9):
    for i in range(h):
        c = plate_col(i, h, lit)
        edge_c = shade(plate_col(1, h, lit), 0.12) if not imac() else plate_col(h - 1, h, lit)
        if i in (0, h - 1):
            continue
        rect(a, x, y + i, 2, 1, c)
        px(a, x + 2, y + i, edge_c if 1 < i < h - 2 else lerp(edge_c, c, 0.5))
    rect(a, x, y, 2, 1, plate_col(0, h, lit))
    rect(a, x, y + h - 1, 2, 1, plate_col(h - 1, h, lit))


def title_ink(lit):
    return T["plate_ink"] if lit else T["plate_ink_dim"]


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: a round ice button (iMac) or a tiny black key (MacBook Pro)."""
    if imac():
        body = lerp(T["key_top"], T["key_bot"], 0.3) if not pressed else T["key_bot"]
        composite(a, x, y, disc_alpha(9, 9, 4.5, 4.5, 4.5), T["key_edge"])
        composite(a, x, y, disc_alpha(9, 9, 4.5, 4.5, 3.6), vgrad(9, [WHITE, body] if not pressed else
                                                                 [shade(body, 0.1), WHITE]))
        if not pressed:
            composite(a, x, y, ellipse_alpha(9, 9, 4.0, 2.6, 2.4, 1.3) * 0.7, WHITE)
        ink = T["key_ink"] if lit else lerp(T["key_ink"], body, 0.5)
        if pressed:
            ink = T["key_ink_on"]
    else:
        face = [(46, 46, 49), (24, 24, 26)] if not pressed else [(12, 12, 13), (20, 20, 22)]
        composite(a, x, y, rr_alpha(9, 9, 2.4), T["well"])
        shape(a, x, y, 9, 9, 2.0, face, T["key_edge"])
        ink = (236, 237, 240) if lit else (150, 152, 156)
        if pressed:
            ink = WHITE
    X, Y = x, y
    if kind == "options":
        rect(a, X + 3, Y + 3, 3, 3, ink)
        for dx, dy in ((3, 3), (5, 3), (3, 5), (5, 5)):
            blend_px(a, X + dx, Y + dy, ink, -0.0)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 3, 5, 1, ink)
        rect(a, X + 2, Y + 5, 5, 1, ink)
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


def tri_right(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x, y + r, n, 1, col)


def tri_left(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x + half + 1 - n, y + r, n, 1, col)


def transport_icon(a, kind, cx, cy, ink):
    if kind == "previous":
        rect(a, cx - 5, cy - 3, 1, 7, ink)
        tri_left(a, cx - 4, cy - 3, 7, ink)
        tri_left(a, cx, cy - 3, 7, ink)
    elif kind == "play":
        tri_right(a, cx - 2, cy - 4, 9, ink)
    elif kind == "pause":
        rect(a, cx - 3, cy - 3, 2, 7, ink)
        rect(a, cx + 1, cy - 3, 2, 7, ink)
    elif kind == "stop":
        rect(a, cx - 3, cy - 3, 6, 6, ink)
    elif kind == "next":
        tri_right(a, cx - 4, cy - 3, 7, ink)
        tri_right(a, cx, cy - 3, 7, ink)
        rect(a, cx + 4, cy - 3, 1, 7, ink)
    elif kind == "eject":
        for r in range(4):
            rect(a, cx - r, cy - 4 + r, 2 * r + 1, 1, ink)
        rect(a, cx - 3, cy + 1, 7, 2, ink)


def mini_transport_icon(a, kind, x, y, ink):
    cx, cy = x + 5, y + 5
    if kind == "previous":
        rect(a, cx - 3, cy - 2, 1, 5, ink)
        tri_left(a, cx - 2, cy - 2, 5, ink)
        tri_left(a, cx + 1, cy - 2, 5, ink)
    elif kind == "play":
        tri_right(a, cx - 1, cy - 3, 7, ink)
    elif kind == "pause":
        rect(a, cx - 2, cy - 2, 2, 5, ink)
        rect(a, cx + 1, cy - 2, 2, 5, ink)
    elif kind == "stop":
        rect(a, cx - 2, cy - 2, 5, 5, ink)
    elif kind == "next":
        tri_right(a, cx - 3, cy - 2, 5, ink)
        tri_right(a, cx, cy - 2, 5, ink)
        rect(a, cx + 3, cy - 2, 1, 5, ink)
    elif kind == "eject":
        for r in range(3):
            rect(a, cx - r, cy - 3 + r, 2 * r + 1, 1, ink)
        rect(a, cx - 2, cy + 1, 5, 1, ink)


def puck(a, x, y, w, h, pressed):
    """The iMac's round "hockey puck" USB mouse, seen from above, as the play button: a
    translucent coloured disc, its darker button half behind a seam, a gloss spot."""
    C = T["C"]
    cx, cy, R = w / 2, h / 2, 8.6
    body = C if not pressed else shade(C, 0.18)
    composite(a, x, y, disc_alpha(w, h, cx + 0.5, cy + 0.8, R) * 0.4, shade(C, 0.6))   # shadow
    composite(a, x, y, disc_alpha(w, h, cx, cy, R), shade(C, 0.45))                     # rim
    composite(a, x, y, disc_alpha(w, h, cx, cy, R - 1.0),
              vgrad(h, [tint(body, 0.55), tint(body, 0.15), body, shade(body, 0.1)]))
    # the button: the far half of the puck, a shade deeper, behind a seam
    X, Y = _grid(w, h, 4)
    disc = (X - cx) ** 2 + (Y - cy) ** 2 <= (R - 1.0) ** 2
    sy = cy - 1.5
    btn = (disc & (Y < sy)).reshape(h, 4, w, 4).mean(axis=(1, 3))
    composite(a, x, y, btn * 0.35, shade(body, 0.3))
    seam = (disc & (np.abs(Y - sy) < 0.5)).reshape(h, 4, w, 4).mean(axis=(1, 3))
    composite(a, x, y, seam * 0.9, shade(C, 0.5))
    # the white inner shell showing through round the edge of the translucent body
    ring = np.clip(disc_alpha(w, h, cx, cy, R - 1.2) - disc_alpha(w, h, cx, cy, R - 2.2), 0, 1)
    composite(a, x, y, ring * 0.3, WHITE)
    if not pressed:
        composite(a, x, y, ellipse_alpha(w, h, cx - 2.6, cy - 5.0, 3.4, 1.4) * 0.8, WHITE)
    o = 1 if pressed else 0
    tri_right(a, 11 + o, int(cy) - 2 + o, 7, shade(C, 0.6))
    tri_right(a, 10 + o, int(cy) - 3 + o, 7, WHITE)


def cell_bg(src, x, y, w, h):
    return src[y:y + h, x:x + w].copy()


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters, bg):
    a = bg.copy()
    if imac():
        composite(a, 0, 0, rr_alpha(8, 43, 3.0), T["key_edge"])
        composite(a, 0, 0, rr_alpha(8, 43, 3.0, 1.0), vgrad(43, [T["key_top"], T["key_bot"]]))
    else:
        composite(a, 0, 0, rr_alpha(8, 43, 2.5), T["well"])
        composite(a, 0, 0, rr_alpha(8, 43, 2.5, 1.0), vgrad(43, [(40, 40, 43), (22, 22, 24)]))
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        gy = y + (h - 5) // 2
        if imac():
            ink = shade(T["C"], 0.15) if on else lerp(T["key_ink"], T["key_bot"], 0.45)
            if on:
                rect(a, 1, y, 6, h, tint(T["C"], 0.65))
        else:
            ink = WHITE if on else (120, 122, 126)
            if on:
                rect(a, 1, y, 6, h, (60, 62, 66))
        draw_text(a, TINY, letter, 2, gy, ink)
    return a


def main_titlebar(lit):
    a = new(275, 14)
    fill(a, 0, 0, 275, 14, 0, 116, glow=MAIN_GLOW)
    if imac():
        gloss_rows(a, 1, 1, 273, 7, 0.55)
        if not lit:
            desat(a, 0, 0, 275, 14, 0.45)
    else:
        rect(a, 0, 13, 275, 1, shade(T["body"], 0.12))
    rect(a, 0, 0, 275, 1, T["rim_hi"])
    rect(a, 0, 0, 1, 14, T["rim_hi"])
    rect(a, 274, 0, 1, 14, T["rim"])
    word = T["title_word"]
    ww = text_w(WORD, word)
    wx = (275 - ww) // 2
    if imac():
        # the wordmark on an ice capsule
        pw = ww + 16
        px0 = (275 - pw) // 2
        ice = T["ice"] if lit else lerp(T["ice"], (200, 204, 208), 0.5)
        composite(a, px0, 2, rr_alpha(pw, 11, 5.5), T["rim"] if lit else (140, 144, 148))
        composite(a, px0, 2, rr_alpha(pw, 11, 5.5, 1.0), vgrad(11, [WHITE, ice, lerp(ice, WHITE, 0.4)]))
        composite(a, px0 + 3, 3, rr_alpha(pw - 6, 4, 2.0) * 0.6, WHITE)
        draw_text(a, WORD, word, wx, 4, T["plate_ink"] if lit else (150, 154, 158))
    else:
        engraved(a, WORD, word, wx, 3, (96, 99, 105) if lit else (156, 159, 164))
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar(main):
    a = new(344, 87)
    fill(a, 0, 0, 344, 87, 0, None)
    for kind, x, y, py_ in [("options", 0, 0, 9), ("minimize", 9, 0, 9), ("close", 18, 0, 9)]:
        b = cell_bg(main, {"options": 6, "minimize": 244, "close": 264}[kind], 3, 9, 9)
        mini_button(b, 0, 0, kind, True)
        a[y:y + 9, x:x + 9] = b
        b = cell_bg(main, {"options": 6, "minimize": 244, "close": 264}[kind], 3, 9, 9)
        mini_button(b, 0, 0, kind, True, pressed=True)
        a[py_:py_ + 9, x:x + 9] = b
    b = cell_bg(main, 254, 3, 9, 9)
    mini_button(b, 0, 0, "shade", True)
    a[18:27, 0:9] = b
    b = cell_bg(main, 254, 3, 9, 9)
    mini_button(b, 0, 0, "shade", True, pressed=True)
    a[18:27, 9:18] = b
    a[0:14, 27:302] = main_titlebar(True)
    a[15:29, 27:302] = main_titlebar(False)
    a[29:43, 27:302] = main_titlebar(True)
    a[42:56, 27:302] = main_titlebar(False)
    bg = cell_bg(main, 10, 22, 8, 43)
    unlit = clutter_bar("", bg)
    lit = clutter_bar("OAIDV", bg)
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = lit[y:y + h]
    return a


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116)
# ------------------------------------------------------------------------------------------

LEFT_SCREEN = (21, 20, 84, 43)
RIGHT_SCREEN = (109, 21, 160, 33)


def main_struct():
    """What shows through the coloured plastic of the iMac's lower half: the CRT's yoke ring, a
    logic board with its chips, screw bosses, a ribbon cable, ribs moulded inside the shell."""
    items = [
        ("line", [(4, 84), (270, 84)], 150),
        ("line", [(4, 108), (270, 108)], 110),
        ("ring", 8, 78, 3, 255), ("ring", 266, 78, 3, 255), ("ring", 8, 103, 3, 255),
        ("ring", 266, 103, 3, 255),
        ("rect", 150, 74, 118, 36, 200),
        ("box", 160, 77, 14, 8, 130), ("box", 178, 77, 22, 8, 130), ("box", 240, 76, 22, 10, 140),
        ("box", 206, 77, 26, 6, 100),
        ("line", [(150, 92), (132, 92), (126, 100), (126, 112)], 170),
        ("line", [(152, 95), (134, 95), (129, 102), (129, 112)], 120),
        ("rect", 10, 88, 2, 22, 120), ("rect", 140, 76, 2, 34, 120),
    ]
    for gx in range(20, 140, 12):
        items.append(("line", [(gx, 109), (gx, 113)], 120))
    return struct_map(275, 116, 7, items)


MAIN_GLOW = [(60, 100, 90, 14, 0.35), (230, 112, 70, 10, -0.35), (140, 72, 120, 4, 0.2), (6, 60, 8, 60, -0.3),
             (270, 60, 8, 60, -0.3)]
EQ_GLOW = [(6, 60, 8, 60, -0.3), (270, 60, 8, 60, -0.3)]


def main_plain():
    """The main window without its titlebar: the base the sheets' cell backgrounds come from."""
    a = new(275, 116)
    if imac():
        st = main_struct()
        fill(a, 0, 0, 275, 116, 0, 116, struct=st, glow=MAIN_GLOW)
        # glossy curved highlight on the lower shell
        composite(a, 0, 70, ellipse_alpha(275, 46, 70, -6, 150, 22) * 0.22, WHITE)
        # the ice panel round the screens
        put(a, 4, 15, surface(267, 56, 15, 116, "ice"), rr_alpha(267, 56, 6))
        composite(a, 4, 15, rr_alpha(267, 56, 6) - rr_alpha(267, 56, 6, 1.0), lerp(T["ice"], T["rim"], 0.5))
        composite(a, 4, 15, (rr_alpha(267, 56, 6, 1.0) - rr_alpha(267, 56, 6, 2.0)), WHITE)
    else:
        fill(a, 0, 0, 275, 116, 0, 116)
    edge(a, 0, 0, 275, 116)
    return a


def screens(a):
    lx, ly, lw, lh = LEFT_SCREEN
    rx, ry, rw, rh = RIGHT_SCREEN
    glass(a, lx, ly, lw, lh)
    glass(a, rx, ry, rw, rh)
    # one L-shaped piece of glass: bridge the frames between the two screens
    rect(a, lx + lw, ry - 3, rx - lx - lw, rh + 6, T["bezel"])
    rect(a, lx + lw, ry - 3, rx - lx - lw, 1, T["bezel_hi"] if imac() else (60, 62, 66))
    rect(a, lx + lw, ry + rh + 2, rx - lx - lw, 1, T["bezel_hi"] if imac() else (60, 62, 66))
    rect(a, lx + lw - 1, ry, rx - lx - lw + 2, rh, T["bezel"])
    if not imac():
        bezel_gloss(a, lx, ly, lw, lh)
        bezel_gloss(a, rx, ry, rw, rh)
        # the iSight camera in the top of the bezel
        cx = rx + rw // 2
        rect(a, cx - 1, ry - 2, 2, 1, (34, 36, 42))
        px(a, cx, ry - 2, (58, 64, 80))
    # a faint rule between the title row and the info row
    rect(a, rx + 2, 38, rw - 4, 1, lerp(T["disp"], T["ink"], 0.1))


def make_main():
    a = main_plain()
    a[0:14, :] = main_titlebar(True)
    screens(a)
    # colon between minutes and seconds
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, T["ink"])
    draw_text(a, TINY, "KBPS", 129, 44, T["ink_mid"])
    draw_text(a, TINY, "KHZ", 169, 44, T["ink_mid"])
    # clutterbar (drawn from titlebar.bmp too)
    a[22:65, 10:18] = clutter_bar("", a[22:65, 10:18])
    # seek slot: the iMac's CD drive slot / the MacBook Pro's slot-loading SuperDrive
    slot(a, 16, 72)
    # the logo in the About spot
    if imac():
        w = logo_alpha(RAINBOW_SVG, "rainbow", 15).shape[1]
        rainbow_logo(a, 253 + (13 - w) // 2, 91)
    else:
        glow_logo(a, 253, 91)
    return a


def glow_logo(a, x, y):
    """The lid's backlit Apple logo: white, a soft halo, a thin shadow ring to lift it off the
    pale aluminium."""
    al = apple_alpha(15)
    h, w = al.shape
    ox = x + (13 - w) // 2
    pad = 3
    big = np.zeros((h + 2 * pad, w + 2 * pad))
    big[pad:pad + h, pad:pad + w] = al
    ring = np.zeros_like(big)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ring = np.maximum(ring, np.roll(np.roll(big, dy, 0), dx, 1))
    halo = big.copy()
    for _ in range(3):
        acc = np.zeros_like(halo)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                acc += np.roll(np.roll(halo, dy, 0), dx, 1)
        halo = acc / 9
    composite(a, ox - pad, y - pad, np.clip(ring - big, 0, 1) * 0.55, (120, 124, 132))
    composite(a, ox - pad, y - pad, np.clip(halo * 0.9, 0, 0.7), (250, 252, 255))
    composite(a, ox, y, al, vgrad(h, [(255, 255, 255), (236, 240, 246)]))


def slot(a, x, y):
    """A 248 x 10 drive slot (the seek bar's track)."""
    if imac():
        composite(a, x, y + 2, rr_alpha(248, 6, 3), shade(T["C"], 0.45))
        composite(a, x, y + 2, rr_alpha(248, 6, 3, 1.0), vgrad(4, [lerp(T["bezel"], (0, 0, 0), 0.4), T["bezel"]])
                  if False else lerp(T["bezel"], (0, 0, 0), 0.3))
        rect(a, x + 4, y + 8, 240, 1, tint(T["face"], 0.5))
        rect(a, x + 4, y + 4, 240, 1, lerp(T["bezel"], T["C"], 0.25))
    else:
        composite(a, x, y + 3, rr_alpha(248, 4, 2), (20, 20, 22))
        rect(a, x + 2, y + 3, 244, 1, (8, 8, 9))
        rect(a, x + 3, y + 7, 242, 1, T["body_hi"])


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36)
# ------------------------------------------------------------------------------------------

CB = [("previous", 0, 23, 18, 16, 88), ("play", 23, 23, 18, 39, 88), ("pause", 46, 23, 18, 62, 88),
      ("stop", 69, 23, 18, 85, 88), ("next", 92, 22, 18, 108, 88)]


def make_cbuttons(main):
    a = new(136, 36)
    for kind, x, w, h, mx, my in CB:
        for pressed, y in ((False, 0), (True, 18)):
            c = cell_bg(main, mx, my, w, h)
            if imac() and kind == "play":
                puck(c, 0, 0, w, h, pressed)
            else:
                o = key(c, 0, 0, w, h, pressed)
                transport_icon(c, kind, w // 2 + o, h // 2 - (1 if imac() else 0) + o, key_ink(pressed))
            a[y:y + h, x:x + w] = c
    for pressed, y in ((False, 0), (True, 16)):
        c = cell_bg(main, 136, 89, 22, 16)
        o = key(c, 0, 0, 22, 16, pressed)
        transport_icon(c, "eject", 11 + o, 8 + o - (1 if imac() else 0), key_ink(pressed))
        a[y:y + 16, 114:136] = c
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle(bg, w, h, label, on, pressed, font=TINY):
    """A key with a label and a green status light (the iMac's power light; the caps-lock LED)."""
    c = bg.copy()
    o = key(c, 0, 0, w, h, pressed, r=3.0 if imac() else 2.4)
    ink = key_ink(pressed)
    tw = text_w(font, label)
    kh = h - 1 if imac() else h
    ty = (kh - 5) // 2 + o
    lx = 4 + o
    led(c, lx, ty + 1 + (1 if h >= 15 else 0) - (0 if h >= 15 else 0), on)
    tx = lx + 3 + max(1, (w - lx - 3 - 2 - tw) // 2)
    draw_text(c, font, label, tx, ty + (1 if h >= 15 else 0) - (1 if imac() and h >= 15 else 0) +
              (0 if h >= 15 else 0), ink)
    return c


def make_shufrep(main):
    a = new(92, 85)
    fill(a, 0, 0, 92, 85, 0, None)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = toggle(cell_bg(main, 210, 89, 28, 15), 28, 15, "REP", on, pressed)
        a[y:y + 15, 28:75] = toggle(cell_bg(main, 164, 89, 47, 15), 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed, mx in [(0, "EQ", False, 219), (23, "PL", False, 242), (46, "EQ", True, 219),
                                  (69, "PL", True, 242)]:
        a[61:73, x:x + 23] = toggle(cell_bg(main, mx, 58, 23, 12), 23, 12, label, False, pressed)
        a[73:85, x:x + 23] = toggle(cell_bg(main, mx, 58, 23, 12), 23, 12, label, True, pressed)
    return a


# ------------------------------------------------------------------------------------------
# monoster, playpaus, numbers, nums_ex, text
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T["disp"])
    for y, on in ((0, True), (12, False)):
        col = T["ink"] if on else T["ink_dim"]
        text_center(a, TINY, "STEREO", 14, y + 4, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 4, col)
    return a


def make_playpaus():
    a = new(48, 9, T["disp"])
    ink = T["ink"]
    tri_right(a, 2, 1, 7, ink)
    rect(a, 9 + 2, 1, 2, 7, ink)
    rect(a, 9 + 5, 1, 2, 7, ink)
    rect(a, 18 + 2, 2, 5, 5, ink)
    rect(a, 36, 0, 3, 9, T["disp"])
    rect(a, 39 + 1, 3, 1, 3, T["led_on"])
    return a


def digit(a, x, y, n, col):
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + 1 + c, y + 1 + r, col)


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["disp"])
    for n in range(10):
        digit(a, 9 * n, 0, n, T["ink"])
    if ex:
        rect(a, 99 + 2, 5, 5, 2, T["ink"])
    else:
        # the minus the app reads at (20, 6, 5, 1) when there's no nums_ex: digit 2's middle
        pass
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, T["disp"])
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key_ = ch if ch in FONT5 else ch.upper()
            g = FONT5[key_]
            x0 = col * 5 + (1 if len(g[0]) <= 3 else 0)
            if len(g[0]) == 5:
                x0 = col * 5
            draw_text(a, FONT5, key_, x0, row * 6, T["ink"])
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def thumb(a, x, y, w, h, selected, grip="v"):
    """Slider thumbs: a translucent coloured gumdrop (iMac) or a small black key (MacBook Pro)."""
    if imac():
        C = T["C"]
        body = tint(C, 0.1) if not selected else shade(C, 0.1)
        r = min(w, h) / 2
        composite(a, x, y, rr_alpha(w, h, r), shade(C, 0.42))
        composite(a, x, y, rr_alpha(w, h, r, 1.0), vgrad(h, [tint(body, 0.45), body, shade(body, 0.12)]))
        composite(a, x + 2, y + 1, rr_alpha(w - 4, max(2, h // 2 - 1), r - 1.5) * (0.6 if not selected else 0.35),
                  WHITE)
        if grip == "v":
            cx = x + w // 2
            rect(a, cx, y + h // 2, 1, max(1, h // 2 - 2), shade(C, 0.35))
        return
    face = [(48, 48, 51), (22, 22, 24)] if not selected else [(16, 16, 17), (30, 30, 32)]
    shape(a, x, y, w, h, min(2.5, h / 2), face, (6, 6, 7))
    if not selected:
        rect(a, x + 2, y + 1, w - 4, 1, (70, 70, 74))
    cx, cy = x + w // 2, y + h // 2
    if grip == "v":
        rect(a, cx - (0 if w % 2 else 1), y + 3, 1 if w % 2 else 2, h - 6, (210, 212, 216))
    else:
        rect(a, x + 3, cy, w - 6, 1, (210, 212, 216))


def make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    bg = cell_bg(main, 120, 72, 29, 10)
    for x, sel in ((248, False), (278, True)):
        c = bg.copy()
        thumb(c, 0, 0, 29, 10, sel)
        if imac():
            # a disc peeking out of the slot
            composite(c, 0, 0, disc_alpha(29, 10, 14.5, 5, 3.2), (226, 230, 236))
            composite(c, 0, 0, disc_alpha(29, 10, 14.5, 5, 1.2), shade(T["C"], 0.3))
        a[0:10, x:x + 29] = c
    a[0:10, 277] = a[0:10, 276]
    return a


def groove(a, x, y, w, level=None, centre=None):
    """A 5-row recessed track with a fill: from the left up to `level` (a fraction), or out from
    `centre` by `level` columns either way."""
    composite(a, x, y, rr_alpha(w, 5, 2.5), shade(T["groove"], 0.2))
    composite(a, x, y, rr_alpha(w, 5, 2.5, 0.8), T["groove"])
    rect(a, x + 2, y + 4, w - 4, 1, lerp(T["groove"], T["body_hi"], 0.25))
    if level is None:
        return
    if centre is None:
        fw = max(0, round(level * (w - 2)))
        if fw:
            al = rr_alpha(fw + 1, 3, 1.5)
            composite(a, x + 1, y + 1, al, vgrad(3, [T["fill_hi"], T["fill"], shade(T["fill"], 0.1)]))
    else:
        reach = level
        x0 = centre - reach
        fw = 2 * reach + 1
        if fw > 0:
            composite(a, x0, y + 1, rr_alpha(fw, 3, 1.2), vgrad(3, [T["fill_hi"], T["fill"], shade(T["fill"], 0.1)]))


def slider_thumbs(a, bg):
    for x, sel in ((0, True), (15, False)):
        c = bg.copy()
        thumb(c, 0, 0, 14, 11, sel)
        a[422:433, x:x + 14] = c


def make_volume(main):
    a = new(68, 433)
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        groove(a, 1, y + 4, 66, level=(i + 1) / 28)
    slider_thumbs(a, cell_bg(main, 140, 58, 14, 11))
    return a


def make_balance(main):
    a = new(68, 433)
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        a[y:y + 15, 0:9] = main[57:72, 177:186]
        a[y:y + 15, 47:68] = main[57:72, 186:207]
        groove(a, 10, y + 4, 36, level=round(16 * i / 27), centre=28)
        rect(a, 28, y + 2, 1, 1, T["label"])
    slider_thumbs(a, cell_bg(main, 190, 58, 14, 11))
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def bar14(lit, title):
    a = new(275, 14)
    fill(a, 0, 0, 275, 14, 0, 116, glow=EQ_GLOW)
    if imac():
        gloss_rows(a, 1, 1, 273, 7, 0.55)
        if not lit:
            desat(a, 0, 0, 275, 14, 0.45)
    else:
        rect(a, 0, 13, 275, 1, shade(T["body"], 0.12))
    rect(a, 0, 0, 275, 1, T["rim_hi"])
    rect(a, 0, 0, 1, 14, T["rim_hi"])
    rect(a, 274, 0, 1, 14, T["rim"])
    tw = text_w(FONT5, title)
    pw = tw + 10
    px0 = (275 - pw) // 2
    plate_cap_left(a, px0 - 4, 2, lit, 10)
    plate(a, px0, 2, pw, lit, 10)
    plate_cap_right(a, px0 + pw, 2, lit, 10)
    draw_text(a, FONT5, title, px0 + 5, 4, title_ink(lit))
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_window():
    a = new(275, 116)
    if imac():
        st = struct_map(275, 116, 3, [("ring", 9, 108, 3, 255), ("ring", 266, 108, 3, 255),
                                      ("line", [(4, 113), (270, 113)], 120)])
        fill(a, 0, 0, 275, 116, 0, 116, struct=st, glow=EQ_GLOW)
        put(a, 4, 15, surface(267, 97, 15, 116, "ice"), rr_alpha(267, 97, 6))
        composite(a, 4, 15, rr_alpha(267, 97, 6) - rr_alpha(267, 97, 6, 1.0), lerp(T["ice"], T["rim"], 0.5))
        composite(a, 4, 15, rr_alpha(267, 97, 6, 1.0) - rr_alpha(267, 97, 6, 2.0), WHITE)
    else:
        fill(a, 0, 0, 275, 116, 0, 116)
        # the slider bay: a shallow recess in the aluminium
        composite(a, 15, 35, rr_alpha(247, 70, 4), shade(T["body"], 0.18))
        put(a, 16, 36, surface(245, 68, 36, 116, "deep"), rr_alpha(245, 68, 3.5))
        rect(a, 19, 104, 239, 1, T["body_hi"])
    edge(a, 0, 0, 275, 116)
    return a


def eq_slider_frame(a, x, y, n, bg):
    a[y:y + 63, x:x + 14] = bg
    v = n / 27
    # vertical groove 5 wide, rows 2..60, filled from the bottom
    composite(a, x + 4, y + 2, rr_alpha(5, 59, 2.5), shade(T["groove"], 0.2))
    composite(a, x + 4, y + 2, rr_alpha(5, 59, 2.5, 0.8), T["groove"])
    top = round((1 - v) * 51) + 6
    hgt = 60 - top
    if hgt > 0:
        g = np.array([ramp([T["fill_hi"], T["fill"]], 0) for _ in range(hgt)], dtype=np.float64)
        col = np.array([lerp(T["fill_hi"], T["fill"], min(1, r / 4)) for r in range(hgt)], dtype=np.float64)
        composite(a, x + 5, y + top, rr_alpha(3, hgt, 1.5), col)
    # the zero mark
    rect(a, x + 1, y + 31, 2, 1, T["label_dim"])
    rect(a, x + 11, y + 31, 2, 1, T["label_dim"])


def make_eqmain():
    a = new(275, 315)
    fill(a, 0, 0, 275, 315, 0, None)
    win = eq_window()
    a[0:116] = win
    a[0:14, :] = bar14(True, "EQUALIZER")
    # graph screen
    glass(a, 86, 17, 113, 19, frame=2, r=2)
    if not imac():
        bezel_gloss(a, 86, 17, 113, 19, frame=2)
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, T["label"])
    bg = win[38:101, 78:92].copy()
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14, bg)
    text_center(a, TINY, "PREAMP", 28, 106, T["label"])
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, T["label"])

    # under the window
    c = cell_bg(win, 264, 3, 9, 9)
    c[:] = bar14(True, "EQUALIZER")[3:12, 264:273]
    mini_button(c, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = c
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        a[119:131, x:x + w] = toggle(cell_bg(win, 14 if label == "ON" else 40, 18, w, 12), w, 12, label, on, pressed)
    a[134:148, :] = bar14(True, "EQUALIZER")
    a[149:163, :] = bar14(False, "EQUALIZER")
    for y, sel in ((164, False), (176, True)):
        c = cell_bg(win, 80, 60, 11, 11)
        thumb(c, 0, 0, 11, 11, sel, grip="h")
        a[y:y + 11, 0:11] = c
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n, bg)
    for y, pressed in ((164, False), (176, True)):
        c = cell_bg(win, 217, 18, 44, 12)
        o = key(c, 0, 0, 44, 12, pressed, r=3.0 if imac() else 2.4)
        text_center(c, TINY, "PRESETS", 22 + o, (3 if imac() else 4) + o, key_ink(pressed))
        a[y:y + 12, 224:268] = c
    # graph background, the line's colours, the preamp line
    rect(a, 0, 294, 113, 19, T["disp"])
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, T["ink_dim"])
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, lerp(T["disp"], T["ink"], 0.3))
    for r in range(19):
        px(a, 115, 294 + r, ramp(T["vis_spec"][:4], r / 18))
    for x in range(113):
        px(a, x, 314, T["ink_mid"] if x % 3 != 2 else T["disp"])
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

PLATE_Y = 3
BZ = 17   # the screen's bezel starts at this row of a 20px bar


def bar20(w, lit):
    a = new(w, 20)
    fill(a, 0, 0, w, 20, 0, None)
    if imac():
        gloss_rows(a, 0, 1, w, 9, 0.5)
        if not lit:
            desat(a, 0, 0, w, 20, 0.45)
    rect(a, 0, 0, w, 1, T["rim_hi"])
    return a


def bezel_rows(t, x0, x1, y0, y1):
    rect(t, x0, y0, x1 - x0, y1 - y0, T["bezel"])


def make_pledit():
    a = new(280, 186)
    fill(a, 0, 0, 280, 186, 0, None)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit)
        bezel_rows(t, 0, 25, BZ, 20)
        rect(t, 0, BZ, 25, 1, T["bezel_hi"])
        a[y:y + 20, 127:152] = t
        # top-left corner
        t = bar20(25, lit)
        rect(t, 0, 0, 1, 20, T["rim_hi"])
        bezel_rows(t, 9, 25, BZ, 20)
        rect(t, 9, BZ, 16, 1, T["bezel_hi"])
        rect(t, 9, BZ, 1, 3, T["bezel_hi"])
        a[y:y + 20, 0:25] = t
        # title
        t = bar20(100, lit)
        bezel_rows(t, 0, 100, BZ, 20)
        rect(t, 0, BZ, 100, 1, T["bezel_hi"])
        title = "PLAYLIST"
        pw = 60
        plate_cap_left(t, 50 - pw // 2 - 4, PLATE_Y, lit)
        plate(t, 50 - pw // 2, PLATE_Y, pw, lit)
        plate_cap_right(t, 50 + pw // 2, PLATE_Y, lit)
        text_center(t, FONT5, title, 50, PLATE_Y + 2, title_ink(lit))
        a[y:y + 20, 26:126] = t
        # top-right corner: close button, the scroll groove's top
        t = bar20(25, lit)
        rect(t, 24, 0, 1, 20, T["rim"])
        bezel_rows(t, 0, 20, BZ, 20)
        rect(t, 0, BZ, 20, 1, T["bezel_hi"])
        rect(t, 19, BZ, 1, 3, T["bezel_hi"])
        rect(t, 10, BZ + 1, 8, 2, lerp(T["bezel"], (0, 0, 0), 0.35))
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    # left side tile: rim, surface, bezel
    t = new(12, 29)
    fill(t, 0, 0, 12, 29, 0, None, stripes=False)
    rect(t, 0, 0, 1, 29, T["rim_hi"])
    rect(t, 9, 0, 3, 29, T["bezel"])
    rect(t, 9, 0, 1, 29, T["bezel_hi"])
    a[42:71, 0:12] = t
    # right side tile: bezel with the scroll groove (cols 5..12), surface, rim
    t = new(20, 29)
    fill(t, 0, 0, 20, 29, 0, None, stripes=False)
    rect(t, 0, 0, 15, 29, T["bezel"])
    rect(t, 14, 0, 1, 29, T["bezel_hi"])
    rect(t, 5, 0, 8, 29, lerp(T["bezel"], (0, 0, 0), 0.35))
    rect(t, 8, 0, 2, 29, lerp(T["bezel"], T["disp"], 0.3))
    rect(t, 19, 0, 1, 29, T["rim"])
    a[42:71, 31:51] = t
    # close pressed, scroll handles
    c = bar20(25, True)[3:12, 14:23].copy()
    mini_button(c, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = c
    for x, sel in ((52, False), (61, True)):
        c = np.zeros((18, 8, 3), dtype=np.int32)
        c[:] = lerp(T["bezel"], (0, 0, 0), 0.35)
        thumb(c, 0, 0, 8, 18, sel, grip="h")
        a[53:71, x:x + 8] = c

    def bottom_base(w):
        t = new(w, 38)
        items = [("line", [(0, 31), (w, 31)], 140)]
        if w > 100:
            items += [("ring", 5, 30, 2, 255), ("ring", w - 6, 30, 2, 255), ("rect", 12, 5, w - 24, 26, 110)]
        fill(t, 0, 0, w, 38, 0, 38, struct=struct_map(w, 38, 0, items))
        if imac():
            gloss_rows(t, 0, 3, w, 6, 0.25)
        rect(t, 0, 37, w, 1, T["rim"])
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, T["rim_hi"])
    bezel_rows(t, 9, 125, 0, 3)
    rect(t, 9, 0, 1, 3, T["bezel_hi"])
    rect(t, 10, 2, 115, 1, T["bezel_hi"])
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        o = key(t, bx, 8, 22, 18, False)
        text_center(t, TINY, lbl, bx + 11, 14 if imac() else 15, key_ink(False))
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, T["rim"])
    bezel_rows(t, 0, 145, 0, 3)
    rect(t, 0, 2, 144, 1, T["bezel_hi"])
    rect(t, 144, 0, 1, 3, T["bezel_hi"])
    glass(t, 6, 9, 56, 8, frame=1, r=1)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        o = key(t, bx, 22, 10, 10, False, r=2.0 if imac() else 1.6)
        mini_transport_icon(t, kind, bx, 22 - (1 if imac() else 0), key_ink(False))
    glass(t, 65, 22, 33, 8, frame=1, r=1)
    rect(t, 84, 22 + 2, 1, 1, T["ink_mid"])
    rect(t, 84, 22 + 5, 1, 1, T["ink_mid"])
    o = key(t, 106, 8, 22, 18, False)
    text_center(t, TINY, "LIST", 117, 14 if imac() else 15, key_ink(False))
    grip(t, 146, 33, 4)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    bezel_rows(t, 0, 25, 0, 3)
    rect(t, 0, 2, 25, 1, T["bezel_hi"])
    a[0:38, 179:204] = t
    return a


def grip(t, right, bottom, n):
    """The resize grip: rows of dots stepping down to the corner."""
    dot = T["body_lo"] if not imac() else shade(T["C"], 0.35)
    hi = T["body_hi"]
    for k in range(n):
        for j in range(k + 1):
            gx, gy = right - 3 * k + 3 * j, bottom - 3 * j
            px(t, gx, gy, dot)
            px(t, gx + 1, gy + 1, hi)


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_gen():
    a = new(194, 109)
    fill(a, 0, 0, 194, 109, 0, None)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn, bz=(0, 25)):
            t = bar20(25, lit)
            bezel_rows(t, bz[0], bz[1], BZ, 20)
            rect(t, bz[0], BZ, bz[1] - bz[0], 1, T["bezel_hi"])
            fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 1, 20, T["rim_hi"])
            rect(t, 8, BZ, 1, 3, T["bezel_hi"])

        def left_end(t):
            plate_cap_left(t, 17, PLATE_Y, lit)
            plate(t, 21, PLATE_Y, 4, lit)

        def centre(t):
            plate(t, 0, PLATE_Y, 25, lit)

        def right_end(t):
            plate(t, 0, PLATE_Y, 4, lit)
            plate_cap_right(t, 4, PLATE_Y, lit)

        def nothing(t):
            pass

        def right(t):
            mini_button(t, 14, 3, "close", lit)
            rect(t, 24, 0, 1, 20, T["rim"])
            rect(t, 17, BZ, 1, 3, T["bezel_hi"])

        piece(0, left, (8, 25))
        piece(26, left_end)
        piece(52, centre)
        piece(78, right_end)
        piece(104, nothing)
        piece(130, right, (0, 18))

    def bottom(w, has_grip, left_edge):
        t = new(w, 14)
        fill(t, 0, 0, w, 14, 0, 14, stripes=True)
        rect(t, 0, 13, w, 1, T["rim"])
        if left_edge:
            rect(t, 0, 0, 1, 14, T["rim_hi"])
            bezel_rows(t, 8, w, 0, 2)
            rect(t, 8, 0, 1, 2, T["bezel_hi"])
            rect(t, 9, 1, w - 9, 1, T["bezel_hi"])
        else:
            rect(t, w - 1, 0, 1, 14, T["rim"])
            bezel_rows(t, 0, w - 7, 0, 2)
            rect(t, w - 8, 0, 1, 2, T["bezel_hi"])
            rect(t, 0, 1, w - 8, 1, T["bezel_hi"])
        if has_grip:
            grip(t, w - 5, 10, 3)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    t = new(25, 14)
    fill(t, 0, 0, 25, 14, 0, 14)
    rect(t, 0, 13, 25, 1, T["rim"])
    bezel_rows(t, 0, 25, 0, 2)
    rect(t, 0, 1, 25, 1, T["bezel_hi"])
    a[72:86, 127:152] = t
    # sides: left (11 wide: rim, surface, bezel at 8..10), right (8 wide: bezel col 0, surface, rim)
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        fill(t, 0, 0, w, h, 0, None, stripes=False)
        if outer_left:
            rect(t, 0, 0, 1, h, T["rim_hi"])
            rect(t, 8, 0, 3, h, T["bezel"])
            rect(t, 8, 0, 1, h, T["bezel_hi"])
        else:
            rect(t, w - 1, 0, 1, h, T["rim"])
            rect(t, 0, 0, 1, h, T["bezel_hi"])
        a[42:42 + h, x:x + w] = t
    c = bar20(25, True)[3:12, 14:23].copy()
    mini_button(c, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = c

    # letters: each row starts at x 1, letters in their own cells, 1px separators of x 0's colour.
    # Each cell row is the plate's row at that height, so the letters sit in the plate seamlessly.
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            for r in range(7):
                rect(a, x, y + r, w, 1, plate_col(1 + r, 9, lit))
            draw_text(a, FONT5, c, x, y + 1, title_ink(lit))
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp
# ------------------------------------------------------------------------------------------


def genex_colours():
    d, ink = T["disp"], T["pl_normal"]
    body = T["body"]
    if imac():
        C = T["C"]
        win_bg, win_text, btn_text = T["ice"], shade(C, 0.6), shade(C, 0.6)
        hdr_bg, hdr_text = lerp(T["ice"], C, 0.25), shade(C, 0.65)
        sb, sb2 = lerp(T["ice"], C, 0.2), C
    else:
        win_bg, win_text, btn_text = body, (40, 42, 46), (236, 237, 240)
        hdr_bg, hdr_text = (222, 224, 228), (40, 42, 46)
        sb, sb2 = (176, 179, 185), (40, 41, 45)
    return [
        d, ink, win_bg, btn_text, win_text, lerp(d, ink, 0.25), T["pl_sel"], hdr_bg, hdr_text,
        T["body_hi"], T["body_lo"], shade(hdr_bg, 0.15), win_bg, sb, sb2, shade(sb, 0.1), shade(sb2, 0.15),
        shade(win_bg, 0.08),
    ]


def make_genex():
    a = new(256, 64)
    fill(a, 0, 0, 256, 64, 0, None)
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    for y, pressed in ((1, False), (16, True)):
        c = a[y:y + 15, 0:47].copy()
        key(c, 0, 0, 47, 15, pressed)
        a[y:y + 15, 0:47] = c
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    bg = T["disp"]
    dots = lerp(T["disp"], T["ink"], 0.12)
    spec = [(ramp(T["vis_spec"], i / 15), f"spectrum {i + 1}") for i in range(16)]
    osc = [(c, f"oscilloscope {i + 1}") for i, c in enumerate(T["vis_osc"])]
    return [(bg, "background"), (dots, "dots")] + spec + osc + [(T["vis_peak"], "peaks")]


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={hexc(T['pl_normal'])}\nCurrent={hexc(T['pl_current'])}\n"
                f"NormalBG={hexc(T['disp'])}\nSelectedBG={hexc(T['pl_sel'])}\n"
                f"MbBG={hexc(T['disp'])}\nMbFG={hexc(T['pl_normal'])}\nFont=Lucida Grande\n")
    name = T["wsz"][:-4].replace("-", " ")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{name}\n{'=' * len(name)}\n\n"
            f"{name} — a personal skin in the style of {T['subject']}.\n"
            "Apple logo © Apple Inc.; private use only.\n\n"
            "A classic (Winamp 2.x format) skin. Every bitmap except the logo was drawn by a script\n"
            "(gen_skin.py) from shapes, gradients, noise and hand-made pixel fonts. Not affiliated\n"
            "with Apple.\n"
        )


# ------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------

SHEETS = {}


def build():
    main = make_main()
    sheets = {
        "main.bmp": main,
        "titlebar.bmp": make_titlebar(main),
        "cbuttons.bmp": make_cbuttons(main),
        "shufrep.bmp": make_shufrep(main),
        "posbar.bmp": make_posbar(main),
        "volume.bmp": make_volume(main),
        "balance.bmp": make_balance(main),
        "monoster.bmp": make_monoster(),
        "playpaus.bmp": make_playpaus(),
        "numbers.bmp": make_numbers(False),
        "nums_ex.bmp": make_numbers(True),
        "text.bmp": make_text(),
        "pledit.bmp": make_pledit(),
        "eqmain.bmp": make_eqmain(),
        "gen.bmp": make_gen(),
        "genex.bmp": make_genex(),
    }
    SHEETS.clear()
    for name, arr in sheets.items():
        SHEETS[name[:-4]] = save(arr, name)
    write_text_files()
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "readme.txt"]
    with zipfile.ZipFile(os.path.join(HERE, T["wsz"]), "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(OUT, n), "rb") as fh:
                z.writestr(info, fh.read())
    return names


# Every rect the app reads, per sheet (x, y, w, h), to check they're in bounds.
READS = {
    "cbuttons": [(0, 0, 136, 36)], "shufrep": [(0, 0, 92, 85)], "posbar": [(0, 0, 307, 10)],
    "volume": [(0, 0, 68, 433)], "balance": [(0, 0, 68, 433)], "monoster": [(0, 0, 56, 24)],
    "playpaus": [(0, 0, 48, 9)], "numbers": [(0, 0, 99, 13)], "nums_ex": [(0, 0, 108, 13)],
    "text": [(0, 0, 155, 18)], "titlebar": [(0, 0, 344, 87)], "main": [(0, 0, 275, 116)],
    "eqmain": [(0, 0, 275, 315)], "pledit": [(0, 0, 280, 110), (179, 0, 25, 38)], "gen": [(0, 0, 194, 103)],
    "genex": [(0, 0, 84, 31)],
}


def check_sheets():
    for name, rects in READS.items():
        im = SHEETS[name]
        assert im.mode == "RGB", name
        for x, y, w, h in rects:
            assert x + w <= im.width and y + h <= im.height, (name, im.size, (x, y, w, h))
    gen_letters()


# ------------------------------------------------------------------------------------------
# Preview: the windows put together from the sprites the way the app does
# ------------------------------------------------------------------------------------------


def blit(dst, sheet, r, dx, dy, w=None, sx=0):
    x, y, rw, rh = r
    w = rw if w is None else w
    dst.paste(sheet.crop((x + sx, y, x + sx + w, y + rh)), (dx, dy))


def stretch(dst, sheet, r, dx, dy, dw, dh):
    x, y, w, h = r
    dst.paste(sheet.crop((x, y, x + w, y + h)).resize((dw, dh), Image.NEAREST), (dx, dy))


FONT_LOOKUP = {}
for _row, _chars in enumerate(FONT_GRID):
    for _col, _ch in enumerate(_chars):
        if _ch is not None:
            FONT_LOOKUP[_ch] = (_row, _col)


def draw_bitmap_text(dst, s, x, y):
    text = SHEETS["text"]
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, text, (col * 5, row * 6, 5, 6), x, y)
        x += 5


def ttf(size):
    for name in ("/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
                 "/usr/share/fonts/google-noto/NotoSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def text_ink():
    """text.bmp's ink as the app finds it: the commonest colour clearly off the space's."""
    im = np.asarray(SHEETS["text"], dtype=np.int32)[:12, :155]
    bg = im[0, 150]
    d = np.abs(im - bg).sum(axis=2)
    cols, counts = np.unique(im[d >= 96].reshape(-1, 3), axis=0, return_counts=True)
    return tuple(int(v) for v in cols[counts.argmax()])


def preview_main(lit, state):
    S = SHEETS
    img = Image.new("RGB", (275, 116))
    img.paste(S["main"], (0, 0))
    blit(img, S["titlebar"], (27, 0 if lit else 15, 275, 14), 0, 0)
    for kind, x, w, h, mx, my in CB:
        blit(img, S["cbuttons"], (x, 18 if state["pressed"] == kind else 0, w, h), mx, my)
    blit(img, S["cbuttons"], (114, 16 if state["pressed"] == "eject" else 0, 22, 16), 136, 89)
    for name, x0, on in (("eq", 0, state["eq"]), ("pl", 23, state["pl"])):
        pressed = state["pressed"] == name
        sx = x0 + (46 if pressed else 0)
        blit(img, S["shufrep"], (sx, 73 if on else 61, 23, 12), 219 + x0, 58)
    blit(img, S["titlebar"], (304, 0, 8, 43), 10, 22)
    spr = {"O": (304, 47, 8, 8, 3), "A": (312, 55, 8, 7, 11), "I": (320, 62, 8, 7, 18), "D": (328, 69, 8, 8, 25),
           "V": (336, 77, 8, 7, 33)}
    for L in state["clutter"]:
        x, y, w, h, oy = spr[L]
        blit(img, S["titlebar"], (x, y, w, h), 10, 22 + oy)
    for name, x0, w, on, dst in (("shuffle", 28, 47, state["shuffle"], 164), ("repeat", 0, 28, state["repeat"], 210)):
        row = (2 if on else 0) + (1 if state["pressed"] == name else 0)
        blit(img, S["shufrep"], (x0, row * 15, w, 15), dst, 89)
    blit(img, S["playpaus"], (0 if state["playing"] else 9, 0, 9, 9), 26, 28)
    blit(img, S["monoster"], (29, 12 if state["stereo"] else 0, 27, 12), 212, 41)
    blit(img, S["monoster"], (0, 0 if state["stereo"] else 12, 29, 12), 239, 41)
    blit(img, S["posbar"], (0, 0, 248, 10), 16, 72)
    tl = round(state["pos"] * 219)
    blit(img, S["posbar"], (278 if state["seek"] else 248, 0, 29, 10), 16 + tl, 72)
    v = state["volume"]
    idx = max(0, round(v / 100 * 28) - 1)
    blit(img, S["volume"], (0, idx * 15, 68, 13), 107, 57)
    blit(img, S["volume"], (0 if state["vdrag"] else 15, 422, 14, 11), 107 + round(v / 100 * 54), 58)
    b = state["balance"]
    idx = int(abs(b) / 100 * 27)
    blit(img, S["balance"], (9, idx * 15, 38, 13), 177, 57)
    blit(img, S["balance"], (15, 422, 14, 11), 177 + round((b + 100) / 200 * 24), 58)
    secs = state["time"]
    m, s = secs // 60, secs % 60
    nums = S["nums_ex"]
    if state["remaining"]:
        blit(img, nums, (99, 0, 9, 13), 38, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    # title: text.bmp's space across the box, then the title in TrueType in text.bmp's ink
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    box = img.crop((111, 22, 265, 36))
    d = ImageDraw.Draw(box)
    d.text((0, 29 - 22), state["title"], fill=text_ink(), font=ttf(11), anchor="lm")
    img.paste(box, (111, 22))
    draw_bitmap_text(img, "192", 111, 43)
    draw_bitmap_text(img, "44", 156, 43)
    cols = [c for c, _ in viscolor()]
    vis = Image.new("RGB", (76, 16))
    vp = vis.load()
    for y in range(16):
        for x in range(76):
            vp[x, y] = cols[1] if (y % 2 == 1 and x % 2 == 0) else cols[0]
    heights = state["bars"]
    for x in range(75):
        if x % 4 == 3:
            continue
        hgt = heights[x // 4] - 2
        for y in range(16 - hgt, 16):
            vp[x, y] = cols[min(17, max(2, y + 2))]
        pk = heights[x // 4] + 2
        if 0 <= 16 - pk < 16:
            vp[x, 16 - pk] = cols[23]
    img.paste(vis, (24, 43))
    return img


def preview_eq(lit, state):
    S = SHEETS
    sheet = S["eqmain"]
    img = Image.new("RGB", (275, 116))
    blit(img, sheet, (0, 0, 275, 116), 0, 0)
    blit(img, sheet, (0, 134 if lit else 149, 275, 14), 0, 0)
    if state["pressed"] == "close":
        blit(img, sheet, (0, 125, 9, 9), 264, 3)
    on, pressed = state["on"], state["pressed"] == "on"
    blit(img, sheet, ((187 if on else 128) if pressed else (69 if on else 10), 119, 26, 12), 14, 18)
    blit(img, sheet, ((95 if state["auto"] else 36), 119, 32, 12), 40, 18)
    blit(img, sheet, (224, 176 if state["pressed"] == "presets" else 164, 44, 12), 217, 18)

    def slider(x, value, drag):
        n = round(value / 100 * 27)
        blit(img, sheet, (13 + (n % 14) * 15, 164 + (n // 14) * 65, 14, 63), x, 38)
        ty = 38 + round((1 - value / 100) * 51)
        blit(img, sheet, (0, 176 if drag else 164, 11, 11), x + 1, ty)

    slider(21, state["preamp"], False)
    for i, v in enumerate(state["bands"]):
        slider(78 + 18 * i, v, state["drag"] == i)
    blit(img, sheet, (0, 294, 113, 19), 86, 17)
    py_ = round((100 - state["preamp"]) / 100 * 18)
    blit(img, sheet, (0, 314, 113, 1), 86, 17 + py_)
    ys = [(100 - v) / 100 * 18 for v in state["bands"]]
    last = round(ys[0])
    for x in range(0, 109):
        i = min(8, x // 12)
        t = (x - i * 12) / 12
        y = round(ys[i] + (ys[i + 1] - ys[i]) * (3 * t * t - 2 * t * t * t))
        y = max(0, min(18, y))
        top, h = min(y, last), 1 + abs(last - y)
        blit(img, sheet, (115, 294 + top, 1, h), 86 + 2 + x, 17 + top)
        last = y
    return img


def preview_playlist(lit, w, h, rows, pressed_close=False, drag=False):
    S = SHEETS
    sheet = S["pledit"]
    img = Image.new("RGB", (w, h))
    ty = 0 if lit else 21
    for x in range(25, w - 25, 25):
        blit(img, sheet, (127, ty, 25, 20), x, 0)
    blit(img, sheet, (0, ty, 25, 20), 0, 0)
    blit(img, sheet, (26, ty, 100, 20), (w - 100) // 2, 0)
    blit(img, sheet, (153, ty, 25, 20), w - 25, 0)
    for y in range(20, h - 38, 29):
        blit(img, sheet, (0, 42, 12, 29), 0, y)
        blit(img, sheet, (31, 42, 20, 29), w - 20, y)
    for x in range(125, w - 150, 25):
        blit(img, sheet, (179, 0, 25, 38), x, h - 38)
    blit(img, sheet, (0, 72, 125, 38), 0, h - 38)
    blit(img, sheet, (126, 72, 150, 38), w - 150, h - 38)
    if pressed_close:
        blit(img, sheet, (52, 42, 9, 9), w - 11, 3)
    d = ImageDraw.Draw(img)
    lx, lw = 12, w - 32
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=T["disp"])
    font = ttf(9)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=T["pl_sel"])
        col = T["pl_current"] if i == 1 else T["pl_normal"]
        d.text((lx + 2, y + 2), f"{i + 1}. {txt}", fill=col, font=font)
        d.text((lx + lw - 3 - d.textlength(dur, font=font), y + 2), dur, fill=col, font=font)
    blit(img, sheet, (61 if drag else 52, 53, 8, 18), w - 15, 20 + 30)
    draw_bitmap_text(img, "3:27/41:10", w - 150 + 7, h - 38 + 10)
    for dx, ch in zip([1, 7, 12, 20, 25], " 0327"):
        draw_bitmap_text(img, ch, w - 150 + 66 + dx, h - 38 + 23)
    return img


def gen_letters():
    g = SHEETS["gen"]
    pxs = g.load()
    out = {}
    for state, y in (("focused", 88), ("unfocused", 96)):
        bg = pxs[0, y]
        letters, n, x = {}, 0, 1
        while x < g.width and n < 26:
            if pxs[x, y] == bg:
                x += 1
                continue
            start = x
            while x < g.width and pxs[x, y] != bg:
                x += 1
            letters[chr(65 + n)] = (start, x - start)
            n += 1
        assert n == 26, f"gen.bmp {state} letters: found {n}"
        out[state] = letters
    return out


def preview_gen(lit, w, h, title, pressed_close=False):
    g = SHEETS["gen"]
    L = gen_letters()
    st = "focused" if lit else "unfocused"
    ty = 0 if lit else 21
    img = Image.new("RGB", (w, h), (0, 0, 0))
    piece = lambda px0: (px0, ty, 25, 20)
    for tx in range(0, w, 25):
        blit(img, g, piece(104), tx, 0)
    text_wd = sum(L[st].get(c, (0, 5))[1] for c in title.upper())
    if text_wd + 100 <= w:
        tx = (w - text_wd) // 2
        for cx in range(tx, tx + text_wd, 25):
            blit(img, g, piece(52), cx, 0, min(25, tx + text_wd - cx))
        blit(img, g, piece(26), tx - 25, 0)
        blit(img, g, piece(78), tx + text_wd, 0)
        x = tx
        for c in title.upper():
            if c in L[st]:
                lx, lw = L[st][c]
                blit(img, g, (lx, 88 if lit else 96, lw, 7), x, 4)
                x += lw
            else:
                x += 5
    blit(img, g, piece(0), 0, 0)
    blit(img, g, piece(130), w - 25, 0)
    if pressed_close:
        blit(img, g, (148, 42, 9, 9), w - 11, 3)
    right_x = w - 8
    side_bottom = h - 14 - 24
    for ty2 in range(20, side_bottom, 29):
        blit(img, g, (127, 42, 11, 29), 0, ty2)
        blit(img, g, (139, 42, 8, 29), right_x, ty2)
        stretch(img, g, (139, 42, 1, 29), right_x - 3, ty2, 3, 29)
    blit(img, g, (158, 42, 11, 24), 0, side_bottom)
    blit(img, g, (170, 42, 8, 24), right_x, side_bottom)
    stretch(img, g, (170, 42, 1, 24), right_x - 3, side_bottom, 3, 24)
    by = h - 14
    for tx in range(0, w, 25):
        blit(img, g, (127, 72, 25, 14), tx, by)
    lw_ = min(125, -(-w // 2))
    rw_ = min(125, w - lw_)
    blit(img, g, (0, 42, 125, 14), 0, by, lw_)
    blit(img, g, (0, 57, 125, 14), w - rw_, by, rw_, 125 - rw_)
    pic = Image.linear_gradient("L").resize((w - 22, h - 34)).convert("RGB")
    arr = np.array(pic).astype(np.float32) / 255
    c0, c1 = np.array(T["vis_spec"][4], np.float32), np.array(T["vis_spec"][1], np.float32)
    col = c0 + (c1 - c0) * arr[..., :1]
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("Think Different - Crazy Ones", "4:12"), ("Bondi Beach - Translucent", "3:47"),
            ("Hello (Again) - Startup Chime", "5:03"), ("Hockey Puck - USB Mouse", "2:58"),
            ("Five Flavours - Fruit Salad", "6:21"), ("Unibody - Precision Cut", "3:33"),
            ("Glass Trackpad - Multi-Touch", "4:40"), ("Backlit Keys - After Dark", "3:09"),
            ("MagSafe - Breakaway", "5:51"), ("Slot Loader - SuperDrive", "4:05"),
            ("Sleep Light - Breathing", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=f"Now Playing - {T['wsz'][:-4].replace('-', ' ')}", bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="Paused: Quiet Hours (Live)", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    EA = dict(pressed=None, on=True, auto=False, preamp=50, drag=None,
              bands=[75, 68, 56, 49, 49, 33, 30, 30, 49, 49])
    EB = dict(pressed="close", on=False, auto=True, preamp=70, drag=3,
              bands=[51, 51, 59, 65, 65, 100, 59, 51, 0, 51])
    cols = []
    for lit, st, est in ((True, A, EA), (False, B, EB)):
        h = 116 + 116 + 232 + 140
        col = Image.new("RGB", (275, h))
        col.paste(preview_main(lit, st), (0, 0))
        col.paste(preview_eq(lit, est), (0, 116))
        col.paste(preview_playlist(lit, 275, 232, rows, pressed_close=not lit, drag=not lit), (0, 232))
        col.paste(preview_gen(lit, 275, 140, "album art", pressed_close=not lit), (0, 464))
        cols.append(col)
    gap = 12
    out = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), (60, 60, 64))
    out.paste(cols[0], (gap, gap))
    out.paste(cols[1], (275 + 2 * gap, gap))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, T["preview"]))


def run(key_):
    global T, OUT, _rng
    T = make_theme(key_)
    OUT = os.path.join(OUT_ROOT, key_)
    os.makedirs(OUT, exist_ok=True)
    _rng = np.random.default_rng(1998)
    names = build()
    check_sheets()
    preview()
    print(f"{T['wsz']}: {len(names)} files, text ink {hexc(text_ink())}")


if __name__ == "__main__":
    os.makedirs(SCRATCH, exist_ok=True)
    args = sys.argv[1:]
    if "--list" in args:
        print("\n".join(THEME_KEYS))
        sys.exit(0)
    for a_ in args:
        if a_ not in THEME_KEYS:
            sys.exit(f"unknown theme {a_!r}; try --list")
    for k in args or THEME_KEYS:
        run(k)
