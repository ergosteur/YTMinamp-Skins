#!/usr/bin/python3
"""Social 2012: classic Winamp 2.x skins in the style of three social networks around 2012.

Forked from skins/ember/gen_skin.py (same sheets, same layouts, same preview logic, by way of the
web-nostalgia generator), with one theme per site:

    twitter-2012    the 2012 web redesign: the dark #222 top bar with Home / Connect / Discover
                    and the June 2012 bird, white modules on the #c0deed page, grey buttons and
                    the blue "Tweet" button
    instagram-2012  the iOS app: the blue leathery nav bar with the script wordmark, linen
                    background, white photo cards, the dark tab bar with its raised blue camera
                    button, round iOS slider knobs, the retro camera icon
    google-plus     Google+, 2011-2013: the black Google bar (+You in white over a red rule),
                    white pages with #f1f1f1 panels, Google's grey and red #dd4b39 buttons,
                    circles, the red g+ square

    /usr/bin/python3 -I gen_skin.py                 # every theme
    /usr/bin/python3 -I gen_skin.py google-plus     # just this one
    /usr/bin/python3 -I gen_skin.py --list

Everything is drawn here from code, except the Twitter bird and the Instagram wordmark (once
each, in the main titlebar), rasterised at build time from source/logo-*/ (see README.md).
Private use only. Each theme writes its sheets into out/<theme>/, zips them flat into
<Name>.wsz and draws preview-<theme>.png beside this script.
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

THEMES = {
    "twitter-2012": dict(
        name="Twitter-2012", site="Twitter", company="X Corp. (formerly Twitter, Inc.)", wsz="Twitter-2012.wsz",
        style="tw",
        body=H("c0deed"), panel=WHITE, panel2=H("f5f8fa"), border=H("a9c6d4"), inner=H("e1e8ed"),
        bar=[H("333333"), H("222222")], bar_dim=[H("4e4e4e"), H("444444")], bar_line=BLACK, bar_line_dim=H("2e2e2e"),
        bar_ink=WHITE, bar_ink2=H("bbbbbb"), bar_ink_dim=H("8a8a8a"), bar_ink2_dim=H("777777"),
        accent=H("0084b4"), accent2=H("2fc2ef"), accent_bg=H("e3f1f9"),
        disp=WHITE, disp_rim=H("cccccc"), disp_in=H("eeeeee"), ink=H("333333"), ink_dim=H("e8e8e8"),
        ink_mid=H("999999"), digit=H("333333"), play_ind=H("0084b4"),
        btn=[WHITE, H("e6e6e6")], btn_pr=[H("e2e2e2"), H("e6e6e6")], btn_rim=H("c2c2c2"), btn_rim_pr=H("a8a8a8"),
        btn_ink=H("444444"),
        pri=[H("33bcef"), H("019ad2")], pri_pr=[H("019ad2"), H("0083c0")], pri_rim=H("057ed0"),
        pri_rim_pr=H("00639c"), pri_ink=WHITE,
        label=H("999999"),
        track=H("eef3f6"), track_rim=H("ccd6dd"), level=[H("8fd8f5"), H("2fc2ef"), H("0084b4")],
        vis_ramp=[H("005f85"), H("0084b4"), H("1aa6dc"), H("2fc2ef"), H("8fd8f5")],
        osc=[H("0084b4"), H("1aa6dc"), H("2fc2ef"), H("6fd2f4"), H("a8e2f8")], peak=H("66757f"),
        pledit=("#333333", "#0084B4", "#FFFFFF", "#DCEEF8"),
        genex=dict(item_bg=WHITE, item_fg=H("333333"), win_bg=H("f5f8fa"), btn_fg=H("333333"), win_fg=H("333333"),
                   divider=H("e1e8ed"), sel=H("dceef8"), head_bg=H("f5f8fa"), head_fg=H("333333"),
                   head_hi=WHITE, head_lo=H("ccd6dd"), head_pr=H("e1e8ed"), dead=H("f5f8fa"),
                   sb=H("eef3f6"), sb2=H("8fb6c9"), sb_pr=H("e1e8ed"), sb_pr2=H("0084b4"), sb_dead=H("f5f8fa")),
        art=(H("c0deed"), H("0084b4")),
        rows=[("Home - Timeline (Live)", "3:12"), ("Connect - @Mentions", "3:58"),
              ("Discover - Trending Topics", "4:05"), ("Fail Whale - Over Capacity", "2:51"),
              ("140 Characters", "3:40"), ("#FF - Follow Friday", "3:21"),
              ("Retweet This", "3:33"), ("Favorites - Starred", "3:09"),
              ("Who To Follow", "3:28"), ("Promoted Tweet", "2:47"), ("Direct Messages", "3:16")],
        title="Home - Timeline (Live)  ***",
    ),
    "instagram-2012": dict(
        name="Instagram-2012", site="Instagram", company="Meta Platforms, Inc. (Instagram)", wsz="Instagram-2012.wsz",
        style="ig",
        body=H("e9e7e2"), panel=WHITE, panel2=H("f3f2ef"), border=H("cfccc6"), inner=H("dedbd5"),
        bar=[H("5583ad"), H("2f5d88")], bar_dim=[H("8b99a6"), H("6d7b89")], bar_line=H("1b3a58"),
        bar_line_dim=H("56626e"), bar_hi=H("88a9c8"), bar_hi_dim=H("a8b2bc"),
        bar_ink=WHITE, bar_ink2=WHITE, bar_ink_dim=H("e2e6ea"), bar_ink2_dim=H("e2e6ea"),
        bar_shadow=H("1d3c5b"), bar_shadow_dim=H("5d6976"),
        accent=H("3f729b"), accent2=H("125688"), accent_bg=H("e4ecf4"),
        disp=H("fbf7ee"), disp_rim=H("d5cfc2"), disp_in=H("efe8d8"), ink=H("2d5d88"), ink_dim=H("efe8da"),
        ink_mid=H("aaa290"), digit=H("2d5d88"), play_ind=H("3f729b"),
        btn=[H("fdfdfd"), H("dcdcdc")], btn_pr=[H("d0d0d0"), H("e4e4e4")], btn_rim=H("a6a6a6"), btn_rim_pr=H("8a8a8a"),
        btn_ink=H("555555"),
        pri=[H("6a99c6"), H("2f5f8f")], pri_pr=[H("2b5784"), H("4677a5")], pri_rim=H("1b3b5a"),
        pri_rim_pr=H("142d46"), pri_ink=WHITE,
        tab=[H("3c3c3c"), H("181818")], tab_pr=[H("555555"), H("2e2e2e")], tab_ink=H("9a9a9a"), tab_ink_pr=WHITE,
        label=H("9c968a"),
        track=H("f6f6f6"), track_rim=H("9c9c9c"), level=[H("4f86bf")], fill_rim=H("2a5a8a"),
        vis_ramp=[H("e5402f"), H("f39c1b"), H("f6c90e"), H("62b346"), H("2f8ad3")],
        osc=[H("2f8ad3"), H("62b346"), H("f6c90e"), H("f39c1b"), H("e5402f")], peak=H("3f729b"),
        pledit=("#333333", "#3F729B", "#FFFFFF", "#E1EAF3"),
        genex=dict(item_bg=WHITE, item_fg=H("333333"), win_bg=H("e9e7e2"), btn_fg=H("555555"), win_fg=H("333333"),
                   divider=H("dedbd5"), sel=H("e1eaf3"), head_bg=H("f3f2ef"), head_fg=H("3f729b"),
                   head_hi=WHITE, head_lo=H("cfccc6"), head_pr=H("e1eaf3"), dead=H("e9e7e2"),
                   sb=H("f3f2ef"), sb2=H("9c9c9c"), sb_pr=H("e1eaf3"), sb_pr2=H("3f729b"), sb_dead=H("e9e7e2")),
        art=(H("f3dfb8"), H("b06a3a")),
        rows=[("Earlybird - Golden Hour", "3:12"), ("X-Pro II - Rooftop", "3:58"),
              ("Valencia - Brunch Shot", "4:05"), ("Lo-fi - Latte Art", "2:51"),
              ("Amaro - Sunset Pier", "3:40"), ("Hefe - Road Trip", "3:21"),
              ("Kelvin - Neon Diner", "3:33"), ("Toaster - Polaroid Day", "3:09"),
              ("Nashville - Porch Swing", "3:28"), ("1977 - Tilt Shift", "2:47"), ("Sutro - Night Sky", "3:16")],
        title="Earlybird - Golden Hour  ***",
    ),
    "google-plus": dict(
        name="Google-Plus", site="Google+", company="Google LLC", wsz="Google-Plus.wsz",
        style="gp",
        body=WHITE, panel=H("f1f1f1"), panel2=H("f5f5f5"), border=H("d9d9d9"), inner=H("e5e5e5"),
        bar=[H("2d2d2d"), H("2d2d2d")], bar_dim=[H("4f4f4f"), H("4f4f4f")], bar_line=H("1a1a1a"),
        bar_line_dim=H("444444"),
        bar_ink=WHITE, bar_ink2=H("cccccc"), bar_ink_dim=H("bdbdbd"), bar_ink2_dim=H("9a9a9a"),
        accent=H("dd4b39"), accent2=H("d14836"), accent_bg=H("fbe4e1"),
        disp=WHITE, disp_rim=H("d9d9d9"), disp_top=H("c0c0c0"), disp_in=H("f1f1f1"), ink=H("333333"),
        ink_dim=H("ebebeb"), ink_mid=H("999999"), digit=H("404040"), play_ind=H("dd4b39"),
        btn=[H("f8f8f8"), H("ececec")], btn_pr=[H("e3e3e3"), H("ececec")], btn_rim=H("d0d0d0"), btn_rim_pr=H("b3b3b3"),
        btn_ink=H("555555"),
        pri=[H("e0533f"), H("d14836")], pri_pr=[H("c53727"), H("b8301f")], pri_rim=H("b0281a"),
        pri_rim_pr=H("8e1e12"), pri_ink=WHITE,
        label=H("999999"),
        track=H("f1f1f1"), track_rim=H("d0d0d0"), level=[H("eea195"), H("dd4b39"), H("c53727")],
        vis_ramp=[H("a82a1b"), H("c53727"), H("dd4b39"), H("e66a5a"), H("ee9488")],
        osc=[H("dd4b39"), H("e46b5c"), H("4d90fe"), H("7aaaf8"), H("aac8f8")], peak=H("4d90fe"),
        pledit=("#333333", "#DD4B39", "#FFFFFF", "#EBEBEB"),
        genex=dict(item_bg=WHITE, item_fg=H("333333"), win_bg=H("f1f1f1"), btn_fg=H("444444"), win_fg=H("333333"),
                   divider=H("e5e5e5"), sel=H("ebebeb"), head_bg=H("f5f5f5"), head_fg=H("444444"),
                   head_hi=WHITE, head_lo=H("d9d9d9"), head_pr=H("e5e5e5"), dead=H("f1f1f1"),
                   sb=H("f1f1f1"), sb2=H("c6c6c6"), sb_pr=H("e5e5e5"), sb_pr2=H("dd4b39"), sb_dead=H("f1f1f1")),
        art=(H("f1f1f1"), H("dd4b39")),
        rows=[("+You - Stream", "3:12"), ("Hangout - On Air", "3:58"),
              ("Circles - Drag To Add", "4:05"), ("Sparks - What's Hot", "2:51"),
              ("+1 - Public", "3:40"), ("Shared With Your Circles", "3:21"),
              ("Instant Upload", "3:33"), ("Ripples", "3:09"),
              ("Huddle - Messenger", "3:28"), ("Communities", "2:47"), ("Events - Party Mode", "3:16")],
        title="+You - Hangout On Air  ***",
    ),
}
THEME_KEYS = list(THEMES)
T = None
KEY = None
S = None       # style code: tw / ig / gp
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


# Fixed noise tiles (deterministic) for the Instagram linen and leather.
_RNG = np.random.default_rng(2012)
_N = _RNG.normal(0, 1, (64, 64))
_ROWN = _RNG.normal(0, 1, 64)
_COLN = _RNG.normal(0, 1, 64)
LINEN = 0.9 * _ROWN[:, None] + 0.9 * _COLN[None, :] + 0.6 * _N
LEATHER = _N.copy()
for _d in (-1, 1):
    LEATHER += 0.5 * np.roll(_N, _d, 0) + 0.5 * np.roll(_N, _d, 1)
LEATHER /= LEATHER.std()


def add_tex(a, x, y, w, h, tex, amp):
    ys = np.arange(y, y + h) % 64
    xs = np.arange(x, x + w) % 64
    a[y:y + h, x:x + w] += np.round(tex[np.ix_(ys, xs)] * amp).astype(np.int32)[:, :, None]


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


# ------------------------------------------------------------------------------------------
# Logos: the one real mark per skin, rasterised from source/ at build time
# ------------------------------------------------------------------------------------------

LOGO_SRC = {
    "twitter": os.path.join(HERE, "source", "logo-twitter", "Logo_of_Twitter.svg"),
    "instagram": os.path.join(HERE, "source", "logo-instagram", "Instagram_logo.svg"),
}


def _bands(mask, axis):
    on = mask.any(axis=axis)
    idx = np.nonzero(on)[0]
    return idx[0], idx[-1] + 1


def logo(kind, height, firm=(0.12, 0.70)):
    """Coverage (HxW float 0..1) of the logo `height` pixels tall, cropped to its ink."""
    os.makedirs(SCRATCH, exist_ok=True)
    png = os.path.join(SCRATCH, f"logo-{kind}.png")
    subprocess.run(["/usr/bin/rsvg-convert", "-h", "800", LOGO_SRC[kind], "-o", png], check=True)
    arr = np.asarray(Image.open(png).convert("RGBA")).astype(np.float32)
    cov = arr[..., 3] / 255
    m = cov > 0.3
    y0, y1 = _bands(m, 1)
    x0, x1 = _bands(m, 0)
    cov = cov[y0:y1, x0:x1]
    h0, w0 = cov.shape
    w = max(1, round(w0 * height / h0))
    ci = Image.fromarray((cov * 255).astype(np.uint8), "L").resize((w, height), Image.LANCZOS)
    c = np.asarray(ci).astype(np.float32) / 255
    return np.clip((c - firm[0]) / firm[1], 0, 1)


def paste_logo(a, x, y, alpha, ink):
    h, w = alpha.shape
    region = a[y:y + h, x:x + w].astype(np.float32)
    src = np.zeros((h, w, 3), np.float32) + np.array(ink, np.float32)
    out = region * (1 - alpha[..., None]) + src * alpha[..., None]
    a[y:y + h, x:x + w] = np.round(out).astype(np.int32)
    return w


LOGO_CACHE = {}


def cached_logo(kind, height):
    k = (kind, height)
    if k not in LOGO_CACHE:
        LOGO_CACHE[k] = logo(kind, height)
    return LOGO_CACHE[k]


# ------------------------------------------------------------------------------------------
# Theme surfaces
# ------------------------------------------------------------------------------------------


def bar_fill(a, x, y, w, h, lit):
    """The titlebar band, whatever its height (14 for main/EQ, 20 for playlist/gen)."""
    top, bot = T["bar"] if lit else T["bar_dim"]
    vgrad(a, x, y, w, h, top, bot)
    if S == "ig":
        add_tex(a, x, y, w, h, LEATHER, 2.2)
        rect(a, x, y, w, 1, T["bar_hi"] if lit else T["bar_hi_dim"])
    rect(a, x, y + h - 1, w, 1, T["bar_line"] if lit else T["bar_line_dim"])


def bar_inks(lit):
    """(bright ink, secondary ink) on the bars."""
    return (T["bar_ink"], T["bar_ink2"]) if lit else (T["bar_ink_dim"], T["bar_ink2_dim"])


def body_fill(a, x, y, w, h):
    rect(a, x, y, w, h, T["body"])
    if S == "ig":
        add_tex(a, x, y, w, h, LINEN, 1.6)


def module(a, x, y, w, h, fill=None, border=None):
    """A content box: Twitter's rounded white module, Instagram's photo card, Google's panel."""
    fill = T["panel"] if fill is None else fill
    border = T["border"] if border is None else border
    if S == "tw":
        rrect(a, x, y, w, h, fill, border, 2)
    elif S == "ig":
        rect(a, x, y, w, h, fill)
        frame(a, x, y, w, h, border)
        rect(a, x + 1, y + h, w - 1, 1, lerp(T["body"], BLACK, 0.12))   # the card's drop shadow
    else:
        rect(a, x, y, w, h, fill)
        frame(a, x, y, w, h, border)


