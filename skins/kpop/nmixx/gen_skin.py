#!/usr/bin/python3
"""NMIXX: a personal fan skin (classic Winamp 2.x format), generated procedurally.

Forked from skins/ember/gen_skin.py by way of private-repo/skins/kpop/artms/gen_skin.py (same sheets,
same layouts, same preview logic). Private use only: the NMIXX logo is JYP Entertainment's and is
rasterised at generation time from source/logo-nmixx/NMIXX_logo.svg (see README.md).

    /usr/bin/python3 -I gen_skin.py              # every theme (there is one: nmixx)
    /usr/bin/python3 -I gen_skin.py nmixx
    /usr/bin/python3 -I gen_skin.py --list

The look: Fe3O4's steel-blue night (the "DASH" overpass at dusk, magnetite's dark metal) with the
neon of AD MARE's "Pick N Mixx" donut shop, and the six members' colours mixed in: one per
transport button (eject included), a small pixel animal of each under her button, and the six as
stepped ramps through the volume bar, EQ and analyzer. The About spot is "O.O" in neon rings.
Writes its sheets into out/nmixx/, zips them flat into NMIXX.wsz and draws preview.png.
"""

import os
import subprocess
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py, which finishes each .wsz
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO_SVG = os.path.join(HERE, "source", "logo-nmixx", "NMIXX_logo.svg")
SCRATCH = os.path.join(HERE, "out", "scratch")

# The six members in official order, with the colours JYP's store merch (pouches, photocard
# backings) gives them; the names agree across fan sources, the shades are this skin's own (no
# official hex values exist). The animals are the members' fan-established emoji. See README.md.
MEMBERS = [
    ("lily", "Lily", (0x8C, 0xC8, 0xF2), "koala"),       # baby blue
    ("haewon", "Haewon", (0xF4, 0xF6, 0xFA), "bear"),    # white (polar bear)
    ("sullyoon", "Sullyoon", (0x1E, 0x34, 0x9A), "deer"),  # dark blue
    ("bae", "Bae", (0xFF, 0xD2, 0x2E), "chick"),         # yellow
    ("jiwoo", "Jiwoo", (0xE8, 0x22, 0x30), "puppy"),     # red
    ("kyujin", "Kyujin", (0xFF, 0x7C, 0xB8), "cat"),     # pink
]
MCOL = {k: c for k, _, c, _ in MEMBERS}

# ------------------------------------------------------------------------------------------
# Palette: Fe3O4 steel blue, AD MARE neon
# ------------------------------------------------------------------------------------------

BODY = (15, 21, 33)          # the overpass at dusk (Fe3O4: Break's cover, #101826..#223044)
BAR = (15, 21, 33)           # titlebars: flat, so gen.bmp's letter cells match them exactly
DISP = (3, 5, 10)
WHITE = (255, 255, 255)
TXT = (226, 236, 250)        # display ink: cool white (text.bmp's ink, so the title's colour too)
RULE = (46, 60, 84)          # thin outlines round the displays and buttons
RULE_HI = (118, 140, 176)    # titlebar rules, focused
RULE_DIM = (44, 54, 72)      # titlebar rules, unfocused
GREY_TXT = (122, 138, 164)
GREY_DIM = (52, 62, 82)
TRACK = (30, 40, 58)         # unlit slider tracks
FACE = (22, 30, 46)          # monochrome button faces
FACE_PR = (8, 11, 18)
SEP = (255, 0, 255)          # gen.bmp letter separators (never shown)
EDGE = (30, 40, 58)          # window outlines
GROOVE = (24, 32, 48)
GREY_MID = (146, 160, 184)
GREY_LO = (104, 116, 138)
STEEL_SEL = (186, 198, 216)
LIGHT = (224, 232, 244)
INK_DARK = (10, 14, 24)
NEON = (255, 104, 116)       # the donut shop's neon ring (AD MARE)
NEON_HALO = (120, 30, 50)


def cool(c):
    """A neutral grey from Ember/ARTMS turned toward the steel blue of this skin."""
    r, g, b = c
    return (max(0, round(r * 0.84)), max(0, round(g * 0.92)), min(255, round(b * 1.08 + 6)))


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    """Colour along a list of stops, t in 0..1."""
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    if n == 0:
        return stops[0]
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def steps(stops, t):
    """Colour from a list of stops without blending: the members side by side, not mixed."""
    t = max(0.0, min(1.0, t))
    return stops[min(len(stops) - 1, int(t * len(stops)))]


def luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def lift(c):
    """A member colour made visible on the dark body for small marks (Sullyoon's dark blue)."""
    return lerp(c, (120, 150, 255), 0.5) if luma(c) < 70 else c


def tint(c, t):
    return lerp(c, WHITE, t)


def shade(c, t):
    return lerp(c, (0, 0, 0), t)


# ------------------------------------------------------------------------------------------
# Theme
# ------------------------------------------------------------------------------------------


