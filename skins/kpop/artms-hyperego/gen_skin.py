#!/usr/bin/python3
"""ARTMS Hyper-Ego: a personal, private classic Winamp 2.x fan skin, generated procedurally.

Based on skins/ember/gen_skin.py (same sheet layouts). High-key platinum/white chrome with
black as the hard accent and the cover's icy grey-blue iris for lit states, after ARTMS's
album "Hyper-Ego". The album cover's eye strips are the main and EQ windows' backdrops; the
ARTMS wordmark comes from an Objekt back template's ink. Writes the bitmaps and text files
into out/, zips them flat into ARTMS-Hyper-Ego.wsz, and draws preview.png (2x).
"""

import os
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
SRC = os.path.join(HERE, "source")
COVER = os.path.join(SRC, "eyes-cover.webp")
WORDMARK_INK = "/home/matt/gitea/ergosteur/objekts-archive/back_templates/Atom02/template-ink.png"
WSZ_NAME = "ARTMS-Hyper-Ego.wsz"

# ------------------------------------------------------------------------------------------
# Palette (names kept from Ember so the shared code reads the same; values are Hyper-Ego's)
# ------------------------------------------------------------------------------------------

BODY = (230, 232, 236)       # platinum white
BODY_2 = (240, 241, 244)
BODY_HI = (255, 255, 255)
BODY_LO = (150, 157, 168)    # cool grey shadow
SLOT = (208, 213, 220)       # recessed slots on the body
DISP = (224, 231, 237)       # frosted icy LCD
DISP_EDGE = (120, 128, 140)
INK = (14, 15, 18)           # the black accent
ICE = (159, 180, 196)        # the cover's iris blue-grey
ICE_HI = (196, 212, 224)
ICE_DEEP = (84, 112, 136)
AMBER = INK                  # "lit" ink on displays and controls
AMBER_HI = (0, 0, 0)
AMBER_DIM = (186, 196, 206)  # unlit display ink
AMBER_MID = (92, 104, 118)   # display labels
COPPER = ICE_DEEP
COPPER_HI = (40, 44, 52)
COPPER_LO = (172, 180, 192)
GREY_TXT = (118, 124, 134)
GREY_DIM = (160, 166, 176)
SEP = (255, 0, 255)          # gen.bmp letter separators (never shown)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    """Colour along a list of stops, t in 0..1."""
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


LEVEL = [(214, 220, 228), (184, 200, 214), ICE, (112, 140, 162), (60, 82, 104)]
TRACK_OFF = (200, 206, 214)  # unlit slider track

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


def raised(a, x, y, w, h, hi=BODY_HI, lo=BODY_LO):
    rect(a, x, y, w, 1, hi)
    rect(a, x, y, 1, h, hi)
    rect(a, x, y + h - 1, w, 1, lo)
    rect(a, x + w - 1, y, 1, h, lo)


def sunken(a, x, y, w, h, hi=BODY_HI, lo=BODY_LO):
    raised(a, x, y, w, h, lo, hi)


_rng = np.random.default_rng(1729)


def brushed(a, x, y, w, h, amp=3.0):
    """Adds a brushed-metal grain: horizontally smeared noise (wraps, so tiles stay seamless)."""
    n = _rng.normal(0, 1, (h, w))
    acc = np.zeros_like(n)
    for d in range(-4, 5):
        acc += np.roll(n, d, axis=1)
    acc /= 3.0
    acc += _rng.normal(0, 0.35, (h, w))
    a[y:y + h, x:x + w] += np.round(acc * amp).astype(np.int32)[:, :, None]


def body(a, x, y, w, h, col=BODY, amp=3.0):
    rect(a, x, y, w, h, col)
    brushed(a, x, y, w, h, amp)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


# ------------------------------------------------------------------------------------------
# Pixel fonts (all designed for this skin)
# ------------------------------------------------------------------------------------------

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

# 7-row squared techno letters, 2px stems, for "HYPER-EGO" (chamfered top-left / bottom-right corners),
# drawn slanted by techno_text(); our own lettering after the cover's logotype.
TECHNO = {
    "H": G("##..##", "##..##", "##..##", "######", "##..##", "##..##", "##..##"),
    "Y": G("##..##", "##..##", "##..##", ".#####", "....##", "....##", "#####."),
    "P": G(".#####", "##..##", "##..##", "#####.", "##....", "##....", "##...."),
    "E": G(".#####", "##....", "##....", "#####.", "##....", "##....", "######"),
    "R": G(".#####", "##..##", "##..##", "#####.", "##.##.", "##..##", "##..##"),
    "-": G("....", "....", "....", "####", "....", "....", "...."),
    "G": G(".#####", "##....", "##....", "##.###", "##..##", "##..##", "#####."),
    "O": G(".#####", "##..##", "##..##", "##..##", "##..##", "##..##", "#####."),
}
SLANT7 = [3, 2, 2, 1, 1, 0, 0]  # per-row shift right


def techno_w(s, gap=1):
    return sum(len(TECHNO[c][0]) for c in s) + gap * (len(s) - 1) + SLANT7[0]


def techno_text(a, s, x, y, col, gap=1, shadow=None):
    for c in s:
        g = TECHNO[c]
        for d, colour in (((1, 1), shadow), ((0, 0), col)):
            if colour is None:
                continue
            for r, row in enumerate(g):
                for k, ch in enumerate(row):
                    if ch == "#":
                        px(a, x + k + SLANT7[r] + d[0], y + r + d[1], colour)
        x += len(g[0]) + gap
    return x


_WORDMARK_CACHE = {}


