#!/usr/bin/python3
"""Windows 7: a classic Winamp 2.x skin in the style of Windows 7's Aero theme, generated procedurally.

Everything is drawn here from code: faked Aero glass (a blue gradient with a blurred mottle and
diagonal light streaks), Windows 7 style command buttons, trackbars, a green progress bar, glossy
dark media buttons and hand-made pixel fonts. The one outside asset is the Windows flag in the
About spot, rasterised at build time from source/logo-windows-flag/flag.svg (private use only).

Writes the bitmaps and text files into out/, zips them flat into Windows-7.wsz, and draws
preview.png (the windows assembled from the sprites at their real positions, 2x).
"""

import os
import subprocess
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
SCRATCH = os.path.join(OUT, "scratch")
os.makedirs(SCRATCH, exist_ok=True)
FLAG_SVG = os.path.join(HERE, "source", "logo-windows-flag", "flag.svg")
WSZ_NAME = "Windows-7.wsz"

# ------------------------------------------------------------------------------------------
# Palette
# ------------------------------------------------------------------------------------------

GLASS_TOP = (169, 201, 236)     # #a9c9ec
GLASS_BOT = (111, 160, 216)     # #6fa0d8
PALE = (216, 228, 242)          # what an inactive window's glass washes toward
EDGE = (36, 58, 88)             # 1px outer edge of the glass
EDGE_DIM = (98, 118, 144)
FACE = (240, 240, 240)          # the window face (#f0f0f0)
FACE_LINE = (122, 142, 168)     # the client area's edge inside the glass
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
INK = (0, 0, 0)                 # caption text
INK_DIM = (64, 72, 84)
TEXT = (24, 24, 24)             # text.bmp
LABEL = (96, 102, 110)          # small grey labels on the face
SEL_BLUE = (204, 232, 255)      # #cce8ff
CUR_BLUE = (30, 95, 180)        # #1e5fb4
VIS_BG = (9, 16, 25)            # the dark display's lower half (and viscolor's background)
VIS_DOT = (22, 36, 52)
SEP = (255, 0, 255)             # gen.bmp letter separators (never shown)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    """Colour along a list of stops, t in 0..1."""
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def new(w, h, col=FACE):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):y + h, max(0, x):x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def blend(a, x, y, col, t):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = lerp(tuple(int(v) for v in a[y, x]), col, t)


def outline(a, x, y, w, h, col):
    rect(a, x, y, w, 1, col)
    rect(a, x, y + h - 1, w, 1, col)
    rect(a, x, y, 1, h, col)
    rect(a, x + w - 1, y, 1, h, col)


def composite(a, x, y, alpha, col, opacity=1.0):
    """Blends a solid colour (or an HxWx3 array) into a at (x, y) through alpha (float HxW)."""
    h, w = alpha.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(a.shape[1], x + w), min(a.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    al = alpha[y0 - y:y1 - y, x0 - x:x1 - x, None] * opacity
    dst = a[y0:y1, x0:x1].astype(np.float64)
    src = np.array(col, dtype=np.float64)
    if src.ndim == 3:
        src = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a[y0:y1, x0:x1] = np.round(dst * (1 - al) + src * al).astype(np.int32)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def poly_mask(w, h, pts, s=4):
    """Coverage (0..1) of a polygon in pixel units (pixel (x, y) spans x..x+1), supersampled."""
    im = Image.new("L", (w * s, h * s), 0)
    ImageDraw.Draw(im).polygon([(x * s, y * s) for x, y in pts], fill=255)
    arr = np.asarray(im, dtype=np.float64) / 255
    return arr.reshape(h, s, w, s).mean(axis=(1, 3))


def round_mask(w, h, r):
    """Coverage of a rounded rectangle w x h with corner radius r, 4x supersampled."""
    s = 4
    yy, xx = np.mgrid[0:h * s, 0:w * s]
    fx = (xx + 0.5) / s
    fy = (yy + 0.5) / s
    dx = np.maximum(0, np.maximum(r - fx, fx - (w - r)))
    dy = np.maximum(0, np.maximum(r - fy, fy - (h - r)))
    inside = (dx * dx + dy * dy) <= r * r
    return inside.reshape(h, s, w, s).mean(axis=(1, 3))


def disc_mask(w, h, cx, cy, r):
    s = 4
    yy, xx = np.mgrid[0:h * s, 0:w * s]
    fx = (xx + 0.5) / s
    fy = (yy + 0.5) / s
    inside = (fx - cx) ** 2 + (fy - cy) ** 2 <= r * r
    return inside.reshape(h, s, w, s).mean(axis=(1, 3))


def rows_face(w, h, stops):
    """HxWx3 float: a vertical gradient through `stops` [(t, colour), ...]."""
    out = np.zeros((h, w, 3))
    for r in range(h):
        t = r / max(1, h - 1)
        for k in range(len(stops) - 1):
            t0, c0 = stops[k]
            t1, c1 = stops[k + 1]
            if t0 <= t <= t1:
                out[r, :] = lerp(c0, c1, 0 if t1 == t0 else (t - t0) / (t1 - t0))
                break
    return out


def shape(a, x, y, outer, face, border, inner=None):
    """Paints a shape: `outer` coverage takes the border colour, `inner` (default: outer shrunk
    by a pixel all round) the face (an HxWx3 array)."""
    h, w = outer.shape
    if inner is None:
        inner = np.zeros_like(outer)
        inner[1:h - 1, 1:w - 1] = np.minimum(outer[1:h - 1, 1:w - 1],
                                             np.minimum.reduce([outer[0:h - 2, 1:w - 1], outer[2:h, 1:w - 1],
                                                                outer[1:h - 1, 0:w - 2], outer[1:h - 1, 2:w]]))
    composite(a, x, y, outer, border)
    composite(a, x, y, inner, face)
    return inner


def blur(m, r, wrap=False):
    """Box blur (radius r) along both axes, three passes; zero padded unless wrap."""
    out = m.astype(np.float64)
    for _ in range(3):
        for axis in (0, 1):
            acc = np.zeros_like(out)
            if wrap:
                for d in range(-r, r + 1):
                    acc += np.roll(out, d, axis=axis)
            else:
                pad = [(0, 0), (0, 0)]
                pad[axis] = (r, r)
                p = np.pad(out, pad)
                n = out.shape[axis]
                for d in range(2 * r + 1):
                    acc += p[d:d + n, :] if axis == 0 else p[:, d:d + n]
            out = acc / (2 * r + 1)
    return out


# ------------------------------------------------------------------------------------------
# Aero glass
# ------------------------------------------------------------------------------------------


def mottle(X, Y, seed, px_=None, py_=None, n=12, lam=(14, 46)):
    """Soft 'what's behind the glass' blobs: a sum of sinusoids, periodic in x (px_) or y (py_)
    when asked, so tiles repeat seamlessly. Mean 0, std about 1."""
    rng = np.random.default_rng(seed)
    acc = np.zeros(X.shape)
    for _ in range(n):
        lx = rng.uniform(*lam)
        ly = rng.uniform(*lam)
        fx = (max(1, round(px_ / lx)) / px_) if px_ else 1 / lx
        fy = (max(1, round(py_ / ly)) / py_) if py_ else 1 / ly
        if rng.random() < 0.5:
            fx = -fx
        ph = rng.uniform(0, 2 * np.pi)
        acc += np.sin(2 * np.pi * (fx * X + fy * Y) + ph)
    return acc / np.sqrt(n / 2)


STREAKS = [(18, 9, 0.16), (52, 3, 0.20), (61, 2, 0.10), (120, 16, 0.12), (168, 4, 0.18), (176, 2, 0.08),
           (238, 11, 0.13), (290, 3, 0.17), (300, 6, 0.08), (352, 13, 0.11)]
STREAK_SLOPE = 0.62


def streaks(X, Y, period=400.0, scale=1.0):
    """Diagonal light streaks ('/' bands) along u = x + k*y, periodic in u."""
    u = X + STREAK_SLOPE * Y
    s = np.zeros(X.shape)
    for c, w, k in STREAKS:
        c = c * period / 400.0
        d = np.abs(((u - c + period / 2) % period) - period / 2)
        s += k * np.exp(-(d / (w * scale)) ** 2)
    return np.clip(s, 0, 0.5)


def glass_base(t, lit=True):
    c = ramp([GLASS_TOP, GLASS_BOT], t)
    return c if lit else lerp(c, PALE, 0.55)


def glass(w, h, t_rows, lit=True, seed=1, ox=0, oy=0, px_=None, py_=None, period=400.0, mott=5.0, streak=1.0):
    """Float HxWx3 Aero glass. t_rows: the gradient position of each row (0 top .. 1 bottom)."""
    Y, X = np.mgrid[0:h, 0:w].astype(np.float64)
    X += ox
    Y += oy
    base = np.array([glass_base(t, lit) for t in t_rows], dtype=np.float64)[:, None, :] * np.ones((1, w, 1))
    m = mottle(X, Y, seed, px_, py_)
    base += (m * mott)[..., None] * np.array([0.8, 0.9, 1.0])
    s = streaks(X, Y, period) * streak * (1.0 if lit else 0.7)
    base = base + (255 - base) * s[..., None]
    return base


def glass_edges(a, x, y, w, h, lit=True, top=True, bottom=True, left=True, right=True, round_top=True):
    """The 1px dark outer edge and the 1px light inner highlight round a glass area."""
    e = EDGE if lit else EDGE_DIM
    hi = 0.55 if lit else 0.45
    if top:
        for xx in range(x + 1, x + w - 1):
            blend(a, xx, y + 1, WHITE, hi)
        rect(a, x, y, w, 1, e)
    if bottom:
        for xx in range(x + 1, x + w - 1):
            blend(a, xx, y + h - 2, WHITE, hi * 0.6)
        rect(a, x, y + h - 1, w, 1, e)
    if left:
        for yy in range(y + (1 if top else 0), y + h - (1 if bottom else 0)):
            blend(a, x + 1, yy, WHITE, hi)
        rect(a, x, y, 1, h, e)
    if right:
        for yy in range(y + (1 if top else 0), y + h - (1 if bottom else 0)):
            blend(a, x + w - 2, yy, WHITE, hi * 0.8)
        rect(a, x + w - 1, y, 1, h, e)
    if round_top and top:
        # rounded top corners: the corner pixel in the edge's colour, the next ones softened
        for cx, dx in ((x, 1), (x + w - 1, -1)):
            if (dx == 1 and left) or (dx == -1 and right):
                blend(a, cx + dx, y + 1, e, 0.65)
                blend(a, cx + 2 * dx, y + 1, e, 0.2)
                blend(a, cx + dx, y + 2, e, 0.2)


def to_int(f):
    return np.clip(np.round(f), 0, 255).astype(np.int32)


# ------------------------------------------------------------------------------------------
# Pixel fonts (all designed for this skin)
# ------------------------------------------------------------------------------------------

def G(*rows):
    return list(rows)


# 5-row font for text.bmp (dark on white).
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
    "M": G("#...#", "##.##", "#.#.#", "#...#", "#...#"),
    "N": G("#..#", "##.#", "#.##", "#..#", "#..#"),
    "O": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "P": G("##.", "#.#", "##.", "#..", "#.."),
    "Q": G(".#.", "#.#", "#.#", "##.", ".##"),
    "R": G("##.", "#.#", "##.", "#.#", "#.#"),
    "S": G(".##", "#..", ".#.", "..#", "##."),
    "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#.#", "#.#", "#.#", "#.#", "###"),
    "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#...#", "#...#", "#.#.#", "##.##", "#...#"),
    "X": G("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": G("###", "..#", ".#.", "#..", "###"),
    " ": G("..", "..", "..", "..", ".."),
}
for _c in "0123456789+-.":
    TINY[_c] = FONT5[_c]

