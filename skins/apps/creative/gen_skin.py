#!/usr/bin/python3
"""FL Studio, RealPlayer 10 and Photoshop CS6: classic Winamp 2.x skins in the style of three
creative / media apps, one theme per skin.

One procedural generator, based on skins/ember/gen_skin.py (sheet layouts, preview renderer) by
way of private-repo/skins/wmp (anti-aliased shape helpers, fonts). Everything is drawn here from
code except each skin's one real logo, read from source/ with Pillow (the SVG rasterised with
rsvg-convert). Private use only.

    /usr/bin/python3 -I gen_skin.py [fl-studio|realplayer|photoshop ...]   (no argument: all)
    /usr/bin/python3 -I gen_skin.py --list

Per theme: the bitmaps and text files in out/<theme>/, zipped flat into <Name>.wsz beside this
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


UI["&"] = [".#..", "#.#.", "#.#.", ".#..", "#.#.", "#..#", ".##."] + ["...."] * 2
UI["."] = [".", ".", ".", ".", ".", ".", "#", ".", "."]
UI[":"] = [".", ".", "#", ".", ".", ".", "#", ".", "."]
UI["%"] = ["#...#", "#..#.", "...#.", "..#..", ".#...", ".#..#", "#...#", ".....", "....."]

# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    # FL Studio 9-12 (2009-2015): the dark grey-blue-green panels, the transport panel, the
    # lime song-position LCD, the channel rack's step buttons (groups of four, grey and red,
    # lit light), the mixer with its peak meters and fader caps, orange highlights.
    "fl-studio": SimpleNamespace(
        name="fl-studio", wsz="FL-Studio.wsz", skin="FL Studio", era="FL Studio 9-12 (2009-2015)",
        owner="Image-Line", logo_note="FL Studio logo",
        frame=[(62, 70, 75), (46, 53, 57)], frame_dim=[(52, 57, 60), (44, 48, 51)],
        body=[(70, 79, 84), (58, 66, 70), (52, 59, 63)], flat=(56, 64, 68),
        rim=(14, 17, 19), hi=(94, 104, 110), lo=(30, 35, 38),
        pane=(16, 20, 22), pane_edge=(8, 10, 11), ink=(176, 228, 126), ink_dim=(36, 50, 36),
        pane_label=(108, 140, 98), body_label=(150, 160, 164),
        title_lit=(204, 212, 216), title_dim=(118, 126, 130),
        btn=[(84, 94, 100), (64, 72, 77), (56, 63, 67)], btn_rim=(20, 24, 26),
        btn_down=[(30, 35, 38), (40, 46, 50)], glyph=(196, 204, 208), glyph_down=(255, 164, 64),
        accent=(246, 150, 48), led_on=(146, 232, 72), led_off=(38, 50, 38),
        pledit=dict(Normal="#C2CCD0", Current="#F7A43C", NormalBG="#262D31", SelectedBG="#4C6A5E"),
        vis_bars=[(250, 84, 56), (246, 170, 60), (232, 222, 72), (120, 214, 70), (48, 140, 52)],
        vis_dots=(26, 32, 34), vis_peak=(255, 255, 255),
        vis_osc=[(255, 196, 120), (246, 160, 70), (220, 130, 50), (180, 100, 40), (140, 76, 32)],
    ),
    # RealPlayer 10 (2004), with the RealOne Player (2001-2002) millennium chrome: metallic
    # silver-blue bars, deep navy body with translucent swooshes, glossy blue pill buttons, the
    # big silver round play button, the Now Playing / Music & My Library / CD / Burn tabs.
    "realplayer": SimpleNamespace(
        name="realplayer", wsz="RealPlayer-10.wsz", skin="RealPlayer 10", era="RealPlayer 10 / RealOne Player",
        owner="RealNetworks", logo_note="RealPlayer logo",
        frame=[(226, 234, 248), (170, 188, 222), (104, 128, 182), (128, 152, 204)],
        frame_dim=[(196, 200, 210), (164, 170, 186), (132, 140, 160), (146, 152, 172)],
        body=[(40, 72, 146), (18, 36, 88), (8, 16, 48)], flat=(14, 28, 72),
        rim=(2, 6, 24), hi=(120, 152, 220), lo=(4, 8, 26),
        pane=(2, 8, 28), pane_edge=(76, 120, 204), ink=(184, 222, 255), ink_dim=(18, 34, 70),
        pane_label=(96, 146, 226), body_label=(170, 196, 240),
        title_lit=(12, 30, 86), title_dim=(96, 104, 126),
        btn=[(176, 212, 255), (74, 134, 234), (22, 64, 176), (50, 104, 214)], btn_rim=(4, 18, 66),
        btn_down=[(12, 34, 110), (36, 86, 186), (96, 156, 244)], glyph=(255, 255, 255), glyph_down=(200, 232, 255),
        silver=[(255, 255, 255), (220, 228, 242), (150, 166, 196), (194, 206, 228)], silver_rim=(30, 44, 90),
        accent=(110, 200, 255), led_on=(120, 230, 255), led_off=(30, 50, 100),
        pledit=dict(Normal="#C4D6F4", Current="#7CD4FF", NormalBG="#061234", SelectedBG="#22468E"),
        vis_bars=[(240, 252, 255), (130, 214, 255), (50, 140, 246), (30, 56, 180)],
        vis_dots=(10, 18, 44), vis_peak=(255, 255, 255),
        vis_osc=[(220, 240, 255), (160, 214, 255), (110, 180, 255), (80, 140, 236), (60, 100, 210)],
    ),
    # Photoshop CS6 (2012), dark interface: #535353 panels, #3c3c3c tab strips, the Options bar
    # as the main titlebar, the tool bar, the Layers / Channels / Paths tabs, the Layers panel's
    # blue selection, thin slider lines with triangle thumbs, Timeline-panel transport icons.
    "photoshop": SimpleNamespace(
        name="photoshop", wsz="Photoshop-CS6.wsz", skin="Photoshop CS6", era="Adobe Photoshop CS6 (2012)",
        owner="Adobe", logo_note="Photoshop CS6 icon",
        frame=[(72, 72, 72), (64, 64, 64)], frame_dim=[(60, 60, 60), (56, 56, 56)],
        body=[(83, 83, 83), (83, 83, 83)], flat=(83, 83, 83), strip=(60, 60, 60),
        rim=(26, 26, 26), hi=(104, 104, 104), lo=(44, 44, 44),
        pane=(36, 36, 36), pane_edge=(24, 24, 24), ink=(224, 224, 224), ink_dim=(64, 64, 64),
        pane_label=(150, 150, 150), body_label=(200, 200, 200),
        title_lit=(222, 222, 222), title_dim=(150, 150, 150),
        btn=[(96, 96, 96), (86, 86, 86)], btn_rim=(34, 34, 34),
        btn_down=[(44, 44, 44), (50, 50, 50)], glyph=(206, 206, 206), glyph_down=(255, 255, 255),
        accent=(74, 111, 165), led_on=(255, 255, 255), led_off=(60, 60, 60),
        pledit=dict(Normal="#D2D2D2", Current="#9CC6FF", NormalBG="#535353", SelectedBG="#4A6FA5"),
        vis_bars=[(236, 236, 236), (190, 190, 190), (130, 130, 130)],
        vis_dots=(46, 46, 46), vis_peak=(255, 255, 255),
        vis_osc=[(236, 236, 236), (200, 200, 200), (170, 170, 170), (140, 140, 140), (110, 110, 110)],
    ),
}


def use_theme(name):
    global T, OUT
    T = THEMES[name]
    OUT = os.path.join(OUT_ROOT, name)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT_ROOT, "scratch"), exist_ok=True)


def FL():
    return T.name == "fl-studio"


def RP():
    return T.name == "realplayer"


def PS():
    return T.name == "photoshop"


def flat_body():
    return T.flat


# ------------------------------------------------------------------------------------------
# Logos (downloaded into source/, opened only with Pillow; SVG rasterised with rsvg-convert)
# ------------------------------------------------------------------------------------------

SRC = os.path.join(HERE, "source")


def logo_rgba(w=None, h=None):
    """The theme's logo as (rgb float array, alpha 0..1), fitted into w x h."""
    scratch = os.path.join(OUT_ROOT, "scratch")
    if PS():
        out = os.path.join(scratch, f"ps-{h}.png")
        subprocess.run(["/usr/bin/rsvg-convert", "-h", str(h * 4),
                        os.path.join(SRC, "logo-ps", "Adobe_Photoshop_CS6_icon.svg"), "-o", out], check=True)
        im = Image.open(out).convert("RGBA")
    elif FL():
        im = Image.open(os.path.join(SRC, "logo-fl", "FL_Studio_11_just_logo.png")).convert("RGBA")
    else:
        im = Image.open(os.path.join(SRC, "logo-real-icon", "Realplayer_computer_icon.png")).convert("RGBA")
        arr = np.array(im)
        # keep the blue "real" swoosh, drop the green "player"
        green = arr[..., 1].astype(int) > arr[..., 2].astype(int)
        arr[green, 3] = 0
        im = Image.fromarray(arr, "RGBA")
        im = im.crop(im.getbbox())
    im = im.crop(im.getbbox())
    sc = min((w or 10 ** 6) / im.width, (h or 10 ** 6) / im.height)
    im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))), Image.LANCZOS)
    im.save(os.path.join(scratch, f"logo-{T.name}.png"))
    a = np.asarray(im).astype(np.float32)
    return a[..., :3], a[..., 3] / 255.0