def wordmark_alpha(h):
    """The ARTMS wordmark's ink as an alpha mask h pixels tall (float 0..1)."""
    if h not in _WORDMARK_CACHE:
        ink = Image.open(WORDMARK_INK).getchannel("A")
        sub = np.asarray(ink.crop((50, 200, 760, 420)))
        ys, xs = np.nonzero(sub > 20)
        box = (50 + xs.min(), 200 + ys.min(), 50 + xs.max() + 1, 200 + ys.max() + 1)
        crop = ink.crop(box)
        w = round(crop.width * h / crop.height)
        m = np.asarray(crop.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255
        _WORDMARK_CACHE[h] = np.clip((m - 0.12) * 1.45, 0, 1) ** 0.8   # crisper edges
    return _WORDMARK_CACHE[h]


def ink_mask(a, mask, x, y, col):
    h, w = mask.shape
    reg = a[y:y + h, x:x + w].astype(np.float32)
    m = mask[:, :, None]
    a[y:y + h, x:x + w] = np.round(reg * (1 - m) + np.array(col, np.float32) * m).astype(np.int32)


# ------------------------------------------------------------------------------------------
# The cover's eye strips (4 horizontal bands, 640x640 source)
# ------------------------------------------------------------------------------------------

STRIPS = [(0, 159), (160, 319), (320, 478), (479, 640)]


def cover_strip(i, w, h, focus_y=0.5, x0=0.0, x1=1.0, wash=0.35):
    """Strip i of the cover, cropped (x0..x1 of its width, height to keep the aspect around
    focus_y) and scaled to w x h, washed towards white by `wash`."""
    img = Image.open(COVER).convert("RGB")
    top, bot = STRIPS[i]
    left, right = int(640 * x0), int(640 * x1)
    sh = round((right - left) * h / w)
    sh = min(sh, bot - top)
    cy = top + (bot - top) * focus_y
    t = int(round(max(top, min(bot - sh, cy - sh / 2))))
    crop = img.crop((left, t, right, t + sh)).resize((w, h), Image.LANCZOS)
    arr = np.asarray(crop).astype(np.float32)
    grey = arr.mean(2, keepdims=True)
    arr = arr * 0.8 + grey * 0.2                       # a little cooler, less pink
    arr = arr * (1 - wash) + np.array([244, 246, 250], np.float32) * wash
    return np.round(arr).astype(np.int32)


def frost(a, x, y, w, h, amt=0.6, col=(240, 243, 247)):
    """White-washes a region (the frosted panels under controls)."""
    reg = a[y:y + h, x:x + w].astype(np.float32)
    a[y:y + h, x:x + w] = np.round(reg * (1 - amt) + np.array(col, np.float32) * amt).astype(np.int32)


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
# Shared pieces
# ------------------------------------------------------------------------------------------


def grill(a, x, y0, w, rows, lit):
    """The titlebars' thin rules: a black (unfocused: grey) hairline with a white line under it."""
    line = INK if lit else (178, 184, 194)
    shade = BODY_HI
    for r in rows:
        rect(a, x, y0 + r, w, 1, line)
        rect(a, x, y0 + r + 1, w, 1, shade)


def plate(a, x, y, w, lit, h=9):
    """A recessed nameplate for a title (rows y..y+h-1)."""
    rect(a, x, y + 1, w, h - 2, DISP if lit else (226, 228, 232))
    rect(a, x, y, w, 1, BODY_LO)
    rect(a, x, y + h - 1, w, 1, BODY_HI)


def plate_cap_left(a, x, y, lit, h=9):
    """4 columns: gap, light rim, dark rim, plate."""
    rect(a, x, y, 2, h, BODY)
    rect(a, x + 2, y, 1, h, BODY_LO)
    plate(a, x + 3, y, 1, lit, h)


def plate_cap_right(a, x, y, lit, h=9):
    plate(a, x, y, 1, lit, h)
    rect(a, x + 1, y, 1, h, BODY_HI)
    rect(a, x + 2, y, 2, h, BODY)


TITLE_LIT = INK
TITLE_DIM = (140, 146, 156)


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button."""
    face = (196, 202, 210) if pressed else (250, 251, 252)
    rect(a, x, y, 9, 9, face)
    if pressed:
        sunken(a, x, y, 9, 9, BODY_HI, (120, 128, 140))
    else:
        raised(a, x, y, 9, 9, BODY_HI, (128, 136, 148))
    ink = INK if (pressed or lit) else (150, 156, 166)
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        for dx, dy in [(3, 3), (4, 3), (5, 3), (3, 4), (4, 4), (5, 4), (3, 5), (4, 5), (5, 5)]:
            if (dx, dy) not in [(3, 3), (5, 3), (3, 5), (5, 5)]:
                px(a, X + dx, Y + dy, ink)
            else:
                px(a, X + dx, Y + dy, lerp(ink, face, 0.55))
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 2, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 2, ink)
        rect(a, X + 2, Y + 5, 5, 1, lerp(ink, face, 0.5))
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]

SCRIPT_FONT = "/usr/share/fonts/urw-base35/Z003-MediumItalic.otf"   # URW Z003 (AGPL + font exception)


def font_mask(text, path, size, stroke=0, gamma=0.75):
    """Renders text antialiased and returns its alpha mask cropped to the ink (float 0..1)."""
    f = ImageFont.truetype(path, size)
    im = Image.new("L", (size * len(text) + 40, size * 3), 0)
    ImageDraw.Draw(im).text((20, size), text, fill=255, font=f, stroke_width=stroke, stroke_fill=255)
    m = np.asarray(im).astype(np.float32) / 255
    ys, xs = np.nonzero(m > 0.04)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return np.clip(m, 0, 1) ** gamma


def cross(a, x, y, col, w=5, h=8, bar=1):
    """A Latin cross (the leggings' print): w wide, h tall, its arm at row h//4."""
    rect(a, x + (w - 2) // 2, y, 2, h, col)
    rect(a, x, y + h // 4, w, bar + 1 if w > 5 else bar, col)


def star(a, x, y, col):
    """A 7x7 four-point sparkle."""
    for d in range(-3, 4):
        px(a, x + 3 + d, y + 3, col)
        px(a, x + 3, y + 3 + d, col)
    for d in (-1, 1):
        px(a, x + 3 + d, y + 3 + d, col)
        px(a, x + 3 + d, y + 3 - d, col)


def clutter_bar(lit_letters):
    a = new(8, 43, BODY)
    rect(a, 0, 0, 8, 43, SLOT)
    sunken(a, 0, 0, 8, 43)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, ICE_HI)
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, INK if on else GREY_TXT)
    return a


def titlebar_base(w=275):
    a = new(w, 14, BODY)
    body(a, 0, 0, w, 14, (238, 240, 243), 1.2)
    for r in range(14):   # chrome: bright top, cooler bottom
        a[r, :] = np.clip(a[r, :] + int(10 - r * 1.6), 0, 255)
    rect(a, 0, 0, w, 1, BODY_HI)
    rect(a, 0, 0, 1, 14, BODY_HI)
    rect(a, w - 1, 0, 1, 14, BODY_LO)
    rect(a, 0, 13, w, 1, (196, 202, 210))
    return a


def main_titlebar(lit):
    a = titlebar_base()
    col = INK if lit else (150, 156, 166)
    wm = wordmark_alpha(8)
    word = "HYPER-EGO"
    gap = 7
    total = wm.shape[1] + gap + techno_w(word)
    x0 = (275 - total) // 2
    grill(a, 18, 0, x0 - 6 - 18, [6], lit)
    end = x0 + total
    grill(a, end + 6, 0, 240 - (end + 6), [6], lit)
    ink_mask(a, wm, x0, 3, col)
    rect(a, x0 + wm.shape[1] + 3, 3, 1, 8, ICE_DEEP if lit else (190, 196, 204))
    techno_text(a, word, x0 + wm.shape[1] + gap, 3, col)
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, BODY)
    body(a, 0, 0, 344, 87, BODY, 1)
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

# Slanted seven segments: the upper half sits one column right of the lower half.
SEG = {
    "a": [(0, c) for c in range(3, 8)],
    "g": [(6, c) for c in range(2, 7)],
    "d": [(12, c) for c in range(1, 6)],
    "f": [(r, c) for r in range(1, 6) for c in (2, 3)],
    "b": [(r, c) for r in range(1, 6) for c in (7, 8)],
    "e": [(r, c) for r in range(7, 12) for c in (0, 1)],
    "c": [(r, c) for r in range(7, 12) for c in (5, 6)],
}
SEG_GHOST = (210, 219, 227)
DIGIT_SEGS = {
    0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc",
    5: "afgcd", 6: "afgedc", 7: "abc", 8: "abcdefg", 9: "abcdfg",
}


def seven_seg(a, x, y, lit_segs, ghost=True):
    rect(a, x, y, 9, 13, DISP)
    for s, cells in SEG.items():
        if s not in lit_segs and ghost:
            for r, c in cells:
                px(a, x + c, y + r, SEG_GHOST)
    for s, cells in SEG.items():
        if s in lit_segs:
            for r, c in cells:
                px(a, x + c, y + r, INK)


def display_box(a, x, y, w, h):
    """A frosted LCD window: grey hairline rim (top/left darker), white lip below."""
    rect(a, x, y, w, h, DISP)
    rect(a, x - 1, y - 1, w + 2, 1, (104, 112, 124))
    rect(a, x - 1, y - 1, 1, h + 2, (104, 112, 124))
    rect(a, x - 1, y + h, w + 2, 1, BODY_HI)
    rect(a, x + w, y - 1, 1, h + 2, BODY_HI)
    rect(a, x, y, w, 1, (198, 208, 218))
    rect(a, x, y, 1, h, (198, 208, 218))


def iris_emblem(a, x, y, lit=True):
    """13x13: an icy iris with the cover's X reflection."""
    for r in range(13):
        for c in range(13):
            d = ((r - 6) ** 2 + (c - 6) ** 2) ** 0.5
            if d <= 6.4:
                if d > 5.4:
                    col = INK
                elif d > 2.6:
                    t = (d - 2.6) / 2.8
                    col = lerp(ICE_HI, ICE_DEEP, t) if lit else lerp((220, 222, 226), (160, 166, 176), t)
                else:
                    col = (40, 34, 34)
                px(a, x + c, y + r, col)
    for i in range(-2, 3):
        px(a, x + 6 + i, y + 6 + i, (250, 252, 255))
        px(a, x + 6 + i, y + 6 - i, (250, 252, 255))


TRAY = (241, 243, 246)


def make_main():
    a = new(275, 116, BODY)
    body(a, 0, 0, 275, 116, BODY, 1.2)
    # the cover's third strip (the iced irises with the X), across the body, faded in and out
    eh = 66
    eyes = cover_strip(2, 275, eh, focus_y=0.58, x0=0.03, x1=0.97, wash=0.15)  # below the logotype
    y0 = 46
    alpha = np.ones((eh, 275), np.float32)
    for r in range(14):
        alpha[r, :] *= r / 14
        alpha[eh - 1 - r, :] *= r / 14
    reg = a[y0:y0 + eh].astype(np.float32)
    a[y0:y0 + eh] = np.round(reg * (1 - alpha[..., None]) + eyes * alpha[..., None]).astype(np.int32)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # left display: indicator, time, analyzer
    display_box(a, 21, 20, 84, 42)
    for x in (48, 60, 78, 90):
        seven_seg(a, x, 26, "")
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, INK)
    rect(a, 24, 60, 76, 1, (204, 214, 222))

    # right display
    display_box(a, 109, 21, 159, 15)
    display_box(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, AMBER_MID)
    draw_text(a, TINY, "KHZ", 169, 44, AMBER_MID)

    # frosted seats under the sliders and the seek bar (the sprites copy these)
    frost(a, 107, 57, 68, 13, 0.55)
    frost(a, 177, 57, 38, 13, 0.55)
    frost(a, 15, 71, 251, 12, 0.35)

    # transport trays: flat white plates with a hairline rim
    for x, y, w, h in ((15, 87, 145, 20), (163, 88, 77, 17)):
        rect(a, x, y, w, h, TRAY)
        rect(a, x, y, w, 1, (176, 184, 194))
        rect(a, x, y, 1, h, (176, 184, 194))
        rect(a, x, y + h - 1, w, 1, BODY_HI)
        rect(a, x + w - 1, y, 1, h, BODY_HI)

    # the About spot: a cross (the leggings' print) and the iris
    x, y, w, h = 243, 88, 28, 20
    rect(a, x, y, w, h, TRAY)
    rect(a, x, y, w, 1, (176, 184, 194))
    rect(a, x, y, 1, h, (176, 184, 194))
    rect(a, x, y + h - 1, w, 1, BODY_HI)
    rect(a, x + w - 1, y, 1, h, BODY_HI)
    cross(a, 245, 92, INK, w=6, h=11)
    iris_emblem(a, 255, 92)
    # a black hairline along the bottom
    rect(a, 4, 111, 267, 1, INK)
    rect(a, 4, 112, 267, 1, BODY_HI)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36): glossy white pills, black glyphs
