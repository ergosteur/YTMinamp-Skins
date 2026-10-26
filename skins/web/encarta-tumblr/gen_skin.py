#!/usr/bin/python3
"""Encarta 97 and Tumblr: classic Winamp 2.x skins in the style of two pieces of software.

Forked from skins/ember/gen_skin.py (same sheets, same layouts, same preview logic, by way of the
social-2012 generator), with one theme per subject:

    encarta-97  Microsoft Encarta 97 Encyclopedia: the black window bars with letter-spaced taupe
                capitals and the "ENCARTA 97" lettering, the cream article pane, the light taupe
                caption strips, the black menu bar as the transport strip, gold "Start Over" /
                "Wizard" buttons, the Pinpointer as the playlist (black body, white list, taupe
                header strip, dark red selection on taupe), and an InterActivities chart (periwinkle
                bars over a taupe plot) as the equalizer
    tumblr      the classic Tumblr dashboard (2012-2015): the #36465d navy page and header with the
                white "t", the search field and the header icons, white rounded post cards, grey
                footer icons, the blue #529ecc "Post" button for Play, the heart (red when on) and
                reblog (green when on) as Shuffle and Repeat, and the seven coloured post-type icons
                (Text, Photo, Quote, Link, Chat, Audio, Video) in the equalizer's titlebar

    /usr/bin/python3 -I gen_skin.py                 # every theme
    /usr/bin/python3 -I gen_skin.py tumblr          # just this one
    /usr/bin/python3 -I gen_skin.py --list

Everything is drawn here from code, except the two real marks (once each, in the main titlebar):
the "ENCARTA 97" lettering, cut from a screenshot of the Encarta 97 title screen, and the Tumblr
"t", cut from the Tumblr wordmark SVG (see README.md). Private use only. Each theme writes its
sheets into out/<theme>/, zips them flat into <Name>.wsz and draws preview-<theme>.png beside this
script.
"""

import os
import subprocess
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

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

# Encarta 97's own colours, sampled from screenshots of the program (WinWorld).
EN_BLACK = BLACK
EN_TAUPE = H("a09683")      # heading band, Pinpointer list header, scroll thumb, title capitals
EN_TAUPE_L = H("d9d6c5")    # caption strips ("Introduction"), selection, MindMaze panel
EN_CREAM = H("ebeae1")      # the article pane
EN_GOLD = H("dcba5c")       # "Start Over" (active) and "Wizard"
EN_RED = H("972938")        # the Pinpointer's selected article
EN_97 = H("b95b5c")         # the "97" of the title screen, and links
EN_PERI = H("6571b4")       # the Pinpointer's titlebar, the chart bars

TB_NAVY = H("36465d")
TB_BLUE = H("529ecc")
TB_RED = H("d95e40")
TB_ORANGE = H("f2992e")
TB_GREEN = H("56bc8a")
TB_PURPLE = H("a77dc2")
TB_GREY = H("748089")
TB_TEXT = H("444444")
TB_META = H("a7a7a7")

THEMES = {
    "encarta-97": dict(
        name="Encarta-97", subject="Microsoft Encarta 97 Encyclopedia", owner="Microsoft Corporation",
        mark="Microsoft Encarta", wsz="Encarta-97.wsz", style="en",
        disp=EN_TAUPE_L, lcd=BLACK, ink=BLACK, ink_dim=H("c3bfab"), ink_mid=H("7a705e"), digit=EN_GOLD,
        play_ind=EN_GOLD,
        level=[H("a3abdc"), EN_PERI, H("3f4a8c")],
        vis_ramp=[H("fff1b8"), H("ffd253"), EN_GOLD, H("b8923a"), H("7c6020")],
        osc=[H("ffe48a"), H("ffd253"), EN_GOLD, H("b8923a"), H("8c6d24")], peak=EN_97,
        pledit=("#000000", "#972938", "#FFFFFF", "#D9D6C5"),
        genex=dict(item_bg=WHITE, item_fg=BLACK, win_bg=EN_CREAM, btn_fg=BLACK, win_fg=BLACK,
                   divider=EN_TAUPE, sel=EN_TAUPE_L, head_bg=EN_TAUPE, head_fg=WHITE,
                   head_hi=H("c4bcaa"), head_lo=H("6e6555"), head_pr=H("8a8070"), dead=EN_CREAM,
                   sb=EN_TAUPE_L, sb2=EN_TAUPE, sb_pr=H("c4bcaa"), sb_pr2=EN_GOLD, sb_dead=EN_CREAM),
        art=(EN_TAUPE_L, H("6e6555")),
        rows=[("Nuclear Energy", "3:12"), ("Shuttle Diplomacy", "3:58"),
              ("MindMaze - The Castle", "4:05"), ("Pinpointer - Word Search", "2:51"),
              ("InterActivities - Orbit", "3:40"), ("World Music - Andes", "3:21"),
              ("Timeline - 1500 to 1600", "3:33"), ("Media+More - Sounds", "3:09"),
              ("Atlas - Lake Titicaca", "3:28"), ("Famous Paintings", "2:47"), ("Dictionary - Ode", "3:16")],
        title="Nuclear Energy - Media Gallery  ***",
    ),
    "tumblr": dict(
        name="Tumblr", subject="the Tumblr dashboard (2012-2015)", owner="Automattic Inc. (Tumblr)",
        mark="Tumblr", wsz="Tumblr.wsz", style="tb",
        disp=H("f3f4f6"), ink=TB_TEXT, ink_dim=H("dfe2e6"), ink_mid=TB_META, digit=TB_TEXT,
        play_ind=TB_BLUE,
        level=[H("9ccaea"), TB_BLUE, H("3d82b0")],
        vis_ramp=[TB_RED, TB_ORANGE, TB_GREEN, TB_BLUE, TB_PURPLE],
        osc=[TB_BLUE, TB_GREEN, TB_ORANGE, TB_RED, TB_PURPLE], peak=TB_NAVY,
        pledit=("#444444", "#529ECC", "#FFFFFF", "#E4ECF4"),
        genex=dict(item_bg=WHITE, item_fg=TB_TEXT, win_bg=H("f3f4f6"), btn_fg=TB_TEXT, win_fg=TB_TEXT,
                   divider=H("e6e6e6"), sel=H("e4ecf4"), head_bg=H("f5f5f5"), head_fg=TB_TEXT,
                   head_hi=WHITE, head_lo=H("d6d6d6"), head_pr=H("e6e6e6"), dead=H("f3f4f6"),
                   sb=H("eeeeee"), sb2=H("c4c4c4"), sb_pr=H("e4ecf4"), sb_pr2=TB_BLUE, sb_dead=H("f3f4f6")),
        art=(H("c9d6e6"), TB_NAVY),
        rows=[("Dashboard - Following", "3:12"), ("Reblogged From Staff", "3:58"),
              ("Audio Post - Now Playing", "4:05"), ("Quote - Late Night", "2:51"),
              ("Photoset - Golden Hour", "3:40"), ("Text Post - 40,000 Notes", "3:21"),
              ("Link - Tumblr Radar", "3:33"), ("Chat - Fandom Hours", "3:09"),
              ("Video - Gif Set", "3:28"), ("Liked Posts", "2:47"), ("Ask Box - Anonymous", "3:16")],
        title="Audio Post - Now Playing  ***",
    ),
}
THEME_KEYS = list(THEMES)
T = None
KEY = None
S = None       # style code: en / tb
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


