#!/usr/bin/python3
"""Windows Media Player: classic Winamp 2.x skins in the style of WMP's full mode: 7, 8, 9 Series,
10 and 11, plus two WMP-flavoured looks that claim no version (Blue and Dark).

One procedural generator (based on skins/ember/gen_skin.py, whose sheet layouts it keeps, with
the anti-aliased shape helpers of private-repo/skins/apps). Everything is drawn here from code:
gradients, glossy round buttons, hand-made pixel fonts, and each era's logo (7, 11, Blue, Dark:
redrawn as shapes, once per skin, in the bottom-right About spot; 8, 9, 10: the real Windows flag
from source/logo-windows-flag, once). The reference screenshots in source/ are only looked at,
never read by this script. Private use only.

    /usr/bin/python3 -I gen_skin.py [wmp7|wmp8|wmp9|wmp10|wmp11|wmp-blue|wmp-dark ...]   (none: all)
    /usr/bin/python3 -I gen_skin.py --list

Per theme: the bitmaps and text files in out/<theme>/, zipped flat into WMP-<n>.wsz beside this
file, and preview-<theme>.png (the windows assembled from the sprites the way the app does, 2x).
"""

import math
import os
import subprocess
import sys
import zipfile
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py, which finishes each .wsz
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.join(HERE, "out")
OUT = None          # out/<theme>, set by use_theme
T = None            # the theme in use

SEP = (255, 0, 255)  # gen.bmp letter separators (never shown)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ------------------------------------------------------------------------------------------
# Colour helpers
# ------------------------------------------------------------------------------------------


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    """Colour along a list of evenly spaced stops, t in 0..1."""
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    if n == 0:
        return tuple(stops[0])
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def grey(c):
    v = int(round(0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]))
    return (v, v, v)


def hexc(c):
    return "#%02X%02X%02X" % tuple(c)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int) and anti-aliased shapes (masks drawn 4x, box-filtered)
# ------------------------------------------------------------------------------------------


def new(w, h, col=BLACK):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        x0, y0 = max(0, x), max(0, y)
        a[y0:y + h, x0:x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def vgrad(h, stops, w=1):
    """(h, w, 3) float rows running through stops (top to bottom)."""
    rows = np.array([ramp(stops, (r + 0.5) / h) for r in range(h)], dtype=np.float32)
    return np.broadcast_to(rows[:, None, :], (h, w, 3)).copy()


def vfill(a, x, y, w, h, stops):
    if w > 0 and h > 0:
        g = np.round(vgrad(h, stops, w)).astype(np.int32)
        x0, y0 = max(0, x), max(0, y)
        a[y0:y + h, x0:x + w] = g[y0 - y:, x0 - x:]


def gcanvas(H, W, y0, h, stops):
    """A full (H, W, 3) canvas whose rows y0..y0+h run through stops (clamped outside)."""
    g = np.zeros((H, W, 3), dtype=np.float32)
    for r in range(H):
        g[r, :, :] = ramp(stops, (r - y0 + 0.5) / max(1, h))
    return g


SS = 4


def mask(w, h, fn):
    im = Image.new("L", (w * SS, h * SS), 0)
    fn(ImageDraw.Draw(im), SS)
    return np.asarray(im.resize((w, h), Image.BOX), dtype=np.float32) / 255.0


def rr_mask(w, h, r, x=0.0, y=0.0, mw=None, mh=None):
    mw = w - x if mw is None else mw
    mh = h - y if mh is None else mh

    def fn(d, S):
        d.rounded_rectangle((x * S, y * S, (x + mw) * S - 1, (y + mh) * S - 1), radius=max(0, r * S), fill=255)
    return mask(w, h, fn)


def ellipse_mask(w, h, x, y, ew, eh):
    return mask(w, h, lambda d, S: d.ellipse((x * S, y * S, (x + ew) * S - 1, (y + eh) * S - 1), fill=255))


def poly_mask(w, h, pts):
    return mask(w, h, lambda d, S: d.polygon([(px_ * S, py_ * S) for px_, py_ in pts], fill=255))


def line_mask(w, h, pts, width):
    return mask(w, h, lambda d, S: d.line([(px_ * S, py_ * S) for px_, py_ in pts], fill=255, width=int(width * S)))


def paint(a, x, y, m, col, alpha=1.0):
    """Blends colour (tuple, or an (h, w, 3) array for the mask) over a through mask m at (x, y)."""
    h, w = m.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(a.shape[1], x + w), min(a.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    mm = (m[y0 - y:y1 - y, x0 - x:x1 - x] * alpha)[..., None]
    c = np.asarray(col, dtype=np.float32)
    if c.ndim == 3:
        c = np.broadcast_to(c, (h, w, 3))[y0 - y:y1 - y, x0 - x:x1 - x]
    reg = a[y0:y1, x0:x1].astype(np.float32)
    a[y0:y1, x0:x1] = np.round(reg * (1 - mm) + c * mm).astype(np.int32)


def rbox(a, x, y, w, h, r, fill, edge=None, alpha=1.0):
    """A rounded box on canvas a: fill is a colour or a list of stops (vertical); edge a 1px rim."""
    if w <= 0 or h <= 0:
        return
    H, W = a.shape[0], a.shape[1]
    if edge is not None:
        paint(a, 0, 0, rr_mask(W, H, r, x, y, w, h), edge, alpha)
        m = rr_mask(W, H, max(0.0, r - 1), x + 1, y + 1, w - 2, h - 2)
        g = gcanvas(H, W, y + 1, h - 2, fill) if isinstance(fill, list) else fill
    else:
        m = rr_mask(W, H, r, x, y, w, h)
        g = gcanvas(H, W, y, h, fill) if isinstance(fill, list) else fill
    paint(a, 0, 0, m, g, alpha)


def sphere(a, cx, cy, d, stops, rim, gloss=0.55, gloss_col=WHITE):
    """A glossy round button of diameter d centred at (cx, cy)."""
    H, W = a.shape[0], a.shape[1]
    x0, y0 = cx - d / 2, cy - d / 2
    if rim is not None:
        paint(a, 0, 0, ellipse_mask(W, H, x0, y0, d, d), rim)
        x0, y0, d = x0 + 1, y0 + 1, d - 2
    paint(a, 0, 0, ellipse_mask(W, H, x0, y0, d, d), gcanvas(H, W, y0, d, stops))
    if gloss:
        paint(a, 0, 0, ellipse_mask(W, H, x0 + d * 0.17, y0 + 0.6, d * 0.66, d * 0.46), gloss_col, gloss)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def supersample(w, h, fn, k=6):
    """Renders fn(X, Y) -> (rgb (h*k, w*k, 3), alpha (h*k, w*k)) at k x and box-filters it down."""
    ys, xs = np.mgrid[0:h * k, 0:w * k].astype(np.float32)
    X, Y = (xs + 0.5) / k, (ys + 0.5) / k
    col, al = fn(X, Y)
    col = col * al[..., None]
    col = col.reshape(h, k, w, k, 3).mean(axis=(1, 3))
    al = al.reshape(h, k, w, k).mean(axis=(1, 3))
    out = np.where(al[..., None] > 1e-6, col / np.maximum(al[..., None], 1e-6), 0)
    return out, al


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

# A UI font for titlebar text: capitals 7 rows, x-height 5, descenders 2 (9 rows in all).
_LOWER = {
    "a": ["", "", ".##.", "...#", ".###", "#..#", ".###"],
    "b": ["#...", "#...", "###.", "#..#", "#..#", "#..#", "###."],
    "c": ["", "", ".###", "#...", "#...", "#...", ".###"],
    "d": ["...#", "...#", ".###", "#..#", "#..#", "#..#", ".###"],
    "e": ["", "", ".##.", "#..#", "####", "#...", ".###"],
    "f": [".##", "#..", "###", "#..", "#..", "#..", "#.."],
    "g": ["", "", ".###", "#..#", "#..#", "#..#", ".###", "...#", ".##."],
    "h": ["#...", "#...", "###.", "#..#", "#..#", "#..#", "#..#"],
    "i": ["#", ".", "#", "#", "#", "#", "#"],
    "j": [".#", "..", ".#", ".#", ".#", ".#", ".#", ".#", "#."],
    "k": ["#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#"],
    "l": ["#", "#", "#", "#", "#", "#", "#"],
    "m": ["", "", "####.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"],
    "n": ["", "", "###.", "#..#", "#..#", "#..#", "#..#"],
    "o": ["", "", ".##.", "#..#", "#..#", "#..#", ".##."],
    "p": ["", "", "###.", "#..#", "#..#", "#..#", "###.", "#...", "#..."],
    "q": ["", "", ".###", "#..#", "#..#", "#..#", ".###", "...#", "...#"],
    "r": ["", "", "#.#", "##.", "#..", "#..", "#.."],
    "s": ["", "", ".###", "#...", ".##.", "...#", "###."],
    "t": ["", ".#.", "###", ".#.", ".#.", ".#.", "..#"],
    "u": ["", "", "#..#", "#..#", "#..#", "#..#", ".###"],
    "v": ["", "", "#.#", "#.#", "#.#", "#.#", ".#."],
    "w": ["", "", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."],
    "x": ["", "", "#..#", "#..#", ".##.", "#..#", "#..#"],
    "y": ["", "", "#..#", "#..#", "#..#", "#..#", ".###", "...#", ".##."],
    "z": ["", "", "####", "..#.", ".#..", "#...", "####"],
    "-": ["", "", "", "", "###", "", ""],
    " ": [".."],
}
UI = {}
for _k, _rows in _LOWER.items():
    _w = max(len(r) for r in _rows)
    UI[_k] = [(r or "." * _w).ljust(_w, ".") for r in _rows] + ["." * _w] * (9 - len(_rows))
for _k, _g in FONT5.items():
    if _k.isupper() or _k.isdigit():
        UI[_k] = [_g[i] for i in (0, 1, 1, 2, 3, 3, 4)] + ["." * len(_g[0])] * 2
UI["9"] = [".##.", "#..#", "#..#", ".###", "...#", "#..#", ".##."] + ["...."] * 2
UI[":"] = [".", ".", "#", ".", ".", "#", ".", ".", "."]
UI["."] = [".", ".", ".", ".", ".", ".", "#", ".", "."]

# Clean sans digits for the time readout (7 x 11, in a 9 x 13 cell), like WMP's status clock.
DIGITS = {
    0: [".#####.", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##",
        "##...##", ".#####."],
    1: ["...##..", "..###..", ".####..", "...##..", "...##..", "...##..", "...##..", "...##..", "...##..",
        "...##..", ".######"],
    2: [".#####.", "##...##", ".....##", ".....##", "....##.", "...##..", "..##...", ".##....", "##.....",
        "##.....", "#######"],
    3: [".#####.", "##...##", ".....##", ".....##", "..####.", ".....##", ".....##", ".....##", ".....##",
        "##...##", ".#####."],
    4: ["....##.", "...###.", "..####.", ".##.##.", "##..##.", "##..##.", "#######", "....##.", "....##.",
        "....##.", "....##."],
    5: ["#######", "##.....", "##.....", "##.....", "######.", ".....##", ".....##", ".....##", ".....##",
        "##...##", ".#####."],
    6: [".#####.", "##...##", "##.....", "##.....", "######.", "##...##", "##...##", "##...##", "##...##",
        "##...##", ".#####."],
    7: ["#######", ".....##", ".....##", "....##.", "....##.", "...##..", "...##..", "..##...", "..##...",
        "..##...", "..##..."],
    8: [".#####.", "##...##", "##...##", "##...##", ".#####.", "##...##", "##...##", "##...##", "##...##",
        "##...##", ".#####."],
    9: [".#####.", "##...##", "##...##", "##...##", "##...##", ".######", ".....##", ".....##", ".....##",
        "##...##", ".#####."],
}


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1, bold=False):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) + (1 if bold else 0) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1, shadow=None, sh=(1, 1), bold=False):
    for c in s:
        if c not in font:
            continue
        g = font[c]
        passes = (0, 1) if bold else (0,)
        if shadow is not None:
            for b in passes:
                for r, row in enumerate(g):
                    for k, ch in enumerate(row):
                        if ch == "#":
                            px(a, x + k + b + sh[0], y + r + sh[1], shadow)
        for b in passes:
            for r, row in enumerate(g):
                for k, ch in enumerate(row):
                    if ch == "#":
                        px(a, x + k + b, y + r, col(r) if callable(col) else col)
        x += len(g[0]) + gap + (1 if bold else 0)
    return x


