#!/usr/bin/python3
"""Web Classic: classic Winamp 2.x skins in the style of four 2000s websites.

Forked from skins/ember/gen_skin.py (same sheets, same layouts, same preview logic), with one
theme per site:

    deviantart   deviantART v5/v6 (2005-2010): dark green-grey header, #dae4d9 body, the green
                 "dA" mark, gallery-thumbnail frames, the bevelled "devious" tabs
    what-cd      What.CD in Gazelle's "Kuro" stylesheet: #222/#303030 greys, the WHAT.CD logo,
                 menu tabs, the user-stats bar with its red-to-green ratio colours
    gmail-2004   early Gmail (2004-2010): white, the #c3d9ff inbox frame, #e8eef7 read rows,
                 the red/blue logo, "Compose Mail", the light-blue selected row
    reddit       old.reddit.com: the #cee3f8 header with the alien and tabs, blue links,
                 orangered/periwinkle vote arrows as the toggles

    /usr/bin/python3 -I gen_skin.py                 # every theme
    /usr/bin/python3 -I gen_skin.py reddit          # just this one
    /usr/bin/python3 -I gen_skin.py --list

Everything is drawn here from code, except the deviantART "dA" mark and the WHAT.CD logo, which
are cut at build time from source/ (see README.md). Private use only. Each theme writes its
sheets into out/<theme>/, zips them flat into <Name>.wsz and draws preview-<theme>.png beside
this script.
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
SRC = os.path.join(HERE, "source")
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
    "deviantart": dict(
        name="deviantArt", site="deviantART", company="DeviantArt, Inc.", wsz="deviantArt.wsz",
        body=H("dae4d9"), side=H("b4c0b3"), edge=H("475149"),
        bar_ink=WHITE, bar_ink_dim=H("c9d2c8"),
        disp=H("f6f8f5"), disp_rim=H("8d9b8e"), ink=H("2c3a30"), ink_dim=H("dfe6de"), ink_mid=H("7e907f"),
        digit=H("3b4a3f"), play=H("5eac74"),
        label=H("4b5d50"),
        btn=(H("f6f8f5"), H("c9d4c8")), btn_pr=(H("b4c0b3"), H("cdd7cc")), btn_rim=H("7e907f"),
        btn_rim_pr=H("475149"), btn_round=1, btn_hi=WHITE, btn_ink=H("475149"), btn_ink_pr=H("2c3a30"),
        mb=H("5d6e61"), mb_dim=H("8c988e"), mb_pr=H("2f3a32"), mb_rim=H("2f3a32"), mb_rim_dim=H("6f7c72"),
        mb_ink=H("dae4d9"), mb_ink_dim=H("dfe6de"),
        track=H("f6f8f5"), track_rim=H("8d9b8e"), level=[H("c7e6cf"), H("5eac74"), H("3d7a52")],
        thumb=(H("ffffff"), H("c9d4c8")), thumb_pr=(H("eef5b8"), H("c7d92f")), thumb_rim=H("6f7c72"),
        grip=H("8d9b8e"),
        vis_ramp=[H("c7d92f"), H("8fc23f"), H("5eac74"), H("3d7a52"), H("2e4a36")],
        osc=[H("2e4a36"), H("3d7a52"), H("5eac74"), H("8fc23f"), H("c7d92f")], peak=H("475149"),
        pledit=("#2C3A30", "#1F7A3F", "#F6F8F5", "#C9D4C8"),
        genex=dict(item_bg=H("f6f8f5"), item_fg=H("2c3a30"), win_bg=H("dae4d9"), btn_fg=H("475149"),
                   win_fg=H("2c3a30"), divider=H("b4c0b3"), sel=H("c9d4c8"), head_bg=H("475149"),
                   head_fg=WHITE, head_hi=H("6d7b70"), head_lo=H("2f3a32"), head_pr=H("3e4a40"),
                   dead=H("dae4d9"), sb=H("c9d4c8"), sb2=H("7e907f"), sb_pr=H("b4c0b3"), sb_pr2=H("475149"),
                   sb_dead=H("dae4d9")),
        art=(H("9ec3b0"), H("2e4a36")),
    ),
    "what-cd": dict(
        name="What-cd", site="What.CD", company="What.CD", wsz="What-cd.wsz",
        body=H("303030"), side=H("282828"), edge=H("121212"),
        bar_ink=WHITE, bar_ink_dim=H("8a8a8a"),
        disp=H("1c1c1c"), disp_rim=H("121212"), ink=H("cccccc"), ink_dim=H("333333"), ink_mid=H("777777"),
        digit=H("cccccc"), play=H("74c42e"),
        label=H("999999"),
        btn=(H("4c4c4c"), H("404040")), btn_pr=(H("2a2a2a"), H("303030")), btn_rim=H("1c1c1c"),
        btn_rim_pr=H("121212"), btn_round=0, btn_hi=H("5a5a5a"), btn_ink=WHITE, btn_ink_pr=H("74c42e"),
        mb=H("454545"), mb_dim=H("333333"), mb_pr=H("222222"), mb_rim=H("121212"), mb_rim_dim=H("1c1c1c"),
        mb_ink=H("cccccc"), mb_ink_dim=H("777777"),
        track=H("1c1c1c"), track_rim=H("121212"),
        # the ratio colours, r00 (red) to r99 (green)
        level=[H("ff0000"), H("ff5e00"), H("ffaa00"), H("74c42e"), H("418b00")],
        thumb=(H("5a5a5a"), H("454545")), thumb_pr=(H("8bd04a"), H("418b00")), thumb_rim=H("121212"),
        grip=H("2a2a2a"),
        vis_ramp=[H("74c42e"), H("418b00"), H("ffaa00"), H("ff5e00"), H("ff1300")],
        osc=[H("ffffff"), H("cccccc"), H("aaaaaa"), H("777777"), H("555555")], peak=H("ffffff"),
        pledit=("#CCCCCC", "#FFFFFF", "#222222", "#454545"),
        genex=dict(item_bg=H("222222"), item_fg=H("cccccc"), win_bg=H("303030"), btn_fg=WHITE,
                   win_fg=H("cccccc"), divider=H("121212"), sel=H("454545"), head_bg=H("121212"),
                   head_fg=WHITE, head_hi=H("454545"), head_lo=H("000000"), head_pr=H("303030"),
                   dead=H("282828"), sb=H("454545"), sb2=H("777777"), sb_pr=H("555555"), sb_pr2=H("aaaaaa"),
                   sb_dead=H("222222")),
        art=(H("454545"), H("121212")),
    ),
    "gmail-2004": dict(
        name="Gmail-2004", site="Gmail", company="Google LLC", wsz="Gmail-2004.wsz",
        body=WHITE, side=H("c3d9ff"), edge=H("a2bae7"),
        bar_ink=BLACK, bar_ink_dim=H("6f7b93"),
        disp=WHITE, disp_rim=H("a2bae7"), ink=BLACK, ink_dim=H("e8eef7"), ink_mid=H("777777"),
        digit=BLACK, play=H("0000cc"),
        label=H("0000cc"),
        btn=(H("fdfdfd"), H("e0e0e0")), btn_pr=(H("cfcfcf"), H("e6e6e6")), btn_rim=H("8e8e8e"),
        btn_rim_pr=H("666666"), btn_round=1, btn_hi=WHITE, btn_ink=H("222222"), btn_ink_pr=H("0000cc"),
        mb=H("e8eef7"), mb_dim=H("f4f6fa"), mb_pr=H("c3d9ff"), mb_rim=H("a2bae7"), mb_rim_dim=H("d3dceb"),
        mb_ink=H("0000cc"), mb_ink_dim=H("9aa6c0"),
        track=WHITE, track_rim=H("a2bae7"), level=[H("c3d9ff"), H("6a8fd8"), H("3366cc")],
        thumb=(H("fdfdfd"), H("dcdcdc")), thumb_pr=(H("e8eef7"), H("a2bae7")), thumb_rim=H("8e8e8e"),
        grip=H("9a9a9a"),
        vis_ramp=[H("d93025"), H("f2b200"), H("2e9a3a"), H("3c64c4"), H("2a4a9a")],
        osc=[H("3c64c4"), H("3c64c4"), H("d93025"), H("f2b200"), H("2e9a3a")], peak=H("d93025"),
        pledit=("#000000", "#0000CC", "#FFFFFF", "#C3D9FF"),
        genex=dict(item_bg=WHITE, item_fg=BLACK, win_bg=WHITE, btn_fg=BLACK, win_fg=BLACK,
                   divider=H("c3d9ff"), sel=H("c3d9ff"), head_bg=H("c3d9ff"), head_fg=BLACK,
                   head_hi=H("e8eef7"), head_lo=H("a2bae7"), head_pr=H("a2bae7"), dead=WHITE,
                   sb=H("e8eef7"), sb2=H("a2bae7"), sb_pr=H("c3d9ff"), sb_pr2=H("3366cc"), sb_dead=WHITE),
        art=(H("e8eef7"), H("3366cc")),
    ),
    "reddit": dict(
        name="Reddit-Classic", site="reddit", company="Reddit, Inc.", wsz="Reddit-Classic.wsz",
        body=WHITE, side=H("eff7ff"), edge=H("5f99cf"),
        bar_ink=BLACK, bar_ink_dim=H("7f8c99"),
        disp=H("eff7ff"), disp_rim=H("cee3f8"), ink=H("0000ff"), ink_dim=H("dde9f5"), ink_mid=H("888888"),
        digit=H("336699"), play=H("ff4500"),
        label=H("336699"),
        btn=(H("eff7ff"), H("eff7ff")), btn_pr=(H("cee3f8"), H("cee3f8")), btn_rim=H("5f99cf"),
        btn_rim_pr=H("336699"), btn_round=0, btn_hi=None, btn_ink=H("336699"), btn_ink_pr=H("ff4500"),
        mb=H("eff7ff"), mb_dim=H("f2f5f8"), mb_pr=H("cee3f8"), mb_rim=H("5f99cf"), mb_rim_dim=H("a9bccd"),
        mb_ink=H("336699"), mb_ink_dim=H("a9bccd"),
        track=WHITE, track_rim=H("cee3f8"), level=[H("ffd2c2"), H("ff8b60"), H("ff4500")],
        level_bal=[H("dcdcff"), H("b4b4ff"), H("9494ff")],
        thumb=(H("ffffff"), H("cee3f8")), thumb_pr=(H("ffb399"), H("ff4500")), thumb_rim=H("5f99cf"),
        grip=H("5f99cf"),
        vis_ramp=[H("ff4500"), H("ff8b60"), H("c6c6ff"), H("9494ff"), H("5f99cf")],
        osc=[H("ff4500"), H("ff8b60"), H("9494ff"), H("5f99cf"), H("336699")], peak=H("ff4500"),
        pledit=("#0000FF", "#FF4500", "#FFFFFF", "#CEE3F8"),
        genex=dict(item_bg=WHITE, item_fg=H("0000ff"), win_bg=WHITE, btn_fg=H("336699"), win_fg=H("222222"),
                   divider=H("cee3f8"), sel=H("cee3f8"), head_bg=H("cee3f8"), head_fg=BLACK,
                   head_hi=H("eff7ff"), head_lo=H("5f99cf"), head_pr=H("5f99cf"), dead=WHITE,
                   sb=H("eff7ff"), sb2=H("5f99cf"), sb_pr=H("cee3f8"), sb_pr2=H("336699"), sb_dead=WHITE),
        art=(H("cee3f8"), H("ff4500")),
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


def round_mask(w, h, r, top=True, bottom=True):
    """Corner cut-outs: r=1 drops the corner pixel, r=2 two then one, r=3 three, one, one."""
    m = np.ones((h, w), dtype=bool)
    insets = {1: [1], 2: [2, 1], 3: [3, 1, 1]}.get(r, [])
    for i, inset in enumerate(insets):
        if top:
            m[i, :inset] = False
            m[i, w - inset:] = False
        if bottom:
            m[h - 1 - i, :inset] = False
            m[h - 1 - i, w - inset:] = False
    return m


def rrect(a, x, y, w, h, fill, border=None, r=2, grad=None, top=True, bottom=True):
    """Rounded rectangle; fill is a colour, or grad=(top, bottom) a vertical gradient."""
    m = round_mask(w, h, r, top, bottom)
    sub = a[y:y + h, x:x + w]
    if grad:
        for k in range(h):
            sub[k][m[k]] = lerp(grad[0], grad[1], k / max(1, h - 1))
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
        if not bottom:
            e[-1, 1:-1] = m[-1, 1:-1]
        sub[m & ~e] = border


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def sprite(a, x, y, rows, pal):
    """Pixel art from strings; pal maps a character to a colour ('.' is left alone)."""
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch in pal:
                px(a, x + c, y + r, pal[ch])


# ------------------------------------------------------------------------------------------
# Pixel fonts (FONT5/TINY from Ember; the 9-row web font after web-nostalgia's)
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

# a few glyphs the web font needs here
WEB["("] = W9(0, ".#", "#.", "#.", "#.", "#.", "#.", "#.", ".#")
WEB[")"] = W9(0, "#.", ".#", ".#", ".#", ".#", ".#", ".#", "#.")
WEB[":"] = W9(3, "#", ".", ".", "#")
WEB[","] = W9(6, ".#", "#.")
WEB["/"] = W9(0, "...#", "...#", "..#.", "..#.", ".#..", ".#..", "#...")
WEB["?"] = W9(0, ".##.", "#..#", "...#", "..#.", ".#..", "....", ".#..")
for _c in "():,/?":
    WEB_B[_c] = bold(WEB[_c])
WEB_B["("] = WEB["("]
WEB_B[")"] = WEB[")"]
TINY[":"] = FONT5[":"]
TINY["J"] = G("..#", "..#", "..#", "#.#", ".#.")
TINY["/"] = FONT5["/"]


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1, shadow=None, underline=None):
    x0 = x
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
    if underline is not None:
        rect(a, x0, y + underline, x - gap - x0, 1, col)
    return x


def text_center(a, font, s, cx, y, col, gap=1, shadow=None):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow)


# ------------------------------------------------------------------------------------------
# Logos and marks
# ------------------------------------------------------------------------------------------


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


def _shrink(cov, rgb, height, firm=True):
    """Resizes a coverage map (and premultiplied colour) to `height` pixels tall."""
    h0, w0 = cov.shape
    w = max(1, round(w0 * height / h0))
    ci = Image.fromarray((np.clip(cov, 0, 1) * 255).astype(np.uint8), "L").resize((w, height), Image.LANCZOS)
    c = np.asarray(ci).astype(np.float32) / 255
    if firm:
        c = np.clip((c - 0.12) / 0.70, 0, 1)
    col = None
    if rgb is not None:
        pre = rgb * cov[..., None]
        ri = Image.fromarray(np.clip(pre, 0, 255).astype(np.uint8), "RGB").resize((w, height), Image.LANCZOS)
        ai = np.maximum(np.asarray(ci).astype(np.float32) / 255, 1e-3)
        col = np.clip(np.asarray(ri).astype(np.float32) / ai[..., None], 0, 255)
    return c, col


def logo_whatcd(height):
    """The WHAT.CD lettering from Gazelle's Kuro stylesheet (its mirror reflection dropped)."""
    arr = np.asarray(Image.open(os.path.join(SRC, "whatcd-gazelle", "kuro-logo.png")).convert("RGBA")).astype(
        np.float32)
    alpha = arr[..., 3] / 255
    rows = _bands(alpha > 0.6, 1)
    y0, y1 = rows[0]
    cols = _bands(alpha[y0:y1] > 0.3, 0)
    x0, x1 = cols[0][0], cols[-1][1]
    return _shrink(alpha[y0:y1, x0:x1], arr[y0:y1, x0:x1, :3], height)