# The caption font, Segoe-like: capitals 6 rows, x-height 4, descenders 2 (8 rows in all).
_CAPS = {
    "A": G("..#..", ".#.#.", "#...#", "#####", "#...#", "#...#"),
    "B": G("###.", "#..#", "###.", "#..#", "#..#", "###."),
    "C": G(".###", "#...", "#...", "#...", "#...", ".###"),
    "D": G("###.", "#..#", "#..#", "#..#", "#..#", "###."),
    "E": G("####", "#...", "###.", "#...", "#...", "####"),
    "F": G("####", "#...", "###.", "#...", "#...", "#..."),
    "G": G(".###.", "#....", "#....", "#..##", "#...#", ".###."),
    "H": G("#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": G("#", "#", "#", "#", "#", "#"),
    "J": G("..#", "..#", "..#", "..#", "..#", "##."),
    "K": G("#..#", "#.#.", "##..", "##..", "#.#.", "#..#"),
    "L": G("#...", "#...", "#...", "#...", "#...", "####"),
    "M": G("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#"),
    "N": G("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": G(".###.", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": G("###.", "#..#", "#..#", "###.", "#...", "#..."),
    "Q": G(".###.", "#...#", "#...#", "#...#", "#..#.", ".##.#"),
    "R": G("###.", "#..#", "#..#", "###.", "#.#.", "#..#"),
    "S": G(".###", "#...", ".##.", "...#", "...#", "###."),
    "T": G("#####", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": G("#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": G("#...#", "#...#", ".#.#.", ".#.#.", ".#.#.", "..#.."),
    "W": G("#...#", "#...#", "#.#.#", "#.#.#", ".#.#.", ".#.#."),
    "X": G("#...#", ".#.#.", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": G("#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": G("####", "...#", "..#.", ".#..", "#...", "####"),
    "7": G("####", "...#", "..#.", "..#.", ".#..", ".#.."),
}
_LOWER = {
    "a": G("....", "....", ".###", "#..#", "#..#", ".###", "....", "...."),
    "b": G("#...", "#...", "###.", "#..#", "#..#", "###.", "....", "...."),
    "c": G("...", "...", ".##", "#..", "#..", ".##", "...", "..."),
    "d": G("...#", "...#", ".###", "#..#", "#..#", ".###", "....", "...."),
    "e": G("....", "....", ".##.", "####", "#...", ".###", "....", "...."),
    "f": G("..#", ".#.", "###", ".#.", ".#.", ".#.", "...", "..."),
    "g": G("....", "....", ".###", "#..#", "#..#", ".###", "...#", ".##."),
    "h": G("#...", "#...", "###.", "#..#", "#..#", "#..#", "....", "...."),
    "i": G("#", ".", "#", "#", "#", "#", ".", "."),
    "j": G(".#", "..", ".#", ".#", ".#", ".#", ".#", "#."),
    "k": G("#..", "#..", "#.#", "##.", "##.", "#.#", "...", "..."),
    "l": G("#", "#", "#", "#", "#", "#", ".", "."),
    "m": G(".....", ".....", "####.", "#.#.#", "#.#.#", "#.#.#", ".....", "....."),
    "n": G("....", "....", "###.", "#..#", "#..#", "#..#", "....", "...."),
    "o": G("....", "....", ".##.", "#..#", "#..#", ".##.", "....", "...."),
    "p": G("....", "....", "###.", "#..#", "#..#", "###.", "#...", "#..."),
    "q": G("....", "....", ".###", "#..#", "#..#", ".###", "...#", "...#"),
    "r": G("...", "...", "#.#", "##.", "#..", "#..", "...", "..."),
    "s": G("...", "...", ".##", "#..", "..#", "##.", "...", "..."),
    "t": G("...", ".#.", "###", ".#.", ".#.", "..#", "...", "..."),
    "u": G("....", "....", "#..#", "#..#", "#..#", ".###", "....", "...."),
    "v": G("...", "...", "#.#", "#.#", "#.#", ".#.", "...", "..."),
    "w": G(".....", ".....", "#...#", "#.#.#", "#.#.#", ".#.#.", ".....", "....."),
    "x": G("...", "...", "#.#", ".#.", ".#.", "#.#", "...", "..."),
    "y": G("....", "....", "#..#", "#..#", "#..#", ".###", "...#", ".##."),
    "z": G("####", "..#.", ".#..", "####"),
}
CAPTION = {}
for _k, _g in _CAPS.items():
    CAPTION[_k] = _g + ["." * len(_g[0])] * 2
for _k, _g in _LOWER.items():
    if len(_g) == 4:
        _g = ["." * len(_g[0])] * 2 + _g + ["." * len(_g[0])] * 2
    CAPTION[_k] = _g
CAPTION[" "] = G("..", "..", "..", "..", "..", "..", "..", "..")


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
        if shadow is not None:
            for r, row in enumerate(g):
                for k, ch in enumerate(row):
                    if ch == "#":
                        px(a, x + k + 1, y + r + 1, shadow)
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col(r) if callable(col) else col)
        x += len(g[0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1, shadow=None):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow)


def text_mask(font, s, w, h, x, y, gap=1):
    m = np.zeros((h, w))
    for c in s:
        if c not in font:
            continue
        for r, row in enumerate(font[c]):
            for k, ch in enumerate(row):
                if ch == "#" and 0 <= y + r < h and 0 <= x + k < w:
                    m[y + r, x + k] = 1
        x += len(font[c][0]) + gap
    return m


def caption(a, s, x, y, lit=True, glow=0.85):
    """Caption text the Aero way: black, over a soft white glow that hugs it."""
    h, w = a.shape[:2]
    m = text_mask(CAPTION, s, w, h, x, y)
    d = m.copy()
    d[1:, :] = np.maximum(d[1:, :], m[:-1, :])
    d[:-1, :] = np.maximum(d[:-1, :], m[1:, :])
    d[:, 1:] = np.maximum(d[:, 1:], d[:, :-1])
    d[:, :-1] = np.maximum(d[:, :-1], d[:, 1:])
    g = blur(d, 2)
    g = np.clip(g / max(1e-6, g.max()) * 1.6, 0, 1) * (glow if lit else glow * 0.7)
    composite(a, 0, 0, g, WHITE)
    composite(a, 0, 0, m, INK if lit else INK_DIM)


# ------------------------------------------------------------------------------------------
# Windows 7 controls
# ------------------------------------------------------------------------------------------

# Command buttons: border, then the upper half's gradient and the lower half's.
BTN = {
    "normal": ((112, 112, 112), (242, 242, 242), (235, 235, 235), (221, 221, 221), (207, 207, 207)),
    "hot": ((60, 127, 177), (234, 246, 253), (217, 240, 252), (190, 230, 253), (167, 217, 245)),
    "pressed": ((44, 98, 139), (229, 244, 252), (196, 229, 246), (152, 209, 239), (104, 179, 219)),
    "onpressed": ((28, 76, 114), (206, 232, 249), (172, 214, 240), (118, 186, 228), (80, 156, 206)),
}


def win_button(a, x, y, w, h, style="normal", r=2.5):
    border, t0, t1, b0, b1 = BTN[style]
    face = rows_face(w, h, [(0, t0), (0.48, t1), (0.5, b0), (1, b1)])
    outer = round_mask(w, h, r)
    inner = shape(a, x, y, outer, face, border)
    # the inner light line (pressed buttons get an inner shadow instead)
    if style in ("normal", "hot"):
        for xx in range(x + 2, x + w - 2):
            blend(a, xx, y + 1, WHITE, 0.8)
        for yy in range(y + 2, y + h - 2):
            blend(a, x + 1, yy, WHITE, 0.45)
            blend(a, x + w - 2, yy, WHITE, 0.45)
    else:
        for xx in range(x + 2, x + w - 2):
            blend(a, xx, y + 1, border, 0.25)
        for yy in range(y + 2, y + h // 2):
            blend(a, x + 1, yy, border, 0.15)
    return inner


def button_label(a, font, s, x, y, w, h, style, dy=0):
    o = 1 if style in ("pressed", "onpressed") else 0
    col = (16, 32, 56) if style != "normal" else (30, 30, 30)
    tw = text_w(font, s)
    rows = len(next(iter(font.values())))
    if font is CAPTION:
        rows = 6
    draw_text(a, font, s, x + (w - tw) // 2 + o, y + (h - rows) // 2 + o + dy, col)


def caption_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 caption button faces: glassy (min/shade/options), red glossy close."""
    if kind == "close" and (lit or pressed):
        if pressed:
            stops = [(0, (196, 120, 110)), (0.45, (160, 52, 46)), (0.5, (128, 28, 24)), (1, (178, 58, 40))]
        else:
            stops = [(0, (240, 182, 170)), (0.45, (214, 104, 92)), (0.5, (199, 69, 69)), (1, (232, 120, 84))]
        ink, inkline = WHITE, (96, 18, 18)
    elif kind == "close":
        stops = [(0, (236, 242, 250)), (0.45, (206, 220, 238)), (0.5, (186, 204, 228)), (1, (214, 228, 244))]
        ink, inkline = (250, 250, 250), (70, 84, 104)
    else:
        if pressed:
            stops = [(0, (170, 196, 226)), (0.45, (120, 156, 202)), (0.5, (86, 126, 182)), (1, (112, 156, 210))]
        elif lit:
            stops = [(0, (238, 245, 252)), (0.45, (200, 220, 244)), (0.5, (160, 192, 230)), (1, (190, 216, 244))]
        else:
            stops = [(0, (240, 245, 250)), (0.45, (216, 228, 242)), (0.5, (196, 212, 232)), (1, (218, 230, 244))]
        ink, inkline = WHITE, (34, 56, 88) if lit or pressed else (88, 102, 122)
    face = rows_face(9, 9, stops)
    a[y:y + 9, x:x + 9] = to_int(face)
    for xx in range(x, x + 9):
        blend(a, xx, y, WHITE, 0.35 if not pressed else 0.1)
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    pts = []
    if kind == "minimize":
        pts = [(c, 6) for c in range(2, 7)]
    elif kind == "shade":
        pts = [(c, 2) for c in range(2, 7)] + [(c, 3) for c in range(2, 7)] + [(2, r) for r in range(4, 7)] + \
              [(6, r) for r in range(4, 7)] + [(c, 6) for c in range(3, 6)]
    elif kind == "close":
        for i in range(5):
            pts += [(2 + i, 2 + i), (6 - i, 2 + i)]
        pts += [(3 + i, 2 + i) for i in range(4)] + [(5 - i, 2 + i) for i in range(4)]
    elif kind == "options":
        pts = [(c, r) for c in range(2, 7) for r in (2, 4, 6)]
    pset = set(pts)
    for (c, r) in pts:
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1)):
            if (c + dc, r + dr) not in pset and 0 <= c + dc < 9 and 0 <= r + dr < 9:
                blend(a, X + c + dc, Y + r + dr, inkline, 0.55)
    for (c, r) in pts:
        px(a, X + c, Y + r, ink)


def app_icon(a, x, y, pressed=False):
    """9x9: the options button as the window's icon: a little blue tile with a white note."""
    stops = ([(0, (120, 186, 246)), (0.5, (40, 128, 222)), (0.52, (20, 100, 200)), (1, (60, 150, 236))]
             if not pressed else [(0, (70, 130, 200)), (0.5, (24, 88, 170)), (0.52, (14, 70, 150)), (1, (40, 110, 190))])
    shape(a, x, y, round_mask(9, 9, 2.2), rows_face(9, 9, stops), (18, 58, 120))
    o = 1 if pressed else 0
    for (c, r) in [(5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (6, 2), (7, 3), (3, 5), (4, 5), (3, 6), (4, 6)]:
        px(a, x + c - 1 + o, y + r + o, WHITE)


# ------------------------------------------------------------------------------------------
# The main window's glass (main.bmp and titlebar.bmp share it)
# ------------------------------------------------------------------------------------------

MAIN_T = [y / 115 for y in range(116)]


def main_glass(lit=True, seed=7):
    g = glass(275, 116, MAIN_T, lit, seed=seed, period=400.0)
    return g


GLASS_MAIN = None
GLASS_EQ = None


def wash_unlit(bar):
    """An inactive titlebar: the active glass washed toward pale, strongest at the top so it meets
    main.bmp's (always active) glass below without a seam."""
    h = bar.shape[0]
    out = bar.astype(np.float64)
    for r in range(h):
        t = 0.6 * (1 - r / (h - 1)) + 0.12
        out[r] = out[r] * (1 - t) + np.array(PALE) * t
    return to_int(out)


def caption_group(a, lit):
    """The frame round the min/shade/close buttons (243..273, rows 1..12): hangs from the top
    edge, bottom corners rounded, dark dividers between the buttons."""
    e = (40, 64, 98) if lit else (110, 128, 152)
    x0, x1, y0, y1 = 243, 273, 1, 12
    rect(a, x0, y0, 1, y1 - y0, e)
    rect(a, x1, y0, 1, y1 - y0, e)
    rect(a, x0 + 1, y1, x1 - x0 - 1, 1, e)
    blend(a, x0, y1, e, 0.4)
    blend(a, x1, y1, e, 0.4)
    for xx in (253, 263):
        rect(a, xx, 3, 1, 9, lerp(e, (255, 255, 255), 0.15))
    rect(a, x0 + 1, 2, x1 - x0 - 1, 1, lerp(e, WHITE, 0.55))
    rect(a, x0 + 1, 11, x1 - x0 - 1, 1, lerp(e, WHITE, 0.35))


def main_titlebar(lit):
    g = to_int(GLASS_MAIN[0:14])
    a = g.copy()
    if not lit:
        a = wash_unlit(a)
    glass_edges(a, 0, 0, 275, 15, lit, bottom=False)
    app_icon(a, 6, 3)
    caption(a, "YTMinamp", 19, 4, lit)
    caption_group(a, lit)
    caption_button(a, 244, 3, "minimize", lit)
    caption_button(a, 254, 3, "shade", lit)
    caption_button(a, 264, 3, "close", lit)
    return a


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    """A slim Windows 7 toolbar strip: light face, letters in grey, the lit ones in a selection box."""
    a = new(8, 43, FACE)
    shape(a, 0, 0, round_mask(8, 43, 2), rows_face(8, 43, [(0, (250, 251, 253)), (1, (226, 232, 240))]),
          (176, 188, 204))
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            shape(a, 1, y, round_mask(6, h, 1.5), rows_face(6, h, [(0, (232, 245, 255)), (1, (196, 226, 252))]),
                  (102, 167, 232))
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, CUR_BLUE if on else (110, 116, 126))
    return a


def make_titlebar():
    a = new(344, 87, FACE)
    for kind, x in (("options", 0), ("minimize", 9), ("close", 18)):
        b = new(9, 9)
        b2 = new(9, 9)
        if kind == "options":
            b[:] = GLASS_MAIN[3:12, 6:15].round().astype(np.int32)
            b2[:] = b
            app_icon(b, 0, 0)
            app_icon(b2, 0, 0, pressed=True)
        else:
            caption_button(b, 0, 0, kind, True)
            caption_button(b2, 0, 0, kind, True, pressed=True)
        a[0:9, x:x + 9] = b
        a[9:18, x:x + 9] = b2
    b = new(9, 9)
    caption_button(b, 0, 0, "shade", True)
    a[18:27, 0:9] = b
    caption_button(b, 0, 0, "shade", True, pressed=True)
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
# The dark glossy display (time, play state, analyzer)
# ------------------------------------------------------------------------------------------

DISP_X, DISP_Y, DISP_W, DISP_H = 20, 19, 86, 44     # outer, border included


def disp_col(y):
    """The display's colour at main.bmp row y: a glossy reflection over the top half, a hard
    edge at row 32, then near-black glass that brightens to #1a2a3a at the bottom."""
    if y <= 32:
        return lerp((66, 84, 106), (30, 42, 56), (y - 20) / 12)
    if y <= 40:
        return lerp((4, 7, 12), VIS_BG, (y - 33) / 7)
    if y <= 58:
        return VIS_BG
    return lerp(VIS_BG, (26, 42, 58), (y - 58) / 3)


def disp_cell(w, h, y0):
    """A sprite cell with the display's background, for a sprite drawn at main.bmp row y0."""
    a = new(w, h)
    for r in range(h):
        a[r, :] = disp_col(y0 + r)
    return a


def dark_display(a, x, y, w, h, y_of=disp_col):
    """Rounded dark glass well set into the light face."""
    for r in range(h):
        a[y + r, x:x + w] = y_of(y + r)
    # soft border: dark ring, a lighter bevel below/right outside it
    ring = (24, 34, 46)
    outline(a, x, y, w, h, ring)
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        a[cy, cx] = lerp(ring, FACE, 0.6)
    rect(a, x + 1, y + h, w - 2, 1, WHITE)
    rect(a, x + w, y + 1, 1, h - 2, WHITE)
    rect(a, x + 1, y - 1, w - 2, 1, (196, 204, 214))
    rect(a, x - 1, y + 1, 1, h - 2, (204, 210, 220))


def text_field(a, x, y, w, h):
    """A Windows 7 text box: white, dark top/left rim, light bottom/right rim."""
    rect(a, x, y, w, h, WHITE)
    rect(a, x, y, w, 1, (171, 173, 179))
    rect(a, x, y, 1, h, (226, 227, 234))
    rect(a, x + w - 1, y, 1, h, (219, 223, 230))
    rect(a, x, y + h - 1, w, 1, (227, 233, 239))
    for cx, cy in ((x, y), (x + w - 1, y)):
        a[cy, cx] = lerp((171, 173, 179), FACE, 0.5)


def etched(a, x, y, w):
    rect(a, x, y, w, 1, (213, 223, 229))
    rect(a, x, y + 1, w, 1, WHITE)


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116)
# ------------------------------------------------------------------------------------------

CLIENT = (6, 15, 263, 94)   # the light face: x, y, w, h (x 6..268, y 15..108)


def window_frame(a, glass_arr, client, lit=True):
    """Glass everywhere, then the light face set into it with a thin edge."""
    a[:] = to_int(glass_arr)
    h, w = a.shape[:2]
    glass_edges(a, 0, 0, w, h, lit)
    cx, cy, cw, ch = client
    rect(a, cx, cy, cw, ch, FACE)
    outline(a, cx - 1, cy - 1, cw + 2, ch + 2, FACE_LINE)
    rect(a, cx, cy, cw, 1, (250, 250, 250))


def make_main():
    a = new(275, 116)
    window_frame(a, GLASS_MAIN, CLIENT)
    a[0:14, :] = main_titlebar(True)
    # a soft gradient on the face toward the bottom, like a Windows 7 dialog's command area
    for y in range(84, 109):
        rect(a, 6, y, 263, 1, lerp(FACE, (226, 233, 242), (y - 84) / 24))
    etched(a, 10, 83, 255)

    # clutterbar slot (drawn from titlebar.bmp too)
    a[22:65, 10:18] = clutter_bar("")

    # left display: play state, time, analyzer
    dark_display(a, DISP_X, DISP_Y, DISP_W, DISP_H)
    for yy in (30, 35):
        rect(a, 72, yy, 2, 2, (210, 236, 255))

    # right: title and kbps/kHz boxes
    text_field(a, 108, 20, 161, 17)
    text_field(a, 108, 38, 161, 16)
    draw_text(a, TINY, "KBPS", 129, 44, LABEL)
    draw_text(a, TINY, "KHZ", 169, 44, LABEL)

    # volume / balance seats: their sheets carry everything; paint the empty frame anyway
    vol = volume_frame(13)
    a[57:70, 107:175] = vol[0:13]
    bal = balance_frame(0)
    a[57:70, 177:215] = bal[0:13, 9:47]

    # seek trough
    a[72:82, 16:264] = trough(248)

    # transport strip (cbuttons draws over it)
    a[88:106, 16:130] = transport_strip(None)

    # the About spot: the Windows flag
    flag_emblem(a, 253, 91)
    return a


# ------------------------------------------------------------------------------------------
# Logo: the Windows flag (source/logo-windows-flag/flag.svg, Wikimedia Commons)
# ------------------------------------------------------------------------------------------

_FLAG = {}


def flag_rgba(h):
    if h not in _FLAG:
        png = os.path.join(SCRATCH, f"flag-{h * 8}.png")
        subprocess.run(["/usr/bin/rsvg-convert", "-h", str(h * 8), FLAG_SVG, "-o", png], check=True)
        im = Image.open(png).convert("RGBA")
        w = max(1, round(im.width * h / im.height))
        _FLAG[h] = np.asarray(im.resize((w, h), Image.LANCZOS), dtype=np.float64)
    return _FLAG[h]


def flag_emblem(a, x, y):
    """13x15 About spot: the flag, small, with a soft white glow under it."""
    f = flag_rgba(11)
    fh, fw = f.shape[:2]
    ox, oy = x + (13 - fw) // 2, y + 2
    al = f[..., 3] / 255
    glow = np.zeros((15 + 4, 13 + 4))
    glow[2 + 2:2 + 2 + fh, 2 + (13 - fw) // 2:2 + (13 - fw) // 2 + fw] = al
    glow = np.clip(blur(glow, 1) * 1.5, 0, 1) * 0.5
    composite(a, x - 2, y - 2, glow, WHITE)
    rgb = f[..., :3] * 1.0
    composite(a, ox, oy, al, rgb)


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36): a WMP12-style dark glass strip with a round play button
# ------------------------------------------------------------------------------------------

STRIP_CELLS = {"previous": (0, 23), "play": (23, 23), "pause": (46, 23), "stop": (69, 23), "next": (92, 22)}
ICON = (236, 242, 248)
ICON_HOT = (190, 230, 255)


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


def icon(a, kind, cx, cy, col, shadow=None, small=False):
    def both(fn):
        if shadow is not None:
            fn(1, shadow)
        fn(0, col)

    if kind == "previous":
        both(lambda d, c: (rect(a, cx - 5 + d, cy - 3 + d, 2, 7, c), tri_left(a, cx - 3 + d, cy - 3 + d, 7, c),
                           tri_left(a, cx + 1 + d, cy - 3 + d, 7, c)))
    elif kind == "next":
        both(lambda d, c: (tri_right(a, cx - 5 + d, cy - 3 + d, 7, c), tri_right(a, cx - 1 + d, cy - 3 + d, 7, c),
                           rect(a, cx + 3 + d, cy - 3 + d, 2, 7, c)))
    elif kind == "play":
        both(lambda d, c: tri_right(a, cx - 2 + d, cy - 4 + d, 9, c))
    elif kind == "pause":
        both(lambda d, c: (rect(a, cx - 3 + d, cy - 3 + d, 2, 7, c), rect(a, cx + 1 + d, cy - 3 + d, 2, 7, c)))
    elif kind == "stop":
        both(lambda d, c: rect(a, cx - 3 + d, cy - 3 + d, 7, 7, c))
    elif kind == "eject":
        def ej(d, c):
            for r in range(4):
                rect(a, cx - r + d, cy - 4 + r + d, 2 * r + 1, 1, c)
            rect(a, cx - 3 + d, cy + 1 + d, 7, 2, c)
        both(ej)


DARK_GLASS = [(0, (110, 122, 138)), (0.08, (78, 90, 106)), (0.46, (44, 52, 64)), (0.5, (14, 18, 24)),
              (0.85, (20, 26, 34)), (1, (40, 52, 66))]


def glow_spot(a, cx, cy, r, col, strength):
    h, w = a.shape[:2]
    Y, X = np.mgrid[0:h, 0:w]
    d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / r
    composite(a, 0, 0, np.clip(1 - d, 0, 1) ** 1.6, col, strength)


def transport_strip(pressed):
    """114 x 18: the dark glass pill (rows 3..14) with the play button's round knob across it."""
    a = new(114, 18, FACE)
    for r in range(18):
        a[r, :] = lerp(FACE, (226, 233, 242), (r + 4) / 24)
    pill = round_mask(114, 13, 6.5)
    shape(a, 0, 3, pill, rows_face(114, 13, DARK_GLASS), (10, 14, 20))
    for xx in range(5, 109):
        blend(a, xx, 4, WHITE, 0.25)
    # dividers between the small buttons
    for xx in (57, 80):
        rect(a, xx, 6, 1, 7, (8, 10, 14))
        rect(a, xx + 1, 6, 1, 7, (70, 80, 94))
    # pressed small buttons: a blue glow behind the icon
    centres = {"previous": (12, 9), "pause": (50, 9), "stop": (69, 9), "next": (98, 9)}
    if pressed in centres:
        cx, cy = centres[pressed]
        sub = a[3:16].copy()
        glow_spot(sub, cx, cy - 3, 9, (60, 150, 255), 0.85)
        a[3:16] = np.where(pill[..., None] > 0.5, sub, a[3:16])
    for kind, (cx, cy) in centres.items():
        on = pressed == kind
        icon(a, kind, cx, cy, ICON_HOT if on else ICON, shadow=(0, 0, 0))
    # the play button: a round glossy knob, 18 across, silver-blue rim, black glass inside
    cx, cy = 34.5, 9.0
    rim = disc_mask(114, 18, cx, cy, 9.0)
    composite(a, 0, 0, rim, (30, 40, 54))
    ring = disc_mask(114, 18, cx, cy, 8.2)
    rimface = rows_face(114, 18, [(0, (226, 236, 248)), (0.5, (150, 172, 200)), (1, (210, 226, 244))])
    composite(a, 0, 0, ring, rimface)
    core = disc_mask(114, 18, cx, cy, 6.6)
    if pressed == "play":
        coreface = rows_face(114, 18, [(0, (60, 120, 200)), (0.48, (20, 70, 150)), (0.52, (6, 40, 110)),
                                       (1, (40, 140, 255))])
    else:
        coreface = rows_face(114, 18, [(0, (96, 108, 124)), (0.45, (40, 48, 60)), (0.52, (6, 8, 12)),
                                       (1, (30, 44, 62))])
    composite(a, 0, 0, core, (16, 20, 28))
    composite(a, 0, 0, disc_mask(114, 18, cx, cy, 5.9), coreface)
    if pressed == "play":
        sub = a.copy()
        glow_spot(sub, cx, cy + 2, 7, (90, 190, 255), 0.9)
        a[:] = np.where(disc_mask(114, 18, cx, cy, 5.9)[..., None] > 0.3, sub, a)
    # gloss on the knob's top half
    gl = disc_mask(114, 18, cx, cy - 2.6, 4.2) * (np.arange(18)[:, None] < 9)
    composite(a, 0, 0, gl, WHITE, 0.22)
    icon(a, "play", 35, 9, WHITE if pressed != "play" else (220, 244, 255), shadow=(0, 0, 0))
    return a


def eject_button(pressed):
    a = new(22, 16, FACE)
    for r in range(16):
        a[r, :] = lerp(FACE, (226, 233, 242), (r + 5) / 24)
    face = rows_face(22, 14, DARK_GLASS)
    shape(a, 0, 1, round_mask(22, 14, 5), face, (10, 14, 20))
    for xx in range(4, 18):
        blend(a, xx, 2, WHITE, 0.25)
    if pressed:
        sub = a.copy()
        glow_spot(sub, 11, 9, 9, (60, 150, 255), 0.85)
        a[:] = np.where(round_mask(22, 16, 5)[..., None] > 0.5, sub, a)
    icon(a, "eject", 11, 8, ICON_HOT if pressed else ICON, shadow=(0, 0, 0))
    return a


def make_cbuttons():
    a = new(136, 36, FACE)
    normal = transport_strip(None)
    for kind, (x, w) in STRIP_CELLS.items():
        a[0:18, x:x + w] = normal[:, x:x + w]
        a[18:36, x:x + w] = transport_strip(kind)[:, x:x + w]
    a[0:16, 114:136] = eject_button(False)
    a[16:32, 114:136] = eject_button(True)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85): Windows 7 command buttons, lit blue when on
# ------------------------------------------------------------------------------------------


def face_bg(w, h, y0, lo=84, hi=108):
    """The main window's face behind a sprite drawn at main row y0 (its bottom gradient)."""
    a = new(w, h)
    for r in range(h):
        y = y0 + r
        a[r, :] = FACE if y < lo else lerp(FACE, (226, 233, 242), (y - lo) / (hi - lo))
    return a


def toggle(w, h, label, on, pressed, y0):
    a = face_bg(w, h, y0)
    style = ("onpressed" if pressed else "pressed") if on else ("hot" if pressed else "normal")
    win_button(a, 0, 0, w, h, style)
    o = 1 if pressed else 0
    col = (12, 52, 110) if on else (36, 36, 36)
    tw = text_w(TINY, label)
    draw_text(a, TINY, label, (w - tw) // 2 + o, (h - 5) // 2 + o, col)
    return a


def make_shufrep():
    a = new(92, 85, FACE)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = toggle(28, 15, "REPEAT", on, pressed, 89)
        a[y:y + 15, 28:75] = toggle(47, 15, "SHUFFLE", on, pressed, 89)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        a[61:73, x:x + 23] = toggle(23, 12, label, False, pressed, 58)
        a[73:85, x:x + 23] = toggle(23, 12, label, True, pressed, 58)
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, WHITE)
    for y, on in ((0, True), (12, False)):
        col = CUR_BLUE if on else (196, 200, 206)
        text_center(a, TINY, "STEREO", 14, y + 4, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 4, col)
    return a


PLAY_COL = (214, 238, 255)


def make_playpaus():
    a = disp_cell(48, 9, 28)
    tri_right(a, 2, 0, 9, PLAY_COL)                       # playing
    rect(a, 9 + 2, 1, 2, 7, PLAY_COL)                     # paused
    rect(a, 9 + 5, 1, 2, 7, PLAY_COL)
    rect(a, 18 + 1, 1, 7, 7, PLAY_COL)                    # stopped
    rect(a, 39 + 1, 3, 1, 3, (110, 200, 255))             # working: a lit dot in its 3px slice
    return a


# Segoe-like display digits, 7x11; "+" is a half-lit pixel (antialiasing).
DIGITS = {
    0: [".+###+.", "+#+.+#+", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##",
        "+#+.+#+", ".+###+."],
    1: ["..+##..", ".+###..", "+#+##..", "...##..", "...##..", "...##..", "...##..", "...##..", "...##..",
        "...##..", "...##.."],
    2: [".+###+.", "+#+.+##", ".....##", ".....##", "....+#+", "...+#+.", "..+#+..", ".+#+...", "+#+....",
        "##.....", "#######"],
    3: ["+####+.", "....+##", ".....##", ".....##", "..####.", "....+#+", ".....##", ".....##", ".....##",
        "....+##", "+####+."],
    4: ["....##.", "...+##.", "..+###.", ".+#+##.", "+#+.##.", "##..##.", "#######", "....##.", "....##.",
        "....##.", "....##."],
    5: ["######.", "##.....", "##.....", "##.....", "#####+.", "....+#+", ".....##", ".....##", ".....##",
        "....+#+", "+####+."],
    6: ["..+###.", ".+#+...", "+#+....", "##.....", "##+##+.", "###.+#+", "##...##", "##...##", "##...##",
        "+#+.+#+", ".+###+."],
    7: ["#######", ".....##", "....+#+", "....##.", "...+#+.", "...##..", "..+#+..", "..##...", "..##...",
        "..##...", "..##..."],
    8: [".+###+.", "+#+.+#+", "##...##", "+#+.+#+", ".+###+.", "+#+.+#+", "##...##", "##...##", "##...##",
        "+#+.+#+", ".+###+."],
    9: [".+###+.", "+#+.+#+", "##...##", "##...##", "##...##", "+#+.###", ".+##+##", ".....##", "....+#+",
        "...+#+.", ".###+.."],
}


def digit_col(r):
    """Digits: white at the top, a cool light blue toward the bottom."""
    return lerp((250, 252, 255), (150, 210, 255), r / 10)


def draw_digit(a, n, x, y):
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + c, y + r, digit_col(r))
            elif ch == "+":
                blend(a, x + c, y + r, digit_col(r), 0.5)


def make_numbers(ex):
    a = disp_cell(108 if ex else 99, 13, 26)
    for n in range(10):
        draw_digit(a, n, 9 * n + 1, 1)
    if ex:
        for c in range(101, 106):
            px(a, c, 6, digit_col(5))
            px(a, c, 7, digit_col(6))
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, WHITE)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key, col * 5, row * 6, TEXT)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10): a Windows 7 progress bar, the thumb a green glossy segment
# ------------------------------------------------------------------------------------------

