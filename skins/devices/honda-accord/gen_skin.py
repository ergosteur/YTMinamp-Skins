#!/usr/bin/python3
"""Honda Accord: a classic Winamp 2.x skin in the style of a late-80s / early-90s Honda Accord's
centre stack, generated procedurally.

Based on skins/ember/gen_skin.py (whose sheet layouts it keeps). The main window is the
4th-generation (1990-93) Honda radio face: black textured plastic, small rectangular rubber
keys, a teal VFD window with seven-segment time digits; the sliders are the 3rd-generation
(1986-89) climate panel's long dark slots with chunky black knobs, its blue-to-red temperature
stripe and "OFF LO . . HI" fan legend; the toggles are the climate key row's square keys with
amber indicator slots; the titlebars are the dash's air-vent louvres. Burgundy dash leather
frames the playlist and gen windows. Everything is drawn here from code except Honda's wordmark,
loaded from source/honda-wordmark.png at generation time and recoloured to the radio's silver
print. Private use only.

    /usr/bin/python3 -I gen_skin.py [accord]   (no argument builds them all)
    /usr/bin/python3 -I gen_skin.py --list

Per theme: the bitmaps and text files in out/<theme>/, zipped flat into <Name>.wsz beside this
file, and preview-<theme>.png (the windows assembled from the sprites the way the app does, 2x).
"""

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
SCRATCH = os.path.join(OUT_ROOT, "scratch")
OUT = None
T = None

THEMES = {
    # 4th-gen (1990-93) Honda radio face, 3rd-gen (1986-89) climate sliders and keys.
    "accord": SimpleNamespace(name="accord", title="Honda Accord", wsz="Honda-Accord.wsz", seed=1986),
}

# ------------------------------------------------------------------------------------------
# Palette
# ------------------------------------------------------------------------------------------

PL = (25, 25, 27)             # black textured dash / radio plastic
PL_HI = (60, 60, 64)
PL_LO = (5, 5, 6)
CAV = (3, 3, 4)               # vent cavities, slots
SILVER = (200, 202, 206)      # silkscreen print
SILVER_DIM = (118, 120, 124)
SILVER_UNLIT = (96, 97, 101)
LEATHER = (70, 32, 39)        # burgundy dash leather
LEATHER_LO = (40, 16, 21)
LEATHER_HI = (104, 52, 60)
GLASS = (5, 13, 13)           # VFD glass (text.bmp's space cell)
VFD = (110, 246, 222)         # lit VFD teal
VFD_MID = (52, 168, 150)
VFD_LABEL = (40, 132, 118)    # printed VFD legends (kbps, kHz)
GHOST = (15, 36, 34)          # unlit segments: within 96 (summed RGB) of GLASS
AMBER = (255, 168, 52)
AMBER_HI = (255, 214, 140)
AMBER_OFF = (66, 46, 28)
TEMP_BLUE = (86, 150, 205)
TEMP_RED = (206, 62, 58)
SEP = (255, 0, 255)


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


def new(w, h, col=PL):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):y + h, max(0, x):x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def raised(a, x, y, w, h, hi=PL_HI, lo=PL_LO):
    rect(a, x, y, w, 1, hi)
    rect(a, x, y, 1, h, hi)
    rect(a, x, y + h - 1, w, 1, lo)
    rect(a, x + w - 1, y, 1, h, lo)


def sunken(a, x, y, w, h, hi=PL_HI, lo=PL_LO):
    raised(a, x, y, w, h, lo, hi)


_rng = np.random.default_rng(1986)


def grain(a, x, y, w, h, amp=2.2):
    """The dash plastic's fine stipple: fine noise and sparse lighter specks."""
    n = _rng.normal(0, 1, (h, w)) * amp
    specks = _rng.random((h, w)) < 0.025
    n = n + specks * 5
    a[y:y + h, x:x + w] += np.round(n).astype(np.int32)[:, :, None]


def plastic(a, x, y, w, h, col=PL, amp=2.2):
    rect(a, x, y, w, h, col)
    grain(a, x, y, w, h, amp)


def leather(a, x, y, w, h):
    """Burgundy leather grain: soft blotches with darker creases."""
    n = _rng.normal(0, 1, (h + 4, w + 4))
    s = np.zeros_like(n)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            s += np.roll(np.roll(n, dy, 0), dx, 1)
    s = s[2:-2, 2:-2] / 3.0
    crease = (s < -1.15).astype(np.float32)
    v = s * 4.0 - crease * 10 + _rng.normal(0, 1.2, (h, w))
    base = np.array(LEATHER, np.float32)
    tint = np.array([1.0, 0.55, 0.6], np.float32)
    a[y:y + h, x:x + w] = np.round(base[None, None, :] + v[:, :, None] * tint).astype(np.int32)


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

# 3x5 font for printed labels.
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
    "/": G("..#", "..#", ".#.", "#..", "#.."),
    "k": G("#..", "#.#", "##.", "#.#", "#.#"),
    "b": G("#..", "##.", "#.#", "#.#", "##."),
    "p": G("##.", "#.#", "##.", "#..", "#.."),
    "s": G(".##", "#..", ".#.", "..#", "##."),
    "z": G("###", "..#", ".#.", "#..", "###"),
}
for _c in "0123456789+-.":
    TINY[_c] = FONT5[_c]

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


WORDMARK_PNG = os.path.join(HERE, "source", "honda-wordmark.png")   # Honda's wordmark (red on transparent)
WORDMARK_H = 8
_WM = {}