# ------------------------------------------------------------------------------------------


def button_face(a, x, y, w, h, pressed, corner=TRAY):
    if pressed:
        for r in range(h):
            rect(a, x, y + r, w, 1, lerp((178, 186, 196), (206, 212, 220), r / max(1, h - 1)))
        rect(a, x, y, w, 1, (92, 100, 112))
        rect(a, x, y, 1, h, (92, 100, 112))
        rect(a, x + 1, y + 1, w - 2, 1, (160, 168, 180))
        rect(a, x + w - 1, y, 1, h, (120, 128, 140))
        rect(a, x, y + h - 1, w, 1, (120, 128, 140))
    else:
        top, mid, bot = (255, 255, 255), (242, 244, 247), (214, 220, 228)
        for r in range(h):
            t = r / max(1, h - 1)
            rect(a, x, y + r, w, 1, lerp(top, mid, t * 2) if t < 0.5 else lerp((230, 234, 239), bot, (t - 0.5) * 2))
        rect(a, x, y, w, 1, (140, 148, 160))
        rect(a, x, y, 1, h, (140, 148, 160))
        rect(a, x + w - 1, y, 1, h, (112, 120, 132))
        rect(a, x, y + h - 1, w, 1, (112, 120, 132))
        rect(a, x + 1, y + 1, w - 2, 1, BODY_HI)
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, corner)


