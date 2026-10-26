#!/usr/bin/python3
"""Android skins: classic Winamp 2.x skins in the style of three Android releases.

Themes (one .wsz each): gingerbread (Android 2.3), ics (Android 4.0, Holo Dark),
marshmallow (Android 6.0, Material). Based on skins/ember/gen_skin.py, whose sheet layouts it
keeps; everything is drawn here from code (gradients, anti-aliased shapes, hand-made pixel fonts,
Droid Sans / Roboto for titles). The one mark used is the Android robot, as a pixel emblem.

    /usr/bin/python3 -I gen_skin.py              # all three
    /usr/bin/python3 -I gen_skin.py ics          # some
    /usr/bin/python3 -I gen_skin.py --list

Writes the sheets to out/<theme>/, zips them flat into <Name>.wsz beside this script and draws
preview-<theme>.png (the windows assembled from the sprites the way the app does, 2x).
"""

import os
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py, which finishes each .wsz
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(HERE, "out", "scratch")
FACES = {
    "droid": "/usr/share/fonts/google-droid-sans-fonts/DroidSans.ttf",
    "droid-bold": "/usr/share/fonts/google-droid-sans-fonts/DroidSans-Bold.ttf",
    "roboto": os.path.join(HERE, "source", "roboto", "Roboto.ttf"),
}

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SEP = (255, 0, 255)          # gen.bmp letter separators (never shown)

T = None                     # the theme being built
OUT = None

# ------------------------------------------------------------------------------------------
# Colour and canvas helpers
# ------------------------------------------------------------------------------------------


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(cols, t):
    """Colour along evenly spaced stops, t in 0..1."""
    t = max(0.0, min(1.0, t))
    n = len(cols) - 1
    i = min(n - 1, int(t * n))
    return lerp(cols[i], cols[i + 1], t * n - i)


def hexc(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


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


def vfill(a, x, y, w, h, stops):
    for r in range(h):
        rect(a, x, y + r, w, 1, ramp(stops, r / max(1, h - 1)))


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def grid(a, rows, x, y, col, half=None):
    """Pixel art: '#' full colour, '+' half blended into what's there (or `half` colour)."""
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + c, y + r, col)
            elif ch == "+" and 0 <= y + r < a.shape[0] and 0 <= x + c < a.shape[1]:
                px(a, x + c, y + r, half if half else lerp(tuple(a[y + r, x + c]), col, 0.5))


# Anti-aliased shapes: coverage masks drawn supersampled and boxed down.
SS = 6


def mask(w, h, fn):
    im = Image.new("L", (w * SS, h * SS), 0)
    fn(ImageDraw.Draw(im), SS)
    return np.asarray(im.resize((w, h), Image.BOX), dtype=np.float32) / 255.0


def rr_mask(w, h, r, x=0.0, y=0.0, mw=None, mh=None):
    mw = w - x if mw is None else mw
    mh = h - y if mh is None else mh
    r = max(0.0, min(r, mw / 2, mh / 2))
    return mask(w, h, lambda d, S: d.rounded_rectangle(
        (round(x * S), round(y * S), round((x + mw) * S) - 1, round((y + mh) * S) - 1), radius=round(r * S), fill=255))


def ellipse_mask(w, h, x, y, ew, eh):
    return mask(w, h, lambda d, S: d.ellipse((round(x * S), round(y * S), round((x + ew) * S) - 1,
                                              round((y + eh) * S) - 1), fill=255))


def poly_mask(w, h, pts):
    return mask(w, h, lambda d, S: d.polygon([(round(px_ * S), round(py_ * S)) for px_, py_ in pts], fill=255))


def pie_mask(w, h, cx, cy, r, a0, a1):
    return mask(w, h, lambda d, S: d.pieslice((round((cx - r) * S), round((cy - r) * S), round((cx + r) * S) - 1,
                                               round((cy + r) * S) - 1), a0, a1, fill=255))


def paint(a, x, y, m, col, alpha=1.0):
    """Blends colour over a through coverage mask m placed at (x, y)."""
    h, w = m.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(a.shape[1], x + w), min(a.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    mm = (m[y0 - y:y1 - y, x0 - x:x1 - x] * alpha)[..., None]
    c = np.asarray(col, dtype=np.float32)
    reg = a[y0:y1, x0:x1].astype(np.float32)
    a[y0:y1, x0:x1] = np.round(reg * (1 - mm) + c * mm).astype(np.int32)


def rrect(a, x, y, w, h, r, col, alpha=1.0):
    paint(a, x, y, rr_mask(w, h, r), col, alpha)


def disc(a, cx, cy, d, col, alpha=1.0):
    """A circle of diameter d centred on the coordinate (cx, cy) (pixel k spans k..k+1)."""
    x0, y0 = int(np.floor(cx - d / 2)) - 1, int(np.floor(cy - d / 2)) - 1
    n = int(np.ceil(d)) + 3
    paint(a, x0, y0, ellipse_mask(n, n, cx - d / 2 - x0, cy - d / 2 - y0, d, d), col, alpha)


def poly(a, pts, col, alpha=1.0):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0 = int(np.floor(min(xs))) - 1, int(np.floor(min(ys))) - 1
    w, h = int(np.ceil(max(xs))) - x0 + 2, int(np.ceil(max(ys))) - y0 + 2
    paint(a, x0, y0, poly_mask(w, h, [(p[0] - x0, p[1] - y0) for p in pts]), col, alpha)


# TrueType text (Droid Sans for Gingerbread, Roboto for the later two)
_FONTS = {}


def font(size, wght=400, face=None):
    face = face or T["face"]
    if face == "droid" and wght >= 600:
        face = "droid-bold"
    key = (face, size, wght)
    if key not in _FONTS:
        f = ImageFont.truetype(FACES[face], size)
        if face == "roboto":
            f.set_variation_by_axes([wght, 100])
        _FONTS[key] = f
    return _FONTS[key]


def tt(a, s, x, y, col, size, wght=400, anchor="ls", alpha=1.0, face=None):
    h, w = a.shape[:2]
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).text((x, y), s, fill=255, font=font(size, wght, face), anchor=anchor)
    paint(a, 0, 0, np.asarray(im, dtype=np.float32) / 255.0, col, alpha)


# ------------------------------------------------------------------------------------------
# Pixel fonts (from Ember)
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
# text.bmp cells are 5 wide: the 5-wide M and W get Ember's 4-wide forms there
TEXT5 = dict(FONT5, M=G("#..#", "####", "####", "#..#", "#..#"), W=G("#..#", "#..#", "####", "####", "#..#"))

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


def glyph_w(font_, c):
    return len(font_[c][0])


def text_w(font_, s, gap=1):
    s = [c for c in s if c in font_]
    return sum(glyph_w(font_, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font_, s, x, y, col, gap=1, shadow=None):
    for c in s:
        if c not in font_:
            continue
        g = font_[c]
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    if shadow is not None:
                        px(a, x + k, y + r + 1, shadow)
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col)
        x += len(g[0]) + gap
    return x


