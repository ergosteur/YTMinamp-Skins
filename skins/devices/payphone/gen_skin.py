#!/usr/bin/python3
"""Payphone skins: classic Winamp 2.x skins styled after the Nortel Millennium payphone.

Based on skins/ember/gen_skin.py (same sheet layouts and preview). Drawn here: a satin-silver
faceplate on a black body, the royal-blue top band, a teal dot-matrix VFD with ghost cells, silver
soft keys, chrome keypad keys, blue printed card tabs and an instruction-card EQ. The Bell mark in
the main titlebar is the real one, read from source/bell-logo-2000s.png at generation time.

    /usr/bin/python3 -I gen_skin.py            # every theme
    /usr/bin/python3 -I gen_skin.py <theme>    # some
    /usr/bin/python3 -I gen_skin.py --list
"""

import os
import sys
import zipfile
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    "millennium-bell": SimpleNamespace(
        name="millennium-bell",
        wsz="Nortel-Millennium-Bell.wsz",
        title="Nortel Millennium (Bell)",
    ),
}
T = None
OUT = None


def use_theme(name):
    global T, OUT
    T = THEMES[name]
    OUT = os.path.join(HERE, "out", name)
    os.makedirs(OUT, exist_ok=True)
    global _rng
    _rng = np.random.default_rng(2006)


# ------------------------------------------------------------------------------------------
# Palette
# ------------------------------------------------------------------------------------------

BODY = (20, 21, 24)            # the black housing
BODY_HI = (58, 60, 66)
BODY_LO = (4, 4, 6)

SILVER_TOP = (214, 217, 220)   # satin faceplate, lit from above
SILVER_BOT = (170, 174, 179)
SILVER_HI = (240, 242, 244)
SILVER_LO = (112, 116, 122)
SILVER_DK = (78, 81, 86)

BAND = [(52, 88, 200), (30, 62, 172), (22, 48, 146)]      # royal-blue top band, top to bottom
BAND_HI = (96, 128, 222)
BAND_LO = (10, 24, 84)
BAND_OFF = [(96, 104, 136), (78, 86, 118), (66, 72, 100)]  # unfocused band

TAB = (12, 78, 150)            # the card's printed blue tabs
TAB_LIGHT = (60, 132, 178)     # the light-blue "Next call" tab
CARD = (246, 246, 240)
CARD_RULE = (196, 200, 208)
NAVY = (20, 40, 92)
RED = (206, 32, 42)            # the card's red 911 row
YELLOW = (246, 198, 44)        # header tabs, coin return
GOLD = (244, 186, 60)          # the Bell ring

VFD_BG = (4, 13, 15)
VFD_GHOST = (15, 34, 36)       # unlit dots: 53 (summed RGB) from VFD_BG, under the ink pick's 96
VFD_INK = (112, 226, 204)
VFD_MID = (62, 150, 134)
VFD_DIM = (30, 76, 70)

KEY_INK = (34, 36, 40)
WHITE = (255, 255, 255)
SEP = (255, 0, 255)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def new(w, h, col=BODY):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        y0, x0 = max(0, y), max(0, x)
        a[y0:y + h, x0:x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def box(a, x, y, w, h, col):
    rect(a, x, y, w, 1, col)
    rect(a, x, y + h - 1, w, 1, col)
    rect(a, x, y, 1, h, col)
    rect(a, x + w - 1, y, 1, h, col)


_rng = np.random.default_rng(2006)


def grain(a, x, y, w, h, amp=2.0):
    """Satin grain: horizontally smeared noise (wraps, so tiles stay seamless)."""
    n = _rng.normal(0, 1, (h, w))
    acc = np.zeros_like(n)
    for d in range(-5, 6):
        acc += np.roll(n, d, axis=1)
    acc /= 3.3
    acc += _rng.normal(0, 0.3, (h, w))
    a[y:y + h, x:x + w] += np.round(acc * amp).astype(np.int32)[:, :, None]


def satin(a, x, y, w, h, top=0, total=116, amp=1.6):
    """The faceplate: a vertical satin gradient by window row (y + top of total), plus grain."""
    for r in range(h):
        t = (top + r) / max(1, total - 1)
        rect(a, x, y + r, w, 1, lerp(SILVER_TOP, SILVER_BOT, t))
    grain(a, x, y, w, h, amp)


def band(a, x, y, w, h, lit=True):
    stops = BAND if lit else BAND_OFF
    for r in range(h):
        rect(a, x, y + r, w, 1, ramp(stops, r / max(1, h - 1)))
    rect(a, x, y, w, 1, BAND_HI if lit else (124, 130, 156))
    rect(a, x, y + h - 1, w, 1, BAND_LO if lit else (46, 50, 70))


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


# ------------------------------------------------------------------------------------------
# Pixel fonts
# ------------------------------------------------------------------------------------------

def G(*rows):
    return list(rows)


# 4x5 glyphs for the VFD's text.bmp cells (and the gen letters).
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
    "…": G("....", "....", "....", "....", "#.#."),
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

# 3x5 print for the faceplate and card labels.
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
    "J": G("..#", "..#", "..#", "#.#", ".#."),
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
    "/": G("..#", "..#", ".#.", "#..", "#.."),
    " ": G("..", "..", "..", "..", ".."),
}
for _c in "0123456789+-.":
    TINY[_c] = FONT5[_c]