TROUGH = [(0, (246, 246, 246)), (0.45, (234, 234, 234)), (0.5, (222, 222, 222)), (1, (236, 236, 236))]


def trough(w):
    a = new(w, 10, FACE)
    shape(a, 0, 0, round_mask(w, 10, 2.5), rows_face(w, 10, TROUGH), (178, 178, 178))
    for xx in range(2, w - 2):
        blend(a, xx, 1, WHITE, 0.6)
    return a


def trough_column():
    t = trough(40)
    return t[:, 20:21]


GREEN = [(0, (214, 246, 206)), (0.18, (120, 222, 110)), (0.45, (20, 190, 52)), (0.5, (6, 176, 37)),
         (0.8, (6, 168, 34)), (1, (52, 208, 78))]
GREEN_SEL = [(0, (236, 255, 228)), (0.18, (160, 240, 150)), (0.45, (50, 214, 82)), (0.5, (24, 200, 60)),
             (0.8, (20, 190, 54)), (1, (90, 232, 120))]


def green_thumb(selected):
    a = np.repeat(trough_column(), 29, axis=1).copy()
    face = rows_face(29, 8, GREEN_SEL if selected else GREEN)
    # the fill's soft ends, as Windows 7's bar has
    shape(a, 0, 1, round_mask(29, 8, 2), face, (28, 130, 44) if not selected else (30, 150, 56))
    for xx in range(2, 27):
        blend(a, xx, 2, WHITE, 0.35)
    # a light sweep across the middle (the bar's moving highlight)
    for xx in range(1, 28):
        t = 1 - abs(xx - 14) / 14
        for yy in range(2, 8):
            blend(a, xx, yy, WHITE, 0.18 * t * t)
    return a


