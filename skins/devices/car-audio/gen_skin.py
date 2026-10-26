#!/usr/bin/python3
"""VW MIB II and Clarion: classic Winamp 2.x skins in the style of two car head units.

One procedural generator, a theme each (based on skins/ember/gen_skin.py, whose sheet layouts it
keeps). Everything is drawn here from code (gradients, anti-aliased shapes, hand-made pixel
fonts, digits rendered from Open Sans for the MIB screen), except the Volkswagen roundel, loaded
from source/ at generation time. The Clarion wordmark is hand-drawn pixel lettering. Private use only.

    /usr/bin/python3 -I gen_skin.py [vw-mib2|clarion ...]   (no argument builds both)
    /usr/bin/python3 -I gen_skin.py --list

Per theme: the bitmaps and text files in out/<theme>/, zipped flat into <Name>.wsz beside this
file, and preview-<theme>.png (the windows assembled from the sprites the way the app does, 2x).
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
OUT = None          # out/<theme>, set by use_theme
T = None            # the theme in use

SEP = (255, 0, 255)  # gen.bmp letter separators (never shown)

# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    # Volkswagen MIB II (Modular Infotainment Platform 2, Composition / Discover Media,
    # 2015-2019): a piano-black glass surround, chrome-ringed hard keys either side of the
    # screen, two knobs below it, and the screen's blue-on-black UI.
    "vw-mib2": SimpleNamespace(
        name="vw-mib2", title="VW MIB II", wsz="VW-MIB-II.wsz", subject="Volkswagen's MIB II infotainment",
        owner="Volkswagen AG", logo_note="Volkswagen logo",
        disp=(13, 19, 30),            # the screen's cards: title, time, kbps (text.bmp's background)
        ink=(236, 241, 247),          # text.bmp, numbers, playpaus
        accent=(38, 160, 232), accent_hi=(110, 200, 250), accent_lo=(18, 70, 112),
        dim=(124, 140, 162), line=(40, 54, 76),
        pledit=dict(Normal="#D6DDE6", Current="#5CC0F5", NormalBG="#0A0F18", SelectedBG="#1D3B5E"),
        vis=[(236, 246, 255), (130, 206, 250), (38, 160, 232), (20, 92, 168), (12, 46, 96)],
        vis_dots=(20, 28, 42), vis_peak=(255, 255, 255),
        genex=None,
    ),
    # The MIB II screen UI on its own (Composition Media radio/media screen, 2015-2019): black
    # screen, status row with the clock, big white centred title, light-grey preset tiles with a
    # red underline, the dark soft-key bar under a red rule. No hardware.
    "vw-mib2-v2": SimpleNamespace(
        name="vw-mib2-v2", title="VW MIB II v2", wsz="VW-MIB-II-v2.wsz",
        subject="Volkswagen's MIB II infotainment screen", owner="Volkswagen AG", logo_note="Volkswagen logo",
        disp=(0, 0, 0), ink=(242, 242, 242),
        accent=(232, 52, 38), accent_hi=(255, 104, 84), accent_lo=(90, 20, 14),
        dim=(150, 152, 158), line=(78, 80, 86),
        pledit=dict(Normal="#F0F0F0", Current="#F2503C", NormalBG="#000000", SelectedBG="#3A3B42"),
        vis=[(250, 250, 250), (214, 216, 222), (170, 174, 182), (122, 126, 136), (84, 88, 98)],
        vis_dots=(16, 16, 20), vis_peak=(232, 52, 38), font="Noto Sans",
        ttf="/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
        genex=None,
    ),
    # Clarion, a representative 2000s single-DIN MP3 CD receiver (styled after the DXZ-series,
    # c. 2003-2005): brushed silver faceplate, a black smoked display window with a cyan
    # segment/dot-matrix display, small rubber keys (RDM / RPT), a big rotary volume knob.
    "clarion": SimpleNamespace(
        name="clarion", title="Clarion", wsz="Clarion.wsz", subject="a 2000s Clarion car CD receiver",
        owner="Clarion Co., Ltd.", logo_note="Clarion wordmark (hand-drawn pixel lettering)",
        disp=(5, 10, 13),
        ink=(70, 222, 255),
        accent=(70, 222, 255), accent_hi=(190, 246, 255), accent_lo=(14, 52, 64),
        dim=(14, 46, 56), line=(16, 38, 46),
        pledit=dict(Normal="#46DEFF", Current="#FFFFFF", NormalBG="#05090C", SelectedBG="#0D3C4E"),
        vis=[(210, 250, 255), (90, 230, 255), (40, 180, 230), (20, 110, 170), (12, 60, 100)],
        vis_dots=(10, 24, 30), vis_peak=(230, 255, 255),
        genex=None,
    ),
    # The Clarion ADX5655z (c. 2002): double-DIN tuner / CD / cassette with a VFD spectrum
    # analyzer, blue/cyan segment banks capped in orange, a pale blue-white dot-matrix readout.
    "clarion-adx5655z": SimpleNamespace(
        name="clarion-adx5655z", title="Clarion ADX5655z", wsz="Clarion-ADX5655z.wsz",
        subject="the Clarion ADX5655z car stereo", owner="Clarion Co., Ltd.",
        logo_note="Clarion wordmark (hand-drawn pixel lettering)",
        disp=(16, 10, 22), ink=(214, 230, 255),
        accent=(255, 146, 36), accent_hi=(255, 196, 70), accent_lo=(80, 40, 10),
        dim=(44, 32, 58), line=(44, 32, 58),
        pledit=dict(Normal="#96C8FF", Current="#FF9224", NormalBG="#100A16", SelectedBG="#34244E"),
        vis=[(255, 190, 70), (150, 225, 255), (40, 74, 196)],
        vis_rows=[(255, 196, 70), (255, 166, 50), (255, 140, 36), (150, 226, 255), (132, 214, 255),
                  (116, 202, 255), (102, 188, 255), (90, 174, 255), (80, 160, 252), (72, 146, 246),
                  (64, 132, 240), (58, 118, 232), (52, 106, 224), (48, 96, 216), (44, 86, 206), (40, 76, 196)],
        vis_dots=(38, 26, 50), vis_peak=(255, 146, 36),
        genex=None,
    ),
    # The same unit, closer to its real front: the keys on the brushed silver faceplate, only the
    # display sections dark VFD glass (the same VFD content and playlist colours).
    "clarion-adx5655z-silver": SimpleNamespace(
        name="clarion-adx5655z-silver", title="Clarion ADX5655z Silver", wsz="Clarion-ADX5655z-Silver.wsz",
        subject="the Clarion ADX5655z car stereo (silver faceplate)", owner="Clarion Co., Ltd.",
        logo_note="Clarion wordmark (hand-drawn pixel lettering)",
        disp=(16, 10, 22), ink=(214, 230, 255),
        accent=(255, 146, 36), accent_hi=(255, 196, 70), accent_lo=(80, 40, 10),
        dim=(44, 32, 58), line=(44, 32, 58),
        pledit=dict(Normal="#96C8FF", Current="#FF9224", NormalBG="#100A16", SelectedBG="#34244E"),
        vis=[(255, 190, 70), (150, 225, 255), (40, 74, 196)],
        vis_rows=[(255, 196, 70), (255, 166, 50), (255, 140, 36), (150, 226, 255), (132, 214, 255),
                  (116, 202, 255), (102, 188, 255), (90, 174, 255), (80, 160, 252), (72, 146, 246),
                  (64, 132, 240), (58, 118, 232), (52, 106, 224), (48, 96, 216), (44, 86, 206), (40, 76, 196)],
        vis_dots=(38, 26, 50), vis_peak=(255, 146, 36),
        genex=None,
    ),
}


def use_theme(name):
    global T, OUT
    T = THEMES[name]
    OUT = os.path.join(OUT_ROOT, name)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    global _rng
    _rng = np.random.default_rng(4242 if name == "clarion" else 1515)


# ------------------------------------------------------------------------------------------
# Colour and canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


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


def new(w, h, col=(0, 0, 0)):
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


def vfill(a, x, y, w, h, stops):
    for r in range(h):
        rect(a, x, y + r, w, 1, ramp(stops, r / max(1, h - 1)))


def hline(a, x, y, w, col):
    rect(a, x, y, w, 1, col)


_rng = np.random.default_rng(1)


def brushed(a, x, y, w, h, amp=3.0, smear=6):
    """Brushed-metal grain: horizontally smeared noise (wraps, so tiles stay seamless)."""
    n = _rng.normal(0, 1, (h, w))
    acc = np.zeros_like(n)
    for d in range(-smear, smear + 1):
        acc += np.roll(n, d, axis=1)
    acc /= np.sqrt(2 * smear + 1)
    acc += _rng.normal(0, 0.3, (h, w))
    a[y:y + h, x:x + w] += np.round(acc * amp).astype(np.int32)[:, :, None]


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


# anti-aliased coverage masks (4x supersampled), painted with paint()

def _grid(w, h, ss=4):
    ys, xs = np.mgrid[0:h * ss, 0:w * ss]
    return (xs + 0.5) / ss, (ys + 0.5) / ss


def _down(m, w, h, ss=4):
    return m.reshape(h, ss, w, ss).mean(axis=(1, 3))


def circle_m(w, h, cx, cy, r):
    X, Y = _grid(w, h)
    return _down(((X - cx) ** 2 + (Y - cy) ** 2 <= r * r).astype(np.float32), w, h)


def ring_m(w, h, cx, cy, r0, r1):
    X, Y = _grid(w, h)
    d2 = (X - cx) ** 2 + (Y - cy) ** 2
    return _down(((d2 <= r1 * r1) & (d2 >= r0 * r0)).astype(np.float32), w, h)


def rr_m(w, h, x0, y0, x1, y1, r):
    """Rounded rectangle [x0, x1) x [y0, y1) with corner radius r."""
    X, Y = _grid(w, h)
    cx = np.clip(X, x0 + r, x1 - r)
    cy = np.clip(Y, y0 + r, y1 - r)
    inside = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1) & ((X - cx) ** 2 + (Y - cy) ** 2 <= r * r)
    return _down(inside.astype(np.float32), w, h)


def poly_m(w, h, pts):
    img = Image.new("L", (w * 4, h * 4), 0)
    ImageDraw.Draw(img).polygon([(x * 4, y * 4) for x, y in pts], fill=255)
    return np.asarray(img.resize((w, h), Image.BOX), dtype=np.float32) / 255


def paint(a, x, y, m, col, alpha=1.0):
    """Blend colour (or an H x W x 3 array) into a at (x, y) through coverage mask m."""
    h, w = m.shape
    y0, x0 = max(0, y), max(0, x)
    y1, x1 = min(a.shape[0], y + h), min(a.shape[1], x + w)
    if y1 <= y0 or x1 <= x0:
        return
    mm = m[y0 - y:y1 - y, x0 - x:x1 - x][:, :, None] * alpha
    src = np.asarray(col, dtype=np.float32)
    if src.ndim == 3:
        src = src[y0 - y:y1 - y, x0 - x:x1 - x]
    reg = a[y0:y1, x0:x1].astype(np.float32)
    a[y0:y1, x0:x1] = np.round(reg * (1 - mm) + src * mm).astype(np.int32)


def vgrad_arr(w, h, stops):
    g = np.array([ramp(stops, r / max(1, h - 1)) for r in range(h)], dtype=np.float32)
    return np.repeat(g[:, None, :], w, axis=1)


def rgrad_arr(w, h, cx, cy, r, stops):
    """Radial gradient, stops from the centre out to r."""
    X, Y = np.mgrid[0:h, 0:w][1] + 0.5, np.mgrid[0:h, 0:w][0] + 0.5
    t = np.clip(np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / r, 0, 1)
    out = np.zeros((h, w, 3), dtype=np.float32)
    for yy in range(h):
        for xx in range(w):
            out[yy, xx] = ramp(stops, t[yy, xx])
    return out


# ------------------------------------------------------------------------------------------
# Pixel fonts (Ember's, plus the Clarion wordmark)
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

# 7-row wordmark letters for the main titlebar.
WORDMARK = {
    "E": G("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "M": G("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "B": G("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "R": G("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
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



for _c, _g in {
    "J": G("..#", "..#", "..#", "#.#", ".#."),
    "/": G("..#", "..#", ".#.", "#..", "#.."),
    ":": G(".", "#", ".", "#", "."),
    "·": G(".", ".", "#", ".", "."),
}.items():
    TINY[_c] = _g

# The Clarion wordmark: bold rounded sans, capital C and lowercase "larion" (7 rows, x-height 5).
CLARION = {
    "C": G(".####", "##...", "##...", "##...", "##...", "##...", ".####"),
    "l": G("##", "##", "##", "##", "##", "##", "##"),
    "a": G(".....", ".....", "####.", "...##", ".####", "##.##", ".####"),
    "r": G("....", "....", "##.#", "####", "##..", "##..", "##.."),
    "i": G("##", "..", "##", "##", "##", "##", "##"),
    "o": G(".....", ".....", ".###.", "##.##", "##.##", "##.##", ".###."),
    "n": G(".....", ".....", "####.", "##.##", "##.##", "##.##", "##.##"),
}


def clarion_wordmark(a, x, y, col, shadow=None):
    return draw_text(a, CLARION, "Clarion", x, y, col, gap=1, shadow=shadow)


CLARION_W = text_w(CLARION, "Clarion")


# ------------------------------------------------------------------------------------------
# Icons
# ------------------------------------------------------------------------------------------


def tri_right(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        rect(a, x, y + r, half - abs(r - half) + 1, 1, col)


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
        tri_right(a, cx - 2, cy - 4, 9, col)
    elif kind == "pause":
        rect(a, cx - 3, cy - 3, 2, 7, col)
        rect(a, cx + 1, cy - 3, 2, 7, col)
    elif kind == "stop":
        rect(a, cx - 3, cy - 3, 7, 7, col)
    elif kind == "next":
        tri_right(a, cx - 5, cy - 3, 7, col)
        tri_right(a, cx - 1, cy - 3, 7, col)
        rect(a, cx + 3, cy - 3, 2, 7, col)
    elif kind == "eject":
        for r in range(4):
            rect(a, cx - r, cy - 4 + r, 2 * r + 1, 1, col)
        rect(a, cx - 3, cy + 1, 7, 2, col)


def mini_transport_icon(a, kind, x, y, col):
    cx, cy = x + 5, y + 5
    if kind == "previous":
        rect(a, cx - 3, cy - 2, 1, 5, col)
        tri_left(a, cx - 2, cy - 2, 5, col)
        tri_left(a, cx + 1, cy - 2, 5, col)
    elif kind == "play":
        tri_right(a, cx - 1, cy - 3, 7, col)
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
            rect(a, cx - r, cy - 3 + r, 2 * r + 1, 1, col)
        rect(a, cx - 2, cy + 1, 5, 1, col)


def caption_glyph(a, kind, x, y, col):
    """Glyph for a 9x9 titlebar button whose top-left is (x, y)."""
    if kind == "options":
        rect(a, x + 2, y + 3, 5, 1, col)
        rect(a, x + 3, y + 4, 3, 1, col)
        px(a, x + 4, y + 5, col)
    elif kind == "minimize":
        rect(a, x + 2, y + 6, 5, 1, col)
    elif kind == "shade":
        rect(a, x + 2, y + 2, 5, 1, col)
        rect(a, x + 2, y + 4, 5, 1, col)
    elif kind == "close":
        for i in range(5):
            px(a, x + 2 + i, y + 2 + i, col)
            px(a, x + 6 - i, y + 2 + i, col)


# ------------------------------------------------------------------------------------------
# Surfaces: the bezel / faceplate, screens, keys
# ------------------------------------------------------------------------------------------

VW_BEZEL = [(32, 33, 37), (18, 19, 22), (9, 9, 11)]
VW_SCREEN = (4, 7, 12)
VW_CHROME = [(236, 239, 243), (176, 180, 186), (98, 101, 107), (150, 154, 160)]
CL_SILVER = [(204, 207, 212), (184, 188, 194), (160, 164, 170)]
CL_INK = (24, 26, 30)          # silkscreen on the silver
CL_PRINT = (84, 88, 96)        # fainter silkscreen
CL_GLASS = (16, 18, 20)        # the display window's black rim


def surface(a, x, y, w, h, top=0, total=116):
    """The unit's body: VW's piano-black glass, Clarion's brushed silver. Shaded by absolute row
    (top = the absolute y of row 0) so pieces cut from different sheets line up."""
    if T.name == "vw-mib2":
        for r in range(h):
            t = (top + r) / total
            rect(a, x, y + r, w, 1, ramp(VW_BEZEL, t))
        # a faint diagonal gloss streak
        for r in range(h):
            for c in range(w):
                u = (c + x + 1.6 * (r + top)) % 260
                if 30 <= u < 70:
                    a[y + r, x + c] += int(5 * np.sin((u - 30) / 40 * np.pi))
    else:
        for r in range(h):
            t = (top + r) / total
            rect(a, x, y + r, w, 1, ramp(CL_SILVER, t))
        brushed(a, x, y, w, h, 4.0)


def frame_edges(a, x, y, w, h):
    """Outer edge of a window: VW a dark rim with a chrome hairline; Clarion a bevelled silver edge."""
    if T.name == "vw-mib2":
        rect(a, x, y, w, 1, (64, 66, 72))
        rect(a, x, y, 1, h, (52, 54, 60))
        rect(a, x + w - 1, y, 1, h, (4, 4, 5))
        rect(a, x, y + h - 1, w, 1, (4, 4, 5))
    else:
        rect(a, x, y, w, 1, (236, 238, 241))
        rect(a, x, y, 1, h, (226, 228, 232))
        rect(a, x + w - 1, y, 1, h, (104, 108, 114))
        rect(a, x, y + h - 1, w, 1, (96, 100, 106))


def screen_box(a, x, y, w, h, r=3, col=None):
    """VW: the flush glass screen. Clarion: the smoked display window in its black rim."""
    if T.name == "vw-mib2":
        paint(a, x, y, rr_m(w, h, 0, 0, w, h, r), (0, 0, 0))
        paint(a, x, y, rr_m(w, h, 1, 1, w - 1, h - 1, r - 1), col or VW_SCREEN)
    else:
        paint(a, x - 1, y - 1, rr_m(w + 2, h + 2, 0, 0, w + 2, h + 2, r + 1), (118, 122, 128))
        paint(a, x, y, rr_m(w, h, 0, 0, w, h, r), CL_GLASS)
        paint(a, x, y, rr_m(w, h, 2, 2, w - 2, h - 2, max(1, r - 2)), col or T.disp)
        # the window's lower lip catches light
        rect(a, x + r, y + h, w - 2 * r, 1, (224, 227, 231))


def card(a, x, y, w, h, col=None, r=2):
    """A flat panel on the MIB screen (the title card, the time tile)."""
    paint(a, x, y, rr_m(w, h, 0, 0, w, h, r), col or T.disp)


def vw_key(a, x, y, w, h, pressed, r=2.5):
    """A MIB II hard key: chrome ring round a gloss-black face."""
    rim = vgrad_arr(w, h, [(120, 124, 130), (88, 90, 96), (176, 180, 186)] if pressed else VW_CHROME)
    paint(a, x, y, rr_m(w, h, 0, 0, w, h, r), rim)
    face = vgrad_arr(w, h, [(6, 6, 8), (16, 17, 20), (26, 27, 31)] if pressed else
                     [(58, 60, 66), (26, 27, 30), (10, 10, 12), (18, 19, 22)])
    paint(a, x, y, rr_m(w, h, 1, 1, w - 1, h - 1, max(0.5, r - 1)), face)
    if not pressed:
        paint(a, x, y, rr_m(w, h, 1.5, 1.5, w - 1.5, 1 + (h - 2) * 0.42, max(0.5, r - 1.5)), (255, 255, 255), 0.06)


def cl_key(a, x, y, w, h, pressed, r=3.0):
    """A Clarion rubber key standing proud of the silver: dark rim, charcoal face, soft shadow."""
    paint(a, x, y, rr_m(w, h, 0, 1, w, h, r), (96, 100, 106), 0.7)
    paint(a, x, y, rr_m(w, h, 0, 0, w, h - 1, r), (20, 21, 24))
    face = vgrad_arr(w, h, [(22, 23, 26), (34, 35, 39), (42, 44, 48)] if pressed else
                     [(92, 94, 100), (58, 60, 65), (40, 41, 45), (34, 35, 38)])
    paint(a, x, y, rr_m(w, h, 1, 1, w - 1, h - 2, max(0.5, r - 1)), face)


def key(a, x, y, w, h, pressed, r=None):
    if T.name == "vw-mib2":
        vw_key(a, x, y, w, h, pressed, 2.5 if r is None else r)
    else:
        cl_key(a, x, y, w, h, pressed, 3.0 if r is None else r)


def key_ink(pressed, on=False):
    if T.name == "vw-mib2":
        if on:
            return T.accent_hi if pressed else T.accent
        return T.accent_hi if pressed else (236, 240, 246)
    if on:
        return T.accent_hi
    return T.accent if pressed else (226, 230, 236)


def knob(a, cx, cy, r, power=False):
    """A rotary knob seen from the front, centred on (cx, cy) (floats, in a's pixels)."""
    x0, y0 = int(cx - r - 2), int(cy - r - 2)
    w = h = int(2 * r + 5)
    lx, ly = cx - x0, cy - y0
    if T.name == "vw-mib2":
        paint(a, x0, y0, circle_m(w, h, lx, ly + 0.6, r + 0.4), (0, 0, 0), 0.8)
        paint(a, x0, y0, circle_m(w, h, lx, ly, r), vgrad_arr(w, h, VW_CHROME))
        # knurled grip: alternating shades round the chrome
        X, Y = np.mgrid[0:h, 0:w][1] + 0.5, np.mgrid[0:h, 0:w][0] + 0.5
        ang = np.arctan2(Y - ly, X - lx)
        knurl = ((np.floor(ang / (2 * np.pi) * 36) % 2) == 0).astype(np.float32)
        paint(a, x0, y0, ring_m(w, h, lx, ly, r - 1.6, r - 0.4) * knurl, (60, 62, 68), 0.55)
        paint(a, x0, y0, circle_m(w, h, lx, ly, r - 1.8), (8, 8, 10))
        paint(a, x0, y0, circle_m(w, h, lx - 0.8, ly - 1.2, r - 3.0), (40, 42, 47), 0.6)
        if power:
            pw = [".#.#.", "#.#.#", "#...#", "#...#", ".###."]
            for rr, row in enumerate(pw):
                for c, ch in enumerate(row):
                    if ch == "#":
                        px(a, int(round(cx)) - 2 + c, int(round(cy)) - 2 + rr, (220, 226, 234))
            px(a, int(round(cx)) - 1, int(round(cy)) - 2, (8, 8, 10))
            px(a, int(round(cx)) + 1, int(round(cy)) - 2, (8, 8, 10))
            px(a, int(round(cx)), int(round(cy)) - 2, (220, 226, 234))
        else:
            rect(a, int(round(cx)) - 0, int(round(cy - r + 3)), 1, 2, (220, 226, 234))
    else:
        paint(a, x0, y0, circle_m(w, h, lx + 0.4, ly + 1.0, r + 0.6), (70, 74, 80), 0.7)
        # black rubber skirt with grip ridges
        paint(a, x0, y0, circle_m(w, h, lx, ly, r), (18, 18, 20))
        X, Y = np.mgrid[0:h, 0:w][1] + 0.5, np.mgrid[0:h, 0:w][0] + 0.5
        ang = np.arctan2(Y - ly, X - lx)
        ridge = ((np.floor(ang / (2 * np.pi) * 28) % 2) == 0).astype(np.float32)
        paint(a, x0, y0, ring_m(w, h, lx, ly, r - 2.2, r - 0.5) * ridge, (52, 54, 58), 0.9)
        # the blue illumination ring
        paint(a, x0, y0, ring_m(w, h, lx, ly, r - 3.6, r - 2.4), T.accent, 0.9)
        # brushed silver cap, concentric
        cap = rgrad_arr(w, h, lx - 1.5, ly - 2, r, [(238, 240, 244), (196, 200, 206), (140, 144, 150)])
        paint(a, x0, y0, circle_m(w, h, lx, ly, r - 3.8), cap)
        paint(a, x0, y0, ring_m(w, h, lx, ly, r - 3.8, r - 3.2), (60, 62, 66), 0.6)
        # pointer dimple
        paint(a, x0, y0, circle_m(w, h, lx - (r - 6.5) * 0.7, ly - (r - 6.5) * 0.7, 1.1), (70, 74, 80))


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

VW_KEYS_L = ["RADIO", "MEDIA", "PHONE", "VOICE"]
VW_KEYS_R = ["MENU", "CAR", "SOUND", "SETUP"]


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button, painted over whatever is under it."""
    if T.name == "vw-mib2":
        vw_key(a, x, y, 9, 9, pressed, 2.0)
        ink = T.accent_hi if pressed else ((226, 232, 240) if lit else (120, 126, 136))
    else:
        cl_key(a, x, y, 9, 9, pressed, 2.0)
        ink = T.accent if pressed else ((226, 230, 236) if lit else (150, 154, 160))
    caption_glyph(a, kind, x, y, ink)


def vw_title_keys(a, lit, active, logo=True):
    """The MIB II hard keys along the top: four left, the roundel, four right (key labels only)."""
    lo, hi = 17, 241
    c = (lo + hi) // 2
    kw, gap = 25, 1
    lefts = [lo + i * (kw + gap) for i in range(4)]
    rights = [hi - 4 * kw - 3 * gap + i * (kw + gap) for i in range(4)]
    for label, kx in list(zip(VW_KEYS_L, lefts)) + list(zip(VW_KEYS_R, rights)):
        vw_key(a, kx, 2, kw, 10, False, 2.0)
        on = lit and label == active
        ink = T.accent_hi if on else ((214, 220, 228) if lit else (104, 110, 120))
        text_center(a, TINY, label, kx + kw // 2 + (kw % 2 == 0), 4, ink)
    if logo:
        vw_logo(a, c - 5, 1, 12, lit)


def vw_logo(a, x, y, size, lit=True):
    """The Volkswagen roundel (simple-icons' monochrome mark), white on the glass."""
    path = os.path.join(SCRATCH, f"vw-{size * 4}.png")
    if not os.path.exists(path):
        subprocess.run(["/usr/bin/rsvg-convert", "-h", str(size * 4),
                        os.path.join(SRC, "vw-logo", "volkswagen.svg"), "-o", path], check=True)
    im = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
    m = np.asarray(im, dtype=np.float32)[:, :, 3] / 255
    col = (226, 232, 240) if lit else (120, 126, 136)
    paint(a, x, y, m, col)


def main_titlebar(lit, which="main"):
    a = new(275, 14)
    surface(a, 0, 0, 275, 14, top=0)
    if T.name == "vw-mib2":
        rect(a, 0, 0, 275, 1, (64, 66, 72))
        rect(a, 0, 0, 1, 14, (52, 54, 60))
        rect(a, 274, 0, 1, 14, (4, 4, 5))
        if which == "main":
            vw_title_keys(a, lit, "MEDIA", logo=True)
        else:
            vw_title_keys(a, lit, "SOUND", logo=False)
            text_center(a, TINY, "EQ", 129, 5, (214, 220, 228) if lit else (104, 110, 120))
        mini_button(a, 6, 3, "options", lit)
    else:
        rect(a, 0, 0, 275, 1, (240, 242, 245))
        rect(a, 0, 0, 1, 14, (230, 232, 236))
        rect(a, 274, 0, 1, 14, (104, 108, 114))
        ink = (14, 16, 20) if lit else (122, 126, 132)
        if which == "main":
            clarion_wordmark(a, 20, 4 - 1, ink, shadow=None if not lit else (226, 229, 233))
            draw_text(a, TINY, "MP3/WMA CD RECEIVER", 70, 5, CL_PRINT if lit else (140, 144, 150))
            s = "50W X 4"
            draw_text(a, TINY, s, 238 - text_w(TINY, s), 5, CL_PRINT if lit else (140, 144, 150))
        else:
            s = "EQUALIZER"
            text_center(a, FONT5, s, 137, 5, ink)
        # a thin groove under the strip
        rect(a, 1, 13, 273, 1, (150, 154, 160))
        mini_button(a, 6, 3, "options", lit)
    if which == "main":
        mini_button(a, 244, 3, "minimize", lit)
        mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, T.disp)
    if T.name == "vw-mib2":
        rect(a, 0, 0, 8, 43, (10, 14, 22))
        for letter, y, h in CLUTTER_SLOTS:
            on = letter in lit_letters
            if on:
                paint(a, 0, y, rr_m(8, h, 0.5, 0, 7.5, h, 1.5), T.accent_lo)
            draw_text(a, TINY, letter, 2, y + (h - 5) // 2, T.accent_hi if on else (96, 110, 130))
        rect(a, 7, 0, 1, 43, (24, 32, 46))
    else:
        rect(a, 0, 0, 8, 43, (14, 16, 18))
        rect(a, 1, 1, 6, 41, T.disp)
        for letter, y, h in CLUTTER_SLOTS:
            on = letter in lit_letters
            draw_text(a, TINY, letter, 2, y + (h - 5) // 2, T.accent if on else T.dim)
    return a


def make_titlebar():
    a = new(344, 87)
    surface(a, 0, 0, 344, 87, top=0, total=87)
    lit, dim = main_titlebar(True), main_titlebar(False)
    a[0:14, 27:302] = lit
    a[15:29, 27:302] = dim
    a[29:43, 27:302] = lit
    a[42:56, 27:302] = dim
    # caption buttons: each cell is the titlebar under it, normal and pressed
    for kind, sx, x in (("options", 6, 0), ("minimize", 244, 9), ("close", 264, 18)):
        cell = lit[3:12, sx:sx + 9].copy()
        a[0:9, x:x + 9] = cell
        p = lit[3:12, sx:sx + 9].copy()
        mini_button(p, 0, 0, kind, True, pressed=True)
        a[9:18, x:x + 9] = p
    a[18:27, 0:9] = lit[3:12, 254:263]
    p = lit[3:12, 254:263].copy()
    mini_button(p, 0, 0, "shade", True, pressed=True)
    a[18:27, 9:18] = p
    unlit = clutter_bar("")
    on = clutter_bar("OAIDV")
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = on[y:y + h]
    return a


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116)
# ------------------------------------------------------------------------------------------

NOTE = G("..##.", "..#.#", "..#..", "###..", "###..")
CL_WIN = (9, 17, 260, 54)        # Clarion's display window: x, y, w, h (rim included)
VW_SCREEN_R = (8, 16, 261, 70)   # the MIB screen


def make_main():
    a = new(275, 116)
    surface(a, 0, 0, 275, 116)
    frame_edges(a, 0, 0, 275, 116)
    if T.name == "vw-mib2":
        x, y, w, h = VW_SCREEN_R
        screen_box(a, x, y, w, h, r=3)
        # a faint top-down glow on the glass
        for r in range(1, 6):
            rect(a, x + 3, y + r, w - 6, 1, lerp(VW_SCREEN, (20, 30, 46), (6 - r) / 10))
        a[22:65, 10:18] = clutter_bar("")
        card(a, 21, 20, 84, 40)                     # time + analyzer tile
        card(a, 108, 20, 160, 35)                   # title / kbps card
        rect(a, 112, 37, 152, 1, T.line)
        for yy in (29, 34):
            rect(a, 73, yy, 2, 2, T.ink)
        draw_text(a, TINY, "KBPS", 129, 44, T.dim)
        draw_text(a, TINY, "KHZ", 169, 44, T.dim)
        # the source tile under the time
        paint(a, 21, 61, rr_m(84, 10, 0, 0, 84, 10, 2.5), T.line)
        paint(a, 21, 61, rr_m(84, 10, 1, 1, 83, 9, 1.5), (9, 13, 21))
        draw_text(a, NOTE_FONT, "n", 25, 63, T.accent)
        draw_text(a, TINY, "MEDIA", 33, 63, T.ink)
        draw_text(a, TINY, "USB", 101 - text_w(TINY, "USB"), 63, T.dim)
        # knobs either side of the hard keys, a chrome strip along the bottom
        knob(a, 8.0, 98.5, 6.5, power=True)
        knob(a, 259.5, 98.5, 6.5)
        rect(a, 18, 110, 230, 1, (150, 154, 160))
        rect(a, 18, 111, 230, 1, (60, 62, 66))
    else:
        x, y, w, h = CL_WIN
        screen_box(a, x, y, w, h, r=3)
        a[22:65, 10:18] = clutter_bar("")
        # display furniture (all on the window's black)
        draw_text(a, TINY, "MP3", 24, 21, T.accent)
        draw_text(a, TINY, "TRK", 48, 21, T.dim)
        draw_text(a, TINY, "TIME", 78, 21, T.dim)
        for yy in (29, 34):
            rect(a, 73, yy, 2, 2, T.accent)
        rect(a, 106, 21, 1, 34, T.line)
        for xx in range(109, 266, 2):
            px(a, xx, 34, T.line)
        draw_text(a, TINY, "KBPS", 129, 44, T.accent)
        draw_text(a, TINY, "KHZ", 169, 44, T.accent)
        for xx in range(22, 266, 2):
            px(a, xx, 55, T.line)
        for i, s in enumerate(("SCN", "RPT", "RDM")):
            draw_text(a, TINY, s, 24 + 27 * i, 61, T.dim)
        # the big volume knob, bottom right (the About spot is its cap)
        knob(a, 259.5, 98.5, 10.5)
        # the faceplate's lower chamfer
        for r, c in enumerate([(150, 154, 160), (128, 132, 138), (116, 120, 126)]):
            rect(a, 1, 112 + r, 273, 1, c)
        draw_text(a, TINY, "OPEN", 141, 107, CL_PRINT)
    a[0:14, :] = main_titlebar(True)
    return a


NOTE_FONT = {"n": NOTE}


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36), shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------

CB = [("previous", 0, 23, 18, 16, 88), ("play", 23, 23, 18, 39, 88), ("pause", 46, 23, 18, 62, 88),
      ("stop", 69, 23, 18, 85, 88), ("next", 92, 22, 18, 108, 88)]


def make_cbuttons(main):
    a = new(136, 36)
    for kind, x, w, h, mx, my in CB + [("eject", 114, 22, 16, 136, 89)]:
        for pressed, y in ((False, 0), (True, h)):
            cell = main[my:my + h, mx:mx + w].copy()
            kw = w - 1 if kind != "next" else w - 1
            key(cell, 1 if kind == "previous" else 0, 0, kw - (1 if kind == "previous" else 0), h, pressed)
            o = 1 if pressed else 0
            cx = (1 + kw) // 2 if kind == "previous" else kw // 2
            transport_icon(cell, kind, cx, h // 2 - (1 if T.name == "clarion" else 0) + o, key_ink(pressed))
            a[y:y + h, x:x + w] = cell
    return a


REPEAT_ICON = G("........#..", "##########.", "#.......#..", "#.........#", "..#.......#", ".##########",
                "..#........")


def toggle_cell(bg, w, h, label, on, pressed, kind="hard"):
    """shufrep's toggles: a hard key with its label and an indicator (shuffle/repeat), or
    an on-screen / on-display soft label (EQ, PL)."""
    a = bg.copy()
    o = 1 if pressed else 0
    if kind == "hard":
        key(a, 0, 0, w - 1, h, pressed)
        ink = key_ink(pressed, on)
        if T.name == "vw-mib2" and label == "REPEAT":
            draw_text(a, {"r": REPEAT_ICON}, "r", (w - 1 - 11) // 2, 3 + o, ink)
            if on:
                rect(a, 5, h - 4 + o, w - 11, 1, T.accent)
        elif T.name == "vw-mib2":
            text_center(a, TINY, label, (w - 1) // 2 + 1, 4 + o, ink)
            if on:
                rect(a, 5, h - 4 + o, w - 11, 1, T.accent)
        else:
            tw = text_w(TINY, label)
            tx = (w - 1 - tw - 5) // 2
            draw_text(a, TINY, label, tx, 4 + o, ink)
            lx = tx + tw + 3
            rect(a, lx, 5 + o, 2, 3, T.accent if on else (12, 14, 16))
            if on:
                px(a, lx - 1, 6 + o, lerp(T.accent, (40, 41, 45), 0.5))
                px(a, lx + 2, 6 + o, lerp(T.accent, (40, 41, 45), 0.5))
    else:
        if T.name == "vw-mib2":
            if on:
                paint(a, 0, 0, rr_m(w, h, 0.5, 0.5, w - 0.5, h - 0.5, 2.5), T.accent_hi if pressed else T.accent)
                ink = (255, 255, 255)
            else:
                paint(a, 0, 0, rr_m(w, h, 0.5, 0.5, w - 0.5, h - 0.5, 2.5), (60, 78, 104) if pressed else T.line)
                paint(a, 0, 0, rr_m(w, h, 1.5, 1.5, w - 1.5, h - 1.5, 1.5), (26, 36, 52) if pressed else (9, 13, 21))
                ink = (196, 206, 220)
            text_center(a, TINY, label, w // 2 + (1 if w % 2 == 0 else 0), 4, ink)
        else:
            col = T.accent if on else T.dim
            if pressed:
                col = T.accent_hi if on else (40, 110, 130)
            rect(a, 1, 1, w - 2, 1, col)
            rect(a, 1, h - 2, w - 2, 1, col)
            rect(a, 1, 1, 1, h - 2, col)
            rect(a, w - 2, 1, 1, h - 2, col)
            text_center(a, TINY, label, w // 2 + 1, 4, col)
    return a


def make_shufrep(main):
    a = new(92, 85)
    surface(a, 0, 0, 92, 85, top=40)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        rep = "REPEAT" if T.name == "vw-mib2" else "RPT"
        shu = "SHUFFLE" if T.name == "vw-mib2" else "RDM"
        a[y:y + 15, 0:28] = toggle_cell(main[89:104, 210:238], 28, 15, rep, on, pressed)
        a[y:y + 15, 28:75] = toggle_cell(main[89:104, 164:211], 47, 15, shu, on, pressed)
    for x, label, pressed, mx in [(0, "EQ", False, 219), (23, "PL", False, 242), (46, "EQ", True, 219),
                                  (69, "PL", True, 242)]:
        bg = main[58:70, mx:mx + 23]
        a[61:73, x:x + 23] = toggle_cell(bg, 23, 12, label, False, pressed, kind="soft")
        a[73:85, x:x + 23] = toggle_cell(bg, 23, 12, label, True, pressed, kind="soft")
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T.disp)
    off = (52, 66, 88) if T.name == "vw-mib2" else T.dim
    on = T.accent
    for y, lit in ((0, True), (12, False)):
        col = on if lit else off
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 42, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T.disp)
    ink = T.ink
    tri_right(a, 2, 1, 7, ink)
    rect(a, 9 + 2, 1, 2, 7, ink)
    rect(a, 9 + 5, 1, 2, 7, ink)
    rect(a, 18 + 2, 2, 5, 5, ink)
    rect(a, 36, 0, 3, 9, T.disp)
    rect(a, 39 + 1, 3, 1, 3, T.accent)
    return a


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


def seven_seg(a, x, y, lit_segs):
    rect(a, x, y, 9, 13, T.disp)
    for s, cells in SEG.items():
        for r, c in cells:
            px(a, x + c, y + r, T.accent if s in lit_segs else (7, 20, 25))


def mib_digit(ch):
    """A 9x13 cell with ch rendered from Open Sans (the MIB screen's clean sans)."""
    img = Image.new("RGB", (9 * 4, 13 * 4), T.disp)
    f = ImageFont.truetype("/usr/share/fonts/open-sans/OpenSans-Regular.ttf", 15 * 4)
    d = ImageDraw.Draw(img)
    if ch == "-":
        d.rectangle((1 * 4, 6 * 4, 7 * 4 - 1, 7 * 4 + 1), fill=T.ink)
    else:
        d.text((4.5 * 4, 6.5 * 4), ch, fill=T.ink, font=f, anchor="mm")
    return np.asarray(img.resize((9, 13), Image.BOX), dtype=np.int32)


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T.disp)
    for n in range(10):
        if T.name == "vw-mib2":
            a[:, 9 * n:9 * n + 9] = mib_digit(str(n))
        else:
            seven_seg(a, 9 * n, 0, DIGIT_SEGS[n])
    if T.name == "clarion":
        seven_seg(a, 90, 0, "")
    if ex:
        if T.name == "vw-mib2":
            a[:, 99:108] = mib_digit("-")
        else:
            seven_seg(a, 99, 0, "g")
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, T.disp)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key_ = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key_, col * 5, row * 6, T.ink)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def seek_track(a, x, w):
    """The seek bar's groove across a (10 rows tall)."""
    if T.name == "vw-mib2":
        rect(a, x, 4, w, 2, (40, 52, 72))
        rect(a, x, 4, w, 1, (52, 66, 90))
    else:
        rect(a, x, 2, w, 1, (110, 114, 120))
        rect(a, x, 3, w, 4, (14, 15, 17))
        rect(a, x, 7, w, 1, (232, 234, 238))
        rect(a, x, 5, w, 1, (26, 28, 31))


def seek_thumb(a, x, pressed):
    if T.name == "vw-mib2":
        paint(a, x, 0, circle_m(29, 10, 14.5, 5.3, 4.6), (0, 0, 0), 0.6)
        paint(a, x, 0, circle_m(29, 10, 14.5, 5, 4.4), T.accent_hi if pressed else T.accent)
        paint(a, x, 0, circle_m(29, 10, 14.5, 5, 3.0), (255, 255, 255) if not pressed else (230, 246, 255))
    else:
        paint(a, x, 0, rr_m(29, 10, 7, 0.5, 22, 10, 2), (20, 21, 24))
        face = vgrad_arr(29, 10, [(28, 29, 32), (36, 38, 42)] if pressed else [(92, 94, 100), (46, 48, 52)])
        paint(a, x, 0, rr_m(29, 10, 8, 1.5, 21, 9, 1.5), face)
        rect(a, x + 10, 4 + (1 if pressed else 0), 9, 1, T.accent_hi if pressed else T.accent)


def make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    seek_track(a, 0 if T.name == "clarion" else 2, 248 if T.name == "clarion" else 244)
    for x, pressed in ((248, False), (278, True)):
        a[0:10, x:x + 29] = a[0:10, 100:129]
        seek_thumb(a, x, pressed)
    return a


def slider_thumb(a, x, y, pressed):
    """14 x 11 volume/balance thumb."""
    if T.name == "vw-mib2":
        rect(a, x, y, 14, 11, VW_SCREEN)
        rect(a, x, y + 5, 14, 2, (36, 48, 66))
        paint(a, x, y, circle_m(14, 11, 7, 5.8, 5.0), (0, 0, 0), 0.6)
        paint(a, x, y, circle_m(14, 11, 7, 5.5, 4.8), T.accent_hi if pressed else (210, 218, 228))
        paint(a, x, y, circle_m(14, 11, 7, 5.5, 3.6), (255, 255, 255))
    else:
        # a block cursor on the display
        rect(a, x + 1, y, 12, 11, T.disp)
        col = T.accent_hi if pressed else T.accent
        rect(a, x + 2, y + 1, 10, 1, col)
        rect(a, x + 2, y + 9, 10, 1, col)
        rect(a, x + 2, y + 1, 1, 9, col)
        rect(a, x + 11, y + 1, 1, 9, col)
        rect(a, x + 4, y + 3, 6, 5, lerp(col, T.disp, 0.55))


def make_volume(main):
    a = new(68, 433)
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = main[57:72, 107:175]
        level = (i + 1) / 28
        if T.name == "vw-mib2":
            fill_to = 7 + round(level * 54)
            rect(a, 3, y + 5, 62, 2, (36, 48, 66))
            rect(a, 3, y + 5, fill_to - 3, 2, T.accent)
            px(a, 3, y + 5, lerp(T.accent, VW_SCREEN, 0.4))
        else:
            segs = 20
            lit = round(level * segs)
            for k in range(segs):
                sx = 3 + 3 * k
                hgt = 2 + round(6 * k / (segs - 1))
                rect(a, sx, y + 10 - hgt, 2, hgt, T.accent if k < lit else T.dim)
        rect(a, 0, y + 13, 68, 2, main[70, 107].tolist())
    slider_thumb(a, 0, 422, True)
    slider_thumb(a, 15, 422, False)
    return a


def make_balance(main):
    a = new(68, 433)
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = main[57:72, 177:215]
        t = i / 27
        if T.name == "vw-mib2":
            rect(a, 12, y + 5, 32, 2, (36, 48, 66))
            reach = round(15 * t)
            rect(a, 28 - reach, y + 5, 2 * reach, 2, T.accent)
            rect(a, 27, y + 3, 2, 6, (150, 166, 186))
        else:
            reach = round(6 * t)
            for k in range(6):
                for sx in (28 + 3 + 3 * k, 28 - 4 - 3 * k):
                    rect(a, sx, y + 4, 2, 5, T.accent if k < reach else T.dim)
            rect(a, 28, y + 3, 1, 7, T.accent)
        rect(a, 9, y + 13, 38, 2, main[70, 177].tolist())
    slider_thumb(a, 0, 422, True)
    slider_thumb(a, 15, 422, False)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
EQ_SLIDER_X = [21] + [78 + 18 * i for i in range(10)]


def eq_slider_frame(bg, n):
    """14 x 63: the slider's track for value n of 0..27 (27 = +12 dB)."""
    a = bg.copy()
    v = n / 27
    centre = round((1 - v) * 51) + 5
    if T.name == "vw-mib2":
        rect(a, 6, 3, 2, 57, (36, 48, 66))
        rect(a, 6, centre, 2, 60 - centre, T.accent)
        for yy in (3, 31, 59):
            rect(a, 2, yy, 2, 1, (52, 66, 88))
            rect(a, 10, yy, 2, 1, (52, 66, 88))
    else:
        rect(a, 1, 0, 12, 63, T.disp)
        for k in range(14):
            yy = 58 - 4 * k
            on = yy + 1 >= centre
            rect(a, 3, yy, 8, 3, T.accent if on else T.dim)
    return a


def eq_thumb(bg, pressed):
    """11 x 11, drawn at the slider's x + 1."""
    a = bg.copy()
    if T.name == "vw-mib2":
        rect(a, 5, 0, 2, 5, (36, 48, 66))
        rect(a, 5, 6, 2, 5, T.accent)
        paint(a, 0, 0, circle_m(11, 11, 5.5, 5.8, 4.8), (0, 0, 0), 0.6)
        paint(a, 0, 0, circle_m(11, 11, 5.5, 5.5, 4.6), T.accent_hi if pressed else (210, 218, 228))
        paint(a, 0, 0, circle_m(11, 11, 5.5, 5.5, 3.4), (255, 255, 255))
    else:
        rect(a, 0, 0, 11, 11, T.disp)
        col = T.accent_hi if pressed else (236, 250, 255)
        rect(a, 0, 3, 11, 1, col)
        rect(a, 0, 7, 11, 1, col)
        rect(a, 0, 3, 1, 5, col)
        rect(a, 10, 3, 1, 5, col)
        rect(a, 2, 5, 7, 1, T.accent)
    return a


def eq_body():
    a = new(275, 116)
    surface(a, 0, 0, 275, 116)
    frame_edges(a, 0, 0, 275, 116)
    if T.name == "vw-mib2":
        screen_box(a, 8, 15, 260, 98, r=3)
        paint(a, 85, 16, rr_m(115, 21, 0, 0, 115, 21, 2.5), T.line)
        paint(a, 85, 16, rr_m(115, 21, 1, 1, 114, 20, 1.5), T.disp)
        lab = T.dim
        for lbl, yy in (("+12", 41), ("0", 66), ("-12", 92)):
            text_center(a, TINY, lbl, 58, yy, lab)
        rect(a, 40, 38, 1, 63, T.line)
        for xx in EQ_SLIDER_X:
            a[38:101, xx:xx + 14] = eq_slider_frame(a[38:101, xx:xx + 14], 14)
        text_center(a, TINY, "PREAMP", 28, 105, lab)
        for i, lbl in enumerate(EQ_BANDS):
            text_center(a, TINY, lbl, 78 + 18 * i + 7, 105, lab)
    else:
        screen_box(a, 85, 16, 115, 21, r=2)
        screen_box(a, 16, 38, 246, 63, r=2)
        for lbl, yy in (("+12", 41), ("0", 66), ("-12", 92)):
            text_center(a, TINY, lbl, 59, yy, T.accent)
        rect(a, 40, 40, 1, 59, T.line)
        for xx in EQ_SLIDER_X:
            a[38:101, xx:xx + 14] = eq_slider_frame(a[38:101, xx:xx + 14], 14)
        text_center(a, TINY, "PREAMP", 28, 105, CL_INK)
        for i, lbl in enumerate(EQ_BANDS):
            text_center(a, TINY, lbl, 78 + 18 * i + 7, 105, CL_INK)
        draw_text(a, TINY, "BEAT EQ", 214, 31, CL_PRINT)
        for r, c in enumerate([(150, 154, 160), (128, 132, 138), (116, 120, 126)]):
            rect(a, 1, 112 + r, 273, 1, c)
    a[0:14, :] = main_titlebar(True, "eq")
    return a


def eq_toggle(bg, w, label, on, pressed):
    a = bg.copy()
    if T.name == "vw-mib2":
        return toggle_cell(a, w, 12, label, on, pressed, kind="soft")
    cl_key(a, 0, 0, w, 12, pressed, 2.5)
    o = 1 if pressed else 0
    tw = text_w(TINY, label)
    tx = (w - tw - 4) // 2
    draw_text(a, TINY, label, tx, 3 + o, (226, 230, 236) if not pressed else T.accent)
    rect(a, tx + tw + 2, 4 + o, 2, 3, T.accent if on else (12, 14, 16))
    return a


def make_eqmain():
    a = new(275, 315)
    surface(a, 0, 0, 275, 315, top=0, total=315)
    body = eq_body()
    a[0:116, :] = body
    lit, dim = main_titlebar(True, "eq"), main_titlebar(False, "eq")
    p = lit[3:12, 264:273].copy()
    mini_button(p, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = p
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        bx = 14 if label == "ON" else 40
        a[119:131, x:x + w] = eq_toggle(body[18:30, bx:bx + w], w, label, on, pressed)
    a[134:148, :] = lit
    a[149:163, :] = dim
    thumb_bg = body[38 + 26:38 + 37, 22:33]
    a[164:175, 0:11] = eq_thumb(thumb_bg, False)
    a[176:187, 0:11] = eq_thumb(thumb_bg, True)
    bg = body[38:101, 21:35]
    for n in range(28):
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = eq_slider_frame(bg, n)
    for y, pressed in ((164, False), (176, True)):
        cell = body[18:30, 217:261].copy()
        if T.name == "vw-mib2":
            cell = toggle_cell(cell, 44, 12, "PRESETS", False, pressed, kind="soft")
        else:
            cl_key(cell, 0, 0, 44, 12, pressed, 2.5)
            text_center(cell, TINY, "PRESETS", 22, 3 + (1 if pressed else 0),
                        T.accent if pressed else (226, 230, 236))
        a[y:y + 12, 224:268] = cell
    # graph: background, preamp line, the curve's colours
    rect(a, 0, 294, 113, 19, T.disp)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, T.line)
    for x in range(1, 113, 12):
        for y in range(0, 19, 2):
            px(a, x, 294 + y, T.line)
    for r in range(19):
        px(a, 115, 294 + r, ramp([T.accent_hi, T.accent, T.accent, T.accent_hi], r / 18))
    for x in range(113):
        px(a, x, 314, lerp(T.dim if T.name == "clarion" else T.line, T.accent, 0.5) if x % 3 != 2 else T.disp)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109)