def text_center(a, font, s, cx, y, col, gap=1, shadow=None, sh=(1, 1), bold=False):
    return draw_text(a, font, s, cx - text_w(font, s, gap, bold) // 2, y, col, gap, shadow, sh, bold)


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    # WMP 7 (2000, Windows Me): the brushed-silver, curvy full-mode frame, the taskbar column of
    # grey buttons (the chosen one blue-violet), round silver play and stop buttons, the green
    # "Ready" status on black and a navy content pane, the embossed Windows Media flag.
    "wmp7": SimpleNamespace(
        name="wmp7", look="v7", label="WMP 7", wsz="WMP-7.wsz", era="Windows Media Player 7 (2000)",
        frame=[(238, 239, 244), (212, 214, 222), (194, 196, 205)],
        body=[(194, 196, 205), (176, 178, 188), (160, 162, 173)],
        rim=(62, 64, 78), hi=(246, 247, 251), lo=(118, 120, 134), gloss=0.0, brushed=2.2,
        pane=(0, 0, 0), pane_edge=(36, 40, 62), ink=(72, 222, 72), ink_dim=(22, 58, 22), pane_label=(44, 150, 52),
        body_label=(54, 56, 72), accent=(64, 74, 200), accent_hi=(132, 140, 240),
        deck=[(150, 152, 164), (124, 126, 140), (138, 140, 152)], deck_rim=(84, 86, 100), deck_hi=(214, 216, 224),
        btn=[(255, 255, 255), (222, 224, 230), (172, 174, 186), (196, 198, 208)], btn_rim=(92, 94, 108),
        btn_down=[(146, 148, 160), (178, 180, 192), (206, 208, 216)], glyph=(64, 66, 82), glyph_down=(40, 46, 130),
        play=[(255, 255, 255), (226, 228, 234), (170, 172, 184), (202, 204, 214)], play_glyph=(70, 72, 88),
        thumb=[(255, 255, 255), (206, 208, 216)], thumb_rim=(80, 82, 96), thumb_down=[(214, 218, 250), (150, 158, 230)],
        thumb_shape="square",
        track=(96, 98, 112), track_hi=(226, 228, 236), fill=[(150, 160, 255), (64, 74, 200)],
        task=[(170, 170, 176), (128, 128, 136), (104, 104, 112)], task_sel=[(128, 136, 240), (70, 70, 190), (40, 38, 140)],
        task_txt=(248, 248, 252), task_txt_dim=(214, 214, 220), task_bg=(70, 78, 104),
        title_lit=(36, 38, 54), title_dim=(122, 124, 138), title_shadow=(250, 250, 253), title_bold=False,
        caption="round",
        combo=[(255, 255, 255), (232, 234, 240)], combo_txt=(20, 22, 40), combo_edge=(96, 98, 114),
        pledit=dict(Normal="#E2E6F4", Current="#4CE04C", NormalBG="#001A52", SelectedBG="#3440B4"),
        vis_bars=[(236, 240, 255), (130, 150, 255), (70, 70, 220), (40, 24, 150)], vis_dots=(18, 20, 40),
        vis_peak=(255, 255, 255), vis_osc=[(140, 255, 140), (96, 232, 96), (72, 210, 72), (52, 180, 52), (36, 140, 36)],
        main_title="Windows Media Player", eq_title="Graphic Equalizer", pl_title="Now Playing",
        logo="flag",
    ),
    # WMP Blue (once "WMP 8"; WMP-flavoured, no version claimed): the periwinkle Luna-matching
    # frame, the blue taskbar column, the silver-blue rounded transport deck with the big round
    # play button, the green seek and volume thumbs, green status text on black; the ring logo.
    "wmp-blue": SimpleNamespace(
        name="wmp-blue", look="blue", label="WMP Blue", wsz="WMP-Blue.wsz",
        era="Windows Media Player's full mode, in periwinkle blue",
        frame=[(164, 186, 248), (112, 140, 228), (146, 168, 236)],
        body=[(150, 172, 238), (136, 158, 230), (118, 142, 220)],
        rim=(44, 66, 160), hi=(226, 234, 255), lo=(84, 106, 196), gloss=0.0, brushed=0.0,
        pane=(0, 0, 0), pane_edge=(52, 74, 168), ink=(44, 232, 44), ink_dim=(14, 52, 14), pane_label=(30, 160, 40),
        body_label=(26, 44, 128), accent=(36, 70, 200), accent_hi=(120, 150, 240),
        deck=[(228, 234, 252), (190, 204, 246), (160, 180, 238), (180, 196, 244)], deck_rim=(66, 92, 186),
        deck_hi=(250, 252, 255),
        btn=[(255, 255, 255), (226, 234, 252), (168, 188, 242), (204, 216, 250)], btn_rim=(64, 90, 180),
        btn_down=[(150, 172, 236), (186, 202, 246), (220, 228, 252)], glyph=(34, 58, 150), glyph_down=(20, 36, 110),
        play=[(255, 255, 255), (230, 236, 252), (166, 186, 240), (206, 218, 250)], play_glyph=(40, 64, 156),
        thumb=[(222, 255, 204), (122, 214, 84), (70, 170, 48)], thumb_rim=(36, 110, 30),
        thumb_down=[(255, 255, 230), (170, 240, 120), (96, 200, 60)], thumb_shape="pill",
        track=(48, 66, 150), track_hi=(236, 242, 255), fill=[(250, 252, 255), (156, 182, 244)],
        task=[(140, 162, 234), (116, 140, 224), (100, 126, 216)], task_sel=[(214, 226, 255), (170, 190, 248), (146, 170, 240)],
        task_txt=(255, 255, 255), task_txt_dim=(232, 238, 255), task_txt_sel=(20, 40, 120), task_bg=(88, 112, 204),
        title_lit=(255, 255, 255), title_dim=(76, 92, 150), title_shadow=(22, 38, 128), title_bold=False,
        caption="xp",
        combo=[(255, 255, 255), (240, 244, 252)], combo_txt=(10, 20, 60), combo_edge=(80, 106, 196),
        pledit=dict(Normal="#DCDCDC", Current="#2CE82C", NormalBG="#000000", SelectedBG="#26408E"),
        vis_bars=[(236, 255, 160), (130, 240, 70), (40, 200, 50), (10, 120, 40)], vis_dots=(16, 30, 18),
        vis_peak=(255, 255, 255), vis_osc=[(150, 255, 150), (100, 240, 100), (60, 220, 60), (40, 190, 40), (24, 150, 24)],
        main_title="Windows Media Player", eq_title="Graphic Equalizer", pl_title="Sample Playlist",
        logo="ring_xp",
    ),
    # WMP Dark (once "WMP 9"; WMP-flavoured, no version claimed): the dark blue-black chrome with
    # a cool sheen, glossy pale-blue round buttons on a dark deck, green seek and volume thumbs,
    # the blue visualisation; the glossy ring logo with the blue play arrow.
    "wmp-dark": SimpleNamespace(
        name="wmp-dark", look="dark", label="WMP Dark", wsz="WMP-Dark.wsz",
        era="Windows Media Player's full mode, in dark blue",
        frame=[(76, 92, 148), (36, 46, 90), (24, 32, 66)],
        body=[(24, 32, 66), (16, 22, 48), (8, 10, 24)],
        rim=(0, 0, 6), hi=(98, 120, 186), lo=(2, 4, 12), gloss=0.10, brushed=0.0,
        pane=(0, 0, 0), pane_edge=(54, 74, 136), ink=(196, 218, 255), ink_dim=(22, 30, 54), pane_label=(96, 126, 200),
        body_label=(150, 170, 222), accent=(110, 170, 255), accent_hi=(170, 210, 255),
        deck=[(58, 72, 124), (22, 28, 60), (10, 12, 28), (20, 26, 54)], deck_rim=(112, 140, 220), deck_hi=(140, 166, 236),
        btn=[(255, 255, 255), (214, 226, 250), (128, 152, 214), (176, 196, 240)], btn_rim=(10, 16, 44),
        btn_down=[(110, 136, 204), (160, 184, 236), (204, 218, 250)], glyph=(22, 38, 108), glyph_down=(10, 22, 80),
        play=[(255, 255, 255), (216, 230, 252), (120, 150, 222), (178, 200, 246)], play_glyph=(24, 44, 124),
        thumb=[(214, 255, 196), (104, 206, 72), (52, 156, 40)], thumb_rim=(14, 70, 14),
        thumb_down=[(255, 255, 230), (160, 240, 120), (84, 196, 56)], thumb_shape="pill",
        track=(4, 6, 16), track_hi=(70, 90, 150), fill=[(150, 200, 255), (50, 110, 230)],
        task=[(52, 64, 112), (32, 40, 78), (22, 28, 58)], task_sel=[(150, 190, 255), (70, 120, 230), (40, 76, 180)],
        task_txt=(206, 218, 250), task_txt_dim=(150, 162, 200), task_txt_sel=(255, 255, 255), task_bg=(6, 8, 20),
        title_lit=(232, 238, 255), title_dim=(118, 126, 150), title_shadow=(0, 0, 0), title_bold=False,
        title_series=(120, 176, 255), title_series_dim=(96, 110, 146),
        caption="glass",
        combo=[(36, 44, 80), (16, 20, 42)], combo_txt=(214, 226, 255), combo_edge=(84, 106, 170),
        pledit=dict(Normal="#C8D4F0", Current="#7CC4FF", NormalBG="#000000", SelectedBG="#1E2E66"),
        vis_bars=[(240, 252, 255), (120, 210, 255), (50, 120, 240), (30, 40, 160)], vis_dots=(10, 14, 30),
        vis_peak=(255, 255, 255), vis_osc=[(200, 230, 255), (150, 200, 255), (110, 170, 255), (80, 130, 230),
                                           (60, 90, 200)],
        main_title="Windows Media Player", eq_title="Graphic Equalizer",
        pl_title="Now Playing",
        logo="ring_9",
    ),
    # WMP 11 (2006; once called "WMP 10" here): near-black chrome, the task tabs along the top
    # (Now Playing lit in glassy blue), the black rounded transport bar with its blue rim and the
    # blue glass play button, round blue thumbs, white text; the same ring logo as 9.
    "wmp11": SimpleNamespace(
        name="wmp11", look="w11", label="WMP 11", wsz="WMP-11.wsz", era="Windows Media Player 11 (2006)",
        frame=[(64, 68, 80), (28, 30, 36), (18, 19, 24)],
        body=[(18, 19, 24), (12, 13, 16), (6, 6, 8)],
        rim=(0, 0, 0), hi=(70, 76, 92), lo=(0, 0, 0), gloss=0.12, brushed=0.0,
        pane=(0, 0, 0), pane_edge=(44, 62, 112), ink=(232, 238, 255), ink_dim=(26, 28, 36), pane_label=(110, 140, 204),
        body_label=(150, 160, 184), accent=(70, 150, 255), accent_hi=(170, 210, 255),
        deck=[(46, 50, 60), (14, 15, 19), (2, 2, 3), (12, 14, 20)], deck_rim=(46, 120, 236), deck_hi=(120, 180, 255),
        btn=[(120, 126, 142), (54, 58, 68), (14, 15, 18), (36, 40, 50)], btn_rim=(0, 0, 0),
        btn_down=[(10, 20, 50), (30, 70, 150), (60, 120, 220)], glyph=(236, 240, 250), glyph_down=(255, 255, 255),
        play=[(196, 228, 255), (90, 164, 250), (20, 70, 190), (40, 110, 230)], play_glyph=(255, 255, 255),
        thumb=[(214, 236, 255), (90, 160, 250), (34, 90, 210)], thumb_rim=(6, 24, 80),
        thumb_down=[(240, 248, 255), (140, 196, 255), (70, 130, 240)], thumb_shape="round",
        track=(30, 32, 40), track_hi=(70, 74, 88), fill=[(150, 200, 255), (40, 110, 230)],
        task=[(46, 50, 60), (26, 28, 34), (18, 19, 24)], task_sel=[(150, 200, 255), (60, 130, 240), (30, 80, 200)],
        task_txt=(200, 206, 222), task_txt_dim=(130, 136, 150), task_txt_sel=(255, 255, 255), task_bg=(4, 4, 6),
        title_lit=(236, 240, 250), title_dim=(126, 130, 142), title_shadow=(0, 0, 0), title_bold=False,
        caption="flat",
        combo=[(40, 44, 54), (16, 17, 22)], combo_txt=(226, 232, 248), combo_edge=(70, 76, 94),
        tabs=["Now Playing", "Library", "Rip", "Burn", "Sync", "Guide"],
        pledit=dict(Normal="#D8DEEA", Current="#5CB0FF", NormalBG="#000000", SelectedBG="#1C3A7A"),
        vis_bars=[(255, 255, 255), (130, 196, 255), (60, 110, 240), (90, 40, 190)], vis_dots=(12, 14, 22),
        vis_peak=(255, 255, 255), vis_osc=[(220, 236, 255), (170, 210, 255), (120, 180, 255), (80, 140, 240),
                                           (60, 100, 210)],
        main_title="Windows Media Player", eq_title="Graphic Equalizer", pl_title="Now Playing List",
        logo="ring_9",
    ),
}

