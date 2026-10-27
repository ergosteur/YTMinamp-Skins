#!/usr/bin/python3
"""Panasonic RX-DS660: a classic Winamp 2.x skin in the style of an early-90s portable stereo
component CD system (boombox), after photos of the user's own unit in source/.

Procedural, based on skins/ember/gen_skin.py (whose sheet layouts it keeps). Everything is drawn
here: matte charcoal plastic with grey silkscreen section lines, a pale olive LCD with dark
seven-segment digits (9x13 cells, thin bars, 2px verticals, a gap at every joint, unlit segments
as a darker tint of the glass), the brushed-silver keypad with black keys, satin black transport
keys, the MOTORIZED VOLUME knob with its red pointer, the graphic equalizer's black slots and
red-marked caps, and the gold XBS LEVEL wedge. The Panasonic wordmark is lettering rendered from
Liberation Sans Bold; "RX-DS660" from Noto Sans ExtraCondensed Bold. Private use only.

    /usr/bin/python3 -I gen_skin.py [rx-ds660 ...]   (no argument builds all)
    /usr/bin/python3 -I gen_skin.py --list

Per theme: the bitmaps and text files in out/<theme>/, zipped flat into <Name>.wsz beside this
file, and preview-<theme>.png (the windows assembled from the sprites the way the app does, 2x).
"""

import math
import os
import sys
import zipfile
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py, which finishes each .wsz
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.join(HERE, "out")
OUT = None
T = None

FONT_WORDMARK = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf"
FONT_MODEL = "/usr/share/fonts/google-noto/NotoSans-ExtraCondensedBold.ttf"
FONT_PREVIEW = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"

THEMES = {
    # Panasonic RX-DS660 (c. 1991-92): portable stereo component CD system with detachable
    # speakers, double-sided auto-reverse cassette, digital synthesizer tuner, XBS and a
    # five-band graphic equalizer, motorized volume, remote control.
    "rx-ds660": SimpleNamespace(
        name="rx-ds660", title="Panasonic RX-DS660", wsz="Panasonic-RX-DS660.wsz",
        subject="the Panasonic RX-DS660 portable stereo component CD system",
        owner="Panasonic Holdings Corporation",
    ),
}

SEP = (255, 0, 255)      # gen.bmp letter separators (never shown)

# ------------------------------------------------------------------------------------------
# Palette (sampled from the photos and evened out)
# ------------------------------------------------------------------------------------------

BODY = (44, 46, 49)          # matte charcoal plastic
BODY_HI = (76, 78, 82)
BODY_LO = (14, 15, 16)
RECESS = (33, 34, 37)        # recessed panels (transport tray, slider bay)
BEZEL = (20, 21, 23)         # the display window's black frame
SLOT = (10, 10, 11)          # slider channels
SILK = (170, 172, 172)       # grey silkscreen
SILK_DIM = (112, 114, 116)
SILK_OFF = (92, 94, 97)      # unfocused titlebars
GOLD = (222, 170, 98)        # REMOTE CONTROL / DIGITAL / XBS print
GOLD_DIM = (128, 102, 66)
RED = (255, 64, 54)          # lit LEDs
RED_HI = (255, 170, 150)
RED_OFF = (78, 34, 32)       # unlit LEDs
RED_MARK = (214, 46, 40)     # the red lines on slider caps and the knob's pointer
SILVER_TOP = (196, 194, 192)
SILVER_BOT = (150, 148, 148)
SILVER_HI = (232, 230, 228)
SILVER_LO = (86, 85, 86)
SILK_SILVER = (58, 58, 60)   # print on the silver keypad
LCD = (166, 171, 146)        # the pale olive glass
LCD_SHADE = (138, 143, 119)  # the glass's inner shadow
LCD_INK = (30, 34, 28)       # segments
LCD_GHOST = (153, 158, 133)  # unlit segments: a darker tint of the glass
LCD_DIM = (96, 102, 82)      # fixed legends in the glass


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def hexc(c):
    return "#%02X%02X%02X" % c


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------

_rng = np.random.default_rng(660)


def use_theme(name):
    global T, OUT, _rng
    T = THEMES[name]
    OUT = os.path.join(OUT_ROOT, name)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT_ROOT, "scratch"), exist_ok=True)
    _rng = np.random.default_rng(660)


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


def raised(a, x, y, w, h, hi=BODY_HI, lo=BODY_LO):
    rect(a, x, y, w, 1, hi)
    rect(a, x, y, 1, h, hi)
    rect(a, x, y + h - 1, w, 1, lo)
    rect(a, x + w - 1, y, 1, h, lo)


def sunken(a, x, y, w, h, hi=BODY_HI, lo=BODY_LO):
    raised(a, x, y, w, h, lo, hi)


def matte(a, x, y, w, h, col=BODY, amp=1.4):
    """Matte plastic: flat colour with a fine grain."""
    rect(a, x, y, w, h, col)
    n = _rng.normal(0, amp, (h, w))
    a[y:y + h, x:x + w] += np.round(n).astype(np.int32)[:, :, None]


def brushed(a, x, y, w, h, top, bot, amp=4.0):
    """Brushed silver: a vertical gradient with horizontally smeared grain (wraps)."""
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(top, bot, r / max(1, h - 1)))
    n = _rng.normal(0, 1, (h, w))
    acc = np.zeros_like(n)
    for d in range(-6, 7):
        acc += np.roll(n, d, axis=1)
    acc /= 3.6
    a[y:y + h, x:x + w] += np.round(acc * amp).astype(np.int32)[:, :, None]


def paint(a, x, y, m, col, alpha=1.0):
    """Blend colour col through coverage mask m (h x w floats 0..1) at x, y (clipped)."""
    h, w = m.shape
    H, W = a.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    mm = m[y0 - y:y1 - y, x0 - x:x1 - x][:, :, None] * alpha
    reg = a[y0:y1, x0:x1].astype(np.float32)
    a[y0:y1, x0:x1] = np.round(reg * (1 - mm) + np.array(col, np.float32) * mm).astype(np.int32)


SS = 4


def disc_m(w, h, cx, cy, r):
    """Anti-aliased disc coverage (centre and radius in pixels)."""
    ys, xs = np.mgrid[0:h * SS, 0:w * SS]
    d = np.hypot((xs + 0.5) / SS - cx, (ys + 0.5) / SS - cy)
    m = (d <= r).astype(np.float32)
    return m.reshape(h, SS, w, SS).mean(axis=(1, 3))