# ------------------------------------------------------------------------------------------


def bar_surface(w, h, top=0):
    a = new(w, h)
    if T.name == "vw-mib2":
        for r in range(h):
            rect(a, 0, r, w, 1, ramp(VW_BEZEL, (top + r) / 116))
    else:
        surface(a, 0, 0, w, h, top=top)
    return a


def bar20(w, lit):
    a = bar_surface(w, 20)
    rect(a, 0, 0, w, 1, (64, 66, 72) if T.name == "vw-mib2" else (240, 242, 245))
    return a


def title_plate(a, x, y, w, lit, h=11):
    """Clarion's title plate: a slim display window. VW: nothing (text straight on the glass)."""
    if T.name == "clarion":
        rect(a, x, y, w, h, CL_GLASS)
        rect(a, x, y + 1, w, h - 2, T.disp)
        rect(a, x, y + h, w, 1, (226, 229, 233))


def title_ink(lit):
    if T.name == "vw-mib2":
        return (236, 241, 247) if lit else (110, 118, 130)
    return T.accent if lit else (38, 110, 130)


def make_pledit():
    a = new(280, 186)
    a[:] = bar_surface(280, 186)
    for lit, y in ((True, 0), (False, 21)):
        # tile
        t = bar20(25, lit)
        if T.name == "vw-mib2":
            rect(t, 0, 18, 25, 1, (2, 2, 3))
        a[y:y + 20, 127:152] = t
        # top-left corner
        t = bar20(25, lit)
        rect(t, 0, 0, 1, 20, (52, 54, 60) if T.name == "vw-mib2" else (230, 232, 236))
        rect(t, 11, 19, 14, 1, (2, 2, 3) if T.name == "vw-mib2" else CL_GLASS)
        a[y:y + 20, 0:25] = t
        # title
        t = bar20(100, lit)
        if T.name == "clarion":
            title_plate(t, 2, 4, 96, lit)
        text_center(t, FONT5, "PLAYLIST" if T.name == "clarion" else "TRACK LIST", 50, 7, title_ink(lit))
        if T.name == "vw-mib2" and lit:
            draw_text(t, NOTE_FONT, "n", 8, 7, T.accent)
        a[y:y + 20, 26:126] = t
        # top-right corner: close button and the scrollbar groove's top
        t = bar20(25, lit)
        rect(t, 24, 0, 1, 20, (4, 4, 5) if T.name == "vw-mib2" else (104, 108, 114))
        mini_button(t, 14, 3, "close", lit)
        rect(t, 9, 14, 10, 6, groove_col())
        rect(t, 0, 19, 6, 1, (2, 2, 3) if T.name == "vw-mib2" else CL_GLASS)
        a[y:y + 20, 153:178] = t
    # left side
    t = bar_surface(12, 29, 40)
    rect(t, 0, 0, 1, 29, (52, 54, 60) if T.name == "vw-mib2" else (230, 232, 236))
    rect(t, 11, 0, 1, 29, (2, 2, 3) if T.name == "vw-mib2" else CL_GLASS)
    a[42:71, 0:12] = t
    # right side: list edge, the scrollbar groove at 4..13, outer edge
    t = bar_surface(20, 29, 40)
    rect(t, 0, 0, 1, 29, (2, 2, 3) if T.name == "vw-mib2" else CL_GLASS)
    rect(t, 4, 0, 10, 29, groove_col())
    if T.name == "vw-mib2":
        rect(t, 8, 0, 2, 29, (24, 32, 46))
    else:
        rect(t, 4, 0, 1, 29, CL_GLASS)
        rect(t, 13, 0, 1, 29, (226, 229, 233))
    rect(t, 19, 0, 1, 29, (4, 4, 5) if T.name == "vw-mib2" else (104, 108, 114))
    a[42:71, 31:51] = t
    t = a[3:12, 153 + 14:153 + 23].copy()
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, pressed in ((52, False), (61, True)):
        h = new(8, 18, groove_col())
        if T.name == "vw-mib2":
            paint(h, 0, 0, rr_m(8, 18, 2, 1, 6, 17, 2), T.accent_hi if pressed else (196, 206, 220))
        else:
            paint(h, 0, 0, rr_m(8, 18, 0.5, 0.5, 7.5, 17.5, 1.5), (14, 14, 16))
            paint(h, 0, 0, rr_m(8, 18, 1.5, 1.5, 6.5, 16.5, 1), vgrad_arr(8, 18, [(214, 218, 222), (150, 154, 160)]))
            for gy in (7, 9, 11):
                rect(h, 2, gy, 4, 1, T.accent if pressed else (96, 100, 106))
        a[53:71, x:x + 8] = h

    def bottom_base(w):
        t = bar_surface(w, 38, 78)
        rect(t, 0, 0, w, 1, (2, 2, 3) if T.name == "vw-mib2" else CL_GLASS)
        rect(t, 0, 37, w, 1, (4, 4, 5) if T.name == "vw-mib2" else (96, 100, 106))
        if T.name == "vw-mib2":
            rect(t, 0, 33, w, 1, (150, 154, 160))
            rect(t, 0, 34, w, 1, (60, 62, 66))
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, (52, 54, 60) if T.name == "vw-mib2" else (230, 232, 236))
    rect(t, 0, 0, 12, 1, t[2, 5].tolist())
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        key(t, bx, 8, 22, 18, False)
        text_center(t, TINY, lbl, bx + 11, 14 if T.name == "vw-mib2" else 13, key_ink(False))
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, (4, 4, 5) if T.name == "vw-mib2" else (104, 108, 114))
    rect(t, 130, 0, 20, 1, t[2, 140].tolist())
    small_display(t, 5, 8, 58, 10)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        key(t, bx, 22, 10, 10, False, 1.5)
        mini_transport_icon(t, kind, bx, 22 - (1 if T.name == "clarion" else 0) + (0 if kind != "play" else 0),
                            key_ink(False))
    small_display(t, 64, 21, 35, 10)
    rect(t, 84, 23 + 1, 1, 1, T.ink)
    rect(t, 84, 23 + 4, 1, 1, T.ink)
    key(t, 106, 8, 22, 18, False)
    text_center(t, TINY, "LIST", 117, 14 if T.name == "vw-mib2" else 13, key_ink(False))
    grip = (150, 154, 160) if T.name == "vw-mib2" else (90, 94, 100)
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx, gy, grip)
            px(t, gx + 1, gy + 1, (0, 0, 0) if T.name == "vw-mib2" else (236, 238, 241))
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


