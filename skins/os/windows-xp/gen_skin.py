#!/usr/bin/python3
"""Windows XP: a classic Winamp 2.x skin in the style of Windows XP's Luna Blue theme.

Drawn from scratch by code (gradients, rounded rectangles, hand-made pixel fonts): a style
homage only, with no logos, no wallpaper and no copied artwork. Writes the bitmaps and text
files into out/, zips them flat into Windows-XP.wsz, and draws preview.png (the windows
assembled from the sprites at their real positions, 2x). Based on skins/ember/gen_skin.py.
"""

import os
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------------------------------
# Palette (Luna Blue, by eye)
# ------------------------------------------------------------------------------------------

FACE = (236, 233, 216)       # dialog face
FACE_LO = (172, 168, 153)    # its shadow
FACE_DK = (113, 111, 100)
WHITE = (255, 255, 255)
INK = (0, 0, 0)
INK_SOFT = (64, 64, 64)
EDGE = (127, 157, 185)       # edit box / list view border
BTN_EDGE = (0, 60, 116)      # push button border
SEL = (49, 106, 197)         # selection blue
LUNA = (0, 84, 227)
NAVY = (0, 36, 112)          # display digits
GHOST = (234, 238, 245)      # unlit segments on the white display
CORNER = (24, 34, 72)        # outside a rounded corner
SEP = (255, 0, 255)          # gen.bmp letter separators (never shown)

# window frame rings, outer to inner
FRAME = [(0, 30, 150), (28, 100, 238), (10, 80, 226), (0, 58, 196)]

# caption gradient: rows 0, 1, 2 fixed, the rest along a ramp
CAP_LIT = [(10, 64, 206), (110, 172, 255), (66, 148, 255)]
CAP_LIT_RAMP = [(34, 122, 255), (6, 96, 242), (0, 86, 230), (0, 80, 222), (0, 72, 212), (0, 62, 198)]
CAP_DIM = [(112, 136, 208), (204, 218, 248), (182, 202, 243)]
CAP_DIM_RAMP = [(166, 190, 238), (148, 174, 232), (134, 162, 227), (126, 154, 224), (118, 145, 218), (110, 136, 210)]
CAP_TEXT = WHITE
CAP_SHADOW = (8, 34, 128)
CAP_TEXT_DIM = (222, 232, 250)

# XP progress-bar green, across a chunk's thickness
GREEN = [(168, 236, 156), (104, 218, 92), (56, 200, 52), (40, 184, 40), (60, 196, 56), (128, 222, 116)]


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


def getpx(a, x, y):
    return tuple(int(v) for v in a[y, x])


def outline(a, x, y, w, h, col):
    rect(a, x, y, w, 1, col)
    rect(a, x, y + h - 1, w, 1, col)
    rect(a, x, y, 1, h, col)
    rect(a, x + w - 1, y, 1, h, col)


def vgrad(a, x, y, w, h, stops):
    for r in range(h):
        rect(a, x, y + r, w, 1, ramp(stops, r / max(1, h - 1)))


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def round_corners(a, x, y, w, h, outside):
    """Softens a 1px-bordered box's corners: each corner pixel blended with what's outside."""
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, lerp(getpx(a, cx, cy), outside, 0.6))


def edit_box(a, x, y, w, h, fill=WHITE):
    """An XP edit box: white field, a 1px blue-grey border (x, y is the border's corner)."""
    rect(a, x, y, w, h, fill)
    outline(a, x, y, w, h, EDGE)


# ------------------------------------------------------------------------------------------
# Pixel fonts (all designed for this skin)
# ------------------------------------------------------------------------------------------

def G(*rows):
    return list(rows)


# 5-row font for text.bmp (Ember's, which is ours).
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

