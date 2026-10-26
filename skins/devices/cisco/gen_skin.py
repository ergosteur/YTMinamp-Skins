#!/usr/bin/python3
"""Cisco classic hardware: Winamp 2.x skins in the style of late-1990s/2000s Cisco gear.

Based on skins/ember/gen_skin.py (its sheet layouts and preview renderer are kept). Two themes:

  cisco       the teal powder-coat of the Catalyst 2900 XL / 2600 era, green-phosphor console,
              the 1996 "CISCO SYSTEMS" bridge badge (Cisco.wsz)
  cisco-2800  the 2800-series ISR's dark blue-grey, amber console, the 2006 bridge logo
              (Cisco-2800.wsz)

    /usr/bin/python3 -I gen_skin.py              # builds both
    /usr/bin/python3 -I gen_skin.py cisco-2800   # one theme
    /usr/bin/python3 -I gen_skin.py --list

Sheets go to out/<theme>/, scratch files to out/scratch/; the .wsz and preview-<theme>.png beside
this file. The logos are read from source/ (downloaded SVGs, rasterised with rsvg-convert) only to
measure the bridge's bar heights; the badges themselves are drawn as pixels here.
"""

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
SRC = os.path.join(HERE, "source")
SCRATCH = os.path.join(OUT_ROOT, "scratch")
OUT = None
T = None
SEP = (255, 0, 255)  # gen.bmp letter separators (never shown)

# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    # Cisco's "teal" (the colour is unofficial: forums cite Pantone 7477; on the 2600 and the
    # Catalyst 2900 XL it photographs as a sea-green teal around #3E8C8C, which is what is used).
    "cisco": SimpleNamespace(
        wsz="Cisco.wsz", metal=(62, 140, 140), amp=2.6,
        silk=(236, 242, 240), silk_dim=(150, 188, 186),
        term=(4, 10, 6), ink=(86, 242, 112), ink_hi=(200, 255, 210), ink_dim=(34, 120, 54),
        ink_ghost=(12, 36, 18), sel=(18, 72, 34),
        logo="1996", prompt="Switch#", series="CATALYST 2900 SERIES XL",
    ),
    # The 2800 ISR (2005-): dark blue-grey front, console sessions often on amber terminals.
    "cisco-2800": SimpleNamespace(
        wsz="Cisco-2800.wsz", metal=(58, 72, 88), amp=2.2,
        silk=(232, 236, 240), silk_dim=(150, 160, 172),
        term=(10, 7, 2), ink=(255, 178, 40), ink_hi=(255, 226, 160), ink_dim=(140, 92, 20),
        ink_ghost=(40, 26, 6), sel=(84, 52, 8),
        logo="2006", prompt="Router#", series="CISCO 2800 SERIES",
    ),
}

LED_GREEN = (96, 250, 110)
LED_GREEN_GLOW = (40, 120, 50)
LED_AMBER = (255, 176, 36)
LED_OFF = (64, 72, 66)      # unlit, on a dark key
LED_DARK = (24, 28, 27)     # unlit, on the bare metal
GOLD = (214, 176, 84)
CABLE = [(150, 205, 238), (104, 174, 220), (74, 142, 196), (48, 104, 156)]   # Cisco console-cable blue
KEY = (36, 40, 42)          # charcoal mode-button face
SOCKET = (8, 9, 10)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def shade(c, f):
    return tuple(max(0, min(255, int(round(v * f)))) for v in c)


def use_theme(name):
    global OUT, T, _rng
    T = THEMES[name]
    T.name = name
    T.hi = shade(T.metal, 1.32)
    T.lo = shade(T.metal, 0.52)
    T.dk = shade(T.metal, 0.34)
    T.mid = shade(T.metal, 0.8)
    OUT = os.path.join(OUT_ROOT, name)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    _rng = np.random.default_rng(2600)


# ------------------------------------------------------------------------------------------
# Canvas helpers
# ------------------------------------------------------------------------------------------


def new(w, h, col=(0, 0, 0)):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):y + h, max(0, x):x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def raised(a, x, y, w, h, hi=None, lo=None):
    hi = T.hi if hi is None else hi
    lo = T.lo if lo is None else lo
    rect(a, x, y, w, 1, hi)
    rect(a, x, y, 1, h, hi)
    rect(a, x, y + h - 1, w, 1, lo)
    rect(a, x + w - 1, y, 1, h, lo)


def sunken(a, x, y, w, h, hi=None, lo=None):
    hi = T.hi if hi is None else hi
    lo = T.lo if lo is None else lo
    raised(a, x, y, w, h, lo, hi)


_rng = np.random.default_rng(2600)


def powder(a, x, y, w, h, col=None, amp=None):
    """Powder-coated metal: flat colour with a fine, even stipple."""
    col = T.metal if col is None else col
    amp = T.amp if amp is None else amp
    rect(a, x, y, w, h, col)
    n = _rng.normal(0, 1, (h, w))
    n = 0.7 * n + 0.15 * np.roll(n, 1, 0) + 0.15 * np.roll(n, 1, 1)
    a[y:y + h, x:x + w] += np.round(n * amp).astype(np.int32)[:, :, None]


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


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
    "/": G("..#", "..#", ".#.", "#..", "#.."),
}
for _c in "0123456789+-.#":
    TINY[_c] = FONT5[_c]