def wordmark_mask(h=WORDMARK_H):
    """Honda's wordmark as a coverage mask h px tall: alpha (or redness against white), cropped,
    then scaled down with a box filter from the full-size art so the strokes stay crisp."""
    if h not in _WM:
        im = Image.open(WORDMARK_PNG).convert("RGBA")
        rgba = np.asarray(im, dtype=np.float32)
        alpha = rgba[..., 3]
        if alpha.min() > 250:   # no transparency: take redness against white
            alpha = np.clip(rgba[..., 0] - (rgba[..., 1] + rgba[..., 2]) / 2, 0, 255)
        m = Image.fromarray(alpha.astype(np.uint8), "L")
        m = m.crop(m.getbbox())
        w = round(m.width * h / m.height)
        m = m.resize((w, h), Image.BOX)
        cov = np.asarray(m, dtype=np.float32) / 255
        cov = np.clip((cov - 0.12) / 0.76, 0, 1)   # firm the edges a little so it reads at 1x
        _WM[h] = cov
    return _WM[h]


WORDMARK_W = wordmark_mask().shape[1]


def honda_wordmark(a, cx, y, lit):
    """The wordmark in the radio's silver print: silver shading to grey, dimmer when unfocused."""
    m = wordmark_mask()
    h, w = m.shape
    x = cx - w // 2
    top, bot = ((236, 238, 242), (150, 152, 158)) if lit else ((128, 129, 133), (86, 87, 91))
    shade = np.array([lerp(top, bot, r / (h - 1)) for r in range(h)], np.float32)[:, None, :]
    sh = a[y + 1:y + 1 + h, x + 1:x + 1 + w].astype(np.float32)
    a[y + 1:y + 1 + h, x + 1:x + 1 + w] = np.round(sh + (np.array(PL_LO) - sh) * m[..., None] * 0.8)
    reg = a[y:y + h, x:x + w].astype(np.float32)
    a[y:y + h, x:x + w] = np.round(reg + (shade - reg) * m[..., None]).astype(np.int32)
    return w


# ------------------------------------------------------------------------------------------
# Shared parts: vents, keys, knobs, VFD glass
# ------------------------------------------------------------------------------------------


def vent(a, x, y, w, rows, lit, tab=None):
    """Air-vent louvres: a black cavity with horizontal slats (rows: their y offsets)."""
    y0, y1 = min(rows) - 1, max(rows) + 2
    rect(a, x, y + y0, w, y1 - y0 + 1, CAV)
    rect(a, x, y + y0 - 1, w, 1, PL_LO)
    rect(a, x, y + y1 + 1, w, 1, PL_HI if lit else (44, 44, 47))
    top, body = ((78, 78, 83), (36, 36, 39)) if lit else ((54, 54, 58), (28, 28, 31))
    for r in rows:
        rect(a, x + 1, y + r, w - 2, 1, top)
        rect(a, x + 1, y + r + 1, w - 2, 1, body)
    if tab is not None:   # the louvre's thumb tab, ribbed
        tx, tr = tab
        rect(a, x + tx, y + tr - 1, 7, 3, (62, 62, 66) if lit else (44, 44, 47))
        rect(a, x + tx, y + tr - 1, 7, 1, (110, 110, 116) if lit else (70, 70, 74))
        for k in range(1, 7, 2):
            px(a, x + tx + k, y + tr, (20, 20, 22))
            px(a, x + tx + k, y + tr + 1, (20, 20, 22))


def rubber_key(a, x, y, w, h, pressed=False):
    """A small rectangular black rubber key with rounded corners."""
    if pressed:
        stops = ((22, 22, 24), (30, 30, 33))
    else:
        stops = ((62, 62, 66), (30, 30, 33))
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(*stops, r / max(1, h - 1)))
    if pressed:
        rect(a, x, y, w, 1, (8, 8, 9))
        rect(a, x, y, 1, h, (12, 12, 13))
        rect(a, x + w - 1, y, 1, h, (40, 40, 44))
        rect(a, x, y + h - 1, w, 1, (44, 44, 48))
    else:
        rect(a, x, y, w, 1, (96, 96, 102))
        rect(a, x, y, 1, h, (72, 72, 77))
        rect(a, x + w - 1, y, 1, h, (14, 14, 16))
        rect(a, x, y + h - 1, w, 1, (8, 8, 9))
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, PL_LO)


def key_well(a, x, y, w, h):
    """The dark gap a key sits in."""
    rect(a, x - 1, y - 1, w + 2, h + 2, (9, 9, 10))
    rect(a, x - 1, y + h, w + 2, 1, (44, 44, 48))