def disc(a, x, y, d, fill, rim, hi=None, grad=None):
    """A round knob, d pixels across, top-left at (x, y); grad=(top, bottom) shades it."""
    c = (d - 1) / 2
    for r in range(d):
        for k in range(d):
            dist = ((r - c) ** 2 + (k - c) ** 2) ** 0.5
            if dist <= c + 0.45:
                col = fill if grad is None else lerp(grad[0], grad[1], r / max(1, d - 1))
                if dist > c - 0.6:
                    col = rim
                px(a, x + k, y + r, col)
    if hi is not None:
        px(a, x + round(c) - 1, y + 2, hi)
        px(a, x + round(c), y + 2, hi)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img

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


# A Helvetica/Arial-flavoured 9-row font: ascenders on row 0, x-height from row 2, baseline row 6.
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
    "C": W9(0, ".###", "#...", "#...", "#...", "#...", "#...", ".###"),
    "D": W9(0, "###.", "#..#", "#..#", "#..#", "#..#", "#..#", "###."),
    "E": W9(0, "####", "#...", "#...", "###.", "#...", "#...", "####"),
    "H": W9(0, "#..#", "#..#", "#..#", "####", "#..#", "#..#", "#..#"),
    "I": W9(0, "###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"),
    "M": W9(0, "#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "P": W9(0, "###.", "#..#", "#..#", "###.", "#...", "#...", "#..."),
    "S": W9(0, ".###", "#...", "#...", ".##.", "...#", "...#", "###."),
    "Y": W9(0, "#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "+": W9(1, "..#..", "..#..", "#####", "..#..", "..#.."),
    "#": W9(1, ".#.#.", "#####", ".#.#.", "#####", ".#.#."),
    "1": W9(0, ".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"),
    "3": W9(0, "###.", "...#", "...#", ".##.", "...#", "...#", "###."),
    ".": W9(6, "#"),
    "·": W9(4, "#"),
    " ": W9(0, "...", "..."),
}


def bold(glyph):
    """Arial-style bold: every stroke one pixel wider (glyph one column wider)."""
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
WEB_B["+"] = W9(1, "..##..", "..##..", "######", "..##..", "..##..")
WEB_B["#"] = W9(1, ".#..#.", "######", ".#..#.", "######", ".#..#.")


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1, shadow=None, sdy=1, sdx=1):
    for c in s:
        if c not in font:
            continue
        g = font[c]
        if shadow is not None:
            for r, row in enumerate(g):
                for k, ch in enumerate(row):
                    if ch == "#":
                        px(a, x + k + sdx, y + r + sdy, shadow)
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col(r) if callable(col) else col)
        x += len(g[0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1, shadow=None, sdy=1, sdx=1):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow, sdy, sdx)


def icon(a, rows, x, y, col):
    for r, row in enumerate(rows):
        for k, ch in enumerate(row):
            if ch == "#":
                px(a, x + k, y + r, col)


