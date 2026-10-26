#!/usr/bin/python3
"""Chrome, Firefox and Discord: classic Winamp 2.x skins in the style of three apps.

One procedural generator, a theme each (based on skins/ember/gen_skin.py, which it keeps the sheet
layouts of). Everything is drawn here from code (gradients, anti-aliased shapes, hand-made pixel
fonts), except one logo per skin (the app's era-matching mark in the About spot), loaded from
source/ at generation time. Private use only.

    /usr/bin/python3 -I gen_skin.py [chrome|firefox|discord ...]   (no argument builds all three)

Per theme: the bitmaps and text files in out/<theme>/, zipped flat into <App>.wsz beside this
file, and preview-<theme>.png (the windows assembled from the sprites the way the app does, 2x).
"""

import os
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


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    # Chrome 1-10 (2008-2011) on Windows: the light blue frame with trapezoid tabs, the pale
    # toolbar, the white omnibox, flat grey glyph buttons and the wrench menu.
    "chrome": SimpleNamespace(
        name="chrome", kind="chrome", app="Chrome", company="Google LLC", wsz="Chrome.wsz",
        frame_lit=[(203, 219, 239), (184, 202, 227), (166, 186, 214)],
        frame_dim=[(229, 235, 243), (219, 227, 237), (208, 218, 231)],
        frame_edge_lit=(112, 134, 168), frame_edge_dim=(168, 180, 198),
        tab_style="trapezoid", tab_edge_lit=(120, 138, 168), tab_edge_dim=(162, 174, 192),
        tab_top=(255, 255, 255), tab_top_dim=(246, 248, 251),
        body_top=(240, 244, 250), body_bot=(222, 229, 239), frame_body=(232, 237, 245),
        edge_hi=(255, 255, 255), edge_lo=(150, 166, 190),
        disp=(255, 255, 255), disp_edge=(160, 174, 194), disp_r=2.5,
        txt=(34, 34, 34), txt_dim=(206, 211, 218), label=(120, 128, 140),
        digit=(60, 64, 67), digit_ghost=None,
        accent=(26, 115, 232), accent_hi=(66, 145, 245), accent_lt=(210, 227, 252),
        glyph=(84, 92, 106), glyph_on=(26, 115, 232),
        btn=[(255, 255, 255), (238, 240, 243), (226, 229, 234)], btn_edge=(170, 180, 196),
        btn_down=[(214, 220, 229), (226, 231, 238)], btn_on=[(234, 243, 254), (210, 227, 252)],
        track=(214, 221, 231), track_edge=(168, 180, 198),
        knob=[(255, 255, 255), (228, 232, 238)], knob_edge=(128, 144, 168),
        knob_down=[(232, 241, 254), (196, 218, 250)], knob_edge_down=(26, 115, 232),
        title_lit=(30, 30, 30), title_dim=(112, 120, 132),
        caption="flat",
        pledit=dict(Normal="#000000", Current="#1A73E8", NormalBG="#FFFFFF", SelectedBG="#D2E3FC"),
        vis_bars=[(26, 115, 232), (66, 145, 245), (138, 186, 250)], vis_dots=(240, 243, 248),
        vis_peak=(32, 33, 36), vis_osc=[(26, 115, 232), (52, 132, 238), (90, 156, 242), (130, 180, 246),
                                         (170, 204, 250)],
        main_title="New Tab", eq_title="Equalizer", pl_title="Playlist",
        logo=os.path.join(SRC, "logo-chrome", "icon-2011.png"),
        logo_url="https://commons.wikimedia.org/wiki/File:Google_Chrome_icon_(2011).png",
    ),
    # Firefox 4 (2011) on Windows 7: Aero glass frame, the orange Firefox menu button, rounded
    # tabs on top, the pale blue toolbar, the white awesomebar and the round "keyhole" button.
    "firefox": SimpleNamespace(
        name="firefox", kind="firefox", app="Firefox", company="the Mozilla Foundation", wsz="Firefox.wsz",
        frame_lit=[(196, 216, 240), (172, 198, 232), (152, 182, 222)],
        frame_dim=[(222, 228, 236), (212, 219, 229), (202, 210, 222)],
        frame_edge_lit=(84, 108, 148), frame_edge_dim=(150, 160, 178),
        tab_style="round", tab_edge_lit=(110, 132, 168), tab_edge_dim=(160, 170, 186),
        tab_top=(252, 253, 255), tab_top_dim=(240, 243, 247),
        body_top=(236, 242, 250), body_bot=(212, 224, 240), frame_body=(226, 234, 245),
        edge_hi=(255, 255, 255), edge_lo=(120, 142, 176),
        disp=(255, 255, 255), disp_edge=(138, 160, 194), disp_r=3.5,
        txt=(0, 0, 0), txt_dim=(206, 212, 222), label=(110, 122, 142),
        digit=(34, 44, 60), digit_ghost=None,
        accent=(230, 96, 0), accent_hi=(255, 149, 0), accent_lt=(255, 225, 196),
        glyph=(50, 66, 92), glyph_on=(214, 88, 0),
        btn=[(253, 254, 255), (236, 242, 250), (214, 225, 240)], btn_edge=(122, 142, 174),
        btn_down=[(190, 206, 228), (214, 226, 242)], btn_on=[(255, 246, 236), (255, 222, 190)],
        track=(206, 216, 230), track_edge=(128, 148, 180),
        knob=[(253, 254, 255), (214, 225, 240)], knob_edge=(100, 122, 158),
        knob_down=[(255, 236, 214), (255, 196, 140)], knob_edge_down=(200, 90, 10),
        title_lit=(16, 24, 40), title_dim=(104, 112, 126),
        caption="aero",
        app_btn=[(255, 170, 60), (255, 149, 0), (230, 96, 0)], app_btn_edge=(166, 68, 0),
        app_btn_dim=[(240, 176, 110), (226, 150, 80), (204, 112, 44)], app_btn_edge_dim=(150, 96, 52),
        pledit=dict(Normal="#000000", Current="#E66000", NormalBG="#FFFFFF", SelectedBG="#FFE1C4"),
        vis_bars=[(230, 96, 0), (255, 149, 0), (255, 196, 90)], vis_dots=(242, 245, 250),
        vis_peak=(40, 52, 80), vis_osc=[(230, 96, 0), (240, 120, 20), (250, 146, 40), (255, 172, 80),
                                         (255, 200, 130)],
        main_title="Now Playing", eq_title="Equalizer", pl_title="Playlist",
        logo=os.path.join(SRC, "logo-firefox", "firefox-3.5-logo.png"),
        logo_url="https://commons.wikimedia.org/wiki/File:Mozilla_Firefox_3.5_logo.png",
    ),
    # Discord today: the dark greys, blurple, round "server icon" buttons that turn into rounded
    # squares when pressed, green/red status colours, channel-name titles.
    "discord": SimpleNamespace(
        name="discord", kind="discord", app="Discord", company="Discord Inc.", wsz="Discord.wsz",
        frame_lit=[(30, 31, 34), (30, 31, 34)], frame_dim=[(30, 31, 34), (30, 31, 34)],
        frame_edge_lit=(30, 31, 34), frame_edge_dim=(30, 31, 34),
        tab_style=None,
        body_top=(49, 51, 56), body_bot=(49, 51, 56), frame_body=(43, 45, 49),
        edge_hi=(58, 60, 66), edge_lo=(24, 25, 28),
        disp=(56, 58, 64), disp_edge=None, disp_r=4,
        txt=(219, 222, 225), txt_dim=(84, 88, 96), label=(148, 155, 164),
        digit=(242, 243, 245), digit_ghost=None,
        accent=(88, 101, 242), accent_hi=(124, 135, 250), accent_lt=(64, 66, 73),
        green=(35, 165, 90), red=(242, 63, 67), grey=(128, 132, 142),
        glyph=(219, 222, 225), glyph_on=(255, 255, 255),
        btn=[(64, 66, 73), (64, 66, 73)], btn_edge=None,
        btn_down=[(54, 56, 62), (54, 56, 62)], btn_on=[(35, 165, 90), (35, 165, 90)],
        track=(78, 80, 88), track_edge=None,
        knob=[(255, 255, 255), (235, 236, 238)], knob_edge=(200, 202, 206),
        knob_down=[(242, 243, 245), (220, 222, 226)], knob_edge_down=(88, 101, 242),
        title_lit=(242, 243, 245), title_dim=(128, 132, 142), title_hash=(128, 132, 142),
        caption="flat_dark",
        pledit=dict(Normal="#DBDEE1", Current="#FFFFFF", NormalBG="#313338", SelectedBG="#404249"),
        vis_bars=[(124, 135, 250), (88, 101, 242), (71, 82, 196)], vis_dots=(62, 64, 71),
        vis_peak=(242, 243, 245), vis_osc=[(124, 135, 250), (106, 118, 246), (88, 101, 242), (71, 82, 196),
                                            (60, 69, 160)],
        main_title="now-playing", eq_title="equalizer", pl_title="playlist",
        logo=os.path.join(SRC, "logo-discord", "discord-clyde.svg"),
        logo_url="https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/discord.svg "
                 "(Simple Icons, the Discord symbol from Discord's brand kit)",
    ),
}


# Classic Chrome's saturated blue frame (Windows Vista/7 basic and XP, non-glass): the same tabs,
# omnibox and logo as "chrome", in a bright blue window with a thick frame round every window.
THEMES["chrome-blue"] = SimpleNamespace(**dict(
    vars(THEMES["chrome"]),
    name="chrome-blue", wsz="Chrome-Classic-Blue.wsz",
    subject="classic Chrome's blue window frame", logo_owner="Google",
    frame_lit=[(96, 148, 218), (78, 128, 202), (58, 108, 184), (47, 94, 168)],
    frame_dim=[(170, 194, 226), (156, 182, 218), (142, 170, 210)],
    frame_edge_lit=(22, 50, 100), frame_edge_dim=(98, 122, 160),
    tab_edge_lit=(30, 62, 118), tab_edge_dim=(104, 128, 166),
    tab_top=(255, 255, 255), tab_top_dim=(240, 244, 250),
    body_top=(242, 246, 252), body_bot=(222, 230, 242), frame_body=(234, 239, 247),
    edge_lo=(58, 108, 184),
    cap_ink=((255, 255, 255), (236, 242, 250)),
    border=3,
))