def climate_key(a, x, y, w, h, label, on, pressed, slot="top"):
    """The climate panel's square key: a grey face, an amber indicator slot, a dark label window
    with white lettering. slot='top' (the real keys) or 'left' (short keys)."""
    face = ((40, 40, 43), (30, 30, 33)) if pressed else ((70, 70, 74), (40, 40, 44))
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(*face, r / max(1, h - 1)))
    if pressed:
        raised(a, x, y, w, h, (10, 10, 11), (56, 56, 60))
    else:
        raised(a, x, y, w, h, (104, 104, 110), (10, 10, 11))
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, PL_LO)
    o = 1 if pressed else 0
    ink = (236, 238, 242) if not pressed else (210, 212, 216)
    if on:
        ink = (250, 250, 250)
    if slot == "top":
        sw = min(8, w - 8)
        sx = x + (w - sw) // 2
        rect(a, sx - 1, y + 2 + o, sw + 2, 3, (14, 12, 10))
        rect(a, sx, y + 3 + o, sw, 1, AMBER if on else AMBER_OFF)
        lw = w - 6
        rect(a, x + 3, y + 6 + o, lw, h - 8, (24, 24, 26))
        rect(a, x + 3, y + 6 + o, lw, 1, (12, 12, 13))
        text_center(a, TINY, label, x + w // 2, y + 7 + o, ink)
    else:
        rect(a, x + 2, y + 3 + o, 4, h - 6, (14, 12, 10))
        rect(a, x + 3, y + 4 + o, 2, h - 8, AMBER if on else AMBER_OFF)
        if on:
            rect(a, x + 3, y + 4 + o, 2, 1, AMBER_HI)
        rect(a, x + 7, y + 2 + o, w - 9, h - 4, (24, 24, 26))
        rect(a, x + 7, y + 2 + o, w - 9, 1, (12, 12, 13))
        text_center(a, TINY, label, x + 7 + (w - 9) // 2, y + (h - 5) // 2 + o, ink)


def slot_h(a, x, y, w, h=5):
    """A long horizontal slider slot (the climate panel's)."""
    rect(a, x, y, w, h, (10, 10, 11))
    rect(a, x, y, w, 1, CAV)
    rect(a, x, y, 1, h, CAV)
    rect(a, x + 1, y + 1, w - 2, 1, (2, 2, 2))
    rect(a, x, y + h - 1, w, 1, (58, 58, 62))
    rect(a, x + w - 1, y, 1, h, (46, 46, 50))


def slot_v(a, x, y, w, h):
    rect(a, x, y, w, h, (10, 10, 11))
    rect(a, x, y, 1, h, CAV)
    rect(a, x, y, w, 1, CAV)
    rect(a, x + 1, y + 1, 1, h - 2, (2, 2, 2))
    rect(a, x + w - 1, y, 1, h, (58, 58, 62))
    rect(a, x, y + h - 1, w, 1, (46, 46, 50))


def climate_knob(a, x, y, w, h, selected=False, ridge=True):
    """The climate slider's chunky black knob: a lit top face, a dark front, a pointer line."""
    top_h = max(2, h // 3)
    tf = ((112, 112, 118), (70, 70, 75)) if selected else ((92, 92, 98), (58, 58, 62))
    ff = ((44, 44, 48), (16, 16, 18)) if selected else ((36, 36, 40), (12, 12, 14))
    rect(a, x, y, w, h, PL_LO)
    for r in range(1, top_h):
        rect(a, x + 1, y + r, w - 2, 1, lerp(*tf, (r - 1) / max(1, top_h - 2)))
    for r in range(top_h, h - 1):
        rect(a, x + 1, y + r, w - 2, 1, lerp(*ff, (r - top_h) / max(1, h - 2 - top_h)))
    rect(a, x + 1, y + 1, w - 2, 1, (150, 150, 156) if selected else (124, 124, 130))
    rect(a, x + 1, y + top_h, w - 2, 1, (6, 6, 7))
    rect(a, x + 1, y + top_h + 1, 1, h - top_h - 2, (54, 54, 58))
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, (14, 14, 15))
    if ridge:
        c = x + w // 2
        rect(a, c, y + 1, 1, h - 2, (176, 176, 182) if selected else (140, 140, 146))
        rect(a, c + 1, y + top_h + 1, 1, h - top_h - 2, (6, 6, 7))


def climate_knob_v(a, x, y, w, h, selected=False):
    """The knob for a vertical slot (EQ, scrollbar): lit top, dark body, a horizontal pointer."""
    climate_knob(a, x, y, w, h, selected, ridge=False)
    c = y + h // 2 + (1 if h > 8 else 0)
    rect(a, x + 2, c, w - 4, 1, (176, 176, 182) if selected else (140, 140, 146))
    rect(a, x + 2, c + 1, w - 4, 1, (6, 6, 7))


def round_knob(a, cx, cy, r, lit=True):
    h, w = a.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]
    d = np.hypot(xs - cx, ys - cy)
    ring = (d <= r + 0.5)
    a[ring] = (8, 8, 9)
    face = d <= r - 0.6
    t = np.clip((ys - (cy - r)) / (2 * r), 0, 1)
    for i in range(3):
        top, bot = (74, 32)[0], (74, 32)[1]
        a[..., i] = np.where(face, np.round(top + (bot - top) * t).astype(np.int32), a[..., i])
    rim = face & (d > r - 1.8) & (ys < cy)
    a[rim] = (110, 110, 116)
    knurl = face & (d > r - 1.8) & (ys >= cy) & ((np.round(np.degrees(np.arctan2(ys - cy, xs - cx))) // 30) % 2 == 0)
    a[knurl] = (18, 18, 20)
    cap = d <= r * 0.45
    a[cap] = (46, 46, 50)
    px(a, int(cx - 1), int(cy - 1), (96, 96, 102))


def vfd_window(a, x, y, w, h):
    """The VFD window: a black rim then the dark teal-black glass."""
    rect(a, x - 2, y - 2, w + 4, h + 4, PL_LO)
    rect(a, x - 2, y + h + 1, w + 4, 1, PL_HI)
    rect(a, x + w + 1, y - 2, 1, h + 4, (40, 40, 44))
    rect(a, x, y, w, h, GLASS)


def tri_right(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        rect(a, x, y + r, half - abs(r - half) + 1, 1, col)


def tri_left(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x + half + 1 - n, y + r, n, 1, col)


def icon(a, kind, cx, cy, col):
    """Transport icons, 7 rows tall, centred on (cx, cy)."""
    if kind == "previous":
        rect(a, cx - 4, cy - 3, 1, 7, col)
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
        tri_right(a, cx - 4, cy - 3, 7, col)
        tri_right(a, cx, cy - 3, 7, col)
        rect(a, cx + 4, cy - 3, 1, 7, col)
    elif kind == "eject":
        for r in range(4):
            rect(a, cx - r, cy - 3 + r, 2 * r + 1, 1, col)
        rect(a, cx - 3, cy + 2, 7, 1, col)


def mini_icon(a, kind, cx, cy, col):
    if kind == "previous":
        rect(a, cx - 3, cy - 2, 1, 5, col)
        tri_left(a, cx - 2, cy - 2, 5, col)
        tri_left(a, cx + 1, cy - 2, 5, col)
    elif kind == "play":
        tri_right(a, cx - 1, cy - 2, 5, col)
    elif kind == "pause":
        rect(a, cx - 2, cy - 2, 2, 5, col)
        rect(a, cx + 1, cy - 2, 2, 5, col)
    elif kind == "stop":
        rect(a, cx - 2, cy - 2, 5, 5, col)
    elif kind == "next":
        tri_right(a, cx - 3, cy - 2, 5, col)
        tri_right(a, cx, cy - 2, 5, col)
        rect(a, cx + 3, cy - 2, 1, 5, col)
    elif kind == "eject":
        for r in range(3):
            rect(a, cx - r, cy - 2 + r, 2 * r + 1, 1, col)
        rect(a, cx - 2, cy + 2, 5, 1, col)


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: a tiny rubber key."""
    rubber_key(a, x, y, 9, 9, pressed)
    ink = SILVER if lit else SILVER_UNLIT
    if pressed:
        ink = (240, 240, 244)
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        rect(a, X + 3, Y + 3, 3, 3, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 1, ink)
        rect(a, X + 2, Y + 4, 5, 1, lerp(ink, PL, 0.5))
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]
VENT_ROWS = [3, 6, 9]


def titlebar_body(w, h=14):
    a = new(w, h)
    plastic(a, 0, 0, w, h)
    rect(a, 0, 0, w, 1, PL_HI)
    return a


def main_titlebar(lit):
    a = titlebar_body(275)
    rect(a, 0, 0, 1, 14, PL_HI)
    rect(a, 274, 0, 1, 14, PL_LO)
    ww = WORDMARK_W
    wx = 137 - ww // 2
    vent(a, 18, 0, wx - 8 - 18, VENT_ROWS, lit, tab=(22, 6))
    vent(a, wx + ww + 8, 0, 240 - (wx + ww + 8), VENT_ROWS, lit, tab=(240 - (wx + ww + 8) - 30, 6))
    honda_wordmark(a, 137, 3, lit)
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def clutter_bar(lit_letters):
    a = new(8, 43, (9, 9, 10))
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        for r in range(h - 1):
            rect(a, 0, y + r, 8, 1, lerp((66, 66, 70), (38, 38, 42), r / max(1, h - 2)))
        rect(a, 0, y, 8, 1, (100, 100, 106))
        rect(a, 0, y + h - 1, 8, 1, (6, 6, 7))
        draw_text(a, TINY, letter, 1, y + (h - 5) // 2, (236, 238, 242) if on else (176, 178, 182))
        rect(a, 5, y + 1, 3, h - 2, (14, 12, 10))
        rect(a, 6, y + 2, 1, h - 4, AMBER if on else AMBER_OFF)
    return a


def make_titlebar():
    a = new(344, 87)
    plastic(a, 0, 0, 344, 87)
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

SEG = {
    "a": [(0, c) for c in range(2, 7)],
    "g": [(6, c) for c in range(2, 7)],
    "d": [(12, c) for c in range(2, 7)],
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
    rect(a, x, y, 9, 13, GLASS)
    for s, cells in SEG.items():
        if s not in lit_segs and ghost:
            for r, c in cells:
                px(a, x + c, y + r, GHOST)
    for s, cells in SEG.items():
        if s in lit_segs:
            for r, c in cells:
                px(a, x + c, y + r, VFD)


# The VFD window: the full width at the top (title and info rows), deeper on the left for the
# time and the analyzer. Inner glass rects.
VFD_TOP = (20, 18, 248, 33)     # x 20..267, y 18..50
VFD_LEFT = (20, 18, 85, 44)     # x 20..104, y 18..61


def make_main():
    a = new(275, 116)
    plastic(a, 0, 0, 275, 116)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = main_titlebar(True)

    a[22:65, 10:18] = clutter_bar("")
    rect(a, 9, 21, 10, 45, (9, 9, 10))
    a[22:65, 10:18] = clutter_bar("")

    # the VFD window (L-shaped: the two rects share the rim)
    for r in (VFD_TOP, VFD_LEFT):
        vfd_window(a, *r)
    for r in (VFD_TOP, VFD_LEFT):
        rect(a, *r, GLASS)
    rect(a, 106, 16, 1, 2, PL_LO)       # the left rect's rim, where it meets the top one's
    # time: ghost segments where the app draws the digits, the colon, the minus's ghost
    for x in (48, 60, 78, 90):
        seven_seg(a, x, 26, "")
    for r, c in SEG["g"]:
        px(a, 36 + c, 26 + r, GHOST)
    for yy in (30, 34):
        rect(a, 72, yy, 2, 2, VFD_MID)
    # a hairline of ghost dots under the analyzer
    for x in range(24, 100, 2):
        px(a, x, 60, GHOST)
    # info row legends
    draw_text(a, TINY, "kbps", 128, 44, VFD_LABEL)
    draw_text(a, TINY, "kHz", 168, 44, VFD_LABEL)

    # climate legend over volume: fan  OFF LO . . HI ; temperature stripe over balance
    lab = SILVER
    text_center(a, TINY, "OFF", 114, 52, lab)
    text_center(a, TINY, "LO", 129, 52, lab)
    px(a, 142, 54, lab)
    rect(a, 154, 53, 2, 2, lab)
    text_center(a, TINY, "HI", 168, 52, lab)
    rect(a, 179, 53, 25, 1, TEMP_BLUE)
    rect(a, 183, 55, 30, 1, TEMP_RED)
    rect(a, 206, 53, 7, 3, TEMP_RED)
    # slider seats (the slider frames cover them)
    slot_h(a, 109, 60, 64)
    slot_h(a, 179, 60, 34)
    # seek slot
    slot_h(a, 18, 74, 244, 6)

    # key labels above the rubber keys, and the keys' wells
    for lbl, x, w in (("REW", 16, 23), ("PLAY", 39, 23), ("PAUSE", 62, 23), ("STOP", 85, 23), ("FF", 108, 22),
                      ("EJECT", 136, 22)):
        text_center(a, TINY, lbl, x + w // 2, 82, SILVER)
    for x, w in ((16, 23), (39, 23), (62, 23), (85, 23), (108, 22)):
        key_well(a, x + 1, 89, w - 2, 16)
    key_well(a, 137, 90, 20, 14)
    rect(a, 163, 88, 76, 17, (9, 9, 10))
    rect(a, 163, 105, 76, 1, (44, 44, 48))

    # the twin small knobs (FAD/BAL, BAS/TRE), bottom right (the About spot)
    for cx, lbl in ((249, "FAD"), (263, "BAS")):
        text_center(a, TINY, lbl, cx, 82, SILVER)
        round_knob(a, cx, 96, 6)
    px(a, 256, 84, SILVER)
    # a model print along the bottom
    draw_text(a, TINY, "ELECTRONIC TUNING STEREO", 16, 108, SILVER_DIM)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons, shufrep, monoster, playpaus, numbers, text
# ------------------------------------------------------------------------------------------


def radio_key(a, x, y, w, h, num, kind, pressed):
    """The 4th-gen radio's preset key: number, a dot, a symbol."""
    rubber_key(a, x, y, w, h, pressed)
    o = 1 if pressed else 0
    ink = (240, 240, 244) if pressed else (214, 216, 220)
    cy = y + h // 2 + o
    if num:
        draw_text(a, FONT5, num, x + 3 + o, cy - 2, ink)
        px(a, x + 8 + o, cy, (150, 150, 156))
        icon(a, kind, x + w - 7 + o, cy, ink)
    else:
        icon(a, kind, x + w // 2 + o, cy, ink)


def make_cbuttons(main):
    a = new(136, 36)
    specs = [("previous", "1", 0, 23, 16), ("play", "2", 23, 23, 39), ("pause", "3", 46, 23, 62),
             ("stop", "4", 69, 23, 85), ("next", "5", 92, 22, 108)]
    for kind, num, x, w, dx in specs:
        for pressed, y in ((False, 0), (True, 18)):
            a[y:y + 18, x:x + w] = main[88:106, dx:dx + w]
            radio_key(a, x + 1, y + 1, w - 2, 16, num, kind, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        a[y:y + 16, 114:136] = main[89:105, 136:158]
        radio_key(a, 115, y + 1, 20, 14, None, "eject", pressed)
    return a


def make_shufrep(main):
    a = new(92, 85, (9, 9, 10))
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        rect(a, 0, y, 75, 15, (9, 9, 10))
        climate_key(a, 1, y, 26, 15, "RPT", on, pressed)
        climate_key(a, 29, y, 45, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        for on, y in ((False, 61), (True, 73)):
            a[y:y + 12, x:x + 23] = main[58:70, 219 + (x % 46):219 + (x % 46) + 23]
            climate_key(a, x, y, 22, 12, label, on, pressed, slot="left")
    return a


def make_monoster(main):
    a = new(56, 24, GLASS)
    for y, lit in ((0, True), (12, False)):
        col = VFD if lit else GHOST
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 42, y + 3, col)
        # the bottom rows reach the window's rim and the plastic under it
        a[y + 10:y + 12, 0:56] = main[51:53, 212:268]
    return a


def make_playpaus():
    a = new(48, 9, GLASS)
    tri_right(a, 2, 1, 7, VFD)
    rect(a, 9 + 2, 1, 2, 7, VFD)
    rect(a, 9 + 5, 1, 2, 7, VFD)
    rect(a, 18 + 2, 2, 5, 5, VFD)
    rect(a, 36, 0, 3, 9, GLASS)
    rect(a, 39 + 1, 3, 1, 3, VFD)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, GLASS)
    for n in range(10):
        seven_seg(a, 9 * n, 0, DIGIT_SEGS[n])
    if ex:
        seven_seg(a, 99, 0, "g")
        for s, cells in SEG.items():   # the minus: the middle segment alone, no ghosts
            if s != "g":
                for r, c in cells:
                    px(a, 99 + c, r, GLASS)
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, GLASS)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key, col * 5, row * 6, VFD)
    return a


# ------------------------------------------------------------------------------------------
# posbar, volume, balance: the climate panel's slots and knobs
# ------------------------------------------------------------------------------------------


def make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    for x, sel in ((248, False), (278, True)):
        a[0:10, x:x + 29] = main[72:82, 100:129]
        climate_knob(a, x + 1, 0, 27, 10, sel)
    return a


def make_volume(main):
    a = new(68, 433)
    for i in range(28):
        y = i * 15
        a[y:y + 13, 0:68] = main[57:70, 107:175]
        a[y + 13:y + 15, 0:68] = main[70:72, 107:175]
    climate_knob(a, 0, 422, 14, 11, True)
    climate_knob(a, 15, 422, 14, 11, False)
    return a


def make_balance(main):
    a = new(68, 433)
    for i in range(28):
        y = i * 15
        a[y:y + 13, 9:47] = main[57:70, 177:215]
    climate_knob(a, 0, 422, 14, 11, True)
    climate_knob(a, 15, 422, 14, 11, False)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
EQ_X = [21] + [78 + 18 * i for i in range(10)]


def title_plate(a, x, y, w, h, lit):
    rect(a, x, y, w, h, (12, 12, 13) if lit else (17, 17, 18))
    rect(a, x, y, w, 1, PL_LO)
    rect(a, x, y + h - 1, w, 1, PL_HI if lit else (44, 44, 47))


def title_ink(lit):
    return SILVER if lit else SILVER_UNLIT


def eq_titlebar(lit):
    a = titlebar_body(275)
    rect(a, 0, 0, 1, 14, PL_HI)
    rect(a, 274, 0, 1, 14, PL_LO)
    title = "EQUALIZER"
    tw = text_w(FONT5, title)
    px0 = (275 - tw) // 2 - 4
    vent(a, 6, 0, px0 - 6 - 6, VENT_ROWS, lit, tab=(14, 6))
    vent(a, px0 + tw + 14, 0, 260 - (px0 + tw + 14), VENT_ROWS, lit, tab=(260 - (px0 + tw + 14) - 22, 6))
    title_plate(a, px0, 2, tw + 8, 10, lit)
    draw_text(a, FONT5, title, px0 + 4, 4, title_ink(lit))
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_frame(bg):
    a = bg.copy()
    slot_v(a, 5, 2, 4, 59)
    for yy in (30,):
        rect(a, 1, yy, 2, 1, SILVER_DIM)
        rect(a, 11, yy, 2, 1, SILVER_DIM)
    return a


def eq_body():
    a = new(275, 116)
    plastic(a, 0, 0, 275, 116)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = eq_titlebar(True)
    # graph: a small VFD window
    vfd_window(a, 86, 17, 113, 19)
    # key wells
    rect(a, 13, 17, 60, 14, (9, 9, 10))
    rect(a, 216, 17, 46, 14, (9, 9, 10))
    # the slider panel: a recessed climate panel
    rect(a, 14, 35, 248, 76, (17, 17, 19))
    sunken(a, 14, 35, 248, 76)
    grain(a, 15, 36, 246, 74, 1.6)
    # temperature stripe up the preamp's side (red = boost, blue = cut), and dB print
    rect(a, 42, 41, 1, 40, TEMP_RED)
    rect(a, 41, 41, 3, 7, TEMP_RED)
    rect(a, 45, 58, 1, 40, TEMP_BLUE)
    rect(a, 44, 97, 3, 1, TEMP_BLUE)
    for lbl, yy in (("+12", 41), ("0", 67), ("-12", 92)):
        text_center(a, TINY, lbl, 59, yy, SILVER)
        rect(a, 68, yy + 2, 4, 1, SILVER_DIM)
    for x in EQ_X:
        a[38:101, x:x + 14] = eq_frame(a[38:101, x:x + 14])
    text_center(a, TINY, "PREAMP", 28, 104, SILVER)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 104, SILVER)
    return a


def make_eqmain():
    a = new(275, 315)
    plastic(a, 0, 0, 275, 315)
    body = eq_body()
    a[0:116, :] = body
    c = new(9, 9)
    mini_button(c, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = c
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        bx = 14 if label == "ON" else 40
        a[119:131, x:x + w] = body[18:30, bx:bx + w]
        climate_key(a, x, 119, w - 1, 12, label, on, pressed, slot="left")
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    climate_knob_v(a, 0, 164, 11, 11, False)
    climate_knob_v(a, 0, 176, 11, 11, True)
    frame = body[38:101, 78:92]
    for n in range(28):
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = frame
    for y, pressed in ((164, False), (176, True)):
        a[y:y + 12, 224:268] = body[18:30, 217:261]
        climate_key(a, 224, y, 44, 12, "PRESETS", False, pressed, slot="left")
    # graph background, preamp line, the curve's colours
    rect(a, 0, 294, 113, 19, GLASS)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, GHOST)
    for x in range(0, 113, 12):
        for y in range(0, 19, 2):
            px(a, x, 294 + y, GHOST)
    for r in range(19):
        px(a, 115, 294 + r, ramp([(200, 255, 244), VFD, VFD_MID, VFD], r / 18))
    for x in range(113):
        px(a, x, 314, VFD_LABEL if x % 3 != 2 else GLASS)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): black plastic bars, burgundy leather sides
# ------------------------------------------------------------------------------------------

BAR_VENT = [4, 7, 10, 13]


def bar20(w, lit):
    a = new(w, 20)
    plastic(a, 0, 0, w, 20)
    rect(a, 0, 0, w, 1, PL_HI)
    rect(a, 0, 19, w, 1, PL_LO)
    return a


def side_tile(w, h, outer_left, inner_w):
    """Leather with a black bezel lip next to the content (inner_w px of it)."""
    t = new(w, h)
    leather(t, 0, 0, w, h)
    if outer_left:
        rect(t, 0, 0, 1, h, LEATHER_HI)
        rect(t, w - inner_w, 0, inner_w, h, PL)
        rect(t, w - inner_w, 0, 1, h, PL_HI)
        rect(t, w - inner_w - 1, 0, 1, h, LEATHER_LO)
    else:
        rect(t, w - 1, 0, 1, h, LEATHER_LO)
        rect(t, 0, 0, inner_w, h, PL)
        rect(t, inner_w - 1, 0, 1, h, PL_LO)
        rect(t, inner_w, 0, 1, h, LEATHER_HI)
    return t


def make_pledit():
    a = new(280, 186)
    plastic(a, 0, 0, 280, 186)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit)
        vent(t, 0, 0, 25, BAR_VENT, lit)
        a[y:y + 20, 127:152] = t
        t = bar20(25, lit)
        rect(t, 0, 0, 1, 20, PL_HI)
        vent(t, 4, 0, 21, BAR_VENT, lit)
        a[y:y + 20, 0:25] = t
        t = bar20(100, lit)
        title_plate(t, 4, 4, 92, 12, lit)
        text_center(t, FONT5, "PLAYLIST", 50, 7, title_ink(lit))
        rect(t, 0, 3, 3, 14, CAV)
        rect(t, 97, 3, 3, 14, CAV)
        a[y:y + 20, 26:126] = t
        t = bar20(25, lit)
        rect(t, 24, 0, 1, 20, PL_LO)
        vent(t, 0, 0, 12, BAR_VENT, lit)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    a[42:71, 0:12] = side_tile(12, 29, True, 3)
    t = side_tile(20, 29, False, 15)
    # the scrollbar: a vertical climate slot at x 5..12
    slot_v(t, 5, 0, 8, 29)
    rect(t, 5, 0, 8, 29, (10, 10, 11))
    rect(t, 5, 0, 1, 29, CAV)
    rect(t, 12, 0, 1, 29, (58, 58, 62))
    rect(t, 8, 0, 2, 29, (4, 4, 5))
    a[42:71, 31:51] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        climate_knob_v(a, x, 53, 8, 18, sel)

    def bottom_base(w):
        t = new(w, 38)
        plastic(t, 0, 0, w, 38)
        rect(t, 0, 0, w, 1, PL_LO)
        rect(t, 0, 1, w, 1, PL_HI)
        rect(t, 0, 37, w, 1, PL_LO)
        return t

    t = bottom_base(125)
    lt = side_tile(12, 1, True, 3)
    rect(t, 0, 0, 1, 38, PL_HI)
    t[0:1, 0:12] = lt[0:1]
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        key_well(t, bx, 8, 22, 18)
        rubber_key(t, bx, 8, 22, 18, False)
        text_center(t, TINY, lbl, bx + 11, 15, (214, 216, 220))
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, PL_LO)
    rt = side_tile(20, 1, False, 15)
    t[0:1, 130:150] = rt[0:1]
    vfd_window(t, 6, 9, 56, 8)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    rect(t, 2, 21, 62, 12, (9, 9, 10))
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        rubber_key(t, bx, 22, 10, 10, False)
        mini_icon(t, kind, bx + 5, 27, (214, 216, 220))
    vfd_window(t, 65, 22, 33, 8)
    rect(t, 84, 24, 1, 1, VFD_MID)
    rect(t, 84, 27, 1, 1, VFD_MID)
    key_well(t, 106, 8, 22, 18)
    rubber_key(t, 106, 8, 22, 18, False)
    text_center(t, TINY, "LIST", 117, 15, (214, 216, 220))
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 30 - 3 * j
            px(t, gx, gy, SILVER_DIM)
            px(t, gx + 1, gy + 1, PL_LO)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GEN_PLATE = (3, 12)   # y, h of the title strip in the 20px bar (letters drawn at y 4, 7 tall)


