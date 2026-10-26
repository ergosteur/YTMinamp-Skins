#!/usr/bin/python3
"""iOS 6: a classic Winamp 2.x skin in the style of iOS 6's skeuomorphic look, generated procedurally.

A style homage only: every pixel is drawn here from code (gradients, anti-aliased shapes via
supersampled masks, hand-made pixel fonts). No artwork, logos or trademarks are copied.
Writes the bitmaps and text files into out/, zips them flat into iOS6.wsz, and draws preview.png
(the windows assembled from the sprites at their real positions, 2x). Based on skins/ember's
generator, which holds the sheet layouts the app reads.
"""

import os
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------------------------------
# Palette
# ------------------------------------------------------------------------------------------

# Navigation bar (blue-grey gloss) and its inactive (desaturated) twin.
NAV_TOP = (178, 191, 207)       # #b2bfcf
NAV_BOT = (109, 132, 162)       # #6d84a2
NAV_HI = (222, 228, 236)
NAV_EDGE = (45, 59, 78)
NAVI_TOP = (186, 188, 192)
NAVI_BOT = (124, 127, 132)
NAVI_HI = (232, 233, 235)
NAVI_EDGE = (82, 84, 88)
TITLE_SHADOW = (44, 58, 78)
TITLE_SHADOW_I = (74, 76, 80)

# Black glossy body and toolbar.
BODY_TOP = (50, 53, 58)
BODY_MID = (26, 27, 30)
BODY_LOW = (18, 19, 21)
BLACK = (0, 0, 0)

# Display glass.
DISP = (6, 8, 11)
DISP_DOTS = (18, 22, 28)
WHITE = (255, 255, 255)
DIM_TXT = (64, 70, 78)
LABEL_TXT = (128, 136, 146)

# iOS blue.
BLUE_TOP = (120, 178, 245)
BLUE_MID = (58, 131, 232)
BLUE_BOT = (28, 92, 200)
BLUE_EDGE = (18, 58, 128)
IOS_BLUE_TXT = (42, 95, 176)

# Light (Settings) materials.
PIN_A = (197, 204, 212)         # #c5ccd4
PIN_B = (203, 210, 216)         # #cbd2d8
FRAME = (199, 207, 217)
FRAME_EDGE = (120, 131, 146)
FRAME_IN = (150, 160, 172)
PANEL = (255, 255, 255)
PANEL_EDGE = (169, 177, 188)
HEADER_TXT = (76, 86, 108)      # grouped-table header text
TRACK_GREY = (232, 234, 237)
SEP = (255, 0, 255)             # gen.bmp letter separators (never shown)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    """Colour along a list of evenly spaced stops, t in 0..1."""
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def stops_at(stops, t):
    """Colour along (position, colour) stops; equal positions make a hard break (gloss line)."""
    if t <= stops[0][0]:
        return stops[0][1]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t0 <= t <= t1 and t1 > t0:
            return lerp(c0, c1, (t - t0) / (t1 - t0))
    return stops[-1][1]


def vgrad(h, stops, w=1):
    """(h, w, 3) array: a vertical gradient through (position, colour) stops."""
    g = np.array([stops_at(stops, (r + 0.5) / h) for r in range(h)], dtype=np.float32)
    return np.repeat(g[:, None, :], w, axis=1)


def grey(c):
    return int(round(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]))


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int) and anti-aliased masks
# ------------------------------------------------------------------------------------------