# Netscape Communicator 4.8 (2002, the last 4.x) on Windows 9x: grey bevels, navy captions, the
# Navigation Toolbar's coloured icons with labels, Location field, the N throbber, a status bar.
THEMES["netscape"] = SimpleNamespace(
    name="netscape", kind="netscape", app="Netscape", company="Netscape Communications",
    wsz="Netscape-4.8.wsz", subject="Netscape Communicator 4.8 (Navigator 4.x)",
    logo_owner="Netscape Communications (AOL)",
    frame_lit=[(0, 0, 128), (0, 0, 128)], frame_dim=[(128, 128, 128), (128, 128, 128)],
    frame_edge_lit=BLACK, frame_edge_dim=BLACK, tab_style=None,
    body_top=(192, 192, 192), body_bot=(192, 192, 192), frame_body=(192, 192, 192),
    edge_hi=WHITE, edge_lo=(128, 128, 128),
    disp=WHITE, disp_edge=(128, 128, 128), disp_r=0,
    txt=BLACK, txt_dim=(192, 192, 192), label=(64, 64, 64),
    digit=BLACK, digit_ghost=None,
    accent=(0, 0, 128), accent_hi=(0, 0, 255), accent_lt=(204, 204, 255),
    glyph=BLACK, glyph_on=(0, 0, 128),
    btn=[(192, 192, 192), (192, 192, 192)], btn_edge=BLACK,
    btn_down=[(192, 192, 192), (192, 192, 192)], btn_on=[(223, 223, 223), (223, 223, 223)],
    track=WHITE, track_edge=(128, 128, 128),
    knob=[(192, 192, 192)] * 2, knob_edge=BLACK, knob_down=[(223, 223, 223)] * 2, knob_edge_down=BLACK,
    title_lit=WHITE, title_dim=(192, 192, 192),
    caption="win9x",
    pledit=dict(Normal="#000000", Current="#0000EE", NormalBG="#FFFFFF", SelectedBG="#CCCCFF"),
    vis_bars=[(0, 0, 128), (0, 0, 255), (96, 160, 255)], vis_dots=(224, 224, 224),
    vis_peak=BLACK, vis_osc=[(0, 0, 128), (0, 0, 192), (0, 0, 255), (64, 128, 255), (128, 176, 255)],
    main_title="Now Playing - Netscape", eq_title="Equalizer", pl_title="Playlist",
    logo=os.path.join(SRC, "logo-netscape", "Netscape_icon.svg"),
    logo_url="https://commons.wikimedia.org/wiki/File:Netscape_icon.svg",
)


def use_theme(name):
    global T, OUT
    T = THEMES[name]
    OUT = os.path.join(OUT_ROOT, name)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT_ROOT, "scratch"), exist_ok=True)


def logo_png(px_h):
    """The theme's logo as a PNG path, rasterised from SVG into out/scratch when needed."""
    if T.logo.endswith(".svg"):
        out = os.path.join(OUT_ROOT, "scratch", f"logo-{T.name}-{px_h}.png")
        if not os.path.exists(out):
            os.system(f"/usr/bin/rsvg-convert -h {px_h} '{T.logo}' -o '{out}'")
        return out
    return T.logo


# ------------------------------------------------------------------------------------------
# Frame pieces: titlebar backgrounds, tabs, caption buttons
# ------------------------------------------------------------------------------------------


def frame_stops(lit):
    return T.frame_lit if lit else T.frame_dim


def frame_bg(a, x, y, w, h, lit):
    vfill(a, x, y, w, h, frame_stops(lit))
    if T.kind == "firefox":
        # faint diagonal glass streaks (period 37 px, so 25 px tiles don't need to line up exactly)
        for yy in range(h):
            for xx in range(w):
                u = (xx + x + 2 * (yy + y)) % 37
                if u < 5:
                    c = a[y + yy, x + xx]
                    a[y + yy, x + xx] = np.minimum(255, c + (6 if lit else 3))


def tab(a, x, y, w, h, lit, slant=4):
    """A tab joined to what's below it (open at the bottom), from x to x + w, rows y..y + h - 1."""
    edge = T.tab_edge_lit if lit else T.tab_edge_dim
    top = T.tab_top if lit else T.tab_top_dim
    fill = [top, T.body_top] if T.kind != "discord" else [top, top]
    H, W = a.shape[0], a.shape[1]
    if T.tab_style == "trapezoid":
        outer = poly_mask(W, H, [(x, y + h + 0.01), (x + slant - 0.6, y), (x + w - slant + 0.6, y),
                                 (x + w, y + h + 0.01)])
        inner = poly_mask(W, H, [(x + 1.2, y + h + 1), (x + slant - 0.1, y + 1), (x + w - slant + 0.1, y + 1),
                                 (x + w - 1.2, y + h + 1)])
    else:  # rounded top corners
        outer = rr_mask(W, H, 3.5, x, y, w, h + 6)
        inner = rr_mask(W, H, 2.5, x + 1, y + 1, w - 2, h + 6)
    paint(a, 0, 0, outer, edge)
    g = np.zeros((H, W, 3), dtype=np.float32)
    g[y:y + h, :, :] = vgrad(h, fill, W)
    g[:y] = top
    g[y + h:] = fill[-1]
    paint(a, 0, 0, inner, g)
    return (fill, y, h)


def tab_colour_at(row, lit, y, h):
    top = T.tab_top if lit else T.tab_top_dim
    return ramp([top, T.body_top], (row - y + 0.5) / h)


