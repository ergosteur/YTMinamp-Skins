#!/usr/bin/python3
"""Dell OptiPlex skin: a classic Winamp 2.x skin styled after the Dell OptiPlex 9010 (2012).

Based on skins/ember/gen_skin.py (same sheet layouts and preview), with the theme scaffolding and
the app-faithful title preview of private-repo/skins/devices/payphone. Every pixel is drawn here
except the Dell wordmark, rasterised at build time from source/dell-logo.svg (rsvg-convert,
supersampled, painted through its mask). The front panel: a satin black bezel above, the silver
stadium-hole steel mesh below with the brushed aluminium DELL badge, and a PowerEdge-style front
LCD (pale text on black glass, a lit blue menu bar) for the displays.

    /usr/bin/python3 -I gen_skin.py            # every theme
    /usr/bin/python3 -I gen_skin.py <theme>    # some
    /usr/bin/python3 -I gen_skin.py --list
"""

import os
import re
import subprocess
import sys
import zipfile
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source")

# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    "optiplex-9010": SimpleNamespace(
        name="optiplex-9010",
        wsz="Dell-OptiPlex-9010.wsz",
        title="Dell OptiPlex 9010",
    ),
}
T = None
OUT = None


def use_theme(name):
    global T, OUT, _rng
    T = THEMES[name]
    OUT = os.path.join(HERE, "out", name)
    os.makedirs(OUT, exist_ok=True)
    _rng = np.random.default_rng(9010)


# ------------------------------------------------------------------------------------------
# Palette
# ------------------------------------------------------------------------------------------

BEZEL = (30, 31, 35)           # satin black plastic
BEZEL_TOP = (44, 45, 50)       # the bezel's sheen near its top edge
BEZEL_HI = (70, 72, 78)
BEZEL_LO = (8, 8, 10)
RECESS = (14, 14, 16)

MESH_TOP = (214, 216, 220)     # the steel mesh's lands, lit from above
MESH_BOT = (172, 175, 180)
HOLE = (22, 22, 26)            # the black chassis behind the holes

ALU = (196, 198, 202)          # the brushed aluminium badge
ALU_HI = (236, 237, 239)
ALU_LO = (120, 122, 127)

LCD_BG = (6, 6, 9)             # the LCD's black glass
PALE = (226, 232, 246)         # top-line text: near-white, faintly blue
PALE_MID = (128, 136, 160)
BAR = (47, 79, 216)            # the lit blue menu bar (#2F4FD8, sampled)
BAR_TXT = (250, 251, 255)
BAR_DIM = (128, 154, 238)      # unselected items on the bar
BOX = (196, 210, 250)          # the selection box on the bar

KEY_TOP = (88, 90, 98)         # the small dark-grey keys beside the LCD
KEY_BOT = (58, 60, 67)
KEY_RIM = (12, 12, 14)
KEY_INK = (238, 240, 244)
KEY_INK_PRESSED = (150, 176, 255)

USB_BLUE = (22, 102, 214)      # USB 3.0's blue tongue
POWER_GREEN = (96, 214, 110)   # the power button's lit ring
EST = (150, 178, 214)          # the EST pull-out tag
SILVER_PRINT = (196, 199, 205)
SILVER_DIM = (112, 114, 120)

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


def new(w, h, col=BEZEL):
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


_rng = np.random.default_rng(9010)


def grain(a, x, y, w, h, amp=2.0):
    """Horizontally smeared noise (wraps, so tiles stay seamless)."""
    n = _rng.normal(0, 1, (h, w))
    acc = np.zeros_like(n)
    for d in range(-5, 6):
        acc += np.roll(n, d, axis=1)
    acc /= 3.3
    acc += _rng.normal(0, 0.3, (h, w))
    a[y:y + h, x:x + w] += np.round(acc * amp).astype(np.int32)[:, :, None]


def bezel(a, x, y, w, h, top=0, total=116, amp=1.2):
    """Satin black: a faint sheen fading down the window (row y + top of total), fine grain."""
    for r in range(h):
        t = min(1.0, (top + r) / max(1, total * 0.55))
        rect(a, x, y + r, w, 1, lerp(BEZEL_TOP, BEZEL, t))
    grain(a, x, y, w, h, amp)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


# ------------------------------------------------------------------------------------------
# The steel mesh: stadium holes in staggered rows, supersampled
# ------------------------------------------------------------------------------------------

MESH_PX = 6.25     # hole pitch: 4 holes per 25 px, so 25-wide tiles repeat seamlessly
MESH_PY = 4.0      # row pitch; odd rows shifted by half a pitch
HOLE_HW = 2.1     # half length of a hole
HOLE_HH = 1.0     # half height (the stadium's end radius)


def mesh_cover(w, h, ox=0.0, oy=0.0, ss=6):
    """Per-pixel (hole coverage, lip light, lip shadow) for a w x h patch at (ox, oy)."""
    ys = (np.arange(h * ss) + 0.5) / ss + oy
    xs = (np.arange(w * ss) + 0.5) / ss + ox
    X, Y = np.meshgrid(xs, ys)
    row = np.floor(Y / MESH_PY)
    cy = row * MESH_PY + MESH_PY / 2
    off = (row % 2) * MESH_PX / 2
    cx = np.round((X - off) / MESH_PX) * MESH_PX + off
    dx = np.maximum(np.abs(X - cx) - (HOLE_HW - HOLE_HH), 0)
    dy = Y - cy
    d = np.sqrt(dx * dx + dy * dy) - HOLE_HH
    hole = (d < 0).astype(float)
    lip = ((d >= 0) & (d < 0.7) & (dy > 0.3)).astype(float)     # lower lip catches the light
    shade = ((d >= 0) & (d < 0.8) & (dy < -0.3)).astype(float)  # upper lip in shadow

    def down(m):
        return m.reshape(h, ss, w, ss).mean(axis=(1, 3))
    return down(hole), down(lip), down(shade)