def make_posbar():
    a = new(307, 10, FACE)
    a[:, 0:248] = trough(248)
    a[:, 248:277] = green_thumb(False)
    a[:, 278:307] = green_thumb(True)
    return a


# ------------------------------------------------------------------------------------------
# volume.bmp / balance.bmp (68 x 433): trackbars, a blue level fill, the blue-tinted thumb
# ------------------------------------------------------------------------------------------

FILL = [(0, (170, 220, 252)), (0.45, (70, 160, 236)), (0.5, (30, 120, 220)), (1, (60, 160, 240))]


def groove(a, x, y, w, h, fill_ranges=()):
    """Horizontal trackbar groove at rows y..y+h-1, with blue fill over [x0, x1) column ranges."""
    shape(a, x, y, round_mask(w, h, 1.5), rows_face(w, h, [(0, (214, 218, 222)), (1, (240, 242, 244))]),
          (150, 154, 160))
    face = rows_face(w, h, FILL)
    for x0, x1 in fill_ranges:
        x0, x1 = max(x0, x + 1), min(x1, x + w - 1)
        if x1 > x0:
            a[y + 1:y + h - 1, x0:x1] = to_int(face[1:h - 1, x0 - x:x1 - x])


def volume_frame(i):
    a = face_bg(68, 15, 57)
    level = (i + 1) / 28
    fill_to = 2 + round(level * 63)
    groove(a, 1, 4, 66, 5, [(0, fill_to)])
    return a