def groove_col():
    return (10, 14, 22) if T.name == "vw-mib2" else (34, 36, 40)


def small_display(a, x, y, w, h):
    if T.name == "vw-mib2":
        paint(a, x, y, rr_m(w, h, 0, 0, w, h, 2), (0, 0, 0))
        paint(a, x, y, rr_m(w, h, 1, 1, w - 1, h - 1, 1.5), T.disp)
    else:
        rect(a, x, y, w, h, CL_GLASS)
        rect(a, x + 1, y + 1, w - 2, h - 2, T.disp)
        rect(a, x, y + h, w, 1, (226, 229, 233))


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GEN_PLATE_Y = 2


def make_gen():
    a = new(194, 109)
    a[:] = bar_surface(194, 109)
    edge_l = (52, 54, 60) if T.name == "vw-mib2" else (230, 232, 236)
    edge_r = (4, 4, 5) if T.name == "vw-mib2" else (104, 108, 114)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn):
            t = bar20(25, lit)
            fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 1, 20, edge_l)

        def left_end(t):
            title_plate(t, 21, GEN_PLATE_Y, 4, lit)
            if T.name == "clarion":
                rect(t, 20, GEN_PLATE_Y, 1, 12, CL_GLASS)

        def centre(t):
            title_plate(t, 0, GEN_PLATE_Y, 25, lit)

        def right_end(t):
            title_plate(t, 0, GEN_PLATE_Y, 4, lit)
            if T.name == "clarion":
                rect(t, 4, GEN_PLATE_Y, 1, 12, CL_GLASS)

        def fill(t):
            pass

        def right(t):
            mini_button(t, 14, 3, "close", lit)
            rect(t, 24, 0, 1, 20, edge_r)

        piece(0, left)
        piece(26, left_end)
        piece(52, centre)
        piece(78, right_end)
        piece(104, fill)
        piece(130, right)

    def bottom(w, grip, left_edge):
        t = bar_surface(w, 14, 100)
        rect(t, 0, 13, w, 1, edge_r if T.name == "vw-mib2" else (96, 100, 106))
        if T.name == "vw-mib2":
            rect(t, 0, 9, w, 1, (150, 154, 160))
            rect(t, 0, 10, w, 1, (60, 62, 66))
        if left_edge:
            rect(t, 0, 0, 1, 14, edge_l)
        else:
            rect(t, w - 1, 0, 1, 14, edge_r)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 7 - 3 * j
                    px(t, gx, gy, (150, 154, 160) if T.name == "vw-mib2" else (90, 94, 100))
                    px(t, gx + 1, gy + 1, (0, 0, 0) if T.name == "vw-mib2" else (236, 238, 241))
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = bar_surface(w, h, 40)
        if outer_left:
            rect(t, 0, 0, 1, h, edge_l)
            rect(t, w - 1, 0, 1, h, (2, 2, 3) if T.name == "vw-mib2" else CL_GLASS)
        else:
            rect(t, w - 1, 0, 1, h, edge_r)
            rect(t, 0, 0, 1, h, (2, 2, 3) if T.name == "vw-mib2" else CL_GLASS)
        a[42:42 + h, x:x + w] = t
    t = a[3:12, 130 + 14:130 + 23].copy()
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t
    # letters: each row starts at x 1, letters in cells of the title's background, 1px separators
    centre_bar = {True: a[0:20, 52:77].copy(), False: a[21:41, 52:77].copy()}
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            for r in range(7):
                rect(a, x, y + r, w, 1, centre_bar[lit][4 + r, 12].tolist())
            draw_text(a, FONT5, c, x, y + 1, title_ink(lit))
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------