# The accurate WMP 8, 9 Series and 10 looks, drawn from screenshots of the real players (see the
# "Accurate looks" section below for how their parts map onto Winamp's layout).
THEMES.update({
    # WMP for Windows XP (8, 2001): the curvy periwinkle frame, the silver bar along the top with
    # the round blue menu button, the taskbar (white bold labels, the chosen one darker with an
    # orange underline) sweeping into the rounded transport, bright green status text on black.
    "wmp8": SimpleNamespace(
        name="wmp8", look="x8", label="WMP 8", wsz="WMP-8.wsz",
        era="Windows Media Player for Windows XP (8, 2001)",
        frame=[(150, 164, 234), (116, 130, 216), (94, 106, 198)],
        body=[(132, 146, 228), (104, 118, 208), (84, 94, 184)],
        rim=(40, 44, 116), hi=(176, 188, 248), lo=(58, 64, 146), gloss=0.0, brushed=0.0,
        silver=[(254, 254, 255), (238, 238, 248), (214, 214, 228), (198, 198, 214)], silver_edge=(118, 120, 160),
        pane=(0, 0, 0), pane_edge=(44, 48, 120), ink=(0, 255, 0), ink_dim=(0, 56, 0), pane_label=(150, 154, 200),
        play_ind=(132, 130, 204), info=(0, 0, 0), info_txt=(255, 255, 255), info_label="Ambience: Random",
        sep=(150, 150, 168),
        body_label=(28, 34, 110), accent=(255, 157, 48), accent_hi=(170, 180, 246),
        deck=[(176, 188, 248), (128, 142, 226), (100, 112, 206), (114, 126, 214)], deck_rim=(52, 58, 140),
        deck_hi=(214, 222, 255),
        btn=[(255, 255, 255), (236, 238, 254), (188, 194, 240), (214, 218, 250)], btn_rim=(64, 70, 160),
        btn_down=[(156, 164, 226), (190, 196, 240), (222, 226, 252)], glyph=(40, 50, 146), glyph_down=(24, 30, 110),
        play=[(255, 255, 255), (238, 240, 255), (184, 190, 240), (212, 216, 250)], play_glyph=(40, 50, 146),
        thumb=[(255, 255, 255), (226, 228, 240), (186, 188, 208)], thumb_rim=(92, 94, 130),
        thumb_down=[(255, 255, 255), (200, 206, 246), (150, 160, 226)], thumb_shape="pill",
        track=(46, 211, 49), groove=(50, 56, 138), track_hi=(150, 164, 236), seek=[(160, 250, 150), (60, 222, 62), (30, 170, 36)],
        fill=[(150, 250, 140), (46, 200, 50)],
        task=[(112, 130, 214), (98, 118, 204), (90, 110, 196)], task_sel=[(84, 106, 190), (68, 92, 172), (62, 84, 162)],
        task_txt=(255, 255, 255), task_txt_dim=(214, 220, 250), task_txt_sel=(255, 255, 255), task_bg=(92, 112, 198),
        title_lit=(30, 36, 110), title_dim=(110, 114, 150), title_shadow=None, title_bold=False,
        caption="x8",
        combo=[(255, 255, 255), (240, 242, 250)], combo_txt=(10, 14, 50), combo_edge=(80, 86, 160),
        pledit=dict(Normal="#00D800", Current="#C8FFC8", NormalBG="#000000", SelectedBG="#2E2E2E"),
        vis_bars=[(210, 246, 255), (70, 196, 244), (24, 110, 210), (10, 30, 110)], vis_dots=(8, 14, 40),
        vis_peak=(255, 255, 255), vis_osc=[(190, 240, 255), (130, 220, 255), (70, 190, 244), (40, 140, 220),
                                           (24, 90, 190)],
        main_title="Windows Media Player", eq_title="Graphic Equalizer", pl_title="Sample Playlist",
        logo="xpflag",
    ),
    # WMP 9 Series (2003): the pale silver-white frame with its soft blue edge, the left taskbar of
    # navy labels on a light grey-blue gradient, the "Now Playing" drop-down by the window buttons,
    # the navy playlist, green status text on black, white glass transport with green thumbs.
    "wmp9": SimpleNamespace(
        name="wmp9", look="x9", label="WMP 9 Series", wsz="WMP-9.wsz",
        era="Windows Media Player 9 Series (2003)",
        frame=[(255, 255, 255), (234, 238, 248), (210, 218, 238)],
        body=[(246, 248, 253), (228, 233, 245), (208, 216, 236)],
        rim=(96, 116, 184), hi=(255, 255, 255), lo=(160, 172, 206), gloss=0.0, brushed=0.0,
        pane=(0, 0, 0), pane_edge=(70, 80, 120), ink=(140, 214, 70), ink_dim=(30, 52, 14), pane_label=(150, 160, 196),
        play_ind=(110, 200, 50), scroll=(44, 52, 92), info=(33, 39, 63), info_txt=(255, 255, 255), info_label="Rotating Particle",
        sep=(33, 39, 63),
        body_label=(20, 36, 100), accent=(56, 106, 179), accent_hi=(150, 180, 240),
        deck=[(255, 255, 255), (240, 243, 250), (210, 218, 234), (226, 232, 244)], deck_rim=(140, 152, 186),
        deck_hi=(255, 255, 255),
        btn=[(255, 255, 255), (240, 243, 250), (198, 206, 224), (222, 228, 240)], btn_rim=(112, 122, 152),
        btn_down=[(176, 186, 210), (206, 214, 232), (234, 238, 248)], glyph=(56, 60, 78), glyph_down=(30, 34, 60),
        play=[(255, 255, 255), (238, 242, 252), (192, 204, 228), (220, 228, 244)], play_glyph=(56, 60, 78),
        thumb=[(250, 252, 250), (216, 222, 220)], thumb_rim=(40, 168, 52),
        thumb_down=[(240, 255, 236), (170, 232, 150)], thumb_shape="pill",
        track=(196, 202, 216), track_hi=(255, 255, 255), seek=[(206, 212, 224), (226, 230, 238)],
        fill=[(176, 240, 150), (70, 186, 60)],
        task=[(214, 226, 246), (196, 212, 238), (180, 198, 232)], task_sel=[(255, 255, 255), (234, 240, 252), (214, 226, 248)],
        task_txt=(20, 36, 100), task_txt_dim=(90, 100, 140), task_txt_sel=(20, 36, 100), task_bg=(196, 212, 238),
        title_lit=(20, 36, 100), title_dim=(120, 128, 160), title_shadow=None, title_bold=False,
        caption="x9",
        combo=[(255, 255, 255), (244, 246, 252)], combo_txt=(10, 14, 40), combo_edge=(130, 146, 190),
        pledit=dict(Normal="#DCE2F4", Current="#9CE650", NormalBG="#394472", SelectedBG="#386AB3"),
        vis_bars=[(255, 255, 255), (190, 220, 255), (150, 90, 220), (90, 30, 160)], vis_dots=(16, 16, 30),
        vis_peak=(255, 255, 255), vis_osc=[(255, 255, 255), (220, 230, 255), (180, 200, 255), (150, 140, 240),
                                           (130, 90, 220)],
        main_title="Windows Media Player", eq_title="Graphic Equalizer", pl_title="Now Playing List",
        logo="xpflag",
    ),
    # WMP 10 (2004): the light blue frame, the task tabs across the top (Now Playing raised and
    # lighter), the darker blue info bar, white text on the black vis area, the blue playlist with
    # white text, and the pale glass transport bar with green seek and volume.
    "wmp10": SimpleNamespace(
        name="wmp10", look="x10", label="WMP 10", wsz="WMP-10.wsz", era="Windows Media Player 10 (2004)",
        frame=[(246, 250, 255), (222, 234, 252), (196, 214, 242)],
        body=[(124, 190, 246), (96, 170, 238), (74, 150, 228)],
        rim=(44, 92, 168), hi=(176, 222, 252), lo=(50, 112, 196), gloss=0.0, brushed=0.0,
        pane=(0, 0, 0), pane_edge=(36, 70, 130), ink=(255, 255, 255), ink_dim=(40, 44, 56), pane_label=(150, 180, 230),
        play_ind=(255, 255, 255), info=(56, 106, 179), info_txt=(255, 255, 255), info_label="Ambience : Water",
        sep=(56, 106, 179),
        body_label=(30, 60, 120), accent=(115, 159, 231), accent_hi=(170, 210, 255),
        deck=[(252, 253, 254), (226, 236, 248), (190, 210, 236), (130, 168, 220)], deck_rim=(70, 120, 196),
        deck_hi=(255, 255, 255),
        btn=[(255, 255, 255), (238, 244, 252), (194, 212, 238), (220, 232, 248)], btn_rim=(96, 132, 190),
        btn_down=[(170, 192, 226), (202, 218, 240), (232, 240, 250)], glyph=(54, 62, 84), glyph_down=(26, 34, 60),
        play=[(255, 255, 255), (238, 244, 252), (190, 208, 236), (218, 230, 248)], play_glyph=(54, 62, 84),
        thumb=[(255, 255, 255), (228, 236, 246), (190, 206, 228)], thumb_rim=(90, 120, 170),
        thumb_down=[(255, 255, 255), (200, 220, 246), (150, 184, 236)], thumb_shape="pill",
        track=(110, 196, 10), groove=(70, 104, 160), track_hi=(220, 234, 250), seek=[(200, 250, 120), (136, 210, 6), (92, 170, 0)],
        fill=[(170, 236, 90), (90, 188, 8)],
        task=[(66, 116, 189), (56, 106, 179), (48, 96, 168)], task_sel=[(150, 190, 244), (115, 159, 231), (96, 140, 220)],
        task_txt=(255, 255, 255), task_txt_dim=(200, 214, 240), task_txt_sel=(255, 255, 255), task_bg=(56, 106, 179),
        title_lit=(52, 64, 96), title_dim=(130, 140, 164), title_shadow=None, title_bold=False,
        tab_txt=(54, 66, 98), tab_sep=(178, 198, 228), scroll=(166, 194, 236),
        caption="x10",
        combo=[(150, 190, 244), (115, 159, 231)], combo_txt=(255, 255, 255), combo_edge=(60, 100, 170),
        tabs=["Now Playing", "Library", "Rip", "Burn", "Sync", "Guide"],
        pledit=dict(Normal="#FFFFFF", Current="#B4C6FF", NormalBG="#5482C3", SelectedBG="#335B9D"),
        vis_bars=[(255, 255, 255), (236, 200, 246), (160, 70, 170), (80, 20, 100)], vis_dots=(20, 10, 26),
        vis_peak=(255, 255, 255), vis_osc=[(255, 255, 255), (246, 220, 250), (220, 170, 236), (180, 110, 200),
                                           (140, 60, 160)],
        main_title="Windows Media Player", eq_title="Graphic Equalizer", pl_title="All Music",
        logo="xpflag",
    ),
})
THEMES = {k: THEMES[k] for k in ("wmp7", "wmp8", "wmp9", "wmp10", "wmp11", "wmp-blue", "wmp-dark")}
NEW = ("x8", "x9", "x10")


def use_theme(name):
    global T, OUT
    T = THEMES[name]
    OUT = os.path.join(OUT_ROOT, name)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT_ROOT, "scratch"), exist_ok=True)


def flat_body():
    return ramp(T.body, 0.45)


def light_frame():
    return T.look in ("v7", "blue") + NEW


# ------------------------------------------------------------------------------------------
# Logos (redrawn from shapes, one per skin)
# ------------------------------------------------------------------------------------------

FLAG = [(242, 80, 34), (64, 178, 60), (36, 112, 222), (252, 196, 26)]   # red, green, blue, yellow


def logo_ring(size, style):
    """The WMP 8 / 9 / 10 logo: a ring split into the Windows colours round a white disc with a play
    arrow (8: dark, 9 and 10: blue and glossier). Returns (rgb, alpha) arrays size x size."""
    R = size / 2 - 0.3
    cx = cy = size / 2
    ring_in = R * 0.70
    disc = R * 0.62
    cols = {"ring_xp": [(236, 70, 30), (90, 186, 50), (250, 196, 30), (40, 110, 220)],
            "ring_9": [(232, 72, 30), (104, 190, 52), (252, 186, 24), (36, 104, 216)]}[style]

    def fn(X, Y):
        dx, dy = X - cx, Y - cy
        r = np.sqrt(dx * dx + dy * dy)
        ang = np.arctan2(dy, dx)                       # 0 = right, positive = down
        out = np.zeros(X.shape + (3,), np.float32)
        al = (r <= R).astype(np.float32)
        # quadrants: top-left red, top-right green, bottom-right yellow, bottom-left blue
        q = np.where(dy < 0, np.where(dx < 0, 0, 1), np.where(dx >= 0, 2, 3))
        base = np.array(cols, np.float32)[q]
        shade = 1.0 + 0.35 * (-dy / R) - 0.12 * (r / R)
        ring = np.clip(base * shade[..., None], 0, 255)
        # thin light seams between the segments
        seam = (np.minimum(np.abs(dx), np.abs(dy)) < R * 0.05) & (r > ring_in)
        ring[seam] = (250, 250, 250)
        out[:] = ring
        # dark rim
        rim = (r > R - 0.9)
        out[rim] = np.clip(base[rim] * 0.55, 0, 255)
        # the white gap and disc
        gap = (r <= ring_in) & (r > disc)
        out[gap] = (250, 251, 255)
        din = r <= disc
        t = np.clip((dy + disc) / (2 * disc), 0, 1)
        dcol = np.stack([255 - 60 * t, 255 - 52 * t, 255 - 36 * t], -1)
        out[din] = dcol[din]
        # the play arrow
        s = disc
        ax0, ax1 = cx - s * 0.42, cx + s * 0.62
        inside = (X >= ax0) & (np.abs(dy) <= (ax1 - X) / (ax1 - ax0) * s * 0.62)
        if style == "ring_xp":
            acol = np.stack([60 - 40 * t, 62 - 40 * t, 70 - 40 * t], -1)
        else:
            acol = np.stack([70 - 50 * t, 140 - 80 * t, 250 - 70 * t], -1)
        out[inside & din] = acol[inside & din]
        # gloss over the top half
        gl = ((dx / (R * 0.8)) ** 2 + ((dy + R * 0.42) / (R * 0.5)) ** 2) < 1
        k = 0.30 if style == "ring_9" else 0.18
        out[gl] = out[gl] * (1 - k) + 255 * k
        return out, al
    return supersample(size, size, fn)


def logo_flag(w, h):
    """The Windows Media mark of WMP 7: the waving four-pane flag with its trail of squares."""
    def fn(X, Y):
        out = np.zeros(X.shape + (3,), np.float32)
        al = np.zeros(X.shape, np.float32)
        # flag body from u 0.32..1 (of w), v 0.1..0.9 (of h), waving
        u, v = X / w, Y / h
        wave = 0.10 * np.sin((u - 0.36) * 8.0)
        vv = v + wave
        fx0, fx1, fy0, fy1 = 0.36, 0.98, 0.12, 0.84
        inflag = (u >= fx0) & (u <= fx1) & (vv >= fy0) & (vv <= fy1)
        mu, mv = (fx0 + fx1) / 2, (fy0 + fy1) / 2
        gapu = np.abs(u - mu) < 0.025
        gapv = np.abs(vv - mv) < 0.03
        q = np.where(vv < mv, np.where(u < mu, 0, 1), np.where(u < mu, 2, 3))
        base = np.array(FLAG, np.float32)[q]
        shade = 1.0 + 0.28 * np.sin((u - 0.36) * 8.0 + 1.4)
        body = inflag & ~gapu & ~gapv
        out[body] = np.clip(base[body] * shade[body][..., None], 0, 255)
        al[body] = 1
        # the trail: small squares fading to the left, in each row's colours
        for i, (su, ss) in enumerate(((0.27, 0.10), (0.15, 0.08), (0.05, 0.06))):
            for row, (vy, ci) in enumerate(((0.30, 0), (0.62, 2))):
                cv = vy + 0.10 * np.sin((su - 0.36) * 8.0)
                sq = (np.abs(u - su) < ss / 2) & (np.abs(v - cv) < ss * w / h / 2 * 1.0)
                col = np.array(FLAG[ci if i % 2 == 0 else ci + 1], np.float32)
                out[sq] = col
                al[sq] = 1
        return out, al
    return supersample(w, h, fn)


def draw_logo(a, x, y, size):
    """The theme's logo, size x size, at (x, y) of canvas a."""
    if T.logo == "flag":
        # on a slate tile, as the flag sat embossed in WMP 7's dark lower-left corner
        rbox(a, x, y, size, size, 4, [(98, 108, 138), (60, 68, 94)], (40, 44, 62))
        rect(a, x + 3, y + 1, size - 6, 1, (132, 142, 170))
        col, al = logo_flag(size - 6, size - 8)
        paint(a, x + 3, y + 4, al, col)
    else:
        col, al = logo_ring(size, T.logo)
        # a soft drop shadow
        sh = np.zeros_like(al)
        sh[1:, 1:] = al[:-1, :-1]
        paint(a, x, y, sh, BLACK, 0.35)
        paint(a, x, y, al, col)


# ------------------------------------------------------------------------------------------
# Frame pieces: titlebar backgrounds, caption buttons
# ------------------------------------------------------------------------------------------


def frame_stops(lit):
    if lit:
        return T.frame
    return [lerp(c, lerp(grey(c), flat_body(), 0.3), 0.75) for c in T.frame]


_brng = np.random.default_rng(2000)


def brushed(a, x, y, w, h, amp):
    """WMP 7's faint brushed-silver grain (horizontal smears; wraps, so tiles stay seamless)."""
    if amp <= 0:
        return
    n = _brng.normal(0, 1, (h, w))
    acc = np.zeros_like(n)
    for d in range(-6, 7):
        acc += np.roll(n, d, axis=1)
    acc /= 4.0
    a[y:y + h, x:x + w] += np.round(acc * amp).astype(np.int32)[:, :, None]