def line_m(w, h, pts, width):
    img = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(img).line([(x * SS, y * SS) for x, y in pts], fill=255, width=max(1, int(width * SS)))
    return np.asarray(img.resize((w, h), Image.BOX), dtype=np.float32) / 255


def ttf_mask(s, path, size, threshold=None):
    """Text rendered by a system font at 1x (hinted): a coverage mask cropped to its ink."""
    f = ImageFont.truetype(path, size)
    l, t, r, b = f.getbbox(s)
    img = Image.new("L", (r - l + 2, b - t + 2), 0)
    ImageDraw.Draw(img).text((-l + 1, -t + 1), s, fill=255, font=f)
    m = np.asarray(img, dtype=np.float32) / 255
    ys, xs = np.nonzero(m > 0.05)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    if threshold is not None:
        m = (m >= threshold).astype(np.float32)
    return m


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


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

# 3x5 caps for the silkscreen.
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
    "M": G("#...#", "##.##", "#.#.#", "#...#", "#...#"),
    "N": G("#..#", "##.#", "#.##", "#..#", "#..#"),
    "O": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "P": G("##.", "#.#", "##.", "#..", "#.."),
    "Q": G(".#.", "#.#", "#.#", "##.", ".##"),
    "R": G("##.", "#.#", "##.", "#.#", "#.#"),
    "S": G(".##", "#..", ".#.", "..#", "##."),
    "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#.#", "#.#", "#.#", "#.#", "###"),
    "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#...#", "#...#", "#.#.#", "##.##", "#...#"),
    "X": G("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": G("###", "..#", ".#.", "#..", "###"),
    " ": G("..", "..", "..", "..", ".."),
    "<": G("..#", ".##", "###", ".##", "..#"),
    ">": G("#..", "##.", "###", "##.", "#.."),
}
for _c in "0123456789+-./":
    TINY[_c] = FONT5[_c]
TINY["1"] = G(".#", "##", ".#", ".#", ".#")
TINY["k"] = G("#..", "#.#", "##.", "#.#", "#.#")


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
# Shared pieces
# ------------------------------------------------------------------------------------------


def section_line(a, x0, x1, y, label, col, ends="down", font=None, label_col=None):
    """Silkscreen section line (x0..x1 inclusive) at row y with a centred label (5 rows,
    y-2..y+2) and short ticks at the ends: 'down' for headers over keys, 'up' for footers."""
    font = font or TINY
    tw = text_w(font, label) if label else 0
    cx = (x0 + x1 + 1) // 2
    lx = cx - tw // 2
    if label:
        rect(a, x0, y, lx - 3 - x0, 1, col)
        rect(a, lx + tw + 3, y, x1 - (lx + tw + 3) + 1, 1, col)
        draw_text(a, font, label, lx, y - 2, label_col or col)
    else:
        rect(a, x0, y, x1 - x0 + 1, 1, col)
    if ends:
        dy = 1 if ends == "down" else -2
        rect(a, x0, y + dy, 1, 2, col)
        rect(a, x1, y + dy, 1, 2, col)


def key_face(a, x, y, w, h, pressed, satin=False):
    """A black rectangular key: soft top highlight, dark edges; pressed sits lower and darker."""
    if pressed:
        top, bot = (24, 25, 27), (34, 35, 38)
    else:
        top, bot = ((62, 63, 67), (28, 29, 31)) if satin else ((54, 55, 59), (26, 27, 29))
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(top, bot, r / max(1, h - 1)))
    if pressed:
        rect(a, x, y, w, 1, (6, 6, 7))
        rect(a, x, y, 1, h, (6, 6, 7))
        rect(a, x + 1, y + 1, w - 2, 1, (14, 14, 15))
        rect(a, x + w - 1, y, 1, h, (52, 53, 57))
        rect(a, x, y + h - 1, w, 1, (52, 53, 57))
    else:
        rect(a, x, y, w, 1, (96, 97, 102) if satin else (84, 85, 90))
        rect(a, x, y, 1, h, (74, 75, 80))
        rect(a, x + w - 1, y, 1, h, (8, 8, 9))
        rect(a, x, y + h - 1, w, 1, (8, 8, 9))
        rect(a, x + 1, y + h - 2, w - 2, 1, (18, 18, 20))


def led(a, x, y, on, w=3, h=2):
    rect(a, x, y, w, h, RED if on else RED_OFF)
    if on:
        rect(a, x, y, w, 1, RED_HI)
    rect(a, x - 1, y - 1, w + 2, 1, BODY_LO)