def tri_right(a, x, y, h, col):
    """Solid right-pointing triangle, h tall (odd), tip to the right."""
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x, y + r, n, 1, col)


def tri_left(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x + half + 1 - n, y + r, n, 1, col)


def transport_icon(a, kind, x, y, w, h, pressed):
    ink = INK
    shadow = None if pressed else BODY_HI
    o = 1 if pressed else 0
    cx, cy = x + w // 2 + o, y + h // 2 + o

    def both(fn):
        if shadow:
            fn(1, shadow)
        fn(0, ink)

    if kind == "previous":
        both(lambda d, c: (rect(a, cx - 6 + d, cy - 3 + d, 2, 7, c), tri_left(a, cx - 4 + d, cy - 3 + d, 7, c),
                           tri_left(a, cx + d, cy - 3 + d, 7, c)))
    elif kind == "play":
        both(lambda d, c: tri_right(a, cx - 2 + d, cy - 4 + d, 9, c))
    elif kind == "pause":
        both(lambda d, c: (rect(a, cx - 4 + d, cy - 3 + d, 3, 7, c), rect(a, cx + 1 + d, cy - 3 + d, 3, 7, c)))
    elif kind == "stop":
        both(lambda d, c: rect(a, cx - 3 + d, cy - 3 + d, 7, 7, c))
    elif kind == "next":
        both(lambda d, c: (tri_right(a, cx - 5 + d, cy - 3 + d, 7, c), tri_right(a, cx - 1 + d, cy - 3 + d, 7, c),
                           rect(a, cx + 3 + d, cy - 3 + d, 2, 7, c)))
    elif kind == "eject":
        def ej(d, c):
            for r in range(4):
                rect(a, cx - 1 - r + d, cy - 4 + r + d, 2 * r + 3, 1, c)
            rect(a, cx - 4 + d, cy + 1 + d, 9, 2, c)
        both(ej)


