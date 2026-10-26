#!/usr/bin/python3
"""Mac OS: classic Winamp 2.x skins in the style of three Mac OS eras, generated procedurally.

    /usr/bin/python3 -I gen_skin.py                 # every theme
    /usr/bin/python3 -I gen_skin.py aqua macos9     # just these
    /usr/bin/python3 -I gen_skin.py --list

Themes: "macos9" (Mac OS 9 Platinum), "aqua" (Mac OS X 10.0-10.3, pinstripes and gel) and
"snow-leopard" (Mac OS X 10.6, the unified grey toolbar and iTunes 9's light display).

A style homage: every pixel is drawn here from code (gradients, bevels, anti-aliased shapes from
supersampled masks, hand-made pixel fonts), except one small Apple logo in the About spot, read
at generation time from source/logo-apple/logo.svg (rasterised with rsvg-convert) and coloured
per era. Forked from skins/ember/gen_skin.py (same sheets, same layouts, same preview logic).
Each theme writes its sheets into out/<theme>/, zips them flat into Mac-OS-*.wsz and draws
preview-<theme>.png beside this script (the windows assembled from the sprites, 2x).
"""

import os
import subprocess
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py, which finishes each .wsz
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(HERE, "out", "scratch")
LOGO_SVG = os.path.join(HERE, "source", "logo-apple", "logo.svg")
TTF = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SEP = (255, 0, 255)          # gen.bmp letter separators (never shown)

T = None                     # the theme being built
OUT = None

# ------------------------------------------------------------------------------------------
# Colour and canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def shade(c, t):
    return lerp(c, BLACK, t)


def tint(c, t):
    return lerp(c, WHITE, t)


def stops_at(stops, t):
    """Colour at t along [(t, colour), ...]; repeated t's make a hard step."""
    t = max(0.0, min(1.0, t))
    if t <= stops[0][0]:
        return stops[0][1]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t0 <= t <= t1 and t1 > t0:
            return lerp(c0, c1, (t - t0) / (t1 - t0))
    return stops[-1][1]


def ramp(cols, t):
    n = len(cols) - 1
    return stops_at([(i / n, c) for i, c in enumerate(cols)], t)


def vgrad(h, stops, w=1):
    rows = np.array([stops_at(stops, (r + 0.5) / h) for r in range(h)], np.float32)
    return np.broadcast_to(rows[:, None, :], (h, w, 3)).copy()


def new(w, h, col=BLACK):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):y + h, max(0, x):x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def bevel(a, x, y, w, h, tl, br):
    """1px frame: tl along the top and left, br along the bottom and right."""
    rect(a, x, y, w, 1, tl)
    rect(a, x, y, 1, h, tl)
    rect(a, x, y + h - 1, w, 1, br)
    rect(a, x + w - 1, y, 1, h, br)


def frame(a, x, y, w, h, col, corners=True):
    """1px outline; corners=False leaves the four corner pixels alone (a 1px rounding)."""
    k = 0 if corners else 1
    rect(a, x + k, y, w - 2 * k, 1, col)
    rect(a, x + k, y + h - 1, w - 2 * k, 1, col)
    rect(a, x, y + k, 1, h - 2 * k, col)
    rect(a, x + w - 1, y + k, 1, h - 2 * k, col)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


SS = 6


def mask(w, h, fn):
    """Coverage (h, w) in 0..1 of whatever fn(draw, S) draws at S-times scale."""
    im = Image.new("L", (w * SS, h * SS), 0)
    fn(ImageDraw.Draw(im), SS)
    return np.asarray(im.resize((w, h), Image.BOX), dtype=np.float32) / 255.0


def rr_mask(w, h, r, x=0.0, y=0.0, mw=None, mh=None):
    mw = w - x if mw is None else mw
    mh = h - y if mh is None else mh
    r = max(0.0, min(r, mw / 2, mh / 2))

    def fn(d, S):
        d.rounded_rectangle((round(x * S), round(y * S), round((x + mw) * S) - 1, round((y + mh) * S) - 1),
                            radius=round(r * S), fill=255)
    return mask(w, h, fn)


def ellipse_mask(w, h, x, y, ew, eh):
    return mask(w, h, lambda d, S: d.ellipse((round(x * S), round(y * S), round((x + ew) * S) - 1,
                                              round((y + eh) * S) - 1), fill=255))