def frame_bg(a, x, y, w, h, lit):
    vfill(a, x, y, w, h, frame_stops(lit))
    if T.gloss:
        # the glassy sheen of 9 and 10: the upper half a little lighter
        hh = max(1, h // 2)
        reg = a[y:y + hh, x:x + w].astype(np.float32)
        a[y:y + hh, x:x + w] = np.round(reg + (255 - reg) * T.gloss * (1 if lit else 0.5)).astype(np.int32)
    brushed(a, x, y, w, h, T.brushed)


def bar_frame(w, h, lit, left_edge=False, right_edge=False):
    """A titlebar strip: the frame gradient, a top highlight and side borders."""
    if T.look in NEW:
        return xbar(w, h, lit, left_edge, right_edge)
    a = new(w, h)
    frame_bg(a, 0, 0, w, h, lit)
    rect(a, 0, 0, w, 1, T.rim)
    rect(a, 0, 1, w, 1, lerp(frame_stops(lit)[0], WHITE, 0.5) if light_frame() else T.hi)
    if left_edge:
        rect(a, 0, 0, 1, h, T.rim)
        rect(a, 1, 1, 1, h - 1, lerp(frame_stops(lit)[0], WHITE, 0.4) if light_frame() else T.hi)
    if right_edge:
        rect(a, w - 1, 0, 1, h, T.rim)
        rect(a, w - 2, 1, 1, h - 1, T.lo)
    return a


def frame_colour_at(row, lit, h=14):
    return ramp(frame_stops(lit), (row + 0.5) / h)


def caption_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: options (the menu), minimize, shade, close."""
    if T.look in NEW:
        return xcaption(a, x, y, kind, lit, pressed)
    W, H = a.shape[1], a.shape[0]
    style = T.caption
    if style == "round":
        # WMP 7's little round silver buttons
        stops = T.btn_down if pressed else ([(255, 255, 255), (214, 216, 224), (160, 162, 174)] if lit
                                             else [(240, 240, 244), (212, 212, 218), (184, 184, 192)])
        sphere(a, x + 4.5, y + 4.5, 9, stops, T.btn_rim if lit else (130, 132, 144), gloss=0.0)
        ink = T.glyph_down if pressed else ((50, 52, 66) if lit else (120, 122, 136))
    elif style == "xp":
        # WMP 8: small rounded silver-blue buttons, the close one with a red cross
        stops = T.btn_down if pressed else ([(255, 255, 255), (220, 230, 252), (176, 194, 244)] if lit
                                             else [(242, 244, 250), (222, 228, 242), (204, 212, 232)])
        rbox(a, x, y, 9, 9, 2.5, stops, T.btn_rim if lit else (128, 144, 196))
        ink = (196, 40, 30) if kind == "close" and lit else ((30, 52, 140) if lit else (120, 134, 180))
    elif style == "glass":
        # WMP 9: light glyphs on the dark chrome; pressed, a glossy blue square lights up
        if pressed:
            rbox(a, x, y, 9, 9, 2.5, [(150, 190, 255), (60, 110, 220)], (20, 40, 110))
        ink = WHITE if pressed else ((210, 222, 250) if lit else (110, 118, 140))
    else:
        # WMP 10: bare glyphs; pressed, a blue glass square
        if pressed:
            rbox(a, x, y, 9, 9, 2, [(130, 190, 255), (40, 110, 230)], (10, 40, 120))
        ink = WHITE if pressed else ((206, 212, 226) if lit else (112, 116, 128))

    o = 1 if (pressed and style in ("round", "xp")) else 0
    X, Y = x + o * 0, y + o * 0
    if kind == "options":
        paint(a, 0, 0, poly_mask(W, H, [(X + 2, Y + 3.3), (X + 7, Y + 3.3), (X + 4.5, Y + 6.3)]), ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 2 if style in ("xp", "round") else 1, ink)
        if style not in ("xp", "round"):
            rect(a, X + 2, Y + 6, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 1, ink)
        rect(a, X + 2, Y + 3, 5, 1, ink)
        rect(a, X + 2, Y + 6, 5, 1, lerp(ink, frame_colour_at(y + 4, lit), 0.4))
    elif kind == "close":
        w = 1.5 if style in ("xp", "round") else 1.3
        paint(a, 0, 0, line_mask(W, H, [(X + 2.3, Y + 2.3), (X + 6.7, Y + 6.7)], w), ink)
        paint(a, 0, 0, line_mask(W, H, [(X + 6.7, Y + 2.3), (X + 2.3, Y + 6.7)], w), ink)


def title_text(a, s, cx, y, lit, series=None):
    """Titlebar text in the UI font, centred on cx (WMP 9: with its "9 Series" in light blue)."""
    col = T.title_lit if lit else T.title_dim
    bold = T.title_bold
    shadow = T.title_shadow if (lit or T.look not in ("v7", "blue")) else None
    if T.look == "v7" and lit:
        shadow, sh = T.title_shadow, (0, 1)
    else:
        sh = (1, 1)
    tw = text_w(UI, s, 1, bold)
    if series:
        tw += 4 + text_w(UI, series, 1, True)
    x = cx - tw // 2
    x = draw_text(a, UI, s, x, y, col, shadow=shadow, sh=sh, bold=bold)
    if series:
        draw_text(a, UI, series, x + 3, y, T.title_series if lit else T.title_series_dim, shadow=shadow,
                  sh=sh, bold=True)


def wmp10_tabs(a, x0, y, h, lit, labels, selected=0, right_limit=240):
    """WMP 10's task tabs along the top: the selected one a blue glass tab, the rest plain text."""
    W, H = a.shape[1], a.shape[0]
    x = x0
    for i, lab in enumerate(labels):
        tw = text_w(UI, lab)
        w = tw + 10
        if x + w > right_limit:
            break
        if i == selected:
            stops = T.task_sel if lit else [lerp(c, (60, 64, 76), 0.6) for c in T.task_sel]
            rbox(a, x, y, w, h + 4, 3, stops, (10, 30, 90) if lit else (30, 32, 40))
            paint(a, 0, 0, rr_mask(W, H, 2.5, x + 1.5, y + 1, w - 3, h * 0.42), WHITE, 0.28 if lit else 0.12)
            draw_text(a, UI, lab, x + 5, y + 2, WHITE if lit else (190, 194, 206), shadow=(10, 40, 120) if lit else None,
                      sh=(0, 1))
        else:
            draw_text(a, UI, lab, x + 5, y + 2, T.task_txt if lit else T.task_txt_dim)
            if i + 1 < len(labels):
                rect(a, x + w, y + 3, 1, h - 5, (60, 64, 76) if lit else (44, 46, 54))
        x += w + 1
    return x


# ------------------------------------------------------------------------------------------
# Fields, buttons, sliders
# ------------------------------------------------------------------------------------------


def pane(a, x, y, w, h, r=2.5):
    """A display pane (the Now Playing glass): the inside is (x, y, w, h)."""
    rbox(a, x - 1, y - 1, w + 2, h + 2, r, T.pane, T.pane_edge)


def button_face(a, x, y, w, h, pressed, on=False, r=None):
    """A rounded push button (EQ/PL, Shuffle/Repeat, ADD...)."""
    r = min(h / 2 - 0.01, 4.5) if r is None else r
    stops = T.btn_down if pressed else T.btn
    edge = T.btn_rim
    if on and not pressed:
        stops = [lerp(c, T.accent_hi, 0.35 if light_frame() else 0.25) for c in T.btn]
    rbox(a, x, y, w, h, r, stops, edge)
    if not pressed:
        H, W = a.shape[0], a.shape[1]
        paint(a, 0, 0, rr_mask(W, H, max(0, r - 1.5), x + 2, y + 1.2, w - 4, h * 0.42), WHITE, 0.35)


def label_on_button(a, x, y, w, h, s, pressed, on, led=True):
    o = 1 if pressed else 0
    ink = T.glyph_down if pressed else T.glyph
    tw = text_w(TINY, s)
    if led:
        lx = x + (w - tw - 4) // 2
        led_col = (60, 230, 60) if on else lerp(T.btn[2], BLACK, 0.25)
        if T.look in ("dark", "w11") and on:
            led_col = (120, 200, 255) if T.look == "w11" else (80, 240, 80)
        rect(a, lx + o, y + h // 2 - 1 + o, 2, 2, led_col)
        draw_text(a, TINY, s, lx + 4 + o, y + (h - 5) // 2 + o, ink)
    else:
        if on:
            ink = {"v7": (40, 48, 176), "blue": (18, 128, 24), "dark": (14, 116, 20), "w11": (130, 196, 255),
                   "x8": (18, 140, 24), "x9": (24, 130, 30), "x10": (40, 120, 220)}[T.look]
        draw_text(a, TINY, s, x + (w - tw) // 2 + o, y + (h - 5) // 2 + o, ink)


def groove(a, x, y, w, th, col=None):
    """A recessed horizontal groove, th tall."""
    W, H = a.shape[1], a.shape[0]
    r = th / 2
    paint(a, 0, 0, rr_mask(W, H, r, x, y + 1, w, th), T.track_hi, 0.8)        # light lip below
    paint(a, 0, 0, rr_mask(W, H, r, x, y, w, th), col or getattr(T, "groove", T.track))


def knob(a, x, y, w, h, pressed, shape=None):
    """A slider thumb: WMP 7's silver block, 8/9's green pill, 10's blue glass bead."""
    shape = shape or T.thumb_shape
    stops = T.thumb_down if pressed else T.thumb
    if shape == "square":
        rbox(a, x, y, w, h, 1.5, stops, T.thumb_rim)
        rect(a, x + 1, y + 1, w - 2, 1, WHITE)
        cx = x + w // 2
        for gx in (cx - 2, cx, cx + 2):
            rect(a, gx, y + 3, 1, h - 6, lerp(T.thumb_rim, stops[-1], 0.4))
    elif shape == "pill":
        rbox(a, x, y, w, h, min(w, h) / 2 - 0.01, stops, T.thumb_rim)
        H, W = a.shape[0], a.shape[1]
        paint(a, 0, 0, rr_mask(W, H, min(w, h) / 2 - 1.5, x + 1.5, y + 1, w - 3, h * 0.45), WHITE, 0.55)
    else:
        sphere(a, x + w / 2, y + h / 2, min(w, h), stops, T.thumb_rim, gloss=0.6)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters, bg):
    """The clutter bar as a column of WMP taskbar buttons (the chosen one lit)."""
    if T.look in NEW:
        return xclutter(lit_letters, bg)
    a = new(8, 43, bg)
    rbox(a, 0, 0, 8, 43, 2, [T.task_bg, T.task_bg])
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        stops = T.task_sel if on else T.task
        vfill(a, 1, y, 6, h, stops)
        rect(a, 1, y, 6, 1, lerp(stops[0], WHITE, 0.35))
        gy = y + (h - 5) // 2
        ink = getattr(T, "task_txt_sel", T.task_txt) if on else T.task_txt
        draw_text(a, TINY, letter, 2, gy, ink)
    return a


def main_titlebar(lit):
    if T.look in NEW:
        return xmain_titlebar(lit)
    a = bar_frame(275, 14, lit, left_edge=True, right_edge=True)
    if T.look == "w11":
        wmp10_tabs(a, 19, 2, 12, lit, T.tabs)
    else:
        title_text(a, T.main_title, 128, 3 if T.look != "v7" else 3, lit, getattr(T, "main_series", None))
    caption_button(a, 6, 3, "options", lit)
    caption_button(a, 244, 3, "minimize", lit)
    caption_button(a, 254, 3, "shade", lit)
    caption_button(a, 264, 3, "close", lit)
    return a


def make_titlebar(main):
    a = new(344, 87, flat_body())
    bar = main_titlebar(True)
    for kind, x in (("options", 0), ("minimize", 9), ("close", 18)):
        src = {"options": 6, "minimize": 244, "close": 264}[kind]
        a[0:9, x:x + 9] = bar[3:12, src:src + 9]
        a[9:18, x:x + 9] = bar_cell_pressed(kind, src)
    a[18:27, 0:9] = bar[3:12, 254:263]
    a[18:27, 9:18] = bar_cell_pressed("shade", 254)
    a[0:14, 27:302] = main_titlebar(True)
    a[15:29, 27:302] = main_titlebar(False)
    a[29:43, 27:302] = main_titlebar(True)
    a[42:56, 27:302] = main_titlebar(False)
    cbg = main_bg()[22:65, 10:18] if T.look in NEW else main[30, 9]
    unlit = clutter_bar("", cbg)
    lit = clutter_bar("OAIDV", cbg)
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = lit[y:y + h]
    return a


def bar_cell_pressed(kind, src):
    cell = bar_frame(275, 14, True, left_edge=True, right_edge=True)[3:12, src:src + 9].copy()
    caption_button(cell, 0, 0, kind, True, pressed=True)
    return cell


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116): the body, the Now Playing panes and the transport deck
# ------------------------------------------------------------------------------------------

DECK = (4, 84, 267, 29)            # the rounded transport deck along the bottom
CB = {"previous": (16, 23), "play": (39, 23), "pause": (62, 23), "stop": (85, 23), "next": (108, 22)}
CB_Y = 88
EJECT = (136, 89, 22, 16)
PLAY_C = (50.5, 97.0)


def main_bg():
    if T.look in NEW:
        return xmain_bg()
    a = new(275, 116)
    vfill(a, 0, 14, 275, 102, T.body)
    brushed(a, 0, 14, 275, 102, T.brushed)
    a[0:14] = main_titlebar(True)
    # outer frame: rim and inner highlight
    rect(a, 0, 0, 1, 116, T.rim)
    rect(a, 274, 0, 1, 116, T.rim)
    rect(a, 0, 115, 275, 1, T.rim)
    rect(a, 1, 14, 1, 101, T.hi)
    rect(a, 1, 14, 273, 1, T.hi if not light_frame() else lerp(T.body[0], WHITE, 0.5))
    rect(a, 273, 15, 1, 100, T.lo)
    rect(a, 1, 114, 273, 1, T.lo)
    # the taskbar recess round the clutter bar (WMP's left button column, in miniature)
    rbox(a, 7, 19, 14, 49, 3, [lerp(T.task_bg, BLACK, 0.15), T.task_bg], lerp(T.task_bg, BLACK, 0.4))
    # the transport deck
    x, y, w, h = DECK
    W, H = 275, 116
    paint(a, 0, 0, rr_mask(W, H, h / 2, x, y + 1, w, h), T.lo if light_frame() else BLACK, 0.5)
    rbox(a, x, y, w, h, h / 2, T.deck, T.deck_rim)
    paint(a, 0, 0, rr_mask(W, H, h / 2 - 2, x + 6, y + 1.5, w - 12, 2), T.deck_hi, 0.7)
    return a


def digit(a, n, x, y, col):
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + 1 + c, y + 1 + r, col)


def tri(a, pts, col, alpha=1.0):
    paint(a, 0, 0, poly_mask(a.shape[1], a.shape[0], pts), col, alpha)


def glyph(a, kind, cx, cy, col, s=1.0):
    W, H = a.shape[1], a.shape[0]
    if kind == "previous":
        tri(a, [(cx - 3.5 * s, cy), (cx + 0.5 * s, cy - 4 * s), (cx + 0.5 * s, cy + 4 * s)], col)
        tri(a, [(cx + 0.5 * s, cy), (cx + 4.5 * s, cy - 4 * s), (cx + 4.5 * s, cy + 4 * s)], col)
        paint(a, 0, 0, rr_mask(W, H, 0.3, cx - 5.2 * s, cy - 4 * s, 1.5 * s, 8 * s), col)
    elif kind == "next":
        tri(a, [(cx + 3.5 * s, cy), (cx - 0.5 * s, cy - 4 * s), (cx - 0.5 * s, cy + 4 * s)], col)
        tri(a, [(cx - 0.5 * s, cy), (cx - 4.5 * s, cy - 4 * s), (cx - 4.5 * s, cy + 4 * s)], col)
        paint(a, 0, 0, rr_mask(W, H, 0.3, cx + 3.7 * s, cy - 4 * s, 1.5 * s, 8 * s), col)
    elif kind == "play":
        tri(a, [(cx - 2.6 * s, cy - 4.6 * s), (cx + 4.6 * s, cy), (cx - 2.6 * s, cy + 4.6 * s)], col)
    elif kind == "pause":
        paint(a, 0, 0, rr_mask(W, H, 0.5, cx - 3.5 * s, cy - 4 * s, 2.6 * s, 8 * s), col)
        paint(a, 0, 0, rr_mask(W, H, 0.5, cx + 0.9 * s, cy - 4 * s, 2.6 * s, 8 * s), col)
    elif kind == "stop":
        paint(a, 0, 0, rr_mask(W, H, 0.8, cx - 3.5 * s, cy - 3.5 * s, 7 * s, 7 * s), col)
    elif kind == "eject":
        tri(a, [(cx - 4.5 * s, cy + 1 * s), (cx, cy - 4 * s), (cx + 4.5 * s, cy + 1 * s)], col)
        paint(a, 0, 0, rr_mask(W, H, 0.4, cx - 4.5 * s, cy + 2.3 * s, 9 * s, 1.8 * s), col)


def centres():
    c = {k: (x + w / 2, CB_Y + 9) for k, (x, w) in CB.items()}
    ex, ey, ew, eh = EJECT
    c["eject"] = (ex + ew / 2, ey + eh / 2)
    c["play"] = PLAY_C
    return c


def transport(a, pressed=None):
    """The transport on the deck (whole-window canvas a): WMP's big round play button in its
    recess, the smaller round buttons in a shared groove, eject apart; one button pressed."""
    if T.look in NEW:
        return xtransport(a, pressed)
    W, H = a.shape[1], a.shape[0]
    C = centres()
    # the groove the small buttons sit in (prev .. next), and eject's own
    gy = C["previous"][1]
    paint(a, 0, 0, rr_mask(W, H, 8.5, 18, gy - 8.5 + 1, 112, 17), T.deck_hi, 0.5)
    paint(a, 0, 0, rr_mask(W, H, 8.5, 18, gy - 8.5, 112, 17), lerp(T.deck[-2], BLACK, 0.35))
    paint(a, 0, 0, rr_mask(W, H, 7.5, 19, gy - 7.5, 110, 15), lerp(T.deck[1], BLACK, 0.18))
    # the play button's well
    cx, cy = C["play"]
    paint(a, 0, 0, ellipse_mask(W, H, cx - 11, cy - 11 + 1, 22, 22), T.deck_hi, 0.6)
    paint(a, 0, 0, ellipse_mask(W, H, cx - 11, cy - 11, 22, 22), lerp(T.deck[-2], BLACK, 0.45))
    for k, (cx, cy) in C.items():
        if k == "play":
            d, stops, ink, s = 18, T.play, T.play_glyph, 1.0
        else:
            d, stops, ink, s = 13, T.btn, T.glyph, 0.68
        if k == pressed:
            stops = T.btn_down if k != "play" or T.look != "w11" else [lerp(c, BLACK, 0.3) for c in T.play]
            ink = T.glyph_down if k != "play" else lerp(T.play_glyph, T.glyph_down, 0.5)
        gl = 0.0 if k == pressed else (0.2 if (T.look == "w11" and k != "play") else 0.5)
        sphere(a, cx, cy, d, stops, T.btn_rim, gloss=gl)
        o = 0.5 if k == pressed else 0
        gx = cx + (0.8 if k == "play" else 0) + o
        glyph(a, k, gx, cy + o, ink, s)


def make_main():
    if T.look in NEW:
        return xmake_main()
    a = main_bg()
    bg = a[30, 9]
    a[22:65, 10:18] = clutter_bar("", bg)
    # left pane: indicator, time, analyzer
    pane(a, 21, 20, 84, 42)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, T.ink)
    # right pane: the title, then kbps/kHz/mono/stereo, a hairline between
    pane(a, 109, 21, 159, 33)
    rect(a, 110, 38, 157, 1, lerp(T.pane, T.pane_edge, 0.6))
    draw_text(a, TINY, "KBPS", 129, 44, T.pane_label)
    draw_text(a, TINY, "KHZ", 169, 44, T.pane_label)
    # volume (a wedge) and balance seats (the sheets' own frames cover them)
    a[57:70, 107:175] = volume_frame(a[57:70, 107:175], 0)
    a[57:70, 177:215] = balance_frame(a[57:70, 177:215], 0)
    # seek bar seat, with WMP's rewind / fast-forward end caps outside it
    groove(a, 17, 75, 246, 4)
    for x0, d in ((9, -1), (266, 1)):
        rbox(a, x0 - 1, 73, 9, 8, 3.5, T.btn, T.btn_rim)
        cx = x0 + 3.5
        tri(a, [(cx - 1.8 * d, 75), (cx + 0.2 * d, 77), (cx - 1.8 * d, 79)], T.glyph)
        tri(a, [(cx + 0.2 * d, 75), (cx + 2.2 * d, 77), (cx + 0.2 * d, 79)], T.glyph)
    transport(a)
    # the logo, once, in the About spot at the deck's right end
    draw_logo(a, 245, 87, 23)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons, shufrep, monoster, playpaus, numbers, text