def make_theme(key):
    cols = [c for _, _, c, _ in MEMBERS]
    lit = [lift(c) for c in cols]
    L = {k: lift(c) for k, c in MCOL.items()}
    # cool to hot: Sullyoon, Lily, Haewon, Bae, Kyujin, Jiwoo
    level = [L["sullyoon"], L["lily"], L["haewon"], L["bae"], L["kyujin"], L["jiwoo"]]
    return dict(
        key=key, title="NMIXX", member=None, objekt=False,
        wsz="NMIXX.wsz", preview="preview.png",
        buttons=cols[:5], eject=cols[5], mini=cols,
        level=level, balance=[GREY_MID] + level[1:],
        shuffle=L["lily"], repeat=L["kyujin"], eq=L["bae"], pl=L["lily"], on=L["bae"], auto=L["lily"],
        vis=("bands", level[::-1]), graph=level[::-1],
        sel_bg=(30, 48, 84), current=NEON, genex_sel=(44, 70, 120), accent=L["lily"],
        name_in_title=None, readme_who="the group",
    )


THEME_KEYS = ["nmixx"]
T = None  # the theme being built
OUT = None


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


def outline(a, x, y, w, h, col):
    rect(a, x, y, w, 1, col)
    rect(a, x, y + h - 1, w, 1, col)
    rect(a, x, y, 1, h, col)
    rect(a, x + w - 1, y, 1, h, col)


def grain(a, x, y, w, h, amp=1.2, seed=1729):
    """A very fine, even noise: just enough to keep the black from looking flat."""
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w))
    n = (n + np.roll(n, 1, axis=1) * 0.5) / 1.2
    a[y:y + h, x:x + w] += np.round(n * amp).astype(np.int32)[:, :, None]


def body(a, x, y, w, h, col=BODY, amp=1.2, seed=1729):
    rect(a, x, y, w, h, col)
    grain(a, x, y, w, h, amp, seed)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def composite(a, x, y, alpha, col, opacity=1.0):
    """Blends a solid colour into a at (x, y) through an alpha mask (float 0..1, H x W)."""
    h, w = alpha.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(a.shape[1], x + w), min(a.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    al = alpha[y0 - y:y1 - y, x0 - x:x1 - x, None] * opacity
    dst = a[y0:y1, x0:x1].astype(np.float64)
    a[y0:y1, x0:x1] = np.round(dst * (1 - al) + np.array(col, dtype=np.float64) * al).astype(np.int32)


# ------------------------------------------------------------------------------------------
# Pixel fonts (Ember's, a few glyphs redrawn for a plainer, Helvetica-like caps)
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
    "M": G("#..#", "####", "#..#", "#..#", "#..#"),
    "N": G("#..#", "##.#", "#.##", "#..#", "#..#"),
    "O": G(".##.", "#..#", "#..#", "#..#", ".##."),
    "P": G("###.", "#..#", "###.", "#...", "#..."),
    "Q": G(".##.", "#..#", "#..#", "#.#.", ".#.#"),
    "R": G("###.", "#..#", "###.", "#.#.", "#..#"),
    "S": G(".###", "#...", ".##.", "...#", "###."),
    "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#..#", "#..#", "#..#", "#..#", ".##."),
    "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#..#", "#..#", "#..#", "####", "#..#"),
    "X": G("#..#", "#..#", ".##.", "#..#", "#..#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": G("####", "...#", ".##.", "#...", "####"),
    "0": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "1": G(".#", "##", ".#", ".#", ".#"),
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
    " ": G("..", "..", "..", "..", ".."),
}
for _c in "0123456789+-.":
    TINY[_c] = FONT5[_c]

# Titles and gen.bmp's letters have room for a 5-wide M and W (text.bmp's 5px cells don't), so
# "NMIXX" reads as itself.
FONTT = dict(FONT5)
FONTT["M"] = G("#...#", "##.##", "#.#.#", "#...#", "#...#")
FONTT["W"] = G("#...#", "#...#", "#.#.#", "##.##", "#...#")