def make_gen():
    a = new(194, 109)
    plastic(a, 0, 0, 194, 109)
    py, ph = GEN_PLATE
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn):
            t = bar20(25, lit)
            fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 1, 20, PL_HI)
            vent(t, 4, 0, 21, BAR_VENT, lit)

        def left_end(t):
            vent(t, 0, 0, 17, BAR_VENT, lit)
            rect(t, 17, py, 3, ph, CAV)
            title_plate(t, 21, py, 4, ph, lit)

        def centre(t):
            title_plate(t, 0, py, 25, ph, lit)

        def right_end(t):
            title_plate(t, 0, py, 4, ph, lit)
            rect(t, 5, py, 3, ph, CAV)
            vent(t, 8, 0, 17, BAR_VENT, lit)

        def fill(t):
            vent(t, 0, 0, 25, BAR_VENT, lit)

        def right(t):
            vent(t, 0, 0, 12, BAR_VENT, lit)
            mini_button(t, 14, 3, "close", lit)
            rect(t, 24, 0, 1, 20, PL_LO)

        piece(0, left)
        piece(26, left_end)
        piece(52, centre)
        piece(78, right_end)
        piece(104, fill)
        piece(130, right)

    def bottom(w, grip, left_edge):
        t = new(w, 14)
        plastic(t, 0, 0, w, 14)
        rect(t, 0, 0, w, 1, PL_LO)
        rect(t, 0, 1, w, 1, PL_HI)
        rect(t, 0, 13, w, 1, PL_LO)
        if left_edge:
            rect(t, 0, 0, 1, 14, PL_HI)
        else:
            rect(t, w - 1, 0, 1, 14, PL_LO)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 10 - 3 * j
                    px(t, gx, gy, SILVER_DIM)
                    px(t, gx + 1, gy + 1, PL_LO)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = side_tile(w, h, outer_left, 2)
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        cell = (12, 12, 13) if lit else (17, 17, 18)
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            rect(a, x, y, w, 7, cell)
            draw_text(a, FONT5, c, x, y + 1, title_ink(lit))
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp, viscolor.txt, pledit.txt, readme.txt
# ------------------------------------------------------------------------------------------