def glass(a, x, y, w, h):
    """The LCD glass in its black frame: a 1px shade along the top and left."""
    rect(a, x - 2, y - 2, w + 4, h + 4, BEZEL)
    rect(a, x - 2, y + h + 1, w + 4, 1, (58, 60, 64))
    rect(a, x + w + 1, y - 2, 1, h + 4, (58, 60, 64))
    rect(a, x, y, w, h, LCD)
    rect(a, x, y, w, 1, LCD_SHADE)
    rect(a, x, y, 1, h, LCD_SHADE)


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: a small black key with a grey glyph."""
    key_face(a, x, y, 9, 9, pressed, satin=True)
    ink = (236, 236, 236) if pressed else ((196, 198, 200) if lit else (110, 112, 115))
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        rect(a, X + 3, Y + 3, 3, 3, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 1, ink)
        rect(a, X + 2, Y + 5, 5, 1, lerp(ink, (40, 40, 40), 0.5))
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


def wordmark(a, x, y, lit):
    """The Panasonic wordmark, lettering rendered from Liberation Sans Bold, in the grey print."""
    m = ttf_mask("Panasonic", FONT_WORDMARK, 11)
    paint(a, x, y, m, (198, 200, 200) if lit else (104, 106, 108))
    return m.shape[1]


def model_print(a, x, y, col, size=10):
    m = ttf_mask("RX-DS660", FONT_MODEL, size)
    paint(a, x, y, m, col)
    return m.shape


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    """The silver keypad in miniature: a brushed strip with five little black keys."""
    a = new(8, 43, BODY)
    brushed(a, 0, 0, 8, 43, SILVER_TOP, SILVER_BOT, 3)
    raised(a, 0, 0, 8, 43, SILVER_HI, SILVER_LO)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        key_face(a, 1, y, 6, h, on)
        gy = y + (h - 5) // 2 + (1 if on else 0)
        draw_text(a, TINY, letter, 2 + (1 if on else 0), gy, RED if on else (176, 178, 180))
    return a


def main_titlebar(lit):
    a = new(275, 14, BODY)
    matte(a, 0, 0, 275, 14, BODY)
    rect(a, 0, 0, 275, 1, BODY_HI)
    rect(a, 0, 0, 1, 14, BODY_HI)
    rect(a, 274, 0, 1, 14, BODY_LO)
    ww = wordmark(a, 19, 3, lit)
    silk = SILK_DIM if lit else (70, 72, 75)
    gold = GOLD if lit else GOLD_DIM
    label = "REMOTE CONTROL"
    tw = text_w(TINY, label)
    tx = 238 - tw
    draw_text(a, TINY, label, tx, 4, gold)
    rect(a, tx, 10, tw, 1, lerp(gold, BODY, 0.35))
    rect(a, 19 + ww + 6, 7, tx - 6 - (19 + ww + 6), 1, silk)
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, BODY)
    matte(a, 0, 0, 344, 87, BODY)
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
# Seven-segment digits (9 x 13 cells): thin bars, 2px verticals, a gap at every joint
# (copied from the VFD generator's history; here dark LCD segments with lighter ghosts)
# ------------------------------------------------------------------------------------------

SEG = {
    "a": [(0, c) for c in range(2, 7)],
    "g": [(6, c) for c in range(2, 7)],
    "d": [(12, c) for c in range(2, 7)],
    "f": [(r, c) for r in range(1, 6) for c in (1, 2)],
    "b": [(r, c) for r in range(1, 6) for c in (6, 7)],
    "e": [(r, c) for r in range(7, 12) for c in (1, 2)],
    "c": [(r, c) for r in range(7, 12) for c in (6, 7)],
}
DIGIT_SEGS = {0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc", 5: "afgcd", 6: "afgedc", 7: "abc",
              8: "abcdefg", 9: "abcdfg"}


def seven_seg_part(a, x, y, segs, col):
    for s in segs:
        for r, c in SEG[s]:
            px(a, x + c, y + r, col)


def seven_seg(a, x, y, lit_segs):
    """A digit cell: lit segments in LCD ink, the rest as ghosts."""
    rect(a, x, y, 9, 13, LCD)
    seven_seg_part(a, x, y, [s for s in SEG if s not in lit_segs], LCD_GHOST)
    seven_seg_part(a, x, y, lit_segs, LCD_INK)


# Tiny digits for the program calendar's boxes (3x5; "1" one column wide so 10-12 fit in 5).
CAL = {str(d): FONT5[str(d)] for d in range(10)}
CAL["1"] = G("#", "#", "#", "#", "#")


def program_calendar(a, x, y, lit_upto):
    """The LCD's boxed program numbers 1-12, in two rows of six (5x5 inside each box)."""
    for n in range(1, 13):
        col_, row = (n - 1) % 6, (n - 1) // 6
        bx, by = x + col_ * 6, y + row * 6
        ink = LCD_INK if n <= lit_upto else LCD_GHOST
        edge = lerp(LCD_DIM, LCD, 0.45)
        for k in range(7):
            px(a, bx + k, by, edge)
            px(a, bx + k, by + 6, edge)
            px(a, bx, by + k, edge)
            px(a, bx + 6, by + k, edge)
        s = str(n)
        w = text_w(CAL, s)
        draw_text(a, CAL, s, bx + 1 + (5 - w) // 2, by + 1, ink)


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116)
# ------------------------------------------------------------------------------------------


def volume_knob(a, cx, cy, r=9.0):
    """The MOTORIZED VOLUME knob in miniature: a tick ring 0..10, black knob, red pointer."""
    H, W = a.shape[:2]
    # ticks: 300 degrees, gap at the bottom; majors at 0, 5, 10
    for i in range(31):
        ang = math.radians(240 - i * 10)
        major = i % 15 == 0
        r0, r1 = r + 1.8, r + (3.6 if major else 3.0)
        m = line_m(W, H, [(cx + r0 * math.cos(ang), cy - r0 * math.sin(ang)),
                          (cx + r1 * math.cos(ang), cy - r1 * math.sin(ang))], 0.8)
        paint(a, 0, 0, m, (210, 212, 212) if major else SILK, 1.0)
    paint(a, 0, 0, disc_m(W, H, cx, cy + 0.6, r + 0.6), BODY_LO, 0.9)     # shadow
    paint(a, 0, 0, disc_m(W, H, cx, cy, r), (70, 72, 76))                 # rim highlight
    paint(a, 0, 0, disc_m(W, H, cx + 0.3, cy + 0.4, r - 0.8), (18, 18, 20))
    paint(a, 0, 0, disc_m(W, H, cx, cy, r - 2.2), (40, 41, 44))           # the grip ring step
    paint(a, 0, 0, disc_m(W, H, cx + 0.2, cy + 0.3, r - 2.9), (24, 25, 27))
    ang = math.radians(200)                                               # about "3" on the dial
    m = line_m(W, H, [(cx + 1.5 * math.cos(ang), cy - 1.5 * math.sin(ang)),
                      (cx + (r - 1.6) * math.cos(ang), cy - (r - 1.6) * math.sin(ang))], 1.3)
    paint(a, 0, 0, m, RED_MARK)


def make_main():
    a = new(275, 116, BODY)
    matte(a, 0, 0, 275, 116, BODY)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # display window: a black frame holding two panes of the LCD glass
    rect(a, 19, 17, 252, 41, BEZEL)
    rect(a, 19, 58, 89, 11, BEZEL)
    rect(a, 19, 17, 252, 1, BODY_LO)
    rect(a, 19, 17, 1, 52, BODY_LO)
    rect(a, 20, 69, 88, 1, (64, 66, 70))
    rect(a, 108, 58, 1, 12, (64, 66, 70))
    rect(a, 109, 58, 162, 1, (64, 66, 70))
    rect(a, 271, 17, 1, 42, (64, 66, 70))
    glass(a, 22, 20, 84, 41)
    glass(a, 110, 20, 158, 35)
    # left pane: CD tag, time digits (ghosts under the sprites), analyzer
    rect(a, 24, 21, 13, 7, LCD_INK)
    draw_text(a, TINY, "CD", 26, 22, LCD)
    for x in (48, 60, 78, 90):
        seven_seg(a, x, 26, "")
    for yy in (29, 35):
        rect(a, 73, yy, 2, 2, LCD_INK)
    # right pane: kbps legend, program calendar
    draw_text(a, TINY, "KBPS", 128, 44, LCD_DIM)
    program_calendar(a, 171, 40, 9)
    # the frame's own print
    text_center(a, TINY, "TIME/FREQUENCY", 64, 63, SILK_DIM)

    # slider seats (the sliders' frames cover them)
    # seek bar seat: a slim recess
    rect(a, 15, 71, 251, 12, RECESS)
    sunken(a, 15, 71, 251, 12)

    # CD transport: the tray of satin black keys
    rect(a, 14, 87, 119, 21, RECESS)
    sunken(a, 14, 87, 119, 21)

    # the silver keypad: eject, shuffle (with its LED), repeat
    brushed(a, 134, 85, 107, 23, SILVER_TOP, SILVER_BOT, 3.5)
    raised(a, 134, 85, 107, 23, SILVER_HI, SILVER_LO)
    rect(a, 133, 84, 109, 1, BODY_LO)
    rect(a, 133, 84, 1, 25, BODY_LO)

    # the volume knob in the About spot
    volume_knob(a, 259.5, 96.5, 9.5)

    # bottom print: PORTABLE STEREO COMPONENT CD SYSTEM  RX-DS660
    mh, mw = ttf_mask("RX-DS660", FONT_MODEL, 9).shape
    mx = 268 - mw
    model_print(a, mx, 115 - mh, (190, 192, 192), 9)
    small = "PORTABLE STEREO COMPONENT CD SYSTEM"
    sw = text_w(TINY, small)
    draw_text(a, TINY, small, mx - 4 - sw, 109, SILK_DIM)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36)
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