# 7x11 thin digits for numbers.bmp (a plain grotesque, not segments).
DIGITS = {
    0: G("..###..", ".#...#.", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#",
         "#.....#", ".#...#.", "..###.."),
    1: G("...#...", "..##...", ".#.#...", "...#...", "...#...", "...#...", "...#...", "...#...",
         "...#...", "...#...", "...#..."),
    2: G("..###..", ".#...#.", "#.....#", "......#", ".....#.", "....#..", "...#...", "..#....",
         ".#.....", "#......", "#######"),
    3: G("..###..", ".#...#.", "......#", "......#", ".....#.", "...##..", ".....#.", "......#",
         "#.....#", ".#...#.", "..###.."),
    4: G(".....#.", "....##.", "...#.#.", "..#..#.", ".#...#.", "#....#.", "#######", ".....#.",
         ".....#.", ".....#.", ".....#."),
    5: G("#######", "#......", "#......", "#.###..", "##...#.", "......#", "......#", "......#",
         "#.....#", ".#...#.", "..###.."),
    6: G("..###..", ".#...#.", "#......", "#......", "#.###..", "##...#.", "#.....#", "#.....#",
         "#.....#", ".#...#.", "..###.."),
    7: G("#######", "......#", ".....#.", ".....#.", "....#..", "....#..", "...#...", "...#...",
         "..#....", "..#....", "..#...."),
    8: G("..###..", ".#...#.", "#.....#", ".#...#.", "..###..", ".#...#.", "#.....#", "#.....#",
         "#.....#", ".#...#.", "..###.."),
    9: G("..###..", ".#...#.", "#.....#", "#.....#", "#.....#", ".#...##", "..###.#", "......#",
         "......#", ".#...#.", "..###.."),
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


def draw_digit(a, n, x, y, col):
    """A 7x11 digit with its stair-steps softened (half-tone pixels in the inner corners)."""
    g = DIGITS[n]
    for r, row in enumerate(g):
        for k, ch in enumerate(row):
            if ch == "#":
                px(a, x + k, y + r, col)
    soft = lerp(DISP, col, 0.35)
    for r in range(len(g) - 1):
        for k in range(len(g[0]) - 1):
            q = (g[r][k], g[r][k + 1], g[r + 1][k], g[r + 1][k + 1])
            if q in (("#", ".", ".", "#"), (".", "#", "#", ".")):
                for dk, dr in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    if g[r + dr][k + dk] == ".":
                        px(a, x + k + dk, y + r + dr, soft)



# ------------------------------------------------------------------------------------------
# The NMIXX logo (rasterised from the SVG) and the members' pixel animals
# ------------------------------------------------------------------------------------------

_logo_cache = {}


def logo_alpha(h):
    """The NMIXX wordmark, h rows tall: rendered big by rsvg-convert, then box-filtered down so
    its thin stencil bars land as clean 1px columns."""
    if h not in _logo_cache:
        os.makedirs(SCRATCH, exist_ok=True)
        big = os.path.join(SCRATCH, f"logo-{h * 8}.png")
        subprocess.run(["/usr/bin/rsvg-convert", "-h", str(h * 8), LOGO_SVG, "-o", big], check=True)
        a = np.asarray(Image.open(big).convert("RGBA"))[..., 3].astype(np.float64) / 255
        rows = np.nonzero(a.max(1) > 0.5)[0]
        cols = np.nonzero(a.max(0) > 0.5)[0]
        a = a[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
        w = max(1, round(a.shape[1] * h / a.shape[0]))
        img = Image.fromarray(np.round(a * 255).astype(np.uint8), "L").resize((w, h), Image.BOX)
        al = np.asarray(img).astype(np.float64) / 255
        _logo_cache[h] = np.clip((al - 0.1) / 0.6, 0, 1)   # firm the bars up at sprite size
    return _logo_cache[h]


# 7-row faces, drawn in the member's colour: '#' her colour, 'o' eyes and 'n' nose (dark),
# 'b' a beak (orange), '.' clear.
ANIMALS = {
    "koala": G("###.....###",
               "#i#.....#i#",
               "####...####",
               "..#o###o#..",
               "..###n###..",
               "...#nnn#...",
               "....###...."),
    "bear": G(".##.....##.",
              ".##.###.##.",
              "..#######..",
              "..#o###o#..",
              "..###n###..",
              "...#####...",
              "....###...."),
    "deer": G(".#.#...#.#.",
              "..##...##..",
              "...#####...",
              "...o###o...",
              "....###....",
              "....#n#....",
              ".....#....."),
    "chick": G("....###....",
               "...#####...",
               "...#o#o#...",
               "...##bb#...",
               "..#######..",
               "..#######..",
               "...#####..."),
    "puppy": G("...#####...",
               "..#######..",
               ".##o###o##.",
               ".##.#n#.##.",
               ".#..###..#.",
               "....###....",
               "..........."),
    "cat": G("..#.....#..",
             "..##...##..",
             "..#######..",
             "..#o###o#..",
             "..###n###..",
             "...#####...",
             "..........."),
}


def draw_animal(a, kind, x, y, col):
    dark = DISP if luma(col) > 60 else (230, 236, 250)
    for r, row in enumerate(ANIMALS[kind]):
        for k, ch in enumerate(row):
            if ch == "#":
                px(a, x + k, y + r, col)
            elif ch in "on":
                px(a, x + k, y + r, dark)
            elif ch == "i":
                px(a, x + k, y + r, tint(col, 0.6))
            elif ch == "b":
                px(a, x + k, y + r, (255, 140, 30))


def oo_emblem(a, x, y, lit=True):
    """'O.O' (the debut single) as two neon rings round a dot, the donut-shop sign's red."""
    col = NEON if lit else GREY_DIM
    yy, xx = np.mgrid[0:9, 0:9]
    d = np.hypot(xx - 4, yy - 4)
    ring = np.clip(1.25 - np.abs(d - 3.4) / 0.9, 0, 1)
    halo = np.clip(1.0 - np.abs(d - 3.4) / 2.2, 0, 1) * 0.35
    for ox in (0, 12):
        if lit:
            composite(a, x + ox, y, halo, NEON_HALO)
        composite(a, x + ox, y, ring, col)
    rect(a, x + 10, y + 7, 1, 1, col)


# ------------------------------------------------------------------------------------------
# Shared pieces
# ------------------------------------------------------------------------------------------


def hrule(a, x, y, w, lit):
    rect(a, x, y, w, 1, RULE_HI if lit else RULE_DIM)


TITLE_LIT = WHITE
TITLE_DIM = GREY_LO


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: flat, outlined; pressed inverts to white."""
    face = LIGHT if pressed else BAR
    rect(a, x, y, 9, 9, face)
    outline(a, x, y, 9, 9, STEEL_SEL if pressed else (cool((92, 92, 100)) if lit else cool((52, 52, 58))))
    ink = cool((10, 10, 12)) if pressed else (cool((236, 236, 240)) if lit else GREY_LO)
    X, Y = x, y
    if kind == "options":
        rect(a, X + 3, Y + 3, 3, 3, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 6, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 1, ink)
        rect(a, X + 2, Y + 4, 5, 1, lerp(ink, face, 0.5))
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


def flat_button(a, x, y, w, h, pressed, face=FACE, edge=RULE):
    rect(a, x, y, w, h, FACE_PR if pressed else face)
    outline(a, x, y, w, h, lerp(edge, (0, 0, 0), 0.3) if pressed else edge)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, DISP)
    outline(a, 0, 0, 8, 43, RULE)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, WHITE if on else cool((84, 84, 90)))
    return a


LOGO_H = 10


def member_ticks(a, x, y, lit, reverse=False):
    """Six short bars, one per member, in the logo's own vertical stencil rhythm."""
    cols = [lift(c) for _, _, c, _ in MEMBERS]
    if reverse:
        cols = cols[::-1]
    for i, c in enumerate(cols):
        rect(a, x + 3 * i, y, 1, 6, c if lit else shade(c, 0.62))


def main_titlebar(lit):
    a = new(275, 14, BAR)
    outline(a, 0, 0, 275, 14, EDGE)
    logo = logo_alpha(LOGO_H)
    lw = logo.shape[1]
    lx = (275 - lw) // 2
    tick_w = 3 * 5 + 1
    # rule, member ticks, logo, member ticks, rule; all clear of the buttons (options to 15, minimize from 244)
    lt = lx - 7 - tick_w
    rt = lx + lw + 7
    hrule(a, 20, 7, lt - 5 - 20, lit)
    hrule(a, rt + tick_w + 5, 7, 239 - (rt + tick_w + 5), lit)
    member_ticks(a, lt, 4, lit, reverse=True)
    member_ticks(a, rt, 4, lit)
    composite(a, lx, 2, logo, WHITE if lit else cool((108, 108, 114)))
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, BAR)
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


def display_box(a, x, y, w, h):
    """A display window: near-black glass with a thin steel rule round it."""
    rect(a, x, y, w, h, DISP)
    outline(a, x - 1, y - 1, w + 2, h + 2, RULE)


BOTTOM_Y = 107   # the free strip under the transport buttons (y 107..114)


def main_decoration(a):
    """Each member's animal under her button (the sixth, Kyujin's cat, under eject)."""
    for i, (_, _, c, animal) in enumerate(MEMBERS):
        if i < 5:
            cx = 16 + 23 * i + 11
        else:
            cx = 136 + 11
        draw_animal(a, animal, cx - 5, BOTTOM_Y, lift(c))


def steel(a, x, y, w, h):
    """Brushed magnetite: a faint horizontal streak texture over the body (Fe3O4)."""
    rng = np.random.default_rng(3434)
    streak = rng.normal(0, 1, (h, -(-w // 6)))
    streak = np.repeat(streak, 6, axis=1)[:, :w]
    streak = (streak + np.roll(streak, 1, axis=0) * 0.6) / 1.6
    a[y:y + h, x:x + w] += np.round(streak * 1.6).astype(np.int32)[:, :, None]


def make_main():
    a = new(275, 116, BODY)
    body(a, 0, 0, 275, 116)
    steel(a, 0, 0, 275, 116)
    outline(a, 0, 0, 275, 116, EDGE)
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # left display: indicator, time, analyzer
    display_box(a, 21, 20, 84, 42)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, TXT)
    # right display: title row, then kbps/kHz/mono/stereo row
    display_box(a, 109, 21, 159, 15)
    display_box(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, GREY_TXT)
    draw_text(a, TINY, "KHZ", 169, 44, GREY_TXT)

    main_decoration(a)
    oo_emblem(a, 245, 92)
    return a



# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36)
# ------------------------------------------------------------------------------------------


def colour_button(a, x, y, w, h, col, pressed):
    face = shade(col, 0.38) if pressed else col
    rect(a, x, y, w, h, face)
    if not pressed:
        rect(a, x, y, w, 1, tint(col, 0.28))
    rect(a, x + w - 1, y, 1, h, shade(col, 0.6))
    rect(a, x, y + h - 1, w, 1, shade(col, 0.6))


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


def transport_icon(a, kind, x, y, w, h, pressed, ink):
    o = 1 if pressed else 0
    cx, cy = x + w // 2 + o, y + h // 2 + o
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
            rect(a, cx - 1 - r, cy - 4 + r, 2 * r + 3, 1, ink)
        rect(a, cx - 4, cy + 1, 9, 2, ink)


def icon_ink(col):
    """White on the darker member colours, near-black on the light ones (Haewon, Lily, Bae, Kyujin)."""
    return INK_DARK if luma(col) > 130 else WHITE


def make_cbuttons():
    a = new(136, 36, BODY)
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18), ("eject", 114, 22, 16)]
    for (kind, x, w, h), col in zip(specs, T["buttons"] + [T["eject"]]):
        for pressed, y in ((False, 0), (True, h)):
            colour_button(a, x, y, w, h, col, pressed)
            ink = icon_ink(col)
            if pressed:
                ink = lerp(ink, shade(col, 0.38), 0.15)
            transport_icon(a, kind, x, y, w, h, pressed, ink)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle(a, x, y, w, h, label, on, pressed, col, led="under"):
    flat_button(a, x, y, w, h, pressed)
    o = 1 if pressed else 0
    ink = WHITE if on else (GREY_MID if pressed else cool((120, 120, 128)))
    tw = text_w(TINY, label)
    if led == "under":
        draw_text(a, TINY, label, x + (w - tw) // 2 + o, y + 3 + o, ink)
        rect(a, x + 4 + o, y + h - 4 + o, w - 9, 1, col if on else cool((34, 34, 38)))
    else:  # a small light at the left
        draw_text(a, TINY, label, x + 7 + (w - 9 - tw) // 2 + o, y + (h - 5) // 2 + o, ink)
        rect(a, x + 3 + o, y + h // 2 - 1 + o, 2, 2, col if on else cool((40, 40, 44)))


def make_shufrep():
    a = new(92, 85, BODY)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        toggle(a, 0, y, 28, 15, "REPEAT", on, pressed, T["repeat"])
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed, T["shuffle"])
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        col = T["eq"] if label == "EQ" else T["pl"]
        toggle(a, x, 61, 23, 12, label, False, pressed, col, led="dot")
        toggle(a, x, 73, 23, 12, label, True, pressed, col, led="dot")
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, DISP)
    for y, on in ((0, True), (12, False)):
        col = WHITE if on else cool((52, 52, 58))
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, DISP)
    tri_right(a, 2, 1, 7, WHITE)                      # playing
    rect(a, 9 + 2, 1, 2, 7, WHITE)                    # paused
    rect(a, 9 + 5, 1, 2, 7, WHITE)
    rect(a, 18 + 2, 2, 5, 5, WHITE)                   # stopped
    rect(a, 36, 0, 3, 9, DISP)                        # not working
    rect(a, 39 + 1, 3, 1, 3, T["accent"])             # working
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, DISP)
    for n in range(10):
        draw_digit(a, n, 9 * n + 1, 1, TXT)
    if ex:
        rect(a, 99 + 2, 6, 5, 1, TXT)                 # minus
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
            draw_text(a, FONT5, key, col * 5, row * 6, TXT)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def pill(a, x, y, w, h, col, edge=None):
    rect(a, x, y, w, h, col)
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        a[cy, cx] = lerp(col, a[cy, cx] if edge is None else edge, 0.6)


