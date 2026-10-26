#!/usr/bin/python3
"""Microsoft Teams, Slack, Palo Alto Networks: classic Winamp 2.x skins in the style of work software.

One procedural generator, a theme each. It builds on skins/ember/gen_skin.py by way of
private-repo/skins/apps/browsers/gen_skin.py (same sheet layouts, helpers and preview). Everything is drawn
here from code (gradients, anti-aliased shapes, hand-made pixel fonts and icons), except one logo
per skin, rasterised from source/ at generation time. Private use only.

    /usr/bin/python3 -I gen_skin.py [teams|slack|palo-alto ...]   (no argument builds all three)
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

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.join(HERE, "out")
SRC = os.path.join(HERE, "source")
OUT = None          # out/<theme>, set by use_theme
T = None            # the theme in use

SEP = (255, 0, 255)  # gen.bmp letter separators (never shown)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ------------------------------------------------------------------------------------------
# Colour helpers
# ------------------------------------------------------------------------------------------


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    """Colour along a list of evenly spaced stops, t in 0..1."""
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def hexc(c):
    return "#%02X%02X%02X" % tuple(c)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int) and anti-aliased shapes (masks drawn 4x, box-filtered)
# ------------------------------------------------------------------------------------------


def new(w, h, col=BLACK):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        x0, y0 = max(0, x), max(0, y)
        a[y0:y + h, x0:x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def vgrad(h, stops, w=1):
    """(h, w, 3) float rows running through stops (top to bottom)."""
    rows = np.array([ramp(stops, (r + 0.5) / h) for r in range(h)], dtype=np.float32)
    return np.broadcast_to(rows[:, None, :], (h, w, 3)).copy()


def vfill(a, x, y, w, h, stops):
    if w > 0 and h > 0:
        g = np.round(vgrad(h, stops, w)).astype(np.int32)
        x0 = max(0, x)
        a[y:y + h, x0:x + w] = g[:, x0 - x:]


SS = 4


def mask(w, h, fn):
    im = Image.new("L", (w * SS, h * SS), 0)
    fn(ImageDraw.Draw(im), SS)
    return np.asarray(im.resize((w, h), Image.BOX), dtype=np.float32) / 255.0


def rr_mask(w, h, r, x=0.0, y=0.0, mw=None, mh=None):
    mw = w - x if mw is None else mw
    mh = h - y if mh is None else mh

    def fn(d, S):
        d.rounded_rectangle((x * S, y * S, (x + mw) * S - 1, (y + mh) * S - 1), radius=max(0, r * S), fill=255)
    return mask(w, h, fn)


def ellipse_mask(w, h, x, y, ew, eh):
    return mask(w, h, lambda d, S: d.ellipse((x * S, y * S, (x + ew) * S - 1, (y + eh) * S - 1), fill=255))


def poly_mask(w, h, pts):
    return mask(w, h, lambda d, S: d.polygon([(px_ * S, py_ * S) for px_, py_ in pts], fill=255))


def line_mask(w, h, pts, width):
    return mask(w, h, lambda d, S: d.line([(px_ * S, py_ * S) for px_, py_ in pts], fill=255, width=int(width * S)))


def paint(a, x, y, m, col, alpha=1.0):
    """Blends colour (tuple, or an (h, w, 3) array for the mask) over a through mask m at (x, y)."""
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


def rbox(a, x, y, w, h, r, fill, edge=None, alpha=1.0):
    """A rounded box: fill is a colour or a list of stops (vertical gradient); edge a 1px rim."""
    if w <= 0 or h <= 0:
        return
    if edge is not None:
        paint(a, x, y, rr_mask(w, h, r), edge, alpha)
        m = rr_mask(w, h, max(0.0, r - 1), 1, 1, w - 2, h - 2)
    else:
        m = rr_mask(w, h, r)
    col = vgrad(h, fill, w) if isinstance(fill, list) else fill
    paint(a, x, y, m, col, alpha)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def logo(a, x, y, size, path_png, bg_circle=None, fit="h"):
    """Pastes a logo (an RGBA PNG rasterised from source/) scaled to size, centred in a size box."""
    im = Image.open(path_png).convert("RGBA")
    bbox = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    im = im.crop(bbox)
    sw, sh = size
    k = min(sw / im.width, sh / im.height)
    nw, nh = max(1, round(im.width * k)), max(1, round(im.height * k))
    im = im.resize((nw, nh), Image.LANCZOS)
    arr = np.asarray(im, dtype=np.float32)
    al = arr[..., 3] / 255.0
    ox, oy = x + (sw - nw) // 2, y + (sh - nh) // 2
    paint(a, ox, oy, al, arr[..., :3])


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
TINY["J"] = G("..#", "..#", "..#", "#.#", ".#.")
TINY[">"] = G("#..", ".#.", "..#", ".#.", "#..")
TINY["/"] = G("..#", "..#", ".#.", "#..", "#..")
for _c in "0123456789+-.:":
    TINY[_c] = FONT5[_c]

# A UI font for titlebar text: capitals 7 rows, x-height 5, descenders 2 (9 rows in all).
_LOWER = {
    "a": ["", "", ".##.", "...#", ".###", "#..#", ".###"],
    "b": ["#...", "#...", "###.", "#..#", "#..#", "#..#", "###."],
    "c": ["", "", ".###", "#...", "#...", "#...", ".###"],
    "d": ["...#", "...#", ".###", "#..#", "#..#", "#..#", ".###"],
    "e": ["", "", ".##.", "#..#", "####", "#...", ".###"],
    "f": [".##", "#..", "###", "#..", "#..", "#..", "#.."],
    "g": ["", "", ".###", "#..#", "#..#", "#..#", ".###", "...#", ".##."],
    "h": ["#...", "#...", "###.", "#..#", "#..#", "#..#", "#..#"],
    "i": ["#", ".", "#", "#", "#", "#", "#"],
    "j": [".#", "..", ".#", ".#", ".#", ".#", ".#", ".#", "#."],
    "k": ["#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#"],
    "l": ["#", "#", "#", "#", "#", "#", "#"],
    "m": ["", "", "####.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"],
    "n": ["", "", "###.", "#..#", "#..#", "#..#", "#..#"],
    "o": ["", "", ".##.", "#..#", "#..#", "#..#", ".##."],
    "p": ["", "", "###.", "#..#", "#..#", "#..#", "###.", "#...", "#..."],
    "q": ["", "", ".###", "#..#", "#..#", "#..#", ".###", "...#", "...#"],
    "r": ["", "", "#.#", "##.", "#..", "#..", "#.."],
    "s": ["", "", ".###", "#...", ".##.", "...#", "###."],
    "t": ["", ".#.", "###", ".#.", ".#.", ".#.", "..#"],
    "u": ["", "", "#..#", "#..#", "#..#", "#..#", ".###"],
    "v": ["", "", "#.#", "#.#", "#.#", "#.#", ".#."],
    "w": ["", "", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."],
    "x": ["", "", "#..#", "#..#", ".##.", "#..#", "#..#"],
    "y": ["", "", "#..#", "#..#", "#..#", "#..#", ".###", "...#", ".##."],
    "z": ["", "", "####", "..#.", ".#..", "#...", "####"],
    "-": ["", "", "", "", "###", "", ""],
    "#": ["", ".#.#.", "#####", ".#.#.", ".#.#.", "#####", ".#.#."],
    "+": ["", "", "..#..", "..#..", "#####", "..#..", "..#.."],
    " ": [".."],
}
UI = {}
for _k, _rows in _LOWER.items():
    _w = max(len(r) for r in _rows)
    UI[_k] = [(r or "." * _w).ljust(_w, ".") for r in _rows] + ["." * _w] * (9 - len(_rows))
for _k, _g in FONT5.items():
    if _k.isupper():
        UI[_k] = [_g[i] for i in (0, 1, 1, 2, 3, 3, 4)] + ["." * len(_g[0])] * 2

# Clean sans digits for the time readout (7 x 11, in a 9 x 13 cell).
DIGITS = {
    0: [".#####.", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##",
        "##...##", ".#####."],
    1: ["...##..", "..###..", ".####..", "...##..", "...##..", "...##..", "...##..", "...##..", "...##..",
        "...##..", ".######"],
    2: [".#####.", "##...##", ".....##", ".....##", "....##.", "...##..", "..##...", ".##....", "##.....",
        "##.....", "#######"],
    3: [".#####.", "##...##", ".....##", ".....##", "..####.", ".....##", ".....##", ".....##", ".....##",
        "##...##", ".#####."],
    4: ["....##.", "...###.", "..####.", ".##.##.", "##..##.", "##..##.", "#######", "....##.", "....##.",
        "....##.", "....##."],
    5: ["#######", "##.....", "##.....", "##.....", "######.", ".....##", ".....##", ".....##", ".....##",
        "##...##", ".#####."],
    6: [".#####.", "##...##", "##.....", "##.....", "######.", "##...##", "##...##", "##...##", "##...##",
        "##...##", ".#####."],
    7: ["#######", ".....##", ".....##", "....##.", "....##.", "...##..", "...##..", "..##...", "..##...",
        "..##...", "..##..."],
    8: [".#####.", "##...##", "##...##", "##...##", ".#####.", "##...##", "##...##", "##...##", "##...##",
        "##...##", ".#####."],
    9: [".#####.", "##...##", "##...##", "##...##", "##...##", ".######", ".....##", ".....##", ".....##",
        "##...##", ".#####."],
}


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1, shadow=None, sh=(1, 1)):
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


def text_center(a, font, s, cx, y, col, gap=1, shadow=None, sh=(1, 1)):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow, sh)



def draw_ui(a, s, x, y, col, bold=False):
    """The UI font; bold draws each glyph twice, one pixel apart (Slack's unread channels)."""
    for c in s:
        if c not in UI:
            continue
        draw_text(a, UI, c, x, y, col)
        if bold:
            draw_text(a, UI, c, x + 1, y, col)
        x += glyph_w(UI, c) + 1 + (1 if bold else 0)
    return x


def ui_w(s, bold=False):
    s = [c for c in s if c in UI]
    return text_w(UI, "".join(s)) + (len(s) if bold else 0)


def icon(a, rows, x, y, col):
    """A hand-drawn pixel icon (rows of '#'), at (x, y)."""
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + c, y + r, col)