def transport_icon(a, kind, cx, cy, ink):
    if kind == "previous":
        rect(a, cx - 6, cy - 3, 1, 7, ink)
        tri_left(a, cx - 5, cy - 3, 7, ink)
        tri_left(a, cx - 1, cy - 3, 7, ink)
    elif kind == "play":
        tri_right(a, cx - 2, cy - 4, 9, ink)
    elif kind == "pause":
        rect(a, cx - 3, cy - 3, 2, 7, ink)
        rect(a, cx + 1, cy - 3, 2, 7, ink)
    elif kind == "stop":
        rect(a, cx - 3, cy - 3, 7, 7, ink)
    elif kind == "next":
        tri_right(a, cx - 5, cy - 3, 7, ink)
        tri_right(a, cx - 1, cy - 3, 7, ink)
        rect(a, cx + 3, cy - 3, 1, 7, ink)
    elif kind == "eject":
        for r in range(3):
            rect(a, cx - r, cy - 3 + r, 2 * r + 1, 1, ink)
        rect(a, cx - 2, cy + 1, 5, 1, ink)


def make_cbuttons(main):
    a = new(136, 36, RECESS)
    specs = [("previous", 0, 23, 16), ("play", 23, 23, 39), ("pause", 46, 23, 62), ("stop", 69, 23, 85),
             ("next", 92, 22, 108)]
    for kind, x, w, dx in specs:
        for pressed, y in ((False, 0), (True, 18)):
            a[y:y + 18, x:x + w] = main[88:106, dx:dx + w]
            key_face(a, x, y, w, 18, pressed, satin=True)
            o = 1 if pressed else 0
            ink = (226, 228, 228) if not pressed else (200, 202, 204)
            transport_icon(a, kind, x + w // 2 + o, y + 9 + o, ink)
    # eject: a black key on the silver keypad with its label above
    for pressed, y in ((False, 0), (True, 16)):
        a[y:y + 16, 114:136] = main[89:105, 136:158]
        text_center(a, TINY, "EJECT", 125, y + 1, SILK_SILVER)
        key_face(a, 115, y + 7, 20, 8, pressed)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def silver_toggle(a, main, x, y, w, src, label, on, pressed):
    """A keypad key on silver: label above, a red LED left of a slim black key."""
    a[y:y + 15, x:x + w] = main[89:104, src:src + w]
    text_center(a, TINY, label, x + w // 2 + 2, y + 1, SILK_SILVER)
    led(a, x + 2, y + 9, on, 3, 2)
    key_face(a, x + 7, y + 7, w - 9, 7, pressed)


def make_shufrep(main):
    a = new(92, 85, BODY)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        silver_toggle(a, main, 0, y, 28, 210, "REPEAT", on, pressed)
        silver_toggle(a, main, 28, y, 47, 164, "SHUFFLE", on, pressed)
    # EQ / PL: black function keys on the body with the label on the key and a red LED
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        for on, y in ((False, 61), (True, 73)):
            src = 219 if label == "EQ" else 242
            a[y:y + 12, x:x + 23] = main[58:70, src:src + 23]
            key_face(a, x, y, 23, 12, pressed)
            o = 1 if pressed else 0
            led(a, x + 4 + o, y + 5 + o, on, 2, 2)
            draw_text(a, TINY, label, x + 10 + o, y + 4 + o, (220, 222, 222) if on else SILK)
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp (LCD)
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, LCD)
    for y, on in ((0, True), (12, False)):
        col = LCD_INK if on else LCD_GHOST
        text_center(a, TINY, "STEREO", 14, y + 4, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 4, col)
    return a


def make_playpaus():
    a = new(48, 9, LCD)
    tri_right(a, 2, 1, 7, LCD_INK)
    rect(a, 9 + 2, 1, 2, 7, LCD_INK)
    rect(a, 9 + 5, 1, 2, 7, LCD_INK)
    rect(a, 18 + 2, 2, 5, 5, LCD_INK)
    rect(a, 36, 0, 3, 9, LCD)
    rect(a, 39 + 1, 3, 1, 3, LCD_INK)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, LCD)
    for n in range(10):
        seven_seg(a, 9 * n, 0, DIGIT_SEGS[n])
    seven_seg(a, 90, 0, "")
    if ex:
        # minus: the middle segment alone on plain glass (main.bmp has no ghost digit there)
        seven_seg_part(a, 99, 0, "g", LCD_INK)
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