def genex_colours():
    if T.name == "vw-mib2":
        return [(10, 15, 24), (214, 221, 230), (16, 17, 20), (236, 240, 246), (214, 221, 230), (40, 54, 76),
                (29, 59, 94), (20, 28, 42), (110, 200, 250), (60, 72, 92), (4, 6, 10), (38, 160, 232),
                (16, 17, 20), (30, 40, 56), (110, 200, 250), (50, 66, 90), (160, 220, 255), (10, 14, 22)]
    return [(5, 9, 12), (70, 222, 255), (180, 184, 190), (226, 230, 236), (24, 26, 30), (110, 114, 120),
            (13, 60, 78), (40, 42, 46), (226, 230, 236), (96, 98, 104), (14, 14, 16), (70, 222, 255),
            (176, 180, 186), (150, 154, 160), (52, 54, 58), (120, 124, 130), (24, 26, 30), (160, 164, 170)]


def make_genex():
    a = bar_surface(256, 64)
    rect(a, 0, 0, 256, 1, a[1, 0].tolist())
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    key(a, 0, 1, 47, 15, False)
    key(a, 0, 16, 47, 15, True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    rows = [(T.disp, "background"), (T.vis_dots, "dots")]
    spec = getattr(T, "vis_rows", None) or [ramp(T.vis, i / 15) for i in range(16)]
    rows += [(c, f"spectrum {i + 1}" + (" (top)" if i == 0 else "")) for i, c in enumerate(spec)]
    osc = [T.vis[0], T.vis[1], T.vis[1], T.vis[2], T.vis[2]]
    rows += [(c, f"oscilloscope {i + 1}") for i, c in enumerate(osc)]
    rows += [(T.vis_peak, "peaks")]
    return rows


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    p = T.pledit
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={p['Normal']}\nCurrent={p['Current']}\nNormalBG={p['NormalBG']}\n"
                f"SelectedBG={p['SelectedBG']}\nMbBG={p['NormalBG']}\nMbFG={p['Normal']}\n"
                f"Font={getattr(T, 'font', 'Arial')}\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(f"{T.title} — a skin in the style of {T.subject}.\n"
                f"{T.owner} logo © {T.owner}.\n\n"
                "A classic (Winamp 2.x format) skin drawn by a script (gen_skin.py) from gradients,\n"
                "shapes and hand-made pixel fonts.\n")


# ------------------------------------------------------------------------------------------
# vw-mib2-v2: the MIB II screen UI alone (no hardware). Black screen, a status row with a thin
# grey rule, big white centred text, light-grey gradient tiles with a red underline when
# selected, a dark soft-key bar under a red rule, thin red/orange highlights, Noto Sans Condensed.
# ------------------------------------------------------------------------------------------

V2_BLACK = (0, 0, 0)
V2_WHITE = (242, 242, 242)
V2_GREY = (150, 152, 158)
V2_RULE = (78, 80, 86)
V2_RULE_DIM = (44, 45, 49)
V2_RED = (232, 52, 38)
V2_RED_HI = (255, 104, 84)
V2_TRACK = (68, 70, 76)
V2_BAR = [(38, 42, 56), (24, 27, 37), (18, 20, 28)]   # the soft-key bar
V2_SEP = (104, 108, 120)
V2_TILE = [(232, 232, 232), (200, 200, 200), (152, 152, 154)]
V2_TILE_SEL = [(252, 252, 252), (232, 232, 232), (190, 190, 192)]
V2_TILE_INK = (36, 38, 42)
V2_FONTS = "/usr/share/fonts/google-noto/"
_tt_cache = {}


def tt_face(size, weight="CondensedSemiBold"):
    k = (size, weight)
    if k not in _tt_cache:
        _tt_cache[k] = ImageFont.truetype(os.path.join(V2_FONTS, f"NotoSans-{weight}.ttf"), size)
    return _tt_cache[k]


def tt(a, s, x, y, size, col, weight="CondensedSemiBold", anchor="la"):
    """Anti-aliased text from Noto Sans painted into a (x, y per PIL's anchor)."""
    h, w = a.shape[:2]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((x, y), s, fill=255, font=tt_face(size, weight), anchor=anchor)
    paint(a, 0, 0, np.asarray(m, dtype=np.float32) / 255, col)


def v2_rule(a, x, y, w, lit=True):
    rect(a, x, y, w, 1, V2_RULE if lit else V2_RULE_DIM)


def v2_softbar(a, x, y, w, h, top=0, total=None):
    """The soft-key bar: a red rule over a dark blue-grey gradient."""
    total = total or h
    for r in range(h):
        rect(a, x, y + r, w, 1, ramp(V2_BAR, (top + r) / max(1, total - 1)))


def v2_tile(a, x, y, w, h, sel=False, under=None):
    """A preset tile: light-grey gradient, thin dark edge, white top line. `under` draws the
    indicator bar in the last two rows (None: none, "dim": grey, "red": selected)."""
    bh = h - 3 if under is not None else h
    paint(a, x, y, rr_m(w, bh, 0, 0, w, bh, 1.2), (20, 20, 22))
    paint(a, x, y, rr_m(w, bh, 1, 1, w - 1, bh - 1, 0.6), vgrad_arr(w, bh, V2_TILE_SEL if sel else V2_TILE))
    rect(a, x + 1, y + 1, w - 2, 1, (255, 255, 255) if sel else (244, 244, 244))
    if sel:
        rect(a, x, y, w, 1, (214, 220, 230))
        rect(a, x, y, 1, bh, (214, 220, 230))
        rect(a, x + w - 1, y, 1, bh, (214, 220, 230))
    if under == "red":
        rect(a, x + 2, y + h - 2, w - 4, 2, V2_RED)
    elif under == "dim":
        rect(a, x + 2, y + h - 1, w - 4, 1, (64, 74, 92))


def v2_caption(a, x, y, kind, lit=True, pressed=False):
    rect(a, x, y, 9, 9, V2_BLACK)
    if pressed:
        paint(a, x, y, rr_m(9, 9, 0, 0, 9, 9, 1.5), (52, 54, 60))
    caption_glyph(a, kind, x, y, V2_RED_HI if pressed else (V2_WHITE if lit else (112, 114, 120)))


def v2_status_row(w, lit, title, logo=False, extra=None):
    a = new(w, 14, V2_BLACK)
    v2_rule(a, 3, 13, w - 6, lit)
    ink = V2_WHITE if lit else (112, 114, 120)
    tt(a, title, w // 2, 7, 11, ink, "CondensedSemiBold", anchor="mm")
    if logo:
        vw_logo(a, 20, 1, 11, lit)
    if extra:
        tt(a, extra, 232, 7, 9, V2_GREY if lit else (90, 92, 98), "CondensedSemiBold", anchor="rm")
    return a


def v2_main_titlebar(lit, which="main"):
    if which == "main":
        a = v2_status_row(275, lit, "Media", logo=True, extra="TP")
        v2_caption(a, 6, 3, "options", lit)
        v2_caption(a, 244, 3, "minimize", lit)
        v2_caption(a, 254, 3, "shade", lit)
    else:
        a = v2_status_row(275, lit, "Sound")
        v2_caption(a, 6, 3, "options", lit)
    v2_caption(a, 264, 3, "close", lit)
    return a


def v2_clutter(lit_letters):
    a = new(8, 43, V2_BLACK)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 0, y, 1, h, V2_RED)
        draw_text(a, TINY, letter, 3, y + (h - 5) // 2, V2_WHITE if on else (86, 88, 94))
    return a


def v2_make_titlebar():
    a = new(344, 87, V2_BLACK)
    lit, dim = v2_main_titlebar(True), v2_main_titlebar(False)
    a[0:14, 27:302] = lit
    a[15:29, 27:302] = dim
    a[29:43, 27:302] = lit
    a[42:56, 27:302] = dim
    for kind, x in (("options", 0), ("minimize", 9), ("close", 18)):
        c = new(9, 9)
        v2_caption(c, 0, 0, kind, True)
        a[0:9, x:x + 9] = c
        v2_caption(c, 0, 0, kind, True, pressed=True)
        a[9:18, x:x + 9] = c
    c = new(9, 9)
    v2_caption(c, 0, 0, "shade", True)
    a[18:27, 0:9] = c
    v2_caption(c, 0, 0, "shade", True, pressed=True)
    a[18:27, 9:18] = c
    unlit, on = v2_clutter(""), v2_clutter("OAIDV")
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = on[y:y + h]
    return a


def v2_gear(a, cx, cy, col, r=5.0):
    w = h = int(2 * r + 4)
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    lx, ly = cx - x0, cy - y0
    m = circle_m(w, h, lx, ly, r - 1.3)
    for k in range(8):
        t = k * np.pi / 4
        c, s = np.cos(t), np.sin(t)
        pts = []
        for u, v in ((r - 2, -1.0), (r + 0.2, -0.8), (r + 0.2, 0.8), (r - 2, 1.0)):
            pts.append((lx + u * c - v * s, ly + u * s + v * c))
        m = np.maximum(m, poly_m(w, h, pts))
    m = np.minimum(m, 1 - circle_m(w, h, lx, ly, 1.7))
    paint(a, x0, y0, m, col)


def v2_make_main():
    a = new(275, 116, V2_BLACK)
    a[0:14, :] = v2_main_titlebar(True)
    a[22:65, 10:18] = v2_clutter("")
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, V2_WHITE)
    tt(a, "kbps", 128, 49, 9, V2_GREY, anchor="ls")
    tt(a, "kHz", 169, 49, 9, V2_GREY, anchor="ls")
    # the red rule and the top of the soft-key bar along the bottom
    rect(a, 0, 109, 275, 1, V2_RED)
    v2_softbar(a, 0, 110, 275, 6)
    # the Setup gear in the About spot
    v2_gear(a, 259.5, 98.5, V2_WHITE)
    return a


def v2_arrow_button(a, x, y, w, h, kind, pressed):
    """MIB's outlined square arrow button ("<" / ">")."""
    s = min(w, h) - 2
    bx, by = x + (w - s) // 2, y + (h - s) // 2
    if pressed:
        rect(a, bx, by, s, s, (56, 58, 64))
    col = V2_RED if pressed else (200, 202, 208)
    rect(a, bx, by, s, 1, col)
    rect(a, bx, by + s - 1, s, 1, col)
    rect(a, bx, by, 1, s, col)
    rect(a, bx + s - 1, by, 1, s, col)
    cx, cy = bx + s / 2, by + s / 2
    d = 1 if kind == "next" else -1
    pts = [(cx - 1.5 * d, cy - 4), (cx + 2.5 * d, cy), (cx - 1.5 * d, cy + 4)]
    m = line_m(a.shape[1], a.shape[0], pts, 1.6)
    paint(a, 0, 0, m, V2_WHITE)


def line_m(w, h, pts, width):
    img = Image.new("L", (w * 4, h * 4), 0)
    ImageDraw.Draw(img).line([(px_ * 4, py_ * 4) for px_, py_ in pts], fill=255, width=int(width * 4),
                             joint="curve")
    return np.asarray(img.resize((w, h), Image.BOX), dtype=np.float32) / 255