def new(w, h, col=BLACK):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[y:y + h, x:x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def fill_grad(a, x, y, w, h, stops):
    a[y:y + h, x:x + w] = np.round(vgrad(h, stops, w)).astype(np.int32)


SS = 4


def mask(w, h, fn):
    """Coverage (h, w) in 0..1 of whatever fn(draw, S) draws at S-times scale."""
    im = Image.new("L", (w * SS, h * SS), 0)
    fn(ImageDraw.Draw(im), SS)
    return np.asarray(im.resize((w, h), Image.BOX), dtype=np.float32) / 255.0


def rr_mask(w, h, r, x=0.0, y=0.0, mw=None, mh=None):
    """A rounded rectangle at (x, y) size mw x mh (default the whole w x h)."""
    mw = w - x if mw is None else mw
    mh = h - y if mh is None else mh

    def fn(d, S):
        d.rounded_rectangle((x * S, y * S, (x + mw) * S - 1, (y + mh) * S - 1), radius=r * S, fill=255)
    return mask(w, h, fn)


def ellipse_mask(w, h, x, y, ew, eh):
    return mask(w, h, lambda d, S: d.ellipse((x * S, y * S, (x + ew) * S - 1, (y + eh) * S - 1), fill=255))


def poly_mask(w, h, pts):
    return mask(w, h, lambda d, S: d.polygon([(px_ * S, py_ * S) for px_, py_ in pts], fill=255))


def paint(a, x, y, m, col, alpha=1.0):
    """Blends colour (tuple, or an array broadcastable to the mask) over a through mask m."""
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


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def pinstripe(a, x, y, w, h, phase=0):
    """The Settings background: soft vertical pinstripes; phase is the window x of column x."""
    for c in range(w):
        col = PIN_B if (phase + c) % 6 >= 4 else PIN_A
        a[y:y + h, x + c] = col


# ------------------------------------------------------------------------------------------
# Pixel fonts (all designed for this skin)
# ------------------------------------------------------------------------------------------

def G(*rows):
    return list(rows)


# 5-row font for text.bmp and gen.bmp's letters.
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
    "W": G("#...#", "#...#", "#.#.#", "#.#.#", ".#.#."),
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

# Mixed-case title lettering for the navigation bars: 7-row cap height, 2 descender rows.
NAVF = {
    "N": G("#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"),
    "P": G("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "E": G("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "M": G("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "o": G("....", "....", ".##.", "#..#", "#..#", "#..#", ".##."),
    "w": G(".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."),
    "l": G("#", "#", "#", "#", "#", "#", "#"),
    "a": G("....", "....", ".##.", "...#", ".###", "#..#", ".###"),
    "y": G("....", "....", "#..#", "#..#", "#..#", "#..#", ".###", "...#", ".##."),
    "i": G("#", ".", "#", "#", "#", "#", "#"),
    "n": G("....", "....", "###.", "#..#", "#..#", "#..#", "#..#"),
    "g": G("....", "....", ".###", "#..#", "#..#", "#..#", ".###", "...#", ".##."),
    "q": G("....", "....", ".###", "#..#", "#..#", "#..#", ".###", "...#", "...#"),
    "u": G("....", "....", "#..#", "#..#", "#..#", "#..#", ".###"),
    "z": G("....", "....", "####", "...#", "..#.", ".#..", "####"),
    "e": G("....", "....", ".##.", "#..#", "####", "#...", ".###"),
    "r": G("...", "...", "#.#", "##.", "#..", "#..", "#.."),
    "s": G("...", "...", ".##", "#..", ".#.", "..#", "##."),
    "t": G("...", ".#.", "###", ".#.", ".#.", ".#.", "..#"),
    "c": G("...", "...", ".##", "#..", "#..", "#..", ".##"),
    " ": G("..", "..", "..", "..", "..", "..", ".."),
}

# Light, Helvetica-like digits for the time display: 6 wide, 11 tall; '+' marks a half-tone pixel.
DIGITS = {
    0: G(".####.", "#+..+#", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#+..+#",
         ".####."),
    1: G("...#..", "..##..", ".+.#..", "...#..", "...#..", "...#..", "...#..", "...#..", "...#..", "...#..",
         "...#.."),
    2: G(".####.", "#+..+#", ".....#", ".....#", "....+#", "...+#.", "..+#..", ".+#...", "+#....", "#.....",
         "######"),
    3: G(".####.", "#+..+#", ".....#", ".....#", "....+#", "..###.", "....+#", ".....#", ".....#", "#+..+#",
         ".####."),
    4: G("....#.", "...##.", "...##.", "..+.#.", "..#.#.", ".+..#.", ".#..#.", "#+..#.", "######", "....#.",
         "....#."),
    5: G("######", "#.....", "#.....", "#.....", "#####.", "....+#", ".....#", ".....#", ".....#", "#+..+#",
         ".####."),
    6: G(".####.", "#+..+#", "#.....", "#.....", "#.###.", "##+.+#", "#....#", "#....#", "#....#", "#+..+#",
         ".####."),
    7: G("######", ".....#", "....+#", "....#.", "...+#.", "...#..", "..+#..", "..#...", "..#...", "..#...",
         "..#..."),
    8: G(".####.", "#+..+#", "#....#", "#+..+#", ".####.", "#+..+#", "#....#", "#....#", "#....#", "#+..+#",
         ".####."),
    9: G(".####.", "#+..+#", "#....#", "#....#", "#+..+#", ".#####", ".....#", ".....#", ".....#", "#+..+#",
         ".####."),
}


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1, shadow=None, sh=(0, 1)):
    """Pixel text; col may be a function of the glyph row. shadow is drawn offset by sh."""
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


def text_center(a, font, s, cx, y, col, gap=1, shadow=None, sh=(0, 1)):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow, sh)


# ------------------------------------------------------------------------------------------
# Shared pieces: navigation bar, bar buttons, glossy rounded buttons, knobs
# ------------------------------------------------------------------------------------------


def nav_stops(lit):
    top, bot, hi = (NAV_TOP, NAV_BOT, NAV_HI) if lit else (NAVI_TOP, NAVI_BOT, NAVI_HI)
    return top, bot, hi


def nav_bar(a, x, y, w, lit, h=14):
    """The navigation bar: light top line, blue-grey gradient with a faint gloss, dark bottom edge."""
    top, bot, hi = nav_stops(lit)
    edge = NAV_EDGE if lit else NAVI_EDGE
    fill_grad(a, x, y, w, h, [(0.0, lerp(top, WHITE, 0.08)), (0.5, lerp(top, bot, 0.42)),
                              (0.5, lerp(top, bot, 0.5)), (1.0, bot)])
    rect(a, x, y, w, 1, hi)
    rect(a, x, y + h - 1, w, 1, edge)


def nav_row(lit, r, h=14):
    """The colour of row r of a navigation bar (for cells blitted onto one)."""
    t = new(1, h)
    nav_bar(t, 0, 0, 1, lit, h)
    return tuple(int(v) for v in t[r, 0])


def nav_title(a, s, cx, lit, y=3):
    """White embossed title with the dark 1px shadow above it."""
    text_center(a, NAVF, s, cx, y, (255, 255, 255) if lit else (244, 244, 245),
                shadow=TITLE_SHADOW if lit else TITLE_SHADOW_I, sh=(0, -1))


def bar_button_colours(lit, pressed):
    if not lit:
        return ((168, 170, 174), (118, 120, 124), (78, 80, 84)) if not pressed else \
            ((120, 122, 126), (90, 92, 96), (60, 62, 66))
    if pressed:
        return (82, 104, 136), (46, 66, 98), (24, 36, 56)
    return (138, 158, 186), (78, 101, 133), (40, 55, 78)


def bar_button(a, x, y, w, h, lit=True, pressed=False, r=3):
    """A small glossy bar button: darker blue-grey rounded rect, dark rim, inner top highlight."""
    top, bot, edge = bar_button_colours(lit, pressed)
    paint(a, x, y, rr_mask(w, h, r), edge)
    inner = rr_mask(w, h, max(0.5, r - 1), 1, 1, w - 2, h - 2)
    paint(a, x, y, inner, vgrad(h, [(0, top), (0.5, lerp(top, bot, 0.45)), (0.5, lerp(top, bot, 0.6)), (1, bot)]))
    hl = rr_mask(w, h, max(0.5, r - 1), 1, 1, w - 2, 1)
    paint(a, x, y, hl, WHITE, 0.25 if not pressed else 0.08)


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button with a white pictogram."""
    bar_button(a, x, y, 9, 9, lit, pressed, r=2)
    ink = (255, 255, 255) if lit else (238, 238, 240)
    sh = (30, 42, 60) if lit else (70, 72, 76)
    X, Y = x, y

    def both(fn):
        fn(0, -1, sh)
        fn(0, 0, ink)

    if kind == "options":
        both(lambda dx, dy, c: [rect(a, X + 2 + dx, Y + 2 + dy + 2 * i, 5, 1, c) for i in range(3)])
    elif kind == "minimize":
        both(lambda dx, dy, c: rect(a, X + 2 + dx, Y + 6 + dy, 5, 1, c))
    elif kind == "shade":
        both(lambda dx, dy, c: (rect(a, X + 2 + dx, Y + 2 + dy, 5, 1, c), rect(a, X + 2 + dx, Y + 4 + dy, 5, 1, c)))
    elif kind == "close":
        def x_(dx, dy, c):
            for i in range(5):
                px(a, X + 2 + i + dx, Y + 2 + i + dy, c)
                px(a, X + 6 - i + dx, Y + 2 + i + dy, c)
        both(x_)


def gloss_pill(a, x, y, w, h, style, pressed=False, r=None):
    """A rounded glossy control: 'blue' (on), 'black' (off on the toolbar), 'white' (off on light)."""
    r = h / 2 - 0.5 if r is None else r
    if style == "blue":
        top, bot, edge = BLUE_TOP, BLUE_BOT, BLUE_EDGE
        if pressed:
            top, bot = lerp(BLUE_TOP, BLUE_BOT, 0.5), lerp(BLUE_BOT, BLACK, 0.25)
    elif style == "black":
        top, bot, edge = (88, 90, 94), (30, 31, 34), (0, 0, 0)
        if pressed:
            top, bot = (46, 47, 50), (16, 16, 18)
    else:
        top, bot, edge = (255, 255, 255), (222, 225, 229), (154, 163, 174)
        if pressed:
            top, bot = (206, 210, 215), (182, 187, 194)
    paint(a, x, y, rr_mask(w, h, r), edge)
    inner = rr_mask(w, h, max(0.5, r - 1), 1, 1, w - 2, h - 2)
    paint(a, x, y, inner, vgrad(h, [(0, top), (0.5, lerp(top, bot, 0.35)), (0.5, lerp(top, bot, 0.55)), (1, bot)]))
    if not pressed:
        paint(a, x, y, rr_mask(w, h, max(0.5, r - 1), 1, 1, w - 2, 1), WHITE, 0.35 if style != "white" else 0.0)


def knob(a, cx, cy, r, pressed=False, shadow=0.45):
    """The white glossy round slider knob (anti-aliased) centred at (cx, cy) on canvas a."""
    size_w, size_h = a.shape[1], a.shape[0]
    if shadow:
        paint(a, 0, 0, ellipse_mask(size_w, size_h, cx - r, cy - r + 1, 2 * r, 2 * r), BLACK, shadow)
    rim = (128, 132, 138) if not pressed else (104, 108, 114)
    paint(a, 0, 0, ellipse_mask(size_w, size_h, cx - r, cy - r, 2 * r, 2 * r), rim)
    top, bot = ((255, 255, 255), (206, 208, 212)) if not pressed else ((226, 228, 231), (170, 173, 178))
    rows = np.array([lerp(top, bot, max(0, min(1, (yy + 0.5 - (cy - r)) / (2 * r)))) for yy in range(size_h)],
                    dtype=np.float32)[:, None, :]
    paint(a, 0, 0, ellipse_mask(size_w, size_h, cx - r + 1, cy - r + 1, 2 * r - 2, 2 * r - 2), rows)
    # a soft specular band across the upper half
    paint(a, 0, 0, ellipse_mask(size_w, size_h, cx - r + 2, cy - r + 1.2, 2 * r - 4, r - 0.6), WHITE,
          0.55 if not pressed else 0.3)


def groove_h(a, x, y, w, h, split=None):
    """Horizontal slider track: blue fill left of split (absolute x), light grey to the right."""
    m = rr_mask(a.shape[1], a.shape[0], h / 2, x, y, w, h)
    paint(a, 0, 0, m, (60, 66, 76))
    inner = rr_mask(a.shape[1], a.shape[0], h / 2 - 1, x + 1, y + 1, w - 2, h - 2)
    full_h = a.shape[0]
    grey_g = np.array([stops_at([(0, (150, 154, 160)), (0.35, (226, 228, 232)), (1, (250, 250, 251))],
                                 max(0, min(1, (yy + 0.5 - y - 1) / max(1, h - 2)))) for yy in range(full_h)],
                      dtype=np.float32)[:, None, :]
    blue_g = np.array([stops_at([(0, (26, 70, 150)), (0.3, (78, 146, 236)), (1, (44, 112, 214))],
                                 max(0, min(1, (yy + 0.5 - y - 1) / max(1, h - 2)))) for yy in range(full_h)],
                      dtype=np.float32)[:, None, :]
    if split is None:
        paint(a, 0, 0, inner, grey_g)
        return
    left = inner.copy()
    left[:, int(split):] = 0
    right = inner.copy()
    right[:, :int(split)] = 0
    paint(a, 0, 0, left, blue_g)
    paint(a, 0, 0, right, grey_g)


def groove_v(a, x, y, w, h, split=None):
    """Vertical slider track: blue fill below split (absolute row), light grey above."""
    W, H = a.shape[1], a.shape[0]
    paint(a, 0, 0, rr_mask(W, H, w / 2, x, y, w, h), (120, 128, 138))
    inner = rr_mask(W, H, w / 2 - 1, x + 1, y + 1, w - 2, h - 2)
    cols_grey = np.array([stops_at([(0, (178, 182, 188)), (0.4, (228, 230, 234)), (1, (246, 247, 248))],
                                   max(0, min(1, (xx + 0.5 - x - 1) / max(1, w - 2)))) for xx in range(W)],
                         dtype=np.float32)[None, :, :]
    cols_blue = np.array([stops_at([(0, (30, 80, 168)), (0.4, (84, 150, 238)), (1, (48, 116, 216))],
                                   max(0, min(1, (xx + 0.5 - x - 1) / max(1, w - 2)))) for xx in range(W)],
                         dtype=np.float32)[None, :, :]
    if split is None:
        paint(a, 0, 0, inner, cols_grey)
        return
    top = inner.copy()
    top[int(split):, :] = 0
    bot = inner.copy()
    bot[:int(split), :] = 0
    paint(a, 0, 0, top, cols_grey)
    paint(a, 0, 0, bot, cols_blue)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, BODY_MID)
    a[:] = main_bg_column()[22:65]
    paint(a, 0, 0, rr_mask(8, 43, 3), (0, 0, 0))
    paint(a, 0, 0, rr_mask(8, 43, 2.5, 1, 1, 6, 41), (14, 15, 18))
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            paint(a, 0, 0, rr_mask(8, 43, 1.5, 1, y, 6, h), BLUE_MID)
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, WHITE if on else (110, 116, 124))
    return a


def main_titlebar(lit, title="Now Playing"):
    a = new(275, 14)
    nav_bar(a, 0, 0, 275, lit)
    nav_title(a, title, 137, lit)
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, (40, 42, 46))
    for kind, x in [("options", 0), ("minimize", 9), ("close", 18)]:
        b = new(9, 9)
        b[:] = nav_slice(True, 3, 9, 9)
        mini_button(b, 0, 0, kind, True)
        a[0:9, x:x + 9] = b
        b[:] = nav_slice(True, 3, 9, 9)
        mini_button(b, 0, 0, kind, True, pressed=True)
        a[9:18, x:x + 9] = b
    b = nav_slice(True, 3, 9, 9)
    mini_button(b, 0, 0, "shade", True)
    a[18:27, 0:9] = b
    b = nav_slice(True, 3, 9, 9)
    mini_button(b, 0, 0, "shade", True, pressed=True)
    a[18:27, 9:18] = b
    a[0:14, 27:302] = main_titlebar(True)
    a[15:29, 27:302] = main_titlebar(False)
    # window-shade bars (not used by every player; copies of the titlebars)
    a[29:43, 27:302] = main_titlebar(True)
    a[42:56, 27:302] = main_titlebar(False)
    unlit = clutter_bar("")
    lit = clutter_bar("OAIDV")
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = lit[y:y + h]
    return a


def nav_slice(lit, y0, w, h, bar_h=14):
    """Rows y0..y0+h of a navigation bar, w wide (backgrounds for button cells)."""
    t = new(w, bar_h)
    nav_bar(t, 0, 0, w, lit, bar_h)
    return t[y0:y0 + h].copy()


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116)
# ------------------------------------------------------------------------------------------

TOOLBAR_Y = 84


def main_bg_column():
    """The body's colour per row (it's horizontally uniform, so sprites can copy it anywhere)."""
    t = new(1, 116)
    fill_grad(t, 0, 14, 1, 70, [(0, BODY_TOP), (0.55, BODY_MID), (1, BODY_LOW)])
    # the black glossy toolbar: black separator, highlight line, gloss break half way
    y = TOOLBAR_Y
    rect(t, 0, y, 1, 1, (0, 0, 0))
    rect(t, 0, y + 1, 1, 1, (98, 100, 104))
    fill_grad(t, 0, y + 2, 1, 116 - y - 2, [(0, (66, 67, 70)), (0.5, (40, 41, 43)), (0.5, (22, 22, 23)),
                                            (1, (4, 4, 5))])
    return t


def display_box(a, x, y, w, h, r=3):
    """Dark glass inset: dark rim, a light lip along the bottom, glossy top rows, flat glass below."""
    paint(a, x - 1, y, rr_mask(w + 2, h + 1, r + 1), (255, 255, 255), 0.13)        # bottom lip
    paint(a, x - 1, y - 1, rr_mask(w + 2, h + 1, r + 1), (0, 0, 0))
    sub = a[y:y + h, x:x + w]
    tmp = sub.copy()
    tmp[:] = DISP
    for r_, alpha in ((0, 0.16), (1, 0.10), (2, 0.05)):
        tmp[r_] = np.round(np.array(DISP) * (1 - alpha) + np.array((200, 214, 232)) * alpha).astype(np.int32)
    paint(a, x, y, rr_mask(w, h, r), tmp)


LOGO_SVG = os.path.join(HERE, "source", "apple-logo", "logo.svg")


def logo_alpha(h):
    """The logo's coverage at h px tall, rasterised by rsvg-convert (anti-aliased edges kept)."""
    import subprocess
    tmp = os.path.join(OUT, "scratch", f"logo-{h}.png")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    subprocess.run(["/usr/bin/rsvg-convert", "-h", str(h), LOGO_SVG, "-o", tmp], check=True)
    al = np.asarray(Image.open(tmp).convert("RGBA"), dtype=np.float32)[..., 3] / 255.0
    # firm up the faint edge pixels so it stays crisp at sprite size
    return np.clip((al - 0.12) / 0.76, 0, 1)