def make_posbar(main):
    a = new(307, 10, BODY)
    a[0:10, 0:248] = main[72:82, 16:264]
    rect(a, 0, 4, 248, 2, TRACK)
    # thumbs: a white pill on the track's own background
    for x, sel in ((248, False), (278, True)):
        a[0:10, x:x + 29] = a[0:10, 100:129]
        pill(a, x + 5, 2, 19, 6, STEEL_SEL if sel else WHITE)
    return a


def slider_thumbs(a):
    for x, sel in ((0, True), (15, False)):
        rect(a, x, 422, 14, 11, BODY)
        pill(a, x + 4, 422, 6, 11, STEEL_SEL if sel else WHITE)


def make_volume(main):
    a = new(68, 433, BODY)
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        level = (i + 1) / 28
        fill_to = 7 + round(level * 54)
        colour = steps(T["level"], i / 27)
        rect(a, 3, y + 5, 62, 3, TRACK)
        rect(a, 3, y + 5, fill_to - 3, 3, colour)
    slider_thumbs(a)
    return a


def make_balance(main):
    a = new(68, 433, BODY)
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        t = i / 27
        colour = steps(T["balance"], t)
        reach = round(16 * t)
        rect(a, 11, y + 5, 34, 3, TRACK)
        rect(a, 28 - max(1, reach), y + 5, 2 * max(1, reach) + 1, 3, colour)
        rect(a, 28, y + 2, 1, 2, STEEL_SEL)
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def titled_bar(w, title, lit, close_x):
    """A 14px titlebar: caps title centred between thin rules."""
    a = new(w, 14, BAR)
    outline(a, 0, 0, w, 14, EDGE)
    tw = text_w(FONTT, title)
    tx = (w - tw) // 2
    hrule(a, 6, 7, tx - 6 - 6, lit)
    hrule(a, tx + tw + 6, 7, close_x - 4 - (tx + tw + 6), lit)
    draw_text(a, FONTT, title, tx, 5, TITLE_LIT if lit else TITLE_DIM)
    mini_button(a, close_x, 3, "close", lit)
    return a