def v2_make_cbuttons(main):
    a = new(136, 36, V2_BLACK)
    for kind, x, w, h, mx, my in CB + [("eject", 114, 22, 16, 136, 89)]:
        for pressed, y in ((False, 0), (True, h)):
            cell = main[my:my + h, mx:mx + w].copy()
            if kind in ("previous", "next"):
                v2_arrow_button(cell, 0, 0, w - 1, h - 3, kind, pressed)
                if pressed:
                    rect(cell, 3, h - 2, w - 7, 2, V2_RED)
            else:
                v2_tile(cell, 0, 0, w - 1, h, sel=pressed, under="red" if pressed else None)
                transport_icon(cell, kind, (w - 1) // 2, (h - 3) // 2, V2_TILE_INK)
            a[y:y + h, x:x + w] = cell
    return a


def v2_make_shufrep(main):
    a = new(92, 85, V2_BLACK)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        under = "red" if on else "dim"
        c = main[89:104, 210:238].copy()
        v2_tile(c, 0, 0, 27, 15, sel=pressed, under=under)
        draw_text(c, {"r": REPEAT_ICON}, "r", 8, 2, V2_TILE_INK)
        a[y:y + 15, 0:28] = c
        c = main[89:104, 164:211].copy()
        v2_tile(c, 0, 0, 46, 15, sel=pressed, under=under)
        tt(c, "Shuffle", 23, 6, 9, V2_TILE_INK, anchor="mm")
        a[y:y + 15, 28:75] = c
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        for on, y in ((False, 61), (True, 73)):
            c = new(23, 12, V2_BLACK)
            v2_tile(c, 0, 0, 22, 12, sel=pressed, under="red" if on else "dim")
            text_center(c, TINY, label, 11, 2, V2_TILE_INK)
            a[y:y + 12, x:x + 23] = c
    return a


def v2_make_monoster():
    a = new(56, 24, V2_BLACK)
    for y, lit in ((0, True), (12, False)):
        col = V2_WHITE if lit else (62, 64, 70)
        sub = a[y:y + 12, 0:29].copy()
        tt(sub, "Stereo", 15, 6, 9, col, anchor="mm")
        a[y:y + 12, 0:29] = sub
        sub = a[y:y + 12, 29:56].copy()
        tt(sub, "Mono", 13, 6, 9, col, anchor="mm")
        a[y:y + 12, 29:56] = sub
    return a


def v2_digit(ch):
    img = Image.new("L", (9 * 4, 13 * 4), 0)
    d = ImageDraw.Draw(img)
    if ch == "-":
        d.rectangle((1 * 4, 6 * 4, 7 * 4 - 1, 7 * 4 + 1), fill=255)
    else:
        d.text((4.5 * 4, 6.6 * 4), ch, fill=255, font=tt_face(17 * 4, "CondensedMedium"), anchor="mm")
    m = np.asarray(img.resize((9, 13), Image.BOX), dtype=np.float32) / 255
    a = new(9, 13, V2_BLACK)
    paint(a, 0, 0, m, V2_WHITE)
    return a


def v2_make_numbers(ex):
    a = new(108 if ex else 99, 13, V2_BLACK)
    for n in range(10):
        a[:, 9 * n:9 * n + 9] = v2_digit(str(n))
    if ex:
        a[:, 99:108] = v2_digit("-")
    return a


def v2_make_posbar(main):
    a = new(307, 10, V2_BLACK)
    rect(a, 0, 4, 248, 2, V2_TRACK)
    for x, pressed in ((248, False), (278, True)):
        rect(a, x, 4, 29, 2, V2_TRACK)
        if pressed:
            paint(a, x, 0, circle_m(29, 10, 14.5, 5, 4.6), V2_RED)
        paint(a, x, 0, circle_m(29, 10, 14.5, 5, 3.4), V2_WHITE)
    return a


def v2_thumb(a, x, y, pressed):
    rect(a, x, y, 14, 11, V2_BLACK)
    rect(a, x, y + 5, 14, 1, V2_TRACK)
    if pressed:
        paint(a, x, y, circle_m(14, 11, 7, 5.5, 5.0), V2_RED)
    paint(a, x, y, circle_m(14, 11, 7, 5.5, 3.8), V2_WHITE)


def v2_make_volume(main):
    a = new(68, 433, V2_BLACK)
    for i in range(28):
        y = i * 15
        fill_to = 7 + round((i + 1) / 28 * 54)
        rect(a, 2, y + 6, 64, 1, V2_TRACK)
        rect(a, 2, y + 5, fill_to - 2, 3, V2_RED)
    v2_thumb(a, 0, 422, True)
    v2_thumb(a, 15, 422, False)
    return a


def v2_make_balance(main):
    a = new(68, 433, V2_BLACK)
    for i in range(28):
        y = i * 15
        reach = round(15 * i / 27)
        rect(a, 11, y + 6, 34, 1, V2_TRACK)
        rect(a, 28 - reach, y + 5, 2 * reach, 3, V2_RED)
        rect(a, 27, y + 3, 2, 7, V2_GREY)
    v2_thumb(a, 0, 422, True)
    v2_thumb(a, 15, 422, False)
    return a


def v2_eq_frame(n):
    a = new(14, 63, V2_BLACK)
    v = n / 27
    centre = round((1 - v) * 51) + 5
    rect(a, 6, 3, 2, 57, V2_TRACK)
    rect(a, 6, centre, 2, 60 - centre, V2_RED)
    for yy in (3, 31, 59):
        rect(a, 1, yy, 3, 1, V2_RULE)
        rect(a, 10, yy, 3, 1, V2_RULE)
    return a


def v2_eq_thumb(pressed):
    a = new(11, 11, V2_BLACK)
    rect(a, 5, 0, 2, 5, V2_TRACK)
    rect(a, 5, 6, 2, 5, V2_RED)
    if pressed:
        paint(a, 0, 0, circle_m(11, 11, 5.5, 5.5, 5.2), V2_RED_HI)
    paint(a, 0, 0, circle_m(11, 11, 5.5, 5.5, 3.9), V2_WHITE)
    return a


def v2_eq_body():
    a = new(275, 116, V2_BLACK)
    a[0:14, :] = v2_main_titlebar(True, "eq")
    # graph frame
    rect(a, 85, 16, 115, 1, V2_RULE)
    rect(a, 85, 36, 115, 1, V2_RULE)
    rect(a, 85, 16, 1, 21, V2_RULE)
    rect(a, 199, 16, 1, 21, V2_RULE)
    for lbl, yy in (("+12 dB", 44), ("0", 69), ("-12 dB", 95)):
        tt(a, lbl, 58, yy, 8, V2_GREY, anchor="mm")
    rect(a, 40, 38, 1, 63, V2_RULE_DIM)
    for xx in EQ_SLIDER_X:
        a[38:101, xx:xx + 14] = v2_eq_frame(14)
    # the soft-key bar with the band labels
    rect(a, 0, 102, 275, 1, V2_RED)
    v2_softbar(a, 0, 103, 275, 13)
    for i, xx in enumerate(EQ_SLIDER_X):
        lbl = "Preamp" if i == 0 else EQ_BANDS[i - 1].replace("K", "k")
        tt(a, lbl, xx + 7, 109, 9 if i else 9, V2_WHITE, anchor="mm")
        if i == 0:
            rect(a, 46, 105, 1, 9, V2_SEP)
    return a


def v2_make_eqmain():
    a = new(275, 315, V2_BLACK)
    body = v2_eq_body()
    a[0:116, :] = body
    c = new(9, 9)
    v2_caption(c, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = c
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        c = new(w, 12, V2_BLACK)
        v2_tile(c, 0, 0, w - 1, 12, sel=pressed, under="red" if on else "dim")
        tt(c, label.capitalize() if label == "AUTO" else "On", (w - 1) // 2, 4, 9, V2_TILE_INK, anchor="mm")
        a[119:131, x:x + w] = c
    a[134:148, :] = v2_main_titlebar(True, "eq")
    a[149:163, :] = v2_main_titlebar(False, "eq")
    a[164:175, 0:11] = v2_eq_thumb(False)
    a[176:187, 0:11] = v2_eq_thumb(True)
    for n in range(28):
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = v2_eq_frame(n)
    for y, pressed in ((164, False), (176, True)):
        c = new(44, 12, V2_BLACK)
        v2_tile(c, 0, 0, 44, 12, sel=pressed, under="red" if pressed else "dim")
        tt(c, "Presets", 22, 4, 9, V2_TILE_INK, anchor="mm")
        a[y:y + 12, 224:268] = c
    rect(a, 0, 294, 113, 19, V2_BLACK)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, V2_RULE_DIM)
    for r in range(19):
        px(a, 115, 294 + r, ramp([V2_RED_HI, V2_RED, V2_RED, V2_RED_HI], r / 18))
    for x in range(113):
        px(a, x, 314, V2_GREY if x % 3 != 2 else V2_BLACK)
    return a


def v2_softkey(a, x, y, w, label, icon, pressed=False):
    """A soft key in the bar: label over a small white icon."""
    if pressed:
        rect(a, x, y, w, 18, (60, 64, 78))
    tt(a, label, x + w // 2, y + 4, 9, V2_WHITE, anchor="mm")
    cx, cy = x + w // 2, y + 13
    if icon == "plus":
        rect(a, cx - 3, cy, 7, 1, V2_WHITE)
        rect(a, cx, cy - 3, 1, 7, V2_WHITE)
    elif icon == "minus":
        rect(a, cx - 3, cy, 7, 1, V2_WHITE)
    elif icon == "check":
        for i, (dx, dy) in enumerate([(-3, 0), (-2, 1), (-1, 2), (0, 1), (1, 0), (2, -1), (3, -2)]):
            px(a, cx + dx, cy + dy, V2_WHITE)
    elif icon == "dots":
        for dx in (-3, 0, 3):
            px(a, cx + dx, cy, V2_WHITE)
    elif icon == "list":
        for dy in (-2, 0, 2):
            px(a, cx - 4, cy + dy, V2_WHITE)
            rect(a, cx - 2, cy + dy, 6, 1, V2_WHITE)


def v2_make_pledit():
    a = new(280, 186, V2_BLACK)
    for lit, y in ((True, 0), (False, 21)):
        t = new(25, 20, V2_BLACK)
        v2_rule(t, 0, 16, 25, lit)
        a[y:y + 20, 127:152] = t
        t = new(25, 20, V2_BLACK)
        v2_rule(t, 3, 16, 22, lit)
        a[y:y + 20, 0:25] = t
        t = new(100, 20, V2_BLACK)
        v2_rule(t, 0, 16, 100, lit)
        tt(t, "Track list", 50, 8, 11, V2_WHITE if lit else (112, 114, 120), anchor="mm")
        a[y:y + 20, 26:126] = t
        t = new(25, 20, V2_BLACK)
        v2_rule(t, 0, 16, 22, lit)
        v2_caption(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t
    a[42:71, 0:12] = 0
    t = new(20, 29, V2_BLACK)
    rect(t, 8, 0, 1, 29, V2_RULE_DIM)
    a[42:71, 31:51] = t
    c = new(9, 9)
    v2_caption(c, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = c
    for x, pressed in ((52, False), (61, True)):
        h = new(8, 18, V2_BLACK)
        rect(h, 3, 0, 1, 18, V2_RULE_DIM)
        paint(h, 0, 0, rr_m(8, 18, 2, 1, 6, 17, 1.5), V2_RED if pressed else (200, 202, 208))
        a[53:71, x:x + 8] = h

    def bottom_base(w):
        t = new(w, 38, V2_BLACK)
        rect(t, 0, 2, w, 1, V2_RED)
        v2_softbar(t, 0, 3, w, 35)
        return t

    t = bottom_base(125)
    for bx, lbl, icon in ((14, "Add", "plus"), (43, "Rem", "minus"), (72, "Sel", "check"), (101, "Misc", "dots")):
        v2_softkey(t, bx, 8, 22, lbl, icon)
        if bx > 14:
            rect(t, bx - 4, 9, 1, 16, V2_SEP)
    rect(t, 125 - 1, 9, 1, 16, V2_SEP)
    a[72:110, 0:125] = t
    t = bottom_base(150)
    rect(t, 5, 8, 58, 10, V2_BLACK)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        mini_transport_icon(t, kind, 3 + 10 * k, 22, V2_WHITE)
    rect(t, 64, 21, 35, 10, V2_BLACK)
    rect(t, 84, 24, 1, 1, V2_WHITE)
    rect(t, 84, 27, 1, 1, V2_WHITE)
    rect(t, 102, 9, 1, 16, V2_SEP)
    v2_softkey(t, 106, 8, 22, "List", "list")
    for k in range(4):
        for j in range(k + 1):
            px(t, 145 - 3 * k + 3 * j, 29 - 3 * j, V2_GREY)
    a[72:110, 126:276] = t
    a[0:38, 179:204] = bottom_base(25)
    return a


def v2_make_gen():
    a = new(194, 109, V2_BLACK)
    for lit, y in ((True, 0), (False, 21)):
        for px0 in (0, 26, 52, 78, 104, 130):
            t = new(25, 20, V2_BLACK)
            v2_rule(t, 3 if px0 == 0 else 0, 16, 22 if px0 in (0, 130) else 25, lit)
            if px0 == 130:
                v2_caption(t, 14, 3, "close", lit)
            a[y:y + 20, px0:px0 + 25] = t

    def bottom(w, grip):
        t = new(w, 14, V2_BLACK)
        rect(t, 0, 4, w, 1, V2_RED)
        v2_softbar(t, 0, 5, w, 9)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    px(t, w - 4 - 3 * k + 3 * j, 11 - 3 * j, V2_GREY)
        return t

    a[42:56, 0:125] = bottom(125, False)
    a[57:71, 0:125] = bottom(125, True)
    a[72:86, 127:152] = bottom(25, False)
    for x, w, h in ((127, 11, 29), (158, 11, 24), (139, 8, 29), (170, 8, 24)):
        a[42:42 + h, x:x + w] = 0
    c = new(9, 9)
    v2_caption(c, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = c
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for ch in GEN_LETTERS:
            w = glyph_w(FONT5, ch) + 1
            rect(a, x, y, w, 7, V2_BLACK)
            draw_text(a, FONT5, ch, x, y + 1, V2_WHITE if lit else (112, 114, 120))
            x += w + 1
        assert x <= 194, x
    return a


def v2_make_genex():
    a = new(256, 64, (14, 16, 22))
    cols = [(0, 0, 0), (242, 242, 242), (14, 16, 22), (36, 38, 42), (242, 242, 242), (70, 72, 78),
            (58, 58, 64), (30, 34, 46), (242, 242, 242), (90, 94, 104), (0, 0, 0), (232, 52, 38),
            (14, 16, 22), (40, 42, 48), (200, 202, 208), (60, 62, 68), (232, 52, 38), (10, 10, 12)]
    for i, c in enumerate(cols):
        px(a, 48 + 2 * i, 0, c)
    v2_tile(a, 0, 1, 47, 15)
    v2_tile(a, 0, 16, 47, 15, sel=True)
    return a


V2_MAKERS = {
    "main.bmp": v2_make_main, "titlebar.bmp": v2_make_titlebar, "cbuttons.bmp": v2_make_cbuttons,
    "shufrep.bmp": v2_make_shufrep, "posbar.bmp": v2_make_posbar, "volume.bmp": v2_make_volume,
    "balance.bmp": v2_make_balance, "monoster.bmp": v2_make_monoster, "numbers.bmp": lambda ex: v2_make_numbers(ex),
    "nums_ex.bmp": lambda ex: v2_make_numbers(ex), "pledit.bmp": v2_make_pledit, "eqmain.bmp": v2_make_eqmain,
    "gen.bmp": v2_make_gen, "genex.bmp": v2_make_genex,
}


# ------------------------------------------------------------------------------------------
# clarion-adx5655z: the Clarion ADX5655z (double-DIN tuner/CD/cassette with spectrum analyzer,
# c. 2002). A black gloss faceplate in a sculpted silver surround, one wide VFD window with
# blue/cyan segment bars capped in orange, a pale blue-white dot-matrix readout, orange outlined
# lozenges, translucent pale-blue preset keys, grey rubber keys and the round silver rocker pad.
# ------------------------------------------------------------------------------------------

AX_VFD = (16, 10, 22)
AX_TINY = dict(TINY, N=G("#..#", "##.#", "#.##", "#..#", "#..#"))
AX_GHOST = (44, 32, 58)
AX_LABEL = (78, 62, 98)
AX_TEXT = (214, 230, 255)
AX_ORANGE = (255, 146, 36)
AX_AMBER = (255, 196, 70)
AX_BLUE = [(140, 220, 255), (88, 170, 255), (52, 104, 228)]
AX_GLOSS = [(34, 34, 38), (14, 14, 17), (6, 6, 8), (12, 12, 15)]
AX_SILVER = [(232, 234, 238), (176, 180, 186), (118, 122, 128), (162, 166, 172)]
AX_PALE = [(214, 236, 252), (150, 200, 240), (96, 156, 214)]
AX_PALE_ON = [(240, 252, 255), (190, 232, 255), (130, 196, 245)]
AX_PALE_INK = (16, 34, 70)
AX_RUBBER = [(186, 188, 192), (146, 148, 154), (112, 114, 120)]
AX_RUBBER_DN = [(104, 106, 112), (124, 126, 132), (140, 142, 148)]
AX_PRINT = (172, 176, 184)
AX_YELLOW = (255, 204, 44)

DOT57 = {
    "0": G(".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": G("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": G(".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": G("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": G("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": G("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": G("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": G("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": G(".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": G(".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    "-": G(".....", ".....", ".....", "#####", ".....", ".....", "....."),
}


def ax_gloss(a, x, y, w, h, top=0, total=116, stops=None):
    for r in range(h):
        rect(a, x, y + r, w, 1, ramp(stops or AX_GLOSS, (top + r) / max(1, total - 1)))


# The playlist and gen windows are tiled pieces: their surround is straight (constant width and
# colour) and their gloss flat down the sides, fading in from the titlebar and out into the bottom
# bar, so the tiles repeat and the pieces meet without a step. The curve is the main window's and EQ's.
AX_STRAIGHT_W = 3.0
AX_STRAIGHT_SILVER = (196, 200, 206)
AX_FLAT = (10, 10, 13)
AX_GLOSS_TOP = [AX_GLOSS[0], AX_GLOSS[1], AX_FLAT]
AX_GLOSS_BOTTOM = [AX_FLAT, AX_GLOSS[2], AX_GLOSS[3]]


def ax_silver_sides(a, top=0, total=116, left=True, right=True, straight=False):
    """The sculpted silver surround down the sides: wider at top and bottom, waisted in the middle
    (or `straight`, for the tiled windows)."""
    h, w = a.shape[:2]
    for r in range(h):
        t = (top + r) / max(1, total - 1)
        sw = AX_STRAIGHT_W if straight else 2.2 + 3.0 * (1 - np.sin(np.pi * t)) ** 1.5
        for side in ((0,) if left else ()) + ((1,) if right else ()):
            m = np.zeros((1, w), np.float32)
            xs = np.arange(w) + 0.5
            if side == 0:
                m[0] = np.clip(sw - xs + 0.5, 0, 1)
            else:
                m[0] = np.clip(sw - (w - xs) + 0.5, 0, 1)
            col = AX_STRAIGHT_SILVER if straight else ramp(AX_SILVER, 0.15 + 0.7 * abs(t - 0.4))
            paint(a, 0, r, m, col)
            # the dark seam where silver meets the gloss
            edge = np.clip(1 - np.abs((xs if side == 0 else w - xs) - sw - 0.5), 0, 1)[None, :]
            paint(a, 0, r, edge, (4, 4, 6), 0.8)


def ax_vfd(a, x, y, w, h, r=3):
    paint(a, x, y, rr_m(w, h, 0, 0, w, h, r), (2, 2, 3))
    paint(a, x, y, rr_m(w, h, 1, 1, w - 1, h - 1, max(1, r - 1)), AX_VFD)
    rect(a, x + r, y + 1, w - 2 * r, 1, (36, 28, 46))


def ax_key(a, x, y, w, h, pressed=False, kind="rubber", r=None):
    """Rubber (grey pill), pale (the translucent blue preset keys) or silver."""
    r = (min(w, h) / 2 - 0.5) if r is None and kind == "rubber" else (2.0 if r is None else r)
    paint(a, x, y, rr_m(w, h, 0, 0.8, w, h, r), (0, 0, 0), 0.7)
    paint(a, x, y, rr_m(w, h, 0, 0, w, h - 0.8, r), (10, 10, 12))
    if kind == "rubber":
        stops = AX_RUBBER_DN if pressed else AX_RUBBER
    elif kind == "pale":
        stops = pressed if isinstance(pressed, list) else (AX_PALE_ON if pressed else AX_PALE)
    else:
        stops = [(150, 154, 160), (190, 194, 200), (220, 222, 226)] if pressed else AX_SILVER
    paint(a, x, y, rr_m(w, h, 1, 1, w - 1, h - 1.8, max(0.5, r - 1)), vgrad_arr(w, h, stops))
    if kind == "pale" and not pressed:
        paint(a, x, y, rr_m(w, h, 1.5, 1.5, w - 1.5, 1 + (h - 3) * 0.4, max(0.5, r - 1.5)), (255, 255, 255), 0.25)


def ax_caption(a, x, y, kind, lit=True, pressed=False):
    ax_key(a, x, y, 9, 9, pressed, "rubber", 2.0)
    caption_glyph(a, kind, x, y, (24, 24, 28) if lit else (80, 82, 88))


def ax_dotchar(a, ch, x, y, col, ghost=None):
    """A 5x7 dot-matrix character on a 2px pitch (9 x 13), with half-lit bridges between
    neighbouring dots so it reads at 1x like a VFD's glowing matrix."""
    g = DOT57[ch]
    on = [[g[r][c] == "#" for c in range(5)] for r in range(7)]
    half = lerp(AX_VFD, col, 0.45)
    for r in range(7):
        for c in range(5):
            if on[r][c]:
                px(a, x + 2 * c, y + 2 * r, col)
                if c < 4 and on[r][c + 1]:
                    px(a, x + 2 * c + 1, y + 2 * r, half)
                if r < 6 and on[r + 1][c]:
                    px(a, x + 2 * c, y + 2 * r + 1, half)
            elif ghost:
                px(a, x + 2 * c, y + 2 * r, ghost)


def ax_italic(a, s, x, y, size, col, anchor="ls"):
    h, w = a.shape[:2]
    m = Image.new("L", (w, h), 0)
    f = ImageFont.truetype("/usr/share/fonts/liberation-sans-fonts/LiberationSans-BoldItalic.ttf", size)
    ImageDraw.Draw(m).text((x, y), s, fill=255, font=f, anchor=anchor)
    paint(a, 0, 0, np.asarray(m, dtype=np.float32) / 255, col)


def ax_titlebar(lit, which="main"):
    a = new(275, 14)
    ax_gloss(a, 0, 0, 275, 14, 0, 116)
    rect(a, 0, 0, 275, 1, AX_SILVER[0])
    rect(a, 0, 1, 275, 1, AX_SILVER[2])
    ax_silver_sides(a, 0, 116)
    dim = (96, 98, 104)
    if which == "main":
        ax_italic(a, "HIGH POWER 45W×4", 19, 11, 9, AX_YELLOW if lit else dim)
        ax_italic(a, "ADX5655z", 238, 11, 10, (236, 238, 242) if lit else dim, anchor="rs")
        ax_caption(a, 244, 3, "minimize", lit)
        ax_caption(a, 254, 3, "shade", lit)
    else:
        s = "TUNER/CD/CASSETTE  SPECTRUM ANALYZER"
        text_center(a, AX_TINY, s, 137, 5, AX_PRINT if lit else dim)
    ax_caption(a, 6, 3, "options", lit)
    ax_caption(a, 264, 3, "close", lit)
    return a


def ax_clutter(lit_letters):
    a = new(8, 43)
    ax_gloss(a, 0, 0, 8, 43, 22, 116)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        ax_key(a, 0, y - 1, 8, h + 1, on, "pale", 1.5)
        draw_text(a, AX_TINY, letter, 3, y + (h - 5) // 2, AX_PALE_INK if not on else (0, 40, 110))
    return a


def ax_make_titlebar():
    a = new(344, 87)
    ax_gloss(a, 0, 0, 344, 87, 0, 87)
    lit, dim = ax_titlebar(True), ax_titlebar(False)
    a[0:14, 27:302] = lit
    a[15:29, 27:302] = dim
    a[29:43, 27:302] = lit
    a[42:56, 27:302] = dim
    for kind, sx, x in (("options", 6, 0), ("minimize", 244, 9), ("close", 264, 18)):
        a[0:9, x:x + 9] = lit[3:12, sx:sx + 9]
        c = lit[3:12, sx:sx + 9].copy()
        ax_caption(c, 0, 0, kind, True, pressed=True)
        a[9:18, x:x + 9] = c
    a[18:27, 0:9] = lit[3:12, 254:263]
    c = lit[3:12, 254:263].copy()
    ax_caption(c, 0, 0, "shade", True, pressed=True)
    a[18:27, 9:18] = c
    unlit, on = ax_clutter(""), ax_clutter("OAIDV")
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = on[y:y + h]
    return a


def ax_lozenge(a, x, y, w, h, col, caption=None):
    """An orange outlined lozenge (hexagonal ends), as round FUNCTION / TUNE and 6 CH."""
    pts = [(x + 3, y), (x + w - 4, y), (x + w - 1, y + h / 2 - 0.5), (x + w - 4, y + h - 1), (x + 3, y + h - 1),
           (x, y + h / 2 - 0.5)]
    m = line_m(a.shape[1], a.shape[0], pts + [pts[0]], 1.0)
    paint(a, 0, 0, np.clip(m * 1.6, 0, 1), col)
    if caption:
        tw = text_w(AX_TINY, caption)
        cx = x + (w - tw) // 2
        rect(a, cx - 1, y - 2, tw + 2, 5, AX_VFD)
        draw_text(a, AX_TINY, caption, cx, y - 2, col)


def ax_chevron(a, x, y, h, col, point="left"):
    """The thin white bracket lines at the ends of the spectrum banks."""
    d = 3
    if point == "left":
        pts = [(x + d, y), (x, y + h / 2), (x + d, y + h)]
    else:
        pts = [(x, y), (x + d, y + h / 2), (x, y + h)]
    paint(a, 0, 0, np.clip(line_m(a.shape[1], a.shape[0], pts, 1.0) * 1.5, 0, 1), col)


def ax_rocker(a, cx, cy, r):
    x0, y0 = int(cx - r - 2), int(cy - r - 2)
    w = h = int(2 * r + 5)
    lx, ly = cx - x0, cy - y0
    paint(a, x0, y0, circle_m(w, h, lx, ly + 0.8, r + 0.3), (0, 0, 0), 0.8)
    paint(a, x0, y0, circle_m(w, h, lx, ly, r), vgrad_arr(w, h, AX_SILVER))
    paint(a, x0, y0, circle_m(w, h, lx, ly, r - 2.2), (12, 12, 14))
    paint(a, x0, y0, circle_m(w, h, lx, ly, r - 3.0), vgrad_arr(w, h, [(70, 72, 78), (40, 42, 46), (30, 31, 34)]))
    # the cross dividing the four arms
    X, Y = np.mgrid[0:h, 0:w][1] + 0.5, np.mgrid[0:h, 0:w][0] + 0.5
    diag = (np.clip(1 - np.abs((X - lx) - (Y - ly)) / 0.8, 0, 1) + np.clip(1 - np.abs((X - lx) + (Y - ly)) / 0.8, 0, 1))
    paint(a, x0, y0, np.clip(diag, 0, 1) * circle_m(w, h, lx, ly, r - 3.0), (10, 10, 12))
    paint(a, x0, y0, circle_m(w, h, lx, ly, 2.6), vgrad_arr(w, h, [(90, 92, 98), (40, 42, 46)]))
    s = r - 5.2
    col = (214, 218, 224)
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        tx, ty = lx + dx * s, ly + dy * s
        if dx == 0:
            pts = [(tx - 1.8, ty - dy * 1.0), (tx + 1.8, ty - dy * 1.0), (tx, ty + dy * 1.4)]
        else:
            pts = [(tx - dx * 1.0, ty - 1.8), (tx - dx * 1.0, ty + 1.8), (tx + dx * 1.4, ty)]
        paint(a, x0, y0, poly_m(w, h, pts), col)


def ax_make_main():
    a = new(275, 116)
    ax_gloss(a, 0, 0, 275, 116)
    ax_silver_sides(a)
    a[0:14, :] = ax_titlebar(True)
    a[22:65, 10:18] = ax_clutter("")
    ax_vfd(a, 20, 17, 248, 54)
    # left bank: the bracket, the time, the analyzer
    ax_chevron(a, 21, 42, 16, (226, 230, 240), "left")
    px(a, 74, 30, AX_TEXT)
    px(a, 74, 34, AX_TEXT)
    draw_text(a, AX_TINY, "TP TA INFO AF PTY REG", 24, 62, AX_LABEL)
    # right: the title row, the FUNCTION and CH lozenges round kbps / kHz, ST
    for xx in range(110, 266, 2):
        px(a, xx, 37, AX_GHOST)
    ax_lozenge(a, 107, 40, 44, 14, AX_ORANGE, "FUNCTION")
    draw_text(a, AX_TINY, "KBPS", 129, 44, AX_ORANGE)
    ax_lozenge(a, 152, 40, 36, 14, AX_ORANGE)
    draw_text(a, AX_TINY, "CH", 169, 44, AX_ORANGE)
    draw_text(a, AX_TINY, "KHZ", 191, 44, AX_LABEL)
    # below the window: the seek slot, MAGI-TUNE, the wordmark, the rocker
    draw_text(a, AX_TINY, "MAGI-TUNE", 226, 83, AX_PRINT)
    draw_text(a, AX_TINY, "CENET", 16, 83, AX_PRINT)
    clarion_wordmark(a, 137 - CLARION_W // 2, 107, (232, 234, 238))
    ax_rocker(a, 259.5, 98.5, 10.5)
    return a


def ax_make_cbuttons(main):
    a = new(136, 36)
    for kind, x, w, h, mx, my in CB + [("eject", 114, 22, 16, 136, 89)]:
        for pressed, y in ((False, 0), (True, h)):
            cell = main[my:my + h, mx:mx + w].copy()
            if kind == "eject":
                ax_key(cell, 0, 1, w - 1, h - 2, pressed, "silver", 3.0)
            else:
                ax_key(cell, 0, 1, w - 1, h - 2, pressed, "rubber")
            o = 1 if pressed else 0
            transport_icon(cell, kind, (w - 1) // 2, (h - 1) // 2 + o - (1 if kind == "eject" else 0),
                           (28, 28, 32) if not pressed else (20, 20, 24))
            a[y:y + h, x:x + w] = cell
    return a


def ax_make_shufrep(main):
    a = new(92, 85)
    ax_gloss(a, 0, 0, 92, 85, 40, 116)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        for x0, w, mx, label in ((0, 28, 210, "RPT"), (28, 47, 164, "RDM")):
            c = main[89:104, mx:mx + w].copy()
            ax_key(c, 0, 0, w - 1, 15, on or pressed, "pale", 2.5)
            o = 1 if pressed else 0
            tw = text_w(AX_TINY, label)
            tx = (w - 1 - tw - 4) // 2
            draw_text(c, AX_TINY, label, tx, 5 + o, AX_PALE_INK)
            rect(c, tx + tw + 2, 6 + o, 2, 3, AX_ORANGE if on else (60, 90, 130))
            a[y:y + 15, x0:x0 + w] = c
    for x, label, pressed, mx in [(0, "EQ", False, 219), (23, "PL", False, 242), (46, "EQ", True, 219),
                                  (69, "PL", True, 242)]:
        for on, y in ((False, 61), (True, 73)):
            c = main[58:70, mx:mx + 23].copy()
            rect(c, 0, 0, 23, 12, AX_VFD)
            col = (AX_AMBER if pressed else AX_ORANGE) if on else (AX_LABEL if not pressed else (110, 90, 130))
            ax_lozenge(c, 0, 0, 22, 12, col)
            text_center(c, AX_TINY, label, 11, 4, AX_TEXT if on else AX_LABEL)
            a[y:y + 12, x:x + 23] = c
    return a


def ax_make_monoster():
    a = new(56, 24, AX_VFD)
    for y, lit in ((0, True), (12, False)):
        col = AX_TEXT if lit else AX_GHOST
        text_center(a, AX_TINY, "STEREO", 14, y + 3, col)
        text_center(a, AX_TINY, "MONO", 42, y + 3, col)
    return a


def ax_make_numbers(ex):
    a = new(108 if ex else 99, 13, AX_VFD)
    for n in range(10):
        ax_dotchar(a, str(n), 9 * n, 0, AX_TEXT, (30, 21, 40))
    if ex:
        ax_dotchar(a, "-", 99, 0, AX_TEXT, (30, 21, 40))
    return a


def ax_make_playpaus():
    a = new(48, 9, AX_VFD)
    tri_right(a, 2, 1, 7, AX_TEXT)
    rect(a, 9 + 2, 1, 2, 7, AX_TEXT)
    rect(a, 9 + 5, 1, 2, 7, AX_TEXT)
    rect(a, 18 + 2, 2, 5, 5, AX_TEXT)
    rect(a, 36, 0, 3, 9, AX_VFD)
    rect(a, 39 + 1, 3, 1, 3, AX_ORANGE)
    return a


def ax_make_text():
    a = new(155, 18, AX_VFD)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            k = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, k, col * 5, row * 6, AX_TEXT)
    return a


def ax_make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    rect(a, 0, 3, 248, 1, (2, 2, 3))
    rect(a, 0, 4, 248, 2, (24, 24, 28))
    rect(a, 0, 6, 248, 1, (96, 98, 104))
    for x, pressed in ((248, False), (278, True)):
        a[0:10, x:x + 29] = a[0:10, 100:129]
        ax_key(a, x + 7, 0, 15, 10, pressed, "silver", 2.0)
        rect(a, x + 14, 2, 1, 6, AX_ORANGE if pressed else (90, 92, 98))
    return a


def ax_bar(a, x, ybot, hgt, lit, cap):
    """One spectrum column: 1px dashes, 3px wide, every other row; orange cap when lit."""
    for k in range(hgt):
        yy = ybot - 2 * k
        if lit is None:
            col = AX_GHOST
        elif k < lit:
            col = AX_ORANGE if (cap and k == lit - 1) else ramp(AX_BLUE, k / max(1, hgt - 1))
        else:
            col = AX_GHOST
        rect(a, x, yy, 3, 1, col)


def ax_thumb(a, x, y, pressed):
    rect(a, x, y, 14, 11, AX_VFD)
    col = AX_AMBER if pressed else AX_ORANGE
    ax_lozenge(a, x + 1, y + 1, 12, 9, col)
    rect(a, x + 5, y + 4, 4, 3, col)


def ax_make_volume(main):
    a = new(68, 433, AX_VFD)
    n = 16
    for i in range(28):
        y = i * 15
        lit = round((i + 1) / 28 * n)
        for k in range(n):
            hgt = 2 + round(3 * k / (n - 1))
            ax_bar(a, 3 + 4 * k, y + 11, hgt, hgt if k < lit else 0, k == lit - 1)
    ax_thumb(a, 0, 422, True)
    ax_thumb(a, 15, 422, False)
    return a


def ax_make_balance(main):
    a = new(68, 433, AX_VFD)
    for i in range(28):
        y = i * 15
        reach = round(4 * i / 27)
        for k in range(4):
            for bx in (30 + 4 * k, 23 - 4 * k):
                hgt = 2 + k
                ax_bar(a, bx, y + 11, hgt, hgt if k < reach else 0, k == reach - 1)
        rect(a, 27, y + 2, 1, 10, AX_ORANGE)
    ax_thumb(a, 0, 422, True)
    ax_thumb(a, 15, 422, False)
    return a


def ax_eq_frame(n):
    a = new(14, 63, AX_VFD)
    v = n / 27
    centre = round((1 - v) * 51) + 5
    segs = 29
    for k in range(segs):
        yy = 60 - 2 * k
        on = yy >= centre
        top = on and (yy - 2 < centre)
        col = (AX_ORANGE if top else ramp(AX_BLUE, k / (segs - 1))) if on else AX_GHOST
        rect(a, 3, yy, 8, 1, col)
    return a


def ax_eq_thumb(pressed):
    a = new(11, 11, AX_VFD)
    col = AX_AMBER if pressed else AX_ORANGE
    rect(a, 0, 3, 11, 1, col)
    rect(a, 0, 7, 11, 1, col)
    rect(a, 0, 3, 1, 5, col)
    rect(a, 10, 3, 1, 5, col)
    rect(a, 3, 5, 5, 1, (255, 240, 200))
    return a


def ax_eq_body():
    a = new(275, 116)
    ax_gloss(a, 0, 0, 275, 116)
    ax_silver_sides(a)
    a[0:14, :] = ax_titlebar(True, "eq")
    ax_vfd(a, 84, 15, 117, 23, 2)
    ax_vfd(a, 9, 36, 257, 77)
    ax_chevron(a, 12, 40, 58, (226, 230, 240), "left")
    ax_chevron(a, 259, 40, 58, (226, 230, 240), "right")
    for lbl, yy in (("+12", 41), ("0", 66), ("-12", 92)):
        text_center(a, AX_TINY, lbl, 59, yy, AX_ORANGE)
    for xx in EQ_SLIDER_X:
        a[38:101, xx:xx + 14] = ax_eq_frame(14)
    text_center(a, AX_TINY, "PREAMP", 28, 105, AX_LABEL)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, AX_TINY, lbl, 78 + 18 * i + 7, 105, AX_LABEL)
    return a


def ax_make_eqmain():
    a = new(275, 315)
    ax_gloss(a, 0, 0, 275, 315, 0, 315)
    body = ax_eq_body()
    a[0:116, :] = body
    lit, dim = ax_titlebar(True, "eq"), ax_titlebar(False, "eq")
    c = lit[3:12, 264:273].copy()
    ax_caption(c, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = c
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        bx = 14 if label == "ON" else 40
        c = body[18:30, bx:bx + w].copy()
        ax_key(c, 0, 0, w - 1, 12, on or pressed, "pale", 2.0)
        tw = text_w(AX_TINY, label)
        tx = (w - 1 - tw - 4) // 2
        draw_text(c, AX_TINY, label, tx, 3 + (1 if pressed else 0), AX_PALE_INK)
        rect(c, tx + tw + 2, 4 + (1 if pressed else 0), 2, 3, AX_ORANGE if on else (60, 90, 130))
        a[119:131, x:x + w] = c
    a[134:148, :] = lit
    a[149:163, :] = dim
    a[164:175, 0:11] = ax_eq_thumb(False)
    a[176:187, 0:11] = ax_eq_thumb(True)
    for n in range(28):
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = ax_eq_frame(n)
    for y, pressed in ((164, False), (176, True)):
        c = body[18:30, 217:261].copy()
        ax_key(c, 0, 0, 44, 12, pressed, "pale", 2.0)
        text_center(c, AX_TINY, "PRESETS", 22, 3 + (1 if pressed else 0), AX_PALE_INK)
        a[y:y + 12, 224:268] = c
    rect(a, 0, 294, 113, 19, AX_VFD)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, AX_GHOST)
    for r in range(19):
        px(a, 115, 294 + r, ramp([AX_AMBER, AX_ORANGE, AX_ORANGE, AX_AMBER], r / 18))
    for x in range(113):
        px(a, x, 314, AX_BLUE[1] if x % 3 != 2 else AX_VFD)
    return a


def ax_bar_piece(w, h, top=0, total=116, left=False, right=False, stops=None):
    """A piece of chrome; `stops` (a gloss ramp) makes it a tiled window's, with straight sides."""
    a = new(w, h)
    ax_gloss(a, 0, 0, w, h, top, total, stops)
    if left or right:
        ax_silver_sides(a, top, total, left, right, straight=stops is not None)
    return a


def ax_tbar(w, h, **kw):
    """Tiled windows: titlebar piece, its gloss fading to the flat sides."""
    return ax_bar_piece(w, h, 0, h, stops=AX_GLOSS_TOP, **kw)


def ax_side(w, h, **kw):
    return ax_bar_piece(w, h, 0, h, stops=[AX_FLAT], **kw)


def ax_bottom(w, h, **kw):
    return ax_bar_piece(w, h, 0, h, stops=AX_GLOSS_BOTTOM, **kw)


def ax_plate(a, x, y, w, h=11):
    rect(a, x, y, w, h, (2, 2, 3))
    rect(a, x, y + 1, w, h - 2, AX_VFD)


def ax_make_pledit():
    a = new(280, 186)
    ax_gloss(a, 0, 0, 280, 186, 0, 186)
    for lit, y in ((True, 0), (False, 21)):
        def top(t):
            rect(t, 0, 0, t.shape[1], 1, AX_SILVER[0])
            rect(t, 0, 1, t.shape[1], 1, AX_SILVER[2])
            return t
        t = top(ax_tbar(25, 20))
        a[y:y + 20, 127:152] = t
        t = top(ax_tbar(25, 20, left=True))
        a[y:y + 20, 0:25] = t
        t = top(ax_tbar(100, 20))
        ax_plate(t, 2, 5, 96)
        text_center(t, FONT5, "PLAYLIST", 50, 8, AX_TEXT if lit else (90, 96, 120))
        a[y:y + 20, 26:126] = t
        t = top(ax_tbar(25, 20, right=True))
        ax_caption(t, 14, 3, "close", lit)
        rect(t, 9, 14, 10, 6, (24, 24, 28))
        a[y:y + 20, 153:178] = t
    a[42:71, 0:12] = ax_side(12, 29, left=True)
    t = ax_side(20, 29, right=True)
    rect(t, 4, 0, 10, 29, (24, 24, 28))
    rect(t, 4, 0, 1, 29, (2, 2, 3))
    a[42:71, 31:51] = t
    c = a[3:12, 167:176].copy()
    ax_caption(c, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = c
    for x, pressed in ((52, False), (61, True)):
        hnd = new(8, 18, (24, 24, 28))
        ax_key(hnd, 0, 0, 8, 18, pressed, "pale", 1.5)
        a[53:71, x:x + 8] = hnd

    def bottom_base(w, left=False, right=False):
        return ax_bottom(w, 38, left=left, right=right)

    t = bottom_base(125, left=True)
    # the cassette door: a smoked window in a silver rim, FULL LOGIC CASSETTE SYSTEM
    paint(t, 8, 3, rr_m(117, 33, 0, 0, 117, 33, 3), AX_SILVER[2])
    paint(t, 8, 3, rr_m(117, 33, 1, 1, 116, 32, 2), vgrad_arr(117, 33, [(52, 54, 60), (28, 29, 33), (36, 38, 42)]))
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        ax_key(t, bx, 8, 22, 15, False, "rubber", 4.0)
        text_center(t, AX_TINY, lbl, bx + 11, 13, (28, 28, 32))
    draw_text(t, AX_TINY, "FULL LOGIC CASSETTE SYSTEM", 14, 27, AX_PRINT)
    a[72:110, 0:125] = t
    t = bottom_base(150, right=True)
    ax_plate(t, 5, 8, 58, 10)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        ax_key(t, bx, 22, 10, 10, False, "rubber", 2.0)
        mini_transport_icon(t, kind, bx, 22, (28, 28, 32))
    ax_plate(t, 64, 21, 35, 10)
    rect(t, 84, 24, 1, 1, AX_TEXT)
    rect(t, 84, 27, 1, 1, AX_TEXT)
    ax_key(t, 106, 8, 22, 15, False, "rubber", 4.0)
    text_center(t, AX_TINY, "LIST", 117, 13, (28, 28, 32))
    for k in range(4):
        for j in range(k + 1):
            px(t, 141 - 3 * k + 3 * j, 29 - 3 * j, AX_PRINT)
    a[72:110, 126:276] = t
    a[0:38, 179:204] = bottom_base(25)
    return a


def ax_make_gen():
    a = new(194, 109)
    ax_gloss(a, 0, 0, 194, 109, 0, 109)
    for lit, y in ((True, 0), (False, 21)):
        for px0 in (0, 26, 52, 78, 104, 130):
            t = ax_tbar(25, 20, left=px0 == 0, right=px0 == 130)
            rect(t, 0, 0, 25, 1, AX_SILVER[0])
            rect(t, 0, 1, 25, 1, AX_SILVER[2])
            if px0 == 26:
                ax_plate(t, 21, 2, 4, 11)
                rect(t, 20, 2, 1, 11, (2, 2, 3))
            elif px0 == 52:
                ax_plate(t, 0, 2, 25, 11)
            elif px0 == 78:
                ax_plate(t, 0, 2, 4, 11)
                rect(t, 4, 2, 1, 11, (2, 2, 3))
            elif px0 == 130:
                ax_caption(t, 14, 3, "close", lit)
            a[y:y + 20, px0:px0 + 25] = t

    def bottom(w, grip, left):
        t = ax_bottom(w, 14, left=left, right=not left)
        rect(t, 0, 12, w, 1, AX_SILVER[2])
        rect(t, 0, 13, w, 1, AX_SILVER[0])
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    px(t, w - 7 - 3 * k + 3 * j, 9 - 3 * j, AX_PRINT)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    t = ax_bottom(25, 14)
    rect(t, 0, 12, 25, 1, AX_SILVER[2])
    rect(t, 0, 13, 25, 1, AX_SILVER[0])
    a[72:86, 127:152] = t
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = ax_side(w, h, left=left, right=not left)
    c = a[3:12, 144:153].copy()
    ax_caption(c, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = c
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for ch in GEN_LETTERS:
            w = glyph_w(FONT5, ch) + 1
            rect(a, x, y, w, 7, AX_VFD)
            draw_text(a, FONT5, ch, x, y + 1, AX_TEXT if lit else (90, 96, 120))
            x += w + 1
        assert x <= 194, x
    return a


def ax_make_genex():
    a = new(256, 64)
    ax_gloss(a, 0, 0, 256, 64, 0, 64)
    cols = [AX_VFD, (150, 200, 255), (20, 20, 24), (28, 28, 32), (214, 230, 255), (70, 56, 90),
            (52, 36, 80), (34, 34, 38), (255, 146, 36), (90, 92, 98), (0, 0, 0), (255, 146, 36),
            (20, 20, 24), (40, 40, 46), (150, 200, 240), (60, 62, 68), (255, 196, 70), (12, 12, 14)]
    rect(a, 0, 0, 256, 1, (20, 20, 24))
    for i, c in enumerate(cols):
        px(a, 48 + 2 * i, 0, c)
    ax_key(a, 0, 1, 47, 15, False, "rubber", 5.0)
    ax_key(a, 0, 16, 47, 15, True, "rubber", 5.0)
    return a


AX_MAKERS = {
    "main.bmp": ax_make_main, "titlebar.bmp": ax_make_titlebar, "cbuttons.bmp": ax_make_cbuttons,
    "shufrep.bmp": ax_make_shufrep, "posbar.bmp": ax_make_posbar, "volume.bmp": ax_make_volume,
    "balance.bmp": ax_make_balance, "monoster.bmp": ax_make_monoster, "playpaus.bmp": ax_make_playpaus,
    "numbers.bmp": lambda ex: ax_make_numbers(ex), "nums_ex.bmp": lambda ex: ax_make_numbers(ex),
    "text.bmp": ax_make_text, "pledit.bmp": ax_make_pledit, "eqmain.bmp": ax_make_eqmain,
    "gen.bmp": ax_make_gen, "genex.bmp": ax_make_genex,
}


# ------------------------------------------------------------------------------------------
# clarion-adx5655z-silver: the same unit with the balance inverted, closer to its real front:
# the keys sit on the satin/brushed silver faceplate (darker silver bevels down the sides) and
# only the display sections are dark VFD glass. The VFD sprites (digits, text, analyzer, EQ
# columns, lozenges) are the ax_* ones. The silver varies vertically only (fine horizontal brush
# streaks on the main window and EQ), and the tiled playlist and gen pieces have straight sides
# of constant columns, so their tiles repeat cleanly.
# ------------------------------------------------------------------------------------------

AXS_SATIN = [(234, 237, 241), (218, 222, 228), (204, 208, 215), (192, 196, 204), (180, 184, 193)]
AXS_FLAT = (206, 210, 217)          # the tiled windows' silver where the sides run
AXS_BEVEL = [(156, 161, 171), (132, 137, 147)]
AXS_EDGE = (74, 78, 86)
AXS_HI = (248, 249, 251)
AXS_SHADOW = (122, 126, 135)
AXS_INK = (24, 26, 32)              # print on the silver
AXS_PRINT = (66, 70, 80)            # smaller print
AXS_DIM = (138, 142, 151)           # unlit titlebar print
AXS_RIM = (10, 10, 13)              # black gloss rim of a glass window
AXS_GROOVE = (40, 42, 49)
AXS_SMOKE = [(66, 70, 80), (34, 36, 42), (48, 52, 60)]
AXS_LED_OFF = (92, 96, 104)
AXS_STREAK = [int(v) for v in np.random.default_rng(5655).integers(-2, 3, 97)]
AXS_TBAR = [AXS_SATIN[0], AXS_SATIN[1], AXS_FLAT]
AXS_BOTTOM = [AXS_FLAT, AXS_SATIN[3], AXS_SATIN[4]]


def axs_satin(a, x, y, w, h, top=0, total=116, stops=None, streaks=True):
    """Satin silver, lighter at the top; `streaks` adds faint horizontal brush lines."""
    for r in range(h):
        c = ramp(stops or AXS_SATIN, (top + r) / max(1, total - 1))
        s = AXS_STREAK[(top + r) % len(AXS_STREAK)] if streaks else 0
        rect(a, x, y + r, w, 1, tuple(v + s for v in c))


def axs_sides(a, top=0, total=116, left=True, right=True):
    """The darker silver bevels down the sides, waisted in the middle (main window and EQ)."""
    h, w = a.shape[:2]
    xs = np.arange(w) + 0.5
    for r in range(h):
        t = (top + r) / max(1, total - 1)
        sw = 3.0 + 3.0 * (1 - np.sin(np.pi * t)) ** 1.5
        col = ramp(AXS_BEVEL, min(1.0, abs(t - 0.4) * 1.6))
        for side in ((0,) if left else ()) + ((1,) if right else ()):
            d = xs if side == 0 else w - xs
            paint(a, 0, r, np.clip(sw - d + 0.5, 0, 1)[None, :], col)
            paint(a, 0, r, np.clip(1 - np.abs(d - sw - 0.5), 0, 1)[None, :], AXS_HI, 0.9)
            paint(a, 0, r, (d < 1).astype(np.float32)[None, :], AXS_EDGE)


def axs_frame_edges(a):
    """Top and bottom outer edges of a whole window body."""
    w = a.shape[1]
    rect(a, 0, 0, w, 1, AXS_EDGE)
    rect(a, 1, 1, w - 2, 1, AXS_HI)
    rect(a, 1, a.shape[0] - 2, w - 2, 1, AXS_SHADOW)
    rect(a, 0, a.shape[0] - 1, w, 1, AXS_EDGE)


def axs_glass(a, rects, r=3, top_line=True):
    """A recessed VFD window (the union of `rects`, x y w h): shadowed silver lip, black gloss rim,
    the dark violet-black glass."""
    h, w = a.shape[:2]

    def union(inset, rr):
        m = np.zeros((h, w), np.float32)
        for (x, y, ww, hh) in rects:
            m = np.maximum(m, rr_m(w, h, x + inset, y + inset, x + ww - inset, y + hh - inset, max(0.5, rr)))
        return m
    paint(a, 0, 1, union(-1, r + 1), AXS_HI, 0.9)
    paint(a, 0, -1, union(-1, r + 1), AXS_SHADOW)
    paint(a, 0, 0, union(-1, r + 1), lerp(AXS_SHADOW, AXS_EDGE, 0.4))
    paint(a, 0, 0, union(0, r), AXS_RIM)
    paint(a, 0, 0, union(1, r - 1), AX_VFD)
    if top_line:
        x, y, ww, hh = rects[0]
        rect(a, x + r, y + 1, ww - 2 * r, 1, (38, 30, 48))


def axs_key_label(a, s, cx, y, col=AXS_INK):
    text_center(a, AX_TINY, s, cx, y, col)


def axs_rocker(a, cx, cy, r):
    x0, y0 = int(cx - r - 3), int(cy - r - 3)
    w = h = int(2 * r + 7)
    paint(a, x0, y0, circle_m(w, h, cx - x0, cy - y0 + 0.6, r + 1.2), AXS_EDGE, 0.9)
    paint(a, x0, y0, circle_m(w, h, cx - x0, cy - y0 + 1.4, r + 1.0), AXS_HI, 0.5)
    ax_rocker(a, cx, cy, r)


def axs_titlebar(lit, which="main"):
    a = new(275, 14)
    axs_satin(a, 0, 0, 275, 14, 0, 116)
    axs_sides(a, 0, 116)
    rect(a, 0, 0, 275, 1, AXS_EDGE)
    rect(a, 1, 1, 273, 1, AXS_HI)
    ink = AXS_INK if lit else AXS_DIM
    if which == "main":
        ax_italic(a, "HIGH POWER 45W×4", 19, 11, 9, ink)
        text_center(a, AX_TINY, "SPECTRUM ANALYZER", 147, 5, AXS_PRINT if lit else AXS_DIM)
        ax_italic(a, "ADX5655z", 239, 11, 10, ink, anchor="rs")
        axs_caption(a, 244, 3, "minimize", lit)
        axs_caption(a, 254, 3, "shade", lit)
    else:
        s = "TUNER/COMPACT DISC/CASSETTE PLAYER WITH SPECTRUM ANALYZER"
        text_center(a, AX_TINY, s, 137, 5, AXS_PRINT if lit else AXS_DIM)
    axs_caption(a, 6, 3, "options", lit)
    axs_caption(a, 264, 3, "close", lit)
    return a


def axs_caption(a, x, y, kind, lit=True, pressed=False):
    ax_key(a, x, y, 9, 9, pressed, "rubber", 2.0)
    caption_glyph(a, kind, x, y, (20, 20, 24) if lit else (96, 98, 104))


def axs_clutter(lit_letters):
    a = new(8, 43)
    axs_satin(a, 0, 0, 8, 43, 22, 116)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        ax_key(a, 0, y - 1, 8, h + 1, on, "pale", 1.5)
        draw_text(a, AX_TINY, letter, 3, y + (h - 5) // 2, AX_PALE_INK if not on else (0, 40, 110))
    return a


def axs_make_titlebar():
    a = new(344, 87)
    axs_satin(a, 0, 0, 344, 87, 0, 87, streaks=False)
    lit, dim = axs_titlebar(True), axs_titlebar(False)
    a[0:14, 27:302] = lit
    a[15:29, 27:302] = dim
    a[29:43, 27:302] = lit
    a[42:56, 27:302] = dim
    for kind, sx, x in (("options", 6, 0), ("minimize", 244, 9), ("close", 264, 18)):
        a[0:9, x:x + 9] = lit[3:12, sx:sx + 9]
        c = lit[3:12, sx:sx + 9].copy()
        axs_caption(c, 0, 0, kind, True, pressed=True)
        a[9:18, x:x + 9] = c
    a[18:27, 0:9] = lit[3:12, 254:263]
    c = lit[3:12, 254:263].copy()
    axs_caption(c, 0, 0, "shade", True, pressed=True)
    a[18:27, 9:18] = c
    unlit, on = axs_clutter(""), axs_clutter("OAIDV")
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = on[y:y + h]
    return a


# the main window's VFD: the right part (title, kbps / kHz, stereo) and the deeper left bank
# (time, analyzer), one window
AXS_GLASS_MAIN = [(20, 17, 248, 40), (20, 17, 86, 48)]


def axs_make_main():
    a = new(275, 116)
    axs_satin(a, 0, 0, 275, 116)
    axs_sides(a)
    axs_frame_edges(a)
    a[0:14, :] = axs_titlebar(True)
    a[22:65, 10:18] = axs_clutter("")
    axs_glass(a, AXS_GLASS_MAIN)
    ax_chevron(a, 21, 42, 16, (226, 230, 240), "left")
    px(a, 74, 30, AX_TEXT)
    px(a, 74, 34, AX_TEXT)
    for xx in range(110, 266, 2):
        px(a, xx, 37, AX_GHOST)
    ax_lozenge(a, 107, 40, 44, 14, AX_ORANGE, "FUNCTION")
    draw_text(a, AX_TINY, "KBPS", 129, 44, AX_ORANGE)
    ax_lozenge(a, 152, 40, 36, 14, AX_ORANGE)
    draw_text(a, AX_TINY, "CH", 169, 44, AX_ORANGE)
    draw_text(a, AX_TINY, "KHZ", 191, 44, AX_LABEL)
    # print on the silver
    draw_text(a, AX_TINY, "CENET", 22, 67, AXS_PRINT)
    draw_text(a, AX_TINY, "MAGI-TUNE", 201, 83, AXS_PRINT)
    clarion_wordmark(a, 127 - CLARION_W // 2, 106, AXS_INK)
    axs_rocker(a, 259.5, 98.5, 10.5)
    return a


def axs_make_shufrep(main):
    a = ax_make_shufrep(main)
    for x, label, pressed, mx in [(0, "EQ", False, 219), (23, "PL", False, 242), (46, "EQ", True, 219),
                                  (69, "PL", True, 242)]:
        for on, y in ((False, 61), (True, 73)):
            c = main[58:70, mx:mx + 23].copy()
            ax_key(c, 0, 0, 22, 12, pressed, "rubber", 2.5)
            o = 1 if pressed else 0
            draw_text(c, AX_TINY, label, 5, 3 + o, AXS_INK)
            rect(c, 14, 4 + o, 3, 3, AX_ORANGE if on else AXS_LED_OFF)
            a[y:y + 12, x:x + 23] = c
    return a


def axs_track(a, x, y, w):
    """A dark recessed slot in the silver, 3px deep, at rows y .. y+2."""
    rect(a, x, y - 1, w, 1, AXS_SHADOW)
    rect(a, x, y, w, 3, AXS_GROOVE)
    rect(a, x, y, w, 1, (22, 23, 28))
    rect(a, x, y + 3, w, 1, AXS_HI)


def axs_thumb(a, x, y, w, h, pressed):
    ax_key(a, x, y, w, h, pressed, "silver", 2.0)
    rect(a, x + w // 2 - 1, y + 2, 2, h - 4, AX_ORANGE if pressed else AXS_INK)


def axs_make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    axs_track(a, 1, 4, 246)
    for x, pressed in ((248, False), (278, True)):
        a[0:10, x:x + 29] = a[0:10, 100:129]
        axs_thumb(a, x + 7, 0, 15, 10, pressed)
    return a


def axs_segs(a, x0, y, n, lit, rev=False):
    """VFD-like lit segments inside a track: n cells, 2px every 3px; `lit` from the start."""
    for k in range(n):
        xx = x0 - 3 * k - 1 if rev else x0 + 3 * k
        if k < lit:
            col = AX_ORANGE if k == lit - 1 else ramp(AX_BLUE[::-1], k / max(1, n - 1))
        else:
            col = (56, 50, 70)
        rect(a, xx, y, 2, 2, col)


def axs_make_volume(main):
    a = new(68, 433)
    axs_satin(a, 0, 0, 68, 433, 57, 116, streaks=False)
    n = 20
    for i in range(28):
        y = i * 15
        a[y:y + 13, :] = main[57:70, 107:175]
        axs_track(a, 2, y + 5, 64)
        axs_segs(a, 4, y + 6, n, round(i / 27 * n))
    c = main[58:69, 107:121].copy()
    for x, pressed in ((0, True), (15, False)):
        t = c.copy()
        axs_thumb(t, 0, 0, 14, 11, pressed)
        a[422:433, x:x + 14] = t
    return a


def axs_make_balance(main):
    a = new(68, 433)
    axs_satin(a, 0, 0, 68, 433, 57, 116, streaks=False)
    for i in range(28):
        y = i * 15
        a[y:y + 13, 9:47] = main[57:70, 177:215]
        axs_track(a, 11, y + 5, 34)
        reach = round(5 * i / 27)
        axs_segs(a, 29, y + 6, 5, reach)
        axs_segs(a, 27, y + 6, 5, reach, rev=True)
        rect(a, 27, y + 4, 2, 5, AX_ORANGE if i == 0 else AXS_INK)
    c = main[58:69, 177:191].copy()
    for x, pressed in ((0, True), (15, False)):
        t = c.copy()
        axs_thumb(t, 0, 0, 14, 11, pressed)
        a[422:433, x:x + 14] = t
    return a


AXS_LABEL = (150, 160, 196)   # band labels in the EQ glass


def axs_eq_body():
    a = new(275, 116)
    axs_satin(a, 0, 0, 275, 116)
    axs_sides(a)
    axs_frame_edges(a)
    a[0:14, :] = axs_titlebar(True, "eq")
    axs_glass(a, [(84, 15, 117, 23), (13, 37, 249, 76)], 3, top_line=False)
    rect(a, 87, 16, 111, 1, (38, 30, 48))
    ax_chevron(a, 16, 41, 56, (226, 230, 240), "left")
    ax_chevron(a, 255, 41, 56, (226, 230, 240), "right")
    for lbl, yy in (("+12", 41), ("0", 66), ("-12", 92)):
        text_center(a, AX_TINY, lbl, 59, yy, AX_ORANGE)
    for xx in EQ_SLIDER_X:
        a[38:101, xx:xx + 14] = ax_eq_frame(14)
    text_center(a, AX_TINY, "PREAMP", 28, 104, AXS_LABEL)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, AX_TINY, lbl, 78 + 18 * i + 7, 104, AXS_LABEL)
    return a


def axs_make_eqmain():
    a = new(275, 315)
    axs_satin(a, 0, 0, 275, 315, 0, 315, streaks=False)
    body = axs_eq_body()
    a[0:116, :] = body
    lit, dim = axs_titlebar(True, "eq"), axs_titlebar(False, "eq")
    c = lit[3:12, 264:273].copy()
    axs_caption(c, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = c
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        bx = 14 if label == "ON" else 40
        c = body[18:30, bx:bx + w].copy()
        ax_key(c, 0, 0, w - 1, 12, pressed, "pale", 2.0)
        tw = text_w(AX_TINY, label)
        tx = (w - 1 - tw - 4) // 2
        draw_text(c, AX_TINY, label, tx, 3 + (1 if pressed else 0), AX_PALE_INK)
        rect(c, tx + tw + 2, 4 + (1 if pressed else 0), 2, 3, AX_ORANGE if on else (60, 90, 130))
        a[119:131, x:x + w] = c
    a[134:148, :] = lit
    a[149:163, :] = dim
    a[164:175, 0:11] = ax_eq_thumb(False)
    a[176:187, 0:11] = ax_eq_thumb(True)
    for n in range(28):
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = ax_eq_frame(n)
    for y, pressed in ((164, False), (176, True)):
        c = body[18:30, 217:261].copy()
        ax_key(c, 0, 0, 44, 12, pressed, "pale", 2.0)
        text_center(c, AX_TINY, "PRESETS", 22, 3 + (1 if pressed else 0), AX_PALE_INK)
        a[y:y + 12, 224:268] = c
    rect(a, 0, 294, 113, 19, AX_VFD)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, AX_GHOST)
    for r in range(19):
        px(a, 115, 294 + r, ramp([AX_AMBER, AX_ORANGE, AX_ORANGE, AX_AMBER], r / 18))
    for x in range(113):
        px(a, x, 314, AX_BLUE[1] if x % 3 != 2 else AX_VFD)
    return a


# Tiled windows: every side is a fixed list of column colours (outer edge first), the same in
# the side pieces and down the titlebar and bottom pieces, so the tiles meet without a step.
AXS_PL_LEFT = [AXS_EDGE] + [AXS_BEVEL[0]] * 3 + [AXS_HI] + [AXS_FLAT] * 4 + [AXS_SHADOW, (40, 40, 46), AXS_RIM]
AXS_PL_RIGHT = ([AXS_RIM, (40, 40, 46), AXS_FLAT, AXS_FLAT, (70, 72, 80)] + [AXS_GROOVE] * 8 + [AXS_HI, AXS_FLAT]
                + [AXS_HI] + [AXS_BEVEL[0]] * 3 + [AXS_EDGE])
AXS_GEN_LEFT = [AXS_EDGE] + [AXS_BEVEL[0]] * 3 + [AXS_HI] + [AXS_FLAT] * 2 + [AXS_RIM] * 4
AXS_GEN_RIGHT = [AXS_RIM, AXS_FLAT, AXS_FLAT, AXS_HI] + [AXS_BEVEL[0]] * 3 + [AXS_EDGE]


def axs_cols(a, x, cols, y0=0, y1=None):
    for k, c in enumerate(cols):
        rect(a, x + k, y0, 1, (a.shape[0] if y1 is None else y1) - y0, c)


def axs_outer(cols):
    """The outer part of a side (edge, bevel, highlight): it runs through every piece."""
    n = 0
    for c in (cols if cols[0] == AXS_EDGE else cols[::-1]):
        n += 1
        if c == AXS_HI:
            break
    return n


def axs_piece(w, h, kind, left=None, right=None):
    """A tiled-window piece: `kind` "top" (satin to flat), "side" (flat) or "bottom" (flat down
    to darker), with `left` / `right` the side's column list running its full height."""
    a = new(w, h)
    if kind == "side":
        rect(a, 0, 0, w, h, AXS_FLAT)
    else:
        axs_satin(a, 0, 0, w, h, 0, h, AXS_TBAR if kind == "top" else AXS_BOTTOM, streaks=False)
    if left:
        axs_cols(a, 0, left if kind == "side" else left[:axs_outer(left)])
    if right:
        cols = right if kind == "side" else right[-axs_outer(right):]
        axs_cols(a, w - len(cols), cols)
    if kind == "top":
        rect(a, 0, 0, w, 1, AXS_EDGE)
        rect(a, 1 if left else 0, 1, w - (1 if left else 0) - (1 if right else 0), 1, AXS_HI)
    if kind == "bottom":
        rect(a, 0, h - 1, w, 1, AXS_EDGE)
        rect(a, 1 if left else 0, h - 2, w - (1 if left else 0) - (1 if right else 0), 1, AXS_SHADOW)
    return a


def axs_print_box(a, x0, x1, y0, y1, col, left=True, right=True):
    """A printed outline (silkscreen box) from x0 to x1 inclusive."""
    rect(a, x0, y0, x1 - x0 + 1, 1, col)
    rect(a, x0, y1, x1 - x0 + 1, 1, col)
    if left:
        rect(a, x0, y0, 1, y1 - y0 + 1, col)
    if right:
        rect(a, x1, y0, 1, y1 - y0 + 1, col)


def axs_make_pledit():
    a = new(280, 186)
    axs_satin(a, 0, 0, 280, 186, 0, 186, streaks=False)
    L, R = AXS_PL_LEFT, AXS_PL_RIGHT
    rim = [AXS_SHADOW, (40, 40, 46), AXS_RIM]       # the list's top edge, rows 17..19
    for lit, y in ((True, 0), (False, 21)):
        ink = AXS_INK if lit else AXS_DIM
        t = axs_piece(25, 20, "top")
        for k, c in enumerate(rim):
            rect(t, 0, 17 + k, 25, 1, c)
        a[y:y + 20, 127:152] = t
        t = axs_piece(25, 20, "top", left=L)
        for k, c in enumerate(rim):
            rect(t, 9 + k, 17 + k, 25 - 9 - k, 1, c)
        axs_cols(t, 9, L[9:], 17, 20)
        a[y:y + 20, 0:25] = t
        t = axs_piece(100, 20, "top")
        for k, c in enumerate(rim):
            rect(t, 0, 17 + k, 100, 1, c)
        axs_print_box(t, 18, 81, 3, 13, AXS_PRINT if lit else AXS_DIM)
        text_center(t, FONT5, "PLAYLIST", 50, 6, ink)
        a[y:y + 20, 26:126] = t
        t = axs_piece(25, 20, "top", right=R)
        for k, c in enumerate(rim):
            rect(t, 0, 17 + k, 5 + 2 - k, 1, c)
        axs_cols(t, 5, R[:3], 17, 20)
        axs_caption(t, 13, 3, "close", lit)
        a[y:y + 20, 153:178] = t
    a[42:71, 0:12] = axs_piece(12, 29, "side", left=L)
    a[42:71, 31:51] = axs_piece(20, 29, "side", right=R)
    c = a[3:12, 166:175].copy()
    axs_caption(c, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = c
    for x, pressed in ((52, False), (61, True)):
        hnd = new(8, 18, AXS_GROOVE)
        ax_key(hnd, 0, 0, 8, 18, pressed, "silver", 1.5)
        for k in range(3):
            rect(hnd, 2, 6 + 2 * k, 4, 1, AXS_SHADOW)
        a[53:71, x:x + 8] = hnd

    def bottom_base(w, left=False, right=False, list_from=0, list_to=None):
        t = axs_piece(w, 38, "bottom", left=L if left else None, right=R if right else None)
        lt = w if list_to is None else list_to
        rect(t, list_from, 0, lt - list_from, 1, AXS_RIM)
        rect(t, list_from, 1, lt - list_from, 1, (40, 40, 46))
        rect(t, list_from, 2, lt - list_from, 1, AXS_HI)
        return t

    t = bottom_base(125, left=True, list_from=10)
    axs_cols(t, 10, L[10:], 0, 2)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        ax_key(t, bx, 6, 22, 15, False, "rubber", 4.0)
        axs_key_label(t, lbl, bx + 11, 11)
    # the cassette door: a smoked slot, FULL LOGIC CASSETTE SYSTEM
    paint(t, 12, 24, rr_m(112, 11, 0, 0, 112, 11, 2), AXS_EDGE)
    paint(t, 12, 24, rr_m(112, 11, 1, 1, 111, 10, 1.5), vgrad_arr(112, 11, AXS_SMOKE))
    rect(t, 14, 35, 108, 1, AXS_HI)
    text_center(t, AX_TINY, "FULL LOGIC CASSETTE SYSTEM", 68, 27, (190, 196, 206))
    a[72:110, 0:125] = t
    t = bottom_base(150, right=True, list_to=130)
    axs_cols(t, 130, R[:2], 0, 2)
    axs_cols(t, 134, R[4:14], 0, 2)
    axs_glass(t, [(5, 8, 58, 10)], 1, top_line=False)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        ax_key(t, bx, 22, 10, 10, False, "rubber", 2.0)
        mini_transport_icon(t, kind, bx, 22, (24, 24, 28))
    axs_glass(t, [(64, 21, 35, 10)], 1, top_line=False)
    rect(t, 84, 24, 1, 1, AX_TEXT)
    rect(t, 84, 27, 1, 1, AX_TEXT)
    ax_key(t, 106, 8, 22, 15, False, "rubber", 4.0)
    axs_key_label(t, "LIST", 117, 13)
    for k in range(4):
        for j in range(k + 1):
            px(t, 141 - 3 * k + 3 * j, 33 - 3 * j, AXS_PRINT)
    a[72:110, 126:276] = t
    a[0:38, 179:204] = bottom_base(25)
    return a


def axs_make_gen():
    a = new(194, 109)
    axs_satin(a, 0, 0, 194, 109, 0, 109, streaks=False)
    L, R = AXS_GEN_LEFT, AXS_GEN_RIGHT
    for lit, y in ((True, 0), (False, 21)):
        box = AXS_PRINT if lit else AXS_DIM
        for px0 in (0, 26, 52, 78, 104, 130):
            t = axs_piece(25, 20, "top", left=L if px0 == 0 else None, right=R if px0 == 130 else None)
            # the art's black rim, rows 16..19
            x0 = 7 if px0 == 0 else 0
            x1 = 18 if px0 == 130 else 24
            rect(t, x0, 16, x1 - x0 + 1, 4, AXS_RIM)
            if px0 == 26:
                axs_print_box(t, 20, 24, 2, 12, box, right=False)
            elif px0 == 52:
                axs_print_box(t, 0, 24, 2, 12, box, left=False, right=False)
            elif px0 == 78:
                axs_print_box(t, 0, 4, 2, 12, box, left=False)
            elif px0 == 130:
                axs_caption(t, 14, 3, "close", lit)
            a[y:y + 20, px0:px0 + 25] = t

    def bottom(w, left):
        t = axs_piece(w, 14, "bottom", left=L if left else None, right=None if left else R)
        if left:
            rect(t, 7, 0, w - 7, 4, AXS_RIM)
        else:
            rect(t, 0, 0, w - 7, 4, AXS_RIM)
        return t

    a[42:56, 0:125] = bottom(125, True)
    t = bottom(125, False)
    for k in range(3):
        for j in range(k + 1):
            px(t, 125 - 6 - 3 * k + 3 * j, 11 - 3 * j, AXS_PRINT)
    a[57:71, 0:125] = t
    t = axs_piece(25, 14, "bottom")
    rect(t, 0, 0, 25, 4, AXS_RIM)
    a[72:86, 127:152] = t
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = axs_piece(w, h, "side", left=L if left else None, right=None if left else R)
    c = a[3:12, 144:153].copy()
    axs_caption(c, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = c
    # the title letters: printed on the silver, each cell the titlebar's own rows 4..10
    tb = axs_piece(25, 20, "top")
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for ch in GEN_LETTERS:
            w = glyph_w(FONT5, ch) + 1
            for r in range(7):
                rect(a, x, y + r, w, 1, tuple(int(v) for v in tb[4 + r, 10]))
            draw_text(a, FONT5, ch, x, y + 1, AXS_INK if lit else AXS_DIM)
            x += w + 1
        assert x <= 194, x
    return a


def axs_make_genex():
    a = new(256, 64)
    axs_satin(a, 0, 0, 256, 64, 0, 64, streaks=False)
    cols = [AX_VFD, (150, 200, 255), (204, 208, 215), (24, 26, 32), (24, 26, 32), (96, 156, 214),
            (52, 36, 80), (180, 184, 193), (24, 26, 32), (236, 238, 242), (180, 184, 193), (112, 116, 124),
            (160, 164, 172), (196, 200, 206), (60, 62, 68), (150, 200, 240), (40, 42, 48), (122, 126, 135)]
    rect(a, 0, 0, 256, 1, (204, 208, 215))
    for i, c in enumerate(cols):
        px(a, 48 + 2 * i, 0, c)
    ax_key(a, 0, 1, 47, 15, False, "rubber", 5.0)
    ax_key(a, 0, 16, 47, 15, True, "rubber", 5.0)
    return a


AXS_MAKERS = dict(AX_MAKERS, **{
    "main.bmp": axs_make_main, "titlebar.bmp": axs_make_titlebar, "shufrep.bmp": axs_make_shufrep,
    "posbar.bmp": axs_make_posbar, "volume.bmp": axs_make_volume, "balance.bmp": axs_make_balance,
    "pledit.bmp": axs_make_pledit, "eqmain.bmp": axs_make_eqmain, "gen.bmp": axs_make_gen,
    "genex.bmp": axs_make_genex,
})


# ------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------

SHEETS = {}


def build():
    if T.name == "vw-mib2-v2":
        return build_with(V2_MAKERS)
    if T.name == "clarion-adx5655z":
        return build_with(AX_MAKERS)
    if T.name == "clarion-adx5655z-silver":
        return build_with(AXS_MAKERS)
    return build_with({})


def build_with(over):
    def mk(name, fn, *args):
        return over[name](*args) if name in over else fn(*args)
    main = mk("main.bmp", make_main)
    sheets = {
        "main.bmp": main,
        "titlebar.bmp": mk("titlebar.bmp", make_titlebar),
        "cbuttons.bmp": mk("cbuttons.bmp", make_cbuttons, main),
        "shufrep.bmp": mk("shufrep.bmp", make_shufrep, main),
        "posbar.bmp": mk("posbar.bmp", make_posbar, main),
        "volume.bmp": mk("volume.bmp", make_volume, main),
        "balance.bmp": mk("balance.bmp", make_balance, main),
        "monoster.bmp": mk("monoster.bmp", make_monoster),
        "playpaus.bmp": mk("playpaus.bmp", make_playpaus),
        "numbers.bmp": mk("numbers.bmp", make_numbers, False),
        "nums_ex.bmp": mk("nums_ex.bmp", make_numbers, True),
        "text.bmp": mk("text.bmp", make_text),
        "pledit.bmp": mk("pledit.bmp", make_pledit),
        "eqmain.bmp": mk("eqmain.bmp", make_eqmain),
        "gen.bmp": mk("gen.bmp", make_gen),
        "genex.bmp": mk("genex.bmp", make_genex),
    }
    SHEETS.clear()
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
    for p in ((getattr(T, "ttf", None) or "/nonexistent"), "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf", "DejaVuSans.ttf"):
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
    # the title box blanked with text.bmp's space, then the title in pledit's font and colour
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    box = img.crop((111, 22, 265, 36))
    ImageDraw.Draw(box).text((0, 3 + 2 + 2), state["title"], fill=T.ink, font=tt_font(11),
                             anchor="lm")
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
    p = T.pledit
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
    c0, c1 = np.array(T.disp, np.float32), np.array(T.accent, np.float32)
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
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=f"Night Drive - {T.title} (Radio Edit)", bars=bars)
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
        print(f"{T.wsz}: {', '.join(n for n in names)}")