# The LCD's own lettering for text.bmp: a segment-display alphabet in each 5x6 cell's top-left
# 4x5 (a 1px gap column and row), built from full-width bars, side verticals and short diagonals
# as on the 14-segment character LCDs of CD players. Lowercase maps to uppercase (the app and
# Winamp look characters up lowercased). O and 0, S and 5 share their shapes, as on the real
# displays.
SEGFONT = {
    "A": G("####", "#..#", "####", "#..#", "#..#"),
    "B": G("####", "#..#", "###.", "#..#", "####"),
    "C": G("####", "#...", "#...", "#...", "####"),
    "D": G("###.", "#..#", "#..#", "#..#", "###."),
    "E": G("####", "#...", "###.", "#...", "####"),
    "F": G("####", "#...", "###.", "#...", "#..."),
    "G": G("####", "#...", "#.##", "#..#", "####"),
    "H": G("#..#", "#..#", "####", "#..#", "#..#"),
    "I": G("###.", ".#..", ".#..", ".#..", "###."),
    "J": G("...#", "...#", "...#", "#..#", "####"),
    "K": G("#..#", "#.#.", "##..", "#.#.", "#..#"),
    "L": G("#...", "#...", "#...", "#...", "####"),
    "M": G("#..#", "####", "####", "#..#", "#..#"),
    "N": G("#..#", "##.#", "#.##", "#..#", "#..#"),
    "O": G("####", "#..#", "#..#", "#..#", "####"),
    "P": G("####", "#..#", "####", "#...", "#..."),
    "Q": G("####", "#..#", "#..#", "#.##", "####"),
    "R": G("####", "#..#", "####", "#.#.", "#..#"),
    "S": G("####", "#...", "####", "...#", "####"),
    "T": G("###.", ".#..", ".#..", ".#..", ".#.."),
    "U": G("#..#", "#..#", "#..#", "#..#", "####"),
    "V": G("#..#", "#..#", "#..#", ".##.", ".##."),
    "W": G("#..#", "#..#", "####", "####", "#..#"),
    "X": G("#..#", ".##.", "....", ".##.", "#..#"),
    "Y": G("#..#", ".##.", ".#..", ".#..", ".#.."),
    "Z": G("####", "...#", ".##.", "#...", "####"),
    "0": G("####", "#..#", "#..#", "#..#", "####"),
    "1": G(".#..", ".#..", ".#..", ".#..", ".#.."),
    "2": G("####", "...#", "####", "#...", "####"),
    "3": G("####", "...#", ".###", "...#", "####"),
    "4": G("#..#", "#..#", "####", "...#", "...#"),
    "5": G("####", "#...", "####", "...#", "####"),
    "6": G("####", "#...", "####", "#..#", "####"),
    "7": G("####", "...#", "...#", "...#", "...#"),
    "8": G("####", "#..#", "####", "#..#", "####"),
    "9": G("####", "#..#", "####", "...#", "####"),
    '"': G("#.#.", "#.#.", "....", "....", "...."),
    "@": G("####", "#..#", "#.##", "#...", "####"),
    "…": G(".....", ".....", ".....", ".....", "#.#.#"),
    ".": G("....", "....", "....", "....", ".#.."),
    ":": G("....", ".#..", "....", ".#..", "...."),
    "(": G("..#.", ".#..", ".#..", ".#..", "..#."),
    ")": G(".#..", "..#.", "..#.", "..#.", ".#.."),
    "-": G("....", "....", ".##.", "....", "...."),
    "'": G(".#..", ".#..", "....", "....", "...."),
    "!": G(".#..", ".#..", ".#..", "....", ".#.."),
    "_": G("....", "....", "....", "....", "####"),
    "+": G("....", ".#..", "###.", ".#..", "...."),
    "\\": G("#...", ".#..", ".#..", "..#.", "...#"),
    "/": G("...#", "..#.", ".#..", ".#..", "#..."),
    "[": G("##..", "#...", "#...", "#...", "##.."),
    "]": G("..##", "...#", "...#", "...#", "..##"),
    "^": G(".##.", "#..#", "....", "....", "...."),
    "&": G(".#..", "#.#.", ".#..", "#.#.", ".#.#"),
    "%": G("#..#", "..#.", ".#..", ".#..", "#..#"),
    ",": G("....", "....", "....", ".#..", "#..."),
    "=": G("....", "####", "....", "####", "...."),
    "$": G("####", "#.#.", "####", ".#.#", "####"),
    "#": G(".#.#", "####", ".#.#", "####", ".#.#"),
    "å": G(".#..", "....", ".###", "#..#", ".###"),
    "ö": G("#..#", "....", ".##.", "#..#", ".##."),
    "ä": G("#..#", "....", ".###", "#..#", ".###"),
    "?": G("####", "...#", ".##.", "....", ".#.."),
    "*": G("#.#.", ".#..", "###.", ".#..", "#.#."),
}
# Unlit segments in every cell (the "8" of the bars and side verticals) as a faint tint of the
# glass, like the time digits' ghosts. Off: the ghosts would outnumber the ink, so the app (which
# colours its TrueType title with text.bmp's commonest non-background colour) would draw the
# title in the ghost tint, and they'd tile across the whole title box under it.
TEXT_GHOST = None


def make_text():
    a = new(155, 18, LCD)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None:
                continue
            x, y = col * 5, row * 6
            if TEXT_GHOST is not None:
                draw_text(a, {"8": SEGFONT["8"]}, "8", x, y, TEXT_GHOST)
            if ch == " ":
                continue
            key_ = ch if ch in SEGFONT else ch.upper()
            draw_text(a, SEGFONT, key_, x, y, LCD_INK)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def slide_cap(a, x, y, w, h, pressed, mark="v"):
    """A black slide-switch cap with the red line the unit's balance and EQ caps carry."""
    top, bot = ((70, 72, 76), (30, 31, 33)) if pressed else ((56, 58, 61), (22, 23, 25))
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(top, bot, r / max(1, h - 1)))
    rect(a, x, y, w, 1, (110, 112, 116) if pressed else (92, 94, 98))
    rect(a, x, y, 1, h, (80, 82, 86))
    rect(a, x + w - 1, y, 1, h, (6, 6, 7))
    rect(a, x, y + h - 1, w, 1, (6, 6, 7))
    col = (255, 96, 84) if pressed else RED_MARK
    if mark == "v":
        cx = x + w // 2
        rect(a, cx - (1 if w % 2 == 0 else 0), y + 2, 1 if w % 2 else 2, h - 4, col)
    else:
        cy = y + h // 2
        rect(a, x + 2, cy, w - 4, 1, col)