def display_box(a, x, y, w, h):
    """A display window (text/digits sit on T['disp']): a text field with an inset top edge."""
    rect(a, x, y, w, h, T["disp"])
    frame(a, x - 1, y - 1, w + 2, h + 2, T["disp_rim"])
    if S == "gp":
        rect(a, x - 1, y - 1, w + 2, 1, T["disp_top"])
    rect(a, x, y, w, 1, T["disp_in"])


def btn(a, x, y, w, h, pressed, primary=False, r=None):
    """Twitter / Google / iOS push button."""
    r = (1 if S == "gp" else 2) if r is None else r
    if primary:
        grad, rim = (T["pri_pr"], T["pri_rim_pr"]) if pressed else (T["pri"], T["pri_rim"])
    else:
        grad, rim = (T["btn_pr"], T["btn_rim_pr"]) if pressed else (T["btn"], T["btn_rim"])
    rrect(a, x, y, w, h, None, rim, r, grad=grad)
    if pressed:
        # an inset shadow along the top
        rect(a, x + 2, y + 1, w - 4, 1, lerp(grad[0], BLACK, 0.08))
    elif primary:
        rect(a, x + 2, y + 1, w - 4, 1, lerp(grad[0], WHITE, 0.25))
    elif S == "ig":
        rect(a, x + 2, y + 1, w - 4, 1, WHITE)