# 5x7 dot-matrix digits for numbers.bmp (one lit dot per pixel pair: 9x13 cells).
DOT7 = {
    0: G(".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    1: G("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    2: G(".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    3: G("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    4: G("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    5: G("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    6: G("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    7: G("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    8: G(".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    9: G(".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    "-": G(".....", ".....", ".....", "#####", ".....", ".....", "....."),
    " ": G(".....", ".....", ".....", ".....", ".....", ".....", "....."),
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


def accent(a, x, y, col):
    """An acute accent over a TINY capital at (x, y)."""
    px(a, x + 1, y - 2, col)
    px(a, x + 2, y - 2, col)


def cedilla(a, x, y, col):
    """A cedilla under a TINY C at (x, y)."""
    px(a, x + 1, y + 5, col)
    px(a, x + 1, y + 6, col)


# ------------------------------------------------------------------------------------------
# VFD pieces
# ------------------------------------------------------------------------------------------


def vfd_cell(a, x, y, glyph=None, col=VFD_INK):
    """A 5x6 text cell: glyph area 4x5 at (x+1, y+1) with ghost dots, gap column and row at
    x and y (so a cell's corner pixel stays the plain display colour)."""
    rect(a, x, y, 5, 6, VFD_BG)
    g = FONT5.get(glyph) if glyph else None
    for r in range(5):
        for c in range(4):
            on = g is not None and c < len(g[0]) and g[r][c] == "#"
            px(a, x + 1 + c, y + 1 + r, col if on else VFD_GHOST)


def vfd_cells(a, x0, y, x1):
    """Ghost cells along a row from x0 up to (not including) x1, pitch 5."""
    for x in range(x0, x1, 5):
        for r in range(5):
            for c in range(4):
                if x + 1 + c < x1:
                    px(a, x + 1 + c, y + 1 + r, VFD_GHOST)


def vfd_word(a, s, x, y, col):
    for i, ch in enumerate(s):
        vfd_cell(a, x + 5 * i, y, ch, col)


def dot_digit(a, x, y, key, ghost=True):
    """9x13: a 5x7 matrix of 1px dots on a 2px pitch; strokes bloom between lit neighbours."""
    rect(a, x, y, 9, 13, VFD_BG)
    g = DOT7[key]
    on = [[g[r][c] == "#" for c in range(5)] for r in range(7)]
    bloom = lerp(VFD_BG, VFD_INK, 0.68)
    for r in range(7):
        for c in range(5):
            if on[r][c]:
                px(a, x + 2 * c, y + 2 * r, VFD_INK)
                if c < 4 and on[r][c + 1]:
                    px(a, x + 2 * c + 1, y + 2 * r, bloom)
                if r < 6 and on[r + 1][c]:
                    px(a, x + 2 * c, y + 2 * r + 1, bloom)
            elif ghost:
                px(a, x + 2 * c, y + 2 * r, VFD_GHOST)


# ------------------------------------------------------------------------------------------
# Keys
# ------------------------------------------------------------------------------------------


def soft_key(a, x, y, w, h, pressed=False):
    """A silver soft key (the row under the display): satin face, dark seam round it."""
    for r in range(h):
        t = r / max(1, h - 1)
        if pressed:
            col = lerp((176, 179, 184), (196, 199, 203), t)
        else:
            col = lerp((236, 238, 240), (184, 188, 193), t)
        rect(a, x, y + r, w, 1, col)
    box(a, x, y, w, h, (62, 64, 70))
    if pressed:
        rect(a, x + 1, y + 1, w - 2, 1, (120, 124, 130))
        rect(a, x + 1, y + 1, 1, h - 2, (138, 142, 148))
    else:
        rect(a, x + 1, y + 1, w - 2, 1, SILVER_HI)
        rect(a, x + 1, y + 1, 1, h - 2, (250, 251, 252))
        rect(a, x + 1, y + h - 2, w - 2, 1, (136, 140, 146))
        rect(a, x + w - 2, y + 2, 1, h - 3, (150, 154, 160))
    # rounded corners into the seam
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, (40, 42, 46))


def chrome_key(a, x, y, w, h, pressed=False):
    """A chrome keypad key: mirror gradient, bright top, dark waist, bright lower lip."""
    stops = [(250, 251, 252), (206, 210, 214), (128, 132, 138), (176, 180, 186), (232, 234, 237)]
    if pressed:
        stops = [(170, 174, 180), (150, 154, 160), (110, 114, 120), (150, 154, 160), (196, 200, 204)]
    for r in range(h):
        rect(a, x, y + r, w, 1, ramp(stops, r / max(1, h - 1)))
    box(a, x, y, w, h, (44, 46, 50))
    rect(a, x + 1, y + h - 2, w - 2, 1, (98, 102, 108) if not pressed else (120, 124, 130))
    rect(a, x + w - 2, y + 1, 1, h - 2, (120, 124, 130))
    if not pressed:
        rect(a, x + 1, y + 1, 1, h - 3, WHITE)
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, (24, 25, 28))


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


def tri_down(a, cx, y, w, col):
    for r in range((w + 1) // 2):
        rect(a, cx - (w // 2) + r, y + r, w - 2 * r, 1, col)


def tri_up(a, cx, y, w, col):
    n = (w + 1) // 2
    for r in range(n):
        k = n - 1 - r
        rect(a, cx - (w // 2) + k, y + r, w - 2 * k, 1, col)


def transport_icon(a, kind, cx, cy, ink):
    if kind == "previous":
        rect(a, cx - 6, cy - 3, 2, 7, ink)
        tri_left(a, cx - 4, cy - 3, 7, ink)
        tri_left(a, cx, cy - 3, 7, ink)
    elif kind == "play":
        tri_right(a, cx - 2, cy - 4, 9, ink)
    elif kind == "pause":
        rect(a, cx - 4, cy - 3, 3, 7, ink)
        rect(a, cx + 1, cy - 3, 3, 7, ink)
    elif kind == "stop":
        rect(a, cx - 3, cy - 3, 7, 7, ink)
    elif kind == "next":
        tri_right(a, cx - 5, cy - 3, 7, ink)
        tri_right(a, cx - 1, cy - 3, 7, ink)
        rect(a, cx + 3, cy - 3, 2, 7, ink)
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


def caption_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: a tiny silver soft key on the blue band."""
    soft_key(a, x, y, 9, 9, pressed)
    ink = KEY_INK if lit else (96, 100, 108)
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        tri_down(a, X + 4, Y + 3, 5, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 1, ink)
        rect(a, X + 2, Y + 4, 5, 1, ink)
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, BODY)
    satin(a, 0, 0, 8, 43, 22, 116)
    rect(a, 0, 0, 8, 1, SILVER_LO)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        soft_key(a, 0, y, 8, h, pressed=on)
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2 + (1 if on else 0), gy + (1 if on else 0), TAB if on else KEY_INK)
    return a


# The Bell mark (the real one, from source/)

LOGO_SRC = os.path.join(HERE, "source", "bell-logo-2000s.png")
RING_CROP = (1, 18, 299, 109)    # the gold ring and head profile, in the source
WORD_CROP = (37, 105, 238, 152)  # the word
RING_W, RING_H = 46, 7           # flattened from the source's proportions so the word can be big
WORD_H = 9
_logo_masks = None


def logo_masks():
    """The real Bell mark (2000s), read from source/ at generation time: one coverage mask for the
    gold ring and one for the blue word, separated by colour against the transparent ground. The
    two are scaled separately, as legibility at 14 px needs: the word to 9 px tall at its own
    proportions, the ring smaller and flatter (46 x 7) to sweep over the word's top. Each is
    thickened in the source first (the ring's hairlines would vanish), scaled down with Lanczos
    and given a contrast curve (steeper for the word, so its letters stay crisp)."""
    global _logo_masks
    if _logo_masks is None:
        im = Image.open(LOGO_SRC).convert("RGBA")
        a = np.array(im).astype(np.float64) / 255
        alpha, r, b = a[..., 3], a[..., 0], a[..., 2]
        gold = np.clip(r, 0, 1) * alpha                          # gold (255,187,17): red channel
        word = np.clip((b - 0.067 * r) / 0.667, 0, 1) * alpha    # blue (0,85,170): blue less gold

        def down(m, crop, w, h, grow, lo, gain):
            i = Image.fromarray(np.round(m * 255).astype(np.uint8)).crop(crop)
            i = i.filter(ImageFilter.MaxFilter(grow))
            r_ = np.array(i.resize((w, h), Image.LANCZOS)).astype(np.float64) / 255
            return np.clip((r_ - lo) * gain, 0, 1)

        word_w = round((WORD_CROP[2] - WORD_CROP[0]) * WORD_H / (WORD_CROP[3] - WORD_CROP[1]))
        _logo_masks = (down(gold, RING_CROP, RING_W, RING_H, 9, 0.08, 1.5),
                       down(word, WORD_CROP, word_w, WORD_H, 3, 0.2, 2.0))
    return _logo_masks


def bell_logo_real(a, x, y, lit=True):
    """The mark as on the phone's blue band: the ring in its gold over "Bell" in white. (x, y) is
    the word's top left; the ring sits on rows 0..6 of the bar, the word on 5..13."""
    ring, word = logo_masks()
    ring_col = GOLD if lit else (176, 170, 150)
    word_col = WHITE if lit else (196, 200, 212)
    rx = x + (word.shape[1] - ring.shape[1]) // 2 + 3
    for m, col, mx, my in ((ring, ring_col, rx, 0), (word, word_col, x, y)):
        h, w = m.shape
        sub = a[my:my + h, mx:mx + w].astype(np.float64)
        c = np.array(col, dtype=np.float64)
        a[my:my + h, mx:mx + w] = np.round(sub + (c - sub) * m[:, :, None]).astype(np.int32)


def main_titlebar(lit):
    a = new(275, 14, BODY)
    rect(a, 0, 0, 275, 14, BODY)
    band(a, 2, 0, 271, 14, lit)
    rect(a, 0, 0, 2, 14, BODY)
    rect(a, 273, 0, 2, 14, BODY)
    rect(a, 0, 0, 275, 1, BODY_HI)
    ink = WHITE if lit else (196, 200, 214)
    draw_text(a, TINY, "CARD PHONE ONLY", 19, 2, ink)
    draw_text(a, TINY, "APPAREIL POUR CARTES SEULEMENT", 19, 8, ink)
    bell_logo_real(a, 192, 5, lit=lit)
    caption_button(a, 6, 3, "options", lit)
    caption_button(a, 244, 3, "minimize", lit)
    caption_button(a, 254, 3, "shade", lit)
    caption_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, BODY)
    for kind, x, y, py_ in [("options", 0, 0, 9), ("minimize", 9, 0, 9), ("close", 18, 0, 9)]:
        b = new(9, 9)
        caption_button(b, 0, 0, kind, True)
        a[y:y + 9, x:x + 9] = b
        caption_button(b, 0, 0, kind, True, pressed=True)
        a[py_:py_ + 9, x:x + 9] = b
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
# main.bmp (275 x 116)
# ------------------------------------------------------------------------------------------

VFD = (21, 19, 247, 41)        # x, y, w, h: the display window (y 19..59)
TAB_Y, TAB_H = 61, 9            # the printed tabs under it (y 61..69)


def speaker(a, x, y, col):
    """7x5 speaker glyph."""
    rect(a, x, y + 1, 2, 3, col)
    rect(a, x + 2, y + 1, 1, 3, col)
    rect(a, x + 3, y, 1, 5, col)
    px(a, x + 5, y + 1, col)
    px(a, x + 5, y + 3, col)
    px(a, x + 6, y, col)
    px(a, x + 6, y + 2, col)
    px(a, x + 6, y + 4, col)


def card_tab(a, x, y, w, h, col):
    rect(a, x, y, w, h, col)
    rect(a, x, y, w, 1, lerp(col, WHITE, 0.25))
    rect(a, x, y + h - 1, w, 1, lerp(col, (0, 0, 0), 0.3))


HANDSET = [  # 13 x 15, side view: earpiece and mouthpiece cups facing right
    "..######.....",
    ".#########...",
    ".##########..",
    "..###...###..",
    "..###........",
    "..###........",
    "..###........",
    "..###........",
    "..###........",
    "..###........",
    "..###........",
    "..###...###..",
    ".##########..",
    ".#########...",
    "..######.....",
]


def handset(a, x, y):
    """The About spot: the Millennium's black handset, standing on end."""
    for r, row in enumerate(HANDSET):
        for c, ch in enumerate(row):
            if ch == "#":
                edge = c == 0 or row[c - 1] != "#" or r == 0 or HANDSET[r - 1][c] != "#"
                px(a, x + c, y + r, (70, 72, 80) if edge else (16, 17, 20))


def make_main():
    a = new(275, 116, BODY)
    # the faceplate in the black housing
    satin(a, 2, 14, 271, 96, 14, 116)
    rect(a, 2, 14, 271, 1, SILVER_HI)
    rect(a, 2, 14, 1, 96, (226, 228, 231))
    rect(a, 272, 14, 1, 96, SILVER_LO)
    rect(a, 2, 109, 271, 1, SILVER_LO)
    rect(a, 2, 110, 271, 1, SILVER_DK)
    rect(a, 0, 111, 275, 5, BODY)
    rect(a, 3, 113, 269, 1, (30, 31, 35))
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # the instruction card behind its clear window, the VFD in it
    box(a, 19, 16, 251, 56, SILVER_LO)
    rect(a, 20, 17, 249, 54, CARD)
    rect(a, 20, 17, 249, 1, (222, 224, 226))
    x, y, w, h = VFD
    rect(a, x, y, w, h, VFD_BG)
    rect(a, x - 1, y - 1, w + 2, 1, (2, 4, 6))
    rect(a, x - 1, y - 1, 1, h + 1, (2, 4, 6))
    rect(a, x + w, y - 1, 1, h + 1, (2, 4, 6))
    # left: indicator, time (a ghost cell for the minus), analyzer
    dot_digit(a, 38, 26, " ")
    for dx in (48, 60, 78, 90):
        dot_digit(a, dx, 26, " ")
    for yy in (30, 34):
        px(a, 73, yy, VFD_INK)
    # right: three rows of ghost cells under the title (text.bmp's grid: x 111 + 5k, y 27 +- 6)
    for ry in (21, 27, 33):
        vfd_cells(a, 111, ry, 265)
    # the info row: kbps, KBPS, kHz, KHZ in cells (y 43, text.bmp's row), then mono/stereo
    vfd_cells(a, 111, 43, 211)
    vfd_word(a, "KBPS", 131, 43, VFD_MID)
    vfd_word(a, "KHZ", 171, 43, VFD_MID)

    # the tabs printed under the display: FRANCAIS, VOLUME (then the volume slider's own tab)
    card_tab(a, 21, TAB_Y, 37, TAB_H, TAB)
    draw_text(a, TINY, "FRANCAIS", 24, TAB_Y + 2, WHITE)
    cedilla(a, 32, TAB_Y + 2, WHITE)
    card_tab(a, 60, TAB_Y, 44, TAB_H, TAB)
    speaker(a, 63, TAB_Y + 2, WHITE)
    draw_text(a, TINY, "VOLUME", 73, TAB_Y + 2, WHITE)
    # slider seats (the sliders' frames cover them): VFD to y 59, card at 60, tab from 61
    for sx, sw in ((107, 68), (177, 38)):
        card_tab(a, sx, TAB_Y, sw, TAB_H, TAB)

    # the card slot (seek bar seat)
    slot_seat(a, 16, 72, 248)

    # the soft-key row (transport) and the chrome keys
    rect(a, 14, 86, 147, 22, (150, 154, 160))
    rect(a, 14, 86, 147, 1, SILVER_LO)
    rect(a, 14, 107, 147, 1, SILVER_HI)
    rect(a, 162, 87, 78, 19, (150, 154, 160))
    rect(a, 162, 87, 78, 1, SILVER_LO)
    rect(a, 162, 105, 78, 1, SILVER_HI)
    # print beside the keys
    draw_text(a, TINY, "911", 241, 90, RED)
    handset(a, 253, 91)
    return a


def slot_seat(a, x, y, w):
    """The card reader's slot across the faceplate, rows y..y+9."""
    rect(a, x, y + 1, w, 8, (64, 66, 72))
    rect(a, x, y + 1, w, 1, (40, 42, 46))
    rect(a, x, y + 8, w, 1, (226, 228, 230))
    rect(a, x + 2, y + 3, w - 4, 4, (8, 8, 10))
    rect(a, x + 2, y + 3, w - 4, 1, (0, 0, 0))
    rect(a, x + 2, y + 6, w - 4, 1, (30, 31, 34))


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36): the soft keys
# ------------------------------------------------------------------------------------------


def make_cbuttons():
    a = new(136, 36, BODY)
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18)]
    for kind, x, w, h in specs:
        for pressed, y in ((False, 0), (True, 18)):
            soft_key(a, x, y, w, h, pressed)
            o = 1 if pressed else 0
            transport_icon(a, kind, x + w // 2 + o, y + h // 2 + o - 1, KEY_INK)
    for pressed, y in ((False, 0), (True, 16)):
        soft_key(a, 114, y, 22, 16, pressed)
        o = 1 if pressed else 0
        transport_icon(a, "eject", 114 + 11 + o, y + 8 + o - 1, KEY_INK)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85): chrome keys (shuffle, repeat), card tabs (EQ, PL)
# ------------------------------------------------------------------------------------------


def chrome_toggle(a, x, y, w, h, label, on, pressed):
    chrome_key(a, x, y, w, h, pressed)
    o = 1 if pressed else 0
    text_center(a, TINY, label, x + w // 2 + o, y + 3 + o, (16, 17, 20))
    # an indicator dot strip under the label, lit teal like the display
    lx, lw = x + 5 + o, w - 10
    rect(a, lx - 1, y + 10 + o, lw + 2, 3, (30, 32, 36))
    for k in range(lw):
        px(a, lx + k, y + 11 + o, (VFD_INK if k % 2 == 0 else lerp(VFD_INK, VFD_BG, 0.5)) if on
           else (VFD_GHOST if k % 2 == 0 else VFD_BG))


def tab_toggle(a, x, y, label, on, pressed):
    """23x12 at main (219|242, 58): rows 0-1 VFD, row 2 card, rows 3-11 a light-blue tab."""
    rect(a, x, y, 23, 2, VFD_BG)
    rect(a, x, y + 2, 23, 10, CARD)
    tx, tw = x, 22
    if on:
        col = lerp(TAB_LIGHT, (0, 0, 0), 0.2) if pressed else TAB_LIGHT
        card_tab(a, tx, y + 3, tw, 9, col)
        ink = WHITE
    else:
        col = (214, 222, 232) if pressed else CARD
        rect(a, tx, y + 3, tw, 9, col)
        box(a, tx, y + 3, tw, 9, TAB_LIGHT)
        ink = TAB
    o = 1 if pressed else 0
    text_center(a, TINY, label, tx + tw // 2 + o, y + 5 + o, ink)


def make_shufrep():
    a = new(92, 85, BODY)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        chrome_toggle(a, 0, y, 28, 15, "REPEAT", on, pressed)
        chrome_toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        tab_toggle(a, x, 61, label, False, pressed)
        tab_toggle(a, x, 73, label, True, pressed)
    return a


# ------------------------------------------------------------------------------------------
# monoster, playpaus, numbers, nums_ex, text
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, VFD_BG)
    for y, on in ((0, True), (12, False)):
        col = VFD_INK if on else VFD_DIM
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, VFD_BG)
    # dot-matrix icons: 1px dots on a 2px pitch, as the time digits
    play = ["#....", "###..", "#####", "###..", "#...."]
    pause = ["##.##", "##.##", "##.##", "##.##", "##.##"]
    stop = ["#####", "#####", "#####", "#####", "#####"]
    for cell, pat in ((0, play), (9, pause), (18, stop)):
        for r, row in enumerate(pat):
            for c, ch in enumerate(row):
                px(a, cell + 2 * c, 2 * r, VFD_INK if ch == "#" else VFD_GHOST)
    rect(a, 36, 0, 3, 9, VFD_BG)
    for r in range(0, 9, 2):
        px(a, 37, r, VFD_GHOST)
    for r in range(0, 9, 2):
        px(a, 40, r, VFD_INK)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, VFD_BG)
    for n in range(10):
        dot_digit(a, 9 * n, 0, n)
    dot_digit(a, 90, 0, " ")
    if ex:
        dot_digit(a, 99, 0, "-")
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, VFD_BG)
    for row in range(3):
        for col in range(31):
            vfd_cell(a, col * 5, row * 6)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            vfd_cell(a, col * 5, row * 6, key)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10): the card slot; the thumb is a phone card
# ------------------------------------------------------------------------------------------


def phone_card(a, x, y, w, h, selected):
    """29x10: a blue chip card pushed into the slot, its gold chip and white stripe showing."""
    face = (46, 84, 196) if selected else (30, 62, 172)
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(lerp(face, WHITE, 0.25), face, r / max(1, h - 1)))
    box(a, x, y, w, h, (10, 22, 80))
    rect(a, x + 1, y + 1, w - 2, 1, lerp(face, WHITE, 0.5))
    # rounded corners
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, (64, 66, 72))
    # chip
    rect(a, x + 4, y + 3, 5, 4, (232, 192, 84))
    rect(a, x + 4, y + 3, 5, 1, (252, 226, 140))
    px(a, x + 6, y + 4, (176, 132, 40))
    px(a, x + 6, y + 5, (176, 132, 40))
    rect(a, x + 4, y + 6, 5, 1, (160, 120, 40))
    # the ring, in the card's print
    for dx, dy in [(13, 3), (14, 2), (15, 2), (16, 2), (17, 2), (18, 2), (19, 2), (20, 2), (21, 3),
                   (20, 4), (19, 4), (18, 4), (17, 4), (16, 4), (15, 4), (14, 4)]:
        px(a, x + dx, y + dy, GOLD)
    rect(a, x + 14, y + 6, 8, 1, lerp(face, WHITE, 0.7))
    rect(a, x + 24, y + 1, 1, h - 2, lerp(face, (0, 0, 0), 0.3))


def make_posbar(main):
    a = new(307, 10, BODY)
    a[0:10, 0:248] = main[72:82, 16:264]
    phone_card(a, 248, 0, 29, 10, False)
    phone_card(a, 278, 0, 29, 10, True)
    return a


# ------------------------------------------------------------------------------------------
# volume.bmp / balance.bmp (68 x 433): blue tabs with a VFD bar in them
# ------------------------------------------------------------------------------------------


def slider_thumb(a, x, y, pressed):
    """14x11 at main y 58: rows 0-1 the VFD's foot, row 2 card, rows 3-10 a small soft key."""
    rect(a, x, y, 14, 2, VFD_BG)
    rect(a, x, y + 2, 14, 1, CARD)
    soft_key(a, x, y + 3, 14, 8, pressed)
    o = 1 if pressed else 0
    for gx in (x + 5, x + 7):
        rect(a, gx + o, y + 5 + o, 1, 4, (90, 94, 100))
        rect(a, gx + 1 + o, y + 5 + o, 1, 4, WHITE)


def slider_frame(a, x, y, w):
    """w x 13 at main y 57: rows 0-2 VFD, row 3 card, rows 4-12 the blue tab."""
    rect(a, x, y, w, 3, VFD_BG)
    rect(a, x, y + 3, w, 1, CARD)
    card_tab(a, x, y + 4, w, 9, TAB)
    rect(a, x + 2, y + 6, w - 4, 5, VFD_BG)
    rect(a, x + 2, y + 6, w - 4, 1, (0, 0, 0))


def make_volume(main):
    a = new(68, 433, BODY)
    for i in range(28):
        y = i * 15
        slider_frame(a, 0, y, 68)
        level = (i + 1) / 28
        lit_to = 3 + round(level * 62)
        for x in range(3, 65, 2):
            hgt = 1 + round(2 * (x - 3) / 62)
            col = VFD_INK if x < lit_to else VFD_GHOST
            rect(a, x, y + 10 - hgt, 1, hgt, col)
    for x0, pressed in ((0, True), (15, False)):
        slider_thumb(a, x0, 422, pressed)
    return a


def make_balance(main):
    a = new(68, 433, BODY)
    for i in range(28):
        y = i * 15
        rect(a, 0, y, 68, 15, BODY)
        slider_frame(a, 9, y, 38)
        reach = round(14 * i / 27)
        for x in range(11, 45, 2):
            d = abs(x - 27)
            col = VFD_INK if (d <= reach and i > 0) or d == 0 else VFD_GHOST
            rect(a, x, y + 8, 1, 2, col)
        px(a, 27, y + 7, VFD_INK)
    for x0, pressed in ((0, True), (15, False)):
        slider_thumb(a, x0, 422, pressed)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315): the instruction card
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = new(275, 14, BODY)
    band(a, 2, 0, 271, 14, lit)
    rect(a, 0, 0, 275, 1, BODY_HI)
    ink = WHITE if lit else (196, 200, 214)
    x = draw_text(a, TINY, "EQUALIZER", 19, 5, ink)
    x = draw_text(a, TINY, "/", x + 3, 5, ink)
    accent(a, x + 3, 5, ink)
    draw_text(a, TINY, "EGALISEUR", x + 3, 5, ink)
    rect(a, 150, 6, 88, 1, lerp(BAND[1], WHITE, 0.25) if lit else (110, 116, 140))
    rect(a, 150, 8, 88, 1, lerp(BAND[1], WHITE, 0.25) if lit else (110, 116, 140))
    caption_button(a, 264, 3, "close", lit)
    return a