def draw_logo(a, x, y, w, h):
    col, al = logo_rgba(w, h)
    lh, lw = al.shape
    ox, oy = x + (w - lw) // 2, y + (h - lh) // 2
    sh = np.zeros_like(al)
    sh[1:, 1:] = al[:-1, :-1]
    if not PS():
        paint(a, ox, oy, sh, BLACK, 0.35)
    paint(a, ox, oy, al, col)
    return (ox, oy, lw, lh)


# ------------------------------------------------------------------------------------------
# Frame pieces
# ------------------------------------------------------------------------------------------


def frame_stops(lit):
    return T.frame if lit else T.frame_dim


def bar_frame(w, h, lit, left_edge=False, right_edge=False):
    a = new(w, h)
    vfill(a, 0, 0, w, h, frame_stops(lit))
    if RP():
        # the chrome's glassy upper half
        hh = h // 2
        reg = a[0:hh].astype(np.float32)
        a[0:hh] = np.round(reg + (255 - reg) * (0.25 if lit else 0.12)).astype(np.int32)
        rect(a, 0, h - 1, w, 1, (40, 60, 120) if lit else (110, 116, 134))
    elif FL():
        rect(a, 0, 1, w, 1, (84, 94, 100) if lit else (68, 74, 78))
        rect(a, 0, h - 1, w, 1, (24, 28, 30))
    else:
        rect(a, 0, 1, w, 1, (92, 92, 92) if lit else (74, 74, 74))
        rect(a, 0, h - 1, w, 1, (40, 40, 40))
    rect(a, 0, 0, w, 1, T.rim)
    if left_edge:
        rect(a, 0, 0, 1, h, T.rim)
        rect(a, 1, 1, 1, h - 2, lerp(frame_stops(lit)[0], WHITE, 0.3))
    if right_edge:
        rect(a, w - 1, 0, 1, h, T.rim)
        rect(a, w - 2, 1, 1, h - 2, lerp(frame_stops(lit)[-1], BLACK, 0.3))
    return a


def frame_colour_at(row, lit, h=14):
    return ramp(frame_stops(lit), (row + 0.5) / h)