def text_center(a, font_, s, cx, y, col, gap=1, shadow=None):
    draw_text(a, font_, s, cx - text_w(font_, s, gap) // 2, y, col, gap, shadow)


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

GB_GREEN = (153, 204, 0)       # #99cc00, Gingerbread's yellow-green
ROBOT = (164, 198, 57)         # #a4c639, the robot's own green
HOLO = (51, 181, 229)          # #33b5e5
HOLO_DK = (0, 153, 204)        # #0099cc
DEEP_ORANGE = (255, 87, 34)    # #ff5722, Google Play Music's accent (Material deep orange 500)
DEEP_ORANGE_DK = (230, 74, 25)  # #e64a19, its status bar (deep orange 700)

THEMES = {
    "gingerbread": dict(
        name="Android 2.3 Gingerbread", wsz="Android-2.3.wsz", face="droid",
        disp=(0, 0, 0), ink=WHITE, digit=WHITE, digit_w=400, accent=GB_GREEN,
        label=(150, 150, 150), dim=(80, 80, 80),
        # the Android 1.x-2.3 progress bar's yellow, and the pressed state's yellow-orange
        fill=[(255, 222, 0), (255, 182, 0), (255, 203, 0)],
        press=[(255, 214, 64), (255, 170, 0), (255, 128, 0)],
        pl=dict(normal="#FFFFFF", current="#99CC00", normalbg="#000000", selectedbg="#B85C00",
                font="Droid Sans"),
        desk=(40, 44, 40),
    ),
    "ics": dict(
        name="Android 4.0 Ice Cream Sandwich", wsz="Android-4.0.wsz", face="roboto",
        disp=(0, 0, 0), ink=HOLO, digit=WHITE, digit_w=250, accent=HOLO,
        label=(138, 138, 138), dim=(70, 70, 70),
        pl=dict(normal="#E8E8E8", current="#33B5E5", normalbg="#000000", selectedbg="#1A5C75",
                font="Roboto"),
        desk=(39, 45, 51),
    ),
    "marshmallow": dict(
        name="Android 6.0 Marshmallow", wsz="Android-6.0.wsz", face="roboto",
        disp=WHITE, ink=(33, 33, 33), digit=(33, 33, 33), digit_w=400, accent=DEEP_ORANGE,
        label=(117, 117, 117), dim=(189, 189, 189),
        pl=dict(normal="#212121", current="#FF5722", normalbg="#FFFFFF", selectedbg="#FFCCBC",
                font="Roboto"),
        desk=(224, 224, 224),
    ),
}
THEME_KEYS = list(THEMES)


def K():
    return T["key"]


def GB():
    return K() == "gingerbread"


def ICS():
    return K() == "ics"


def MM():
    return K() == "marshmallow"


# ------------------------------------------------------------------------------------------
# Shared pieces: backgrounds, the robot, icons
# ------------------------------------------------------------------------------------------

ROBOT_ROWS = [
    "...+.....+...",
    "....#...#....",
    "...+#####+...",
    "..+#######+..",
    "..##.###.##..",
    "..#########..",
    ".............",
    "+.#########.+",
    "#.#########.#",
    "#.#########.#",
    "#.#########.#",
    "+.#########.+",
    "..+#######+..",
    "....##.##....",
    "....+#.#+....",
]


def robot(a, x, y, col=ROBOT):
    grid(a, ROBOT_ROWS, x, y, col)


def main_body_col(y):
    """The main window's background colour at row y (whole-window coordinates)."""
    if GB():
        if 84 <= y <= 112:      # the media-button bar
            if y == 84:
                return (96, 96, 96)
            return ramp([(62, 62, 62), (40, 40, 40), (22, 22, 22)], (y - 85) / 27)
        return ramp([(30, 30, 30), (6, 6, 6), (0, 0, 0)], (y - 14) / 70) if y < 84 else (0, 0, 0)
    if ICS():
        # background_holo_dark: black at the top to #272d33 at the bottom
        c = lerp((0, 0, 0), (39, 45, 51), max(0, (y - 30)) / 85)
        if 84 <= y <= 112:
            c = lerp(c, (0, 0, 0), 0.65)
            if y == 84:
                c = (40, 40, 40)
        return c
    return (250, 250, 250)


def main_body(a, x, y, w, h, y0=0):
    for r in range(h):
        rect(a, x, y + r, w, 1, main_body_col(y0 + y + r))


def card(a, x, y, w, h, fill=WHITE, r=2.0, lift=1):
    """Material card: soft shadow (heavier below) then the white face."""
    for d, al in ((3, 0.05), (2, 0.08), (1, 0.10)):
        rrect_at(a, x - d + 1, y - d + 1 + lift, w + 2 * d - 2, h + 2 * d - 2, r + d, BLACK, al)
    rrect_at(a, x, y, w, h, r, fill)


def rrect_at(a, x, y, w, h, r, col, alpha=1.0):
    if w <= 0 or h <= 0:
        return
    paint(a, x, y, rr_mask(w, h, r), col, alpha)


def display(a, x, y, w, h):
    """A display window: (x, y, w, h) is its flat interior in the display colour."""
    D = T["disp"]
    if GB():
        rrect_at(a, x - 2, y - 2, w + 4, h + 4, 3, (70, 70, 70))
        rrect_at(a, x - 1, y - 1, w + 2, h + 2, 2, (20, 20, 20))
        rect(a, x, y, w, h, D)
    elif ICS():
        rect(a, x - 1, y - 1, w + 2, h + 2, (30, 30, 30))
        rect(a, x, y, w, h, D)
        # the Holo text field's underline, with its little end ticks
        rect(a, x - 1, y + h, w + 2, 1, HOLO_DK)
        rect(a, x - 1, y + h - 2, 1, 2, HOLO_DK)
        rect(a, x + w, y + h - 2, 1, 2, HOLO_DK)
    else:
        card(a, x - 1, y - 1, w + 2, h + 2)
        rect(a, x, y, w, h, D)


# ------------------------------------------------------------------------------------------
# Transport and other glyphs (anti-aliased polygons)
# ------------------------------------------------------------------------------------------


def glyph(a, kind, cx, cy, col, s=1.0, alpha=1.0):
    """Media glyphs centred on the coordinate (cx, cy)."""
    def P(*pts):
        poly(a, [(cx + u * s, cy + v * s) for u, v in pts], col, alpha)

    if kind == "play":
        P((-3, -4.5), (-3, 4.5), (4.5, 0))
    elif kind == "pause":
        P((-3.5, -4), (-1, -4), (-1, 4), (-3.5, 4))
        P((1, -4), (3.5, -4), (3.5, 4), (1, 4))
    elif kind == "stop":
        P((-3.5, -3.5), (3.5, -3.5), (3.5, 3.5), (-3.5, 3.5))
    elif kind == "previous":
        P((-4.5, -4), (-2.5, -4), (-2.5, 4), (-4.5, 4))
        P((4.5, -4), (4.5, 4), (-2.5, 0))
    elif kind == "next":
        P((2.5, -4), (4.5, -4), (4.5, 4), (2.5, 4))
        P((-4.5, -4), (-4.5, 4), (2.5, 0))
    elif kind == "eject":
        P((-4.5, 1), (4.5, 1), (0, -4))
        P((-4.5, 2.5), (4.5, 2.5), (4.5, 4.5), (-4.5, 4.5))


def mini_glyph(a, kind, x, y, col):
    """The playlist's 10x10 mini transport, as small pixel glyphs."""
    cx, cy = x + 5, y + 5
    if kind == "previous":
        rect(a, cx - 3, cy - 2, 1, 5, col)
        for r in range(5):
            n = 2 - abs(r - 2) + 1
            rect(a, cx + 2 - n + 1, cy - 2 + r, n, 1, col)
    elif kind == "play":
        for r in range(7):
            n = 3 - abs(r - 3) + 1
            rect(a, cx - 1, cy - 3 + r, n, 1, col)
    elif kind == "pause":
        rect(a, cx - 2, cy - 2, 2, 5, col)
        rect(a, cx + 1, cy - 2, 2, 5, col)
    elif kind == "stop":
        rect(a, cx - 2, cy - 2, 5, 5, col)
    elif kind == "next":
        for r in range(5):
            n = 2 - abs(r - 2) + 1
            rect(a, cx - 2, cy - 2 + r, n, 1, col)
        rect(a, cx + 2, cy - 2, 1, 5, col)
    elif kind == "eject":
        for r in range(3):
            rect(a, cx - r, cy - 3 + r, 2 * r + 1, 1, col)
        rect(a, cx - 2, cy + 1, 5, 1, col)


REPEAT_ICON = ["........#..", ".#########.", ".#......#..", ".#.........", ".#.......#.",
               ".........#.", "..#......#.", ".#########.", "..#........"]
SHUFFLE_ICON = ["#.....###", ".#.....##", "..#...#.#", ".....#...", "....#....",
                "...#.#...", "..#...#.#", ".#.....##", "#.....###"]


# ------------------------------------------------------------------------------------------
# Titlebar buttons and bars
# ------------------------------------------------------------------------------------------


def bar_glyph(a, x, y, kind, col):
    """9x9 titlebar glyphs."""
    if kind == "options":
        if GB():                       # the 2.x menu key's glyph: three bars
            for r in (2, 4, 6):
                rect(a, x + 2, y + r, 5, 1, col)
        else:                          # the Holo / Material overflow menu: three dots
            for r in (1, 4, 7):
                rect(a, x + 4, y + r, 1, 1, col)
                px(a, x + 4, y + r, col)
            for r in (1, 4, 7):
                rect(a, x + 4, y + r, 1, 1, col)
    elif kind == "minimize":
        rect(a, x + 2, y + 6, 5, 1, col)
    elif kind == "shade":
        rect(a, x + 2, y + 2, 5, 1, col)
        rect(a, x + 2, y + 2, 1, 5, col)
        rect(a, x + 6, y + 2, 1, 5, col)
        rect(a, x + 2, y + 6, 5, 1, col)
        rect(a, x + 2, y + 3, 5, 1, col)
    elif kind == "close":
        for i in range(5):
            px(a, x + 2 + i, y + 2 + i, col)
            px(a, x + 6 - i, y + 2 + i, col)


def bar_button(a, x, y, kind, lit, pressed, on_light=False):
    """Draws a titlebar button over the bar already painted at (x, y)."""
    if GB():
        ink = (220, 220, 220) if lit else (130, 130, 130)
        if pressed:
            for r in range(9):
                rect(a, x, y + r, 9, 1, ramp(T["press"], r / 8))
            ink = (40, 24, 0)
    elif ICS():
        ink = (230, 230, 230) if lit else (120, 120, 120)
        if pressed:
            rect(a, x, y, 9, 9, lerp(tuple(a[y + 4, x + 4]), HOLO, 0.55))
            ink = WHITE
    else:
        ink = WHITE if not on_light else (117, 117, 117)
        if not lit and not on_light:
            ink = (245, 245, 245)
        if pressed:
            disc(a, x + 4.5, y + 4.5, 9, WHITE if not on_light else BLACK, 0.3 if not on_light else 0.12)
    bar_glyph(a, x, y, kind, ink)


def status_bg(w, lit, h=14):
    a = new(w, h)
    if GB():
        stops = [(70, 70, 70), (34, 34, 34), (10, 10, 10)] if lit else [(46, 46, 46), (24, 24, 24), (8, 8, 8)]
        vfill(a, 0, 0, w, h, stops)
        rect(a, 0, h - 1, w, 1, BLACK)
    elif ICS():
        rect(a, 0, 0, w, h, BLACK)
    else:
        rect(a, 0, 0, w, h, DEEP_ORANGE_DK if lit else (158, 158, 158))
    return a


def status_icons(a, lit):
    """Notification icon on the left; data, signal, battery and the clock on the right."""
    yb = 11                                          # the icons' bottom row + 1
    if GB():
        icon = GB_GREEN if lit else (110, 110, 110)
        note = (210, 210, 210) if lit else (110, 110, 110)
        clock = (230, 230, 230) if lit else (130, 130, 130)
    elif ICS():
        icon = HOLO if lit else (100, 100, 100)
        note = WHITE if lit else (110, 110, 110)
        clock = WHITE if lit else (120, 120, 120)
    else:
        icon = note = clock = WHITE if lit else (238, 238, 238)
    # notification: a beamed note (the music app playing)
    grid(a, ["..#####", "..#...#", "..#...#", "..#...#", "###.###", "###.###"], 20, 4, note)
    # clock
    tt(a, "12:30", 239, yb, clock, 10, 400 if not MM() else 500, anchor="rs")
    cw = int(round(font(10, 400 if not MM() else 500).getlength("12:30")))
    x = 239 - cw - 4
    # battery: 5 x 9 with a nub
    bx = x - 5
    rect(a, bx + 1, yb - 9, 3, 1, icon)
    rect(a, bx, yb - 8, 5, 8, icon)
    if GB():
        rect(a, bx + 1, yb - 7, 3, 1, lerp(icon, BLACK, 0.4))
    elif ICS():
        rect(a, bx, yb - 8, 5, 8, (200, 200, 200) if lit else (100, 100, 100))
        rect(a, bx + 1, yb - 7, 3, 2, BLACK)
    x = bx - 3
    if GB():
        # four signal bars, then the "3G" data indicator
        for i, hgt in enumerate((3, 5, 7, 9)):
            rect(a, x - 10 + 3 * i, yb - hgt, 2, hgt, icon)
        x -= 13
        draw_text(a, TINY, "3G", x - 7, yb - 7, icon)
    else:
        poly(a, [(x - 9, yb), (x, yb), (x, yb - 9)], icon)                  # signal wedge
        x -= 12
        paint(a, 0, 0, pie_mask(a.shape[1], a.shape[0], x - 5, yb + 0.5, 10, 225, 315), icon)   # wifi fan


def main_titlebar(lit):
    a = status_bg(275, lit)
    status_icons(a, lit)
    for kind, x in (("options", 6), ("minimize", 244), ("shade", 254), ("close", 264)):
        bar_button(a, x, 3, kind, lit, False)
    return a


def win_bar_bg(w, h, lit):
    """EQ, playlist and generic windows: Gingerbread's title bar, the Holo action bar, the Material
    app bar. Rows 0..15 are the bar; a 20px bar's last rows are the frame above the list."""
    a = new(w, h)
    bar_h = 16 if h == 20 else h
    if GB():
        stops = [(112, 112, 112), (72, 72, 72), (46, 46, 46)] if lit else [(70, 70, 70), (48, 48, 48), (34, 34, 34)]
        vfill(a, 0, 0, w, bar_h, stops)
        rect(a, 0, 0, w, 1, (150, 150, 150) if lit else (90, 90, 90))
        rect(a, 0, bar_h - 1, w, 1, BLACK)
        if h == 20:
            rect(a, 0, 16, w, 4, (12, 12, 12))
            rect(a, 0, 19, w, 1, (34, 34, 34))
    elif ICS():
        rect(a, 0, 0, w, h, (28, 28, 28) if lit else (20, 20, 20))
        line = 15 if h == 20 else h - 1
        rect(a, 0, line - (1 if lit else 0), w, 2 if lit else 1, HOLO if lit else (60, 60, 60))
        if h == 20:
            rect(a, 0, 16, w, 4, BLACK)
    else:
        rect(a, 0, 0, w, bar_h, DEEP_ORANGE if lit else (224, 224, 224))
        if h == 20:
            rect(a, 0, 16, w, 4, (250, 250, 250))
            for r, al in ((16, 0.22), (17, 0.10), (18, 0.04)):
                rect(a, 0, r, w, 1, lerp((250, 250, 250), BLACK, al))
    return a


def title_col(lit):
    if GB():
        return WHITE if lit else (150, 150, 150)
    if ICS():
        return WHITE if lit else (130, 130, 130)
    return WHITE if lit else (117, 117, 117)


def bar_title(a, s, cx, baseline, lit):
    if GB():
        tt(a, s, cx + 1, baseline + 1, BLACK, 11, 400, anchor="ms", alpha=0.8)
        tt(a, s, cx, baseline, title_col(lit), 11, 400, anchor="ms")
    elif ICS():
        tt(a, s, cx, baseline, title_col(lit), 11, 350, anchor="ms")
    else:
        tt(a, s, cx, baseline, title_col(lit), 11, 500, anchor="ms")


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43)
    main_body(a, 0, 0, 8, 43, 22)
    if GB():
        rrect_at(a, 0, 0, 8, 43, 2, (40, 40, 40))
        rrect_at(a, 1, 1, 6, 41, 1.5, (8, 8, 8))
    elif ICS():
        rect(a, 0, 0, 8, 43, (14, 14, 14))
        rect(a, 0, 0, 1, 43, (40, 40, 40))
    else:
        rect(a, 0, 0, 8, 43, (238, 238, 238))
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        gy = y + (h - 5) // 2
        if on and MM():
            rect(a, 1, y, 6, h, (255, 204, 188))
        draw_text(a, TINY, letter, 2, gy, T["accent"] if on else T["label"] if not MM() else (158, 158, 158))
    return a


