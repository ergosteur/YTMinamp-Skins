#!/usr/bin/python3
"""Nortel Norstar M7310: classic Winamp 2.x skins in the style of the Meridian Norstar M7310
office phone, in its charcoal and ash colourways, generated procedurally.

Based on skins/ember/gen_skin.py (whose sheet layouts it keeps), by way of the sibling
devices/honda-accord generator's theme scaffold. The main window is the phone's face: the
grey-green dot-matrix LCD in its dark bezel (time, title, kbps/kHz, analyzer; dark pixels on the
pale glass), the display's soft keys for EQ / PL, the volume rocker as the volume slider, the red
Hold and Rls keys for pause and stop, a sage-green Line key for play, grey keys elsewhere with the
phone's LCD triangle indicators beside the toggles, the message-waiting lamp in the About spot.
The titlebars are the speaker grille's slots; window titles sit on the memory keys' paper label
strips, and the playlist is one. The "meridian" logo (source/meridian-logo.png) is the main
titlebar's wordmark, its rule running out towards the buttons; the NORTEL mark
(source/nortel-logo.png) is small on the body. Both are loaded at build time, masked, scaled and
painted in each theme's print colour. Private use only.

    /usr/bin/python3 -I gen_skin.py [m7310-charcoal m7310-ash]   (no argument builds them all)
    /usr/bin/python3 -I gen_skin.py --list

Per theme: the bitmaps and text files in out/<theme>/, zipped flat into <Name>.wsz beside this
file, preview-<theme>.png (the windows assembled from the sprites the way the app does, 2x), and
4x detail crops in out/scratch/.
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
SOURCE = os.path.join(HERE, "source")
OUT_ROOT = os.path.join(HERE, "out")
SCRATCH = os.path.join(OUT_ROOT, "scratch")
OUT = None
T = None
SEP = (255, 0, 255)

# ------------------------------------------------------------------------------------------
# Themes: one layout, two plastics. Colours sampled from the reference photos (source/).
# ------------------------------------------------------------------------------------------

THEMES = {
    "m7310-charcoal": SimpleNamespace(
        name="m7310-charcoal", title="Nortel Norstar M7310", wsz="Nortel-Norstar-M7310.wsz", seed=7310,
        colourway="charcoal",
        BODY=(46, 46, 47), BODY_HI=(76, 76, 78), BODY_LO=(18, 18, 19), SLOT=(13, 13, 14), SLOT_LIP=(66, 66, 68),
        BEZEL=(60, 61, 63), BEZEL_HI=(88, 89, 92), BEZEL_LO=(26, 26, 28), RIB=(96, 97, 100),
        KEY=(160, 160, 156), KEY_HI=(206, 206, 202), KEY_LO=(104, 104, 101), KEY_INK=(40, 40, 40),
        RED=(222, 96, 76), RED_HI=(250, 156, 136), RED_LO=(148, 52, 40), RED_INK=(64, 20, 14),
        GREEN=(128, 166, 150), GREEN_HI=(176, 206, 194), GREEN_LO=(82, 114, 102), GREEN_INK=(26, 44, 38),
        PAPER=(220, 214, 198), PAPER_LO=(176, 170, 154), PAPER_DIM=(150, 146, 136),
        GLASS=(182, 196, 185), INK=(34, 40, 36),
        PRINT=(184, 184, 180), PRINT_DIM=(120, 120, 118), PRINT_UNLIT=(104, 104, 104),
        WELL=(20, 20, 21), NUB=(58, 59, 61), NUB_HI=(108, 109, 112),
        SEL=(150, 176, 164), CURRENT=(150, 30, 20), ITEM_HDR=(70, 70, 72),
    ),
    "m7310-ash": SimpleNamespace(
        name="m7310-ash", title="Nortel Norstar M7310 (Ash)", wsz="Nortel-Norstar-M7310-Ash.wsz", seed=7311,
        colourway="ash",
        BODY=(214, 207, 188), BODY_HI=(238, 233, 219), BODY_LO=(150, 143, 126), SLOT=(118, 112, 98),
        SLOT_LIP=(234, 229, 214),
        BEZEL=(68, 72, 78), BEZEL_HI=(100, 104, 110), BEZEL_LO=(38, 40, 44), RIB=(118, 122, 128),
        KEY=(176, 177, 173), KEY_HI=(216, 217, 213), KEY_LO=(124, 125, 121), KEY_INK=(44, 44, 44),
        RED=(234, 92, 60), RED_HI=(255, 152, 124), RED_LO=(160, 52, 32), RED_INK=(70, 20, 10),
        GREEN=(148, 200, 178), GREEN_HI=(194, 228, 212), GREEN_LO=(96, 146, 126), GREEN_INK=(26, 50, 40),
        PAPER=(234, 231, 216), PAPER_LO=(176, 172, 158), PAPER_DIM=(196, 192, 178),
        GLASS=(168, 184, 164), INK=(30, 36, 30),
        PRINT=(84, 82, 74), PRINT_DIM=(136, 131, 116), PRINT_UNLIT=(150, 145, 130),
        WELL=(132, 126, 110), NUB=(70, 74, 80), NUB_HI=(130, 134, 140),
        SEL=(176, 204, 186), CURRENT=(170, 36, 20), ITEM_HDR=(196, 190, 172),
    ),
}

PALETTE_KEYS = [k for k in vars(THEMES["m7310-charcoal"]) if k.isupper()]


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def hexc(c):
    return "#%02X%02X%02X" % tuple(c)


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def new(w, h, col=None):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = BODY if col is None else col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):max(0, y + h), max(0, x):max(0, x + w)] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def raised(a, x, y, w, h, hi=None, lo=None):
    hi = BODY_HI if hi is None else hi
    lo = BODY_LO if lo is None else lo
    rect(a, x, y, w, 1, hi)
    rect(a, x, y, 1, h, hi)
    rect(a, x, y + h - 1, w, 1, lo)
    rect(a, x + w - 1, y, 1, h, lo)


def sunken(a, x, y, w, h, hi=None, lo=None):
    raised(a, x, y, w, h, BODY_LO if lo is None else lo, BODY_HI if hi is None else hi)


_rng = np.random.default_rng(7310)


def grain(a, x, y, w, h, amp=1.4):
    """The phone's fine matte stipple."""
    n = _rng.normal(0, 1, (h, w)) * amp
    a[y:y + h, x:x + w] += np.round(n).astype(np.int32)[:, :, None]