def make_cbuttons():
    a = new(136, 36, TRAY)
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18)]
    for kind, x, w, h in specs:
        for pressed, y in ((False, 0), (True, 18)):
            button_face(a, x, y, w, h, pressed)
            transport_icon(a, kind, x, y, w, h, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        button_face(a, 114, y, 22, 16, pressed)
        transport_icon(a, "eject", 114, y, 22, 16, pressed)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle(a, x, y, w, h, label, on, pressed, led="under", corner=TRAY):
    button_face(a, x, y, w, h, pressed, corner)
    o = 1 if pressed else 0
    ink = INK if on else ((96, 102, 112) if pressed else (128, 134, 144))
    tw = text_w(TINY, label)
    if led == "under":
        tx = x + (w - tw) // 2 + o
        ty = y + 3 + o
        draw_text(a, TINY, label, tx, ty, ink)
        lc = ICE_DEEP if on else (200, 206, 214)
        rect(a, x + 4 + o, y + h - 5 + o, w - 9, 1, lc)
        if on:
            rect(a, x + 4 + o, y + h - 4 + o, w - 9, 1, ICE)
    else:  # LED dot at the left
        tx = x + 7 + (w - 9 - tw) // 2 + o
        ty = y + (h - 5) // 2 + o
        draw_text(a, TINY, label, tx, ty, ink)
        lc = ICE_DEEP if on else (196, 202, 210)
        rect(a, x + 3 + o, y + h // 2 - 1 + o, 2, 2, lc)


def make_shufrep():
    a = new(92, 85, TRAY)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        toggle(a, 0, y, 28, 15, "REPEAT", on, pressed)
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        toggle(a, x, 61, 23, 12, label, False, pressed, led="dot", corner=(236, 238, 242))
        toggle(a, x, 73, 23, 12, label, True, pressed, led="dot", corner=(236, 238, 242))
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp (56 x 24), playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, DISP)
    for y, on in ((0, True), (12, False)):
        col = INK if on else AMBER_DIM
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, DISP)
    tri_right(a, 2, 1, 7, INK)
    rect(a, 9 + 2, 1, 2, 7, INK)
    rect(a, 9 + 5, 1, 2, 7, INK)
    rect(a, 18 + 2, 2, 5, 5, INK)
    rect(a, 36, 0, 3, 9, DISP)
    rect(a, 39 + 1, 3, 1, 3, ICE_DEEP)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, DISP)
    for n in range(10):
        seven_seg(a, 9 * n, 0, DIGIT_SEGS[n])
    seven_seg(a, 90, 0, "")
    if ex:
        rect(a, 99, 0, 9, 13, DISP)
        for r, c in SEG["g"]:
            px(a, 99 + c, r, INK)
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
            draw_text(a, FONT5, key, col * 5, row * 6, INK)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def chrome_thumb(a, x, y, w, h, selected, grip="v"):
    top, bot = ((232, 240, 247), ICE) if selected else ((255, 255, 255), (206, 212, 220))
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(top, bot, r / max(1, h - 1)))
    rect(a, x, y, w, 1, BODY_HI)
    rect(a, x, y, 1, h, BODY_HI)
    rect(a, x + w - 1, y, 1, h, (58, 64, 74))
    rect(a, x, y + h - 1, w, 1, (58, 64, 74))
    px(a, x, y, (150, 156, 166))
    cx = x + w // 2
    if grip == "v":
        for gx in (cx - 2, cx, cx + 2):
            rect(a, gx, y + 3, 1, h - 6, INK)
    else:
        for gy in (y + h // 2 - 2, y + h // 2, y + h // 2 + 2):
            rect(a, x + 3, gy, w - 6, 1, INK)


copper_thumb = chrome_thumb


def make_posbar(main):
    a = new(307, 10, BODY)
    a[0:10, 0:248] = main[72:82, 16:264]
    rect(a, 0, 4, 248, 1, (110, 118, 130))
    rect(a, 0, 5, 248, 1, BODY_HI)
    for x in range(0, 248, 31):
        rect(a, x, 3, 1, 3, (110, 118, 130))
    chrome_thumb(a, 248, 0, 29, 10, False)
    chrome_thumb(a, 278, 0, 29, 10, True)
    return a


def slider_thumbs(a):
    chrome_thumb(a, 0, 422, 14, 11, True)
    chrome_thumb(a, 15, 422, 14, 11, False)


TRACK_BG = (246, 248, 250)


def make_volume(main):
    a = new(68, 433, BODY)
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        rect(a, 1, y + 3, 66, 7, TRACK_BG)
        sunken(a, 1, y + 3, 66, 7, BODY_HI, (128, 136, 148))
        level = (i + 1) / 28
        fill_to = 7 + round(level * 54)
        colour = ramp(LEVEL, level)
        for x in range(2, 66):
            hgt = 1 + round(4 * (x - 2) / 63)
            top = y + 9 - hgt
            rect(a, x, top, 1, hgt, colour if x < fill_to else TRACK_OFF)
        rect(a, 0, y + 13, 68, 2, BODY)
    slider_thumbs(a)
    return a


def make_balance(main):
    a = new(68, 433, BODY)
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        rect(a, 10, y + 3, 36, 7, TRACK_BG)
        sunken(a, 10, y + 3, 36, 7, BODY_HI, (128, 136, 148))
        t = i / 27
        colour = (150, 158, 170) if i == 0 else ramp(LEVEL[1:], t)
        reach = round(12 * t)
        for x in range(11, 45):
            d = abs(x - 28)
            hgt = 1 + round(4 * min(d, 16) / 16)
            top = y + 9 - hgt
            rect(a, x, top, 1, hgt, colour if d <= max(1, reach) else TRACK_OFF)
        rect(a, 28, y + 2, 1, 2, INK)
        rect(a, 9, y + 13, 38, 2, BODY)
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = titlebar_base()
    title = "EQUALIZER"
    col = INK if lit else (150, 156, 166)
    wm = wordmark_alpha(7)
    tw = text_w(FONT5, title)
    total = wm.shape[1] + 7 + tw
    x0 = (275 - total) // 2
    grill(a, 6, 0, x0 - 6 - 6, [6], lit)
    grill(a, x0 + total + 6, 0, 260 - (x0 + total + 6), [6], lit)
    ink_mask(a, wm, x0, 3, col)
    rect(a, x0 + wm.shape[1] + 3, 3, 1, 7, ICE_DEEP if lit else (190, 196, 204))
    draw_text(a, FONT5, title, x0 + wm.shape[1] + 7, 4, col)
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    """14x63 slot whose lit column rises with the value (n of 0..27)."""
    rect(a, x, y, 14, 63, (240, 242, 245))
    sunken(a, x, y, 14, 63, BODY_HI, (150, 158, 170))
    rect(a, x + 4, y + 2, 5, 59, TRACK_BG)
    sunken(a, x + 4, y + 2, 5, 59, BODY_HI, (120, 128, 140))
    v = n / 27
    centre = round((1 - v) * 51) + 5
    colour = ramp(LEVEL[1:], v)
    for r in range(3, 60):
        rect(a, x + 5, y + r, 3, 1, colour if r >= centre else (214, 220, 228))
    rect(a, x + 1, y + 30, 2, 1, INK)
    rect(a, x + 11, y + 30, 2, 1, INK)


def make_eqmain():
    a = new(275, 315, BODY)
    body(a, 0, 0, 275, 315, BODY, 1.2)
    # the cover's four eye strips stacked across the body, white seams between, washed out
    focus = [0.52, 0.5, 0.5, 0.46]
    y = 15
    for i in range(4):
        band = cover_strip(i, 271, 24, focus_y=focus[i], wash=0.3)
        a[y:y + 24, 2:273] = band
        y += 25
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = eq_titlebar(True)
    sunken(a, 85, 16, 115, 21)
    # slider bay: frosted, so the strips only glimmer between the sliders
    frost(a, 16, 36, 245, 68, 0.45)
    rect(a, 16, 36, 245, 1, (150, 158, 170))
    rect(a, 16, 36, 1, 68, (150, 158, 170))
    rect(a, 16, 103, 245, 1, BODY_HI)
    rect(a, 260, 36, 1, 68, BODY_HI)
    rect(a, 39, 37, 1, 66, INK)
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        rect(a, 43, yy - 1, 30, 7, (246, 248, 250))
        text_center(a, TINY, lbl, 58, yy, INK)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    # labels on a white band
    rect(a, 2, 104, 271, 8, (246, 248, 250))
    text_center(a, TINY, "PREAMP", 28, 106, INK)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, INK)
    rect(a, 2, 112, 271, 3, BODY)
    rect(a, 4, 113, 267, 1, INK)
    # small plates behind the ON/AUTO and PRESETS buttons and the free top spots
    rect(a, 2, 15, 83, 20, (240, 242, 245))
    rect(a, 201, 15, 72, 20, (240, 242, 245))
    star(a, 75, 20, INK)
    cross(a, 205, 19, INK, w=5, h=10)

    # under the window: buttons
    mini_button(a, 0, 125, "close", True, pressed=True)
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        toggle(a, x, 119, w, 12, label, on, pressed, led="dot", corner=(240, 242, 245))
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    chrome_thumb(a, 0, 164, 11, 11, False, grip="h")
    chrome_thumb(a, 0, 176, 11, 11, True, grip="h")
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        button_face(a, 224, y, 44, 12, pressed, corner=(240, 242, 245))
        o = 1 if pressed else 0
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 3 + o, INK)
    # graph
    rect(a, 0, 294, 113, 19, DISP)
    for x in range(0, 113, 12):
        for yy in range(1, 19, 2):
            px(a, 2 + x, 294 + yy, (200, 210, 220))
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, (176, 188, 200))
    for r in range(19):
        px(a, 115, 294 + r, ramp([INK, ICE_DEEP, INK], r / 18))
    for x in range(113):
        px(a, x, 314, ICE_DEEP if x % 3 != 2 else DISP)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