# ------------------------------------------------------------------------------------------
# Icons (pixel art)
# ------------------------------------------------------------------------------------------

IC = {
    "bell": ["...#...", "..###..", ".#####.", ".#####.", ".#####.", "#######", "...#..."],
    "chat": ["#######", "#.....#", "#.###.#", "#.....#", "#######", ".##....", ".#....."],
    "teams": [".#...#.", "###.###", ".#...#.", ".......", "###.###", "###.###"],
    "calendar": ["#######", "#######", "#.....#", "#.#.#.#", "#.....#", "#.#.#.#", "#######"],
    "calls": ["##.....", "###....", ".##....", "..##...", "...###.", "....###", ".....##"],
    "files": ["####...", "#..##..", "#...##.", "#....#.", "#....#.", "#....#.", "######."],
    "apps": ["##.##..", "##.##..", ".......", "##.##..", "##.##.."],
    "cam": ["#####..", "#...#.#", "#...###", "#...###", "#...#.#", "#####.."],
    "mic": [".###.", ".###.", ".###.", "#.#.#", "#...#", ".###.", "..#..", ".###."],
    "search": [".##..", "#..#.", "#..#.", ".##..", "....#"],
    "lock": [".###.", "#...#", "#...#", "#####", "##.##", "##.##", "#####"],
    "shuffle": ["......#..", "##...####", "..#.#..#.", "...#.....", "..#.#..#.", "##...####",
                "......#.."],
    "repeat": ["......#..", ".#######.", "#.....#..", "#.......#", "..#.....#", ".#######.",
               "..#......"],
    "chevron": ["#...#", ".#.#.", "..#.."],
    "hash": [".#.#.", "#####", ".#.#.", "#####", ".#.#."],
    "check": ["....#", "...#.", "#.#..", ".#..."],
}


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    # The new Microsoft Teams (2023+), Fluent 2, light: a #f5f5f5 window, a light grey title bar,
    # the Teams purple, white cards with hairline borders, and the app rail down the left (here in
    # classic Teams' dark #33344a). The main window is a meeting: Join, Leave, Share, mic, camera.
    "teams": SimpleNamespace(
        name="teams", wsz="Microsoft-Teams.wsz", subject="Microsoft Teams (the new Teams, 2023)",
        logo_owner="Microsoft", logo=os.path.join(SRC, "logo-teams", "teams.svg"),
        logo_url="https://commons.wikimedia.org/wiki/File:Microsoft_Office_Teams_(2018%E2%80%93present).svg",
        bar_lit=[(235, 235, 235), (235, 235, 235)], bar_dim=[(245, 245, 245), (245, 245, 245)],
        bar_line=(224, 224, 224), edge=(198, 198, 198),
        body=(245, 245, 245), frame_body=(245, 245, 245),
        rail=(51, 52, 74), rail_ink=(186, 186, 214), rail_sel=(127, 133, 245),
        disp=(255, 255, 255), disp_edge=(209, 209, 209), disp_r=4,
        txt=(36, 36, 36), label=(112, 112, 112), flabel=(112, 112, 112), digit=(36, 36, 36),
        accent=(91, 95, 199), accent_dk=(68, 71, 145), accent_lt=(232, 235, 250),
        red=(196, 49, 75), green=(107, 183, 0), yellow=(255, 170, 68), grey=(138, 136, 134),
        btn=(255, 255, 255), btn_edge=(209, 209, 209), btn_down=(224, 224, 224), glyph=(66, 66, 66),
        track=(209, 209, 209),
        title_lit=(36, 36, 36), title_dim=(150, 150, 150),
        pledit=dict(Normal="#242424", Current="#5B5FC7", NormalBG="#FFFFFF", SelectedBG="#E8EBFA"),
        vis_bars=[(160, 164, 250), (91, 95, 199), (68, 71, 145)], vis_dots=(238, 238, 242),
        vis_peak=(196, 49, 75),
        vis_osc=[(91, 95, 199), (110, 114, 214), (127, 133, 245), (160, 164, 250), (196, 199, 252)],
        main_title="Now playing", eq_title="Equalizer", pl_title="Chat", gen_bg=((232, 235, 250), (91, 95, 199)),
    ),
    # Slack since the 2019 logo: the aubergine sidebar and top bar, a white message pane, channel
    # names for window titles (bold white when focused, like an unread channel), the composer,
    # emoji-reaction pills, the green send button and red mention badges.
    "slack": SimpleNamespace(
        name="slack", wsz="Slack.wsz", subject="Slack (the 2019 brand, 2023 layout)",
        logo_owner="Slack Technologies (Salesforce)", logo=os.path.join(SRC, "logo-slack", "slack.svg"),
        logo_url="https://commons.wikimedia.org/wiki/File:Slack_icon_2019.svg",
        bar_lit=[(53, 13, 54), (53, 13, 54)], bar_dim=[(84, 58, 85), (84, 58, 85)],
        bar_line=None, edge=(36, 6, 37),
        body=(255, 255, 255), frame_body=(63, 14, 64),
        rail=(63, 14, 64), rail_ink=(207, 195, 207), rail_sel=(17, 100, 163),
        disp=(255, 255, 255), disp_edge=(187, 186, 187), disp_r=5,
        txt=(29, 28, 29), label=(97, 96, 97), flabel=(97, 96, 97), digit=(29, 28, 29),
        accent=(18, 100, 163), accent_dk=(17, 80, 140), accent_lt=(232, 245, 250),
        ring=(29, 155, 209), send=(0, 122, 90),
        red=(224, 30, 90), yellow=(236, 178, 46), green=(46, 182, 125), blue=(54, 197, 240),
        btn=(240, 239, 240), btn_edge=None, btn_down=(221, 220, 221), glyph=(97, 96, 97),
        track=(221, 221, 221),
        title_lit=(255, 255, 255), title_dim=(188, 171, 188),
        pledit=dict(Normal="#CFC3CF", Current="#FFFFFF", NormalBG="#3F0E40", SelectedBG="#1164A3"),
        vis_bars=[(224, 30, 90), (236, 178, 46), (46, 182, 125), (54, 197, 240)], vis_dots=(242, 242, 242),
        vis_peak=(63, 14, 64),
        vis_osc=[(18, 100, 163), (54, 197, 240), (46, 182, 125), (236, 178, 46), (224, 30, 90)],
        main_title="now-playing", eq_title="equalizer", pl_title="playlist",
        gen_bg=((74, 21, 75), (17, 100, 163)),
    ),
    # A Palo Alto Networks firewall: the PA-series hardware front (black chassis, the orange stripe,
    # port LEDs, vents) framing the PAN-OS web interface (white panels, grey-blue tables, the
    # Dashboard/ACC/Monitor/Policies/Objects/Network/Device tab row, the orange Commit button).
    "palo-alto": SimpleNamespace(
        name="palo-alto", wsz="Palo-Alto-Networks.wsz",
        subject="a Palo Alto Networks firewall (PA-series hardware, PAN-OS web interface)",
        logo_owner="Palo Alto Networks", logo=os.path.join(SRC, "logo-paloalto", "paloalto.svg"),
        logo_url="https://commons.wikimedia.org/wiki/File:PaloAltoNetworks_2020_Logo.svg",
        bar_lit=[(52, 55, 59), (36, 38, 41), (30, 32, 35)], bar_dim=[(70, 72, 76), (58, 60, 63), (54, 56, 59)],
        bar_line=None, edge=(8, 8, 9),
        body=(33, 35, 38), frame_body=(33, 35, 38),
        rail=None, stripe=(250, 88, 45),
        disp=(255, 255, 255), disp_edge=(150, 160, 170), disp_r=1.5,
        txt=(51, 51, 51), label=(150, 158, 166), flabel=(120, 130, 140), digit=(31, 58, 86),
        accent=(250, 88, 45), accent_dk=(200, 60, 24), accent_lt=(255, 222, 210), blue=(15, 110, 170),
        led=(63, 221, 106), led_off=(36, 52, 40), amber=(255, 176, 0),
        btn=[(74, 78, 83), (54, 57, 61)], btn_edge=(12, 13, 14), btn_down=[(38, 40, 43), (46, 48, 52)],
        glyph=(214, 219, 224), track=(12, 13, 14),
        title_lit=(236, 239, 242), title_dim=(140, 146, 152),
        pledit=dict(Normal="#333333", Current="#1E7D32", NormalBG="#FFFFFF", SelectedBG="#D8E6F3"),
        vis_bars=[(127, 182, 221), (15, 110, 170), (10, 70, 120)], vis_dots=(236, 240, 244),
        vis_peak=(250, 88, 45),
        vis_osc=[(15, 110, 170), (40, 130, 190), (70, 150, 205), (100, 170, 215), (140, 195, 230)],
        main_title="", eq_title="", pl_title="",
        gen_bg=((236, 240, 244), (15, 110, 170)),
    ),
}