# lowercase for the console prompt (x-height 3)
PROMPT = dict(TINY)
PROMPT.update({
    "w": G(".....", ".....", "#...#", "#.#.#", ".#.#."),
    "i": G("#", ".", "#", "#", "#"),
    "t": G(".#.", "###", ".#.", ".#.", "..#"),
    "c": G("...", "...", ".##", "#..", ".##"),
    "h": G("#..", "#..", "##.", "#.#", "#.#"),
    "o": G("...", "...", ".#.", "#.#", ".#."),
    "u": G("...", "...", "#.#", "#.#", ".##"),
    "e": G("...", ".#.", "#.#", "##.", ".##"),
    "r": G("...", "...", "#.#", "##.", "#.."),
})


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
                    px(a, x + k, y + r, col)
        x += len(g[0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1, shadow=None):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow)


# ------------------------------------------------------------------------------------------
# The logos: bar heights measured from the downloaded SVGs, drawn as pixels
# ------------------------------------------------------------------------------------------

_BARS = {}


def logo_bars(which):
    """[(top_frac, bottom_frac)] per bar of the bridge, measured from the rasterised SVG."""
    if which in _BARS:
        return _BARS[which]
    if which == "1996":
        svg = os.path.join(SRC, "logo-1996", "Cisco_logo_1996.svg")
    else:
        svg = os.path.join(SRC, "logo-2006", "Cisco_logo.svg")
    png = os.path.join(SCRATCH, f"logo-{which}.png")
    subprocess.run(["/usr/bin/rsvg-convert", "-h", "400", svg, "-o", png], check=True)
    a = np.array(Image.open(png).convert("RGBA")).astype(int)
    H, W, _ = a.shape
    bars = []
    if which == "1996":
        # the bars are holes cut up from the bottom of the blue box
        hole = a[..., 3] < 100
        y = H - 3
        tallest = 0
        x = 0
        runs = []
        while x < W:
            if hole[y, x]:
                s = x
                while x < W and hole[y, x]:
                    x += 1
                c = (s + x) // 2
                h = 0
                while hole[y - h, c]:
                    h += 1
                runs.append(h)
                tallest = max(tallest, h)
            x += 1
        bars = [(1 - h / tallest, 1.0) for h in runs]
    else:
        blue = (a[..., 3] > 128) & (a[..., 2] > a[..., 0])
        cols = blue.any(0)
        x = 0
        spans = []
        while x < W:
            if cols[x]:
                s = x
                while x < W and cols[x]:
                    x += 1
                ys = np.where(blue[:, (s + x) // 2])[0]
                spans.append((ys.min(), ys.max()))
            x += 1
        top = min(s[0] for s in spans)
        bot = max(s[1] for s in spans)
        bars = [((s0 - top) / (bot - top), (s1 - top) / (bot - top)) for s0, s1 in spans]
    _BARS[which] = bars
    return bars


def logo_w():
    return 51 if T.logo == "1996" else 27


def draw_logo(a, x, y, col):
    """The badge, 12 rows tall from y. 1996: CISCO SYSTEMS over the bridge; 2006: bridge over CISCO."""
    bars = logo_bars(T.logo)
    if T.logo == "1996":
        draw_text(a, TINY, "CISCO", x, y, col)
        draw_text(a, TINY, "SYSTEMS", x + 24, y, col)
        # bridge: 26 one-pixel bars, two apart, up to 6 tall, standing on row y+11
        for i, (t, _) in enumerate(bars):
            h = max(1, round((1 - t) * 6))
            rect(a, x + i * 2, y + 12 - h, 1, h, col)
    else:
        for i, (t, b) in enumerate(bars):
            r0 = round(t * 5)
            r1 = round(b * 5)
            rect(a, x + i * 3, y + r0, 2, r1 - r0 + 1, col)
        draw_text(a, FONT5, "CISCO", x, y + 7, col, gap=2)


# ------------------------------------------------------------------------------------------
# Hardware pieces
# ------------------------------------------------------------------------------------------


def screw(a, cx, cy):
    """5x5 Phillips pan head."""
    hi, mid, lo, slot = (214, 220, 222), (150, 158, 162), (70, 76, 80), (40, 44, 46)
    pat = [".hhh.", "hmsmh", "hsssl", "hmsml", ".lll."]
    for r, row in enumerate(pat):
        for c, ch in enumerate(row):
            col = {"h": hi, "m": mid, "l": lo, "s": slot}.get(ch)
            if col:
                px(a, cx - 2 + c, cy - 2 + r, col)
    px(a, cx - 1, cy - 1, mid)
    px(a, cx + 2, cy + 2, T.lo)


def vents(a, x, y, w, rows):
    """Punched horizontal vent slots: a dark slot with a lit lower lip, in 10px lengths."""
    xx = x
    while xx + 4 <= x + w:
        L = min(10, x + w - xx)
        for r in rows:
            rect(a, xx, y + r, L, 1, T.dk)
            rect(a, xx, y + r + 1, L, 1, T.hi)
            px(a, xx, y + r, T.lo)
            px(a, xx + L - 1, y + r, T.lo)
        xx += L + 3


def term_box(a, x, y, w, h):
    """A console window: dark metal rim, black glass."""
    rect(a, x, y, w, h, T.term)
    sunken(a, x - 1, y - 1, w + 2, h + 2, T.hi, T.dk)


def led(a, x, y, w, h, col):
    rect(a, x, y, w, h, col)
    if col not in (LED_OFF, LED_DARK):
        px(a, x, y, lerp(col, (255, 255, 255), 0.5))


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: a small black recessed key with a white glyph."""
    rect(a, x, y, 9, 9, (16, 18, 19) if pressed else (30, 34, 36))
    if pressed:
        sunken(a, x, y, 9, 9, (70, 76, 80), (4, 4, 4))
    else:
        raised(a, x, y, 9, 9, (88, 96, 100), (6, 7, 8))
    ink = T.ink if pressed else (T.silk if lit else T.silk_dim)
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        rect(a, X + 3, Y + 3, 3, 3, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 2, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 2, ink)
        rect(a, X + 2, Y + 5, 5, 1, lerp(ink, (30, 34, 36), 0.5))
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    """The clutterbar as a column of LED legends: letter, then its LED."""
    a = new(8, 43, (20, 24, 25))
    sunken(a, 0, 0, 8, 43, T.hi, T.dk)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 1, gy, T.silk if on else (120, 128, 130))
        led(a, 5, gy + 1, 2, 3, LED_GREEN if on else LED_OFF)
    return a


def main_titlebar(lit):
    a = new(275, 14)
    powder(a, 0, 0, 275, 14)
    rect(a, 0, 0, 275, 1, T.hi)
    rect(a, 0, 0, 1, 14, T.hi)
    rect(a, 274, 0, 1, 14, T.lo)
    rect(a, 0, 13, 275, 1, T.lo)
    lw = logo_w()
    lx = (275 - lw) // 2
    vents(a, 19, 0, lx - 8 - 19, [3, 6, 9])
    vx = lx + lw + 8
    vents(a, vx, 0, 238 - vx, [3, 6, 9])
    draw_logo(a, lx, 1, T.silk if lit else T.silk_dim)
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87)
    powder(a, 0, 0, 344, 87)
    for kind, x in (("options", 0), ("minimize", 9), ("close", 18)):
        b = new(9, 9)
        mini_button(b, 0, 0, kind, True)
        a[0:9, x:x + 9] = b
        mini_button(b, 0, 0, kind, True, pressed=True)
        a[9:18, x:x + 9] = b
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

LEGEND = [("SYST", LED_GREEN), ("RPS", LED_DARK), ("STAT", LED_GREEN), ("UTIL", LED_DARK),
          ("DUPLX", LED_DARK), ("SPEED", LED_DARK)]


def console_port(a, x, y):
    """The CONSOLE port (About spot): an RJ-45 jack in Cisco's light-blue console surround."""
    w, h = 18, 14
    rect(a, x - 2, y - 2, w + 4, h + 4, CABLE[1])
    raised(a, x - 2, y - 2, w + 4, h + 4, CABLE[0], CABLE[3])
    socket(a, x, y, w, h, notch=6)
    text_center(a, TINY, "CONSOLE", x + w // 2, y + h + 4, T.silk)


def socket(a, x, y, w, h, notch=None):
    """RJ-45 jack opening: a rectangle with the latch notch along the bottom, gold pins at the top."""
    notch = notch or max(4, w // 2 - 2)
    body_h = h - 3
    nx = x + (w - notch) // 2
    rect(a, x - 1, y - 1, w + 2, body_h + 2, T.dk)
    rect(a, nx - 1, y + body_h, notch + 2, 4, T.dk)
    rect(a, x, y, w, body_h, SOCKET)
    rect(a, nx, y + body_h - 1, notch, 4, SOCKET)
    rect(a, x - 1, y + body_h + 1, nx - x + 1, 1, T.hi)
    rect(a, nx + notch + 1, y + body_h + 1, x + w - nx - notch, 1, T.hi)
    rect(a, nx - 1, y + body_h + 4, notch + 2, 1, T.hi)
    # eight contacts
    cx = x + w // 2
    for i in range(8):
        gx = cx - 7 + 2 * i
        if x < gx < x + w - 1:
            rect(a, gx, y + 1, 1, 2, GOLD)
            px(a, gx, y + 3, lerp(GOLD, SOCKET, 0.6))


def make_main():
    a = new(275, 116)
    powder(a, 0, 0, 275, 116)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # left console window: prompt, time, analyzer
    term_box(a, 21, 19, 84, 43)
    draw_text(a, PROMPT, T.prompt, 23, 20, T.ink_dim)
    pw = text_w(PROMPT, T.prompt)
    rect(a, 23 + pw + 2, 20, 3, 5, T.ink_dim)   # the block cursor
    for yy in (30, 35):
        rect(a, 73, yy, 2, 2, T.ink)
    rect(a, 24, 60, 76, 1, T.ink_ghost)

    # right console window: title row, then kbps/kHz/mono/stereo row
    term_box(a, 109, 21, 159, 15)
    term_box(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, T.ink_dim)
    draw_text(a, TINY, "KHZ", 169, 44, T.ink_dim)

    # slider seats (covered by the sliders' frames)
    sunken(a, 106, 56, 70, 15)
    sunken(a, 176, 56, 40, 15)

    # seek channel, with a screw either side
    sunken(a, 15, 71, 250, 12, T.hi, T.dk)
    screw(a, 7, 77)
    screw(a, 269, 77)
    screw(a, 5, 20)

    # LED legend along the bottom
    x = 18
    for label, col in LEGEND:
        led(a, x, 110, 4, 2, col)
        x = draw_text(a, TINY, label, x + 6, 108, T.silk) + 6
    console_port(a, 248, 89)
    rect(a, 3, 114, 269, 1, T.lo)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36): the transport as a row of RJ-45 jacks
# ------------------------------------------------------------------------------------------


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


def transport_icon(a, kind, cx, cy, col):
    if kind == "previous":
        rect(a, cx - 5, cy - 3, 2, 7, col)
        tri_left(a, cx - 3, cy - 3, 7, col)
        tri_left(a, cx + 1, cy - 3, 7, col)
    elif kind == "play":
        tri_right(a, cx - 2, cy - 3, 7, col)
    elif kind == "pause":
        rect(a, cx - 3, cy - 3, 2, 7, col)
        rect(a, cx + 1, cy - 3, 2, 7, col)
    elif kind == "stop":
        rect(a, cx - 3, cy - 3, 6, 6, col)
    elif kind == "next":
        tri_right(a, cx - 5, cy - 3, 7, col)
        tri_right(a, cx - 1, cy - 3, 7, col)
        rect(a, cx + 3, cy - 3, 2, 7, col)
    elif kind == "eject":
        for r in range(3):
            rect(a, cx - r, cy - 3 + r, 2 * r + 1, 1, col)
        rect(a, cx - 2, cy + 1, 5, 1, col)


def jack(a, x, y, w, h, kind, pressed):
    """A transport button: an RJ-45 jack with its link (green) and activity (amber) LEDs."""
    sx, sw = x + 2, w - 4
    sh = h - 4
    socket(a, sx, y + 1, sw, sh, notch=8 if h > 16 else 6)
    body_h = sh - 3
    icon = LED_GREEN if pressed else (196, 204, 206)
    cy = y + 1 + 4 + (body_h - 4) // 2
    transport_icon(a, kind, sx + sw // 2, cy, icon)
    # LEDs in the jack's lower corners, beside the notch
    ly = y + 1 + body_h + 1
    led(a, sx, ly, 3, 2, LED_GREEN)
    led(a, sx + sw - 3, ly, 3, 2, LED_AMBER if pressed else LED_OFF)


CB = [("previous", 0, 23, 18, 16, 88), ("play", 23, 23, 18, 39, 88), ("pause", 46, 23, 18, 62, 88),
      ("stop", 69, 23, 18, 85, 88), ("next", 92, 22, 18, 108, 88)]


def make_cbuttons(main):
    a = new(136, 36)
    for kind, x, w, h, dx, dy in CB:
        for pressed, y in ((False, 0), (True, 18)):
            a[y:y + h, x:x + w] = main[dy:dy + h, dx:dx + w]
            jack(a, x, y, w, h, kind, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        a[y:y + 16, 114:136] = main[89:105, 136:158]
        jack(a, 114, y, 22, 16, "eject", pressed)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85): mode keys with LEDs
# ------------------------------------------------------------------------------------------


def mode_key(a, x, y, w, h, label, on, pressed, layout="above"):
    """A small charcoal key with an LED legend: LED above the label (15 tall) or left of it."""
    face = shade(KEY, 0.7) if pressed else KEY
    rect(a, x + 1, y + 1, w - 2, h - 2, face)
    if pressed:
        sunken(a, x, y, w, h, (90, 98, 100), (4, 5, 6))
    else:
        raised(a, x + 1, y + 1, w - 2, h - 2, (78, 86, 88), (12, 14, 15))
        rect(a, x, y + h - 1, w, 1, T.dk)
        rect(a, x + w - 1, y, 1, h, T.dk)
        rect(a, x, y, w, 1, T.lo)
        rect(a, x, y, 1, h, T.lo)
    o = 1 if pressed else 0
    ink = T.silk if on else (176, 184, 186)
    lc = LED_GREEN if on else LED_OFF
    tw = text_w(TINY, label)
    if layout == "above":
        led(a, x + (w - 6) // 2 + o, y + 3 + o, 6, 2, lc)
        draw_text(a, TINY, label, x + (w - tw) // 2 + o, y + 7 + o, ink)
    else:
        led(a, x + 3 + o, y + h // 2 - 1 + o, 3, 2, lc)
        draw_text(a, TINY, label, x + 7 + (w - 9 - tw) // 2 + o, y + (h - 5) // 2 + o, ink)


def make_shufrep(main):
    a = new(92, 85)
    powder(a, 0, 0, 92, 85)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = main[89:104, 210:238]
        a[y:y + 15, 28:75] = main[89:104, 164:211]
        mode_key(a, 0, y, 28, 15, "REPEAT", on, pressed)
        mode_key(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        src = 219 if label == "EQ" else 242
        for on, y in ((False, 61), (True, 73)):
            a[y:y + 12, x:x + 23] = main[58:70, src:src + 23]
            mode_key(a, x, y, 23, 12, label, on, pressed, layout="left")
    return a


# ------------------------------------------------------------------------------------------
# monoster, playpaus, numbers, nums_ex, text
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T.term)
    for y, on in ((0, True), (12, False)):
        col = T.ink if on else T.ink_ghost
        text_center(a, TINY, "STEREO", 14, y + 4, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 4, col)
    return a


def make_playpaus():
    a = new(48, 9, T.term)
    tri_right(a, 2, 1, 7, T.ink)
    rect(a, 9 + 2, 1, 2, 7, T.ink)
    rect(a, 9 + 5, 1, 2, 7, T.ink)
    rect(a, 18 + 2, 2, 5, 5, T.ink)
    rect(a, 36, 0, 3, 9, T.term)
    rect(a, 39 + 1, 3, 1, 3, T.ink)
    return a


_DIGITS = {}


def mono_glyph(ch):
    """A Courier digit (Nimbus Mono PS Bold, URW's Courier) as a 0..1 coverage map, 7x11."""
    if ch in _DIGITS:
        return _DIGITS[ch]
    f = ImageFont.truetype("/usr/share/fonts/urw-base35/NimbusMonoPS-Bold.otf", 160)
    im = Image.new("L", (200, 220), 0)
    ImageDraw.Draw(im).text((20, 10), ch, fill=255, font=f)
    if ch == "-":
        ref = Image.new("L", (200, 220), 0)
        ImageDraw.Draw(ref).text((20, 10), "0", fill=255, font=f)
        x0, y0, x1, y1 = ref.getbbox()
        bx0, by0, bx1, by1 = im.getbbox()
        crop = im.crop((x0, y0, x1, y1))
    else:
        crop = im.crop(im.getbbox())
    m = np.array(crop.resize((7, 11), Image.LANCZOS)).astype(np.float32) / 255
    m = np.clip((m - 0.12) / 0.6, 0, 1)
    _DIGITS[ch] = m
    return m


def draw_glyph(a, m, x, y, ink, bg):
    h, w = m.shape
    for r in range(h):
        for c in range(w):
            t = float(m[r, c])
            if t > 0.02:
                a[y + r, x + c] = lerp(bg, ink, t)


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T.term)
    for n in range(10):
        draw_glyph(a, mono_glyph(str(n)), 9 * n + 1, 1, T.ink, T.term)
    if ex:
        draw_glyph(a, mono_glyph("-"), 99 + 1, 1, T.ink, T.term)
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, T.term)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key, col * 5, row * 6, T.ink)
    return a


# ------------------------------------------------------------------------------------------
# posbar (the console cable and its plug), volume / balance (LED meters)
# ------------------------------------------------------------------------------------------


def cable(a, x, y, w):
    """The light-blue console cable lying in the channel, 4 rows from y."""
    for r, col in enumerate(CABLE):
        rect(a, x, y + r, w, 1, col)
    for xx in range(x + 3, x + w, 9):
        px(a, xx, y + 1, lerp(CABLE[1], CABLE[0], 0.6))


def plug(a, x, y, pressed):
    """29x10 thumb: the cable's RJ-45 plug - blue boot, clear body, gold contacts at the tip."""
    boot = [shade(c, 1.12 if pressed else 1.0) for c in CABLE]
    # boot (strain relief), tapering into the cable
    for c in range(11):
        r0, r1 = (2, 7) if c < 3 else (1, 8)
        for r in range(r0, r1 + 1):
            px(a, x + c, y + r, ramp(boot, (r - r0) / (r1 - r0)))
    for gx in (5, 7, 9):
        rect(a, x + gx, y + 2, 1, 6, shade(boot[2], 0.8))
    # clear plastic body
    body = (222, 232, 236) if pressed else (196, 208, 214)
    rect(a, x + 11, y + 1, 18, 8, body)
    rect(a, x + 11, y + 1, 18, 1, (240, 246, 248))
    rect(a, x + 11, y + 8, 18, 1, (120, 134, 142))
    rect(a, x + 28, y + 1, 1, 8, (120, 134, 142))
    # wires seen through it, contacts at the tip, the latch on top
    for i, c in enumerate([(240, 140, 40), (60, 140, 220), (90, 180, 90), (150, 110, 80)]):
        rect(a, x + 12, y + 3 + i, 9, 1, lerp(c, body, 0.45))
    for gy in range(2, 8):
        rect(a, x + 22, y + gy, 5, 1, GOLD if gy % 2 == 0 else lerp(GOLD, body, 0.5))
    rect(a, x + 13, y, 10, 1, (150, 162, 168))


def make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    rect(a, 0, 1, 248, 8, T.dk)
    rect(a, 0, 1, 248, 1, shade(T.dk, 0.7))
    cable(a, 0, 3, 248)
    for xt, pressed in ((248, False), (278, True)):
        a[0:10, xt:xt + 29] = a[0:10, 100:129]
        plug(a, xt, 0, pressed)
    return a


def slider_thumb(a, x, y, pressed):
    """14x11: a brushed steel slide with a dark grip line."""
    top, bot = ((236, 242, 244), (170, 178, 182)) if pressed else ((206, 212, 216), (130, 138, 142))
    for r in range(11):
        rect(a, x, y + r, 14, 1, lerp(top, bot, r / 10))
    raised(a, x, y, 14, 11, (250, 252, 252), (52, 56, 60))
    rect(a, x + 6, y + 2, 2, 7, (40, 44, 48))
    if pressed:
        rect(a, x + 6, y + 2, 2, 7, shade(T.ink, 0.8))


def meter_plate(a, x, y, w):
    rect(a, x, y + 2, w, 9, (14, 16, 17))
    sunken(a, x, y + 2, w, 9, T.dk, T.hi)


def make_volume(main):
    a = new(68, 433)
    powder(a, 0, 0, 68, 433)
    nseg = 16
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = main[56:71, 106:174]
        meter_plate(a, 0, y, 68)
        level = (i + 1) / 28
        lit = round(level * nseg)
        for k in range(nseg):
            sx = 3 + k * 4 - (0 if k < 8 else 0)
            col = LED_GREEN if k < 12 else LED_AMBER
            if k < lit:
                rect(a, sx, y + 5, 3, 3, col)
                px(a, sx, y + 5, lerp(col, (255, 255, 255), 0.45))
            else:
                rect(a, sx, y + 5, 3, 3, (30, 38, 32) if k < 12 else (44, 34, 16))
    for x, pressed in ((0, True), (15, False)):
        slider_thumb(a, x, 422, pressed)
    return a


def make_balance(main):
    a = new(68, 433)
    powder(a, 0, 0, 68, 433)
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = main[56:71, 176:214]
        meter_plate(a, 9, y, 38)
        reach = round(i / 27 * 4)
        for k in range(-4, 5):
            sx = 9 + 17 + k * 4
            d = abs(k)
            on = d == 0 or d <= reach
            col = LED_GREEN if d == 0 else LED_AMBER
            if on:
                rect(a, sx, y + 5, 3, 3, col)
                px(a, sx, y + 5, lerp(col, (255, 255, 255), 0.45))
            else:
                rect(a, sx, y + 5, 3, 3, (44, 34, 16))
    for x, pressed in ((0, True), (15, False)):
        slider_thumb(a, x, 422, pressed)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def silk_titlebar(w, title, lit, close_x=None, h=14):
    a = new(w, h)
    powder(a, 0, 0, w, h)
    rect(a, 0, 0, w, 1, T.hi)
    rect(a, 0, 0, 1, h, T.hi)
    rect(a, w - 1, 0, 1, h, T.lo)
    tw = text_w(FONT5, title)
    tx = (w - tw) // 2
    end = (close_x - 4) if close_x else w - 6
    vents(a, 6, 0, tx - 8 - 6, [3, 6, 9])
    vents(a, tx + tw + 8, 0, end - (tx + tw + 8), [3, 6, 9])
    draw_text(a, FONT5, title, tx, 4, T.silk if lit else T.silk_dim, shadow=T.lo)
    if close_x:
        mini_button(a, close_x, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    """14x63: a vertical LED bar graph whose lit column rises with the value (n of 0..27)."""
    rect(a, x, y, 14, 63, (14, 16, 17))
    sunken(a, x, y, 14, 63, T.dk, T.hi)
    v = n / 27
    nseg = 19
    lit = round(v * nseg)
    for k in range(nseg):
        sy = y + 59 - k * 3 - 2
        col = LED_GREEN if k < 13 else LED_AMBER
        if k < lit:
            rect(a, x + 4, sy, 6, 2, col)
            px(a, x + 4, sy, lerp(col, (255, 255, 255), 0.45))
        else:
            rect(a, x + 4, sy, 6, 2, (30, 38, 32) if k < 13 else (44, 34, 16))
    px(a, x + 1, y + 31, T.silk_dim)
    px(a, x + 12, y + 31, T.silk_dim)


def eq_thumb(a, x, y, pressed):
    top, bot = ((236, 242, 244), (170, 178, 182)) if pressed else ((206, 212, 216), (130, 138, 142))
    for r in range(11):
        rect(a, x, y + r, 11, 1, lerp(top, bot, r / 10))
    raised(a, x, y, 11, 11, (250, 252, 252), (52, 56, 60))
    rect(a, x + 2, y + 5, 7, 1, (40, 44, 48))
    if pressed:
        rect(a, x + 2, y + 5, 7, 1, shade(T.ink, 0.8))


def make_eqmain():
    a = new(275, 315)
    powder(a, 0, 0, 275, 315)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = silk_titlebar(275, "EQUALIZER", True, 264)
    term_box(a, 86, 17, 113, 19)
    rect(a, 16, 36, 245, 68, shade(T.metal, 0.9))
    sunken(a, 16, 36, 245, 68)
    for lbl, yy in (("+12", 41), ("0", 66), ("-12", 92)):
        text_center(a, TINY, lbl, 58, yy, T.silk)
        rect(a, 42, yy + 2, 3, 1, T.silk_dim)
        rect(a, 71, yy + 2, 3, 1, T.silk_dim)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    text_center(a, TINY, "PREAMP", 28, 106, T.silk)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, T.silk)
    screw(a, 6, 108)
    screw(a, 268, 108)
    rect(a, 3, 113, 269, 1, T.lo)

    mini_button(a, 0, 125, "close", True, pressed=True)
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        dx = 14 if label == "ON" else 40
        a[119:131, x:x + w] = a[18:30, dx:dx + w]
        mode_key(a, x, 119, w, 12, label, on, pressed, layout="left")
    a[134:148, :] = silk_titlebar(275, "EQUALIZER", True, 264)
    a[149:163, :] = silk_titlebar(275, "EQUALIZER", False, 264)
    eq_thumb(a, 0, 164, False)
    eq_thumb(a, 0, 176, True)
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        a[y:y + 12, 224:268] = a[18:30, 217:261]
        mode_key(a, 224, y, 44, 12, "PRESETS", False, pressed, layout="none")
    # PRESETS has no LED: paint the face over it and centre the label
    for y, pressed in ((164, False), (176, True)):
        face = shade(KEY, 0.7) if pressed else KEY
        rect(a, 226, y + 2, 40, 8, face)
        o = 1 if pressed else 0
        text_center(a, TINY, "PRESETS", 246 + o, y + 3 + o, T.ink if pressed else T.silk)
    # graph: console black, a dotted grid
    rect(a, 0, 294, 113, 19, T.term)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, T.ink_ghost)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, T.ink_ghost)
    for r in range(19):
        px(a, 115, 294 + r, ramp([T.ink_hi, T.ink, T.ink, T.ink_dim], r / 18))
    for x in range(113):
        px(a, x, 314, T.ink_dim if x % 3 != 2 else T.term)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109)
# ------------------------------------------------------------------------------------------


def bar20(w):
    a = new(w, 20)
    powder(a, 0, 0, w, 20)
    rect(a, 0, 0, w, 1, T.hi)
    return a


BAR_VENTS = [4, 7, 10]


def make_pledit():
    a = new(280, 186)
    powder(a, 0, 0, 280, 186)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25)
        vents(t, 0, 0, 25, BAR_VENTS)
        rect(t, 0, 19, 25, 1, T.lo)
        a[y:y + 20, 127:152] = t
        t = bar20(25)
        rect(t, 0, 0, 1, 20, T.hi)
        screw(t, 6, 8)
        vents(t, 12, 0, 13, BAR_VENTS)
        rect(t, 11, 19, 14, 1, T.lo)
        a[y:y + 20, 0:25] = t
        t = bar20(100)
        text_center(t, FONT5, "PLAYLIST", 50, 6, T.silk if lit else T.silk_dim, shadow=T.lo)
        tw = text_w(FONT5, "PLAYLIST")
        vents(t, 0, 0, 50 - tw // 2 - 6, BAR_VENTS)
        vents(t, 50 + tw // 2 + 6, 0, 100 - (50 + tw // 2 + 6), BAR_VENTS)
        rect(t, 0, 19, 100, 1, T.lo)
        a[y:y + 20, 26:126] = t
        t = bar20(25)
        rect(t, 24, 0, 1, 20, T.lo)
        vents(t, 0, 0, 11, BAR_VENTS)
        mini_button(t, 14, 3, "close", lit)
        rect(t, 0, 19, 6, 1, T.lo)
        rect(t, 9, 14, 10, 6, (20, 24, 25))
        rect(t, 9, 14, 10, 1, T.dk)
        a[y:y + 20, 153:178] = t

    t = new(12, 29)
    powder(t, 0, 0, 12, 29)
    rect(t, 0, 0, 1, 29, T.hi)
    rect(t, 11, 0, 1, 29, T.dk)
    rect(t, 4, 0, 1, 29, T.lo)
    a[42:71, 0:12] = t
    t = new(20, 29)
    powder(t, 0, 0, 20, 29)
    rect(t, 0, 0, 1, 29, T.dk)
    rect(t, 19, 0, 1, 29, T.lo)
    rect(t, 4, 0, 10, 29, (20, 24, 25))
    rect(t, 4, 0, 1, 29, T.dk)
    rect(t, 13, 0, 1, 29, T.hi)
    rect(t, 8, 0, 2, 29, (30, 34, 36))
    a[42:71, 31:51] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        top, bot = ((236, 242, 244), (170, 178, 182)) if sel else ((206, 212, 216), (130, 138, 142))
        for r in range(18):
            rect(a, x, 53 + r, 8, 1, lerp(top, bot, r / 17))
        raised(a, x, 53, 8, 18, (250, 252, 252), (52, 56, 60))
        for gy in (59, 61, 63):
            rect(a, x + 2, gy, 4, 1, (60, 66, 70) if not sel else shade(T.ink, 0.7))

    def bottom_base(w):
        t = new(w, 38)
        powder(t, 0, 0, w, 38)
        rect(t, 0, 0, w, 1, T.hi)
        rect(t, 0, 37, w, 1, T.lo)
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, T.hi)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        sub = t[8:26, bx:bx + 22].copy()
        mode_key(sub, 0, 0, 22, 18, lbl, False, False, layout="none")
        rect(sub, 2, 2, 18, 14, KEY)
        text_center(sub, TINY, lbl, 11, 7, T.silk)
        t[8:26, bx:bx + 22] = sub
    draw_text(t, TINY, T.series, 14, 29, T.silk)
    screw(t, 6, 31)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, T.lo)
    term_box(t, 6, 9, 56, 8)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        rect(t, bx, 22, 10, 10, KEY)
        raised(t, bx, 22, 10, 10, (78, 86, 88), (8, 9, 10))
        mini_transport_icon(t, kind, bx, 22, T.silk)
    term_box(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, T.ink_dim)
    rect(t, 84, 22 + 5, 1, 1, T.ink_dim)
    sub = t[8:26, 106:128].copy()
    rect(sub, 0, 0, 22, 18, KEY)
    raised(sub, 0, 0, 22, 18, (78, 86, 88), (8, 9, 10))
    text_center(sub, TINY, "LIST", 11, 7, T.silk)
    t[8:26, 106:128] = sub
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 34 - 3 * j
            px(t, gx, gy, T.hi)
            px(t, gx + 1, gy + 1, T.dk)
    screw(t, 140, 14)
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


def make_gen():
    a = new(194, 109)
    powder(a, 0, 0, 194, 109)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn, flat=False):
            t = bar20(25)
            if flat:
                rect(t, 0, 1, 25, 19, T.metal)
            fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 1, 20, T.hi)
            screw(t, 6, 8)
            vents(t, 12, 0, 13, BAR_VENTS)

        def left_end(t):
            vents(t, 0, 0, 17, BAR_VENTS)

        def centre(t):
            pass

        def right_end(t):
            vents(t, 8, 0, 17, BAR_VENTS)

        def fill(t):
            vents(t, 0, 0, 25, BAR_VENTS)

        def right(t):
            vents(t, 0, 0, 11, BAR_VENTS)
            mini_button(t, 14, 3, "close", lit)
            rect(t, 24, 0, 1, 20, T.lo)

        piece(0, left)
        piece(26, left_end, flat=True)
        piece(52, centre, flat=True)
        piece(78, right_end, flat=True)
        piece(104, fill)
        piece(130, right)

    def bottom(w, grip, left_edge):
        t = new(w, 14)
        powder(t, 0, 0, w, 14)
        rect(t, 0, 13, w, 1, T.lo)
        if left_edge:
            rect(t, 0, 0, 1, 14, T.hi)
        else:
            rect(t, w - 1, 0, 1, 14, T.lo)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 10 - 3 * j
                    px(t, gx, gy, T.hi)
                    px(t, gx + 1, gy + 1, T.dk)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        powder(t, 0, 0, w, h)
        if outer_left:
            rect(t, 0, 0, 1, h, T.hi)
            rect(t, 4, 0, 1, h, T.lo)
        else:
            rect(t, w - 1, 0, 1, h, T.lo)
            rect(t, w - 5, 0, 1, h, T.lo)
        a[42:42 + h, x:x + w] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            rect(a, x, y, w, 7, T.metal)
            draw_text(a, FONT5, c, x, y + 1, T.silk if lit else T.silk_dim)
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp, text files
# ------------------------------------------------------------------------------------------