def caption_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button."""
    W, H = a.shape[1], a.shape[0]
    if RP():
        stops = T.btn_down if pressed else (T.btn if lit else [(200, 206, 220), (150, 160, 184), (120, 128, 150)])
        sphere(a, x + 4.5, y + 4.5, 9, stops, T.btn_rim if lit else (100, 106, 126), gloss=0.0 if pressed else 0.5)
        ink = WHITE if lit or pressed else (236, 238, 244)
    elif FL():
        if pressed:
            rbox(a, x, y, 9, 9, 1.5, [(26, 30, 33), (34, 39, 42)], (10, 12, 13))
        ink = T.glyph_down if pressed else ((176, 184, 188) if lit else (112, 118, 122))
    else:
        if pressed:
            rect(a, x, y, 9, 9, (40, 40, 40))
            rect(a, x, y, 9, 1, (28, 28, 28))
        ink = WHITE if pressed else ((206, 206, 206) if lit else (140, 140, 140))
    X, Y = x, y
    if kind == "options":
        if PS():
            # the tool preset picker: the Move tool and its little arrow
            for dx, dy in ((3, 1), (2, 2), (3, 2), (4, 2), (3, 3), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4),
                           (3, 5), (2, 6), (3, 6), (4, 6), (3, 7)):
                px(a, X + dx - 1, Y + dy, ink)
            for dx in range(3):
                px(a, X + 6 + dx, Y + 6, ink)
            px(a, X + 7, Y + 7, ink)
        else:
            paint(a, 0, 0, poly_mask(W, H, [(X + 2, Y + 3.3), (X + 7, Y + 3.3), (X + 4.5, Y + 6.3)]), ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 2 if RP() else 1, ink)
        if not RP():
            rect(a, X + 2, Y + 6, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 2, ink)
        rect(a, X + 2, Y + 6, 5, 1, lerp(ink, frame_colour_at(y + 4, lit), 0.4))
    elif kind == "close":
        wd = 1.5 if RP() else 1.3
        paint(a, 0, 0, line_mask(W, H, [(X + 2.3, Y + 2.3), (X + 6.7, Y + 6.7)], wd), ink)
        paint(a, 0, 0, line_mask(W, H, [(X + 6.7, Y + 2.3), (X + 2.3, Y + 6.7)], wd), ink)


def title_text(a, s, x, y, lit, centre=False, col=None):
    col = col or (T.title_lit if lit else T.title_dim)
    if centre:
        x = x - text_w(UI, s) // 2
    shadow = (255, 255, 255) if (RP() and lit) else (BLACK if FL() and lit else None)
    sh = (0, 1)
    if RP() and lit:
        shadow = lerp(T.frame[1], WHITE, 0.6)
    return draw_text(a, UI, s, x, y, col, shadow=shadow, sh=sh)


def rp_tab(a, x, y, w, h, label, lit, selected):
    """RealPlayer's glossy blue tab (selected) or plain label on the chrome."""
    W, H = a.shape[1], a.shape[0]
    if selected:
        stops = T.btn if lit else [lerp(c, (150, 156, 176), 0.6) for c in T.btn]
        rbox(a, x, y, w, h, 4, stops, T.btn_rim if lit else (90, 96, 118))
        paint(a, 0, 0, rr_mask(W, H, 3, x + 2, y + 1, w - 4, h * 0.42), WHITE, 0.45 if lit else 0.2)
        draw_text(a, UI, label, x + (w - text_w(UI, label)) // 2, y + 2, WHITE,
                  shadow=(8, 30, 100) if lit else None, sh=(0, 1))
    else:
        title_text(a, label, x + (w - text_w(UI, label)) // 2, y + 2, lit)


def ps_tab(a, x, y, w, h, label, lit, active):
    """A Photoshop CS6 panel tab: the active one in the panel's grey, joined to the panel."""
    if active:
        rect(a, x, y, w, h, T.flat)
        rect(a, x, y, w, 1, (110, 110, 110))
        rect(a, x, y, 1, h, (40, 40, 40))
        rect(a, x + w - 1, y, 1, h, (40, 40, 40))
        draw_text(a, UI, label, x + (w - text_w(UI, label)) // 2, y + 3, (230, 230, 230) if lit else (176, 176, 176))
    else:
        draw_text(a, UI, label, x + (w - text_w(UI, label)) // 2, y + 3, (156, 156, 156) if lit else (124, 124, 124))
        rect(a, x + w, y + 3, 1, h - 5, (48, 48, 48))


# ------------------------------------------------------------------------------------------
# Small shared drawing
# ------------------------------------------------------------------------------------------


def lcd(a, x, y, w, h):
    """A recessed display: the inside is (x, y, w, h)."""
    if RP():
        rbox(a, x - 1, y - 1, w + 2, h + 2, 3, [T.pane, T.pane], T.pane_edge)
        W, H = a.shape[1], a.shape[0]
        paint(a, 0, 0, rr_mask(W, H, 2, x + 1, y, w - 2, max(2, h * 0.3)), WHITE, 0.05)
    elif FL():
        rect(a, x, y, w, h, T.pane)
        rect(a, x - 1, y - 1, w + 2, 1, T.pane_edge)
        rect(a, x - 1, y - 1, 1, h + 2, T.pane_edge)
        rect(a, x - 1, y + h, w + 2, 1, (88, 98, 104))
        rect(a, x + w, y - 1, 1, h + 2, (88, 98, 104))
    else:
        rect(a, x, y, w, h, T.pane)
        rect(a, x - 1, y - 1, w + 2, h + 2, T.pane_edge)
        rect(a, x, y, w, h, T.pane)
        rect(a, x - 1, y + h, w + 2, 1, (100, 100, 100))


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


def digit(a, n, x, y, col):
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + 1 + c, y + 1 + r, col)


def fl_knob(a, cx, cy, d, value, lit=True):
    """An FL Studio knob: dark round body, light rim, value arc in orange, pointer line."""
    W, H = a.shape[1], a.shape[0]
    paint(a, 0, 0, ellipse_mask(W, H, cx - d / 2, cy - d / 2 + 1, d, d), BLACK, 0.4)
    sphere(a, cx, cy, d, [(110, 120, 126), (60, 68, 72), (40, 46, 50)], (16, 19, 21), gloss=0.15)
    ang0, ang1 = math.radians(135), math.radians(135 + 270 * value)
    r = d / 2 - 1.2
    pts = [(cx + r * math.cos(ang0 + (ang1 - ang0) * t / 20), cy + r * math.sin(ang0 + (ang1 - ang0) * t / 20))
           for t in range(21)]
    paint(a, 0, 0, line_mask(W, H, pts, 1.3), T.accent)
    paint(a, 0, 0, line_mask(W, H, [(cx, cy), (cx + (r - 1) * math.cos(ang1), cy + (r - 1) * math.sin(ang1))], 1.2),
          (230, 236, 238))


def fl_button(a, x, y, w, h, pressed, r=2.0):
    if pressed:
        rbox(a, x, y, w, h, r, T.btn_down, T.btn_rim)
    else:
        rbox(a, x, y, w, h, r, T.btn, T.btn_rim)
        rect(a, x + 2, y + 1, w - 4, 1, (104, 114, 120))


def rp_pill(a, x, y, w, h, pressed, on=False, stops=None):
    W, H = a.shape[1], a.shape[0]
    st = stops or (T.btn_down if pressed else T.btn)
    if on and not pressed:
        st = [lerp(c, (120, 220, 255), 0.35) for c in st]
    paint(a, 0, 0, rr_mask(W, H, h / 2, x, y + 1, w, h), BLACK, 0.35)
    rbox(a, x, y, w, h, h / 2 - 0.01, st, T.btn_rim)
    if not pressed:
        paint(a, 0, 0, rr_mask(W, H, h / 2 - 1.5, x + 2, y + 1, w - 4, h * 0.38), WHITE, 0.32 if h < 16 else 0.5)


def ps_button(a, x, y, w, h, pressed):
    """CS6 push button: flat mid grey with a dark outline (pressed: darker)."""
    rect(a, x, y, w, h, T.btn_rim)
    vfill(a, x + 1, y + 1, w - 2, h - 2, T.btn_down if pressed else T.btn)
    if not pressed:
        rect(a, x + 1, y + 1, w - 2, 1, (116, 116, 116))


def ps_checkbox(a, x, y, on, pressed=False, lit=True):
    rect(a, x, y, 8, 8, (30, 30, 30))
    rect(a, x + 1, y + 1, 6, 6, (52, 52, 52) if not pressed else (40, 40, 40))
    if pressed:
        rect(a, x, y, 8, 1, T.accent)
        rect(a, x, y, 1, 8, T.accent)
        rect(a, x + 7, y, 1, 8, T.accent)
        rect(a, x, y + 7, 8, 1, T.accent)
    if on:
        col = WHITE if lit else (180, 180, 180)
        for dx, dy in ((1, 4), (2, 5), (3, 6), (4, 5), (5, 4), (6, 3), (7, 2), (2, 4), (3, 5), (4, 4), (5, 3), (6, 2)):
            px(a, x + dx, y + dy - 1, col)


# Photoshop tool icons, 7x7 pixel art (the CS6 tool bar, top to bottom)
PS_TOOLS = {
    "move": ["...#...", "..###..", "...#...", "#######", "...#...", "..###..", "...#..."],
    "marquee": ["##.##.#", "......#", "#......", "#.....#", "......#", "#......", "#.##.##"],
    "lasso": [".####..", "#....#.", "#.....#", ".#...#.", "..###..", "..#....", ".#....."],
    "crop": [".#.....", "######.", ".#...#.", ".#...#.", ".#...#.", ".######", ".....#."],
    "eyedrop": [".....##", "....###", "...###.", "..#.#..", ".#.#...", "#.#....", "##....."],
    "brush": [".....##", "....##.", "...##..", "..##...", ".##....", "###....", "##....."],
    "stamp": ["..###..", "..###..", "...#...", "...#...", "#######", "#######", "......."],
    "eraser": ["...###.", "..#..#.", ".#..#..", "#..#...", "####...", ".......", "#######"],
    "gradient": ["#######", "#.#.###", "##.#.##", "#.#.###", "##.#.##", "#.#.###", "#######"],
    "dodge": [".###...", "#####..", "#####..", ".###...", "...#...", "....#..", ".....#."],
    "pen": ["...#...", "..###..", "..#.#..", ".#.#.#.", ".#...#.", "..###..", "..###.."],
    "type": ["#######", "#..#..#", "...#...", "...#...", "...#...", "...#...", "..###.."],
    "path": ["#......", "##.....", "###....", "####...", "#####..", "##.....", "#.#...."],
    "shape": ["#######", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", "#######"],
    "hand": ["..#.#..", ".##.##.", ".#####.", "#######", ".#####.", "..####.", "..###.."],
    "zoom": [".###...", "#...#..", "#...#..", "#...#..", ".####..", "....##.", ".....##"],
}


def icon7(a, name, x, y, col):
    for r, row in enumerate(PS_TOOLS[name]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + c, y + r, col)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]
FL_MENUS = ["FILE", "EDIT", "ADD", "PATTERNS", "VIEW", "OPTIONS", "TOOLS", "HELP"]
RP_TABS = ["Now Playing", "Music & My Library", "CD", "Burn"]


def clutter_bar(lit_letters, bg):
    a = new(8, 43, bg)
    if FL():
        rect(a, 0, 0, 8, 43, (28, 33, 36))
        for i, (letter, y, h) in enumerate(CLUTTER_SLOTS):
            on = letter in lit_letters
            red = i % 2 == 1
            face = ((246, 166, 174) if red else (216, 222, 224)) if on else ((122, 82, 88) if red else (98, 106, 111))
            rect(a, 1, y, 6, h, face)
            rect(a, 1, y, 6, 1, lerp(face, WHITE, 0.3))
            rect(a, 1, y + h - 1, 6, 1, lerp(face, BLACK, 0.3))
            draw_text(a, TINY, letter, 2, y + (h - 5) // 2, (40, 30, 32) if on else (210, 214, 216))
    elif RP():
        rbox(a, 0, 0, 8, 43, 3.5, [(6, 14, 40), (2, 6, 22)], (60, 90, 160))
        for letter, y, h in CLUTTER_SLOTS:
            on = letter in lit_letters
            st = [lerp(c, (120, 220, 255), 0.3) for c in T.btn] if on else T.silver
            rbox(a, 1, y, 6, h, 2.5, st, T.btn_rim)
            draw_text(a, TINY, letter, 2, y + (h - 5) // 2, WHITE if on else (24, 40, 90))
    else:
        rect(a, 0, 0, 8, 43, T.strip)
        rect(a, 0, 0, 8, 1, (40, 40, 40))
        for letter, y, h in CLUTTER_SLOTS:
            on = letter in lit_letters
            if on:
                rect(a, 1, y, 6, h, (38, 38, 38))
                rect(a, 1, y, 6, 1, (28, 28, 28))
            draw_text(a, TINY, letter, 2, y + (h - 5) // 2, WHITE if on else (190, 190, 190))
    return a


def main_titlebar(lit):
    a = bar_frame(275, 14, lit, left_edge=True, right_edge=True)
    if FL():
        # FL's main menu, in its small capitals
        x = 20
        for m in FL_MENUS:
            w = text_w(TINY, m)
            if x + w > 238:
                break
            draw_text(a, TINY, m, x, 5, (196, 204, 208) if lit else (112, 120, 124), shadow=(24, 28, 30) if lit else None)
            x += w + 6
    elif RP():
        x = 19
        for i, lab in enumerate(RP_TABS):
            w = text_w(UI, lab) + (12 if i == 0 else 8)
            rp_tab(a, x, 1, w, 12, lab, lit, i == 0)
            x += w + 1
            if i + 1 < len(RP_TABS):
                rect(a, x, 4, 1, 7, (90, 110, 160) if lit else (150, 154, 168))
                x += 2
        assert x <= 242, x
    else:
        # the Options bar of the Move tool
        rect(a, 17, 3, 1, 9, (44, 44, 44))
        rect(a, 18, 3, 1, 9, (96, 96, 96))
        ink = T.title_lit if lit else T.title_dim
        ps_checkbox(a, 21, 3, True, lit=lit)
        x = draw_text(a, UI, "Auto-Select:", 31, 3, ink) + 2
        fw = text_w(UI, "Layer") + 13
        rect(a, x, 2, fw, 11, (34, 34, 34))
        rect(a, x + 1, 3, fw - 2, 9, (58, 58, 58) if lit else (54, 54, 54))
        draw_text(a, UI, "Layer", x + 3, 3, ink)
        tri(a, [(x + fw - 8, 6), (x + fw - 3, 6), (x + fw - 5.5, 9)], ink)
        x += fw + 4
        ps_checkbox(a, x, 3, False, lit=lit)
        x = draw_text(a, UI, "Show Transform Controls", x + 10, 3, ink)
        assert x <= 240, x
    caption_button(a, 6, 3, "options", lit)
    caption_button(a, 244, 3, "minimize", lit)
    caption_button(a, 254, 3, "shade", lit)
    caption_button(a, 264, 3, "close", lit)
    return a


def bar_cell_pressed(kind, src):
    cell = bar_frame(275, 14, True, left_edge=True, right_edge=True)[3:12, src:src + 9].copy()
    caption_button(cell, 0, 0, kind, True, pressed=True)
    return cell


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
    unlit = clutter_bar("", main[30, 9])
    lit = clutter_bar("OAIDV", main[30, 9])
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = lit[y:y + h]
    return a


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116)
# ------------------------------------------------------------------------------------------

CB = {"previous": (16, 23), "play": (39, 23), "pause": (62, 23), "stop": (85, 23), "next": (108, 22)}
CB_Y = 88
EJECT = (136, 89, 22, 16)
ABOUT = (244, 85, 26, 27)        # the logo's box (About spot)
STEP_Y = 107                     # FL: the channel-rack strip


def window_rims(a, h=116):
    rect(a, 0, 0, 1, h, T.rim)
    rect(a, 274, 0, 1, h, T.rim)
    rect(a, 0, h - 1, 275, 1, T.rim)
    rect(a, 1, 14, 1, h - 15, T.hi)
    rect(a, 1, 14, 273, 1, T.hi)
    rect(a, 273, 15, 1, h - 16, T.lo)
    rect(a, 1, h - 2, 273, 1, T.lo)


def swoosh(a, cx, cy, rx, ry, width, alpha, y0=14):
    """RealOne's translucent swoosh: a thin elliptical band, faded."""
    W, H = a.shape[1], a.shape[0]
    outer = ellipse_mask(W, H, cx - rx, cy - ry, 2 * rx, 2 * ry)
    inner = ellipse_mask(W, H, cx - rx + width, cy - ry + width * 0.6, 2 * rx - 2 * width, 2 * ry - 1.2 * width)
    m = np.clip(outer - inner, 0, 1)
    m[:y0] = 0
    xs = np.linspace(0, 1, W)[None, :]
    paint(a, 0, 0, m * (0.3 + 0.7 * xs), (150, 200, 255), alpha)


def main_bg():
    a = new(275, 116)
    vfill(a, 0, 14, 275, 102, T.body)
    if RP():
        swoosh(a, 150, 170, 230, 140, 10, 0.30)
        swoosh(a, 100, 175, 260, 150, 2.5, 0.55)
        swoosh(a, 300, 40, 120, 70, 6, 0.22)
    a[0:14] = main_titlebar(True)
    window_rims(a)
    if FL():
        # the transport panel's recess and the channel-rack strip
        rect(a, 14, 86, 148, 21, (40, 46, 50))
        rect(a, 14, 86, 148, 1, (28, 32, 35))
        rect(a, 14, 106, 148, 1, (84, 94, 100))
    elif RP():
        W, H = 275, 116
        x, y, w, h = 6, 85, 236, 25
        paint(a, 0, 0, rr_mask(W, H, h / 2, x, y + 1, w, h), BLACK, 0.5)
        rbox(a, x, y, w, h, h / 2, T.silver, T.silver_rim)
        paint(a, 0, 0, rr_mask(W, H, h / 2 - 2, x + 8, y + 1.5, w - 16, h * 0.4), WHITE, 0.45)
        # the groove the transport sits in
        paint(a, 0, 0, rr_mask(W, H, 9, 15, 87, 145, 20), (110, 126, 160), 0.6)
    else:
        rect(a, 2, 15, 271, 1, (100, 100, 100))
        # the Timeline panel's strip under the seek bar
        rect(a, 2, 85, 271, 1, (64, 64, 64))
        rect(a, 2, 86, 271, 1, (96, 96, 96))
    return a


def centres():
    c = {k: (x + w / 2, CB_Y + 9) for k, (x, w) in CB.items()}
    ex, ey, ew, eh = EJECT
    c["eject"] = (ex + ew / 2, ey + eh / 2)
    return c


def transport(a, pressed=None):
    W, H = a.shape[1], a.shape[0]
    C = centres()
    for k, (cx, cy) in C.items():
        p = k == pressed
        if k == "eject":
            x, y, w, h = EJECT
        else:
            x, w = CB[k]
            y, h = CB_Y, 18
        if FL():
            fl_button(a, x + 1, y + 1, w - 2, h - 2, p)
            ink = T.glyph_down if p else ((156, 224, 86) if k == "play" else T.glyph)
            glyph(a, k, cx + (0.6 if k == "play" else 0) + (0.5 if p else 0), cy + (0.5 if p else 0), ink, 0.8)
        elif RP():
            if k == "play":
                st = T.btn_down if p else T.btn
                paint(a, 0, 0, ellipse_mask(W, H, cx - 10, cy - 9, 20, 20), BLACK, 0.4)
                sphere(a, cx, cy, 18, st, T.btn_rim, gloss=0.0 if p else 0.55)
                glyph(a, k, cx + 0.8, cy + 0.5, (8, 24, 80), 0.85)
                glyph(a, k, cx + 0.8, cy, WHITE if not p else T.glyph_down, 0.85)
            else:
                rp_pill(a, x + 1, y + 2, w - 2, h - 4, p)
                glyph(a, k, cx + (0.5 if p else 0), cy + (0.5 if p else 0), T.glyph_down if p else T.glyph, 0.72)
        else:
            if p:
                rect(a, x + 2, y + 1, w - 4, h - 2, (40, 40, 40))
                rect(a, x + 2, y + 1, w - 4, 1, (28, 28, 28))
                rect(a, x + 2, y + h - 2, w - 4, 1, (98, 98, 98))
            glyph(a, k, cx, cy, T.glyph_down if p else T.glyph, 0.72)


def fl_steps(a):
    """The channel rack along the bottom: mute LED, channel name and sixteen step buttons."""
    y = STEP_Y
    rect(a, 16, y + 2, 3, 3, T.led_on)
    rect(a, 15, y + 1, 5, 1, (30, 36, 38))
    rect(a, 21, y, 26, 7, (80, 90, 96))
    rect(a, 21, y + 6, 26, 1, (30, 34, 37))
    draw_text(a, TINY, "KICK", 22, y + 1, (226, 230, 232))
    pattern = [1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0]
    for i in range(16):
        x = 50 + i * 9 + (i // 4) * 2
        red = (i // 4) % 2 == 1
        on = pattern[i]
        face = ((246, 166, 174) if red else (216, 222, 224)) if on else ((122, 82, 88) if red else (98, 106, 111))
        rect(a, x, y, 8, 7, face)
        rect(a, x, y, 8, 1, lerp(face, WHITE, 0.35))
        rect(a, x, y + 6, 8, 1, lerp(face, BLACK, 0.35))


def make_main():
    a = main_bg()
    bg = a[30, 9]
    a[22:65, 10:18] = clutter_bar("", bg)
    lcd(a, 21, 20, 84, 42)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, T.ink)
    lcd(a, 109, 21, 159, 33)
    rect(a, 110, 38, 157, 1, lerp(T.pane, T.pane_label, 0.35))
    draw_text(a, TINY, "KBPS", 129, 44, T.pane_label)
    draw_text(a, TINY, "KHZ", 169, 44, T.pane_label)
    a[57:70, 107:175] = volume_frame(a[57:70, 107:175], 0)
    a[57:70, 177:215] = balance_frame(a[57:70, 177:215], 0)
    a[72:82, 16:264] = seek_rail(a[72:82, 16:264])
    transport(a)
    for name, x0, w in (("eq", 219, 23), ("pl", 242, 23)):
        a[58:70, x0:x0 + w] = toggle_cell(a[58:70, x0:x0 + w], w, 12, name.upper(), False, False)
    a[89:104, 164:211] = toggle_cell(a[89:104, 164:211], 47, 15, "SHUFFLE", False, False, ends="left")
    a[89:104, 210:238] = toggle_cell(a[89:104, 210:238], 28, 15, "REPEAT", False, False, ends="right")
    if FL():
        fl_steps(a)
    x, y, w, h = ABOUT
    if PS():
        draw_logo(a, 246, 88, 22, 22)
    elif RP():
        draw_logo(a, 243, 88, 28, 20)
    else:
        draw_logo(a, x, y, w, h)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons, shufrep, monoster, playpaus, numbers, text
# ------------------------------------------------------------------------------------------


def make_cbuttons(main):
    a = new(136, 36, flat_body())
    sheet_x = {"previous": 0, "play": 23, "pause": 46, "stop": 69, "next": 92}
    for k, (mx, w) in CB.items():
        x = sheet_x[k]
        a[0:18, x:x + w] = main[CB_Y:CB_Y + 18, mx:mx + w]
        p = main_bg()
        transport(p, k)
        a[18:36, x:x + w] = p[CB_Y:CB_Y + 18, mx:mx + w]
    ex, ey, ew, eh = EJECT
    a[0:16, 114:136] = main[ey:ey + eh, ex:ex + ew]
    p = main_bg()
    transport(p, "eject")
    a[16:32, 114:136] = p[ey:ey + eh, ex:ex + ew]
    return a


PS_LABELS = {"SHUFFLE": "Shuffle", "REPEAT": "Loop", "EQ": "EQ", "PL": "PL", "ON": "On", "AUTO": "Auto"}


def toggle_cell(bg, w, h, label, on, pressed, ends="both", led=True):
    """A toggle or push button cell drawn on bg (ends: which ends are rounded, for joined pairs)."""
    a = bg.copy()
    if PS():
        if label in PS_LABELS and led:
            s = PS_LABELS[label]
            font = UI if s != s.upper() else TINY
            tw = text_w(font, s)
            x0 = max(0, (w - tw - 9) // 2)
            ps_checkbox(a, x0, (h - 8) // 2, on, pressed)
            draw_text(a, font, s, x0 + 9, (h - 7) // 2 if font is UI else (h - 5) // 2, T.body_label)
        else:
            ps_button(a, 0, 0, w, h, pressed)
            if label:
                text_center(a, UI, label.capitalize() if label != "PRESETS" else "Presets", w // 2 + (1 if pressed else 0),
                            (h - 7) // 2 + (1 if pressed else 0), WHITE if pressed else T.body_label)
        return a
    ext = 8
    big = np.zeros((h, w + ext, 3), np.int32)
    if ends == "left":
        big[:, :w] = a
        ox = 0
    elif ends == "right":
        big[:, ext:] = a
        ox = ext
    else:
        big = a.copy()
        ox = 0
    bw = big.shape[1]
    if FL():
        fl_button(big, 0, 0, bw, h, pressed)
    else:
        rp_pill(big, 0, 0, bw, h - 1, pressed, on)
    a = big[:, ox:ox + w].copy()
    if ends == "left":
        rect(a, w - 1, 1, 1, h - 2, T.btn_rim)
    elif ends == "right":
        rect(a, 0, 1, 1, h - 2, T.btn_rim)
    o = 1 if pressed else 0
    if not label:
        return a
    tw = text_w(TINY, label)
    if FL():
        ink = T.accent if on else (T.glyph if not pressed else (220, 226, 228))
        if h >= 15:
            draw_text(a, TINY, label, (w - tw) // 2 + o, 3 + o, ink, shadow=None if pressed else (24, 28, 30))
            if led:
                rect(a, 4 + o, h - 5 + o, w - 8, 2, T.led_on if on else T.led_off)
        else:
            lx = (w - tw - 5) // 2
            if led:
                rect(a, lx + o, h // 2 - 1 + o, 3, 3, T.led_on if on else T.led_off)
            draw_text(a, TINY, label, lx + 5 + o, (h - 5) // 2 + o, ink)
    else:
        ink = (255, 255, 255) if not on else (200, 245, 255)
        if led:
            lx = (w - tw - 5) // 2
            col = T.led_on if on else T.led_off
            rect(a, lx + o, (h - 1) // 2 - 1 + o, 3, 3, col)
            draw_text(a, TINY, label, lx + 5 + o, (h - 1 - 5) // 2 + o, ink,
                      shadow=T.btn_rim if h >= 15 else None, sh=(0, 1))
        else:
            draw_text(a, TINY, label, (w - tw) // 2 + o, (h - 1 - 5) // 2 + o, ink,
                      shadow=T.btn_rim if h >= 15 else None, sh=(0, 1))
    return a


def make_shufrep(main):
    base = main_bg()
    a = new(92, 85, flat_body())
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = toggle_cell(base[89:104, 210:238], 28, 15, "REPEAT", on, pressed, ends="right",
                                        led=not RP())
        a[y:y + 15, 28:75] = toggle_cell(base[89:104, 164:211], 47, 15, "SHUFFLE", on, pressed, ends="left")
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        src = base[58:70, 219 + (x % 46):219 + (x % 46) + 23]
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
    tri(a, [(2, 1), (8, 4.5), (2, 8)], (156, 224, 86) if FL() else col)
    rect(a, 9 + 2, 1, 2, 7, col)
    rect(a, 9 + 5, 1, 2, 7, col)
    rect(a, 18 + 2, 2, 5, 5, col)
    rect(a, 36, 0, 3, 9, T.pane)
    rect(a, 39 + 1, 3, 1, 3, col)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T.pane)
    for n in range(10):
        if FL():
            # LCD ghost segments behind the lit ones
            for r, row in enumerate(DIGITS[8]):
                for c, ch in enumerate(row):
                    if ch == "#":
                        px(a, 9 * n + 1 + c, 1 + r, T.ink_dim)
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
# posbar.bmp, volume.bmp, balance.bmp
# ------------------------------------------------------------------------------------------


def seek_rail(seat):
    """248 x 10: the seek bar's rail."""
    t = seat.copy()
    W, H = t.shape[1], t.shape[0]
    if FL():
        # the playlist's time ruler: dark strip, a tick per beat and a longer one per bar
        rect(t, 0, 1, 248, 8, (22, 26, 28))
        rect(t, 0, 1, 248, 1, (12, 14, 15))
        rect(t, 0, 8, 248, 1, (84, 94, 100))
        for i, x in enumerate(range(3, 246, 8)):
            rect(t, x, 2, 1, 4 if i % 4 == 0 else 2, (120, 130, 134) if i % 4 == 0 else (70, 78, 82))
        rect(t, 2, 6, 244, 1, (52, 60, 64))
    elif RP():
        paint(t, 0, 0, rr_mask(W, H, 3, 2, 3, 244, 5), (150, 180, 240), 0.5)
        paint(t, 0, 0, rr_mask(W, H, 3, 2, 2, 244, 5), (2, 6, 22))
        paint(t, 0, 0, rr_mask(W, H, 2, 3, 3, 242, 2), (40, 70, 140), 0.6)
    else:
        rect(t, 2, 4, 244, 1, (30, 30, 30))
        rect(t, 2, 5, 244, 1, (112, 112, 112))
        for i, x in enumerate(range(2, 247, 10)):
            rect(t, x, 1, 1, 2 if i % 5 else 3, (130, 130, 130))
    return t


def ps_triangle(a, cx, y, pressed, w=9):
    """Photoshop's slider triangle, pointing up at the line above it: dark outline, light fill."""
    h = (w + 1) // 2
    fill = WHITE if pressed else (214, 214, 214)
    for r in range(h):
        rect(a, cx - r, y + r, 2 * r + 1, 1, (24, 24, 24))
        if 0 < r < h - 1:
            rect(a, cx - r + 1, y + r, 2 * r - 1, 1, fill)


def make_posbar(main):
    a = new(307, 10, flat_body())
    a[0:10, 0:248] = main[72:82, 16:264]
    seat = seek_rail(main_bg()[72:82, 16:264])
    for x0, sel in ((248, False), (278, True)):
        t = seat[:, 100:129].copy()
        W, H = 29, 10
        if FL():
            # the song position marker: an orange flag on the ruler
            col = (255, 196, 110) if sel else T.accent
            tri(t, [(8.5, 0.5), (20.5, 0.5), (14.5, 7.5)], (30, 20, 10), 0.6)
            tri(t, [(9, 0), (20, 0), (14.5, 6.5)], col)
            rect(t, 14, 6, 1, 4, col)
        elif RP():
            st = [lerp(c, (140, 210, 255), 0.4) for c in T.silver] if sel else T.silver
            rbox(t, 6, 1, 17, 8, 3.99, st, T.silver_rim)
            paint(t, 0, 0, rr_mask(W, H, 2.5, 8, 1.5, 13, 3), WHITE, 0.6)
        else:
            rect(t, 14, 3, 1, 3, (30, 30, 30))
            ps_triangle(t, 14, 5, sel)
        a[0:10, x0:x0 + 29] = t
    return a


def volume_frame(seat, level):
    """68 x 13."""
    t = seat.copy()
    W, H = t.shape[1], t.shape[0]
    if FL():
        # a horizontal peak meter in a dark slot, with the fader's groove under it
        rect(t, 2, 2, 64, 9, (20, 24, 26))
        rect(t, 2, 2, 64, 1, (10, 12, 13))
        rect(t, 2, 10, 64, 1, (84, 94, 100))
        n = round(level * 31)
        for i in range(31):
            x = 3 + 2 * i
            colr = ramp(T.vis_bars[::-1][1:], i / 30)
            rect(t, x, 3, 1, 4, colr if i < n else lerp(colr, (20, 24, 26), 0.8))
        rect(t, 3, 8, 62, 1, (8, 10, 11))
    elif RP():
        paint(t, 0, 0, rr_mask(W, H, 3, 3, 5, 62, 5), (150, 180, 240), 0.5)
        paint(t, 0, 0, rr_mask(W, H, 3, 3, 4, 62, 5), (2, 6, 22))
        if level > 0:
            m = rr_mask(W, H, 2, 4, 5, 60, 3)
            m[:, int(4 + level * 60):] = 0
            paint(t, 0, 0, m, gcanvas(H, W, 5, 3, [(170, 230, 255), (40, 120, 240)]))
    else:
        # an Opacity slider: the thin line, filled in blue up to the value
        rect(t, 4, 4, 60, 1, (30, 30, 30))
        rect(t, 4, 5, 60, 1, (112, 112, 112))
        if level > 0:
            rect(t, 4, 4, round(level * 60), 1, T.accent)
            rect(t, 4, 5, round(level * 60), 1, lerp(T.accent, WHITE, 0.3))
    return t


def balance_frame(seat, reach):
    """38 x 13."""
    t = seat.copy()
    W, H = t.shape[1], t.shape[0]
    if FL():
        rect(t, 2, 2, 34, 9, (20, 24, 26))
        rect(t, 2, 2, 34, 1, (10, 12, 13))
        rect(t, 2, 10, 34, 1, (84, 94, 100))
        half = round(reach * 15)
        for x in range(3, 35):
            d = abs(x - 18.5)
            rect(t, x, 4, 1, 3, T.accent if d <= half + 0.5 and reach > 0 else (44, 34, 26))
        rect(t, 18, 0, 2, 2, (200, 206, 210))
    elif RP():
        paint(t, 0, 0, rr_mask(W, H, 3, 2, 5, 34, 5), (150, 180, 240), 0.5)
        paint(t, 0, 0, rr_mask(W, H, 3, 2, 4, 34, 5), (2, 6, 22))
        if reach > 0:
            half = 1 + reach * 15
            m = rr_mask(W, H, 1.5, 19 - half, 5, 2 * half, 3)
            paint(t, 0, 0, m, gcanvas(H, W, 5, 3, [(170, 230, 255), (40, 120, 240)]))
        rect(t, 18, 1, 2, 2, T.body_label)
    else:
        # Color Balance's cyan-to-red line
        for x in range(3, 35):
            u = (x - 3) / 31
            rect(t, x, 4, 1, 2, lerp((0, 200, 230), (230, 40, 40), u))
        rect(t, 18, 1, 1, 2, (180, 180, 180))
    return t


def slider_thumbs(a, seat):
    for x, sel in ((0, True), (15, False)):
        t = seat[1:12, 20:34].copy()
        W, H = 14, 11
        if FL():
            # FL's fader cap, on the dark slot it slides in
            rect(t, 0, 1, 14, 9, (20, 24, 26))
            rect(t, 0, 1, 14, 1, (10, 12, 13))
            rect(t, 0, 9, 14, 1, (84, 94, 100))
            rbox(t, 3, 0, 8, 11, 1.5, [(196, 204, 208), (120, 128, 132)] if not sel else [(230, 236, 238), (160, 168, 172)],
                 (16, 19, 21))
            rect(t, 4, 5, 6, 1, T.accent if sel else (40, 44, 46))
        elif RP():
            st = [lerp(c, (140, 210, 255), 0.4) for c in T.silver] if sel else T.silver
            sphere(t, 7, 5.5, 10, st, T.silver_rim, gloss=0.6)
        else:
            t[:, :] = T.flat
            rect(t, 0, 3, 14, 1, (30, 30, 30))
            rect(t, 0, 4, 14, 1, (112, 112, 112))
            rect(t, 0, 3, 7, 1, T.accent)
            rect(t, 0, 4, 7, 1, lerp(T.accent, WHITE, 0.3))
            ps_triangle(t, 7, 5, sel)
        a[422:433, x:x + 14] = t


def make_volume(main):
    a = new(68, 433, flat_body())
    seat = main_bg()[57:70, 107:175]
    for i in range(28):
        a[i * 15:i * 15 + 13, 0:68] = volume_frame(seat, (i + 1) / 28)
        a[i * 15 + 13:i * 15 + 15, 0:68] = seat[-2:]
    slider_thumbs(a, main_bg()[57:72, 107:175])
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
    slider_thumbs(a, main_bg()[57:72, 107:175])
    if PS():
        # the balance thumb sits on the colour line, not the blue-filled opacity line
        for x, sel in ((0, True), (15, False)):
            t = new(14, 11, T.flat)
            for c in range(14):
                rect(t, c, 3, 1, 2, lerp((0, 200, 230), (230, 40, 40), (c + 9) / 31))
            ps_triangle(t, 7, 5, sel)
            a[422:433, x:x + 14] = t
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
SLIDER_X = [21] + [78 + 18 * i for i in range(10)]


def eq_titlebar(lit):
    a = bar_frame(275, 14, lit, left_edge=True, right_edge=True)
    if FL():
        title_text(a, "Mixer - Master", 8, 3, lit)
        # FL's window-title arrows at the left of the title, the strip's grip dots to the right
        x = 8 + text_w(UI, "Mixer - Master") + 8
        for gx in range(x, 252, 4):
            px(a, gx, 6, (84, 94, 100) if lit else (64, 70, 74))
            px(a, gx, 8, (84, 94, 100) if lit else (64, 70, 74))
    elif RP():
        tw = text_w(UI, "Graphic Equalizer") + 16
        rp_tab(a, 137 - tw // 2, 1, tw, 12, "Graphic Equalizer", lit, True)
    else:
        rect(a, 1, 1, 273, 12, T.strip if lit else (56, 56, 56))
        rect(a, 1, 13, 273, 1, (40, 40, 40))
        x = 3
        for i, lab in enumerate(["Equalizer", "Adjustments", "Styles"]):
            w = text_w(UI, lab) + 12
            ps_tab(a, x, 2, w, 12, lab, lit, i == 0)
            x += w + 1
        # the panel's flyout menu
        for yy in (5, 7, 9):
            rect(a, 250, yy, 6, 1, (190, 190, 190) if lit else (130, 130, 130))
    caption_button(a, 264, 3, "close", lit)
    return a


def eq_frame_bg():
    a = new(275, 116)
    vfill(a, 0, 14, 275, 102, T.body)
    window_rims(a)
    if FL():
        rect(a, 15, 35, 246, 77, (30, 35, 38))
        for i, x in enumerate(SLIDER_X):
            sx = x - 2
            col = (56, 64, 68) if i % 2 == 0 else (50, 57, 61)
            if i == 0:
                col = (62, 70, 75)
            rect(a, sx, 36, 18, 75, col)
            rect(a, sx, 36, 18, 1, lerp(col, WHITE, 0.15))
            rect(a, sx, 102, 18, 8, (26, 30, 33))
        rect(a, 42, 36, 33, 75, (50, 57, 61))
    elif RP():
        swoosh(a, 150, 170, 230, 140, 10, 0.30)
        swoosh(a, 100, 175, 260, 150, 2.5, 0.55)
        rbox(a, 15, 35, 246, 77, 5, [(10, 24, 66), (2, 8, 28)], T.pane_edge)
    else:
        rect(a, 2, 15, 271, 1, (100, 100, 100))
        # the tool bar column
        rect(a, 2, 16, 11, 97, T.strip)
        rect(a, 12, 16, 1, 97, (44, 44, 44))
        tools = ["move", "marquee", "lasso", "crop", "eyedrop", "brush", "stamp", "eraser", "gradient", "pen",
                 "type", "path"]
        y = 18
        for name in tools[:10]:
            icon7(a, name, 4, y, (206, 206, 206))
            y += 8 + (1 if name in ("lasso", "eyedrop", "gradient") else 0)
        # foreground / background colour swatches
        rect(a, 6, 103, 6, 6, (24, 24, 24))
        rect(a, 7, 104, 4, 4, WHITE)
        rect(a, 3, 100, 6, 6, (24, 24, 24))
        rect(a, 4, 101, 4, 4, BLACK)
    return a


def eq_slider_frame(bg, n):
    """14x63 for value n of 0..27."""
    a = bg.copy()
    W, H = a.shape[1], a.shape[0]
    v = n / 27
    top = round((1 - v) * 51) + 5
    if FL():
        # the insert's peak meter (left) and the fader's groove (centre)
        rect(a, 1, 2, 4, 59, (14, 16, 18))
        for r in range(3, 60, 2):
            colr = ramp(T.vis_bars, (r - 3) / 57)
            rect(a, 2, r, 2, 1, colr if r >= top else lerp(colr, (14, 16, 18), 0.82))
        rect(a, 8, 3, 2, 57, (12, 14, 15))
        rect(a, 10, 3, 1, 57, (90, 100, 106))
        for yy in (8, 31, 54):
            rect(a, 11, yy, 2, 1, (120, 130, 134))
    elif RP():
        paint(a, 0, 0, rr_mask(W, H, 1.5, 5, 2, 4, 59), lerp(T.pane_edge, BLACK, 0.3))
        paint(a, 0, 0, rr_mask(W, H, 1, 6, 3, 2, 57), (10, 16, 40))
        m = rr_mask(W, H, 1, 6, 3, 2, 57)
        m[:top, :] = 0
        paint(a, 0, 0, m, gcanvas(H, W, 3, 57, T.vis_bars))
        for yy in (8, 31, 54):
            rect(a, 1, yy, 2, 1, T.pane_label)
            rect(a, 11, yy, 2, 1, T.pane_label)
    else:
        rect(a, 4, 3, 1, 57, (30, 30, 30))
        rect(a, 5, 3, 1, 57, (112, 112, 112))
        rect(a, 4, top + 1, 1, 60 - top - 1, T.accent)
        rect(a, 5, top + 1, 1, 60 - top - 1, lerp(T.accent, WHITE, 0.3))
        for yy in (8, 31, 54):
            rect(a, 1, yy, 2, 1, (140, 140, 140))
    return a


def eq_thumb(bg, pressed):
    """11x11, drawn at the slider's x + 1."""
    a = bg.copy()
    W, H = 11, 11
    if FL():
        rbox(a, 0, 2, 11, 7, 1.5, [(206, 214, 218), (120, 128, 132)] if not pressed else [(236, 240, 242), (166, 172, 176)],
             (16, 19, 21))
        rect(a, 1, 5, 9, 1, T.accent if pressed else (36, 40, 42))
    elif RP():
        st = [lerp(c, (140, 210, 255), 0.4) for c in T.silver] if pressed else T.silver
        rbox(a, 0, 2, 11, 7, 3.49, st, T.silver_rim)
        paint(a, 0, 0, rr_mask(W, H, 2, 1.5, 2.5, 8, 2.5), WHITE, 0.6)
    else:
        # the line passes under the thumb: unfilled above its middle, filled below
        a[:, :] = T.flat
        rect(a, 3, 0, 1, 11, (30, 30, 30))
        rect(a, 4, 0, 1, 11, (112, 112, 112))
        rect(a, 3, 6, 1, 5, T.accent)
        rect(a, 4, 6, 1, 5, lerp(T.accent, WHITE, 0.3))
        fill = WHITE if pressed else (214, 214, 214)
        # a left-pointing triangle with its tip at the line
        for c in range(5):
            half = c
            rect(a, 5 + c, 5 - half, 1, 2 * half + 1, (24, 24, 24))
            if 0 < c < 4:
                rect(a, 5 + c, 5 - half + 1, 1, 2 * half - 1, fill)
    return a


def make_eqmain():
    a = new(275, 315, flat_body())
    base = eq_frame_bg()
    a[0:116] = base
    a[0:14] = eq_titlebar(True)
    if FL():
        rect(a, 86, 17, 113, 19, T.pane)
        rect(a, 85, 16, 115, 1, T.pane_edge)
        rect(a, 85, 36, 115, 1, (88, 98, 104))
        fl_knob(a, 58.5, 50, 13, 0.5)
        draw_text(a, TINY, "PAN", 53, 59, T.body_label)
        fl_knob(a, 58.5, 80, 13, 0.78)
        draw_text(a, TINY, "VOL", 53, 89, T.body_label)
    elif RP():
        lcd(a, 86, 17, 113, 19)
        for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
            text_center(a, TINY, lbl, 58, yy, T.pane_label)
    else:
        lcd(a, 86, 17, 113, 19)
        for lbl, yy in (("+12", 41), ("0", 66), ("-12", 92)):
            text_center(a, TINY, lbl, 58, yy, T.pane_label)
    seat = a[38:101, 21:35].copy()
    for i, x in enumerate(SLIDER_X):
        a[38:101, x:x + 14] = eq_slider_frame(a[38:101, x:x + 14], 14)
    lab_y = 104
    labcol = (210, 216, 218) if FL() else T.pane_label
    text_center(a, TINY, "PRE", 28, lab_y, labcol)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, lab_y, labcol)
    for x, w, lbl in ((14, 26, "ON"), (40, 32, "AUTO")):
        a[18:30, x:x + w] = toggle_cell(base[18:30, x:x + w], w, 12, lbl, False, False)
    a[18:30, 217:261] = toggle_cell(base[18:30, 217:261], 44, 12, "PRESETS", False, False, led=False)

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
    tseat = base[38:101, 22:33]
    a[164:175, 0:11] = eq_thumb(tseat[2:13], False)
    a[176:187, 0:11] = eq_thumb(tseat[2:13], True)
    for n in range(28):
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = eq_slider_frame(seat, n)
    for y, pressed in ((164, False), (176, True)):
        a[y:y + 12, 224:268] = toggle_cell(base[18:30, 217:261], 44, 12, "PRESETS", False, pressed, led=False)
    # graph background (FL: the parametric EQ's grid; Photoshop: the Curves grid)
    rect(a, 0, 294, 113, 19, T.pane)
    if PS():
        for x in (28, 56, 84):
            rect(a, x, 294, 1, 19, (62, 62, 62))
        for y in (4, 9, 14):
            rect(a, 0, 294 + y, 113, 1, (62, 62, 62))
    else:
        for x in range(0, 113, 12):
            for y in range(1, 19, 2):
                px(a, 2 + x, 294 + y, T.vis_dots)
        for x in range(0, 113, 2):
            px(a, x, 294 + 9, lerp(T.pane, T.pane_label, 0.4))
    curve = {"fl-studio": [(255, 200, 120), T.accent, (220, 110, 40)],
             "realplayer": T.vis_bars[:3], "photoshop": [(240, 240, 240), (220, 220, 220), (200, 200, 200)]}[T.name]
    for r in range(19):
        px(a, 115, 294 + r, ramp(curve, r / 18))
    for x in range(113):
        px(a, x, 314, lerp(T.pane, T.pane_label, 0.8) if x % 3 != 2 else T.pane)
    return a


def eq_close_pressed():
    bar = bar_frame(275, 14, True, left_edge=True, right_edge=True)
    cell = bar[3:12, 264:273].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    return cell


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109)
# ------------------------------------------------------------------------------------------


def bar20(w, lit, left_edge=False, right_edge=False):
    a = bar_frame(w, 20, lit, left_edge, right_edge)
    if PS():
        rect(a, 0 if not left_edge else 1, 1, w - (1 if left_edge else 0) - (1 if right_edge else 0), 19,
             T.strip if lit else (56, 56, 56))
        rect(a, 0, 19, w, 1, (40, 40, 40))
        if left_edge:
            rect(a, 1, 1, 1, 19, (74, 74, 74))
        if right_edge:
            rect(a, w - 2, 1, 1, 19, (44, 44, 44))
    else:
        rect(a, 0, 19, w, 1, flat_body() if FL() else (2, 6, 24))
    return a


def side_tile(w, h, left):
    t = new(w, h, flat_body())
    if RP():
        vfill(t, 0, 0, w, h, [T.flat, T.flat])
    if left:
        rect(t, 0, 0, 1, h, T.rim)
        rect(t, 1, 0, 1, h, T.hi)
        rect(t, w - 1, 0, 1, h, T.pane_edge if not PS() else (60, 60, 60))
    else:
        rect(t, w - 1, 0, 1, h, T.rim)
        rect(t, w - 2, 0, 1, h, T.lo)
        rect(t, 0, 0, 1, h, T.pane_edge if not PS() else (60, 60, 60))
    return t


def scroll_groove_col():
    return {"fl-studio": (30, 35, 38), "realplayer": (4, 12, 40), "photoshop": (66, 66, 66)}[T.name]


def scroll_handle(pressed):
    t = new(8, 18, scroll_groove_col())
    if FL():
        rbox(t, 0, 0, 8, 18, 1.5, [(150, 158, 162), (100, 108, 112)] if not pressed else [(200, 206, 210), (150, 156, 160)],
             (16, 19, 21))
        for gy in (7, 9, 11):
            rect(t, 2, gy, 4, 1, (60, 66, 70))
    elif RP():
        st = [lerp(c, (140, 210, 255), 0.4) for c in T.silver] if pressed else T.silver
        rbox(t, 0, 0, 8, 18, 3.99, st, T.silver_rim)
        paint(t, 0, 0, rr_mask(8, 18, 2.5, 1.5, 1, 3, 16), WHITE, 0.45)
    else:
        rbox(t, 1, 0, 6, 18, 2.99, [(130, 130, 130), (130, 130, 130)] if not pressed else [(160, 160, 160), (160, 160, 160)])
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


def title_piece_pl(lit):
    t = bar20(100, lit)
    if FL():
        title_text(t, "Playlist - Song", 50, 6, lit, centre=True)
    elif RP():
        tw = text_w(UI, "Now Playing") + 16
        rp_tab(t, 50 - tw // 2, 3, tw, 14, "Now Playing", lit, True)
    else:
        x = 0
        for i, lab in enumerate(["Layers", "Channels", "Paths"]):
            w = text_w(UI, lab) + (3 if i else 4)
            ps_tab(t, x, 6, w, 14, lab, lit, i == 0)
            x += w + 1
        assert x <= 100, x
    return t


FL_CLIPS = [(0, 22, (88, 128, 112)), (24, 14, (88, 128, 112)), (40, 30, (128, 104, 150)), (72, 22, (88, 128, 112)),
            (96, 27, (150, 120, 84))]


def fl_clips(t, x0, y0, w, clips):
    """FL playlist pattern clips: coloured blocks with a lighter title strip and note dashes."""
    rect(t, x0, y0, w, 9, (30, 35, 38))
    for cx, cw, col in clips:
        cw = min(cw, w - cx)
        if cw <= 2:
            continue
        x = x0 + cx
        rect(t, x, y0 + 1, cw, 7, lerp(col, BLACK, 0.25))
        rect(t, x, y0 + 1, cw, 2, lerp(col, WHITE, 0.25))
        rect(t, x, y0 + 1, 1, 7, lerp(col, WHITE, 0.4))
        for k in range(cx % 5, cw - 2, 4):
            rect(t, x + 2 + k, y0 + 4 + (k * 7 + cx) % 3, 2, 1, lerp(col, WHITE, 0.6))


def make_pledit():
    a = new(280, 186, flat_body())
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar20(25, lit)
        a[y:y + 20, 0:25] = bar20(25, lit, left_edge=True)
        a[y:y + 20, 26:126] = title_piece_pl(lit)
        t = bar20(25, lit, right_edge=True)
        caption_button(t, 14, 3, "close", lit)
        if PS():
            for yy in (5, 7, 9):
                rect(t, 5, yy, 6, 1, (190, 190, 190) if lit else (130, 130, 130))
        a[y:y + 20, 153:178] = t

    a[42:71, 0:12] = side_tile(12, 29, True)
    t = side_tile(20, 29, False)
    rect(t, 5, 0, 8, 29, scroll_groove_col())
    rect(t, 4, 0, 1, 29, T.pane_edge if not PS() else (60, 60, 60))
    rect(t, 13, 0, 1, 29, T.pane_edge if not PS() else (60, 60, 60))
    a[42:71, 31:51] = t
    bar = bar20(25, True, right_edge=True)
    cell = bar[3:12, 14:23].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = cell
    a[53:71, 52:60] = scroll_handle(False)
    a[53:71, 61:69] = scroll_handle(True)

    def bottom_base(w):
        t = new(w, 38, flat_body())
        if RP():
            vfill(t, 0, 0, w, 38, [(24, 46, 104), (10, 20, 56), (6, 12, 36)])
        rect(t, 0, 0, w, 1, T.pane_edge if not PS() else (60, 60, 60))
        rect(t, 0, 1, w, 1, T.hi)
        rect(t, 0, 36, w, 1, T.lo)
        rect(t, 0, 37, w, 1, T.rim)
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, T.rim)
    rect(t, 1, 1, 1, 36, T.hi)
    rect(t, 0, 0, 12, 1, t[5, 5])
    rect(t, 1, 0, 1, 1, T.hi)
    rect(t, 11, 0, 1, 1, T.pane_edge)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        if PS():
            ps_bottom_button(t, bx, 8, lbl)
        else:
            t[8:26, bx:bx + 22] = toggle_cell(t[8:26, bx:bx + 22], 22, 18, lbl, False, False, led=False)
    if FL():
        fl_clips(t, 14, 27, 109, FL_CLIPS)
    elif PS():
        # the rest of the Layers panel's footer: link and fx
        for dx, dy in ((0, 1), (1, 0), (2, 0), (3, 1), (3, 3), (2, 4), (1, 4), (0, 3)):
            px(t, 4 + dx, 12 + dy, (190, 190, 190))
            px(t, 4 + dx, 16 + dy, (190, 190, 190))
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, T.rim)
    rect(t, 148, 1, 1, 36, T.lo)
    rect(t, 130, 0, 18, 1, t[5, 140])
    rect(t, 130, 0, 1, 1, T.pane_edge)
    lcd(t, 6, 9, 56, 8)
    if FL():
        rect(t, 1, 21, 63, 12, (40, 46, 50))
        rect(t, 1, 21, 63, 1, (28, 32, 35))
        col = T.glyph
    elif RP():
        rbox(t, 1, 21, 63, 12, 6, T.silver, T.silver_rim)
        col = (20, 50, 140)
    else:
        col = T.glyph
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        mini_transport_icon(t, kind, 3 + 10 * k, 22, col)
    lcd(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, T.ink)
    rect(t, 84, 22 + 5, 1, 1, T.ink)
    if PS():
        ps_bottom_button(t, 106, 8, "LIST")
    else:
        t[8:26, 106:128] = toggle_cell(t[8:26, 106:128], 22, 18, "LIST", False, False, led=False)
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 32 - 3 * j
            px(t, gx, gy, T.body_label)
            px(t, gx + 1, gy + 1, BLACK)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    if FL():
        fl_clips(t, 0, 27, 25, [(3, 20, (88, 128, 112))])
    a[0:38, 179:204] = t
    return a


def ps_bottom_button(t, x, y, label):
    """Layers-panel footer icons (new layer, delete, ...) with the playlist's label under them."""
    ink = (206, 206, 206)
    icon = {"ADD": "new", "REM": "trash", "SEL": "marquee", "MISC": "fx", "LIST": "folder"}[label]
    cx = x + 7
    if icon == "new":
        rect(t, cx, y + 1, 7, 8, ink)
        rect(t, cx + 1, y + 2, 5, 6, (83, 83, 83))
        rect(t, cx + 4, y + 1, 3, 3, (83, 83, 83))
        rect(t, cx + 4, y + 1, 1, 3, ink)
        rect(t, cx + 4, y + 3, 3, 1, ink)
    elif icon == "trash":
        rect(t, cx, y + 2, 7, 1, ink)
        rect(t, cx + 2, y + 1, 3, 1, ink)
        rect(t, cx + 1, y + 3, 5, 6, ink)
        for k in (2, 4):
            rect(t, cx + k, y + 4, 1, 4, (83, 83, 83))
    elif icon == "marquee":
        icon7(t, "marquee", cx, y + 1, ink)
    elif icon == "fx":
        draw_text(t, UI, "fx", cx, y + 1, ink)
    elif icon == "folder":
        rect(t, cx, y + 2, 3, 1, ink)
        rect(t, cx, y + 3, 8, 6, ink)
        rect(t, cx + 1, y + 5, 6, 3, (83, 83, 83))
    text_center(t, TINY, label, x + 11, y + 11, (170, 170, 170))


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_bottom(w, grip, left_edge):
    t = new(w, 14, flat_body())
    if RP():
        vfill(t, 0, 0, w, 14, [(14, 28, 72), (6, 12, 36)])
    rect(t, 0, 12, w, 1, T.lo)
    rect(t, 0, 13, w, 1, T.rim)
    rect(t, 0, 0, w, 1, T.pane_edge if not PS() else (60, 60, 60))
    if left_edge:
        rect(t, 0, 0, 1, 14, T.rim)
        rect(t, 1, 1, 1, 12, T.hi)
        rect(t, 0, 0, 11, 1, t[6, 6])
        rect(t, 10, 0, 1, 1, T.pane_edge)
    else:
        rect(t, w - 1, 0, 1, 14, T.rim)
        rect(t, w - 2, 1, 1, 12, T.lo)
        rect(t, w - 8, 0, 7, 1, t[6, w - 5])
        rect(t, w - 9, 0, 1, 1, T.pane_edge)
    if grip:
        for k in range(3):
            for j in range(k + 1):
                gx, gy = w - 5 - 3 * k + 3 * j, 9 - 3 * j
                px(t, gx, gy, T.body_label)
                px(t, gx + 1, gy + 1, BLACK)
    return t


def gen_title_pieces(lit):
    """left_end, centre, right_end: the box the gen window's title letters sit in."""
    l, c, r = bar20(25, lit), bar20(25, lit), bar20(25, lit)
    if RP():
        big = bar20(75, lit)
        stops = T.btn if lit else [lerp(c_, (150, 156, 176), 0.6) for c_ in T.btn]
        # a glossy pill from x 17 (left_end) through the centre to x 7 of right_end
        W, H = 75, 20
        rbox(big, 17, 2, 41, 15, 7, stops, T.btn_rim if lit else (90, 96, 118))
        paint(big, 0, 0, rr_mask(W, H, 5, 19, 3, 37, 6), WHITE, 0.4 if lit else 0.2)
        l = big[:, 0:25].copy()
        mid = big[:, 37:38].copy()
        c = np.repeat(mid, 25, axis=1)
        r = big[:, 50:75].copy()
    elif PS():
        act = T.flat
        rect(l, 20, 3, 5, 17, act)
        rect(l, 20, 3, 5, 1, (110, 110, 110))
        rect(l, 20, 3, 1, 17, (40, 40, 40))
        rect(c, 0, 3, 25, 17, act)
        rect(c, 0, 3, 25, 1, (110, 110, 110))
        rect(r, 0, 3, 5, 17, act)
        rect(r, 0, 3, 5, 1, (110, 110, 110))
        rect(r, 4, 3, 1, 17, (40, 40, 40))
    return l, c, r


def make_gen():
    a = new(194, 109, flat_body())
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, t):
            a[y:y + 20, px0:px0 + 25] = t
        l, c, r = gen_title_pieces(lit)
        piece(0, bar20(25, lit, left_edge=True))
        piece(26, l)
        piece(52, c)
        piece(78, r)
        piece(104, bar20(25, lit))
        t = bar20(25, lit, right_edge=True)
        caption_button(t, 14, 3, "close", lit)
        piece(130, t)

    a[42:56, 0:125] = gen_bottom(125, False, True)
    a[57:71, 0:125] = gen_bottom(125, True, False)
    t = gen_bottom(25, False, False)
    t[:, :] = t[:, 5:6]
    a[72:86, 127:152] = t
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = side_tile(w, h, left)
    bar = bar20(25, True, right_edge=True)
    cell = bar[3:12, 14:23].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = cell

    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        centre = a[(0 if lit else 21) + 4:(0 if lit else 21) + 11, 60].copy()
        if FL():
            col = T.title_lit if lit else T.title_dim
        elif RP():
            col = WHITE if lit else (236, 238, 244)
        else:
            col = (230, 230, 230) if lit else (176, 176, 176)
        x = 1
        for ch in GEN_LETTERS:
            w = glyph_w(FONT5, ch) + 1
            for r in range(7):
                a[y + r, x:x + w] = centre[r]
            draw_text(a, FONT5, ch, x, y + 1, col)
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
    win_txt = T.body_label
    hdr = T.frame[-1] if not RP() else (24, 46, 104)
    hdr_txt = T.title_lit if not RP() else (220, 234, 255)
    btn_txt = T.glyph
    groove = scroll_groove_col()
    thumb = {"fl-studio": (150, 158, 162), "realplayer": (190, 202, 222), "photoshop": (130, 130, 130)}[T.name]
    # itemBG, itemFG, wndBG, buttonFG, wndFG, hilite, selColor, hdrBG, hdrFG, hdrTop, hdrMid, hdrBot,
    # hdrEmpty, sbFG, sbBG, sbInvFG, sbInvBG, sbDead (genex_wacup.py derives the other six)
    return [item_bg, item_fg, win, btn_txt, win_txt, T.accent, sel, hdr, hdr_txt,
            lerp(hdr, WHITE, 0.3), hdr, lerp(hdr, BLACK, 0.5), win,
            thumb, groove, lerp(thumb, WHITE, 0.3), groove, groove]


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
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n", encoding="utf-8") as f:
        f.write(
            f"{T.skin} — a skin in the style of {T.era}.\n"
            f"{T.owner} logo © {T.owner}.\n\n"
            "A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py) from\n"
            f"gradients, shapes and hand-made pixel fonts, apart from the {T.logo_note} in the About spot.\n"
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
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    box = img.crop((111, 22, 265, 36))
    ImageDraw.Draw(box).text((0, 7), state["title"], fill=text_ink(), font=tt_font(11), anchor="lm")
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
             title=f"{T.skin} - a personal skin", bars=bars)
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
            print(f"{k:11s} {t.wsz:18s} {t.era}")
        sys.exit(0)
    for theme in (sys.argv[1:] or list(THEMES)):
        use_theme(theme)
        names = build()
        check_bounds()
        preview()
        print(f"{T.wsz}: {len(names)} files")