# ------------------------------------------------------------------------------------------


def make_cbuttons(main):
    a = new(136, 36, flat_body())
    normal = main
    sheet_x = {"previous": 0, "play": 23, "pause": 46, "stop": 69, "next": 92}
    for k, (mx, w) in CB.items():
        x = sheet_x[k]
        a[0:18, x:x + w] = normal[CB_Y:CB_Y + 18, mx:mx + w]
        p = main_bg()
        transport(p, k)
        a[18:36, x:x + w] = p[CB_Y:CB_Y + 18, mx:mx + w]
    ex, ey, ew, eh = EJECT
    a[0:16, 114:136] = normal[ey:ey + eh, ex:ex + ew]
    p = main_bg()
    transport(p, "eject")
    a[16:32, 114:136] = p[ey:ey + eh, ex:ex + ew]
    return a


def toggle_cell(bg, w, h, label, on, pressed, led=True, r=None, ends="both"):
    """A push button cell on bg; ends: which ends are rounded (the shuffle/repeat pair joins)."""
    a = bg.copy()
    if ends == "both":
        button_face(a, 0, 0, w, h, pressed, on, r)
    else:
        # draw wider and crop so that one end stays square
        ext = 8
        big = np.zeros((h, w + ext, 3), np.int32)
        if ends == "left":
            big[:, :w] = a
            button_face(big, 0, 0, w + ext, h, pressed, on, r)
            a = big[:, :w].copy()
            rect(a, w - 1, 1, 1, h - 2, T.btn_rim)
        else:
            big[:, ext:] = a
            button_face(big, 0, 0, w + ext, h, pressed, on, r)
            a = big[:, ext:].copy()
            rect(a, 0, 1, 1, h - 2, T.btn_rim)
    label_on_button(a, 0, 0, w, h, label, pressed, on, led)
    return a


def make_shufrep(main):
    a = new(92, 85, flat_body())
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = toggle_cell(main[89:104, 210:238], 28, 15, "REPEAT", on, pressed, led=False,
                                        ends="right")
        a[y:y + 15, 28:75] = toggle_cell(main[89:104, 164:211], 47, 15, "SHUFFLE", on, pressed, ends="left")
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        src = main[58:70, 219 + (x % 46):219 + (x % 46) + 23]
        a[61:73, x:x + 23] = toggle_cell(src, 23, 12, label, False, pressed)
        a[73:85, x:x + 23] = toggle_cell(src, 23, 12, label, True, pressed)
    return a


def make_monoster():
    a = new(56, 24, T.pane)
    for y, on in ((0, True), (12, False)):
        col = T.ink if on else T.ink_dim
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T.pane)
    col = T.ink
    tri(a, [(2, 1), (8, 4.5), (2, 8)], getattr(T, "play_ind", col))
    rect(a, 9 + 2, 1, 2, 7, col)
    rect(a, 9 + 5, 1, 2, 7, col)
    rect(a, 18 + 2, 2, 5, 5, col)
    rect(a, 36, 0, 3, 9, T.pane)
    rect(a, 39 + 1, 3, 1, 3, col)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T.pane)
    for n in range(10):
        digit(a, n, 9 * n, 0, T.ink)
    if ex:
        rect(a, 99 + 2, 6, 5, 2, T.ink)
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]

TEXT_FONT = dict(FONT5, M=G("#..#", "####", "####", "#..#", "#..#"), W=G("#..#", "#..#", "####", "####", "#..#"))


def make_text():
    a = new(155, 18, T.pane)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, TEXT_FONT, key, col * 5, row * 6, T.ink)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def make_posbar(main):
    a = new(307, 10, flat_body())
    a[0:10, 0:248] = main[72:82, 16:264]
    for x0, sel in ((248, False), (278, True)):
        t = main[72:82, 16 + 100:16 + 129].copy()
        if T.thumb_shape == "square":
            knob(t, 9, 0, 11, 10, sel)
        elif T.thumb_shape == "pill":
            knob(t, 7, 1, 15, 8, sel)
        else:
            knob(t, 9, 0, 10, 10, sel)
        a[0:10, x0:x0 + 29] = t
    return a


def volume_frame(seat, level):
    """68 x 13: WMP's volume wedge (thin at the left, tall at the right), filled to level 0..1."""
    t = seat.copy()
    W, H = t.shape[1], t.shape[0]
    x0, x1, yb = 3, 65, 10
    pts = [(x0, yb), (x1, yb), (x1, yb - 7), (x0, yb - 1.2)]
    paint(t, 0, 0, poly_mask(W, H, [(x, y + 1) for x, y in pts]), T.track_hi, 0.8)
    paint(t, 0, 0, poly_mask(W, H, pts), getattr(T, "groove", T.track))
    if level > 0:
        m = poly_mask(W, H, [(x0 + 1, yb - 0.6), (x1 - 1, yb - 0.6), (x1 - 1, yb - 6.2), (x0 + 1, yb - 1.4)])
        m[:, int(x0 + 1 + level * (x1 - x0 - 2)):] = 0
        paint(t, 0, 0, m, gcanvas(H, W, 3, 8, T.fill))
    return t


def balance_frame(seat, reach):
    """38 x 13: a flat groove with a centre notch, lit outwards from the centre by reach 0..1."""
    t = seat.copy()
    W, H = t.shape[1], t.shape[0]
    groove(t, 2, 5, 34, 4)
    if reach > 0:
        half = 1 + reach * 15
        m = rr_mask(W, H, 1.5, 19 - half, 5.5, 2 * half, 3)
        paint(t, 0, 0, m, gcanvas(H, W, 5, 4, T.fill))
    rect(t, 18, 2, 2, 2, T.body_label)
    return t


def slider_thumbs(a, seat):
    for x, sel in ((0, True), (15, False)):
        t = seat[1:12, 20:34].copy()
        if T.thumb_shape == "square":
            knob(t, 2, 0, 10, 11, sel)
        elif T.thumb_shape == "pill":
            knob(t, 3, 0, 8, 11, sel)
        else:
            knob(t, 2, 0, 10, 10, sel)
        a[422:433, x:x + 14] = t


def make_volume(main):
    a = new(68, 433, flat_body())
    seat = main_bg()[57:70, 107:175]
    for i in range(28):
        a[i * 15:i * 15 + 13, 0:68] = volume_frame(seat, (i + 1) / 28)
        a[i * 15 + 13:i * 15 + 15, 0:68] = seat[-2:]
    slider_thumbs(a, main[57:72, 107:175])
    return a


def make_balance(main):
    a = new(68, 433, flat_body())
    seat = main_bg()[57:70, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 13, 9:47] = balance_frame(seat, i / 27)
        a[y:y + 13, 0:9] = seat[:, :1]
        a[y:y + 13, 47:68] = seat[:, -1:]
        a[y + 13:y + 15, :] = seat[-1, 0]
    slider_thumbs(a, main[57:72, 107:175])
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    if T.look in NEW:
        return xeq_titlebar(lit)
    a = bar_frame(275, 14, lit, left_edge=True, right_edge=True)
    if T.look == "w11":
        wmp10_tabs(a, 6, 2, 12, lit, [T.eq_title])
    else:
        title_text(a, T.eq_title, 137, 3, lit)
    caption_button(a, 264, 3, "close", lit)
    return a