def make_titlebar():
    a = new(344, 87, T["disp"])
    lit, unlit = main_titlebar(True), main_titlebar(False)
    a[0:14, 27:302] = lit
    a[15:29, 27:302] = unlit
    a[29:43, 27:302] = lit
    a[42:56, 27:302] = unlit
    cells = {"options": ((0, 0), (0, 9), 6), "minimize": ((9, 0), (9, 9), 244), "close": ((18, 0), (18, 9), 264),
             "shade": ((0, 18), (9, 18), 254)}
    for kind, ((nx, ny), (px_, py_), bx) in cells.items():
        base = status_bg(275, True)
        status_icons(base, True)
        b = base[3:12, bx:bx + 9].copy()
        n = b.copy()
        bar_button(n, 0, 0, kind, True, False)
        p = b.copy()
        bar_button(p, 0, 0, kind, True, True)
        a[ny:ny + 9, nx:nx + 9] = n
        a[py_:py_ + 9, px_:px_ + 9] = p
    off = clutter_bar("")
    on = clutter_bar("OAIDV")
    a[0:43, 304:312] = off
    a[0:43, 312:320] = off
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = on[y:y + h]
    return a


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116)
# ------------------------------------------------------------------------------------------


def main_plain():
    a = new(275, 116)
    main_body(a, 0, 0, 275, 116)
    a[0:14, :] = main_titlebar(True)
    if MM():
        # the control card along the bottom
        card(a, 4, 85, 267, 27, r=2)
    # displays
    display(a, 21, 20, 84, 42)
    display(a, 109, 21, 159, 15)
    display(a, 109, 40, 159, 14)
    # window edge
    edge = {"gingerbread": (54, 54, 54), "ics": (44, 48, 52), "marshmallow": (200, 200, 200)}[K()]
    rect(a, 0, 14, 1, 102, edge)
    rect(a, 274, 14, 1, 102, edge)
    rect(a, 0, 115, 275, 1, edge)
    return a


