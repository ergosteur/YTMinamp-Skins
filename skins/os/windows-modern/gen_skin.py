#!/usr/bin/python3
"""Windows Modern: three classic Winamp 2.x skins in the style of Windows 8, 10 and 11.

Forked from skins/ember/gen_skin.py (same sheets, same layouts, same preview logic). Every pixel
is drawn here from code: flat rectangles, rounded rectangles, soft shadows and hand-made pixel
fonts and line icons. The one outside asset is each version's Windows logo, small in the About
spot, rasterised at build time from the SVGs in source/ (private use only; see README.md). No
wallpapers, no screenshots: a style homage.

    /usr/bin/python3 -I gen_skin.py              # all three
    /usr/bin/python3 -I gen_skin.py win10        # just this one

Themes:
  win8   Metro: the Start screen. A saturated purple body, live tiles in Metro tile colours with
         white glyphs, thin lowercase lettering, no gradients, shadows or rounding at all.
  win10  Dark mode, black and blue: near-black chrome, white MDL2-style line glyphs, Windows 10
         blue (#0078d7) as the one accent, a 1px accent window border, square corners.
  win11  Light Mica: a faintly blue-tinted light body, rounded white cards and buttons with a
         soft shadow and a darker bottom stroke, Fluent line icons, accent #005fb8, circular
         slider thumbs with an accent centre, an accent-filled round play button.

Each writes its sheets into out/<theme>/, zips them flat into Windows-<n>.wsz and draws
preview-<theme>.png beside this script (both windows' states, 2x).
"""

import os
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SEP = (255, 0, 255)  # gen.bmp letter separators (never shown)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    if n == 0:
        return stops[0]
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def hexc(c):
    return "#%02X%02X%02X" % c


def H(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

METRO = dict(lime=H("a4c400"), green=H("60a917"), emerald=H("008a00"), teal=H("00aba9"),
             cyan=H("1ba1e2"), cobalt=H("0050ef"), indigo=H("6a00ff"), violet=H("aa00ff"),
             magenta=H("d80073"), crimson=H("a20025"), red=H("e51400"), orange=H("fa6800"),
             amber=H("f0a30a"))


def make_theme(key):
    if key == "win8":
        purple = H("4617b4")
        deep = H("2d0d82")
        return dict(
            key=key, style="win8", ver="8", wsz="Windows-8.wsz", preview="preview-win8.png",
            titles=dict(main="music", eq="equalizer", pl="playlist"), title_x="left",
            body=purple, noise=0.0, border=None,
            bar=purple, title_ink=WHITE, title_dim=H("a58ae0"),
            cap_ink=WHITE, cap_dim=H("a58ae0"), cap_press=WHITE, cap_press_ink=purple,
            close_press=METRO["red"],
            disp=METRO["teal"], disp_ink=WHITE, disp_dim=lerp(METRO["teal"], WHITE, 0.28),
            info=deep, info_ink=WHITE, info_dim=H("8466cf"),
            label=H("c9b8f0"), label_dim=H("8466cf"),
            track=H("7d5bd6"), fill=METRO["cyan"], thumb=WHITE, thumb_pr=H("d6ccf2"),
            btn=deep, btn_pr=H("1d0758"), btn_ink=WHITE, btn_ink_pr=H("d6ccf2"),
            tog_ink=H("a58ae0"), tog_on=METRO["magenta"], tog_on_ink=WHITE,
            tiles=dict(previous=METRO["cobalt"], play=METRO["green"], pause=METRO["orange"],
                       stop=METRO["red"], next=METRO["magenta"], eject=METRO["teal"]),
            toggles=dict(shuffle=METRO["orange"], repeat=METRO["amber"], eq=METRO["green"],
                         pl=METRO["cyan"], on=METRO["green"], auto=METRO["orange"]),
            list_bg=deep, list_ink=WHITE, list_cur=H("6fd3ff"), list_sel=METRO["magenta"],
            accent=METRO["cyan"], digits_bold=False,
            vis_bg=METRO["teal"], vis_dots=lerp(METRO["teal"], BLACK, 0.12),
            vis=[WHITE, lerp(WHITE, METRO["teal"], 0.18), lerp(WHITE, METRO["teal"], 0.38),
                 lerp(WHITE, METRO["teal"], 0.55)],
            osc=WHITE, peak=H("fff2a0"),
            graph=[WHITE, H("bff5f4")],
            logo="2012", logo_h=13, logo_ink=WHITE,
        )
    if key == "win10":
        blue = H("0078d7")
        return dict(
            key=key, style="win10", ver="10", wsz="Windows-10.wsz", preview="preview-win10.png",
            titles=dict(main="Now Playing", eq="Equalizer", pl="Playlist"), title_x="left",
            body=H("1f1f1f"), noise=0.0, border=blue,
            bar=H("000000"), title_ink=WHITE, title_dim=H("7a7a7a"),
            cap_ink=WHITE, cap_dim=H("7a7a7a"), cap_press=H("4d4d4d"), cap_press_ink=WHITE,
            close_press=H("e81123"),
            disp=H("000000"), disp_ink=WHITE, disp_dim=H("3a3a3a"),
            info=H("000000"), info_ink=WHITE, info_dim=H("6e6e6e"),
            label=H("a0a0a0"), label_dim=H("5c5c5c"),
            track=H("7a7a7a"), fill=blue, thumb=blue, thumb_pr=H("f0f0f0"),
            btn=H("2b2b2b"), btn_pr=H("555555"), btn_ink=WHITE, btn_ink_pr=WHITE,
            tog_ink=H("a0a0a0"), tog_on=blue, tog_on_ink=WHITE,
            tiles=None, toggles=None,
            list_bg=H("000000"), list_ink=WHITE, list_cur=H("4cc2ff"), list_sel=H("003e6b"),
            accent=blue, digits_bold=False,
            vis_bg=H("000000"), vis_dots=H("1c1c1c"),
            vis=[H("99d9ff"), H("4cc2ff"), blue, H("005a9e"), H("003e6b")],
            osc=H("4cc2ff"), peak=WHITE,
            graph=[H("4cc2ff"), blue],
            logo="2012", logo_h=13, logo_ink=blue,
        )
    if key == "win11":
        acc = H("005fb8")
        return dict(
            key=key, style="win11", ver="11", wsz="Windows-11.wsz", preview="preview-win11.png",
            titles=dict(main="Now playing", eq="Equalizer", pl="Playlist"), title_x="left",
            body=H("f1f3f8"), body2=H("eceff6"), noise=0.55, border=H("c9ccd3"),
            bar=H("f1f3f8"), title_ink=H("1a1a1a"), title_dim=H("8a8d93"),
            cap_ink=H("1a1a1a"), cap_dim=H("8a8d93"), cap_press=H("dfe2e8"), cap_press_ink=H("1a1a1a"),
            close_press=H("c42b1c"),
            card=H("fbfbfc"), card_edge=H("e3e5ea"), card_stroke=H("d0d3d9"),
            disp=H("ffffff"), disp_ink=H("1a1a1a"), disp_dim=H("e2e5ea"),
            info=H("ffffff"), info_ink=H("1a1a1a"), info_dim=H("9a9ea6"),
            label=H("5d5f63"), label_dim=H("a3a6ad"),
            track=H("8a8d93"), fill=acc, thumb=WHITE, thumb_pr=WHITE,
            btn=H("fbfbfc"), btn_pr=H("f2f3f5"), btn_ink=H("1a1a1a"), btn_ink_pr=H("5d5f63"),
            tog_ink=H("5d5f63"), tog_on=acc, tog_on_ink=WHITE,
            tiles=None, toggles=None,
            list_bg=WHITE, list_ink=H("1a1a1a"), list_cur=acc, list_sel=H("cce4f7"),
            accent=acc, digits_bold=True,
            vis_bg=WHITE, vis_dots=H("eef0f4"),
            vis=[H("003a75"), acc, H("3c8ad6"), H("8cbde9"), H("cfe3f6")],
            osc=acc, peak=H("1a1a1a"),
            graph=[acc, H("3c8ad6")],
            logo="2021", logo_h=11, logo_ink=H("0078d4"),
        )
    raise KeyError(key)


THEME_KEYS = ["win8", "win10", "win11"]
T = None
OUT = None


def S():
    return T["style"]


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def new(w, h, col=None):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = T["body"] if col is None else col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):y + h, max(0, x):x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def outline(a, x, y, w, h, col):
    rect(a, x, y, w, 1, col)
    rect(a, x, y + h - 1, w, 1, col)
    rect(a, x, y, 1, h, col)
    rect(a, x + w - 1, y, 1, h, col)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def composite(a, x, y, alpha, col, opacity=1.0):
    """Blends a solid colour through an alpha mask (h x w floats) at x, y, clipped."""
    h, w = alpha.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(a.shape[1], x + w), min(a.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    al = alpha[y0 - y:y1 - y, x0 - x:x1 - x][:, :, None] * opacity
    reg = a[y0:y1, x0:x1].astype(np.float64)
    a[y0:y1, x0:x1] = np.round(reg * (1 - al) + np.array(col, dtype=np.float64) * al).astype(np.int32)


def rrect_alpha(w, h, r, ss=6):
    """Coverage of a w x h rounded rectangle with corner radius r (supersampled)."""
    ys = (np.arange(h * ss) + 0.5) / ss
    xs = (np.arange(w * ss) + 0.5) / ss
    X, Y = np.meshgrid(xs, ys)
    cx = np.clip(X, r, w - r)
    cy = np.clip(Y, r, h - r)
    inside = ((X - cx) ** 2 + (Y - cy) ** 2) <= r * r + 1e-9 if r > 0 else np.ones_like(X, bool)
    return inside.reshape(h, ss, w, ss).mean(axis=(1, 3))


def circle_alpha(d, ss=8):
    return rrect_alpha(d, d, d / 2, ss)


def rfill(a, x, y, w, h, col, r=0):
    if w <= 0 or h <= 0:
        return
    if r <= 0:
        rect(a, x, y, w, h, col)
    else:
        composite(a, x, y, rrect_alpha(w, h, r), col)


def soft_shadow(a, x, y, w, h, r, opacity=0.13, blur=1.3, dy=1):
    pad = 4
    al = np.zeros((h + 2 * pad, w + 2 * pad))
    al[pad:pad + h, pad:pad + w] = rrect_alpha(w, h, r)
    img = Image.fromarray((al * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(blur))
    al = np.asarray(img).astype(np.float64) / 255
    composite(a, x - pad, y - pad + dy, al, (20, 30, 50), opacity)


def card(a, x, y, w, h, face=None, r=3, shadow=True, edge=None, stroke=None, top_hi=False):
    """Win11 elevated surface: soft shadow, 1px border with a darker bottom stroke, face."""
    face = T["card"] if face is None else face
    edge = T["card_edge"] if edge is None else edge
    stroke = T["card_stroke"] if stroke is None else stroke
    if shadow:
        soft_shadow(a, x, y, w, h, r)
    rfill(a, x, y, w, h, stroke, r)
    rfill(a, x, y, w, h - 1, edge, r)
    rfill(a, x + 1, y + 1, w - 2, h - 3 if h > 4 else h - 2, face, max(0, r - 1))
    rect(a, x + r, y + h - 2, w - 2 * r, 1, face) if h > 4 else None
    if top_hi:
        rect(a, x + r, y + 1, w - 2 * r, 1, WHITE)


def body_fill(a, x, y, w, h, seed=7):
    """The window body: flat, or (win11) a soft vertical Mica tint with a faint grain."""
    if S() != "win11":
        rect(a, x, y, w, h, T["body"])
        return
    top, bot = T["body"], T["body2"]
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(top, bot, r / max(1, h - 1)))
    rng = np.random.default_rng(seed)
    n = rng.normal(0, T["noise"], (h, w))
    tint = np.stack([n * 0.8, n * 0.9, n * 1.2], -1)
    a[y:y + h, x:x + w] = np.round(a[y:y + h, x:x + w] + tint).astype(np.int32)


# ------------------------------------------------------------------------------------------
# Pixel fonts (all drawn for this skin)
# ------------------------------------------------------------------------------------------


def G(*rows):
    return list(rows)


# 4x5 caps for text.bmp (the marquee, kbps/kHz, the playlist's readouts).
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

# 3x5 caps for small labels.
TINY = {
    "A": G(".#.", "#.#", "###", "#.#", "#.#"), "B": G("##.", "#.#", "##.", "#.#", "##."),
    "C": G(".##", "#..", "#..", "#..", ".##"), "D": G("##.", "#.#", "#.#", "#.#", "##."),
    "E": G("###", "#..", "##.", "#..", "###"), "F": G("###", "#..", "##.", "#..", "#.."),
    "G": G(".##", "#..", "#.#", "#.#", ".##"), "H": G("#.#", "#.#", "###", "#.#", "#.#"),
    "I": G("###", ".#.", ".#.", ".#.", "###"), "K": G("#.#", "#.#", "##.", "#.#", "#.#"),
    "L": G("#..", "#..", "#..", "#..", "###"), "M": G("#.#", "###", "###", "#.#", "#.#"),
    "N": G("##.", "#.#", "#.#", "#.#", "#.#"), "O": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "P": G("##.", "#.#", "##.", "#..", "#.."),
    "Q": G(".#.", "#.#", "#.#", "##.", ".##"), "R": G("##.", "#.#", "##.", "#.#", "#.#"),
    "S": G(".##", "#..", ".#.", "..#", "##."), "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#.#", "#.#", "#.#", "#.#", "###"), "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "X": G("#.#", "#.#", ".#.", "#.#", "#.#"), "Y": G("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": G("###", "..#", ".#.", "#..", "###"), " ": G("..", "..", "..", "..", ".."),
}
for _c in "0123456789+-.":
    TINY[_c] = FONT5[_c]