def apple_emblem(a, x, y, h):
    """A silver (light chrome) logo with a dark drop shadow, on the black toolbar."""
    m = logo_alpha(h)
    mh = m.shape[0]
    paint(a, x, y + 1, m, BLACK, 0.9)
    paint(a, x, y, m, vgrad(mh, [(0, (250, 251, 252)), (0.45, (206, 210, 216)), (0.5, (176, 180, 188)),
                                 (1, (226, 229, 233))]))


def make_main():
    a = new(275, 116)
    col = main_bg_column()
    a[:] = col
    # a soft reflective sheen across the upper body (above the slider rows, which stay uniform)
    yy, xx = np.mgrid[0:116, 0:275].astype(np.float32)
    sheen = np.exp(-(((xx * 0.18 + yy) - 44) / 9.0) ** 2) * ((yy >= 14) & (yy < 54))
    sheen *= np.clip((54 - yy) / 8, 0, 1)
    a[:] = np.round(a + sheen[..., None] * 16).astype(np.int32)
    a[0:14, :] = main_titlebar(True)

    # clutterbar slot (drawn from titlebar.bmp too)
    a[22:65, 10:18] = clutter_bar("")

    # left display: indicator, time, analyzer
    display_box(a, 21, 20, 84, 42)
    for yy_ in (29, 34):
        rect(a, 73, yy_, 2, 2, (210, 214, 220))
    # right display: title row, then kbps/kHz/mono/stereo row
    display_box(a, 109, 21, 159, 15)
    display_box(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, LABEL_TXT)
    draw_text(a, TINY, "KHZ", 169, 44, LABEL_TXT)

    # seek bar groove (posbar.bmp repeats it)
    posbar_groove(a, 16, 72)

    # the emblem (the About button's spot): the Apple logo, small and silver
    apple_emblem(a, 255, 89, 18)
    # outer rims of the window
    rect(a, 0, 14, 1, 102, (0, 0, 0))
    rect(a, 274, 14, 1, 102, (0, 0, 0))
    rect(a, 0, 115, 275, 1, (0, 0, 0))
    rect(a, 1, 14, 1, TOOLBAR_Y - 14, (64, 66, 70))
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36): white pictograms on the black toolbar, a soft glow when pressed
# ------------------------------------------------------------------------------------------