def make_posbar(main):
    a = new(307, 10, BODY)
    a[0:10, 0:248] = main[72:82, 16:264]
    rect(a, 0, 3, 248, 4, SLOT)
    sunken(a, 0, 3, 248, 4, BODY_LO, (60, 62, 66))
    for x in range(0, 248, 4):
        px(a, x + 2, 1, SILK_DIM if (x // 4) % 5 == 0 else (72, 74, 78))
        px(a, x + 2, 8, SILK_DIM if (x // 4) % 5 == 0 else (72, 74, 78))
    for x0, pressed in ((248, False), (278, True)):
        rect(a, x0, 0, 29, 10, BODY)
        slide_cap(a, x0, 0, 29, 10, pressed)
        for gx in (x0 + 6, x0 + 9, x0 + 19, x0 + 22):
            rect(a, gx, 3, 1, 4, (14, 14, 15))
            rect(a, gx + 1, 3, 1, 4, (80, 82, 86))
    return a


def slider_thumbs(a):
    slide_cap(a, 0, 422, 14, 11, True)
    slide_cap(a, 15, 422, 14, 11, False)


def make_volume(main):
    """The VOLUME scale: tick marks that turn red up to the level (the unit's red LED arrows),
    over a black channel."""
    a = new(68, 433, BODY)
    seat = main[57:70, 107:175]
    n_ticks = 17
    for i in range(28):
        y = i * 15
        a[y:y + 13, 0:68] = seat
        rect(a, 0, y + 13, 68, 2, BODY)
        rect(a, 2, y + 6, 64, 3, SLOT)
        sunken(a, 1, y + 5, 66, 5, BODY_LO, (64, 66, 70))
        level = (i + 1) / 28
        for k in range(n_ticks):
            tx = 7 + round(k * 54 / (n_ticks - 1))
            major = k % 4 == 0
            lit = tx <= 7 + level * 54 + 0.5
            col = RED if lit else ((132, 134, 136) if major else (86, 88, 92))
            rect(a, tx, y + (1 if major else 2), 1, 3 if major else 2, col)
            px(a, tx, y + 11, col if major else (60, 62, 66))
    slider_thumbs(a)
    return a


def make_balance(main):
    """The BALANCE scale: LEFT / RIGHT tick scale over a black channel, centre tick in red."""
    a = new(68, 433, BODY)
    seat = main[57:70, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 13, 9:47] = seat
        rect(a, 9, y + 13, 38, 2, BODY)
        rect(a, 11, y + 6, 34, 3, SLOT)
        sunken(a, 10, y + 5, 36, 5, BODY_LO, (64, 66, 70))
        for k in range(11):
            tx = 16 + round(k * 24 / 10)
            centre = k == 5
            col = RED if centre else ((132, 134, 136) if k in (0, 10) else (86, 88, 92))
            rect(a, tx, y + (1 if centre or k in (0, 10) else 2), 1, 3 if centre or k in (0, 10) else 2, col)
        draw_text(a, {"L": G("#..", "#..", "#..", "##.")}, "L", 10, y + 1, SILK_DIM)
        draw_text(a, {"R": G("##.", "#.#", "##.", "#.#")}, "R", 43, y + 1, SILK_DIM)
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
EQ_X = [21] + [78 + 18 * i for i in range(10)]


def eq_titlebar(lit):
    a = new(275, 14, BODY)
    matte(a, 0, 0, 275, 14, BODY)
    rect(a, 0, 0, 275, 1, BODY_HI)
    rect(a, 0, 0, 1, 14, BODY_HI)
    rect(a, 274, 0, 1, 14, BODY_LO)
    col = SILK if lit else SILK_OFF
    draw_text(a, TINY, "XBS", 8, 5, GOLD if lit else GOLD_DIM)
    section_line(a, 26, 252, 7, "GRAPHIC EQUALIZER", SILK_DIM if lit else (70, 72, 75), ends="up",
                 label_col=col)
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    """14x63: the black slot of the unit's graphic equalizer with its grey tick scale."""
    rect(a, x, y, 14, 63, RECESS)
    for k in range(13):
        ty = y + 6 + round(k * 51 / 12)
        major = k in (0, 6, 12)
        rect(a, x + 10, ty, 3 if major else 2, 1, (140, 142, 144) if major else (88, 90, 94))
        rect(a, x + 1, ty, 2 if major else 1, 1, (88, 90, 94) if major else (60, 62, 66))
    rect(a, x + 4, y + 1, 6, 61, SLOT)
    sunken(a, x + 4, y + 1, 6, 61, BODY_LO, (64, 66, 70))


def eq_thumb(a, x, y, pressed):
    slide_cap(a, x, y, 11, 11, pressed, mark="h")
    rect(a, x + 2, y + 2, 7, 1, (90, 92, 96) if not pressed else (120, 122, 126))
    rect(a, x + 2, y + 8, 7, 1, (12, 12, 13))


def xbs_wedge(a, x, y, w, h, col):
    """The gold XBS LEVEL wedge: an outlined triangle, wide at MAX, filled with gold rules."""
    for r in range(h):
        width = max(1, round(w * (1 - r / (h - 1))))
        px(a, x, y + r, col)
        px(a, x + width - 1 if width > 1 else x, y + r, col)
        if r % 2 == 0 and width > 3:
            rect(a, x + 2, y + r, width - 3, 1, lerp(col, RECESS, 0.35))
    rect(a, x, y, w, 1, col)


def make_eqmain():
    a = new(275, 315, BODY)
    matte(a, 0, 0, 275, 315, BODY)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = eq_titlebar(True)
    # graph: LCD glass
    glass(a, 86, 17, 113, 19)
    # slider bay
    rect(a, 15, 38 - 2, 248, 68, RECESS)
    sunken(a, 15, 36, 248, 68)
    # the XBS LEVEL wedge beside the preamp, with its MAX / MIN, then the dB scale
    draw_text(a, TINY, "MAX", 41, 40, GOLD)
    xbs_wedge(a, 42, 47, 11, 44, GOLD)
    draw_text(a, TINY, "MIN", 41, 94, GOLD)
    for lbl, yy in (("+12", 42), ("0", 67), ("-12", 92)):
        draw_text(a, TINY, lbl, 74 - text_w(TINY, lbl), yy, SILK_DIM)
    for x in EQ_X:
        eq_slider_frame(a, x, 38, 14)
    text_center(a, TINY, "PREAMP", 28, 106, SILK_DIM)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, SILK_DIM)
    rect(a, 4, 113, 267, 1, (60, 62, 66))

    # under the window: buttons
    mini_button(a, 0, 125, "close", True, pressed=True)
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        a[119:131, x:x + w] = a[18:30, (14 if label == "ON" else 40):(14 if label == "ON" else 40) + w]
        key_face(a, x, 119, w, 12, pressed)
        o = 1 if pressed else 0
        led(a, x + 4 + o, 119 + 5 + o, on, 2, 2)
        draw_text(a, TINY, label, x + 9 + o + (w - 9 - text_w(TINY, label)) // 2 - 1, 119 + 4 + o,
                  (226, 228, 228) if on else SILK)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    eq_thumb(a, 0, 164, False)
    eq_thumb(a, 0, 176, True)
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        key_face(a, 224, y, 44, 12, pressed)
        o = 1 if pressed else 0
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 4 + o, (226, 228, 228) if pressed else SILK)
    # graph: the curve in LCD ink, a dotted zero line and faint band columns
    rect(a, 0, 294, 113, 19, LCD)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, LCD_GHOST)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, lerp(LCD_GHOST, LCD_DIM, 0.4))
    for r in range(19):
        px(a, 115, 294 + r, lerp(LCD_INK, (70, 76, 60), abs(r - 9) / 18))
    for x in range(113):
        px(a, x, 314, LCD_DIM if x % 3 != 2 else LCD)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