def btn_ink(primary, pressed=False):
    return T["pri_ink"] if primary else T["btn_ink"]


def tab_cell(a, x, y, w, h, pressed, src=None):
    """Instagram's tab bar: the bar's own gradient (copied from main.bmp), lighter when pressed."""
    if src is not None:
        a[y:y + h, x:x + w] = src
    else:
        vgrad(a, x, y, w, h, *T["tab"])
    if pressed:
        rrect(a, x + 1, y + 1, w - 2, h - 2, None, H("111111"), 2, grad=T["tab_pr"])
        rect(a, x + 3, y + 2, w - 6, 1, H("6a6a6a"))


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button."""
    if S == "tw":
        face = [H("1a1a1a"), H("111111")] if pressed else ([H("4a4a4a"), H("383838")] if lit else
                                                           [H("5c5c5c"), H("525252")])
        rrect(a, x, y, 9, 9, None, H("0d0d0d") if lit else H("3a3a3a"), 1, grad=face)
        ink = WHITE if pressed else (H("c8c8c8") if lit else H("8a8a8a"))
    elif S == "ig":
        face = [H("24486d"), H("33618d")] if pressed else ([H("4d79a3"), H("2b5680")] if lit else
                                                           [H("8796a4"), H("6f7d8b")])
        rrect(a, x, y, 9, 9, None, T["bar_line"] if lit else H("56626e"), 1, grad=face)
        if not pressed:
            rect(a, x + 1, y + 1, 7, 1, lerp(face[0], WHITE, 0.25))
        ink = WHITE if lit else H("e2e6ea")
    else:
        face = H("4a4a4a") if pressed else (H("2d2d2d") if lit else H("4f4f4f"))
        rect(a, x, y, 9, 9, face)
        frame(a, x, y, 9, 9, H("5a5a5a") if lit else H("6a6a6a"))
        ink = WHITE if pressed else (H("cccccc") if lit else H("9a9a9a"))
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


QUILL = [  # a feather quill, nib at the bottom left
    "......####",
    ".....#####",
    "....####.#",
    "...####.#.",
    "...###.#..",
    "..###.#...",
    "..##......",
    ".#........",
    "#.........",
]

CIRCLES_ICON = [  # Google+'s circles: two overlapping rings
    "..###...###..",
    ".#...#.#...#.",
    "#.....#.....#",
    "#....#.#....#",
    "#.....#.....#",
    ".#...#.#...#.",
    "..###...###..",
]


def circles_icon(a, x, y, col):
    icon(a, CIRCLES_ICON, x, y, col)


def gplus_square(a, x, y, size=13, lit=True):
    """The red g+ square (hand-drawn)."""
    red = T["accent"] if lit else H("a8a8a8")
    rrect(a, x, y, size, size, None, lerp(red, BLACK, 0.18), 1, grad=(lerp(red, WHITE, 0.08), lerp(red, BLACK, 0.06)))
    g = [".####", "##.##", "##.##", ".####", "...##", "####."]
    p = [".#.", "###", ".#."]
    icon(a, g, x + 2, y + 3, WHITE)
    icon(a, p, x + 8, y + 3, WHITE)


def ig_camera(a, x, y):
    """Instagram's retro camera icon (2010-2016), 13x13, drawn by hand."""
    m = round_mask(13, 13, 2)
    for r in range(13):
        for c in range(13):
            if not m[r, c]:
                continue
            if r < 5:
                col = lerp(H("efe3cc"), H("d8c4a2"), r / 4)
            else:
                col = lerp(H("8e623f"), H("5f3c24"), (r - 5) / 7)
                if (r * 7 + c * 3) % 5 == 0:
                    col = lerp(col, BLACK, 0.12)                     # a hint of leather grain
            px(a, x + c, y + r, col)
    # the edge
    e = H("4a2e1a")
    for r in range(13):
        for c in range(13):
            if m[r, c] and (r in (0, 12) or c in (0, 12) or not m[max(0, r - 1), c] or not m[min(12, r + 1), c]):
                px(a, x + c, y + r, lerp(a[y + r, x + c].tolist(), e, 0.55))
    # the rainbow stripe, top left
    for i, col in enumerate((H("e5402f"), H("f6c90e"), H("62b346"), H("2f8ad3"))):
        rect(a, x + 2 + i, y + 1, 1, 4, col)
    # viewfinder, top right
    rect(a, x + 9, y + 2, 2, 2, H("222222"))
    px(a, x + 9, y + 2, H("6f8fb0"))
    # the lens
    for r in range(13):
        for c in range(13):
            d = ((r - 7.5) ** 2 + (c - 6) ** 2) ** 0.5
            if d <= 3.6:
                col = H("1c1c1c") if d > 2.4 else (H("3b5a7a") if d > 1.2 else H("5c86ad"))
                px(a, x + c, y + r, col)
    px(a, x + 5, y + 6, WHITE)
    # the line between the top and the body
    for c in range(1, 12):
        if not (3 <= c <= 9):
            px(a, x + c, y + 5, H("4a2e1a"))