def icon_mask(kind, w, h, scale=1.0):
    cx, cy = w / 2, h / 2
    s = scale
    if kind == "play":
        return poly_mask(w, h, [(cx - 4 * s, cy - 5.5 * s), (cx - 4 * s, cy + 5.5 * s), (cx + 5.5 * s, cy)])
    if kind == "pause":
        return mask(w, h, lambda d, S: (d.rectangle(((cx - 4.5 * s) * S, (cy - 5 * s) * S, (cx - 1.5 * s) * S - 1,
                                                     (cy + 5 * s) * S - 1), fill=255),
                                        d.rectangle(((cx + 1.5 * s) * S, (cy - 5 * s) * S, (cx + 4.5 * s) * S - 1,
                                                     (cy + 5 * s) * S - 1), fill=255)))
    if kind == "stop":
        return mask(w, h, lambda d, S: d.rectangle(((cx - 4.5 * s) * S, (cy - 4.5 * s) * S, (cx + 4.5 * s) * S - 1,
                                                    (cy + 4.5 * s) * S - 1), fill=255))
    if kind in ("previous", "next"):
        def fn(d, S):
            sg = -1 if kind == "previous" else 1
            hh = 4.5 * s
            # two triangles pointing the way, and a bar at the far end
            for ox in (-4.5 * s, 0.0):
                bx = cx + sg * ox if sg == 1 else cx - ox
                tip = bx + sg * 4.5 * s
                d.polygon([(bx * S, (cy - hh) * S), (bx * S, (cy + hh) * S), (tip * S, cy * S)], fill=255)
            bar = cx + sg * 4.5 * s
            x0, x1 = (bar, bar + 2 * s) if sg == 1 else (bar - 2 * s, bar)
            d.rectangle((x0 * S, (cy - hh) * S, x1 * S - 1, (cy + hh) * S - 1), fill=255)
        return mask(w, h, fn)
    if kind == "eject":
        return mask(w, h, lambda d, S: (d.polygon([((cx - 5 * s) * S, (cy + 1 * s) * S), ((cx + 5 * s) * S,
                                                   (cy + 1 * s) * S), (cx * S, (cy - 4.5 * s) * S)], fill=255),
                                        d.rectangle(((cx - 5 * s) * S, (cy + 2.5 * s) * S, (cx + 5 * s) * S - 1,
                                                     (cy + 4.5 * s) * S - 1), fill=255)))
    raise ValueError(kind)