def paint(a, x, y, m, col, alpha=1.0):
    """Blends colour (a tuple, or an array the mask's size) over a through mask m at (x, y)."""
    h, w = m.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(a.shape[1], x + w), min(a.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    mm = m[y0 - y:y1 - y, x0 - x:x1 - x]
    mm = (mm * alpha if np.ndim(alpha) == 0 else mm * np.asarray(alpha)[y0 - y:y1 - y, x0 - x:x1 - x])[..., None]
    c = np.asarray(col, dtype=np.float32)
    if c.ndim == 3:
        c = np.broadcast_to(c, (h, w, 3))[y0 - y:y1 - y, x0 - x:x1 - x]
    reg = a[y0:y1, x0:x1].astype(np.float32)
    a[y0:y1, x0:x1] = np.round(reg * (1 - mm) + c * mm).astype(np.int32)


# ------------------------------------------------------------------------------------------
# Pixel fonts (all drawn for these skins)
# ------------------------------------------------------------------------------------------


def G(*rows):
    return list(rows)


def cap(*rows):            # 7 rows from the cap line; two blank descender rows
    return list(rows) + ["." * len(rows[0])] * 2


def xh(*rows):             # 5 rows of x-height (rows 2-6)
    b = "." * len(rows[0])
    return [b, b] + list(rows) + [b, b]


def desc(*rows):           # x-height and descender (rows 2-8)
    b = "." * len(rows[0])
    return [b, b] + list(rows)


def up(*rows):             # 6 rows from row 1 (a t)
    b = "." * len(rows[0])
    return [b] + list(rows) + [b, b]


# A Lucida-like regular face (1px stems): caps 7 rows, x-height 5, descenders 2. Aqua and Snow
# Leopard's titles and labels, and the small labels everywhere.
REG = {
    "A": cap("..#..", ".#.#.", ".#.#.", "#...#", "#####", "#...#", "#...#"),
    "B": cap("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": cap(".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": cap("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": cap("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": cap("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": cap(".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": cap("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": cap("#", "#", "#", "#", "#", "#", "#"),
    "J": cap("...#", "...#", "...#", "...#", "...#", "#..#", ".##."),
    "K": cap("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": cap("#...", "#...", "#...", "#...", "#...", "#...", "####"),
    "M": cap("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": cap("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": cap(".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": cap("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": cap(".###.", "#...#", "#...#", "#...#", "#...#", "#..#.", ".##.#"),
    "R": cap("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": cap(".###.", "#...#", "#....", ".###.", "....#", "#...#", ".###."),
    "T": cap("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": cap("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": cap("#...#", "#...#", "#...#", ".#.#.", ".#.#.", ".#.#.", "..#.."),
    "W": cap("#.....#", "#.....#", "#..#..#", "#..#..#", ".#.#.#.", ".#.#.#.", ".#...#."),
    "X": cap("#...#", ".#.#.", ".#.#.", "..#..", ".#.#.", ".#.#.", "#...#"),
    "Y": cap("#...#", ".#.#.", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": cap("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "a": xh(".###.", "....#", ".####", "#...#", ".####"),
    "b": cap("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": xh(".###", "#...", "#...", "#...", ".###"),
    "d": cap("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": xh(".###.", "#...#", "#####", "#....", ".###."),
    "f": cap("..##", ".#..", "###.", ".#..", ".#..", ".#..", ".#.."),
    "g": desc(".####", "#...#", "#...#", "#...#", ".####", "....#", ".###."),
    "h": cap("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": cap("#", ".", "#", "#", "#", "#", "#"),
    "j": G("..#", "...", "..#", "..#", "..#", "..#", "..#", "..#", "##."),
    "k": cap("#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#"),
    "l": cap("#", "#", "#", "#", "#", "#", "#"),
    "m": xh("###.##.", "#..#..#", "#..#..#", "#..#..#", "#..#..#"),
    "n": xh("####.", "#...#", "#...#", "#...#", "#...#"),
    "o": xh(".###.", "#...#", "#...#", "#...#", ".###."),
    "p": desc("####.", "#...#", "#...#", "#...#", "####.", "#....", "#...."),
    "q": desc(".####", "#...#", "#...#", "#...#", ".####", "....#", "....#"),
    "r": xh("#.##", "##..", "#...", "#...", "#..."),
    "s": xh(".###", "#...", ".##.", "...#", "###."),
    "t": up(".#.", "###", ".#.", ".#.", ".#.", "..#"),
    "u": xh("#...#", "#...#", "#...#", "#...#", ".####"),
    "v": xh("#...#", "#...#", ".#.#.", ".#.#.", "..#.."),
    "w": xh("#.....#", "#..#..#", "#..#..#", ".#.#.#.", ".#...#."),
    "x": xh("#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": desc("#...#", "#...#", ".#.#.", ".#.#.", "..#..", ".#...", "#...."),
    "z": xh("####", "..#.", ".#..", "#...", "####"),
    "0": cap(".##.", "#..#", "#..#", "#..#", "#..#", "#..#", ".##."),
    "1": cap(".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"),
    "2": cap(".##.", "#..#", "...#", "..#.", ".#..", "#...", "####"),
    "3": cap("###.", "...#", "...#", ".##.", "...#", "...#", "###."),
    "4": cap("..#.", ".##.", "#.#.", "#.#.", "####", "..#.", "..#."),
    "5": cap("####", "#...", "###.", "...#", "...#", "#..#", ".##."),
    "6": cap(".##.", "#...", "#...", "###.", "#..#", "#..#", ".##."),
    "7": cap("####", "...#", "..#.", "..#.", ".#..", ".#..", ".#.."),
    "8": cap(".##.", "#..#", "#..#", ".##.", "#..#", "#..#", ".##."),
    "9": cap(".##.", "#..#", "#..#", ".###", "...#", "...#", ".##."),
    "+": cap(".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "-": cap("...", "...", "...", "###", "...", "...", "..."),
    ".": cap(".", ".", ".", ".", ".", ".", "#"),
    " ": cap("...", "...", "...", "...", "...", "...", "..."),
}

# A Chicago/Charcoal-like bold face (2px stems, 1px counters): Mac OS 9's titles.
BOLD = {
    "A": cap(".###.", "##.##", "##.##", "#####", "##.##", "##.##", "##.##"),
    "B": cap("####.", "##.##", "##.##", "####.", "##.##", "##.##", "####."),
    "C": cap(".####", "##...", "##...", "##...", "##...", "##...", ".####"),
    "D": cap("####.", "##.##", "##.##", "##.##", "##.##", "##.##", "####."),
    "E": cap("#####", "##...", "##...", "####.", "##...", "##...", "#####"),
    "F": cap("#####", "##...", "##...", "####.", "##...", "##...", "##..."),
    "G": cap(".####", "##...", "##...", "##.##", "##.##", "##.##", ".####"),
    "H": cap("##.##", "##.##", "##.##", "#####", "##.##", "##.##", "##.##"),
    "I": cap("##", "##", "##", "##", "##", "##", "##"),
    "J": cap("...##", "...##", "...##", "...##", "...##", "##.##", ".###."),
    "K": cap("##.##", "##.##", "####.", "###..", "####.", "##.##", "##.##"),
    "L": cap("##...", "##...", "##...", "##...", "##...", "##...", "#####"),
    "M": cap("##...##", "###.###", "#######", "##.#.##", "##...##", "##...##", "##...##"),
    "N": cap("##..##", "###.##", "######", "##.###", "##..##", "##..##", "##..##"),
    "O": cap(".###.", "##.##", "##.##", "##.##", "##.##", "##.##", ".###."),
    "P": cap("####.", "##.##", "##.##", "####.", "##...", "##...", "##..."),
    "Q": cap(".###.", "##.##", "##.##", "##.##", "##.##", ".###.", "...##"),
    "R": cap("####.", "##.##", "##.##", "####.", "##.##", "##.##", "##.##"),
    "S": cap(".####", "##...", "##...", ".###.", "...##", "...##", "####."),
    "T": cap("######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##.."),
    "U": cap("##.##", "##.##", "##.##", "##.##", "##.##", "##.##", ".###."),
    "V": cap("##.##", "##.##", "##.##", "##.##", "##.##", ".###.", "..#.."),
    "W": cap("##...##", "##...##", "##.#.##", "##.#.##", "#######", "###.###", "##...##"),
    "X": cap("##.##", "##.##", ".###.", "..#..", ".###.", "##.##", "##.##"),
    "Y": cap("##..##", "##..##", ".####.", "..##..", "..##..", "..##..", "..##.."),
    "Z": cap("#####", "...##", "..##.", ".##..", "##...", "##...", "#####"),
    "a": xh(".###.", "...##", ".####", "##.##", ".####"),
    "b": cap("##...", "##...", "####.", "##.##", "##.##", "##.##", "####."),
    "c": xh(".####", "##...", "##...", "##...", ".####"),
    "d": cap("...##", "...##", ".####", "##.##", "##.##", "##.##", ".####"),
    "e": xh(".###.", "##.##", "#####", "##...", ".####"),
    "f": cap("..###", ".##..", "####.", ".##..", ".##..", ".##..", ".##.."),
    "g": desc(".####", "##.##", "##.##", "##.##", ".####", "...##", "####."),
    "h": cap("##...", "##...", "####.", "##.##", "##.##", "##.##", "##.##"),
    "i": cap("##", "..", "##", "##", "##", "##", "##"),
    "j": G("..##", "....", "..##", "..##", "..##", "..##", "..##", "..##", "###."),
    "k": cap("##...", "##...", "##.##", "####.", "###..", "####.", "##.##"),
    "l": cap("##", "##", "##", "##", "##", "##", "##"),
    "m": xh("######.", "##.#.##", "##.#.##", "##.#.##", "##.#.##"),
    "n": xh("####.", "##.##", "##.##", "##.##", "##.##"),
    "o": xh(".###.", "##.##", "##.##", "##.##", ".###."),
    "p": desc("####.", "##.##", "##.##", "##.##", "####.", "##...", "##..."),
    "q": desc(".####", "##.##", "##.##", "##.##", ".####", "...##", "...##"),
    "r": xh("##.##", "####.", "##...", "##...", "##..."),
    "s": xh(".####", "##...", ".###.", "...##", "####."),
    "t": up(".##..", "####.", ".##..", ".##..", ".##..", "..##."),
    "u": xh("##.##", "##.##", "##.##", "##.##", ".####"),
    "v": xh("##.##", "##.##", "##.##", ".###.", "..#.."),
    "w": xh("##...##", "##.#.##", "##.#.##", "#######", ".##.##."),
    "x": xh("##.##", ".###.", "..#..", ".###.", "##.##"),
    "y": desc("##.##", "##.##", "##.##", "##.##", ".####", "...##", "####."),
    "z": xh("#####", "..##.", ".##..", "##...", "#####"),
    " ": cap("...", "...", "...", "...", "...", "...", "..."),
}

# 5-row font for text.bmp (Ember's cells).
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

# 3x5 caps for the display's small labels.
TINY = {
    "A": G(".#.", "#.#", "###", "#.#", "#.#"), "B": G("##.", "#.#", "##.", "#.#", "##."),
    "C": G(".##", "#..", "#..", "#..", ".##"), "D": G("##.", "#.#", "#.#", "#.#", "##."),
    "E": G("###", "#..", "##.", "#..", "###"), "H": G("#.#", "#.#", "###", "#.#", "#.#"),
    "I": G("###", ".#.", ".#.", ".#.", "###"), "K": G("#.#", "#.#", "##.", "#.#", "#.#"),
    "M": G("#.#", "###", "###", "#.#", "#.#"), "N": G("##.", "#.#", "#.#", "#.#", "#.#"),
    "O": G(".#.", "#.#", "#.#", "#.#", ".#."), "P": G("##.", "#.#", "##.", "#..", "#.."),
    "R": G("##.", "#.#", "##.", "#.#", "#.#"), "S": G(".##", "#..", ".#.", "..#", "##."),
    "T": G("###", ".#.", ".#.", ".#.", ".#."), "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "Z": G("###", "..#", ".#.", "#..", "###"), " ": G("..", "..", "..", "..", ".."),
}


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1, shadow=None, sh=(0, 1), shadow_alpha=1.0):
    """Draws s with its top row at y; col may be a function of the glyph row."""
    for c in s:
        if c not in font:
            continue
        g = font[c]
        if shadow is not None:
            for r, row in enumerate(g):
                for k, ch in enumerate(row):
                    if ch == "#":
                        X, Y = x + k + sh[0], y + r + sh[1]
                        if 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]:
                            a[Y, X] = lerp(tuple(a[Y, X]), shadow, shadow_alpha)
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col(r) if callable(col) else col)
        x += len(g[0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1, **kw):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, **kw)


def grid(a, rows, x, y, col):
    for r, row in enumerate(rows):
        for k, ch in enumerate(row):
            if ch == "#":
                px(a, x + k, y + r, col)


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    "macos9": dict(
        kind="os9", name="Mac OS 9", wsz="Mac-OS-9.wsz", title="YTMinamp", font="BOLD",
        body=(221, 221, 221), side=(221, 221, 221), edge=(0, 0, 0), hi=WHITE, lo=(153, 153, 153),
        mid=(187, 187, 187), dk=(102, 102, 102),
        disp=WHITE, ink=BLACK, ink_dim=(196, 196, 196), list_edge=(0, 0, 0),
        accent=(102, 102, 204), sel=(204, 204, 255),
        title_lit=BLACK, title_dim=(136, 136, 136), emboss=None,
        prog=[(0, (204, 204, 255)), (0.45, (153, 153, 255)), (1, (102, 102, 204))],
        vis=[(51, 51, 153), (90, 90, 200), (140, 140, 235), (190, 190, 255)], vis_dots=(232, 232, 240),
        osc=(51, 51, 153), peak=BLACK, graph=[(51, 51, 153), (102, 102, 204), (153, 153, 255)],
        pl=dict(normal="#000000", current="#3333CC", normalbg="#FFFFFF", selectedbg="#CCCCFF"),
        desk=(102, 102, 153),
    ),
    "aqua": dict(
        kind="aqua", name="Mac OS X Aqua", wsz="Mac-OS-X-Aqua.wsz", title="YTMinamp", font="REG",
        body=WHITE, stripe=(238, 240, 242), side=(244, 245, 246), edge=(140, 140, 140),
        hi=WHITE, lo=(170, 170, 170), mid=(200, 200, 200), dk=(110, 110, 110),
        disp=(226, 232, 201), ink=(34, 40, 26), ink_dim=(186, 194, 160), rim=(122, 130, 104),
        list_edge=(138, 138, 138), accent=(56, 117, 215), sel=(181, 213, 255),
        title_lit=BLACK, title_dim=(150, 150, 150), emboss=None,
        vis=[(34, 40, 26), (66, 74, 54), (104, 112, 88), (146, 154, 128)], vis_dots=(214, 221, 186),
        osc=(34, 40, 26), peak=(20, 24, 14), graph=[(20, 70, 160), (56, 117, 215), (100, 160, 240)],
        pl=dict(normal="#000000", current="#1C5BC8", normalbg="#FFFFFF", selectedbg="#B5D5FF"),
        desk=(58, 110, 165),
    ),
    "snow-leopard": dict(
        kind="snow", name="Mac OS X Snow Leopard", wsz="Mac-OS-X-Snow-Leopard.wsz", title="YTMinamp",
        font="REG", body=(214, 214, 214), side=(214, 214, 214), edge=(110, 110, 110), hi=(246, 246, 246),
        lo=(150, 150, 150), mid=(190, 190, 190), dk=(90, 90, 90),
        disp=(221, 227, 234), ink=(36, 40, 45), ink_dim=(184, 192, 202), rim=(128, 134, 142),
        list_edge=(140, 140, 140), accent=(56, 110, 205), sel=(194, 214, 242),
        title_lit=(34, 34, 34), title_dim=(140, 140, 140), emboss=(248, 248, 248),
        panel=(219, 225, 232), panel_edge=(160, 168, 178),
        vis=[(36, 42, 52), (66, 76, 92), (104, 116, 134), (146, 158, 176)], vis_dots=(208, 215, 224),
        osc=(36, 42, 52), peak=(20, 24, 30), graph=[(30, 70, 150), (56, 110, 205), (110, 160, 230)],
        pl=dict(normal="#000000", current="#2A5DB0", normalbg="#FFFFFF", selectedbg="#C2D6F2"),
        desk=(70, 76, 86),
    ),
}
THEME_KEYS = list(THEMES)


def K():
    return T["kind"]


# ------------------------------------------------------------------------------------------
# Surfaces
# ------------------------------------------------------------------------------------------


def body_col(win, y):
    """The window body's colour at row y of window win ('main', 'eq', 'pl', 'gen')."""
    if K() == "aqua":
        return T["body"] if y % 2 == 0 else T["stripe"]
    if K() == "snow" and win in ("main", "eq"):
        # the unified toolbar: the gradient carries on under the titlebar, down the window
        return lerp((214, 214, 214), (178, 178, 178), max(0, y - 14) / 101)
    return T["body"]


def fill_body(a, x, y, w, h, win, y0):
    for r in range(h):
        rect(a, x, y + r, w, 1, body_col(win, y0 + r))


def title_col(r, chrome, lit, win):
    t = r / max(1, chrome - 1)
    if K() == "os9":
        return T["body"]
    if K() == "aqua":
        base = lerp((246, 246, 246), (214, 214, 214), t) if lit else lerp((252, 252, 252), (238, 238, 238), t)
        return base if r % 2 == 0 else shade(base, 0.07 if lit else 0.03)
    unified = win in ("main", "eq")
    if lit:
        return lerp((236, 236, 236), (214, 214, 214), t) if unified else lerp((232, 232, 232), (182, 182, 182), t)
    return lerp((246, 246, 246), (226, 226, 226), t) if unified else lerp((244, 244, 244), (216, 216, 216), t)


def ridge_rows(chrome):
    return range(3, 11) if chrome <= 14 else range(3, 13)


def ridges(a, x0, x1, chrome, cut=()):
    """Platinum's engraved titlebar lines, from x0 up to x1, skipping the (start, end) cut-outs."""
    for r in ridge_rows(chrome):
        col = WHITE if (r - 3) % 2 == 0 else (153, 153, 153)
        for x in range(x0, x1):
            if not any(c0 <= x < c1 for c0, c1 in cut):
                a[r, x] = col


def bar(w, h, lit, win, chrome=14, left=False, right=False):
    """A titlebar strip: chrome rows of title, the rest window body; outer edges where asked."""
    a = new(w, h)
    for r in range(h):
        rect(a, 0, r, w, 1, title_col(r, chrome, lit, win) if r < chrome else body_col(win, r))
    if K() == "snow" and lit:
        rect(a, 0, 1, w, 1, (246, 246, 246))
    if K() != "os9" and chrome < h:
        rect(a, 0, chrome - 1, w, 1, (150, 150, 150) if K() == "snow" else (176, 176, 176))
    rect(a, 0, 0, w, 1, T["edge"])
    if K() == "os9":
        rect(a, 0, 1, w, 1, WHITE)
    if left:
        rect(a, 0, 0, 1, h, T["edge"])
        if K() == "os9":
            rect(a, 1, 1, 1, h - 1, WHITE)
    if right:
        rect(a, w - 1, 0, 1, h, T["edge"])
        if K() == "os9":
            rect(a, w - 2, 1, 1, h - 1, T["lo"])
    return a


# ------------------------------------------------------------------------------------------
# Gel (Aqua and Snow Leopard)
# ------------------------------------------------------------------------------------------

GELS = {
    # rim, body stops (top to bottom: under the gloss, middle, the glow at the bottom), gloss
    "blue": ((30, 76, 140), [(0, (40, 104, 190)), (0.5, (61, 143, 216)), (1, (170, 222, 255))], 0.9),
    "blue_dn": ((18, 50, 104), [(0, (24, 74, 156)), (0.5, (36, 106, 186)), (1, (108, 176, 236))], 0.6),
    "clear": ((128, 128, 128), [(0, (200, 200, 200)), (0.5, (222, 222, 222)), (1, (253, 253, 253))], 0.95),
    "graphite": ((112, 116, 124), [(0, (150, 156, 166)), (0.5, (178, 184, 194)), (1, (232, 236, 242))], 0.85),
    "red": ((136, 24, 16), [(0, (190, 36, 26)), (0.5, (220, 62, 46)), (1, (255, 160, 136))], 0.9),
    "red_dn": ((96, 14, 8), [(0, (140, 24, 16)), (0.5, (170, 40, 28)), (1, (220, 110, 90))], 0.6),
    "yellow": ((150, 98, 6), [(0, (214, 144, 14)), (0.5, (238, 180, 36)), (1, (255, 232, 150))], 0.9),
    "yellow_dn": ((110, 70, 4), [(0, (170, 110, 8)), (0.5, (196, 140, 24)), (1, (236, 200, 110))], 0.6),
    "green": ((28, 104, 24), [(0, (36, 140, 36)), (0.5, (64, 172, 56)), (1, (170, 238, 150))], 0.9),
    "green_dn": ((18, 74, 16), [(0, (24, 104, 24)), (0.5, (44, 134, 40)), (1, (120, 200, 104))], 0.6),
    # Snow Leopard: subtler, softer gloss
    "s_red": ((168, 44, 36), [(0, (214, 76, 66)), (0.55, (226, 92, 80)), (1, (246, 170, 156))], 0.6),
    "s_red_dn": ((120, 26, 20), [(0, (160, 44, 36)), (0.55, (178, 58, 48)), (1, (210, 120, 108))], 0.4),
    "s_yellow": ((176, 128, 30), [(0, (226, 170, 52)), (0.55, (236, 190, 70)), (1, (250, 228, 160))], 0.6),
    "s_yellow_dn": ((130, 92, 16), [(0, (184, 132, 30)), (0.55, (200, 150, 44)), (1, (230, 200, 120))], 0.4),
    "s_green": ((60, 130, 40), [(0, (96, 176, 64)), (0.55, (114, 192, 80)), (1, (190, 236, 166))], 0.6),
    "s_green_dn": ((40, 96, 26), [(0, (66, 136, 44)), (0.55, (80, 152, 56)), (1, (146, 200, 120))], 0.4),
    "s_grey": ((150, 150, 150), [(0, (200, 200, 200)), (0.55, (214, 214, 214)), (1, (244, 244, 244))], 0.6),
    "s_grey_dn": ((110, 110, 110), [(0, (160, 160, 160)), (0.55, (176, 176, 176)), (1, (210, 210, 210))], 0.4),
    "s_blue": ((40, 84, 160), [(0, (70, 128, 214)), (0.5, (92, 152, 230)), (1, (176, 214, 250))], 0.65),
    "s_blue_dn": ((26, 60, 124), [(0, (44, 96, 180)), (0.5, (60, 118, 200)), (1, (130, 180, 236))], 0.45),
}


def gel(a, x, y, w, h, name, r=None, gloss=None):
    """An Aqua gel lozenge: dark rim, colour deepest under a white gloss, glowing at the bottom."""
    rim, stops, g = GELS[name]
    g = g if gloss is None else gloss
    r = h / 2 if r is None else r
    xi, yi = int(np.floor(x)), int(np.floor(y))
    fx, fy = x - xi, y - yi
    W, H = int(np.ceil(fx + w)), int(np.ceil(fy + h))
    paint(a, xi, yi, rr_mask(W, H, r, fx, fy, w, h), rim)
    body = vgrad(H, [(fy / H + s * h / H, c) for s, c in stops], W)
    paint(a, xi, yi, rr_mask(W, H, r - 1, fx + 1, fy + 1, w - 2, h - 2), body)
    gh = max(1.5, (h - 2) * 0.48)
    m = rr_mask(W, H, max(0.5, min(r - 1.5, gh / 2)), fx + 1.5, fy + 1, w - 3, gh)
    al = np.array([g * (1 - 0.75 * max(0, min(1, (rr - fy - 1) / gh))) for rr in range(H)], np.float32)[:, None]
    paint(a, xi, yi, m, WHITE, np.broadcast_to(al, m.shape))


def gloss_grey(a, x, y, w, h, pressed, r=3):
    """Snow Leopard's glossy grey push button."""
    rim = (122, 122, 122) if not pressed else (88, 88, 88)
    if pressed:
        stops = [(0, (194, 194, 194)), (0.5, (184, 184, 184)), (0.5, (168, 168, 168)), (1, (190, 190, 190))]
    else:
        stops = [(0, (254, 254, 254)), (0.5, (242, 242, 242)), (0.5, (228, 228, 228)), (1, (248, 248, 248))]
    paint(a, x, y, rr_mask(w, h, r), rim)
    paint(a, x, y, rr_mask(w, h, r - 1, 1, 1, w - 2, h - 2), vgrad(h, [(0, stops[0][1])] + [
        ((1 + s * (h - 2)) / h, c) for s, c in stops] + [(1, stops[-1][1])], w))


# ------------------------------------------------------------------------------------------
# Controls
# ------------------------------------------------------------------------------------------

BLUE_INK = (14, 30, 56)
GREY_INK = (36, 36, 36)


def push(a, x, y, w, h, state="up", r=None, default=False):
    """A push button in this theme; state up/down/on/ondown. Returns (ink, emboss)."""
    down = state in ("down", "ondown")
    on = state in ("on", "ondown")
    if K() == "os9":
        if on:
            face, tl, br = ((176, 176, 232), (120, 120, 190), (226, 226, 255)) if not down else \
                ((150, 150, 214), (100, 100, 170), (200, 200, 240))
        elif down:
            face, tl, br = (160, 160, 160), (110, 110, 110), (200, 200, 200)
        else:
            face, tl, br = T["body"], WHITE, (153, 153, 153)
        rect(a, x + 1, y + 1, w - 2, h - 2, face)
        bevel(a, x + 1, y + 1, w - 2, h - 2, tl, br)
        if not down and not on:
            rect(a, x + 2, y + h - 3, w - 4, 1, (196, 196, 196))
            rect(a, x + w - 3, y + 2, 1, h - 4, (196, 196, 196))
        frame(a, x, y, w, h, (51, 51, 51), corners=False)
        return BLACK, None
    if K() == "aqua":
        if on or (default and not down):
            name = "blue_dn" if down else "blue"
        elif down:
            name = "blue_dn" if default else "blue"
        else:
            name = "clear"
        gel(a, x, y, w, h, name, r)
        return (BLUE_INK if name.startswith("blue") else GREY_INK), None
    gloss_grey(a, x, y, w, h, down, 3 if r is None else r)
    return ((40, 96, 196) if on else (44, 44, 44)), (252, 252, 252)


def tb_button(a, x, y, kind, lit=True, pressed=False):
    """A 9x9 titlebar button: Platinum boxes, or the traffic lights."""
    if K() == "os9":
        if not lit and not pressed:
            return  # Mac OS 9 hides an inactive window's boxes
        rect(a, x, y, 9, 9, T["body"])
        bevel(a, x, y, 9, 9, (119, 119, 119), WHITE)
        frame(a, x + 1, y + 1, 7, 7, BLACK)
        if pressed:
            rect(a, x + 2, y + 2, 5, 5, (119, 119, 119))
            rect(a, x + 2, y + 2, 5, 1, (85, 85, 85))
            rect(a, x + 2, y + 2, 1, 5, (85, 85, 85))
        else:
            rect(a, x + 2, y + 2, 5, 5, (204, 204, 204))
            rect(a, x + 2, y + 2, 5, 1, WHITE)
            rect(a, x + 2, y + 2, 1, 5, WHITE)
            rect(a, x + 2, y + 6, 5, 1, (153, 153, 153))
            rect(a, x + 6, y + 2, 1, 5, (153, 153, 153))
        ink = BLACK
        if kind == "shade":       # the collapse box: a bar across the middle
            rect(a, x + 2, y + 4, 5, 1, ink)
        elif kind == "minimize":
            rect(a, x + 2, y + 6, 5, 1, ink)
        elif kind == "options":
            rect(a, x + 3, y + 4, 3, 1, ink)
            px(a, x + 4, y + 5, ink)
        return
    if K() == "aqua":
        col = {"options": "graphite", "minimize": "yellow", "shade": "green", "close": "red"}[kind]
        if not lit and not pressed:
            col = "graphite" if kind == "options" else "clear"
        elif pressed:
            col = col + "_dn" if col != "graphite" else "blue_dn"
        gloss = None
    else:
        col = {"options": "s_grey", "minimize": "s_yellow", "shade": "s_green", "close": "s_red"}[kind]
        if not lit and not pressed:
            col = "s_grey"
        elif pressed:
            col += "_dn"
        gloss = None
    gel(a, x, y, 9, 9, col, 4.5, gloss)
    if pressed:
        ink = GELS[col][0]
        ink = shade(ink, 0.35)
        cx, cy = x + 4, y + 4
        if kind == "close":
            for d in (-1, 0, 1):
                px(a, cx + d, cy + d, ink)
                px(a, cx + d, cy - d, ink)
        elif kind == "minimize":
            rect(a, cx - 2, cy, 5, 1, ink)
        elif kind == "shade":
            rect(a, cx - 2, cy, 5, 1, ink)
            rect(a, cx, cy - 2, 1, 5, ink)
        else:
            rect(a, cx - 1, cy - 1, 3, 1, ink)
            px(a, cx, cy, ink)


CHECK = ["......#", ".....##", "#...##.", "##.##..", ".###...", "..#....", "......."]


def checkbox(a, x, y, on, pressed):
    """A 9x9 checkbox."""
    if K() == "os9":
        rect(a, x, y, 9, 9, (170, 170, 170) if pressed else WHITE)
        frame(a, x, y, 9, 9, BLACK)
        if not pressed:
            rect(a, x + 1, y + 1, 7, 1, (204, 204, 204))
            rect(a, x + 1, y + 1, 1, 7, (204, 204, 204))
        if on:
            grid(a, CHECK, x + 1, y + 1, BLACK)
        return
    if K() == "aqua":
        gel(a, x, y, 9, 9, ("blue_dn" if pressed else "blue") if on else ("blue" if pressed else "clear"), 2)
        if on:
            grid(a, CHECK, x + 1, y + 1, BLUE_INK)
        return
    if on:
        gel(a, x, y, 9, 9, "s_blue_dn" if pressed else "s_blue", 2)
        grid(a, CHECK, x + 1, y + 1, (20, 30, 50))
    else:
        gloss_grey(a, x, y, 9, 9, pressed, 2)


def tview(a):
    """The transposed view of a: draw a horizontal control into it to get a vertical one."""
    return a.transpose(1, 0, 2)


def groove(a, x, y, w, h, fill=None):
    """A horizontal slider track (rows y..y+h-1); fill = (x0, x1) of it shown as a level."""
    if K() == "os9":
        rect(a, x + 1, y + 1, w - 2, h - 2, (240, 240, 240))
        rect(a, x + 1, y + 1, w - 2, 1, (187, 187, 187))
        frame(a, x, y, w, h, (68, 68, 68), corners=False)
        if fill and fill[1] > fill[0]:
            f0, f1 = max(x + 1, fill[0]), min(x + w - 1, fill[1])
            a[y + 1:y + h - 1, f0:f1] = np.round(vgrad(h - 2, T["prog"], f1 - f0)).astype(np.int32)
            rect(a, f0, y + 1, f1 - f0, 1, (220, 220, 255))
        return
    W = w
    m = rr_mask(W, h, h / 2)
    rim = (134, 134, 134) if K() == "aqua" else (122, 122, 122)
    paint(a, x, y, m, rim)
    inner = rr_mask(W, h, h / 2 - 1, 1, 1, W - 2, h - 2)
    lo, hi = ((188, 188, 188), (244, 244, 244)) if K() == "aqua" else ((172, 172, 172), (228, 228, 228))
    paint(a, x, y, inner, vgrad(h, [(0, lo), (1, hi)], W))
    if fill and fill[1] > fill[0]:
        f0, f1 = fill
        sub = inner.copy()
        sub[:, :max(0, f0 - x)] = 0
        sub[:, max(0, f1 - x):] = 0
        name = "blue" if K() == "aqua" else "s_blue"
        tmp = a[y:y + h, x:x + W].copy()
        gel(tmp, 0, 0, W, h, name, h / 2, 0.55)
        if K() == "aqua":   # the progress bar's barber-pole stripes
            for yy in range(h):
                for xx in range(W):
                    if ((xx + yy) // 3) % 2 == 0:
                        tmp[yy, xx] = lerp(tuple(tmp[yy, xx]), WHITE, 0.16)
        paint(a, x, y, sub, tmp.astype(np.float32))


def knob(a, x, y, w, h, selected, point="down"):
    """A slider thumb filling the box (x, y, w, h): Platinum's pointed thumb or a round gel."""
    if K() == "os9":
        face = (204, 204, 255) if selected else T["body"]
        tip = 3
        body_h = h - tip
        if point == "down":
            for r in range(h):
                k = max(0, r - body_h + 1)
                x0, x1 = x + k, x + w - 1 - k
                if x1 < x0:
                    break
                rect(a, x0, y + r, x1 - x0 + 1, 1, face)
                px(a, x0, y + r, BLACK)
                px(a, x1, y + r, BLACK)
                if r == 0 or r == h - 1:
                    rect(a, x0, y + r, x1 - x0 + 1, 1, BLACK)
                elif r < body_h:
                    px(a, x0 + 1, y + r, WHITE)
                    px(a, x1 - 1, y + r, (136, 136, 136) if not selected else (120, 120, 200))
            rect(a, x + 1, y + 1, w - 2, 1, WHITE)
            gc = (102, 102, 204) if selected else (119, 119, 119)
            cx = x + w // 2
            for gx in (cx - 2, cx, cx + 2):
                rect(a, gx, y + 3, 1, body_h - 4, gc)
            return
        # pointing right (the EQ's vertical sliders)
        t = tview(a)
        knob(t, y, x, h, w, selected, "down")
        return
    name = ("blue_dn" if selected else "blue") if K() == "aqua" else None
    if name:
        gel(a, x, y, w, h, name, min(w, h) / 2)
        return
    # Snow Leopard: a white glossy knob with a grey rim
    rim = (112, 112, 112) if not selected else (84, 84, 84)
    paint(a, int(x), int(y), rr_mask(int(np.ceil(w)), int(np.ceil(h)), min(w, h) / 2), rim)
    top, bot = ((255, 255, 255), (206, 206, 206)) if not selected else ((214, 214, 214), (170, 170, 170))
    W, H = int(np.ceil(w)), int(np.ceil(h))
    paint(a, int(x), int(y), rr_mask(W, H, min(w, h) / 2 - 1, 1, 1, W - 2, H - 2), vgrad(H, [(0, top), (1, bot)], W))
    paint(a, int(x), int(y), rr_mask(W, H, max(0.5, min(w, h) / 2 - 2), 2, 1.2, W - 4, (H - 2) * 0.45), WHITE, 0.6)


def field(a, x, y, w, h):
    """A display window (interior x, y, w, h, flat display colour) with its rim outside."""
    if K() == "os9":
        bevel(a, x - 2, y - 2, w + 4, h + 4, (136, 136, 136), WHITE)
        bevel(a, x - 1, y - 1, w + 2, h + 2, BLACK, (204, 204, 204))
        rect(a, x, y, w, h, T["disp"])
        return
    paint(a, x - 1, y - 1, rr_mask(w + 2, h + 2, 3.5), T["rim"])
    paint(a, x - 1, y - 1, rr_mask(w + 2, h + 2, 2.5, 1, 1, w, h), T["disp"])
    # the inset's shade along the top, and a lighter lip under the bottom
    rect(a, x + 2, y, w - 4, 1, shade(T["disp"], 0.10))
    rect(a, x + 1, y + h + 1, w, 1, lerp(tuple(a[y + h + 1, x + 1]), WHITE, 0.6))


def title_font():
    return BOLD if T["font"] == "BOLD" else REG


def draw_title(a, s, cx, y, lit):
    f = title_font()
    tx = cx - text_w(f, s) // 2
    emb = T["emboss"] if lit else None
    draw_text(a, f, s, tx, y, T["title_lit"] if lit else T["title_dim"], shadow=emb, shadow_alpha=0.85)
    return tx, tx + text_w(f, s)


# ------------------------------------------------------------------------------------------
# The Apple logo (About spot): source/logo-apple/logo.svg, rasterised at build time
# ------------------------------------------------------------------------------------------

_LOGO = {}


def logo_mask(h):
    """Coverage of the logo, h px tall (anti-aliased by box-filtering a large rasterisation)."""
    if h in _LOGO:
        return _LOGO[h]
    big = os.path.join(SCRATCH, f"apple-{h * 16}.png")
    if not os.path.exists(big):
        subprocess.run(["/usr/bin/rsvg-convert", "-h", str(h * 16), LOGO_SVG, "-o", big], check=True)
    im = Image.open(big).convert("RGBA").split()[3]
    bb = im.getbbox()
    im = im.crop(bb)
    w = max(1, round(im.width * h / im.height))
    m = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255.0
    _LOGO[h] = m
    return m


RAINBOW = [(97, 187, 70), (253, 184, 39), (245, 130, 31), (224, 58, 62), (150, 61, 151), (0, 157, 220)]


def apple_emblem(a, x, y, w=13, h=15):
    """The era's Apple: six-colour stripes (Mac OS 9), blue gel (Aqua), glossy graphite (10.6)."""
    m = logo_mask(h - 1)
    mh, mw = m.shape
    ox, oy = x + (w - mw) // 2, y
    if K() == "os9":
        bands = [0, 0.40, 0.52, 0.64, 0.76, 0.88, 1.0]
        cols = np.zeros((mh, mw, 3), np.float32)
        for r in range(mh):
            t = (r + 0.5) / mh
            i = next(k for k in range(6) if t < bands[k + 1])
            cols[r, :] = RAINBOW[i]
        paint(a, ox, oy, m, cols)
        return
    if K() == "aqua":
        paint(a, ox, oy + 1, m, (120, 140, 170), 0.35)
        paint(a, ox, oy, m, vgrad(mh, [(0, (150, 205, 255)), (0.45, (52, 128, 214)), (1, (28, 84, 170))], mw))
        hi = m.copy()
        hi[mh // 2:] = 0
        paint(a, ox, oy, hi, WHITE, 0.25)
        return
    paint(a, ox, oy + 1, m, (250, 250, 250), 0.8)
    paint(a, ox, oy, m, vgrad(mh, [(0, (130, 130, 134)), (0.5, (78, 78, 82)), (1, (44, 44, 48))], mw))


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

BTN_X = {"options": 6, "minimize": 244, "shade": 254, "close": 264}


def window_titlebar(lit, title, win, buttons):
    a = bar(275, 14, lit, win, 14, left=True, right=True)
    f = title_font()
    tw = text_w(f, title)
    tx = (275 - tw) // 2
    if K() == "os9" and lit:
        cut = [(tx - 6, tx + tw + 6)] + [(BTN_X[b] - 2, BTN_X[b] + 11) for b in buttons]
        ridges(a, 3, 272, 14, cut)
    draw_title(a, title, 275 // 2, 3, lit)
    for b in buttons:
        tb_button(a, BTN_X[b], 3, b, lit)
    return a


def main_titlebar(lit):
    return window_titlebar(lit, T["title"], "main", ("options", "minimize", "shade", "close"))


CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters, bg):
    a = bg.copy()
    if K() == "os9":
        rect(a, 0, 0, 8, 43, T["body"])
        bevel(a, 0, 0, 8, 43, WHITE, (136, 136, 136))
    else:
        inner = (246, 246, 246) if K() == "aqua" else (226, 226, 226)
        paint(a, 0, 0, rr_mask(8, 43, 3), T["lo"])
        paint(a, 0, 0, rr_mask(8, 43, 2, 1, 1, 6, 41), inner)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        gy = y + (h - 5) // 2
        if on:
            if K() == "os9":
                rect(a, 1, y, 6, h, T["sel"])
                draw_text(a, TINY, letter, 2, gy, (51, 51, 153))
            else:
                rect(a, 1, y, 6, h, T["accent"])
                draw_text(a, TINY, letter, 2, gy, WHITE)
        else:
            draw_text(a, TINY, letter, 2, gy, (110, 110, 110))
    return a


def make_titlebar(main_plain):
    a = new(344, 87, T["body"])
    lit_bar = main_titlebar(True)
    for kind, x, y in [("options", 0, 0), ("minimize", 9, 0), ("close", 18, 0), ("shade", 0, 18)]:
        for pressed, dx, dy in ((False, 0, 0), (True, 9 if kind == "shade" else 0, 0 if kind == "shade" else 9)):
            b = lit_bar[3:12, BTN_X[kind]:BTN_X[kind] + 9].copy()
            if K() != "os9":
                b = bar(9, 14, True, "main", 14)[3:12].copy()
            tb_button(b, 0, 0, kind, True, pressed)
            a[y + dy:y + dy + 9, x + dx:x + dx + 9] = b
    a[0:14, 27:302] = lit_bar
    a[15:29, 27:302] = main_titlebar(False)
    a[29:43, 27:302] = lit_bar
    a[42:56, 27:302] = main_titlebar(False)
    bg = main_plain[22:65, 10:18]
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


def window_edges(a):
    h, w = a.shape[:2]
    if K() == "os9":
        frame(a, 0, 0, w, h, BLACK)
        rect(a, 1, 1, w - 2, 1, WHITE)
        rect(a, 1, 1, 1, h - 2, WHITE)
        rect(a, 1, h - 2, w - 2, 1, T["lo"])
        rect(a, w - 2, 1, 1, h - 2, T["lo"])
    else:
        frame(a, 0, 0, w, h, T["edge"])


def main_plain():
    """main.bmp's body alone (what sits under every sprite drawn on it)."""
    a = new(275, 116)
    fill_body(a, 0, 0, 275, 116, "main", 0)
    window_edges(a)
    return a


def make_main(plain):
    a = plain.copy()
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("", plain[22:65, 10:18])
    field(a, 21, 20, 84, 42)
    for yy in (30, 34):
        rect(a, 72, yy, 2, 2, T["ink"])
    field(a, 109, 21, 159, 15)
    field(a, 109, 40, 159, 14)
    lab = lerp(T["ink"], T["disp"], 0.3)
    draw_text(a, TINY, "KBPS", 129, 44, lab)
    draw_text(a, TINY, "KHZ", 169, 44, lab)
    apple_emblem(a, 253, 91)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36), shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def tri_right(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        rect(a, x, y + r, half - abs(r - half) + 1, 1, col)


def tri_left(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x + half + 1 - n, y + r, n, 1, col)


def transport_icon(a, kind, x, y, w, h, pressed, ink, emboss=None):
    o = 1 if (pressed and K() == "os9") else 0
    cx, cy = x + w // 2 + o, y + h // 2 + o

    def shape(dy, c):
        if kind == "previous":
            rect(a, cx - 5, cy - 3 + dy, 2, 7, c)
            tri_left(a, cx - 3, cy - 3 + dy, 7, c)
            tri_left(a, cx + 1, cy - 3 + dy, 7, c)
        elif kind == "play":
            tri_right(a, cx - 2, cy - 4 + dy, 9, c)
        elif kind == "pause":
            rect(a, cx - 4, cy - 3 + dy, 3, 7, c)
            rect(a, cx + 1, cy - 3 + dy, 3, 7, c)
        elif kind == "stop":
            rect(a, cx - 3, cy - 3 + dy, 7, 7, c)
        elif kind == "next":
            tri_right(a, cx - 5, cy - 3 + dy, 7, c)
            tri_right(a, cx - 1, cy - 3 + dy, 7, c)
            rect(a, cx + 3, cy - 3 + dy, 2, 7, c)
        elif kind == "eject":
            for r in range(4):
                rect(a, cx - 1 - r, cy - 4 + r + dy, 2 * r + 3, 1, c)
            rect(a, cx - 4, cy + 1 + dy, 9, 2, c)

    if emboss is not None:
        tmp = a.copy()
        shape(1, emboss)
        a[:] = np.round(tmp * 0.3 + a * 0.7).astype(np.int32)
    shape(0, ink)


def make_cbuttons(main):
    a = new(136, 36, T["body"])
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18)]
    r = 5 if K() == "aqua" else 3
    for kind, x, w, h in specs:
        for pressed, y in ((False, 0), (True, 18)):
            a[y:y + h, x:x + w] = main[88:88 + h, 16 + x:16 + x + w]
            cell = a[y:y + h, x:x + w]
            ink, emb = push(cell, 0, 0, w - 1, h, "down" if pressed else "up", r, default=True)
            transport_icon(cell, kind, 0, 0, w - 1, h, pressed, ink, emb)
    for pressed, y in ((False, 0), (True, 16)):
        a[y:y + 16, 114:136] = main[89:105, 136:158]
        cell = a[y:y + 16, 114:136]
        ink, emb = push(cell, 0, 0, 22, 16, "down" if pressed else "up", r, default=True)
        transport_icon(cell, "eject", 0, 0, 22, 16, pressed, ink, emb)
    return a


REPEAT_ICON = ["......#....", ".#########.", "#.....#...#", "#.........#", "#...#.....#", ".#########.",
               "....#......"]
SHUFFLE_ICON = ["........#..", "###...#####", "...#.#..#..", "....#......", "...#.#..#..", "###...#####",
                "........#.."]


def icon(a, rows, x, y, w, h, ink, emboss, pressed):
    o = 1 if (pressed and K() == "os9") else 0
    gx = x + (w - len(rows[0])) // 2 + o
    gy = y + (h - len(rows)) // 2 + o
    if emboss is not None:
        tmp = a.copy()
        grid(tmp, rows, gx, gy + 1, emboss)
        a[:] = np.round(a * 0.3 + tmp * 0.7).astype(np.int32)
    grid(a, rows, gx, gy, ink)


def label(a, s, x, y, w, h, ink, emboss, pressed, font=None):
    font = REG if font is None else font
    o = 1 if (pressed and K() == "os9") else 0
    tw = text_w(font, s)
    tx = x + (w - tw) // 2 + o
    ty = y + (h - 7) // 2 + o
    draw_text(a, font, s, tx, ty, ink, shadow=emboss, shadow_alpha=0.7)


def make_shufrep(main):
    a = new(92, 85, T["body"])
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        st = ("ondown" if pressed else "on") if on else ("down" if pressed else "up")
        a[y:y + 15, 0:28] = main[89:104, 210:238]
        cell = a[y:y + 15, 0:28]
        ink, emb = push(cell, 0, 0, 28, 15, st)
        icon(cell, REPEAT_ICON, 0, 0, 28, 15, ink, emb, pressed)
        a[y:y + 15, 28:75] = main[89:104, 164:211]
        cell = a[y:y + 15, 28:75]
        ink, emb = push(cell, 0, 0, 46, 15, st)
        icon(cell, SHUFFLE_ICON, 0, 0, 46, 15, ink, emb, pressed)
    for x, lab, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        mx = 219 if lab == "EQ" else 242
        for on, y in ((False, 61), (True, 73)):
            st = ("ondown" if pressed else "on") if on else ("down" if pressed else "up")
            a[y:y + 12, x:x + 23] = main[58:70, mx:mx + 23]
            cell = a[y:y + 12, x:x + 23]
            ink, emb = push(cell, 0, 0, 22 if lab == "EQ" else 23, 12, st)
            label(cell, lab, 0, 0, 22 if lab == "EQ" else 23, 12, ink, emb, pressed)
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T["disp"])
    for y, on in ((0, True), (12, False)):
        col = T["ink"] if on else T["ink_dim"]
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 42, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T["disp"])
    ink = T["ink"]
    tri_right(a, 2, 1, 7, ink)
    rect(a, 9 + 2, 1, 2, 7, ink)
    rect(a, 9 + 5, 1, 2, 7, ink)
    rect(a, 18 + 2, 2, 5, 5, ink)
    rect(a, 39 + 1, 3, 1, 3, ink)
    return a


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
    6: ["..####.", ".##....", "##.....", "##.....", "######.", "##...##", "##...##", "##...##", "##...##",
        "##...##", ".#####."],
    7: ["#######", ".....##", ".....##", "....##.", "....##.", "...##..", "...##..", "..##...", "..##...",
        "..##...", "..##..."],
    8: [".#####.", "##...##", "##...##", "##...##", ".#####.", "##...##", "##...##", "##...##", "##...##",
        "##...##", ".#####."],
    9: [".#####.", "##...##", "##...##", "##...##", "##...##", ".######", ".....##", ".....##", ".....##",
        "....##.", ".####.."],
}


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["disp"])
    for n in range(10):
        grid(a, DIGITS[n], 9 * n + 1, 1, T["ink"])
    if ex:
        rect(a, 99 + 2, 6, 5, 2, T["ink"])
    else:
        rect(a, 20, 6, 5, 1, T["ink"])
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
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key, col * 5, row * 6, T["ink"])
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def make_posbar(main):
    a = new(307, 10, T["body"])
    a[0:10, 0:248] = main[72:82, 16:264]
    groove(a, 0, 3, 248, 5)
    for x, sel in ((248, False), (278, True)):
        a[:, x:x + 29] = a[:, 100:129]
        if K() == "os9":
            knob(a, x + 8, 0, 13, 10, sel)
        elif K() == "aqua":
            knob(a, x + 6.5, 0.5, 16, 9, sel)
        else:
            knob(a, x + 9.5, 0, 10, 10, sel)
    return a


def slider_thumbs(a, strip):
    """The two thumbs at y 422 over a 14x11 crop of the track behind them."""
    for x, sel in ((0, True), (15, False)):
        a[422:433, x:x + 14] = strip
        cell = a[422:433, x:x + 14]
        if K() == "os9":
            knob(cell, 2, 0, 11, 11, sel)
        else:
            knob(cell, 1.5, 0, 11, 11, sel)


def make_volume(main):
    a = new(68, 433, T["body"])
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        groove(a, 1, y + 4, 66, 5, fill=(2, 7 + round((i + 1) / 28 * 54)))
    tmp = seat.copy()
    groove(tmp, 1, 4, 66, 5, fill=(2, 34))
    slider_thumbs(a, tmp[1:12, 27:41])
    return a


def make_balance(main):
    a = new(68, 433, T["body"])
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        reach = round(17 * i / 27)
        groove(a, 10, y + 4, 36, 5, fill=(28 - reach, 28 + reach) if i else None)
        if K() == "os9":
            rect(a, 27, y + 2, 2, 2, (102, 102, 102))
    tmp = new(68, 15)
    tmp[:, 9:47] = seat
    groove(tmp, 10, 4, 36, 5)
    slider_thumbs(a, tmp[1:12, 21:35])
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    return window_titlebar(lit, "Equalizer", "eq", ("close",))


def bay_col():
    return {"os9": T["body"], "aqua": (236, 236, 236), "snow": T.get("panel")}[K()]


def eq_bay(a, x, y, w, h):
    if K() == "os9":
        bevel(a, x, y, w, h, (153, 153, 153), WHITE)
        bevel(a, x + 1, y + 1, w - 2, h - 2, WHITE, (153, 153, 153))
        return
    edge = (192, 192, 192) if K() == "aqua" else T["panel_edge"]
    paint(a, x, y, rr_mask(w, h, 4), edge)
    paint(a, x, y, rr_mask(w, h, 3, 1, 1, w - 2, h - 2), bay_col())


def eq_frame_into(a, n):
    """The 14x63 slider slot at value n (0..27) drawn over a (its bay background)."""
    v = n / 27
    centre = round((1 - v) * 51) + 5
    t = tview(a)
    groove(t, 2, 5, 59, 4, fill=(centre, 61))
    tick = (120, 120, 120) if K() == "os9" else (150, 150, 150)
    rect(a, 1, 31, 2, 1, tick)
    rect(a, 11, 31, 2, 1, tick)


def eq_window():
    a = new(275, 116)
    fill_body(a, 0, 0, 275, 116, "eq", 0)
    window_edges(a)
    a[0:14, :] = eq_titlebar(True)
    eq_bay(a, 16, 37, 245, 66)
    field(a, 86, 17, 113, 19)
    lc = (153, 153, 153) if K() == "os9" else (190, 190, 190)
    rect(a, 39, 40, 1, 60, lc)
    rect(a, 40, 40, 1, 60, WHITE)
    dk = (68, 68, 68)
    for lbl, yy in (("+12 dB", 40), ("0 dB", 66), ("-12 dB", 91)):
        text_center(a, REG, lbl, 59, yy, dk)
    text_center(a, REG, "Preamp", 28, 104, dk)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, REG, lbl, 78 + 18 * i + 7, 104, dk)
    return a


def make_eqmain():
    a = new(275, 315, T["body"])
    win = eq_window()
    a[0:116, :] = win
    plain = win.copy()
    for x in [21] + [78 + 18 * i for i in range(10)]:
        cell = a[38:101, x:x + 14]
        eq_frame_into(cell, 14)
    # close pressed
    b = a[3:12, 264:273].copy()
    tb_button(b, 0, 0, "close", True, True)
    a[125:134, 0:9] = b
    # ON / AUTO checkboxes
    for x, lab, on, pressed in [
        (10, "On", False, False), (36, "Auto", False, False), (69, "On", True, False), (95, "Auto", True, False),
        (128, "On", False, True), (154, "Auto", False, True), (187, "On", True, True), (213, "Auto", True, True),
    ]:
        w = 26 if lab == "On" else 32
        wx = 14 if lab == "On" else 40
        a[119:131, x:x + w] = plain[18:30, wx:wx + w]
        cell = a[119:131, x:x + w]
        checkbox(cell, 0, 1, on, pressed)
        draw_text(cell, REG, lab, 11, 2, (20, 20, 20))
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    # slider thumbs over the slot behind them
    slot = plain[38:101, 21:35].copy()
    eq_frame_into(slot, 14)
    ty = round((1 - 14 / 27) * 51)
    for y, sel in ((164, False), (176, True)):
        a[y:y + 11, 0:11] = slot[ty:ty + 11, 1:12]
        cell = a[y:y + 11, 0:11]
        if K() == "os9":
            knob(cell, 0, 1, 11, 9, sel, point="right")
        else:
            knob(cell, 0, 0, 11, 11, sel)
    for n in range(28):
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = plain[38:101, 21:35]
        eq_frame_into(a[y:y + 63, x:x + 14], n)
    for y, pressed in ((164, False), (176, True)):
        a[y:y + 12, 224:268] = plain[18:30, 217:261]
        cell = a[y:y + 12, 224:268]
        ink, emb = push(cell, 0, 0, 44, 12, "down" if pressed else "up")
        label(cell, "Presets", 0, 0, 44, 12, ink, emb, pressed)
    # graph
    rect(a, 0, 294, 113, 19, T["disp"])
    dots = lerp(T["ink_dim"], T["disp"], 0.3)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, dots)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, T["ink_dim"])
    g = T["graph"]
    for r in range(19):
        px(a, 115, 294 + r, ramp([g[0], g[1], g[2], g[1], g[0]], r / 18))
    for x in range(113):
        px(a, x, 314, T["ink_dim"] if x % 3 != 2 else T["disp"])
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

CHROME = 16      # a 20px bar's title rows; the rest is the frame's body above the list


def bar20(w, lit, win, left=False, right=False, ridge=None, cut=()):
    """A 20px bar; ridge = (x0, x1) of Platinum's lines when lit."""
    a = bar(w, 20, lit, win, CHROME, left, right)
    if K() == "os9" and lit and ridge:
        ridges(a, ridge[0], ridge[1], CHROME, cut)
    return a


def side_fill(a, x, y, w, h):
    col = T["side"]
    rect(a, x, y, w, h, col)


def bottom_base(w, h):
    t = new(w, h)
    if K() == "snow":
        for r in range(h):
            rect(t, 0, r, w, 1, lerp((214, 214, 214), (176, 176, 176), r / max(1, h - 1)))
        rect(t, 0, 0, w, 1, (240, 240, 240))
    else:
        fill_body(t, 0, 0, w, h, "pl", 0)
    rect(t, 0, h - 1, w, 1, T["edge"])
    if K() == "os9":
        rect(t, 0, h - 2, w, 1, T["lo"])
    return t


def track(a, x, y, h, top=False, bottom=False):
    """The playlist's scrollbar track, 10 wide (its 8px interior takes the thumb)."""
    if K() == "os9":
        rect(a, x, y, 1, h, BLACK)
        rect(a, x + 9, y, 1, h, BLACK)
        rect(a, x + 1, y, 8, h, (187, 187, 187))
        rect(a, x + 1, y, 1, h, (153, 153, 153))
        if top:
            rect(a, x, y, 10, 1, BLACK)
            rect(a, x + 1, y + 1, 8, 1, (153, 153, 153))
        if bottom:
            rect(a, x, y + h - 1, 10, 1, BLACK)
        return
    rim = (166, 166, 166) if K() == "aqua" else (150, 150, 150)
    cols = [(206, 206, 206), (226, 226, 226), (244, 244, 244), (250, 250, 250), (250, 250, 250),
            (246, 246, 246), (238, 238, 238), (226, 226, 226)] if K() == "aqua" else \
        [(196, 196, 196), (212, 212, 212), (226, 226, 226), (234, 234, 234), (236, 236, 236),
         (232, 232, 232), (224, 224, 224), (214, 214, 214)]
    pt, pb = (0 if top else 6), (0 if bottom else 6)
    H = h + pt + pb
    big = np.zeros((H, 10, 3), np.int32)
    big[pt:pt + h] = a[y:y + h, x:x + 10]
    big[:pt] = a[y:y + 1, x:x + 10]
    big[pt + h:] = a[y + h - 1:y + h, x:x + 10]
    oy = pt
    paint(big, 0, 0, rr_mask(10, H, 5), rim)
    inner = rr_mask(10, H, 4, 1, 1, 8, H - 2)
    colgrad = np.broadcast_to(np.array(cols, np.float32)[None, :, :], (H, 8, 3))
    full = np.zeros((H, 10, 3), np.float32)
    full[:, 1:9] = colgrad
    paint(big, 0, 0, inner, full)
    a[y:y + h, x:x + 10] = big[oy:oy + h]


def scroll_thumb(a, x, y, sel):
    """8x18 thumb."""
    if K() == "os9":
        face = (170, 170, 238) if sel else (204, 204, 255)
        rect(a, x, y, 8, 18, face)
        frame(a, x, y, 8, 18, BLACK)
        rect(a, x + 1, y + 1, 6, 1, WHITE)
        rect(a, x + 1, y + 1, 1, 16, WHITE)
        rect(a, x + 6, y + 2, 1, 15, (102, 102, 204))
        rect(a, x + 2, y + 16, 5, 1, (102, 102, 204))
        for gy in (y + 6, y + 8, y + 10):
            rect(a, x + 2, gy, 4, 1, (80, 80, 170))
            rect(a, x + 2, gy + 1, 4, 1, WHITE)
        return
    name = ("blue_dn" if sel else "blue") if K() == "aqua" else ("s_blue_dn" if sel else "s_blue")
    t = tview(a[y:y + 18, x:x + 8])
    gel(t, 0, 0, 18, 8, name, 4)


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


def grow_box(t, x, y):
    """The bottom-right resize corner: Platinum's two squares, or Aqua's diagonal lines."""
    if K() == "os9":
        for (bx, by, s) in ((x, y, 8), (x + 3, y + 3, 8)):
            rect(t, bx, by, s, s, T["body"])
            frame(t, bx, by, s, s, (68, 68, 68))
            rect(t, bx + 1, by + 1, s - 2, 1, WHITE)
            rect(t, bx + 1, by + 1, 1, s - 2, WHITE)
        return
    dark = (140, 140, 140) if K() == "aqua" else (120, 120, 120)
    for d in (3, 6, 9):
        for i in range(d + 1):
            px(t, x + 10 - i, y + 10 - d + i, dark)
            px(t, x + 11 - i, y + 10 - d + i, WHITE)


def make_pledit():
    a = new(280, 186, T["body"])
    le = T["list_edge"]
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit, "pl", ridge=(0, 25))
        rect(t, 0, 19, 25, 1, le)
        a[y:y + 20, 127:152] = t
        t = bar20(25, lit, "pl", left=True, ridge=(3, 25))
        side_fill(t, 1 if K() != "os9" else 2, CHROME, 10 if K() != "os9" else 9, 4)
        rect(t, 11, 19, 14, 1, le)
        a[y:y + 20, 0:25] = t
        t = bar20(100, lit, "pl")
        if K() == "os9":
            pass
        draw_title(t, "Playlist", 50, 4, lit)
        rect(t, 0, 19, 100, 1, le)
        a[y:y + 20, 26:126] = t
        t = bar20(25, lit, "pl", right=True, ridge=(0, 12))
        side_fill(t, 6, CHROME, 18 if K() != "os9" else 17, 4)
        rect(t, 0, 19, 6, 1, le)
        rect(t, 5, 19, 1, 1, le)
        track(t, 9, 17, 3, top=True)
        tb_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    # left side tile
    t = new(12, 29)
    side_fill(t, 0, 0, 12, 29)
    rect(t, 0, 0, 1, 29, T["edge"])
    if K() == "os9":
        rect(t, 1, 0, 1, 29, WHITE)
    rect(t, 11, 0, 1, 29, le)
    a[42:71, 0:12] = t
    # right side tile: the list's edge, the scrollbar's track, the outer edge
    t = new(20, 29)
    side_fill(t, 0, 0, 20, 29)
    rect(t, 0, 0, 1, 29, le)
    rect(t, 19, 0, 1, 29, T["edge"])
    if K() == "os9":
        rect(t, 18, 0, 1, 29, T["lo"])
    track(t, 4, 0, 29)
    a[42:71, 31:51] = t
    # close pressed, scroll thumbs (over the track's interior)
    b = a[3:12, 167:176].copy()
    tb_button(b, 0, 0, "close", True, True)
    a[42:51, 52:61] = b
    for x, sel in ((52, False), (61, True)):
        a[53:71, x:x + 8] = t[0:18, 5:13]
        scroll_thumb(a, x, 53, sel)

    # bottom pieces
    t = bottom_base(125, 38)
    rect(t, 0, 0, 1, 38, T["edge"])
    if K() == "os9":
        rect(t, 1, 0, 1, 37, WHITE)
    rect(t, 11, 0, 114, 1, le)
    for bx, lbl in ((14, "Add"), (43, "Rem"), (72, "Sel"), (101, "Misc")):
        cell = t[8:26, bx:bx + 22]
        ink, emb = push(cell, 0, 0, 22, 18, "up", 6 if K() == "aqua" else None)
        label(cell, lbl, 0, 0, 22, 18, ink, emb, False)
    a[72:110, 0:125] = t

    t = bottom_base(150, 38)
    rect(t, 149, 0, 1, 38, T["edge"])
    if K() == "os9":
        rect(t, 148, 0, 1, 37, T["lo"])
    rect(t, 0, 0, 131, 1, le)
    side_fill(t, 131, 0, 18 if K() != "os9" else 17, 1)
    track(t, 134, 0, 3, bottom=True)
    field(t, 6, 9, 56, 8)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        cell = t[22:32, bx:bx + 10]
        ink, emb = push(cell, 0, 0, 10, 10, "up", 3 if K() == "aqua" else 2)
        mini_transport_icon(cell, kind, 0, 0, ink)
    field(t, 65, 22, 33, 8)
    rect(t, 84, 24, 1, 1, lerp(T["ink"], T["disp"], 0.4))
    rect(t, 84, 27, 1, 1, lerp(T["ink"], T["disp"], 0.4))
    cell = t[8:26, 106:128]
    ink, emb = push(cell, 0, 0, 22, 18, "up", 6 if K() == "aqua" else None)
    label(cell, "List", 0, 0, 22, 18, ink, emb, False)
    grow_box(t, 135, 23)
    a[72:110, 126:276] = t

    t = bottom_base(25, 38)
    rect(t, 0, 0, 25, 1, le)
    a[0:38, 179:204] = t
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_gen():
    a = new(194, 109, T["body"])
    for lit, y in ((True, 0), (False, 21)):
        pieces = [
            (0, bar20(25, lit, "gen", left=True, ridge=(3, 25))),
            (26, bar20(25, lit, "gen", ridge=(0, 20))),
            (52, bar20(25, lit, "gen")),
            (78, bar20(25, lit, "gen", ridge=(5, 25))),
            (104, bar20(25, lit, "gen", ridge=(0, 25))),
            (130, bar20(25, lit, "gen", right=True, ridge=(0, 12))),
        ]
        for x, t in pieces:
            if x == 0:
                side_fill(t, 1 if K() != "os9" else 2, CHROME, 24, 4)
            elif x == 130:
                side_fill(t, 0, CHROME, 24 if K() != "os9" else 23, 4)
                tb_button(t, 14, 3, "close", lit)
            else:
                side_fill(t, 0, CHROME, 25, 4)
            a[y:y + 20, x:x + 25] = t

    def bottom(w, left_edge, right_edge, grip):
        t = bottom_base(w, 14)
        if left_edge:
            rect(t, 0, 0, 1, 14, T["edge"])
            if K() == "os9":
                rect(t, 1, 0, 1, 13, WHITE)
        if right_edge:
            rect(t, w - 1, 0, 1, 14, T["edge"])
            if K() == "os9":
                rect(t, w - 2, 0, 1, 13, T["lo"])
        if grip:
            if K() == "os9":
                grow_box(t, w - 15, 1)
            else:
                grow_box(t, w - 15, 0)
        return t

    a[42:56, 0:125] = bottom(125, True, False, False)
    a[57:71, 0:125] = bottom(125, False, True, True)
    a[72:86, 127:152] = bottom(25, False, False, False)
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        side_fill(t, 0, 0, w, h)
        if outer_left:
            rect(t, 0, 0, 1, h, T["edge"])
            if K() == "os9":
                rect(t, 1, 0, 1, h, WHITE)
        else:
            rect(t, w - 1, 0, 1, h, T["edge"])
            if K() == "os9":
                rect(t, w - 2, 0, 1, h, T["lo"])
        a[42:42 + h, x:x + w] = t
    b = a[3:12, 144:153].copy()
    tb_button(b, 0, 0, "close", True, True)
    a[42:51, 148:157] = b

    # letters: each row starts at x 1, letters in their own cells, 1px separators of x 0's colour
    f = title_font()
    for lit, y, ty in ((True, 88, 0), (False, 96, 21)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(f, c) + 1
            a[y:y + 7, x:x + w] = a[ty + 4:ty + 11, 52:53]
            draw_text(a, f, c, x, y, T["title_lit"] if lit else T["title_dim"])
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------


def hexc(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


def genex_colours():
    k = K()
    if k == "os9":
        return [WHITE, BLACK, (221, 221, 221), BLACK, BLACK, (153, 153, 153), (204, 204, 255), (221, 221, 221),
                BLACK, WHITE, (119, 119, 119), (187, 187, 204), (221, 221, 221), (187, 187, 187), (204, 204, 255),
                (153, 153, 153), (153, 153, 255), (187, 187, 187)]
    if k == "aqua":
        return [WHITE, BLACK, (236, 236, 236), BLACK, BLACK, (190, 190, 190), (181, 213, 255), (242, 242, 242),
                BLACK, WHITE, (160, 160, 160), (181, 213, 255), (236, 236, 236), (228, 228, 228), (61, 143, 216),
                (208, 208, 208), (31, 98, 184), (228, 228, 228)]
    return [WHITE, BLACK, (232, 232, 232), BLACK, (34, 34, 34), (196, 196, 196), (194, 214, 242), (242, 242, 242),
            (51, 51, 51), WHITE, (166, 166, 166), (194, 214, 242), (232, 232, 232), (230, 230, 230), (106, 158, 230),
            (208, 208, 208), (61, 116, 209), (230, 230, 230)]


def make_genex():
    a = new(256, 64, genex_colours()[2])
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    push(a, 0, 1, 47, 15, "up", 4)
    push(a, 0, 16, 47, 15, "down", 4)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    v = T["vis"]
    out = [(T["disp"], "background"), (T["vis_dots"], "dots")]
    for i in range(16):
        out.append((ramp(v, i / 15), f"spectrum {i + 1}" + (" (top)" if i == 0 else "")))
    for i in range(5):
        out.append((lerp(T["osc"], T["disp"], i * 0.15), f"oscilloscope {i + 1}"))
    out.append((T["peak"], "peaks"))
    return out


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    p = T["pl"]
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={p['normal']}\nCurrent={p['current']}\nNormalBG={p['normalbg']}\n"
                f"SelectedBG={p['selectedbg']}\nMbBG={p['normalbg']}\nMbFG={p['normal']}\nFont=Arial\n")
    n = T["name"]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n", encoding="utf-8") as f:
        f.write(
            f"{n} — a skin in the style of {n}, drawn from scratch (apart from the Apple logo in\n"
            "the About spot).\n\n"
            "A classic (Winamp 2.x format) skin, generated by a script (gen_skin.py) from gradients,\n"
            "bevels, anti-aliased shapes and hand-made pixel fonts; no other skin's artwork is used.\n\n"
            "Apple logo © Apple Inc.\n"
        )


# ------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------

SHEETS = {}


def build():
    plain = main_plain()
    main = make_main(plain)
    sheets = {
        "main.bmp": main,
        "titlebar.bmp": make_titlebar(plain),
        "cbuttons.bmp": make_cbuttons(plain),
        "shufrep.bmp": make_shufrep(plain),
        "posbar.bmp": make_posbar(plain),
        "volume.bmp": make_volume(plain),
        "balance.bmp": make_balance(plain),
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
    # genex.bmp completed for real Winamp and WACUP: all 24 colours, readable text, and the
    # standard 112x59 button and scrollbar layout (skins/genex_wacup.py).
    genex_wacup.process(os.path.join(HERE, T["wsz"]))
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


def ttf(size=11):
    try:
        return ImageFont.truetype(TTF, size)
    except OSError:
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
    for name, x0, on in (("eq", 0, state["eq"]), ("pl", 23, state["pl"])):
        sx = x0 + (46 if state["pressed"] == name else 0)
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
    # the title box blanked with text.bmp's space, then the title in TrueType in text.bmp's ink
    for x in range(0, 154, 5):
        blit(img, S["text"], (150, 0, min(5, 154 - x), 6), 111 + x, 24)
    d = ImageDraw.Draw(img)
    d.text((111, 24 + 3 + 2), state["title"], fill=T["ink"], font=ttf(11), anchor="lm")
    img.paste(S["main"].crop((265, 21, 275, 37)), (265, 21))
    draw_bitmap_text(img, "192", 111, 43)
    draw_bitmap_text(img, "44", 156, 43)
    cols = [c for c, _ in viscolor()]
    vis = Image.new("RGB", (76, 16))
    vp = vis.load()
    for y in range(16):
        for x in range(76):
            vp[x, y] = cols[1] if (y % 2 == 1 and x % 2 == 0) else cols[0]
    for x in range(75):
        if x % 4 == 3:
            continue
        hgt = state["bars"][x // 4] - 2
        for y in range(16 - hgt, 16):
            vp[x, y] = cols[min(17, max(2, y + 2))]
        pk = state["bars"][x // 4] + 2
        if 0 <= 16 - pk < 16:
            vp[x, 16 - pk] = cols[23]
    img.paste(vis, (24, 43))
    return img


def preview_eq(lit, state):
    sheet = SHEETS["eqmain"]
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
    sheet = SHEETS["pledit"]
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
    p = T["pl"]
    lx, lw = 12, w - 32
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=hexc(p["normalbg"]))
    font = ttf(11)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=hexc(p["selectedbg"]))
        col = hexc(p["current"]) if i == 1 else hexc(p["normal"])
        d.text((lx + 2, y + 8), f"{i + 1}. {txt}", fill=col, font=font, anchor="lm")
        d.text((lx + lw - 3, y + 8), dur, fill=col, font=font, anchor="rm")
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
    col = np.stack([40 + 120 * arr[..., 0], 70 + 110 * arr[..., 0], 110 + 120 * arr[..., 0]], -1)
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("Night Drive - Copper Wire", "4:12"), ("Slow Burn - Lantern Hours", "3:47"),
            ("Kiln - Second Firing", "5:03"), ("Ash & Smoke - Afterglow", "2:58"),
            ("Ember Trio - Coal Seam", "6:21"), ("Field Notes - Warm Static", "3:33"),
            ("Tinder - Small Hours", "4:40"), ("The Forge - Bellows", "3:09"),
            ("Hearth - Long Winter", "5:51"), ("Glowworm - Low Light", "4:05"),
            ("Foundry - Pour", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=f"{T['name']} - a style homage", bars=bars)
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
    out = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), T["desk"])
    out.paste(cols[0], (gap, gap))
    out.paste(cols[1], (275 + 2 * gap, gap))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, f"preview-{T['key']}.png"))


def check_sheets():
    """Sizes and the app's own reads: gen.bmp's letter rows, text.bmp's plain space cell."""
    sizes = {"main": (275, 116), "titlebar": (344, 87), "cbuttons": (136, 36), "shufrep": (92, 85),
             "posbar": (307, 10), "volume": (68, 433), "balance": (68, 433), "monoster": (56, 24),
             "playpaus": (48, 9), "numbers": (99, 13), "nums_ex": (108, 13), "text": (155, 18),
             "pledit": (280, 186), "eqmain": (275, 315), "gen": (194, 109), "genex": (256, 64)}
    for k, s in sizes.items():
        assert SHEETS[k].size == s and SHEETS[k].mode == "RGB", (k, SHEETS[k].size)
    gen_letters()
    sp = np.asarray(SHEETS["text"].crop((150, 0, 155, 6)))
    assert (sp == np.array(T["disp"])).all(), "text.bmp's space cell must be plain display colour"


def run(key):
    global T, OUT
    T = dict(THEMES[key], key=key)
    OUT = os.path.join(HERE, "out", key)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    names = build()
    check_sheets()
    preview()
    print(f"{key}: {T['wsz']} ({len(names)} files), preview-{key}.png")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        print("\n".join(THEME_KEYS))
        sys.exit(0)
    keys = []
    for a in args:
        if a not in THEMES:
            sys.exit(f"unknown theme {a!r}; try --list")
        keys.append(a)
    for k in keys or THEME_KEYS:
        run(k)