def emblem(a, x, y):
    """13x15 at the About spot."""
    if S == "tw":
        # the blue compose button
        rrect(a, x, y + 1, 13, 13, None, T["pri_rim"], 2, grad=T["pri"])
        rect(a, x + 2, y + 2, 9, 1, lerp(T["pri"][0], WHITE, 0.3))
        icon(a, QUILL, x + 2, y + 3, WHITE)
    elif S == "ig":
        ig_camera(a, x, y + 1)
    else:
        gplus_square(a, x, y + 1)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, T["panel"])
    if S == "gp":
        rect(a, 0, 0, 8, 43, T["panel2"])
    frame(a, 0, 0, 8, 43, T["inner"] if S != "ig" else T["border"])
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, T["accent_bg"])
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, T["accent"] if on else T["label"])
    return a


HOUSE = ["...#...", "..###..", ".#####.", "#######", ".##.##.", ".##.##.", ".##.##."]
AT = [".####.", "#....#", "#.##.#", "#.#.##", "#.###.", "#.....", ".####."]
HASH = [".#..#.", ".#..#.", "######", ".#..#.", "######", ".#..#.", ".#..#."]


def main_titlebar(lit):
    a = new(275, 14)
    bar_fill(a, 0, 0, 275, 14, lit)
    ink, ink2 = bar_inks(lit)
    if S == "tw":
        # Home (current, white) / Connect / Discover, each with its icon, as the 2012 top bar
        x = 18
        for ic, word, cur in ((HOUSE, "Home", True), (AT, "Connect", False), (HASH, "Discover", False)):
            col = ink if cur else ink2
            icon(a, ic, x, 3, col)
            x += len(ic[0]) + 3
            x = draw_text(a, WEB_B if cur else WEB, word, x, 3, col, shadow=BLACK, sdx=0, sdy=-1) + 7
        # the bird, then the blue compose button
        al = cached_logo("twitter", 11)
        bx = 186 - al.shape[1] // 2
        paste_logo(a, bx, 2, al, T["accent2"] if lit else H("8a8a8a"))
        cx = 222
        rrect(a, cx, 2, 17, 10, None, T["pri_rim"] if lit else H("3a3a3a"), 2,
              grad=T["pri"] if lit else (H("6a6a6a"), H("5a5a5a")))
        q = ["....###", "...####", "..###.#", "..##.#.", ".##....", "#......"]
        icon(a, q, cx + 5, 4, WHITE if lit else H("bdbdbd"))
    elif S == "ig":
        al = cached_logo("instagram", 13)
        lx = (275 - al.shape[1]) // 2
        shadow = T["bar_shadow"] if lit else T["bar_shadow_dim"]
        sh = np.zeros_like(al)
        sh[:-1] = al[1:]                                     # iOS: the text's shadow is one px above
        paste_logo(a, lx, 0, sh * 0.7, shadow)
        paste_logo(a, lx, 0, al, ink)
    else:
        # the Google bar: +You in white over a red rule, the rest grey
        x = 21
        items = ["+You", "Search", "Images", "Mail", "Drive", "More"]
        for i, s in enumerate(items):
            cur = i == 0
            f = WEB_B if cur else WEB
            w = text_w(f, s)
            if cur:
                rect(a, x - 3, 0, w + 6, 2, T["accent"] if lit else H("8a8a8a"))
            draw_text(a, f, s, x, 4, ink if cur else ink2)
            x += w + 8
        # the triangle after "More"
        tx = x - 6
        for r in range(3):
            rect(a, tx + r, 7 + r, 5 - 2 * r, 1, ink2)
        # the notification count, red when there are some
        nx = 222
        rect(a, nx, 2, 16, 10, T["accent"] if lit else H("6a6a6a"))
        text_center(a, WEB_B, "3", nx + 8, 2, WHITE if lit else H("bdbdbd"))
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, T["body"])
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