def eq_frame_bg():
    a = new(275, 116)
    vfill(a, 0, 14, 275, 102, T.body)
    brushed(a, 0, 14, 275, 102, T.brushed)
    rect(a, 0, 0, 1, 116, T.rim)
    rect(a, 274, 0, 1, 116, T.rim)
    rect(a, 0, 115, 275, 1, T.rim)
    rect(a, 1, 14, 1, 101, T.hi)
    rect(a, 1, 14, 273, 1, T.hi if not light_frame() else lerp(T.body[0], WHITE, 0.5))
    rect(a, 273, 15, 1, 100, T.lo)
    rect(a, 1, 114, 273, 1, T.lo)
    if T.look in NEW:
        # the enhancement pane's header band (WMP's info-bar colour) behind ON/AUTO/graph/PRESETS
        rbox(a, 4, 16, 267, 17, 3, [lerp(T.info, WHITE, 0.08), T.info], lerp(T.info, BLACK, 0.3))
    # the slider bay: a pane like WMP's Now Playing enhancements panel
    rbox(a, 15, 35, 246, 77, 4, [lerp(T.pane, T.pane_edge, 0.12), T.pane], T.pane_edge)
    return a


def eq_slider_frame(bg, n):
    """14x63: a slim groove lit from the bottom up to the value (n of 0..27)."""
    a = bg.copy()
    W, H = a.shape[1], a.shape[0]
    v = n / 27
    paint(a, 0, 0, rr_mask(W, H, 1.5, 5, 2, 4, 59), lerp(T.pane_edge, BLACK, 0.3))
    paint(a, 0, 0, rr_mask(W, H, 1, 6, 3, 2, 57), (24, 26, 34))
    top = round((1 - v) * 51) + 5
    m = rr_mask(W, H, 1, 6, 3, 2, 57)
    m[:top, :] = 0
    paint(a, 0, 0, m, gcanvas(H, W, 3, 57, T.vis_bars))
    for yy in (8, 31, 54):
        rect(a, 1, yy, 2, 1, T.pane_label)
        rect(a, 11, yy, 2, 1, T.pane_label)
    return a


def eq_thumb(bg, pressed):
    a = bg.copy()
    if T.thumb_shape == "round":
        knob(a, 0, 0, 11, 11, pressed)
    elif T.thumb_shape == "pill":
        knob(a, 0, 2, 11, 7, pressed)
    else:
        knob(a, 0, 1, 11, 9, pressed)
    return a


def make_eqmain():
    a = new(275, 315, flat_body())
    base = eq_frame_bg()
    a[0:116] = base
    a[0:14] = eq_titlebar(True)
    # graph seat
    pane(a, 86, 17, 113, 19)
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, T.pane_label)
    seat = a[38:101, 21:35].copy()
    for x in [21] + [78 + 18 * i for i in range(10)]:
        a[38:101, x:x + 14] = eq_slider_frame(a[38:101, x:x + 14], 14)
    text_center(a, TINY, "PREAMP", 28, 104, T.pane_label)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 104, T.pane_label)
    rect(a, 40, 39, 1, 60, lerp(T.pane, T.pane_edge, 0.6))
    for x, w, lbl in ((14, 26, "ON"), (40, 32, "AUTO")):
        a[18:30, x:x + w] = toggle_cell(base[18:30, x:x + w], w, 12, lbl, False, False)
    a[18:30, 217:261] = toggle_cell(base[18:30, 217:261], 44, 12, "PRESETS", False, False, led=False)

    # under the window
    a[125:134, 0:9] = eq_close_pressed()
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        src = base[18:30, 14:40] if label == "ON" else base[18:30, 40:72]
        a[119:131, x:x + w] = toggle_cell(src, w, 12, label, on, pressed)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    a[164:175, 0:11] = eq_thumb(seat[2:13, 1:12], False)
    a[176:187, 0:11] = eq_thumb(seat[2:13, 1:12], True)
    for n in range(28):
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = eq_slider_frame(seat, n)
    for y, pressed in ((164, False), (176, True)):
        a[y:y + 12, 224:268] = toggle_cell(base[18:30, 217:261], 44, 12, "PRESETS", False, pressed, led=False)
    # graph
    rect(a, 0, 294, 113, 19, T.pane)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, T.vis_dots)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, lerp(T.pane, T.pane_label, 0.4))
    for r in range(19):
        px(a, 115, 294 + r, ramp(T.vis_bars[:3], r / 18))
    for x in range(113):
        px(a, x, 314, lerp(T.pane, T.pane_label, 0.8) if x % 3 != 2 else T.pane)
    return a


def eq_close_pressed():
    bar = bar_frame(275, 14, True, left_edge=True, right_edge=True)
    cell = bar[3:12, 264:273].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    return cell


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------


def bar20(w, lit, left_edge=False, right_edge=False):
    a = bar_frame(w, 20, lit, left_edge, right_edge)
    rect(a, 0, 19, w, 1, flat_body())
    return a


def side_tile(w, h, left):
    t = new(w, h, flat_body())
    if left:
        rect(t, 0, 0, 1, h, T.rim)
        rect(t, 1, 0, 1, h, T.hi)
        rect(t, w - 1, 0, 1, h, T.pane_edge)
    else:
        rect(t, w - 1, 0, 1, h, T.rim)
        rect(t, w - 2, 0, 1, h, T.lo)
        rect(t, 0, 0, 1, h, T.pane_edge)
    return t


def scroll_groove_col():
    return getattr(T, "scroll", None) or lerp(T.pane, T.pane_edge, 0.25)


def scroll_handle(pressed):
    t = new(8, 18, scroll_groove_col())
    if T.thumb_shape == "square":
        rbox(t, 0, 0, 8, 18, 1.5, T.thumb_down if pressed else T.thumb, T.thumb_rim)
        for gy in (6, 8, 10):
            rect(t, 2, gy, 4, 1, T.thumb_rim)
    else:
        rbox(t, 0, 0, 8, 18, 3.99, T.thumb_down if pressed else T.thumb, T.thumb_rim)
        paint(t, 0, 0, rr_mask(8, 18, 2.5, 1.5, 1, 3, 16), WHITE, 0.45)
    return t


def mini_transport_icon(a, kind, x, y, col):
    cx, cy = x + 5, y + 5
    if kind == "previous":
        rect(a, cx - 3, cy - 2, 1, 5, col)
        tri(a, [(cx - 2, cy + 0.5), (cx + 0.5, cy - 2.5), (cx + 0.5, cy + 3.5)], col)
        tri(a, [(cx + 0.5, cy + 0.5), (cx + 3, cy - 2.5), (cx + 3, cy + 3.5)], col)
    elif kind == "play":
        tri(a, [(cx - 2, cy - 3), (cx + 3, cy + 0.5), (cx - 2, cy + 4)], col)
    elif kind == "pause":
        rect(a, cx - 2, cy - 2, 2, 5, col)
        rect(a, cx + 1, cy - 2, 2, 5, col)
    elif kind == "stop":
        rect(a, cx - 2, cy - 2, 5, 5, col)
    elif kind == "next":
        tri(a, [(cx + 2, cy + 0.5), (cx - 0.5, cy - 2.5), (cx - 0.5, cy + 3.5)], col)
        tri(a, [(cx - 0.5, cy + 0.5), (cx - 3, cy - 2.5), (cx - 3, cy + 3.5)], col)
        rect(a, cx + 2, cy - 2, 1, 5, col)
    elif kind == "eject":
        tri(a, [(cx - 2.5, cy + 0.5), (cx + 0.5, cy - 3), (cx + 3.5, cy + 0.5)], col)
        rect(a, cx - 2, cy + 1, 5, 1, col)


def combo(t, x, y, w, h, text, lit):
    """WMP's playlist drop-down: a list icon, the playlist's name and the arrow button."""
    W, H = t.shape[1], t.shape[0]
    stops = T.combo if lit else [lerp(c, flat_body(), 0.35) for c in T.combo]
    rbox(t, x, y, w, h, 2, stops, T.combo_edge)
    ink = T.combo_txt if lit else lerp(T.combo_txt, stops[0], 0.45)
    # list icon
    for r in (0, 2, 4):
        rect(t, x + 3, y + 3 + r, 1, 1, ink)
        rect(t, x + 5, y + 3 + r, 4, 1, ink)
    draw_text(t, UI, text, x + 12, y + 2, ink)
    bx = x + w - 11
    rbox(t, bx, y + 1, 10, h - 2, 1.5, T.btn if lit else [lerp(c, flat_body(), 0.4) for c in T.btn], T.btn_rim)
    tri(t, [(bx + 2.5, y + 5), (bx + 7.5, y + 5), (bx + 5, y + 8)], T.glyph)


def title_piece_pl(lit):
    if T.look in NEW:
        return xtitle_piece_pl(lit)
    t = bar20(100, lit)
    if T.look == "w11":
        tw = text_w(UI, T.pl_title) + 10
        wmp10_tabs(t, 50 - tw // 2, 4, 15, lit, [T.pl_title], right_limit=100)
    else:
        combo(t, 2, 4, 96, 13, T.pl_title, lit)
    return t


def make_pledit():
    a = new(280, 186, flat_body())
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar20(25, lit)
        a[y:y + 20, 0:25] = bar20(25, lit, left_edge=True)
        a[y:y + 20, 26:126] = title_piece_pl(lit)
        t = bar20(25, lit, right_edge=True)
        caption_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    a[42:71, 0:12] = side_tile(12, 29, True)
    t = side_tile(20, 29, False)
    rect(t, 5, 0, 8, 29, scroll_groove_col())
    rect(t, 4, 0, 1, 29, T.pane_edge)
    rect(t, 13, 0, 1, 29, T.pane_edge)
    rect(t, 14, 0, 4, 29, flat_body())
    a[42:71, 31:51] = t
    bar = bar20(25, True, right_edge=True)
    cell = bar[3:12, 14:23].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = cell
    a[53:71, 52:60] = scroll_handle(False)
    a[53:71, 61:69] = scroll_handle(True)

    def bottom_base(w):
        t = new(w, 38, flat_body())
        brushed(t, 0, 0, w, 38, T.brushed)
        rect(t, 0, 0, w, 1, T.pane_edge)
        rect(t, 0, 1, w, 1, T.hi if not light_frame() else lerp(flat_body(), WHITE, 0.5))
        rect(t, 0, 36, w, 1, T.lo)
        rect(t, 0, 37, w, 1, T.rim)
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, T.rim)
    rect(t, 1, 1, 1, 36, T.hi)
    rect(t, 0, 0, 12, 1, flat_body())
    rect(t, 1, 0, 1, 1, T.hi)
    rect(t, 11, 0, 1, 1, T.pane_edge)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        t[8:26, bx:bx + 22] = toggle_cell(t[8:26, bx:bx + 22], 22, 18, lbl, False, False, led=False, r=4)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, T.rim)
    rect(t, 148, 1, 1, 36, T.lo)
    rect(t, 130, 0, 18, 1, flat_body())
    rect(t, 130, 0, 1, 1, T.pane_edge)
    pane(t, 6, 9, 56, 8, r=1.5)
    # the mini transport on a small deck
    rbox(t, 1, 21, 63, 12, 6, T.deck, T.deck_rim)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        mini_transport_icon(t, kind, bx, 22, T.glyph if light_frame() else T.task_txt)
    pane(t, 65, 22, 33, 8, r=1.5)
    rect(t, 84, 22 + 2, 1, 1, T.ink)
    rect(t, 84, 22 + 5, 1, 1, T.ink)
    t[8:26, 106:128] = toggle_cell(t[8:26, 106:128], 22, 18, "LIST", False, False, led=False, r=4)
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 32 - 3 * j
            px(t, gx, gy, T.body_label)
            px(t, gx + 1, gy + 1, T.hi if light_frame() else BLACK)
    a[72:110, 126:276] = t

    a[0:38, 179:204] = bottom_base(25)
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_bottom(w, grip, left_edge):
    t = new(w, 14, flat_body())
    brushed(t, 0, 0, w, 14, T.brushed)
    rect(t, 0, 12, w, 1, T.lo)
    rect(t, 0, 13, w, 1, T.rim)
    rect(t, 0, 0, w, 1, T.pane_edge)
    if left_edge:
        rect(t, 0, 0, 1, 14, T.rim)
        rect(t, 1, 1, 1, 12, T.hi)
        rect(t, 0, 0, 11, 1, flat_body())
        rect(t, 10, 0, 1, 1, T.pane_edge)
    else:
        rect(t, w - 1, 0, 1, 14, T.rim)
        rect(t, w - 2, 1, 1, 12, T.lo)
        rect(t, w - 8, 0, 7, 1, flat_body())
        rect(t, w - 9, 0, 1, 1, T.pane_edge)
    if grip:
        for k in range(3):
            for j in range(k + 1):
                gx, gy = w - 5 - 3 * k + 3 * j, 9 - 3 * j
                px(t, gx, gy, T.body_label)
                px(t, gx + 1, gy + 1, T.hi if light_frame() else BLACK)
    return t


def make_gen():
    a = new(194, 109, flat_body())
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, t):
            a[y:y + 20, px0:px0 + 25] = t

        piece(0, bar20(25, lit, left_edge=True))
        for px0 in (26, 52, 78, 104):
            piece(px0, bar20(25, lit))
        t = bar20(25, lit, right_edge=True)
        caption_button(t, 14, 3, "close", lit)
        piece(130, t)

    a[42:56, 0:125] = gen_bottom(125, False, True)
    a[57:71, 0:125] = gen_bottom(125, True, False)
    t = new(25, 14, flat_body())
    brushed(t, 0, 0, 25, 14, T.brushed)
    rect(t, 0, 0, 25, 1, T.pane_edge)
    rect(t, 0, 12, 25, 1, T.lo)
    rect(t, 0, 13, 25, 1, T.rim)
    a[72:86, 127:152] = t
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = side_tile(w, h, left)
    bar = bar20(25, True, right_edge=True)
    cell = bar[3:12, 14:23].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = cell

    # letters: each row starts at x 1, each letter in its own cell, 1px separators of x 0's colour;
    # a cell's background is the title piece's own rows 4..10, so the letters sit on the bar
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        centre = a[(0 if lit else 21) + 4:(0 if lit else 21) + 11, 60].copy()
        col = T.title_lit if lit else T.title_dim
        shadow = T.title_shadow if (T.look == "blue" and lit) else None
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            for r in range(7):
                a[y + r, x:x + w] = centre[r]
            draw_text(a, FONT5, c, x, y + 1, col, shadow=shadow)
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp, text files
# ------------------------------------------------------------------------------------------


def genex_colours():
    p = T.pledit
    item_bg, item_fg = rgb(p["NormalBG"]), rgb(p["Normal"])
    sel = rgb(p["SelectedBG"])
    win = flat_body()
    win_txt = T.body_label if light_frame() else T.task_txt
    hdr = T.task[1]
    return [item_bg, item_fg, win, T.glyph, win_txt, T.pane_edge, sel, hdr, T.task_txt,
            lerp(hdr, WHITE, 0.3), lerp(hdr, BLACK, 0.5), T.task_sel[1], win,
            T.btn[2], T.btn_rim, T.btn_down[0], T.accent, scroll_groove_col()]