GENEX_COLOURS = [
    GLASS,             # item background
    (110, 236, 214),   # item text
    (26, 26, 28),      # window background
    (214, 216, 220),   # button text
    (222, 224, 228),   # window text
    (62, 62, 66),      # dividers, sunken borders
    (22, 84, 76),      # selection bar
    (40, 40, 44),      # list header background
    (200, 202, 206),   # list header text
    (78, 78, 84),      # header frame, light
    (8, 8, 9),         # header frame, dark
    (52, 52, 56),      # header frame, pressed
    (26, 26, 28),      # header dead area
    (48, 48, 52),      # scrollbar
    (110, 110, 116),   # scrollbar 2
    (64, 64, 70),      # scrollbar pressed
    (150, 150, 156),   # scrollbar pressed 2
    (14, 14, 16),      # scrollbar dead area
]


def make_genex():
    a = new(256, 64)
    plastic(a, 0, 1, 256, 63)
    rect(a, 0, 0, 256, 1, PL)
    for i, c in enumerate(GENEX_COLOURS):
        px(a, 48 + 2 * i, 0, c)
    rubber_key(a, 0, 1, 47, 15, False)
    rubber_key(a, 0, 16, 47, 15, True)
    return a


VISCOLOR = (
    [(GLASS, "background"), (GHOST, "dots")]
    + [(ramp([(214, 255, 246), (130, 248, 226), (80, 220, 196), (44, 160, 144), (24, 96, 88)], i / 15),
        f"spectrum {i + 1}") for i in range(16)]
    + [((200, 255, 244), "oscilloscope 1"), ((130, 246, 222), "oscilloscope 2"), ((90, 214, 192), "oscilloscope 3"),
       ((60, 170, 152), "oscilloscope 4"), ((40, 120, 108), "oscilloscope 5"), ((236, 255, 250), "peaks")]
)