BAR20_GRILL = [8]
PLATE_Y = 3


def bar20(w, lit):
    a = new(w, 20, BODY)
    body(a, 0, 0, w, 20, (238, 240, 243), 1.2)
    for r in range(20):
        a[r, :] = np.clip(a[r, :] + int(8 - r * 0.9), 0, 255)
    rect(a, 0, 0, w, 1, BODY_HI)
    return a


def make_pledit():
    a = new(280, 186, BODY)
    body(a, 0, 0, 280, 186, BODY, 1.2)
    script = font_mask("Hyper-Ego", SCRIPT_FONT, 17, gamma=0.6)
    for lit, y in ((True, 0), (False, 21)):
        col = INK if lit else (150, 156, 166)
        # top tile
        t = bar20(25, lit)
        grill(t, 0, 0, 25, BAR20_GRILL, lit)
        rect(t, 0, 19, 25, 1, BODY_LO)
        a[y:y + 20, 127:152] = t
        # top-left corner: a small cross, then the rule
        t = bar20(25, lit)
        rect(t, 0, 0, 1, 20, BODY_HI)
        cross(t, 4, 4, col, w=5, h=9)
        grill(t, 12, 0, 13, BAR20_GRILL, lit)
        rect(t, 11, 19, 14, 1, BODY_LO)
        rect(t, 11, 14, 1, 6, BODY_LO)
        a[y:y + 20, 0:25] = t
        # title: "Hyper-Ego" in script
        t = bar20(100, lit)
        sh, sw = script.shape
        sx = (100 - sw) // 2
        grill(t, 0, 0, sx - 4, BAR20_GRILL, lit)
        grill(t, sx + sw + 4, 0, 100 - (sx + sw + 4), BAR20_GRILL, lit)
        ink_mask(t, script, sx, max(1, (19 - sh) // 2), col)
        rect(t, 0, 19, 100, 1, BODY_LO)
        a[y:y + 20, 26:126] = t
        # top-right corner: close button, the scrollbar groove's top
        t = bar20(25, lit)
        rect(t, 24, 0, 1, 20, BODY_LO)
        grill(t, 0, 0, 12, BAR20_GRILL, lit)
        mini_button(t, 14, 3, "close", lit)
        rect(t, 0, 19, 6, 1, BODY_LO)
        rect(t, 5, 13, 1, 7, BODY_HI)
        rect(t, 9, 14, 10, 6, SLOT)
        rect(t, 9, 14, 10, 1, BODY_LO)
        rect(t, 9, 14, 1, 6, BODY_LO)
        rect(t, 18, 14, 1, 6, BODY_HI)
        a[y:y + 20, 153:178] = t

    # left side tile
    t = new(12, 29)
    body(t, 0, 0, 12, 29, BODY, 1.2)
    rect(t, 0, 0, 1, 29, BODY_HI)
    rect(t, 11, 0, 1, 29, BODY_LO)
    rect(t, 4, 0, 1, 29, INK)
    a[42:71, 0:12] = t
    # right side tile: list edge, scrollbar groove at 5..12, outer edge
    t = new(20, 29)
    body(t, 0, 0, 20, 29, BODY, 1.2)
    rect(t, 0, 0, 1, 29, BODY_HI)
    rect(t, 19, 0, 1, 29, BODY_LO)
    rect(t, 4, 0, 10, 29, SLOT)
    rect(t, 4, 0, 1, 29, BODY_LO)
    rect(t, 13, 0, 1, 29, BODY_HI)
    rect(t, 8, 0, 2, 29, (190, 196, 206))
    rect(t, 16, 0, 1, 29, INK)
    a[42:71, 31:51] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        chrome_thumb(a, x, 53, 8, 18, sel, grip="h")

    def bottom_base(w):
        t = new(w, 38)
        body(t, 0, 0, w, 38, BODY, 1.2)
        rect(t, 0, 0, w, 1, BODY_HI)
        rect(t, 0, 37, w, 1, BODY_LO)
        rect(t, 0, 35, w, 1, INK)
        rect(t, 0, 36, w, 1, BODY_HI)
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, BODY_HI)
    rect(t, 11, 0, 1, 1, BODY_LO)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        button_face(t, bx, 8, 22, 18, False, corner=BODY)
        text_center(t, TINY, lbl, bx + 11, 15, INK)
    # a block mark under the buttons: the wordmark, small
    wm = wordmark_alpha(6)
    rect(t, 12, 27, 112, 8, BODY)
    ink_mask(t, wm, 15, 28, INK)
    star(t, 15 + wm.shape[1] + 4, 27, INK)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, BODY_LO)
    display_box(t, 6, 9, 56, 8)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        button_face(t, bx, 22, 10, 10, False, corner=BODY)
        mini_transport_icon(t, kind, bx, 22)
    display_box(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, AMBER_MID)
    rect(t, 84, 22 + 5, 1, 1, AMBER_MID)
    button_face(t, 106, 8, 22, 18, False, corner=BODY)
    text_center(t, TINY, "LIST", 117, 15, INK)
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx, gy, INK)
            px(t, gx + 1, gy + 1, BODY_HI)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