# Slack with white text areas, like its message pane: the playlist (and any pledit-coloured text
# in the gen.bmp frames) is white with Slack's text colour; the aubergine chrome stays.
THEMES["slack-light"] = SimpleNamespace(**dict(
    vars(THEMES["slack"]), name="slack-light", base="slack", wsz="Slack-Light.wsz",
    subject="Slack (the 2019 brand, 2023 layout), light message pane",
    pledit=dict(Normal="#1D1C1D", Current="#1264A3", NormalBG="#FFFFFF", SelectedBG="#E8F5FA"),
    gen_bg=((255, 255, 255), (232, 245, 250)),
))

ALIASES = {"palo": "palo-alto", "pa": "palo-alto"}


def use_theme(name):
    global T, OUT
    T = THEMES[ALIASES.get(name, name)]
    OUT = os.path.join(OUT_ROOT, T.name)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT_ROOT, "scratch"), exist_ok=True)


def logo_png(px_h):
    """The theme's logo as a PNG (rasterised from SVG into out/scratch). Palo Alto's black
    wordmark is turned white, for the dark chassis; its orange mark stays."""
    out = os.path.join(OUT_ROOT, "scratch", f"logo-{T.name}-{px_h}.png")
    if not os.path.exists(out):
        subprocess.run(["/usr/bin/rsvg-convert", "-h", str(px_h), T.logo, "-o", out], check=True)
        if T.name == "palo-alto":
            im = np.asarray(Image.open(out).convert("RGBA")).astype(np.int32)
            rgb_ = im[..., :3]
            dark = rgb_.sum(-1) < 200
            rgb_[dark] = (236, 239, 242)
            Image.fromarray(np.dstack([rgb_, im[..., 3:]]).astype(np.uint8), "RGBA").save(out)
    return out


IS = lambda *n: T.name in n or getattr(T, "base", None) in n   # noqa: E731


# ------------------------------------------------------------------------------------------
# Frame pieces
# ------------------------------------------------------------------------------------------


def bar_stops(lit):
    return T.bar_lit if lit else T.bar_dim


def bar_frame(w, h, lit, left_edge=False, right_edge=False):
    """A titlebar strip: the bar colour, its hairline, the window's outer edges."""
    a = new(w, h)
    vfill(a, 0, 0, w, h, bar_stops(lit))
    if IS("palo-alto"):
        rect(a, 0, 0, w, 1, (78, 82, 87) if lit else (92, 95, 99))
        rect(a, 0, 0, w, 1, (78, 82, 87) if lit else (92, 95, 99))
    else:
        rect(a, 0, 0, w, 1, T.edge)
    if left_edge:
        rect(a, 0, 0, 1, h, T.edge)
        if IS("palo-alto"):
            rect(a, 2, 1, 2, h - 1, T.stripe if lit else lerp(T.stripe, (60, 60, 60), 0.45))
    if right_edge:
        rect(a, w - 1, 0, 1, h, T.edge)
    return a