def make_main(plain):
    a = plain.copy()
    a[22:65, 10:18] = clutter_bar("")
    # the time's colon
    for yy in (30, 35):
        if MM() or ICS():
            disc(a, 74.0, yy + 0.0, 2.0, T["digit"])
        else:
            rect(a, 73, yy - 1, 2, 2, T["digit"])
    lab = T["label"]
    draw_text(a, TINY, "KBPS", 129, 44, lab)
    draw_text(a, TINY, "KHZ", 169, 44, lab)
    # the robot in the About spot
    robot(a, 253, 91)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36)
# ------------------------------------------------------------------------------------------

CB = [("previous", 0, 23, 16), ("play", 23, 23, 39), ("pause", 46, 23, 62), ("stop", 69, 23, 85),
      ("next", 92, 22, 108)]


def gb_face(a, x, y, w, h, pressed, light=False, r=2.5):
    """Android 2.x buttons: the light grey default button, or the dark media button; both
    turn yellow-orange when pressed."""
    if pressed:
        stops = T["press"]
        edge = (150, 80, 0)
    elif light:
        stops = [(250, 250, 250), (222, 222, 222), (188, 188, 188)]
        edge = (100, 100, 100)
    else:
        stops = [(86, 86, 86), (52, 52, 52), (30, 30, 30)]
        edge = (8, 8, 8)
    rrect_at(a, x, y, w, h, r, edge)
    face = new(w - 2, h - 2)
    vfill(face, 0, 0, w - 2, h - 2, stops)
    m = rr_mask(w - 2, h - 2, max(0.5, r - 1))
    reg = a[y + 1:y + h - 1, x + 1:x + w - 1].astype(np.float32)
    a[y + 1:y + h - 1, x + 1:x + w - 1] = np.round(reg * (1 - m[..., None]) + face * m[..., None]).astype(np.int32)
    if not pressed:
        hl = (255, 255, 255) if light else (120, 120, 120)
        rect(a, x + 2, y + 1, w - 4, 1, hl)


def holo_face(a, x, y, w, h, pressed, on_bar=False):
    """Holo dark button: a flat dark grey face, a lighter top edge; Holo blue when pressed."""
    if pressed:
        rect(a, x, y, w, h, (28, 103, 130))
        rect(a, x, y, w, 1, (60, 160, 200))
    else:
        rect(a, x, y, w, h, (52, 52, 52) if not on_bar else (40, 40, 40))
        rect(a, x, y, w, 1, (82, 82, 82))
        rect(a, x, y + h - 1, w, 1, (24, 24, 24))


def make_cbuttons(plain):
    a = new(136, 36)
    for kind, sx, w, mx in CB:
        for pressed, sy in ((False, 0), (True, 18)):
            cell = plain[88:106, mx:mx + w].copy()
            transport_cell(cell, kind, w, 18, pressed)
            a[sy:sy + 18, sx:sx + w] = cell
    for pressed, sy in ((False, 0), (True, 16)):
        cell = plain[89:105, 136:158].copy()
        transport_cell(cell, "eject", 22, 16, pressed)
        a[sy:sy + 16, 114:136] = cell
    return a