# 7x11 bold digits (Helvetica-bold-ish), drawn at (1, 1) in each 9x13 cell.
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


def draw_digit(a, x, y, n):
    rect(a, x, y, 9, 13, T["disp"])
    if n is None:
        return
    for r, row in enumerate(DIGITS[n]):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + 1 + c, y + 1 + r, T["digit"])


TAB_Y = 85    # Instagram: where the dark tab bar starts on main.bmp


def make_main():
    a = new(275, 116, T["body"])
    body_fill(a, 0, 0, 275, 116)
    a[0:14, :] = main_titlebar(True)
    if S == "tw":
        frame(a, 0, 14, 275, 102, lerp(T["body"], BLACK, 0.18))
        module(a, 4, 16, 267, 68)
        # the module's grey footer (as under the tweet box) holds the transport
        module(a, 4, 85, 267, 26, T["panel2"])
        rect(a, 5, 85, 265, 1, T["inner"])
    elif S == "ig":
        frame(a, 0, 14, 275, 102, lerp(T["body"], BLACK, 0.2))
        module(a, 4, 16, 267, 66)
        # the dark tab bar along the bottom
        rect(a, 1, TAB_Y, 273, 1, H("0e0e0e"))
        rect(a, 1, TAB_Y + 1, 273, 1, H("5a5a5a"))
        vgrad(a, 1, TAB_Y + 2, 273, 115 - TAB_Y - 2, *T["tab"])
        rect(a, 0, 115, 275, 1, BLACK)
    else:
        frame(a, 0, 14, 275, 102, T["border"])
        # the grey ribbon down the left, Google+ style
        rect(a, 1, 15, 6, 100, T["panel2"])
        rect(a, 7, 15, 1, 100, T["inner"])
        # the panel the transport sits on
        rect(a, 13, 85, 258, 26, T["panel"])
        frame(a, 13, 85, 258, 26, T["inner"])
    a[22:65, 10:18] = clutter_bar("")
    # left display: indicator, time, analyzer
    display_box(a, 21, 20, 84, 42)
    for x in (48, 60, 78, 90):
        draw_digit(a, x, 26, None)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, T["digit"])
    # right display: title row, then the kbps/kHz row
    display_box(a, 109, 21, 159, 15)
    display_box(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, T["ink_mid"])
    draw_text(a, TINY, "KHZ", 169, 44, T["ink_mid"])
    # slider and seek seats are the module itself; a hairline under the seek bar
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


def tray_colour():
    return T["tab"][1] if S == "ig" else (T["panel2"] if S == "tw" else T["panel"])


def main_panel_colour():
    return T["panel"]


CB_POS = {"previous": (16, 88), "play": (39, 88), "pause": (62, 88), "stop": (85, 88), "next": (108, 88),
          "eject": (136, 89)}


def make_cbuttons(main):
    a = new(136, 36, tray_colour())
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18), ("eject", 114, 22, 16)]
    for kind, x, w, h in specs:
        mx, my = CB_POS[kind]
        for pressed, y in ((False, 0), (True, h)):
            primary = kind == "play"
            if S == "ig":
                src = main[my:my + h, mx:mx + w]
                if primary:
                    a[y:y + h, x:x + w] = src
                    btn(a, x + 1, y, w - 2, h, pressed, primary=True, r=2)
                    transport_icon(a, kind, x, y, w, h, pressed, WHITE, T["pri_rim"], -1)
                else:
                    tab_cell(a, x, y, w, h, pressed, src)
                    transport_icon(a, kind, x, y, w, h, pressed, T["tab_ink_pr"] if pressed else T["tab_ink"],
                                   BLACK, -1)
            else:
                a[y:y + h, x:x + w] = main[my:my + h, mx:mx + w]
                btn(a, x, y, w, h, pressed, primary=primary)
                transport_icon(a, kind, x, y, w, h, pressed, btn_ink(primary))
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle(a, x, y, w, h, label, on, pressed, where="panel"):
    """A small text button; on = the theme's primary (blue/red) button."""
    o = 1 if pressed else 0
    if S == "ig" and where == "tray":
        if on:
            btn(a, x + 1, y + 1, w - 2, h - 2, pressed, primary=True, r=2)
            ink = WHITE
        else:
            tab_cell(a, x, y, w, h, pressed, a[y:y + h, x:x + w].copy())
            ink = T["tab_ink_pr"] if pressed else T["tab_ink"]
    else:
        btn(a, x, y, w, h, pressed, primary=on)
        ink = btn_ink(on)
    tw = text_w(TINY, label)
    draw_text(a, TINY, label, x + (w - tw) // 2 + o, y + (h - 5) // 2 + o, ink)


def make_shufrep(main):
    a = new(92, 85, tray_colour())
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = main[89:104, 210:238]
        a[y:y + 15, 28:75] = main[89:104, 164:211]
        toggle(a, 0, y, 28, 15, "REPEAT", on, pressed, "tray")
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed, "tray")
    # EQ / PL sit on the main panel, not the tray
    rect(a, 0, 61, 92, 24, main_panel_colour())
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
    ink = T["digit"]
    tri_right(a, 2, 1, 7, T["play_ind"])
    rect(a, 9 + 2, 1, 2, 7, ink)
    rect(a, 9 + 5, 1, 2, 7, ink)
    rect(a, 18 + 2, 2, 5, 5, ink)
    rect(a, 36, 0, 3, 9, T["disp"])
    rect(a, 39 + 1, 3, 1, 3, T["play_ind"])
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