SLOT_TOP = (214, 218, 224)


def eq_slider_frame(a, x, y, n):
    """14x63 on the white card: a slot filled with Bell blue up to the value (n of 0..27)."""
    rect(a, x, y, 14, 63, CARD)
    rect(a, x + 4, y + 1, 6, 61, (150, 156, 166))
    rect(a, x + 5, y + 2, 4, 59, SLOT_TOP)
    v = n / 27
    centre = round((1 - v) * 51) + 5
    for r in range(2, 61):
        if r >= centre:
            rect(a, x + 5, y + r, 4, 1, ramp([(70, 110, 220), TAB, (16, 40, 120)], (r - 2) / 58))
    rect(a, x + 1, y + 30, 2, 1, RED)
    rect(a, x + 11, y + 30, 2, 1, RED)


def eq_card(a):
    """The card on the EQ body (rows 15..112)."""
    box(a, 5, 15, 265, 98, SILVER_LO)
    rect(a, 6, 16, 263, 96, CARD)
    # header: blue column, yellow tab round the graph, light-blue tab round PRESETS
    card_tab(a, 6, 16, 70, 20, TAB)
    rect(a, 77, 16, 132, 20, YELLOW)
    rect(a, 77, 35, 132, 1, (206, 160, 30))
    tri_down(a, 142, 36, 7, NAVY)
    card_tab(a, 210, 16, 59, 20, TAB_LIGHT)
    # rules between the card's rows (horizontal only; columns as the card prints them)
    for yy in (43, 68, 94):
        rect(a, 76, yy, 193, 1, CARD_RULE)
    rect(a, 39, 37, 1, 66, CARD_RULE)
    rect(a, 75, 37, 1, 76, CARD_RULE)
    rect(a, 6, 104, 263, 1, CARD_RULE)
    # dB labels: +12 in the card's red, the rest in blue
    for lbl, yy, col in (("+12DB", 41, RED), ("0DB", 66, TAB), ("-12DB", 92, TAB)):
        text_center(a, TINY, lbl, 58, yy, col)
    text_center(a, TINY, "PREAMP", 28, 106, NAVY)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, TAB)