def balance_frame(i):
    a = face_bg(68, 15, 57)
    t = i / 27
    reach = round(16 * t)
    groove(a, 10, 4, 36, 5, [(28 - reach, 28 + reach)] if i else [])
    rect(a, 28, 1, 1, 2, (120, 128, 138))
    rect(a, 28, 10, 1, 2, (120, 128, 138))
    return a


THUMB = [(0, (250, 253, 255)), (0.45, (220, 238, 252)), (0.5, (190, 222, 248)), (1, (150, 200, 240))]
THUMB_SEL = [(0, (226, 242, 252)), (0.45, (176, 216, 244)), (0.5, (120, 186, 236)), (1, (80, 160, 226))]


def slider_thumb(selected, bg):
    """14x11: Windows 7's horizontal trackbar thumb, pointing down, tinted blue."""
    a = bg.copy()
    outer = poly_mask(14, 11, [(1.5, 0), (12.5, 0), (14, 1.5), (14, 7), (7, 11), (0, 7), (0, 1.5)])
    inner = poly_mask(14, 11, [(2, 1), (12, 1), (13, 2), (13, 6.6), (7, 9.8), (1, 6.6), (1, 2)])
    shape(a, 0, 0, outer, rows_face(14, 11, THUMB_SEL if selected else THUMB),
          (44, 98, 139) if selected else (60, 127, 177), inner)
    for xx in range(3, 11):
        blend(a, xx, 1, WHITE, 0.7)
    return a


