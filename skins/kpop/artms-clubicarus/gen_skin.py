#!/usr/bin/python3
"""ARTMS Club Icarus: a personal classic Winamp 2.x fan skin (private use only).

Built on Ember's generator (skins/ember/gen_skin.py): the same sprite layouts, restyled after
ARTMS's album "Club Icarus": a teal-green underground tunnel, white square wall tiles with a rust
band, fluorescent tubes, black leather, iridescent feather wings, and a pixelated serif logotype.

Photos: source/cover.webp is the main window's backdrop, source/wings-tunnel.jpg the EQ's.
The ARTMS wordmark comes from objekts-archive's Atom02 back template (ink alpha).

Writes the bitmaps and text files into out/, zips them flat into ARTMS-Club-Icarus.wsz, and draws
preview.png (the windows assembled from the sprites at their real positions, 2x).
"""

import os
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
SRC = os.path.join(HERE, "source")
ARTMS_INK = "/home/matt/gitea/ergosteur/objekts-archive/back_templates/Atom02/template-ink.png"
WSZ_NAME = "ARTMS-Club-Icarus.wsz"
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------------------------------
# Palette: tunnel teal-green, fluorescent mint, black leather, wing pastels
# ------------------------------------------------------------------------------------------

BODY = (14, 25, 22)
BODY_HI = (58, 90, 81)
BODY_LO = (3, 7, 6)
SLOT = (7, 14, 12)
DISP = (6, 15, 12)
MINT = (168, 236, 210)
MINT_HI = (236, 255, 247)
MINT_MID = (92, 150, 130)
MINT_DIM = (24, 48, 40)
GREY_TXT = (104, 132, 122)
GREY_DIM = (56, 74, 68)
TEAL = (111, 214, 200)
PEACH = (242, 184, 160)
LILAC = (200, 176, 224)
PINK = (240, 168, 200)
RUST = (112, 74, 56)
TILE = (40, 66, 59)
TILE_HI = (58, 90, 81)
GROUT = (15, 27, 24)
SEP = (255, 0, 255)          # gen.bmp letter separators (never shown)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    """Colour along a list of stops, t in 0..1."""
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


WINGS = [TEAL, LILAC, PINK, PEACH]                       # the iridescent feathers, in order
LEVEL = [(30, 74, 66), (70, 170, 156), TEAL, LILAC, PINK, PEACH]

# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def new(w, h, col=BODY):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[y:y + h, x:x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def raised(a, x, y, w, h, hi=BODY_HI, lo=BODY_LO):
    rect(a, x, y, w, 1, hi)
    rect(a, x, y, 1, h, hi)
    rect(a, x, y + h - 1, w, 1, lo)
    rect(a, x + w - 1, y, 1, h, lo)


def sunken(a, x, y, w, h, hi=BODY_HI, lo=BODY_LO):
    raised(a, x, y, w, h, lo, hi)


_rng = np.random.default_rng(2024)


def grain(a, x, y, w, h, amp=2.0):
    """Fine soft grain (wraps horizontally, so tiles stay seamless)."""
    n = _rng.normal(0, 1, (h, w))
    acc = (n + np.roll(n, 1, axis=1) + np.roll(n, -1, axis=1)) / 2.0
    a[y:y + h, x:x + w] += np.round(acc * amp).astype(np.int32)[:, :, None]


def body(a, x, y, w, h, col=BODY, amp=2.0):
    rect(a, x, y, w, h, col)
    grain(a, x, y, w, h, amp)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def tiles(a, x, y, w, h, ox=0, oy=0, xs=(0, 12), xp=25, ys=(0, 14), yp=29, face=TILE, hi=TILE_HI, grout=GROUT):
    """The tunnel's square wall tiles: faces with a lit top-left edge, dark grout lines.
    Grout falls where (ox + i) % xp is in xs and (oy + j) % yp is in ys, so pieces placed on
    those periods line up."""
    for j in range(h):
        gy = (oy + j) % yp
        for i in range(w):
            gx = (ox + i) % xp
            if gx in xs or gy in ys:
                c = grout
            elif (gx - 1) in xs or (gy - 1) in ys:
                c = hi
            else:
                c = face
            a[y + j, x + i] = c
    grain(a, x, y, w, h, 1.5)


# ------------------------------------------------------------------------------------------
# Photos
# ------------------------------------------------------------------------------------------