def track(a, x, y, w, h):
    if S == "ig":
        rrect(a, x, y, w, h, None, T["track_rim"], 2 if h > 5 else 1, grad=(H("dcdcdc"), WHITE))
    elif S == "tw":
        rrect(a, x, y, w, h, T["track"], T["track_rim"], 1)
        rect(a, x + 1, y + 1, w - 2, 1, lerp(T["track"], BLACK, 0.06))
    else:
        rect(a, x, y, w, h, T["track"])
        frame(a, x, y, w, h, T["track_rim"])


def fill_bar(a, x, y, w, h, colour):
    """The filled part of a track (inside its rim)."""
    if w <= 0:
        return
    if S == "ig":
        vgrad(a, x, y, w, h, lerp(colour, WHITE, 0.35), lerp(colour, BLACK, 0.2))
        rect(a, x, y, w, 1, lerp(colour, WHITE, 0.55))
    else:
        rect(a, x, y, w, h, colour)
        rect(a, x, y, w, 1, lerp(colour, WHITE, 0.3))


def thumb(a, x, y, w, h, selected, grip="v"):
    """Seek / volume / EQ thumb for Twitter and Google: a small push button with a grip."""
    btn(a, x, y, w, h, False, primary=selected, r=1)
    gc = lerp(T["pri"][1], WHITE, 0.5) if selected else H("a0a0a0")
    cx = x + w // 2
    if grip == "v":
        for gx in (cx - 2, cx, cx + 2):
            rect(a, gx, y + 3, 1, h - 6, gc)
    else:
        for gy in (y + h // 2 - 2, y + h // 2, y + h // 2 + 2):
            rect(a, x + 3, gy, w - 6, 1, gc)


def ios_knob(a, x, y, d, selected):
    disc(a, x, y, d, None, H("8a8a8a") if not selected else H("5f7f9f"),
         grad=(WHITE, H("d6d6d6")) if not selected else (H("e8f0f8"), H("b9cde0")))
    px(a, x + d // 2 - 1, y + 2, WHITE)


def make_posbar(main):
    a = new(307, 10, T["body"])
    a[0:10, 0:248] = main[72:82, 16:264]
    track(a, 0, 2, 248, 6)
    if S == "ig":
        for x0, sel in ((248, False), (278, True)):
            a[0:10, x0:x0 + 29] = a[0:10, 100:129]            # the plain track behind the knob
            ios_knob(a, x0 + 9, 0, 10, sel)
    else:
        thumb(a, 248, 0, 29, 10, False)
        thumb(a, 278, 0, 29, 10, True)
    return a


def volume_cell(a, y, level, seat):
    a[y:y + 15, 0:68] = seat
    track(a, 1, y + 3, 66, 7)
    fill_to = 7 + round(level * 54)
    fill_bar(a, 2, y + 4, fill_to - 2, 5, ramp(T["level"], level))


def make_volume(main):
    a = new(68, 433, T["body"])
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        volume_cell(a, y, (i + 1) / 28, seat)
        rect(a, 0, y + 13, 68, 2, a[y + 12, 0].tolist())
    if S == "ig":
        # each knob carries the track behind it: filled to its centre, empty after
        for x0, sel in ((0, True), (15, False)):
            tmp = new(68, 15)
            volume_cell(tmp, 0, 0.5, seat)
            c = 7 + round(0.5 * 54)                            # the fill's end in tmp
            a[422:433, x0:x0 + 14] = tmp[1:12, c - 7:c + 7]
            ios_knob(a, x0 + 1, 422, 11, sel)
    else:
        thumb(a, 0, 422, 14, 11, True)
        thumb(a, 15, 422, 14, 11, False)
    return a


def make_balance(main):
    a = new(68, 433, T["body"])
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        track(a, 10, y + 3, 36, 7)
        t = i / 27
        reach = round(16 * t)
        if reach and S != "ig":
            fill_bar(a, 28 - reach, y + 4, 2 * reach + 1, 5, ramp(T["level"], t))
        elif reach:
            fill_bar(a, 28 - reach, y + 4, 2 * reach + 1, 5, lerp(T["level"][0], WHITE, 0.45 * (1 - t)))
        rect(a, 28, y + 3, 1, 7, T["track_rim"])
        rect(a, 9, y + 13, 38, 2, a[y + 12, 9].tolist())
    if S == "ig":
        for x0, sel in ((0, True), (15, False)):
            tmp = new(38, 15)
            tmp[:, :] = seat
            track(tmp, 1, 3, 36, 7)
            a[422:433, x0:x0 + 14] = tmp[1:12, 4:18]
            ios_knob(a, x0 + 1, 422, 11, sel)
    else:
        thumb(a, 0, 422, 14, 11, True)
        thumb(a, 15, 422, 14, 11, False)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def nav_title(a, s, cx, y, lit, left=None):
    """A window title on a bar: Twitter's #hashtag, iOS's centred bold title, Google's +You item."""
    ink, ink2 = bar_inks(lit)
    if S == "tw":
        w = text_w(WEB_B, s)
        x = cx - w // 2 if left is None else left
        sh = BLACK if lit else None
        x = draw_text(a, WEB_B, "#", x, y, T["accent2"] if lit else ink2, shadow=sh, sdx=0, sdy=-1) + 1
        draw_text(a, WEB_B, s[1:], x, y, ink, shadow=sh, sdx=0, sdy=-1)
    elif S == "ig":
        w = text_w(WEB_B, s)
        x = cx - w // 2 if left is None else left
        draw_text(a, WEB_B, s, x, y, ink, shadow=T["bar_shadow"] if lit else T["bar_shadow_dim"], sdx=0, sdy=-1)
    else:
        w = text_w(WEB_B, s)
        x = cx - w // 2 if left is None else left
        if lit:
            rect(a, x - 3, 0, w + 6, 2, T["accent"])
        draw_text(a, WEB_B, s, x, y, ink)
    return x, w


def eq_titlebar(lit):
    a = new(275, 14)
    bar_fill(a, 0, 0, 275, 14, lit)
    if S == "tw":
        nav_title(a, "#equalizer", 0, 3, lit, left=18)
    elif S == "ig":
        nav_title(a, "Equalizer", 137, 2, lit)
    else:
        x, w = nav_title(a, "Equalizer", 0, 4, lit, left=18)
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_bay_colour():
    return T["panel"]


def eq_slider_frame(a, x, y, n):
    """14x63 slot whose fill rises with the value (n of 0..27)."""
    rect(a, x, y, 14, 63, eq_bay_colour())
    track(a, x + 4, y + 1, 6, 61)
    v = n / 27
    top = round((1 - v) * 51) + 6
    fill_bar(a, x + 5, y + top, 4, 60 - top, ramp(T["level"], v))
    rect(a, x + 1, y + 31, 2, 1, T["label"])
    rect(a, x + 11, y + 31, 2, 1, T["label"])


def make_eqmain():
    a = new(275, 315, T["body"])
    body_fill(a, 0, 0, 275, 315)
    a[0:14, :] = eq_titlebar(True)
    if S == "tw":
        frame(a, 0, 14, 275, 102, lerp(T["body"], BLACK, 0.18))
        module(a, 4, 15, 267, 98)
        rect(a, 5, 36, 265, 1, T["inner"])
        lab_y = 106
    elif S == "ig":
        frame(a, 0, 14, 275, 102, lerp(T["body"], BLACK, 0.2))
        module(a, 12, 36, 251, 76)
        lab_y = 105
    else:
        frame(a, 0, 14, 275, 102, T["border"])
        rect(a, 1, 15, 6, 100, T["panel2"])
        rect(a, 7, 15, 1, 100, T["inner"])
        rect(a, 14, 36, 249, 77, T["panel"])
        frame(a, 14, 36, 249, 77, T["inner"])
        lab_y = 106
    for lbl, yy in (("+12", 41), ("0", 67), ("-12", 93)):
        text_center(a, TINY, lbl, 58, yy, T["label"])
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    text_center(a, TINY, "PREAMP", 28, lab_y, T["label"])
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, lab_y, T["label"])

    # under the window: buttons
    b = a[0:14, 264:273][3:12].copy()
    b = eq_titlebar(True)[3:12, 264:273].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = b
    on_bg = a[18:30, 14:72].copy()                            # what the ON / AUTO buttons sit on
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        a[119:131, x:x + w] = on_bg[:, 0:w] if label == "ON" else on_bg[:, 26:26 + w]
        toggle(a, x, 119, w, 12, label, on, pressed)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    if S == "ig":
        for y0, sel in ((164, False), (176, True)):
            tmp = new(14, 63)
            eq_slider_frame(tmp, 0, 0, 14)
            t2 = round((1 - 14 / 27) * 51)
            a[y0:y0 + 11, 0:11] = tmp[t2:t2 + 11, 1:12]
            ios_knob(a, 0, y0, 11, sel)
    else:
        thumb(a, 0, 164, 11, 11, False, grip="h")
        thumb(a, 0, 176, 11, 11, True, grip="h")
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    pbg = a[18:30, 217:261].copy()
    for y, pressed in ((164, False), (176, True)):
        a[y:y + 12, 224:268] = pbg
        toggle(a, 224, y, 44, 12, "PRESETS", False, pressed)
    # graph
    rect(a, 0, 294, 113, 19, T["disp"])
    grid = lerp(T["disp"], T["ink"], 0.1)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, grid)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, lerp(T["disp"], T["ink"], 0.25))
    gl = T["vis_ramp"]
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
    return T["body"] if S != "gp" else T["panel"]