# More web-font capitals (the 9-row Helvetica-ish font)
WEB.update({
    "A": W9(0, ".##.", "#..#", "#..#", "####", "#..#", "#..#", "#..#"),
    "Q": W9(0, ".##.", "#..#", "#..#", "#..#", "#.##", "#..#", ".##."),
    "R": W9(0, "###.", "#..#", "#..#", "###.", "#.#.", "#..#", "#..#"),
    "T": W9(0, "#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
})
for _c in "AQRT":
    WEB_B[_c] = bold(WEB[_c])
WEB_B["T"] = W9(0, "######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##..")

# Letter-spaced title capitals, 7 rows (Encarta's window titles; also gen.bmp's letters there)
CAPS7 = {
    "A": G(".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": G("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": G(".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": G("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": G("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": G("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": G(".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": G("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": G("###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"),
    "J": G("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": G("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": G("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": G("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": G("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": G(".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": G("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": G(".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": G("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": G(".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": G("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": G("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": G("#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#.."),
    "W": G("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": G("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": G("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": G("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    " ": G("...", "...", "...", "...", "...", "...", "..."),
}
for _k, _g in CAPS7.items():
    assert len(_g) == 7 and len(set(map(len, _g))) == 1, _k


# ------------------------------------------------------------------------------------------
# Logos: the one real mark per skin
# ------------------------------------------------------------------------------------------

TUMBLR_SVG = os.path.join(HERE, "source", "logo-tumblr", "Tumblr_Logo.svg")
ENCARTA_PNG = os.path.join(HERE, "source", "encarta97-winworld", "encarta97-title.png")


def _bands(mask, axis):
    on = mask.any(axis=axis)
    idx = np.nonzero(on)[0]
    return idx[0], idx[-1] + 1


def _resize_cov(cov, w, h):
    ci = Image.fromarray(np.clip(cov * 255, 0, 255).astype(np.uint8), "L").resize((w, h), Image.LANCZOS)
    return np.asarray(ci).astype(np.float32) / 255


def tumblr_t(height, firm=(0.12, 0.70)):
    """The "t" of the Tumblr wordmark (the dashboard's "t" logo), `height` px tall."""
    os.makedirs(SCRATCH, exist_ok=True)
    png = os.path.join(SCRATCH, "tumblr-wordmark.png")
    subprocess.run(["/usr/bin/rsvg-convert", "-h", "800", TUMBLR_SVG, "-o", png], check=True)
    cov = np.asarray(Image.open(png).convert("RGBA")).astype(np.float32)[..., 3] / 255
    cols = (cov > 0.3).any(axis=0)
    x0 = int(np.argmax(cols))
    x1 = x0 + int(np.argmax(~cols[x0:]))            # the first run of inked columns: the "t"
    cov = cov[:, x0:x1]
    y0, y1 = _bands(cov > 0.3, 1)
    cov = cov[y0:y1]
    h0, w0 = cov.shape
    c = _resize_cov(cov, max(1, round(w0 * height / h0)), height)
    return np.clip((c - firm[0]) / firm[1], 0, 1)


def encarta_logo(height):
    """ENCARTA (black ink) and 97 (red) from the Encarta 97 title screen: two coverage masks."""
    im = np.asarray(Image.open(ENCARTA_PNG).convert("RGB")).astype(np.float32)[205:325, 430:915]
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    ink = np.clip((150 - lum) / 120, 0, 1)
    red = np.clip(((r - (g + b) / 2) - 30) / 50, 0, 1) * (lum > 70)
    # keep the ENCARTA line: the first run of inked rows left of the 97, not "encyclopedia" below it
    rows = (ink[:, :330] > 0.5).any(axis=1)
    top = int(np.argmax(rows))
    end = top + int(np.argmax(~rows[top:]))
    ink[end:, :] = 0
    ink[:top, :] = 0
    both = (ink > 0.4) | (red > 0.4)
    y0, y1 = _bands(both, 1)
    x0, x1 = _bands(both, 0)
    ink, red = ink[y0:y1, x0:x1], red[y0:y1, x0:x1]
    h0, w0 = ink.shape
    w = max(1, round(w0 * height / h0))
    firm = lambda c: np.clip((c - 0.1) / 0.65, 0, 1)
    return firm(_resize_cov(ink, w, height)), firm(_resize_cov(red, w, height))


def paste_logo(a, x, y, alpha, ink):
    h, w = alpha.shape
    region = a[y:y + h, x:x + w].astype(np.float32)
    src = np.zeros((h, w, 3), np.float32) + np.array(ink, np.float32)
    out = region * (1 - alpha[..., None]) + src * alpha[..., None]
    a[y:y + h, x:x + w] = np.round(out).astype(np.int32)
    return w


LOGO_CACHE = {}


def cached(kind, height):
    k = (kind, height)
    if k not in LOGO_CACHE:
        LOGO_CACHE[k] = tumblr_t(height) if kind == "tumblr" else encarta_logo(height)
    return LOGO_CACHE[k]


# ------------------------------------------------------------------------------------------
# Theme surfaces
# ------------------------------------------------------------------------------------------


def lcd():
    return T.get("lcd", T["disp"])


def bar_fill(a, x, y, w, h, lit):
    """A titlebar band, whatever its height (14 for main/EQ, 20 for playlist/gen)."""
    if S == "en":
        rect(a, x, y, w, h, BLACK if lit else H("3c3c3c"))
    else:
        rect(a, x, y, w, h, TB_NAVY if lit else H("56606e"))
        rect(a, x, y + h - 1, w, 1, H("2c3a4d") if lit else H("4a5360"))


def bar_ink(lit):
    if S == "en":
        return EN_TAUPE if lit else H("8a8a8a")
    return WHITE if lit else H("c2c7ce")


def body_colour():
    return BLACK if S == "en" else TB_NAVY


def spaced(a, s, x, y, col, gap=2):
    return draw_text(a, CAPS7, s, x, y, col, gap=gap)


def spaced_w(s, gap=2):
    return text_w(CAPS7, s, gap)


def card(a, x, y, w, h, fill=WHITE):
    """Tumblr's white post card (3px corners)."""
    rrect(a, x, y, w, h, fill, None, 3)


def display_box(a, x, y, w, h, col=None):
    """A display window: Encarta's caption strip (taupe rim), Tumblr's light grey field."""
    col = T["disp"] if col is None else col
    rect(a, x, y, w, h, col)
    if S == "en":
        frame(a, x - 1, y - 1, w + 2, h + 2, BLACK if col == BLACK else EN_TAUPE)
    else:
        frame(a, x - 1, y - 1, w + 2, h + 2, H("dfe3e8"))
        rect(a, x, y, w, 1, H("e8ebef"))


def btn(a, x, y, w, h, pressed, primary=False, r=None):
    """Encarta's "Show Chart" button (gold "Start Over" when primary); Tumblr's grey / blue button."""
    if S == "en":
        if primary:
            fill, rim = (H("b89a44"), H("6e5a22")) if pressed else (EN_GOLD, H("8a7432"))
        else:
            fill, rim = (EN_TAUPE_L, H("5a5a5a")) if pressed else (H("f4f3ee"), H("6e6e6e"))
        rect(a, x, y, w, h, fill)
        frame(a, x, y, w, h, rim)
        if not pressed:
            rect(a, x + 1, y + 1, w - 2, 1, lerp(fill, WHITE, 0.4))
    else:
        r = 2 if r is None else r
        if primary:
            grad, rim = ((H("4285b3"), H("4a90bf")), H("3a77a0")) if pressed else ((H("5ea7d4"), TB_BLUE), H("4a8fbd"))
        else:
            grad, rim = ((H("e8e8e8"), H("eeeeee")), H("c4c4c4")) if pressed else ((WHITE, H("f2f2f2")), H("d6d6d6"))
        rrect(a, x, y, w, h, None, rim, r, grad=grad)


def btn_ink(primary, pressed=False):
    if S == "en":
        return BLACK
    return WHITE if primary else H("888888")


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: Encarta's "|-" "|o" "|x" (white on black); Tumblr's header glyphs."""
    if S == "en":
        if pressed:
            rect(a, x, y, 9, 9, EN_TAUPE)
            ink, sep = BLACK, BLACK
        else:
            rect(a, x, y, 9, 9, BLACK if lit else H("3c3c3c"))
            ink, sep = (WHITE, EN_TAUPE) if lit else (H("a0a0a0"), H("707070"))
        if kind == "options":
            for r in range(3):
                rect(a, x + 1 + r, y + 3 + r, 5 - 2 * r, 1, ink)
            rect(a, x + 8, y + 1, 1, 7, sep)
            return
        rect(a, x + 1, y + 1, 1, 7, sep)
        if kind == "minimize":
            rect(a, x + 3, y + 5, 5, 1, ink)
        elif kind == "shade":
            frame(a, x + 3, y + 2, 5, 5, ink)
            rect(a, x + 3, y + 3, 5, 1, ink)
        elif kind == "close":
            for i in range(5):
                px(a, x + 3 + i, y + 2 + i, ink)
                px(a, x + 7 - i, y + 2 + i, ink)
        return
    if pressed:
        rrect(a, x, y, 9, 9, lerp(TB_NAVY, WHITE, 0.22), None, 1)
        ink = WHITE
    else:
        ink = H("b4bcc6") if lit else H("9aa2ad")
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        rect(a, X + 2, Y + 3, 5, 1, ink)
        rect(a, X + 2, Y + 5, 5, 1, ink)
        rect(a, X + 2, Y + 7, 5, 1, ink)
        rect(a, X + 2, Y + 1, 5, 1, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 6, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 1, ink)
        frame(a, X + 2, Y + 2, 5, 5, ink)
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


# ------------------------------------------------------------------------------------------
# Icons
# ------------------------------------------------------------------------------------------

HEART = [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]

TB_HOME = ["....#....", "...###...", "..#####..", ".#######.", "#########", ".##...##.", ".##...##.", ".##...##."]
TB_COMPASS = ["..#####..", ".#.....#.", "#.....#.#", "#....##.#", "#...#...#", "#.##....#", "#.#.....#",
              ".#.....#.", "..#####.."]
TB_MAIL = ["##########", "##......##", "#.#....#.#", "#..#..#..#", "#...##...#", "#........#", "##########"]
TB_BOLT = ["...##", "..##.", ".##..", "#####", "..##.", ".##..", ".#...", "#...."]
TB_USER = ["..###..", ".#####.", ".#####.", "..###..", ".......", ".#####.", "#######", "#######"]
TB_GLASS = [".##..", "#..#.", "#..#.", ".###.", "....#"]


def reblog(a, x, y, col):
    """Tumblr's reblog arrows, 11x11."""
    rect(a, x, y + 2, 8, 2, col)          # top arm, pointing right
    rect(a, x, y + 2, 2, 5, col)
    rect(a, x + 8, y, 1, 6, col)
    rect(a, x + 9, y + 1, 1, 4, col)
    rect(a, x + 10, y + 2, 1, 2, col)
    rect(a, x + 3, y + 7, 8, 2, col)      # bottom arm, pointing left
    rect(a, x + 9, y + 4, 2, 5, col)
    rect(a, x + 2, y + 5, 1, 6, col)
    rect(a, x + 1, y + 6, 1, 4, col)
    rect(a, x, y + 7, 1, 2, col)


def post_icon(a, kind, x, y, col):
    """Tumblr's post-type icons, 9x9 (the 2012 set, flat, one colour each)."""
    if kind == "text":
        icon(a, ["..#......", ".#.#.....", ".#.#..##.", "#...#...#", "#####.###", "#...##..#",
                 "#...#.###"], x, y + 1, col)
    elif kind == "photo":
        icon(a, [".##......", "#########", "###...###", "##.###.##", "##.###.##", "##.###.##", "###...###",
                 "#########"], x, y, col)
    elif kind == "quote":
        icon(a, ["...#...#", "..#...#.", ".##..##.", "###.###.", "###.###.", ".#...#.."], x, y + 1, col)
    elif kind == "link":
        disc(a, x, y, 9, col, col)
        for i in range(4):
            px(a, x + 2 + i, y + 6 - i, WHITE)
            px(a, x + 3 + i, y + 6 - i, WHITE)
    elif kind == "chat":
        rrect(a, x, y + 1, 8, 6, col, None, 1)
        px(a, x + 8, y + 3, col)
        px(a, x + 8, y + 4, col)
        icon(a, ["#.....", "#.#.#.", "###.#.", "#.#.#."], x + 1, y + 2, WHITE)
    elif kind == "audio":
        icon(a, ["..#####..", ".#.....#.", "#.......#", "#.......#", "##.....##", "##.....##",
                 "##.....##"], x, y + 1, col)
        px(a, x + 4, y + 5, col)
        px(a, x + 4, y + 6, col)
        px(a, x + 3, y + 6, col)
    elif kind == "video":
        disc(a, x, y, 4, col, col)
        disc(a, x + 3, y, 4, col, col)
        rect(a, x, y + 4, 6, 4, col)
        icon(a, ["..#", ".##", "###", ".##", "..#"][::-1], x + 6, y + 3, col)


POST_TYPES = [("text", TB_TEXT), ("photo", TB_RED), ("quote", TB_ORANGE), ("link", TB_GREEN),
              ("chat", H("4da8d6")), ("audio", TB_PURPLE), ("video", TB_GREY)]


def emblem(a, x, y):
    """13x15 at the About spot: Encarta's help button; Tumblr's blue compose (pencil) button."""
    if S == "en":
        disc(a, x, y + 1, 13, BLACK, WHITE)
        icon(a, [".###.", "#...#", "....#", "...#.", "..#..", "..#..", ".....", "..#.."], x + 4, y + 3, WHITE)
    else:
        rrect(a, x, y + 1, 13, 13, None, H("4a8fbd"), 2, grad=(H("5ea7d4"), TB_BLUE))
        for i in range(6):
            rect(a, x + 3 + i, y + 9 - i, 2, 2, WHITE)
        px(a, x + 3, y + 11, WHITE)
        px(a, x + 9, y + 3, H("cfe4f3"))


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]
CLUTTER_TB = {"O": TB_RED, "A": TB_ORANGE, "I": TB_GREEN, "D": TB_BLUE, "V": TB_PURPLE}


def clutter_bar(lit_letters):
    if S == "en":
        a = new(8, 43, BLACK)
        for letter, y, h in CLUTTER_SLOTS:
            on = letter in lit_letters
            if on:
                rect(a, 1, y, 6, h, H("3a321c"))
            draw_text(a, TINY, letter, 2, y + (h - 5) // 2, EN_GOLD if on else H("7a705e"))
        return a
    a = new(8, 43, WHITE)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        col = CLUTTER_TB[letter]
        if on:
            rect(a, 1, y, 6, h, lerp(col, WHITE, 0.82))
        draw_text(a, TINY, letter, 2, y + (h - 5) // 2, col if on else H("c8c8c8"))
    return a


def main_titlebar(lit):
    a = new(275, 14)
    bar_fill(a, 0, 0, 275, 14, lit)
    ink = bar_ink(lit)
    if S == "en":
        # MICROSOFT  [ENCARTA 97]  ENCYCLOPEDIA, as the program's own titlebar spells it
        inkc, redc = cached("encarta", 14)
        lw = inkc.shape[1]
        w1, w2 = spaced_w("MICROSOFT", 1), spaced_w("ENCYCLOPEDIA", 1)
        total = w1 + 7 + lw + 7 + w2
        x = 128 - total // 2
        spaced(a, "MICROSOFT", x, 4, ink, 1)
        lx = x + w1 + 7
        paste_logo(a, lx, 0, inkc, EN_CREAM if lit else H("9a9a9a"))
        paste_logo(a, lx, 0, redc, EN_97 if lit else H("8a6d6d"))
        spaced(a, "ENCYCLOPEDIA", lx + lw + 7, 4, ink, 1)
    else:
        al = cached("tumblr", 11)
        paste_logo(a, 19, 1, al, WHITE if lit else H("c2c7ce"))
        # the search field
        sx = 32
        rrect(a, sx, 2, 92, 10, lerp(TB_NAVY, WHITE, 0.13 if lit else 0.1), None, 2)
        sink = H("aab3bf") if lit else H("9aa2ad")
        icon(a, TB_GLASS, sx + 4, 4, sink)
        draw_text(a, WEB, "Search Tumblr", sx + 12, 3, sink)
        # the header's icons: dashboard, explore, inbox, activity, account
        ic = H("dfe4ea") if lit else H("a4acb6")
        x = 146
        for g in (TB_HOME, TB_COMPASS, TB_MAIL, TB_BOLT, TB_USER):
            icon(a, g, x, 7 - len(g) // 2, WHITE if (g is TB_HOME and lit) else ic)
            x += len(g[0]) + 9
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, body_colour())
    bar = main_titlebar(True)
    for kind, x, bx in [("options", 0, 6), ("minimize", 9, 244), ("close", 18, 264)]:
        b = bar[3:12, bx:bx + 9].copy()
        mini_button(b, 0, 0, kind, True)
        a[0:9, x:x + 9] = b
        b = bar[3:12, bx:bx + 9].copy()
        mini_button(b, 0, 0, kind, True, pressed=True)
        a[9:18, x:x + 9] = b
    b = bar[3:12, 254:263].copy()
    mini_button(b, 0, 0, "shade", True)
    a[18:27, 0:9] = b
    b = bar[3:12, 254:263].copy()
    mini_button(b, 0, 0, "shade", True, pressed=True)
    a[18:27, 9:18] = b
    a[0:14, 27:302] = bar
    a[15:29, 27:302] = main_titlebar(False)
    a[29:43, 27:302] = bar
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

# 7x11 bold digits, drawn at (1, 1) in each 9x13 cell.
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


def draw_digit(a, x, y, n):
    rect(a, x, y, 9, 13, lcd())
    if n is None:
        return
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + 1 + c, y + 1 + r, T["digit"])


STRIP_Y = 85     # Encarta: the black menu bar along the bottom of main.bmp
EN_SEPS = [15, 38, 61, 84, 107, 130, 135, 158, 162, 240, 248]


def make_main():
    if S == "en":
        a = new(275, 116, BLACK)
        rect(a, 1, 14, 273, STRIP_Y - 14, EN_CREAM)
        # the menu bar: grey separators between the items, as in Encarta's own
        for x in EN_SEPS:
            rect(a, x, STRIP_Y + 3, 1, 23, H("5a5a5a"))
        rect(a, 1, STRIP_Y, 273, 1, H("2a2a2a"))
    else:
        a = new(275, 116, TB_NAVY)
        card(a, 4, 16, 267, 96)
        rect(a, 8, 84, 259, 1, H("ebebeb"))          # the card footer's hairline
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")
    if S == "en":
        frame(a, 9, 21, 10, 45, EN_TAUPE)
    # left display: indicator, time, analyzer
    display_box(a, 21, 20, 84, 42, lcd())
    for x in (48, 60, 78, 90):
        draw_digit(a, x, 26, None)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, T["digit"])
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


def transport_icon(a, kind, x, y, w, h, pressed, ink, shadow=None, sdy=1):
    o = 1 if pressed else 0
    cx, cy = x + w // 2 + o, y + h // 2 + o

    def both(fn):
        if shadow:
            fn(sdy, shadow)
        fn(0, ink)

    if kind == "previous":
        both(lambda d, c: (rect(a, cx - 6, cy - 3 + d, 2, 7, c), tri_left(a, cx - 4, cy - 3 + d, 7, c),
                           tri_left(a, cx, cy - 3 + d, 7, c)))
    elif kind == "play":
        both(lambda d, c: tri_right(a, cx - 2, cy - 4 + d, 9, c))
    elif kind == "pause":
        both(lambda d, c: (rect(a, cx - 4, cy - 3 + d, 3, 7, c), rect(a, cx + 1, cy - 3 + d, 3, 7, c)))
    elif kind == "stop":
        both(lambda d, c: rect(a, cx - 3, cy - 3 + d, 7, 7, c))
    elif kind == "next":
        both(lambda d, c: (tri_right(a, cx - 5, cy - 3 + d, 7, c), tri_right(a, cx - 1, cy - 3 + d, 7, c),
                           rect(a, cx + 3, cy - 3 + d, 2, 7, c)))
    elif kind == "eject":
        def ej(d, c):
            for r in range(4):
                rect(a, cx - 1 - r, cy - 4 + r + d, 2 * r + 3, 1, c)
            rect(a, cx - 4, cy + 1 + d, 9, 2, c)
        both(ej)


CB_POS = {"previous": (16, 88), "play": (39, 88), "pause": (62, 88), "stop": (85, 88), "next": (108, 88),
          "eject": (136, 89)}


def menu_cell(a, x, y, w, h, mx, pressed):
    """Encarta's menu-bar item: plain black; pressed, a taupe block between the separators."""
    if pressed:
        x0 = x + (1 if (mx - 1) in EN_SEPS or mx in EN_SEPS else 0)
        x1 = x + w - (1 if (mx + w - 1) in EN_SEPS else 0)
        rect(a, x0, y + 1, x1 - x0, h - 2, EN_TAUPE)


def make_cbuttons(main):
    a = new(136, 36, body_colour())
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18), ("eject", 114, 22, 16)]
    for kind, x, w, h in specs:
        mx, my = CB_POS[kind]
        for pressed, y in ((False, 0), (True, h)):
            a[y:y + h, x:x + w] = main[my:my + h, mx:mx + w]
            if S == "en":
                menu_cell(a, x, y, w, h, mx, pressed)
                ink = BLACK if pressed else (EN_GOLD if kind == "play" else WHITE)
                transport_icon(a, kind, x, y, w, h, pressed, ink)
            elif kind == "play":
                btn(a, x + 1, y + 1, w - 2, h - 2, pressed, primary=True)
                transport_icon(a, kind, x, y, w, h, pressed, WHITE)
            else:
                if pressed:
                    rrect(a, x + 2, y + 1, w - 4, h - 2, H("eef1f4"), None, 2)
                transport_icon(a, kind, x, y, w, h, pressed, TB_TEXT if pressed else H("9a9a9a"))
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle(a, x, y, w, h, label, on, pressed):
    """A small text button on the panel (EQ / PL / ON / AUTO / PRESETS)."""
    o = 1 if pressed else 0
    btn(a, x, y, w, h, pressed, primary=on)
    tw = text_w(TINY, label)
    draw_text(a, TINY, label, x + (w - tw) // 2 + o, y + (h - 5) // 2 + o, btn_ink(on))


def en_strip_toggle(a, x, y, w, h, label, on, pressed):
    """Encarta's "Start Over" on the black bar: taupe outline when idle, gold block when on."""
    o = 1 if pressed else 0
    if on:
        rect(a, x, y + 1, w, h - 2, H("b89a44") if pressed else EN_GOLD)
        ink = BLACK
    else:
        rect(a, x, y + 1, w, h - 2, H("2a2a2a") if pressed else BLACK)
        frame(a, x, y + 1, w, h - 2, EN_TAUPE)
        ink = EN_TAUPE if not pressed else EN_TAUPE_L
    draw_text(a, TINY, label, x + (w - text_w(TINY, label)) // 2 + o, y + (h - 5) // 2 + o, ink)


def tb_toggle(a, x, y, w, h, kind, on, pressed):
    """Tumblr's footer actions: the heart (red when liked) and reblog (green when reblogged)."""
    o = 1 if pressed else 0
    if pressed:
        rrect(a, x + 1, y, w - 2, h, H("eef1f4"), None, 2)
    if kind == "shuffle":
        col = TB_RED if on else H("a7a7a7")
        icon(a, HEART, x + 4 + o, y + 5 + o, col)
        draw_text(a, WEB, "shuffle", x + 14 + o, y + 3 + o, TB_TEXT if on else H("a7a7a7"))
    else:
        reblog(a, x + (w - 11) // 2 + o, y + 2 + o, TB_GREEN if on else H("a7a7a7"))


def make_shufrep(main):
    a = new(92, 85, body_colour())
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = main[89:104, 210:238]
        a[y:y + 15, 28:75] = main[89:104, 164:211]
        if S == "en":
            en_strip_toggle(a, 0, y, 28, 15, "REPEAT", on, pressed)
            en_strip_toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
        else:
            tb_toggle(a, 0, y, 28, 15, "repeat", on, pressed)
            tb_toggle(a, 28, y, 47, 15, "shuffle", on, pressed)
    # EQ / PL sit on the main panel
    rect(a, 0, 61, 92, 24, EN_CREAM if S == "en" else WHITE)
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
    a = new(48, 9, lcd())
    ink = T["digit"]
    tri_right(a, 2, 1, 7, T["play_ind"])
    rect(a, 9 + 2, 1, 2, 7, ink)
    rect(a, 9 + 5, 1, 2, 7, ink)
    rect(a, 18 + 2, 2, 5, 5, ink)
    rect(a, 36, 0, 3, 9, lcd())
    rect(a, 39 + 1, 3, 1, 3, T["play_ind"])
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, lcd())
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


def track(a, x, y, w, h):
    if S == "en":
        rect(a, x, y, w, h, EN_TAUPE_L)
        frame(a, x, y, w, h, EN_TAUPE)
    else:
        rrect(a, x, y, w, h, H("e9e9e9"), H("d6d6d6"), 1 if h < 6 else 2)


def fill_bar(a, x, y, w, h, colour):
    if w <= 0:
        return
    rect(a, x, y, w, h, colour)
    if S == "tb":
        rect(a, x, y, w, 1, lerp(colour, WHITE, 0.25))


def en_thumb(a, x, y, w, h, selected, grip="v"):
    """Encarta's scroll thumb: a flat taupe block (gold while held)."""
    fill = EN_GOLD if selected else EN_TAUPE
    rect(a, x, y, w, h, fill)
    frame(a, x, y, w, h, H("6e5a22") if selected else H("6e6555"))
    rect(a, x + 1, y + 1, w - 2, 1, lerp(fill, WHITE, 0.35))
    gc = lerp(fill, BLACK, 0.35)
    if grip == "v":
        for gx in (x + w // 2 - 2, x + w // 2, x + w // 2 + 2):
            rect(a, gx, y + 3, 1, h - 5, gc)
    else:
        for gy in (y + h // 2 - 2, y + h // 2, y + h // 2 + 2):
            rect(a, x + 3, gy, w - 6, 1, gc)


def tb_knob(a, x, y, d, selected):
    disc(a, x, y, d, None, TB_BLUE if selected else H("c4c4c4"),
         grad=(H("f2f8fc"), H("d8e8f4")) if selected else (WHITE, H("eeeeee")))


def make_posbar(main):
    a = new(307, 10, body_colour())
    a[0:10, 0:248] = main[72:82, 16:264]
    track(a, 0, 3, 248, 4) if S == "tb" else track(a, 0, 2, 248, 6)
    if S == "en":
        en_thumb(a, 248, 0, 29, 10, False)
        en_thumb(a, 278, 0, 29, 10, True)
    else:
        for x0, sel in ((248, False), (278, True)):
            a[0:10, x0:x0 + 29] = a[0:10, 100:129]
            tb_knob(a, x0 + 9, 0, 10, sel)
    return a


def volume_cell(a, y, level, seat):
    a[y:y + 15, 0:68] = seat
    track(a, 1, y + 3, 66, 7)
    fill_to = 7 + round(level * 54)
    fill_bar(a, 2, y + 4, fill_to - 2, 5, ramp(T["level"], level))


def knob_sprites(a, tmp_row, c):
    """Tumblr's round knobs carry the track behind them (filled to the centre)."""
    for x0, sel in ((0, True), (15, False)):
        a[422:433, x0:x0 + 14] = tmp_row[1:12, c - 7:c + 7]
        tb_knob(a, x0 + 1, 422, 11, sel)


def make_volume(main):
    a = new(68, 433, body_colour())
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        volume_cell(a, y, (i + 1) / 28, seat)
        rect(a, 0, y + 13, 68, 2, a[y + 12, 0].tolist())
    if S == "en":
        en_thumb(a, 0, 422, 14, 11, True)
        en_thumb(a, 15, 422, 14, 11, False)
    else:
        tmp = new(68, 15)
        volume_cell(tmp, 0, 0.5, seat)
        knob_sprites(a, tmp, 7 + round(0.5 * 54))
    return a


def make_balance(main):
    a = new(68, 433, body_colour())
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        track(a, 10, y + 3, 36, 7)
        t = i / 27
        reach = round(16 * t)
        if reach:
            fill_bar(a, 28 - reach, y + 4, 2 * reach + 1, 5, ramp(T["level"], t))
        rect(a, 28, y + 3, 1, 7, EN_TAUPE if S == "en" else H("c4c4c4"))
        rect(a, 9, y + 13, 38, 2, a[y + 12, 9].tolist())
    if S == "en":
        en_thumb(a, 0, 422, 14, 11, True)
        en_thumb(a, 15, 422, 14, 11, False)
    else:
        tmp = new(38, 15)
        tmp[:, :] = seat
        track(tmp, 1, 3, 36, 7)
        knob_sprites(a, tmp, 11)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
EN_PLOT = H("dcd8c8")        # the InterActivities chart's plot area
EN_GRID = H("aaa48f")
EN_GRID_ROWS = (1, 16, 31, 46, 61)


def eq_titlebar(lit):
    a = new(275, 14)
    bar_fill(a, 0, 0, 275, 14, lit)
    if S == "en":
        spaced(a, "EQUALIZER", 8, 4, bar_ink(lit))
    else:
        draw_text(a, WEB_B, "Equalizer", 8, 3, bar_ink(lit))
        # the dashboard's post bar: the seven post types on a white pill
        n = len(POST_TYPES)
        pw = n * 9 + (n - 1) * 7 + 12
        px0 = 150 - pw // 2
        rrect(a, px0, 1, pw, 12, WHITE if lit else H("d0d4da"), None, 2)
        for i, (kind, col) in enumerate(POST_TYPES):
            post_icon(a, kind, px0 + 6 + i * 16, 2, col if lit else lerp(col, H("d0d4da"), 0.55))
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    """14x63 slot whose fill rises with the value (n of 0..27)."""
    v = n / 27
    top = round((1 - v) * 51) + 6
    if S == "en":
        rect(a, x, y, 14, 63, EN_PLOT)
        for r in EN_GRID_ROWS:
            rect(a, x, y + r, 14, 1, EN_GRID)
        rect(a, x + 3, y + top, 8, 63 - top, ramp(T["level"], 0.35 + 0.5 * v))
        rect(a, x + 3, y + top, 8, 1, lerp(ramp(T["level"], 0.35 + 0.5 * v), WHITE, 0.3))
        rect(a, x + 10, y + top + 1, 1, 62 - top, lerp(ramp(T["level"], 0.35 + 0.5 * v), BLACK, 0.25))
    else:
        rect(a, x, y, 14, 63, WHITE)
        track(a, x + 4, y + 1, 6, 61)
        fill_bar(a, x + 5, y + top, 4, 60 - top, ramp(T["level"], v))
        rect(a, x + 1, y + 31, 2, 1, H("d6d6d6"))
        rect(a, x + 11, y + 31, 2, 1, H("d6d6d6"))


def make_eqmain():
    if S == "en":
        a = new(275, 315, BLACK)
        rect(a, 1, 14, 273, 101, EN_CREAM)
        rect(a, 1, 14, 273, 23, EN_TAUPE)                 # the heading band holds the controls
        # the chart: preamp plot and the bands' plot, gridlines across, black axes
        for x0, x1 in ((18, 38), (74, 260)):
            rect(a, x0, 38, x1 - x0, 63, EN_PLOT)
            for r in EN_GRID_ROWS:
                rect(a, x0, 38 + r, x1 - x0, 1, EN_GRID)
            rect(a, x0 - 1, 38, 1, 64, BLACK)
            rect(a, x0 - 1, 101, x1 - x0 + 1, 1, BLACK)
        lab_y = 105
        lab_col, db_col = BLACK, EN_RED
    else:
        a = new(275, 315, TB_NAVY)
        card(a, 4, 16, 267, 96)
        rect(a, 8, 34, 259, 1, H("ebebeb"))
        lab_y = 104
        lab_col, db_col = TB_META, TB_META
    a[0:14, :] = eq_titlebar(True)
    for lbl, yy in (("+12", 41), ("0", 67), ("-12", 93)):
        text_center(a, TINY, lbl, 58, yy, db_col)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    text_center(a, TINY, "PREAMP", 28, lab_y, lab_col)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, lab_y, lab_col)

    b = eq_titlebar(True)[3:12, 264:273].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = b
    on_bg = a[18:30, 14:72].copy()
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        a[119:131, x:x + w] = on_bg[:, 0:w] if label == "ON" else on_bg[:, 26:26 + w]
        toggle(a, x + 1, 119, w - 2, 12, label, on, pressed)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    if S == "en":
        en_thumb(a, 0, 164, 11, 11, False, grip="h")
        en_thumb(a, 0, 176, 11, 11, True, grip="h")
    else:
        for y0, sel in ((164, False), (176, True)):
            tmp = new(14, 63)
            eq_slider_frame(tmp, 0, 0, 14)
            t2 = round((1 - 14 / 27) * 51)
            a[y0:y0 + 11, 0:11] = tmp[t2:t2 + 11, 1:12]
            tb_knob(a, 0, y0, 11, sel)
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    pbg = a[18:30, 217:261].copy()
    for y, pressed in ((164, False), (176, True)):
        a[y:y + 12, 224:268] = pbg
        toggle(a, 224, y, 44, 12, "PRESETS", False, pressed)
    # graph: Encarta's black InterActivity stage with a gold line; Tumblr's light field
    gbg = lcd()
    rect(a, 0, 294, 113, 19, gbg)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, lerp(gbg, T["digit"] if S == "en" else T["ink"], 0.15))
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, lerp(gbg, T["digit"] if S == "en" else T["ink"], 0.3))
    gl = T["vis_ramp"] if S == "en" else [TB_BLUE, TB_BLUE]
    for r in range(19):
        px(a, 115, 294 + r, ramp(gl, r / 18))
    for x in range(113):
        px(a, x, 314, lerp(gbg, EN_97 if S == "en" else T["ink"], 0.7) if x % 3 != 2 else gbg)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------


def bar20(w, lit):
    a = new(w, 20)
    bar_fill(a, 0, 0, w, 20, lit)
    return a


def side_tile(w, h):
    return new(w, h, body_colour())


def pl_title(t, lit):
    if S == "en":
        s = "PINPOINTER"
        spaced(t, s, 50 - spaced_w(s) // 2, 4, bar_ink(lit))
    else:
        s = "Queue"
        draw_text(t, WEB_B, s, 50 - text_w(WEB_B, s) // 2, 5, bar_ink(lit))


def make_pledit():
    side = body_colour()
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
        if S == "en":
            # the Pinpointer's taupe "Articles in list" header strip over the list and scrollbar
            st = EN_TAUPE if lit else H("8a8478")
            rect(a, 12, y + 14, 13, 6, st)
            rect(a, 127, y + 14, 25, 6, st)
            rect(a, 26, y + 14, 100, 6, st)
            rect(a, 153, y + 14, 19, 6, st)

    # left side tile
    a[42:71, 0:12] = side_tile(12, 29)
    # right side tile: the scrollbar groove at 4..13
    t = side_tile(20, 29)
    if S == "en":
        rect(t, 4, 0, 10, 29, EN_CREAM)
    else:
        rect(t, 5, 0, 8, 29, H("2e3c50"))
    a[42:71, 31:51] = t
    t = bar20(25, True)[3:12, 14:23].copy()
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        a[53:71, x:x + 8] = a[42:60, 36:44]
        if S == "en":
            en_thumb(a, x, 53, 8, 18, sel, grip="h")
        else:
            rrect(a, x + 1, 53, 6, 18, WHITE if sel else H("8d99a8"), None, 2)

    def text_button(t, bx, by, w, h, lbl):
        if S == "en":
            # the Pinpointer's "Wizard": gold outline and gold capitals on black
            frame(t, bx, by + 2, w, h - 4, EN_GOLD)
            text_center(t, TINY, lbl, bx + w // 2, by + (h - 5) // 2, EN_GOLD)
        else:
            rrect(t, bx, by + 1, w, h - 2, lerp(TB_NAVY, WHITE, 0.12), lerp(TB_NAVY, WHITE, 0.25), 2)
            text_center(t, TINY, lbl, bx + w // 2, by + (h - 5) // 2, H("dfe4ea"))

    t = side_tile(125, 38)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        text_button(t, bx, 8, 22, 18, lbl)
    a[72:110, 0:125] = t

    t = side_tile(150, 38)
    display_box(t, 6, 9, 56, 8)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        mini_face(t, bx, 22)
        mini_transport_icon(t, kind, bx, 22)
    display_box(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, T["ink"])
    rect(t, 84, 22 + 5, 1, 1, T["ink"])
    text_button(t, 106, 8, 22, 18, "LIST")
    grip = EN_TAUPE if S == "en" else H("8d99a8")
    for k in range(4):
        for j in range(k + 1):
            px(t, 145 - 3 * k + 3 * j, 29 - 3 * j, grip)
    a[72:110, 126:276] = t

    a[0:38, 179:204] = side_tile(25, 38)
    return a


def mini_face(t, bx, by):
    if S == "en":
        frame(t, bx, by, 10, 10, H("5a5a5a"))
    else:
        rrect(t, bx, by, 10, 10, lerp(TB_NAVY, WHITE, 0.12), None, 1)


def mini_transport_icon(a, kind, x, y):
    ink = (EN_GOLD if kind == "play" else WHITE) if S == "en" else H("dfe4ea")
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
    a = new(194, 109, body_colour())
    for lit, y in ((True, 0), (False, 21)):
        for px0 in (0, 26, 52, 78, 104, 130):
            t = bar20(25, lit)
            if px0 == 130:
                mini_button(t, 14, 3, "close", lit)
            a[y:y + 20, px0:px0 + 25] = t

    def bottom(w, grip):
        t = side_tile(w, 14)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    px(t, w - 4 - 3 * k + 3 * j, 10 - 3 * j, EN_TAUPE if S == "en" else H("8d99a8"))
        return t

    a[42:56, 0:125] = bottom(125, False)
    a[57:71, 0:125] = bottom(125, True)
    a[72:86, 127:152] = bottom(25, False)
    for x, w, h in ((127, 11, 29), (158, 11, 24), (139, 8, 29), (170, 8, 24)):
        a[42:42 + h, x:x + w] = side_tile(w, h)
    t = bar20(25, True)[3:12, 14:23].copy()
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: cells cut from the title piece's own rows, so the title sits seamlessly
    font = CAPS7 if S == "en" else FONT5
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        bar = bar20(194, lit)
        ink = bar_ink(lit)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(font, c) + 1
            a[y:y + 7, x:x + w] = bar[4:11, x:x + w]
            draw_text(a, font, c, x, y + (0 if S == "en" else 1), ink)
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
    rect(a, 0, 1, 47, 30, T["genex"]["win_bg"])
    btn(a, 0, 1, 47, 15, False)
    btn(a, 0, 16, 47, 15, True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    bg = lcd()
    dots = lerp(bg, T["digit"] if S == "en" else T["ink"], 0.12)
    out = [(bg, "background"), (dots, "dots")]
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
    mark = {"en": "the \"ENCARTA 97\" lettering in the main titlebar",
            "tb": "the Tumblr \"t\" in the main titlebar"}[S]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{T['name']} — a personal skin in the style of {T['subject']}. {T['mark']} logo © {T['owner']}; "
            f"private use only.\n\n"
            f"A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py) from\n"
            f"rectangles and hand-made pixel fonts; the only real mark is {mark}.\n"
            f"Not affiliated with {T['owner']}.\n"
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
            info = zipfile.ZipInfo(n, date_time=(2014, 1, 1, 0, 0, 0))
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
for _k, _v in {"<": "[", ">": "]", "{": "[", "}": "]"}.items():
    FONT_LOOKUP[_k] = FONT_LOOKUP[_v]


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
    """text.bmp's ink as the app finds it: the commonest colour clearly off the space cell's."""
    arr = np.asarray(SHEETS["text"])[:12, :155].reshape(-1, 3).astype(int)
    bg = np.asarray(SHEETS["text"])[0, 150].astype(int)
    far = arr[np.abs(arr - bg).sum(1) >= 96]
    vals, counts = np.unique(far, axis=0, return_counts=True)
    return tuple(int(v) for v in vals[counts.argmax()])


def preview_main(lit, state):
    S_ = SHEETS
    img = Image.new("RGB", (275, 116))
    img.paste(S_["main"], (0, 0))
    blit(img, S_["titlebar"], (27, 0 if lit else 15, 275, 14), 0, 0)
    cb = {"previous": (0, 23, 18), "play": (23, 23, 18), "pause": (46, 23, 18), "stop": (69, 23, 18),
          "next": (92, 22, 18)}
    for k, (x, w, h) in cb.items():
        blit(img, S_["cbuttons"], (x, 18 if state["pressed"] == k else 0, w, h), *CB_POS[k])
    blit(img, S_["cbuttons"], (114, 16 if state["pressed"] == "eject" else 0, 22, 16), 136, 89)
    for name, x0, on in (("eq", 0, state["eq"]), ("pl", 23, state["pl"])):
        pressed = state["pressed"] == name
        sx = x0 + (46 if pressed else 0)
        blit(img, S_["shufrep"], (sx, 73 if on else 61, 23, 12), 219 + x0, 58)
    blit(img, S_["titlebar"], (304, 0, 8, 43), 10, 22)
    spr = {"O": (304, 47, 8, 8, 3), "A": (312, 55, 8, 7, 11), "I": (320, 62, 8, 7, 18), "D": (328, 69, 8, 8, 25),
           "V": (336, 77, 8, 7, 33)}
    for L in state["clutter"]:
        x, y, w, h, oy = spr[L]
        blit(img, S_["titlebar"], (x, y, w, h), 10, 22 + oy)
    for name, x0, w, on, dst in (("shuffle", 28, 47, state["shuffle"], 164), ("repeat", 0, 28, state["repeat"], 210)):
        row = (2 if on else 0) + (1 if state["pressed"] == name else 0)
        blit(img, S_["shufrep"], (x0, row * 15, w, 15), dst, 89)
    blit(img, S_["playpaus"], (0 if state["playing"] else 9, 0, 9, 9), 26, 28)
    blit(img, S_["monoster"], (29, 12 if state["stereo"] else 0, 27, 12), 212, 41)
    blit(img, S_["monoster"], (0, 0 if state["stereo"] else 12, 29, 12), 239, 41)
    blit(img, S_["posbar"], (0, 0, 248, 10), 16, 72)
    tl = round(state["pos"] * 219)
    blit(img, S_["posbar"], (278 if state["seek"] else 248, 0, 29, 10), 16 + tl, 72)
    v = state["volume"]
    idx = max(0, round(v / 100 * 28) - 1)
    blit(img, S_["volume"], (0, idx * 15, 68, 13), 107, 57)
    blit(img, S_["volume"], (0 if state["vdrag"] else 15, 422, 14, 11), 107 + round(v / 100 * 54), 58)
    b = state["balance"]
    idx = int(abs(b) / 100 * 27)
    blit(img, S_["balance"], (9, idx * 15, 38, 13), 177, 57)
    blit(img, S_["balance"], (15, 422, 14, 11), 177 + round((b + 100) / 200 * 24), 58)
    secs = state["time"]
    m, s = secs // 60, secs % 60
    nums = S_["nums_ex"]
    if state["remaining"]:
        blit(img, nums, (99, 0, 9, 13), 36, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    # the title box blanked with text.bmp's space, then the title in TrueType, text.bmp's ink
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S_["text"], (150, 0, w, 6), 111 + x, 24)
    box = img.crop((111, 22, 265, 36))
    ImageDraw.Draw(box).text((0, 2 + 3 + 2), state["title"], fill=text_ink(), font=tt_font(11), anchor="lm")
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
    sheet = SHEETS["eqmain"]
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
    sheet = SHEETS["pledit"]
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
    font = tt_font(9)
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
                blit(img, g, (52, ty + 4, 5, 7), x, 4)
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


def preview():
    rows = T["rows"]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=T["title"], bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="Paused: Away From Keyboard", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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


SIZES = {"main": (275, 116), "titlebar": (344, 87), "cbuttons": (136, 36), "shufrep": (92, 85),
         "posbar": (307, 10), "volume": (68, 433), "balance": (68, 433), "monoster": (56, 24),
         "playpaus": (48, 9), "numbers": (99, 13), "nums_ex": (108, 13), "text": (155, 18),
         "pledit": (280, 186), "eqmain": (275, 315), "gen": (194, 109), "genex": (256, 64)}


def run(key):
    global T, KEY, OUT, S
    KEY, T = key, THEMES[key]
    S = T["style"]
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
            assert im.size == SIZES[n[:-4]], (n, im.size)
    # the title box is blanked with text.bmp's space cell: it must be the display colour
    assert SHEETS["text"].getpixel((152, 2)) == T["disp"] == SHEETS["main"].getpixel((200, 27)), key
    ink = text_ink()
    assert sum(abs(a - b) for a, b in zip(ink, T["disp"])) >= 200, (key, ink)
    print(f"{key:15s} -> {T['wsz']}, preview-{key}.png (title ink #{'%02x%02x%02x' % ink})")


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