def plastic(a, x, y, w, h, col=None, amp=1.4):
    rect(a, x, y, w, h, BODY if col is None else col)
    grain(a, x, y, w, h, amp)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def paint(a, mask, x, y, col):
    """Paints colour `col` through a 0..1 mask at (x, y)."""
    h, w = mask.shape
    sub = a[y:y + h, x:x + w].astype(np.float32)
    m = mask[:sub.shape[0], :sub.shape[1], None]
    a[y:y + h, x:x + w] = np.round(sub * (1 - m) + np.array(col, np.float32) * m).astype(np.int32)


# ------------------------------------------------------------------------------------------
# Logos: loaded from source/ at build time, masked, cropped, scaled, painted in print colour
# ------------------------------------------------------------------------------------------


def logo_mask(path):
    """0..1 ink mask from an image: its alpha times its darkness against white."""
    a = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32)
    lum = a[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)
    return a[..., 3] / 255 * np.clip((240 - lum) / (240 - lum.min()), 0, 1)


def bbox(mk, t=0.1):
    ys, xs = np.nonzero(mk > t)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def downscale(mk, w, h):
    """Supersampled down-scale: LANCZOS to 4x the target, then a BOX average to it."""
    im = Image.fromarray(np.round(np.clip(mk, 0, 1) * 255).astype(np.uint8), "L")
    im = im.resize((w * 4, h * 4), Image.LANCZOS).resize((w, h), Image.BOX)
    return np.asarray(im).astype(np.float32) / 255


_LOGOS = {}