def make_eqmain():
    a = new(275, 315, BODY)
    satin(a, 2, 14, 271, 97, 14, 116)
    rect(a, 2, 14, 271, 1, SILVER_HI)
    rect(a, 2, 14, 1, 97, (226, 228, 231))
    rect(a, 272, 14, 1, 97, SILVER_LO)
    rect(a, 2, 110, 271, 1, SILVER_DK)
    rect(a, 0, 111, 275, 5, BODY)
    a[0:14, :] = eq_titlebar(True)
    eq_card(a)
    # graph seat (the graph sprite covers 86,17 113x19)
    rect(a, 85, 16, 115, 21, (2, 4, 6))
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)

    # under the window: buttons
    caption_button(a, 0, 125, "close", True, pressed=True)
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        soft_key(a, x, 119, w, 12, pressed)
        o = 1 if pressed else 0
        rect(a, x + 3 + o, 119 + 4 + o, 3, 3, (30, 32, 36))
        px(a, x + 4 + o, 119 + 5 + o, VFD_INK if on else VFD_GHOST)
        draw_text(a, TINY, label, x + 8 + o + (w - 10 - text_w(TINY, label)) // 2, 119 + 3 + o, KEY_INK)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    for y, pressed in ((164, False), (176, True)):
        rect(a, 0, y, 11, 11, CARD)
        soft_key(a, 0, y, 11, 11, pressed)
        o = 1 if pressed else 0
        rect(a, 2 + o, y + 5 + o, 7, 1, (90, 94, 100))
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        soft_key(a, 224, y, 44, 12, pressed)
        o = 1 if pressed else 0
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 3 + o, KEY_INK)
    # graph: a small VFD with ghost dots
    rect(a, 0, 294, 113, 19, VFD_BG)
    for x in range(0, 113, 2):
        for y in range(0, 19, 2):
            px(a, x, 294 + y, VFD_GHOST)
    for r in range(19):
        px(a, 115, 294 + r, ramp([(170, 250, 230), VFD_INK, (70, 170, 150)], r / 18))
    for x in range(113):
        px(a, x, 314, VFD_MID if x % 2 == 0 else VFD_BG)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the blue band, silver sides, black edges
