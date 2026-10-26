#!/usr/bin/python3
"""Web Nostalgia: classic Winamp 2.x skins in the style of three 2000s websites.

Forked from skins/ember/gen_skin.py (same sheets, same layouts, same preview logic), with one
theme per site:

    myspace         MySpace, circa 2005-2007: the blue header, light-blue boxes, orange headers,
                    the dark music-player bar
    facebook-2006   early Facebook: the #3b5998 bar, #d8dfea section headers, flat blue buttons
    neopets         Neopets, circa 2003-2008: sky-blue header, yellow tiled pattern, rounded
                    orange-trimmed panels, bubbly lettering, a gold NP coin

    /usr/bin/python3 -I gen_skin.py                 # every theme
    /usr/bin/python3 -I gen_skin.py neopets         # just this one
    /usr/bin/python3 -I gen_skin.py --list

Everything is drawn here from code, except each site's wordmark (once, in the main titlebar),
which is rasterised at build time from source/logo-*/ (see README.md). Private use only.
Each theme writes its sheets into out/<theme>/, zips them flat into <Name>.wsz and draws
preview-<theme>.png beside this script.
"""

import os
import subprocess
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py, which finishes each .wsz
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(HERE, "out", "scratch")
SEP = (255, 0, 255)          # gen.bmp letter separators (never shown)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def H(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    if n == 0:
        return stops[0]
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    "myspace": dict(
        name="MySpace", company="Myspace LLC (formerly MySpace, Inc.)", wsz="MySpace.wsz",
        logo="myspace",
        body=WHITE, panel=H("d5e8fb"), panel2=H("b1d0f0"), border=H("6698cb"), dark=H("003399"),
        nav=H("6698cb"), bar_dim=H("6b7fae"), nav_dim=H("a9bcd6"),
        bar_ink=WHITE, bar_ink_dim=H("d8e0ee"),
        accent=H("ff6600"), accent_bg=H("ffcc99"),
        # the music player: a dark bar with white text
        disp=H("262626"), disp_rim=H("6698cb"), ink=WHITE, ink_dim=H("4a4a4a"), ink_mid=H("9fc3e8"),
        btn=WHITE, btn_pr=H("b1d0f0"), btn_rim=H("6698cb"), btn_ink=H("003399"), btn_ink_pr=H("003399"),
        tog_on=H("ff6600"), tog_off=H("336699"),
        label=H("336699"),
        track=H("e8f1fb"), track_rim=H("6698cb"), level=[H("b1d0f0"), H("6698cb"), H("003399")],
        thumb=[H("ffffff"), H("c9c9c9")], thumb_pr=[H("ffe0c2"), H("ff9933")], thumb_rim=H("666666"),
        vis_ramp=[H("ffcc99"), H("ff9933"), H("6698cb"), H("336699"), H("003399")],
        osc=[H("ffffff"), H("cfe2f3"), H("9fc3e8"), H("6698cb"), H("336699")], peak=H("ff9933"),
        pledit=("#000000", "#003399", "#FFFFFF", "#CFE2F3"),
        genex=dict(item_bg=WHITE, item_fg=BLACK, win_bg=H("ffffff"), btn_fg=H("003399"), win_fg=BLACK,
                   divider=H("6698cb"), sel=H("cfe2f3"), head_bg=H("ffcc99"), head_fg=H("ff6600"),
                   head_hi=WHITE, head_lo=H("6698cb"), head_pr=H("b1d0f0"), dead=WHITE,
                   sb=H("d5e8fb"), sb2=H("6698cb"), sb_pr=H("b1d0f0"), sb_pr2=H("003399"), sb_dead=WHITE),
        art=(H("6698cb"), H("003399")),
    ),
    "facebook-2006": dict(
        name="Facebook-2006", company="Meta Platforms, Inc. (Facebook)", wsz="Facebook-2006.wsz",
        logo="facebook",
        body=WHITE, panel=H("f7f7f7"), panel2=H("d8dfea"), border=H("bdc7d8"), dark=H("3b5998"),
        nav=H("3b5998"), bar_dim=H("6d84b4"), nav_dim=H("6d84b4"),
        bar_ink=WHITE, bar_ink_dim=H("dfe4ee"),
        accent=H("3b5998"), accent_bg=H("d8dfea"),
        disp=WHITE, disp_rim=H("bdc7d8"), ink=H("333333"), ink_dim=H("eceff5"), ink_mid=H("808080"),
        btn=H("3b5998"), btn_pr=H("29447e"), btn_rim=None, btn_ink=WHITE, btn_ink_pr=WHITE,
        btn_hi=H("d9dfea"), btn_lo=H("0e1f5b"),
        tog_on=WHITE, tog_off=H("7f93bd"),
        label=H("3b5998"),
        track=H("eceff5"), track_rim=H("bdc7d8"), level=[H("d8dfea"), H("6d84b4"), H("3b5998")],
        thumb=[H("3b5998"), H("3b5998")], thumb_pr=[H("29447e"), H("29447e")], thumb_rim=None,
        vis_ramp=[H("d8dfea"), H("afbdd4"), H("6d84b4"), H("3b5998"), H("29447e")],
        osc=[H("3b5998"), H("4d68a1"), H("6d84b4"), H("8fa1c7"), H("afbdd4")], peak=H("29447e"),
        pledit=("#333333", "#3B5998", "#FFFFFF", "#D8DFEA"),
        genex=dict(item_bg=WHITE, item_fg=H("333333"), win_bg=H("f7f7f7"), btn_fg=WHITE, win_fg=H("333333"),
                   divider=H("d8dfea"), sel=H("d8dfea"), head_bg=H("d8dfea"), head_fg=H("3b5998"),
                   head_hi=WHITE, head_lo=H("3b5998"), head_pr=H("afbdd4"), dead=H("f7f7f7"),
                   sb=H("eceff5"), sb2=H("6d84b4"), sb_pr=H("d8dfea"), sb_pr2=H("3b5998"), sb_dead=H("f7f7f7")),
        art=(H("d8dfea"), H("3b5998")),
    ),
    "neopets": dict(
        name="Neopets", company="Neopets, Inc.", wsz="Neopets.wsz",
        logo="neopets",
        body=H("fff1a8"), body_dot=H("ffe27a"), panel=H("fffbe0"), panel2=H("ffcc00"), border=H("cc6600"),
        dark=H("1f6fd0"), sky=[H("1f6fd0"), H("5fb0ff")], sky_dim=[H("7d93ad"), H("a9bccf")],
        bar_ink=WHITE, bar_ink_dim=H("e6ecf2"), outline=H("000066"), outline_dim=H("5d6680"),
        accent=H("cc6600"), accent_bg=H("ffcc00"),
        disp=H("fffbe0"), disp_rim=H("cc6600"), ink=H("000066"), ink_dim=H("f6e7b0"), ink_mid=H("cc6600"),
        btn=H("3d7fe0"), btn_top=H("8fc4ff"), btn_pr=H("1f55b0"), btn_rim=H("000066"), btn_ink=WHITE,
        btn_ink_pr=H("ffe066"),
        tog_on=H("660000"), tog_off=H("000066"),
        label=H("000066"),
        track=H("fffbe0"), track_rim=H("cc6600"), level=[H("33cc33"), H("ffcc00"), H("ff6600"), H("e8261c")],
        thumb=[H("fff6b0"), H("ffbf1f")], thumb_pr=[H("ffe0a0"), H("ff8a00")], thumb_rim=H("000066"),
        vis_ramp=[H("e8261c"), H("ff8a00"), H("ffcc00"), H("33cc33"), H("1f6fd0")],
        osc=[H("1f6fd0"), H("3d7fe0"), H("33aa33"), H("ff8a00"), H("e8261c")], peak=H("cc00cc"),
        pledit=("#000066", "#CC6600", "#FFFBE0", "#FFE080"),
        genex=dict(item_bg=H("fffbe0"), item_fg=H("000066"), win_bg=H("fff1a8"), btn_fg=WHITE, win_fg=H("000066"),
                   divider=H("cc6600"), sel=H("ffe080"), head_bg=H("ffcc00"), head_fg=H("000066"),
                   head_hi=H("fff6b0"), head_lo=H("cc6600"), head_pr=H("ff9900"), dead=H("fff1a8"),
                   sb=H("fffbe0"), sb2=H("3d7fe0"), sb_pr=H("ffe080"), sb_pr2=H("1f55b0"), sb_dead=H("fff1a8")),
        art=(H("ffe080"), H("ff8a00")),
    ),
}
THEME_KEYS = list(THEMES)
T = None
KEY = None
OUT = None

# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def new(w, h, col=WHITE):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):y + h, max(0, x):x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def frame(a, x, y, w, h, col):
    rect(a, x, y, w, 1, col)
    rect(a, x, y + h - 1, w, 1, col)
    rect(a, x, y, 1, h, col)
    rect(a, x + w - 1, y, 1, h, col)


def bevel(a, x, y, w, h, hi, lo):
    rect(a, x, y, w, 1, hi)
    rect(a, x, y, 1, h, hi)
    rect(a, x, y + h - 1, w, 1, lo)
    rect(a, x + w - 1, y, 1, h, lo)


def vgrad(a, x, y, w, h, top, bot):
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(top, bot, r / max(1, h - 1)))


def round_mask(w, h, r):
    m = np.ones((h, w), dtype=bool)
    for i in range(r):
        inset = r - i if r == 1 else [2, 1, 0][i] if r == 2 else [3, 1, 1][i]
        m[i, :inset] = False
        m[i, w - inset:] = False
        m[h - 1 - i, :inset] = False
        m[h - 1 - i, w - inset:] = False
    return m


def rrect(a, x, y, w, h, fill, border=None, r=2, grad=None):
    """Rounded rectangle; fill is a colour, or grad=(top, bottom) a vertical gradient."""
    m = round_mask(w, h, r)
    sub = a[y:y + h, x:x + w]
    if grad:
        for k in range(h):
            row = lerp(grad[0], grad[1], k / max(1, h - 1))
            sub[k][m[k]] = row
    else:
        sub[m] = fill
    if border is not None:
        e = m.copy()
        e[1:, :] &= m[:-1, :]
        e[:-1, :] &= m[1:, :]
        e[:, 1:] &= m[:, :-1]
        e[:, :-1] &= m[:, 1:]
        e[0, :] = e[-1, :] = False
        e[:, 0] = e[:, -1] = False
        sub[m & ~e] = border


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def sparkle(a, x, y, col):
    """A small four-point glitter star."""
    px(a, x, y, WHITE)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        px(a, x + dx, y + dy, col)


STAR_BIG = ["...#...", "..###..", "#######", ".#####.", "..###..", ".##.##.", ".#...#."]
STAR_SMALL = ["..#..", ".###.", "#####", ".###.", ".#.#."]


