#!/usr/bin/python3
"""MSN Messenger, Office 2007 and Office 2010: classic Winamp 2.x skins in the style of three
Microsoft apps of the 2005-2010 era.

One procedural generator, a theme each (based on skins/ember/gen_skin.py by way of
private-repo/skins/apps/browsers/gen_skin.py, keeping Ember's sheet layouts). Everything is drawn here from
code (gradients, anti-aliased shapes, hand-made pixel fonts), except one real logo per skin,
rasterised from source/ at generation time. Private use only.

    /usr/bin/python3 -I gen_skin.py [msn|office2007|office2010 ...]   (no argument builds all)
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
for _c in "0123456789+-.":
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


# Digits and a few marks for the UI font (titlebars), padded like its capitals.
for _k in "0123456789.":
    _g = FONT5[_k]
    UI[_k] = [_g[i] for i in (0, 1, 1, 2, 3, 3, 4)] + ["." * len(_g[0])] * 2
UI["?"] = [".##.", "#..#", "...#", "..#.", ".#..", "....", ".#..", "....", "...."]


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    # MSN Messenger 7.5 (2005, Windows XP): the light blue and white window, the green and blue
    # buddies, glossy round buttons, green/red status dots, the contact list.
    "msn": SimpleNamespace(
        name="msn", kind="msn", app="MSN Messenger", wsz="MSN-Messenger.wsz",
        subject="MSN Messenger 7.5", owner="Microsoft Corporation",
        frame_lit=[(250, 252, 255), (222, 235, 251), (196, 218, 245)],
        frame_dim=[(250, 251, 253), (234, 240, 248), (220, 229, 241)],
        frame_edge_lit=(98, 132, 186), frame_edge_dim=(160, 176, 202),
        body=[(255, 255, 255), (240, 246, 254), (214, 230, 249)], frame_body=(210, 226, 247),
        edge_lo=(120, 150, 196),
        disp=(255, 255, 255), disp_edge=(127, 157, 185), disp_r=2.5,
        txt=(0, 0, 0), txt_dim=(196, 206, 220), label=(84, 110, 156),
        digit=(24, 48, 98),
        accent=(52, 112, 214), accent_lt=(204, 224, 250),
        green=(58, 170, 52), red=(222, 58, 44), grey=(150, 160, 176),
        glyph=(30, 64, 128), play=(255, 255, 255),
        btn=[(255, 255, 255), (238, 244, 252), (205, 222, 245), (226, 237, 251)], btn_edge=(126, 156, 204),
        btn_down=[(150, 190, 240), (96, 152, 228), (58, 116, 210), (98, 156, 230)],
        btn_on=[(255, 255, 255), (238, 244, 252), (205, 222, 245), (226, 237, 251)],
        btn_on_edge=(126, 156, 204), btn_down_edge=(40, 80, 160),
        track=(222, 233, 248), track_edge=(126, 156, 204),
        knob=[(255, 255, 255), (232, 241, 252), (196, 216, 244), (220, 233, 250)], knob_edge=(84, 120, 180),
        knob_down=[(170, 204, 248), (110, 162, 232), (64, 120, 212), (100, 156, 230)],
        knob_edge_down=(36, 76, 156),
        title_lit=(16, 40, 96), title_dim=(120, 136, 164), title_2=(16, 40, 96), title_2_dim=(120, 136, 164),
        pledit=dict(Normal="#000000", Current="#1E7B1E", NormalBG="#FFFFFF", SelectedBG="#C6DEF7", Font="Tahoma"),
        vis_bars=[(110, 206, 92), (58, 170, 52), (52, 140, 170), (52, 112, 214), (40, 80, 170)],
        vis_dots=(232, 240, 250), vis_peak=(24, 48, 98),
        vis_osc=[(52, 112, 214), (70, 128, 220), (90, 146, 226), (120, 168, 232), (160, 196, 240)],
        main_title=[("MSN Messenger", "title")], eq_title="Equalizer", pl_title="Playlist", gen_tab=False,
        logo=os.path.join(SRC, "logo-msn", "wlm-logo.svg"),
        logo_url="https://commons.wikimedia.org/wiki/File:WLM_logo.svg",
    ),
    # Office 2007, the Blue colour scheme: the round Office Button, the Quick Access Toolbar, the
    # blue ribbon with boxed groups and label bands, glossy buttons that turn orange when pressed
    # and amber when checked.
    "office2007": SimpleNamespace(
        name="office2007", kind="o7", app="Office 2007", wsz="Office-2007.wsz",
        subject="Microsoft Office 2007 (Blue)", owner="Microsoft Corporation",
        frame_lit=[(228, 238, 251), (210, 225, 245), (194, 214, 240)],
        frame_dim=[(236, 242, 249), (226, 234, 244), (216, 227, 241)],
        frame_edge_lit=(101, 138, 190), frame_edge_dim=(160, 180, 208),
        body=[(214, 228, 245), (199, 218, 241), (191, 212, 238)], frame_body=(191, 212, 238),
        edge_lo=(141, 178, 227),
        group=[(240, 246, 253), (226, 236, 249), (216, 229, 246)], group_band=[(202, 220, 243), (190, 211, 239)],
        group_edge=(150, 182, 224),
        disp=(255, 255, 255), disp_edge=(171, 193, 222), disp_r=0.5,
        txt=(0, 0, 0), txt_dim=(196, 206, 222), label=(62, 106, 170),
        digit=(21, 66, 139),
        accent=(79, 129, 189), accent_lt=(255, 226, 150),
        glyph=(21, 66, 139), play=(52, 140, 52),
        btn=[(252, 253, 255), (234, 241, 251), (216, 229, 245), (228, 238, 250)], btn_edge=(141, 178, 227),
        btn_down=[(252, 196, 140), (250, 160, 90), (246, 134, 48), (250, 176, 104)],
        btn_down_edge=(142, 129, 101),
        btn_on=[(255, 236, 178), (255, 216, 108), (255, 196, 64), (255, 222, 128)],
        btn_on_edge=(194, 165, 120),
        track=(198, 214, 236), track_edge=(120, 150, 196),
        knob=[(255, 255, 255), (234, 241, 251), (210, 225, 245), (226, 237, 250)], knob_edge=(92, 124, 172),
        knob_down=[(252, 210, 160), (250, 170, 100), (246, 138, 52), (250, 180, 110)],
        knob_edge_down=(150, 104, 52),
        title_lit=(21, 66, 139), title_dim=(122, 142, 172), title_2=(62, 106, 170), title_2_dim=(150, 166, 190),
        pledit=dict(Normal="#000000", Current="#15428B", NormalBG="#FFFFFF", SelectedBG="#FFE7A2", Font="Segoe UI"),
        vis_bars=[(167, 191, 222), (79, 129, 189), (56, 93, 138)], vis_dots=(232, 238, 246),
        vis_peak=(192, 80, 77),
        vis_osc=[(79, 129, 189), (100, 145, 198), (128, 164, 208), (156, 184, 218), (190, 208, 230)],
        main_title=[("Now Playing", "title"), (" - YTMinamp", "title_2")],
        eq_title="Equalizer", pl_title="Playlist", gen_tab=True,
        tab_top=(255, 255, 255), tab_bot=(218, 230, 246), tab_edge=(141, 178, 227),
        tabs=["Home", "Insert"], tab_text=(21, 66, 139),
        logo=os.path.join(SRC, "logo-office2007", "office-2007-logo.svg"),
        logo_url="https://commons.wikimedia.org/wiki/File:Microsoft_Office_2007_logo.svg",
    ),
    # Office 2010 (Word, Silver): the flatter silver ribbon, the blue File tab and Backstage,
    # the Word icon as the window menu, yellow-orange checked and pressed states.
    "office2010": SimpleNamespace(
        name="office2010", kind="o10", app="Office 2010", wsz="Office-2010.wsz",
        subject="Microsoft Office 2010 (Word, Silver)", owner="Microsoft Corporation",
        frame_lit=[(246, 248, 251), (234, 238, 243), (223, 228, 235)],
        frame_dim=[(248, 249, 251), (242, 244, 247), (236, 239, 243)],
        frame_edge_lit=(146, 153, 163), frame_edge_dim=(186, 191, 198),
        body=[(255, 255, 255), (246, 248, 251), (234, 238, 243)], frame_body=(223, 228, 235),
        edge_lo=(190, 195, 202),
        disp=(255, 255, 255), disp_edge=(171, 173, 179), disp_r=0,
        txt=(0, 0, 0), txt_dim=(206, 210, 216), label=(90, 98, 110),
        digit=(43, 87, 154),
        accent=(43, 87, 154), accent_lt=(253, 231, 155), word=(43, 87, 154),
        backstage=[(62, 116, 190), (43, 87, 154)],
        glyph=(64, 70, 80), play=(43, 87, 154),
        btn=[(255, 255, 255), (247, 249, 251), (240, 243, 247), (240, 243, 247)], btn_edge=(197, 201, 207),
        btn_down=[(251, 219, 148), (249, 197, 104), (249, 197, 104), (251, 212, 130)],
        btn_down_edge=(194, 155, 74),
        btn_on=[(254, 240, 192), (253, 228, 150), (253, 228, 150), (254, 236, 176)],
        btn_on_edge=(222, 186, 96),
        track=(214, 219, 226), track_edge=(160, 166, 176),
        knob=[(255, 255, 255), (244, 246, 249), (230, 234, 239), (236, 239, 243)], knob_edge=(128, 136, 148),
        knob_down=[(253, 228, 160), (250, 204, 116), (250, 204, 116), (252, 218, 140)],
        knob_edge_down=(170, 130, 60),
        title_lit=(59, 59, 59), title_dim=(150, 150, 150), title_2=(110, 110, 110), title_2_dim=(170, 170, 170),
        pledit=dict(Normal="#000000", Current="#2B579A", NormalBG="#FFFFFF", SelectedBG="#D5E1F2", Font="Segoe UI"),
        vis_bars=[(120, 160, 214), (43, 87, 154), (30, 60, 110)], vis_dots=(238, 241, 245),
        vis_peak=(247, 150, 70),
        vis_osc=[(43, 87, 154), (70, 110, 172), (100, 136, 190), (136, 166, 208), (176, 198, 226)],
        main_title=[("Now Playing", "title"), (" - YTMinamp", "title_2")],
        eq_title="Equalizer", pl_title="Playlist", gen_tab=True,
        tab_top=(255, 255, 255), tab_bot=(255, 255, 255), tab_edge=(190, 195, 202),
        tabs=["Home", "Insert"], tab_text=(59, 59, 59),
        logo=os.path.join(SRC, "logo-office2010", "office-2010-logo.svg"),
        logo_url="https://commons.wikimedia.org/wiki/File:Microsoft_Office_2010_logo.svg",
    ),
}


def use_theme(name):
    global T, OUT
    T = THEMES[name]
    OUT = os.path.join(OUT_ROOT, name)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT_ROOT, "scratch"), exist_ok=True)


def logo_png(px_h):
    """The theme's logo rasterised into out/scratch; Office logos are cut to their square mark."""
    out = os.path.join(OUT_ROOT, "scratch", f"logo-{T.name}-{px_h}.png")
    if not os.path.exists(out):
        subprocess.run(["/usr/bin/rsvg-convert", "-h", str(px_h), T.logo, "-o", out], check=True)
        if T.kind != "msn":
            im = Image.open(out).convert("RGBA")
            al = np.asarray(im.getchannel("A")) > 8
            cols = al.any(axis=0)
            # the mark ends at the first gap wider than a twelfth of the height (before the wordmark)
            x, gap = int(np.argmax(cols)), 0
            while x < im.width and gap < im.height // 12:
                gap = 0 if cols[x] else gap + 1
                x += 1
            x -= gap
            im.crop((0, 0, x, im.height)).save(out)
    return out