def side_tile(w, h):
    t = new(w, h, frame_side())
    if S == "ig":
        add_tex(t, 0, 0, w, h, LINEN, 1.6)
    return t


def pl_title(t, lit):
    if S == "tw":
        nav_title(t, "#playlist", 50, 6, lit)
    elif S == "ig":
        nav_title(t, "Playlist", 50, 5, lit)
    else:
        ink, ink2 = bar_inks(lit)
        w = text_w(WEB_B, "Playlist")
        x0 = 50 - (w + 17) // 2
        circles_icon(t, x0, 7, ink2)
        nav_title(t, "Playlist", 0, 6, lit, left=x0 + 17)


def make_pledit():
    side = frame_side()
    edge = lerp(T["body"], BLACK, 0.18) if S == "tw" else (lerp(T["body"], BLACK, 0.2) if S == "ig" else T["border"])
    inner = T["inner"] if S != "ig" else T["border"]
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

    # left side tile
    t = side_tile(12, 29)
    rect(t, 0, 0, 1, 29, edge)
    rect(t, 11, 0, 1, 29, inner)
    a[42:71, 0:12] = t
    # right side tile: list edge, scrollbar groove at 5..12, outer edge
    t = side_tile(20, 29)
    rect(t, 0, 0, 1, 29, inner)
    rect(t, 19, 0, 1, 29, edge)
    rect(t, 4, 0, 10, 29, T["track"] if S != "ig" else H("f3f3f3"))
    rect(t, 4, 0, 1, 29, T["track_rim"])
    rect(t, 13, 0, 1, 29, T["track_rim"])
    a[42:71, 31:51] = t
    t = bar20(25, True)[3:12, 14:23].copy()
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        a[53:71, x:x + 8] = a[42:60, 36:44]
        if S == "ig":
            rrect(a, x, 53, 8, 18, None, H("5f7f9f") if sel else H("8a8a8a"), 2,
                  grad=(H("e8f0f8"), H("b9cde0")) if sel else (WHITE, H("d6d6d6")))
        else:
            thumb(a, x, 53, 8, 18, sel, grip="h")

    dark = S == "ig"     # Instagram: the bottom is the dark tab bar

    def bottom_base(w):
        t = side_tile(w, 38)
        if dark:
            rect(t, 0, 0, w, 1, H("0e0e0e"))
            rect(t, 0, 1, w, 1, H("5a5a5a"))
            vgrad(t, 0, 2, w, 36, *T["tab"])
            rect(t, 0, 37, w, 1, BLACK)
        else:
            rect(t, 0, 0, w, 1, inner)
            rect(t, 0, 37, w, 1, edge)
        return t

    def text_button(t, bx, by, w, h, lbl):
        if dark:
            rrect(t, bx, by, w, h, None, H("0a0a0a"), 2, grad=(H("4a4a4a"), H("262626")))
            rect(t, bx + 2, by + 1, w - 4, 1, H("6a6a6a"))
            text_center(t, TINY, lbl, bx + w // 2, by + (h - 5) // 2 - 1, BLACK)
            text_center(t, TINY, lbl, bx + w // 2, by + (h - 5) // 2, H("d0d0d0"))
        else:
            btn(t, bx, by, w, h, False)
            text_center(t, TINY, lbl, bx + w // 2, by + (h - 5) // 2, T["btn_ink"])

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, edge)
    if not dark:
        rect(t, 1, 0, 11, 1, side)
        rect(t, 11, 0, 1, 1, inner)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        text_button(t, bx, 8, 22, 18, lbl)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, edge)
    if not dark:
        rect(t, 130, 0, 19, 1, side)
        rect(t, 130, 0, 1, 1, inner)
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
    grip = H("8a8a8a") if dark else lerp(side, BLACK, 0.3)
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx, gy, grip)
            px(t, gx + 1, gy + 1, BLACK if dark else WHITE)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