def glow(a, cx, cy, sigma, alpha):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = np.exp(-(((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2) / (2 * sigma * sigma)))
    paint(a, 0, 0, g.astype(np.float32), WHITE, alpha)


def pictogram(a, kind, pressed, dark_bg=True, scale=1.0, cy_off=0.0):
    h, w = a.shape[:2]
    m = icon_mask(kind, w, h, scale)
    if cy_off:
        m = np.roll(m, int(cy_off), axis=0)
    if pressed:
        glow(a, w / 2, h / 2 + cy_off, 5.0, 0.55)
    sh = np.roll(m, -1 if not dark_bg else 1, axis=0)
    paint(a, 0, 0, sh, BLACK, 0.7)
    paint(a, 0, 0, m, vgrad(h, [(0, (255, 255, 255)), (1, (206, 208, 212))]) if not pressed else WHITE)


def make_cbuttons(main):
    a = new(136, 36)
    specs = [("previous", 0, 23, 18, 16), ("play", 23, 23, 18, 39), ("pause", 46, 23, 18, 62),
             ("stop", 69, 23, 18, 85), ("next", 92, 22, 18, 108)]
    for kind, x, w, h, dst in specs:
        for pressed, y in ((False, 0), (True, 18)):
            cell = main[88:88 + h, dst:dst + w].copy()
            pictogram(cell, kind, pressed, scale=0.9 if kind in ("previous", "next") else 1.0)
            a[y:y + h, x:x + w] = cell
    for pressed, y in ((False, 0), (True, 16)):
        cell = main[89:105, 136:158].copy()
        pictogram(cell, "eject", pressed, scale=0.95)
        a[y:y + 16, 114:136] = cell
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85): segmented-control toggles, blue when on
# ------------------------------------------------------------------------------------------


def toggle_cell(bg, label, on, pressed, style_off="black", pad=1):
    a = bg.copy()
    h, w = a.shape[:2]
    gloss_pill(a, 0, pad, w, h - 2 * pad, "blue" if on else style_off, pressed, r=min(4, (h - 2 * pad) / 2 - 0.5))
    if on or style_off == "black":
        ink, sh, sho = WHITE, (0, 0, 0) if not on else BLUE_EDGE, (0, -1)
        if not on:
            ink = (214, 216, 220) if not pressed else (170, 172, 176)
    else:
        ink, sh, sho = (HEADER_TXT if not pressed else (50, 58, 74)), (255, 255, 255), (0, 1)
    text_center(a, TINY, label, w // 2, (h - 5) // 2, ink, shadow=sh, sh=sho)
    return a


def make_shufrep(main):
    a = new(92, 85)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = toggle_cell(main[89:104, 210:238], "REPEAT", on, pressed)
        a[y:y + 15, 28:75] = toggle_cell(main[89:104, 164:211], "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        dst = 219 if label == "EQ" else 242
        bg = main[58:70, dst:dst + 23]
        a[61:73, x:x + 23] = toggle_cell(bg, label, False, pressed, pad=0)
        a[73:85, x:x + 23] = toggle_cell(bg, label, True, pressed, pad=0)
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp (56 x 24), playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, DISP)
    for y, on in ((0, True), (12, False)):
        col = WHITE if on else DIM_TXT
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    # Standard sheet is 42 wide; 48 so the 9px "working" cell at x 39 fits too.
    a = new(48, 9, DISP)
    c = new(9, 9, DISP)
    paint(c, 0, 0, poly_mask(9, 9, [(2, 1), (2, 8), (8, 4.5)]), WHITE)
    a[:, 0:9] = c
    c = new(9, 9, DISP)
    paint(c, 0, 0, mask(9, 9, lambda d, S: (d.rectangle((2 * S, 1 * S, 4 * S - 1, 8 * S - 1), fill=255),
                                             d.rectangle((5 * S, 1 * S, 7 * S - 1, 8 * S - 1), fill=255))), WHITE)
    a[:, 9:18] = c
    rect(a, 18 + 2, 2, 5, 5, WHITE)                   # stopped
    rect(a, 36, 0, 3, 9, DISP)                        # not working
    rect(a, 39 + 1, 3, 1, 3, (90, 160, 240))          # working: a lit dot in its 3px slice
    return a


def digit(a, n, x, y, col=WHITE):
    half = lerp(DISP, col, 0.45)
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + c, y + r, col)
            elif ch == "+":
                px(a, x + c, y + r, half)


def make_numbers(ex):
    a = new(108 if ex else 99, 13, DISP)
    for n in range(10):
        digit(a, n, 9 * n + 2, 1)
    if ex:
        rect(a, 99 + 2, 6, 6, 1, WHITE)               # minus
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
            draw_text(a, FONT5, key, col * 5, row * 6, WHITE)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def posbar_groove(a, x, y):
    """The seek track at (x, y), 248 x 10, drawn in place on canvas a."""
    sub = a[y:y + 10, x:x + 248].copy()
    groove_h(sub, 1, 3, 246, 5)
    a[y:y + 10, x:x + 248] = sub


def make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    for x0, sel in ((248, False), (278, True)):
        cell = main[72:82, 100:129].copy()     # the plain track, uniform along its length
        knob(cell, 14.5, 4.8, 4.6, pressed=sel, shadow=0.4)
        a[0:10, x0:x0 + 29] = cell
    return a