def caption_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: options (the menu), minimize, shade, close."""
    if T.kind == "netscape":
        return ns_caption_button(a, x, y, kind, lit, pressed)
    W, H = a.shape[1], a.shape[0]
    style = T.caption
    if kind == "options":
        if T.kind == "chrome":
            if pressed:
                rbox(a, x, y, 9, 9, 2, [(150, 170, 200), (170, 188, 214)], (104, 124, 156))
            cap = getattr(T, "cap_ink", ((60, 72, 92), (120, 130, 146)))
            ink = ((60, 72, 92) if pressed else cap[0]) if lit else cap[1]
            # the wrench: a jaw ring at the top right, a handle down to the bottom left
            paint(a, 0, 0, ellipse_mask(W, H, x + 3.6, y + 0.8, 4.8, 4.8), ink)
            paint(a, 0, 0, ellipse_mask(W, H, x + 4.9, y + 0.0, 2.6, 2.9),
                  [(150, 170, 200), (170, 188, 214)][0] if pressed else frame_colour_at(y + 1, lit), 1.0)
            paint(a, 0, 0, line_mask(W, H, [(x + 1.6, y + 7.4), (x + 5.2, y + 3.8)], 1.9), ink)
            return
        if T.kind == "firefox":
            # the dropmarker inside the orange menu button (the button itself is drawn by the bar)
            stops = T.app_btn if lit else T.app_btn_dim
            if pressed:
                rect(a, x, y, 9, 9, lerp(stops[-1], BLACK, 0.18))
            else:
                vfill(a, x, y, 9, 9, [ramp(stops, (y + 0.5) / 12), ramp(stops, (y + 8.5) / 12)])
            ink = WHITE
            o = 1 if pressed else 0
            paint(a, 0, 0, poly_mask(W, H, [(x + 1.5, y + 3 + o), (x + 7.5, y + 3 + o), (x + 4.5, y + 6.5 + o)]), ink)
            return
        # discord: a rounded-square menu button with three dots
        if pressed:
            rbox(a, x, y, 9, 9, 2.5, T.accent)
        ink = (WHITE if pressed else ((181, 186, 193) if lit else (110, 114, 122)))
        for dx in (1.6, 4.0, 6.4):
            paint(a, 0, 0, ellipse_mask(W, H, x + dx - 0.2, y + 3.4, 1.8, 1.8), ink)
        return

    if style == "aero":
        # Windows 7 caption buttons: glassy, the close one red
        if kind == "close":
            top, bot = ((232, 150, 140), (196, 64, 50)) if lit else ((224, 196, 194), (196, 160, 158))
            if pressed:
                top, bot = (170, 50, 36), (214, 100, 84)
        else:
            top, bot = ((236, 244, 252), (176, 200, 230)) if lit else ((236, 239, 243), (210, 216, 225))
            if pressed:
                top, bot = (150, 178, 214), (196, 214, 236)
        rbox(a, x, y, 9, 9, 2, [top, lerp(top, bot, 0.45), bot],
             (60, 80, 112) if lit else (140, 150, 166))
        ink = WHITE
        sh = (40, 56, 84) if kind != "close" else (110, 30, 20)
    elif style == "flat":
        if pressed:
            if kind == "close":
                rbox(a, x, y, 9, 9, 2, [(224, 84, 70), (196, 56, 44)], (150, 40, 30))
            else:
                rbox(a, x, y, 9, 9, 2, [(150, 170, 200), (170, 188, 214)], (104, 124, 156))
        cap = getattr(T, "cap_ink", ((64, 76, 98), (124, 134, 150)))
        ink = WHITE if (pressed and kind == "close") else (cap[0] if lit else cap[1])
        sh = None
    else:  # flat_dark
        if pressed:
            rbox(a, x, y, 9, 9, 1.5, T.red if kind == "close" else (64, 66, 73))
        ink = WHITE if pressed else ((181, 186, 193) if lit else (110, 114, 122))
        sh = None

    def g(fn):
        if sh is not None:
            fn(0.0, 0.7, sh)
        fn(0, 0, ink)

    if kind == "minimize":
        g(lambda dx, dy, c: rect(a, x + 2, y + 5 + round(dy), 5, 1 + (1 if style == "aero" else 0), c))
    elif kind == "shade":
        g(lambda dx, dy, c: (rect(a, x + 2, y + 2 + round(dy), 5, 1, c), rect(a, x + 2, y + 2 + round(dy), 1, 5, c),
                             rect(a, x + 6, y + 2 + round(dy), 1, 5, c), rect(a, x + 2, y + 6 + round(dy), 5, 1, c),
                             rect(a, x + 2, y + 3 + round(dy), 5, 1, c)))
    elif kind == "close":
        def cross(dx, dy, c):
            paint(a, 0, 0, line_mask(W, H, [(x + 2.2, y + 2.2 + dy), (x + 6.8, y + 6.8 + dy)], 1.4), c)
            paint(a, 0, 0, line_mask(W, H, [(x + 6.8, y + 2.2 + dy), (x + 2.2, y + 6.8 + dy)], 1.4), c)
        g(cross)


def frame_colour_at(row, lit, h=14):
    return ramp(frame_stops(lit), (row + 0.5) / h)


def title_text(a, s, x, y, lit, on_tab=True):
    """Titlebar text in the UI font (Discord: a channel name, its # in grey)."""
    if T.kind == "netscape":
        return ns_title(a, s, x, y, lit)
    if T.kind == "discord":
        col = T.title_lit if lit else T.title_dim
        if s.startswith("#"):
            x = draw_text(a, UI, "#", x, y, T.title_hash)
            s = s[1:]
        draw_text(a, UI, s, x, y, col)
        return
    col = T.title_lit if lit else T.title_dim
    draw_text(a, UI, s, x, y, col)


def new_tab_button(a, x, y, lit):
    """The small "new tab" button after the tabs."""
    W, H = a.shape[1], a.shape[0]
    edge = T.tab_edge_lit if lit else T.tab_edge_dim
    fill = lerp(T.tab_top if lit else T.tab_top_dim, frame_colour_at(y + 3, lit), 0.55)
    if T.tab_style == "trapezoid":
        # Chrome's slanted little button
        paint(a, 0, 0, poly_mask(W, H, [(x, y + 7), (x + 3, y), (x + 15, y), (x + 12, y + 7)]), edge)
        paint(a, 0, 0, poly_mask(W, H, [(x + 1.6, y + 6), (x + 3.8, y + 1), (x + 13.4, y + 1), (x + 11.2, y + 6)]),
              fill)
    else:
        rbox(a, x, y, 13, 8, 2.5, fill, edge)
        cx = x + 6
        rect(a, cx, y + 2, 1, 4, edge)
        rect(a, cx - 2, y + 4, 5, 1, edge)


def bar_frame(w, h, lit, left_edge=False, right_edge=False):
    """A titlebar strip: the frame gradient, a top highlight and side borders."""
    if T.kind == "netscape":
        return ns_bar_frame(w, h, lit, left_edge, right_edge)
    a = new(w, h)
    frame_bg(a, 0, 0, w, h, lit)
    edge = T.frame_edge_lit if lit else T.frame_edge_dim
    if T.kind != "discord":
        rect(a, 0, 0, w, 1, edge)
        rect(a, 0, 1, w, 1, lerp(frame_colour_at(1, lit, h), WHITE, 0.45))
        if left_edge:
            rect(a, 0, 0, 1, h, edge)
            rect(a, 1, 1, 1, h - 1, lerp(frame_colour_at(1, lit, h), WHITE, 0.45))
        if right_edge:
            rect(a, w - 1, 0, 1, h, edge)
    return a


def apply_border(t, left=False, right=False, bottom=False, y0=0):
    """Themes with a thick window frame (T.border px of the frame colour, a dark outer line)."""
    bw = getattr(T, "border", None)
    if not bw:
        return t
    h, w = t.shape[0], t.shape[1]
    col = T.frame_lit[-1]
    inner = lerp(col, BLACK, 0.25)
    if left:
        rect(t, 0, y0, bw, h - y0, col)
        rect(t, bw, y0, 1, h - y0, inner)
        rect(t, 0, y0, 1, h - y0, T.frame_edge_lit)
    if right:
        rect(t, w - bw, y0, bw, h - y0, col)
        rect(t, w - bw - 1, y0, 1, h - y0, inner)
        rect(t, w - 1, y0, 1, h - y0, T.frame_edge_lit)
    if bottom:
        x0 = bw + 1 if left else 0
        x1 = w - bw - 1 if right else w
        rect(t, 0, h - bw, w, bw, col)
        rect(t, x0, h - bw - 1, x1 - x0, 1, inner)
        rect(t, 0, h - 1, w, 1, T.frame_edge_lit)
        if left:
            rect(t, 0, y0, 1, h - y0, T.frame_edge_lit)
        if right:
            rect(t, w - 1, y0, 1, h - y0, T.frame_edge_lit)
    return t


# ------------------------------------------------------------------------------------------
# Fields, buttons, sliders
# ------------------------------------------------------------------------------------------


def field(a, x, y, w, h):
    """A display field (omnibox / awesomebar / message box): the inside is (x, y, w, h)."""
    if T.kind == "netscape":
        return ns_field(a, x, y, w, h)
    if T.disp_edge is not None:
        # a soft outer shadow line on top for the inset look
        rbox(a, x - 1, y - 1, w + 2, h + 2, T.disp_r, T.disp, T.disp_edge)
        rect(a, x + 1, y, w - 2, 1, lerp(T.disp, T.disp_edge, 0.25))
    else:
        rbox(a, x - 1, y - 1, w + 2, h + 2, T.disp_r, T.disp)


def button_face(a, x, y, w, h, pressed, on=False, r=None):
    r = (2.5 if T.kind != "discord" else h / 2 - 0.01) if r is None else r
    if T.kind == "discord":
        stops = T.btn_on if on else T.btn
        if pressed:
            stops = [lerp(c, BLACK, 0.2) for c in stops]
        rbox(a, x, y, w, h, r, stops)
        return
    stops = T.btn_on if on else T.btn
    if pressed:
        stops = T.btn_down if not on else [lerp(c, BLACK, 0.1) for c in T.btn_on]
    rbox(a, x, y, w, h, r, stops, T.btn_edge if not on else lerp(T.btn_edge, T.accent, 0.5))
    if not pressed:
        rect(a, x + 2, y + 1, w - 4, 1, lerp(stops[0], WHITE, 0.6))


def label_on_button(a, x, y, w, h, s, pressed, on):
    o = 1 if pressed else 0
    if T.kind == "discord":
        ink = WHITE if on else ((181, 186, 193) if not pressed else (219, 222, 225))
        text_center(a, TINY, s, x + w // 2 + (w % 2 == 0 and 0), y + (h - 5) // 2 + o, ink)
        return
    ink = T.glyph_on if on else T.glyph
    text_center(a, TINY, s, x + w // 2, y + (h - 5) // 2 + o, ink, shadow=None if pressed else WHITE, sh=(0, 1))


def track_h(a, x, y, w, th, fill_from=None, fill_to=None, colour=None):
    """A horizontal rounded groove th tall; accent fill between fill_from..fill_to (absolute x)."""
    if T.kind == "netscape":
        return ns_track_h(a, x, y, w, th, fill_from, fill_to, colour)
    W, H = a.shape[1], a.shape[0]
    r = th / 2
    if T.track_edge is not None:
        paint(a, 0, 0, rr_mask(W, H, r, x, y, w, th), T.track_edge)
        inner = rr_mask(W, H, max(0, r - 1), x + 1, y + 1, w - 2, th - 2)
    else:
        inner = rr_mask(W, H, r, x, y, w, th)
    paint(a, 0, 0, inner, T.track)
    if fill_from is not None and fill_to is not None and fill_to > fill_from:
        f = inner.copy()
        f[:, :max(0, int(fill_from))] = 0
        f[:, max(0, int(fill_to)):] = 0
        col = colour or T.accent
        g = vgrad(H, [lerp(col, WHITE, 0.2), col, lerp(col, BLACK, 0.08)], W) if T.kind != "discord" else col
        paint(a, 0, 0, f, g)


def track_v(a, x, y, h, tw, fill_from=None):
    """A vertical groove tw wide from row y; accent fill from row fill_from to the bottom."""
    if T.kind == "netscape":
        return ns_track_v(a, x, y, h, tw, fill_from)
    W, H = a.shape[1], a.shape[0]
    r = tw / 2
    if T.track_edge is not None:
        paint(a, 0, 0, rr_mask(W, H, r, x, y, tw, h), T.track_edge)
        inner = rr_mask(W, H, max(0, r - 1), x + 1, y + 1, tw - 2, h - 2)
    else:
        inner = rr_mask(W, H, r, x, y, tw, h)
    paint(a, 0, 0, inner, T.track)
    if fill_from is not None:
        f = inner.copy()
        f[:int(fill_from), :] = 0
        paint(a, 0, 0, f, T.accent)


def knob(a, x, y, w, h, pressed, r=None):
    if T.kind == "netscape":
        return ns_knob(a, x, y, w, h, pressed, r)
    stops = T.knob_down if pressed else T.knob
    edge = T.knob_edge_down if pressed else T.knob_edge
    r = min(w, h) / 2 - 0.01 if r is None else r
    if T.kind == "discord":
        paint(a, x, y + 1, rr_mask(w, h, r), BLACK, 0.25)
    rbox(a, x, y, w, h, r, stops, edge)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters, bg):
    if T.kind == "netscape":
        return ns_clutter_bar(lit_letters, bg)
    a = new(8, 43, bg)
    if T.kind == "discord":
        rbox(a, 0, 0, 8, 43, 3.5, (30, 31, 34))
    else:
        rbox(a, 0, 0, 8, 43, 2.5, T.btn[:2], T.btn_edge)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rbox(a, 1, y, 6, h, 1.5, T.accent if T.kind == "discord" else T.accent_lt)
        gy = y + (h - 5) // 2
        if T.kind == "discord":
            ink = WHITE if on else (148, 155, 164)
        else:
            ink = T.glyph_on if on else T.label
        draw_text(a, TINY, letter, 2, gy, ink)
    return a


def main_titlebar(lit):
    a = bar_frame(275, 14, lit, left_edge=True, right_edge=True)
    if T.kind == "chrome":
        tab(a, 18, 2, 92, 12, lit, slant=6)
        title_text(a, T.main_title, 30, 4, lit)
        new_tab_button(a, 106, 5, lit)
    elif T.kind == "firefox":
        # the orange Firefox menu button, hanging from the top edge
        stops = T.app_btn if lit else T.app_btn_dim
        edge = T.app_btn_edge if lit else T.app_btn_edge_dim
        rbox(a, 4, -4, 56, 17, 3.5, [stops[0], stops[1], stops[2]], edge)
        rect(a, 5, 0, 54, 1, lerp(stops[0], WHITE, 0.35))
        draw_text(a, UI, "Firefox", 19, 2, WHITE, shadow=lerp(stops[2], BLACK, 0.35), sh=(0, 1))
        tab(a, 66, 2, 90, 12, lit)
        title_text(a, T.main_title, 76, 4, lit)
        new_tab_button(a, 159, 4, lit)
    elif T.kind == "netscape":
        title_text(a, T.main_title, 18, 4, lit)
    else:
        title_text(a, "# " + T.main_title, 20, 2, lit)
    caption_button(a, 6, 3, "options", lit)
    caption_button(a, 244, 3, "minimize", lit)
    caption_button(a, 254, 3, "shade", lit)
    caption_button(a, 264, 3, "close", lit)
    return a


def make_titlebar(main):
    a = new(344, 87, T.frame_body)
    bar = main_titlebar(True)
    for kind, x in (("options", 0), ("minimize", 9), ("close", 18)):
        src = {"options": 6, "minimize": 244, "close": 264}[kind]
        a[0:9, x:x + 9] = bar[3:12, src:src + 9]
        a[9:18, x:x + 9] = bar_cell_pressed(kind, src)
    a[18:27, 0:9] = main_titlebar(True)[3:12, 254:263]
    a[18:27, 9:18] = bar_cell_pressed("shade", 254)
    a[0:14, 27:302] = main_titlebar(True)
    a[15:29, 27:302] = main_titlebar(False)
    a[29:43, 27:302] = main_titlebar(True)
    a[42:56, 27:302] = main_titlebar(False)
    unlit = clutter_bar("", main[30, 9])
    lit = clutter_bar("OAIDV", main[30, 9])
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = lit[y:y + h]
    return a


def bar_cell_pressed(kind, src):
    """The 9x9 pressed button, over the bar it sits on (Firefox's menu button: over the orange)."""
    if T.kind == "firefox" and kind == "options":
        cell = main_titlebar(True)[3:12, src:src + 9].copy()
    else:
        cell = bar_frame(275, 14, True, left_edge=True, right_edge=True)[3:12, src:src + 9].copy()
    caption_button(cell, 0, 0, kind, True, pressed=True)
    return cell


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116) and the transport tray
# ------------------------------------------------------------------------------------------

TRAY_X, TRAY_Y, TRAY_W, TRAY_H = 16, 88, 142, 18
CB = {"previous": (0, 23), "play": (23, 23), "pause": (46, 23), "stop": (69, 23), "next": (92, 22)}
EJECT = (120, 1, 22, 16)   # within the tray canvas


def body_stops():
    return [T.body_top, T.body_bot]


def main_bg():
    if T.kind == "netscape":
        return ns_main_bg()
    a = new(275, 116)
    vfill(a, 0, 14, 275, 102, body_stops())
    a[0:14] = main_titlebar(True)
    edge = T.frame_edge_lit
    if T.kind == "discord":
        # the server rail down the left, with the selected-server pill
        rect(a, 0, 14, 20, 56, (30, 31, 34))
        rbox(a, -2, 36, 4, 18, 1.5, (242, 243, 245))
        rect(a, 0, 115, 275, 1, T.edge_lo)
    else:
        rect(a, 0, 14, 275, 1, lerp(T.body_top, WHITE, 0.6))
        rect(a, 0, 0, 1, 116, edge)
        rect(a, 274, 0, 1, 116, edge)
        rect(a, 0, 115, 275, 1, edge)
        rect(a, 1, 14, 1, 101, lerp(T.body_top, WHITE, 0.6))
        apply_border(a, True, True, True, y0=14)
    return a


def digit(a, n, x, y, col):
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + 1 + c, y + 1 + r, col)