def caption_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar buttons: options, minimize, shade, close (Fluent / Slack / chassis styles)."""
    W, H = a.shape[1], a.shape[0]
    if IS("teams"):
        ink = (66, 66, 66) if lit else (150, 150, 150)
        if pressed:
            rbox(a, x, y, 9, 9, 2, (196, 43, 28) if kind == "close" else (214, 214, 214))
            ink = WHITE if kind == "close" else (36, 36, 36)
    elif IS("slack"):
        ink = (230, 220, 230) if lit else (170, 150, 170)
        if pressed:
            rbox(a, x, y, 9, 9, 2, T.red if kind == "close" else (110, 70, 111))
            ink = WHITE
    else:
        rbox(a, x, y, 9, 9, 1.5, T.btn_down if pressed else ([(84, 88, 93), (60, 63, 67)] if lit else
                                                           [(88, 90, 94), (76, 78, 82)]), T.btn_edge)
        ink = (T.accent if kind == "close" else WHITE) if pressed else ((206, 212, 218) if lit else (150, 155, 160))
    o = 1 if (pressed and IS("palo-alto")) else 0
    x += o
    y += o
    if kind == "options":
        if IS("teams"):
            for dx in (2, 4, 6):          # the "..." more button
                rect(a, x + dx, y + 4, 1, 1, ink)
        elif IS("slack"):
            for dy in (2, 4, 6):          # the hamburger
                rect(a, x + 2, y + dy, 5, 1, ink)
        else:
            for dy in (2, 4, 6):
                rect(a, x + 2, y + dy, 5, 1, ink)
    elif kind == "minimize":
        rect(a, x + 2, y + 5, 5, 1, ink)
    elif kind == "shade":
        rect(a, x + 2, y + 2, 5, 1, ink)
        rect(a, x + 2, y + 3, 5, 1, ink)
        rect(a, x + 2, y + 6, 5, 1, ink)
        rect(a, x + 2, y + 2, 1, 5, ink)
        rect(a, x + 6, y + 2, 1, 5, ink)
    elif kind == "close":
        paint(a, 0, 0, line_mask(W, H, [(x + 2.2, y + 2.2), (x + 6.8, y + 6.8)], 1.3), ink)
        paint(a, 0, 0, line_mask(W, H, [(x + 6.8, y + 2.2), (x + 2.2, y + 6.8)], 1.3), ink)


def title_col(lit):
    return T.title_lit if lit else T.title_dim


def channel_title(a, name, x, y, lit, chevron=False):
    """Slack: '# name', bold white when focused (an unread channel), plain lilac when not."""
    col = title_col(lit)
    icon(a, IC["hash"], x, y + 2, (190, 170, 190) if lit else (150, 128, 150))
    x = draw_ui(a, name, x + 8, y, col, bold=lit)
    if chevron:
        icon(a, IC["chevron"], x + 2, y + 4, col)
    return x


def mention_badge(a, x, y, n):
    """Slack's red mention badge (a pill with a white count)."""
    s = str(n)
    w = max(9, text_w(TINY, s) + 5)
    rbox(a, x, y, w, 9, 4.49, T.red)
    text_center(a, TINY, s, x + w // 2, y + 2, WHITE)
    return w


def search_box(a, x, y, w, h, lit, text="Search"):
    if IS("teams"):
        rbox(a, x, y, w, h, 3, WHITE if lit else (250, 250, 250), (214, 214, 214) if lit else (230, 230, 230))
        ink = (97, 97, 97) if lit else (170, 170, 170)
    else:  # slack: the translucent box on the aubergine bar
        rbox(a, x, y, w, h, 4, (100, 70, 101) if lit else (110, 88, 111))
        ink = (222, 210, 222) if lit else (170, 150, 170)
    icon(a, IC["search"], x + 4, y + (h - 5) // 2, ink)
    draw_text(a, TINY, text.upper(), x + 12, y + (h - 5) // 2, ink)


def pa_vents(a, x0, x1, y, rows=2, lit=True):
    """The chassis' ventilation slots."""
    hole, rim = ((10, 10, 11), (70, 74, 78)) if lit else ((34, 35, 37), (84, 86, 90))
    for r in range(rows):
        off = 0 if r % 2 == 0 else 3
        for x in range(x0 + off, x1 - 4, 6):
            rect(a, x, y + r * 3, 4, 2, hole)
            rect(a, x, y + r * 3 + 2, 4, 1, rim)


PA_TABS = ["DASHBOARD", "ACC", "MONITOR", "POLICIES", "OBJECTS", "NETWORK", "DEVICE"]


def pa_tab_row(a, x, y, lit, selected="ACC", x1=258):
    """PAN-OS's top tab row in capitals, the selected tab white with the orange underline."""
    widths = [text_w(TINY, t) for t in PA_TABS]
    gap = (x1 - x - sum(widths)) / (len(PA_TABS) - 1)
    cx = x
    for t, w in zip(PA_TABS, widths):
        xi = int(round(cx))
        if t == selected:
            rect(a, xi - 3, 1, w + 6, 13, (64, 68, 73) if lit else (78, 80, 84))
            rect(a, xi - 3, 12, w + 6, 2, T.accent if lit else lerp(T.accent, (80, 80, 80), 0.5))
            col = WHITE if lit else (190, 194, 198)
        else:
            col = (160, 168, 176) if lit else (120, 124, 128)
        draw_text(a, TINY, t, xi, y, col)
        cx += w + gap


def main_titlebar(lit):
    a = bar_frame(275, 14, lit, left_edge=True, right_edge=True)
    if IS("teams"):
        rect(a, 1, 13, 273, 1, T.bar_line)
        draw_ui(a, T.main_title, 19, 2, title_col(lit), bold=True)
        # the meeting's own controls: camera, mic (muted), then a hairline
        ink = (66, 66, 66) if lit else (160, 160, 160)
        search_box(a, 88, 2, 96, 10, lit)
        icon(a, IC["cam"], 202, 4, ink)
        icon(a, IC["mic"], 216, 3, ink)
        rect(a, 214, 10, 9, 1, T.red if lit else (210, 150, 160))   # the "muted" slash, flattened
        paint(a, 0, 0, line_mask(275, 14, [(214.5, 3.5), (221.5, 11)], 1.1), T.red if lit else (210, 150, 160))
        rect(a, 230, 3, 1, 8, (209, 209, 209))
    elif IS("slack"):
        channel_title(a, T.main_title, 19, 2, lit)
        search_box(a, 100, 2, 130, 10, lit, "Search YTMinamp")
    else:
        if lit:
            logo(a, 15, 1, (68, 12), logo_png(48))
        if not lit:
            # the unfocused logo: the same, greyed
            t = bar_frame(275, 14, True)
            logo(t, 15, 1, (68, 12), logo_png(48))
            g = t[1:13, 15:83].mean(-1, keepdims=True)
            bgc = np.array(bar_stops(False)[1])
            lum = (g - 36) / 200
            a[1:13, 15:83] = np.round(bgc + np.clip(lum, 0, 1) * (np.array([170, 174, 178]) - bgc)).astype(np.int32)
        draw_text(a, TINY, "PA-460", 86, 5, (150, 156, 162) if lit else (110, 114, 118))
        pa_vents(a, 114, 226, 3, rows=3, lit=lit)
        icon(a, IC["lock"], 231, 3, (214, 219, 224) if lit else (130, 134, 138))
    caption_button(a, 6, 3, "options", lit)
    caption_button(a, 244, 3, "minimize", lit)
    caption_button(a, 254, 3, "shade", lit)
    caption_button(a, 264, 3, "close", lit)
    return a


CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters, bg):
    a = new(8, 43, bg)
    if IS("palo-alto"):
        rbox(a, 0, 0, 8, 43, 1.5, (14, 15, 16), (6, 6, 7))
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            if IS("palo-alto"):
                rbox(a, 1, y, 6, h, 1, (70, 30, 18))
            else:
                rbox(a, 1, y, 6, h, 1.5, T.rail_sel)
        gy = y + (h - 5) // 2
        if IS("palo-alto"):
            ink = T.accent if on else T.label
        else:
            ink = WHITE if on else T.rail_ink
        draw_text(a, TINY, letter, 2, gy, ink)
    return a


def make_titlebar(main):
    a = new(344, 87, T.frame_body)
    bar = main_titlebar(True)
    for kind, x in (("options", 0), ("minimize", 9), ("close", 18)):
        src = {"options": 6, "minimize": 244, "close": 264}[kind]
        a[0:9, x:x + 9] = bar[3:12, src:src + 9]
        a[9:18, x:x + 9] = bar_cell_pressed(kind, src)
    a[18:27, 0:9] = bar[3:12, 254:263]
    a[18:27, 9:18] = bar_cell_pressed("shade", 254)
    a[0:14, 27:302] = bar
    a[15:29, 27:302] = main_titlebar(False)
    a[29:43, 27:302] = bar
    a[42:56, 27:302] = main_titlebar(False)
    unlit = clutter_bar("", main[30, 9])
    lit = clutter_bar("OAIDV", main[30, 9])
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = lit[y:y + h]
    return a


def bar_cell_pressed(kind, src):
    cell = bar_frame(275, 14, True, left_edge=True, right_edge=True)[3:12, src:src + 9].copy()
    caption_button(cell, 0, 0, kind, True, pressed=True)
    return cell


# ------------------------------------------------------------------------------------------
# Window bodies: rails (Teams, Slack), the orange stripe (Palo Alto), outer edges
# ------------------------------------------------------------------------------------------

RAIL_W = {"main": 20, "eq": 12, "pl": 12, "gen": 11}


def left_side(a, y0, y1, which):
    """The left strip of a window body from row y0 to y1 (exclusive)."""
    if y1 <= y0:
        return
    if T.rail is not None and which == "main":
        # wide enough for the clutterbar, then narrower so the seek bar and transport clear it
        rect(a, 0, y0, 20, 70 - y0, T.rail)
        rect(a, 0, 70, 14, y1 - 70, T.rail)
        rect(a, 14, 70, 2, 1, T.rail)
        px(a, 14, 71, T.rail)
    elif T.rail is not None:
        rect(a, 0, y0, RAIL_W[which], y1 - y0, T.rail)
    else:
        rect(a, 0, y0, 1, y1 - y0, T.edge)
        rect(a, 2, y0, 2, y1 - y0, T.stripe)


def right_side(a, y0, y1):
    rect(a, a.shape[1] - 1, y0, 1, y1 - y0, T.edge)


def rail_icon(a, name, x, y, selected=False, pill_x=0):
    if selected:
        rect(a, pill_x, y - 1, 2, 9, T.rail_sel)
        icon(a, IC[name], x, y, T.rail_sel)
    else:
        icon(a, IC[name], x, y, T.rail_ink)


def main_bg():
    a = new(275, 116, T.body)
    a[0:14] = main_titlebar(True)
    left_side(a, 14, 116, "main")
    right_side(a, 14, 116)
    rect(a, 0, 115, 275, 1, T.edge)
    if IS("teams"):
        rail_icon(a, "bell", 4, 76)
        rail_icon(a, "chat", 4, 89)
        rail_icon(a, "teams", 4, 103, selected=True)
    elif IS("slack"):
        # the 2023 rail: Activity with a mention badge, DMs
        icon(a, IC["bell"], 3, 76, T.rail_ink)
        rbox(a, 7, 72, 7, 7, 3.49, T.red)
        draw_text(a, TINY, "3", 9, 73, WHITE)
        icon(a, IC["chat"], 3, 90, T.rail_ink)
        rbox(a, 2, 101, 10, 10, 2.5, (95, 52, 96))
        draw_text(a, TINY, "Y", 3, 103, WHITE)     # the workspace tile
        draw_text(a, TINY, "M", 7, 103, WHITE)
    else:
        rect(a, 0, 14, 275, 1, (58, 61, 65))
    return a


def field(a, x, y, w, h):
    """A display field: the inside is (x, y, w, h) in the display colour."""
    rbox(a, x - 1, y - 1, w + 2, h + 2, T.disp_r, T.disp, T.disp_edge)


# ------------------------------------------------------------------------------------------
# Buttons, toggles, sliders
# ------------------------------------------------------------------------------------------


def tri(a, pts, col, alpha=1.0):
    paint(a, 0, 0, poly_mask(a.shape[1], a.shape[0], pts), col, alpha)


def glyph(a, kind, cx, cy, col, s=1.0):
    W, H = a.shape[1], a.shape[0]
    if kind == "previous":
        tri(a, [(cx - 3 * s, cy), (cx + 3.5 * s, cy - 4 * s), (cx + 3.5 * s, cy + 4 * s)], col)
        rect(a, int(round(cx - 4.6 * s)), int(round(cy - 4 * s)), max(1, round(1.6 * s)), int(round(8 * s)), col)
    elif kind == "next":
        tri(a, [(cx + 3 * s, cy), (cx - 3.5 * s, cy - 4 * s), (cx - 3.5 * s, cy + 4 * s)], col)
        rect(a, int(round(cx + 3.2 * s)), int(round(cy - 4 * s)), max(1, round(1.6 * s)), int(round(8 * s)), col)
    elif kind == "play":
        tri(a, [(cx - 3 * s, cy - 4.5 * s), (cx + 4.5 * s, cy), (cx - 3 * s, cy + 4.5 * s)], col)
    elif kind == "pause":
        paint(a, 0, 0, rr_mask(W, H, 0.6, cx - 3.5 * s, cy - 4 * s, 2.6 * s, 8 * s), col)
        paint(a, 0, 0, rr_mask(W, H, 0.6, cx + 1 * s, cy - 4 * s, 2.6 * s, 8 * s), col)
    elif kind == "stop":
        paint(a, 0, 0, rr_mask(W, H, 1.0, cx - 3.5 * s, cy - 3.5 * s, 7 * s, 7 * s), col)
    elif kind == "eject":
        tri(a, [(cx - 4.5 * s, cy + 1 * s), (cx, cy - 4 * s), (cx + 4.5 * s, cy + 1 * s)], col)
        paint(a, 0, 0, rr_mask(W, H, 0.5, cx - 4.5 * s, cy + 2.5 * s, 9 * s, 1.8 * s), col)
    elif kind == "hangup":
        # a handset lying face down (Teams' Leave)
        paint(a, 0, 0, rr_mask(W, H, 2.5, cx - 6, cy - 2.5, 12, 4.2), col)
        paint(a, 0, 0, rr_mask(W, H, 1.0, cx - 6, cy - 0.5, 3.2, 3.6), col)
        paint(a, 0, 0, rr_mask(W, H, 1.0, cx + 2.8, cy - 0.5, 3.2, 3.6), col)
    elif kind == "share":
        # Teams' Share: a screen with an arrow going up out of it
        x0, y0 = int(cx - 5), int(cy - 3)
        rect(a, x0, y0, 11, 1, col)
        rect(a, x0, y0, 1, 8, col)
        rect(a, x0 + 10, y0, 1, 8, col)
        rect(a, x0, y0 + 7, 11, 1, col)
        rect(a, x0 + 3, y0 + 9, 5, 1, col)
        tri(a, [(cx - 3, cy + 0.5), (cx + 0.5, cy - 4.5), (cx + 4, cy + 0.5)], col)
        rect(a, int(cx - 0.5), int(cy), 2, 4, col)
    elif kind == "send":
        # Slack's send arrow: a paper plane seen side-on
        tri(a, [(cx - 4.5, cy - 4.5), (cx + 5, cy), (cx - 4.5, cy + 4.5), (cx - 2.5, cy)], col)


TRAY_X, TRAY_Y, TRAY_W, TRAY_H = 16, 88, 142, 18
CB = {"previous": (0, 23), "play": (23, 23), "pause": (46, 23), "stop": (69, 23), "next": (92, 22)}
EJECT = (120, 1, 22, 16)   # within the tray canvas


def tray(bg, pressed=None):
    """The transport tray (prev..next, eject) on bg (TRAY_W x TRAY_H), one button pressed."""
    a = bg.copy()
    W, H = a.shape[1], a.shape[0]
    cells = {k: (x, 0, w, H) for k, (x, w) in CB.items()}
    cells["eject"] = EJECT
    for k, (x, y, w, h) in cells.items():
        p = k == pressed
        cx, cy = x + w / 2, y + h / 2
        if IS("teams"):
            # Fluent buttons: secondary (white, hairline), Join (brand purple), Leave (red)
            x0, w0 = x + 1, w - 2
            if k == "play":
                rbox(a, x0, y + 1, w0, h - 2, 3, T.accent_dk if p else T.accent)
                o = 1 if p else 0
                draw_text(a, TINY, "JOIN", x0 + 3 + o, int(cy) - 2 + o, WHITE)
            elif k == "stop":
                rbox(a, x0, y + 1, w0, h - 2, 3, (164, 38, 44) if p else T.red)
                glyph(a, "hangup", cx + (1 if p else 0), cy + (1 if p else 0), WHITE)
            else:
                rbox(a, x0, y + 1, w0, h - 2, 3, T.btn_down if p else T.btn, (180, 180, 180) if p else T.btn_edge)
                o = 0.5 if p else 0
                if k == "eject":
                    glyph(a, "share", cx + o, cy + o, (36, 36, 36) if p else T.glyph)
                else:
                    glyph(a, k, cx + o, cy + o, (36, 36, 36) if p else T.glyph, 0.95)
        elif IS("slack"):
            # the composer's toolbar: plain grey icons, the green send button for play
            if k == "play":
                rbox(a, x + 2, y + 1, w - 4, h - 2, 3, (0, 92, 68) if p else T.send)
                glyph(a, "send", cx + (0.5 if p else 0), cy + (0.5 if p else 0), WHITE)
            else:
                if p:
                    rbox(a, x + 2, y + 1, w - 4, h - 2, 3, (232, 232, 232))
                glyph(a, k, cx, cy, (29, 28, 29) if p else T.glyph, 0.9)
        else:
            # chassis keys; Commit (play) is PAN-OS orange
            o = 1 if p else 0
            if k == "play":
                stops = [(200, 66, 30), (226, 76, 38)] if p else [(255, 128, 92), (250, 88, 45), (226, 70, 30)]
                rbox(a, x + 1, y + 1, w - 2, h - 2, 2, stops, (60, 18, 6))
                glyph(a, k, cx + o, cy + o, WHITE, 0.95)
            else:
                rbox(a, x + 1, y + 1, w - 2, h - 2, 2, T.btn_down if p else T.btn, T.btn_edge)
                if not p:
                    rect(a, x + 3, y + 2, w - 6, 1, (98, 103, 109))
                glyph(a, k, cx + o, cy + o, T.accent if p else T.glyph, 0.9)
    return a


def toggle_cell(bg, w, h, label, on, pressed):
    a = bg.copy()
    if IS("teams"):
        if on:
            rbox(a, 0, 0, w, h, 3, (205, 210, 245) if pressed else T.accent_lt, T.accent)
            ink = T.accent_dk
        else:
            rbox(a, 0, 0, w, h, 3, T.btn_down if pressed else T.btn, (180, 180, 180) if pressed else T.btn_edge)
            ink = (66, 66, 66)
        o = 1 if pressed else 0
        badge = label in ("SHUFFLE", "REPEAT", "EQ", "PL", "ON", "AUTO")
        if label:
            shift = 0 if (label == "REPEAT" or not badge) else (2 if w < 30 else 3)
            text_center(a, TINY, label, w // 2 - shift + o, (h - 5) // 2 + o, ink)
        if badge:
            # the presence badge: available when on, offline when off, away while held
            bx, by = w - 6, (h - 5) // 2
            if label == "REPEAT":
                bx, by = w - 5, 0
            col = T.yellow if pressed else (T.green if on else None)
            if col is not None:
                paint(a, bx, by, ellipse_mask(5, 5, 0, 0, 5, 5), col)
            else:
                paint(a, bx, by, ellipse_mask(5, 5, 0, 0, 5, 5), T.grey)
                paint(a, bx, by, ellipse_mask(5, 5, 1, 1, 3, 3), a[by + 2, bx + 2] * 0 + np.array(
                    T.accent_lt if on else T.btn, np.int32))
    elif IS("slack"):
        # emoji-reaction pills: grey, or blue-ringed once reacted
        dark = sum(bg[h // 2, 0]) < 300
        if dark:
            rbox(a, 0, 0, w, h, min(h / 2 - 0.01, 5), (70, 36, 71) if pressed else (96, 58, 97))
            ink = (240, 232, 240)
        elif on:
            rbox(a, 0, 0, w, h, h / 2 - 0.01, (210, 232, 244) if pressed else T.accent_lt, T.ring)
            ink = T.accent
        else:
            rbox(a, 0, 0, w, h, h / 2 - 0.01, T.btn_down if pressed else T.btn)
            ink = (60, 59, 60)
        o = 1 if pressed else 0
        if label == "SHUFFLE":
            icon(a, IC["shuffle"], 4 + o, (h - 7) // 2 + o, T.accent if on else T.glyph)
            draw_text(a, TINY, label, 15 + o, (h - 5) // 2 + o, ink)
        elif label == "REPEAT":
            icon(a, IC["repeat"], 4 + o, (h - 7) // 2 + o, T.accent if on else T.glyph)
            draw_text(a, FONT5, "1" if on else "0", 18 + o, (h - 5) // 2 + o, ink)
        elif label:
            text_center(a, TINY, label, w // 2 + o, (h - 5) // 2 + o, ink)
    else:
        # chassis keys with a link LED under the silkscreen label
        rbox(a, 0, 0, w, h, 1.5, T.btn_down if pressed else T.btn, T.btn_edge)
        if not pressed:
            rect(a, 2, 1, w - 4, 1, (98, 103, 109))
        o = 1 if pressed else 0
        if label:
            ly = 2 if h <= 12 else 3
            text_center(a, TINY, label, w // 2 + o, ly + o, (236, 239, 242) if on else (176, 182, 188))
            led = T.led if on else T.led_off
            rect(a, 4 + o, h - 4 + o, w - 8, 1, led)
            if on:
                rect(a, 4 + o, h - 3 + o, w - 8, 1, lerp(T.led, T.btn[1], 0.6))
    return a


def track_h(a, x, y, w, th, fill_from=None, fill_to=None, colour=None):
    W, H = a.shape[1], a.shape[0]
    r = th / 2
    inner = rr_mask(W, H, r, x, y, w, th)
    paint(a, 0, 0, inner, T.track)
    if IS("palo-alto"):
        top = inner.copy()
        top[y + 1:, :] = 0
        paint(a, 0, 0, top, (0, 0, 0))
    if fill_from is not None and fill_to is not None and fill_to > fill_from:
        f = inner.copy()
        f[:, :max(0, int(fill_from))] = 0
        f[:, max(0, int(fill_to)):] = 0
        paint(a, 0, 0, f, colour or (T.accent if not IS("slack") else T.accent))


def track_v(a, x, y, h, tw, fill_from=None):
    W, H = a.shape[1], a.shape[0]
    inner = rr_mask(W, H, tw / 2, x, y, tw, h)
    paint(a, 0, 0, inner, T.track)
    if fill_from is not None:
        f = inner.copy()
        f[:int(fill_from), :] = 0
        paint(a, 0, 0, f, T.accent)


def knob(a, x, y, w, h, pressed):
    """Fluent: a white disc in a brand ring; Slack: a white disc; Palo Alto: a metal key."""
    W, H = a.shape[1], a.shape[0]
    if IS("teams"):
        d = min(w, h)
        x0, y0 = x + (w - d) / 2, y + (h - d) / 2
        paint(a, 0, 0, ellipse_mask(W, H, x0, y0, d, d), T.accent_dk if pressed else T.accent)
        paint(a, 0, 0, ellipse_mask(W, H, x0 + 2, y0 + 2, d - 4, d - 4), WHITE)
    elif IS("slack"):
        d = min(w, h)
        x0, y0 = x + (w - d) / 2, y + (h - d) / 2
        paint(a, 0, 0, ellipse_mask(W, H, x0, y0 + 0.6, d, d), BLACK, 0.18)
        paint(a, 0, 0, ellipse_mask(W, H, x0, y0, d, d), (160, 160, 160) if not pressed else T.accent)
        paint(a, 0, 0, ellipse_mask(W, H, x0 + 1, y0 + 1, d - 2, d - 2), WHITE)
    else:
        stops = [(150, 156, 162), (110, 115, 120)] if pressed else [(222, 226, 230), (150, 156, 162)]
        rbox(a, x, y, w, h, 1.5, stops, (10, 10, 11))
        cx = x + w // 2
        rect(a, cx, y + 2, 1, h - 4, T.accent)


# ------------------------------------------------------------------------------------------
# main.bmp and friends
# ------------------------------------------------------------------------------------------

DIGITS_COL = None


def digit(a, n, x, y, col):
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + 1 + c, y + 1 + r, col)


def make_main():
    a = main_bg()
    bg = a[30, 9]
    a[22:65, 10:18] = clutter_bar("", bg)
    if IS("slack"):
        # the composer: one rounded box round the title (message) and info (toolbar) rows
        rbox(a, 107, 19, 163, 37, 5, T.disp, T.disp_edge)
        rect(a, 109, 38, 159, 1, (232, 232, 232))
        field(a, 21, 20, 84, 42)
    else:
        field(a, 21, 20, 84, 42)
        field(a, 109, 21, 159, 15)
        field(a, 109, 40, 159, 14)
    if IS("palo-alto"):
        # the display as a PAN-OS dashboard widget: a grey-blue header strip
        rect(a, 21, 20, 84, 4, (228, 233, 238))
        rect(a, 21, 23, 84, 1, (200, 208, 216))
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, T.digit)
    draw_text(a, TINY, "KBPS", 129, 44, T.flabel)
    draw_text(a, TINY, "KHZ", 169, 44, T.flabel)
    track_h(a, 108, 61, 66, 5)
    track_h(a, 178, 61, 36, 5)
    track_h(a, 16, 74, 248, 6)
    a[TRAY_Y:TRAY_Y + TRAY_H, TRAY_X:TRAY_X + TRAY_W] = tray(a[TRAY_Y:TRAY_Y + TRAY_H, TRAY_X:TRAY_X + TRAY_W])
    if IS("palo-alto"):
        # silkscreen under the keys
        x, w = CB["play"]
        text_center(a, TINY, "COMMIT", TRAY_X + x + w // 2, 108, T.accent)
        # the front-panel status LEDs in the About spot
        for i, (lbl, col) in enumerate((("PWR", T.led), ("STS", T.led), ("HA", T.amber), ("ALM", None))):
            x, y = 248 + (i % 2) * 14, 89 + (i // 2) * 11
            rect(a, x, y, 3, 2, col if col else (60, 30, 24))
            if col:
                rect(a, x - 1, y, 1, 2, lerp(col, T.body, 0.6))
                rect(a, x + 3, y, 1, 2, lerp(col, T.body, 0.6))
            text_center(a, TINY, lbl, x + 1, y + 4, T.label)
    else:
        logo(a, 246, 87, (20, 20), logo_png(80))
    return a


def make_cbuttons(main):
    a = new(136, 36, T.frame_body)
    clean = main_bg()
    clean = clean[TRAY_Y:TRAY_Y + TRAY_H, TRAY_X:TRAY_X + TRAY_W]
    normal = tray(clean)
    for k, (x, w) in CB.items():
        a[0:18, x:x + w] = normal[:, x:x + w]
        a[18:36, x:x + w] = tray(clean, k)[:, x:x + w]
    ex, ey, ew, eh = EJECT
    a[0:16, 114:136] = normal[ey:ey + eh, ex:ex + ew]
    a[16:32, 114:136] = tray(clean, "eject")[ey:ey + eh, ex:ex + ew]
    return a


def make_shufrep(main):
    a = new(92, 85, T.frame_body)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = toggle_cell(main[89:104, 210:238], 28, 15, "REPEAT", on, pressed)
        a[y:y + 15, 28:75] = toggle_cell(main[89:104, 164:211], 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        src = main[58:70, 219 + (x % 46):219 + (x % 46) + 23]
        a[61:73, x:x + 23] = toggle_cell(src, 23, 12, label, False, pressed)
        a[73:85, x:x + 23] = toggle_cell(src, 23, 12, label, True, pressed)
    return a


def make_monoster():
    a = new(56, 24, T.disp)
    on_col = T.blue if IS("palo-alto") else T.accent
    off = lerp(T.disp, T.flabel, 0.3)
    for y, on in ((0, True), (12, False)):
        col = on_col if on else off
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T.disp)
    if IS("teams"):
        # presence: Available (playing), Away (paused), Do not disturb (stopped)
        for x0, col in ((0, T.green), (9, T.yellow), (18, T.red)):
            paint(a, x0, 0, ellipse_mask(9, 9, 0, 0, 9, 9), col)
        tri(a, [(3, 2), (7, 4.5), (3, 7)], WHITE)
        rect(a, 9 + 3, 2, 1, 5, WHITE)
        rect(a, 9 + 5, 2, 1, 5, WHITE)
        rect(a, 18 + 2, 4, 5, 1, WHITE)
        rect(a, 18 + 2, 4, 5, 1, WHITE)
        col = T.accent
    else:
        col = T.green if IS("slack") else T.led
        if IS("palo-alto"):
            col = (30, 140, 60)
        tri(a, [(2, 1), (8, 4.5), (2, 8)], col)
        rect(a, 9 + 2, 1, 2, 7, col)
        rect(a, 9 + 5, 1, 2, 7, col)
        rect(a, 18 + 2, 2, 5, 5, T.red if IS("slack") else T.accent)
    rect(a, 36, 0, 3, 9, T.disp)
    rect(a, 39 + 1, 3, 1, 3, col)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T.disp)
    for n in range(10):
        digit(a, n, 9 * n, 0, T.digit)
    if ex:
        rect(a, 99 + 2, 6, 5, 2, T.digit)
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]

TEXT_FONT = dict(FONT5, M=G("#..#", "####", "####", "#..#", "#..#"), W=G("#..#", "#..#", "####", "####", "#..#"))


def make_text():
    a = new(155, 18, T.disp)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, TEXT_FONT, key, col * 5, row * 6, T.txt)
    return a


def make_posbar(main):
    a = new(307, 10, T.frame_body)
    a[0:10, 0:248] = main[72:82, 16:264]
    for x0, sel in ((248, False), (278, True)):
        t = main[72:82, 16 + 100:16 + 129].copy()
        track_h(t, -20, 2, 69, 6, fill_from=0, fill_to=14)
        if IS("palo-alto"):
            knob(t, 9, 0, 11, 10, sel)
        else:
            knob(t, 9, 0, 10, 10, sel)
        a[0:10, x0:x0 + 29] = t
    return a


def slider_thumbs(a, seat):
    for x, sel in ((0, True), (15, False)):
        t = seat[1:12, 20:34].copy()
        track_h(t, -10, 4, 40, 5, fill_from=0, fill_to=7)
        if IS("palo-alto"):
            knob(t, 2, 0, 10, 11, sel)
        else:
            knob(t, 1, 0, 12, 11, sel)
        a[422:433, x:x + 14] = t


def make_volume(main):
    a = new(68, 433, T.frame_body)
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        t = seat.copy()
        level = (i + 1) / 28
        track_h(t, 1, 4, 66, 5, fill_from=0, fill_to=1 + round(level * 66))
        a[y:y + 15, 0:68] = t
    slider_thumbs(a, seat)
    return a


def make_balance(main):
    a = new(68, 433, T.frame_body)
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        t = seat.copy()
        reach = round(17 * i / 27)
        track_h(t, 1, 4, 36, 5, fill_from=19 - max(1, reach), fill_to=19 + max(1, reach),
                colour=T.accent if i else T.label)
        a[y:y + 15, 9:47] = t
        a[y:y + 15, 0:9] = seat[:, :1]
        a[y:y + 15, 47:68] = seat[:, -1:]
    slider_thumbs(a, main[57:72, 107:175])
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = bar_frame(275, 14, lit, left_edge=True, right_edge=True)
    if IS("teams"):
        rect(a, 1, 13, 273, 1, T.bar_line)
        draw_ui(a, T.eq_title, 8, 2, title_col(lit), bold=True)
        search_box(a, 90, 2, 96, 10, lit)
        # the signed-in avatar with its presence dot
        paint(a, 238, 2, ellipse_mask(10, 10, 0, 0, 10, 10), T.accent if lit else (190, 190, 205))
        draw_text(a, TINY, "Y", 241, 4, WHITE)
        paint(a, 244, 7, ellipse_mask(6, 6, 0, 0, 6, 6), bar_stops(lit)[0])
        paint(a, 245, 8, ellipse_mask(4, 4, 0, 0, 4, 4), T.green)
    elif IS("slack"):
        channel_title(a, T.eq_title, 8, 2, lit, chevron=True)
        # the members button: three avatars and a count
        for i, c in enumerate(((236, 178, 46), (54, 197, 240), (46, 182, 125))):
            rbox(a, 220 + i * 5, 3, 8, 8, 2, c if lit else lerp(c, bar_stops(lit)[0], 0.5), bar_stops(lit)[0])
        draw_text(a, FONT5, "3", 240, 4, title_col(lit))
    else:
        pa_tab_row(a, 9, 5, lit, "ACC", 256)
    caption_button(a, 264, 3, "close", lit)
    return a


def eq_frame_bg():
    a = new(275, 116, T.body)
    left_side(a, 14, 116, "eq")
    right_side(a, 14, 116)
    rect(a, 0, 115, 275, 1, T.edge)
    if IS("teams"):
        for i, (n, sel) in enumerate((("calendar", False), ("calls", True), ("files", False), ("apps", False))):
            if i == 3:
                icon(a, ["#.#.#"], 3, 100, T.rail_ink)
            else:
                rail_icon(a, n, 3, 22 + i * 18, selected=sel, pill_x=0)
    elif IS("slack"):
        icon(a, ["#.#.#"], 3, 26, T.rail_ink)
    else:
        rect(a, 0, 14, 275, 1, (58, 61, 65))
    return a


def eq_slider_frame(bg, n):
    a = bg.copy()
    v = n / 27
    centre = round((1 - v) * 51) + 5
    track_v(a, 5, 1, 61, 4, fill_from=centre)
    return a


def eq_thumb(bg, pressed):
    a = bg.copy()
    track_v(a, 4, -20, 60, 4, fill_from=5)
    if IS("palo-alto"):
        a[:, :] = bg
        track_v(a, 4, -20, 60, 4, fill_from=5)
        stops = [(150, 156, 162), (110, 115, 120)] if pressed else [(222, 226, 230), (150, 156, 162)]
        rbox(a, 0, 2, 11, 7, 1.5, stops, (10, 10, 11))
        rect(a, 2, 5, 7, 1, T.accent)
    else:
        knob(a, 0, 0, 11, 11, pressed)
    return a


def make_eqmain():
    a = new(275, 315, T.frame_body)
    base = eq_frame_bg()
    a[0:116] = base
    a[0:14] = eq_titlebar(True)
    field(a, 86, 17, 113, 19)
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, T.label)
    seat = base[38:101, 21:35]
    for x in [21] + [78 + 18 * i for i in range(10)]:
        a[38:101, x:x + 14] = eq_slider_frame(base[38:101, x:x + 14], 14)
    text_center(a, TINY, "PREAMP", 28, 104, T.label)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 104, T.label)
    rect(a, 40, 39, 1, 60, lerp(T.body, T.label, 0.35))
    for x, w, lbl in ((14, 26, "ON"), (40, 32, "AUTO")):
        a[18:30, x:x + w] = toggle_cell(base[18:30, x:x + w], w, 12, lbl, False, False)
    a[18:30, 217:261] = toggle_cell(base[18:30, 217:261], 44, 12, "PRESETS", False, False)

    a[125:134, 0:9] = eq_close_pressed()
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        src = base[18:30, 14:40] if label == "ON" else base[18:30, 40:72]
        a[119:131, x:x + w] = toggle_cell(src, w, 12, label, on, pressed)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    a[164:175, 0:11] = eq_thumb(base[40:51, 22:33], False)
    a[176:187, 0:11] = eq_thumb(base[40:51, 22:33], True)
    for n in range(28):
        x, y = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        a[y:y + 63, x:x + 14] = eq_slider_frame(seat, n)
    for y, pressed in ((164, False), (176, True)):
        a[y:y + 12, 224:268] = toggle_cell(base[18:30, 217:261], 44, 12, "PRESETS", False, pressed)
    rect(a, 0, 294, 113, 19, T.disp)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, T.vis_dots)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, lerp(T.disp, T.flabel, 0.35))
    stops = [T.accent, T.accent_dk] if not IS("palo-alto") else [T.blue, (10, 70, 120)]
    for r in range(19):
        px(a, 115, 294 + r, ramp(stops, r / 18))
    for x in range(113):
        px(a, x, 314, lerp(T.disp, T.flabel, 0.7) if x % 3 != 2 else T.disp)
    return a


def eq_close_pressed():
    bar = bar_frame(275, 14, True, left_edge=True, right_edge=True)
    cell = bar[3:12, 264:273].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    return cell


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109)
# ------------------------------------------------------------------------------------------


def bar20(w, lit, left_edge=False, right_edge=False):
    a = bar_frame(w, 20, lit, left_edge, right_edge)
    if IS("teams"):
        rect(a, 0, 19, w, 1, T.bar_line)
    return a


def side_tile(w, h, left, which):
    t = new(w, h, T.frame_body)
    if left:
        left_side(t, 0, h, which)
    else:
        right_side(t, 0, h)
    return t


def scroll_groove_col():
    return {"teams": (240, 240, 240), "slack": (63, 14, 64), "slack-light": (248, 248, 248),
            "palo-alto": (20, 21, 23)}[T.name]


def scroll_handle(pressed):
    t = new(8, 18, scroll_groove_col())
    if IS("teams"):
        rbox(t, 2, 0, 4, 18, 1.99, (97, 97, 97) if pressed else (189, 189, 189))
    elif IS("slack-light"):
        rbox(t, 1, 0, 6, 18, 2.99, (97, 96, 97) if pressed else (187, 186, 187))
    elif IS("slack"):
        rbox(t, 1, 0, 6, 18, 2.99, (190, 175, 190) if pressed else (120, 86, 121))
    else:
        rbox(t, 0, 0, 8, 18, 1.5, T.btn_down if pressed else T.btn, T.btn_edge)
        rect(t, 2, 8, 4, 2, T.accent if pressed else (130, 136, 142))
    return t


def mini_transport_icon(a, kind, x, y, col):
    cx, cy = x + 5, y + 5
    if kind == "previous":
        rect(a, cx - 3, cy - 2, 1, 5, col)
        tri(a, [(cx - 2, cy + 0.5), (cx + 0.5, cy - 2.5), (cx + 0.5, cy + 3.5)], col)
        tri(a, [(cx + 0.5, cy + 0.5), (cx + 3, cy - 2.5), (cx + 3, cy + 3.5)], col)
    elif kind == "play":
        tri(a, [(cx - 2, cy - 3), (cx + 3, cy + 0.5), (cx - 2, cy + 4)], col)
    elif kind == "pause":
        rect(a, cx - 2, cy - 2, 2, 5, col)
        rect(a, cx + 1, cy - 2, 2, 5, col)
    elif kind == "stop":
        rect(a, cx - 2, cy - 2, 5, 5, col)
    elif kind == "next":
        tri(a, [(cx + 2, cy + 0.5), (cx - 0.5, cy - 2.5), (cx - 0.5, cy + 3.5)], col)
        tri(a, [(cx - 0.5, cy + 0.5), (cx - 3, cy - 2.5), (cx - 3, cy + 3.5)], col)
        rect(a, cx + 2, cy - 2, 1, 5, col)
    elif kind == "eject":
        tri(a, [(cx - 2.5, cy + 0.5), (cx + 0.5, cy - 3), (cx + 3.5, cy + 0.5)], col)
        rect(a, cx - 2, cy + 1, 5, 1, col)


def title_piece_pl(lit):
    t = bar20(100, lit)
    if IS("teams"):
        s = T.pl_title
        x = 50 - (ui_w(s, True) + 12) // 2
        icon(t, IC["chat"], x, 6, T.accent if lit else (170, 170, 190))
        draw_ui(t, s, x + 12, 5, title_col(lit), bold=True)
    elif IS("slack"):
        w = 8 + ui_w(T.pl_title, lit) + 3 + 9
        x = channel_title(t, T.pl_title, 50 - w // 2, 5, lit)
        mention_badge(t, x + 3, 6, 2)
    else:
        s1, s2 = "MONITOR", "TRAFFIC"
        w = text_w(TINY, s1) + 8 + text_w(TINY, s2)
        x = 50 - w // 2
        draw_text(t, TINY, s1, x, 7, (150, 158, 166) if lit else (110, 114, 118))
        draw_text(t, TINY, ">", x + text_w(TINY, s1) + 2, 7, (150, 158, 166) if lit else (110, 114, 118))
        draw_text(t, TINY, s2, x + text_w(TINY, s1) + 8, 7, WHITE if lit else (170, 174, 178))
        rect(t, x + text_w(TINY, s1) + 7, 15, text_w(TINY, s2) + 2, 2,
             T.accent if lit else lerp(T.accent, (80, 80, 80), 0.5))
    return t


def bar_fill(t, lit):
    """What a plain stretch of a 20px titlebar carries: the chassis vents for Palo Alto."""
    if IS("palo-alto"):
        pa_vents(t, 0, t.shape[1] + 3, 5, rows=3, lit=lit)


def rj45(t, x, y, n, lit_link=True, act=False):
    """An RJ45 port 10x8 with its two LEDs above (link green, activity amber)."""
    rect(t, x, y + 3, 10, 8, (8, 8, 9))
    rect(t, x + 1, y + 4, 8, 6, (24, 25, 27))
    rect(t, x + 3, y + 9, 4, 2, (8, 8, 9))
    for k in range(4):
        rect(t, x + 2 + 2 * k, y + 4, 1, 2, (150, 130, 60))
    rect(t, x + 1, y, 3, 2, T.led if lit_link else T.led_off)
    rect(t, x + 6, y, 3, 2, T.amber if act else (52, 40, 20))
    draw_text(t, TINY, str(n), x + 3 - (2 if n > 9 else 0), y + 13, T.label)


def make_pledit():
    a = new(280, 186, T.frame_body)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit)
        bar_fill(t, lit)
        a[y:y + 20, 127:152] = t
        t = bar20(25, lit, left_edge=True)
        if IS("palo-alto"):
            pa_vents(t, 8, 28, 5, rows=3, lit=lit)
        a[y:y + 20, 0:25] = t
        a[y:y + 20, 26:126] = title_piece_pl(lit)
        t = bar20(25, lit, right_edge=True)
        if IS("palo-alto"):
            pa_vents(t, -3, 13, 5, rows=3, lit=lit)
        caption_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    a[42:71, 0:12] = side_tile(12, 29, True, "pl")
    t = side_tile(20, 29, False, "pl")
    rect(t, 5, 0, 8, 29, scroll_groove_col())
    if IS("slack-light"):
        # the white list runs on into a light scrollbar groove, with a hairline after it
        rect(t, 0, 0, 13, 29, scroll_groove_col())
        rect(t, 0, 0, 1, 29, WHITE)
        rect(t, 13, 0, 1, 29, (221, 221, 221))
    a[42:71, 31:51] = t
    cell = bar20(25, True, right_edge=True)[3:12, 14:23].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = cell
    a[53:71, 52:60] = scroll_handle(False)
    a[53:71, 61:69] = scroll_handle(True)

    def bottom_base(w, left=False, right=False):
        t = new(w, 38, T.frame_body)
        if IS("teams"):
            rect(t, 0, 0, w, 1, (224, 224, 224))
        rect(t, 0, 37, w, 1, T.edge)
        if left:
            left_side(t, 0, 37, "pl")
            rect(t, 0, 37, w, 1, T.edge)
        if right:
            right_side(t, 0, 38)
        return t

    t = bottom_base(125, left=True)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        t[8:26, bx:bx + 22] = toggle_cell(t[8:26, bx:bx + 22], 22, 18, lbl, False, False)
    if IS("palo-alto"):
        draw_text(t, TINY, "MGT", 14, 29, T.label)
        rect(t, 28, 30, 3, 2, T.led)
    a[72:110, 0:125] = t

    t = bottom_base(150, right=True)
    field(t, 6, 9, 56, 8)
    gcol = {"teams": T.glyph, "slack": (207, 195, 207), "slack-light": (207, 195, 207),
            "palo-alto": T.glyph}[T.name]
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        mini_transport_icon(t, kind, 3 + 10 * k, 22, gcol)
    field(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, T.flabel)
    rect(t, 84, 22 + 5, 1, 1, T.flabel)
    t[8:26, 106:128] = toggle_cell(t[8:26, 106:128], 22, 18, "LIST", False, False)
    for k in range(4):
        for j in range(k + 1):
            px(t, 145 - 3 * k + 3 * j, 31 - 3 * j, T.label if not IS("slack") else (150, 120, 150))
    a[72:110, 126:276] = t

    t = bottom_base(25)
    if IS("palo-alto"):
        rj45(t, 1, 6, 1, True, True)
        rj45(t, 13, 6, 2, True, False)
    elif IS("teams"):
        pass
    a[0:38, 179:204] = t
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_bottom(w, grip, left_edge):
    t = new(w, 14, T.frame_body)
    rect(t, 0, 13, w, 1, T.edge)
    if left_edge:
        left_side(t, 0, 13, "gen")
        if IS("teams"):
            # the meeting tile's name tag, muted mic and all
            rbox(t, 14, 2, 72, 10, 2, (230, 230, 230))
            icon(t, IC["mic"], 17, 3, (97, 97, 97))
            paint(t, 0, 0, line_mask(w, 14, [(16.5, 3.5), (22.5, 10.5)], 1.0), T.red)
            draw_text(t, TINY, "NOW PLAYING", 26, 4, (36, 36, 36))
        elif IS("slack"):
            draw_text(t, TINY, "HUDDLE", 15, 5, (207, 195, 207))
            rbox(t, 42, 4, 9, 7, 3.49, T.green)
            draw_text(t, TINY, "LIVE", 54, 5, (46, 182, 125))
        else:
            draw_text(t, TINY, "HA", 14, 5, T.label)
            rect(t, 23, 6, 3, 2, T.amber)
            draw_text(t, TINY, "ACTIVE", 30, 5, T.label)
    else:
        right_side(t, 0, 14)
    if grip:
        for k in range(3):
            for j in range(k + 1):
                px(t, w - 4 - 3 * k + 3 * j, 9 - 3 * j, T.label if not IS("slack") else (150, 120, 150))
    return t


def make_gen():
    a = new(194, 109, T.frame_body)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, t):
            a[y:y + 20, px0:px0 + 25] = t

        t = bar20(25, lit, left_edge=True)
        if IS("palo-alto"):
            pa_vents(t, 8, 28, 5, rows=3, lit=lit)
        piece(0, t)
        t = bar20(25, lit)
        bar_fill(t, lit)
        if IS("palo-alto"):
            t[1:19, 17:25] = bar_frame(8, 20, lit)[1:19, 0:1]
        piece(26, t)
        piece(52, bar20(25, lit))
        t = bar20(25, lit)
        bar_fill(t, lit)
        if IS("palo-alto"):
            t[1:19, 0:8] = bar_frame(8, 20, lit)[1:19, 0:1]
        piece(78, t)
        t = bar20(25, lit)
        bar_fill(t, lit)
        piece(104, t)
        t = bar20(25, lit, right_edge=True)
        if IS("palo-alto"):
            pa_vents(t, -3, 13, 5, rows=3, lit=lit)
        caption_button(t, 14, 3, "close", lit)
        piece(130, t)

    a[42:56, 0:125] = gen_bottom(125, False, True)
    a[57:71, 0:125] = gen_bottom(125, True, False)
    t = new(25, 14, T.frame_body)
    rect(t, 0, 13, 25, 1, T.edge)
    a[72:86, 127:152] = t
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = side_tile(w, h, left, "gen")
    cell = bar20(25, True, right_edge=True)[3:12, 14:23].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = cell

    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        centre = a[(0 if lit else 21) + 4:(0 if lit else 21) + 11, 60]
        col = title_col(lit)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            for r in range(7):
                a[y + r, x:x + w] = centre[r]
            draw_text(a, FONT5, c, x, y + 1, col)
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp, viscolor.txt, pledit.txt, readme.txt
# ------------------------------------------------------------------------------------------


def genex_colours():
    return {
        "teams": [WHITE, (36, 36, 36), (245, 245, 245), (36, 36, 36), (36, 36, 36), (224, 224, 224),
                  (232, 235, 250), (250, 250, 250), (97, 97, 97), WHITE, (209, 209, 209), (91, 95, 199),
                  (245, 245, 245), (224, 224, 224), (189, 189, 189), (200, 200, 200), (91, 95, 199),
                  (245, 245, 245)],
        "slack": [WHITE, (29, 28, 29), (248, 248, 248), (29, 28, 29), (29, 28, 29), (221, 221, 221),
                  (232, 245, 250), (248, 248, 248), (97, 96, 97), WHITE, (221, 221, 221), (18, 100, 163),
                  (248, 248, 248), (240, 239, 240), (63, 14, 64), (221, 221, 221), (18, 100, 163),
                  (248, 248, 248)],
        "slack-light": [WHITE, (29, 28, 29), WHITE, (29, 28, 29), (29, 28, 29), (221, 221, 221),
                        (232, 245, 250), (248, 248, 248), (97, 96, 97), WHITE, (221, 221, 221), (18, 100, 163),
                        WHITE, (248, 248, 248), (187, 186, 187), (221, 221, 221), (97, 96, 97),
                        (248, 248, 248)],
        "palo-alto": [WHITE, (51, 51, 51), (33, 35, 38), (236, 239, 242), (236, 239, 242), (58, 61, 65),
                      (216, 230, 243), (238, 241, 244), (51, 51, 51), WHITE, (150, 160, 170), (250, 88, 45),
                      (33, 35, 38), (54, 57, 61), (130, 136, 142), (38, 40, 43), (250, 88, 45), (20, 21, 23)],
    }[T.name]


def make_genex():
    a = new(256, 64, T.frame_body)
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    a[1:16, 0:47] = toggle_cell(new(47, 15, T.frame_body), 47, 15, "", False, False)
    a[16:31, 0:47] = toggle_cell(new(47, 15, T.frame_body), 47, 15, "", False, True)
    return a


def viscolor():
    cols = [(T.disp, "background"), (T.vis_dots, "dots")]
    for i in range(16):
        cols.append((ramp(T.vis_bars, i / 15), f"spectrum {i + 1}" + (" (top)" if i == 0 else "")))
    for i, c in enumerate(T.vis_osc):
        cols.append((c, f"oscilloscope {i + 1}"))
    cols.append((T.vis_peak, "peaks"))
    return cols


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    p = T.pledit
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={p['Normal']}\nCurrent={p['Current']}\nNormalBG={p['NormalBG']}\n"
                f"SelectedBG={p['SelectedBG']}\nMbBG={p['NormalBG']}\nMbFG={p['Normal']}\nFont=Arial\n")
    title = T.wsz[:-4].replace("-", " ")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(f"{title} - a personal skin in the style of {T.subject}.\n"
                f"{T.logo_owner} logo (c) {T.logo_owner}; private use only.\n\n"
                "A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py),\n"
                "except the logo.\n")


# ------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------

SHEETS = {}


def build():
    main = make_main()
    sheets = {
        "main.bmp": main,
        "titlebar.bmp": make_titlebar(main),
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
    """The app's title colour: text.bmp's commonest colour other than its background."""
    arr = np.asarray(SHEETS["text"]).reshape(-1, 3)
    bg = tuple(arr[0])
    cols, counts = np.unique(arr, axis=0, return_counts=True)
    order = [tuple(int(v) for v in cols[i]) for i in np.argsort(-counts)]
    return next(c for c in order if c != bg)


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
    ImageDraw.Draw(box).text((0, 3 + 2 + 2), state["title"], fill=text_ink(), font=tt_font(11), anchor="lm")
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
    c0, c1 = np.array(T.gen_bg[0], np.float32), np.array(T.gen_bg[1], np.float32)
    col = c0 + (c1 - c0) * arr[..., :1]
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


PREVIEW_TITLE = {"teams": "Weekly sync (can everyone hear me?)", "slack": "Sounds good, let me circle back",
                 "slack-light": "Per my last message",
                 "palo-alto": "Commit successful - 3 warnings"}
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
             title=PREVIEW_TITLE[T.name], bars=bars)
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
    if sys.argv[1:] == ["--list"]:
        for k, v in THEMES.items():
            print(f"{k:12s} {v.wsz}")
        sys.exit(0)
    for theme in (sys.argv[1:] or list(THEMES)):
        use_theme(theme)
        names = build()
        preview()
        print(f"{T.wsz}: {', '.join(n for n in names)}")