def mini_transport_icon(a, kind, x, y):
    ink = INK
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
    a = new(194, 109, BODY)
    body(a, 0, 0, 194, 109, BODY, 1.2)
    for lit, y in ((True, 0), (False, 21)):
        col = INK if lit else (150, 156, 166)

        def piece(px0, fn):
            t = bar20(25, lit)
            fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 1, 20, BODY_HI)
            cross(t, 4, 4, col, w=5, h=9)
            grill(t, 12, 0, 13, BAR20_GRILL, lit)

        def left_end(t):
            grill(t, 0, 0, 16, BAR20_GRILL, lit)
            plate_cap_left(t, 17, PLATE_Y, lit)
            plate(t, 21, PLATE_Y, 4, lit)

        def centre(t):
            plate(t, 0, PLATE_Y, 25, lit)

        def right_end(t):
            plate(t, 0, PLATE_Y, 4, lit)
            plate_cap_right(t, 4, PLATE_Y, lit)
            grill(t, 9, 0, 16, BAR20_GRILL, lit)

        def fill(t):
            grill(t, 0, 0, 25, BAR20_GRILL, lit)

        def right(t):
            grill(t, 0, 0, 12, BAR20_GRILL, lit)
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
        body(t, 0, 0, w, 14, BODY, 1.2)
        rect(t, 0, 13, w, 1, BODY_LO)
        rect(t, 0, 9, w, 1, INK)
        rect(t, 0, 10, w, 1, BODY_HI)
        if left_edge:
            rect(t, 0, 0, 1, 14, BODY_HI)
        else:
            rect(t, w - 1, 0, 1, 14, BODY_LO)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 7 - 3 * j
                    px(t, gx, gy, INK)
                    px(t, gx + 1, gy + 1, BODY_HI)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        body(t, 0, 0, w, h, BODY, 1.2)
        if outer_left:
            rect(t, 0, 0, 1, h, BODY_HI)
            rect(t, 4, 0, 1, h, INK)
        else:
            rect(t, w - 1, 0, 1, h, BODY_LO)
            rect(t, w - 5, 0, 1, h, INK)
        a[42:42 + h, x:x + w] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: each row starts at x 1, letters in their own cells, 1px separators of x 0's colour
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            rect(a, x, y, w, 7, DISP if lit else (226, 228, 232))
            draw_text(a, FONT5, c, x, y + 1, TITLE_LIT if lit else TITLE_DIM)
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------

GENEX_COLOURS = [
    (244, 245, 247),   # item background
    (42, 44, 48),      # item text
    (230, 232, 236),   # window background
    (14, 15, 18),      # button text
    (14, 15, 18),      # window text
    (176, 182, 192),   # dividers, sunken borders
    (201, 214, 224),   # selection bar
    (220, 224, 230),   # list header background
    (14, 15, 18),      # list header text
    (255, 255, 255),   # header frame, light
    (140, 148, 160),   # header frame, dark
    (159, 180, 196),   # header frame, pressed
    (230, 232, 236),   # header dead area
    (212, 217, 224),   # scrollbar
    (159, 180, 196),   # scrollbar 2
    (190, 196, 204),   # scrollbar pressed
    (84, 112, 136),    # scrollbar pressed 2
    (226, 228, 232),   # scrollbar dead area
]