def tri(a, pts, col, alpha=1.0):
    paint(a, 0, 0, poly_mask(a.shape[1], a.shape[0], pts), col, alpha)


def glyph(a, kind, cx, cy, col, s=1.0):
    """Transport glyphs centred at (cx, cy): Chrome's are the toolbar's arrows and stop cross."""
    W, H = a.shape[1], a.shape[0]
    if T.kind == "chrome" and kind in ("previous", "next"):
        d = -1 if kind == "previous" else 1
        pts = [(cx + 6 * d, cy), (cx + 0.5 * d, cy - 5.5), (cx + 0.5 * d, cy - 2), (cx - 6 * d, cy - 2),
               (cx - 6 * d, cy + 2), (cx + 0.5 * d, cy + 2), (cx + 0.5 * d, cy + 5.5)]
        tri(a, pts, col)
    elif kind == "previous":
        tri(a, [(cx - 4 * s, cy), (cx + 0.5 * s, cy - 4.5 * s), (cx + 0.5 * s, cy + 4.5 * s)], col)
        tri(a, [(cx + 0.5 * s, cy), (cx + 5 * s, cy - 4.5 * s), (cx + 5 * s, cy + 4.5 * s)], col)
        rect(a, int(round(cx - 6 * s)), int(round(cy - 4.5 * s)), max(1, round(1.6 * s)), int(round(9 * s)), col)
    elif kind == "next":
        tri(a, [(cx + 4 * s, cy), (cx - 0.5 * s, cy - 4.5 * s), (cx - 0.5 * s, cy + 4.5 * s)], col)
        tri(a, [(cx - 0.5 * s, cy), (cx - 5 * s, cy - 4.5 * s), (cx - 5 * s, cy + 4.5 * s)], col)
        rect(a, int(round(cx + 4.4 * s)), int(round(cy - 4.5 * s)), max(1, round(1.6 * s)), int(round(9 * s)), col)
    elif kind == "play":
        tri(a, [(cx - 3 * s, cy - 5 * s), (cx + 5 * s, cy), (cx - 3 * s, cy + 5 * s)], col)
    elif kind == "pause":
        paint(a, 0, 0, rr_mask(W, H, 0.6, cx - 4 * s, cy - 4.5 * s, 3 * s, 9 * s), col)
        paint(a, 0, 0, rr_mask(W, H, 0.6, cx + 1 * s, cy - 4.5 * s, 3 * s, 9 * s), col)
    elif kind == "stop":
        if T.kind == "chrome":
            paint(a, 0, 0, line_mask(W, H, [(cx - 4, cy - 4), (cx + 4, cy + 4)], 2.3), col)
            paint(a, 0, 0, line_mask(W, H, [(cx + 4, cy - 4), (cx - 4, cy + 4)], 2.3), col)
        else:
            paint(a, 0, 0, rr_mask(W, H, 1.0, cx - 4 * s, cy - 4 * s, 8 * s, 8 * s), col)
    elif kind == "eject":
        tri(a, [(cx - 5 * s, cy + 1 * s), (cx, cy - 4.5 * s), (cx + 5 * s, cy + 1 * s)], col)
        paint(a, 0, 0, rr_mask(W, H, 0.5, cx - 5 * s, cy + 2.5 * s, 10 * s, 2 * s), col)


def tray(bg, pressed=None):
    """The transport tray (prev..next, eject) on bg (TRAY_W x TRAY_H), one button pressed."""
    if T.kind == "netscape":
        return ns_tray(bg, pressed)
    a = bg.copy()
    W, H = a.shape[1], a.shape[0]
    centres = {k: (x + w / 2, H / 2) for k, (x, w) in CB.items()}
    ex, ey, ew, eh = EJECT
    centres["eject"] = (ex + ew / 2, ey + eh / 2)

    if T.kind == "chrome":
        # flat toolbar buttons: just glyphs; pressed gets the rounded grey "hot" box
        for k, (cx, cy) in centres.items():
            if k == pressed:
                if k == "eject":
                    rbox(a, ex, ey, ew, eh, 3, [(204, 212, 224), (220, 227, 236)], (150, 164, 186))
                else:
                    x, w = CB[k]
                    rbox(a, x, 0, w, H, 3, [(204, 212, 224), (220, 227, 236)], (150, 164, 186))
            col = (34, 40, 52) if k == pressed else T.glyph
            o = 0.5 if k == pressed else 0
            if k != pressed:
                glyph(a, k, cx, cy + 1, WHITE)   # the toolbar's white emboss under each glyph
            glyph(a, k, cx + o, cy + o, col)
        return a

    if T.kind == "firefox":
        # one rounded bar with the round "keyhole" play button in it; eject on its own
        by, bh = 2, 14
        bar_x0, bar_x1 = 1, CB["next"][0] + CB["next"][1] - 1
        rbox(a, bar_x0, by, bar_x1 - bar_x0, bh, 3.5, T.btn, T.btn_edge)
        rect(a, bar_x0 + 3, by + 1, bar_x1 - bar_x0 - 6, 1, WHITE)
        for k in ("previous", "pause", "stop", "next"):
            x, w = CB[k]
            if k == pressed:
                seg = np.zeros((H, W), dtype=np.float32)
                seg[:, x:x + w] = rr_mask(W, H, 2.5, bar_x0 + 1, by + 1, bar_x1 - bar_x0 - 2, bh - 2)[:, x:x + w]
                paint(a, 0, 0, seg, T.btn_down[0])
                seg2 = seg.copy()
                seg2[by + 2:, :] = 0
                paint(a, 0, 0, seg2, lerp(T.btn_down[0], BLACK, 0.15))
        for xdiv in (CB["pause"][0] + CB["pause"][1], CB["stop"][0] + CB["stop"][1]):
            rect(a, xdiv, by + 2, 1, bh - 4, lerp(T.btn_edge, T.btn[1], 0.4))
            rect(a, xdiv + 1, by + 2, 1, bh - 4, WHITE)
        rect(a, CB["previous"][0] + CB["previous"][1] - 1, by + 2, 1, bh - 4, lerp(T.btn_edge, T.btn[1], 0.4))
        # the round button (play), its rim standing out of the bar
        cx, cy = centres["play"]
        R = 9
        paint(a, 0, 0, ellipse_mask(W, H, cx - R, cy - R, 2 * R, 2 * R), T.btn_edge)
        stops = T.btn_down if pressed == "play" else [(255, 255, 255), (232, 240, 250), (200, 216, 238)]
        g = np.zeros((H, W, 3), dtype=np.float32)
        g[:] = vgrad(H, stops, W)
        paint(a, 0, 0, ellipse_mask(W, H, cx - R + 1, cy - R + 1, 2 * R - 2, 2 * R - 2), g)
        if pressed != "play":
            paint(a, 0, 0, ellipse_mask(W, H, cx - R + 3, cy - R + 1.5, 2 * R - 6, R - 1.5), WHITE, 0.6)
        # eject
        if pressed == "eject":
            rbox(a, ex, ey, ew, eh, 3.5, T.btn_down, T.btn_edge)
        else:
            rbox(a, ex, ey, ew, eh, 3.5, T.btn, T.btn_edge)
            rect(a, ex + 3, ey + 1, ew - 6, 1, WHITE)
        for k, (cx, cy) in centres.items():
            o = 1 if k == pressed else 0
            s = 1.15 if k == "play" else 0.85
            glyph(a, k, cx + o * 0.5, cy + 1 + o * 0.5, WHITE, s)
            glyph(a, k, cx + o * 0.5, cy + o * 0.5, T.glyph, s)
        return a

    # discord: round "server icons"; the pressed one becomes a blurple rounded square
    for k, (cx, cy) in centres.items():
        d = 16 if k == "eject" else 18
        x0, y0 = cx - d / 2, cy - d / 2
        if k == pressed:
            paint(a, 0, 0, rr_mask(W, H, 5, x0, y0, d, d), lerp(T.accent, BLACK, 0.1))
            ink = WHITE
        else:
            col = T.accent if k == "play" else (30, 31, 34)
            paint(a, 0, 0, ellipse_mask(W, H, x0, y0, d, d), col)
            ink = WHITE if k == "play" else (219, 222, 225)
        glyph(a, k, cx, cy, ink, 0.78 if k != "eject" else 0.7)
    return a