def photo(name, box, size, bright=0.5, blur=0.0, sat=1.0, tint=(0, 0, 0)):
    """A crop of a source photo, resized, darkened and graded; returns an int array."""
    im = Image.open(os.path.join(SRC, name)).convert("RGB").crop(box).resize(size, Image.LANCZOS)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    f = np.array(im).astype(np.float32)
    lum = (f @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    f = lum + (f - lum) * sat
    f = f * bright + np.array(tint, np.float32)
    return np.clip(np.round(f), 0, 255).astype(np.int32)


def vignette(a, x, y, w, h, strength=0.35):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.42
    m = 1 - strength * d ** 1.6
    a[y:y + h, x:x + w] = np.round(a[y:y + h, x:x + w] * m[..., None]).astype(np.int32)


def dim(a, x, y, w, h, k, toward=DISP):
    """Frosts a region toward a dark glass colour (k = 0 none, 1 solid)."""
    reg = a[y:y + h, x:x + w].astype(np.float32)
    a[y:y + h, x:x + w] = np.round(reg * (1 - k) + np.array(toward, np.float32) * k).astype(np.int32)


# ------------------------------------------------------------------------------------------
# Pixel fonts
# ------------------------------------------------------------------------------------------

def G(*rows):
    return list(rows)


# 5-row font for text.bmp, titles and gen.bmp's letters (Ember's).
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
    "M": G("#..#", "####", "####", "#..#", "#..#"),
    "N": G("#..#", "##.#", "#.##", "#..#", "#..#"),
    "O": G(".##.", "#..#", "#..#", "#..#", ".##."),
    "P": G("###.", "#..#", "###.", "#...", "#..."),
    "Q": G(".##.", "#..#", "#..#", "#.#.", ".#.#"),
    "R": G("###.", "#..#", "###.", "#.#.", "#..#"),
    "S": G(".###", "#...", ".##.", "...#", "###."),
    "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#..#", "#..#", "#..#", "#..#", ".##."),
    "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#..#", "#..#", "####", "####", "#..#"),
    "X": G("#..#", "#..#", ".##.", "#..#", "#..#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": G("####", "...#", ".##.", "#...", "####"),
    "0": G("###", "#.#", "#.#", "#.#", "###"),
    "1": G(".#.", "##.", ".#.", ".#.", "###"),
    "2": G("###", "..#", "###", "#..", "###"),
    "3": G("###", "..#", ".##", "..#", "###"),
    "4": G("#.#", "#.#", "###", "..#", "..#"),
    "5": G("###", "#..", "###", "..#", "###"),
    "6": G("###", "#..", "###", "#.#", "###"),
    "7": G("###", "..#", ".#.", ".#.", ".#."),
    "8": G("###", "#.#", "###", "#.#", "###"),
    "9": G("###", "#.#", "###", "..#", "###"),
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

# 3x5 font for small labels.
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

# A pixelated old-style serif for "Club Icarus": 9 rows, x-height 6, thick-thin strokes with
# stair-stepped bowls and bracketed serifs (drawn for this skin in the logotype's spirit).
_X = "........"
SERIF = {
    "C": G("...####.#",
           ".##....##",
           "##......#",
           "##.......",
           "##.......",
           "##.......",
           "##.......",
           ".##.....#",
           "...#####."),
    "l": G("###.", ".##.", ".##.", ".##.", ".##.", ".##.", ".##.", ".##.", "####"),
    "u": G(_X, _X, _X,
           "###.###.",
           ".##..##.",
           ".##..##.",
           ".##..##.",
           ".##..##.",
           "..###.##"),
    "b": G("###.....",
           ".##.....",
           ".##.....",
           ".##.###.",
           ".###..##",
           ".##...##",
           ".##...##",
           ".##..##.",
           "##.###.."),
    "I": G("######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##..", "..##..", "######"),
    "c": G(_X[:7], _X[:7], _X[:7],
           "..####.",
           ".##...#",
           "##.....",
           "##.....",
           ".##...#",
           "..####."),
    "a": G(_X[:7], _X[:7], _X[:7],
           ".####..",
           "#...##.",
           "..####.",
           ".##.##.",
           "##..##.",
           ".###.##"),
    "r": G(_X[:6], _X[:6], _X[:6],
           "##.###",
           ".###..",
           ".##...",
           ".##...",
           ".##...",
           "####.."),
    "s": G(_X[:6], _X[:6], _X[:6],
           ".####.",
           "##...#",
           ".###..",
           "...##.",
           "#...##",
           ".####."),
    " ": G(*["...."] * 9),
}

# Time digits in the same serif spirit: 7x11 inside numbers.bmp's 9x13 cells.
DIGITS = {
    0: G("..###..", ".##..#.", "##...##", "##...##", "##...##", "##...##",
         "##...##", "##...##", "##...##", ".##..#.", "..###.."),
    1: G("...##..", ".####..", "...##..", "...##..", "...##..", "...##..",
         "...##..", "...##..", "...##..", "...##..", ".######"),
    2: G(".####..", "#...##.", "....##.", "....##.", "...##..", "..##...",
         ".##....", "##.....", "##.....", "##...#.", "#######"),
    3: G(".####..", "#...##.", "....##.", "....##.", "..###..", "....##.",
         ".....##", ".....##", ".....##", "#...##.", ".####.."),
    4: G("....##.", "...###.", "..#.##.", ".#..##.", "#...##.", "#...##.",
         "#######", "....##.", "....##.", "....##.", "...####"),
    5: G("#######", "##.....", "##.....", "##.....", "#####..", "....##.",
         ".....##", ".....##", ".....##", "#...##.", ".####.."),
    6: G("..####.", ".##...#", "##.....", "##.....", "#####..", "##..##.",
         "##...##", "##...##", "##...##", ".##..#.", "..###.."),
    7: G("#######", "#....##", "....##.", "....##.", "...##..", "...##..",
         "..##...", "..##...", "..##...", "..##...", ".####.."),
    8: G(".#####.", "##...##", "##...##", ".##..#.", "..###..", ".#..##.",
         "##...##", "##...##", "##...##", "##...##", ".#####."),
    9: G("..###..", ".#..##.", "##...##", "##...##", "##...##", ".##..##",
         "..#####", ".....##", ".....##", "#...##.", ".####.."),
}


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1, shadow=None):
    for c in s:
        if c not in font:
            continue
        g = font[c]
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    if shadow is not None:
                        px(a, x + k + 1, y + r + 1, shadow)
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col(r) if callable(col) else col)
        x += len(g[0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1, shadow=None):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow)


def glow_text(a, font, s, x, y, col, halo, gap=1):
    """Fluorescent-sign text: a soft halo one pixel round the strokes, then the strokes."""
    w = text_w(font, s, gap)
    h = len(next(iter(font.values())))
    m = new(w + 2, h + 2, (0, 0, 0))
    draw_text(m, font, s, 1, 1, (1, 1, 1), gap)
    lit = m[..., 0] > 0
    ring = np.zeros_like(lit)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        ring |= np.roll(np.roll(lit, dy, 0), dx, 1)
    ring &= ~lit
    for j, i in zip(*np.nonzero(ring)):
        X, Y = x - 1 + i, y - 1 + j
        if 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]:
            a[Y, X] = np.round(a[Y, X] * 0.4 + np.array(halo) * 0.6).astype(np.int32)
    draw_text(a, font, s, x, y, col, gap)


# ------------------------------------------------------------------------------------------
# The ARTMS wordmark (from the Atom02 objekt back template's ink alpha)
# ------------------------------------------------------------------------------------------

_WORDMARK = {}