def logo_da(height):
    """The green "dA" mark, cut out of its frame in the 2010-2014 icon."""
    arr = np.asarray(Image.open(os.path.join(SRC, "commons-deviantart", "DeviantArt_logo.png")).convert(
        "RGBA")).astype(np.float32)[..., :3]
    lime = (arr[..., 1] > 150) & (arr[..., 0] > 110) & (arr[..., 2] < 120)
    ys, xs = np.nonzero(lime)
    fy0, fy1, fx0, fx1 = ys.min(), ys.max(), xs.min(), xs.max()
    mid = (fx0 + fx1) // 2
    run = 0
    while lime[fy0 + run, mid]:
        run += 1
    inset = run + 3
    sub = arr[fy0 + inset:fy1 - inset, fx0 + inset:fx1 - inset]
    bg_g, lime_g = 93.0, float(arr[lime][:, 1].mean())
    cov = np.clip((sub[..., 1] - bg_g) / (lime_g - bg_g), 0, 1)
    m = cov > 0.5
    rr, cc = _bands(m, 1), _bands(m, 0)
    cov = cov[rr[0][0]:rr[-1][1], cc[0][0]:cc[-1][1]]
    return _shrink(cov, None, height)


def logo_reddit_word(height):
    """The old lowercase "reddit" wordmark."""
    os.makedirs(SCRATCH, exist_ok=True)
    png = os.path.join(SCRATCH, "reddit-word.png")
    subprocess.run(["/usr/bin/rsvg-convert", "-h", "400", os.path.join(SRC, "commons-reddit", "Reddit_Old.svg"),
                    "-o", png], check=True)
    arr = np.asarray(Image.open(png).convert("RGBA")).astype(np.float32)
    # dark strokes; the white hole in the i's dot counts as ink too
    cov = (arr[..., 3] / 255)
    rr, cc = _bands(cov > 0.3, 1), _bands(cov > 0.3, 0)
    cov = cov[rr[0][0]:rr[-1][1], cc[0][0]:cc[-1][1]]
    return _shrink(cov, None, height)