BAR_LINE_Y = 9


def bar20(w):
    a = new(w, 20, BODY)
    matte(a, 0, 0, w, 20, BODY)
    rect(a, 0, 0, w, 1, BODY_HI)
    return a


def bar_line(t, x0, x1, lit):
    rect(t, x0, BAR_LINE_Y, x1 - x0, 1, SILK_DIM if lit else (70, 72, 75))


def mesh(a, x, y, w, h):
    """Speaker grille: black perforated mesh (a staggered dot grid)."""
    rect(a, x, y, w, h, (26, 27, 29))
    for r in range(h):
        for c in range(w):
            if (r % 2 == 0 and c % 2 == 0) or (r % 2 == 1 and c % 2 == 1):
                px(a, x + c, y + r, (8, 8, 9))


def lcd_box(a, x, y, w, h):
    rect(a, x - 1, y - 1, w + 2, h + 2, BEZEL)
    rect(a, x, y, w, h, LCD)


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


def make_pledit():
    a = new(280, 186, BODY)
    matte(a, 0, 0, 280, 186, BODY)
    for lit, y in ((True, 0), (False, 21)):
        # top tile
        t = bar20(25)
        bar_line(t, 0, 25, lit)
        rect(t, 0, 19, 25, 1, BODY_LO)
        a[y:y + 20, 127:152] = t
        # top-left corner
        t = bar20(25)
        rect(t, 0, 0, 1, 20, BODY_HI)
        bar_line(t, 5, 25, lit)
        rect(t, 5, BAR_LINE_Y - 2, 1, 2, SILK_DIM if lit else (70, 72, 75))
        rect(t, 11, 19, 14, 1, BODY_LO)
        rect(t, 11, 12, 1, 8, BODY_LO)
        a[y:y + 20, 0:25] = t
        # title: the line broken for a label, cassette-door style
        t = bar20(100)
        bar_line(t, 0, 100, lit)
        label = "PLAYLIST"
        tw = text_w(TINY, label)
        lx = 50 - (tw + 16) // 2
        rect(t, lx - 2, BAR_LINE_Y - 3, tw + 20, 7, BODY)
        tri_left(t, lx, BAR_LINE_Y - 2, 5, SILK if lit else SILK_OFF)
        draw_text(t, TINY, label, lx + 6, BAR_LINE_Y - 2, SILK if lit else SILK_OFF)
        tri_right(t, lx + 6 + tw + 3, BAR_LINE_Y - 2, 5, SILK if lit else SILK_OFF)
        rect(t, 0, 19, 100, 1, BODY_LO)
        a[y:y + 20, 26:126] = t
        # top-right corner: close button, the scrollbar groove's top
        t = bar20(25)
        rect(t, 24, 0, 1, 20, BODY_LO)
        bar_line(t, 0, 11, lit)
        mini_button(t, 14, 3, "close", lit)
        rect(t, 0, 19, 6, 1, BODY_LO)
        rect(t, 5, 13, 1, 7, BODY_HI)
        rect(t, 9, 14, 10, 6, SLOT)
        rect(t, 9, 14, 10, 1, BODY_LO)
        rect(t, 9, 14, 1, 6, BODY_LO)
        rect(t, 18, 14, 1, 6, (60, 62, 66))
        a[y:y + 20, 153:178] = t

    # left side tile
    t = new(12, 29)
    matte(t, 0, 0, 12, 29)
    rect(t, 0, 0, 1, 29, BODY_HI)
    rect(t, 11, 0, 1, 29, BODY_LO)
    a[42:71, 0:12] = t
    # right side tile: list edge, scrollbar channel at 5..12, outer edge
    t = new(20, 29)
    matte(t, 0, 0, 20, 29)
    rect(t, 0, 0, 1, 29, (60, 62, 66))
    rect(t, 19, 0, 1, 29, BODY_LO)
    rect(t, 4, 0, 10, 29, SLOT)
    rect(t, 4, 0, 1, 29, BODY_LO)
    rect(t, 13, 0, 1, 29, (60, 62, 66))
    for ty in range(2, 29, 5):
        rect(t, 15, ty, 2, 1, (86, 88, 92))
    a[42:71, 31:51] = t
    # close pressed, scroll handles
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        slide_cap(a, x, 53, 8, 18, sel, mark="h")

    # bottom pieces
    def bottom_base(w):
        t = new(w, 38)
        matte(t, 0, 0, w, 38)
        rect(t, 0, 0, w, 1, (60, 62, 66))
        rect(t, 0, 37, w, 1, BODY_LO)
        return t

    # left: the tape deck's keys (labels printed above, like FAST / REV / FWD / STOP)
    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, BODY_HI)
    rect(t, 11, 0, 1, 1, BODY_LO)
    rect(t, 12, 7, 112, 21, RECESS)
    sunken(t, 12, 7, 112, 21)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        key_face(t, bx, 8, 22, 18, False, satin=True)
        text_center(t, TINY, lbl, bx + 11, 15, (210, 212, 212))
    label = "AUTO REVERSE"
    tw = text_w(TINY, label)
    lx = 68 - (tw + 16) // 2
    tri_left(t, lx, 30, 5, SILK_DIM)
    draw_text(t, TINY, label, lx + 6, 30, SILK)
    tri_right(t, lx + 6 + tw + 3, 30, 5, SILK_DIM)
    a[72:110, 0:125] = t

    # right: running time on the LCD, the mini transport, LIST, grip
    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, BODY_LO)
    lcd_box(t, 6, 9, 56, 8)
    rect(t, 1, 21, 63, 12, RECESS)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        key_face(t, bx, 22, 10, 10, False, satin=True)
        mini_transport_icon(t, kind, bx, 22, (210, 212, 212))
    lcd_box(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, LCD_INK)
    rect(t, 84, 22 + 5, 1, 1, LCD_INK)
    key_face(t, 106, 8, 22, 18, False, satin=True)
    text_center(t, TINY, "LIST", 117, 15, (210, 212, 212))
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 33 - 3 * j
            px(t, gx, gy, SILK_DIM)
            px(t, gx + 1, gy + 1, BODY_LO)
    a[72:110, 126:276] = t

    # fill: a band of speaker grille between chrome rules
    t = bottom_base(25)
    rect(t, 0, 6, 25, 1, (150, 152, 156))
    rect(t, 0, 7, 25, 1, (96, 98, 102))
    mesh(t, 0, 8, 25, 19)
    rect(t, 0, 27, 25, 1, (190, 192, 196))
    rect(t, 0, 28, 25, 1, (110, 112, 116))
    a[0:38, 179:204] = t
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GEN_PLATE_Y = 4