def genex_colours():
    return [
        T.term, T.ink, T.metal, T.silk, T.silk, T.lo, T.sel, shade(T.metal, 0.75), T.silk,
        T.hi, T.dk, T.lo, T.metal, shade(T.metal, 0.7), (196, 204, 208), shade(T.metal, 0.6),
        T.ink, T.dk,
    ]


def make_genex():
    a = new(256, 64)
    powder(a, 0, 1, 256, 63)
    rect(a, 0, 0, 256, 1, T.metal)
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    for y, pressed in ((1, False), (16, True)):
        rect(a, 0, y, 47, 15, shade(KEY, 0.7) if pressed else KEY)
        (sunken if pressed else raised)(a, 0, y, 47, 15, (78, 86, 88), (8, 9, 10))
    return a


def viscolor():
    spec = [(lerp(T.ink_hi, T.ink, i / 6) if i < 6 else lerp(T.ink, T.ink_dim, (i - 6) / 9),
             f"spectrum {i + 1}") for i in range(16)]
    osc = [(lerp(T.ink_hi, T.ink_dim, i / 4), f"oscilloscope {i + 1}") for i in range(5)]
    return [(T.term, "background"), (T.ink_ghost, "dots")] + spec + osc + [(T.ink_hi, "peaks")]


def hexc(c):
    return "#%02X%02X%02X" % tuple(c)


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={hexc(T.ink)}\nCurrent={hexc(T.ink_hi)}\nNormalBG={hexc(T.term)}\n"
                f"SelectedBG={hexc(T.sel)}\nMbBG={hexc(T.term)}\nMbFG={hexc(T.ink)}\nFont=Courier New\n")
    name = T.wsz[:-4]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{name} — a skin in the style of Cisco classic hardware.\n"
            "Cisco logo © Cisco Systems, Inc.\n\n"
            "Generated procedurally by gen_skin.py.\n"
        )


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
    with zipfile.ZipFile(os.path.join(HERE, T.wsz), "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(OUT, n), "rb") as fh:
                z.writestr(info, fh.read())
    # genex.bmp completed for real Winamp and WACUP: all 24 colours, readable text, and the
    # standard 112x59 button and scrollbar layout (skins/genex_wacup.py).
    genex_wacup.process(os.path.join(HERE, T.wsz))
    return names


# ------------------------------------------------------------------------------------------
# Preview
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


def tt_font(size, mono=False):
    paths = (["/usr/share/fonts/liberation-mono-fonts/LiberationMono-Regular.ttf"] if mono else []) + \
        ["/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf", "DejaVuSans.ttf"]
    for p in paths:
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
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    box = img.crop((111, 22, 265, 36))
    ImageDraw.Draw(box).text((0, 7), state["title"], fill=T.ink, font=tt_font(11), anchor="lm")
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
    lx, lw = 12, w - 32
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=T.term)
    font = tt_font(10, mono=True)
    for i, (txt, dur) in enumerate(rows):
        y = 22 + i * 13
        if y + 13 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 12), fill=T.sel)
        col = T.ink_hi if i == 1 else T.ink
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
    col = np.stack([30 + 60 * arr[..., 0], 60 + 90 * arr[..., 0], 80 + 100 * arr[..., 0]], -1)
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("Fa0/1 - Link Up (Remix)", "4:12"), ("Spanning Tree - Blocking", "3:47"),
            ("Native VLAN - Trunk Line", "5:03"), ("Half Duplex - Collisions", "2:58"),
            ("Console 9600 - 8N1", "6:21"), ("Rollover - Light Blue", "3:33"),
            ("Running-Config - Write Mem", "4:40"), ("IOS 12.0 - Reload", "3:09"),
            ("Gi0/1 - Uplink", "5:51"), ("Show Run - Interfaces", "4:05"),
            ("RPS - Redundant Power", "3:22"), ("Telnet - Line VTY 0 4", "4:44"),
            ("Enable Secret - Level 15", "3:58")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title="Spanning Tree - Blocking (Port Fa0/12)", bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="%LINK-3-UPDOWN: Interface Fa0/1", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
    out.save(os.path.join(HERE, f"preview-{T.name}.png"))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--list"]:
        for k, v in THEMES.items():
            print(f"{k:12s} {v.wsz}")
        sys.exit(0)
    for theme in (args or list(THEMES)):
        use_theme(theme)
        names = build()
        preview()
        print(f"{T.wsz}: {', '.join(names)}")