def make_volume():
    a = new(68, 433, FACE)
    for i in range(28):
        a[i * 15:i * 15 + 15] = volume_frame(i)
    bg = face_bg(14, 11, 58)
    a[422:433, 0:14] = slider_thumb(True, bg)
    a[422:433, 15:29] = slider_thumb(False, bg)
    return a


def make_balance():
    a = new(68, 433, FACE)
    for i in range(28):
        a[i * 15:i * 15 + 15] = balance_frame(i)
    bg = face_bg(14, 11, 58)
    a[422:433, 0:14] = slider_thumb(True, bg)
    a[422:433, 15:29] = slider_thumb(False, bg)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
EQ_CLIENT = (6, 15, 263, 97)   # y 15..111


def eq_titlebar(lit):
    a = to_int(GLASS_EQ[0:14])
    if not lit:
        a = wash_unlit(a)
    glass_edges(a, 0, 0, 275, 15, lit, bottom=False)
    caption(a, "Equalizer", 8, 4, lit)
    # a lone close button, framed the way the main window's group is
    e = (40, 64, 98) if lit else (110, 128, 152)
    rect(a, 263, 1, 1, 11, e)
    rect(a, 273, 1, 1, 11, e)
    rect(a, 264, 12, 9, 1, e)
    rect(a, 264, 2, 9, 1, lerp(e, WHITE, 0.55))
    caption_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(n):
    """14x63: a vertical trackbar groove, filled blue from the value down."""
    a = new(14, 63, FACE)
    shape(a, 5, 2, round_mask(4, 59, 1.5), rows_face(4, 59, [(0, (214, 218, 222)), (1, (232, 236, 240))]),
          (150, 154, 160))
    v = n / 27
    top = round((1 - v) * 51) + 6
    for r in range(max(top, 3), 60):
        t = (r - top) / max(1, 59 - top)
        col = lerp((80, 170, 245), (24, 110, 214), t)
        rect(a, 6, r, 2, 1, col)
        px(a, 6, r, lerp(col, WHITE, 0.35))
    for xx in (1, 2, 11, 12):
        px(a, xx, 31, (150, 156, 164))
    for yy in (7, 55):
        px(a, 1, yy, (190, 194, 200))
        px(a, 12, yy, (190, 194, 200))
    return a


def eq_thumb(selected):
    a = new(11, 11, FACE)
    shape(a, 0, 0, round_mask(11, 11, 2.5), rows_face(11, 11, THUMB_SEL if selected else THUMB),
          (44, 98, 139) if selected else (60, 127, 177))
    for xx in range(2, 9):
        blend(a, xx, 1, WHITE, 0.7)
    for yy in (4, 6):
        rect(a, 3, yy, 5, 1, (110, 150, 190) if not selected else (60, 110, 170))
        rect(a, 3, yy + 1, 5, 1, lerp(WHITE, (200, 230, 250), 0.3))
    return a


def eq_graph():
    """113x19 dark glass: grid dots, a dotted zero line."""
    a = new(113, 19)
    for r in range(19):
        a[r, :] = lerp((40, 54, 72), (20, 28, 38), r / 8) if r < 9 else lerp((4, 7, 12), (16, 28, 40), (r - 9) / 9)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            blend(a, 2 + x, y, (90, 140, 190), 0.35)
    for x in range(0, 113, 2):
        blend(a, x, 9, (110, 160, 210), 0.45)
    return a


def make_eqmain():
    a = new(275, 315, FACE)
    w = new(275, 116)
    window_frame(w, GLASS_EQ, EQ_CLIENT)
    w[0:14] = eq_titlebar(True)
    # graph well
    dark_display(w, 85, 16, 115, 21, lambda y: (20, 28, 38))
    w[17:36, 86:199] = eq_graph()
    # slider bay: a Windows 7 group box
    shape(w, 15, 35, round_mask(247, 70, 3), rows_face(247, 70, [(0, (252, 252, 252)), (1, (244, 246, 248))]),
          (213, 223, 229))
    rect(w, 41, 38, 1, 64, (213, 223, 229))
    rect(w, 42, 38, 1, 64, WHITE)
    for lbl, yy in (("+12DB", 40), ("+0DB", 66), ("-12DB", 92)):
        text_center(w, TINY, lbl, 59, yy, LABEL)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        f = eq_slider_frame(14)
        w[38:101, x:x + 14] = np.where(np.all(f == FACE, axis=2)[..., None], w[38:101, x:x + 14], f)
    text_center(w, TINY, "PREAMP", 28, 106, LABEL)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(w, TINY, lbl, 78 + 18 * i + 7, 106, LABEL)
    a[0:116] = w

    # under the window: buttons (their background is the face)
    cb = new(9, 9)
    caption_button(cb, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = cb
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        bw = 26 if label == "ON" else 32
        a[119:131, x:x + bw] = toggle(bw, 12, label, on, pressed, 0)
    a[134:148] = eq_titlebar(True)
    a[149:163] = eq_titlebar(False)
    a[164:175, 0:11] = eq_thumb(False)
    a[176:187, 0:11] = eq_thumb(True)
    # slider frames sit inside the group box; give them its white
    for n in range(28):
        f = eq_slider_frame(n)
        f[np.all(f == FACE, axis=2)] = (250, 250, 251)
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = f
    for y, pressed in ((164, False), (176, True)):
        a[y:y + 12, 224:268] = toggle(44, 12, "PRESETS", False, pressed, 0)
    a[294:313, 0:113] = eq_graph()
    for r in range(19):
        px(a, 115, 294 + r, ramp([(220, 248, 255), (120, 220, 255), (40, 160, 250), (60, 110, 230)], r / 18))
    for x in range(113):
        px(a, x, 314, (150, 200, 240) if x % 3 != 2 else (24, 34, 46))
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): glass frames round a white list
# ------------------------------------------------------------------------------------------

GLASS_SIDE = 5           # glass columns at each side
BAR_FACE_Y = 17          # top bars: glass rows 0..16, face rows 17..19
BAR_T = [y / 116 for y in range(20)]
SIDE_T = 0.45
BOT_T = 0.9


def bar_glass(w, lit, seed=21, ox=0):
    return to_int(glass(w, 20, BAR_T, lit, seed=seed, ox=ox, px_=25, period=25.0 * 14))


def side_glass(w, h, lit=True, seed=31, ox=0):
    return to_int(glass(w, h, [SIDE_T] * h, lit, seed=seed, ox=ox, py_=h, period=h / STREAK_SLOPE * 1.0))


def bottom_glass(w, h, lit=True, seed=41):
    return to_int(glass(w, h, [0.6 + 0.3 * r / max(1, h - 1) for r in range(h)], lit, seed=seed, px_=25,
                        period=25.0 * 14))


def pill_alpha():
    """The caption glow's strength by bar row (20 rows): the white haze behind a title."""
    r = np.arange(20)
    al = 0.74 * np.exp(-((r - 6.5) / 4.2) ** 2)
    al[BAR_FACE_Y:] = 0
    al[0] = 0
    return al


def pill_rows(lit):
    """The caption glow over untextured glass, by row: what gen.bmp's letter cells carry."""
    al = pill_alpha() * (1 if lit else 0.8)
    return [lerp(glass_base(BAR_T[r], lit), WHITE, al[r]) for r in range(20)]


def pill_over(t, lit, x0, x1, fade_l, fade_r):
    """Washes columns x0..x1-1 of bar t with the caption glow (the glass shows through faintly);
    fade_l/fade_r: columns over which it eases in and out."""
    al = pill_alpha() * (1 if lit else 0.8)
    for x in range(x0, x1):
        k = 1.0
        if fade_l and x < x0 + fade_l:
            k = (x - x0 + 1) / (fade_l + 1)
        if fade_r and x >= x1 - fade_r:
            k = min(k, (x1 - x) / (fade_r + 1))
        k = k * k * (3 - 2 * k)
        for r in range(1, BAR_FACE_Y):
            t[r, x] = lerp(tuple(int(v) for v in t[r, x]), WHITE, al[r] * k)