# The UI font: a thin proportional face, caps 7 rows (rows 0-6), x-height 5 (rows 2-6), descenders
# in rows 7-8. Titles; its caps are also gen.bmp's letters (7-row cells).
_UP = {
    "A": G("..#..", ".#.#.", "#...#", "#...#", "#####", "#...#", "#...#"),
    "B": G("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": G(".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": G("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."),
    "E": G("####", "#...", "#...", "###.", "#...", "#...", "####"),
    "F": G("####", "#...", "#...", "###.", "#...", "#...", "#..."),
    "G": G(".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": G("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": G("#", "#", "#", "#", "#", "#", "#"),
    "J": G("...#", "...#", "...#", "...#", "...#", "#..#", ".##."),
    "K": G("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": G("#...", "#...", "#...", "#...", "#...", "#...", "####"),
    "M": G("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": G("#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": G(".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": G("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": G(".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": G("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": G(".###.", "#...#", "#....", ".###.", "....#", "#...#", ".###."),
    "T": G("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": G("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": G("#...#", "#...#", "#...#", ".#.#.", ".#.#.", ".#.#.", "..#.."),
    "W": G("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": G("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": G("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": G("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
}
_LO = {
    "a": G("....", "....", ".##.", "...#", ".###", "#..#", ".###"),
    "b": G("#...", "#...", "###.", "#..#", "#..#", "#..#", "###."),
    "c": G("...", "...", ".##", "#..", "#..", "#..", ".##"),
    "d": G("...#", "...#", ".###", "#..#", "#..#", "#..#", ".###"),
    "e": G("....", "....", ".##.", "#..#", "####", "#...", ".###"),
    "f": G("..#", ".#.", "###", ".#.", ".#.", ".#.", ".#."),
    "g": G("....", "....", ".###", "#..#", "#..#", "#..#", ".###", "...#", ".##."),
    "h": G("#...", "#...", "###.", "#..#", "#..#", "#..#", "#..#"),
    "i": G("#", ".", "#", "#", "#", "#", "#"),
    "j": G(".#", "..", ".#", ".#", ".#", ".#", ".#", ".#", "#."),
    "k": G("#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#"),
    "l": G("#", "#", "#", "#", "#", "#", "#"),
    "m": G(".....", ".....", "####.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": G("....", "....", "###.", "#..#", "#..#", "#..#", "#..#"),
    "o": G("....", "....", ".##.", "#..#", "#..#", "#..#", ".##."),
    "p": G("....", "....", "###.", "#..#", "#..#", "#..#", "###.", "#...", "#..."),
    "q": G("....", "....", ".###", "#..#", "#..#", "#..#", ".###", "...#", "...#"),
    "r": G("...", "...", "#.#", "##.", "#..", "#..", "#.."),
    "s": G("...", "...", ".##", "#..", ".#.", "..#", "##."),
    "t": G(".#.", ".#.", "###", ".#.", ".#.", ".#.", "..#"),
    "u": G("....", "....", "#..#", "#..#", "#..#", "#..#", ".###"),
    "v": G("...", "...", "#.#", "#.#", "#.#", "#.#", ".#."),
    "w": G(".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."),
    "x": G("...", "...", "#.#", "#.#", ".#.", "#.#", "#.#"),
    "y": G("....", "....", "#..#", "#..#", "#..#", "#..#", ".###", "...#", ".##."),
    "z": G("...", "...", "###", "..#", ".#.", "#..", "###"),
}
UI = {}
for _k, _g in list(_UP.items()) + list(_LO.items()):
    UI[_k] = _g + ["." * len(_g[0])] * (9 - len(_g))
UI[" "] = ["..."] * 9


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1):
    for c in s:
        if c not in font:
            continue
        g = font[c]
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col)
        x += len(g[0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap)


# ------------------------------------------------------------------------------------------
# Line icons (1px strokes, MDL2 / Fluent style; Metro's solid for win8)
# ------------------------------------------------------------------------------------------

REPEAT_ICON = G(".......#...", ".########..", "#......#...", "#.........#",
                "...#......#", "..########.", "...#.......")
SHUFFLE_ICON = G("........#..", "##....####.", "..#..#..#..", "...##......",
                 "..#..#..#..", "##....####.", "........#..")


LOGO_SVGS = {"2012": os.path.join(HERE, "source", "logo-2012", "logo.svg"),
             "2021": os.path.join(HERE, "source", "logo-2021", "logo.svg")}


def logo_alpha(which, h):
    """The Windows logo (Wikimedia Commons SVG, see README) as an h-tall coverage mask: rasterised
    large with rsvg-convert, box-filtered down, then contrast-curved so the panes stay crisp and
    the thin gaps between them stay open."""
    import subprocess
    png = os.path.join(HERE, "out", "scratch", f"logo-{which}-260.png")
    os.makedirs(os.path.dirname(png), exist_ok=True)
    if not os.path.exists(png):
        subprocess.run(["/usr/bin/rsvg-convert", "-h", "260", LOGO_SVGS[which], "-o", png], check=True)
    im = Image.open(png).convert("RGBA")
    al = Image.fromarray(np.asarray(im)[..., 3])
    w = round(im.width * h / im.height)
    cov = np.asarray(al.resize((w, h), Image.BOX)).astype(np.float64) / 255
    return np.clip((cov - 0.45) / 0.35, 0, 1)


def bitmap(a, rows, x, y, col):
    for r, row in enumerate(rows):
        for k, ch in enumerate(row):
            if ch == "#":
                px(a, x + k, y + r, col)


def tri_right(a, x, y, h, col, hollow=False):
    """Right-pointing triangle h tall (odd)."""
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        if hollow and 0 < r < h - 1:
            px(a, x, y + r, col)
            px(a, x + n - 1, y + r, col)
        else:
            rect(a, x, y + r, n if not hollow or r in (0, h - 1) else 1, 1, col)


def tri_left(a, x, y, h, col, hollow=False):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        if hollow and 0 < r < h - 1:
            px(a, x + half, y + r, col)
            px(a, x + half + 1 - n, y + r, col)
        else:
            rect(a, x + half + 1 - n, y + r, n, 1, col)


def transport_glyph(a, kind, cx, cy, ink):
    """The transport glyphs, centred on (cx, cy): solid for win8, line art for win10/11."""
    line = S() != "win8"
    if kind == "previous":
        if line:
            rect(a, cx - 4, cy - 3, 1, 7, ink)
            tri_left(a, cx - 3, cy - 3, 7, ink, hollow=True)
            tri_left(a, cx + 1, cy - 3, 7, ink, hollow=True)
        else:
            rect(a, cx - 5, cy - 3, 2, 7, ink)
            tri_left(a, cx - 3, cy - 3, 7, ink)
            tri_left(a, cx + 1, cy - 3, 7, ink)
    elif kind == "play":
        if line:
            for r in range(9):
                n = 4 - abs(r - 4)
                px(a, cx - 2, cy - 4 + r, ink)
                px(a, cx - 2 + n, cy - 4 + r, ink)
        else:
            tri_right(a, cx - 2, cy - 4, 9, ink)
    elif kind == "pause":
        if line:
            outline(a, cx - 3, cy - 3, 2, 7, ink)
            outline(a, cx + 1, cy - 3, 2, 7, ink)
        else:
            rect(a, cx - 3, cy - 3, 2, 7, ink)
            rect(a, cx + 1, cy - 3, 2, 7, ink)
    elif kind == "stop":
        if line:
            outline(a, cx - 3, cy - 3, 7, 7, ink)
        else:
            rect(a, cx - 3, cy - 3, 7, 7, ink)
    elif kind == "next":
        if line:
            tri_right(a, cx - 4, cy - 3, 7, ink, hollow=True)
            tri_right(a, cx, cy - 3, 7, ink, hollow=True)
            rect(a, cx + 4, cy - 3, 1, 7, ink)
        else:
            tri_right(a, cx - 5, cy - 3, 7, ink)
            tri_right(a, cx - 1, cy - 3, 7, ink)
            rect(a, cx + 3, cy - 3, 2, 7, ink)
    elif kind == "eject":
        for r in range(4):
            if line and 0 < r < 3:
                px(a, cx - r, cy - 4 + r, ink)
                px(a, cx + r, cy - 4 + r, ink)
            else:
                rect(a, cx - r, cy - 4 + r, 2 * r + 1, 1, ink)
        rect(a, cx - 3, cy + 1, 7, 1 if line else 2, ink)


def mini_glyph(a, kind, cx, cy, ink):
    """5x5 playlist mini-transport glyphs."""
    if kind == "previous":
        rect(a, cx - 3, cy - 2, 1, 5, ink)
        tri_left(a, cx - 2, cy - 2, 5, ink)
        tri_left(a, cx + 1, cy - 2, 5, ink)
    elif kind == "play":
        tri_right(a, cx - 1, cy - 3, 7, ink, hollow=S() != "win8")
    elif kind == "pause":
        rect(a, cx - 2, cy - 2, 1 if S() != "win8" else 2, 5, ink)
        rect(a, cx + 1, cy - 2, 1 if S() != "win8" else 2, 5, ink)
    elif kind == "stop":
        (outline if S() != "win8" else rect)(a, cx - 2, cy - 2, 5, 5, ink)
    elif kind == "next":
        tri_right(a, cx - 3, cy - 2, 5, ink)
        tri_right(a, cx, cy - 2, 5, ink)
        rect(a, cx + 3, cy - 2, 1, 5, ink)
    elif kind == "eject":
        for r in range(3):
            rect(a, cx - r, cy - 3 + r, 2 * r + 1, 1, ink)
        rect(a, cx - 2, cy + 1, 5, 1, ink)


# ------------------------------------------------------------------------------------------
# Caption buttons (9x9) and titlebars
# ------------------------------------------------------------------------------------------


def cap_button(a, x, y, kind, lit=True, pressed=False, bg=None):
    """9x9 caption button drawn over whatever bar is already at x, y."""
    st = S()
    ink = T["cap_ink"] if lit else T["cap_dim"]
    if pressed:
        if kind == "close":
            if st == "win11":
                rfill(a, x, y, 9, 9, T["close_press"], 2)
            else:
                rect(a, x, y, 9, 9, T["close_press"])
            ink = WHITE
        else:
            if st == "win11":
                rfill(a, x, y, 9, 9, T["cap_press"], 2)
            else:
                rect(a, x, y, 9, 9, T["cap_press"])
            ink = T["cap_press_ink"]
    if kind == "options":
        if st == "win8":      # a chevron, Metro's app-bar "more"
            for i in range(3):
                px(a, x + 2 + i, y + 3 + i, ink)
                px(a, x + 6 - i, y + 3 + i, ink)
        elif st == "win10":   # the hamburger
            for r in (2, 4, 6):
                rect(a, x + 2, y + r, 5, 1, ink)
        else:                 # Fluent "more": three dots
            for c in (2, 4, 6):
                px(a, x + c, y + 4, ink)
    elif kind == "minimize":
        rect(a, x + 2, y + 5, 5, 1, ink)
    elif kind == "shade":
        outline(a, x + 2, y + 2, 5, 5, ink)
    elif kind == "close":
        for i in range(5):
            px(a, x + 2 + i, y + 2 + i, ink)
            px(a, x + 6 - i, y + 2 + i, ink)


def bar_base(w, h):
    a = new(w, h, T["bar"])
    if S() == "win10":
        rect(a, 0, 0, w, 1, T["border"])
    elif S() == "win11":
        rect(a, 0, 0, w, 1, T["border"])
    return a


def edges(a, left=True, right=True):
    """The 1px window border down the sides (win10 accent, win11 grey)."""
    if T["border"] is None:
        return
    if left:
        rect(a, 0, 0, 1, a.shape[0], T["border"])
    if right:
        rect(a, a.shape[1] - 1, 0, 1, a.shape[0], T["border"])


def title_text(a, s, x, y, lit, center=False):
    col = T["title_ink"] if lit else T["title_dim"]
    if center:
        x = x - text_w(UI, s) // 2
    draw_text(a, UI, s, x, y, col)


def main_titlebar(lit):
    a = bar_base(275, 14)
    edges(a)
    title_text(a, T["titles"]["main"], 21, 2 if S() != "win8" else 2, lit)
    cap_button(a, 6, 3, "options", lit)
    cap_button(a, 244, 3, "minimize", lit)
    cap_button(a, 254, 3, "shade", lit)
    cap_button(a, 264, 3, "close", lit)
    return a


CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    st = S()
    a = new(8, 43)
    if st == "win8":
        rect(a, 0, 0, 8, 43, T["info"])
    elif st == "win10":
        rect(a, 0, 0, 8, 43, T["btn"])
    else:
        rect(a, 0, 0, 8, 43, T["body"])
        card(a, 0, 0, 8, 43, r=3, shadow=False)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            if st == "win11":
                rfill(a, 1, y, 6, h, T["accent"], 1)
            else:
                rect(a, 1 if st != "win8" else 0, y, 6 if st != "win8" else 8, h, T["accent"] if st == "win10" else METRO["magenta"])
        gy = y + (h - 5) // 2
        ink = WHITE if on else (T["label"] if st != "win11" else T["label"])
        draw_text(a, TINY, letter, 2, gy, ink)
    return a


def make_titlebar(main):
    a = new(344, 87)
    for kind, x in (("options", 0), ("minimize", 9), ("close", 18)):
        pos = {"options": 6, "minimize": 244, "close": 264}[kind]
        for pressed, y in ((False, 0), (True, 9)):
            b = main[3:12, pos:pos + 9].copy()
            cap_button(b, 0, 0, kind, True, pressed, bg=tuple(main[7, pos + 4]))
            a[y:y + 9, x:x + 9] = b
    for pressed, x in ((False, 0), (True, 9)):
        b = main[3:12, 254:263].copy()
        cap_button(b, 0, 0, "shade", True, pressed, bg=tuple(main[7, 258]))
        a[18:27, x:x + 9] = b
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
# Digits (numbers.bmp / nums_ex.bmp): thin, modern, 7x11 in a 9x13 cell
# ------------------------------------------------------------------------------------------

DIGITS = {
    0: G(".#####.", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#",
         "#.....#", "#.....#", ".#####."),
    1: G("...#...", "..##...", ".#.#...", "...#...", "...#...", "...#...", "...#...", "...#...",
         "...#...", "...#...", "...#..."),
    2: G(".#####.", "#.....#", "......#", "......#", ".....#.", "....#..", "...#...", "..#....",
         ".#.....", "#......", "#######"),
    3: G(".#####.", "#.....#", "......#", "......#", "......#", "..####.", "......#", "......#",
         "......#", "#.....#", ".#####."),
    4: G(".....#.", "....##.", "...#.#.", "..#..#.", ".#...#.", "#....#.", "#######", ".....#.",
         ".....#.", ".....#.", ".....#."),
    5: G("#######", "#......", "#......", "#......", "######.", "......#", "......#", "......#",
         "......#", "#.....#", ".#####."),
    6: G("..####.", ".#.....", "#......", "#......", "######.", "#.....#", "#.....#", "#.....#",
         "#.....#", "#.....#", ".#####."),
    7: G("#######", "......#", ".....#.", ".....#.", "....#..", "....#..", "...#...", "...#...",
         "..#....", "..#....", "..#...."),
    8: G(".#####.", "#.....#", "#.....#", "#.....#", "#.....#", ".#####.", "#.....#", "#.....#",
         "#.....#", "#.....#", ".#####."),
    9: G(".#####.", "#.....#", "#.....#", "#.....#", "#.....#", ".######", "......#", "......#",
         "......#", ".....#.", ".####.."),
}


def digit(a, n, x, y, col, bold):
    g = DIGITS[n]
    for r, row in enumerate(g):
        for k, ch in enumerate(row):
            if ch == "#":
                px(a, x + 1 + k, y + 1 + r, col)
    if bold:
        # thicken the left verticals by one column to the right (a semibold weight)
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#" and k + 1 < len(row) and row[k + 1] == "." and \
                        (r > 0 and g[r - 1][k] == "#" or r + 1 < len(g) and g[r + 1][k] == "#") and k < 3:
                    px(a, x + 2 + k, y + 1 + r, col)
                if ch == "#" and k > 0 and row[k - 1] == "." and k >= 4 and \
                        (r > 0 and g[r - 1][k] == "#" or r + 1 < len(g) and g[r + 1][k] == "#"):
                    px(a, x + k, y + 1 + r, col)


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["disp"])
    for n in range(10):
        digit(a, n, 9 * n, 0, T["disp_ink"], T["digits_bold"])
    if ex:
        rect(a, 99 + 2, 6, 5, 1, T["disp_ink"])
        if T["digits_bold"]:
            rect(a, 99 + 2, 7, 5, 1, T["disp_ink"])
    return a


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116)
# ------------------------------------------------------------------------------------------


def panel(a, x, y, w, h, col, r=3):
    """A display panel: a flat block (win8/win10) or a white rounded card (win11)."""
    st = S()
    if st == "win8":
        rect(a, x, y, w, h, col)
    elif st == "win10":
        rect(a, x, y, w, h, col)
        outline(a, x - 1, y - 1, w + 2, h + 2, H("333333"))
    else:
        card(a, x - 1, y - 1, w + 2, h + 2, face=col, r=r)


def make_main():
    st = S()
    a = new(275, 116)
    body_fill(a, 0, 0, 275, 116, seed=11)
    edges(a)
    if T["border"] is not None:
        rect(a, 0, 115, 275, 1, T["border"])
    a[0:14, :] = main_titlebar(True)
    # left display: indicator, time, analyzer; a live tile on win8
    if st == "win8":
        rect(a, 20, 20, 85, 43, T["disp"])
    else:
        panel(a, 21, 21, 83, 41, T["disp"])
    a[22:65, 10:18] = clutter_bar("")
    for yy in (30, 35):
        rect(a, 74, yy, 2, 2, T["disp_ink"])
    # right display: the title row, the kbps/kHz/mono/stereo row
    if st == "win8":
        rect(a, 108, 20, 161, 17, T["info"])
        rect(a, 108, 39, 161, 16, T["info"])
    else:
        panel(a, 109, 21, 159, 15, T["info"])
        panel(a, 109, 40, 159, 14, T["info"])
    draw_text(a, TINY, "KBPS", 128, 44, T["info_dim"])
    draw_text(a, TINY, "KHZ", 168, 44, T["info_dim"])
    if st == "win11":
        # a soft card behind the transport row
        card(a, 13, 85, 230, 24, face=lerp(T["body"], WHITE, 0.45), r=4, shadow=True)
    # the note mark (the About spot)
    lh = T["logo_h"]
    composite(a, 253 + (13 - lh) // 2, 91 + (15 - lh) // 2, logo_alpha(T["logo"], lh), T["logo_ink"])
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36)
# ------------------------------------------------------------------------------------------

CB_SPECS = [("previous", 0, 23, 18, 16, 88), ("play", 23, 23, 18, 39, 88), ("pause", 46, 23, 18, 62, 88),
            ("stop", 69, 23, 18, 85, 88), ("next", 92, 22, 18, 108, 88)]


def button(a, x, y, w, h, pressed, kind=None, face=None):
    """A button face in the theme's style, drawn over the background already at x, y."""
    st = S()
    if st == "win8":
        col = face if face is not None else T["btn"]
        if pressed:
            col = lerp(col, BLACK, 0.25)
            rect(a, x + 2, y + 2, w - 4, h - 4, col)   # Metro's press: the tile sinks back
        else:
            rect(a, x + 1, y + 1, w - 2, h - 2, col)
    elif st == "win10":
        col = face if face is not None else (T["btn_pr"] if pressed else T["btn"])
        if face is not None and pressed:
            col = lerp(face, WHITE, 0.2)
        rect(a, x + 1, y + 1, w - 2, h - 2, col)
    else:
        if face is not None:
            soft_shadow(a, x + 1, y + 1, w - 2, h - 2, 3, opacity=0.18 if not pressed else 0.06)
            rfill(a, x + 1, y + 1, w - 2, h - 2, lerp(face, BLACK, 0.12) if pressed else face, 3)
            if not pressed:
                rect(a, x + 4, y + 1, w - 8, 1, lerp(face, WHITE, 0.22))
        elif pressed:
            rfill(a, x + 1, y + 1, w - 2, h - 2, T["card_edge"], 3)
            rfill(a, x + 2, y + 2, w - 4, h - 4, T["btn_pr"], 2)
        else:
            card(a, x + 1, y + 1, w - 2, h - 2, face=T["btn"], r=3, shadow=True, top_hi=False)


def make_cbuttons(main):
    st = S()
    a = new(136, 36)
    specs = CB_SPECS + [("eject", 114, 22, 16, 136, 89)]
    for kind, x, w, h, dx, dy in specs:
        for pressed in (False, True):
            y = h if pressed else 0
            b = main[dy:dy + h, dx:dx + w].copy()
            o = 1 if pressed and st == "win8" else 0
            if st == "win8":
                button(b, 0, 0, w, h, pressed, face=T["tiles"][kind])
                ink = WHITE
            elif st == "win11" and kind == "play":
                # the accent-filled round play button
                d = 17
                cx0 = (w - d) // 2
                soft_shadow(b, cx0, 0, d, d, d / 2, opacity=0.25 if not pressed else 0.08)
                composite(b, cx0, 0, circle_alpha(d), lerp(T["accent"], BLACK, 0.18) if pressed else T["accent"])
                tri_right(b, w // 2 - 2, h // 2 - 5, 9, WHITE)
                a[y:y + h, x:x + w] = b
                continue
            else:
                button(b, 0, 0, w, h, pressed)
                ink = T["btn_ink_pr"] if pressed else T["btn_ink"]
            transport_glyph(b, kind, w // 2 + o, h // 2 - (1 if kind == "eject" else 0), ink)
            a[y:y + h, x:x + w] = b
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle(b, w, h, on, pressed, icon=None, label=None, tile=None):
    st = S()
    if st == "win8":
        face = tile if on else T["btn"]
        button(b, 0, 0, w, h, pressed, face=face)
        ink = WHITE if on else T["tog_ink"]
    elif st == "win10":
        button(b, 0, 0, w, h, pressed, face=T["tog_on"] if on else None)
        ink = T["tog_on_ink"] if on else T["tog_ink"]
    else:
        button(b, 0, 0, w, h, pressed, face=T["tog_on"] if on else None)
        ink = T["tog_on_ink"] if on else T["tog_ink"]
    o = 1 if (pressed and st == "win8") else 0
    if icon is not None:
        iw, ih = len(icon[0]), len(icon)
        bitmap(b, icon, (w - iw) // 2 + o * 0, (h - ih) // 2, ink)
    if label is not None:
        text_center(b, TINY, label, w // 2, (h - 5) // 2, ink)


def make_shufrep(main):
    a = new(92, 85)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        b = main[89:104, 210:238].copy()
        toggle(b, 28, 15, on, pressed, icon=REPEAT_ICON, tile=T["toggles"]["repeat"] if T["toggles"] else None)
        a[y:y + 15, 0:28] = b
        b = main[89:104, 164:211].copy()
        toggle(b, 47, 15, on, pressed, icon=SHUFFLE_ICON, tile=T["toggles"]["shuffle"] if T["toggles"] else None)
        a[y:y + 15, 28:75] = b
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        dx = 219 if label == "EQ" else 242
        for on, y in ((False, 61), (True, 73)):
            b = main[58:70, dx:dx + 23].copy()
            tile = T["toggles"][label.lower()] if T["toggles"] else None
            toggle(b, 23, 12, on, pressed, label=label, tile=tile)
            a[y:y + 12, x:x + 23] = b
    return a


# ------------------------------------------------------------------------------------------
# monoster, playpaus, text
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T["info"])
    for y, on in ((0, True), (12, False)):
        col = T["info_ink"] if on else T["info_dim"]
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T["disp"])
    ink = T["disp_ink"]
    tri_right(a, 2, 1, 7, ink)
    rect(a, 9 + 2, 1, 2, 7, ink)
    rect(a, 9 + 5, 1, 2, 7, ink)
    rect(a, 18 + 2, 2, 5, 5, ink)
    rect(a, 39 + 1, 3, 1, 3, ink)
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, T["info"])
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            g = FONT5[key]
            x0 = col * 5 + (1 if len(g[0]) <= 3 else 0) if len(g[0]) < 5 else col * 5
            draw_text(a, FONT5, key, x0, row * 6, T["info_ink"])
    return a


# ------------------------------------------------------------------------------------------
# Sliders: posbar.bmp, volume.bmp, balance.bmp
# ------------------------------------------------------------------------------------------


def track_h(a, x0, x1, cy, col, thick, ends=True):
    """Horizontal track from x0 to x1 (exclusive) centred on row cy; win11's has round ends
    (ends=False for a piece cut from the middle, as under a thumb)."""
    if x1 <= x0:
        return
    if S() == "win11" and not ends:
        rect(a, x0, cy - 1, x1 - x0, 3, col)
    elif S() == "win11":
        rfill(a, x0, cy - 1, x1 - x0, 3, col, 1.5)
    else:
        rect(a, x0, cy - thick // 2, x1 - x0, thick, col)


def track_v(a, cx, y0, y1, col, thick, ends=True):
    if y1 <= y0:
        return
    if S() == "win11" and not ends:
        rect(a, cx - 1, y0, 3, y1 - y0, col)
    elif S() == "win11":
        rfill(a, cx - 1, y0, 3, y1 - y0, col, 1.5)
    else:
        rect(a, cx - thick // 2, y0, thick, y1 - y0, col)


def thumb(a, x, y, w, h, pressed, horizontal=True):
    """The thumb, centred in the w x h box at x, y (the track already drawn under it)."""
    st = S()
    cx, cy = x + w // 2, y + h // 2
    if st == "win8":
        col = T["thumb_pr"] if pressed else T["thumb"]
        if horizontal:
            rect(a, cx - 2, y, 5, h, col)
        else:
            rect(a, x, cy - 2, w, 5, col)
    elif st == "win10":
        col = T["thumb_pr"] if pressed else T["thumb"]
        if horizontal:
            rect(a, cx - 2, y, 4 if w % 2 == 0 else 5, h, col)
        else:
            rect(a, x + 1, cy - 2, w - 2, 5, col)
    else:
        d = min(w, h) if min(w, h) % 2 == 1 else min(w, h) - 1
        ox, oy = cx - d // 2, cy - d // 2
        soft_shadow(a, ox, oy, d, d, d / 2, opacity=0.22, blur=0.9)
        composite(a, ox, oy, circle_alpha(d), T["card_edge"])
        composite(a, ox + 1, oy + 1, circle_alpha(d - 2), WHITE)
        dot = 5 if pressed else 3
        composite(a, cx - dot // 2, cy - dot // 2, circle_alpha(dot), T["accent"])


def make_posbar(main):
    a = new(307, 10)
    bg = main[72:82, 16:264].copy()
    a[0:10, 0:248] = bg
    cy = 5 if S() != "win8" else 5
    track_h(a, 2, 246, cy, T["track"], 1 if S() != "win8" else 2)
    row = main[72:82, 140:141].copy()
    for x0, sel in ((248, False), (278, True)):
        a[0:10, x0:x0 + 29] = np.repeat(row, 29, axis=1)
        track_h(a, x0, x0 + 29, cy, T["track"], 1 if S() != "win8" else 2, ends=False)
        if S() == "win11":
            thumb(a, x0, 0, 29, 10, sel)
        elif S() == "win8":
            rect(a, x0 + 10, 0, 9, 10, T["thumb_pr"] if sel else T["thumb"])
        else:
            rect(a, x0 + 12, 0, 5, 10, T["thumb_pr"] if sel else T["thumb"])
    return a


def slider_thumb_sheet(a, main, frame_y_row, fill_left):
    """The two 14x11 thumbs at y 422: bg = the slider row, track left filled (volume) or not."""
    for x0, sel in ((0, True), (15, False)):
        a[422:433, x0:x0 + 14] = np.repeat(a[1:12, 66:67], 14, axis=1)
        cy = 422 + 5
        if fill_left:
            track_h(a, x0 + 7, x0 + 14, cy, T["track"], 1, ends=False)
            track_h(a, x0, x0 + 7, cy, T["fill"], 3, ends=False)
        else:
            track_h(a, x0, x0 + 14, cy, T["track"], 1, ends=False)
        thumb(a, x0, 422, 14, 11, sel)


def make_volume(main):
    a = new(68, 433)
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        level = (i + 1) / 28
        fill_to = 7 + round(level * 54)
        cy = y + 6
        track_h(a, 2, 66, cy, T["track"], 1)
        track_h(a, 2, fill_to, cy, T["fill"], 3)
    a[420:433, :] = seat[0:13]
    slider_thumb_sheet(a, main, 57, True)
    return a


def make_balance(main):
    a = new(68, 433)
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        cy = y + 6
        track_h(a, 11, 45, cy, T["track"], 1)
        rect(a, 28, cy - 3, 1, 2, T["label"])
        rect(a, 28, cy + 2, 1, 2, T["label"])
    a[420:433, 0:68] = np.repeat(seat[0:13, 0:1], 68, axis=1)
    a[0:420, 0:9] = np.repeat(a[0:420, 9:10], 9, axis=1)
    a[0:420, 47:68] = np.repeat(a[0:420, 46:47], 21, axis=1)
    slider_thumb_sheet(a, main, 57, False)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = bar_base(275, 14)
    edges(a)
    title_text(a, T["titles"]["eq"], 137, 2, lit, center=True)
    cap_button(a, 264, 3, "close", lit)
    return a


def eq_slider_bg():
    return T["card"] if S() == "win11" else (T["body"] if S() == "win8" else T["body"])


def eq_slider_frame(a, x, y, n):
    """14x63 frame: a vertical track, filled from the bottom up to the value (n of 0..27)."""
    rect(a, x, y, 14, 63, eq_slider_bg())
    v = n / 27
    centre = round((1 - v) * 51) + 5
    cx = x + 6
    track_v(a, cx, y + 2, y + 61, T["track"], 1)
    track_v(a, cx, y + centre, y + 61, T["fill"], 3)
    # the zero mark
    rect(a, x + 1, y + 30, 2, 1, T["label_dim"])
    rect(a, x + 11, y + 30, 2, 1, T["label_dim"])


def eq_thumb(a, x, y, pressed):
    rect(a, x, y, 11, 11, eq_slider_bg())
    track_v(a, x + 5, y, y + 5, T["track"], 1, ends=False)
    track_v(a, x + 5, y + 5, y + 11, T["fill"], 3, ends=False)
    thumb(a, x, y, 11, 11, pressed, horizontal=False)


def make_eqmain():
    st = S()
    a = new(275, 315)
    body_fill(a, 0, 0, 275, 116, seed=23)
    edges(a[0:116])
    if T["border"] is not None:
        rect(a, 0, 115, 275, 1, T["border"])
    a[0:14, :] = eq_titlebar(True)
    rect(a, 0, 116, 275, 199, T["body"])
    # the graph panel
    if st == "win8":
        rect(a, 84, 15, 117, 23, T["disp"])
    else:
        panel(a, 86, 17, 113, 19, T["disp"])
    # the slider bay
    if st == "win11":
        card(a, 15, 37, 247, 74, r=4)
    elif st == "win10":
        rect(a, 16, 37, 245, 66, T["body"])
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 57, yy, T["label"])
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    lab = T["label"]
    text_center(a, TINY, "PRE", 28, 104, lab)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 104, lab)

    # under the window: buttons
    b = a[3:12, 264:273].copy()
    cap_button(b, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = b
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        dx = 14 if label == "ON" else 40
        b = a[18:30, dx:dx + w].copy()
        tile = T["toggles"][label.lower()] if T["toggles"] else None
        toggle(b, w, 12, on, pressed, label=label, tile=tile)
        a[119:131, x:x + w] = b
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    eq_thumb(a, 0, 164, False)
    eq_thumb(a, 0, 176, True)
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        b = a[18:30, 217:261].copy()
        toggle(b, 44, 12, False, pressed, label="PRESETS", tile=None)
        a[y:y + 12, 224:268] = b
    # graph
    rect(a, 0, 294, 113, 19, T["disp"])
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, T["disp_dim"])
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, T["disp_dim"])
    for r in range(19):
        px(a, 115, 294 + r, ramp(T["graph"], r / 18))
    for x in range(113):
        px(a, x, 314, lerp(T["disp"], T["disp_ink"], 0.45) if x % 3 != 2 else T["disp"])
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------


def bar20(w, top=True):
    a = new(w, 20, T["bar"])
    if top and T["border"] is not None:
        rect(a, 0, 0, w, 1, T["border"])
    return a


def readout(a, x, y, w, h):
    """A small panel in the text.bmp colours for the playlist's readouts."""
    if S() == "win11":
        card(a, x - 1, y - 1, w + 2, h + 2, face=T["info"], r=2, shadow=False)
    elif S() == "win10":
        rect(a, x, y, w, h, T["info"])
        outline(a, x - 1, y - 1, w + 2, h + 2, H("333333"))
    else:
        rect(a, x - 1, y - 1, w + 2, h + 2, T["info"])


def make_pledit():
    st = S()
    a = new(280, 186)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25)
        a[y:y + 20, 127:152] = t
        t = bar20(25)
        edges(t, right=False)
        a[y:y + 20, 0:25] = t
        t = bar20(100)
        title_text(t, T["titles"]["pl"], 50, 5, lit, center=True)
        a[y:y + 20, 26:126] = t
        t = bar20(25)
        edges(t, left=False)
        cap_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t
    if st != "win8":
        for y in (19, 40):
            # the list's top hairline (win10: grey, win11: the card edge)
            line = H("333333") if st == "win10" else T["card_edge"]
            for x0, x1 in ((127, 152), (0, 25), (26, 126), (153, 178)):
                rect(a, x0, y, x1 - x0, 1, line)
            rect(a, 0, y, 11, 1, T["bar"])
            rect(a, 0, y, 1, 1, T["border"])
            rect(a, 153 + 6, y, 19, 1, T["bar"])
            rect(a, 177, y, 1, 1, T["border"])
    # left side tile
    t = new(12, 29)
    edges(t, right=False)
    if st != "win8":
        rect(t, 11, 0, 1, 29, H("333333") if st == "win10" else T["card_edge"])
    a[42:71, 0:12] = t
    # right side tile: list edge, the scrollbar groove (cols 5..12), outer edge
    t = new(20, 29)
    edges(t, left=False)
    if st == "win8":
        rect(t, 5, 0, 8, 29, T["info"])
    elif st == "win10":
        rect(t, 0, 0, 1, 29, H("333333"))
        rect(t, 5, 0, 8, 29, H("171717"))
    else:
        rect(t, 0, 0, 1, 29, T["card_edge"])
    a[42:71, 31:51] = t
    # close pressed, scroll handles
    b = a[3:12, 153 + 14:153 + 23].copy()
    cap_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = b
    for x, sel in ((52, False), (61, True)):
        groove = a[42 + 5:42 + 23, 31 + 5:31 + 13].copy()
        a[53:71, x:x + 8] = groove
        if st == "win8":
            rect(a, x + 1, 53, 6, 18, WHITE if sel else H("a58ae0"))
        elif st == "win10":
            rect(a, x + 2, 53, 4, 18, H("a6a6a6") if sel else H("5d5d5d"))
        else:
            rfill(a, x + 2, 54, 4 if sel else 3, 16, H("5d5f63") if sel else H("8a8d93"), 1.5)

    def bottom_base(w, left=False, right=False):
        t = new(w, 38)
        body_fill(t, 0, 0, w, 38, seed=31)
        if st != "win8":
            rect(t, 0, 0, w, 1, H("333333") if st == "win10" else T["card_edge"])
        if T["border"] is not None:
            rect(t, 0, 37, w, 1, T["border"])
        edges(t, left=left, right=right)
        return t

    def pl_button(t, bx, by, w, h, label):
        button(t, bx, by, w, h, False, face=T["toggles"]["pl"] if False else None)
        text_center(t, TINY, label, bx + w // 2, by + (h - 5) // 2, T["btn_ink"] if st != "win8" else WHITE)

    t = bottom_base(125, left=True)
    rect(t, 0, 0, 12, 1, T["body"]) if st == "win8" else None
    if st != "win8":
        rect(t, 1, 0, 11, 1, t[5, 5])
        rect(t, 11, 0, 1, 1, H("333333") if st == "win10" else T["card_edge"])
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        pl_button(t, bx, 8, 22, 18, lbl)
    a[72:110, 0:125] = t

    t = bottom_base(150, right=True)
    if st != "win8":
        rect(t, 130, 0, 19, 1, t[5, 140])
        rect(t, 130, 0, 1, 1, H("333333") if st == "win10" else T["card_edge"])
    readout(t, 6, 9, 56, 8)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        mini_glyph(t, kind, bx + 5, 22 + 5, T["label"] if st != "win8" else WHITE)
    readout(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, T["info_dim"])
    rect(t, 84, 22 + 5, 1, 1, T["info_dim"])
    pl_button(t, 106, 8, 22, 18, "LIST")
    grip = T["label_dim"]
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 30 - 3 * j
            rect(t, gx, gy, 1 if st != "win8" else 2, 1 if st != "win8" else 2, grip)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_gen():
    st = S()
    a = new(194, 109)
    for lit, y in ((True, 0), (False, 21)):
        for px0 in (0, 26, 52, 78, 104, 130):
            t = bar20(25)
            if px0 == 0:
                edges(t, right=False)
            if px0 == 130:
                edges(t, left=False)
                cap_button(t, 14, 3, "close", lit)
            a[y:y + 20, px0:px0 + 25] = t

    def bottom(w, grip, left_edge):
        t = new(w, 14)
        body_fill(t, 0, 0, w, 14, seed=41)
        if T["border"] is not None:
            rect(t, 0, 13, w, 1, T["border"])
        if left_edge:
            edges(t, right=False)
        else:
            edges(t, left=False)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 5 - 3 * k + 3 * j, 9 - 3 * j
                    px(t, gx, gy, T["label_dim"])
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    t = bottom(25, False, True)
    if T["border"] is not None:
        t[:, 0] = t[:, 1]
    a[72:86, 127:152] = t
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        edges(t, left=outer_left, right=not outer_left)
        a[42:42 + h, x:x + w] = t
    b = a[3:12, 130 + 14:130 + 23].copy()
    cap_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = b

    # letters: each row starts at x 1, letters in their own cells, 1px separators of x 0's colour
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(UI, c) + 1
            rect(a, x, y, w, 7, T["bar"])
            draw_text(a, UI, c, x, y, T["title_ink"] if lit else T["title_dim"])
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp and the text files
# ------------------------------------------------------------------------------------------


def genex_colours():
    st = S()
    if st == "win8":
        purple, deep = T["body"], T["info"]
        return [deep, WHITE, purple, WHITE, WHITE, H("6a45c4"), METRO["magenta"], purple, WHITE,
                H("7d5bd6"), H("1d0758"), METRO["magenta"], purple, H("3a1294"), H("a58ae0"),
                H("3a1294"), WHITE, deep]
    if st == "win10":
        return [H("000000"), WHITE, H("1f1f1f"), WHITE, WHITE, H("333333"), H("003e6b"), H("1f1f1f"),
                H("a0a0a0"), H("333333"), H("000000"), H("0078d7"), H("1f1f1f"), H("171717"), H("5d5d5d"),
                H("171717"), H("a6a6a6"), H("171717")]
    return [WHITE, H("1a1a1a"), H("f1f3f8"), H("1a1a1a"), H("1a1a1a"), H("e3e5ea"), H("cce4f7"), H("f9f9fb"),
            H("5d5f63"), H("ffffff"), H("d0d3d9"), H("cce4f7"), H("f1f3f8"), H("f1f3f8"), H("8a8d93"),
            H("f1f3f8"), H("5d5f63"), H("f1f3f8")]


def make_genex():
    a = new(256, 64)
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    b = new(47, 15)
    button(b, 0, 0, 47, 15, False)
    a[1:16, 0:47] = b
    b = new(47, 15)
    button(b, 0, 0, 47, 15, True)
    a[16:31, 0:47] = b
    return a


def viscolor():
    spec = [ramp(T["vis"], i / 15) for i in range(16)]
    osc = [lerp(T["osc"], T["vis_bg"], k * 0.15) for k in range(5)]
    return ([(T["vis_bg"], "background"), (T["vis_dots"], "dots")]
            + [(c, f"spectrum {i + 1}" + (" (top)" if i == 0 else "")) for i, c in enumerate(spec)]
            + [(c, f"oscilloscope {k + 1}") for k, c in enumerate(osc)]
            + [(T["peak"], "peaks")])


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={hexc(T['list_ink'])}\nCurrent={hexc(T['list_cur'])}\n"
                f"NormalBG={hexc(T['list_bg'])}\nSelectedBG={hexc(T['list_sel'])}\n"
                f"MbBG={hexc(T['list_bg'])}\nMbFG={hexc(T['list_ink'])}\nFont=Arial\n")
    v = T["ver"]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(f"Windows {v} \u2014 a skin in the style of Windows {v}, drawn from scratch (apart from\n"
                f"the small Windows logo). Not affiliated with Microsoft.\n\n"
                "A classic (Winamp 2.x format) skin. Every bitmap was drawn by a script (gen_skin.py)\n"
                "from rectangles, rounded rectangles and hand-made pixel fonts and icons; the one\n"
                "exception is the Windows logo in the bottom-right corner. No wallpapers or screenshots.\n\n"
                "Windows logo \u00a9 Microsoft; private use only.\n")


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
    with zipfile.ZipFile(os.path.join(HERE, T["wsz"]), "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(OUT, n), "rb") as fh:
                z.writestr(info, fh.read())
    return names


# ------------------------------------------------------------------------------------------
# Preview: the windows put together from the sprites the way the app does (as in Ember)
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
    Sh = SHEETS
    img = Image.new("RGB", (275, 116))
    img.paste(Sh["main"], (0, 0))
    blit(img, Sh["titlebar"], (27, 0 if lit else 15, 275, 14), 0, 0)
    for b, sx, sy, dx in (("options", 0, 0, 6), ("minimize", 9, 0, 244), ("close", 18, 0, 264)):
        blit(img, Sh["titlebar"], (sx, 9 if state["pressed"] == b else 0, 9, 9), dx, 3)
    blit(img, Sh["titlebar"], (9 if state["pressed"] == "shade" else 0, 18, 9, 9), 254, 3)
    for k, x, w, h, dx, dy in CB_SPECS:
        blit(img, Sh["cbuttons"], (x, 18 if state["pressed"] == k else 0, w, h), dx, dy)
    blit(img, Sh["cbuttons"], (114, 16 if state["pressed"] == "eject" else 0, 22, 16), 136, 89)
    for name, x0, on in (("eq", 0, state["eq"]), ("pl", 23, state["pl"])):
        pressed = state["pressed"] == name
        sx = x0 + (46 if pressed else 0)
        blit(img, Sh["shufrep"], (sx, 73 if on else 61, 23, 12), 219 + x0, 58)
    blit(img, Sh["titlebar"], (304, 0, 8, 43), 10, 22)
    spr = {"O": (304, 47, 8, 8, 3), "A": (312, 55, 8, 7, 11), "I": (320, 62, 8, 7, 18), "D": (328, 69, 8, 8, 25),
           "V": (336, 77, 8, 7, 33)}
    for L in state["clutter"]:
        x, y, w, h, oy = spr[L]
        blit(img, Sh["titlebar"], (x, y, w, h), 10, 22 + oy)
    for name, x0, w, on, dst in (("shuffle", 28, 47, state["shuffle"], 164), ("repeat", 0, 28, state["repeat"], 210)):
        row = (2 if on else 0) + (1 if state["pressed"] == name else 0)
        blit(img, Sh["shufrep"], (x0, row * 15, w, 15), dst, 89)
    blit(img, Sh["playpaus"], (0 if state["playing"] else 9, 0, 9, 9), 26, 28)
    blit(img, Sh["playpaus"], (39, 0, 3, 9), 24, 28)
    blit(img, Sh["monoster"], (29, 12 if state["stereo"] else 0, 27, 12), 212, 41)
    blit(img, Sh["monoster"], (0, 0 if state["stereo"] else 12, 29, 12), 239, 41)
    blit(img, Sh["posbar"], (0, 0, 248, 10), 16, 72)
    tl = round(state["pos"] * 219)
    blit(img, Sh["posbar"], (278 if state["seek"] else 248, 0, 29, 10), 16 + tl, 72)
    v = state["volume"]
    idx = max(0, round(v / 100 * 28) - 1)
    blit(img, Sh["volume"], (0, idx * 15, 68, 13), 107, 57)
    blit(img, Sh["volume"], (0 if state["vdrag"] else 15, 422, 14, 11), 107 + round(v / 100 * 54), 58)
    b = state["balance"]
    idx = int(abs(b) / 100 * 27)
    blit(img, Sh["balance"], (9, idx * 15, 38, 13), 177, 57)
    blit(img, Sh["balance"], (15, 422, 14, 11), 177 + round((b + 100) / 200 * 24), 58)
    secs = state["time"]
    m, s = secs // 60, secs % 60
    nums = Sh["nums_ex"]
    if state["remaining"]:
        blit(img, nums, (99, 0, 9, 13), 38, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, Sh["text"], (150, 0, w, 6), 111 + x, 24)
    draw_bitmap_text(img, state["title"][:30], 111, 24)
    draw_bitmap_text(img, "320", 111, 43)
    draw_bitmap_text(img, "44", 156, 43)
    cols = [c for c, _ in viscolor()]
    vis = Image.new("RGB", (76, 16))
    vp = vis.load()
    for y in range(16):
        for x in range(76):
            vp[x, y] = cols[1] if (y % 2 == 1 and x % 2 == 0) else cols[0]
    for x in range(75):
        if x % 4 == 3:
            continue
        hgt = state["bars"][x // 4] - 2
        for y in range(16 - hgt, 16):
            vp[x, y] = cols[min(17, max(2, y + 2))]
        pk = state["bars"][x // 4] + 2
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=T["list_bg"])
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 9)
    except OSError:
        font = ImageFont.load_default()
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=T["list_sel"])
        col = T["list_cur"] if i == 1 else T["list_ink"]
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
    # a stand-in picture: a plain gradient in the accent
    pic = Image.linear_gradient("L").resize((w - 22, h - 34))
    arr = np.asarray(pic).astype(np.float32)[..., None] / 255
    c0, c1 = np.array(lerp(T["accent"], WHITE, 0.55), np.float32), np.array(lerp(T["accent"], BLACK, 0.35), np.float32)
    col = c0 * (1 - arr) + c1 * arr
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("Tile Grid - Live Updates", "4:12"), ("Start Screen - Semantic Zoom", "3:47"),
            ("Charms Bar - Swipe In", "5:03"), ("Snap View - Side by Side", "2:58"),
            ("Accent Colour - Cobalt", "6:21"), ("Flat Design - No Chrome", "3:33"),
            ("Action Center - Quiet Hours", "4:40"), ("Mica - Soft Light", "3:09"),
            ("Rounded Corners - Four Pixels", "5:51"), ("Fluent - Reveal", "4:05"),
            ("Dark Mode - Night Light", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=f"WINDOWS {T['ver']} - A STYLE HOMAGE  ***", bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="PAUSED: QUIET HOURS (LIVE)", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
    out.save(os.path.join(HERE, T["preview"]))


def run(key):
    global T, OUT
    T = make_theme(key)
    OUT = os.path.join(HERE, "out", key)
    os.makedirs(OUT, exist_ok=True)
    names = build()
    preview()
    for n in names:
        if n.endswith(".bmp"):
            im = Image.open(os.path.join(OUT, n))
            assert im.mode == "RGB", (n, im.mode)
    print(f"{key:6s} -> {T['wsz']}, {T['preview']}")


if __name__ == "__main__":
    keys = [a.lower() for a in sys.argv[1:]]
    for k in keys:
        if k not in THEME_KEYS:
            sys.exit(f"unknown theme {k!r}; themes: {', '.join(THEME_KEYS)}")
    for k in keys or THEME_KEYS:
        run(k)