def eq_title():
    return "NMIXX EQUALIZER"


def eq_slider_frame(a, x, y, n, bg=None):
    """14x63 slot: a thin track whose fill rises with the value (n of 0..27)."""
    if bg is not None:
        a[y:y + 63, x:x + 14] = bg
    else:
        rect(a, x, y, 14, 63, BODY)
    v = n / 27
    centre = round((1 - v) * 51) + 5
    colour = steps(T["level"], v)
    rect(a, x + 6, y + 3, 2, 57, TRACK)
    rect(a, x + 6, y + centre, 2, 60 - centre, colour)
    rect(a, x + 1, y + 30, 2, 1, cool((80, 80, 86)))
    rect(a, x + 11, y + 30, 2, 1, cool((80, 80, 86)))




def make_eqmain():
    a = new(275, 315, BODY)
    body(a, 0, 0, 275, 315, seed=4242)
    steel(a, 0, 0, 275, 116)
    outline(a, 0, 0, 275, 116, EDGE)
    a[0:14, :] = titled_bar(275, eq_title(), True, 264)
    outline(a, 85, 16, 115, 21, RULE)
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, GREY_TXT)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14, bg=a[38:101, x:x + 14].copy())
    text_center(a, TINY, "PREAMP", 28, 106, GREY_MID, shadow=None)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, GREY_MID)

    # under the window: buttons
    mini_button(a, 0, 125, "close", True, pressed=True)
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        toggle(a, x, 119, w, 12, label, on, pressed, T["on"] if label == "ON" else T["auto"], led="dot")
    a[134:148, :] = titled_bar(275, eq_title(), True, 264)
    a[149:163, :] = titled_bar(275, eq_title(), False, 264)
    for y, sel in ((164, False), (176, True)):
        rect(a, 0, y, 11, 11, BODY)
        pill(a, 0, y + 3, 11, 5, STEEL_SEL if sel else WHITE)
    # the 28 frames (the app takes the band's background from these, not from the window)
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        flat_button(a, 224, y, 44, 12, pressed)
        o = 1 if pressed else 0
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 3 + o, WHITE if pressed else cool((180, 180, 186)))
    # graph
    rect(a, 0, 294, 113, 19, DISP)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, EDGE)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, cool((44, 44, 48)))
    for r in range(19):
        px(a, 115, 294 + r, steps(T["graph"], r / 18))
    for x in range(113):
        px(a, x, 314, cool((120, 120, 126)) if x % 3 != 2 else DISP)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