PLEDIT = dict(Normal="#5AE6CC", Current="#E0FFF8", NormalBG="#050C0C", SelectedBG="#18524A")


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in VISCOLOR:
            f.write(f"{r},{g},{b}, // {note}\n")
    p = PLEDIT
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={p['Normal']}\nCurrent={p['Current']}\nNormalBG={p['NormalBG']}\n"
                f"SelectedBG={p['SelectedBG']}\nMbBG={p['NormalBG']}\nMbFG={p['Normal']}\nFont=Arial\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            "Honda Accord - a skin in the style of a Honda Accord's dash: the 1990-93 Honda radio\n"
            "with its teal VFD, and the 1986-89 climate panel's sliders and keys.\n"
            "Honda wordmark (c) Honda Motor Co., Ltd.\n\n"
            "Drawn by a script (gen_skin.py): rectangles, bevels, noise and hand-made pixel fonts;\n"
            "the wordmark recoloured to the radio's silver print.\n"
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
        "monoster.bmp": make_monoster(main),
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
    # genex.bmp completed for real Winamp and WACUP (all 24 colours, readable text, Winamp's layout).
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
    """text.bmp's ink as the app picks it: the commonest colour of its first two rows that isn't
    within 96 (summed RGB) of the space cell's."""
    t = np.asarray(SHEETS["text"], dtype=np.int32)[:12]
    space = t[0, 150]
    flat = t.reshape(-1, 3)
    far = np.abs(flat - space).sum(1) > 96
    vals, counts = np.unique(flat[far], axis=0, return_counts=True)
    return tuple(int(v) for v in vals[counts.argmax()])


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
    # the title row (y 27-32) blanked with text.bmp's space, then the title as the app draws it:
    # 11px TrueType in text.bmp's ink, baseline under the row, clipped to y 22-39
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 27)
    box = img.crop((111, 22, 265, 40))
    ImageDraw.Draw(box).text((0, 33 - 22), state["title"], fill=text_ink(), font=tt_font(11), anchor="ls")
    img.paste(box, (111, 22))
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
                blit(img, g, (lx, 88 if lit else 96, lw, 7), x, 4 + 1)
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
    c0, c1 = np.array(GLASS, np.float32), np.array(VFD_MID, np.float32)
    col = c0 + (c1 - c0) * arr[..., :1]
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