def mini_face(t, bx, by):
    if S == "ig":
        rrect(t, bx, by, 10, 10, None, H("0a0a0a"), 1, grad=(H("4a4a4a"), H("262626")))
    else:
        btn(t, bx, by, 10, 10, False, r=1)


def mini_transport_icon(a, kind, x, y):
    ink = H("d0d0d0") if S == "ig" else T["btn_ink"]
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
    edge = lerp(T["body"], BLACK, 0.18) if S == "tw" else (lerp(T["body"], BLACK, 0.2) if S == "ig" else T["border"])
    inner = T["inner"] if S != "ig" else T["border"]
    a = new(194, 109, side)
    for lit, y in ((True, 0), (False, 21)):
        for px0 in (0, 26, 52, 78, 104, 130):
            t = bar20(25, lit)
            if px0 == 130:
                mini_button(t, 14, 3, "close", lit)
            if S == "gp" and lit:
                # the red rule over the title, Google bar style: under the title and 4px past it
                if px0 == 26:
                    rect(t, 21, 0, 4, 2, T["accent"])
                elif px0 == 52:
                    rect(t, 0, 0, 25, 2, T["accent"])
                elif px0 == 78:
                    rect(t, 0, 0, 4, 2, T["accent"])
            a[y:y + 20, px0:px0 + 25] = t

    dark = S == "ig"

    def bottom(w, grip, left_edge):
        t = side_tile(w, 14)
        if dark:
            rect(t, 0, 0, w, 1, H("0e0e0e"))
            rect(t, 0, 1, w, 1, H("5a5a5a"))
            vgrad(t, 0, 2, w, 12, *T["tab"])
            rect(t, 0, 13, w, 1, BLACK)
        else:
            rect(t, 0, 13, w, 1, edge)
            rect(t, 0, 0, w, 1, inner)
        if left_edge:
            rect(t, 0, 0, 1, 14, edge)
            if not dark:
                rect(t, 1, 0, 10, 1, side)
                rect(t, 10, 0, 1, 1, inner)
        else:
            rect(t, w - 1, 0, 1, 14, edge)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 10 - 3 * j
                    px(t, gx, gy, H("8a8a8a") if dark else lerp(side, BLACK, 0.3))
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    t = bottom(125, True, False)
    if not dark:
        rect(t, 114, 0, 10, 1, side)
        rect(t, 114, 0, 1, 1, inner)
    a[57:71, 0:125] = t
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = side_tile(w, h)
        if outer_left:
            rect(t, 0, 0, 1, h, edge)
            rect(t, w - 1, 0, 1, h, inner)
        else:
            rect(t, w - 1, 0, 1, h, edge)
            rect(t, 0, 0, 1, h, inner)
        a[42:42 + h, x:x + w] = t
    t = bar20(25, True)[3:12, 14:23].copy()
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: cells cut from the title piece's own rows 4..10, so the title sits seamlessly
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        bar = new(194, 20)
        for xx in range(0, 194, 25):
            bar[:, xx:xx + 25] = a[(0 if lit else 21):(20 if lit else 41), 52:77][:, :min(25, 194 - xx)]
        ink, _ = bar_inks(lit)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            a[y:y + 7, x:x + w] = bar[4:11, x:x + w]
            if S == "ig":
                draw_text(a, FONT5, c, x, y + 1, ink, shadow=T["bar_shadow"] if lit else T["bar_shadow_dim"],
                          sdx=0, sdy=-1)
            else:
                draw_text(a, FONT5, c, x, y + 1, ink)
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
    disp = T["disp"]
    dots = lerp(disp, T["ink"], 0.1)
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
    name, site, owner = T["name"], T["site"], T["company"].rstrip(".")
    era = {"tw": "Twitter, 2012", "ig": "Instagram's iOS app, 2012", "gp": "Google+, 2011-2013"}[S]
    mark = {"tw": "the Twitter bird in the main titlebar",
            "ig": "the Instagram wordmark in the main titlebar and its camera icon at the About spot",
            "gp": "the g+ square at the About spot"}[S]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{name} — a personal skin in the style of {era}. {site} logo © {owner}; private use only.\n\n"
            f"A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py) from\n"
            f"rectangles and hand-made pixel fonts; the only marks are {mark}.\n"
            f"Not affiliated with {owner}.\n"
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
            info = zipfile.ZipInfo(n, date_time=(2012, 6, 6, 0, 0, 0))
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