RULE_Y = 7          # the titlebars' rule row (20px bars), through the middle of the title
TITLE_Y = 5         # FONT5 glyph top in 20px bars, level with gen.bmp's letters (5..9)


def bar20(w, lit, rule=True, x0=0, x1=None):
    a = new(w, 20, BAR)
    rect(a, 0, 0, w, 1, EDGE)
    if rule:
        hrule(a, x0, RULE_Y, (w if x1 is None else x1) - x0, lit)
    return a


def pl_title():
    return "NMIXX PLAYLIST"


def make_pledit():
    a = new(280, 186, BODY)
    body(a, 0, 0, 280, 186, seed=99)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit)
        a[y:y + 20, 127:152] = t
        t = bar20(25, lit, x0=6)
        rect(t, 0, 0, 1, 20, EDGE)
        a[y:y + 20, 0:25] = t
        # title (100 wide, centred)
        t = bar20(100, lit, rule=False)
        title = pl_title()
        tw = text_w(FONTT, title)
        hrule(t, 0, RULE_Y, (100 - tw) // 2 - 5, lit)
        hrule(t, (100 + tw) // 2 + 5, RULE_Y, 100 - ((100 + tw) // 2 + 5), lit)
        text_center(t, FONTT, title, 50, TITLE_Y, TITLE_LIT if lit else TITLE_DIM)
        a[y:y + 20, 26:126] = t
        # top-right: close button
        t = bar20(25, lit, x1=11)
        rect(t, 24, 0, 1, 20, EDGE)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    # left side tile
    t = new(12, 29)
    body(t, 0, 0, 12, 29, amp=0)
    rect(t, 0, 0, 1, 29, EDGE)
    rect(t, 11, 0, 1, 29, RULE)
    a[42:71, 0:12] = t
    # right side tile: list edge, scrollbar groove, outer edge
    t = new(20, 29)
    body(t, 0, 0, 20, 29, amp=0)
    rect(t, 0, 0, 1, 29, RULE)
    rect(t, 19, 0, 1, 29, EDGE)
    rect(t, 8, 0, 2, 29, GROOVE)
    a[42:71, 31:51] = t
    # close pressed, scroll handles (on the groove's colours)
    t = new(9, 9, BAR)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        rect(a, x, 53, 8, 18, BODY)
        pill(a, x + 1, 53, 6, 18, STEEL_SEL if sel else WHITE)

    def bottom_base(w):
        t = new(w, 38)
        body(t, 0, 0, w, 38, amp=0)
        rect(t, 0, 0, w, 1, RULE)
        rect(t, 0, 37, w, 1, EDGE)
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, EDGE)
    rect(t, 0, 0, 12, 1, BODY)
    rect(t, 11, 0, 1, 1, RULE)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        flat_button(t, bx, 8, 22, 18, False)
        text_center(t, TINY, lbl, bx + 11, 15, STEEL_SEL)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, EDGE)
    rect(t, 130, 0, 20, 1, BODY)
    rect(t, 130, 0, 1, 1, RULE)
    display_box(t, 6, 9, 56, 8)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        colour_button(t, bx, 22, 10, 10, T["mini"][k], False)
        mini_transport_icon(t, kind, bx, 22, icon_ink(T["mini"][k]))
    display_box(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, GREY_TXT)
    rect(t, 84, 22 + 5, 1, 1, GREY_TXT)
    flat_button(t, 106, 8, 22, 18, False)
    text_center(t, TINY, "LIST", 117, 15, STEEL_SEL)
    for k in range(4):
        for j in range(k + 1):
            px(t, 145 - 3 * k + 3 * j, 29 - 3 * j, GREY_MID)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


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


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GEN_RULE_Y = 7      # gen titles sit at y 4..10 (letters 5..9), so its rule runs through their middle