def star(a, x, y, big, lit=True):
    """A yellow five-point star with a dark outline, centred on (x, y)."""
    g = STAR_BIG if big else STAR_SMALL
    n = len(g)
    m = np.array([[c == "#" for c in row] for row in g])
    o = np.zeros((n + 2, n + 2), bool)
    for dy in range(3):
        for dx in range(3):
            o[dy:dy + n, dx:dx + n] |= m
    fill = H("ffe600") if lit else H("d6d6c8")
    line = BLACK if lit else H("4a4f5a")
    for r in range(n + 2):
        for c in range(n + 2):
            inside = 1 <= r <= n and 1 <= c <= n and m[r - 1, c - 1]
            if inside:
                px(a, x - n // 2 + c - 1, y - n // 2 + r - 1, fill)
            elif o[r, c]:
                px(a, x - n // 2 + c - 1, y - n // 2 + r - 1, line)


# ------------------------------------------------------------------------------------------
# Pixel fonts (all designed for these skins)
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
    "|": G("#", "#", "#", "#", "#"),
    " ": G("..", "..", "..", "..", ".."),
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
    "!": G("#", "#", "#", ".", "#"),
    "|": G("#", "#", "#", "#", "#"),
    "'": G("#", "#", ".", ".", "."),
    "*": G("#.#", ".#.", "#.#", "...", "..."),
}
for _c in "0123456789+-.:":
    TINY[_c] = FONT5[_c]


def W9(top, *rows):
    """A glyph in the 9-row web font: rows start at row `top` (0 = ascender line, 2 = x-height)."""
    w = len(rows[0])
    out = ["." * w] * top + list(rows)
    out += ["." * w] * (9 - len(out))
    assert len(out) == 9, rows
    return out


# A Verdana/Tahoma-flavoured 9-row font: ascenders on row 0, x-height from row 2, baseline row 6.
WEB = {
    "a": W9(2, ".##.", "...#", ".###", "#..#", ".###"),
    "b": W9(0, "#...", "#...", "###.", "#..#", "#..#", "#..#", "###."),
    "c": W9(2, ".###", "#...", "#...", "#...", ".###"),
    "d": W9(0, "...#", "...#", ".###", "#..#", "#..#", "#..#", ".###"),
    "e": W9(2, ".##.", "#..#", "####", "#...", ".###"),
    "f": W9(0, "..##", ".#..", "###.", ".#..", ".#..", ".#..", ".#.."),
    "g": W9(2, ".###", "#..#", "#..#", "#..#", ".###", "...#", ".##."),
    "h": W9(0, "#...", "#...", "###.", "#..#", "#..#", "#..#", "#..#"),
    "i": W9(0, "#", ".", "#", "#", "#", "#", "#"),
    "j": W9(0, ".#", "..", ".#", ".#", ".#", ".#", ".#", ".#", "#."),
    "k": W9(0, "#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#"),
    "l": W9(0, "#", "#", "#", "#", "#", "#", "#"),
    "m": W9(2, "###.##.", "#..#..#", "#..#..#", "#..#..#", "#..#..#"),
    "n": W9(2, "###.", "#..#", "#..#", "#..#", "#..#"),
    "o": W9(2, ".##.", "#..#", "#..#", "#..#", ".##."),
    "p": W9(2, "###.", "#..#", "#..#", "#..#", "###.", "#...", "#..."),
    "q": W9(2, ".###", "#..#", "#..#", "#..#", ".###", "...#", "...#"),
    "r": W9(2, "#.##", "##..", "#...", "#...", "#..."),
    "s": W9(2, ".###", "#...", ".##.", "...#", "###."),
    "t": W9(1, ".#..", "###.", ".#..", ".#..", ".#..", "..##"),
    "u": W9(2, "#..#", "#..#", "#..#", "#..#", ".###"),
    "v": W9(2, "#...#", "#...#", ".#.#.", ".#.#.", "..#.."),
    "w": W9(2, "#..#..#", "#..#..#", "#..#..#", "#..#..#", ".##.##."),
    "x": W9(2, "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": W9(2, "#..#", "#..#", "#..#", "#..#", ".###", "...#", ".##."),
    "z": W9(2, "####", "..#.", ".#..", "#...", "####"),
    "A": W9(0, ".##.", "#..#", "#..#", "####", "#..#", "#..#", "#..#"),
    "B": W9(0, "###.", "#..#", "#..#", "###.", "#..#", "#..#", "###."),
    "C": W9(0, ".###", "#...", "#...", "#...", "#...", "#...", ".###"),
    "D": W9(0, "###.", "#..#", "#..#", "#..#", "#..#", "#..#", "###."),
    "E": W9(0, "####", "#...", "#...", "###.", "#...", "#...", "####"),
    "F": W9(0, "####", "#...", "#...", "###.", "#...", "#...", "#..."),
    "G": W9(0, ".###", "#...", "#...", "#.##", "#..#", "#..#", ".###"),
    "H": W9(0, "#..#", "#..#", "#..#", "####", "#..#", "#..#", "#..#"),
    "I": W9(0, "###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"),
    "J": W9(0, "..#", "..#", "..#", "..#", "..#", "#.#", ".#."),
    "K": W9(0, "#..#", "#..#", "#.#.", "##..", "#.#.", "#..#", "#..#"),
    "L": W9(0, "#...", "#...", "#...", "#...", "#...", "#...", "####"),
    "M": W9(0, "#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": W9(0, "#..#", "##.#", "##.#", "#.##", "#.##", "#..#", "#..#"),
    "O": W9(0, ".##.", "#..#", "#..#", "#..#", "#..#", "#..#", ".##."),
    "P": W9(0, "###.", "#..#", "#..#", "###.", "#...", "#...", "#..."),
    "Q": W9(0, ".##.", "#..#", "#..#", "#..#", "#..#", "#.#.", ".#.#"),
    "R": W9(0, "###.", "#..#", "#..#", "###.", "#.#.", "#..#", "#..#"),
    "S": W9(0, ".###", "#...", "#...", ".##.", "...#", "...#", "###."),
    "T": W9(0, "#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": W9(0, "#..#", "#..#", "#..#", "#..#", "#..#", "#..#", ".##."),
    "V": W9(0, "#...#", "#...#", "#...#", ".#.#.", ".#.#.", ".#.#.", "..#.."),
    "W": W9(0, "#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": W9(0, "#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": W9(0, "#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": W9(0, "####", "...#", "...#", "..#.", ".#..", "#...", "####"),
    "0": W9(0, ".##.", "#..#", "#..#", "#..#", "#..#", "#..#", ".##."),
    "1": W9(0, ".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"),
    "2": W9(0, ".##.", "#..#", "...#", "..#.", ".#..", "#...", "####"),
    "3": W9(0, "###.", "...#", "...#", ".##.", "...#", "...#", "###."),
    "4": W9(0, "#..#", "#..#", "#..#", "####", "...#", "...#", "...#"),
    "5": W9(0, "####", "#...", "###.", "...#", "...#", "#..#", ".##."),
    "6": W9(0, ".##.", "#...", "#...", "###.", "#..#", "#..#", ".##."),
    "7": W9(0, "####", "...#", "..#.", "..#.", ".#..", ".#..", ".#.."),
    "8": W9(0, ".##.", "#..#", "#..#", ".##.", "#..#", "#..#", ".##."),
    "9": W9(0, ".##.", "#..#", "#..#", ".###", "...#", "...#", ".##."),
    "[": W9(0, "##", "#.", "#.", "#.", "#.", "#.", "#.", "##"),
    "]": W9(0, "##", ".#", ".#", ".#", ".#", ".#", ".#", "##"),
    "|": W9(0, "#", "#", "#", "#", "#", "#", "#", "#"),
    ".": W9(6, "#"),
    "'": W9(0, "#", "#"),
    "!": W9(0, "#", "#", "#", "#", "#", ".", "#"),
    "&": W9(0, ".#..", "#.#.", "#.#.", ".#..", "#.#.", "#..#", ".##."),
    "-": W9(4, "###"),
    "·": W9(4, "#"),
    " ": W9(0, "...", "..."),
}


def bold(glyph):
    """Tahoma-style bold: every stroke one pixel wider (glyph one column wider)."""
    out = []
    for row in glyph:
        r = row + "."
        out.append("".join("#" if r[i] == "#" or (i > 0 and r[i - 1] == "#") else "." for i in range(len(r))))
    return out


WEB_B = {k: bold(v) for k, v in WEB.items()}
WEB_B[" "] = W9(0, "..", "..")
WEB_B["m"] = W9(2, "####.###.", "##.##.##.", "##.##.##.", "##.##.##.", "##.##.##.")
WEB_B["w"] = W9(2, "##.##.##", "##.##.##", "##.##.##", "##.##.##", ".##.##..")
WEB_B["v"] = W9(2, "##..##", "##..##", ".##.#.", ".####.", "..##..")
WEB_B["x"] = W9(2, "##..##", ".####.", "..##..", ".####.", "##..##")
WEB_B["k"] = W9(0, "##...", "##...", "##.##", "####.", "###..", "####.", "##.##")
WEB_B["r"] = W9(2, "##.##", "####.", "##...", "##...", "##...")


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


def bubble_text(a, s, x, y, fill, outline, gap=1):
    """Chunky outlined lettering (Neopets-style): bold uppercase with a 1px outline all round."""
    w = text_w(WEB_B, s, gap) + 2
    m = np.zeros((9, w), dtype=bool)
    cx = 1
    for c in s:
        g = WEB_B[c]
        for r in range(7):
            for k, ch in enumerate(g[r]):
                if ch == "#":
                    m[r + 1, cx + k] = True
        cx += len(g[0]) + gap
    o = m.copy()
    o[1:, :] |= m[:-1, :]
    o[:-1, :] |= m[1:, :]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    for r in range(9):
        for k in range(w):
            if m[r, k]:
                px(a, x + k, y + r, fill(r) if callable(fill) else fill)
            elif o[r, k]:
                px(a, x + k, y + r, outline)
    return w


def bubble_w(s, gap=1):
    return text_w(WEB_B, s, gap) + 2


# ------------------------------------------------------------------------------------------
# Logos: the one real mark per skin, rasterised from source/ at build time
# ------------------------------------------------------------------------------------------

LOGO_SRC = {
    "myspace": os.path.join(HERE, "source", "logo-myspace", "MySpace_logo.svg"),
    "facebook": os.path.join(HERE, "source", "logo-facebook", "Facebook.svg"),
    "neopets": os.path.join(HERE, "source", "logo-neopets", "Neopets_logo_2024.png"),
}


def _raster(kind):
    src = LOGO_SRC[kind]
    if src.endswith(".svg"):
        os.makedirs(SCRATCH, exist_ok=True)
        png = os.path.join(SCRATCH, f"logo-{kind}.png")
        subprocess.run(["/usr/bin/rsvg-convert", "-h", "800", src, "-o", png], check=True)
        src = png
    return Image.open(src).convert("RGBA")


def _bands(mask, axis):
    """Runs of non-empty rows (axis=1) or columns (axis=0) of a boolean mask."""
    on = mask.any(axis=axis)
    runs, start = [], None
    for i, v in enumerate(on):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append((start, i))
            start = None
    if start is not None:
        runs.append((start, len(on)))
    return runs


def logo(kind, height):
    """Returns (alpha HxW float 0..1, colour HxWx3 or None) for the logo at `height` pixels."""
    im = _raster(kind)
    arr = np.asarray(im).astype(np.float32)
    if kind == "facebook":
        # white letters on the blue box: coverage from how far each pixel is from the blue
        blue = arr[5, 5, :3]
        cov = np.clip((arr[..., :3].mean(-1) - blue.mean()) / (255 - blue.mean()), 0, 1)
        m = cov > 0.3
        rows = _bands(m, 1)
        y0, y1 = rows[0][0], rows[-1][1]
        cols = _bands(m, 0)
        cols = [c for c in cols if c[1] - c[0] > 8]          # drop the (R) mark
        x0, x1 = cols[0][0], max(c[1] for c in cols if c[0] < arr.shape[1] * 0.9)
        cov = cov[y0:y1, x0:x1]
        rgb = None
    else:
        alpha = arr[..., 3] / 255
        m = alpha > 0.3
        if kind == "myspace":
            # the figures and "myspace.com"; the tagline under them (the lower ~40%) is dropped
            y0, y1 = 0, int(m.shape[0] * 0.60)
            cols = _bands(m[y0:y1], 0)
            cols = [c for c in cols if c[1] - c[0] > m.shape[0] * 0.02]   # drop the TM
            x0, x1 = cols[0][0], cols[-1][1]
        else:  # neopets: the lettering only (its stars sit above it); the (R) is dropped
            hh = m.shape[0]
            cols = _bands(m, 0)
            cols = [c for c in cols if c[1] - c[0] > 30]
            x0, x1 = 60, cols[-1][1]
            y0, y1 = int(hh * 0.31), int(hh * 0.92)
            alpha = alpha.copy()
            stars = (arr[..., 0] > 150) & (arr[..., 2] < 120)
            alpha[stars] = 0
            alpha[:int(hh * 0.445), :int(arr.shape[1] * 0.6)] = 0   # the star outlines over n-e-o
        cov = alpha[y0:y1, x0:x1]
        rgb = arr[y0:y1, x0:x1, :3]
    h0, w0 = cov.shape
    w = max(1, round(w0 * height / h0))
    ci = Image.fromarray((cov * 255).astype(np.uint8), "L").resize((w, height), Image.LANCZOS)
    c = np.asarray(ci).astype(np.float32) / 255
    c = np.clip((c - 0.12) / 0.70, 0, 1)                    # firm up the edges at sprite size
    col = None
    if rgb is not None and kind == "neopets":
        # premultiply so the black/yellow don't bleed into each other's fringes
        pre = rgb * cov[..., None]
        ri = Image.fromarray(np.clip(pre, 0, 255).astype(np.uint8), "RGB").resize((w, height), Image.LANCZOS)
        ai = np.asarray(Image.fromarray((cov * 255).astype(np.uint8), "L").resize((w, height), Image.LANCZOS))
        ai = np.maximum(ai.astype(np.float32) / 255, 1e-3)
        col = np.clip(np.asarray(ri).astype(np.float32) / ai[..., None], 0, 255)
    return c, col


def paste_logo(a, x, y, alpha, ink=None, rgb=None, recolour=None):
    h, w = alpha.shape
    region = a[y:y + h, x:x + w].astype(np.float32)
    if rgb is not None:
        src = rgb.copy()
        if recolour:
            src = recolour(src)
    else:
        src = np.zeros((h, w, 3), np.float32) + np.array(ink, np.float32)
    out = region * (1 - alpha[..., None]) + src * alpha[..., None]
    a[y:y + h, x:x + w] = np.round(out).astype(np.int32)
    return w


# ------------------------------------------------------------------------------------------
# Theme-specific surfaces
# ------------------------------------------------------------------------------------------


def bar_fill(a, x, y, w, h, lit):
    """The titlebar band, whatever its height (14 for main/EQ, 20 for playlist/gen)."""
    if KEY == "myspace":
        # the dark header with the light-blue nav strip under it
        dark, nav = (T["dark"], T["nav"]) if lit else (T["bar_dim"], T["nav_dim"])
        rect(a, x, y, w, h, dark)
        rect(a, x, y + h - 3, w, 1, WHITE if lit else lerp(WHITE, dark, 0.4))
        rect(a, x, y + h - 2, w, 2, nav)
    elif KEY == "facebook-2006":
        rect(a, x, y, w, h, T["dark"] if lit else T["bar_dim"])
        rect(a, x, y + h - 1, w, 1, H("29447e") if lit else H("5b70a0"))
    else:
        top, bot = T["sky"] if lit else T["sky_dim"]
        vgrad(a, x, y, w, h, top, bot)
        rect(a, x, y + h - 1, w, 1, T["outline"] if lit else T["outline_dim"])


def body_fill(a, x, y, w, h):
    rect(a, x, y, w, h, T["body"])
    if KEY == "neopets":
        # a tiled pattern: little diamonds on a 10px grid, offset every other row
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                gx, gy = xx % 10, yy % 10
                if (gy < 5 and abs(gx - 2) + abs(gy - 2) <= 1) or (gy >= 5 and abs(gx - 7) + abs(gy - 7) <= 1):
                    a[yy, xx] = T["body_dot"]


def panel(a, x, y, w, h, fill=None, border=None, r=None):
    """A content box: square 1px-bordered on MySpace/Facebook, rounded on Neopets."""
    fill = T["panel"] if fill is None else fill
    border = T["border"] if border is None else border
    if KEY == "neopets":
        rrect(a, x, y, w, h, fill, border, 2 if r is None else r)
    else:
        rect(a, x, y, w, h, fill)
        frame(a, x, y, w, h, border)


def display_box(a, x, y, w, h):
    """A display window (text/digits sit on T['disp'])."""
    if KEY == "neopets":
        rrect(a, x - 2, y - 2, w + 4, h + 4, T["disp"], T["disp_rim"], 2)
        rrect(a, x - 1, y - 1, w + 2, h + 2, T["disp"], lerp(T["disp_rim"], T["disp"], 0.55), 1)
        rect(a, x, y, w, h, T["disp"])
    elif KEY == "myspace":
        rect(a, x - 1, y - 1, w + 2, h + 2, H("111111"))
        rect(a, x, y, w, h, T["disp"])
        rect(a, x, y, w, 1, H("3a3a3a"))
    else:
        frame(a, x - 1, y - 1, w + 2, h + 2, T["disp_rim"])
        rect(a, x, y, w, h, T["disp"])


def button_face(a, x, y, w, h, pressed):
    if KEY == "myspace":
        rect(a, x, y, w, h, T["btn_pr"] if pressed else T["btn"])
        frame(a, x, y, w, h, T["btn_rim"])
        if not pressed:
            rect(a, x + 1, y + h - 2, w - 2, 1, H("e4eef9"))
    elif KEY == "facebook-2006":
        rect(a, x, y, w, h, T["btn_pr"] if pressed else T["btn"])
        if pressed:
            bevel(a, x, y, w, h, T["btn_lo"], T["btn_hi"])
        else:
            bevel(a, x, y, w, h, T["btn_hi"], T["btn_lo"])
    else:
        if pressed:
            rrect(a, x, y, w, h, None, T["btn_rim"], 2, grad=(T["btn_pr"], lerp(T["btn_pr"], T["btn"], 0.6)))
        else:
            rrect(a, x, y, w, h, None, T["btn_rim"], 2, grad=(T["btn_top"], T["btn"]))
            # the glossy highlight across the top half
            rect(a, x + 3, y + 2, w - 6, 1, lerp(T["btn_top"], WHITE, 0.6))


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button."""
    if KEY == "myspace":
        face = T["nav"] if not pressed else T["dark"]
        if not lit:
            face = T["nav_dim"]
        rect(a, x, y, 9, 9, face)
        frame(a, x, y, 9, 9, WHITE if lit else H("dfe6f0"))
        ink = WHITE
    elif KEY == "facebook-2006":
        face = H("29447e") if pressed else (H("4c66a4") if lit else H("7f93bd"))
        rect(a, x, y, 9, 9, face)
        frame(a, x, y, 9, 9, H("6d84b4") if lit else H("98a8ca"))
        ink = WHITE
    else:
        rrect(a, x, y, 9, 9, None, T["outline"] if lit else T["outline_dim"], 2,
              grad=((H("ffe680"), H("ff9900")) if not pressed else (H("ff9900"), H("cc6600")))
              if lit else (H("e6e2cc"), H("bdb7a0")))
        ink = T["outline"] if lit else T["outline_dim"]
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        rect(a, X + 3, Y + 3, 3, 3, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 2, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 2, ink)
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


def emblem(a, x, y):
    """13x15 at the About spot."""
    if KEY == "myspace":
        # an "online now" figure: orange head, blue body, a little glint
        rect(a, x, y, 13, 15, T["panel"])
        shape = [
            "....###......",
            "...#####.....",
            "...#####.....",
            "...#####.....",
            "....###......",
            ".............",
            "..#######....",
            ".#########...",
            ".#########...",
            ".##.###.##...",
            ".##.###.##...",
            "....###......",
            "....#.#......",
            "....#.#......",
            ".............",
        ]
        for r, row in enumerate(shape):
            for c, ch in enumerate(row):
                if ch == "#":
                    px(a, x + c, y + r, H("ff9933") if r < 5 else T["dark"])
        px(a, x + 4, y + 1, H("ffd9b3"))
        px(a, x + 11, y + 2, H("ff6600"))
        px(a, x + 10, y + 2, H("ffb380"))
        px(a, x + 12, y + 2, H("ffb380"))
        px(a, x + 11, y + 1, H("ffb380"))
        px(a, x + 11, y + 3, H("ffb380"))
    elif KEY == "facebook-2006":
        rect(a, x, y + 1, 13, 13, T["dark"])
        frame(a, x, y + 1, 13, 13, H("29447e"))
        f = ["....###", "...#...", "...#...", ".#####.", "...#...", "...#...", "...#...", "...#...", "...#..."]
        draw_text(a, {"f": bold(f)}, "f", x + 3, y + 4, WHITE)
    else:
        # our own gold "NP" coin
        m = np.zeros((13, 13), bool)
        for r in range(13):
            for c in range(13):
                m[r, c] = (r - 6) ** 2 + (c - 6) ** 2 <= 6.4 ** 2
        for r in range(13):
            for c in range(13):
                if not m[r, c]:
                    continue
                d = ((r - 6) ** 2 + (c - 6) ** 2) ** 0.5
                if d > 5.3:
                    col = H("8a5a00")
                elif d > 4.3:
                    col = H("ffd84a") if r + c < 12 else H("d99a00")
                else:
                    col = lerp(H("fff1a0"), H("f5b800"), (r + c) / 24)
                px(a, x + c, y + 1 + r, col)
        np_ = {"N": G("#..#", "##.#", "#.##", "#..#", "#..#"), "P": G("##.", "#.#", "##.", "#..", "#..")}
        draw_text(a, np_, "NP", x + 3, y + 5, H("8a5a00"))
        px(a, x + 3, y + 3, WHITE)
        px(a, x + 4, y + 3, H("fffbe0"))


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, T["body"])
    if KEY == "neopets":
        rrect(a, 0, 0, 8, 43, T["panel"], T["border"], 2)
    elif KEY == "myspace":
        rect(a, 0, 0, 8, 43, T["panel"])
        frame(a, 0, 0, 8, 43, T["border"])
    else:
        rect(a, 0, 0, 8, 43, T["panel"])
        frame(a, 0, 0, 8, 43, T["border"])
    on_bg = T["accent_bg"] if KEY != "facebook-2006" else T["panel2"]
    on_ink = T["accent"]
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, on_bg)
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, on_ink if on else T["label"])
    return a


LOGO_CACHE = {}


def main_titlebar(lit):
    a = new(275, 14)
    bar_fill(a, 0, 0, 275, 14, lit)
    if KEY == "myspace":
        al, _ = LOGO_CACHE.setdefault("main", logo("myspace", 10))
        paste_logo(a, 19, 1, al, WHITE if lit else T["bar_ink_dim"])
        # a tagline in our own words, right of the logo
        tag = "friends · music · blogs"
        draw_text(a, WEB, tag, 240 - 4 - text_w(WEB, tag), 1, T["bar_ink"] if lit else T["bar_ink_dim"])
    elif KEY == "facebook-2006":
        al, _ = LOGO_CACHE.setdefault("main", logo("facebook", 10))
        paste_logo(a, 20, 2, al, WHITE if lit else T["bar_ink_dim"])
        links = ["home", "profile", "friends", "music"]
        x = 236
        for s in reversed(links):
            x -= text_w(WEB, s)
            draw_text(a, WEB, s, x, 3, T["bar_ink"] if lit else T["bar_ink_dim"])
            x -= 7
    else:
        al, _ = LOGO_CACHE.setdefault("main", logo("neopets", 13))
        lw = al.shape[1]
        lx = (275 - lw) // 2
        # white halo, then the black lettering, like the logo on the site's coloured header
        halo = np.zeros((al.shape[0] + 2, lw + 2), np.float32)
        for dy in range(3):
            for dx in range(3):
                halo[dy:dy + al.shape[0], dx:dx + lw] = np.maximum(halo[dy:dy + al.shape[0], dx:dx + lw], al)
        paste_logo(a, lx - 1, 0, halo[1:14], WHITE if lit else H("dfe3e8"))
        paste_logo(a, lx, 0, al, BLACK if lit else H("4a4f5a"))
        # our own stars either side of it
        for sx, sy, big in ((lx - 14, 5, True), (lx - 6, 9, False), (lx + lw + 6, 4, False), (lx + lw + 13, 8, True)):
            star(a, sx, sy, big, lit)
        for sx, sy in ((40, 4), (70, 9), (205, 5), (232, 9)):
            sparkle(a, sx, sy, H("ffe066") if lit else H("d8dde4"))
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, T["body"])
    for kind, x in [("options", 0), ("minimize", 9), ("close", 18)]:
        b = new(9, 9, T["body"])
        mini_button(b, 0, 0, kind, True)
        a[0:9, x:x + 9] = b
        b = new(9, 9, T["body"])
        mini_button(b, 0, 0, kind, True, pressed=True)
        a[9:18, x:x + 9] = b
    b = new(9, 9, T["body"])
    mini_button(b, 0, 0, "shade", True)
    a[18:27, 0:9] = b
    b = new(9, 9, T["body"])
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

# 7x11 bold digits (Verdana-bold-ish), drawn at (1, 1) in each 9x13 cell.
DIGITS = {
    0: [".#####.", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##",
        "##...##", ".#####."],
    1: ["...##..", "..###..", ".####..", "...##..", "...##..", "...##..", "...##..", "...##..", "...##..",
        "...##..", ".######"],
    2: [".#####.", "##...##", ".....##", ".....##", "....##.", "...##..", "..##...", ".##....", "##.....",
        "##.....", "#######"],
    3: [".#####.", "##...##", ".....##", ".....##", ".....##", "..####.", ".....##", ".....##", ".....##",
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
for _d, _g in DIGITS.items():
    assert len(_g) == 11 and all(len(r) == 7 for r in _g), _d


def digit_ink():
    return {"myspace": WHITE, "facebook-2006": T["dark"], "neopets": T["ink"]}[KEY]


def draw_digit(a, x, y, n):
    rect(a, x, y, 9, 13, T["disp"])
    if n is None:
        return
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + 1 + c, y + 1 + r, digit_ink())


def make_main():
    a = new(275, 116, T["body"])
    body_fill(a, 0, 0, 275, 116)
    a[0:14, :] = main_titlebar(True)
    if KEY == "myspace":
        frame(a, 0, 14, 275, 102, T["border"])
        # the profile box round the displays and sliders
        panel(a, 4, 16, 267, 68, T["panel"], T["border"])
        # the "Contacting" box round the transport
        panel(a, 13, 85, 250, 24, T["panel"], T["border"])
        rect(a, 1, 110, 273, 5, T["accent_bg"])
        rect(a, 1, 109, 273, 1, H("ff9933"))
        # glitter, sparingly
        for sx, sy in ((268, 88), (266, 104), (8, 89), (10, 104)):
            sparkle(a, sx, sy, H("ff99cc"))
    elif KEY == "facebook-2006":
        frame(a, 0, 14, 275, 102, T["border"])
        rect(a, 1, 15, 273, 100, WHITE)
        # the grey sidebar column, and a section header bar above the transport
        rect(a, 1, 15, 6, 100, T["panel"])
        rect(a, 7, 15, 1, 100, T["panel2"])
        rect(a, 13, 84, 257, 1, T["dark"])
        rect(a, 13, 85, 257, 24, T["panel"])
        rect(a, 13, 109, 257, 1, T["panel2"])
    else:
        # an outline round the window body
        rect(a, 0, 14, 275, 2, T["body"])
        rect(a, 0, 14, 1, 102, T["border"])
        rect(a, 274, 14, 1, 102, T["border"])
        rect(a, 0, 115, 275, 1, T["border"])
        rect(a, 1, 14, 273, 1, lerp(T["body"], WHITE, 0.4))
        # the blue tray behind the transport
        rrect(a, 13, 85, 237, 25, H("cfe6ff"), H("1f6fd0"), 3)
    a[22:65, 10:18] = clutter_bar("")
    # left display: indicator, time, analyzer
    display_box(a, 21, 20, 84, 42)
    for x in (48, 60, 78, 90):
        draw_digit(a, x, 26, None)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, digit_ink())
    # right display: title row, then the kbps/kHz row
    display_box(a, 109, 21, 159, 15)
    display_box(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, T["ink_mid"])
    draw_text(a, TINY, "KHZ", 169, 44, T["ink_mid"])
    emblem(a, 253, 91)
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


def transport_icon(a, kind, x, y, w, h, pressed):
    ink = T["btn_ink_pr"] if pressed else T["btn_ink"]
    shadow = None
    if KEY == "neopets" and not pressed:
        shadow = T["btn_rim"]
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


def tray_colour():
    return {"myspace": T["panel"], "facebook-2006": T["panel"], "neopets": H("cfe6ff")}[KEY]


def make_cbuttons():
    a = new(136, 36, tray_colour())
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


def toggle(a, x, y, w, h, label, on, pressed):
    """A small text button; when on, the label lights up (and, off the Facebook theme, the face)."""
    o = 1 if pressed else 0
    if KEY == "myspace":
        rect(a, x, y, w, h, T["accent_bg"] if on else (T["btn_pr"] if pressed else WHITE))
        frame(a, x, y, w, h, H("ff9933") if on else T["btn_rim"])
        ink = T["accent"] if on else T["tog_off"]
    elif KEY == "facebook-2006":
        button_face(a, x, y, w, h, pressed)
        ink = T["tog_on"] if on else T["tog_off"]
    else:
        if on:
            rrect(a, x, y, w, h, None, T["btn_rim"], 2,
                  grad=(H("ffd27a"), H("ff8a00")) if not pressed else (H("ff8a00"), H("e06a00")))
        else:
            rrect(a, x, y, w, h, None, T["btn_rim"], 2,
                  grad=(H("fff6b0"), H("ffcc00")) if not pressed else (H("ffcc00"), H("e8b000")))
        ink = T["tog_on"] if on else T["tog_off"]
    tw = text_w(TINY, label)
    draw_text(a, TINY, label, x + (w - tw) // 2 + o, y + (h - 5) // 2 + o, ink)


def make_shufrep():
    a = new(92, 85, tray_colour())
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        toggle(a, 0, y, 28, 15, "REPEAT", on, pressed)
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    # EQ / PL sit on the main panel, not the tray
    rect(a, 0, 61, 92, 24, main_panel_colour())
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        toggle(a, x, 61, 23, 12, label, False, pressed)
        toggle(a, x, 73, 23, 12, label, True, pressed)
    return a


def main_panel_colour():
    return {"myspace": T["panel"], "facebook-2006": WHITE, "neopets": T["body"]}[KEY]


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T["disp"])
    for y, on in ((0, True), (12, False)):
        col = T["ink"] if on else T["ink_dim"]
        if KEY == "myspace" and on:
            col = H("ff9933")
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T["disp"])
    ink = digit_ink()
    play = H("33cc33") if KEY == "neopets" else (H("ff9933") if KEY == "myspace" else ink)
    tri_right(a, 2, 1, 7, play)
    rect(a, 9 + 2, 1, 2, 7, ink)
    rect(a, 9 + 5, 1, 2, 7, ink)
    rect(a, 18 + 2, 2, 5, 5, ink)
    rect(a, 36, 0, 3, 9, T["disp"])
    rect(a, 39 + 1, 3, 1, 3, ink)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["disp"])
    for n in range(10):
        draw_digit(a, 9 * n, 0, n)
    draw_digit(a, 90, 0, None)
    if ex:
        draw_digit(a, 99, 0, None)
        rect(a, 99 + 2, 6, 5, 2, digit_ink())
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, T["disp"])
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key, col * 5, row * 6, T["ink"])
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def thumb(a, x, y, w, h, selected, grip="v"):
    top, bot = T["thumb_pr"] if selected else T["thumb"]
    if KEY == "neopets":
        rrect(a, x, y, w, h, None, T["thumb_rim"], 2 if min(w, h) > 8 else 1, grad=(top, bot))
        rect(a, x + 2, y + 1, max(1, w - 4), 1, lerp(top, WHITE, 0.7))
    elif KEY == "facebook-2006":
        rect(a, x, y, w, h, top)
        bevel(a, x, y, w, h, H("d9dfea"), H("0e1f5b"))
    else:
        vgrad(a, x, y, w, h, top, bot)
        frame(a, x, y, w, h, T["thumb_rim"])
        rect(a, x + 1, y + 1, w - 2, 1, WHITE)
    cx = x + w // 2
    gc = {"myspace": H("888888"), "facebook-2006": H("8fa1c7"), "neopets": H("cc6600")}[KEY]
    if grip == "v":
        for gx in (cx - 2, cx, cx + 2):
            rect(a, gx, y + 3, 1, h - 6, gc)
    else:
        for gy in (y + h // 2 - 2, y + h // 2, y + h // 2 + 2):
            rect(a, x + 3, gy, w - 6, 1, gc)


def track(a, x, y, w, h):
    if KEY == "neopets":
        rrect(a, x, y, w, h, T["track"], T["track_rim"], 2 if h > 4 else 1)
    else:
        rect(a, x, y, w, h, T["track"])
        frame(a, x, y, w, h, T["track_rim"])


def make_posbar(main):
    a = new(307, 10, T["body"])
    a[0:10, 0:248] = main[72:82, 16:264]
    track(a, 0, 2, 248, 6)
    thumb(a, 248, 0, 29, 10, False)
    thumb(a, 278, 0, 29, 10, True)
    return a


def slider_thumbs(a):
    thumb(a, 0, 422, 14, 11, True)
    thumb(a, 15, 422, 14, 11, False)


def make_volume(main):
    a = new(68, 433, T["body"])
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        track(a, 1, y + 3, 66, 7)
        level = (i + 1) / 28
        fill_to = 7 + round(level * 54)
        colour = ramp(T["level"], level)
        rect(a, 2, y + 4, fill_to - 2, 5, colour)
        if KEY == "neopets":
            rect(a, 3, y + 4, max(0, fill_to - 4), 1, lerp(colour, WHITE, 0.55))
        rect(a, 0, y + 13, 68, 2, a[y + 12, 0].tolist())
    slider_thumbs(a)
    return a


def make_balance(main):
    a = new(68, 433, T["body"])
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        track(a, 10, y + 3, 36, 7)
        t = i / 27
        colour = ramp(T["level"], t)
        reach = round(16 * t)
        if reach:
            rect(a, 28 - reach, y + 4, 2 * reach + 1, 5, colour)
        rect(a, 28, y + 3, 1, 7, T["track_rim"])
        rect(a, 9, y + 13, 38, 2, a[y + 12, 9].tolist())
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = new(275, 14)
    bar_fill(a, 0, 0, 275, 14, lit)
    ink = T["bar_ink"] if lit else T["bar_ink_dim"]
    if KEY == "myspace":
        # the nav strip's links, ours, with this page picked out in orange
        items = ["home", "browse", "search", "music", "equalizer"]
        x = 18
        for i, s in enumerate(items):
            if i:
                x = draw_text(a, WEB, "|", x + 2, 1, H("6698cb") if lit else H("8f9fc0")) + 2
            col = (H("ff9933") if lit else H("e8c9a8")) if s == "equalizer" else ink
            x = draw_text(a, WEB_B if s == "equalizer" else WEB, s, x, 1, col)
    elif KEY == "facebook-2006":
        s = "[ equalizer ]"
        draw_text(a, WEB_B, s, 18, 2, ink, gap=1)
    else:
        s = "EQUALIZER"
        w = bubble_w(s)
        bubble_text(a, s, (275 - w) // 2, 2, (lambda r: lerp(H("fffbe0"), H("ffcc00"), r / 8)) if lit else H("e8e8e8"),
                    T["outline"] if lit else T["outline_dim"])
        for sx, sy in ((80, 5), (192, 8)):
            sparkle(a, sx, sy, H("ffe066") if lit else H("d8dde4"))
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    """14x63 slot whose fill rises with the value (n of 0..27)."""
    bay = eq_bay_colour()
    rect(a, x, y, 14, 63, bay)
    if KEY == "neopets":
        rrect(a, x + 4, y + 1, 6, 61, T["track"], T["track_rim"], 2)
    else:
        rect(a, x + 4, y + 1, 6, 61, T["track"])
        frame(a, x + 4, y + 1, 6, 61, T["track_rim"])
    v = n / 27
    top = round((1 - v) * 51) + 6
    colour = ramp(T["level"], v)
    for r in range(top, 60):
        rect(a, x + 5, y + r, 4, 1, colour)
    rect(a, x + 1, y + 31, 2, 1, T["label"])
    rect(a, x + 11, y + 31, 2, 1, T["label"])


def eq_bay_colour():
    return {"myspace": T["panel"], "facebook-2006": WHITE, "neopets": T["panel"]}[KEY]


def make_eqmain():
    a = new(275, 315, T["body"])
    body_fill(a, 0, 0, 275, 315)
    a[0:14, :] = eq_titlebar(True)
    if KEY == "myspace":
        frame(a, 0, 14, 275, 102, T["border"])
        panel(a, 16, 36, 245, 68, T["panel"], T["border"])
        rect(a, 1, 108, 273, 7, T["accent_bg"])
        rect(a, 1, 107, 273, 1, H("ff9933"))
        sparkle(a, 7, 100, H("ff99cc"))
        sparkle(a, 268, 26, H("ff99cc"))
    elif KEY == "facebook-2006":
        frame(a, 0, 14, 275, 102, T["border"])
        rect(a, 1, 15, 6, 100, T["panel"])
        rect(a, 7, 15, 1, 100, T["panel2"])
        rect(a, 8, 15, 266, 19, T["panel"])
        rect(a, 8, 34, 266, 1, T["panel2"])
        rect(a, 16, 36, 245, 68, WHITE)
        frame(a, 16, 36, 245, 68, T["panel2"])
        rect(a, 16, 36, 245, 1, T["dark"])
        rect(a, 1, 107, 273, 1, T["panel2"])
        rect(a, 1, 108, 273, 7, T["panel"])
    else:
        rect(a, 0, 14, 1, 102, T["border"])
        rect(a, 274, 14, 1, 102, T["border"])
        rect(a, 0, 115, 275, 1, T["border"])
        rrect(a, 16, 36, 245, 68, T["panel"], T["border"], 3)
    for lbl, yy in (("+12", 41), ("0", 67), ("-12", 93)):
        text_center(a, TINY, lbl, 58, yy, T["label"])
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    lab_y = 109 if KEY != "neopets" else 106
    lab_col = T["accent"] if KEY == "myspace" else T["label"]
    text_center(a, TINY, "PREAMP", 28, lab_y, lab_col)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, lab_y, lab_col)

    # under the window: buttons
    b = new(9, 9, T["body"])
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = b
    rect(a, 10, 119, 235, 12, main_panel_colour())
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        toggle(a, x, 119, w, 12, label, on, pressed)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    thumb(a, 0, 164, 11, 11, False, grip="h")
    thumb(a, 0, 176, 11, 11, True, grip="h")
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        rect(a, 224, y, 44, 12, main_panel_colour())
        toggle(a, 224, y, 44, 12, "PRESETS", False, pressed)
    # graph
    rect(a, 0, 294, 113, 19, T["disp"])
    grid = lerp(T["disp"], T["ink"], 0.12)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, grid)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, lerp(T["disp"], T["ink"], 0.25))
    gl = T["level"][::-1]
    for r in range(19):
        px(a, 115, 294 + r, ramp(gl, r / 18))
    for x in range(113):
        px(a, x, 314, lerp(T["disp"], T["ink"], 0.5) if x % 3 != 2 else T["disp"])
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------


def bar20(w, lit):
    a = new(w, 20)
    bar_fill(a, 0, 0, w, 20, lit)
    return a


def frame_side():
    """Colour of the 20/12px playlist and gen side frames."""
    return {"myspace": T["panel"], "facebook-2006": T["panel"], "neopets": T["panel2"]}[KEY]


def pl_title(t, lit):
    ink = T["bar_ink"] if lit else T["bar_ink_dim"]
    if KEY == "myspace":
        text_center(t, WEB_B, "my playlist", 50, 4, ink)
    elif KEY == "facebook-2006":
        text_center(t, WEB_B, "[ playlist ]", 50, 5, ink)
    else:
        s = "PLAYLIST"
        w = bubble_w(s)
        bubble_text(t, s, 50 - w // 2, 5, (lambda r: lerp(H("fffbe0"), H("ffcc00"), r / 8)) if lit else H("e8e8e8"),
                    T["outline"] if lit else T["outline_dim"])


def make_pledit():
    side = frame_side()
    edge = T["border"]
    a = new(280, 186, side)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit)
        a[y:y + 20, 127:152] = t
        t = bar20(25, lit)
        a[y:y + 20, 0:25] = t
        t = bar20(100, lit)
        pl_title(t, lit)
        a[y:y + 20, 26:126] = t
        t = bar20(25, lit)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    # left side tile
    t = new(12, 29, side)
    rect(t, 0, 0, 1, 29, edge)
    rect(t, 11, 0, 1, 29, edge)
    a[42:71, 0:12] = t
    # right side tile: list edge, scrollbar groove at 5..12, outer edge
    t = new(20, 29, side)
    rect(t, 0, 0, 1, 29, edge)
    rect(t, 19, 0, 1, 29, edge)
    rect(t, 4, 0, 10, 29, T["track"])
    rect(t, 4, 0, 1, 29, T["track_rim"])
    rect(t, 13, 0, 1, 29, T["track_rim"])
    a[42:71, 31:51] = t
    t = new(9, 9, side)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        thumb(a, x, 53, 8, 18, sel, grip="h")

    def bottom_base(w):
        t = new(w, 38, side)
        rect(t, 0, 0, w, 1, edge)
        rect(t, 0, 37, w, 1, edge)
        if KEY == "myspace":
            rect(t, 0, 33, w, 4, T["accent_bg"])
            rect(t, 0, 32, w, 1, H("ff9933"))
        elif KEY == "facebook-2006":
            rect(t, 0, 33, w, 1, T["panel2"])
        else:
            rect(t, 0, 34, w, 1, lerp(side, T["border"], 0.5))
        return t

    def text_button(t, bx, by, w, h, lbl):
        if KEY == "myspace":
            button_face(t, bx, by, w, h, False)
            text_center(t, TINY, lbl, bx + w // 2, by + (h - 5) // 2, T["btn_ink"])
        elif KEY == "facebook-2006":
            button_face(t, bx, by, w, h, False)
            text_center(t, TINY, lbl, bx + w // 2, by + (h - 5) // 2, WHITE)
        else:
            button_face(t, bx, by, w, h, False)
            text_center(t, TINY, lbl, bx + w // 2 + 1, by + (h - 5) // 2 + 1, T["btn_rim"])
            text_center(t, TINY, lbl, bx + w // 2, by + (h - 5) // 2, WHITE)

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, edge)
    rect(t, 1, 0, 11, 1, side)
    rect(t, 11, 0, 1, 1, edge)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        text_button(t, bx, 8, 22, 18, lbl)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, edge)
    rect(t, 130, 0, 19, 1, side)
    rect(t, 130, 0, 1, 1, edge)
    display_box(t, 6, 9, 56, 8)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        mini_face(t, bx, 22)
        mini_transport_icon(t, kind, bx, 22)
    display_box(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, T["ink"])
    rect(t, 84, 22 + 5, 1, 1, T["ink"])
    text_button(t, 106, 8, 22, 18, "LIST")
    grip = T["border"]
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx, gy, grip)
            px(t, gx + 1, gy + 1, lerp(grip, side, 0.5))
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


def mini_face(t, bx, by):
    if KEY == "neopets":
        rrect(t, bx, by, 10, 10, None, T["btn_rim"], 1, grad=(T["btn_top"], T["btn"]))
    elif KEY == "facebook-2006":
        rect(t, bx, by, 10, 10, T["btn"])
        bevel(t, bx, by, 10, 10, T["btn_hi"], T["btn_lo"])
    else:
        rect(t, bx, by, 10, 10, WHITE)
        frame(t, bx, by, 10, 10, T["btn_rim"])


def mini_transport_icon(a, kind, x, y):
    ink = T["btn_ink"]
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
    side = frame_side()
    edge = T["border"]
    a = new(194, 109, side)
    for lit, y in ((True, 0), (False, 21)):
        for px0 in (0, 26, 52, 78, 104, 130):
            t = bar20(25, lit)
            if px0 == 130:
                mini_button(t, 14, 3, "close", lit)
            a[y:y + 20, px0:px0 + 25] = t

    def bottom(w, grip, left_edge):
        t = new(w, 14, side)
        rect(t, 0, 13, w, 1, edge)
        if KEY == "myspace":
            rect(t, 0, 9, w, 4, T["accent_bg"])
            rect(t, 0, 8, w, 1, H("ff9933"))
        if left_edge:
            rect(t, 0, 0, 1, 14, edge)
        else:
            rect(t, w - 1, 0, 1, 14, edge)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 7 - 3 * j
                    px(t, gx, gy, T["border"])
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h, side)
        if outer_left:
            rect(t, 0, 0, 1, h, edge)
            rect(t, w - 1, 0, 1, h, edge)
        else:
            rect(t, w - 1, 0, 1, h, edge)
            rect(t, 0, 0, 1, h, edge)
        a[42:42 + h, x:x + w] = t
    t = new(9, 9, side)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: cells cut from the titlebar's own rows 4..10, so the title sits seamlessly
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        bar = bar20(194, lit)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            a[y:y + 7, x:x + w] = bar[4:11, x:x + w]
            draw_text(a, FONT5, c, x, y + 1, T["bar_ink"] if lit else T["bar_ink_dim"])
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------


def genex_colours():
    g = T["genex"]
    return [g["item_bg"], g["item_fg"], g["win_bg"], g["btn_fg"], g["win_fg"], g["divider"], g["sel"],
            g["head_bg"], g["head_fg"], g["head_hi"], g["head_lo"], g["head_pr"], g["dead"], g["sb"], g["sb2"],
            g["sb_pr"], g["sb_pr2"], g["sb_dead"]]


def make_genex():
    a = new(256, 64, T["genex"]["win_bg"])
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    bg = T["genex"]["win_bg"]
    rect(a, 0, 1, 47, 30, bg)
    button_face(a, 0, 1, 47, 15, False)
    button_face(a, 0, 16, 47, 15, True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    disp = T["disp"]
    dots = lerp(disp, T["ink"], 0.12)
    out = [(disp, "background"), (dots, "dots")]
    for i in range(16):
        out.append((ramp(T["vis_ramp"], i / 15), f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}"))
    for i, c in enumerate(T["osc"]):
        out.append((c, f"oscilloscope {i + 1}"))
    out.append((T["peak"], "peaks"))
    return out


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    normal, current, nbg, sbg = T["pledit"]
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={normal}\nCurrent={current}\nNormalBG={nbg}\nSelectedBG={sbg}\n"
                f"MbBG={nbg}\nMbFG={normal}\nFont=Arial\n")
    site = T["name"].split("-")[0]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{site} — a skin in the style of {site}, drawn from scratch (apart from the logo).\n"
            f"\n"
            f"A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py) from\n"
            f"rectangles and hand-made pixel fonts, except the {site} wordmark in the main titlebar.\n\n"
            f"{site} logo © {T['company'].rstrip('.')}.\n"
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
    for name, arr in sheets.items():
        SHEETS[name[:-4]] = save(arr, name)
    write_text_files()
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "readme.txt"]
    wsz = os.path.join(HERE, T["wsz"])
    with zipfile.ZipFile(wsz, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2006, 6, 6, 0, 0, 0))
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
for _k, _v in {"<": "[", ">": "]", "{": "[", "}": "]"}.items():
    FONT_LOOKUP[_k] = FONT_LOOKUP[_v]


def draw_bitmap_text(dst, s, x, y):
    text = SHEETS["text"]
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, text, (col * 5, row * 6, 5, 6), x, y)
        x += 5


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
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    draw_bitmap_text(img, state["title"][:30], 111, 24)
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
    normal, current, nbg, sbg = (H(c) for c in T["pledit"])
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=nbg)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 9)
    except OSError:
        font = ImageFont.load_default()
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=sbg)
        col = current if i == 1 else normal
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
    arr = np.array(pic).astype(np.float32)[..., :1] / 255
    c0, c1 = (np.array(c, np.float32) for c in T["art"])
    col = c0 + (c1 - c0) * arr
    img.paste(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)), (11, 20))
    return img


PREVIEW_ROWS = {
    "myspace": [("Bedroom Demo - Track 1 (acoustic)", "3:12"), ("The Band Page - Profile Song", "3:58"),
                ("Friend Request - Top 8", "4:05"), ("Glitter Text - Hearts", "2:51"),
                ("Away Message - Brb", "3:40"), ("Layout Code - Div Overlay", "3:21"),
                ("Bulletin Board - Repost This", "3:33"), ("Thanks For The Add", "3:09"),
                ("Mood: Listening", "3:28"), ("Picture Comments", "2:47"), ("Online Now", "3:16")],
    "facebook-2006": [("Poke - You Have Been Poked", "3:02"), ("The Wall - Write Something", "4:10"),
                      ("Mini-Feed - Status Update", "3:44"), ("Is Listening To Music", "2:59"),
                      ("Group: 1,000,000 Strong", "3:31"), ("Relationship Status", "4:20"),
                      ("Dorm Room Sessions", "3:15"), ("Network - Class Of 2009", "3:48"),
                      ("Tagged In 3 Photos", "2:44"), ("Courses - Spring Term", "3:37"),
                      ("Friend Details", "3:05")],
    "neopets": [("Battledome - Victory Fanfare", "2:12"), ("Faerieland Lullaby", "3:41"),
                ("Neopian Plaza Theme", "2:58"), ("Daily Freebies Jingle", "1:47"),
                ("Shop Wizard Waltz", "3:05"), ("Haunted Woods - Night", "4:12"),
                ("Tyrannian Drums", "2:33"), ("Mystery Island Breeze", "3:22"),
                ("Lost Desert Caravan", "3:50"), ("Kiko Lake Splash", "2:27"),
                ("Altador Cup Anthem", "3:18")],
}
PREVIEW_TITLE = {"myspace": "THANKS FOR THE ADD! (ACOUSTIC)  ***",
                 "facebook-2006": "IS LISTENING TO MUSIC  ***",
                 "neopets": "NEOPIAN PLAZA THEME  ***"}


def preview():
    rows = PREVIEW_ROWS[KEY]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=PREVIEW_TITLE[KEY], bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="PAUSED: AWAY FROM KEYBOARD", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
    out.save(os.path.join(HERE, f"preview-{KEY}.png"))


def run(key):
    global T, KEY, OUT
    KEY, T = key, THEMES[key]
    LOGO_CACHE.clear()
    SHEETS.clear()
    OUT = os.path.join(HERE, "out", key)
    os.makedirs(OUT, exist_ok=True)
    names = build()
    preview()
    for n in names:
        if n.endswith(".bmp"):
            im = Image.open(os.path.join(OUT, n))
            assert im.mode == "RGB", (n, im.mode)
    # the title box is blanked with text.bmp's space cell: it must be the display colour
    assert SHEETS["text"].getpixel((152, 2)) == T["disp"] == SHEETS["main"].getpixel((200, 27)), key
    print(f"{key:14s} -> {T['wsz']}, preview-{key}.png")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        print("\n".join(THEME_KEYS))
        sys.exit(0)
    keys = []
    for a in args:
        if a in ("all", "--all"):
            keys = THEME_KEYS[:]
        elif a in THEME_KEYS:
            keys.append(a)
        else:
            sys.exit(f"unknown theme {a!r}; try --list")
    for k in keys or THEME_KEYS:
        run(k)