def bar20(w, lit, left_edge=False, right_edge=False, ox=0):
    """A top bar piece: glass with the top edge and highlight, face rows at the bottom."""
    t = bar_glass(w, lit, ox=ox)
    e = EDGE if lit else EDGE_DIM
    rect(t, 0, 0, w, 1, e)
    for xx in range(w):
        blend(t, xx, 1, WHITE, 0.5 if lit else 0.4)
    x0 = GLASS_SIDE if left_edge else 0
    x1 = w - GLASS_SIDE if right_edge else w
    rect(t, x0, BAR_FACE_Y, x1 - x0, 20 - BAR_FACE_Y, FACE)
    rect(t, x0, BAR_FACE_Y, x1 - x0, 1, FACE_LINE)
    if left_edge:
        rect(t, 0, 0, 1, 20, e)
        for yy in range(1, 20):
            blend(t, 1, yy, WHITE, 0.5 if lit else 0.4)
        rect(t, GLASS_SIDE - 1, BAR_FACE_Y, 1, 3, FACE_LINE)
        px(t, 0, 0, lerp(e, (0, 0, 0), 0.4))
        blend(t, 1, 1, e, 0.65)
        blend(t, 2, 1, e, 0.2)
        blend(t, 1, 2, e, 0.2)
    if right_edge:
        rect(t, w - 1, 0, 1, 20, e)
        for yy in range(1, 20):
            blend(t, w - 2, yy, WHITE, 0.4 if lit else 0.3)
        rect(t, w - GLASS_SIDE, BAR_FACE_Y, 1, 3, FACE_LINE)
        px(t, w - 1, 0, lerp(e, (0, 0, 0), 0.4))
        blend(t, w - 2, 1, e, 0.65)
        blend(t, w - 3, 1, e, 0.2)
        blend(t, w - 2, 2, e, 0.2)
    return t


def close_group(t, x, lit):
    """The lone close button's frame on a 20px bar (button at x+1, row 3)."""
    e = (40, 64, 98) if lit else (110, 128, 152)
    rect(t, x, 1, 1, 11, e)
    rect(t, x + 10, 1, 1, 11, e)
    rect(t, x + 1, 12, 9, 1, e)
    rect(t, x + 1, 2, 9, 1, lerp(e, WHITE, 0.55))
    caption_button(t, x + 1, 3, "close", lit)


def side_tile(w, h, left, list_border=True):
    """A side piece: glass at the outer GLASS_SIDE columns, face inside, a border by the list."""
    t = new(w, h, FACE)
    g = side_glass(GLASS_SIDE, h, ox=0 if left else 7)
    if left:
        t[:, 0:GLASS_SIDE] = g
        rect(t, 0, 0, 1, h, EDGE)
        for yy in range(h):
            blend(t, 1, yy, WHITE, 0.5)
        rect(t, GLASS_SIDE, 0, 1, h, FACE_LINE)
        if list_border:
            rect(t, w - 1, 0, 1, h, (130, 135, 144))
    else:
        t[:, w - GLASS_SIDE:w] = g
        rect(t, w - 1, 0, 1, h, EDGE)
        for yy in range(h):
            blend(t, w - 2, yy, WHITE, 0.4)
        rect(t, w - GLASS_SIDE - 1, 0, 1, h, FACE_LINE)
        if list_border:
            rect(t, 0, 0, 1, h, (130, 135, 144))
    return t


def bottom_piece(w, h, left_edge=False, right_edge=False):
    """A bottom piece: face, then glass under it (the last 5 rows) with the bottom edge."""
    t = new(w, h, FACE)
    for r in range(h - GLASS_SIDE):
        t[r, :] = lerp(FACE, (226, 233, 242), r / max(1, h - GLASS_SIDE - 1) * 0.8)
    gy = h - GLASS_SIDE
    t[gy:h] = bottom_glass(w, GLASS_SIDE)
    rect(t, 0, gy - 1, w, 1, FACE_LINE)
    rect(t, 0, h - 1, w, 1, EDGE)
    for xx in range(w):
        blend(t, xx, h - 2, WHITE, 0.3)
    if left_edge:
        t[0:gy, 0:GLASS_SIDE] = side_glass(GLASS_SIDE, gy, seed=33)
        rect(t, 0, 0, 1, h, EDGE)
        for yy in range(h - 1):
            blend(t, 1, yy, WHITE, 0.5)
        rect(t, GLASS_SIDE, 0, 1, gy, FACE_LINE)
    if right_edge:
        t[0:gy, w - GLASS_SIDE:w] = side_glass(GLASS_SIDE, gy, seed=34, ox=7)
        rect(t, w - 1, 0, 1, h, EDGE)
        for yy in range(h - 1):
            blend(t, w - 2, yy, WHITE, 0.4)
        rect(t, w - GLASS_SIDE - 1, 0, 1, gy, FACE_LINE)
    return t