def make_gen():
    a = new(194, 109, BODY)
    body(a, 0, 0, 194, 109, seed=7)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, x0=None, x1=None, close=False, left_edge=False, right_edge=False):
            t = new(25, 20, BAR)
            rect(t, 0, 0, 25, 1, EDGE)
            if x0 is not None:
                hrule(t, x0, GEN_RULE_Y, x1 - x0, lit)
            if left_edge:
                rect(t, 0, 0, 1, 20, EDGE)
            if right_edge:
                rect(t, 24, 0, 1, 20, EDGE)
            if close:
                mini_button(t, 14, 3, "close", lit)
            a[y:y + 20, px0:px0 + 25] = t

        piece(0, 6, 25, left_edge=True)       # left
        piece(26, 0, 19)                       # left end: the rule stops before the title
        piece(52)                              # centre: plain, under the letters
        piece(78, 6, 25)                       # right end
        piece(104, 0, 25)                      # fill
        piece(130, 0, 11, close=True, right_edge=True)

    def bottom(w, grip, left_edge):
        t = new(w, 14)
        body(t, 0, 0, w, 14, amp=0)
        rect(t, 0, 13, w, 1, EDGE)
        if left_edge:
            rect(t, 0, 0, 1, 14, EDGE)
        else:
            rect(t, w - 1, 0, 1, 14, EDGE)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    px(t, w - 4 - 3 * k + 3 * j, 9 - 3 * j, GREY_MID)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        body(t, 0, 0, w, h, amp=0)
        if outer_left:
            rect(t, 0, 0, 1, h, EDGE)
            rect(t, w - 1, 0, 1, h, RULE)
        else:
            rect(t, w - 1, 0, 1, h, EDGE)
            rect(t, 0, 0, 1, h, RULE)
        a[42:42 + h, x:x + w] = t
    t = new(9, 9, BAR)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: each row starts at x 1, letters in their own cells, 1px separators of x 0's colour
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONTT, c) + 1
            rect(a, x, y, w, 7, BAR)
            draw_text(a, FONTT, c, x, y + 1, TITLE_LIT if lit else TITLE_DIM)
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------


def genex_colours():
    return [
        (0, 0, 0),          # item background
        cool((232, 232, 236)),    # item text
        BODY,               # window background
        (255, 255, 255),    # button text
        cool((232, 232, 236)),    # window text
        cool((52, 52, 58)),       # dividers, sunken borders
        T["genex_sel"],     # selection bar
        cool((22, 22, 26)),       # list header background
        cool((236, 236, 240)),    # list header text
        cool((70, 70, 78)),       # header frame, light
        cool((4, 4, 6)),          # header frame, dark
        T["genex_sel"],     # header frame, pressed
        BODY,               # header dead area
        EDGE,       # scrollbar
        STEEL_SEL,    # scrollbar 2
        cool((44, 44, 50)),       # scrollbar pressed
        T["accent"],        # scrollbar pressed 2
        cool((16, 16, 18)),       # scrollbar dead area
    ]