def make_genex():
    a = new(256, 64, flat_body())
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    a[1:16, 0:47] = toggle_cell(new(47, 15, flat_body()), 47, 15, "", False, False, led=False)
    a[16:31, 0:47] = toggle_cell(new(47, 15, flat_body()), 47, 15, "", False, True, led=False)
    return a


def viscolor():
    cols = [(T.pane, "background"), (T.vis_dots, "dots")]
    for i in range(16):
        cols.append((ramp(T.vis_bars, i / 15), f"spectrum {i + 1}" + (" (top)" if i == 0 else "")))
    for i, c in enumerate(T.vis_osc):
        cols.append((c, f"oscilloscope {i + 1}"))
    cols.append((T.vis_peak, "peaks"))
    return cols


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    p = T.pledit
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={p['Normal']}\nCurrent={p['Current']}\nNormalBG={p['NormalBG']}\n"
                f"SelectedBG={p['SelectedBG']}\nMbBG={p['NormalBG']}\nMbFG={p['Normal']}\nFont=Tahoma\n")
    name = T.label
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n", encoding="utf-8") as f:
        if T.look in NEW:
            spot = "the titlebar's menu button" if T.look == "x10" else "the About spot"
            f.write(
                f"{name} - a skin in the style of {T.era}.\n"
                "Windows logo (c) Microsoft Corporation.\n\n"
                "A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py) from\n"
                "gradients, shapes and hand-made pixel fonts, after screenshots of the real player; the\n"
                f"Windows flag in {spot} is the real logo.\n"
            )
            return
        f.write(
            f"{name} — a skin in the style of {T.era}.\n"
            "Windows Media Player logo © Microsoft Corporation.\n\n"
            "A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py) from\n"
            "gradients, shapes and hand-made pixel fonts; the logo in the About spot is redrawn from\n"
            "shapes too.\n"
        )


# ------------------------------------------------------------------------------------------
# Accurate looks: WMP 8 (x8), WMP 9 Series (x9) and WMP 10 (x10), after screenshots
#
# How the real players' parts sit on Winamp's fixed layout:
# - titlebar: 8's silver bar with the round blue menu button (options), 9's silver-white frame
#   with its "Now Playing" drop-down by the window buttons, 10's task tabs (the Windows flag,
#   10's window icon, as the options button);
# - the clutter bar: the left taskbar in miniature (8, 9), or a column of 10's info-bar buttons;
# - one black display: the status line on top (play indicator, time, the song title in the
#   status text's colour: text.bmp's ink), a separator, the visualisation and stream info below,
#   and the info bar ("Ambience: Random") as its own strip under the visualisation;
# - the green seek bar and volume, the round glass transport (play the big one in its well,
#   previous/next as pills), 8's silver foot, 10's slanted status panel round shuffle/repeat;
# - the Windows flag once: the About spot (8, 9) or the titlebar's menu button (10).
# ------------------------------------------------------------------------------------------

_flag_cache = {}


def flag(h):
    """The 2002-2012 Windows flag (source/logo-windows-flag), h px tall: (rgb, alpha) arrays."""
    if h not in _flag_cache:
        svg = os.path.join(HERE, "source", "logo-windows-flag", "flag-multicolored.svg")
        png = os.path.join(OUT_ROOT, "scratch", "flag-600.png")
        if not os.path.exists(png):
            subprocess.run(["/usr/bin/rsvg-convert", "-h", "600", svg, "-o", png], check=True)
        im = Image.open(png).convert("RGBA")
        w = max(1, round(h * im.width / im.height))
        arr = np.asarray(im.resize((w, h), Image.LANCZOS), dtype=np.float32)
        _flag_cache[h] = (arr[..., :3], np.clip(arr[..., 3] / 255.0, 0, 1))
    return _flag_cache[h]


def draw_flag(a, x, y, h, alpha=1.0):
    col, al = flag(h)
    paint(a, x, y, al, col, alpha)


def xbar(w, h, lit, left_edge=False, right_edge=False):
    """A titlebar strip for the accurate looks (8: periwinkle with the silver bar inset)."""
    a = new(w, h)
    st = frame_stops(lit)
    vfill(a, 0, 0, w, h, st)
    rect(a, 0, 0, w, 1, T.rim)
    rect(a, 0, 1, w, 1, lerp(st[0], WHITE, 0.6))
    if left_edge:
        rect(a, 0, 0, 1, h, T.rim)
        rect(a, 1, 1, 1, h - 1, lerp(st[0], WHITE, 0.5))
    if right_edge:
        rect(a, w - 1, 0, 1, h, T.rim)
        rect(a, w - 2, 1, 1, h - 1, T.lo)
    if T.look == "x8":
        y0, bh = (2, 11) if h == 14 else (3, 14)
        x0 = 3 if left_edge else -12
        x1 = w - 3 if right_edge else w + 12
        stops = T.silver if lit else [lerp(c, (200, 200, 212), 0.55) for c in T.silver]
        rbox(a, x0, y0, x1 - x0, bh, bh / 2 - 0.01, stops, T.silver_edge if lit else (136, 138, 168))
    elif T.look == "x10" and h == 14:
        rect(a, 0, h - 1, w, 1, (150, 180, 226) if lit else (176, 188, 210))
    return a


def chevrons(a, x, y, ink):
    W, H = a.shape[1], a.shape[0]
    paint(a, 0, 0, line_mask(W, H, [(x + 2.3, y + 4.0), (x + 4.5, y + 1.9), (x + 6.7, y + 4.0)], 1.1), ink)
    paint(a, 0, 0, line_mask(W, H, [(x + 2.3, y + 5.0), (x + 4.5, y + 7.1), (x + 6.7, y + 5.0)], 1.1), ink)


def xcaption(a, x, y, kind, lit, pressed):
    """9x9 titlebar buttons of the accurate looks."""
    W, H = a.shape[1], a.shape[0]
    st = T.caption
    if kind == "options":
        if st == "x8":
            # 8's round blue button (it shows the menu bar) with white chevrons
            stops = ([(150, 186, 255), (40, 88, 220), (18, 46, 170)] if lit else
                     [(196, 204, 230), (140, 150, 196), (120, 128, 176)])
            if pressed:
                stops = [(20, 50, 160), (40, 80, 200), (90, 130, 240)]
            sphere(a, x + 4.5, y + 4.5, 9, stops, (10, 26, 100) if lit else (100, 106, 150), gloss=0.0 if pressed else 0.45)
            chevrons(a, x, y, WHITE)
        elif st == "x9":
            stops = T.btn_down if pressed else ([(255, 255, 255), (236, 240, 248), (200, 208, 226)] if lit else
                                                [(246, 246, 250), (230, 232, 238), (214, 216, 226)])
            sphere(a, x + 4.5, y + 4.5, 9, stops, (110, 124, 170) if lit else (160, 166, 186), gloss=0.0)
            chevrons(a, x, y, T.title_lit if lit else T.title_dim)
        else:
            # 10's window icon, the Windows flag (it opens the window menu, as options does)
            if pressed:
                rbox(a, x - 0, y, 9, 9, 2, [(200, 220, 248), (150, 184, 236)], (90, 130, 196))
            draw_flag(a, x + (1 if pressed else 0), y + 1, 8, 1.0 if lit else 0.55)
        return
    if st == "x8":
        stops = T.btn_down if pressed else ([(255, 255, 255), (228, 230, 242), (186, 188, 210)] if lit else
                                            [(238, 238, 244), (216, 216, 226), (198, 198, 212)])
        sphere(a, x + 4.5, y + 4.5, 9, stops, (90, 94, 132) if lit else (150, 152, 178), gloss=0.0 if pressed else 0.4)
        ink = (34, 40, 96) if lit else (128, 130, 156)
    else:
        if pressed:
            rbox(a, x, y, 9, 9, 2, [(255, 255, 255), (206, 220, 242)], (110, 136, 190))
        ink = T.title_lit if lit else T.title_dim
    if kind == "minimize":
        rect(a, x + 2, y + 6, 5, 2, ink)
    elif kind == "shade":
        if st == "x8":
            rect(a, x + 2, y + 2, 5, 2, ink)
            rect(a, x + 2, y + 6, 5, 1, lerp(ink, WHITE, 0.4))
        else:
            rect(a, x + 2, y + 2, 5, 2, ink)
            rect(a, x + 2, y + 2, 1, 5, ink)
            rect(a, x + 6, y + 2, 1, 5, ink)
            rect(a, x + 2, y + 6, 5, 1, ink)
    elif kind == "close":
        paint(a, 0, 0, line_mask(W, H, [(x + 2.2, y + 2.2), (x + 6.8, y + 6.8)], 1.5), ink)
        paint(a, 0, 0, line_mask(W, H, [(x + 6.8, y + 2.2), (x + 2.2, y + 6.8)], 1.5), ink)


def down_tri(a, cx, cy, col, s=1.0):
    tri(a, [(cx - 2.5 * s, cy - 1.2 * s), (cx + 2.5 * s, cy - 1.2 * s), (cx, cy + 1.6 * s)], col)


def x10_tab(a, x, y, w, h, label, lit, arrow=False):
    """WMP 10's raised, lighter active tab (its foot runs off the strip's bottom)."""
    W, H = a.shape[1], a.shape[0]
    stops = T.task_sel if lit else [lerp(c, (196, 204, 218), 0.6) for c in T.task_sel]
    rbox(a, x, y, w, h + 4, 3, stops, (70, 110, 180) if lit else (150, 160, 182))
    paint(a, 0, 0, rr_mask(W, H, 2.5, x + 1.5, y + 1, w - 3, h * 0.45), WHITE, 0.30 if lit else 0.15)
    ink = WHITE if lit else (236, 240, 246)
    tw = text_w(UI, label)
    lx = x + 4 if arrow else x + (w - tw) // 2
    draw_text(a, UI, label, lx, y + 2, ink, shadow=(50, 90, 160) if lit else None, sh=(0, 1))
    if arrow:
        down_tri(a, x + w - 6, y + 6, ink)


def xtabs(a, lit):
    """WMP 10's task tabs across the main titlebar: Now Playing raised, its drop-down arrow, then
    Library, Rip, Burn, Sync, Guide between hairline separators."""
    x = 18
    w = text_w(UI, "Now Playing") + 8
    x10_tab(a, x, 1, w, 13, "Now Playing", lit)
    x += w
    ink = T.tab_txt if lit else T.title_dim
    down_tri(a, x + 5, 7, ink)
    x += 10
    for lab in T.tabs[1:]:
        rect(a, x, 3, 1, 9, T.tab_sep if lit else lerp(T.tab_sep, (220, 224, 232), 0.5))
        rect(a, x + 1, 3, 1, 9, WHITE if lit else (236, 238, 242))
        tw = text_w(UI, lab)
        draw_text(a, UI, lab, x + 6, 3, ink)
        x += tw + 12
    assert x <= 242, x
    return x