def make_main():
    a = main_bg()
    bg = a[30, 9]
    # clutterbar
    a[22:65, 10:18] = clutter_bar("", bg)
    # left display: indicator, time, analyzer
    field(a, 21, 20, 84, 42)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, T.digit)
    # right displays: title, then kbps/kHz/mono/stereo
    field(a, 109, 21, 159, 15)
    field(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, T.label)
    draw_text(a, TINY, "KHZ", 169, 44, T.label)
    # volume, balance seats (the sheets' own frames cover them)
    track_h(a, 108, 61, 66, 5)
    track_h(a, 178, 61, 36, 5)
    # seek bar seat
    track_h(a, 16, 74, 248, 6)
    # transport tray
    a[TRAY_Y:TRAY_Y + TRAY_H, TRAY_X:TRAY_X + TRAY_W] = tray(a[TRAY_Y:TRAY_Y + TRAY_H, TRAY_X:TRAY_X + TRAY_W])
    # the logo, once, in the About spot
    if T.kind == "netscape":
        ns_main_extras(a)
    elif T.kind == "discord":
        paint(a, 245, 85, ellipse_mask(22, 22, 0, 0, 22, 22), T.accent)
        logo(a, 249, 89, (14, 14), logo_png(64))
    else:
        logo(a, 245, 86, (21, 21), logo_png(64))
    return a


# ------------------------------------------------------------------------------------------
# cbuttons, shufrep, monoster, playpaus, numbers, text
# ------------------------------------------------------------------------------------------


def make_cbuttons(main):
    a = new(136, 36, T.frame_body)
    # main already carries the unpressed tray; take the cells from fresh renders
    clean = main_bg()[TRAY_Y:TRAY_Y + TRAY_H, TRAY_X:TRAY_X + TRAY_W]
    normal = tray(clean)
    for k, (x, w) in CB.items():
        a[0:18, x:x + w] = normal[:, x:x + w]
        a[18:36, x:x + w] = tray(clean, k)[:, x:x + w]
    ex, ey, ew, eh = EJECT
    a[0:16, 114:136] = normal[ey:ey + eh, ex:ex + ew]
    a[16:32, 114:136] = tray(clean, "eject")[ey:ey + eh, ex:ex + ew]
    return a


def toggle_cell(bg, w, h, label, on, pressed):
    if T.kind == "netscape":
        return ns_toggle_cell(bg, w, h, label, on, pressed)
    a = bg.copy()
    if T.kind == "discord":
        stops = [T.green, T.green] if on else [(64, 66, 73), (64, 66, 73)]
        if pressed:
            stops = [lerp(c, BLACK, 0.2) for c in stops]
        rbox(a, 0, 0, w, h, min(h / 2 - 0.01, 4), stops)
    else:
        button_face(a, 0, 0, w, h, pressed, on)
    label_on_button(a, 0, 0, w, h, label, pressed, on)
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
    on_col = T.accent if T.kind != "discord" else T.green
    for y, on in ((0, True), (12, False)):
        col = on_col if on else T.txt_dim
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T.disp)
    col = T.accent if T.kind != "discord" else T.green
    tri(a, [(2, 1), (8, 4.5), (2, 8)], col)
    rect(a, 9 + 2, 1, 2, 7, col)
    rect(a, 9 + 5, 1, 2, 7, col)
    rect(a, 18 + 2, 2, 5, 5, T.red if T.kind == "discord" else col)
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


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def make_posbar(main):
    a = new(307, 10, T.frame_body)
    a[0:10, 0:248] = main[72:82, 16:264]
    for x0, sel in ((248, False), (278, True)):
        t = main[72:82, 16 + 100:16 + 129].copy()
        # the groove under the thumb: played (accent) left of its centre, the rest plain
        track_h(t, -20, 2, 69, 6, fill_from=0, fill_to=14)
        if T.kind == "discord":
            knob(t, 10, 0, 9, 10, sel, r=3)
        elif T.kind == "chrome":
            knob(t, 8, 0, 13, 10, sel, r=4.99)
        elif T.kind == "netscape":
            knob(t, 0, 0, 29, 10, sel)
        else:
            knob(t, 7, 0, 15, 10, sel, r=3.5)
        a[0:10, x0:x0 + 29] = t
    return a


def slider_thumbs(a, seat):
    for x, sel in ((0, True), (15, False)):
        t = new(14, 11, seat[1, 0])
        t[:, :] = seat[1:12, 20:34]
        track_h(t, -10, 4, 40, 5, fill_from=0, fill_to=7)
        if T.kind == "discord":
            knob(t, 3, 0, 8, 11, sel, r=3)
        else:
            knob(t, 1, 0, 12, 11, sel, r=5.49 if T.kind == "chrome" else 3.5)
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
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = bar_frame(275, 14, lit, left_edge=True, right_edge=True)
    if T.kind == "discord":
        title_text(a, "# " + T.eq_title, 8, 2, lit)
    elif T.kind == "netscape":
        ns_caption_button(a, 6, 3, "options", lit)
        title_text(a, T.eq_title, 18, 4, lit)
    else:
        tab(a, 6, 2, 84, 12, lit, slant=6)
        title_text(a, T.eq_title, 22, 4, lit)
    caption_button(a, 264, 3, "close", lit)
    return a


def eq_frame_bg():
    if T.kind == "netscape":
        return ns_eq_frame_bg()
    a = new(275, 116)
    vfill(a, 0, 14, 275, 102, body_stops())
    if T.kind != "discord":
        edge = T.frame_edge_lit
        rect(a, 0, 0, 1, 116, edge)
        rect(a, 274, 0, 1, 116, edge)
        rect(a, 0, 115, 275, 1, edge)
        rect(a, 1, 14, 1, 101, lerp(T.body_top, WHITE, 0.6))
        rect(a, 0, 14, 275, 1, lerp(T.body_top, WHITE, 0.6))
        apply_border(a, True, True, True, y0=14)
    else:
        rect(a, 0, 115, 275, 1, T.edge_lo)
    return a


def eq_slider_frame(bg, n):
    """14x63: a vertical groove whose accent fill rises with the value (n of 0..27)."""
    a = bg.copy()
    v = n / 27
    centre = round((1 - v) * 51) + 5
    track_v(a, 5, 1, 61, 4 if T.kind != "chrome" else 4, fill_from=centre)
    return a


def eq_thumb(bg, pressed):
    a = bg.copy()
    track_v(a, 4, -20, 60, 4, fill_from=5)
    if T.kind == "discord":
        knob(a, 0, 2, 11, 7, pressed, r=3)
    else:
        knob(a, 0, 0, 11, 11, pressed, r=5.49 if T.kind == "chrome" else 3.5)
    return a


def make_eqmain():
    a = new(275, 315, T.frame_body)
    base = eq_frame_bg()
    a[0:116] = base
    a[0:14] = eq_titlebar(True)
    # graph seat
    field(a, 86, 17, 113, 19)
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, T.label)
    seat = base[38:101, 21:35]
    for x in [21] + [78 + 18 * i for i in range(10)]:
        a[38:101, x:x + 14] = eq_slider_frame(base[38:101, x:x + 14], 14)
    text_center(a, TINY, "PREAMP", 28, 104, T.label)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 104, T.label)
    if T.kind != "discord":
        rect(a, 40, 39, 1, 60, lerp(T.body_top, T.edge_lo, 0.5))
    # ON / AUTO / PRESETS buttons on the window, unpressed and off
    for x, w, lbl in ((14, 26, "ON"), (40, 32, "AUTO")):
        a[18:30, x:x + w] = toggle_cell(base[18:30, x:x + w], w, 12, lbl, False, False)
    a[18:30, 217:261] = toggle_cell(base[18:30, 217:261], 44, 12, "PRESETS", False, False)

    # under the window
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
    # graph
    rect(a, 0, 294, 113, 19, T.disp)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, T.vis_dots)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, lerp(T.disp, T.label, 0.35))
    stops = T.vis_osc[:3] + [lerp(T.accent, BLACK, 0.2)]
    for r in range(19):
        px(a, 115, 294 + r, ramp(stops, r / 18))
    for x in range(113):
        px(a, x, 314, lerp(T.disp, T.label, 0.7) if x % 3 != 2 else T.disp)
    return a


def eq_close_pressed():
    bar = bar_frame(275, 14, True, left_edge=True, right_edge=True)
    cell = bar[3:12, 264:273].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    return cell


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------


def bar20(w, lit, left_edge=False, right_edge=False):
    a = bar_frame(w, 20, lit, left_edge, right_edge)
    # the frame's bottom row continues into the body
    rect(a, 0, 19, w, 1, T.frame_body if T.kind != "discord" else (30, 31, 34))
    return a


def side_tile(w, h, left):
    if T.kind == "netscape":
        return ns_side_tile(w, h, left)
    t = new(w, h, T.frame_body)
    if T.kind != "discord":
        if left:
            rect(t, 0, 0, 1, h, T.frame_edge_lit)
            rect(t, 1, 0, 1, h, lerp(T.frame_body, WHITE, 0.6))
            rect(t, w - 1, 0, 1, h, lerp(T.frame_body, T.edge_lo, 0.6))
        else:
            rect(t, w - 1, 0, 1, h, T.frame_edge_lit)
            rect(t, 0, 0, 1, h, lerp(T.frame_body, WHITE, 0.6))
        apply_border(t, left=left, right=not left)
    return t


def scroll_handle(pressed):
    t = new(8, 18, T.frame_body)
    t[:, :] = scroll_groove_col()
    if T.kind == "discord":
        rbox(t, 1, 0, 6, 18, 2.99, (26, 27, 30) if not pressed else T.accent)
    else:
        rbox(t, 0, 0, 8, 18, 2.5, T.btn_down if pressed else T.btn, T.btn_edge)
        for gy in (6, 8, 10):
            rect(t, 2, gy, 4, 1, T.btn_edge)
    return t