def paste_logo(a, x, y, alpha, ink=None, rgb=None):
    h, w = alpha.shape
    region = a[y:y + h, x:x + w].astype(np.float32)
    src = rgb if rgb is not None else np.zeros((h, w, 3), np.float32) + np.array(ink, np.float32)
    out = region * (1 - alpha[..., None]) + src * alpha[..., None]
    a[y:y + h, x:x + w] = np.round(out).astype(np.int32)
    return w


SNOO_CACHE = {}


def snoo_grid():
    """Reddit's alien, head only, drawn as shapes at 8x and reduced to a 15x13 pixel sprite."""
    if "g" in SNOO_CACHE:
        return SNOO_CACHE["g"]
    S = 8
    W_, H_ = 15, 13
    layers = {}
    for name in ("black", "white", "orange"):
        layers[name] = Image.new("L", (W_ * S, H_ * S), 0)

    def ell(cx, cy, rx, ry, fill_layer, outline=True, wdt=1.0):
        box = ((cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S)
        if outline:
            ImageDraw.Draw(layers["black"]).ellipse(box, fill=255)
            inner = ((cx - rx + wdt) * S, (cy - ry + wdt) * S, (cx + rx - wdt) * S, (cy + ry - wdt) * S)
            for nm in layers:
                ImageDraw.Draw(layers[nm]).ellipse(inner, fill=255 if nm == fill_layer else 0)
        else:
            for nm in layers:
                ImageDraw.Draw(layers[nm]).ellipse(box, fill=255 if nm == fill_layer else 0)

    d = ImageDraw.Draw(layers["black"])
    d.line([(7.5 * S, 5.5 * S), (8.6 * S, 1.6 * S), (11.0 * S, 1.9 * S)], fill=255, width=int(0.9 * S))
    ell(12.4, 2.0, 1.75, 1.75, "white")
    ell(2.1, 6.4, 1.9, 1.9, "white")
    ell(12.9, 6.4, 1.9, 1.9, "white")
    ell(7.5, 8.6, 6.4, 4.1, "white")
    ell(5.1, 8.0, 1.15, 1.15, "orange", outline=False)
    ell(9.9, 8.0, 1.15, 1.15, "orange", outline=False)
    ImageDraw.Draw(layers["black"]).arc((4.6 * S, 7.6 * S, 10.4 * S, 11.2 * S), 25, 155, fill=255,
                                         width=int(0.8 * S))
    for nm in ("white", "orange"):
        ImageDraw.Draw(layers[nm]).arc((4.6 * S, 7.6 * S, 10.4 * S, 11.2 * S), 25, 155, fill=0, width=int(0.8 * S))
    arrs = {k: np.asarray(v).astype(np.float32).reshape(H_, S, W_, S).mean(axis=(1, 3)) / 255 for k, v in
            layers.items()}
    g = []
    for r in range(H_):
        row = ""
        for c in range(W_):
            b, w, o = arrs["black"][r, c], arrs["white"][r, c], arrs["orange"][r, c]
            if o >= 0.35:
                row += "o"
            elif b >= 0.3:
                row += "#"
            elif w >= 0.4:
                row += "w"
            else:
                row += "."
        g.append(row)
    SNOO_CACHE["g"] = g
    return g


GMAIL = {
    "G": ["..######.", ".##....##", "##.......", "##.......", "##.......", "##..#####", "##.....##",
          "##.....##", "##.....##", ".##....##", "..######."],
    "M": ["##.......##", "###.....###", "##.#...#.##", "##..#.#..##", "##...#...##", "##.......##",
          "##.......##", "##.......##", "##.......##", "##.......##", "#=========#"],
    "a": [".####.", "....##", ".#####", "##..##", "##..##", ".#####"],
    "i": ["##", "..", "##", "##", "##", "##", "##", "##"],
    "l": ["##"] * 11,
}


def gmail_logo(a, x, y, lit=True):
    """The 2004 wordmark: blue G, the red envelope M, then a, i, l; 11 rows tall."""
    if lit:
        blue, red, yel, grn, pap, fold = H("3c64c4"), H("d93025"), H("f2b200"), H("2e9a3a"), WHITE, H("d8d8d8")
    else:
        blue, red, yel, grn, pap, fold = H("9aa9cf"), H("d9a39e"), H("e6d49a"), H("9fc6a4"), WHITE, H("e4e4e4")
    sprite(a, x, y, GMAIL["G"], {"#": blue})
    x += 10
    rect(a, x + 2, y + 1, 7, 9, pap)
    sprite(a, x, y, GMAIL["M"], {"#": red, "=": fold})
    x += 12
    sprite(a, x, y + 5, GMAIL["a"], {"#": yel})
    x += 7
    sprite(a, x, y + 3, GMAIL["i"], {"#": blue})
    x += 3
    sprite(a, x, y, GMAIL["l"], {"#": grn})
    return x + 2


ARROW_UP = ["..#..", ".###.", "#####", ".###.", ".###."]
ARROW_DN = ARROW_UP[::-1]
ARROW7_UP = ["...#...", "..###..", ".#####.", "#######", "..###..", "..###.."]
UPVOTE, DOWNVOTE, NOVOTE = H("ff4500"), H("9494ff"), H("c6c6c6")

STAR = ["....#....", "...###...", "...###...", "#########", ".#######.", "..#####..", "..##.##..", ".##...##.",
        ".#.....#."]


def star(a, x, y, lit=True):
    """Gmail's star: yellow with a darker rim."""
    m = np.array([[ch == "#" for ch in row] for row in STAR])
    h, w = m.shape
    for r in range(h):
        for c in range(w):
            if not m[r, c]:
                continue
            edge = r == 0 or c == 0 or r == h - 1 or c == w - 1 or not (m[r - 1, c] and m[r + 1, c] and m[r, c - 1]
                                                                           and m[r, c + 1])
            col = (H("c79100") if edge else H("ffd34d")) if lit else (H("b0b0b0") if edge else H("e4e4e4"))
            px(a, x + c, y + r, col)


# ------------------------------------------------------------------------------------------
# Theme-specific surfaces
# ------------------------------------------------------------------------------------------


def bar_fill(a, x, y, w, h, lit):
    """The titlebar band, whatever its height (14 for main/EQ, 20 for playlist/gen)."""
    if KEY == "deviantart":
        top, bot = (H("5f6d62"), H("475149")) if lit else (H("a3ada3"), H("929d93"))
        vgrad(a, x, y, w, h, top, bot)
        rect(a, x, y, w, 1, H("76847a") if lit else H("b8c1b8"))
        rect(a, x, y + h - 1, w, 1, H("2f3a32") if lit else H("7a867c"))
    elif KEY == "what-cd":
        rect(a, x, y, w, h, H("1c1c1c") if lit else H("2a2a2a"))
        rect(a, x, y + h - 1, w, 1, H("121212") if lit else H("222222"))
    elif KEY == "gmail-2004":
        if h < 20:
            rect(a, x, y, w, h, WHITE)
        else:
            rect(a, x, y, w, h, H("c3d9ff") if lit else H("e8eef7"))
    else:
        rect(a, x, y, w, h, H("cee3f8") if lit else H("e8eef4"))
        rect(a, x, y + h - 1, w, 1, H("5f99cf") if lit else H("b4c4d4"))


def display_box(a, x, y, w, h):
    """A display window (text/digits sit on T['disp'])."""
    if KEY == "deviantart":
        # a gallery-thumbnail frame: hairline border and a soft drop shadow right and below
        rect(a, x + 1, y + h + 1, w + 1, 1, H("aebaad"))
        rect(a, x + w + 1, y + 1, 1, h + 1, H("aebaad"))
        rect(a, x + 2, y + h + 2, w, 1, H("c6d0c5"))
        rect(a, x + w + 2, y + 2, 1, h, H("c6d0c5"))
        frame(a, x - 1, y - 1, w + 2, h + 2, T["disp_rim"])
        rect(a, x, y, w, h, T["disp"])
    elif KEY == "what-cd":
        rect(a, x - 1, y - 1, w + 2, h + 2, H("121212"))
        rect(a, x - 1, y + h, w + 2, 1, H("454545"))
        rect(a, x + w, y - 1, 1, h + 2, H("3a3a3a"))
        rect(a, x, y, w, h, T["disp"])
    elif KEY == "gmail-2004":
        rrect(a, x - 1, y - 1, w + 2, h + 2, T["disp"], T["disp_rim"], 1)
        rect(a, x, y, w, h, T["disp"])
    else:
        frame(a, x - 1, y - 1, w + 2, h + 2, H("a9c9ea"))
        rect(a, x, y, w, h, T["disp"])


def button_face(a, x, y, w, h, pressed):
    top, bot = T["btn_pr"] if pressed else T["btn"]
    rim = T["btn_rim_pr"] if pressed else T["btn_rim"]
    if T["btn_round"]:
        rrect(a, x, y, w, h, None, rim, T["btn_round"], grad=(top, bot))
    else:
        vgrad(a, x, y, w, h, top, bot)
        frame(a, x, y, w, h, rim)
    if not pressed and T["btn_hi"] is not None:
        rect(a, x + 2, y + 1, w - 4, 1, T["btn_hi"])


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button."""
    face = T["mb_pr"] if pressed else (T["mb"] if lit else T["mb_dim"])
    rim = T["mb_rim"] if lit else T["mb_rim_dim"]
    if KEY in ("deviantart", "gmail-2004"):
        rrect(a, x, y, 9, 9, face, rim, 1)
    else:
        rect(a, x, y, 9, 9, face)
        frame(a, x, y, 9, 9, rim)
    ink = T["mb_ink"] if lit else T["mb_ink_dim"]
    if KEY == "reddit" and pressed:
        ink = UPVOTE
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


def toggle(a, x, y, w, h, label, on, pressed, arrow=True):
    """A small text button whose 'on' state is lit the site's way."""
    o = 1 if pressed else 0
    if KEY == "deviantart":
        # a devious tab: rounded, bevelled, the picked one pale with a green line along its top
        if on:
            grad = (H("e6ede5"), H("d4ddd3")) if pressed else (WHITE, H("e9efe8"))
            rrect(a, x, y, w, h, None, H("475149"), 2, grad=grad, bottom=False)
            rect(a, x + 2, y + 1, w - 4, 1, H("5eac74"))
            ink = H("1f5a35")
        else:
            grad = (H("a9b6a8"), H("bfcabe")) if pressed else (H("d4ddd3"), H("b4c0b3"))
            rrect(a, x, y, w, h, None, H("7e907f"), 2, grad=grad, bottom=False)
            if not pressed:
                rect(a, x + 2, y + 1, w - 4, 1, H("eef3ed"))
            ink = H("5d6e61")
        tw = text_w(TINY, label)
        draw_text(a, TINY, label, x + (w - tw) // 2 + o, y + (h - 5) // 2 + o + (1 if h > 12 else 0), ink)
        return
    if KEY == "what-cd":
        rect(a, x, y, w, h, H("303030") if pressed else H("454545"))
        frame(a, x, y, w, h, H("1c1c1c"))
        if not pressed:
            rect(a, x + 1, y + 1, w - 2, 1, H("555555"))
        ink = WHITE if on else H("999999")
        if on:
            rect(a, x + 2, y + h - 3, w - 4, 1, H("74c42e"))
        tw = text_w(TINY, label)
        draw_text(a, TINY, label, x + (w - tw) // 2 + o, y + (h - 5) // 2 + o - (1 if h > 12 else 0), ink)
        return
    if KEY == "gmail-2004":
        face = H("c3d9ff") if on else WHITE
        if pressed:
            face = H("a2bae7") if on else H("e8eef7")
        rrect(a, x, y, w, h, face, H("a2bae7") if on else H("c3d9ff"), 1)
        ink = H("0000cc") if on else H("8894ad")
        tw = text_w(TINY, label)
        tx = x + (w - tw) // 2 + o
        ty = y + (h - 5) // 2 + o
        draw_text(a, TINY, label, tx, ty, ink)
        if on:
            rect(a, tx, ty + 6, tw, 1, ink)
        return
    # reddit: an orangered upvote when on, a periwinkle downvote when off
    rect(a, x, y, w, h, H("eff7ff") if pressed else WHITE)
    frame(a, x, y, w, h, H("cee3f8") if not pressed else H("5f99cf"))
    ink = H("336699") if on else H("888888")
    tw = text_w(TINY, label)
    if not arrow:
        draw_text(a, TINY, label, x + (w - tw) // 2 + o, y + (h - 5) // 2 + o, ink)
        return
    arr, col = (ARROW_UP, UPVOTE) if on else (ARROW_DN, DOWNVOTE)
    if tw + 7 <= w - 3:
        gx = x + (w - (tw + 7)) // 2 + o
        sprite(a, gx, y + (h - 5) // 2 + o, arr, {"#": col})
        draw_text(a, TINY, label, gx + 7, y + (h - 5) // 2 + o, ink)
    else:
        sprite(a, x + (w - 5) // 2 + o, y + 2 + o, arr, {"#": col})
        draw_text(a, TINY, label, x + (w - tw) // 2 + o, y + 8 + o, ink)


def emblem(a, x, y):
    """13x15 at the About spot."""
    if KEY == "deviantart":
        # a gallery thumbnail: frame, a little landscape, its drop shadow
        rect(a, x + 1, y + 14, 12, 1, H("aebaad"))
        rect(a, x + 12, y + 2, 1, 13, H("aebaad"))
        frame(a, x, y + 1, 12, 13, H("7e907f"))
        rect(a, x + 1, y + 2, 10, 11, WHITE)
        vgrad(a, x + 2, y + 3, 8, 6, H("a8cde0"), H("e3f0f5"))
        for c in range(8):
            hh = 2 + (1 if 2 <= c <= 5 else 0) + (1 if 3 <= c <= 4 else 0)
            rect(a, x + 2 + c, y + 11 - hh, 1, hh, H("5eac74"))
        rect(a, x + 2, y + 11, 8, 1, H("3d7a52"))
        rect(a, x + 7, y + 4, 2, 2, H("f2d14a"))
    elif KEY == "what-cd":
        # a compact disc
        for r in range(13):
            for c in range(13):
                d = ((r - 6) ** 2 + (c - 6) ** 2) ** 0.5
                if d > 6.4:
                    continue
                if d < 1.3:
                    col = H("303030")
                elif d < 2.5:
                    col = H("8a8a8a")
                elif d > 5.6:
                    col = H("6a6a6a")
                else:
                    t = ((np.arctan2(r - 6, c - 6) + np.pi) / (2 * np.pi) * 4) % 1
                    col = lerp(H("b8b8b8"), H("eeeeee"), abs(t - 0.5) * 2)
                px(a, x + c, y + 1 + r, col)
    elif KEY == "gmail-2004":
        star(a, x + 2, y + 3)
    else:
        sprite(a, x + 3, y, ARROW7_UP, {"#": UPVOTE})
        for c in (4, 6, 8):
            px(a, x + c, y + 7, H("c6c6c6"))
        sprite(a, x + 3, y + 9, ARROW7_UP[::-1], {"#": DOWNVOTE})


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]
CLUTTER_ON = {"deviantart": (H("c7e6cf"), H("1f5a35")), "what-cd": (H("454545"), WHITE),
              "gmail-2004": (H("c3d9ff"), H("0000cc")), "reddit": (H("ffe3d9"), UPVOTE)}


def clutter_bar(lit_letters):
    a = new(8, 43, T["disp"])
    frame(a, 0, 0, 8, 43, T["disp_rim"] if KEY != "reddit" else H("a9c9ea"))
    on_bg, on_ink = CLUTTER_ON[KEY]
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, on_bg)
        draw_text(a, TINY, letter, 2, y + (h - 5) // 2, on_ink if on else T["ink_mid"])
    return a


LOGO_CACHE = {}


def logo_cached(name, fn, *args):
    if name not in LOGO_CACHE:
        LOGO_CACHE[name] = fn(*args)
    return LOGO_CACHE[name]


def reddit_tabs(a, right, lit, items=("hot", "new", "top"), picked=0, y0=4, bottom=13):
    """Old reddit's tab menu: tabs standing on the header's bottom line, the picked one white."""
    x = right
    spans = []
    for s in reversed(items):
        w = text_w(WEB_B if s == items[picked] else WEB, s) + 6
        x -= w
        spans.append((x, w, s))
        x -= 2
    for x, w, s in spans:
        sel = s == items[picked]
        face = WHITE if sel else (H("eff7ff") if lit else H("f2f5f8"))
        rect(a, x, y0, w, bottom - y0 + 1, face)
        rect(a, x, y0, w, 1, H("5f99cf") if lit else H("b4c4d4"))
        rect(a, x, y0, 1, bottom - y0, H("5f99cf") if lit else H("b4c4d4"))
        rect(a, x + w - 1, y0, 1, bottom - y0, H("5f99cf") if lit else H("b4c4d4"))
        if sel:
            rect(a, x + 1, bottom, w - 2, 1, WHITE)
        ink = (UPVOTE if sel else H("336699")) if lit else H("9aa8b6")
        draw_text(a, WEB_B if sel else WEB, s, x + 3, y0 + 1, ink)
    return spans[-1][0]


def da_tabs(a, x, y, items, picked, lit, h=11):
    """Devious tabs on the dark header: rounded tops, a bevel, the picked one the page's colour."""
    for i, s in enumerate(items):
        sel = i == picked
        font = WEB_B if sel else WEB
        w = text_w(font, s) + 8
        if sel:
            face = (H("eef3ed"), H("dae4d9")) if lit else (H("c9d2c8"), H("bcc6bb"))
            rim = H("2f3a32") if lit else H("7a867c")
        else:
            face = (H("76847a"), H("5d6b60")) if lit else (H("a6b0a7"), H("97a298"))
            rim = H("2f3a32") if lit else H("8c988e")
        rrect(a, x, y, w, h, None, rim, 2, grad=face, bottom=False)
        rect(a, x + 2, y + 1, w - 4, 1, lerp(face[0], WHITE, 0.5))
        ink = (H("2c3a30") if sel else H("e9efe8")) if lit else (H("5d6e61") if sel else H("e4e9e3"))
        draw_text(a, font, s, x + 4, y + 1, ink)
        x += w + 1
    return x


def whatcd_menu(a, items, picked, lit, y=2, h=12):
    """Kuro's menu: #454545 tabs on #222, the current page's tab the content colour."""
    ws = [text_w(WEB, s) + 10 for s in items]
    total = sum(ws) + (len(ws) - 1)
    x = (275 - total) // 2
    for i, (s, w) in enumerate(zip(items, ws)):
        sel = i == picked
        face = (H("303030") if sel else H("454545")) if lit else (H("333333") if sel else H("3a3a3a"))
        rect(a, x, y, w, h, face)
        ink = WHITE if lit else H("8a8a8a")
        draw_text(a, WEB, s, x + 5, y + 1, ink)
        x += w + 1


def main_titlebar(lit):
    a = new(275, 14)
    bar_fill(a, 0, 0, 275, 14, lit)
    if KEY == "deviantart":
        al, _ = logo_cached("da", logo_da, 10)
        x = 19
        paste_logo(a, x, 2, al, H("c7d92f") if lit else H("c8cfc4"))
        x += al.shape[1] + 4
        ink = WHITE if lit else H("e4e9e3")
        x = draw_text(a, WEB, "deviant", x, 3, ink)
        draw_text(a, WEB_B, "ART", x + 1, 3, ink)
        tag = "where ART meets application!"
        draw_text(a, WEB, tag, 238 - text_w(WEB, tag), 3, H("aab5aa") if lit else H("c4ccc3"))
    elif KEY == "what-cd":
        al, rgb = logo_cached("whatcd", logo_whatcd, 9)
        lw = al.shape[1]
        lx = (275 - lw) // 2
        if lit:
            paste_logo(a, lx, 2, al, rgb=rgb)
        else:
            paste_logo(a, lx, 2, al, H("6a6a6a"))
        for gx0, gx1 in ((20, lx - 8), (lx + lw + 8, 238)):
            for gx in range(gx0, gx1, 2):
                px(a, gx, 6, H("303030") if lit else H("333333"))
    elif KEY == "gmail-2004":
        x = gmail_logo(a, 19, 1, lit)
        draw_text(a, TINY, "BETA", x + 1, 7, H("888888") if lit else H("bbbbbb"))
        links = ["Settings", "Help", "Sign out"]
        x = 238
        for i, s in enumerate(reversed(links)):
            x -= text_w(WEB, s)
            draw_text(a, WEB, s, x, 2, H("0000cc") if lit else H("8f9bc6"), underline=8)
            if i < len(links) - 1:
                x -= 8
                draw_text(a, WEB, "|", x + 3, 2, H("888888") if lit else H("cccccc"))
    else:
        g = snoo_grid()
        pal = {"#": BLACK, "w": WHITE, "o": UPVOTE} if lit else {"#": H("8c98a4"), "w": WHITE, "o": H("e0b8a8")}
        sprite(a, 17, 0, g, pal)
        al, _ = logo_cached("rword", logo_reddit_word, 9)
        paste_logo(a, 34, 3, al, BLACK if lit else H("8c98a4"))
        reddit_tabs(a, 238, lit)
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


def draw_digit(a, x, y, n):
    rect(a, x, y, 9, 13, T["disp"])
    if n is None:
        return
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + 1 + c, y + 1 + r, T["digit"])


def whatcd_stats(a, y):
    """The user-stats bar: Up, Down, Ratio (in its ratio colour), Required."""
    rect(a, 1, y, 273, 7, H("1c1c1c"))
    parts = [("UP:", H("777777")), ("1.21 TB", H("aaaaaa")), ("DOWN:", H("777777")), ("298 GB", H("aaaaaa")),
             ("RATIO:", H("777777")), ("4.07", H("74c42e")), ("REQUIRED:", H("777777")), ("0.60", H("aaaaaa"))]
    total = sum(text_w(TINY, s) for s, _ in parts) + 3 * (len(parts) - 1) + 6 * 3
    x = (275 - total) // 2
    for i, (s, col) in enumerate(parts):
        x = draw_text(a, TINY, s, x, y + 1, col) + (3 if i % 2 == 0 else 9)


def make_main():
    a = new(275, 116, T["body"])
    a[0:14, :] = main_titlebar(True)
    if KEY == "deviantart":
        rect(a, 0, 14, 1, 102, T["edge"])
        rect(a, 274, 14, 1, 102, T["edge"])
        rect(a, 0, 115, 275, 1, T["edge"])
        rect(a, 1, 14, 273, 1, H("eef3ed"))
        rrect(a, 12, 85, 239, 24, H("e9efe8"), H("b4c0b3"), 2)
        rect(a, 4, 111, 267, 1, H("c4cec3"))
    elif KEY == "what-cd":
        rect(a, 0, 14, 1, 102, T["edge"])
        rect(a, 274, 14, 1, 102, T["edge"])
        rect(a, 0, 115, 275, 1, T["edge"])
        rect(a, 4, 16, 267, 68, H("282828"))
        frame(a, 4, 16, 267, 68, H("222222"))
        rect(a, 12, 85, 239, 22, H("222222"))
        whatcd_stats(a, 108)
    elif KEY == "gmail-2004":
        rrect(a, 2, 15, 271, 99, H("c3d9ff"), None, 3)
        rect(a, 13, 85, 236, 1, H("a2bae7"))
    else:
        rect(a, 0, 14, 1, 102, H("cee3f8"))
        rect(a, 274, 14, 1, 102, H("cee3f8"))
        rect(a, 1, 110, 273, 5, H("eff7ff"))
        rect(a, 1, 109, 273, 1, H("cee3f8"))
        rect(a, 0, 115, 275, 1, H("cee3f8"))
        rect(a, 13, 85, 236, 1, H("e6e6e6"))
    a[22:65, 10:18] = clutter_bar("")
    display_box(a, 21, 20, 84, 42)
    for x in (48, 60, 78, 90):
        draw_digit(a, x, 26, None)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, T["digit"])
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
    o = 1 if pressed else 0
    cx, cy = x + w // 2 + o, y + h // 2 + o
    if kind == "previous":
        rect(a, cx - 6, cy - 3, 2, 7, ink)
        tri_left(a, cx - 4, cy - 3, 7, ink)
        tri_left(a, cx, cy - 3, 7, ink)
    elif kind == "play":
        tri_right(a, cx - 2, cy - 4, 9, ink)
    elif kind == "pause":
        rect(a, cx - 4, cy - 3, 3, 7, ink)
        rect(a, cx + 1, cy - 3, 3, 7, ink)
    elif kind == "stop":
        rect(a, cx - 3, cy - 3, 7, 7, ink)
    elif kind == "next":
        tri_right(a, cx - 5, cy - 3, 7, ink)
        tri_right(a, cx - 1, cy - 3, 7, ink)
        rect(a, cx + 3, cy - 3, 2, 7, ink)
    elif kind == "eject":
        for r in range(4):
            rect(a, cx - 1 - r, cy - 4 + r, 2 * r + 3, 1, ink)
        rect(a, cx - 4, cy + 1, 9, 2, ink)


def make_cbuttons(main):
    a = new(136, 36, main[95, 30].tolist())
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


def make_shufrep(main):
    a = new(92, 85, main[90, 165].tolist())
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        toggle(a, 0, y, 28, 15, "REPEAT", on, pressed)
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    rect(a, 0, 61, 92, 24, main[58, 218].tolist())
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        toggle(a, x, 61, 23, 12, label, False, pressed)
        toggle(a, x, 73, 23, 12, label, True, pressed)
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T["disp"])
    for y, on in ((0, True), (12, False)):
        col = T["ink"] if on else T["ink_dim"]
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T["disp"])
    tri_right(a, 2, 1, 7, T["play"])
    rect(a, 9 + 2, 1, 2, 7, T["digit"])
    rect(a, 9 + 5, 1, 2, 7, T["digit"])
    rect(a, 18 + 2, 2, 5, 5, T["digit"])
    rect(a, 36, 0, 3, 9, T["disp"])
    rect(a, 39 + 1, 3, 1, 3, T["play"])
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["disp"])
    for n in range(10):
        draw_digit(a, 9 * n, 0, n)
    draw_digit(a, 90, 0, None)
    if ex:
        draw_digit(a, 99, 0, None)
        rect(a, 99 + 2, 6, 5, 2, T["digit"])
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
    if KEY in ("deviantart", "gmail-2004"):
        rrect(a, x, y, w, h, None, T["thumb_rim"], 1, grad=(top, bot))
        rect(a, x + 2, y + 1, w - 4, 1, lerp(top, WHITE, 0.6))
    else:
        vgrad(a, x, y, w, h, top, bot)
        frame(a, x, y, w, h, T["thumb_rim"])
    cx = x + w // 2
    gc = T["grip"] if not selected else lerp(bot, BLACK, 0.3)
    if grip == "v":
        for gx in (cx - 2, cx, cx + 2):
            rect(a, gx, y + 3, 1, h - 6, gc)
    else:
        for gy in (y + h // 2 - 2, y + h // 2, y + h // 2 + 2):
            rect(a, x + 3, gy, w - 6, 1, gc)


def track(a, x, y, w, h):
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
        rect(a, 2, y + 4, fill_to - 2, 5, ramp(T["level"], level))
        rect(a, 0, y + 13, 68, 2, a[y + 12, 0].tolist())
    slider_thumbs(a)
    return a


def make_balance(main):
    a = new(68, 433, T["body"])
    seat = main[57:72, 177:215]
    stops = T.get("level_bal", T["level"])
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        track(a, 10, y + 3, 36, 7)
        t = i / 27
        reach = round(16 * t)
        if reach:
            rect(a, 28 - reach, y + 4, 2 * reach + 1, 5, ramp(stops, t))
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
    if KEY == "deviantart":
        da_tabs(a, 18, 3, ["player", "equalizer", "playlist"], 1, lit)
    elif KEY == "what-cd":
        whatcd_menu(a, ["index", "torrents", "equalizer", "forums", "irc"], 2, lit)
    elif KEY == "gmail-2004":
        draw_text(a, WEB_B, "Compose Mail", 18, 2, H("0000cc") if lit else H("8f9bc6"), underline=8)
        draw_text(a, WEB_B, "Equalizer", 108, 2, BLACK if lit else H("999999"))
        rect(a, 0, 13, 275, 1, H("c3d9ff") if lit else H("e8eef7"))
    else:
        draw_text(a, WEB_B, "EQUALIZER", 18, 3, BLACK if lit else H("8c98a4"))
        reddit_tabs(a, 258, lit, ("hot", "new", "presets"), 0)
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n, bay):
    """14x63 slot whose fill rises with the value (n of 0..27)."""
    rect(a, x, y, 14, 63, bay)
    rect(a, x + 4, y + 1, 6, 61, T["track"])
    frame(a, x + 4, y + 1, 6, 61, T["track_rim"])
    v = n / 27
    top = round((1 - v) * 51) + 6
    colour = ramp(T["level"], v)
    for r in range(top, 60):
        rect(a, x + 5, y + r, 4, 1, colour)
    rect(a, x + 1, y + 31, 2, 1, T["ink_mid"])
    rect(a, x + 11, y + 31, 2, 1, T["ink_mid"])


EQ_BAY = {"deviantart": H("e9efe8"), "what-cd": H("282828"), "gmail-2004": WHITE, "reddit": WHITE}


def make_eqmain():
    a = new(275, 315, T["body"])
    a[0:14, :] = eq_titlebar(True)
    bay = EQ_BAY[KEY]
    if KEY == "deviantart":
        rect(a, 0, 14, 1, 102, T["edge"])
        rect(a, 274, 14, 1, 102, T["edge"])
        rect(a, 0, 115, 275, 1, T["edge"])
        rect(a, 1, 14, 273, 1, H("eef3ed"))
        rrect(a, 16, 36, 245, 68, bay, H("b4c0b3"), 2)
    elif KEY == "what-cd":
        rect(a, 0, 14, 1, 102, T["edge"])
        rect(a, 274, 14, 1, 102, T["edge"])
        rect(a, 0, 115, 275, 1, T["edge"])
        rect(a, 16, 36, 245, 68, bay)
        frame(a, 16, 36, 245, 68, H("222222"))
        rect(a, 17, 37, 243, 1, H("121212"))
    elif KEY == "gmail-2004":
        rrect(a, 2, 15, 271, 98, H("c3d9ff"), None, 3)
        rrect(a, 16, 36, 245, 68, bay, H("a2bae7"), 1)
    else:
        rect(a, 0, 14, 1, 102, H("cee3f8"))
        rect(a, 274, 14, 1, 102, H("cee3f8"))
        rect(a, 0, 115, 275, 1, H("cee3f8"))
        rect(a, 16, 36, 245, 68, bay)
        frame(a, 16, 36, 245, 68, H("cee3f8"))
    for lbl, yy in (("+12", 41), ("0", 67), ("-12", 93)):
        text_center(a, TINY, lbl, 58, yy, T["ink_mid"])
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14, bay)
    lab_y = 106
    lab_col = T["label"]
    text_center(a, TINY, "PREAMP", 28, lab_y, lab_col)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, lab_y, lab_col)

    # under the window: buttons
    b = new(9, 9, T["body"])
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = b
    under = a[20, 12].tolist()
    rect(a, 10, 119, 235, 12, under)
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
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n, bay)
    for y, pressed in ((164, False), (176, True)):
        rect(a, 224, y, 44, 12, under)
        toggle(a, 224, y, 44, 12, "PRESETS", False, pressed, arrow=False)
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