def x9_combo(a, x, y, w, h, text, lit):
    """WMP 9's drop-down: a white box, the now-playing page icon, the label, a chevron."""
    W, H = a.shape[1], a.shape[0]
    stops = T.combo if lit else [lerp(c, (226, 228, 236), 0.5) for c in T.combo]
    rbox(a, x, y, w, h, 2, stops, T.combo_edge if lit else (170, 176, 196))
    ink = T.combo_txt if lit else (120, 124, 140)
    # the page icon with its play arrow
    rect(a, x + 2, y + 2, 7, h - 4, (120, 136, 180) if lit else (170, 176, 196))
    rect(a, x + 3, y + 3, 5, h - 6, WHITE)
    tri(a, [(x + 4, y + 4), (x + 7, y + h / 2), (x + 4, y + h - 4)], (40, 70, 160) if lit else (150, 156, 176))
    draw_text(a, UI, text, x + 12, y + (h - 9) // 2 + 1, ink)
    cx, cy = x + w - 6, y + h / 2
    paint(a, 0, 0, line_mask(W, H, [(cx - 2.6, cy - 1.4), (cx, cy + 1.2), (cx + 2.6, cy - 1.4)], 1.4), ink)


def xmain_titlebar(lit):
    a = xbar(275, 14, lit, left_edge=True, right_edge=True)
    if T.look == "x10":
        xtabs(a, lit)
    elif T.look == "x9":
        x9_combo(a, 146, 1, 92, 12, "Now Playing", lit)
    caption_button(a, 6, 3, "options", lit)
    caption_button(a, 244, 3, "minimize", lit)
    caption_button(a, 254, 3, "shade", lit)
    caption_button(a, 264, 3, "close", lit)
    return a


def xclutter(lit_letters, bg):
    """The clutter bar: 8's taskbar (the chosen item darker, underlined orange), 9's (lighter,
    navy labels), or 10's little info-bar buttons."""
    a = np.array(bg, dtype=np.int32).copy()
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        gy = y + (h - 5) // 2
        if T.look == "x8":
            if on:
                vfill(a, 0, y, 8, h, T.task_sel)
                rect(a, 0, y + h - 1, 8, 1, T.accent)
            else:
                rect(a, 0, y + h - 1, 8, 1, lerp(a[y + h - 1, 4], WHITE, 0.45))
            draw_text(a, TINY, letter, 2, gy, T.task_txt)
        elif T.look == "x9":
            if on:
                vfill(a, 0, y, 8, h - 1, T.task_sel)
                rect(a, 7, y, 1, h - 1, (170, 186, 220))
            rect(a, 0, y + h - 1, 8, 1, lerp(a[y + h - 1, 4], WHITE, 0.6))
            draw_text(a, TINY, letter, 2, gy, T.task_txt)
        else:
            stops = T.task_sel if on else [lerp(c, WHITE, 0.12) for c in T.task]
            rbox(a, 0, y, 8, h - 1, 1.5, stops, (34, 70, 130))
            rect(a, 1, y + 1, 6, 1, lerp(stops[0], WHITE, 0.4))
            draw_text(a, TINY, letter, 2, y + (h - 1 - 5) // 2, WHITE)
    return a


def xmain_bg():
    a = new(275, 116)
    vfill(a, 0, 14, 275, 102, T.body)
    a[0:14] = main_titlebar(True)
    W, H = 275, 116
    rect(a, 0, 0, 1, 116, T.rim)
    rect(a, 274, 0, 1, 116, T.rim)
    rect(a, 0, 115, 275, 1, T.rim)
    rect(a, 1, 14, 1, 101, T.hi)
    rect(a, 273, 15, 1, 100, T.lo)
    rect(a, 1, 114, 273, 1, T.lo)
    if T.look == "x8":
        # the taskbar column (it sweeps down into the transport chin)
        rbox(a, 3, 15, 19, 74, 4, T.task)
        rect(a, 21, 18, 1, 66, lerp(T.task[1], WHITE, 0.25))
        # the silver foot to the right of the chin, where WMP 8's playlist ends
        paint(a, 0, 0, rr_mask(W, H, 7, 158, 87, 114, 24), T.lo, 0.6)
        rbox(a, 158, 86, 114, 24, 7, T.silver, T.silver_edge)
        # the rounded transport chin
        paint(a, 0, 0, rr_mask(W, H, 14, 2, 84, 164, 31), T.rim, 0.5)
        rbox(a, 2, 83, 164, 31, 14, T.deck, T.deck_rim)
        paint(a, 0, 0, rr_mask(W, H, 12, 10, 84.5, 146, 2), T.deck_hi, 0.7)
    elif T.look == "x9":
        rbox(a, 3, 15, 19, 72, 3, T.task, lerp(T.task[2], (60, 80, 140), 0.3))
        paint(a, 0, 0, rr_mask(W, H, 14, 2, 84, 271, 31), T.lo, 0.6)
        rbox(a, 2, 83, 271, 31, 14, T.deck, T.deck_rim)
        paint(a, 0, 0, rr_mask(W, H, 12, 10, 84.5, 255, 2), WHITE, 0.9)
    else:
        # the info bar, wrapped round the display's left side and under the visualisation
        info = [lerp(T.info, WHITE, 0.10), T.info, lerp(T.info, BLACK, 0.08)]
        edge = lerp(T.info, BLACK, 0.35)
        m = np.maximum(rr_mask(W, H, 3, 2, 14, 271, 45), rr_mask(W, H, 3, 2, 14, 19, 58))
        m = np.maximum(m, rr_mask(W, H, 3, 2, 57, 105, 15))
        paint(a, 0, 0, m, edge)
        m2 = np.maximum(rr_mask(W, H, 2, 3, 15, 269, 43), rr_mask(W, H, 2, 3, 15, 17, 56))
        m2 = np.maximum(m2, rr_mask(W, H, 2, 3, 57, 103, 14))
        paint(a, 0, 0, m2, gcanvas(H, W, 14, 58, info))
        rect(a, 3, 15, 269, 1, lerp(T.info, WHITE, 0.3))
        # the pale glass transport bar
        paint(a, 0, 0, rr_mask(W, H, 14, 2, 84, 271, 31), T.lo, 0.6)
        rbox(a, 2, 83, 271, 31, 14, T.deck, T.deck_rim)
        paint(a, 0, 0, rr_mask(W, H, 12, 10, 84.5, 255, 2), WHITE, 0.9)
        # the recessed, slanted status panel (shuffle and repeat sit in it)
        pts = [(166, 86.5), (241, 86.5), (241, 109.5), (157, 109.5)]
        paint(a, 0, 0, poly_mask(W, H, [(x + 0.0, y + 1) for x, y in pts]), WHITE, 0.8)
        paint(a, 0, 0, poly_mask(W, H, pts), (150, 178, 218))
        inner = [(166.8, 87.5), (240, 87.5), (240, 108.5), (158.6, 108.5)]
        paint(a, 0, 0, poly_mask(W, H, inner), gcanvas(H, W, 87, 22, [(196, 214, 238), (218, 230, 246)]))
    return a


def pill(a, cx, cy, w, h, stops, rim, gloss=0.5):
    W, H = a.shape[1], a.shape[0]
    rbox(a, cx - w / 2, cy - h / 2, w, h, h / 2 - 0.01, stops, rim)
    if gloss:
        paint(a, 0, 0, rr_mask(W, H, h / 2 - 1.5, cx - w / 2 + 2, cy - h / 2 + 1, w - 4, h * 0.42), WHITE, gloss)


def xtransport(a, pressed=None):
    """WMP's round glass transport: play the big button in its well, pause/stop/eject round,
    previous and next as pills."""
    W, H = a.shape[1], a.shape[0]
    C = centres()
    cx, cy = C["play"]
    paint(a, 0, 0, ellipse_mask(W, H, cx - 11.5, cy - 11.5 + 1, 23, 23), T.deck_hi, 0.8)
    paint(a, 0, 0, ellipse_mask(W, H, cx - 11.5, cy - 11.5, 23, 23), lerp(T.deck[2], BLACK, 0.18))
    for k, (cx, cy) in C.items():
        down = k == pressed
        stops = T.btn_down if down else (T.play if k == "play" else T.btn)
        ink = T.glyph_down if down else (T.play_glyph if k == "play" else T.glyph)
        gl = 0.0 if down else 0.5
        o = 0.5 if down else 0
        if k == "play":
            sphere(a, cx, cy, 19, stops, T.btn_rim, gloss=gl)
            glyph(a, k, cx + 0.8 + o, cy + o, ink, 0.95)
        elif k in ("previous", "next"):
            pill(a, cx, cy, 19, 12, stops, T.btn_rim, gl)
            glyph(a, k, cx + o, cy + o, ink, 0.68)
        else:
            sphere(a, cx, cy, 14, stops, T.btn_rim, gloss=gl)
            glyph(a, k, cx + o, cy + o, ink, 0.62)


def xmake_main():
    a = main_bg()
    W, H = 275, 116
    a[22:65, 10:18] = clutter_bar("", a[22:65, 10:18])
    # the display: status line (indicator, time, title) over the visualisation and stream info
    rbox(a, 20, 16, 251, 42, 3, T.pane, T.pane_edge)
    rect(a, 22, 40, 247, 1, T.sep)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, T.ink)
    # the info bar under the visualisation ("Ambience: Random")
    if T.look != "x10":
        rbox(a, 20, 58, 86, 13, 2.5, [lerp(T.info, WHITE, 0.06), T.info], T.pane_edge)
    bold = False
    tw = text_w(UI, T.info_label, 1, bold)
    assert tw <= 80, tw
    draw_text(a, UI, T.info_label, 24, 60, T.info_txt, bold=bold)
    draw_text(a, TINY, "KBPS", 129, 44, T.pane_label)
    draw_text(a, TINY, "KHZ", 169, 44, T.pane_label)
    a[57:70, 107:175] = volume_frame(a[57:70, 107:175], 0)
    a[57:70, 177:215] = balance_frame(a[57:70, 177:215], 0)
    # the seek bar: 8's and 10's green tube, 9's pale groove; WMP's rewind / fast-forward caps
    if T.look == "x9":
        groove(a, 17, 75, 246, 4, T.track)
    else:
        paint(a, 0, 0, rr_mask(W, H, 2.5, 17, 75, 246, 5), T.track_hi, 0.8)
        paint(a, 0, 0, rr_mask(W, H, 2.5, 17, 74, 246, 5), gcanvas(H, W, 74, 5, T.seek))
    for x0, d in ((9, -1), (266, 1)):
        rbox(a, x0 - 1, 73, 9, 8, 3.5, T.btn, T.btn_rim)
        cx = x0 + 3.5
        tri(a, [(cx - 1.8 * d, 75), (cx + 0.2 * d, 77), (cx - 1.8 * d, 79)], T.glyph)
        tri(a, [(cx + 0.2 * d, 75), (cx + 2.2 * d, 77), (cx + 0.2 * d, 79)], T.glyph)
    transport(a)
    if T.look == "x10":
        # the About spot: WMP 10's round "switch to skin mode" button
        cx, cy = 257.5, 98
        sphere(a, cx, cy, 16, T.btn, T.btn_rim, gloss=0.5)
        paint(a, 0, 0, line_mask(W, H, [(cx - 3.2, cy - 3.2), (cx + 1.6, cy + 1.6)], 1.5), T.glyph)
        tri(a, [(cx + 3.2, cy + 3.2), (cx - 1.2, cy + 3.2), (cx + 3.2, cy - 1.2)], T.glyph)
        rect(a, round(cx - 4), round(cy + 4), 8, 1, T.glyph)
    else:
        # the Windows flag, once, in the About spot (at the foot of the real taskbar)
        draw_flag(a, 249, 90, 15)
    return a


def xeq_titlebar(lit):
    a = xbar(275, 14, lit, left_edge=True, right_edge=True)
    if T.look == "x10":
        x10_tab(a, 6, 1, text_w(UI, T.eq_title) + 10, 13, T.eq_title, lit)
    else:
        title_text(a, T.eq_title, 137, 3, lit)
    caption_button(a, 264, 3, "close", lit)
    return a


def xtitle_piece_pl(lit):
    t = bar20(100, lit)
    W, H = t.shape[1], t.shape[0]
    if T.look == "x8":
        combo(t, 2, 4, 96, 13, T.pl_title, lit)
    elif T.look == "x9":
        # the playlist pane's periwinkle header (where "Find Album Info" sits)
        stops = [(120, 136, 210), (96, 113, 191)] if lit else [(170, 176, 206), (150, 156, 190)]
        rbox(t, 4, 4, 92, 13, 2, stops, (70, 84, 160) if lit else (140, 146, 176))
        text_center(t, UI, T.pl_title, 50, 6, WHITE if lit else (236, 238, 246))
    else:
        # WMP 10's "All Music" drop-down
        stops = T.combo if lit else [lerp(c, (196, 204, 218), 0.6) for c in T.combo]
        rbox(t, 12, 4, 76, 13, 2, stops, T.combo_edge if lit else (150, 160, 182))
        paint(t, 0, 0, rr_mask(W, H, 1.5, 13.5, 5, 73, 5), WHITE, 0.28 if lit else 0.14)
        ink = WHITE if lit else (236, 240, 246)
        tw = text_w(UI, T.pl_title) + 10
        x = 50 - tw // 2
        draw_text(t, UI, T.pl_title, x, 6, ink, shadow=(50, 90, 160) if lit else None, sh=(0, 1))
        down_tri(t, x + tw - 4, 10, ink)
    return t


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
    # main.bmp shows the shuffle/repeat and EQ/PL buttons in their resting state too
    SHEETS.clear()
    for name, arr in sheets.items():
        SHEETS[name[:-4]] = save(arr, name)
    write_text_files()
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "readme.txt"]
    wsz = os.path.join(HERE, T.wsz)
    with zipfile.ZipFile(wsz, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(OUT, n), "rb") as fh:
                z.writestr(info, fh.read())
    # genex.bmp completed for real Winamp and WACUP: all 24 colours, readable text, and the
    # standard 112x59 button and scrollbar layout (skins/genex_wacup.py).
    genex_wacup.process(wsz)
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


def draw_bitmap_text(dst, s, x, y):
    text = SHEETS["text"]
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, text, (col * 5, row * 6, 5, 6), x, y)
        x += 5


def tt_font(size):
    for p in ("/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def text_ink():
    """text.bmp's ink: the commonest non-background colour of its letters (what the app uses)."""
    arr = np.asarray(SHEETS["text"]).reshape(-1, 3)
    bg = tuple(arr[150 % 155])
    cols, counts = np.unique(arr, axis=0, return_counts=True)
    best = [(n, tuple(c)) for c, n in zip(cols, counts) if tuple(c) != tuple(T.pane)]
    return max(best)[1]


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
        blit(img, nums, (99, 0, 9, 13), 36, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    # the title box blanked with text.bmp's space, then the title in TrueType in text.bmp's ink
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 27)
    # (Winamp/WACUP's text row is y 27-32; the TrueType capitals stand on its bottom)
    box = img.crop((111, 22, 265, 40))
    ImageDraw.Draw(box).text((0, 33 - 22), state["title"], fill=text_ink(), font=tt_font(11), anchor="ls")
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
    p = T.pledit
    lx, lw = 12, w - 32
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=rgb(p["NormalBG"]))
    font = tt_font(11)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=rgb(p["SelectedBG"]))
        col = rgb(p["Current"]) if i == 1 else rgb(p["Normal"])
        d.text((lx + 2, y + 1), f"{i + 1}. {txt}", fill=col, font=font)
        d.text((lx + lw - 3 - d.textlength(dur, font=font), y + 1), dur, fill=col, font=font)
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
    c0, c1 = np.array(T.vis_bars[0], np.float32), np.array(T.vis_bars[-1], np.float32)
    col = c0 + (c1 - c0) * arr[..., :1]
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


PREVIEW_ROWS = [("Night Drive - Copper Wire", "4:12"), ("Slow Burn - Lantern Hours", "3:47"),
                ("Kiln - Second Firing", "5:03"), ("Ash & Smoke - Afterglow", "2:58"),
                ("Ember Trio - Coal Seam", "6:21"), ("Field Notes - Warm Static", "3:33"),
                ("Tinder - Small Hours", "4:40"), ("The Forge - Bellows", "3:09"),
                ("Hearth - Long Winter", "5:51"), ("Glowworm - Low Light", "4:05"),
                ("Foundry - Pour", "3:22")]


def preview():
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=f"{T.label} - a personal skin", bars=bars)
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
        col.paste(preview_playlist(lit, 275, 232, PREVIEW_ROWS, pressed_close=not lit, drag=not lit), (0, 232))
        col.paste(preview_gen(lit, 275, 140, "album art", pressed_close=not lit), (0, 464))
        cols.append(col)
    gap = 12
    out = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), (60, 60, 64))
    out.paste(cols[0], (gap, gap))
    out.paste(cols[1], (275 + 2 * gap, gap))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, f"preview-{T.name}.png"))


def check_bounds():
    """Every sheet at the size the app reads (at least)."""
    need = {"main": (275, 116), "titlebar": (344, 87), "cbuttons": (136, 36), "shufrep": (92, 85),
            "posbar": (307, 10), "volume": (68, 433), "balance": (68, 433), "monoster": (56, 24),
            "playpaus": (42, 9), "numbers": (99, 13), "nums_ex": (108, 13), "text": (155, 18),
            "pledit": (280, 186), "eqmain": (275, 315), "gen": (194, 109), "genex": (256, 64)}
    for k, (w, h) in need.items():
        im = SHEETS[k]
        assert im.width >= w and im.height >= h and im.mode == "RGB", (k, im.size, im.mode)


if __name__ == "__main__":
    if "--list" in sys.argv:
        for k, t in THEMES.items():
            print(f"{k:9s} {t.wsz:13s} {t.era}")
        sys.exit(0)
    for theme in (sys.argv[1:] or list(THEMES)):
        use_theme(theme)
        names = build()
        check_bounds()
        preview()
        print(f"{T.wsz}: {len(names)} files")