def make_genex():
    a = new(256, 64, BODY)
    body(a, 0, 1, 256, 63, BODY, 1.2)
    rect(a, 0, 0, 256, 1, BODY)
    for i, c in enumerate(GENEX_COLOURS):
        px(a, 48 + 2 * i, 0, c)
    button_face(a, 0, 1, 47, 15, False, corner=BODY)
    button_face(a, 0, 16, 47, 15, True, corner=BODY)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------

VISCOLOR = (
    [(DISP, "background"), ((204, 214, 222), "dots")]
    + [(ramp([INK, (36, 50, 66), ICE_DEEP, (124, 150, 170), ICE], i / 15),
        f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}") for i in range(16)]
    + [(INK, "oscilloscope 1"), ((36, 44, 56), "oscilloscope 2"), ((62, 82, 104), "oscilloscope 3"),
       (ICE_DEEP, "oscilloscope 4"), ((120, 146, 166), "oscilloscope 5"), (INK, "peaks")]
)


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in VISCOLOR:
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write("[Text]\nNormal=#2A2C30\nCurrent=#000000\nNormalBG=#F4F5F7\nSelectedBG=#C9D6E0\n"
                "MbBG=#F4F5F7\nMbFG=#2A2C30\nFont=Arial\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n", encoding="utf-8") as f:
        f.write("ARTMS Hyper-Ego — a personal fan skin. ARTMS logo, album art and photos © MODHAUS; "
                "for private use only.\n")


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
    for name, arr in sheets.items():
        SHEETS[name[:-4]] = save(arr, name)
    write_text_files()
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "readme.txt"]
    wsz = os.path.join(HERE, WSZ_NAME)
    with zipfile.ZipFile(wsz, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(os.path.join(OUT, n), n)
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
    # eq / pl toggles
    for name, x0, on in (("eq", 0, state["eq"]), ("pl", 23, state["pl"])):
        pressed = state["pressed"] == name
        sx = x0 + (46 if pressed else 0)
        blit(img, S["shufrep"], (sx, 73 if on else 61, 23, 12), 219 + x0, 58)
    # clutter
    blit(img, S["titlebar"], (304, 0, 8, 43), 10, 22)
    spr = {"O": (304, 47, 8, 8, 3), "A": (312, 55, 8, 7, 11), "I": (320, 62, 8, 7, 18), "D": (328, 69, 8, 8, 25),
           "V": (336, 77, 8, 7, 33)}
    for L in state["clutter"]:
        x, y, w, h, oy = spr[L]
        blit(img, S["titlebar"], (x, y, w, h), 10, 22 + oy)
    # shuffle/repeat
    for name, x0, w, on, dst in (("shuffle", 28, 47, state["shuffle"], 164), ("repeat", 0, 28, state["repeat"], 210)):
        row = (2 if on else 0) + (1 if state["pressed"] == name else 0)
        blit(img, S["shufrep"], (x0, row * 15, w, 15), dst, 89)
    blit(img, S["playpaus"], (0 if state["playing"] else 9, 0, 9, 9), 26, 28)
    blit(img, S["monoster"], (29, 12 if state["stereo"] else 0, 27, 12), 212, 41)
    blit(img, S["monoster"], (0, 0 if state["stereo"] else 12, 29, 12), 239, 41)
    # posbar
    blit(img, S["posbar"], (0, 0, 248, 10), 16, 72)
    tl = round(state["pos"] * 219)
    blit(img, S["posbar"], (278 if state["seek"] else 248, 0, 29, 10), 16 + tl, 72)
    # volume
    v = state["volume"]
    idx = max(0, round(v / 100 * 28) - 1)
    blit(img, S["volume"], (0, idx * 15, 68, 13), 107, 57)
    blit(img, S["volume"], (0 if state["vdrag"] else 15, 422, 14, 11), 107 + round(v / 100 * 54), 58)
    b = state["balance"]
    idx = int(abs(b) / 100 * 27)
    blit(img, S["balance"], (9, idx * 15, 38, 13), 177, 57)
    blit(img, S["balance"], (15, 422, 14, 11), 177 + round((b + 100) / 200 * 24), 58)
    # time
    secs = state["time"]
    m, s = secs // 60, secs % 60
    nums = S["nums_ex"]
    if state["remaining"]:
        blit(img, nums, (99, 0, 9, 13), 38, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    # title: the space cell across the box, then the title (the app uses a TrueType font; text.bmp here)
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    draw_bitmap_text(img, state["title"][:30], 111, 24)
    draw_bitmap_text(img, "192", 111, 43)
    draw_bitmap_text(img, "44", 156, 43)
    # analyzer
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=(0xF4, 0xF5, 0xF7))
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 9)
    except OSError:
        font = ImageFont.load_default()
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=(0xC9, 0xD6, 0xE0))
        col = (0, 0, 0) if i == 1 else (0x2A, 0x2C, 0x30)
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
    # the album art: the cover itself
    pic = Image.open(COVER).convert("RGB").resize((w - 22, h - 34), Image.LANCZOS)
    img.paste(pic, (11, 20))
    return img


def preview():
    rows = [(f"ARTMS - Track {n:02d}", f"{2 + n % 3}:{(17 * n) % 60:02d}") for n in range(1, 12)]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title="ARTMS - HYPER-EGO  ***", bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="PAUSED: ARTMS - TRACK 05", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