def make_gen():
    a = new(194, 109, BODY)
    matte(a, 0, 0, 194, 109)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn):
            t = bar20(25)
            fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 1, 20, BODY_HI)
            bar_line(t, 5, 25, lit)
            rect(t, 5, BAR_LINE_Y - 2, 1, 2, SILK_DIM if lit else (70, 72, 75))

        def left_end(t):
            bar_line(t, 0, 20, lit)

        def centre(t):
            pass

        def right_end(t):
            bar_line(t, 5, 25, lit)

        def fill(t):
            bar_line(t, 0, 25, lit)

        def right(t):
            bar_line(t, 0, 11, lit)
            mini_button(t, 14, 3, "close", lit)
            rect(t, 24, 0, 1, 20, BODY_LO)

        piece(0, left)
        piece(26, left_end)
        piece(52, centre)
        piece(78, right_end)
        piece(104, fill)
        piece(130, right)

    def bottom(w, grip, left_edge):
        t = new(w, 14)
        matte(t, 0, 0, w, 14)
        rect(t, 0, 13, w, 1, BODY_LO)
        if left_edge:
            rect(t, 0, 0, 1, 14, BODY_HI)
        else:
            rect(t, w - 1, 0, 1, 14, BODY_LO)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 10 - 3 * j
                    px(t, gx, gy, SILK_DIM)
                    px(t, gx + 1, gy + 1, BODY_LO)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        matte(t, 0, 0, w, h)
        if outer_left:
            rect(t, 0, 0, 1, h, BODY_HI)
            rect(t, w - 1, 0, 1, h, BODY_LO)
        else:
            rect(t, w - 1, 0, 1, h, BODY_LO)
            rect(t, 0, 0, 1, h, (60, 62, 66))
        a[42:42 + h, x:x + w] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            rect(a, x, y, w, 7, BODY)
            draw_text(a, FONT5, c, x, y + 1, SILK if lit else SILK_OFF)
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp, text files
# ------------------------------------------------------------------------------------------

GENEX_COLOURS = [
    LCD,               # item background
    LCD_INK,           # item text
    BODY,              # window background
    (226, 228, 228),   # button text
    (214, 216, 216),   # window text
    (24, 25, 27),      # dividers, sunken borders
    (128, 136, 108),   # selection bar
    (34, 35, 38),      # list header background
    SILK,              # list header text
    (84, 85, 90),      # header frame, light
    (8, 8, 9),         # header frame, dark
    (60, 61, 65),      # header frame, pressed
    BODY,              # header dead area
    (40, 41, 44),      # scrollbar
    (96, 98, 102),     # scrollbar 2
    (56, 58, 61),      # scrollbar pressed
    RED_MARK,          # scrollbar pressed 2
    (20, 21, 23),      # scrollbar dead area
]


def make_genex():
    a = new(256, 64, BODY)
    matte(a, 0, 1, 256, 63)
    rect(a, 0, 0, 256, 1, BODY)
    for i, c in enumerate(GENEX_COLOURS):
        px(a, 48 + 2 * i, 0, c)
    key_face(a, 0, 1, 47, 15, False)
    key_face(a, 0, 16, 47, 15, True)
    return a


def viscolor():
    spec = [lerp((22, 26, 20), (78, 84, 64), i / 15) for i in range(16)]
    return ([(LCD, "background"), (LCD_GHOST, "dots")]
            + [(c, f"spectrum {i + 1}" + (" (top)" if i == 0 else "")) for i, c in enumerate(spec)]
            + [((22, 26, 20), "oscilloscope 1"), ((36, 40, 32), "oscilloscope 2"), ((50, 56, 42), "oscilloscope 3"),
               ((64, 70, 54), "oscilloscope 4"), ((80, 86, 66), "oscilloscope 5"), ((12, 14, 10), "peaks")])


PLEDIT = dict(Normal="#262B22", Current="#8A0F08", NormalBG=hexc(LCD), SelectedBG="#8C9678")


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        p = PLEDIT
        f.write(f"[Text]\nNormal={p['Normal']}\nCurrent={p['Current']}\nNormalBG={p['NormalBG']}\n"
                f"SelectedBG={p['SelectedBG']}\nMbBG={p['NormalBG']}\nMbFG={p['Normal']}\nFont=Arial\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{T.title} - a skin in the style of {T.subject}.\n"
            "Panasonic logo (c) Panasonic Holdings Corporation.\n\n"
            "Classic Winamp 2.x skin for YTMinamp's Winamp mode, generated by a script: matte\n"
            "charcoal plastic, grey and gold silkscreen, a pale olive LCD with seven-segment\n"
            "digits, the silver keypad, the motorized volume knob and the graphic equalizer.\n"
            "The Panasonic wordmark is lettering rendered from Liberation Sans Bold.\n"
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
    try:
        return ImageFont.truetype(FONT_PREVIEW, size)
    except OSError:
        return ImageFont.load_default()


def text_ink():
    """text.bmp's ink as the app finds it: the commonest non-background colour of its letters."""
    arr = np.asarray(SHEETS["text"]).reshape(-1, 3)
    bg = tuple(np.asarray(SHEETS["text"])[0, 150])
    cols, counts = np.unique(arr, axis=0, return_counts=True)
    best = [(n, tuple(int(v) for v in c)) for c, n in zip(cols, counts) if tuple(c) != bg]
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
        blit(img, nums, (99, 0, 9, 13), 38, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    # the title box blanked with text.bmp's space, then the title in a TrueType font in text.bmp's ink
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    if state.get("bitmap"):
        # Options > "Use bitmap font for main title display": text.bmp cell by cell
        draw_bitmap_text(img, state["title"][:30], 111, 24)
    else:
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
    p = PLEDIT
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
    c0, c1 = np.array((40, 42, 46), np.float32), np.array((180, 60, 48), np.float32)
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
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=17, remaining=False,
             title="Night Drive - Auto Reverse (Radio Edit)", bars=bars, bitmap=True)
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


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--list"]:
        for k, v in THEMES.items():
            print(f"{k:10s} {v.wsz}")
        sys.exit(0)
    for theme in (args or list(THEMES)):
        use_theme(theme)
        names = build()
        preview()
        print(f"{T.wsz}: {', '.join(names)}")