def mesh(a, x, y, w, h, top=0, total=116, ox=0.0, oy=0.0):
    """Paints the mesh into a[y:y+h, x:x+w]; lands shade by window row (y + top of total)."""
    hole, lip, shade = mesh_cover(w, h, ox, oy)
    land = np.zeros((h, w, 3))
    for r in range(h):
        land[r, :] = lerp(MESH_TOP, MESH_BOT, (top + r) / max(1, total - 1))
    n = _rng.normal(0, 1.2, (h, w))[:, :, None]
    land = land + n
    land = land + lip[:, :, None] * 22 - shade[:, :, None] * 30
    out = land * (1 - hole[:, :, None]) + np.array(HOLE) * hole[:, :, None]
    a[y:y + h, x:x + w] = np.round(out).astype(np.int32)


# ------------------------------------------------------------------------------------------
# The Dell wordmark, from source/dell-logo.svg
# ------------------------------------------------------------------------------------------

_LOGO = {}


def logo_mask(width, ring=False):
    """Alpha mask (float, 0..1) of the Dell logo, `width` px wide. Without the ring it is the
    wordmark alone: the ring's group is dropped from a copy of the SVG in out/scratch."""
    key = (width, ring)
    if key in _LOGO:
        return _LOGO[key]
    svg = open(os.path.join(SOURCE, "dell-logo.svg"), encoding="utf-8").read()
    if not ring:
        svg = re.sub(r'<g\s+transform="[^"]*"\s+id="g3460">.*?</g>', "", svg, flags=re.S)
    scratch = os.path.join(HERE, "out", "scratch")
    os.makedirs(scratch, exist_ok=True)
    src = os.path.join(scratch, f"logo-{'ring' if ring else 'word'}.svg")
    with open(src, "w", encoding="utf-8") as f:
        f.write(svg)
    png = src[:-4] + ".png"
    subprocess.run(["/usr/bin/rsvg-convert", "-h", "1200", src, "-o", png], check=True)
    im = Image.open(png).convert("RGBA")
    alpha = im.getchannel("A")
    alpha = alpha.crop(alpha.getbbox())
    h = max(1, round(alpha.height * width / alpha.width))
    m = np.array(alpha.resize((width, h), Image.LANCZOS)).astype(float) / 255
    _LOGO[key] = np.clip(m, 0, 1)
    return _LOGO[key]


def paint_mask(a, m, x, y, col):
    h, w = m.shape
    region = a[y:y + h, x:x + w].astype(float)
    a[y:y + h, x:x + w] = np.round(region * (1 - m[:, :, None]) + np.array(col) * m[:, :, None]).astype(np.int32)


def G(*rows):
    return list(rows)


# 5-row font for text.bmp, titles and gen.bmp's letters.
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