# ------------------------------------------------------------------------------------------
# Shared drawing: gloss, fields, buttons, tracks, knobs
# ------------------------------------------------------------------------------------------


def gloss_fill(h, w, stops):
    """Four stops: the top half runs s0->s1, then a hard split, the bottom half s2->s3."""
    g = np.zeros((h, w, 3), dtype=np.float32)
    top = max(1, h // 2)
    g[:top] = vgrad(top, stops[:2], w)
    g[top:] = vgrad(h - top, stops[2:], w)
    return g


def gbox(a, x, y, w, h, r, stops, edge=None, alpha=1.0):
    """A rounded box filled with gloss_fill (or a plain colour); edge a 1px rim."""
    if w <= 0 or h <= 0:
        return
    H, W = a.shape[:2]
    if edge is not None:
        paint(a, 0, 0, rr_mask(W, H, r, x, y, w, h), edge, alpha)
        m = rr_mask(W, H, max(0.0, r - 1), x + 1, y + 1, w - 2, h - 2)
        fy, fh = y + 1, h - 2
    else:
        m = rr_mask(W, H, r, x, y, w, h)
        fy, fh = y, h
    if isinstance(stops, list):
        fy0 = int(np.floor(fy))
        fh = max(1, int(np.ceil(fy + fh)) - fy0)
        fy = fy0
        g = np.zeros((H, W, 3), dtype=np.float32)
        y0, y1 = max(0, fy), min(H, fy + fh)
        gf = gloss_fill(fh, W, stops) if len(stops) == 4 else vgrad(fh, stops, W)
        g[y0:y1] = gf[y0 - fy:y1 - fy]
        if fy > 0:
            g[:y0] = gf[0]
        if y1 < H:
            g[y1:] = gf[-1]
        paint(a, 0, 0, m, g, alpha)
    else:
        paint(a, 0, 0, m, stops, alpha)


def frame_stops(lit):
    return T.frame_lit if lit else T.frame_dim


def frame_colour_at(row, lit, h=14):
    return ramp(frame_stops(lit), (row + 0.5) / h)


def frame_bg(a, x, y, w, h, lit):
    vfill(a, x, y, w, h, frame_stops(lit))


def field(a, x, y, w, h):
    """A white display field; the inside is (x, y, w, h)."""
    gbox(a, x - 1, y - 1, w + 2, h + 2, T.disp_r, T.disp, T.disp_edge)
    if T.kind == "msn":
        rect(a, x + 1, y, w - 2, 1, lerp(T.disp, T.disp_edge, 0.2))


def button_face(a, x, y, w, h, pressed, on=False, r=None):
    if r is None:
        r = {"msn": min(h / 2 - 0.01, 6), "o7": 2.5, "o10": 1.5}[T.kind]
    if pressed:
        stops, edge = T.btn_down, T.btn_down_edge
    elif on:
        stops, edge = T.btn_on, T.btn_on_edge
    else:
        stops, edge = T.btn, T.btn_edge
    gbox(a, x, y, w, h, r, stops, edge)
    if T.kind != "o10" and not pressed:
        rect(a, x + int(r) + 1, y + 1, w - 2 * int(r) - 2, 1, lerp(stops[0], WHITE, 0.7))


def track_h(a, x, y, w, th, fill_from=None, fill_to=None, colour=None):
    """A horizontal groove th tall; accent fill between fill_from..fill_to (absolute x)."""
    W, H = a.shape[1], a.shape[0]
    r = th / 2 if T.kind == "msn" else (1.0 if T.kind == "o7" else 0.0)
    paint(a, 0, 0, rr_mask(W, H, r, x, y, w, th), T.track_edge)
    inner = rr_mask(W, H, max(0, r - 1), x + 1, y + 1, w - 2, th - 2)
    paint(a, 0, 0, inner, T.track)
    if T.kind == "msn":
        sh = inner.copy()
        sh[y + 2:, :] = 0
        paint(a, 0, 0, sh, lerp(T.track, T.track_edge, 0.35))
    if fill_from is not None and fill_to is not None and fill_to > fill_from:
        f = inner.copy()
        f[:, :max(0, int(fill_from))] = 0
        f[:, max(0, int(fill_to)):] = 0
        col = colour or T.accent
        if T.kind == "o10":
            g = col
        else:
            g = vgrad(H, [lerp(col, WHITE, 0.45), col, lerp(col, BLACK, 0.1)], W)
        paint(a, 0, 0, f, g)


def track_v(a, x, y, h, tw, fill_from=None):
    W, H = a.shape[1], a.shape[0]
    r = tw / 2 if T.kind == "msn" else (1.0 if T.kind == "o7" else 0.0)
    paint(a, 0, 0, rr_mask(W, H, r, x, y, tw, h), T.track_edge)
    inner = rr_mask(W, H, max(0, r - 1), x + 1, y + 1, tw - 2, h - 2)
    paint(a, 0, 0, inner, T.track)
    if fill_from is not None:
        f = inner.copy()
        f[:int(fill_from), :] = 0
        col = T.accent
        g = col if T.kind == "o10" else np.broadcast_to(
            np.array([lerp(col, WHITE, 0.4), col, lerp(col, BLACK, 0.1)], np.float32)[
                np.clip((np.arange(W) - x) * 3 // max(1, tw), 0, 2)][None, :, :], (H, W, 3)).copy()
        paint(a, 0, 0, f, g)


def knob(a, x, y, w, h, pressed, r=None):
    stops = T.knob_down if pressed else T.knob
    edge = T.knob_edge_down if pressed else T.knob_edge
    if r is None:
        r = {"msn": min(w, h) / 2 - 0.01, "o7": 2.0, "o10": 1.0}[T.kind]
    gbox(a, x, y, w, h, r, stops, edge)


def buddy(a, x, y, h, col, alpha=1.0):
    """A Messenger buddy (head and shoulders), h tall, its box's top left at (x, y); glossy."""
    W, H = a.shape[1], a.shape[0]
    hd = h * 0.46
    bw = h * 0.92
    cx = x + bw / 2
    cut = min(H, int(np.ceil(y + h)))

    def clip(m):
        m = m.copy()
        m[cut:] = 0
        return m
    dark = lerp(col, BLACK, 0.35)
    paint(a, 0, 0, ellipse_mask(W, H, cx - hd / 2, y, hd, hd), dark, alpha)
    paint(a, 0, 0, clip(rr_mask(W, H, bw * 0.45, x, y + hd * 0.92, bw, bw * 0.9)), dark, alpha)
    paint(a, 0, 0, ellipse_mask(W, H, cx - hd / 2 + 0.6, y + 0.6, hd - 1.2, hd - 1.2), col, alpha)
    paint(a, 0, 0, clip(rr_mask(W, H, bw * 0.4, x + 0.7, y + hd * 0.92 + 0.7, bw - 1.4, bw * 0.9)), col, alpha)
    hi = lerp(col, WHITE, 0.6)
    paint(a, 0, 0, ellipse_mask(W, H, cx - hd * 0.3, y + hd * 0.12, hd * 0.4, hd * 0.32), hi, 0.8 * alpha)


def status_dot(a, cx, cy, d, col):
    """A glossy round status dot (online green, busy red)."""
    W, H = a.shape[1], a.shape[0]
    paint(a, 0, 0, ellipse_mask(W, H, cx - d / 2, cy - d / 2, d, d), lerp(col, BLACK, 0.35))
    paint(a, 0, 0, ellipse_mask(W, H, cx - d / 2 + 0.6, cy - d / 2 + 0.6, d - 1.2, d - 1.2), col)
    paint(a, 0, 0, ellipse_mask(W, H, cx - d * 0.28, cy - d * 0.4, d * 0.5, d * 0.36), WHITE, 0.6)


# ------------------------------------------------------------------------------------------
# Titlebar pieces: caption buttons, the options button (buddy / Office Button / Word icon), QAT
# ------------------------------------------------------------------------------------------


def caption_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 caption buttons: minimize, shade, close (options is drawn by options_button)."""
    W, H = a.shape[1], a.shape[0]
    if kind == "options":
        options_button(a, x, y, lit, pressed)
        return
    if T.kind == "msn":
        if kind == "close":
            stops = ([(250, 170, 150), (232, 96, 70), (200, 52, 30), (226, 90, 64)] if not pressed else
                     [(200, 60, 40), (176, 40, 24), (160, 30, 16), (190, 56, 36)])
            if not lit:
                stops = [lerp(c, (220, 226, 236), 0.6) for c in stops]
            gbox(a, x, y, 9, 9, 2, stops, (150, 50, 40) if lit else (170, 170, 186))
            ink = WHITE
        else:
            stops = T.btn_down if pressed else T.btn
            gbox(a, x, y, 9, 9, 2, stops, T.btn_edge if lit else (170, 182, 204))
            ink = WHITE if pressed else ((30, 64, 128) if lit else (130, 146, 172))
    else:
        if pressed:
            if kind == "close":
                gbox(a, x, y, 9, 9, 1 if T.kind == "o7" else 0,
                     [(240, 140, 120), (214, 70, 50), (196, 44, 24), (226, 100, 80)] if T.kind == "o7"
                     else [(212, 64, 48), (212, 64, 48), (200, 50, 36), (200, 50, 36)], (150, 50, 40))
            else:
                gbox(a, x, y, 9, 9, 1 if T.kind == "o7" else 0, T.btn_down, T.btn_down_edge)
        if T.kind == "o7":
            ink = (60, 86, 130) if lit else (130, 150, 180)
        else:
            ink = (70, 76, 86) if lit else (150, 154, 160)
        if pressed and kind == "close":
            ink = WHITE
    if kind == "minimize":
        rect(a, x + 2, y + 6, 5, 2 if T.kind != "o10" else 1, ink)
    elif kind == "shade":
        rect(a, x + 2, y + 2, 5, 2, ink)
        rect(a, x + 2, y + 4, 1, 3, ink)
        rect(a, x + 6, y + 4, 1, 3, ink)
        rect(a, x + 2, y + 6, 5, 1, ink)
    elif kind == "close":
        wd = 1.3 if T.kind == "o10" else 1.5
        paint(a, 0, 0, line_mask(W, H, [(x + 2.1, y + 2.1), (x + 6.9, y + 6.9)], wd), ink)
        paint(a, 0, 0, line_mask(W, H, [(x + 6.9, y + 2.1), (x + 2.1, y + 6.9)], wd), ink)


ORB_C = (10.5, 7.0)
ORB_R = 7.0


def options_button(a, x, y, lit, pressed):
    """MSN: the buddies icon; Office 2007: the Office Button (drawn whole by the bar, x/y its
    9x9 cell); Office 2010: the Word icon (window menu)."""
    W, H = a.shape[1], a.shape[0]
    if T.kind == "msn":
        if pressed:
            gbox(a, x, y, 9, 9, 2, T.btn_down, T.btn_down_edge)
        buddy(a, x + 3.6, y - 0.2, 6.6, (70, 140, 226) if lit else (150, 170, 200))
        buddy(a, x - 0.4, y + 2.0, 7.0, (60, 176, 54) if lit else (150, 186, 150))
        return
    if T.kind == "o10":
        col = T.word if not pressed else lerp(T.word, BLACK, 0.3)
        if not lit:
            col = lerp(col, (200, 206, 214), 0.45)
        # a page behind, the blue W tile in front
        gbox(a, x + 3, y, 6, 9, 0.5, (250, 251, 253), (150, 156, 166))
        for yy in (2, 4, 6):
            rect(a, x + 5, y + yy, 3, 1, (150, 170, 200))
        gbox(a, x, y + 1, 7, 7, 1, [lerp(col, WHITE, 0.25), col], lerp(col, BLACK, 0.3))
        ink = WHITE
        for r, row in enumerate(["#...#", "#...#", "#.#.#", ".#.#."]):
            for c, ch in enumerate(row):
                if ch == "#":
                    px(a, x + 1 + c, y + 3 + r, ink)
        return
    # Office 2007: the orb, centred on ORB_C relative to the bar (x, y is the 9x9 cell at 6, 3)
    ox, oy = x - 6, y - 3
    cx, cy = ox + ORB_C[0], oy + ORB_C[1]
    R = ORB_R
    paint(a, 0, 0, ellipse_mask(W, H, cx - R, cy - R, 2 * R, 2 * R), (64, 84, 124) if lit else (120, 136, 164))
    glass = [(246, 249, 255), (200, 216, 240), (150, 178, 218), (214, 230, 250)]
    if pressed:
        glass = [(255, 236, 196), (250, 190, 110), (236, 140, 50), (252, 200, 120)]
    g = np.zeros((H, W, 3), np.float32)
    top = int(round(cy))
    g[:top] = vgrad(top, glass[:2], W)
    g[top:] = vgrad(H - top, glass[2:], W)
    paint(a, 0, 0, ellipse_mask(W, H, cx - R + 0.9, cy - R + 0.9, 2 * R - 1.8, 2 * R - 1.8), g)
    logo(a, int(round(cx - 5)), int(round(cy - 5)), (10, 10), logo_png(96))
    paint(a, 0, 0, ellipse_mask(W, H, cx - 4.5, cy - R + 1.0, 9, 4.5), WHITE, 0.3)


def qat(a, x, y, lit):
    """The Quick Access Toolbar: save, undo, redo and its drop-down; returns the x after it."""
    W, H = a.shape[1], a.shape[0]
    k = 1.0 if lit else 0.45
    fl = lerp((64, 96, 168), frame_colour_at(y + 3, lit), 1 - k)
    rect(a, x, y + 1, 7, 7, fl)                       # floppy
    rect(a, x + 1, y + 1, 5, 3, lerp(WHITE, fl, 1 - k))
    rect(a, x + 2, y + 5, 3, 2, lerp((200, 210, 228), fl, 1 - k))
    blue = lerp((40, 110, 210), frame_colour_at(y + 3, lit), 1 - k)
    for i, d in enumerate((1, -1)):
        bx = x + 10 + 9 * i
        cx = bx + 3.5
        pts = [(cx + 3 * d * -1, y + 4.5), (cx - 0.5 * d * -1, y + 2.0), (cx + 2.5 * d, y + 3.0),
               (cx + 2.5 * d, y + 7.0)]
        paint(a, 0, 0, line_mask(W, H, pts[1:], 1.4), blue)
        paint(a, 0, 0, poly_mask(W, H, [(cx - 3.2 * d, y + 2.2), (cx + 0.2 * d, y + 0.2), (cx + 0.2 * d, y + 4.4)]),
              blue)
    dd = x + 29
    ink = lerp((60, 70, 90), frame_colour_at(y + 3, lit), 1 - k)
    rect(a, dd, y + 2, 5, 1, ink)
    rect(a, dd, y + 4, 5, 1, ink)
    rect(a, dd + 1, y + 5, 3, 1, ink)
    rect(a, dd + 2, y + 6, 1, 1, ink)
    return dd + 6


def title_parts(a, parts, x, y, lit):
    for s, role in parts:
        col = getattr(T, role if lit else role + "_dim") if role != "title" else (T.title_lit if lit else T.title_dim)
        x = draw_text(a, UI, s, x, y, col)
    return x


def parts_w(parts):
    return text_w(UI, "".join(s for s, _ in parts))


def office_tab(a, x, y, w, h, lit):
    """A selected ribbon tab: rounded top corners, open at the bottom into the ribbon."""
    H, W = a.shape[:2]
    edge = T.tab_edge if lit else lerp(T.tab_edge, WHITE, 0.4)
    paint(a, 0, 0, rr_mask(W, H, 2.5, x, y, w, h + 6), edge)
    g = np.zeros((H, W, 3), np.float32)
    g[:] = vgrad(H, [T.tab_top, T.tab_bot], W) if T.kind == "o7" else np.array(T.tab_top, np.float32)
    if T.kind == "o7":
        g[y:y + h] = vgrad(h, [T.tab_top, T.tab_bot], W)
        g[y + h:] = T.tab_bot
    paint(a, 0, 0, rr_mask(W, H, 1.5, x + 1, y + 1, w - 2, h + 6), g)


def tab_row(a, y, lit, sel_title, x0):
    """Ribbon tabs from x0 on a bar: (2010) the blue File tab, Home, Insert, then the selected tab."""
    H = a.shape[0]
    x = x0
    if T.kind == "o10":
        fw = text_w(UI, "File") + 10
        col = T.word if lit else lerp(T.word, (220, 224, 230), 0.35)
        gbox(a, x, y, fw, H - y + 3, 1.5, [lerp(col, WHITE, 0.2), col], lerp(col, BLACK, 0.25))
        draw_text(a, UI, "File", x + 5, y + 1, WHITE)
        x += fw + 5
    ink = T.tab_text if lit else lerp(T.tab_text, WHITE, 0.5)
    for s in T.tabs:
        draw_text(a, UI, s, x + 3, y + 1, ink)
        x += text_w(UI, s) + 9
    sw = text_w(UI, sel_title) + 10
    office_tab(a, x, y - 1, sw, H - y + 1, lit)
    draw_text(a, UI, sel_title, x + 5, y + 1, ink)
    return x + sw


def bar_frame(w, h, lit, left_edge=False, right_edge=False):
    """A titlebar strip: the frame gradient, a top highlight and side borders."""
    a = new(w, h)
    frame_bg(a, 0, 0, w, h, lit)
    edge = T.frame_edge_lit if lit else T.frame_edge_dim
    rect(a, 0, 0, w, 1, edge)
    rect(a, 0, 1, w, 1, lerp(frame_colour_at(1, lit, h), WHITE, 0.6))
    if left_edge:
        rect(a, 0, 0, 1, h, edge)
        rect(a, 1, 1, 1, h - 1, lerp(frame_colour_at(1, lit, h), WHITE, 0.6))
    if right_edge:
        rect(a, w - 1, 0, 1, h, edge)
    return a


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters, bg):
    a = bg.copy() if isinstance(bg, np.ndarray) and bg.ndim == 3 else new(8, 43, bg)
    gbox(a, 0, 0, 8, 43, 3.5 if T.kind == "msn" else (1.5 if T.kind == "o7" else 0), T.btn[:2], T.btn_edge)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            if T.kind == "msn":
                gbox(a, 1, y, 6, h, 2, [T.accent_lt, lerp(T.accent_lt, T.accent, 0.3)])
            else:
                gbox(a, 1, y, 6, h, 1 if T.kind == "o7" else 0, T.btn_on, None)
        gy = y + (h - 5) // 2
        ink = (T.accent if T.kind == "msn" else T.glyph) if on else T.label
        draw_text(a, TINY, letter, 2, gy, ink)
    return a


def main_titlebar(lit, pressed_options=False):
    a = bar_frame(275, 14, lit, left_edge=True, right_edge=True)
    if T.kind == "msn":
        # a soft white swoosh across the bar
        W, H = 275, 14
        paint(a, 0, 0, ellipse_mask(W, H, 60, -26, 260, 34), WHITE, 0.35 if lit else 0.2)
        options_button(a, 6, 3, lit, pressed_options)
        title_parts(a, T.main_title, 19, 3, lit)
    else:
        options_button(a, 6, 3, lit, pressed_options)
        qx = qat(a, 21 if T.kind == "o7" else 19, 3, lit)
        rect(a, qx + 1, 3, 1, 9, lerp(frame_colour_at(6, lit), BLACK, 0.12))
        tw = parts_w(T.main_title)
        title_parts(a, T.main_title, max(qx + 8, (275 - tw) // 2), 3, lit)
    caption_button(a, 244, 3, "minimize", lit)
    caption_button(a, 254, 3, "shade", lit)
    caption_button(a, 264, 3, "close", lit)
    return a


def make_titlebar(main):
    a = new(344, 87, T.frame_body)
    bar = main_titlebar(True)
    pbar = main_titlebar(True, pressed_options=True)
    a[0:9, 0:9] = bar[3:12, 6:15]
    a[9:18, 0:9] = pbar[3:12, 6:15]
    for kind, x in (("minimize", 9), ("close", 18)):
        src = {"minimize": 244, "close": 264}[kind]
        a[0:9, x:x + 9] = bar[3:12, src:src + 9]
        a[9:18, x:x + 9] = bar_cell_pressed(kind, src)
    a[18:27, 0:9] = bar[3:12, 254:263]
    a[18:27, 9:18] = bar_cell_pressed("shade", 254)
    a[0:14, 27:302] = bar
    a[15:29, 27:302] = main_titlebar(False)
    a[29:43, 27:302] = bar
    a[42:56, 27:302] = main_titlebar(False)
    unlit = clutter_bar("", main_clean()[22:65, 10:18])
    lit = clutter_bar("OAIDV", main_clean()[22:65, 10:18])
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = lit[y:y + h]
    return a


def bar_cell_pressed(kind, src, w=275, h=14):
    cell = bar_frame(w, h, True, left_edge=True, right_edge=True)[3:12, src:src + 9].copy()
    if T.kind == "msn":
        full = main_titlebar(True)
        cell = full[3:12, src:src + 9].copy() if w == 275 else cell
    caption_button(cell, 0, 0, kind, True, pressed=True)
    return cell


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116): the body (Messenger's window / a ribbon with groups)
# ------------------------------------------------------------------------------------------

TRAY_X, TRAY_Y, TRAY_W, TRAY_H = 16, 88, 142, 18
CB = {"previous": (0, 23), "play": (23, 23), "pause": (46, 23), "stop": (69, 23), "next": (92, 22)}
EJECT = (120, 1, 22, 16)   # within the tray canvas
GROUP_SPLIT = 161           # Office: the Playback | Options groups


def body_bg(w, h, eq=False):
    """The window body below a 14px titlebar (rows 14..h-1)."""
    a = new(w, h, T.frame_body)
    vfill(a, 0, 14, w, h - 14, T.body)
    W, H = w, h
    if T.kind == "msn" and not eq:
        # Messenger's soft swooshes
        paint(a, 0, 0, ellipse_mask(W, H, -60, 70, 420, 120), WHITE, 0.45)
        paint(a, 0, 0, ellipse_mask(W, H, 120, 84, 260, 90), lerp(T.body[2], T.accent, 0.12), 0.5)
    elif T.kind == "o7":
        if eq:
            ribbon_group(a, 3, 15, w - 6, h - 18, None)
        else:
            ribbon_group(a, 3, 15, w - 6, 70, None)
            ribbon_group(a, 3, 86, GROUP_SPLIT - 4, 28, "PLAYBACK")
            ribbon_group(a, GROUP_SPLIT, 86, w - 3 - GROUP_SPLIT, 28, "OPTIONS")
    else:
        if not eq:
            rect(a, 4, 85, w - 8, 1, (214, 218, 224))
            rect(a, 4, 86, w - 8, 1, WHITE)
            for gx in (GROUP_SPLIT - 1,):
                vfill(a, gx, 88, 1, 25, [(236, 239, 243), (196, 201, 208), (236, 239, 243)])
                vfill(a, gx + 1, 88, 1, 25, [WHITE, WHITE])
            text_center(a, TINY, "PLAYBACK", (4 + GROUP_SPLIT) // 2, 108, T.label)
            text_center(a, TINY, "OPTIONS", (GROUP_SPLIT + 271) // 2, 108, T.label)
    edge = T.frame_edge_lit
    rect(a, 0, 0, 1, h, edge)
    rect(a, w - 1, 0, 1, h, edge)
    rect(a, 0, h - 1, w, 1, edge)
    rect(a, 1, 14, 1, h - 15, lerp(T.body[0], WHITE, 0.6))
    return a


def ribbon_group(a, x, y, w, h, label):
    """An Office 2007 group: a rounded light box, its label band along the bottom."""
    gbox(a, x, y, w, h, 3, T.group, T.group_edge)
    H, W = a.shape[:2]
    inner = rr_mask(W, H, 2, x + 1, y + 1, w - 2, h - 2)
    hl = inner - rr_mask(W, H, 1.5, x + 2, y + 2, w - 4, h - 4)
    paint(a, 0, 0, np.clip(hl, 0, 1), WHITE, 0.6)
    if label:
        band = inner.copy()
        band[:y + h - 8] = 0
        g = np.zeros((H, W, 3), np.float32)
        g[y + h - 8:y + h] = vgrad(8, T.group_band, W)
        paint(a, 0, 0, band, g)
        text_center(a, TINY, label, x + w // 2, y + h - 7, T.label)


def digit(a, n, x, y, col):
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + 1 + c, y + 1 + r, col)


def tri(a, pts, col, alpha=1.0):
    paint(a, 0, 0, poly_mask(a.shape[1], a.shape[0], pts), col, alpha)


def glyph(a, kind, cx, cy, col, s=1.0):
    W, H = a.shape[1], a.shape[0]
    if kind == "previous":
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
        paint(a, 0, 0, rr_mask(W, H, 1.0, cx - 4 * s, cy - 4 * s, 8 * s, 8 * s), col)
    elif kind == "eject":
        tri(a, [(cx - 5 * s, cy + 1 * s), (cx, cy - 4.5 * s), (cx + 5 * s, cy + 1 * s)], col)
        paint(a, 0, 0, rr_mask(W, H, 0.5, cx - 5 * s, cy + 2.5 * s, 10 * s, 2 * s), col)


def tray(bg, pressed=None):
    """The transport tray (prev..next, eject) on bg (TRAY_W x TRAY_H), one button pressed."""
    a = bg.copy()
    W, H = a.shape[1], a.shape[0]
    centres = {k: (x + w / 2, H / 2) for k, (x, w) in CB.items()}
    ex, ey, ew, eh = EJECT
    centres["eject"] = (ex + ew / 2, ey + eh / 2)

    if T.kind == "msn":
        # glossy round buttons; play is the big green one; pressed ones go deep blue
        for k, (cx, cy) in centres.items():
            d = {"play": 18, "eject": 15}.get(k, 16)
            x0, y0 = cx - d / 2, cy - d / 2
            if k == pressed:
                stops, edge = T.btn_down, T.btn_down_edge
            elif k == "play":
                stops, edge = [(200, 240, 180), (110, 200, 90), (60, 160, 50), (110, 204, 96)], (40, 120, 36)
            else:
                stops, edge = T.btn, T.btn_edge
            gbox(a, x0, y0, d, d, d / 2 - 0.01, stops, edge)
            paint(a, 0, 0, ellipse_mask(W, H, x0 + d * 0.2, y0 + 1.2, d * 0.6, d * 0.38), WHITE, 0.55)
            ink = WHITE if (k == pressed or k == "play") else T.glyph
            o = 0.5 if k == pressed else 0
            if k == "play" and k != pressed:
                glyph(a, k, cx + o + 0.3, cy + o + 0.8, (30, 110, 30), 0.72)
            glyph(a, k, cx + o + (0.3 if k == "play" else 0), cy + o, ink, 0.72 if k != "eject" else 0.62)
        return a

    # Office: a joined strip of small buttons (prev..next), eject on its own
    by, bh = 1, 16
    x0s, x1s = 0, CB["next"][0] + CB["next"][1]
    r = 2.5 if T.kind == "o7" else 1.0
    gbox(a, x0s, by, x1s - x0s, bh, r, T.btn, T.btn_edge)
    inner = rr_mask(W, H, max(0, r - 1), x0s + 1, by + 1, x1s - x0s - 2, bh - 2)
    if pressed in CB:
        x, w = CB[pressed]
        seg = np.zeros((H, W), np.float32)
        seg[:, x + 1:x + w - 1] = inner[:, x + 1:x + w - 1]
        g = np.zeros((H, W, 3), np.float32)
        g[by + 1:by + bh - 1] = gloss_fill(bh - 2, W, T.btn_down)
        paint(a, 0, 0, seg, g)
        rect(a, x, by, 1, bh, T.btn_down_edge)
        rect(a, x + w - 1, by, 1, bh, T.btn_down_edge)
        rect(a, x, by, w, 1, T.btn_down_edge)
        rect(a, x, by + bh - 1, w, 1, T.btn_down_edge)
    for k in ("play", "pause", "stop", "next"):
        xd = CB[k][0]
        if pressed in (k,) or (pressed in CB and CB[pressed][0] + CB[pressed][1] == xd + 1):
            continue
        rect(a, xd, by + 2, 1, bh - 4, T.btn_edge)
        if T.kind == "o7":
            rect(a, xd + 1, by + 2, 1, bh - 4, WHITE)
    if pressed == "eject":
        gbox(a, ex, ey, ew, eh, r, T.btn_down, T.btn_down_edge)
    else:
        gbox(a, ex, ey, ew, eh, r, T.btn, T.btn_edge)
    for k, (cx, cy) in centres.items():
        o = 0.5 if k == pressed else 0
        col = T.play if k == "play" else T.glyph
        s = 0.8 if k == "play" else 0.66
        glyph(a, k, cx + o + (0.4 if k == "play" else 0), cy + o, col, s if k != "eject" else 0.6)
    return a


def about_icon(a):
    """The About spot (245..266, 86..107): the Messenger buddies / Office help / Office 2010 logo."""
    if T.kind == "msn":
        logo(a, 244, 85, (24, 23), logo_png(96))
    elif T.kind == "o7":
        W, H = a.shape[1], a.shape[0]
        cx, cy, d = 255.5, 96.5, 15
        paint(a, 0, 0, ellipse_mask(W, H, cx - d / 2, cy - d / 2, d, d), (40, 84, 160))
        paint(a, 0, 0, ellipse_mask(W, H, cx - d / 2 + 1, cy - d / 2 + 1, d - 2, d - 2), (54, 116, 208))
        paint(a, 0, 0, ellipse_mask(W, H, cx - 5, cy - 6.4, 10, 6.4), WHITE, 0.45)
        draw_text(a, UI, "?", int(cx) - 1, int(cy) - 3, WHITE)
    else:
        logo(a, 245, 86, (22, 22), logo_png(96))


def make_main():
    a = body_bg(275, 116)
    a[0:14] = main_titlebar(True)
    bg = a[30, 9]
    a[22:65, 10:18] = clutter_bar("", a[22:65, 10:18])
    field(a, 21, 20, 84, 42)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, T.digit)
    field(a, 109, 21, 159, 15)
    field(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, T.label)
    draw_text(a, TINY, "KHZ", 169, 44, T.label)
    track_h(a, 108, 61, 66, 5)
    track_h(a, 178, 61, 36, 5)
    track_h(a, 16, 74, 248, 6)
    a[TRAY_Y:TRAY_Y + TRAY_H, TRAY_X:TRAY_X + TRAY_W] = tray(a[TRAY_Y:TRAY_Y + TRAY_H, TRAY_X:TRAY_X + TRAY_W])
    about_icon(a)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons, shufrep, monoster, playpaus, numbers, text
# ------------------------------------------------------------------------------------------


def main_clean():
    a = body_bg(275, 116)
    a[0:14] = main_titlebar(True)
    return a


def make_cbuttons(main):
    a = new(136, 36, T.frame_body)
    clean = main_clean()[TRAY_Y:TRAY_Y + TRAY_H, TRAY_X:TRAY_X + TRAY_W]
    normal = tray(clean)
    for k, (x, w) in CB.items():
        a[0:18, x:x + w] = normal[:, x:x + w]
        a[18:36, x:x + w] = tray(clean, k)[:, x:x + w]
    ex, ey, ew, eh = EJECT
    a[0:16, 114:136] = normal[ey:ey + eh, ex:ex + ew]
    a[16:32, 114:136] = tray(clean, "eject")[ey:ey + eh, ex:ex + ew]
    return a


def toggle_cell(bg, w, h, label, on, pressed, toggle=True, ink=None):
    """A button; MSN toggles carry a status dot (green on, red off)."""
    a = bg.copy()
    o = 1 if pressed else 0
    if T.kind == "msn":
        button_face(a, 0, 0, w, h, pressed)
        lab = WHITE if pressed else (ink or T.glyph)
        if not toggle or not label:
            if label:
                text_center(a, TINY, label, w // 2, (h - 5) // 2 + o, lab)
            return a
        dcol = T.green if on else T.red
        tw = text_w(TINY, label)
        if h >= 15:   # dot above the label
            status_dot(a, w / 2, 4.5 + o, 5, dcol)
            text_center(a, TINY, label, w // 2 + (1 if w % 2 == 0 else 0), 8 + o, lab)
        else:
            x0 = (w - (tw + 7)) // 2
            status_dot(a, x0 + 2.5 + o, h / 2 + o * 0.5, 5, dcol)
            draw_text(a, TINY, label, x0 + 7 + o, (h - 5) // 2 + o, lab)
        return a
    button_face(a, 0, 0, w, h, pressed, on and toggle)
    if label:
        text_center(a, TINY, label, w // 2, (h - 5) // 2 + o, ink or T.glyph)
    return a


def make_shufrep(main):
    a = new(92, 85, T.frame_body)
    clean = main_clean()
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = toggle_cell(clean[89:104, 210:238], 28, 15, "REPEAT", on, pressed)
        a[y:y + 15, 28:75] = toggle_cell(clean[89:104, 164:211], 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        src = clean[58:70, 219 + (x % 46):219 + (x % 46) + 23]
        a[61:73, x:x + 23] = toggle_cell(src, 23, 12, label, False, pressed)
        a[73:85, x:x + 23] = toggle_cell(src, 23, 12, label, True, pressed)
    return a


def make_monoster():
    a = new(56, 24, T.disp)
    on_col = T.green if T.kind == "msn" else T.accent
    for y, on in ((0, True), (12, False)):
        col = on_col if on else T.txt_dim
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T.disp)
    col = (52, 150, 46) if T.kind != "o10" else T.word
    tri(a, [(2, 1), (8, 4.5), (2, 8)], col)
    rect(a, 9 + 2, 1, 2, 7, T.digit)
    rect(a, 9 + 5, 1, 2, 7, T.digit)
    rect(a, 18 + 2, 2, 5, 5, (200, 60, 44) if T.kind == "msn" else T.digit)
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
    clean = main_clean()
    track_h(clean, 16, 74, 248, 6)
    a[0:10, 0:248] = clean[72:82, 16:264]
    for x0, sel in ((248, False), (278, True)):
        t = clean[72:82, 16 + 100:16 + 129].copy()
        track_h(t, -20, 2, 69, 6, fill_from=0, fill_to=14)
        if T.kind == "msn":
            buddy(t, 10, 0, 10, (64, 132, 222) if sel else (58, 172, 52))
        elif T.kind == "o7":
            knob(t, 9, 0, 11, 10, sel)
            for gx in (12, 14, 16):
                rect(t, gx, 3, 1, 4, lerp(T.knob_edge_down if sel else T.knob_edge, WHITE, 0.3))
        else:
            knob(t, 10, 0, 9, 10, sel)
        a[0:10, x0:x0 + 29] = t
    return a


def slider_thumbs(a, seat):
    for x, sel in ((0, True), (15, False)):
        t = seat[1:12, 20:34].copy()
        track_h(t, -10, 4, 40, 5, fill_from=0, fill_to=7)
        if T.kind == "msn":
            knob(t, 1, 0, 11, 11, sel)
            paint(t, 0, 0, ellipse_mask(14, 11, 3.5, 1.2, 6, 3.5), WHITE, 0.6)
        elif T.kind == "o7":
            knob(t, 3, 0, 8, 11, sel)
        else:
            knob(t, 3, 0, 7, 11, sel)
        a[422:433, x:x + 14] = t


def make_volume(main):
    a = new(68, 433, T.frame_body)
    clean = main_clean()
    seat = clean[57:72, 107:175]
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
    clean = main_clean()
    seat = clean[57:72, 177:215]
    for i in range(28):
        y = i * 15
        t = seat.copy()
        reach = round(17 * i / 27)
        track_h(t, 1, 4, 36, 5, fill_from=19 - max(1, reach), fill_to=19 + max(1, reach),
                colour=T.accent if i else T.label)
        a[y:y + 15, 9:47] = t
        a[y:y + 15, 0:9] = seat[:, :1]
        a[y:y + 15, 47:68] = seat[:, -1:]
    slider_thumbs(a, clean[57:72, 107:175])
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = bar_frame(275, 14, lit, left_edge=True, right_edge=True)
    if T.kind == "msn":
        paint(a, 0, 0, ellipse_mask(275, 14, 60, -26, 260, 34), WHITE, 0.35 if lit else 0.2)
        buddy(a, 6.2, 3.4, 7.4, (60, 176, 54) if lit else (150, 186, 150))
        title_parts(a, [(T.eq_title, "title")], 18, 3, lit)
    else:
        tab_row(a, 3, lit, T.eq_title, 5)
    caption_button(a, 264, 3, "close", lit)
    return a


def eq_frame_bg():
    return body_bg(275, 116, eq=True)


def eq_slider_frame(bg, n):
    a = bg.copy()
    v = n / 27
    centre = round((1 - v) * 51) + 5
    track_v(a, 5, 1, 61, 4, fill_from=centre)
    return a


def eq_thumb(bg, pressed):
    a = bg.copy()
    track_v(a, 4, -20, 60, 4, fill_from=5)
    if T.kind == "msn":
        knob(a, 0, 0, 11, 11, pressed)
        paint(a, 0, 0, ellipse_mask(11, 11, 2.5, 1.2, 6, 3.5), WHITE, 0.6)
    else:
        knob(a, 0, 2, 11, 7, pressed)
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
    rect(a, 40, 39, 1, 60, lerp(T.body[1], T.edge_lo, 0.6))
    for x, w, lbl in ((14, 26, "ON"), (40, 32, "AUTO")):
        a[18:30, x:x + w] = toggle_cell(base[18:30, x:x + w], w, 12, lbl, False, False)
    a[18:30, 217:261] = toggle_cell(base[18:30, 217:261], 44, 12, "PRESETS", False, False, toggle=False)

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
        a[y:y + 12, 224:268] = toggle_cell(base[18:30, 217:261], 44, 12, "PRESETS", False, pressed, toggle=False)
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
    cell = eq_titlebar(True)[3:12, 264:273].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    return cell


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------


def bar20(w, lit, left_edge=False, right_edge=False):
    a = bar_frame(w, 20, lit, left_edge, right_edge)
    rect(a, 0, 19, w, 1, T.frame_body)
    return a


def side_tile(w, h, left):
    t = new(w, h, T.frame_body)
    if left:
        rect(t, 0, 0, 1, h, T.frame_edge_lit)
        rect(t, 1, 0, 1, h, lerp(T.frame_body, WHITE, 0.6))
        rect(t, w - 1, 0, 1, h, lerp(T.frame_body, T.edge_lo, 0.8))
    else:
        rect(t, w - 1, 0, 1, h, T.frame_edge_lit)
        rect(t, 0, 0, 1, h, lerp(T.frame_body, WHITE, 0.6))
    return t


def scroll_groove_col():
    return lerp(T.frame_body, WHITE, 0.45)


def scroll_handle(pressed):
    t = new(8, 18, scroll_groove_col())
    gbox(t, 0, 0, 8, 18, 3.5 if T.kind == "msn" else (1.5 if T.kind == "o7" else 0),
         T.btn_down if pressed else T.btn, T.btn_down_edge if pressed else T.btn_edge)
    for gy in (6, 8, 10):
        rect(t, 2, gy, 4, 1, T.btn_down_edge if pressed else T.btn_edge)
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
    """The 100px title piece: a ribbon tab (Office), or the title beside a buddy (Messenger)."""
    t = bar20(100, lit)
    if T.kind == "msn":
        paint(t, 0, 0, ellipse_mask(100, 20, -40, -20, 180, 30), WHITE, 0.3 if lit else 0.15)
        tw = text_w(UI, T.pl_title)
        x0 = 50 - (tw + 11) // 2
        buddy(t, x0, 5.4, 8, (60, 176, 54) if lit else (150, 186, 150))
        title_parts(t, [(T.pl_title, "title")], x0 + 11, 5, lit)
    else:
        office_tab(t, 0, 4, 100, 15, lit)
        title_parts(t, [(T.pl_title, "title")], 50 - text_w(UI, T.pl_title) // 2, 7, lit)
    return t


def make_pledit():
    a = new(280, 186, T.frame_body)
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar20(25, lit)
        a[y:y + 20, 0:25] = bar20(25, lit, left_edge=True)
        a[y:y + 20, 26:126] = title_piece_pl(lit)
        t = bar20(25, lit, right_edge=True)
        caption_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    a[42:71, 0:12] = side_tile(12, 29, True)
    t = side_tile(20, 29, False)
    rect(t, 5, 0, 8, 29, scroll_groove_col())
    rect(t, 4, 0, 1, 29, lerp(T.frame_body, T.edge_lo, 0.8))
    rect(t, 13, 0, 1, 29, lerp(T.frame_body, WHITE, 0.5))
    a[42:71, 31:51] = t
    cell = bar20(25, True, right_edge=True)[3:12, 14:23].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = cell
    a[53:71, 52:60] = scroll_handle(False)
    a[53:71, 61:69] = scroll_handle(True)

    def bottom_base(w):
        t = new(w, 38, T.frame_body)
        vfill(t, 0, 0, w, 38, [lerp(T.frame_body, WHITE, 0.35), T.frame_body])
        rect(t, 0, 0, w, 1, lerp(T.frame_body, T.edge_lo, 0.8))
        rect(t, 0, 1, w, 1, lerp(T.frame_body, WHITE, 0.6))
        rect(t, 0, 37, w, 1, T.frame_edge_lit)
        return t

    t = bottom_base(125)
    lab = None
    if T.kind == "o10":
        # Backstage: the blue File panel with its white commands
        vfill(t, 0, 1, 125, 36, T.backstage)
        rect(t, 0, 0, 125, 1, lerp(T.word, BLACK, 0.25))
        lab = WHITE
    rect(t, 0, 0, 1, 38, T.frame_edge_lit)
    if T.kind != "o10":
        rect(t, 1, 1, 1, 36, lerp(T.frame_body, WHITE, 0.6))
    rect(t, 0, 0, 12, 1, T.frame_body if T.kind != "o10" else lerp(T.word, BLACK, 0.25))
    rect(t, 0, 0, 1, 1, T.frame_edge_lit)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        if T.kind == "o10":
            seg = t[8:26, bx:bx + 22]
            gbox(seg, 0, 0, 22, 18, 0, [(255, 255, 255)], None, alpha=0.14)
            rect(seg, 0, 17, 22, 1, lerp(T.word, WHITE, 0.35))
            text_center(seg, TINY, lbl, 11, 7, WHITE)
        else:
            t[8:26, bx:bx + 22] = toggle_cell(t[8:26, bx:bx + 22], 22, 18, lbl, False, False, toggle=False)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, T.frame_edge_lit)
    rect(t, 130, 0, 19, 1, T.frame_body)
    field(t, 6, 9, 56, 8)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        mini_transport_icon(t, kind, 3 + 10 * k, 22, T.glyph)
    field(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, T.label)
    rect(t, 84, 22 + 5, 1, 1, T.label)
    t[8:26, 106:128] = toggle_cell(t[8:26, 106:128], 22, 18, "LIST", False, False, toggle=False)
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 31 - 3 * j
            px(t, gx, gy, T.label)
            px(t, gx + 1, gy + 1, WHITE)
    a[72:110, 126:276] = t

    a[0:38, 179:204] = bottom_base(25)
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_bottom(w, grip, left_edge):
    t = new(w, 14, T.frame_body)
    rect(t, 0, 13, w, 1, T.frame_edge_lit)
    if left_edge:
        rect(t, 0, 0, 1, 14, T.frame_edge_lit)
        rect(t, 1, 0, 1, 13, lerp(T.frame_body, WHITE, 0.6))
    else:
        rect(t, w - 1, 0, 1, 14, T.frame_edge_lit)
    if grip:
        for k in range(3):
            for j in range(k + 1):
                gx, gy = w - 4 - 3 * k + 3 * j, 9 - 3 * j
                px(t, gx, gy, T.label)
                px(t, gx + 1, gy + 1, WHITE)
    return t


TAB_Y_GEN = 3
TAB_H_GEN = 16


def make_gen():
    a = new(194, 109, T.frame_body)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, t):
            a[y:y + 20, px0:px0 + 25] = t

        piece(0, bar20(25, lit, left_edge=True))
        for px0, tx, tw in ((26, 16, 200), (52, -100, 300), (78, -191, 200)):
            t = bar20(25, lit)
            if T.gen_tab:
                office_tab(t, tx, TAB_Y_GEN, tw, TAB_H_GEN, lit)
            piece(px0, t)
        piece(104, bar20(25, lit))
        t = bar20(25, lit, right_edge=True)
        caption_button(t, 14, 3, "close", lit)
        piece(130, t)

    a[42:56, 0:125] = gen_bottom(125, False, True)
    a[57:71, 0:125] = gen_bottom(125, True, False)
    a[72:86, 127:152] = new(25, 14, T.frame_body)
    rect(a, 127, 85, 25, 1, T.frame_edge_lit)
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = side_tile(w, h, left)
    cell = bar20(25, True, right_edge=True)[3:12, 14:23].copy()
    caption_button(cell, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = cell

    # letters: each row starts at x 1, each letter in its own cell, 1px separators of x 0's colour;
    # a cell's background is the centre piece's own rows 4..10, so the letters sit on the tab
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        centre = a[(0 if lit else 21) + 4:(0 if lit else 21) + 11, 60].copy()
        col = T.title_lit if lit else T.title_dim
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
# genex.bmp, text files
# ------------------------------------------------------------------------------------------


def genex_colours():
    sel = rgb(T.pledit["SelectedBG"])
    return [WHITE, BLACK, T.frame_body, (20, 24, 32), (20, 24, 32), lerp(T.frame_body, T.edge_lo, 0.7),
            sel, lerp(T.body[0], WHITE, 0.4), T.glyph, WHITE, T.edge_lo, T.btn_down_edge,
            T.frame_body, T.btn[1], T.btn_edge, T.btn_down[1], T.accent, T.track]


def make_genex():
    a = new(256, 64, T.frame_body)
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    a[1:16, 0:47] = toggle_cell(new(47, 15, T.frame_body), 47, 15, "", False, False, toggle=False)
    a[16:31, 0:47] = toggle_cell(new(47, 15, T.frame_body), 47, 15, "", False, True, toggle=False)
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
                f"SelectedBG={p['SelectedBG']}\nMbBG={p['NormalBG']}\nMbFG={p['Normal']}\nFont={p['Font']}\n")
    name = T.wsz[:-4]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{name} — a skin in the style of {T.subject}.\n"
            f"{T.app} logo © {T.owner}.\n\n"
            "A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py) from\n"
            "gradients, shapes and hand-made pixel fonts, except the logo.\n"
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
    for p in ("/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def text_ink():
    """text.bmp's ink as the app takes it: the commonest colour of the letter rows far from the
    space cell's background (the main window's TrueType title is drawn in it)."""
    t = np.asarray(SHEETS["text"].convert("RGB"), dtype=np.int32)[:12, :155]
    bg = t[0, 150]
    far = np.abs(t - bg).sum(axis=2) >= 96
    keys, counts = np.unique((t[far] * [65536, 256, 1]).sum(axis=1), return_counts=True)
    k = int(keys[np.argmax(counts)])
    return (k >> 16, (k >> 8) & 255, k & 255)


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
    ImageDraw.Draw(box).text((0, 3 + 2 + 2), state["title"], fill=text_ink(), font=tt_font(11),
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
    c0, c1 = np.array(lerp(T.accent, WHITE, 0.8), np.float32), np.array(T.accent, np.float32)
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
             title=f"{T.wsz[:-4]} - a personal skin, private use", bars=bars)
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
        for k, t in THEMES.items():
            print(f"{k:12s} {t.wsz:20s} {t.subject}")
        sys.exit(0)
    for theme in (args or list(THEMES)):
        use_theme(theme)
        names = build()
        preview()
        print(f"{T.wsz}: {', '.join(n for n in names)}")