def vol_thumb(bg, pressed):
    """14 x 11 knob cell over a track that's blue to its centre and grey after."""
    cell = bg.copy()
    groove_h(cell, -6, 2, 26, 5, split=7)
    knob(cell, 7, 5.0, 5.2, pressed=pressed, shadow=0.35)
    return cell


def make_volume(main):
    a = new(68, 433)
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        cell = seat.copy()
        level = (i + 1) / 28
        fill_to = 7 + round(level * 54)
        groove_h(cell, 1, 3, 66, 5, split=fill_to)
        a[y:y + 15, 0:68] = cell
    bg = main[58:69, 120:134]
    a[422:433, 0:14] = vol_thumb(bg, True)
    a[422:433, 15:29] = vol_thumb(bg, False)
    return a


def make_balance(main):
    a = new(68, 433)
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        cell = seat.copy()
        groove_h(cell, 1, 3, 36, 5)
        rect(cell, 18, 1, 2, 1, (120, 126, 134))   # centre mark above the track
        rect(cell, 18, 9, 2, 1, (120, 126, 134))
        a[y:y + 15, 9:47] = cell
        a[y:y + 15, 0:9] = main[57:72, 168:177]
        a[y:y + 15, 47:68] = main[57:72, 215:236]
    bg = main[58:69, 120:134].copy()
    cell = bg.copy()
    groove_h(cell, -6, 2, 26, 5)
    t1 = cell.copy()
    knob(t1, 7, 5.0, 5.2, pressed=True, shadow=0.35)
    t2 = cell.copy()
    knob(t2, 7, 5.0, 5.2, pressed=False, shadow=0.35)
    a[422:433, 0:14] = t1
    a[422:433, 15:29] = t2
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = new(275, 14)
    nav_bar(a, 0, 0, 275, lit)
    nav_title(a, "Equalizer", 137, lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(n):
    """14x63 slot on the white panel: a vertical iOS track, blue below the value (n of 0..27)."""
    a = new(14, 63, PANEL)
    v = n / 27
    centre = round((1 - v) * 51) + 5
    groove_v(a, 4, 1, 5, 61, split=centre)
    # the zero mark
    rect(a, 0, 31, 3, 1, (200, 205, 212))
    rect(a, 11, 31, 3, 1, (200, 205, 212))
    return a


def eq_thumb(pressed):
    a = new(11, 11, PANEL)
    groove_v(a, 3, -4, 5, 19, split=5)
    knob(a, 5.5, 5.3, 5.1, pressed=pressed, shadow=0.3)
    return a


def eqmain_bg():
    a = new(275, 116)
    pinstripe(a, 0, 14, 275, 102)
    a[0:14] = eq_titlebar(True)
    # rims
    rect(a, 0, 14, 1, 102, FRAME_EDGE)
    rect(a, 274, 14, 1, 102, FRAME_EDGE)
    rect(a, 0, 115, 275, 1, FRAME_EDGE)
    # slider panel, a grouped-table cell
    paint(a, 16, 37, rr_mask(245, 68, 6), WHITE, 0.8)
    paint(a, 16, 36, rr_mask(245, 68, 6), PANEL_EDGE)
    paint(a, 17, 37, rr_mask(243, 66, 5), PANEL)
    rect(a, 40, 37, 1, 66, (224, 227, 231))
    # graph panel, sitting on the slider panel's top edge
    paint(a, 85, 16, rr_mask(115, 21, 3), PANEL_EDGE)
    paint(a, 86, 17, rr_mask(113, 19, 2), PANEL)
    rect(a, 86, 36, 113, 1, PANEL_EDGE)
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, (140, 148, 158))
        rect(a, 43, yy + 2, 3, 1, (210, 214, 220))
        rect(a, 71, yy + 2, 3, 1, (210, 214, 220))
    text_center(a, TINY, "PREAMP", 28, 107, HEADER_TXT, shadow=WHITE)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 107, HEADER_TXT, shadow=WHITE)
    return a