def make_genex():
    a = new(256, 64, BODY)
    rect(a, 0, 0, 256, 1, BODY)
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    flat_button(a, 0, 1, 47, 15, False)
    flat_button(a, 0, 16, 47, 15, True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    kind, stops = T["vis"]
    spec = []
    for i in range(16):
        if kind == "bands":
            # stacked member bands, top to bottom (16 rows: 3,3,3,3,2,2)
            k = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5][i]
            c = stops[k]
        else:
            c = ramp(stops, i / 15)
        spec.append((c, f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}"))
    return ([((0, 0, 0), "background"), (GROOVE, "dots")] + spec
            + [((255, 255, 255), "oscilloscope 1"), (cool((220, 220, 224)), "oscilloscope 2"),
               (cool((180, 180, 186)), "oscilloscope 3"), (cool((140, 140, 146)), "oscilloscope 4"),
               (cool((100, 100, 106)), "oscilloscope 5"), ((255, 255, 255), "peaks")])


def hexc(c):
    return "#%02X%02X%02X" % tuple(c)


def pledit_colours():
    return dict(Normal=(0xE8, 0xE8, 0xE8), Current=T["current"], NormalBG=(0, 0, 0), SelectedBG=T["sel_bg"])


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    c = pledit_colours()
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={hexc(c['Normal'])}\nCurrent={hexc(c['Current'])}\nNormalBG={hexc(c['NormalBG'])}\n"
                f"SelectedBG={hexc(c['SelectedBG'])}\nMbBG=#000000\nMbFG=#E8E8E8\nFont=Arial\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(f"{T['wsz'][:-4]}\n\n")
        f.write("NMIXX — a skin in the style of NMIXX. NMIXX logo © JYP Entertainment.\n")


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
    with zipfile.ZipFile(os.path.join(HERE, T["wsz"]), "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))   # deterministic archive
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(OUT, n), "rb") as fh:
                z.writestr(info, fh.read())
    # genex.bmp completed for real Winamp and WACUP: all 24 colours, readable text, and the
    # standard 112x59 button and scrollbar layout (skins/genex_wacup.py).
    genex_wacup.process(os.path.join(HERE, T["wsz"]))
    return names


# ------------------------------------------------------------------------------------------
# Preview: the windows put together from the sprites the way the app does (as in Ember)
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
    return [c for c, _ in viscolor()]


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
    draw_bitmap_text(img, "320", 111, 43)
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
    c = pledit_colours()
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=c["NormalBG"])
    try:
        font = ImageFont.truetype("LiberationSans-Regular.ttf", 9)
    except OSError:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 9)
        except OSError:
            font = ImageFont.load_default()
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=c["SelectedBG"])
        col = c["Current"] if i == 1 else c["Normal"]
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
    c = np.array(T["accent"], dtype=np.float32)
    col = 10 + arr[..., 0:1] * (c - 10) * 0.8
    img.paste(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("NMIXX - O.O", "3:11"), ("NMIXX - DASH", "3:02"),
            ("NMIXX - Love Me Like This", "2:58"), ("NMIXX - DICE", "3:12"),
            ("NMIXX - Party O'Clock", "3:00"), ("NMIXX - See that?", "2:55"),
            ("NMIXX - Know About Me", "2:43"), ("NMIXX - Blue Valentine", "3:08"),
            ("NMIXX - High Horse", "2:51"), ("NMIXX - Soñar (Breaker)", "3:27"),
            ("NMIXX - Funky Glitter Christmas", "3:14")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    title = "NMIXX - DASH (3:02)  ***"
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=title, bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="PAUSED: O.O  ***", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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


def run(key):
    global T, OUT
    T = make_theme(key)
    OUT = os.path.join(HERE, "out", key)
    os.makedirs(OUT, exist_ok=True)
    names = build()
    preview()
    for n in names:
        p = os.path.join(OUT, n)
        if n.endswith(".bmp"):
            im = Image.open(p)
            assert im.mode == "RGB", (n, im.mode)
    print(f"{key:16s} -> {T['wsz']}, {T['preview']}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    if "--list" in args:
        print("\n".join(THEME_KEYS))
        sys.exit(0)
    keys = []
    for a in args:
        a = a.lower().replace("--theme=", "")
        if a in ("all", "--all"):
            keys = THEME_KEYS[:]
        elif a in THEME_KEYS:
            keys.append(a)
        elif a != "--theme":
            sys.exit(f"unknown theme {a!r}; try --list")
    for k in keys or THEME_KEYS:
        run(k)