# ------------------------------------------------------------------------------------------


def bar20(w, lit):
    a = new(w, 20, BODY)
    band(a, 0, 0, w, 18, lit)
    rect(a, 0, 0, w, 1, BODY_HI if lit else (70, 72, 80))
    # the faceplate's top lip under the band
    rect(a, 0, 18, w, 1, SILVER_HI if lit else (200, 202, 206))
    rect(a, 0, 19, w, 1, SILVER_TOP)
    return a


def side_strip(w, h, outer_left):
    """A side tile: black housing at the outer edge, satin faceplate, the card's grey rim inside."""
    t = new(w, h, BODY)
    satin(t, 0, 0, w, h, 40, 116, amp=0)
    for c in range(w):
        d = c if outer_left else w - 1 - c   # distance from the outside
        if d < 2:
            col = BODY if d == 0 else (40, 42, 46)
        elif d == 2:
            col = SILVER_HI if outer_left else SILVER_LO
        else:
            col = lerp(SILVER_TOP, SILVER_BOT, 0.3)
        rect(t, c, 0, 1, h, col)
    return t


def bottom_satin(w, h):
    t = new(w, h, BODY)
    satin(t, 0, 0, w, h - 4, 70, 116)
    rect(t, 0, h - 5, w, 1, SILVER_LO)
    rect(t, 0, h - 4, w, 4, BODY)
    rect(t, 0, h - 2, w, 1, (30, 31, 35))
    rect(t, 0, 0, w, 1, (226, 228, 231))
    return t