def make_eqmain():
    a = new(275, 315)
    pinstripe(a, 0, 0, 275, 315)
    bg = eqmain_bg()
    a[0:116] = bg
    for x in [21] + [78 + 18 * i for i in range(10)]:
        a[38:101, x:x + 14] = eq_slider_frame(14)

    # under the window: buttons
    c = nav_slice(True, 3, 9, 9)
    mini_button(c, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = c
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        dst = 14 if label == "ON" else 40
        a[119:131, x:x + w] = toggle_cell(bg[18:30, dst:dst + w], label, on, pressed, style_off="white", pad=0)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    a[164:175, 0:11] = eq_thumb(False)
    a[176:187, 0:11] = eq_thumb(True)
    for n in range(28):
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = eq_slider_frame(n)
    for y, pressed in ((164, False), (176, True)):
        cell = bg[18:30, 217:261].copy()
        bar_button(cell, 0, 0, 44, 12, True, pressed, r=3)
        text_center(cell, TINY, "PRESETS", 22, 4 if not pressed else 4, WHITE, shadow=(36, 50, 72), sh=(0, -1))
        a[y:y + 12, 224:268] = cell
    # graph: white with a faint grid
    g = new(113, 19, PANEL)
    for x in range(0, 113, 12):
        rect(g, 2 + x, 0, 1, 19, (236, 239, 243))
    rect(g, 0, 9, 113, 1, (214, 219, 226))
    a[294:313, 0:113] = g
    for r in range(19):
        px(a, 115, 294 + r, ramp([(30, 100, 220), (46, 120, 230), (30, 100, 220)], r / 18))
    for x in range(113):
        px(a, x, 314, (150, 186, 236) if x % 3 != 2 else PANEL)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

NAV20 = 14      # the navigation bar's rows in a 20px top piece; the rest is frame


def bar20(w, lit, left_edge=False, right_edge=False, list_x0=None, list_x1=None):
    """A top piece: navigation bar over the frame, with the list's top rim on the last row."""
    a = new(w, 20, FRAME)
    nav_bar(a, 0, 0, w, lit, NAV20)
    rect(a, 0, NAV20, w, 1, lerp(FRAME, WHITE, 0.45))
    if list_x0 is not None:
        x1 = w if list_x1 is None else list_x1
        rect(a, list_x0, 19, x1 - list_x0, 1, FRAME_IN)
    if left_edge:
        rect(a, 0, NAV20, 1, 20 - NAV20, FRAME_EDGE)
    if right_edge:
        rect(a, w - 1, NAV20, 1, 20 - NAV20, FRAME_EDGE)
    return a


def toolbar_bg(w, h):
    a = new(w, h)
    fill_grad(a, 0, 0, w, h, [(0, lerp(NAV_TOP, WHITE, 0.08)), (0.5, lerp(NAV_TOP, NAV_BOT, 0.42)),
                              (0.5, lerp(NAV_TOP, NAV_BOT, 0.5)), (1, NAV_BOT)])
    rect(a, 0, 0, w, 1, NAV_EDGE)
    rect(a, 0, 1, w, 1, NAV_HI)
    rect(a, 0, h - 1, w, 1, NAV_EDGE)
    return a


def text_button(t, x, y, w, h, label):
    bar_button(t, x, y, w, h, True, False, r=4)
    text_center(t, TINY, label, x + w // 2, y + (h - 5) // 2, WHITE, shadow=(36, 50, 72), sh=(0, -1))


def scroll_handle(pressed):
    t = new(8, 18, TRACK_GREY)
    rect(t, 0, 0, 1, 18, (206, 211, 217))
    rect(t, 7, 0, 1, 18, (206, 211, 217))
    paint(t, 0, 0, rr_mask(8, 18, 2.5, 1.5, 1, 5, 16), (70, 78, 90) if pressed else (128, 136, 148))
    return t


def make_pledit():
    a = new(280, 186, FRAME)
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar20(25, lit, list_x0=0)
        a[y:y + 20, 0:25] = bar20(25, lit, left_edge=True, list_x0=11)
        t = bar20(100, lit, list_x0=0)
        nav_title(t, "Playlist", 50, lit)
        a[y:y + 20, 26:126] = t
        t = bar20(25, lit, right_edge=True, list_x0=0, list_x1=6)
        mini_button(t, 14, 3, "close", lit)
        # the scroll track's top end
        rect(t, 10, 16, 8, 4, TRACK_GREY)
        rect(t, 10, 16, 8, 1, (206, 211, 217))
        rect(t, 10, 16, 1, 4, (206, 211, 217))
        rect(t, 17, 16, 1, 4, (206, 211, 217))
        a[y:y + 20, 153:178] = t

    # left side tile
    t = new(12, 29, FRAME)
    rect(t, 0, 0, 1, 29, FRAME_EDGE)
    rect(t, 1, 0, 1, 29, lerp(FRAME, WHITE, 0.4))
    rect(t, 11, 0, 1, 29, FRAME_IN)
    a[42:71, 0:12] = t
    # right side tile: list edge, scroll track at 5..12, outer edge
    t = new(20, 29, FRAME)
    rect(t, 0, 0, 1, 29, FRAME_IN)
    rect(t, 5, 0, 8, 29, TRACK_GREY)
    rect(t, 5, 0, 1, 29, (206, 211, 217))
    rect(t, 12, 0, 1, 29, (206, 211, 217))
    rect(t, 18, 0, 1, 29, lerp(FRAME, BLACK, 0.06))
    rect(t, 19, 0, 1, 29, FRAME_EDGE)
    a[42:71, 31:51] = t
    # close pressed, scroll handles
    c = nav_slice(True, 3, 9, 9)
    mini_button(c, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = c
    a[53:71, 52:60] = scroll_handle(False)
    a[53:71, 61:69] = scroll_handle(True)

    # bottom pieces: an iOS toolbar
    t = toolbar_bg(125, 38)
    rect(t, 0, 0, 1, 38, NAV_EDGE)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        text_button(t, bx, 8, 22, 18, lbl)
    a[72:110, 0:125] = t

    t = toolbar_bg(150, 38)
    rect(t, 149, 0, 1, 38, NAV_EDGE)
    # running time readout
    readout(t, 6, 9, 56, 8)
    # mini transport
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        mini_transport_icon(t, kind, 3 + 10 * k, 22 - 1, (36, 50, 72))
        mini_transport_icon(t, kind, 3 + 10 * k, 22, WHITE)
    # mini time
    readout(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, (170, 176, 184))
    rect(t, 84, 22 + 5, 1, 1, (170, 176, 184))
    text_button(t, 106, 8, 22, 18, "LIST")
    grip(t, 147, 35, 4)
    a[72:110, 126:276] = t

    a[0:38, 179:204] = toolbar_bg(25, 38)
    return a


def tri_right(a, x, y, h, col):
    """Solid right-pointing triangle, h tall (odd), tip to the right."""
    half = h // 2
    for r in range(h):
        rect(a, x, y + r, half - abs(r - half) + 1, 1, col)


def tri_left(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x + half + 1 - n, y + r, n, 1, col)


def mini_transport_icon(a, kind, x, y, ink):
    """Crisp 10x10 pictograms for the playlist's mini transport."""
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


def readout(t, x, y, w, h):
    paint(t, x - 1, y - 1, rr_mask(w + 2, h + 2, 2), (36, 50, 72))
    paint(t, x - 1, y, rr_mask(w + 2, h + 1, 2), WHITE, 0.25)
    paint(t, x - 1, y - 1, rr_mask(w + 2, h + 1, 2), (24, 34, 50))
    rect(t, x, y, w, h, DISP)


def grip(t, x, y, n):
    """A resize grip: diagonal rows of white dots with dark shadows, bottom-right corner at (x, y)."""
    for k in range(n):
        for j in range(k + 1):
            gx, gy = x - 3 * k + 3 * j, y - 3 * j
            px(t, gx, gy, (232, 236, 242))
            px(t, gx + 1, gy + 1, (44, 58, 80))


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_bottom(w, grip_, left_edge):
    t = new(w, 14, FRAME)
    rect(t, 0, 0, w, 1, FRAME_IN)
    rect(t, 0, 1, w, 1, lerp(FRAME, WHITE, 0.4))
    rect(t, 0, 13, w, 1, FRAME_EDGE)
    if left_edge:
        rect(t, 0, 0, 1, 14, FRAME_EDGE)
    else:
        rect(t, w - 1, 0, 1, 14, FRAME_EDGE)
    if grip_:
        for k in range(3):
            for j in range(k + 1):
                gx, gy = w - 4 - 3 * k + 3 * j, 10 - 3 * j
                px(t, gx, gy, (250, 251, 252))
                px(t, gx + 1, gy + 1, (120, 130, 144))
    return t


def make_gen():
    a = new(194, 109, FRAME)
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 0:25] = bar20(25, lit, left_edge=True, list_x0=10)
        for x0 in (26, 52, 78, 104):
            a[y:y + 20, x0:x0 + 25] = bar20(25, lit, list_x0=0)
        t = bar20(25, lit, right_edge=True, list_x0=0, list_x1=15)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 130:155] = t

    a[42:56, 0:125] = gen_bottom(125, False, True)
    a[57:71, 0:125] = gen_bottom(125, True, False)
    t = gen_bottom(25, False, False)
    t[:, 24] = t[:, 23]
    a[72:86, 127:152] = t
    # sides: left 11 wide, right 8 (its first column is stretched 3px wider by the app)
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h, FRAME)
        if outer_left:
            rect(t, 0, 0, 1, h, FRAME_EDGE)
            rect(t, 1, 0, 1, h, lerp(FRAME, WHITE, 0.4))
            rect(t, w - 1, 0, 1, h, FRAME_IN)
        else:
            rect(t, w - 1, 0, 1, h, FRAME_EDGE)
        a[42:42 + h, x:x + w] = t
    c = nav_slice(True, 3, 9, 9)
    mini_button(c, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = c

    # letters: each row starts at x 1, letters in their own cells (on the bar's rows 4..10),
    # 1px separators of x 0's colour
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        bar = nav_slice(lit, 4, 194, 7)
        x = 1
        for c_ in GEN_LETTERS:
            w = glyph_w(FONT5, c_) + 1
            a[y:y + 7, x:x + w] = bar[:, x:x + w]
            draw_text(a, FONT5, c_, x, y + 1, WHITE if lit else (244, 244, 245),
                      shadow=TITLE_SHADOW if lit else TITLE_SHADOW_I, sh=(0, -1))
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------

GENEX_COLOURS = [
    (255, 255, 255),   # item background
    (0, 0, 0),         # item text
    (197, 204, 212),   # window background
    (255, 255, 255),   # button text
    (43, 54, 70),      # window text
    (200, 205, 212),   # dividers, sunken borders
    (58, 131, 232),    # selection bar
    (168, 180, 192),   # list header background
    (255, 255, 255),   # list header text
    (226, 231, 237),   # header frame, light
    (125, 137, 152),   # header frame, dark
    (109, 132, 162),   # header frame, pressed
    (197, 204, 212),   # header dead area
    (233, 236, 240),   # scrollbar
    (128, 136, 148),   # scrollbar 2
    (220, 224, 230),   # scrollbar pressed
    (70, 78, 90),      # scrollbar pressed 2
    (233, 236, 240),   # scrollbar dead area
]


def make_genex():
    a = new(256, 64, (197, 204, 212))
    for i, c in enumerate(GENEX_COLOURS):
        px(a, 48 + 2 * i, 0, c)
    # a bar button and its pressed state, for players that read them
    cell = new(47, 15, (197, 204, 212))
    bar_button(cell, 0, 0, 47, 15, True, False, r=4)
    a[1:16, 0:47] = cell
    cell = new(47, 15, (197, 204, 212))
    bar_button(cell, 0, 0, 47, 15, True, True, r=4)
    a[16:31, 0:47] = cell
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------

VISCOLOR = (
    [(DISP, "background"), (DISP_DOTS, "dots")]
    + [(ramp([(255, 255, 255), (200, 228, 255), (110, 176, 246), (52, 120, 228), (30, 74, 176), (18, 44, 120)],
             i / 15), f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}") for i in range(16)]
    + [((255, 255, 255), "oscilloscope 1"), ((200, 228, 255), "oscilloscope 2"), ((140, 192, 248), "oscilloscope 3"),
       ((90, 156, 240), "oscilloscope 4"), ((58, 120, 220), "oscilloscope 5"), ((255, 255, 255), "peaks")]
)

PLEDIT = dict(Normal="#000000", Current="#2A5FB0", NormalBG="#FFFFFF", SelectedBG="#CFE0F7",
              MbBG="#FFFFFF", MbFG="#000000", Font="Arial")


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in VISCOLOR:
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write("[Text]\n" + "".join(f"{k}={v}\n" for k, v in PLEDIT.items()))
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n", encoding="utf-8") as f:
        f.write(
            "iOS 6 — a skin in the style of iOS 6's skeuomorphic look, drawn from scratch "
            "except for the logo. Not affiliated with Apple.\n\n"
            "A classic (Winamp 2.x format) skin: blue-grey glossy navigation bars, a black glossy\n"
            "toolbar with white pictograms, blue-filled sliders with white knobs, pinstripes and\n"
            "white grouped panels. Every bitmap was drawn by a script (gen_skin.py) from gradients,\n"
            "anti-aliased shapes and hand-made pixel fonts; the one exception is the small logo in\n"
            "the main window's emblem spot. A style homage only.\n\n"
            "Apple logo © Apple Inc.; private use only.\n"
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
    for name, arr in sheets.items():
        SHEETS[name[:-4]] = save(arr, name)
    write_text_files()
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "readme.txt"]
    wsz = os.path.join(HERE, "iOS6.wsz")
    with zipfile.ZipFile(wsz, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2012, 9, 19, 0, 0, 0))
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
        blit(img, nums, (99, 0, 9, 13), 38, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    draw_bitmap_text(img, state["title"][:30], 111, 24)
    draw_bitmap_text(img, "256", 111, 43)
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=hex_rgb(PLEDIT["NormalBG"]))
    try:
        font = ImageFont.truetype("/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf", 9)
    except OSError:
        font = ImageFont.load_default()
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=hex_rgb(PLEDIT["SelectedBG"]))
        col = hex_rgb(PLEDIT["Current"]) if i == 1 else hex_rgb(PLEDIT["Normal"])
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
    # a stand-in picture: a cool gradient
    pic = Image.linear_gradient("L").resize((w - 22, h - 34)).convert("RGB")
    arr = np.array(pic).astype(np.float32) / 255
    col = np.stack([30 + 60 * arr[..., 0], 60 + 90 * arr[..., 0], 110 + 120 * arr[..., 0]], -1)
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("Harbour Lights - Glass Tide", "4:12"), ("Paper Planes - Morning Ferry", "3:47"),
            ("Linen - Quiet Settings", "5:03"), ("Pinstripe - Blue Hour", "2:58"),
            ("Slide to Unlock - Afterglow", "6:21"), ("Field Notes - Soft Focus", "3:33"),
            ("Bay Bridge - Night Run", "4:40"), ("Chrome & Felt - Bellows", "3:09"),
            ("Leather Bound - Long Winter", "5:51"), ("Glass Shelf - Low Light", "4:05"),
            ("Coverflow - Pour", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title="IOS 6 - A SKIN IN THAT STYLE  ***", bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="PAUSED: QUIET HOURS (LIVE)", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