def scroll_groove_col():
    return (43, 45, 49) if T.kind == "discord" else lerp(T.frame_body, T.edge_lo, 0.2)


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
    """The 100px title piece: a tab (its slants in the 4px end caps), or a channel name."""
    t = bar20(100, lit)
    if T.kind == "discord":
        title_text(t, "# " + T.pl_title, 50 - text_w(UI, "# " + T.pl_title) // 2, 5, lit)
    elif T.kind == "netscape":
        title_text(t, T.pl_title, 50 - text_w(UI, T.pl_title) // 2, 4, lit)
    else:
        tab(t, 0, 4, 100, 15, lit, slant=4)
        title_text(t, T.pl_title, 50 - text_w(UI, T.pl_title) // 2, 6, lit)
    return t


def make_pledit():
    if T.kind == "netscape":
        return ns_make_pledit()
    a = new(280, 186, T.frame_body)
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar20(25, lit)
        t = bar20(25, lit, left_edge=True)
        a[y:y + 20, 0:25] = t
        a[y:y + 20, 26:126] = title_piece_pl(lit)
        t = bar20(25, lit, right_edge=True)
        caption_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    a[42:71, 0:12] = side_tile(12, 29, True)
    # right tile: list edge, the scrollbar groove at 5..12, outer edge
    t = side_tile(20, 29, False)
    rect(t, 5, 0, 8, 29, scroll_groove_col())
    if T.kind != "discord":
        rect(t, 4, 0, 1, 29, lerp(T.frame_body, T.edge_lo, 0.6))
        rect(t, 13, 0, 1, 29, lerp(T.frame_body, WHITE, 0.5))
    a[42:71, 31:51] = t
    bar = bar20(25, True, right_edge=True)
    cell = bar[3:12, 14:23].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = cell
    a[53:71, 52:60] = scroll_handle(False)
    a[53:71, 61:69] = scroll_handle(True)

    def bottom_base(w):
        t = new(w, 38, T.frame_body)
        if T.kind != "discord":
            rect(t, 0, 0, w, 1, lerp(T.frame_body, T.edge_lo, 0.6))
            rect(t, 0, 1, w, 1, lerp(T.frame_body, WHITE, 0.6))
            rect(t, 0, 37, w, 1, T.frame_edge_lit)
        else:
            rect(t, 0, 37, w, 1, T.edge_lo)
        return t

    t = bottom_base(125)
    if T.kind != "discord":
        rect(t, 0, 0, 1, 38, T.frame_edge_lit)
        rect(t, 1, 1, 1, 36, lerp(T.frame_body, WHITE, 0.6))
        rect(t, 0, 0, 12, 1, T.frame_body)
        rect(t, 0, 0, 1, 1, T.frame_edge_lit)
        rect(t, 11, 0, 1, 1, lerp(T.frame_body, T.edge_lo, 0.6))
        apply_border(t, left=True, bottom=True)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        t[8:26, bx:bx + 22] = toggle_cell(t[8:26, bx:bx + 22], 22, 18, lbl, False, False)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    if T.kind != "discord":
        rect(t, 149, 0, 1, 38, T.frame_edge_lit)
        rect(t, 130, 0, 19, 1, T.frame_body)
        apply_border(t, right=True, bottom=True)
    field(t, 6, 9, 56, 8)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        mini_transport_icon(t, kind, bx, 22, T.glyph if T.kind != "discord" else (181, 186, 193))
    field(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, T.label)
    rect(t, 84, 22 + 5, 1, 1, T.label)
    t[8:26, 106:128] = toggle_cell(t[8:26, 106:128], 22, 18, "LIST", False, False)
    grip_col = T.label
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 31 - 3 * j
            px(t, gx, gy, grip_col)
            if T.kind != "discord":
                px(t, gx + 1, gy + 1, WHITE)
    a[72:110, 126:276] = t

    a[0:38, 179:204] = apply_border(bottom_base(25), bottom=True)
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_bottom(w, grip, left_edge):
    if T.kind == "netscape":
        return ns_gen_bottom(w, grip, left_edge)
    t = new(w, 14, T.frame_body)
    if T.kind != "discord":
        rect(t, 0, 13, w, 1, T.frame_edge_lit)
        if left_edge:
            rect(t, 0, 0, 1, 14, T.frame_edge_lit)
            rect(t, 1, 0, 1, 13, lerp(T.frame_body, WHITE, 0.6))
        else:
            rect(t, w - 1, 0, 1, 14, T.frame_edge_lit)
        apply_border(t, left=left_edge, right=not left_edge, bottom=True)
    else:
        rect(t, 0, 13, w, 1, T.edge_lo)
    if grip:
        for k in range(3):
            for j in range(k + 1):
                gx, gy = w - 4 - (getattr(T, "border", 0) or 0) - 3 * k + 3 * j, 9 - 3 * j
                px(t, gx, gy, T.label)
                if T.kind != "discord":
                    px(t, gx + 1, gy + 1, WHITE)
    return t


TAB_Y_GEN = 2
TAB_H_GEN = 17


def make_gen():
    a = new(194, 109, T.frame_body)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, t):
            a[y:y + 20, px0:px0 + 25] = t

        piece(0, bar20(25, lit, left_edge=True))
        t = bar20(25, lit)
        if T.tab_style:
            tab(t, 16, TAB_Y_GEN, 200, TAB_H_GEN, lit, slant=4)
        piece(26, t)
        t = bar20(25, lit)
        if T.tab_style:
            tab(t, -100, TAB_Y_GEN, 300, TAB_H_GEN, lit, slant=4)
        piece(52, t)
        t = bar20(25, lit)
        if T.tab_style:
            tab(t, -191, TAB_Y_GEN, 200, TAB_H_GEN, lit, slant=4)
        piece(78, t)
        piece(104, bar20(25, lit))
        t = bar20(25, lit, right_edge=True)
        caption_button(t, 14, 3, "close", lit)
        piece(130, t)

    a[42:56, 0:125] = gen_bottom(125, False, True)
    a[57:71, 0:125] = gen_bottom(125, True, False)
    a[72:86, 127:152] = new(25, 14, T.frame_body)
    if T.kind == "netscape":
        rect(a, 127, 84, 25, 1, SHADOW)
        rect(a, 127, 85, 25, 1, BLACK)
    elif T.kind != "discord":
        rect(a, 127, 85, 25, 1, T.frame_edge_lit)
        apply_border(a[72:86, 127:152], bottom=True)
    else:
        rect(a, 127, 85, 25, 1, T.edge_lo)
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = side_tile(w, h, left)
    bar = bar20(25, True, right_edge=True)
    cell = bar[3:12, 14:23].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = cell

    # letters: each row starts at x 1, each letter in its own cell, 1px separators of x 0's colour;
    # a cell's background is the title piece's own rows 4..10, so the letters sit on the tab
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        centre = a[(0 if lit else 21) + 4:(0 if lit else 21) + 11, 60]
        col = T.title_lit if lit else T.title_dim
        if T.kind == "discord":
            col = (148, 155, 164) if lit else (100, 104, 112)
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
# Netscape Communicator 4.x: Windows 9x grey, bevels, navy captions, the Navigation Toolbar
# ------------------------------------------------------------------------------------------

FACE = (192, 192, 192)
LIGHT = (223, 223, 223)
SHADOW = (128, 128, 128)
NAVY = (0, 0, 128)


def bevel(a, x, y, w, h, tl, br):
    rect(a, x, y, w, 1, tl)
    rect(a, x, y, 1, h, tl)
    rect(a, x, y + h - 1, w, 1, br)
    rect(a, x + w - 1, y, 1, h, br)


def w9_button(a, x, y, w, h, pressed=False, face=FACE):
    rect(a, x, y, w, h, face)
    if pressed:
        bevel(a, x, y, w, h, BLACK, WHITE)
        bevel(a, x + 1, y + 1, w - 2, h - 2, SHADOW, LIGHT)
    else:
        bevel(a, x, y, w, h, WHITE, BLACK)
        bevel(a, x + 1, y + 1, w - 2, h - 2, LIGHT, SHADOW)


def w9_sunken(a, x, y, w, h):
    bevel(a, x, y, w, h, SHADOW, WHITE)
    bevel(a, x + 1, y + 1, w - 2, h - 2, BLACK, LIGHT)


def dither(a, x, y, w, h, c0=WHITE, c1=FACE):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px(a, xx, yy, c0 if (xx + yy) % 2 == 0 else c1)


def bold(a, font, s, x, y, col):
    """Caption text (plain: the pixel capitals are too narrow to embolden and stay legible)."""
    draw_text(a, font, s, x, y, col)


def ns_bar_frame(w, h, lit, left_edge=False, right_edge=False):
    """A Windows 9x caption strip: the frame's two light rows, the navy (or grey) caption, face below."""
    a = new(w, h, FACE)
    cap = NAVY if lit else SHADOW
    rect(a, 0, 0, w, 1, LIGHT)
    rect(a, 0, 1, w, 1, WHITE)
    x0 = 3 if left_edge else 0
    x1 = w - 3 if right_edge else w
    rect(a, x0, 3, x1 - x0, 11, cap)
    if left_edge:
        rect(a, 0, 0, 1, h, LIGHT)
        rect(a, 1, 1, 1, h - 1, WHITE)
    if right_edge:
        rect(a, w - 1, 0, 1, h, BLACK)
        rect(a, w - 2, 1, 1, h - 1, SHADOW)
    return a


def ns_title(a, s, x, y, lit):
    bold(a, UI, s, x, y, WHITE if lit else FACE)


def ship_wheel(a, x, y, rim=(128, 72, 24), hub=(200, 150, 60)):
    """9x9: Navigator's ship's wheel (the window icon), drawn here."""
    W, H = a.shape[1], a.shape[0]
    cx, cy = x + 4.5, y + 4.5
    for k in range(8):
        import math
        ang = k * math.pi / 4
        paint(a, 0, 0, line_mask(W, H, [(cx, cy), (cx + 4.4 * math.cos(ang), cy + 4.4 * math.sin(ang))], 1.0), rim)
    paint(a, 0, 0, ellipse_mask(W, H, cx - 3.2, cy - 3.2, 6.4, 6.4), rim)
    paint(a, 0, 0, ellipse_mask(W, H, cx - 2.2, cy - 2.2, 4.4, 4.4), NAVY)
    paint(a, 0, 0, ellipse_mask(W, H, cx - 1.3, cy - 1.3, 2.6, 2.6), hub)


def ns_caption_button(a, x, y, kind, lit=True, pressed=False):
    if kind == "options":
        if pressed:
            rect(a, x, y, 9, 9, (0, 0, 64) if lit else SHADOW)
        ship_wheel(a, x, y)
        return
    w9_button(a, x, y, 9, 9, pressed)
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "minimize":
        rect(a, X + 2, Y + 5, 4, 2, BLACK)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 4, BLACK)
        rect(a, X + 3, Y + 4, 3, 1, FACE)
    elif kind == "close":
        for i in range(4):
            rect(a, X + 2 + i, Y + 2 + i, 2, 1, BLACK)
            rect(a, X + 5 - i, Y + 2 + i, 2, 1, BLACK)


def ns_field(a, x, y, w, h):
    rect(a, x, y, w, h, T.disp)
    w9_sunken(a, x - 2, y - 2, w + 4, h + 4)


def ns_track_h(a, x, y, w, th, fill_from=None, fill_to=None, colour=None):
    """A thin sunken channel; navy progress blocks between fill_from..fill_to."""
    rect(a, x, y, w, th, WHITE)
    bevel(a, x, y, w, th, SHADOW, WHITE)
    rect(a, x + 1, y + 1, w - 2, 1, BLACK)
    if fill_from is not None and fill_to is not None and fill_to > fill_from:
        col = NAVY if colour is None or colour == T.accent else SHADOW
        for bx in range(int(fill_from), int(fill_to), 4):
            rect(a, max(bx, x + 2), y + 2, min(3, int(fill_to) - bx), th - 3, col)


def ns_track_v(a, x, y, h, tw, fill_from=None):
    rect(a, x, y, tw, h, WHITE)
    bevel(a, x, y, tw, h, SHADOW, WHITE)
    rect(a, x + 1, y + 1, 1, h - 2, BLACK)
    if fill_from is not None:
        for by in range(y + h - 3, int(fill_from) - 1, -4):
            top = max(int(fill_from), by - 2, y + 2)
            rect(a, x + 2, top, tw - 3, by - top + 1, NAVY)


def ns_knob(a, x, y, w, h, pressed, r=None):
    w9_button(a, x, y, w, h, False, LIGHT if pressed else FACE)


def ns_icon(a, kind, cx, cy, s=1.0):
    """Navigator 4-style toolbar icons (drawn here): green arrows, a red octagon, a house."""
    W, H = a.shape[1], a.shape[0]

    def shape(pts, top, bot, edge):
        m = poly_mask(W, H, [(cx + px_ * s + 1, cy + py_ * s + 1) for px_, py_ in pts])
        paint(a, 0, 0, m, SHADOW)                    # drop shadow
        m = poly_mask(W, H, [(cx + px_ * s, cy + py_ * s) for px_, py_ in pts])
        paint(a, 0, 0, m, edge)
        g = vgrad(H, [top, bot], W)
        inner = poly_mask(W, H, [(cx + px_ * s * 0.78 + (0.15 if px_ < 0 else -0.15),
                                  cy + py_ * s * 0.74) for px_, py_ in pts])
        paint(a, 0, 0, inner, g)

    green = ((150, 230, 120), (20, 130, 30), (0, 70, 0))
    if kind in ("previous", "next"):
        d = -1 if kind == "previous" else 1
        pts = [(8 * d, 0), (1 * d, -7), (1 * d, -3), (-8 * d, -3), (-8 * d, 3), (1 * d, 3), (1 * d, 7)]
        shape(pts, *green)
    elif kind == "play":   # Reload: a circling arrow
        R0, R1 = 7.0 * s, 3.4 * s
        ring = ellipse_mask(W, H, cx - R0, cy - R0, 2 * R0, 2 * R0) - ellipse_mask(W, H, cx - R1, cy - R1, 2 * R1, 2 * R1)
        wedge = poly_mask(W, H, [(cx, cy), (cx + 9, cy - 9), (cx + 9, cy + 1)])
        ring = np.clip(ring - wedge, 0, 1)
        sh = np.zeros_like(ring)
        sh[1:, 1:] = ring[:-1, :-1]
        paint(a, 0, 0, sh, SHADOW)
        paint(a, 0, 0, ring, green[2])
        inner = ellipse_mask(W, H, cx - R0 + 1, cy - R0 + 1, 2 * R0 - 2, 2 * R0 - 2) - \
            ellipse_mask(W, H, cx - R1 - 1, cy - R1 - 1, 2 * R1 + 2, 2 * R1 + 2)
        inner = np.clip(inner - poly_mask(W, H, [(cx, cy), (cx + 10, cy - 10), (cx + 10, cy + 2.5)]), 0, 1)
        paint(a, 0, 0, inner, vgrad(H, green[:2], W))
        tri(a, [(cx + 2.5, cy - 9), (cx + 9.5, cy - 4.5), (cx + 2.5, cy - 0.5)], green[2])
        tri(a, [(cx + 3.6, cy - 6.8), (cx + 7.4, cy - 4.5), (cx + 3.6, cy - 2.4)], green[1])
    elif kind == "stop":
        import math
        pts = [(7.5 * math.cos(math.pi / 8 + k * math.pi / 4), 7.5 * math.sin(math.pi / 8 + k * math.pi / 4))
               for k in range(8)]
        shape(pts, (255, 110, 90), (180, 0, 0), (90, 0, 0))
        rect(a, int(cx - 4), int(cy - 1), 8, 2, WHITE)
    elif kind == "pause":
        for dx in (-5, 1):
            shape([(dx, -6), (dx + 4, -6), (dx + 4, 6), (dx, 6)], (140, 170, 255), (0, 0, 170), (0, 0, 80))
    elif kind == "eject":  # Home: a house
        roof = [(-8, -0.5), (0, -7.5), (8, -0.5)]
        tri(a, [(cx + p[0] + 1, cy + p[1] + 1) for p in roof], SHADOW)
        rect(a, int(cx - 5), int(cy), 11, 7, SHADOW)
        rect(a, int(cx - 6), int(cy - 1), 11, 7, (90, 50, 10))
        rect(a, int(cx - 5), int(cy), 9, 5, (255, 236, 170))
        rect(a, int(cx - 1), int(cy + 1), 3, 5, (150, 80, 20))
        tri(a, [(cx + p[0], cy + p[1]) for p in roof], (120, 30, 10))
        tri(a, [(cx - 5.5, cy - 1.5), (cx, cy - 5.8), (cx + 5.5, cy - 1.5)], (220, 70, 40))


NS_LABELS = {"previous": "BACK", "play": "RELOAD", "pause": "PAUSE", "stop": "STOP", "next": "FORWARD",
             "eject": "HOME"}


def ns_tray(bg, pressed=None):
    a = bg.copy()
    centres = {k: (x + w / 2, TRAY_H / 2) for k, (x, w) in CB.items()}
    ex, ey, ew, eh = EJECT
    centres["eject"] = (ex + ew / 2, ey + eh / 2)
    for k, (cx, cy) in centres.items():
        o = 0
        if k == pressed:
            if k == "eject":
                bevel(a, ex, ey, ew, eh, SHADOW, WHITE)
            else:
                x, w = CB[k]
                bevel(a, x, 0, w, TRAY_H, SHADOW, WHITE)
            o = 1
        ns_icon(a, k, cx + o, cy + o, 0.85 if k == "eject" else 1.0)
    return a


def ns_toggle_cell(bg, w, h, label, on, pressed):
    a = bg.copy()
    if on:
        w9_button(a, 0, 0, w, h, True)
        dither(a, 2, 2, w - 4, h - 4)
    else:
        w9_button(a, 0, 0, w, h, pressed)
    o = 1 if (pressed or on) else 0
    if label:
        text_center(a, TINY, label, w // 2 + o, (h - 5) // 2 + o, NAVY if on else BLACK)
    return a


def ns_clutter_bar(lit_letters, bg):
    a = new(8, 43, FACE)
    bevel(a, 0, 0, 8, 43, WHITE, SHADOW)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, WHITE)
            bevel(a, 1, y, 6, h, SHADOW, WHITE)
        draw_text(a, TINY, letter, 2 + (1 if on else 0), y + (h - 5) // 2, NAVY if on else BLACK)
    return a


def collapse_tab(a, x, y, h):
    """Navigator's toolbar collapse tab: a narrow raised bar with a small arrow at the top."""
    rect(a, x, y, 7, h, FACE)
    bevel(a, x, y, 7, h, WHITE, SHADOW)
    tri(a, [(x + 1.5, y + 3), (x + 5.5, y + 3), (x + 3.5, y + 5.5)], BLACK)
    for yy in range(y + 8, y + h - 2, 2):
        px(a, x + 2, yy, WHITE)
        px(a, x + 3, yy + 1, SHADOW)
        px(a, x + 4, yy, WHITE)


def etched_h(a, x, y, w):
    rect(a, x, y, w, 1, SHADOW)
    rect(a, x, y + 1, w, 1, WHITE)


def ns_main_bg():
    a = new(275, 116, FACE)
    a[0:14] = main_titlebar(True)
    # the window frame below the caption
    rect(a, 0, 14, 1, 102, LIGHT)
    rect(a, 1, 14, 1, 101, WHITE)
    rect(a, 274, 0, 1, 116, BLACK)
    rect(a, 273, 1, 1, 114, SHADOW)
    rect(a, 0, 115, 275, 1, BLACK)
    rect(a, 1, 114, 273, 1, SHADOW)
    return a


def ns_main_extras(a):
    """What makes main.bmp Navigator: toolbar bands, labels, the Location/Bookmarks row, the throbber."""
    etched_h(a, 2, 70, 271)
    etched_h(a, 2, 83, 271)
    collapse_tab(a, 3, 15, 54)
    collapse_tab(a, 3, 72, 11)
    collapse_tab(a, 3, 86, 27)
    # the Bookmarks button and Location: label over the location field
    W, H = a.shape[1], a.shape[0]
    rect(a, 110, 14, 4, 5, (0, 120, 60))           # a bookmark ribbon
    tri(a, [(110, 19), (112, 17), (114, 19)], FACE)
    draw_text(a, TINY, "BOOKMARKS", 116, 14, BLACK)
    draw_text(a, TINY, "LOCATION:", 160, 14, BLACK)
    rect(a, 158, 14, 1, 5, SHADOW)
    # toolbar labels under the buttons
    # (nudged apart from their buttons' centres so neighbours keep a gap)
    for k, x in {"previous": 17, "play": 38, "pause": 64, "stop": 89, "next": 107, "eject": 141}.items():
        draw_text(a, TINY, NS_LABELS[k], x, 107, BLACK)
    # the throbber: the N, in a sunken box at the end of the toolbar
    bx, by, bw, bh = 243, 85, 28, 27
    rect(a, bx, by, bw, bh, (0, 0, 0))
    bevel(a, bx, by, bw, bh, SHADOW, WHITE)
    png = logo_png(96)
    im = Image.open(png).convert("RGBA").resize((bw - 2, bw - 2), Image.LANCZOS)
    arr = np.asarray(im, dtype=np.float32)
    top = (arr.shape[0] - (bh - 2)) // 2
    arr = arr[top:top + bh - 2]
    paint(a, bx + 1, by + 1, arr[..., 3] / 255.0, arr[..., :3])
    return a


def ns_side_tile(w, h, left):
    t = new(w, h, FACE)
    if left:
        rect(t, 0, 0, 1, h, LIGHT)
        rect(t, 1, 0, 1, h, WHITE)
    else:
        rect(t, w - 1, 0, 1, h, BLACK)
        rect(t, w - 2, 0, 1, h, SHADOW)
    return t


def ns_status_panel(t, x0, x1, y, h, open_left=False, open_right=False):
    """A sunken status-bar panel from x0 to x1 (exclusive), rows y..y + h - 1."""
    rect(t, x0, y, x1 - x0, 1, SHADOW)
    rect(t, x0, y + h - 1, x1 - x0, 1, WHITE)
    if not open_left:
        rect(t, x0, y, 1, h, SHADOW)
    if not open_right:
        rect(t, x1 - 1, y, 1, h, WHITE)


def padlock(t, x, y):
    rect(t, x + 1, y, 4, 1, (90, 90, 90))
    rect(t, x, y + 1, 1, 3, (90, 90, 90))
    rect(t, x + 5, y + 1, 1, 3, (90, 90, 90))
    rect(t, x - 1, y + 3, 8, 5, (200, 160, 30))
    bevel(t, x - 1, y + 3, 8, 5, (255, 230, 120), (120, 90, 10))
    px(t, x + 3, y + 5, BLACK)


def component_icons(t, x, y):
    """The Component Bar's little icons (drawn here): Navigator, Mail, Discussion, Composer."""
    ship_wheel(t, x, y - 1)
    # mail: an envelope
    rect(t, x + 11, y + 1, 9, 6, WHITE)
    bevel(t, x + 11, y + 1, 9, 6, (60, 60, 120), (60, 60, 120))
    for i in range(4):
        px(t, x + 12 + i, y + 2 + i // 2 + (i % 2), (60, 60, 120))
        px(t, x + 18 - i, y + 2 + i // 2 + (i % 2), (60, 60, 120))
    # discussion: two speech balloons
    rect(t, x + 22, y, 6, 4, (255, 255, 160))
    bevel(t, x + 22, y, 6, 4, (100, 100, 40), (100, 100, 40))
    rect(t, x + 25, y + 3, 6, 4, (160, 220, 255))
    bevel(t, x + 25, y + 3, 6, 4, (30, 80, 120), (30, 80, 120))
    # composer: a pen over a page
    rect(t, x + 33, y, 6, 8, WHITE)
    bevel(t, x + 33, y, 6, 8, SHADOW, SHADOW)
    for i in range(6):
        px(t, x + 34 + i, y + 6 - i, (160, 40, 40))
        px(t, x + 35 + i, y + 6 - i, (220, 80, 60))


def ns_scroll_handle(pressed):
    t = new(8, 18, FACE)
    w9_button(t, 0, 0, 8, 18, False, LIGHT if pressed else FACE)
    return t


def win9x_grip(t, x, y):
    """The 12x12 size grip in a status bar's corner: three diagonal ridges."""
    for k in (0, 4, 8):
        for i in range(12 - k):
            px(t, x + k + i, y + 11 - i, WHITE)
            px(t, x + k + i + 1, y + 11 - i, SHADOW)
            px(t, x + k + i + 2, y + 11 - i, SHADOW)


def ns_make_pledit():
    a = new(280, 186, FACE)
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar20(25, lit)
        a[y:y + 20, 0:25] = bar20(25, lit, left_edge=True)
        a[y:y + 20, 26:126] = title_piece_pl(lit)
        t = bar20(25, lit, right_edge=True)
        caption_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t
    # left tile: the frame, then the list's sunken edge
    t = ns_side_tile(12, 29, True)
    rect(t, 10, 0, 1, 29, SHADOW)
    rect(t, 11, 0, 1, 29, BLACK)
    a[42:71, 0:12] = t
    # right tile: the list's edge, the scrollbar track (dithered) at 5..12, the frame
    t = ns_side_tile(20, 29, False)
    rect(t, 0, 0, 1, 29, LIGHT)
    rect(t, 1, 0, 1, 29, WHITE)
    dither(t, 5, 0, 8, 29)
    a[42:71, 31:51] = t
    cell = bar20(25, True, right_edge=True)[3:12, 14:23].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = cell
    a[53:71, 52:60] = ns_scroll_handle(False)
    a[53:71, 61:69] = ns_scroll_handle(True)

    def bottom_base(w):
        t = new(w, 38, FACE)
        rect(t, 0, 0, w, 1, LIGHT)
        rect(t, 0, 1, w, 1, WHITE)
        rect(t, 0, 36, w, 1, SHADOW)
        rect(t, 0, 37, w, 1, BLACK)
        return t

    # bottom left: buttons, then the status bar (security padlock, "Document: Done")
    t = bottom_base(125)
    rect(t, 0, 0, 1, 37, LIGHT)
    rect(t, 1, 1, 1, 35, WHITE)
    rect(t, 2, 0, 9, 2, FACE)
    rect(t, 10, 0, 1, 2, SHADOW)
    rect(t, 11, 0, 1, 2, BLACK)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        t[7:25, bx:bx + 22] = ns_toggle_cell(t[7:25, bx:bx + 22], 22, 18, lbl, False, False)
    ns_status_panel(t, 3, 16, 27, 9)
    padlock(t, 7, 28)
    ns_status_panel(t, 18, 125, 27, 9, open_right=True)
    draw_text(t, TINY, "DOCUMENT: DONE", 22, 29, BLACK)
    a[72:110, 0:125] = t

    t = bottom_base(25)
    ns_status_panel(t, 0, 25, 27, 9, open_left=True, open_right=True)
    a[0:38, 179:204] = t

    # bottom right: readouts, mini transport, LIST, the Component Bar, the size grip
    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, BLACK)
    rect(t, 148, 1, 1, 36, SHADOW)
    rect(t, 130, 0, 18, 2, FACE)
    rect(t, 130, 0, 1, 2, LIGHT)
    rect(t, 131, 0, 1, 2, WHITE)
    ns_status_panel(t, -4, 2, 27, 9, open_left=True)
    rect(t, 2, 20, 1, 15, FACE)
    ns_field(t, 6, 9, 56, 8)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        mini_transport_icon(t, kind, 3 + 10 * k, 22, BLACK)
    ns_field(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, T.label)
    rect(t, 84, 22 + 5, 1, 1, T.label)
    t[7:25, 106:128] = ns_toggle_cell(t[7:25, 106:128], 22, 18, "LIST", False, False)
    ns_status_panel(t, 101, 133, 27, 9)
    component_icons_small(t, 104, 28)
    win9x_grip(t, 135, 24)
    a[72:110, 126:276] = t
    return a


def component_icons_small(t, x, y):
    """Navigator, Mail and Composer, the Component Bar's little icons (drawn here)."""
    ship_wheel(t, x - 1, y - 1)
    rect(t, x + 10, y + 1, 8, 5, WHITE)
    bevel(t, x + 10, y + 1, 8, 5, (60, 60, 120), (60, 60, 120))
    for i in range(3):
        px(t, x + 11 + i, y + 2 + i, (60, 60, 120))
        px(t, x + 16 - i, y + 2 + i, (60, 60, 120))
    rect(t, x + 20, y, 6, 7, WHITE)
    bevel(t, x + 20, y, 6, 7, SHADOW, SHADOW)
    for i in range(6):
        px(t, x + 21 + i, y + 6 - i, (160, 40, 40))
        px(t, x + 22 + i, y + 6 - i, (220, 80, 60))


def ns_gen_bottom(w, grip, left_edge):
    t = new(w, 14, FACE)
    rect(t, 0, 12, w, 1, SHADOW)
    rect(t, 0, 13, w, 1, BLACK)
    if left_edge:
        rect(t, 0, 0, 1, 13, LIGHT)
        rect(t, 1, 0, 1, 12, WHITE)
    else:
        rect(t, w - 1, 0, 1, 14, BLACK)
        rect(t, w - 2, 0, 1, 13, SHADOW)
    if grip:
        for k in (0, 3, 6):
            for i in range(9 - k):
                px(t, w - 11 + k + i, y_ := 10 - i, WHITE)
                px(t, w - 10 + k + i, y_, SHADOW)
    return t


def ns_eq_frame_bg():
    a = new(275, 116, FACE)
    rect(a, 0, 14, 1, 102, LIGHT)
    rect(a, 1, 14, 1, 101, WHITE)
    rect(a, 274, 0, 1, 116, BLACK)
    rect(a, 273, 1, 1, 114, SHADOW)
    rect(a, 0, 115, 275, 1, BLACK)
    rect(a, 1, 114, 273, 1, SHADOW)
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp, text files
# ------------------------------------------------------------------------------------------


def genex_colours():
    if T.kind == "discord":
        return [(49, 51, 56), (219, 222, 225), (43, 45, 49), (242, 243, 245), (219, 222, 225), (30, 31, 34),
                (64, 66, 73), (43, 45, 49), (148, 155, 164), (63, 65, 71), (30, 31, 34), (88, 101, 242),
                (43, 45, 49), (43, 45, 49), (26, 27, 30), (43, 45, 49), (88, 101, 242), (43, 45, 49)]
    acc_lt = T.accent_lt
    return [WHITE, BLACK, T.frame_body, (20, 24, 32), (20, 24, 32), lerp(T.frame_body, T.edge_lo, 0.7),
            acc_lt, lerp(T.body_top, WHITE, 0.4), (40, 48, 60), WHITE, T.edge_lo, T.accent,
            T.frame_body, T.btn[1], T.btn_edge, T.btn_down[0], T.accent, T.track]


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
    owner = T.company
    if hasattr(T, "subject"):
        title = T.wsz[:-4].replace("-", " ")
        with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
            f.write(f"{title} - a personal skin in the style of {T.subject}.\n"
                    f"{T.logo_owner} logo (c) {T.logo_owner}; private use only.\n\n"
                    "A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py),\n"
                    "except the logo in the About spot.\n")
        return
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{T.app} - a skin in the style of {T.app}, drawn from scratch. Not affiliated with {T.company.rstrip('.')}.\n"
            f"{'=' * (len(T.app) * 2 + 40)}\n\n"
            "A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py) from\n"
            "gradients, shapes and hand-made pixel fonts, except the logo in the About spot.\n\n"
            f"{T.app} logo (c) {owner}; private use only.\n"
        )


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
    c0, c1 = np.array(T.accent_lt if T.kind != "discord" else (43, 45, 49), np.float32), np.array(T.accent, np.float32)
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
             title=f"{T.app} - a skin in the style of {T.app}", bars=bars)
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