def pl_title(t, lit):
    if KEY == "deviantart":
        s = "my gallery"
        w = text_w(WEB_B, s) + 10
        x = 50 - w // 2
        if lit:
            face, rim, ink = (H("f6f8f5"), H("e9efe8")), H("2f3a32"), H("2c3a30")
        else:
            face, rim, ink = (H("c9d2c8"), H("bcc6bb")), H("7a867c"), H("5d6e61")
        rrect(t, x, 6, w, 14, None, rim, 2, grad=face, bottom=False)
        rect(t, x + 2, 7, w - 4, 1, H("5eac74") if lit else H("d4dbd3"))
        draw_text(t, WEB_B, s, x + 5, 9, ink)
    elif KEY == "what-cd":
        text_center(t, WEB_B, "Torrents", 50, 5, WHITE if lit else H("8a8a8a"))
    elif KEY == "gmail-2004":
        text_center(t, WEB_B, "Inbox (3)", 50, 5, BLACK if lit else H("8894ad"))
    else:
        text_center(t, WEB_B, "PLAYLIST", 50, 6, BLACK if lit else H("8c98a4"))


def text_button(t, bx, by, w, h, lbl):
    button_face(t, bx, by, w, h, False)
    text_center(t, TINY, lbl, bx + w // 2, by + (h - 5) // 2, T["btn_ink"])


def mini_face(t, bx, by):
    if T["btn_round"]:
        rrect(t, bx, by, 10, 10, None, T["btn_rim"], 1, grad=T["btn"])
    else:
        vgrad(t, bx, by, 10, 10, *T["btn"])
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


def bottom_strip(t, w, h):
    """Each site's footer band along the bottom of the playlist/gen frames."""
    if KEY == "deviantart":
        rect(t, 0, h - 5, w, 4, H("475149"))
        rect(t, 0, h - 5, w, 1, H("76847a"))
    elif KEY == "what-cd":
        rect(t, 0, h - 5, w, 4, H("1c1c1c"))
    elif KEY == "gmail-2004":
        pass
    else:
        rect(t, 0, h - 5, w, 4, H("eff7ff"))
        rect(t, 0, h - 5, w, 1, H("cee3f8"))


def make_pledit():
    side = T["side"]
    edge = T["edge"]
    a = new(280, 186, side)
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar20(25, lit)
        a[y:y + 20, 0:25] = bar20(25, lit)
        t = bar20(100, lit)
        pl_title(t, lit)
        a[y:y + 20, 26:126] = t
        t = bar20(25, lit)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    t = new(12, 29, side)
    rect(t, 0, 0, 1, 29, edge)
    rect(t, 11, 0, 1, 29, edge)
    a[42:71, 0:12] = t
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
        bottom_strip(t, w, 38)
        return t

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
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        mini_face(t, bx, 22)
        mini_transport_icon(t, kind, bx, 22)
    display_box(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, T["ink"])
    rect(t, 84, 22 + 5, 1, 1, T["ink"])
    text_button(t, 106, 8, 22, 18, "LIST")
    grip = T["grip"]
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx, gy, grip)
    a[72:110, 126:276] = t

    a[0:38, 179:204] = bottom_base(25)
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_gen():
    side = T["side"]
    edge = T["edge"]
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
        bottom_strip(t, w, 14)
        rect(t, 0, 0, 1, 14, edge) if left_edge else rect(t, w - 1, 0, 1, 14, edge)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    px(t, w - 4 - 3 * k + 3 * j, 7 - 3 * j, T["grip"])
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h in ((127, 11, 29), (158, 11, 24), (139, 8, 29), (170, 8, 24)):
        t = new(w, h, side)
        if w == 11:
            rect(t, 0, 0, 1, h, edge)
            rect(t, w - 1, 0, 1, h, edge)
        else:
            # the right tile's first column is stretched to fill the gap by the picture: keep it plain
            rect(t, 1, 0, 1, h, edge)
            rect(t, w - 1, 0, 1, h, edge)
        a[42:42 + h, x:x + w] = t
    t = new(9, 9, side)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: cells cut from the titlebar's own rows 4..10, so the title sits seamlessly
    gen_ink = {"deviantart": (WHITE, H("e4e9e3")), "what-cd": (WHITE, H("8a8a8a")),
               "gmail-2004": (BLACK, H("8894ad")), "reddit": (BLACK, H("8c98a4"))}[KEY]
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        bar = bar20(194, lit)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            a[y:y + 7, x:x + w] = bar[4:11, x:x + w]
            draw_text(a, FONT5, c, x, y + 1, gen_ink[0] if lit else gen_ink[1])
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
    button_face(a, 0, 1, 47, 15, False)
    button_face(a, 0, 16, 47, 15, True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    disp = T["disp"]
    out = [(disp, "background"), (lerp(disp, T["ink"], 0.12), "dots")]
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
    site, owner = T["site"], T["company"]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{T['name']} — a skin in the style of {site}. {site} logo © {owner}.\n\n"
            f"A classic (Winamp 2.x format) skin, drawn by a script (gen_skin.py) from rectangles and\n"
            f"hand-made pixel fonts.\n"
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


def text_ink():
    """text.bmp's ink as the app finds it: the commonest colour well away from the space cell's."""
    arr = np.asarray(SHEETS["text"]).astype(np.int32)[:12, :155]
    bg = arr[2, 152]
    far = np.abs(arr - bg).sum(-1) >= 96
    cols, counts = np.unique(arr[far].reshape(-1, 3), axis=0, return_counts=True)
    return tuple(int(v) for v in cols[counts.argmax()])


def title_font():
    for path in ("/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(path, 11)
        except OSError:
            continue
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
        blit(img, nums, (99, 0, 9, 13), 38, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    # the title: the space cell across the box, then a TrueType line in text.bmp's ink, as the app
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    layer = Image.new("RGB", (154, 14))
    layer.paste(img.crop((111, 22, 265, 36)))
    ImageDraw.Draw(layer).text((0, 24 + 3 + 2 - 22), state["title"], fill=text_ink(), font=title_font(), anchor="lm")
    img.paste(layer, (111, 22))
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
    font = ImageFont.truetype("/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf", 9)
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
    img.paste(Image.fromarray(np.clip(c0 + (c1 - c0) * arr, 0, 255).astype(np.uint8)), (11, 20))
    return img


PREVIEW_ROWS = {
    "deviantart": [("Digital Art - Fractal Dreams", "3:12"), ("Daily Deviation - Nightfall", "3:58"),
                   ("Fan Art - Sketch Dump", "4:05"), ("Photography - Macro Dew", "2:51"),
                   ("Traditional - Ink Study", "3:40"), ("Literature - Prose Poem", "3:21"),
                   ("Wallpaper - Minimal Blue", "3:33"), ("Skins - Winamp Classic", "3:09"),
                   ("Pixel Art - Tiny Town", "3:28"), ("Stock - Texture Pack", "2:47"),
                   ("Journal - Commissions Open", "3:16")],
    "what-cd": [("Artist - Album [2004] FLAC / Lossless / Log (100%)", "4:12"),
                ("Artist - Single [V0] MP3 / 320", "3:47"), ("Various - Compilation [CD] FLAC", "5:03"),
                ("Artist - EP [Vinyl] 24bit Lossless", "2:58"), ("Artist - Live [WEB] FLAC", "6:21"),
                ("Artist - Demo [Cassette] V2 (VBR)", "3:33"), ("Artist - Remixes [WEB] 320", "4:40"),
                ("Artist - Bootleg [CD] FLAC / Cue", "3:09"), ("Artist - Soundtrack [SACD]", "5:51"),
                ("Artist - B-Sides [CD] V0", "4:05"), ("Artist - Anthology [CD] FLAC", "3:22")],
    "gmail-2004": [("Gmail Team - Welcome to Gmail", "3:02"), ("me (2) - Re: weekend plans?", "4:10"),
                   ("Invitation - You've been invited", "3:44"), ("Newsletter - Weekly digest", "2:59"),
                   ("Old friend - Long time no see", "3:31"), ("Photos - Album shared", "4:20"),
                   ("Reminder - Concert tonight", "3:15"), ("Labels - Music, Starred", "3:48"),
                   ("Archive - All Mail", "2:44"), ("Chat - Saved conversation", "3:37"),
                   ("Drafts - Unsent reply", "3:05")],
    "reddit": [("TIL the original Winamp skin format is still used", "3:12"),
               ("What album got you through 2008? (self)", "3:58"),
               ("Found my old mp3 player, still works [pic]", "4:05"),
               ("Ask reddit: best headphones under $50?", "2:51"),
               ("This song has been stuck in my head all week", "3:40"),
               ("[OC] I made a visualizer in a weekend", "3:21"), ("Upvote if you remember this", "3:33"),
               ("Linux users: which player do you use?", "3:09"), ("The front page right now", "3:28"),
               ("Mods are asleep, post good music", "2:47"), ("Daily discussion thread", "3:16")],
}
PREVIEW_TITLE = {"deviantart": "Daily Deviation - Nightfall (3:58)",
                 "what-cd": "Artist - Album [2004] FLAC / Lossless",
                 "gmail-2004": "Welcome to Gmail - Gmail Team",
                 "reddit": "TIL the Winamp skin format is still used"}


def preview():
    rows = PREVIEW_ROWS[KEY]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=PREVIEW_TITLE[KEY], bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="Paused: away from keyboard", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
    # the app's title takes text.bmp's ink: it must be the theme's ink
    assert text_ink() == T["ink"], (key, text_ink())
    print(f"{key:12s} -> {T['wsz']}, preview-{key}.png")


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