PREVIEW_ROWS = [("Night Drive - Interstate 5", "4:12"), ("Slow Burn - Lantern Hours", "3:47"),
                ("Coastline - Highway One", "5:03"), ("Rearview - Afterglow", "2:58"),
                ("Cassette Side B - Tape Hiss", "6:21"), ("Field Notes - Warm Static", "3:33"),
                ("Overpass - Small Hours", "4:40"), ("Tollbooth - Exact Change", "3:09"),
                ("Long Winter - Defrost", "5:51"), ("Glowworm - Low Light", "4:05"),
                ("Parking Lot - Idle", "3:22")]


def preview():
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title="Night Drive - Honda Accord (Radio Edit)", bars=bars)
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
    # 4x crops for checking details
    os.makedirs(SCRATCH, exist_ok=True)
    m = preview_main(True, A)
    e = preview_eq(True, EA)
    for name, im, box in (("display", m, (8, 14, 270, 64)), ("sliders", m, (100, 48, 272, 84)),
                          ("keys", m, (0, 78, 275, 116)), ("titlebar", m, (0, 0, 275, 22)),
                          ("eq", e, (0, 0, 275, 116))):
        c = im.crop(box)
        c.resize((c.width * 4, c.height * 4), Image.NEAREST).save(os.path.join(SCRATCH, f"{T.name}-{name}-4x.png"))


def use_theme(name):
    global T, OUT, _rng
    T = THEMES[name]
    OUT = os.path.join(OUT_ROOT, name)
    os.makedirs(OUT, exist_ok=True)
    _rng = np.random.default_rng(T.seed)


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