def artms_alpha(h):
    """The wordmark's alpha at h pixels tall, as a float array (0..1)."""
    if h not in _WORDMARK:
        al = Image.open(ARTMS_INK).split()[-1].crop((90, 240, 720, 390))
        al = al.crop(al.getbbox())
        w = round(al.width * h / al.height)
        f = np.array(al.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255
        _WORDMARK[h] = np.clip((f - 0.18) / 0.62, 0, 1)
    return _WORDMARK[h]


def draw_artms(a, x, y, h, col, shadow=None):
    al = artms_alpha(h)
    hh, ww = al.shape
    for dx, dy, c in ([(1, 1, shadow)] if shadow is not None else []) + [(0, 0, col)]:
        reg = a[y + dy:y + dy + hh, x + dx:x + dx + ww].astype(np.float32)
        k = al[:reg.shape[0], :reg.shape[1], None]
        a[y + dy:y + dy + hh, x + dx:x + dx + ww] = np.round(reg * (1 - k) + np.array(c) * k).astype(np.int32)
    return ww


# ------------------------------------------------------------------------------------------
# Shared pieces: leather, tubes, pearl thumbs
# ------------------------------------------------------------------------------------------


def leather(a, x, y, w, h, pressed=False):
    """Black leather: a soft sheen across the top, pebbled grain, rolled edges."""
    for r in range(h):
        t = r / max(1, h - 1)
        if pressed:
            c = lerp((9, 13, 12), (16, 22, 20), t)
        else:
            c = ramp([(50, 60, 58), (34, 42, 40), (22, 28, 27), (14, 18, 17)], t)
        rect(a, x, y + r, w, 1, c)
    n = _rng.normal(0, 1, (h, w))
    n = (n + np.roll(n, 1, 0) + np.roll(n, 1, 1)) / 2.2
    a[y:y + h, x:x + w] += np.round(n * (1.4 if pressed else 2.2)).astype(np.int32)[:, :, None]
    if pressed:
        rect(a, x, y, w, 1, BODY_LO)
        rect(a, x, y, 1, h, BODY_LO)
        rect(a, x + 1, y + 1, w - 2, 1, (5, 8, 7))
        rect(a, x + w - 1, y, 1, h, (40, 56, 51))
        rect(a, x, y + h - 1, w, 1, (40, 56, 51))
    else:
        rect(a, x, y, w, 1, (86, 104, 98))
        rect(a, x, y, 1, h, (64, 80, 75))
        rect(a, x + w - 1, y, 1, h, BODY_LO)
        rect(a, x, y + h - 1, w, 1, BODY_LO)
        rect(a, x + 1, y + h - 2, w - 2, 1, (10, 13, 12))
        # a stitched seam just inside the top edge
        for i in range(x + 2, x + w - 2, 2):
            px(a, i, y + 2, (58, 72, 68))


def tube(a, x, y, w, lit, seg=13, gap=3, phase=0):
    """A row of fluorescent tubes (rows y-1..y+1): bright core, green glow; off when unlit.
    The segment pattern repeats every seg+gap from absolute x = phase."""
    for i in range(x, x + w):
        on = (i - phase) % (seg + gap) < seg
        if not on:
            continue
        if lit:
            px(a, i, y, (226, 255, 242))
            px(a, i, y - 1, lerp(a[y - 1, i].tolist(), (80, 170, 140), 0.55))
            px(a, i, y + 1, lerp(a[y + 1, i].tolist(), (60, 140, 116), 0.5))
        else:
            px(a, i, y, (52, 70, 64))


def pearl_thumb(a, x, y, w, h, selected, grip="v"):
    """A pearly feather-white thumb with an iridescent sheen (teal at the top, pink below)."""
    for r in range(h):
        for c in range(w):
            t = (r / max(1, h - 1)) * 0.65 + (c / max(1, w - 1)) * 0.35
            base = ramp([(214, 246, 236), (190, 232, 226), (222, 206, 236), (246, 206, 218)], t)
            if selected:
                base = lerp(base, (255, 236, 244), 0.35)
            px(a, x + c, y + r, base)
    hi = (255, 255, 255)
    lo = (24, 52, 46)
    rect(a, x, y, w, 1, hi)
    rect(a, x, y, 1, h, hi)
    rect(a, x + w - 1, y, 1, h, lo)
    rect(a, x, y + h - 1, w, 1, lo)
    ink = (120, 150, 160) if not selected else (176, 120, 160)
    cx = x + w // 2
    if grip == "v":
        for gx in (cx - 2, cx, cx + 2):
            rect(a, gx, y + 3, 1, h - 6, ink)
    else:
        for gy in (y + h // 2 - 2, y + h // 2, y + h // 2 + 2):
            rect(a, x + 3, gy, w - 6, 1, ink)


def plate(a, x, y, w, lit, h=9):
    """A recessed dark-glass nameplate for a title (rows y..y+h-1)."""
    rect(a, x, y + 1, w, h - 2, DISP if lit else (10, 16, 14))
    rect(a, x, y, w, 1, BODY_LO)
    rect(a, x, y + h - 1, w, 1, BODY_HI)


def plate_cap_left(a, x, y, lit, h=9):
    """4 columns: gap, dark rim, plate."""
    rect(a, x + 2, y, 1, h, BODY_LO)
    plate(a, x + 3, y, 1, lit, h)


def plate_cap_right(a, x, y, lit, h=9):
    plate(a, x, y, 1, lit, h)
    rect(a, x + 1, y, 1, h, BODY_HI)


TITLE_LIT = MINT
TITLE_DIM = (96, 122, 113)


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: leather with a mint glyph."""
    leather(a, x, y, 9, 9, pressed)
    for i in range(x + 2, x + 7, 2):   # no seam on so small a button
        a[y + 2, i] = a[y + 3, i]
    ink = MINT_HI if pressed else (MINT if lit else (110, 130, 124))
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        rect(a, X + 3, Y + 3, 3, 3, ink)
        for dx, dy in [(3, 3), (5, 3), (3, 5), (5, 5)]:
            px(a, X + dx, Y + dy, lerp(ink, (30, 40, 38), 0.5))
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 2, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 2, ink)
        rect(a, X + 2, Y + 5, 5, 1, lerp(ink, (30, 40, 38), 0.5))
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


def bar_bg(w, h=14):
    """Titlebar ground: dark tunnel-ceiling green, a little lighter at the top."""
    a = new(w, h, BODY)
    for r in range(h):
        rect(a, 0, r, w, 1, lerp((26, 42, 37), (10, 18, 16), r / (h - 1)))
    grain(a, 0, 0, w, h, 1.2)
    rect(a, 0, 0, w, 1, BODY_HI)
    return a


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, SLOT)
    sunken(a, 0, 0, 8, 43)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, (22, 58, 50))
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, MINT_HI if on else GREY_TXT)
    return a


TITLE = "Club Icarus"


def main_titlebar(lit):
    a = bar_bg(275)
    rect(a, 0, 0, 1, 14, BODY_HI)
    rect(a, 274, 0, 1, 14, BODY_LO)
    tw = text_w(SERIF, TITLE)
    aw = artms_alpha(7).shape[1]
    # group: ARTMS wordmark, a 2px feather dot, the serif title; centred between the buttons
    gw = aw + 9 + tw
    gx = 18 + (240 - 18 - gw) // 2
    tx = gx + aw + 9
    tube(a, 19, 6, gx - 5 - 19, lit, phase=19)
    tube(a, tx + tw + 5, 6, 240 - (tx + tw + 5), lit, phase=tx + tw + 5)
    top, bot = (MINT_HI, (120, 214, 184)) if lit else ((128, 150, 142), (84, 104, 97))
    draw_artms(a, gx, 4, 7, (196, 236, 222) if lit else (98, 118, 111), shadow=BODY_LO)
    dot = PINK if lit else GREY_DIM
    rect(a, gx + aw + 3, 6, 2, 2, dot)
    if lit:
        glow_text(a, SERIF, TITLE, tx, 2, lambda r: lerp(top, bot, r / 8), (28, 70, 58))
    else:
        draw_text(a, SERIF, TITLE, tx, 2, lambda r: lerp(top, bot, r / 8), shadow=BODY_LO)
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, BODY)
    body(a, 0, 0, 344, 87, BODY, 1.5)
    for kind, x, y, py_ in [("options", 0, 0, 9), ("minimize", 9, 0, 9), ("close", 18, 0, 9)]:
        b = new(9, 9)
        mini_button(b, 0, 0, kind, True)
        a[y:y + 9, x:x + 9] = b
        mini_button(b, 0, 0, kind, True, pressed=True)
        a[py_:py_ + 9, x:x + 9] = b
    b = new(9, 9)
    mini_button(b, 0, 0, "shade", True)
    a[18:27, 0:9] = b
    mini_button(b, 0, 0, "shade", True, pressed=True)
    a[18:27, 9:18] = b
    a[0:14, 27:302] = main_titlebar(True)
    a[15:29, 27:302] = main_titlebar(False)
    a[29:43, 27:302] = main_titlebar(True)
    a[42:56, 27:302] = main_titlebar(False)
    unlit = clutter_bar("")
    lit = clutter_bar("OAIDV")
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = lit[y:y + h]
    return a


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116)
# ------------------------------------------------------------------------------------------


def serif_digit(a, x, y, n, col=MINT, halo=(18, 46, 38)):
    """A 9x13 numbers.bmp cell: the digit with a faint fluorescent halo."""
    rect(a, x, y, 9, 13, DISP)
    if n is None:
        return
    g = DIGITS[n]
    m = np.zeros((13, 9), bool)
    for r, row in enumerate(g):
        for c, ch in enumerate(row):
            if ch == "#":
                m[r + 1, c + 1] = True
    ring = np.zeros_like(m)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        ring |= np.roll(np.roll(m, dy, 0), dx, 1)
    ring &= ~m
    for r, c in zip(*np.nonzero(ring)):
        px(a, x + c, y + r, halo)
    for r, c in zip(*np.nonzero(m)):
        px(a, x + c, y + r, lerp(MINT_HI, col, r / 12))


def display_box(a, x, y, w, h):
    """A recessed display: dark rim, green-black glass."""
    rect(a, x, y, w, h, DISP)
    sunken(a, x - 1, y - 1, w + 2, h + 2, BODY_HI, BODY_LO)
    rect(a, x, y, w, 1, (2, 6, 5))
    rect(a, x, y, 1, h, (2, 6, 5))


def wing_pixels(n=13, ss=8):
    """A wing as a fan of feathers (ellipses rooted at the shoulder, top-left), supersampled and
    snapped to n x n pixels. Returns {(x, y): (feather index 0..1, distance along it 0..1)}."""
    import math
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / ss
    rx, ry = 1.2, 3.5
    owner = np.full((N, N), -1.0, np.float32)
    along = np.zeros((N, N), np.float32)
    feathers = 6
    for k in range(feathers):
        f = k / (feathers - 1)
        ang = math.radians(-30 + 100 * f)         # top feather points up-right, the last straight down
        length = 13.5 - 5.5 * f
        width = 1.8
        cx = rx + math.cos(ang) * length / 2
        cy = ry + math.sin(ang) * length / 2
        dx, dy = xx - cx, yy - cy
        u = dx * math.cos(ang) + dy * math.sin(ang)
        v = -dx * math.sin(ang) + dy * math.cos(ang)
        # a feather: blunt at the root, tapered to a point at the tip
        half = length / 2
        taper = np.clip(1.1 - np.maximum(0, u) / half * 0.8, 0.25, 1.1)
        inside = (u / half) ** 2 + (v / (width * taper)) ** 2 <= 1
        m = inside & (owner < 0)                  # lower feathers tuck under the ones above
        owner[m] = f
        along[m] = np.clip((u[m] + half) / length, 0, 1)
    out = {}
    for y in range(n):
        for x in range(n):
            blk = owner[y * ss:(y + 1) * ss, x * ss:(x + 1) * ss]
            cov = (blk >= 0).mean()
            if cov >= 0.45:
                sel = blk >= 0
                out[(x, y)] = (float(np.median(blk[sel])),
                               float(along[y * ss:(y + 1) * ss, x * ss:(x + 1) * ss][sel].mean()))
    return out


def wing_emblem(a, x, y, lit=True):
    """13x13: a wing as on the cover's members: pearl-white coverts at the shoulder, the feathers
    turning iridescent (teal, lilac, pink, peach) towards their tips."""
    pix = wing_pixels()
    for (c, r), (f, t) in pix.items():
        if not lit:
            col = lerp((96, 112, 106), GREY_DIM, t)
        else:
            tip = ramp(WINGS, f)
            col = lerp((246, 255, 251), tip, min(1.0, t * 1.5))
        px(a, x + c, y + r, col)
    # dark hairlines where one feather meets the next, so the feathers read separately
    for (c, r), (f, t) in pix.items():
        below = pix.get((c, r + 1))
        if below and below[0] > f + 0.01 and t > 0.35:
            px(a, x + c, y + r + 1, lerp(a[y + r + 1, x + c].tolist(), (20, 36, 32), 0.55))


def make_main():
    # the cover's tunnel: the corridor, the walking members and their wings, darkened
    a = photo("cover.webp", (0, 150, 640, 420), (275, 116), bright=0.68, blur=0.5, sat=0.95,
              tint=(-4, 0, -2))
    vignette(a, 0, 0, 275, 116, 0.5)
    raised(a, 0, 0, 275, 116, BODY_HI, BODY_LO)
    a[0:14, :] = main_titlebar(True)

    a[22:65, 10:18] = clutter_bar("")

    # frosted glass behind the display cluster, so the photo stays mood, not noise
    dim(a, 19, 18, 251, 38, 0.55)
    # left display: indicator, time, analyzer
    display_box(a, 21, 20, 84, 42)
    for x in (48, 60, 78, 90):
        serif_digit(a, x, 26, None)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, MINT)
    rect(a, 24, 60, 76, 1, (16, 34, 28))

    # right display: title row, then kbps/kHz/mono/stereo row
    display_box(a, 109, 21, 159, 15)
    display_box(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, MINT_MID)
    draw_text(a, TINY, "KHZ", 169, 44, MINT_MID)

    # slider seats and seek bar seat: frosted
    dim(a, 106, 56, 160, 15, 0.6)
    sunken(a, 106, 56, 70, 15)
    sunken(a, 176, 56, 40, 15)
    sunken(a, 218, 57, 48, 14)
    dim(a, 15, 71, 250, 12, 0.6)
    sunken(a, 15, 71, 250, 12)

    # transport tray
    dim(a, 15, 87, 145, 20, 0.7)
    sunken(a, 15, 87, 145, 20)
    dim(a, 163, 88, 77, 17, 0.7)
    sunken(a, 163, 88, 77, 17)

    # the wing (the About button's spot)
    dim(a, 251, 90, 17, 15, 0.45)
    wing_emblem(a, 253, 92)
    # the tunnel wall's rust band along the bottom
    rect(a, 3, 110, 269, 1, lerp(RUST, BODY_LO, 0.3))
    rect(a, 3, 111, 269, 1, RUST)
    rect(a, 3, 112, 269, 1, BODY_LO)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36)
# ------------------------------------------------------------------------------------------


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


def transport_icon(a, kind, x, y, w, h, pressed):
    ink = MINT_HI if pressed else MINT
    shadow = None if pressed else BODY_LO
    o = 1 if pressed else 0
    cx, cy = x + w // 2 + o, y + h // 2 + o

    def both(fn):
        if shadow:
            fn(1, shadow)
        fn(0, ink)

    if kind == "previous":
        both(lambda d, c: (rect(a, cx - 6 + d, cy - 3 + d, 2, 7, c), tri_left(a, cx - 4 + d, cy - 3 + d, 7, c),
                           tri_left(a, cx + d, cy - 3 + d, 7, c)))
    elif kind == "play":
        both(lambda d, c: tri_right(a, cx - 2 + d, cy - 4 + d, 9, c))
    elif kind == "pause":
        both(lambda d, c: (rect(a, cx - 4 + d, cy - 3 + d, 3, 7, c), rect(a, cx + 1 + d, cy - 3 + d, 3, 7, c)))
    elif kind == "stop":
        both(lambda d, c: rect(a, cx - 3 + d, cy - 3 + d, 7, 7, c))
    elif kind == "next":
        both(lambda d, c: (tri_right(a, cx - 5 + d, cy - 3 + d, 7, c), tri_right(a, cx - 1 + d, cy - 3 + d, 7, c),
                           rect(a, cx + 3 + d, cy - 3 + d, 2, 7, c)))
    elif kind == "eject":
        def ej(d, c):
            for r in range(4):
                rect(a, cx - 1 - r + d, cy - 4 + r + d, 2 * r + 3, 1, c)
            rect(a, cx - 4 + d, cy + 1 + d, 9, 2, c)
        both(ej)


def make_cbuttons():
    a = new(136, 36, BODY)
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18)]
    for kind, x, w, h in specs:
        for pressed, y in ((False, 0), (True, 18)):
            leather(a, x, y, w, h, pressed)
            transport_icon(a, kind, x, y, w, h, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        leather(a, 114, y, 22, 16, pressed)
        transport_icon(a, "eject", 114, y, 22, 16, pressed)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle(a, x, y, w, h, label, on, pressed, led="under"):
    leather(a, x, y, w, h, pressed)
    for i in range(x + 2, x + w - 2):     # no seam: the LED and label take the room
        a[y + 2, i] = a[y + 3, i]
    o = 1 if pressed else 0
    if on:
        ink = MINT_HI
    else:
        ink = (140, 160, 152) if pressed else (118, 140, 132)
    tw = text_w(TINY, label)
    if led == "under":
        tx = x + (w - tw) // 2 + o
        ty = y + 3 + o
        draw_text(a, TINY, label, tx, ty, ink, shadow=None if pressed else BODY_LO)
        n = w - 9
        for i in range(n):
            c = ramp(WINGS, i / max(1, n - 1)) if on else (30, 42, 39)
            px(a, x + 4 + o + i, y + h - 5 + o, c)
            if on:
                px(a, x + 4 + o + i, y + h - 4 + o, lerp(c, (20, 26, 25), 0.6))
    else:  # LED dot at the left
        tx = x + 7 + (w - 9 - tw) // 2 + o
        ty = y + (h - 5) // 2 + o
        draw_text(a, TINY, label, tx, ty, ink, shadow=None if pressed else BODY_LO)
        lc = TEAL if on else (30, 44, 40)
        rect(a, x + 3 + o, y + h // 2 - 1 + o, 2, 2, lc)


def make_shufrep():
    a = new(92, 85, BODY)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        toggle(a, 0, y, 28, 15, "REPEAT", on, pressed)
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        toggle(a, x, 61, 23, 12, label, False, pressed, led="dot")
        toggle(a, x, 73, 23, 12, label, True, pressed, led="dot")
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp (56 x 24), playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, DISP)
    for y, on in ((0, True), (12, False)):
        col = MINT if on else MINT_DIM
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    # Standard sheet is 42 wide; 48 so the 9px "working" cell at x 39 fits too.
    a = new(48, 9, DISP)
    tri_right(a, 2, 1, 7, MINT)                       # playing
    rect(a, 9 + 2, 1, 2, 7, MINT)                     # paused
    rect(a, 9 + 5, 1, 2, 7, MINT)
    rect(a, 18 + 2, 2, 5, 5, MINT)                    # stopped
    rect(a, 36, 0, 3, 9, DISP)                        # not working
    rect(a, 39 + 1, 3, 1, 3, PINK)                    # working: a lit dot in its 3px slice
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, DISP)
    for n in range(10):
        serif_digit(a, 9 * n, 0, n)
    serif_digit(a, 90, 0, None)                       # blank cell
    if ex:
        rect(a, 99, 0, 9, 13, DISP)                   # minus
        rect(a, 99 + 2, 5, 5, 1, (18, 46, 38))
        rect(a, 99 + 2, 7, 5, 1, (18, 46, 38))
        rect(a, 99 + 2, 6, 5, 1, MINT)
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, DISP)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key, col * 5, row * 6, MINT)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------

GROOVE = (5, 12, 10)
TRACK_OFF = (22, 38, 34)


def make_posbar(main):
    a = new(307, 10, BODY)
    a[0:10, 0:248] = main[72:82, 16:264]
    rect(a, 0, 2, 248, 6, GROOVE)
    sunken(a, 0, 2, 248, 6, (48, 74, 66), BODY_LO)
    rect(a, 2, 4, 244, 2, (12, 26, 22))
    for x in range(8, 244, 12):
        px(a, x, 4, (40, 80, 68))
    pearl_thumb(a, 248, 0, 29, 10, False)
    pearl_thumb(a, 278, 0, 29, 10, True)
    return a


def slider_thumbs(a):
    pearl_thumb(a, 0, 422, 14, 11, True)
    pearl_thumb(a, 15, 422, 14, 11, False)


def make_volume(main):
    a = new(68, 433, BODY)
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        rect(a, 1, y + 3, 66, 7, GROOVE)
        sunken(a, 1, y + 3, 66, 7, (48, 74, 66), BODY_LO)
        level = (i + 1) / 28
        fill_to = 7 + round(level * 54)
        for x in range(2, 66):
            hgt = 1 + round(4 * (x - 2) / 63)
            top = y + 9 - hgt
            if x < fill_to:
                # the wings' iridescence along the wedge, brightening with the level
                c = ramp(WINGS, (x - 2) / 63)
                rect(a, x, top, 1, hgt, lerp((30, 60, 54), c, 0.45 + 0.55 * level))
            else:
                rect(a, x, top, 1, hgt, TRACK_OFF)
        rect(a, 0, y + 13, 68, 2, BODY)
    slider_thumbs(a)
    return a


def make_balance(main):
    a = new(68, 433, BODY)
    seat = main[57:72, 177:215]
    neutral = (110, 140, 130)
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        rect(a, 10, y + 3, 36, 7, GROOVE)
        sunken(a, 10, y + 3, 36, 7, (48, 74, 66), BODY_LO)
        t = i / 27
        colour = neutral if i == 0 else ramp([TEAL, LILAC, PINK, PEACH], t)
        reach = round(12 * t)
        for x in range(11, 45):
            d = abs(x - 28)
            hgt = 1 + round(4 * min(d, 16) / 16)
            top = y + 9 - hgt
            col = colour if d <= max(1, reach) else TRACK_OFF
            rect(a, x, top, 1, hgt, col)
        rect(a, 28, y + 2, 1, 2, MINT if i == 0 else (60, 90, 80))
        rect(a, 9, y + 13, 38, 2, BODY)
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = bar_bg(275)
    rect(a, 0, 0, 1, 14, BODY_HI)
    rect(a, 274, 0, 1, 14, BODY_LO)
    title = "EQUALIZER"
    sw = text_w(SERIF, TITLE)
    fw = text_w(FONT5, title)
    gw = sw + 6 + fw
    gx = (275 - gw) // 2
    tube(a, 6, 6, gx - 6 - 6, lit, phase=6)
    tube(a, gx + gw + 6, 6, 260 - (gx + gw + 6), lit, phase=gx + gw + 6)
    top, bot = (MINT_HI, (120, 214, 184)) if lit else ((128, 150, 142), (84, 104, 97))
    if lit:
        glow_text(a, SERIF, TITLE, gx, 2, lambda r: lerp(top, bot, r / 8), (28, 70, 58))
    else:
        draw_text(a, SERIF, TITLE, gx, 2, lambda r: lerp(top, bot, r / 8), shadow=BODY_LO)
    draw_text(a, FONT5, title, gx + sw + 6, 6, (PINK if lit else TITLE_DIM), shadow=BODY_LO)
    mini_button(a, 264, 3, "close", lit)
    return a


SLOT_BG = (12, 22, 19)


def eq_slider_frame(a, x, y, n):
    """14x63 slot whose lit column rises with the value (n of 0..27)."""
    rect(a, x, y, 14, 63, SLOT_BG)
    sunken(a, x, y, 14, 63, (44, 68, 61), BODY_LO)
    rect(a, x + 4, y + 2, 5, 59, GROOVE)
    sunken(a, x + 4, y + 2, 5, 59, (40, 62, 56), BODY_LO)
    v = n / 27
    centre = round((1 - v) * 51) + 5
    for r in range(3, 60):
        on = r >= centre
        # the column carries the wing gradient: teal at the floor, pink-peach at the top
        c = ramp(LEVEL, 1 - (r - 3) / 56)
        rect(a, x + 5, y + r, 3, 1, lerp(c, (30, 60, 54), 0.25) if on else (16, 30, 26))
    rect(a, x + 1, y + 30, 2, 1, (70, 110, 98))
    rect(a, x + 11, y + 30, 2, 1, (70, 110, 98))


def make_eqmain():
    a = new(275, 315, BODY)
    body(a, 0, 0, 275, 315)
    # the night photo's wings, in focus, across the window
    a[0:116, :] = photo("wings-tunnel.jpg", (420, 470, 1660, 993), (275, 116), bright=0.72, blur=0.4,
                        sat=1.05, tint=(-6, 0, -2))
    vignette(a, 0, 0, 275, 116, 0.45)
    raised(a, 0, 0, 275, 116, BODY_HI, BODY_LO)
    a[0:14, :] = eq_titlebar(True)
    # frosted strip behind the buttons row and the graph
    dim(a, 12, 16, 252, 16, 0.5)
    sunken(a, 85, 16, 115, 21)
    # slider bay: frosted glass, the wings faint through it
    dim(a, 16, 36, 245, 68, 0.5)
    sunken(a, 16, 36, 245, 68)
    rect(a, 39, 37, 1, 66, BODY_LO)
    rect(a, 40, 37, 1, 66, (44, 66, 60))
    # dB scale on its own dark backing
    rect(a, 41, 38, 33, 63, (7, 14, 12))
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, MINT_MID)
        rect(a, 42, yy + 2, 3, 1, (60, 96, 86))
        rect(a, 71, yy + 2, 3, 1, (60, 96, 86))
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    # labels row, on a dark strip
    dim(a, 12, 104, 252, 8, 0.75)
    text_center(a, TINY, "PREAMP", 28, 106, (170, 200, 190))
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, (170, 200, 190))
    rect(a, 3, 112, 269, 1, RUST)
    rect(a, 3, 113, 269, 1, BODY_LO)

    # under the window: buttons
    mini_button(a, 0, 125, "close", True, pressed=True)
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        toggle(a, x, 119, w, 12, label, on, pressed, led="dot")
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    pearl_thumb(a, 0, 164, 11, 11, False, grip="h")
    pearl_thumb(a, 0, 176, 11, 11, True, grip="h")
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        leather(a, 224, y, 44, 12, pressed)
        for i in range(226, 266):
            a[y + 2, i] = a[y + 3, i]
        o = 1 if pressed else 0
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 3 + o, MINT_HI if pressed else MINT,
                    shadow=None if pressed else BODY_LO)
    # graph
    rect(a, 0, 294, 113, 19, DISP)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, (16, 36, 30))
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, (22, 50, 42))
    for r in range(19):
        px(a, 115, 294 + r, ramp([PEACH, PINK, LILAC, TEAL, (70, 170, 156)], r / 18))
    for x in range(113):
        px(a, x, 314, (120, 100, 150) if x % 3 != 2 else DISP)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

PLATE_Y = 3
TUBE_Y = 9               # one continuous tube: the title's end pieces land off the 25px grid


def bar20(w, lit):
    """A 20px frame bar: the tunnel ceiling with a fluorescent tube (in phase across pieces)."""
    a = new(w, 20, BODY)
    for r in range(20):
        rect(a, 0, r, w, 1, lerp((26, 42, 37), (10, 18, 16), r / 19))
    grain(a, 0, 0, w, 20, 1.2)
    rect(a, 0, 0, w, 1, BODY_HI)
    return a


def bar_tube(t, x, w, lit):
    tube(t, x, TUBE_Y, w, lit, seg=1, gap=0)


def make_pledit():
    a = new(280, 186, BODY)
    body(a, 0, 0, 280, 186)
    for lit, y in ((True, 0), (False, 21)):
        # top tile
        t = bar20(25, lit)
        bar_tube(t, 0, 25, lit)
        rect(t, 0, 19, 25, 1, BODY_LO)
        a[y:y + 20, 127:152] = t
        # top-left corner
        t = bar20(25, lit)
        rect(t, 0, 0, 1, 20, BODY_HI)
        bar_tube(t, 4, 21, lit)
        rect(t, 11, 19, 14, 1, BODY_LO)
        rect(t, 11, 13, 1, 7, BODY_LO)
        a[y:y + 20, 0:25] = t
        # title
        t = bar20(100, lit)
        title = "ICARUS PLAYLIST"
        plate_cap_left(t, 0, PLATE_Y + 1, lit, 11)
        plate(t, 4, PLATE_Y + 1, 92, lit, 11)
        plate_cap_right(t, 96, PLATE_Y + 1, lit, 11)
        text_center(t, FONT5, title, 50, PLATE_Y + 4, TITLE_LIT if lit else TITLE_DIM)
        rect(t, 0, 19, 100, 1, BODY_LO)
        a[y:y + 20, 26:126] = t
        # top-right corner: close button, the scrollbar groove's top
        t = bar20(25, lit)
        rect(t, 24, 0, 1, 20, BODY_LO)
        bar_tube(t, 0, 11, lit)
        mini_button(t, 14, 3, "close", lit)
        rect(t, 0, 19, 6, 1, BODY_LO)
        rect(t, 5, 13, 1, 7, BODY_HI)
        rect(t, 9, 14, 10, 6, SLOT)
        rect(t, 9, 14, 10, 1, BODY_LO)
        rect(t, 9, 14, 1, 6, BODY_LO)
        rect(t, 18, 14, 1, 6, BODY_HI)
        a[y:y + 20, 153:178] = t

    # left side tile: wall tiles, period 29 down the side
    t = new(12, 29)
    tiles(t, 1, 0, 10, 29, ox=1, xs=(0,), xp=11, ys=(0, 14), yp=29)
    rect(t, 0, 0, 1, 29, BODY_HI)
    rect(t, 11, 0, 1, 29, BODY_LO)
    a[42:71, 0:12] = t
    # right side tile: list edge, scrollbar groove at 5..12, then tiles out to the edge
    t = new(20, 29)
    tiles(t, 14, 0, 5, 29, ox=0, xs=(5,), xp=6, ys=(0, 14), yp=29)
    rect(t, 0, 0, 4, 29, (20, 34, 30))
    rect(t, 0, 0, 1, 29, BODY_HI)
    rect(t, 3, 0, 1, 29, BODY_LO)
    rect(t, 19, 0, 1, 29, BODY_LO)
    rect(t, 4, 0, 10, 29, SLOT)
    rect(t, 4, 0, 1, 29, BODY_LO)
    rect(t, 13, 0, 1, 29, BODY_HI)
    rect(t, 8, 0, 2, 29, (16, 30, 26))
    a[42:71, 31:51] = t
    # close pressed, scroll handles
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        pearl_thumb(a, x, 53, 8, 18, sel, grip="h")

    # bottom pieces: the tiled wall with its rust band; pieces sit on 25px steps
    def bottom_base(w, ox):
        t = new(w, 38)
        tiles(t, 0, 1, w, 30, ox=ox, oy=0, xs=(0, 12), xp=25, ys=(0, 15), yp=15)
        rect(t, 0, 0, w, 1, BODY_HI)
        rect(t, 0, 31, w, 1, GROUT)
        rect(t, 0, 32, w, 3, RUST)
        rect(t, 0, 32, w, 1, lerp(RUST, (255, 255, 255), 0.15))
        grain(t, 0, 32, w, 3, 2)
        rect(t, 0, 35, w, 2, GROUT)
        rect(t, 0, 37, w, 1, BODY_LO)
        return t

    t = bottom_base(125, 0)
    rect(t, 0, 0, 1, 38, BODY_HI)
    rect(t, 1, 0, 11, 1, TILE)
    rect(t, 11, 0, 1, 1, BODY_LO)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        leather(t, bx, 8, 22, 18, False)
        text_center(t, TINY, lbl, bx + 11, 15, MINT, shadow=BODY_LO)
    a[72:110, 0:125] = t

    t = bottom_base(150, 0)
    rect(t, 149, 0, 1, 38, BODY_LO)
    rect(t, 130, 0, 19, 1, TILE)
    rect(t, 130, 0, 1, 1, BODY_HI)
    # a dark backing for the readouts and mini transport
    rect(t, 1, 6, 101, 28, (8, 16, 14))
    sunken(t, 1, 6, 101, 28)
    display_box(t, 6, 9, 56, 8)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        leather(t, bx, 22, 10, 10, False)
        for i in range(bx + 2, bx + 8):
            t[24, i] = t[25, i]
        mini_transport_icon(t, kind, bx, 22)
    display_box(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, MINT_MID)
    rect(t, 84, 22 + 5, 1, 1, MINT_MID)
    leather(t, 106, 8, 22, 18, False)
    text_center(t, TINY, "LIST", 117, 15, MINT, shadow=BODY_LO)
    # resize grip
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx, gy, MINT)
            px(t, gx + 1, gy + 1, BODY_LO)
    a[72:110, 126:276] = t

    t = bottom_base(25, 0)
    a[0:38, 179:204] = t
    return a


def mini_transport_icon(a, kind, x, y):
    ink = MINT
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


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_gen():
    a = new(194, 109, BODY)
    body(a, 0, 0, 194, 109)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn):
            t = bar20(25, lit)
            fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 1, 20, BODY_HI)
            bar_tube(t, 4, 21, lit)

        def left_end(t):
            bar_tube(t, 0, 15, lit)
            plate_cap_left(t, 17, PLATE_Y, lit)
            plate(t, 21, PLATE_Y, 4, lit)

        def centre(t):
            plate(t, 0, PLATE_Y, 25, lit)

        def right_end(t):
            plate(t, 0, PLATE_Y, 4, lit)
            plate_cap_right(t, 4, PLATE_Y, lit)
            bar_tube(t, 10, 15, lit)

        def fill(t):
            bar_tube(t, 0, 25, lit)

        def right(t):
            bar_tube(t, 0, 11, lit)
            mini_button(t, 14, 3, "close", lit)
            rect(t, 24, 0, 1, 20, BODY_LO)

        piece(0, left)
        piece(26, left_end)
        piece(52, centre)
        piece(78, right_end)
        piece(104, fill)
        piece(130, right)

    # bottom caps and fill (14 tall): a tile row over the rust band
    def bottom(w, grip, left_edge):
        t = new(w, 14)
        tiles(t, 0, 0, w, 8, ox=0, oy=0, xs=(0, 12), xp=25, ys=(0,), yp=8)
        rect(t, 0, 8, w, 1, GROUT)
        rect(t, 0, 9, w, 2, RUST)
        rect(t, 0, 11, w, 2, GROUT)
        rect(t, 0, 13, w, 1, BODY_LO)
        if left_edge:
            rect(t, 0, 0, 1, 14, BODY_HI)
        else:
            rect(t, w - 1, 0, 1, 14, BODY_LO)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 7 - 3 * j
                    px(t, gx, gy, MINT)
                    px(t, gx + 1, gy + 1, BODY_LO)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]  # fill tile: no right edge
    # sides: tiles, period 29
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        if outer_left:
            tiles(t, 1, 0, w - 2, h, ox=0, xs=(w - 2,), xp=w - 1, ys=(0, 14), yp=29)
            rect(t, 0, 0, 1, h, BODY_HI)
            rect(t, w - 1, 0, 1, h, BODY_LO)
        else:
            tiles(t, 1, 0, w - 2, h, ox=0, xs=(w - 2,), xp=w - 1, ys=(0, 14), yp=29)
            rect(t, 0, 0, 1, h, BODY_HI)
            rect(t, w - 1, 0, 1, h, BODY_LO)
        a[42:42 + h, x:x + w] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: each row starts at x 1, letters in their own cells, 1px separators of x 0's colour
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            rect(a, x, y, w, 7, DISP if lit else (10, 16, 14))
            draw_text(a, FONT5, c, x, y + 1, TITLE_LIT if lit else TITLE_DIM)
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------

GENEX_COLOURS = [
    (14, 26, 23),      # item background
    (159, 216, 196),   # item text
    (16, 28, 25),      # window background
    (200, 240, 224),   # button text
    (214, 236, 228),   # window text
    (40, 66, 59),      # dividers, sunken borders
    (31, 74, 66),      # selection bar
    (24, 40, 36),      # list header background
    (240, 168, 200),   # list header text
    (70, 100, 92),     # header frame, light
    (4, 8, 7),         # header frame, dark
    (40, 90, 80),      # header frame, pressed
    (16, 28, 25),      # header dead area
    (30, 50, 45),      # scrollbar
    (111, 214, 200),   # scrollbar 2
    (44, 70, 63),      # scrollbar pressed
    (200, 176, 224),   # scrollbar pressed 2
    (10, 18, 16),      # scrollbar dead area
]


def make_genex():
    a = new(256, 64, BODY)
    body(a, 0, 1, 256, 63)
    rect(a, 0, 0, 256, 1, BODY)
    for i, c in enumerate(GENEX_COLOURS):
        px(a, 48 + 2 * i, 0, c)
    leather(a, 0, 1, 47, 15, False)
    leather(a, 0, 16, 47, 15, True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------

VISCOLOR = (
    [(DISP, "background"), ((18, 40, 33), "dots")]
    + [(ramp([PEACH, PINK, LILAC, TEAL, (60, 170, 150), (24, 92, 80)], i / 15),
        f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}") for i in range(16)]
    + [(MINT_HI, "oscilloscope 1"), (MINT, "oscilloscope 2"), ((120, 200, 176), "oscilloscope 3"),
       ((80, 150, 130), "oscilloscope 4"), ((50, 104, 90), "oscilloscope 5"), ((255, 240, 248), "peaks")]
)

PL_NORMAL = (0x9F, 0xD8, 0xC4)
PL_CURRENT = (0xF0, 0xA8, 0xC8)
PL_BG = (0x0E, 0x1A, 0x17)
PL_SEL = (0x1F, 0x4A, 0x42)


def hexc(c):
    return "#%02X%02X%02X" % c


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in VISCOLOR:
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={hexc(PL_NORMAL)}\nCurrent={hexc(PL_CURRENT)}\nNormalBG={hexc(PL_BG)}\n"
                f"SelectedBG={hexc(PL_SEL)}\nMbBG={hexc(PL_BG)}\nMbFG={hexc(PL_NORMAL)}\nFont=Arial\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n", encoding="utf-8") as f:
        f.write(
            "ARTMS Club Icarus — a personal fan skin.\n"
            "ARTMS logo, album art and photos © MODHAUS; for private use only.\n"
        )


# ------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------

SHEETS = {}


def build():
    main = make_main()
    sheets = {
        "main.bmp": main,
        "titlebar.bmp": make_titlebar(),
        "cbuttons.bmp": make_cbuttons(),
        "shufrep.bmp": make_shufrep(),
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
    for name, arr in sheets.items():
        SHEETS[name[:-4]] = save(arr, name)
    write_text_files()
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "readme.txt"]
    wsz = os.path.join(HERE, WSZ_NAME)
    with zipfile.ZipFile(wsz, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(os.path.join(OUT, n), n)
    return names


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
for _k, _v in {"<": "[", ">": "]", "{": "[", "}": "]"}.items():
    FONT_LOOKUP[_k] = FONT_LOOKUP[_v]


def draw_bitmap_text(dst, s, x, y):
    text = SHEETS["text"]
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, text, (col * 5, row * 6, 5, 6), x, y)
        x += 5


def viscolors():
    return [c for c, _ in VISCOLOR]


def preview_main(lit, state):
    S = SHEETS
    img = Image.new("RGB", (275, 116))
    img.paste(S["main"], (0, 0))
    blit(img, S["titlebar"], (27, 0 if lit else 15, 275, 14), 0, 0)
    cb = {"previous": (0, 23, 18), "play": (23, 23, 18), "pause": (46, 23, 18), "stop": (69, 23, 18),
          "next": (92, 22, 18)}
    pos = {"previous": (16, 88), "play": (39, 88), "pause": (62, 88), "stop": (85, 88), "next": (108, 88)}
    for k, (x, w, h) in cb.items():
        blit(img, S["cbuttons"], (x, 18 if state["pressed"] == k else 0, w, h), *pos[k])
    blit(img, S["cbuttons"], (114, 16 if state["pressed"] == "eject" else 0, 22, 16), 136, 89)
    # eq / pl toggles
    for name, x0, on in (("eq", 0, state["eq"]), ("pl", 23, state["pl"])):
        pressed = state["pressed"] == name
        sx = x0 + (46 if pressed else 0)
        blit(img, S["shufrep"], (sx, 73 if on else 61, 23, 12), 219 + x0, 58)
    # clutter
    blit(img, S["titlebar"], (304, 0, 8, 43), 10, 22)
    spr = {"O": (304, 47, 8, 8, 3), "A": (312, 55, 8, 7, 11), "I": (320, 62, 8, 7, 18), "D": (328, 69, 8, 8, 25),
           "V": (336, 77, 8, 7, 33)}
    for L in state["clutter"]:
        x, y, w, h, oy = spr[L]
        blit(img, S["titlebar"], (x, y, w, h), 10, 22 + oy)
    # shuffle/repeat
    for name, x0, w, on, dst in (("shuffle", 28, 47, state["shuffle"], 164), ("repeat", 0, 28, state["repeat"], 210)):
        row = (2 if on else 0) + (1 if state["pressed"] == name else 0)
        blit(img, S["shufrep"], (x0, row * 15, w, 15), dst, 89)
    blit(img, S["playpaus"], (0 if state["playing"] else 9, 0, 9, 9), 26, 28)
    blit(img, S["monoster"], (29, 12 if state["stereo"] else 0, 27, 12), 212, 41)
    blit(img, S["monoster"], (0, 0 if state["stereo"] else 12, 29, 12), 239, 41)
    # posbar
    blit(img, S["posbar"], (0, 0, 248, 10), 16, 72)
    tl = round(state["pos"] * 219)
    blit(img, S["posbar"], (278 if state["seek"] else 248, 0, 29, 10), 16 + tl, 72)
    # volume
    v = state["volume"]
    idx = max(0, round(v / 100 * 28) - 1)
    blit(img, S["volume"], (0, idx * 15, 68, 13), 107, 57)
    blit(img, S["volume"], (0 if state["vdrag"] else 15, 422, 14, 11), 107 + round(v / 100 * 54), 58)
    b = state["balance"]
    idx = int(abs(b) / 100 * 27)
    blit(img, S["balance"], (9, idx * 15, 38, 13), 177, 57)
    blit(img, S["balance"], (15, 422, 14, 11), 177 + round((b + 100) / 200 * 24), 58)
    # time
    secs = state["time"]
    m, s = secs // 60, secs % 60
    nums = S["nums_ex"]
    if state["remaining"]:
        blit(img, nums, (99, 0, 9, 13), 38, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    # title: the space cell across the box, then the title (the app uses a TrueType font; text.bmp here)
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    draw_bitmap_text(img, state["title"][:30], 111, 24)
    draw_bitmap_text(img, "192", 111, 43)
    draw_bitmap_text(img, "44", 156, 43)
    # analyzer
    cols = viscolors()
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
            vp[x, y] = cols[min(17, max(2, 2 - 2 + y))]
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=PL_BG)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 9)
    except OSError:
        font = ImageFont.load_default()
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=PL_SEL)
        col = PL_CURRENT if i == 1 else PL_NORMAL
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
    # the picture: the album cover, cropped to fill (the app draws the playing track's art)
    pw, ph = w - 22, h - 34
    cov = Image.open(os.path.join(SRC, "cover.webp")).convert("RGB")
    top = (640 - round(640 * ph / pw)) // 2
    img.paste(cov.crop((0, top, 640, top + round(640 * ph / pw))).resize((pw, ph), Image.LANCZOS), (11, 20))
    return img


def preview():
    rows = [("Sample Artist - Underpass", "4:12"), ("Sample Artist - Fluorescent", "3:47"),
            ("Sample Artist - Feathers", "5:03"), ("Sample Artist - Last Train", "2:58"),
            ("Sample Artist - Tile & Grout", "6:21"), ("Sample Artist - Mint Light", "3:33"),
            ("Sample Artist - Leather", "4:40"), ("Sample Artist - Wax Wings", "3:09"),
            ("Sample Artist - Sun Too Close", "5:51"), ("Sample Artist - Night Walk", "4:05"),
            ("Sample Artist - Exit B", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title="ARTMS - CLUB ICARUS  ***", bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="PAUSED: UNDERPASS (NIGHT)", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
    out.save(os.path.join(HERE, "preview.png"))


if __name__ == "__main__":
    names = build()
    preview()
    for n in names:
        p = os.path.join(OUT, n)
        if n.endswith(".bmp"):
            im = Image.open(p)
            print(f"{n:14s} {im.size[0]}x{im.size[1]} {im.mode}")
        else:
            print(f"{n:14s} {os.path.getsize(p)} bytes")