# Caption font: a humanist sans, 1px skeletons on an 8-row grid (caps rows 0-5, x-height
# rows 2-5, descenders rows 6-7), set bold by doubling each pixel to the right, so counters
# are two pixels wide in the skeleton.
_CAPS = {
    "A": G(".##.", "#..#", "#..#", "####", "#..#", "#..#"),
    "B": G("###.", "#..#", "###.", "#..#", "#..#", "###."),
    "C": G(".###", "#...", "#...", "#...", "#...", ".###"),
    "D": G("###.", "#..#", "#..#", "#..#", "#..#", "###."),
    "E": G("###", "#..", "##.", "#..", "#..", "###"),
    "F": G("###", "#..", "##.", "#..", "#..", "#.."),
    "G": G(".###", "#...", "#...", "#.##", "#..#", ".###"),
    "H": G("#..#", "#..#", "####", "#..#", "#..#", "#..#"),
    "I": G("#", "#", "#", "#", "#", "#"),
    "J": G("..#", "..#", "..#", "..#", "..#", "##."),
    "K": G("#..#", "#.#.", "##..", "##..", "#.#.", "#..#"),
    "L": G("#..", "#..", "#..", "#..", "#..", "###"),
    "M": G("#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#"),
    "N": G("#..#", "##.#", "#.##", "#..#", "#..#", "#..#"),
    "O": G(".##.", "#..#", "#..#", "#..#", "#..#", ".##."),
    "P": G("###.", "#..#", "#..#", "###.", "#...", "#..."),
    "Q": G(".##.", "#..#", "#..#", "#..#", "#.#.", ".#.#"),
    "R": G("###.", "#..#", "#..#", "###.", "#.#.", "#..#"),
    "S": G(".###", "#...", ".##.", "...#", "...#", "###."),
    "T": G("####", ".#..", ".#..", ".#..", ".#..", ".#.."),
    "U": G("#..#", "#..#", "#..#", "#..#", "#..#", ".##."),
    "V": G("#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#.."),
    "W": G("#..#..#", "#..#..#", "#..#..#", "#..#..#", "#..#..#", ".##.##."),
    "X": G("#..#", "#..#", ".##.", ".##.", "#..#", "#..#"),
    "Y": G("#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": G("####", "...#", "..#.", ".#..", "#...", "####"),
}
_LOWER = {   # (rows, first row on the grid)
    "a": (G(".###", "#..#", "#..#", ".###"), 2),
    "b": (G("#...", "#...", "###.", "#..#", "#..#", "###."), 0),
    "c": (G(".##", "#..", "#..", ".##"), 2),
    "d": (G("...#", "...#", ".###", "#..#", "#..#", ".###"), 0),
    "e": (G(".##.", "####", "#...", ".###"), 2),
    "f": (G(".#", "#.", "##", "#.", "#.", "#."), 0),
    "g": (G(".###", "#..#", "#..#", ".###", "...#", ".##."), 2),
    "h": (G("#...", "#...", "###.", "#..#", "#..#", "#..#"), 0),
    "i": (G("#", ".", "#", "#", "#", "#"), 0),
    "j": (G(".#", "..", ".#", ".#", ".#", ".#", "#."), 0),
    "k": (G("#..", "#..", "#.#", "##.", "##.", "#.#"), 0),
    "l": (G("#", "#", "#", "#", "#", "#"), 0),
    "m": (G("###.##.", "#..#..#", "#..#..#", "#..#..#"), 2),
    "n": (G("###.", "#..#", "#..#", "#..#"), 2),
    "o": (G(".##.", "#..#", "#..#", ".##."), 2),
    "p": (G("###.", "#..#", "#..#", "###.", "#...", "#..."), 2),
    "q": (G(".###", "#..#", "#..#", ".###", "...#", "...#"), 2),
    "r": (G("###", "#..", "#..", "#.."), 2),
    "s": (G(".##", "#..", "..#", "##."), 2),
    "t": (G("#.", "##", "#.", "#.", ".#"), 1),
    "u": (G("#..#", "#..#", "#..#", ".###"), 2),
    "v": (G("#...#", "#...#", ".#.#.", "..#.."), 2),
    "w": (G("#..#..#", "#..#..#", "#..#..#", ".##.##."), 2),
    "x": (G("#..#", ".##.", ".##.", "#..#"), 2),
    "y": (G("#..#", "#..#", "#..#", ".###", "...#", ".##."), 2),
    "z": (G("###", "..#", ".#.", "###"), 2),
}


def _bold(rows, top=0, height=8):
    w = len(rows[0]) + 1
    out = [["."] * w for _ in range(height)]
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "#":
                out[top + r][c] = "#"
                out[top + r][c + 1] = "#"
    return ["".join(r) for r in out]


CAPTION = {c: _bold(g) for c, g in _CAPS.items()}
CAPTION.update({c: _bold(g, top) for c, (g, top) in _LOWER.items()})
CAPTION[" "] = ["..."] * 8


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


def caption_text(a, s, x, y, lit):
    """Bold caption: white with a dark drop shadow when lit, pale and flat when not."""
    if lit:
        draw_text(a, CAPTION, s, x, y, CAP_TEXT, gap=1, shadow=CAP_SHADOW)
    else:
        draw_text(a, CAPTION, s, x, y, CAP_TEXT_DIM, gap=1)


def caption_w(s):
    return text_w(CAPTION, s, 1)


# ------------------------------------------------------------------------------------------
# The Luna window: caption bar, frame, caption buttons
# ------------------------------------------------------------------------------------------


def cap_colours(h, lit):
    fixed, stops = (CAP_LIT, CAP_LIT_RAMP) if lit else (CAP_DIM, CAP_DIM_RAMP)
    return fixed + [ramp(stops, i / max(1, h - 4)) for i in range(h - 3)]


def caption(w, h, lit, round_left=True, round_right=True):
    """A Luna caption strip, h rows: glossy band at the top, deep blue body, rounded top corners."""
    a = new(w, h)
    cols = cap_colours(h, lit)
    for r in range(h):
        rect(a, 0, r, w, 1, cols[r])
    edge = FRAME[0] if lit else (96, 120, 196)
    if round_left:
        rect(a, 0, 0, 1, h, edge)
        for r in range(1, h):
            px(a, 1, r, lerp(cols[r], WHITE, 0.22))
    if round_right:
        rect(a, w - 1, 0, 1, h, edge)
        for r in range(1, h):
            px(a, w - 2, r, lerp(cols[r], edge, 0.35))
    for side, on in ((0, round_left), (1, round_right)):
        if not on:
            continue
        m = (lambda x: x) if side == 0 else (lambda x: w - 1 - x)
        for x, y in ((0, 0), (1, 0), (0, 1)):
            px(a, m(x), y, CORNER)
        for x, y in ((2, 0), (1, 1), (0, 2)):
            px(a, m(x), y, lerp(edge, CORNER, 0.3))
        px(a, m(2), 1, lerp(cols[1], edge, 0.5))
        px(a, m(1), 2, lerp(cols[2], edge, 0.5))
    return a


def window(w, h, cap_h, lit=True, top_h=None):
    """A whole Luna window: caption (cap_h rows), dialog face, a 4px blue frame on the sides
    and bottom. top_h: where the frame's sides start being plain frame (defaults to cap_h)."""
    a = new(w, h, FACE)
    a[0:cap_h] = caption(w, cap_h, lit)
    for y in range(cap_h, h):
        for x in list(range(4)) + list(range(w - 4, w)):
            ring = min(x, w - 1 - x, h - 1 - y)
            a[y, x] = FRAME[ring]
    for y in range(h - 4, h):
        for x in range(4, w - 4):
            a[y, x] = FRAME[h - 1 - y]
    return a


def cap_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 Luna caption button: white rim, glossy face, white glyph; the close one red-orange."""
    bar = [getpx(a, x, y + r) for r in range(9)]
    close = kind == "close"
    if lit:
        if close:
            stops = [(186, 52, 22), (214, 76, 44), (196, 60, 28)] if pressed else \
                [(246, 150, 120), (228, 84, 46), (216, 64, 26), (200, 50, 18)]
        else:
            stops = [(14, 58, 186), (34, 88, 220), (40, 100, 232)] if pressed else \
                [(124, 176, 255), (66, 132, 250), (36, 100, 238), (28, 88, 228)]
        rim, glyph = (240, 246, 255), WHITE
    else:
        if close:
            stops = [(214, 140, 120), (200, 120, 98)] if pressed else [(236, 184, 166), (216, 146, 124)]
        else:
            stops = [(142, 166, 226), (156, 180, 232)] if pressed else [(196, 212, 246), (158, 182, 234)]
        rim, glyph = (236, 242, 252), (248, 250, 255)
    vgrad(a, x + 1, y + 1, 7, 7, stops)
    rect(a, x + 1, y, 7, 1, rim)
    rect(a, x + 1, y + 8, 7, 1, rim)
    rect(a, x, y + 1, 1, 7, rim)
    rect(a, x + 8, y + 1, 1, 7, rim)
    for cx, cy in ((0, 0), (8, 0), (0, 8), (8, 8)):
        px(a, x + cx, y + cy, lerp(bar[cy], rim, 0.35))
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "minimize":
        rect(a, X + 2, Y + 5, 4, 2, glyph)
    elif kind == "shade":
        outline(a, X + 2, Y + 2, 5, 5, glyph)
        rect(a, X + 2, Y + 3, 5, 1, glyph)
    elif kind == "close":
        soft = lerp(glyph, stops[len(stops) // 2], 0.45)
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, glyph)
            px(a, X + 6 - i, Y + 2 + i, glyph)
        for i in range(4):
            px(a, X + 3 + i, Y + 2 + i, soft)
            px(a, X + 5 - i, Y + 2 + i, soft)


LOGO_SVG = os.path.join(HERE, "source", "logo-windows-flag", "flag-multicolored.svg")
_LOGO_PNG = os.path.join(OUT, "scratch", "flag-256.png")


def logo(size):
    """The XP-era Windows flag (see README for its source), rasterised once with rsvg-convert
    and scaled down to `size` px wide, as RGBA."""
    if not os.path.exists(_LOGO_PNG):
        os.makedirs(os.path.dirname(_LOGO_PNG), exist_ok=True)
        import subprocess
        subprocess.run(["/usr/bin/rsvg-convert", "-w", "256", LOGO_SVG, "-o", _LOGO_PNG], check=True)
    im = Image.open(_LOGO_PNG).convert("RGBA")
    h = max(1, round(im.height * size / im.width))
    return im.resize((size, h), Image.LANCZOS)


def flag_icon(a, x, y, size, pressed=False):
    """Composites the flag onto the canvas at (x, y), vertically centred in a size x size box;
    pressed: nudged a pixel and dimmed."""
    im = logo(size)
    arr = np.asarray(im).astype(np.float32)
    rgb, al = arr[..., :3], arr[..., 3:4] / 255.0
    al = np.clip((al - 0.15) / 0.7, 0, 1)        # crisper edge at sprite size
    if pressed:
        rgb = rgb * 0.75
    o = 1 if pressed else 0
    oy = y + (size - im.height) // 2 + o
    ox = x + o
    h, w = im.height, im.width
    h = min(h, a.shape[0] - oy)
    w = min(w, a.shape[1] - ox)
    dst = a[oy:oy + h, ox:ox + w].astype(np.float32)
    a[oy:oy + h, ox:ox + w] = np.round(dst * (1 - al[:h, :w]) + rgb[:h, :w] * al[:h, :w]).astype(np.int32)


def main_titlebar(lit, pressed=None):
    a = caption(275, 14, lit)
    flag_icon(a, 6, 3, 9, pressed == "options")
    caption_text(a, "Winamp", 19, 4, lit)
    cap_button(a, 244, 3, "minimize", lit, pressed == "minimize")
    cap_button(a, 254, 3, "shade", lit, pressed == "shade")
    cap_button(a, 264, 3, "close", lit, pressed == "close")
    return a


def eq_titlebar(lit, pressed=False):
    a = caption(275, 14, lit)
    caption_text(a, "Equalizer", 6, 4, lit)
    cap_button(a, 264, 3, "close", lit, pressed)
    return a


# ------------------------------------------------------------------------------------------
# Push buttons, toggles, thumbs
# ------------------------------------------------------------------------------------------


def xp_button(a, x, y, w, h, pressed=False, on=False):
    """An XP push button: rounded dark-blue rim, white-to-beige face (pressed: darker, flat);
    `on` gives the face a pale blue tint (a latched toggle)."""
    outside = getpx(a, x, y)
    if pressed:
        stops = [(208, 205, 192), (226, 224, 214), (234, 232, 224), (240, 239, 233)]
        if on:
            stops = [(176, 196, 232), (200, 216, 244), (214, 226, 248)]
    else:
        stops = [WHITE, (250, 250, 246), (242, 241, 235), (232, 230, 222), (214, 208, 196)]
        if on:
            stops = [(246, 250, 255), (226, 236, 252), (210, 224, 250), (196, 214, 246)]
    vgrad(a, x + 1, y + 1, w - 2, h - 2, stops)
    if not pressed:
        rect(a, x + w - 2, y + 2, 1, h - 4, lerp(stops[-2], (214, 208, 196), 0.6))
    outline(a, x, y, w, h, BTN_EDGE)
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, lerp(BTN_EDGE, outside, 0.65))
    for cx, cy in ((x + 1, y + 1), (x + w - 2, y + 1), (x + 1, y + h - 2), (x + w - 2, y + h - 2)):
        px(a, cx, cy, lerp(getpx(a, cx, cy), BTN_EDGE, 0.3))


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


GLYPH = (24, 32, 56)
GLYPH_PLAY = (24, 32, 56)


def transport_icon(a, kind, x, y, w, h, pressed):
    ink = GLYPH
    o = 1 if pressed else 0
    cx, cy = x + w // 2 + o, y + h // 2 + o
    if kind == "previous":
        rect(a, cx - 6, cy - 3, 2, 7, ink)
        tri_left(a, cx - 4, cy - 3, 7, ink)
        tri_left(a, cx, cy - 3, 7, ink)
    elif kind == "play":
        tri_right(a, cx - 2, cy - 4, 9, GLYPH_PLAY)
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
            rect(a, cx - 1 - r, cy - 4 + r, 2 * r + 3, 1, ink)
        rect(a, cx - 4, cy + 1, 9, 2, ink)


def green_dot(a, x, y, on):
    """A 3x3 indicator light: XP green when on, a grey socket when off."""
    if on:
        rect(a, x, y, 3, 3, (40, 176, 40))
        px(a, x, y, (128, 222, 116))
        px(a, x + 1, y, (96, 210, 86))
        px(a, x, y + 1, (96, 210, 86))
        px(a, x + 2, y + 2, (24, 128, 24))
    else:
        rect(a, x, y, 3, 3, (196, 192, 178))
        px(a, x + 2, y + 2, (226, 224, 214))
        px(a, x, y, (160, 156, 142))


def toggle(a, x, y, w, h, label, on, pressed, led="under"):
    xp_button(a, x, y, w, h, pressed, on)
    o = 1 if pressed else 0
    ink = (0, 60, 170) if on else INK
    tw = text_w(TINY, label)
    if led == "under":
        draw_text(a, TINY, label, x + (w - tw) // 2 + o, y + 3 + o, ink)
        bx = x + 4 + o
        bw = w - 8
        if on:
            for k in range(0, bw, 4):
                rect(a, bx + k, y + h - 5 + o, min(3, bw - k), 2, GREEN[2])
                rect(a, bx + k, y + h - 5 + o, min(3, bw - k), 1, GREEN[0])
        else:
            rect(a, bx, y + h - 5 + o, bw - 1, 2, (214, 210, 196))
    else:
        draw_text(a, TINY, label, x + 7 + (w - 9 - tw) // 2 + o, y + (h - 5) // 2 + o, ink)
        green_dot(a, x + 3 + o, y + h // 2 - 1 + o, on)


def shape_thumb(a, x, y, mask, face, border, rim):
    """Draws a thumb from a mask (list of strings): 1px border on its outline, a coloured rim
    just inside, a face gradient top to bottom."""
    h, w = len(mask), len(mask[0])
    inside = lambda i, j: 0 <= j < h and 0 <= i < w and mask[j][i] == "#"
    for j in range(h):
        for i in range(w):
            if not inside(i, j):
                continue
            n4 = [inside(i + 1, j), inside(i - 1, j), inside(i, j + 1), inside(i, j - 1)]
            if not all(n4):
                col = border
            else:
                n8 = [inside(i + di, j + dj) for di in (-2, -1, 0, 1, 2) for dj in (-1, 0, 1)
                      if abs(di) <= 1 or dj == 0]
                col = ramp(face, j / max(1, h - 1))
                if not all(n8):
                    col = rim
            px(a, x + i, y + j, col)
    return a


def thumb_down(w, h):
    """A trackbar thumb pointing down: full width over the groove, the point below it
    (sprites are opaque, so the body has to cover the groove edge to edge)."""
    rows = []
    for j in range(h):
        if j == 0:
            rows.append("." + "#" * (w - 2) + ".")
        elif j < h - 3:
            rows.append("#" * w)
        else:
            k = (j - (h - 4)) * 2
            n = max(2, w - 2 * k) if j < h - 1 else 2
            if j == h - 1:
                n = 2 + (w % 2)
            m = (w - n) // 2
            rows.append("." * m + "#" * n + "." * (w - n - m))
    return rows


def thumb_right(w, h):
    t = thumb_down(h, w)
    return ["".join(t[j][i] for j in range(w)) for i in range(h)]


THUMB_FACE = [WHITE, (246, 246, 240), (232, 230, 220)]
THUMB_EDGE = (28, 81, 128)
THUMB_RIM = (120, 214, 104)      # Luna's green glow
THUMB_RIM_HOT = (250, 180, 56)   # and its orange when grabbed


def trackbar_thumb(a, x, y, w, h, hot, direction="down"):
    mask = thumb_down(w, h) if direction == "down" else thumb_right(w, h)
    shape_thumb(a, x, y, mask, THUMB_FACE, THUMB_EDGE, THUMB_RIM_HOT if hot else THUMB_RIM)


def scroll_thumb(a, x, y, w, h, pressed, grip="h"):
    """A Luna scrollbar thumb: pale periwinkle, rounded, with a ridged grip in the middle."""
    outside = getpx(a, x, y)
    if pressed:
        stops = [(178, 200, 250), (160, 186, 246), (150, 176, 240)]
        edge, gl, gd = (96, 128, 220), (210, 226, 255), (104, 140, 226)
    else:
        stops = [(214, 228, 254), (196, 214, 252), (184, 204, 250)]
        edge, gl, gd = (134, 162, 232), (238, 244, 255), (140, 170, 238)
    if grip == "h":
        for r in range(h):
            rect(a, x, y + r, w, 1, ramp(stops, r / max(1, h - 1)))
    else:
        for c in range(w):
            rect(a, x + c, y, 1, h, ramp(stops, c / max(1, w - 1)))
    outline(a, x, y, w, h, edge)
    rect(a, x + 1, y + 1, w - 2, 1, lerp(stops[0], WHITE, 0.6))
    rect(a, x + 1, y + 1, 1, h - 2, lerp(stops[0], WHITE, 0.4))
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, lerp(edge, outside, 0.7))
    cx, cy = x + w // 2, y + h // 2
    if grip == "h":
        for k in (-3, -1, 1, 3):
            if 2 <= cy + k - y < h - 2:
                rect(a, cx - (w // 2 - 2), cy + k - 1, w - 4 if w > 6 else w - 3, 1, gl)
                rect(a, cx - (w // 2 - 2), cy + k, w - 4 if w > 6 else w - 3, 1, gd)
    else:
        for k in (-3, -1, 1, 3):
            rect(a, cx + k - 1, cy - 2, 1, 5, gl)
            rect(a, cx + k, cy - 2, 1, 5, gd)


def green_chunks(a, x, y, w, h, axis="x", step=4, chunk=3):
    """XP progress-bar fill: green chunks across `w` (axis x) or up from the bottom (axis y)."""
    if axis == "x":
        for k in range(0, w, step):
            cw = min(chunk, w - k)
            for r in range(h):
                rect(a, x + k, y + r, cw, 1, ramp(GREEN, r / max(1, h - 1)))
    else:
        for k in range(0, w, step):
            ch = min(chunk, w - k)
            for c in range(h):
                rect(a, x + c, y - k - ch + 1, 1, ch, ramp(GREEN, c / max(1, h - 1)))


def groove(a, x, y, w, h):
    """The trackbar channel: a thin sunken slot."""
    rect(a, x, y, w, h, (244, 243, 238))
    rect(a, x, y, w, 1, FACE_LO)
    rect(a, x, y, 1, h, FACE_LO)
    rect(a, x, y + h - 1, w, 1, WHITE)
    rect(a, x + w - 1, y, 1, h, WHITE)
    rect(a, x + 1, y + 1, w - 2, 1, (226, 224, 214))


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, FACE)
    rect(a, 0, 0, 8, 43, (246, 245, 240))
    outline(a, 0, 0, 8, 43, EDGE)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, SEL)
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, WHITE if on else (92, 92, 92))
    return a


def make_titlebar():
    a = new(344, 87, FACE)
    for kind, x, bx in (("options", 0, 6), ("minimize", 9, 244), ("close", 18, 264)):
        a[0:9, x:x + 9] = main_titlebar(True)[3:12, bx:bx + 9]
        a[9:18, x:x + 9] = main_titlebar(True, kind)[3:12, bx:bx + 9]
    a[18:27, 0:9] = main_titlebar(True)[3:12, 254:263]
    a[18:27, 9:18] = main_titlebar(True, "shade")[3:12, 254:263]
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

SEG = {
    "a": [(0, c) for c in range(2, 7)] + [(1, c) for c in range(3, 6)],
    "g": [(6, c) for c in range(2, 7)],
    "d": [(12, c) for c in range(2, 7)] + [(11, c) for c in range(3, 6)],
    "f": [(r, c) for r in range(1, 6) for c in (1, 2)],
    "b": [(r, c) for r in range(1, 6) for c in (6, 7)],
    "e": [(r, c) for r in range(7, 12) for c in (1, 2)],
    "c": [(r, c) for r in range(7, 12) for c in (6, 7)],
}
DIGIT_SEGS = {
    0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc",
    5: "afgcd", 6: "afgedc", 7: "abc", 8: "abcdefg", 9: "abcdfg",
}


def seven_seg(a, x, y, lit_segs, ghost=True):
    rect(a, x, y, 9, 13, WHITE)
    for s, cells in SEG.items():
        if s not in lit_segs and ghost:
            for r, c in cells:
                px(a, x + c, y + r, GHOST)
    for s, cells in SEG.items():
        if s in lit_segs:
            for r, c in cells:
                px(a, x + c, y + r, NAVY)


def make_main():
    a = window(275, 116, 14)
    a[0:14] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # left display: an edit-box field for the indicator, time and analyzer
    edit_box(a, 20, 19, 86, 44)
    for x in (48, 60, 78, 90):
        seven_seg(a, x, 26, "")
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, NAVY)
    rect(a, 23, 60, 78, 1, (226, 230, 238))

    # right: title field and the kbps/kHz/mono/stereo field
    edit_box(a, 108, 20, 161, 17)
    edit_box(a, 108, 39, 161, 16)
    draw_text(a, TINY, "KBPS", 129, 44, (90, 100, 120))
    draw_text(a, TINY, "KHZ", 169, 44, (90, 100, 120))
    rect(a, 207, 41, 1, 12, (220, 226, 236))

    # seek bar seat: a sunken trough edge round the posbar
    outline(a, 15, 71, 250, 12, FACE_LO)
    rect(a, 15, 82, 250, 1, WHITE)
    rect(a, 264, 71, 1, 12, WHITE)

    # transport: a toolbar-like groove under the buttons
    rect(a, 15, 87, 145, 1, FACE_LO)
    rect(a, 15, 106, 145, 1, WHITE)
    rect(a, 162, 87, 78, 1, FACE_LO)
    rect(a, 162, 105, 78, 1, WHITE)

    # the About spot: the flag
    flag_icon(a, 250, 89, 17)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36), shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def make_cbuttons():
    a = new(136, 36, FACE)
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18)]
    for kind, x, w, h in specs:
        for pressed, y in ((False, 0), (True, 18)):
            xp_button(a, x, y, w, h, pressed)
            transport_icon(a, kind, x, y, w, h, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        xp_button(a, 114, y, 22, 16, pressed)
        transport_icon(a, "eject", 114, y, 22, 16, pressed)
    return a


def make_shufrep():
    a = new(92, 85, FACE)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        toggle(a, 0, y, 28, 15, "REPEAT", on, pressed)
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        toggle(a, x, 61, 23, 12, label, False, pressed, led="dot")
        toggle(a, x, 73, 23, 12, label, True, pressed, led="dot")
    return a


# ------------------------------------------------------------------------------------------
# monoster, playpaus, numbers, nums_ex, text
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, WHITE)
    for y, on in ((0, True), (12, False)):
        col = NAVY if on else (204, 210, 222)
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, WHITE)
    tri_right(a, 3, 1, 7, (36, 168, 36))           # playing: XP green
    px(a, 3, 2, (120, 214, 110))
    px(a, 3, 3, (120, 214, 110))
    rect(a, 9 + 2, 1, 2, 7, NAVY)                  # paused
    rect(a, 9 + 5, 1, 2, 7, NAVY)
    rect(a, 18 + 2, 2, 5, 5, NAVY)                 # stopped
    rect(a, 36, 0, 3, 9, WHITE)                    # not working
    rect(a, 39 + 1, 3, 1, 3, (36, 168, 36))        # working
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, WHITE)
    for n in range(10):
        seven_seg(a, 9 * n, 0, DIGIT_SEGS[n])
    seven_seg(a, 90, 0, "")
    if ex:
        rect(a, 99, 0, 9, 13, WHITE)
        for r, c in SEG["g"]:
            px(a, 99 + c, r, NAVY)
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
            draw_text(a, FONT5, key, col * 5, row * 6, INK)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def make_posbar():
    a = new(307, 10, FACE)
    # an XP progress-bar trough: white, rounded, blue-grey rim
    rect(a, 0, 0, 248, 10, FACE)
    rect(a, 1, 1, 246, 8, WHITE)
    outline(a, 0, 0, 248, 10, (104, 120, 140))
    round_corners(a, 0, 0, 248, 10, FACE)
    rect(a, 1, 1, 246, 1, (228, 230, 234))
    rect(a, 1, 8, 246, 1, (246, 247, 249))
    scroll_thumb(a, 248, 0, 29, 10, False, grip="v")
    scroll_thumb(a, 278, 0, 29, 10, True, grip="v")
    return a


def slider_thumbs(a):
    trackbar_thumb(a, 0, 422, 14, 11, True)
    trackbar_thumb(a, 15, 422, 14, 11, False)


def make_volume():
    a = new(68, 433, FACE)
    for i in range(28):
        y = i * 15
        groove(a, 1, y + 3, 66, 6)
        level = (i + 1) / 28
        fill = min(62, round(4 + 54 * level))   # up to the thumb's middle
        if fill:
            green_chunks(a, 3, y + 5, fill, 3)
    slider_thumbs(a)
    return a


def make_balance():
    a = new(68, 433, FACE)
    for i in range(28):
        y = i * 15
        groove(a, 10, y + 3, 36, 6)
        rect(a, 27, y + 1, 2, 2, FACE_DK)       # the centre mark
        reach = round(12 * i / 27) + (2 if i else 0)
        if reach:
            green_chunks(a, 29, y + 5, reach, 3)
            # mirrored to the left of the centre
            seg = a[y + 5:y + 8, 29:29 + reach].copy()
            a[y + 5:y + 8, 27 - reach:27] = seg[:, ::-1]
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_slider_frame(a, x, y, n):
    """14x63: a vertical channel filling with green chunks from the bottom (n of 0..27)."""
    rect(a, x, y, 14, 63, FACE)
    groove(a, x + 4, y + 2, 6, 59)
    fill = min(56, round(2 + 51 * n / 27))   # up to the thumb's middle
    green_chunks(a, x + 5, y + 58, fill, 4, axis="y")
    for ty in (y + 2, y + 31, y + 60):
        rect(a, x + 12, ty, 2, 1, FACE_DK)


def make_eqmain():
    a = new(275, 315, FACE)
    a[0:116] = window(275, 116, 14)
    a[0:14] = eq_titlebar(True)
    # graph field
    edit_box(a, 85, 16, 115, 21)
    # a group box round the sliders
    gx, gy, gw, gh = 15, 37, 247, 68
    outline(a, gx, gy, gw, gh, (208, 208, 191))
    round_corners(a, gx, gy, gw, gh, FACE)
    rect(a, 40, 39, 1, 63, (208, 208, 191))
    rect(a, 41, 39, 1, 63, WHITE)
    for lbl, yy in (("+12DB", 40), ("0DB", 66), ("-12DB", 93)):
        text_center(a, TINY, lbl, 58, yy, INK_SOFT)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    text_center(a, TINY, "PREAMP", 28, 106, INK)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, INK)

    # under the window
    a[125:134, 0:9] = eq_titlebar(True, True)[3:12, 264:273]
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        toggle(a, x, 119, w, 12, label, on, pressed, led="dot")
    a[134:148] = eq_titlebar(True)
    a[149:163] = eq_titlebar(False)
    trackbar_thumb(a, 0, 164, 11, 11, False, "right")
    trackbar_thumb(a, 0, 176, 11, 11, True, "right")
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        xp_button(a, 224, y, 44, 12, pressed)
        o = 1 if pressed else 0
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 3 + o, INK)
    # graph: white with a light grid, the zero line, and the line's colours down x 115
    rect(a, 0, 294, 113, 19, WHITE)
    for x in range(0, 113, 12):
        for y in range(0, 19, 2):
            px(a, 2 + x, 294 + y, (222, 228, 238))
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, (200, 210, 226))
    for r in range(19):
        px(a, 115, 294 + r, ramp([(40, 170, 40), (0, 120, 160), LUNA, (0, 70, 200), (224, 68, 28)], r / 18))
    for x in range(113):
        px(a, x, 314, (150, 170, 200) if x % 3 != 2 else WHITE)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): cut from whole windows
# ------------------------------------------------------------------------------------------

BAR_CAP = 15      # caption rows of the 20px bars; the rest is dialog face


def pl_window(w, h, lit):
    """A whole playlist window (no title text, no buttons): caption, face, frame, and the list
    view's 1px border round the list and the scroll track."""
    a = window(w, h, BAR_CAP, lit)
    lx0, lx1 = 11, w - 6           # list view border columns
    ly0, ly1 = 19, h - 38          # and rows
    rect(a, lx0, ly0, lx1 - lx0 + 1, ly1 - ly0 + 1, WHITE)
    outline(a, lx0, ly0, lx1 - lx0 + 1, ly1 - ly0 + 1, EDGE)
    # the scroll track (tile x 4..13 of the right tile, which starts at w - 20)
    tx = w - 16
    rect(a, tx, ly0 + 1, 10, ly1 - ly0 - 1, (247, 246, 242))
    rect(a, tx, ly0 + 1, 1, ly1 - ly0 - 1, (238, 237, 229))
    rect(a, tx + 9, ly0 + 1, 1, ly1 - ly0 - 1, (238, 237, 229))
    return a


def make_pledit():
    a = new(280, 186, FACE)
    W, H = 275, 232
    for lit, y in ((True, 0), (False, 21)):
        win = pl_window(W, H, lit)
        a[y:y + 20, 0:25] = win[0:20, 0:25]
        a[y:y + 20, 127:152] = win[0:20, 100:125]
        t = win[0:20, 100:200].copy()
        title = "Playlist Editor"
        caption_text(t, title, (100 - caption_w(title)) // 2, 4, lit)
        a[y:y + 20, 26:126] = t
        t = win[0:20, W - 25:W].copy()
        cap_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t
        if lit:
            cap_button(t, 14, 3, "close", lit, pressed=True)
            a[42:51, 52:61] = t[3:12, 14:23]
    win = pl_window(W, H, True)
    a[42:71, 0:12] = win[40:69, 0:12]
    a[42:71, 31:51] = win[40:69, W - 20:W]
    scroll_thumb(a, 52, 53, 8, 18, False)
    scroll_thumb(a, 61, 53, 8, 18, True)

    # bottom-left: the four buttons
    t = win[H - 38:H, 0:125].copy()
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        xp_button(t, bx, 8, 22, 18)
        text_center(t, TINY, lbl, bx + 11, 15, INK)
    a[72:110, 0:125] = t

    # bottom-right: running time, mini transport, mini time, LIST, resize grip
    t = win[H - 38:H, W - 150:W].copy()
    edit_box(t, 5, 8, 58, 10)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        xp_button(t, bx, 22, 10, 10)
        mini_transport_icon(t, kind, bx, 22)
    edit_box(t, 64, 21, 35, 10)
    rect(t, 84, 22 + 2, 1, 1, INK_SOFT)
    rect(t, 84, 22 + 5, 1, 1, INK_SOFT)
    xp_button(t, 106, 8, 22, 18)
    text_center(t, TINY, "LIST", 117, 15, INK)
    xp_grip(t, 145, 32)
    a[72:110, 126:276] = t

    # bottom fill tile
    a[0:38, 179:204] = win[H - 38:H, 125:150]
    return a


def xp_grip(a, x, y):
    """XP's size grip: a triangle of raised dots, bottom-right corner at (x, y)."""
    for k in range(3):
        for j in range(k + 1):
            gx = x - 4 * k + 4 * j - 1
            gy = y - 4 * j - 1
            px(a, gx - 1, gy - 1, WHITE)
            px(a, gx, gy, (184, 180, 162))
            px(a, gx - 1, gy, (214, 210, 196))


def mini_transport_icon(a, kind, x, y):
    ink = GLYPH
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
    W, H = 250, 120
    for lit, y in ((True, 0), (False, 21)):
        win = window(W, H, BAR_CAP, lit)
        plain = win[0:20, 100:125]
        for x0 in (26, 52, 78, 104):
            a[y:y + 20, x0:x0 + 25] = plain
        a[y:y + 20, 0:25] = win[0:20, 0:25]
        t = win[0:20, W - 25:W].copy()
        cap_button(t, 14, 3, "close", lit)
        a[y:y + 20, 130:155] = t
        if lit:
            cap_button(t, 14, 3, "close", lit, pressed=True)
            a[42:51, 148:157] = t[3:12, 14:23]
    win = window(W, H, BAR_CAP, True)
    a[42:56, 0:125] = win[H - 14:H, 0:125]
    t = win[H - 14:H, W - 125:W].copy()
    xp_grip(t, 121, 10)
    a[57:71, 0:125] = t
    a[72:86, 127:152] = win[H - 14:H, 100:125]
    a[42:71, 127:138] = win[30:59, 0:11]
    a[42:66, 158:169] = win[30:54, 0:11]
    a[42:71, 139:147] = win[30:59, W - 8:W]
    a[42:66, 170:178] = win[30:54, W - 8:W]
    # the close-pressed sprite sits between the side pieces: written last
    t = window(W, H, BAR_CAP, True)[0:20, W - 25:W].copy()
    cap_button(t, 14, 3, "close", True, pressed=True)
    a[42:51, 148:157] = t[3:12, 14:23]

    # letters: each row starts at x 1, letters in their own cells (on the caption's own rows
    # 4..10), 1px separators of x 0's colour
    for lit, y in ((True, 88), (False, 96)):
        cell_bg = window(W, H, BAR_CAP, lit)[4:11, 100]
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            g = CAPTION[c]
            w = len(g[0]) + 1
            for r in range(7):
                rect(a, x, y + r, w, 1, tuple(int(v) for v in cell_bg[r]))
            cell = a[y:y + 7, x:x + w]
            tmp = np.zeros((8, w + 1, 3), dtype=np.int32)
            tmp[0:7, 0:w] = cell
            tmp[7, :] = tmp[6, 0]
            tmp[0:7, w] = tmp[0:7, 0]
            caption_text(tmp, c, 0, 0, lit)
            a[y:y + 7, x:x + w] = tmp[0:7, 0:w]
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------

GENEX_COLOURS = [
    (255, 255, 255),   # item background
    (0, 0, 0),         # item text
    FACE,              # window background
    (0, 0, 0),         # button text
    (0, 0, 0),         # window text
    EDGE,              # dividers, sunken borders
    SEL,               # selection bar
    (235, 234, 219),   # list header background
    (0, 0, 0),         # list header text
    (255, 255, 255),   # header frame, light
    (172, 168, 153),   # header frame, dark
    (199, 197, 178),   # header frame, pressed
    FACE,              # header dead area
    (196, 214, 252),   # scrollbar
    (134, 162, 232),   # scrollbar 2
    (160, 186, 246),   # scrollbar pressed
    (96, 128, 220),    # scrollbar pressed 2
    (247, 246, 242),   # scrollbar dead area
]


def make_genex():
    a = new(256, 64, FACE)
    for i, c in enumerate(GENEX_COLOURS):
        px(a, 48 + 2 * i, 0, c)
    xp_button(a, 0, 1, 47, 15, False)
    xp_button(a, 0, 16, 47, 15, True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------

VISCOLOR = (
    [((255, 255, 255), "background"), ((214, 222, 236), "dots")]
    + [(ramp([(70, 206, 60), (40, 184, 48), (20, 160, 110), (10, 120, 200), LUNA, (0, 60, 180)],
             i / 15), f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}") for i in range(16)]
    + [((0, 54, 180), "oscilloscope 1"), ((0, 84, 227), "oscilloscope 2"), ((40, 120, 240), "oscilloscope 3"),
       ((90, 150, 245), "oscilloscope 4"), ((140, 180, 250), "oscilloscope 5"), ((0, 36, 112), "peaks")]
)


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in VISCOLOR:
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write("[Text]\nNormal=#000000\nCurrent=#0054E3\nNormalBG=#FFFFFF\nSelectedBG=#C1D2EE\n"
                "MbBG=#FFFFFF\nMbFG=#000000\nFont=Arial\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            "Windows XP \u2014 a skin in the style of Windows XP's Luna theme, drawn from scratch\n"
            "apart from the logo. Not affiliated with Microsoft.\n\n"
            "A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py)\n"
            "from gradients, rounded rectangles and hand-made pixel fonts, with no wallpaper,\n"
            "screenshots or copied artwork. The one exception is the Windows flag (the titlebar\n"
            "icon and the About spot).\n\n"
            "Windows logo \u00a9 Microsoft; private use only.\n"
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
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "readme.txt"]
    wsz = os.path.join(HERE, "Windows-XP.wsz")
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


def preview_font(size=11):
    for name in ("LiberationSans-Regular.ttf", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def preview_main(lit, state):
    S = SHEETS
    img = Image.new("RGB", (275, 116))
    img.paste(S["main"], (0, 0))
    blit(img, S["titlebar"], (27, 0 if lit else 15, 275, 14), 0, 0)
    if state["pressed"] == "close":
        blit(img, S["titlebar"], (18, 9, 9, 9), 264, 3)
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
        blit(img, nums, (99, 0, 9, 13), 38, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    # title: text.bmp's space across the box, then the title in pledit's font and colour
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    d = ImageDraw.Draw(img)
    d.text((111, 27 + 2), state["title"], fill=(0, 0, 0), font=preview_font(11), anchor="lm")
    img.paste(S["main"].crop((265, 20, 275, 40)), (265, 20))
    draw_bitmap_text(img, "192", 111, 43)
    draw_bitmap_text(img, "44", 156, 43)
    cols = [c for c, _ in VISCOLOR]
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
            vp[x, y] = cols[min(17, max(2, y))]
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=(0xFF, 0xFF, 0xFF))
    font = preview_font(11)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 13
        if y + 13 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 12), fill=(0xC1, 0xD2, 0xEE))
        col = (0x00, 0x54, 0xE3) if i == 1 else (0, 0, 0)
        d.text((lx + 2, y + 7), f"{i + 1}. {txt}", fill=col, font=font, anchor="lm")
        d.text((lx + lw - 3, y + 7), dur, fill=col, font=font, anchor="rm")
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
    # a stand-in picture: a plain sky-to-meadow gradient
    pw, ph = w - 22, h - 34
    yy = np.linspace(0, 1, ph)[:, None] * np.ones((1, pw))
    top, mid, bot = np.array([70, 130, 220]), np.array([170, 205, 245]), np.array([70, 150, 60])
    t1 = np.clip(yy / 0.6, 0, 1)[..., None]
    t2 = np.clip((yy - 0.6) / 0.4, 0, 1)[..., None]
    col = np.where(yy[..., None] < 0.6, top + (mid - top) * t1, mid + (bot - mid) * t2)
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("Morning Commute - Blue Hour", "4:12"), ("Start Up - Ten Seconds", "3:47"),
            ("Green Hills - Open Fields", "5:03"), ("Taskbar Waltz - Notification", "2:58"),
            ("Default Theme - Royale", "6:21"), ("Sky Over Grass - Cloud Study", "3:33"),
            ("Dial-Up Dreams - Handshake", "4:40"), ("Recycle Bin - Empty", "3:09"),
            ("Balloon Tips - Hover", "5:51"), ("System Tray - Quiet Hours", "4:05"),
            ("Shut Down - Goodnight", "3:22"), ("Log Off - Switch User", "4:18"),
            ("Classic Mode - Grey Days", "2:44")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title="Windows XP - a Luna-style skin", bars=bars)
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
    out = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), (58, 62, 70))
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