# Wordmark letters for the main titlebar: capitals 7 rows high, lowercase on a 5-row x-height
# with the p's descender below.
WORDMARK = {
    "Y": G("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "T": G("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "M": G("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "i": G(".#.", "...", "##.", ".#.", ".#.", ".#.", "###"),
    "n": G(".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "a": G(".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "m": G(".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "p": G(".....", ".....", "####.", "#...#", "#...#", "#...#", "####.", "#....", "#...."),
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



# ------------------------------------------------------------------------------------------
# TrueType print (the bezel's italic model name, the LCD's digits)
# ------------------------------------------------------------------------------------------

ITALIC = "/usr/share/fonts/open-sans/OpenSans-SemiboldItalic.ttf"
ITALIC_BOLD = "/usr/share/fonts/open-sans/OpenSans-BoldItalic.ttf"


def tt_mask(s, size, path=ITALIC, ss=4):
    """Antialiased mask of s (float 0..1), rendered at ss x and scaled down; (mask, baseline)."""
    f = ImageFont.truetype(path, size * ss)
    l, t, r, b = f.getbbox(s, anchor="ls")
    im = Image.new("L", (r - l + 4 * ss, b - t + 4 * ss), 0)
    ImageDraw.Draw(im).text((2 * ss - l, 2 * ss - t), s, fill=255, font=f, anchor="ls")
    w, h = -(-im.width // ss), -(-im.height // ss)
    im = im.crop((0, 0, w * ss, h * ss)).resize((w, h), Image.BOX)
    return np.array(im).astype(float) / 255, (2 * ss - t) / ss


def tt_print(a, s, x, baseline, size, col, path=ITALIC):
    m, base = tt_mask(s, size, path)
    y = int(round(baseline - base))
    m = m[:, 1:]  # the mask's left margin is 2px; keep x as the ink's left edge (about)
    h, w = m.shape
    y0, x0 = max(0, y), max(0, x - 1)
    m = m[y0 - y:, x0 - (x - 1):]
    h = min(m.shape[0], a.shape[0] - y0)
    w = min(m.shape[1], a.shape[1] - x0)
    paint_mask(a, m[:h, :w], x0, y0, col)
    return x + w


def tt_width(s, size, path=ITALIC):
    m, _ = tt_mask(s, size, path)
    cols = np.where(m.max(0) > 0.15)[0]
    return int(cols[-1] - cols[0] + 1)


# ------------------------------------------------------------------------------------------
# Glyphs and keys
# ------------------------------------------------------------------------------------------

GLYPHS = {
    "prev": G("...##", "..##.", ".##..", "##...", ".##..", "..##.", "...##"),
    "next": G("##...", ".##..", "..##.", "...##", "..##.", ".##..", "##..."),
    "check": G(".......##", "......##.", ".....##..", "##..##...", ".####....", "..##....."),
    "pause": G("##.##", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##"),
    "power": G("...#...", ".#.#.#.", "#..#..#", "#.....#", "#.....#", ".#...#.", "..###.."),
    "eject": G("...#...", "..###..", ".#####.", "#######", ".......", "#######"),
    "close": G("#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "min": G(".....", ".....", ".....", ".....", "#####"),
    "shade": G("#####", ".....", ".....", ".....", "....."),
    "tick": G("....#", "...#.", "#.#..", ".#..."),
    "home": G("..#..", ".###.", "#####", ".#.#.", ".###."),
}


def glyph(a, name, x, y, col):
    for r, row in enumerate(GLYPHS[name]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + c, y + r, col)


def glyph_center(a, name, cx, cy, col):
    g = GLYPHS[name]
    glyph(a, name, cx - len(g[0]) // 2, cy - len(g) // 2, col)


def key(a, x, y, w, h, pressed=False, corner=None):
    """A small dark-grey key (the PowerEdge's < check > keys): satin face, black seam round it.
    `corner` is the colour put in the rounded corners (what shows behind the key)."""
    for r in range(h):
        t = r / max(1, h - 1)
        col = lerp((50, 52, 58), (62, 64, 71), t) if pressed else lerp(KEY_TOP, KEY_BOT, t)
        rect(a, x, y + r, w, 1, col)
    box(a, x, y, w, h, KEY_RIM)
    if pressed:
        rect(a, x + 1, y + 1, w - 2, 1, (34, 35, 40))
        rect(a, x + 1, y + 1, 1, h - 2, (40, 41, 46))
    else:
        rect(a, x + 1, y + 1, w - 2, 1, (128, 131, 140))
        rect(a, x + 1, y + 2, 1, h - 3, (104, 107, 115))
        rect(a, x + 1, y + h - 2, w - 2, 1, (44, 45, 51))
    if corner is not None:
        for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
            px(a, cx, cy, corner)


def key_glyph(a, name, x, y, w, h, pressed, col=None):
    o = 1 if pressed else 0
    ink = col or (KEY_INK_PRESSED if pressed else KEY_INK)
    glyph_center(a, name, x + w // 2 + o, y + h // 2 + o, ink)


def caption_key(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar key."""
    key(a, x, y, 9, 9, pressed, corner=BEZEL_LO)
    ink = KEY_INK if lit else (150, 152, 158)
    o = 1 if pressed else 0
    if kind == "options":
        # the small round ID button: a grey dome with an "i"
        rect(a, x, y, 9, 9, BEZEL)
        for yy in range(9):
            for xx in range(9):
                d = ((xx - 4) ** 2 + (yy - 4) ** 2) ** 0.5
                if d <= 4.3:
                    c = lerp((110, 112, 120), (50, 52, 58), yy / 8) if not pressed else (48, 50, 56)
                    if d > 3.4:
                        c = KEY_RIM
                    px(a, x + xx, y + yy, c)
        px(a, x + 4 + o, y + 2 + o, ink)
        rect(a, x + 4 + o, y + 4 + o, 1, 3, ink)
    else:
        glyph(a, {"minimize": "min", "shade": "shade", "close": "close"}[kind], x + 2 + o, y + 2 + o, ink)


# ------------------------------------------------------------------------------------------
# The LCD: black glass, the lit blue field
# ------------------------------------------------------------------------------------------


def lcd_window(a, x, y, w, h):
    """Black glass round a lit field: the glass is (x, y, w, h); the field is inset 2px."""
    rect(a, x - 1, y - 1, w + 2, 1, BEZEL_LO)
    rect(a, x - 1, y - 1, 1, h + 2, BEZEL_LO)
    rect(a, x - 1, y + h, w + 2, 1, BEZEL_HI)
    rect(a, x + w, y - 1, 1, h + 2, (52, 54, 60))
    rect(a, x, y, w, h, LCD_BG)
    rect(a, x + 2, y + 2, w - 4, h - 4, BAR)


def badge(a, x, y, w, h):
    """The brushed aluminium badge with the DELL wordmark standing out in bright relief."""
    rect(a, x, y, w, h, ALU)
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp((190, 192, 197), (150, 153, 159), r / max(1, h - 1)))
    grain(a, x, y, w, h, 3.0)
    rect(a, x, y, w, 1, ALU_HI)
    rect(a, x, y, 1, h, (222, 223, 226))
    rect(a, x, y + h - 1, w, 1, ALU_LO)
    rect(a, x + w - 1, y, 1, h, ALU_LO)
    m = np.clip((logo_mask(w - 4) - 0.12) * 1.5, 0, 1)   # crisper edges at this size
    lx, ly = x + 2, y + (h - m.shape[0]) // 2 - 1
    paint_mask(a, np.clip(m * 1.3, 0, 1), lx + 1, ly + 1, (70, 72, 78))   # the relief's shadow
    paint_mask(a, m, lx, ly, (250, 251, 252))


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, RECESS)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        key(a, 0, y, 8, h, pressed=on, corner=RECESS)
        gy = y + (h - 5) // 2
        o = 1 if on else 0
        draw_text(a, TINY, letter, 2 + o, gy + o, KEY_INK_PRESSED if on else KEY_INK)
    return a


def main_titlebar(lit):
    a = new(275, 14, BEZEL)
    bezel(a, 0, 0, 275, 14, 0, 116)
    rect(a, 0, 0, 275, 1, BEZEL_HI)
    rect(a, 0, 0, 1, 14, (56, 58, 64))
    rect(a, 274, 0, 1, 14, BEZEL_LO)
    # the model name in the bezel's white italic print
    tt_print(a, "OptiPlex 9010", 19, 11, 10, (244, 245, 248) if lit else (150, 152, 158))
    caption_key(a, 6, 3, "options", lit)
    caption_key(a, 244, 3, "minimize", lit)
    caption_key(a, 254, 3, "shade", lit)
    caption_key(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, BEZEL)
    for kind, x, y, py_ in [("options", 0, 0, 9), ("minimize", 9, 0, 9), ("close", 18, 0, 9)]:
        b = new(9, 9)
        caption_key(b, 0, 0, kind, True)
        a[y:y + 9, x:x + 9] = b
        caption_key(b, 0, 0, kind, True, pressed=True)
        a[py_:py_ + 9, x:x + 9] = b
    b = new(9, 9)
    caption_key(b, 0, 0, "shade", True)
    a[18:27, 0:9] = b
    caption_key(b, 0, 0, "shade", True, pressed=True)
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

LCD_L = (20, 18, 86, 44)        # glass x, y, w, h: time and analyzer (field 22..103, 20..59)
LCD_R = (107, 18, 163, 38)      # title and info rows (field 109..267, 20..53)
MESH_Y = 86                     # the mesh from here down


def jack(a, x, y):
    """A 3.5mm jack: 7x7 ring in the bezel."""
    for yy in range(7):
        for xx in range(7):
            d = ((xx - 3) ** 2 + (yy - 3) ** 2) ** 0.5
            if d <= 3.4:
                c = (6, 6, 8) if d < 1.6 else lerp((120, 122, 130), (40, 41, 46), yy / 6)
                px(a, x + xx, y + yy, c)


def mic_icon(a, x, y, col):
    rect(a, x + 1, y, 1, 3, col)
    px(a, x, y + 2, col)
    px(a, x + 2, y + 2, col)
    px(a, x + 1, y + 3, col)
    px(a, x + 1, y + 4, col)


def phones_icon(a, x, y, col):
    rect(a, x + 1, y, 3, 1, col)
    px(a, x, y + 1, col)
    px(a, x + 4, y + 1, col)
    rect(a, x, y + 2, 1, 3, col)
    rect(a, x + 4, y + 2, 1, 3, col)


def plate(a, x, y, w, h):
    """A black plastic recess set into the mesh (rounded corners keep the mesh)."""
    keep = [a[y, x].copy(), a[y, x + w - 1].copy(), a[y + h - 1, x].copy(), a[y + h - 1, x + w - 1].copy()]
    rect(a, x, y, w, h, RECESS)
    rect(a, x, y, w, 1, (4, 4, 5))
    rect(a, x, y, 1, h, (6, 6, 7))
    rect(a, x, y + h - 1, w, 1, (60, 62, 68))
    rect(a, x + w - 1, y, 1, h, (48, 50, 56))
    for (cx, cy), c in zip(((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)), keep):
        a[cy, cx] = c


def make_main():
    a = new(275, 116, BEZEL)
    bezel(a, 0, 14, 275, MESH_Y - 14, 14, 116)
    a[0:14, :] = main_titlebar(True)
    rect(a, 0, 14, 1, MESH_Y - 14, (56, 58, 64))
    rect(a, 274, 14, 1, MESH_Y - 14, BEZEL_LO)
    # the bezel's lower lip over the mesh
    rect(a, 0, MESH_Y - 2, 275, 1, (60, 62, 68))
    rect(a, 0, MESH_Y - 1, 275, 1, BEZEL_LO)
    mesh(a, 0, MESH_Y, 275, 116 - MESH_Y, MESH_Y, 116)
    rect(a, 0, MESH_Y, 1, 116 - MESH_Y, (120, 122, 128))
    rect(a, 274, MESH_Y, 1, 116 - MESH_Y, (96, 98, 104))
    rect(a, 0, 115, 275, 1, (90, 92, 98))

    # clutterbar seat (titlebar.bmp draws the keys)
    a[22:65, 10:18] = clutter_bar("")

    # the LCD: two lit fields behind one strip of black glass
    lcd_window(a, *LCD_L)
    lcd_window(a, *LCD_R)
    for yy in (30, 34):
        rect(a, 73, yy, 2, 2, BAR_TXT)
    # the info row: KBPS / KHZ printed on the field
    draw_text(a, TINY, "KBPS", 129, 43, BAR_DIM)
    draw_text(a, TINY, "KHZ", 169, 43, BAR_DIM)

    # under the left LCD: microphone and headphone jacks, the hard-drive light
    jack(a, 24, 62)
    jack(a, 34, 62)
    rect(a, 45, 65, 3, 1, (210, 220, 236))   # the hard-drive light
    rect(a, 45, 66, 3, 1, (96, 100, 110))

    # the slim optical drive across the bezel: its tray seam is the seek bar
    rect(a, 12, 70, 254, 14, (38, 39, 44))
    rect(a, 12, 70, 254, 1, (66, 68, 74))
    rect(a, 12, 83, 254, 1, BEZEL_LO)
    rect(a, 12, 70, 1, 14, (60, 62, 68))
    rect(a, 265, 70, 1, 14, BEZEL_LO)
    grain(a, 13, 71, 252, 12, 1.0)
    slot_seat(a, 16, 72, 248)
    px(a, 266 - 4, 78, (20, 20, 22))

    # on the mesh: the transport keys' recess, the ports' recess, the badge
    plate(a, 14, 86, 146, 22)
    plate(a, 162, 87, 78, 19)
    badge(a, 241, 88, 32, 19)
    return a


def slot_seat(a, x, y, w):
    """The drive's tray seam (the seek bar's track), rows y..y+9."""
    rect(a, x, y + 3, w, 4, (16, 16, 18))
    rect(a, x, y + 3, w, 1, (4, 4, 5))
    rect(a, x, y + 7, w, 1, (70, 72, 78))
    # the drive's DVD+RW print and tray light at the ends, under the seam's line
    rect(a, x, y + 5, w, 1, (24, 24, 27))


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36): the < check > keys and friends
# ------------------------------------------------------------------------------------------

TRANSPORT = [("prev", 0, 23, 18), ("check", 23, 23, 18), ("pause", 46, 23, 18),
             ("power", 69, 23, 18), ("next", 92, 22, 18)]


def make_cbuttons():
    a = new(136, 36, RECESS)
    for kind, x, w, h in TRANSPORT:
        for pressed, y in ((False, 0), (True, 18)):
            key(a, x, y, w, h, pressed, corner=RECESS)
            col = None
            if kind == "power":
                col = (150, 255, 160) if pressed else POWER_GREEN
            key_glyph(a, kind, x, y, w, h, pressed, col)
    for pressed, y in ((False, 0), (True, 16)):
        key(a, 114, y, 22, 16, pressed, corner=RECESS)
        key_glyph(a, "eject", 114, y, 22, 16, pressed)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85): USB ports (shuffle, repeat), keys with a check (EQ, PL)
# ------------------------------------------------------------------------------------------


def usb_port(a, x, y, on):
    """A front USB-A port, 14x6: steel shell, the tongue blue when lit (USB 3.0's blue)."""
    rect(a, x, y, 14, 6, (150, 154, 162))
    box(a, x, y, 14, 6, (90, 92, 100))
    rect(a, x + 1, y + 1, 12, 4, (6, 6, 8))
    rect(a, x + 2, y + 1, 10, 2, USB_BLUE if on else (40, 42, 48))
    if on:
        rect(a, x + 2, y + 1, 10, 1, (90, 160, 250))


def trident(a, x, y, col):
    """The USB trident, 7x5."""
    rect(a, x, y + 2, 6, 1, col)
    px(a, x + 6, y + 2, col)
    px(a, x + 2, y + 1, col)
    px(a, x + 3, y, col)
    px(a, x + 4, y, col)
    px(a, x + 3, y + 3, col)
    px(a, x + 4, y + 4, col)
    px(a, x, y + 1, col)
    px(a, x, y + 3, col)


def port_toggle(a, x, y, w, h, label, on, pressed):
    rect(a, x, y, w, h, RECESS)
    o = 1 if pressed else 0
    pw = 14
    usb_port(a, x + (w - pw) // 2 + o, y + 1 + o, on)
    ink = KEY_INK if on else (128, 130, 138)
    if pressed:
        ink = KEY_INK_PRESSED
    text_center(a, TINY, label, x + w // 2 + o, y + 9 + o, ink)
    if w > 40:
        trident(a, x + 3 + o, y + 2 + o, USB_BLUE if on else (70, 72, 80))
        trident(a, x + w - 10 + o, y + 2 + o, USB_BLUE if on else (70, 72, 80))


def check_key(a, x, y, w, h, label, on, pressed):
    rect(a, x, y, w, h, BEZEL)
    key(a, x, y, w, h, pressed, corner=BEZEL)
    o = 1 if pressed else 0
    tw = text_w(TINY, label)
    tx = x + (w - (tw + 6)) // 2 + o
    draw_text(a, TINY, label, tx, y + (h - 5) // 2 + o, KEY_INK if on else (140, 142, 150))
    glyph(a, "tick", tx + tw + 2, y + (h - 4) // 2 + o, (150, 190, 255) if on else (74, 76, 84))


def make_shufrep():
    a = new(92, 85, RECESS)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        port_toggle(a, 0, y, 28, 15, "REPEAT", on, pressed)
        port_toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        check_key(a, x, 61, 23, 12, label, False, pressed)
        check_key(a, x, 73, 23, 12, label, True, pressed)
    return a


# ------------------------------------------------------------------------------------------
# monoster, playpaus, numbers, nums_ex, text: the lit field
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, BAR)
    for y, on in ((0, True), (12, False)):
        for x0, w, s in ((0, 29, "STEREO"), (29, 27, "MONO")):
            if on:
                # the selected item: a pale box, the text inverted into it
                rect(a, x0 + 1, y + 1, w - 2, 10, BOX)
                text_center(a, TINY, s, x0 + w // 2, y + 3, BAR)
            else:
                text_center(a, TINY, s, x0 + w // 2, y + 3, BAR_DIM)
    return a


def make_playpaus():
    a = new(48, 9, BAR)
    tri_right(a, 2, 1, 7, BAR_TXT)
    rect(a, 9 + 2, 1, 2, 7, BAR_TXT)
    rect(a, 9 + 5, 1, 2, 7, BAR_TXT)
    rect(a, 18 + 2, 2, 5, 5, BAR_TXT)
    rect(a, 36, 0, 3, 9, BAR)
    rect(a, 39 + 1, 3, 1, 3, BAR_TXT)
    return a


def tri_right(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x, y + r, n, 1, col)


def digit_cell(ch):
    """9x13: an italic numeral, white on the lit field (the LCD's bigger font)."""
    a = new(9, 13, BAR)
    if ch == " ":
        return a
    if ch == "-":
        rect(a, 2, 6, 5, 2, BAR_TXT)
        return a
    m, base = tt_mask(ch, 15, ITALIC_BOLD)
    cols = np.where(m.max(0) > 0.1)[0]
    rows = np.where(m.max(1) > 0.1)[0]
    m = m[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    # fit into 8x11 (narrow the glyph if it must)
    hh, ww = m.shape
    tw = min(ww, 8)
    th = 11
    im = Image.fromarray((m * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
    m = np.clip(np.array(im).astype(float) / 255 * 1.15, 0, 1)
    paint_mask(a, m, (9 - tw + 1) // 2, 1, BAR_TXT)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, BAR)
    for n in range(10):
        a[:, 9 * n:9 * n + 9] = digit_cell(str(n))
    a[:, 90:99] = digit_cell(" ")
    if ex:
        a[:, 99:108] = digit_cell("-")
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, BAR)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key_ = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key_, col * 5, row * 6, BAR_TXT)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10): the tray seam; the thumb is the EST pull-out tag
# ------------------------------------------------------------------------------------------


def est_tag(a, x, y, w, h, selected):
    face = lerp(EST, WHITE, 0.25) if selected else EST
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(lerp(face, WHITE, 0.35), lerp(face, (0, 0, 0), 0.18), r / max(1, h - 1)))
    box(a, x, y, w, h, (40, 52, 70))
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, (38, 39, 44))
    # the tag's black grip ends, as it sits in the bezel
    rect(a, x + 1, y + 1, 3, h - 2, (20, 21, 24))
    rect(a, x + w - 4, y + 1, 3, h - 2, (20, 21, 24))
    text_center(a, TINY, "EST", x + w // 2, y + 3, (26, 40, 70))


def make_posbar(main):
    a = new(307, 10, BEZEL)
    a[0:10, 0:248] = main[72:82, 16:264]
    est_tag(a, 248, 0, 29, 10, False)
    est_tag(a, 278, 0, 29, 10, True)
    return a


# ------------------------------------------------------------------------------------------
# volume.bmp / balance.bmp (68 x 433): little LCD bars in the bezel
# ------------------------------------------------------------------------------------------


def slider_thumb(a, x, y, pressed):
    rect(a, x, y, 14, 11, BEZEL)
    key(a, x, y, 14, 11, pressed, corner=BEZEL)
    o = 1 if pressed else 0
    for gx in (x + 5, x + 8):
        rect(a, gx + o, y + 3 + o, 1, 5, (30, 31, 35))
        rect(a, gx + 1 + o, y + 3 + o, 1, 5, (140, 143, 152))


def lcd_strip(a, x, y, w, h):
    rect(a, x - 1, y - 1, w + 2, 1, BEZEL_LO)
    rect(a, x - 1, y - 1, 1, h + 2, BEZEL_LO)
    rect(a, x - 1, y + h, w + 2, 1, BEZEL_HI)
    rect(a, x + w, y - 1, 1, h + 2, (52, 54, 60))
    rect(a, x, y, w, h, LCD_BG)


def make_volume(main):
    a = new(68, 433, BEZEL)
    seat = main[57:70, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 13, 0:68] = seat
        lcd_strip(a, 2, y + 3, 64, 7)
        level = (i + 1) / 28
        lit_to = 3 + round(level * 62)
        for x in range(4, 64, 3):
            col = BAR if x < lit_to else (18, 20, 34)
            rect(a, x, y + 5, 2, 3, col)
        a[y + 13:y + 15, :] = BEZEL
    for x0, pressed in ((0, True), (15, False)):
        slider_thumb(a, x0, 422, pressed)
    return a


def make_balance(main):
    a = new(68, 433, BEZEL)
    seat = main[57:70, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 13, 9:47] = seat
        lcd_strip(a, 11, y + 3, 34, 7)
        reach = round(15 * i / 27)
        for x in range(12, 44, 2):
            d = abs(x - 27.5)
            on = d <= 1 or d <= reach
            rect(a, x, y + 5, 1, 3, BAR if on else (18, 20, 34))
    for x0, pressed in ((0, True), (15, False)):
        slider_thumb(a, x0, 422, pressed)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315): bezel strip above, the mesh below with black slots in it
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
EQ_MESH_Y = 37


def eq_titlebar(lit):
    a = new(275, 14, BEZEL)
    bezel(a, 0, 0, 275, 14, 0, 116)
    rect(a, 0, 0, 275, 1, BEZEL_HI)
    rect(a, 0, 0, 1, 14, (56, 58, 64))
    rect(a, 274, 0, 1, 14, BEZEL_LO)
    tt_print(a, "Equalizer", 7, 11, 10, (244, 245, 248) if lit else (150, 152, 158))
    caption_key(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    """14x63 black slot; the lit LCD column rises to the value (n of 0..27)."""
    rect(a, x, y, 14, 63, RECESS)
    box(a, x, y, 14, 63, (4, 4, 5))
    rect(a, x, y + 62, 14, 1, (70, 72, 78))
    rect(a, x + 13, y, 1, 63, (56, 58, 64))
    rect(a, x + 4, y + 2, 6, 59, LCD_BG)
    v = n / 27
    top = round((1 - v) * 51) + 5
    for r in range(3, 60):
        if r % 2:
            continue
        rect(a, x + 5, y + r, 4, 1, BAR if r >= top else (16, 18, 30))
    rect(a, x + 1, y + 31, 2, 1, (110, 112, 120))
    rect(a, x + 11, y + 31, 2, 1, (110, 112, 120))


def make_eqmain():
    a = new(275, 315, BEZEL)
    bezel(a, 0, 14, 275, EQ_MESH_Y - 14, 14, 116)
    a[0:14, :] = eq_titlebar(True)
    rect(a, 0, 14, 1, EQ_MESH_Y - 14, (56, 58, 64))
    rect(a, 274, 14, 1, EQ_MESH_Y - 14, BEZEL_LO)
    rect(a, 0, EQ_MESH_Y - 2, 275, 1, (60, 62, 68))
    rect(a, 0, EQ_MESH_Y - 1, 275, 1, BEZEL_LO)
    mesh(a, 0, EQ_MESH_Y, 275, 116 - EQ_MESH_Y, EQ_MESH_Y, 116)
    rect(a, 0, EQ_MESH_Y, 1, 116 - EQ_MESH_Y, (120, 122, 128))
    rect(a, 274, EQ_MESH_Y, 1, 116 - EQ_MESH_Y, (96, 98, 104))
    rect(a, 0, 115, 275, 1, (90, 92, 98))
    # the graph's LCD (the graph sprite covers 86,17 113x19)
    lcd_strip(a, 86, 17, 113, 19)
    # black plates on the mesh: dB scale, band labels
    plate(a, 40, 37, 36, 65)
    for lbl, yy in (("+12DB", 41), ("0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, SILVER_PRINT)
    plate(a, 14, 104, 249, 10)
    text_center(a, TINY, "PREAMP", 28, 106, SILVER_PRINT)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, SILVER_PRINT)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)

    # under the window: keys
    caption_key(a, 0, 125, "close", True, pressed=True)
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        check_key(a, x, 119, w, 12, label, on, pressed)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    for y, pressed in ((164, False), (176, True)):
        rect(a, 0, y, 11, 11, RECESS)
        key(a, 0, y, 11, 11, pressed, corner=RECESS)
        o = 1 if pressed else 0
        rect(a, 2 + o, y + 5 + o, 7, 1, (30, 31, 35))
        rect(a, 2 + o, y + 6 + o, 7, 1, (140, 143, 152))
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        rect(a, 224, y, 44, 12, BEZEL)
        key(a, 224, y, 44, 12, pressed, corner=BEZEL)
        o = 1 if pressed else 0
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 3 + o, KEY_INK_PRESSED if pressed else KEY_INK)
    # graph: the lit field with faint unlit grid dots, the curve white
    rect(a, 0, 294, 113, 19, BAR)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, (36, 64, 184))
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, (36, 64, 184))
    for r in range(19):
        px(a, 115, 294 + r, BAR_TXT)
    for x in range(113):
        px(a, x, 314, BAR_DIM if x % 3 != 2 else BAR)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): bezel band and sides, mesh foot
# ------------------------------------------------------------------------------------------


def bar20(w, lit):
    a = new(w, 20, BEZEL)
    bezel(a, 0, 0, w, 20, 0, 60)
    rect(a, 0, 0, w, 1, BEZEL_HI if lit else (54, 56, 62))
    rect(a, 0, 19, w, 1, BEZEL_LO)
    return a


def side_strip(w, h, outer_left):
    """Bezel side: satin black, a highlight on the outer edge, a dark line at the list."""
    t = new(w, h, BEZEL)
    for c in range(w):
        d = c if outer_left else w - 1 - c
        col = BEZEL
        if d == 0:
            col = (56, 58, 64) if outer_left else BEZEL_LO
        elif d == w - 1:
            col = BEZEL_LO
        rect(t, c, 0, 1, h, col)
    return t


def mesh_foot(w, h):
    """A mesh foot piece, phase-locked to x multiples of 25 (the tiles' grid)."""
    t = new(w, h, BEZEL)
    rect(t, 0, 0, w, 1, (60, 62, 68))
    rect(t, 0, 1, w, 1, BEZEL_LO)
    mesh(t, 0, 2, w, h - 3, 2, h)
    rect(t, 0, h - 1, w, 1, (90, 92, 98))
    return t


def foot_edges(t, left, right):
    h, w = t.shape[:2]
    if left:
        rect(t, 0, 2, 1, h - 2, (120, 122, 128))
    if right:
        rect(t, w - 1, 2, 1, h - 2, (96, 98, 104))


def small_lcd(a, x, y, w, h):
    rect(a, x - 1, y - 1, w + 2, h + 2, LCD_BG)
    rect(a, x, y, w, h, BAR)


def make_pledit():
    a = new(280, 186, BEZEL)
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar20(25, lit)
        t = bar20(25, lit)
        rect(t, 0, 0, 1, 20, (56, 58, 64))
        a[y:y + 20, 0:25] = t
        t = bar20(100, lit)
        s = "Playlist"
        tt_print(t, s, 50 - tt_width(s, 10) // 2, 14, 10, (244, 245, 248) if lit else (150, 152, 158))
        a[y:y + 20, 26:126] = t
        t = bar20(25, lit)
        rect(t, 24, 0, 1, 20, BEZEL_LO)
        caption_key(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t
    # side tiles: left 12, right 20 with the scroll groove at 5..12
    a[42:71, 0:12] = side_strip(12, 29, True)
    t = side_strip(20, 29, False)
    rect(t, 4, 0, 10, 29, RECESS)
    rect(t, 4, 0, 1, 29, BEZEL_LO)
    rect(t, 13, 0, 1, 29, (52, 54, 60))
    a[42:71, 31:51] = t
    t = new(9, 9)
    caption_key(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        rect(a, x, 53, 8, 18, RECESS)
        key(a, x, 53, 8, 18, sel, corner=RECESS)
        for gy in (59, 61, 63):
            rect(a, x + 2, gy, 4, 1, (30, 31, 35))

    # bottom pieces (38 tall): the mesh with black plates for the keys and LCDs
    t = mesh_foot(125, 38)
    foot_edges(t, True, False)
    plate(t, 11, 6, 114, 23)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        key(t, bx, 8, 22, 18, False, corner=RECESS)
        text_center(t, TINY, lbl, bx + 11, 14, KEY_INK)
    a[72:110, 0:125] = t

    t = mesh_foot(150, 38)
    foot_edges(t, False, True)
    plate(t, 1, 6, 130, 28)
    small_lcd(t, 6, 9, 56, 8)
    icons = ["prev", "check", "pause", "power", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        key(t, bx, 22, 10, 10, False, corner=RECESS)
        mini_icon(t, kind, bx, 22)
    small_lcd(t, 65, 22, 33, 8)
    px(t, 84, 24, BAR_TXT)
    px(t, 84, 27, BAR_TXT)
    key(t, 106, 8, 22, 18, False, corner=RECESS)
    text_center(t, TINY, "LIST", 117, 14, KEY_INK)
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 143 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx, gy, (60, 62, 68))
            px(t, gx + 1, gy + 1, WHITE)
    a[72:110, 126:276] = t

    a[0:38, 179:204] = mesh_foot(25, 38)
    return a


MINI = {
    "prev": G("..#", ".#.", "#..", ".#.", "..#"),
    "check": G("....#", "...#.", "#.#..", ".#..."),
    "pause": G("#.#", "#.#", "#.#", "#.#", "#.#"),
    "power": G("..#..", "#.#.#", "#...#", "#...#", ".###."),
    "next": G("#..", ".#.", "..#", ".#.", "#.."),
    "eject": G("..#..", ".###.", "#####", ".....", "#####"),
}


def mini_icon(a, kind, x, y):
    g = MINI[kind]
    gx, gy = x + 5 - len(g[0]) // 2, y + 5 - len(g) // 2
    col = POWER_GREEN if kind == "power" else KEY_INK
    for r, row in enumerate(g):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, gx + c, gy + r, col)


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_gen():
    a = new(194, 109, BEZEL)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn=None):
            t = bar20(25, lit)
            if fn:
                fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 1, 20, (56, 58, 64))

        def right(t):
            caption_key(t, 14, 3, "close", lit)
            rect(t, 24, 0, 1, 20, BEZEL_LO)

        piece(0, left)
        piece(26)
        piece(52)
        piece(78)
        piece(104)
        piece(130, right)

    def bottom(w, grip, left_edge):
        t = mesh_foot(w, 14)
        foot_edges(t, left_edge, not left_edge)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 6 - 3 * k + 3 * j, 9 - 3 * j
                    px(t, gx, gy, (60, 62, 68))
                    px(t, gx + 1, gy + 1, WHITE)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = mesh_foot(25, 14)
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = side_strip(w, h, outer_left)
    t = new(9, 9)
    caption_key(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: white print on the bezel (cells copy the band's rows 4..10)
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        strip = bar20(194, lit)[4:11]
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            a[y:y + 7, x:x + w] = strip[:, x:x + w]
            draw_text(a, FONT5, c, x, y + 1, (238, 240, 244) if lit else (150, 152, 158))
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp (the 18 colours; genex_wacup.py completes it)
# ------------------------------------------------------------------------------------------

GENEX_COLOURS = [
    (32, 58, 190),     # item background (the lit field)
    (226, 232, 250),   # item text
    BEZEL,             # window background
    KEY_INK,           # button text
    (226, 230, 238),   # window text
    (70, 72, 80),      # dividers
    (14, 26, 104),     # selection bar
    (52, 54, 60),      # list header background
    (238, 240, 244),   # list header text
    (96, 98, 106),     # header frame light
    (8, 8, 10),        # header frame dark
    (40, 42, 48),      # header frame pressed
    BEZEL,             # header dead area
    (66, 68, 76),      # scrollbar
    BAR,               # scrollbar 2
    (50, 52, 58),      # scrollbar pressed
    (110, 140, 250),   # scrollbar pressed 2
    RECESS,            # scrollbar dead area
]


def make_genex():
    a = new(256, 64, BEZEL)
    for i, c in enumerate(GENEX_COLOURS):
        px(a, 48 + 2 * i, 0, c)
    key(a, 0, 1, 47, 15, False, corner=BEZEL)
    key(a, 0, 16, 47, 15, True, corner=BEZEL)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    spec = [(ramp([WHITE, (196, 212, 255), (128, 160, 250)], i / 15), f"spectrum {i + 1}") for i in range(16)]
    return ([(BAR, "background"), ((40, 70, 204), "dots")] + spec
            + [(WHITE, "oscilloscope 1"), ((226, 234, 255), "oscilloscope 2"), ((196, 212, 255), "oscilloscope 3"),
               ((160, 184, 252), "oscilloscope 4"), ((128, 160, 250), "oscilloscope 5"), (WHITE, "peaks")])


def hexc(c):
    return "#%02X%02X%02X" % c


PLEDIT = dict(Normal=(172, 190, 250), Current=WHITE, NormalBG=(32, 58, 190), SelectedBG=(14, 26, 104),
              MbBG=(32, 58, 190), MbFG=(226, 232, 250))


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
            f"{T.title} - a skin in the style of the Dell OptiPlex 9010 desktop (2012): the satin\n"
            "black bezel with its slim optical drive and front ports, the silver stadium-hole steel\n"
            "mesh, the brushed aluminium DELL badge, and a PowerEdge-style blue-backlit front LCD.\n"
            "Every bitmap was drawn by a script (gen_skin.py).\n\n"
            "Dell logo (c) Dell Inc. OptiPlex and PowerEdge are names of Dell Inc.\n"
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


PREVIEW_ROWS = [("Dial-Up Dreams - Boot Sequence", "4:12"), ("Front Panel - Blue Backlight", "3:47"),
                ("Stadium Holes - Steel Mesh", "5:03"), ("Tray Open - Slim Drive", "2:58"),
                ("Service Tag - Express Code", "6:21"), ("Cubicle Hum - Fan Curve", "3:33"),
                ("Setup / View - Menu Line", "4:40"), ("USB 3.0 - SuperSpeed", "3:09"),
                ("Badge Plate - Brushed", "5:51"), ("Help Desk - Ticket 9010", "4:05"),
                ("Power On - Self Test", "3:22")]


def preview():
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title="Front Panel - Blue Backlight (2012 Mix)", bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True, bitmap=True,
             title="OPTIPLEX 9010 - SERVICE TAG 7X3K9", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
    assert (space == np.array(BAR)).all(), "space cell must be the plain display colour"
    assert text_ink() == BAR_TXT, text_ink()
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