def edge_cols(t, left, right):
    h = t.shape[0]
    w = t.shape[1]
    if left:
        rect(t, 0, 0, 1, h, BODY)
        rect(t, 1, 0, 1, h, (40, 42, 46))
        rect(t, 2, 0, 1, h - 5, SILVER_HI)
    if right:
        rect(t, w - 1, 0, 1, h, BODY)
        rect(t, w - 2, 0, 1, h, (40, 42, 46))
        rect(t, w - 3, 0, 1, h - 5, SILVER_LO)


def small_vfd(a, x, y, w, h):
    rect(a, x - 1, y - 1, w + 2, h + 2, (2, 4, 6))
    rect(a, x, y, w, h, VFD_BG)


def make_pledit():
    a = new(280, 186, BODY)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit)
        a[y:y + 20, 127:152] = t
        t = bar20(25, lit)
        rect(t, 0, 0, 2, 18, BODY)
        a[y:y + 20, 0:25] = t
        t = bar20(100, lit)
        ink = WHITE if lit else (196, 200, 214)
        s1 = "PLAYLIST / LISTE"
        text_center(t, TINY, s1, 50, 7, ink)
        a[y:y + 20, 26:126] = t
        t = bar20(25, lit)
        rect(t, 23, 0, 2, 18, BODY)
        caption_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t
    # corners' side columns under the band (rows 18-19) match the side tiles
    for y in (0, 21):
        a[y + 18:y + 20, 0:12] = side_strip(12, 2, True)
        a[y + 18:y + 20, 153 + 5:178] = side_strip(20, 2, False)
    # side tiles: left 12 (card rim at the inner edge), right 20 (scroll groove at 5..12)
    t = side_strip(12, 29, True)
    rect(t, 11, 0, 1, 29, CARD_RULE)
    a[42:71, 0:12] = t
    t = side_strip(20, 29, False)
    rect(t, 0, 0, 1, 29, CARD_RULE)
    rect(t, 4, 0, 10, 29, (150, 154, 160))
    rect(t, 4, 0, 1, 29, SILVER_LO)
    rect(t, 13, 0, 1, 29, SILVER_HI)
    rect(t, 8, 0, 2, 29, (126, 130, 136))
    a[42:71, 31:51] = t
    t = new(9, 9)
    caption_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        soft_key(a, x, 53, 8, 18, sel)
        for gy in (59, 61, 63):
            rect(a, x + 2, gy, 4, 1, (110, 114, 120))

    # bottom pieces (38 tall)
    t = bottom_satin(125, 38)
    edge_cols(t, True, False)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        soft_key(t, bx, 8, 22, 18)
        text_center(t, TINY, lbl, bx + 11, 14, KEY_INK)
    a[72:110, 0:125] = t

    t = bottom_satin(150, 38)
    edge_cols(t, False, True)
    small_vfd(t, 6, 9, 56, 8)
    for x in range(7, 62, 5):
        for r in range(5):
            for c in range(4):
                if x + 1 + c < 62:
                    px(t, x + 1 + c, 10 + 1 + r, VFD_GHOST)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        soft_key(t, bx, 22, 10, 10)
        mini_transport_icon(t, kind, bx, 22, KEY_INK)
    small_vfd(t, 65, 22, 33, 8)
    for x in (66 + 1, 66 + 7, 66 + 12, 66 + 20, 66 + 25):
        for r in range(5):
            for c in range(4):
                px(t, x + 1 + c, 23 + 1 + r, VFD_GHOST)
    px(t, 84, 22 + 2, VFD_INK)
    px(t, 84, 22 + 5, VFD_INK)
    soft_key(t, 106, 8, 22, 18)
    text_center(t, TINY, "LIST", 117, 14, KEY_INK)
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 143 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx, gy, SILVER_LO)
            px(t, gx + 1, gy + 1, SILVER_HI)
    a[72:110, 126:276] = t

    t = bottom_satin(25, 38)
    a[0:38, 179:204] = t
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_gen():
    a = new(194, 109, BODY)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn=None):
            t = bar20(25, lit)
            if fn:
                fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 2, 18, BODY)
            t[18:20, 0:12] = side_strip(12, 2, True)

        def right(t):
            caption_button(t, 14, 3, "close", lit)
            rect(t, 23, 0, 2, 18, BODY)
            t[18:20, 17:25] = side_strip(8, 2, False)

        piece(0, left)
        piece(26)
        piece(52)
        piece(78)
        piece(104)
        piece(130, right)

    def bottom(w, grip, left_edge):
        t = bottom_satin(w, 14)
        edge_cols(t, left_edge, not left_edge)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 6 - 3 * k + 3 * j, 7 - 3 * j
                    px(t, gx, gy, SILVER_LO)
                    px(t, gx + 1, gy + 1, SILVER_HI)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    t = bottom_satin(25, 14)
    a[72:86, 127:152] = t
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = side_strip(w, h, outer_left)
    t = new(9, 9)
    caption_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: white print on the band (cells copy the band's rows 4..10)
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        strip = bar20(194, lit)[4:11]
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            a[y:y + 7, x:x + w] = strip[:, x:x + w]
            draw_text(a, FONT5, c, x, y + 1, WHITE if lit else (196, 200, 214))
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp (the 18 colours; genex_wacup.py completes it)
# ------------------------------------------------------------------------------------------

GENEX_COLOURS = [
    CARD,              # item background
    NAVY,              # item text
    (198, 201, 205),   # window background (satin)
    (20, 22, 26),      # button text
    (16, 18, 22),      # window text
    (140, 144, 150),   # dividers
    (30, 62, 172),     # selection bar
    (30, 62, 172),     # list header background
    (255, 255, 255),   # list header text
    (96, 128, 222),    # header frame light
    (10, 24, 84),      # header frame dark
    (22, 48, 146),     # header frame pressed
    (198, 201, 205),   # header dead area
    (184, 188, 193),   # scrollbar
    (30, 62, 172),     # scrollbar 2
    (150, 154, 160),   # scrollbar pressed
    (22, 48, 146),     # scrollbar pressed 2
    (176, 180, 184),   # scrollbar dead area
]


def make_genex():
    a = new(256, 64, (198, 201, 205))
    for i, c in enumerate(GENEX_COLOURS):
        px(a, 48 + 2 * i, 0, c)
    soft_key(a, 0, 1, 47, 15, False)
    soft_key(a, 0, 16, 47, 15, True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    spec = [(ramp([(176, 252, 232), VFD_INK, (70, 178, 158)], i / 15), f"spectrum {i + 1}") for i in range(16)]
    return ([(VFD_BG, "background"), (VFD_GHOST, "dots")] + spec
            + [((180, 250, 232), "oscilloscope 1"), ((140, 236, 214), "oscilloscope 2"),
               (VFD_INK, "oscilloscope 3"), ((84, 190, 170), "oscilloscope 4"),
               ((60, 150, 134), "oscilloscope 5"), ((214, 255, 244), "peaks")])


def hexc(c):
    return "#%02X%02X%02X" % c


PLEDIT = dict(Normal=NAVY, Current=RED, NormalBG=CARD, SelectedBG=(250, 214, 92), MbBG=VFD_BG, MbFG=VFD_INK)


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write("[Text]\n")
        for k, v in PLEDIT.items():
            f.write(f"{k}={hexc(v)}\n")
        f.write("Font=Arial\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{T.title} - a skin in the style of the Nortel Millennium payphone in Bell Canada's\n"
            "2000s livery: the royal-blue top band, the satin faceplate, the teal dot-matrix VFD,\n"
            "the silver soft keys and chrome keypad, and the bilingual instruction card.\n"
            "Every bitmap was drawn by a script (gen_skin.py).\n\n"
            "Bell logo (c) Bell Canada. Nortel and Millennium are names of Nortel Networks.\n"
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
    # genex.bmp completed for real Winamp and WACUP (skins/genex_wacup.py).
    genex_wacup.process(wsz)
    return names


# ------------------------------------------------------------------------------------------
# Preview: the windows assembled from the sprites the way the app does
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
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, SHEETS["text"], (col * 5, row * 6, 5, 6), x, y)
        x += 5


def text_ink():
    """text.bmp's ink as the app picks it: the commonest colour 96+ (summed RGB) from the space cell."""
    t = np.array(SHEETS["text"])[:12, :155].reshape(-1, 3).astype(int)
    bg = np.array(SHEETS["text"])[0, 150].astype(int)
    far = t[np.abs(t - bg).sum(1) >= 96]
    vals, counts = np.unique(far, axis=0, return_counts=True)
    return tuple(int(v) for v in vals[counts.argmax()])


def tt_font(size):
    for p in ("/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
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
    blit(img, S["playpaus"], (36 if state["playing"] else 39, 0, 3, 9), 24, 28)
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
    blit(img, nums, (99 if state["remaining"] else 90, 0, 9, 13), 38, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    # the title row blanked with text.bmp's space, then the title as the app draws it
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 27)
    if state.get("bitmap"):
        draw_bitmap_text(img, state["title"][:31], 111, 27)
    else:
        box_ = img.crop((111, 22, 265, 40))
        ImageDraw.Draw(box_).text((0, 33 - 22), state["title"], fill=text_ink(), font=tt_font(11), anchor="ls")
        img.paste(box_, (111, 22))
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=PLEDIT["NormalBG"])
    font = tt_font(9)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=PLEDIT["SelectedBG"])
        col = PLEDIT["Current"] if i == 1 else PLEDIT["Normal"]
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
    col = np.stack([30 + 40 * arr[..., 0], 50 + 90 * arr[..., 0], 120 + 110 * arr[..., 0]], -1)
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


PREVIEW_ROWS = [("Long Distance - Interurbain", "4:12"), ("Card Phone Only - Seulement", "3:47"),
                ("Next Call - Appel suivant", "5:03"), ("Coin Return - Lunchtime", "2:58"),
                ("Bell-Northern - Millennium", "6:21"), ("Smart Touch - Ring Swoosh", "3:33"),
                ("411 - Directory Assistance", "4:40"), ("Phone Booth - Winter Glass", "3:09"),
                ("Dial Tone - Armoured Cord", "5:51"), ("Operator - Zero Plus", "4:05"),
                ("Collect Call - Frais vires", "3:22")]


def preview():
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title="Long Distance - Interurbain (Radio Edit)", bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True, bitmap=True,
             title="BNR MILLENNIUM - BELL-NORTHERN", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
    out.save(os.path.join(HERE, "out", "scratch", f"preview-{T.name}-1x.png"))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, f"preview-{T.name}.png"))


def check():
    """Invariants the app depends on."""
    t = np.array(SHEETS["text"]).astype(int)
    space = t[0:6, 150:155]
    assert (space[0, 0] == VFD_BG).all(), "space cell's corner must be the plain display colour"
    assert (np.abs(space - np.array(VFD_BG)).sum(2) < 96).all(), "space cell ghosts too bright"
    assert text_ink() == VFD_INK, text_ink()
    gen_letters()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--list"]:
        for k, v in THEMES.items():
            print(f"{k:18s} {v.wsz}")
        sys.exit(0)
    os.makedirs(os.path.join(HERE, "out", "scratch"), exist_ok=True)
    for theme in (args or list(THEMES)):
        use_theme(theme)
        names = build()
        check()
        preview()
        print(f"{T.wsz}: {', '.join(names)}")