def transport_cell(c, kind, w, h, pressed):
    cx, cy = w / 2, h / 2
    if GB():
        gb_face(c, 0, 0, w, h, pressed, r=2.5)
        if pressed:
            glyph(c, kind, cx, cy + 0.5, (120, 60, 0), 0.9)
            glyph(c, kind, cx, cy, WHITE, 0.9)
        else:
            glyph(c, kind, cx, cy + 1, BLACK, 0.9)
            glyph(c, kind, cx, cy, WHITE, 0.9)
    elif ICS():
        if pressed:
            rect(c, 0, 0, w, h, lerp(tuple(c[h // 2, 0]), HOLO, 0.5))
        rect(c, w - 1, 3, 1, h - 6, (44, 44, 44))       # Holo's thin dividers between buttons
        glyph(c, kind, cx - 0.5, cy, WHITE, 0.85)
    else:
        grey = (97, 97, 97)
        if kind == "play":
            # the floating action button
            for d, al in ((2.0, 0.10), (1.0, 0.16)):
                disc(c, cx, cy + d * (1.5 if pressed else 1), 16 + d, BLACK, al)
            disc(c, cx, cy, 16, DEEP_ORANGE_DK if pressed else DEEP_ORANGE)
            glyph(c, "play", cx + 0.5, cy, WHITE, 0.75)
        else:
            if pressed:
                disc(c, cx, cy, 16, BLACK, 0.12)
            glyph(c, kind, cx, cy, grey, 0.85)


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle_cell(c, w, h, label, on, pressed, icon=None):
    """Android toggle buttons. 2.3 and 4.0: the ToggleButton (label over an indicator light);
    6.0: an icon or label tinted with the accent when on."""
    if GB():
        gb_face(c, 0, 0, w, h, pressed, light=True, r=2)
        ink = BLACK if not pressed else (60, 30, 0)
        tw = text_w(TINY, label)
        ty = 2 if h >= 15 else 1
        draw_text(c, TINY, label, (w - tw) // 2, ty + (1 if h >= 15 else 0), ink)
        ly = h - 4 if h >= 15 else h - 4
        lw = min(w - 8, max(9, tw))
        lx = (w - lw) // 2
        if on:
            rect(c, lx, ly, lw, 2, (124, 214, 0))
            rect(c, lx, ly, lw, 1, (190, 250, 90))
        else:
            rect(c, lx, ly, lw, 2, (128, 128, 128))
            rect(c, lx, ly + 1, lw, 1, (110, 110, 110))
    elif ICS():
        holo_face(c, 0, 0, w, h, pressed)
        ink = WHITE if (on or pressed) else (170, 170, 170)
        tw = text_w(TINY, label)
        draw_text(c, TINY, label, (w - tw) // 2, 2 if h >= 15 else 1, ink)
        lw = w - 8
        rect(c, 4, h - 4, lw, 2 if h >= 15 else 2, HOLO if on else (90, 90, 90))
        if h < 15:
            rect(c, 4, h - 4, lw, 1, HOLO if on else (90, 90, 90))
    else:
        if pressed:
            rrect_at(c, 1, 0, w - 2, h, 3, BLACK, 0.10)
        ink = DEEP_ORANGE if on else (117, 117, 117)
        if icon is not None:
            iw, ih = len(icon[0]), len(icon)
            grid(c, icon, (w - iw) // 2, (h - ih) // 2, ink)
        else:
            tw = text_w(TINY, label)
            draw_text(c, TINY, label, (w - tw) // 2, 2, ink)
            if on:
                rect(c, (w - tw) // 2 - 1, h - 3, tw + 2, 2, DEEP_ORANGE)


def make_shufrep(plain):
    a = new(92, 85)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        c = plain[89:104, 210:238].copy()
        toggle_cell(c, 28, 15, "REPEAT", on, pressed, REPEAT_ICON if MM() else None)
        a[y:y + 15, 0:28] = c
        c = plain[89:104, 164:211].copy()
        toggle_cell(c, 47, 15, "SHUFFLE", on, pressed, SHUFFLE_ICON if MM() else None)
        a[y:y + 15, 28:75] = c
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        for on, y in ((False, 61), (True, 73)):
            mx = 219 if label == "EQ" else 242
            c = plain[58:70, mx:mx + 23].copy()
            toggle_cell(c, 23, 12, label, on, pressed)
            a[y:y + 12, x:x + 23] = c
    return a


# ------------------------------------------------------------------------------------------
# monoster, playpaus, numbers, nums_ex, text
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T["disp"])
    for y, on in ((0, True), (12, False)):
        col = T["accent"] if on else T["dim"]
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 42, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T["disp"])
    acc = T["accent"]
    poly(a, [(2, 0.5), (2, 8.5), (8, 4.5)], acc)                        # playing
    rect(a, 11, 1, 2, 7, acc)                                            # paused
    rect(a, 14, 1, 2, 7, acc)
    rect(a, 20, 2, 5, 5, acc)                                            # stopped
    rect(a, 36, 0, 3, 9, T["disp"])                                      # not working
    rect(a, 40, 3, 1, 3, acc)                                            # working
    return a


def digit_cell(ch):
    c = new(9, 13, T["disp"])
    if ch == "-":
        rect(c, 2, 6, 5, 1, T["digit"])
        return c
    if ch == " ":
        return c
    size = 16 if GB() else 16
    tt(c, ch, 4.5, 12.4, T["digit"], size, T["digit_w"], anchor="ms")
    return c


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["disp"])
    for n in range(10):
        a[0:13, 9 * n:9 * n + 9] = digit_cell(str(n))
    if ex:
        a[0:13, 99:108] = digit_cell("-")
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
            key = ch if ch in TEXT5 else ch.upper()
            draw_text(a, TEXT5, key, col * 5, row * 6, T["ink"])
    return a


# ------------------------------------------------------------------------------------------
# Sliders: posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def track_cols():
    """(track colour, fill colour) for the thin Holo / Material lines."""
    if ICS():
        return (78, 78, 78), HOLO
    return (189, 189, 189), DEEP_ORANGE


def hline(a, x, y_centre, w, col, soft=True):
    """A thin horizontal line on the pixel row y_centre, with soft half rows round it (a 2px look)."""
    rect(a, x, y_centre, w, 1, col)
    if soft:
        for yy in (y_centre - 1, y_centre + 1):
            for xx in range(x, x + w):
                px(a, xx, yy, lerp(tuple(a[yy, xx]), col, 0.35))


def gb_track(a, x, y, w, h, upto=None):
    """Android 2.x progress bar: grey rounded track, the yellow progress over it."""
    r = h / 2
    rrect_at(a, x - 1, y - 1, w + 2, h + 2, r + 1, (8, 8, 8))
    t = new(w, h)
    vfill(t, 0, 0, w, h, [(157, 158, 157), (90, 93, 90), (116, 118, 116)])
    if upto is not None and upto > 0:
        f = new(w, h)
        vfill(f, 0, 0, w, h, T["fill"])
        t[:, :upto] = f[:, :upto]
    m = rr_mask(w, h, r)
    reg = a[y:y + h, x:x + w].astype(np.float32)
    a[y:y + h, x:x + w] = np.round(reg * (1 - m[..., None]) + t * m[..., None]).astype(np.int32)


def gb_knob(a, cx, cy, d, pressed):
    disc(a, cx, cy + 0.6, d, BLACK, 0.6)
    if pressed:
        disc(a, cx, cy, d, (200, 110, 0))
        disc(a, cx, cy - 0.3, d - 1.6, (255, 196, 40))
        disc(a, cx - 0.6, cy - 1.0, d * 0.45, (255, 236, 150))
    else:
        disc(a, cx, cy, d, (96, 96, 96))
        disc(a, cx, cy - 0.3, d - 1.6, (214, 214, 214))
        disc(a, cx - 0.6, cy - 1.0, d * 0.45, (250, 250, 250))


def holo_knob(a, cx, cy, pressed, d_halo=10, d_dot=5):
    if ICS():
        disc(a, cx, cy, d_halo, HOLO, 0.45 if pressed else 0.25)
        disc(a, cx, cy, d_dot + (1.5 if pressed else 0), HOLO)
    else:
        if pressed:
            disc(a, cx, cy, d_halo, DEEP_ORANGE, 0.22)
        disc(a, cx, cy, d_dot + (2 if pressed else 0), DEEP_ORANGE)


def make_posbar(plain):
    a = new(307, 10)
    bg = plain[72:82, 16:264].copy()
    if GB():
        gb_track(bg, 1, 2, 246, 6)
    else:
        trk, _ = track_cols()
        rect(bg, 1, 4, 246, 2, trk)
    a[0:10, 0:248] = bg
    for sx, pressed in ((248, False), (278, True)):
        c = bg[:, 100:129].copy()
        if GB():
            gb_knob(c, 14.5, 5.0, 9.6, pressed)
        else:
            holo_knob(c, 14.5, 5.0, pressed, 10, 6 if ICS() else 7)
        a[0:10, sx:sx + 29] = c
    return a


def vol_frame(bg, level):
    """68x13 volume frame filled up to the thumb's centre (x 7 + level * 54)."""
    c = bg.copy()
    fill_to = 7 + round(level * 54)
    if GB():
        gb_track(c, 2, 4, 64, 5, upto=fill_to - 2)
    else:
        trk, fl = track_cols()
        hline(c, 2, 6, 64, trk)
        if fill_to > 2:
            hline(c, 2, 6, fill_to - 2, fl)
    return c


def vol_thumbs(a, bg, level_cut=7):
    """Thumbs 14x11 at (15, 422) normal and (0, 422) pressed; their backgrounds show the track
    filled on the left half, so they sit on the fill's end."""
    for sx, pressed in ((15, False), (0, True)):
        f = vol_frame(bg, 0.5)                   # fill to x 34: crop it round that point
        c = f[1:12, 34 - 7:34 + 7].copy()
        if GB():
            gb_knob(c, 7.0, 5.5, 10.4, pressed)
        else:
            holo_knob(c, 7.0, 5.5, pressed, 11, 6 if ICS() else 7)
        a[422:433, sx:sx + 14] = c


def make_volume(plain):
    a = new(68, 433)
    bg = plain[57:70, 107:175].copy()
    for i in range(28):
        a[i * 15:i * 15 + 13, :] = vol_frame(bg, (i + 1) / 28)
        a[i * 15 + 13:i * 15 + 15, :] = plain[70:72, 107:175]
    vol_thumbs(a, bg)
    return a


def make_balance(plain):
    a = new(68, 433)
    bg = plain[57:70, 177:215].copy()
    for i in range(28):
        c = bg.copy()
        if GB():
            gb_track(c, 2, 4, 34, 5)
        else:
            trk, _ = track_cols()
            hline(c, 2, 6, 34, trk)
        mark = T["accent"] if i == 0 else (T["label"] if not MM() else (158, 158, 158))
        rect(c, 18, 0, 2, 2, mark)
        rect(c, 18, 11, 2, 2, mark)
        a[i * 15:i * 15 + 13, 9:47] = c
        a[i * 15:i * 15 + 13, 0:9] = plain[57:70, 168:177]
        a[i * 15:i * 15 + 13, 47:68] = plain[57:70, 215:236]
    # thumbs: on the neutral track
    clean = bg.copy()
    if GB():
        gb_track(clean, 2, 4, 34, 5)
    else:
        hline(clean, 2, 6, 34, track_cols()[0])
    for sx, pressed in ((15, False), (0, True)):
        c = clean[1:12, 5:19].copy()
        if GB():
            gb_knob(c, 7.0, 5.5, 10.4, pressed)
        else:
            holo_knob(c, 7.0, 5.5, pressed, 11, 6 if ICS() else 7)
        a[422:433, sx:sx + 14] = c
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = win_bar_bg(275, 14, lit)
    bar_title(a, "Equalizer", 137, 10 if ICS() else 11, lit)
    bar_button(a, 264, 3, "close", lit, False, on_light=MM() and not lit)
    return a


def eq_body_col(y):
    if GB():
        return ramp([(26, 26, 26), (0, 0, 0)], (y - 14) / 100)
    if ICS():
        return lerp((0, 0, 0), (39, 45, 51), max(0, y - 14) / 101)
    return (250, 250, 250)


def eq_window():
    a = new(275, 116)
    for r in range(116):
        rect(a, 0, r, 275, 1, eq_body_col(r))
    a[0:14, :] = eq_titlebar(True)
    if MM():
        card(a, 12, 36, 251, 74)
        # the graph: a flat outlined field (a card's shadow would show between the slider slots)
        rrect_at(a, 84, 15, 117, 23, 2, (224, 224, 224))
        rect(a, 85, 16, 115, 21, WHITE)
    elif GB():
        rrect_at(a, 12, 35, 251, 70, 3, (60, 60, 60))
        rrect_at(a, 13, 36, 249, 68, 2.5, (14, 14, 14))
        rrect_at(a, 84, 15, 117, 23, 2, (70, 70, 70))
        rect(a, 85, 16, 115, 21, BLACK)
    else:
        rect(a, 16, 103, 245, 1, (51, 51, 51))
        rect(a, 85, 16, 115, 21, BLACK)
        rect(a, 85, 37, 115, 1, HOLO_DK)
    # dB marks between the preamp and the bands
    lab = T["label"]
    sep = {"gingerbread": (48, 48, 48), "ics": (40, 40, 40), "marshmallow": (224, 224, 224)}[K()]
    rect(a, 39, 39, 1, 62, sep)
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, lab)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        a[38:101, x:x + 14] = eq_slider_frame(a[38:101, x:x + 14].copy(), 14 / 27)
    lab2 = T["label"] if not GB() else (170, 170, 170)
    text_center(a, TINY, "PREAMP", 28, 106 if not MM() else 104, lab2)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106 if not MM() else 104, lab2)
    edge = {"gingerbread": (54, 54, 54), "ics": (44, 48, 52), "marshmallow": (200, 200, 200)}[K()]
    rect(a, 0, 14, 1, 102, edge)
    rect(a, 274, 14, 1, 102, edge)
    rect(a, 0, 115, 275, 1, edge)
    return a


def eq_slider_frame(bg, v):
    """14x63 slot: a vertical track on column 6, filled from the bottom to the thumb's centre."""
    c = bg.copy()
    centre = round((1 - v) * 51 + 5.5)           # first filled row
    if GB():
        t = new(5, 59)
        vfill_h(t, [(157, 158, 157), (90, 93, 90), (116, 118, 116)])
        f = new(5, 59)
        vfill_h(f, T["fill"])
        t[centre - 2:, :] = f[centre - 2:, :]
        rrect_at(c, 3, 1, 7, 61, 3.5, (8, 8, 8))
        m = rr_mask(5, 59, 2.5)
        reg = c[2:61, 4:9].astype(np.float32)
        c[2:61, 4:9] = np.round(reg * (1 - m[..., None]) + t * m[..., None]).astype(np.int32)
    else:
        trk, fl = track_cols()
        for r in range(3, 60):
            col = fl if r >= centre else trk
            px(c, 6, r, col)
            for xx in (5, 7):
                px(c, xx, r, lerp(tuple(c[r, xx]), col, 0.35))
    return c


def vfill_h(a, stops):
    """Horizontal gradient across a's columns (a vertical track's rounded shading)."""
    w = a.shape[1]
    for k in range(w):
        a[:, k] = ramp(stops, k / max(1, w - 1))


def eq_toggle(c, w, h, label, on, pressed):
    if GB() or ICS():
        toggle_cell(c, w, h, label, on, pressed)
        return
    # Material: a switch for ON, a checkbox for AUTO
    if pressed:
        rrect_at(c, 0, 0, w, h, 3, BLACK, 0.08)
    if label == "ON":
        tx = 2
        draw_text(c, TINY, "ON", tx, 4, (97, 97, 97))
        trk = (255, 171, 145) if on else (189, 189, 189)
        rrect_at(c, 11, 4, 13, 5, 2.5, trk)
        cx = 20.5 if on else 14.5
        disc(c, cx, 6.9, 8, BLACK, 0.18)
        disc(c, cx, 6.5, 8, DEEP_ORANGE if on else (245, 245, 245))
        if not on:
            disc(c, cx, 6.5, 8, (180, 180, 180), 0.0)
    else:
        bx, by = 2, 2
        if on:
            rrect_at(c, bx, by, 8, 8, 1.2, DEEP_ORANGE)
            grid(c, ["......", ".....#", "....#.", "#..#..", ".##...", "......"], bx + 1, by + 1, WHITE)
        else:
            rrect_at(c, bx, by, 8, 8, 1.2, (117, 117, 117))
            rect(c, bx + 1, by + 1, 6, 6, tuple(c[0, 0]) if not pressed else tuple(c[by + 4, bx + 4 - 3]))
            rrect_at(c, bx + 1, by + 1, 6, 6, 0.5, (250, 250, 250))
        draw_text(c, TINY, "AUTO", 13, 4, (97, 97, 97))


def presets_cell(c, pressed):
    if GB():
        gb_face(c, 0, 0, 44, 12, pressed, light=True, r=2)
        text_center(c, TINY, "PRESETS", 22, 4 - 1, BLACK)
    elif ICS():
        holo_face(c, 0, 0, 44, 12, pressed)
        text_center(c, TINY, "PRESETS", 22, 3, WHITE)
    else:
        if pressed:
            rrect_at(c, 0, 0, 44, 12, 2, BLACK, 0.1)
        text_center(c, TINY, "PRESETS", 22, 4, DEEP_ORANGE)


def eq_thumb(bg, pressed):
    c = bg.copy()
    if GB():
        gb_knob(c, 5.5, 5.5, 10.4, pressed)
    else:
        holo_knob(c, 5.5, 5.5, pressed, 11, 6 if ICS() else 7)
    return c


def eq_close_pressed():
    t = eq_titlebar(True)
    bar_button(t, 264, 3, "close", True, True)
    return t[3:12, 264:273]


def make_eqmain():
    a = new(275, 315, T["disp"])
    win = eq_window()
    a[0:116, :] = win
    # the window's plain background under the sliders: one slot without its track
    slot_bg = win[38:101, 21:35].copy()
    plain_slot = new(14, 63)
    for r in range(63):
        plain_slot[r, :] = eq_body_col(38 + r) if not MM() else WHITE
    if GB():
        plain_slot = slot_bg.copy()
        plain_slot[:, :] = slot_bg[:, 0:1]
    # buttons under the window
    a[125:134, 0:9] = eq_close_pressed()
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        wx = 14 if label == "ON" else 40
        c = win[18:30, wx:wx + w].copy()
        eq_toggle(c, w, 12, label, on, pressed)
        a[119:131, x:x + w] = c
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    # slider thumbs on the plain slot background at the fill's edge
    for y, pressed in ((164, False), (176, True)):
        ref = eq_slider_frame(plain_slot, 0.5)
        # rows round the boundary (first filled row 31): thumb rows 26..36 -> centre 31.5
        cell = ref[26:37, 1:12]
        a[y:y + 11, 0:11] = eq_thumb(cell, pressed)
    for n in range(28):
        a[164 + (n // 14) * 65:164 + (n // 14) * 65 + 63, 13 + (n % 14) * 15:13 + (n % 14) * 15 + 14] = \
            eq_slider_frame(plain_slot, n / 27)
    for y, pressed in ((164, False), (176, True)):
        c = win[18:30, 217:261].copy()
        presets_cell(c, pressed)
        a[y:y + 12, 224:268] = c
    # the graph: background, preamp line, the line's colours by height
    g = new(113, 19, (0, 0, 0) if not MM() else WHITE)
    gridc = {"gingerbread": (30, 30, 30), "ics": (22, 34, 40), "marshmallow": (238, 238, 238)}[K()]
    for x in range(0, 113, 14):
        rect(g, x + 1, 0, 1, 19, gridc)
    rect(g, 0, 9, 113, 1, lerp(gridc, T["label"], 0.4))
    a[294:313, 0:113] = g
    line = {"gingerbread": [(204, 255, 51), GB_GREEN, (255, 182, 0), (255, 120, 0)],
            "ics": [(153, 221, 245), HOLO, HOLO_DK, (0, 112, 153)],
            "marshmallow": [(191, 54, 12), DEEP_ORANGE_DK, DEEP_ORANGE, (255, 138, 101)]}[K()]
    for r in range(19):
        px(a, 115, 294 + r, ramp(line, r / 18))
    pre = {"gingerbread": (110, 110, 110), "ics": (90, 90, 90), "marshmallow": (189, 189, 189)}[K()]
    for x in range(113):
        px(a, x, 314, pre if x % 3 != 2 else g[0, 0])
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109)
# ------------------------------------------------------------------------------------------


def frame_col():
    return {"gingerbread": (12, 12, 12), "ics": (0, 0, 0), "marshmallow": (250, 250, 250)}[K()]


def edge_cols():
    """(outer edge, inner edge next to the list)"""
    return {"gingerbread": ((54, 54, 54), (34, 34, 34)), "ics": ((44, 48, 52), (34, 34, 34)),
            "marshmallow": ((200, 200, 200), (224, 224, 224))}[K()]


def side_tile(w, h, left, list_side=True):
    t = new(w, h, frame_col())
    outer, inner = edge_cols()
    if left:
        rect(t, 0, 0, 1, h, outer)
        if list_side:
            rect(t, w - 1, 0, 1, h, inner)
    else:
        rect(t, w - 1, 0, 1, h, outer)
        if list_side:
            rect(t, 0, 0, 1, h, inner)
    return t


def bottom_base(w, h=38):
    t = new(w, h, frame_col())
    outer, inner = edge_cols()
    if GB():
        vfill(t, 0, 0, w, h, [(62, 62, 62), (40, 40, 40), (22, 22, 22)])
        rect(t, 0, 0, w, 1, (96, 96, 96))
        rect(t, 0, h - 1, w, 1, outer)
    elif ICS():
        rect(t, 0, 0, w, h, (12, 12, 12))
        rect(t, 0, 0, w, 1, (51, 51, 51))
        rect(t, 0, h - 1, w, 1, outer)
    else:
        rect(t, 0, 0, w, h, WHITE)
        for r, al in ((0, 0.14), (1, 0.05)):
            rect(t, 0, r, w, 1, lerp(WHITE, BLACK, al))
        rect(t, 0, h - 1, w, 1, outer)
    return t


def text_button(t, x, y, w, h, label, pressed=False):
    if GB():
        gb_face(t, x, y, w, h, pressed, light=True, r=2.5)
        text_center(t, TINY, label, x + w // 2, y + (h - 5) // 2, BLACK)
    elif ICS():
        if pressed:
            rect(t, x, y, w, h, (28, 103, 130))
        text_center(t, TINY, label, x + w // 2, y + (h - 5) // 2, WHITE)
        rect(t, x + w + 3, y + 3, 1, h - 6, (51, 51, 51))
    else:
        if pressed:
            rrect_at(t, x, y, w, h, 2, BLACK, 0.1)
        text_center(t, TINY, label, x + w // 2, y + (h - 5) // 2, DEEP_ORANGE)


def readout(t, x, y, w, h):
    """A box for text.bmp readouts (playlist times): the display colour, framed per theme."""
    if GB():
        rrect_at(t, x - 1, y - 1, w + 2, h + 2, 1.5, (90, 90, 90))
        rect(t, x, y, w, h, T["disp"])
    elif ICS():
        rect(t, x, y, w, h, T["disp"])
        rect(t, x, y + h, w, 1, HOLO_DK)
    else:
        rect(t, x, y, w, h, T["disp"])


def grip(t, x0, y0, n):
    col = {"gingerbread": (130, 130, 130), "ics": (90, 90, 90), "marshmallow": (189, 189, 189)}[K()]
    for k in range(n):
        for j in range(k + 1):
            px(t, x0 - 3 * k + 3 * j, y0 - 3 * j, col)


def make_pledit():
    a = new(280, 186, frame_col())
    outer, inner = edge_cols()
    for lit, y in ((True, 0), (False, 21)):
        t = win_bar_bg(25, 20, lit)
        a[y:y + 20, 127:152] = t
        t = win_bar_bg(25, 20, lit)
        rect(t, 0, 0, 1, 20, outer)
        rect(t, 11, 19, 14, 1, inner)
        a[y:y + 20, 0:25] = t
        t = win_bar_bg(100, 20, lit)
        bar_title(t, "Playlist", 50, 12, lit)
        rect(t, 0, 19, 100, 1, inner)
        a[y:y + 20, 26:126] = t
        t = win_bar_bg(25, 20, lit)
        rect(t, 24, 0, 1, 20, outer)
        bar_button(t, 14, 3, "close", lit, False, on_light=MM() and not lit)
        rect(t, 0, 19, 6, 1, inner)
        a[y:y + 20, 153:178] = t
        # the list's top edge across the fill tile too
        a[y + 19, 127:152] = inner
    # sides
    a[42:71, 0:12] = side_tile(12, 29, True)
    t = side_tile(20, 29, False)
    groove = {"gingerbread": (20, 20, 20), "ics": (8, 8, 8), "marshmallow": (245, 245, 245)}[K()]
    rect(t, 5, 0, 8, 29, groove)
    a[42:71, 31:51] = t
    for x, sel in ((52, False), (61, True)):
        c = new(8, 18, groove)
        if GB():
            rrect_at(c, 2, 0, 4, 18, 2, (180, 180, 180) if not sel else (255, 170, 0))
        elif ICS():
            rect(c, 3, 0, 3, 18, (110, 110, 110) if not sel else HOLO)
        else:
            rrect_at(c, 2, 0, 4, 18, 2, (189, 189, 189) if not sel else DEEP_ORANGE)
        a[53:71, x:x + 8] = c
    t = win_bar_bg(25, 20, True)
    rect(t, 24, 0, 1, 20, outer)
    bar_button(t, 14, 3, "close", True, True)
    a[42:51, 52:61] = t[3:12, 14:23]

    # bottom: left (buttons), right (readouts, mini transport, LIST, grip), fill
    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, outer)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        text_button(t, bx, 8, 22, 18, lbl)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, outer)
    readout(t, 6, 9, 56, 8)
    ink = {"gingerbread": WHITE, "ics": (230, 230, 230), "marshmallow": (97, 97, 97)}[K()]
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        mini_glyph(t, kind, 3 + 10 * k, 22, ink)
    readout(t, 65, 22, 33, 8)
    rect(t, 84, 24, 1, 1, T["ink"])
    rect(t, 84, 27, 1, 1, T["ink"])
    text_button(t, 106, 8, 22, 18, "LIST")
    if ICS():
        rect(t, 106 + 22 + 3, 11, 1, 12, (12, 12, 12))
    grip(t, 145, 34, 4)
    a[72:110, 126:276] = t
    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_bottom(w, grip_, left_edge):
    t = new(w, 14, frame_col())
    outer, inner = edge_cols()
    if GB():
        vfill(t, 0, 0, w, 14, [(40, 40, 40), (22, 22, 22)])
    elif MM():
        rect(t, 0, 0, w, 14, (250, 250, 250))
    rect(t, 0, 0, w, 1, inner)
    rect(t, 0, 13, w, 1, outer)
    if left_edge:
        rect(t, 0, 0, 1, 14, outer)
    else:
        rect(t, w - 1, 0, 1, 14, outer)
    if grip_:
        grip(t, w - 4, 10, 3)
    return t


def make_gen():
    a = new(194, 109, frame_col())
    outer, inner = edge_cols()
    for lit, y in ((True, 0), (False, 21)):
        for px0 in (0, 26, 52, 78, 104, 130):
            t = win_bar_bg(25, 20, lit)
            rect(t, 0, 19, 25, 1, inner)
            if px0 == 0:
                rect(t, 0, 0, 1, 20, outer)
            if px0 == 130:
                rect(t, 24, 0, 1, 20, outer)
                bar_button(t, 14, 3, "close", lit, False, on_light=MM() and not lit)
            a[y:y + 20, px0:px0 + 25] = t
    a[42:56, 0:125] = gen_bottom(125, False, True)
    a[57:71, 0:125] = gen_bottom(125, True, False)
    t = gen_bottom(25, False, False)
    t[:, 24] = t[:, 23]
    a[72:86, 127:152] = t
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = side_tile(w, h, left)
    t = win_bar_bg(25, 20, True)
    bar_button(t, 14, 3, "close", True, True)
    a[42:51, 148:157] = t[3:12, 14:23]
    # letters: the bar's own rows 4..10 as each cell's background, separated by SEP
    for lit, y in ((True, 88), (False, 96)):
        bar = win_bar_bg(194, 20, lit)
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for ch in GEN_LETTERS:
            w = glyph_w(FONT5, ch) + 1
            a[y:y + 7, x:x + w] = bar[4:11, x:x + w]
            draw_text(a, FONT5, ch, x, y + 1, title_col(lit))
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp, text files
# ------------------------------------------------------------------------------------------


def genex_colours():
    return {
        "gingerbread": [(0, 0, 0), (255, 255, 255), (24, 24, 24), (0, 0, 0), (230, 230, 230), (64, 64, 64),
                        (184, 92, 0), (48, 48, 48), (255, 255, 255), (96, 96, 96), (0, 0, 0), (255, 170, 0),
                        (24, 24, 24), (40, 40, 40), (160, 160, 160), (60, 60, 60), (255, 182, 0), (16, 16, 16)],
        "ics": [(0, 0, 0), (232, 232, 232), (17, 17, 17), (255, 255, 255), (220, 220, 220), (51, 51, 51),
                (26, 92, 117), (28, 28, 28), HOLO, (68, 68, 68), (0, 0, 0), HOLO, (17, 17, 17), (24, 24, 24),
                (102, 102, 102), (34, 34, 34), HOLO, (0, 0, 0)],
        "marshmallow": [WHITE, (33, 33, 33), (250, 250, 250), DEEP_ORANGE, (33, 33, 33), (224, 224, 224),
                        (255, 204, 188), WHITE, (117, 117, 117), WHITE, (224, 224, 224), (255, 204, 188),
                        (250, 250, 250), (245, 245, 245), (189, 189, 189), (238, 238, 238), DEEP_ORANGE,
                        (250, 250, 250)],
    }[K()]


def make_genex():
    a = new(256, 64, frame_col())
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    for y, pressed in ((1, False), (16, True)):
        if GB():
            gb_face(a, 0, y, 47, 15, pressed, light=True)
        elif ICS():
            holo_face(a, 0, y, 47, 15, pressed)
        else:
            rect(a, 0, y, 47, 15, WHITE if not pressed else (238, 238, 238))
            rect(a, 0, y + 14, 47, 1, (224, 224, 224))
    return a


def viscolor():
    if GB():
        bg, dots = (0, 0, 0), (26, 26, 26)
        spec = [(220, 255, 90), (190, 240, 40), GB_GREEN, (120, 170, 0), (80, 120, 0), (50, 80, 0)]
        osc = [(220, 255, 120), (190, 240, 60), GB_GREEN, (120, 170, 0), (80, 120, 0)]
        peak = (255, 214, 64)
    elif ICS():
        bg, dots = (0, 0, 0), (18, 30, 36)
        spec = [(190, 236, 252), (120, 210, 240), HOLO, HOLO_DK, (0, 110, 150), (0, 70, 100)]
        osc = [(200, 240, 255), (130, 215, 245), HOLO, HOLO_DK, (0, 110, 150)]
        peak = WHITE
    else:
        bg, dots = WHITE, (238, 238, 238)
        spec = [(191, 54, 12), DEEP_ORANGE_DK, DEEP_ORANGE, (255, 112, 67), (255, 138, 101), (255, 204, 188)]
        osc = [(191, 54, 12), DEEP_ORANGE_DK, DEEP_ORANGE, (255, 138, 101), (255, 171, 145)]
        peak = (66, 66, 66)
    out = [(bg, "background"), (dots, "dots")]
    out += [(ramp(spec, i / 15), f"spectrum {i + 1}") for i in range(16)]
    out += [(c, f"oscilloscope {i + 1}") for i, c in enumerate(osc)]
    out += [(peak, "peaks")]
    return out


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    p = T["pl"]
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={p['normal']}\nCurrent={p['current']}\nNormalBG={p['normalbg']}\n"
                f"SelectedBG={p['selectedbg']}\nMbBG={p['normalbg']}\nMbFG={p['normal']}\nFont={p['font']}\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        title = T["wsz"][:-4]
        f.write(
            f"{title} - a skin in the style of {T['name']}.\n"
            "Android robot logo (c) Google LLC.\n\n"
            "A classic (Winamp 2.x format) skin, drawn procedurally by a script (gen_skin.py):\n"
            "gradients, anti-aliased shapes, hand-made pixel fonts, and Droid Sans / Roboto for\n"
            "the window titles. No screenshots or Android artwork were copied; the robot is a\n"
            "13x15 pixel rendition of Google's Android robot (CC BY 3.0).\n"
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
        "titlebar.bmp": make_titlebar(),
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


def text_ink():
    """text.bmp's ink as the app finds it: the commonest colour in the first two rows far from the
    space cell's."""
    a = np.asarray(SHEETS["text"])[:12, :155].reshape(-1, 3).astype(int)
    bg = np.asarray(SHEETS["text"])[0, 150].astype(int)
    far = np.abs(a - bg).sum(1) >= 96
    vals, counts = np.unique(a[far], axis=0, return_counts=True)
    return tuple(int(v) for v in vals[counts.argmax()])


def pl_font(size=11):
    face = "droid" if GB() else "roboto"
    return font(size, 400, face)


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
    if state["pressed"] == "close":
        blit(img, S["titlebar"], (18, 9, 9, 9), 264, 3)
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
    # the title box blanked with text.bmp's space, then the title in the playlist's TrueType font
    # in text.bmp's ink, clipped as the app clips it
    for x in range(0, 154, 5):
        blit(img, S["text"], (150, 0, min(5, 154 - x), 6), 111 + x, 24)
    layer = Image.new("RGB", (275, 116))
    layer.paste(img)
    ImageDraw.Draw(layer).text((111, 24 + 3 + 2), state["title"], fill=text_ink(), font=pl_font(11), anchor="lm")
    img.paste(layer.crop((111, 22, 265, 36)), (111, 22))
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
    f = pl_font(11)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=hexc(p["selectedbg"]))
        col = hexc(p["current"]) if i == 1 else hexc(p["normal"])
        d.text((lx + 2, y + 8), f"{i + 1}. {txt}", fill=col, font=f, anchor="lm")
        d.text((lx + lw - 3, y + 8), dur, fill=col, font=f, anchor="rm")
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
    c0, c1 = {"gingerbread": ((20, 30, 0), (153, 204, 0)), "ics": ((0, 20, 30), (51, 181, 229)),
              "marshmallow": ((255, 204, 188), (230, 74, 25))}[K()]
    col = np.stack([c0[i] + (c1[i] - c0[i]) * arr[..., 0] for i in range(3)], -1)
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
        col.paste(preview_playlist(lit, 275, 232, PREVIEW_ROWS, pressed_close=not lit, drag=not lit), (0, 232))
        col.paste(preview_gen(lit, 275, 140, "album art", pressed_close=not lit), (0, 464))
        cols.append(col)
    gap = 12
    out = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), T["desk"])
    out.paste(cols[0], (gap, gap))
    out.paste(cols[1], (275 + 2 * gap, gap))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, f"preview-{K()}.png"))


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
    title_box = np.asarray(SHEETS["main"].crop((111, 24, 265, 30)))
    assert (title_box == np.array(T["disp"])).all(), "the title box must be the display colour"


def run(key):
    global T, OUT
    T = dict(THEMES[key], key=key)
    OUT = os.path.join(HERE, "out", key)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    names = build()
    check_sheets()
    preview()
    print(f"{key}: {T['wsz']} ({len(names)} files), preview-{key}.png, title ink {text_ink()}")


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