def meridian_strip(width, s=3.0):
    """The meridian logo `width` px wide: the word at 1/s scale in the centre and its rule run out
    to both ends (the rule's own scaled columns, repeated). Returns (mask, word_x0, word_x1)."""
    key = ("meridian", width, s)
    if key in _LOGOS:
        return _LOGOS[key]
    mk = logo_mask(os.path.join(SOURCE, "meridian-logo.png"))
    x0, y0, x1, y1 = bbox(mk)
    # Crop with a sub-pixel vertical offset that lands the left rule on one pixel row.
    best = None
    for off in np.arange(0, s, 0.25):
        top = y0 - 3 - off
        iy = int(np.floor(top))
        fr = float(top - iy)
        H = int(np.ceil((y1 + 3 - top) / s))
        sub = mk[iy:iy + int(H * s) + 2, x0 - 4:x1 + 4]
        im = Image.fromarray(np.round(sub * 255).astype(np.uint8), "L").transform(
            (sub.shape[1], int(H * s)), Image.AFFINE, (1, 0, 0, 0, 1, fr), Image.BILINEAR)
        sc = downscale(np.asarray(im).astype(np.float32) / 255, int(round(sub.shape[1] / s)), H)
        score = sc[:, 3].max() + sc[:, -4].max()
        if best is None or score > best[0]:
            best = (score, sc)
    sc = best[1]
    sc = np.clip(sc * 1.15, 0, 1) ** 0.9
    rows = np.nonzero(sc.max(1) > 0.05)[0]
    sc = sc[rows.min():rows.max() + 1]
    # the word: source columns with ink on more rows than the rule's, in scaled coordinates
    cols = np.nonzero((mk > 0.3).sum(0) > 7)[0]
    wx0 = int(np.floor((cols.min() - (x0 - 4)) / s)) - 1
    wx1 = int(np.ceil((cols.max() - (x0 - 4)) / s)) + 2
    left_end, right_end = sc[:, :wx0], sc[:, wx1:]
    word = sc[:, wx0:wx1]
    ww = word.shape[1]
    lw = (width - ww) // 2
    rw = width - ww - lw
    cap = 3

    def run(part, n, cap_left):
        col = part[:, part.shape[1] // 2:part.shape[1] // 2 + 1]
        if cap_left:
            return np.concatenate([part[:, :cap], np.repeat(col, max(0, n - cap - (part.shape[1] - cap) // 2), 1),
                                   part[:, -((part.shape[1] - cap) // 2):]], 1)[:, :n] if n > 0 else part[:, :0]
        return np.concatenate([part[:, :(part.shape[1] - cap) // 2],
                               np.repeat(col, max(0, n - cap - (part.shape[1] - cap) // 2), 1),
                               part[:, -cap:]], 1)[:, -n:] if n > 0 else part[:, :0]

    out = np.concatenate([run(left_end, lw, True), word, run(right_end, rw, False)], 1)
    _LOGOS[key] = (out, lw, lw + ww)
    return _LOGOS[key]


def nortel_mark(h):
    key = ("nortel", h)
    if key not in _LOGOS:
        mk = logo_mask(os.path.join(SOURCE, "nortel-logo.png"))
        x0, y0, x1, y1 = bbox(mk)
        mk = mk[y0:y1, x0:x1]
        w = round(mk.shape[1] * h / mk.shape[0])
        _LOGOS[key] = np.clip(downscale(mk, w, h) * 1.25, 0, 1)
    return _LOGOS[key]


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

# 3x5 capitals for printed labels.
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
}
for _c in "0123456789+-.":
    TINY[_c] = FONT5[_c]

# The phone's key lettering: mixed case, capitals 5 rows, lowercase on a 4-row x-height under a
# 1-row ascender line, descenders a 6th row.
SMALL = dict(TINY)
SMALL.update({
    "a": G("...", ".##", "#.#", "#.#", ".##"),
    "b": G("#..", "##.", "#.#", "#.#", "##."),
    "c": G("...", ".##", "#..", "#..", ".##"),
    "d": G("..#", ".##", "#.#", "#.#", ".##"),
    "e": G("...", ".#.", "###", "#..", ".##"),
    "f": G(".#", "#.", "##", "#.", "#."),
    "g": G("...", ".##", "#.#", ".##", "..#", "##."),
    "h": G("#..", "##.", "#.#", "#.#", "#.#"),
    "i": G("#", ".", "#", "#", "#"),
    "k": G("#..", "#.#", "##.", "##.", "#.#"),
    "l": G("#", "#", "#", "#", "#"),
    "m": G(".....", "####.", "#.#.#", "#.#.#", "#.#.#"),
    "n": G("...", "##.", "#.#", "#.#", "#.#"),
    "o": G("...", ".#.", "#.#", "#.#", ".#."),
    "p": G("...", "##.", "#.#", "#.#", "##.", "#.."),
    "r": G("..", "#.", "##", "#.", "#."),
    "s": G("...", ".##", "##.", ".##", "##."),
    "t": G(".#.", "###", ".#.", ".#.", "..#"),
    "u": G("...", "#.#", "#.#", "#.#", ".##"),
    "y": G("...", "#.#", "#.#", ".##", "..#", "##."),
    "z": G("...", "###", "..#", ".#.", "###"),
})

# 5x7 dot matrix for the clock, as the M7310's LCD draws its characters: one dot per pixel with
# a 1px gap, filling numbers.bmp's 9x13 cell exactly.
DOT57 = {
    0: G(".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    1: G("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    2: G(".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    3: G("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    4: G("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    5: G("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    6: G("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    7: G("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    8: G(".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    9: G(".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    "-": G(".....", ".....", ".....", ".###.", ".....", ".....", "....."),
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
            x += 3
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


# ------------------------------------------------------------------------------------------
# Shared parts: grille, keys, indicators, LCD glass, label strips
# ------------------------------------------------------------------------------------------


def grille(a, x, y, w, rows, lit=True):
    """Speaker grille: horizontal slots (rows: their y offsets), each a dark slit with a lit lip
    under it."""
    slot = SLOT if lit else lerp(SLOT, BODY, 0.35)
    for r in rows:
        rect(a, x, y + r, w, 1, slot)
        rect(a, x, y + r + 1, w, 1, lerp(BODY, SLOT_LIP, 0.5))
        px(a, x, y + r, lerp(slot, BODY, 0.5))
        px(a, x + w - 1, y + r, lerp(slot, BODY, 0.5))


def key_colours(kind, pressed=False):
    face, hi, lo, ink = {
        "grey": (KEY, KEY_HI, KEY_LO, KEY_INK),
        "red": (RED, RED_HI, RED_LO, RED_INK),
        "green": (GREEN, GREEN_HI, GREEN_LO, GREEN_INK),
        "dark": (NUB, NUB_HI, BEZEL_LO, KEY_HI),
    }[kind]
    if pressed:
        face, hi = lerp(face, lo, 0.35), lerp(hi, lo, 0.5)
    return face, hi, lo, ink


def key(a, x, y, w, h, kind="grey", pressed=False):
    """A Norstar key: a flat matte face, a lit top edge, a darker skirt, rounded corners."""
    face, hi, lo, ink = key_colours(kind, pressed)
    top = lerp(face, hi, 0.18)
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(top, face, r / max(1, h - 1)))
    if pressed:
        rect(a, x, y, w, 1, lo)
        rect(a, x, y, 1, h, lerp(lo, face, 0.4))
        rect(a, x + w - 1, y, 1, h, lerp(face, lo, 0.3))
    else:
        rect(a, x + 1, y, w - 2, 1, hi)
        rect(a, x, y + 1, 1, h - 2, lerp(hi, face, 0.4))
        rect(a, x + w - 1, y + 1, 1, h - 2, lerp(face, lo, 0.6))
        rect(a, x + 1, y + h - 1, w - 2, 1, lo)
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        a[cy, cx] = (a[cy, cx] + np.array(lo)) // 2
    return ink


def well(a, x, y, w, h, col=None):
    """The dark gap round a key."""
    rect(a, x, y, w, h, WELL if col is None else col)


def glass(a, x, y, w, h):
    """LCD glass with a thin dark inner rim at top and left (the bezel's shadow)."""
    rect(a, x, y, w, h, GLASS)
    rect(a, x - 1, y - 1, w + 2, 1, BEZEL_LO)
    rect(a, x - 1, y - 1, 1, h + 2, BEZEL_LO)
    rect(a, x - 1, y + h, w + 2, 1, BEZEL_HI)
    rect(a, x + w, y - 1, 1, h + 2, BEZEL_HI)


TRI = G("#..", "##.", "###", "##.", "#..")


def indicator(a, x, y, on, h=7):
    """The phone's LCD indicator beside a key: a 6-wide sliver of glass in a dark rim, with a
    black triangle when on."""
    rect(a, x, y, 6, h, BEZEL_LO)
    rect(a, x + 1, y + 1, 4, h - 2, GLASS)
    if on:
        for r, row in enumerate(TRI[:h - 2] if h < 7 else TRI):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + 2 + k, y + 1 + r + max(0, (h - 7) // 2), INK)


def paper_strip(a, x, y, w, h, lit=True):
    """A memory key's paper designation strip under its clear cap."""
    p = PAPER if lit else PAPER_DIM
    rect(a, x, y, w, h, p)
    rect(a, x, y, w, 1, PAPER_LO)
    rect(a, x, y, 1, h, lerp(PAPER_LO, p, 0.4))
    rect(a, x + 1, y + h - 1, w - 1, 1, lerp(p, (255, 255, 255), 0.35))
    return p


def tri_right(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        rect(a, x, y + r, half - abs(r - half) + 1, 1, col)


def tri_left(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x + half + 1 - n, y + r, n, 1, col)


def mini_icon(a, kind, cx, cy, col):
    """Transport icons, 5 rows tall, centred on (cx, cy)."""
    if kind == "previous":
        rect(a, cx - 4, cy - 2, 1, 5, col)
        tri_left(a, cx - 3, cy - 2, 5, col)
        tri_left(a, cx, cy - 2, 5, col)
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


def icon7(a, kind, cx, cy, col):
    """Transport icons, 7 rows tall."""
    if kind == "previous":
        rect(a, cx - 5, cy - 3, 1, 7, col)
        tri_left(a, cx - 4, cy - 3, 7, col)
        tri_left(a, cx, cy - 3, 7, col)
    elif kind == "next":
        tri_right(a, cx - 4, cy - 3, 7, col)
        tri_right(a, cx, cy - 3, 7, col)
        rect(a, cx + 4, cy - 3, 1, 7, col)
    elif kind == "eject":
        for r in range(4):
            rect(a, cx - r, cy - 3 + r, 2 * r + 1, 1, col)
        rect(a, cx - 3, cy + 2, 7, 2, col)


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: a tiny grey key."""
    rect(a, x, y, 9, 9, WELL)
    ink = key(a, x, y, 9, 9, "grey" if lit else "grey", pressed)
    if not lit:
        a[y:y + 9, x:x + 9] = (a[y:y + 9, x:x + 9] * 3 + np.array(BODY) * 2) // 5
        ink = lerp(KEY_INK, BODY, 0.35)
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        rect(a, X + 3, Y + 3, 3, 3, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 1, ink)
        rect(a, X + 2, Y + 4, 5, 1, lerp(ink, KEY, 0.5))
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]
GRILLE14 = [2, 5, 8, 11]


def titlebar_body(w, h=14):
    a = new(w, h)
    plastic(a, 0, 0, w, h)
    rect(a, 0, 0, w, 1, BODY_HI)
    return a


def main_titlebar(lit):
    """The meridian wordmark in the centre, its rule running out towards the buttons."""
    a = titlebar_body(275)
    rect(a, 0, 0, 1, 14, BODY_HI)
    rect(a, 274, 0, 1, 14, BODY_LO)
    x0, x1 = 19, 240
    mk, wx0, wx1 = meridian_strip(x1 - x0)
    y = (14 - mk.shape[0] + 1) // 2
    # grille slots above the rule either side of the word, clear of it
    rule_row = int(np.argmax(mk[:, 2])) + y
    for gx, gw in ((x0 + 2, wx0 - 6), (x0 + wx1 + 4, (x1 - x0) - wx1 - 6)):
        grille(a, gx, 0, gw, [r for r in (2, 5, 8) if r + 1 < rule_row - 1], lit)
    paint(a, mk, x0, y, PRINT if lit else PRINT_UNLIT)
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def clutter_bar(lit_letters):
    a = new(8, 43, WELL)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        key(a, 0, y, 8, h, "grey", on)
        draw_text(a, TINY, letter, 2 + (1 if on else 0), y + (h - 5) // 2 + (1 if on else 0) - (0 if h == 7 else 0),
                  KEY_INK)
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

def ghost():
    return lerp(GLASS, INK, 0.07)


def dot_digit(a, x, y, glyph, ghosts=True):
    """A 5x7 dot-matrix character in a 9x13 cell: lit dots in ink, unlit ones as the LCD's
    faint pixel grid; neighbouring lit dots are joined by a half-tone so strokes read."""
    rect(a, x, y, 9, 13, GLASS)
    g = glyph
    on = lambda r, c: 0 <= r < 7 and 0 <= c < 5 and g[r][c] == "#"
    join = lerp(GLASS, INK, 0.7)
    for r in range(7):
        for c in range(5):
            if on(r, c):
                px(a, x + 2 * c, y + 2 * r, INK)
                if on(r, c + 1):
                    px(a, x + 2 * c + 1, y + 2 * r, join)
                if on(r + 1, c):
                    px(a, x + 2 * c, y + 2 * r + 1, join)
            elif ghosts:
                px(a, x + 2 * c, y + 2 * r, ghost())


BEZEL_R = (18, 16, 253, 56)        # x 18..270, y 16..71
GLASS_L = (21, 19, 83, 43)         # x 21..103, y 19..61 (time, analyzer)
GLASS_T = (108, 19, 160, 36)       # x 108..267, y 19..54 (title, kbps/kHz, stereo)


def message_lamp(a, x, y):
    """The message-waiting lamp: a small grey triangle with a dark dot, 13 wide."""
    for r in range(9):
        n = 2 * r + 1 if r < 7 else 13
        rect(a, x + 6 - min(r, 6), y + r, min(n, 13), 1, KEY if r else KEY_HI)
        px(a, x + 6 - min(r, 6), y + r, KEY_HI)
        px(a, x + 6 + min(r, 6), y + r, KEY_LO)
    rect(a, x, y + 9, 13, 1, KEY_LO)
    rect(a, x + 5, y + 5, 3, 2, INK)
    px(a, x + 6, y + 4, INK)
    rect(a, x - 1, y + 10, 15, 1, BODY_LO)


def make_main():
    a = new(275, 116)
    plastic(a, 0, 0, 275, 116)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = main_titlebar(True)

    rect(a, 9, 21, 10, 45, WELL)
    a[22:65, 10:18] = clutter_bar("")

    # the display bezel: a dark raised frame holding the LCD and the soft-key row
    bx, by, bw, bh = BEZEL_R
    rect(a, bx, by, bw, bh, BEZEL)
    grain(a, bx, by, bw, bh, 1.0)
    raised(a, bx, by, bw, bh, BEZEL_HI, BEZEL_LO)
    rect(a, bx - 1, by - 1, bw + 2, 1, BODY_LO)
    rect(a, bx - 1, by - 1, 1, bh + 2, BODY_LO)
    for r in (GLASS_L, GLASS_T):
        glass(a, *r)
    # the clock: the LCD's faint dot grid where the app draws the digits, the colon, minus's
    for x in (48, 60, 78, 90):
        dot_digit(a, x, 26, DOT57[" "])
    for r in range(7):
        for c in range(5):
            px(a, 36 + 2 * c, 26 + 2 * r, ghost())
    for yy in (30, 34):
        rect(a, 72, yy, 2, 2, INK)
    # analyzer floor: a dotted line under the bars
    for x in range(24, 100, 2):
        px(a, x, 60, ghost())
    # info row legends
    draw_text(a, SMALL, "kbps", 128, 44, lerp(INK, GLASS, 0.3))
    draw_text(a, SMALL, "kHz", 168, 44, lerp(INK, GLASS, 0.3))
    # the slotted ribs under the LCD, over the soft keys (left of the volume rocker)
    for yy in (64, 66, 68):
        rect(a, 22, yy, 81, 1, RIB)
        rect(a, 22, yy + 1, 81, 1, BEZEL_LO)
    # wells for the rocker, balance and the soft keys
    well(a, 107, 57, 68, 13, BEZEL_LO)
    well(a, 177, 57, 38, 13, BEZEL_LO)

    # seek: the body's recessed groove line
    rect(a, 16, 76, 248, 1, BODY_LO)
    rect(a, 16, 77, 248, 1, lerp(BODY_LO, BODY, 0.4))
    rect(a, 16, 78, 248, 1, BODY_HI)

    # key wells: transport and eject
    for x, w in ((16, 23), (39, 23), (62, 23), (85, 23), (108, 22)):
        well(a, x + 1, 89, w - 2, 16)
    well(a, 137, 90, 20, 14)

    # the message-waiting lamp (the About spot) and a small grille beside it
    message_lamp(a, 253, 92)
    grille(a, 243, 89, 6, [1, 4, 7, 10, 13])

    # the groove across the body, the NORTEL mark on it
    mk = nortel_mark(8)
    mx = 137 - mk.shape[1] // 2
    rect(a, 6, 110, mx - 4 - 6, 1, BODY_LO)
    rect(a, 6, 111, mx - 4 - 6, 1, BODY_HI)
    rect(a, mx + mk.shape[1] + 4, 110, 269 - (mx + mk.shape[1] + 4), 1, BODY_LO)
    rect(a, mx + mk.shape[1] + 4, 111, 269 - (mx + mk.shape[1] + 4), 1, BODY_HI)
    paint(a, mk, mx, 107, PRINT)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons, shufrep, monoster, playpaus, numbers, text
# ------------------------------------------------------------------------------------------

TRANSPORT = [  # kind, sheet x, width, main x, key colour, label
    ("previous", 0, 23, 16, "grey", None),
    ("play", 23, 23, 39, "green", "Line"),
    ("pause", 46, 23, 62, "red", "Hold"),
    ("stop", 69, 23, 85, "red", "Rls"),
    ("next", 92, 22, 108, "grey", None),
]


def phone_key(a, x, y, w, h, kind, colour, label, pressed):
    ink = key(a, x, y, w, h, colour, pressed)
    o = 1 if pressed else 0
    cx = x + w // 2 + o
    if label:
        text_center(a, SMALL, label, cx, y + 2 + o, ink)
        mini_icon(a, kind, cx, y + h - 4 + o, ink)
    elif kind in ("previous", "next", "eject"):
        icon7(a, kind, cx, y + h // 2 + o, ink)
    else:
        mini_icon(a, kind, cx, y + h // 2 + o, ink)


def make_cbuttons(main):
    a = new(136, 36)
    for kind, x, w, dx, colour, label in TRANSPORT:
        for pressed, y in ((False, 0), (True, 18)):
            a[y:y + 18, x:x + w] = main[88:106, dx:dx + w]
            phone_key(a, x + 2, y + 2, w - 4, 14, kind, colour, label, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        a[y:y + 16, 114:136] = main[89:105, 136:158]
        phone_key(a, 116, y + 2, 18, 12, "eject", "grey", None, pressed)
    return a


def toggle(a, x, y, w, h, label, on, pressed, colour="grey", well_col=None):
    """A key with the phone's LCD triangle indicator to its left (on the body or bezel)."""
    indicator(a, x, y + (h - 7) // 2, on)
    kx, kw = x + 7, w - 8
    well(a, kx - 1, y, kw + 2, h, WELL if well_col is None else well_col)
    ink = key(a, kx, y + 1, kw, h - 2, colour, pressed)
    o = 1 if pressed else 0
    text_center(a, SMALL, label, kx + kw // 2 + o, y + (h - 5) // 2 + o, ink)


def make_shufrep(main):
    a = new(92, 85)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = main[89:104, 210:238]
        a[y:y + 15, 28:75] = main[89:104, 164:211]
        toggle(a, 0, y, 28, 15, "Rpt", on, pressed)
        toggle(a, 28, y, 47, 15, "Shuffle", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        for on, y in ((False, 61), (True, 73)):
            a[y:y + 12, x:x + 23] = main[58:70, 219 + (x % 46):219 + (x % 46) + 23]
            toggle(a, x, y, 23, 12, label, on, pressed, well_col=BEZEL_LO)
    return a


def make_monoster():
    a = new(56, 24, GLASS)
    for y, lit in ((0, True), (12, False)):
        col = INK if lit else ghost()
        text_center(a, TINY, "STEREO", 14, y + 4, col)
        text_center(a, TINY, "MONO", 42, y + 4, col)
    return a


def make_playpaus():
    a = new(48, 9, GLASS)
    tri_right(a, 2, 1, 7, INK)
    rect(a, 9 + 2, 1, 2, 7, INK)
    rect(a, 9 + 5, 1, 2, 7, INK)
    rect(a, 18 + 2, 2, 5, 5, INK)
    rect(a, 36, 0, 3, 9, GLASS)
    rect(a, 39 + 1, 3, 1, 3, INK)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, GLASS)
    for n in range(10):
        dot_digit(a, 9 * n, 0, DOT57[n])
    dot_digit(a, 90, 0, DOT57[" "])
    if ex:
        dot_digit(a, 99, 0, DOT57["-"], ghosts=False)
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
            k = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, k, col * 5, row * 6, INK)
    return a


# ------------------------------------------------------------------------------------------
# posbar, volume (the volume rocker), balance
# ------------------------------------------------------------------------------------------


def nub(a, x, y, w, h, selected):
    """The slider thumb: a small dark key with a lit grip line."""
    rect(a, x, y, w, h, BEZEL_LO)
    face = NUB if not selected else lerp(NUB, NUB_HI, 0.3)
    rect(a, x + 1, y + 1, w - 2, h - 2, face)
    rect(a, x + 1, y + 1, w - 2, 1, NUB_HI)
    rect(a, x + 1, y + h - 2, w - 2, 1, lerp(face, BEZEL_LO, 0.5))
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        a[cy, cx] = (a[cy, cx] + np.array(BODY)) // 2
    return face


def nub_h(a, x, y, w, h, selected):
    face = nub(a, x, y, w, h, selected)
    c = x + w // 2
    for gx in (c - 2, c, c + 2):
        rect(a, gx, y + 3, 1, h - 6, GLASS if selected else NUB_HI)


def nub_v(a, x, y, w, h, selected):
    nub(a, x, y, w, h, selected)
    c = y + h // 2
    for gy in ((c - 2, c, c + 2) if h > 12 else (c,)):
        rect(a, x + 3, gy, w - 6, 1, GLASS if selected else NUB_HI)


def make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    for x, sel in ((248, False), (278, True)):
        a[0:10, x:x + 29] = main[72:82, 100:129]
        rect(a, x + 1, 0, 27, 10, BODY_LO)
        ink = key(a, x + 2, 0, 25, 9, "grey", sel)
        for gx in (x + 12, x + 14, x + 16):
            rect(a, gx, 2 + (1 if sel else 0), 1, 5, KEY_LO)
    return a


def speaker(a, x, y, big, col):
    """Speaker glyph: a cone and, for the big one, sound waves."""
    rect(a, x, y + 2, 2, 3, col)
    for r in range(7):
        d = abs(r - 3)
        if d <= 3:
            rect(a, x + 2, y + r, 1 if d == 3 else 2, 1, col)
    if big:
        for r in (1, 5):
            px(a, x + 5, y + r, col)
        rect(a, x + 6, y + 2, 1, 3, col)
        rect(a, x + 8, y + 1, 1, 5, col)
        for r in (0, 6):
            px(a, x + 7, y + r, col)
    else:
        rect(a, x + 5, y + 2, 1, 3, col)


def make_volume(main):
    a = new(68, 433, BEZEL)
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = main[57:72, 107:175]
        rect(a, 0, y, 68, 13, BEZEL_LO)
        key(a, 1, y + 1, 66, 11, "grey")
        speaker(a, 4, y + 3, False, KEY_INK)
        speaker(a, 55, y + 3, True, KEY_INK)
        # the level window
        gx, gw = 14, 39
        glass(a, gx, y + 4, gw, 5)
        level = (i + 1) / 28
        n = round(level * 13)
        for k in range(13):
            bx = gx + 1 + 3 * k
            hgt = 2 + round(1 * k / 12)
            col = INK if k < n else ghost()
            rect(a, bx, y + 8 - hgt, 2, hgt, col)
    nub_h(a, 0, 422, 14, 11, True)
    nub_h(a, 15, 422, 14, 11, False)
    return a


def make_balance(main):
    a = new(68, 433, BEZEL)
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = main[57:72, 177:215]
        rect(a, 9, y, 38, 13, BEZEL_LO)
        key(a, 10, y + 1, 36, 11, "grey")
        draw_text(a, TINY, "L", 13, y + 4, KEY_INK)
        draw_text(a, TINY, "R", 40, y + 4, KEY_INK)
        gx, gw = 18, 21
        glass(a, gx, y + 4, gw, 5)
        reach = round(9 * i / 27)
        c = gx + gw // 2
        for d in range(-9, 10):
            on = abs(d) <= reach and (i > 0 or d == 0)
            if d % 2 == 0:
                rect(a, c + d, y + 5, 1, 3, INK if on else ghost())
    nub_h(a, 0, 422, 14, 11, True)
    nub_h(a, 15, 422, 14, 11, False)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
EQ_X = [21] + [78 + 18 * i for i in range(10)]


def title_ink(lit):
    return INK if lit else lerp(INK, PAPER_DIM, 0.45)


def label_titlebar(title, lit, close_x=264):
    """14px titlebar: grille slots either side of a paper label strip carrying the title."""
    a = titlebar_body(275)
    rect(a, 0, 0, 1, 14, BODY_HI)
    rect(a, 274, 0, 1, 14, BODY_LO)
    tw = text_w(FONT5, title)
    pw = tw + 10
    px0 = (275 - pw) // 2
    grille(a, 6, 0, px0 - 6 - 5, GRILLE14[:3] + [11], lit)
    grille(a, px0 + pw + 5, 0, close_x - 5 - (px0 + pw + 5), GRILLE14[:3] + [11], lit)
    rect(a, px0 - 1, 1, pw + 2, 12, BODY_LO)
    paper_strip(a, px0, 2, pw, 10, lit)
    draw_text(a, FONT5, title, px0 + 5, 4, title_ink(lit))
    mini_button(a, close_x, 3, "close", lit)
    return a


def eq_frame(bg, n=None):
    """A slider's slot: a tall pale indicator strip (like the one between the Line keys) whose
    dark bars rise with the value (n of 0..27)."""
    a = bg.copy()
    rect(a, 3, 1, 8, 61, BODY_LO)
    rect(a, 4, 2, 6, 59, GLASS)
    rect(a, 4, 61, 6, 1, BODY_HI)
    if n is not None:
        v = n / 27
        centre = round((1 - v) * 51) + 5
        for r in range(4, 60, 2):
            on = r >= centre
            rect(a, 5, r, 4, 1, INK if on else ghost())
    return a


def eq_body():
    a = new(275, 116)
    plastic(a, 0, 0, 275, 116)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = label_titlebar("EQUALIZER", True)
    # graph: an LCD in the dark bezel
    rect(a, 82, 15, 121, 23, BEZEL)
    raised(a, 82, 15, 121, 23, BEZEL_HI, BEZEL_LO)
    glass(a, 86, 17, 113, 19)
    # key wells
    rect(a, 216, 17, 46, 14, WELL)
    # a grille panel between the preamp and the bands, the dB print beside it
    grille(a, 52, 38, 22, list(range(1, 62, 3)))
    for lbl, yy in (("+12", 39), ("0", 66), ("-12", 93)):
        text_center(a, TINY, lbl, 44, yy, PRINT)
    for x in EQ_X:
        a[38:101, x:x + 14] = eq_frame(a[38:101, x:x + 14])
    text_center(a, TINY, "PREAMP", 28, 104, PRINT)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 104, PRINT)
    rect(a, 4, 111, 267, 1, BODY_LO)
    rect(a, 4, 112, 267, 1, BODY_HI)
    return a


def memory_key(a, x, y, w, h, label, pressed):
    """A programmable memory key: a clear cap over a paper designation strip."""
    rect(a, x, y, w, h, WELL)
    o = 1 if pressed else 0
    rect(a, x + 1, y + 1 + o, w - 2, h - 2 - o, KEY_LO)
    paper_strip(a, x + 2, y + 2 + o, w - 4, h - 4 - o, True)
    if pressed:
        a[y + 2:y + h - 2, x + 2:x + w - 2] = (a[y + 2:y + h - 2, x + 2:x + w - 2] * 5 + np.array(KEY_LO) * 2) // 7
    rect(a, x + 2, y + 2 + o, w - 4, 1, lerp(PAPER, (255, 255, 255), 0.6))   # the clear cap's sheen
    text_center(a, SMALL, label, x + w // 2 + o, y + (h - 5) // 2 + o, INK)


def make_eqmain():
    a = new(275, 315)
    plastic(a, 0, 0, 275, 315)
    body = eq_body()
    a[0:116, :] = body
    c = new(9, 9)
    mini_button(c, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = c
    for x, label, on, pressed in [
        (10, "On", False, False), (36, "Auto", False, False), (69, "On", True, False), (95, "Auto", True, False),
        (128, "On", False, True), (154, "Auto", False, True), (187, "On", True, True), (213, "Auto", True, True),
    ]:
        w = 26 if label == "On" else 32
        bx = 14 if label == "On" else 40
        a[119:131, x:x + w] = body[18:30, bx:bx + w]
        toggle(a, x, 119, w, 12, label, on, pressed)
    a[134:148, :] = label_titlebar("EQUALIZER", True)
    a[149:163, :] = label_titlebar("EQUALIZER", False)
    for y, sel in ((164, False), (176, True)):
        a[y:y + 11, 0:11] = body[40:51, 22:33]
        rect(a, 0, y, 11, 11, BODY)
        k = new(11, 11)
        key(k, 0, 0, 11, 11, "grey", sel)
        rect(k, 2, 5, 7, 1, KEY_LO)
        rect(k, 2, 6, 7, 1, KEY_HI)
        a[y:y + 11, 0:11] = k
    base = body[38:101, 78:92]
    for n in range(28):
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = eq_frame(base, n)
    for y, pressed in ((164, False), (176, True)):
        a[y:y + 12, 224:268] = body[18:30, 217:261]
        memory_key(a, 224, y, 44, 12, "Presets", pressed)
    # graph background, preamp line, the curve's colours
    rect(a, 0, 294, 113, 19, GLASS)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, ghost())
    for x in range(0, 113, 12):
        for y in range(0, 19, 2):
            px(a, x, 294 + y, ghost())
    for r in range(19):
        px(a, 115, 294 + r, lerp(INK, GLASS, 0.15 * r / 18))
    for x in range(113):
        px(a, x, 314, lerp(INK, GLASS, 0.55) if x % 3 != 2 else GLASS)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109)
# ------------------------------------------------------------------------------------------

GRILLE20 = [3, 6, 9, 12, 15]


def bar20(w, lit):
    a = new(w, 20)
    plastic(a, 0, 0, w, 20)
    rect(a, 0, 0, w, 1, BODY_HI)
    rect(a, 0, 19, w, 1, BODY_LO)
    return a


def side_tile(w, h, outer_left, inner_w=0):
    t = new(w, h)
    plastic(t, 0, 0, w, h)
    if outer_left:
        rect(t, 0, 0, 1, h, BODY_HI)
        rect(t, w - 1, 0, 1, h, BODY_LO)
    else:
        rect(t, w - 1, 0, 1, h, BODY_LO)
        rect(t, 0, 0, 1, h, BODY_HI)
    return t


def small_key(a, x, y, w, h, label):
    well(a, x - 1, y - 1, w + 2, h + 2)
    ink = key(a, x, y, w, h, "grey")
    text_center(a, SMALL, label, x + w // 2, y + (h - 5) // 2, ink)


def make_pledit():
    a = new(280, 186)
    plastic(a, 0, 0, 280, 186)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit)
        grille(t, 0, 0, 25, GRILLE20, lit)
        a[y:y + 20, 127:152] = t
        t = bar20(25, lit)
        rect(t, 0, 0, 1, 20, BODY_HI)
        grille(t, 4, 0, 21, GRILLE20, lit)
        a[y:y + 20, 0:25] = t
        t = bar20(100, lit)
        rect(t, 3, 3, 94, 14, BODY_LO)
        paper_strip(t, 4, 4, 92, 12, lit)
        text_center(t, FONT5, "PLAYLIST", 50, 7, title_ink(lit))
        a[y:y + 20, 26:126] = t
        t = bar20(25, lit)
        rect(t, 24, 0, 1, 20, BODY_LO)
        grille(t, 0, 0, 12, GRILLE20, lit)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    a[42:71, 0:12] = side_tile(12, 29, True)
    t = side_tile(20, 29, False)
    # the scrollbar's groove at x 5..12
    rect(t, 5, 0, 8, 29, WELL)
    rect(t, 5, 0, 1, 29, BODY_LO)
    rect(t, 12, 0, 1, 29, BODY_HI)
    a[42:71, 31:51] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        k = new(8, 18, WELL)
        key(k, 0, 0, 8, 18, "grey", sel)
        for gy in (7, 9, 11):
            rect(k, 2, gy, 4, 1, KEY_LO)
        a[53:71, x:x + 8] = k

    def bottom_base(w):
        t = new(w, 38)
        plastic(t, 0, 0, w, 38)
        rect(t, 0, 0, w, 1, BODY_LO)
        rect(t, 0, 1, w, 1, BODY_HI)
        rect(t, 0, 37, w, 1, BODY_LO)
        # the body's groove line
        rect(t, 0, 33, w, 1, BODY_LO)
        rect(t, 0, 34, w, 1, BODY_HI)
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, BODY_HI)
    for bx, lbl in ((14, "Add"), (43, "Rem"), (72, "Sel"), (101, "Misc")):
        small_key(t, bx + 1, 9, 20, 16, lbl)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, BODY_LO)
    # the running time: a small LCD in a bezel
    rect(t, 3, 6, 62, 14, BEZEL)
    glass(t, 6, 9, 56, 8)
    rect(t, 2, 21, 62, 12, WELL)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        colour = {"play": "green", "pause": "red", "stop": "red"}.get(kind, "grey")
        ink = key(t, bx, 22, 10, 10, colour)
        mini_icon(t, kind, bx + 5, 27, ink)
    rect(t, 63, 20, 37, 12, BEZEL)
    glass(t, 65, 22, 33, 8)
    rect(t, 84, 24, 1, 1, INK)
    rect(t, 84, 27, 1, 1, INK)
    small_key(t, 107, 9, 20, 16, "List")
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 30 - 3 * j
            px(t, gx, gy, BODY_LO)
            px(t, gx + 1, gy + 1, BODY_HI)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GEN_PLATE = (3, 11)   # the label strip in the 20px bar: y 3..13 (letters drawn at y 4, 7 tall)


def make_gen():
    a = new(194, 109)
    plastic(a, 0, 0, 194, 109)
    py, ph = GEN_PLATE
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn):
            t = bar20(25, lit)
            fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def strip(t, x, w):
            p = PAPER if lit else PAPER_DIM
            rect(t, x, py - 1, w, 1, BODY_LO)
            rect(t, x, py, w, 1, PAPER_LO)
            rect(t, x, py + 1, w, ph - 2, p)
            rect(t, x, py + ph - 1, w, 1, lerp(p, (255, 255, 255), 0.35))

        def left(t):
            rect(t, 0, 0, 1, 20, BODY_HI)
            grille(t, 4, 0, 21, GRILLE20, lit)

        def left_end(t):
            grille(t, 0, 0, 16, GRILLE20, lit)
            rect(t, 19, py - 1, 1, ph + 1, BODY_LO)
            strip(t, 20, 5)
            rect(t, 20, py, 1, ph, lerp(PAPER_LO, PAPER if lit else PAPER_DIM, 0.4))

        def centre(t):
            strip(t, 0, 25)

        def right_end(t):
            strip(t, 0, 5)
            rect(t, 5, py - 1, 1, ph + 1, BODY_LO)
            grille(t, 9, 0, 16, GRILLE20, lit)

        def fill(t):
            grille(t, 0, 0, 25, GRILLE20, lit)

        def right(t):
            grille(t, 0, 0, 12, GRILLE20, lit)
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
        plastic(t, 0, 0, w, 14)
        rect(t, 0, 0, w, 1, BODY_LO)
        rect(t, 0, 1, w, 1, BODY_HI)
        rect(t, 0, 13, w, 1, BODY_LO)
        rect(t, 0, 9, w, 1, BODY_LO)
        rect(t, 0, 10, w, 1, BODY_HI)
        if left_edge:
            rect(t, 0, 0, 1, 14, BODY_HI)
        else:
            rect(t, w - 1, 0, 1, 14, BODY_LO)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 7 - 3 * j
                    px(t, gx, gy, BODY_LO)
                    px(t, gx + 1, gy + 1, BODY_HI)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = side_tile(w, h, outer_left)
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        cell = PAPER if lit else PAPER_DIM
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


def genex_colours():
    return [
        PAPER,                         # item background: the designation strip
        INK,                           # item text
        BODY,                          # window background
        KEY_INK,                       # button text (on the grey key faces)
        PRINT,                         # window text
        BODY_LO,                       # dividers, sunken borders
        SEL,                           # selection bar
        ITEM_HDR,                      # list header background
        PRINT if T.colourway == "charcoal" else KEY_INK,   # list header text
        BODY_HI,                       # header frame, light
        BODY_LO,                       # header frame, dark
        KEY_LO,                        # header frame, pressed
        BODY,                          # header dead area
        KEY,                           # scrollbar
        KEY_LO,                        # scrollbar 2
        KEY_HI,                        # scrollbar pressed
        KEY_LO,                        # scrollbar pressed 2
        WELL,                          # scrollbar dead area
    ]


def make_genex():
    a = new(256, 64)
    plastic(a, 0, 1, 256, 63)
    rect(a, 0, 0, 256, 1, BODY)
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    key(a, 0, 1, 47, 15, "grey")
    key(a, 0, 16, 47, 15, "grey", True)
    return a


def viscolor():
    dark = [lerp(INK, GLASS, 0.32 * i / 15) for i in range(16)]
    return ([(GLASS, "background"), (ghost(), "dots")]
            + [(c, f"spectrum {i + 1}") for i, c in enumerate(dark)]
            + [(lerp(INK, GLASS, t), f"oscilloscope {k + 1}") for k, t in enumerate((0, 0.08, 0.16, 0.24, 0.32))]
            + [(lerp(INK, (0, 0, 0), 0.4), "peaks")])


def pledit_colours():
    return dict(Normal=hexc(INK), Current=hexc(CURRENT), NormalBG=hexc(PAPER), SelectedBG=hexc(SEL))


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    p = pledit_colours()
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={p['Normal']}\nCurrent={p['Current']}\nNormalBG={p['NormalBG']}\n"
                f"SelectedBG={p['SelectedBG']}\nMbBG={p['NormalBG']}\nMbFG={p['Normal']}\nFont=Arial\n")
    name = T.wsz[:-4].replace("-", " ")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{name} - a skin in the style of the Meridian Norstar M7310 office phone\n"
            f"({T.colourway} colourway): its grey-green dot-matrix LCD, Hold and Rls keys, Line keys,\n"
            "volume rocker, speaker grille and paper designation strips.\n"
            "Nortel logo (c) Nortel Networks. Meridian logo (c) Nortel Networks (Meridian Norstar\n"
            "was Northern Telecom / Nortel's key telephone system).\n\n"
            "Drawn by a script (gen_skin.py): rectangles, bevels, noise and hand-made pixel fonts,\n"
            "with the two logos masked and painted in the skin's print colour.\n"
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


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


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
    p = pledit_colours()
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
    c0, c1 = np.array(GLASS, np.float32), np.array(GREEN_LO, np.float32)
    col = c0 + (c1 - c0) * arr[..., :1]
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


PREVIEW_ROWS = [("Hold Music - Please Stay On The Line", "4:12"), ("Line 1 - Ringing", "3:47"),
                ("Conference Call - Trans", "5:03"), ("Intercom - Page All", "2:58"),
                ("Speed Dial - Memory 12", "6:21"), ("Do Not Disturb - Quiet Hours", "3:33"),
                ("Handsfree - Mute", "4:40"), ("Message Waiting - Lamp On", "3:09"),
                ("Feature 0 - Release", "5:51"), ("Call Forward - After Hours", "4:05"),
                ("Voicemail - Press Rls", "3:22")]


def preview():
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=196, remaining=False,
             title="Hold Music - Please Stay On The Line (Jan 14)", bars=bars)
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
    mb = preview_main(False, B)
    e = preview_eq(True, EA)
    p = preview_playlist(True, 275, 232, PREVIEW_ROWS)
    for name, im, box in (("display", m, (8, 14, 272, 72)), ("keys", m, (0, 70, 275, 116)),
                          ("keys-b", mb, (0, 70, 275, 116)), ("titlebar", m, (0, 0, 275, 16)),
                          ("eq", e, (0, 0, 275, 116)), ("playlist-bottom", p, (0, 190, 275, 232)),
                          ("playlist-top", p, (0, 0, 275, 40))):
        c = im.crop(box)
        c.resize((c.width * 4, c.height * 4), Image.NEAREST).save(os.path.join(SCRATCH, f"{T.name}-{name}-4x.png"))


def use_theme(name):
    global T, OUT, _rng
    T = THEMES[name]
    OUT = os.path.join(OUT_ROOT, name)
    os.makedirs(OUT, exist_ok=True)
    _rng = np.random.default_rng(T.seed)
    for k in PALETTE_KEYS:
        globals()[k] = getattr(T, k)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--list"]:
        for k, v in THEMES.items():
            print(f"{k:16s} {v.wsz}")
        sys.exit(0)
    for theme in (args or list(THEMES)):
        use_theme(theme)
        names = build()
        preview()
        print(f"{T.wsz}: {', '.join(names)}")