def pl_button(t, x, y, w, h, label):
    win_button(t, x, y, w, h, "normal")
    tw = text_w(TINY, label)
    draw_text(t, TINY, label, x + (w - tw) // 2, y + (h - 5) // 2, (36, 36, 36))


def make_pledit():
    a = new(280, 186, FACE)
    for lit, y in ((True, 0), (False, 21)):
        # top tile
        t = bar20(25, lit)
        rect(t, 0, 19, 25, 1, (130, 135, 144))
        a[y:y + 20, 127:152] = t
        # top-left corner
        t = bar20(25, lit, left_edge=True)
        rect(t, 11, 19, 14, 1, (130, 135, 144))
        a[y:y + 20, 0:25] = t
        # title: the caption glow, "Playlist" in it; x 0..3 and 96..99 are its end caps
        t = bar20(100, lit, ox=0)
        rect(t, 0, 19, 100, 1, (130, 135, 144))
        pill_over(t, lit, 0, 100, 5, 5)
        tw = text_w(CAPTION, "Playlist")
        draw_text(t, CAPTION, "Playlist", 50 - tw // 2, 4, INK if lit else INK_DIM)
        a[y:y + 20, 26:126] = t
        # top-right corner: close button, the scrollbar's top
        t = bar20(25, lit, right_edge=True)
        rect(t, 0, 19, 6, 1, (130, 135, 144))
        close_group(t, 13, lit)
        rect(t, 5, 19, 1, 1, (130, 135, 144))
        rect(t, 9, 18, 10, 2, (232, 232, 232))
        rect(t, 9, 18, 10, 1, (200, 200, 200))
        a[y:y + 20, 153:178] = t

    # left side tile: glass 0..4, face 5..10, the list's border at 11
    a[42:71, 0:12] = side_tile(12, 29, True)
    # right side tile: list border, face, the scrollbar track at 4..13, face, glass 15..19
    t = side_tile(20, 29, False)
    rect(t, 4, 0, 10, 29, (232, 232, 232))
    rect(t, 4, 0, 1, 29, (214, 214, 214))
    rect(t, 13, 0, 1, 29, (214, 214, 214))
    a[42:71, 31:51] = t
    # close pressed, scroll handles
    t = new(9, 9)
    caption_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        a[53:71, x:x + 8] = scroll_thumb(sel)

    # bottom pieces (38 tall: face rows 0..32, glass 33..37)
    t = bottom_piece(125, 38, left_edge=True)
    rect(t, 11, 0, 114, 1, (130, 135, 144))
    rect(t, 11, 0, 1, 1, (130, 135, 144))
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        pl_button(t, bx, 8, 22, 18, lbl)
    a[72:110, 0:125] = t

    t = bottom_piece(150, 38, right_edge=True)
    rect(t, 0, 0, 131, 1, (130, 135, 144))
    rect(t, 130, 0, 1, 1, (130, 135, 144))
    # running time readout
    text_field(t, 5, 8, 58, 10)
    # mini transport: little dark glass buttons
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    strip = new(60, 10, FACE)
    for r in range(10):
        strip[r, :] = t[22 + r, 3]
    shape(strip, 0, 0, round_mask(60, 10, 4.5), rows_face(60, 10, DARK_GLASS), (10, 14, 20))
    for k, kind in enumerate(icons):
        mini_transport_icon(strip, kind, 10 * k, 0)
        if 0 < k:
            rect(strip, 10 * k, 3, 1, 4, (60, 70, 84))
    t[22:32, 3:63] = strip
    # mini time
    text_field(t, 65, 21, 34, 10)
    rect(t, 84, 22 + 2, 1, 1, (90, 96, 104))
    rect(t, 84, 22 + 5, 1, 1, (90, 96, 104))
    # LIST button
    pl_button(t, 106, 8, 22, 18, "LIST")
    # resize grip (Windows 7's dots)
    for k in range(3):
        for j in range(k + 1):
            gx, gy = 141 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx + 1, gy + 1, WHITE)
            px(t, gx, gy, (150, 160, 172))
    a[72:110, 126:276] = t

    t = bottom_piece(25, 38)
    rect(t, 0, 0, 25, 1, (130, 135, 144))
    a[0:38, 179:204] = t
    return a


def scroll_thumb(selected):
    """8x18: a Windows 7 scrollbar thumb, light glass (blue when dragged), with a grip."""
    a = new(8, 18, (232, 232, 232))
    if selected:
        stops = [(0, (230, 244, 252)), (0.5, (196, 228, 248)), (0.52, (170, 214, 244)), (1, (190, 224, 248))]
        border = (60, 127, 177)
    else:
        stops = [(0, (252, 252, 252)), (0.5, (236, 236, 236)), (0.52, (222, 222, 222)), (1, (232, 232, 232))]
        border = (151, 151, 151)
    # gradient across (Windows 7's vertical thumb shades left to right)
    face = np.transpose(rows_face(18, 8, stops), (1, 0, 2))
    shape(a, 0, 0, round_mask(8, 18, 2), face, border)
    for yy in (6, 8, 10):
        rect(a, 2, yy, 4, 1, (130, 140, 150) if not selected else (60, 110, 160))
        rect(a, 2, yy + 1, 4, 1, WHITE)
    return a


def mini_transport_icon(a, kind, x, y):
    ink = ICON
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
    a = new(194, 109, FACE)
    for lit, y in ((True, 0), (False, 21)):
        def put(px0, t):
            a[y:y + 20, px0:px0 + 25] = t

        # left corner: glass edge, face from x 5
        put(0, bar20(25, lit, left_edge=True))
        # the caption glow's left end: glass fading into it over the last 8 columns
        t = bar20(25, lit)
        pill_over(t, lit, 17, 25, 8, 0)
        put(26, t)
        # its uniform middle
        t = bar20(25, lit)
        pill_over(t, lit, 0, 25, 0, 0)
        put(52, t)
        t = bar20(25, lit)
        pill_over(t, lit, 0, 8, 0, 8)
        put(78, t)
        put(104, bar20(25, lit))
        t = bar20(25, lit, right_edge=True)
        close_group(t, 13, lit)
        put(130, t)

    # bottom (14 tall: face rows 0..8, glass 9..13)
    a[42:56, 0:125] = bottom_piece(125, 14, left_edge=True)
    t = bottom_piece(125, 14, right_edge=True)
    for k in range(2):
        for j in range(k + 1):
            gx, gy = 116 - 3 * k + 3 * j, 6 - 3 * j
            px(t, gx + 1, gy + 1, WHITE)
            px(t, gx, gy, (150, 160, 172))
    a[57:71, 0:125] = t
    a[72:86, 127:152] = bottom_piece(25, 14)
    # sides: left 11 wide (glass 0..4, face 5..10), right 8 wide (face 0..2, glass 3..7);
    # the right one's first column is stretched over a wider inset, so it is plain face
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = side_tile(w, h, left, list_border=False)
        if not left:
            rect(t, 0, 0, w - GLASS_SIDE - 1, h, FACE)
        a[42:42 + h, x:x + w] = t
    t = new(9, 9)
    caption_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: each row starts at x 1, letters in their own cells, 1px separators of x 0's colour;
    # each cell carries the caption glow's rows 4..10 behind its letter
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        pr = pill_rows(lit)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(CAPTION, c) + 1
            for r in range(7):
                rect(a, x, y + r, w, 1, pr[4 + r])
            draw_text(a, CAPTION, c, x, y, INK if lit else INK_DIM)
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------

GENEX_COLOURS = [
    (255, 255, 255),   # item background
    (0, 0, 0),         # item text
    (240, 240, 240),   # window background
    (0, 0, 0),         # button text
    (0, 0, 0),         # window text
    (160, 160, 160),   # dividers, sunken borders
    (204, 232, 255),   # selection bar (#cce8ff)
    (255, 255, 255),   # list header background
    (76, 96, 122),     # list header text
    (255, 255, 255),   # header frame, light
    (213, 213, 213),   # header frame, dark
    (188, 220, 244),   # header frame, pressed
    (255, 255, 255),   # header dead area
    (232, 232, 232),   # scrollbar
    (205, 205, 205),   # scrollbar 2
    (198, 232, 250),   # scrollbar pressed
    (96, 160, 220),    # scrollbar pressed 2
    (240, 240, 240),   # scrollbar dead area
]


def make_genex():
    a = new(256, 64, FACE)
    for i, c in enumerate(GENEX_COLOURS):
        px(a, 48 + 2 * i, 0, c)
    win_button(a, 0, 1, 47, 15, "normal")
    win_button(a, 0, 16, 47, 15, "pressed")
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------

VISCOLOR = (
    [(VIS_BG, "background"), (VIS_DOT, "dots")]
    + [(ramp([(220, 248, 255), (120, 222, 255), (40, 170, 250), (24, 110, 222), (18, 66, 176), (14, 42, 120)],
             i / 15), f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}") for i in range(16)]
    + [((210, 244, 255), "oscilloscope 1"), ((150, 218, 255), "oscilloscope 2"), ((100, 186, 248), "oscilloscope 3"),
       ((62, 150, 232), "oscilloscope 4"), ((40, 110, 200), "oscilloscope 5"), ((255, 255, 255), "peaks")]
)

PLEDIT = dict(Normal="#000000", Current="#1E5FB4", NormalBG="#FFFFFF", SelectedBG="#CCE8FF",
              MbBG="#FFFFFF", MbFG="#000000", Font="Arial")


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


REGION = [(2, 0), (273, 0), (273, 1), (274, 1), (274, 2), (275, 2), (275, 116), (0, 116), (0, 2), (1, 2), (1, 1),
          (2, 1)]


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in VISCOLOR:
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write("[Text]\n" + "".join(f"{k}={v}\n" for k, v in PLEDIT.items()))
    with open(os.path.join(OUT, "region.txt"), "w", newline="\r\n") as f:
        pts = " ".join(f"{x},{y}" for x, y in REGION)
        f.write("; the main window's top corners rounded, as Windows 7's are\n")
        for sec in ("Normal", "Equalizer"):
            f.write(f"[{sec}]\nNumPoints={len(REGION)}\nPointList={pts}\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            "Windows 7 — a skin in the style of Windows 7's Aero theme, drawn from scratch\n"
            "(apart from the Windows flag in the About spot). Not affiliated with Microsoft.\n\n"
            "A classic (Winamp 2.x format) skin: Aero glass frames, the light window face, Windows 7\n"
            "buttons and trackbars, a green progress bar for the seek bar, a dark glossy display.\n"
            "Every bitmap was drawn by a script (gen_skin.py) from gradients, shapes and hand-made\n"
            "pixel fonts; no screenshots or copied artwork.\n\n"
            "Windows logo © Microsoft; private use only.\n"
        )


# ------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------

SHEETS = {}


def build():
    global GLASS_MAIN, GLASS_EQ
    GLASS_MAIN = main_glass(True, seed=7)
    GLASS_EQ = main_glass(True, seed=11)
    sheets = {
        "main.bmp": make_main(),
        "titlebar.bmp": make_titlebar(),
        "cbuttons.bmp": make_cbuttons(),
        "shufrep.bmp": make_shufrep(),
        "posbar.bmp": make_posbar(),
        "volume.bmp": make_volume(),
        "balance.bmp": make_balance(),
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
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "region.txt", "readme.txt"]
    wsz = os.path.join(HERE, WSZ_NAME)
    with zipfile.ZipFile(wsz, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(OUT, n), "rb") as f:
                z.writestr(info, f.read())
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


def ui_font(size=11):
    for name in ("LiberationSans-Regular.ttf", "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
                 "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


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
    if state["pressed"] == "close":
        blit(img, S["titlebar"], (18, 9, 9, 9), 264, 3)
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
    # title: the space cell across the box, then the title in pledit's font and Normal colour
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    layer = Image.new("RGB", (154, 14), (255, 255, 255))
    ImageDraw.Draw(layer).text((0, 7 + 2 - 2), state["title"], fill=hexrgb(PLEDIT["Normal"]), font=ui_font(11),
                               anchor="lm")
    img.paste(layer, (111, 22))
    draw_bitmap_text(img, "192", 111, 43)
    draw_bitmap_text(img, "44", 156, 43)
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
            vp[x, y] = cols[min(17, max(2, y + 2))]
        pk = heights[x // 4] + 2
        if 0 <= 16 - pk < 16:
            vp[x, 16 - pk] = cols[23]
    img.paste(vis, (24, 43))
    # region.txt: the cut corners show what's behind
    for x, y in ((0, 0), (1, 0), (0, 1), (274, 0), (273, 0), (274, 1)):
        img.putpixel((x, y), BG)
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=hexrgb(PLEDIT["NormalBG"]))
    font = ui_font(11)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=hexrgb(PLEDIT["SelectedBG"]))
        col = hexrgb(PLEDIT["Current"] if i == 1 else PLEDIT["Normal"])
        d.text((lx + 2, y + 7), f"{i + 1}. {txt}", fill=col, font=font, anchor="lm")
        d.text((lx + lw - 3 - d.textlength(dur, font=font), y + 7), dur, fill=col, font=font, anchor="lm")
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
    # a stand-in picture: a sky-blue gradient
    pic = Image.linear_gradient("L").resize((w - 22, h - 34)).convert("RGB")
    arr = np.array(pic).astype(np.float32) / 255
    col = np.stack([30 + 120 * arr[..., 0], 80 + 120 * arr[..., 0], 160 + 80 * arr[..., 0]], -1)
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


BG = (58, 96, 140)


def preview():
    rows = [("Clear Skies - Translucent", "4:12"), ("Glass Harbour - Peek", "3:47"),
            ("Aero - Snap to Edge", "5:03"), ("Taskbar Lights - Jump List", "2:58"),
            ("The Seven - Shake", "6:21"), ("Libraries - Homegroup", "3:33"),
            ("Blue Hour - Flip 3D", "4:40"), ("Gadgets - Sidebar", "3:09"),
            ("Harmony - Calm Glass", "5:51"), ("Sky Mosaic - Sunrise", "4:05"),
            ("Theme Pack - Landscapes", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title="Windows 7 - Aero glass for Winamp", bars=bars)
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
        col = Image.new("RGB", (275, h), BG)
        col.paste(preview_main(lit, st), (0, 0))
        col.paste(preview_eq(lit, est), (0, 116))
        col.paste(preview_playlist(lit, 275, 232, rows, pressed_close=not lit, drag=not lit), (0, 232))
        col.paste(preview_gen(lit, 275, 140, "album art", pressed_close=not lit), (0, 464))
        cols.append(col)
    gap = 12
    out = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), BG)
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
