#!/usr/bin/python3
"""iPod: classic Winamp 2.x skins in the style of the iPod classic (6th/7th gen) and iPod mini.

One procedural generator, several themes. Every bitmap is drawn here from code (shapes,
gradients, brushing noise, hand-made pixel fonts), apart from the Apple logo in the About spot,
which is rasterised from source/logo-apple/apple-logo.svg (Wikimedia Commons) at build time.

    /usr/bin/python3 -I gen_skin.py                  # every theme
    /usr/bin/python3 -I gen_skin.py classic-black    # one or more themes
    /usr/bin/python3 -I gen_skin.py --list

Each theme writes its sheets into out/<theme>/, zips them flat into <name>.wsz beside this
script, and draws preview-<theme>.png (the windows assembled from the sprites at their real
positions, as the app does, 2x).
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
OUT_ROOT = os.path.join(HERE, "out")
SCRATCH = os.path.join(OUT_ROOT, "scratch")
LOGO_SVG = os.path.join(HERE, "source", "logo-apple", "apple-logo.svg")
SEP = (255, 0, 255)  # gen.bmp letter separators (never shown)


# ------------------------------------------------------------------------------------------
# Colour helpers
# ------------------------------------------------------------------------------------------


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def tint(c, t):
    return lerp(c, (255, 255, 255), t)


def shade(c, t):
    return lerp(c, (0, 0, 0), t)


def desat(c, k):
    g = luma(c)
    return lerp(c, (g, g, g), k)


def saturate(c, k):
    g = luma(c)
    return tuple(int(round(max(0, min(255, g + (v - g) * (1 + k))))) for v in c)


def hexc(c):
    return "#%02X%02X%02X" % tuple(c)


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

# iPod mini body tones. Pink, blue and green are the 2nd generation's (more vivid than the 1st's);
# silver was unchanged; gold was 1st generation only (champagne).
MINI = {
    "silver": (198, 201, 205),
    "gold": (212, 190, 140),
    "pink": (234, 132, 178),
    "blue": (84, 152, 216),
    "green": (138, 196, 78),
}

# The -metal set: the same colours, a touch deeper so the sheen has room above them; silver
# lifted toward a cool metallic grey, gold kept champagne.
MINI_METAL = {
    "silver": (184, 190, 198),
    "gold": (204, 182, 134),
    "pink": (228, 120, 168),
    "blue": (74, 140, 206),
    "green": (126, 186, 68),
}

CLASSIC_SCREEN = dict(
    scr=(252, 252, 252), ink=(14, 14, 16), dim=(112, 114, 120), faint=(226, 229, 234),
    strip_top=(253, 253, 254), strip_bot=(203, 207, 214), strip_line=(140, 145, 152), strip_ink=(18, 18, 20),
    acc_top=(132, 186, 248), acc_bot=(26, 96, 212), acc_ink=(255, 255, 255), batt=(96, 196, 72),
    pl_normal=(14, 14, 16), pl_current=(24, 92, 206), pl_sel=(0xB9, 0xD4, 0xF5),
    vis_spec=[(150, 200, 252), (96, 162, 240), (52, 122, 224), (26, 92, 204), (18, 64, 160)],
    vis_osc=[(20, 70, 180), (40, 100, 210), (70, 130, 226), (110, 160, 236), (150, 190, 244)],
    vis_peak=(10, 40, 120),
)


def make_theme(key):
    if key.startswith("classic-"):
        black = key == "classic-black"
        t = dict(CLASSIC_SCREEN)
        if black:
            t.update(
                body=(44, 45, 49), body_hi=(84, 85, 91), body_lo=(14, 14, 16), amp=1.6,
                bezel=(8, 8, 9),
                wheel=(28, 28, 30), wheel_hi=(58, 58, 62), wheel_lo=(6, 6, 7), glyph=(156, 156, 162),
                key_ink=(176, 176, 182),
                centre=(54, 55, 60), centre_ring=(16, 16, 18),
                label=(176, 177, 182), label_dim=(118, 119, 124), mark=(104, 168, 255),
                word_lit=(198, 199, 204), word_shadow=(12, 12, 14), word_unlit=(112, 113, 118),
                logo=((206, 208, 212), (128, 130, 136)),
            )
        else:
            t.update(
                body=(204, 206, 210), body_hi=(240, 241, 243), body_lo=(140, 142, 147), amp=3.2,
                bezel=(26, 26, 28),
                wheel=(246, 246, 246), wheel_hi=(255, 255, 255), wheel_lo=(196, 197, 200), glyph=(132, 134, 140),
                key_ink=(104, 106, 112),
                centre=(212, 214, 218), centre_ring=(168, 170, 175),
                label=(78, 80, 86), label_dim=(130, 132, 137), mark=(30, 100, 214),
                word_lit=(84, 86, 92), word_shadow=(242, 243, 245), word_unlit=(150, 152, 157),
                logo=((150, 152, 158), (84, 86, 92)),
            )
        name = "Black" if black else "Silver"
        t.update(key=key, model="classic", name=name, wsz=f"iPod-classic-{name}.wsz",
                 preview=f"preview-{key}.png", wordmark="iPod classic")
        return t
    metal = key.endswith("-metal")
    colour = key.split("-")[1]
    c = MINI_METAL[colour] if metal else MINI[colour]
    glyph = (138, 140, 145) if colour == "silver" else shade(c, 0.22)
    t = dict(
        body=c, body_hi=tint(c, 0.5), body_lo=shade(c, 0.38), amp=2.0,
        bezel=(66, 70, 74),
        # the mini's monochrome LCD: pale grey-blue, dark grey pixels
        scr=(178, 191, 196), ink=(44, 50, 54), dim=(96, 106, 112), faint=(162, 175, 181),
        strip_top=(178, 191, 196), strip_bot=(178, 191, 196), strip_line=(70, 78, 84), strip_ink=(44, 50, 54),
        acc_top=(76, 84, 90), acc_bot=(40, 46, 50), acc_ink=(186, 198, 203), batt=(44, 50, 54),
        wheel=(224, 224, 222), wheel_hi=(242, 242, 240), wheel_lo=(178, 178, 178), glyph=glyph,
        key_ink=(108, 110, 116) if colour == "silver" else shade(c, 0.36),
        centre=(230, 230, 228), centre_ring=(176, 176, 176),
        label=shade(c, 0.62), label_dim=shade(c, 0.32), mark=shade(c, 0.72),
        word_lit=shade(c, 0.5), word_shadow=tint(c, 0.45), word_unlit=shade(c, 0.2),
        logo=(shade(c, 0.25), shade(c, 0.55)),
        pl_normal=(44, 50, 54), pl_current=(8, 10, 12), pl_sel=(140, 156, 163),
        vis_spec=[(120, 132, 138), (98, 109, 115), (78, 87, 93), (60, 67, 72), (44, 50, 54)],
        vis_osc=[(44, 50, 54), (60, 67, 72), (78, 87, 93), (98, 109, 115), (120, 132, 138)],
        vis_peak=(30, 34, 38),
    )
    name = colour.capitalize()
    t.update(key=key, model="mini", name=name, wsz=f"iPod-mini-{name}{'-Metal' if metal else ''}.wsz",
             preview=f"preview-{key}.png", wordmark="iPod mini", metal=metal)
    if metal:
        # machined edges: a crisp near-white chamfer, a deep shadow edge
        t.update(body_hi=tint(desat(c, 0.55), 0.72), body_lo=shade(saturate(c, 0.2), 0.5),
                 metal_hi=tint(desat(c, 0.5), 0.55), metal_lo=shade(saturate(c, 0.25), 0.36),
                 logo=(tint(desat(c, 0.6), 0.75), tint(desat(c, 0.4), 0.25)))
    return t


THEME_KEYS = (["classic-silver", "classic-black"] + [f"mini-{k}" for k in MINI]
              + [f"mini-{k}-metal" for k in MINI])
T = None
OUT = None
_rng = None

# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def new(w, h, col=None):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = T["body"] if col is None else col
    return a


def rect(a, x, y, w, h, col):
    assert x >= 0 and y >= 0 and x + w <= a.shape[1] and y + h <= a.shape[0], (x, y, w, h, a.shape)
    if w > 0 and h > 0:
        a[y:y + h, x:x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def brushed(a, x, y, w, h, amp):
    """Fine brushed-aluminium grain: horizontally smeared noise (wraps, so tiles stay seamless)."""
    n = _rng.normal(0, 1, (h, w))
    acc = np.zeros_like(n)
    for d in range(-6, 7):
        acc += np.roll(n, d, axis=1)
    acc /= 3.6
    acc += _rng.normal(0, 0.3, (h, w))
    a[y:y + h, x:x + w] += np.round(acc * amp).astype(np.int32)[:, :, None]


def body(a, x, y, w, h, prof=None, ox=0, oy=0):
    """Fills a body surface. prof names the sheen profile (metal themes only) and (ox, oy) is
    where the array's (0, 0) sits in its window, so pieces drawn apart share one sheen."""
    if T.get("metal"):
        metal(a, x, y, w, h, prof, ox, oy)
        return
    rect(a, x, y, w, h, T["body"])
    brushed(a, x, y, w, h, T["amp"])


def _circ_blur_x(n, k):
    """Box blur of length k along x, circular (so a tile's left and right edges still meet)."""
    f = np.zeros(n.shape[1])
    f[:k] = 1.0 / k
    f = np.roll(f, -(k // 2))
    return np.real(np.fft.ifft(np.fft.fft(n, axis=1) * np.fft.fft(f)[None, :], axis=1))


def sheen(prof, WX, WY):
    """-1 (shadow) .. 0 (base) .. 1 (specular) across a window's body. Tiled pieces only vary
    along the axis they don't tile on: top and bottom bars by y, side tiles not at all."""
    if prof == "win":  # main and EQ windows, 275 x 116: a broad, slightly tilted highlight band
        band = np.exp(-((WY - 34 - 0.10 * (WX - 137)) / 26.0) ** 2)
        fall = np.clip(WY / 116.0, 0, 1) ** 1.7
        sides = ((WX - 137) / 137.0) ** 4
        return 0.95 * band - 0.6 * fall - 0.3 * sides + 0.05
    if prof == "top":  # 20px titlebars of the playlist and gen windows
        return 0.85 * np.exp(-((WY - 7) / 7.0) ** 2) - 0.12 + 0 * WX
    if prof == "bottom38":
        return -0.12 - 0.6 * np.clip(WY / 37.0, 0, 1) ** 1.6 + 0 * WX
    if prof == "bottom14":
        return -0.12 - 0.5 * np.clip(WY / 13.0, 0, 1) ** 1.6 + 0 * WX
    return np.full(WX.shape, -0.12)  # side tiles, spare sheet areas


def metal(a, x, y, w, h, prof, ox, oy):
    """Anodised, brushed aluminium: a sheen (desaturated toward white in the highlight, deeper
    in the shadow) under dense horizontal streaks of varying length and strength."""
    c = np.array(T["body"], dtype=np.float64)
    hi = np.array(T["metal_hi"], dtype=np.float64)
    lo = np.array(T["metal_lo"], dtype=np.float64)
    WX, WY = np.meshgrid(np.arange(w) + x + ox, np.arange(h) + y + oy)
    t = sheen(prof, WX.astype(np.float64), WY.astype(np.float64))
    # gentle tonal drift so no stretch reads as a flat fill (varies along y only: tiles stay whole)
    t = t + 0.06 * np.sin(WY / 5.3 + 1.7) * np.sin(WY / 13.1)
    tp, tn = np.clip(t, 0, 1)[..., None], np.clip(-t, 0, 1)[..., None]
    col = c + (hi - c) * tp + (lo - c) * tn
    # the brushing: streaks of several lengths, each row its own strength, plus a few long glints
    s = np.zeros((h, w))
    for k, wt in ((3, 0.6), (9, 1.0), (27, 1.0), (61, 0.65)):
        n = _rng.normal(0, 1, (h, w))
        s += wt * _circ_blur_x(n, min(k, w)) * np.sqrt(min(k, w))
    s *= _rng.uniform(0.55, 1.35, (h, 1))
    glint = np.zeros((h, w))
    for _ in range(max(1, (w * h) // 260)):
        gy, gx = _rng.integers(0, h), _rng.integers(0, w)
        ln = int(_rng.integers(6, 48))
        cols = (gx + np.arange(ln)) % w
        glint[gy, cols] += _rng.choice([-1.0, 1.0]) * _rng.uniform(0.4, 1.1) * np.hanning(ln + 2)[1:-1]
    s = s / 2.6 + glint
    lum = (0.299 * col[..., 0] + 0.587 * col[..., 1] + 0.114 * col[..., 2])[..., None]
    amp = 3.4 + 2.2 * (lum / 255.0)  # brighter metal shows its brushing more
    col = col + s[..., None] * amp
    a[y:y + h, x:x + w] = np.round(np.clip(col, 0, 255)).astype(np.int32)


def raised(a, x, y, w, h):
    rect(a, x, y, w, 1, T["body_hi"])
    rect(a, x, y, 1, h, T["body_hi"])
    rect(a, x, y + h - 1, w, 1, T["body_lo"])
    rect(a, x + w - 1, y, 1, h, T["body_lo"])


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


# --- antialiased shapes (supersampled alpha masks) ---------------------------------------


def _grid(w, h, ss):
    xs = (np.arange(w * ss) + 0.5) / ss
    ys = (np.arange(h * ss) + 0.5) / ss
    return np.meshgrid(xs, ys)


def rr_alpha(w, h, r, inset=0.0, ss=4):
    """Rounded rectangle w x h with corner radius r (r = h/2 gives a capsule), shrunk by inset."""
    X, Y = _grid(w, h, ss)
    x0, y0, x1, y1 = inset, inset, w - inset, h - inset
    rr = max(0.0, min(r - inset, (x1 - x0) / 2, (y1 - y0) / 2))
    dx = np.maximum(np.maximum(x0 + rr - X, X - (x1 - rr)), 0)
    dy = np.maximum(np.maximum(y0 + rr - Y, Y - (y1 - rr)), 0)
    inside = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1) & (dx * dx + dy * dy <= rr * rr + 1e-9)
    return inside.reshape(h, ss, w, ss).mean(axis=(1, 3))


def disc_alpha(w, h, cx, cy, rad, ss=4):
    X, Y = _grid(w, h, ss)
    inside = (X - cx) ** 2 + (Y - cy) ** 2 <= rad * rad
    return inside.reshape(h, ss, w, ss).mean(axis=(1, 3))


def composite(a, x, y, al, col):
    h, w = al.shape
    reg = a[y:y + h, x:x + w].astype(np.float64)
    c = np.asarray(col, dtype=np.float64)
    if c.ndim == 1:
        c = c[None, None, :]
    elif c.ndim == 2:          # one colour per row
        c = c[:, None, :]
    out = reg * (1 - al[..., None]) + c * al[..., None]
    a[y:y + h, x:x + w] = np.round(out).astype(np.int32)


def vgrad(h, stops):
    return np.array([ramp(stops, r / max(1, h - 1)) for r in range(h)], dtype=np.float64)


def shape(a, x, y, w, h, r, stops, edge):
    """A filled rounded shape: a 1px ring of the edge colour round a gradient face."""
    composite(a, x, y, rr_alpha(w, h, r), edge)
    composite(a, x, y, rr_alpha(w, h, r, 1.0), vgrad(h, stops))


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
    "0": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "1": G(".#.", "##.", ".#.", ".#.", "###"),
    "2": G("##.", "..#", ".#.", "#..", "###"),
    "3": G("##.", "..#", ".#.", "..#", "##."),
    "4": G("#.#", "#.#", "###", "..#", "..#"),
    "5": G("###", "#..", "##.", "..#", "##."),
    "6": G(".##", "#..", "##.", "#.#", ".#."),
    "7": G("###", "..#", ".#.", ".#.", ".#."),
    "8": G(".#.", "#.#", ".#.", "#.#", ".#."),
    "9": G(".#.", "#.#", ".##", "..#", "##."),
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
for _c in "0123456789+-.":
    TINY[_c] = FONT5[_c]

# 7-row wordmark letters ("iPod classic", "iPod mini"), x-height 5.
WORD = {
    "i": G("#", ".", "#", "#", "#", "#", "#"),
    "P": G("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "o": G("....", "....", ".##.", "#..#", "#..#", "#..#", ".##."),
    "d": G("...#", "...#", ".###", "#..#", "#..#", "#..#", ".###"),
    "c": G("...", "...", ".##", "#..", "#..", "#..", ".##"),
    "l": G("#", "#", "#", "#", "#", "#", "#"),
    "a": G("....", "....", ".##.", "...#", ".###", "#..#", ".###"),
    "s": G("...", "...", ".##", "#..", ".#.", "..#", "##."),
    "m": G(".....", ".....", "####.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": G("....", "....", "###.", "#..#", "#..#", "#..#", "#..#"),
    " ": G("..", "..", "..", "..", "..", "..", ".."),
}

# Time digits: a bold sans, 7x11, drawn in 9x13 cells.
DIGITS = {
    0: G(".#####.", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##",
         "##...##", ".#####."),
    1: G("...##..", "..###..", ".####..", "...##..", "...##..", "...##..", "...##..", "...##..", "...##..",
         "...##..", "...##.."),
    2: G(".#####.", "##...##", ".....##", ".....##", "....##.", "...##..", "..##...", ".##....", "##.....",
         "##.....", "#######"),
    3: G(".#####.", "##...##", ".....##", ".....##", "..####.", ".....##", ".....##", ".....##", ".....##",
         "##...##", ".#####."),
    4: G("....##.", "...###.", "..####.", ".##.##.", "##..##.", "##..##.", "#######", "....##.", "....##.",
         "....##.", "....##."),
    5: G("#######", "##.....", "##.....", "######.", ".....##", ".....##", ".....##", ".....##", ".....##",
         "##...##", ".#####."),
    6: G(".#####.", "##...##", "##.....", "##.....", "######.", "##...##", "##...##", "##...##", "##...##",
         "##...##", ".#####."),
    7: G("#######", ".....##", ".....##", "....##.", "....##.", "...##..", "...##..", "..##...", "..##...",
         "..##...", "..##..."),
    8: G(".#####.", "##...##", "##...##", "##...##", ".#####.", "##...##", "##...##", "##...##", "##...##",
         "##...##", ".#####."),
    9: G(".#####.", "##...##", "##...##", "##...##", "##...##", ".######", ".....##", ".....##", ".....##",
         "##...##", ".#####."),
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
        if shadow is not None:
            for r, row in enumerate(g):
                for k, ch in enumerate(row):
                    if ch == "#":
                        px(a, x + k, y + r + 1, shadow)
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col(r) if callable(col) else col)
        x += len(g[0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1, shadow=None):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow)


def text_in(a, font, s, x, w, y, col):
    """Text centred in the w columns from x (exact, for odd and even widths alike)."""
    draw_text(a, font, s, x + (w - text_w(font, s)) // 2, y, col)


# ------------------------------------------------------------------------------------------
# The Apple logo (the one real mark; private-use skins), rasterised from the SVG
# ------------------------------------------------------------------------------------------

_LOGO = None


def logo_alpha(h):
    """Alpha mask of the Apple logo, h pixels tall, box-downsampled from a 400px raster."""
    global _LOGO
    if _LOGO is None:
        png = os.path.join(SCRATCH, "apple-400.png")
        if not os.path.exists(png):
            subprocess.run(["/usr/bin/rsvg-convert", "-h", "400", LOGO_SVG, "-o", png], check=True)
        _LOGO = Image.open(png).convert("RGBA").getchannel("A")
    w = max(1, round(_LOGO.width * h / _LOGO.height))
    al = np.asarray(_LOGO.resize((w, h), Image.BOX), dtype=np.float64) / 255
    return np.clip((al - 0.12) / 0.76, 0, 1)  # firm up the edges a touch


def apple_logo(a, x, y, h, top, bot):
    al = logo_alpha(h)
    composite(a, x, y, al, vgrad(h, [top, bot]))
    return al.shape[1]


# ------------------------------------------------------------------------------------------
# Shared pieces
# ------------------------------------------------------------------------------------------


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar key: a small rounded key in the click wheel's colour, grey glyph."""
    face = [T["wheel_hi"], T["wheel"]] if not pressed else [shade(T["wheel"], 0.12), shade(T["wheel"], 0.06)]
    edge = lerp(T["wheel_lo"], (0, 0, 0), 0.25) if luma(T["body"]) > 90 else lerp(T["wheel_lo"], T["body_hi"], 0.3)
    shape(a, x, y, 9, 9, 2.2, face, edge)
    ink = T["mark"] if pressed else (T["glyph"] if lit else lerp(T["glyph"], T["wheel"], 0.45))
    X, Y = x, y
    if kind == "options":
        rect(a, X + 3, Y + 3, 3, 3, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 3, 5, 1, ink)
        rect(a, X + 2, Y + 5, 5, 1, ink)
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


def plate_rows(h):
    """Row colours of a title plate h tall: border, gradient (the screen's title strip), border."""
    rows = []
    for r in range(h):
        if r in (0, h - 1):
            rows.append(T["strip_line"])
        else:
            rows.append(ramp([T["strip_top"], T["strip_bot"]], (r - 1) / max(1, h - 3)))
    return rows


def plate(a, x, y, w, h=9):
    for r, c in enumerate(plate_rows(h)):
        rect(a, x, y + r, w, 1, c)


def plate_cap_left(a, x, y, h=9):
    """4 columns: body, body, rounded border, plate."""
    rect(a, x + 2, y + 1, 1, h - 2, T["strip_line"])
    plate(a, x + 3, y, 1, h)
    px(a, x + 3, y, lerp(T["strip_line"], a[y, x + 1], 0.5))
    px(a, x + 3, y + h - 1, lerp(T["strip_line"], a[y + h - 1, x + 1], 0.5))


def plate_cap_right(a, x, y, h=9):
    plate(a, x, y, 1, h)
    rect(a, x + 1, y + 1, 1, h - 2, T["strip_line"])
    px(a, x, y, lerp(T["strip_line"], a[y, x + 2], 0.5))
    px(a, x, y + h - 1, lerp(T["strip_line"], a[y + h - 1, x + 2], 0.5))


def title_ink(lit):
    return T["strip_ink"] if lit else lerp(T["strip_ink"], T["strip_bot"], 0.55)


def screen_box(a, x, y, w, h):
    """A small screen window: 1px bezel round a screen-coloured box."""
    rect(a, x - 1, y - 1, w + 2, h + 2, T["bezel"])
    rect(a, x, y, w, h, T["scr"])
    for cx, cy in ((x - 1, y - 1), (x + w, y - 1), (x - 1, y + h), (x + w, y + h)):
        px(a, cx, cy, lerp(T["bezel"], T["body"], 0.6))


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43)
    body(a, 0, 0, 8, 43, "win", 10, 22)
    rect(a, 1, 1, 6, 41, lerp(T["body"], T["body_lo"], 0.35))
    rect(a, 0, 0, 8, 1, T["body_lo"])
    rect(a, 0, 0, 1, 43, T["body_lo"])
    rect(a, 7, 0, 1, 43, T["body_hi"])
    rect(a, 0, 42, 8, 1, T["body_hi"])
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, T["mark"] if on else T["label_dim"])
    return a


def main_titlebar(lit):
    a = new(275, 14)
    body(a, 0, 0, 275, 14, "win")
    rect(a, 0, 0, 275, 1, T["body_hi"])
    rect(a, 0, 0, 1, 14, T["body_hi"])
    rect(a, 274, 0, 1, 14, T["body_lo"])
    word = T["wordmark"]
    ww = text_w(WORD, word)
    wx = (275 - ww) // 2
    if lit:
        draw_text(a, WORD, word, wx, 3, T["word_lit"], shadow=T["word_shadow"])
    else:
        draw_text(a, WORD, word, wx, 3, T["word_unlit"])
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87)
    body(a, 0, 0, 344, 87)
    lit_bar = main_titlebar(True)
    for kind, x, bx in [("options", 0, 6), ("minimize", 9, 244), ("close", 18, 264)]:
        for pressed, y in ((False, 0), (True, 9)):
            b = lit_bar[3:12, bx:bx + 9].copy()
            mini_button(b, 0, 0, kind, True, pressed)
            a[y:y + 9, x:x + 9] = b
    for pressed, x in ((False, 0), (True, 9)):
        b = lit_bar[3:12, 254:263].copy()
        mini_button(b, 0, 0, "shade", True, pressed)
        a[18:27, x:x + 9] = b
    a[0:14, 27:302] = lit_bar
    a[15:29, 27:302] = main_titlebar(False)
    a[29:43, 27:302] = lit_bar
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

# The screen: one L-shaped window, the iPod's display. The title strip runs along its top;
# the clock and analyzer sit in the taller left part, the track info in the right part.
SCR_TOP, SCR_RIGHT_BOTTOM, SCR_LEFT_BOTTOM = 16, 54, 61
SCR_X0, SCR_X1, SCR_SPLIT = 21, 267, 103

CAPSULE = (16, 88, 114, 18)   # the transport keys' strip (prev .. next)
CB_SPECS = [("previous", 0, 23), ("play", 23, 23), ("pause", 46, 23), ("stop", 69, 23), ("next", 92, 22)]
MENU_KEY = (136, 89, 22, 16)  # the eject button, drawn as the wheel's MENU key
TOGGLES = {"shuffle": (164, 89, 47, 15, "SHUFFLE"), "repeat": (210, 89, 28, 15, "REPEAT"),
           "eq": (219, 58, 23, 12, "EQ"), "pl": (242, 58, 23, 12, "PL")}
MAIN_BASE = None  # main.bmp before the keys and toggles are drawn (their sprites' backgrounds)


def offsets(r2):
    r = int(np.ceil(np.sqrt(r2)))
    return [(dx, dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if dx * dx + dy * dy <= r2]


def dilate(m, r2):
    out = np.zeros_like(m)
    for dx, dy in offsets(r2):
        out |= np.roll(np.roll(m, dy, axis=0), dx, axis=1)
    return out


def draw_screen_shape(a, mask):
    """Screen-coloured mask with a 2px bezel (rounded) and a 1px recess ring outside it."""
    d2 = dilate(mask, 5)
    d3 = dilate(mask, 10)
    ys, xs = np.nonzero(mask)
    y0, x0 = ys.min(), xs.min()
    ring = d3 & ~d2
    for y, x in zip(*np.nonzero(ring)):
        dark = y < y0 or x < x0
        a[y, x] = lerp(a[y, x], T["body_lo"] if dark else T["body_hi"], 0.75)
    a[d2 & ~mask] = T["bezel"]
    a[mask] = T["scr"]
    # round the screen's own corners by a pixel
    for y, x in zip(*np.nonzero(mask)):
        n = mask[y - 1, x] + mask[y + 1, x] + mask[y, x - 1] + mask[y, x + 1]
        if n == 2 and not (mask[y - 1, x] and mask[y + 1, x]) and not (mask[y, x - 1] and mask[y, x + 1]):
            if not mask[y - 1, x - 1] or not mask[y + 1, x + 1] or not mask[y - 1, x + 1] or not mask[y + 1, x - 1]:
                a[y, x] = lerp(T["scr"], T["bezel"], 0.6)


def battery(a, x, y):
    """12x5 battery glyph, full."""
    rect(a, x, y, 11, 1, T["strip_ink"])
    rect(a, x, y + 4, 11, 1, T["strip_ink"])
    rect(a, x, y, 1, 5, T["strip_ink"])
    rect(a, x + 10, y, 1, 5, T["strip_ink"])
    rect(a, x + 11, y + 1, 1, 3, T["strip_ink"])
    if T["model"] == "classic":
        for r in range(3):
            rect(a, x + 2, y + 1 + r, 7, 1, [tint(T["batt"], 0.35), T["batt"], shade(T["batt"], 0.2)][r])
    else:
        rect(a, x + 2, y + 2, 7, 1, T["batt"])
        rect(a, x + 2, y + 1, 7, 3, T["batt"])


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


def wheel_glyph(a, kind, cx, cy, ink):
    """The click wheel's labels: thin grey glyphs."""
    if kind == "previous":
        rect(a, cx - 5, cy - 2, 1, 5, ink)
        tri_left(a, cx - 4, cy - 2, 5, ink)
        tri_left(a, cx - 1, cy - 2, 5, ink)
    elif kind == "next":
        tri_right(a, cx - 3, cy - 2, 5, ink)
        tri_right(a, cx, cy - 2, 5, ink)
        rect(a, cx + 3, cy - 2, 1, 5, ink)
    elif kind == "pause":      # the wheel's play/pause label
        tri_right(a, cx - 4, cy - 2, 5, ink)
        rect(a, cx + 1, cy - 2, 1, 5, ink)
        rect(a, cx + 3, cy - 2, 1, 5, ink)
    elif kind == "stop":
        rect(a, cx - 2, cy - 2, 5, 5, ink)
    elif kind == "play":
        tri_right(a, cx - 1, cy - 3, 7, ink)


def draw_transport(a, pressed=None):
    """The transport keys as one strip of the click wheel, play as its round centre button."""
    x0, y0, w, h = CAPSULE
    composite(a, x0 - 1, y0 - 1, rr_alpha(w + 2, h + 2, (h + 2) / 2),
              T["body_lo"] if luma(T["body"]) > 90 else T["body_hi"])
    composite(a, x0 - 1, y0 - 1, rr_alpha(w + 2, h + 2, (h + 2) / 2, 0.6), T["body"])
    edge = T["wheel_lo"] if luma(T["wheel"]) > 90 else lerp(T["wheel_lo"], T["body_hi"], 0.25)
    composite(a, x0, y0, rr_alpha(w, h, h / 2), edge)
    inner = rr_alpha(w, h, h / 2, 1.0)
    face = vgrad(h, [T["wheel_hi"], T["wheel"], T["wheel"], lerp(T["wheel"], T["wheel_lo"], 0.5)])
    cols = np.repeat(face[:, None, :], w, axis=1)
    for kind, sx, sw in CB_SPECS:
        if kind == pressed and kind != "play":
            cols[:, sx:sx + sw] = np.array([shade(tuple(int(v) for v in c), 0.13) for c in face])[:, None, :]
    composite(a, x0, y0, inner, cols)
    # the centre button
    _, sx, sw = CB_SPECS[1]
    cx, cy = sx + sw / 2, h / 2
    centre = T["centre"] if pressed != "play" else shade(T["centre"], 0.12)
    composite(a, x0, y0, disc_alpha(w, h, cx, cy, 8.5), T["centre_ring"])
    cface = vgrad(h, [tint(centre, 0.25), centre, shade(centre, 0.08)])
    composite(a, x0, y0, disc_alpha(w, h, cx, cy, 7.5), np.repeat(cface[:, None, :], w, axis=1))
    for kind, sx, sw in CB_SPECS:
        ink = T["mark"] if kind == pressed else T["glyph"]
        wheel_glyph(a, kind, x0 + sx + sw // 2, y0 + h // 2, ink)


def draw_menu_key(a, pressed=False):
    x, y, w, h = MENU_KEY
    edge = T["wheel_lo"] if luma(T["wheel"]) > 90 else lerp(T["wheel_lo"], T["body_hi"], 0.25)
    face = [T["wheel_hi"], T["wheel"], lerp(T["wheel"], T["wheel_lo"], 0.5)]
    if pressed:
        face = [shade(c, 0.13) for c in face]
    shape(a, x, y, w, h, 5, face, edge)
    text_in(a, TINY, "MENU", x, w, y + 5, T["mark"] if pressed else T["key_ink"])


def draw_toggle(a, x, y, w, h, label, on, pressed):
    """A toggle as a row of the iPod's menu: plain row when off, the selection bar when on."""
    if on:
        stops = [T["acc_top"], T["acc_bot"]]
        if pressed:
            stops = [shade(c, 0.15) for c in stops]
        edge, ink = shade(T["acc_bot"], 0.3), T["acc_ink"]
    else:
        stops = [T["scr"], lerp(T["scr"], T["faint"], 0.6)] if not pressed else [T["faint"], shade(T["faint"], 0.06)]
        edge, ink = T["strip_line"] if T["model"] == "classic" else T["bezel"], T["ink"]
    shape(a, x, y, w, h, 3, stops, edge)
    text_in(a, TINY, label, x, w, y + (h - 5) // 2, ink)


def make_main():
    global MAIN_BASE
    a = new(275, 116)
    body(a, 0, 0, 275, 116, "win")
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # the screen
    m = np.zeros((116, 275), dtype=bool)
    m[SCR_TOP:SCR_RIGHT_BOTTOM + 1, SCR_X0:SCR_X1 + 1] = True
    m[SCR_TOP:SCR_LEFT_BOTTOM + 1, SCR_X0:SCR_SPLIT + 1] = True
    draw_screen_shape(a, m)
    # its title strip
    for r, c in enumerate(vgrad(7, [T["strip_top"], T["strip_bot"]])):
        rect(a, SCR_X0 + 1 if r == 0 else SCR_X0, SCR_TOP + r, SCR_X1 - SCR_X0 + (-1 if r == 0 else 1), 1,
             tuple(int(v) for v in c))
    rect(a, SCR_X0, SCR_TOP + 7, SCR_X1 - SCR_X0 + 1, 1, T["strip_line"])
    text_center(a, TINY, "NOW PLAYING", (SCR_X0 + SCR_X1) // 2 + 1, SCR_TOP + 1, T["strip_ink"])
    battery(a, SCR_X1 - 15, SCR_TOP + 1)
    # the clock's colon
    for yy in (30, 34):
        rect(a, 72, yy, 2, 2, T["ink"])
    # a hairline between the clock/analyzer and the track info, and under the title
    rect(a, 106, 27, 1, 26, T["faint"])
    rect(a, 110, 38, 156, 1, T["faint"])
    draw_text(a, TINY, "KBPS", 129, 44, T["dim"])
    draw_text(a, TINY, "KHZ", 169, 44, T["dim"])

    # the seek bar's track (posbar.bmp copies it)
    track_y = 74
    composite(a, 17, track_y, rr_alpha(246, 6, 3), T["strip_line"] if T["model"] == "classic" else T["bezel"])
    composite(a, 17, track_y, rr_alpha(246, 6, 3, 1.0), vgrad(6, [T["faint"], T["scr"], T["scr"]]))

    MAIN_BASE = a.copy()
    draw_transport(a)
    draw_menu_key(a)
    for k, (x, y, w, h, label) in TOGGLES.items():
        draw_toggle(a, x, y, w, h, label, False, False)
    # the About spot: the Apple logo, as on the back of the iPod
    al = logo_alpha(14)
    lw = al.shape[1]
    top, bot = T["logo"]
    composite(a, 253 + (13 - lw) // 2, 91, al, vgrad(14, [top, bot]))
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36), shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def make_cbuttons(main):
    a = new(136, 36)
    x0, y0, w, h = CAPSULE
    for kind, sx, sw in CB_SPECS:
        a[0:18, sx:sx + sw] = main[y0:y0 + 18, x0 + sx:x0 + sx + sw]
        t = MAIN_BASE.copy()
        draw_transport(t, pressed=kind)
        a[18:36, sx:sx + sw] = t[y0:y0 + 18, x0 + sx:x0 + sx + sw]
    x, y, w, h = MENU_KEY
    a[0:16, 114:136] = main[y:y + 16, x:x + 22]
    t = MAIN_BASE.copy()
    draw_menu_key(t, pressed=True)
    a[16:32, 114:136] = t[y:y + 16, x:x + 22]
    return a


def make_shufrep():
    a = new(92, 85)
    body(a, 0, 0, 92, 85)

    def cell(kind, on, pressed):
        x, y, w, h, label = TOGGLES[kind]
        t = MAIN_BASE[y:y + h, x:x + w].copy()
        draw_toggle(t, 0, 0, w, h, label, on, pressed)
        return t

    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = cell("repeat", on, pressed)
        a[y:y + 15, 28:75] = cell("shuffle", on, pressed)
    for kind, x, pressed in [("eq", 0, False), ("pl", 23, False), ("eq", 46, True), ("pl", 69, True)]:
        a[61:73, x:x + 23] = cell(kind, False, pressed)
        a[73:85, x:x + 23] = cell(kind, True, pressed)
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T["scr"])
    for y, on in ((0, True), (12, False)):
        col = T["ink"] if on else T["faint"]
        text_center(a, TINY, "STEREO", 14, y + 4, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 4, col)
    return a


def make_playpaus():
    a = new(48, 9, T["scr"])
    acc = T["mark"] if T["model"] == "classic" else T["ink"]
    tri_right(a, 2, 1, 7, acc)                         # playing
    rect(a, 9 + 2, 1, 2, 7, T["ink"])                  # paused
    rect(a, 9 + 5, 1, 2, 7, T["ink"])
    rect(a, 18 + 2, 2, 5, 5, T["ink"])                 # stopped
    rect(a, 36, 0, 3, 9, T["scr"])                     # not working
    rect(a, 39 + 1, 3, 1, 3, acc)                      # working
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["scr"])
    for n in range(10):
        draw_text(a, {0: DIGITS[n]}, [0], 9 * n + 1, 1, T["ink"])
    if ex:
        rect(a, 99 + 2, 6, 5, 2, T["ink"])            # minus
    else:
        pass                                           # numbers.bmp's minus: unused when nums_ex exists
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, T["scr"])
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


def make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    for x0, pressed in ((248, False), (278, True)):
        a[0:10, x0:x0 + 29] = np.repeat(a[0:10, 120:121], 29, axis=1)
        stops = [T["acc_top"], T["acc_bot"]]
        if pressed:
            stops = [tint(T["acc_top"], 0.2), shade(T["acc_bot"], 0.1)]
        shape(a, x0, 0, 29, 10, 5, stops, shade(T["acc_bot"], 0.35))
        hl = rr_alpha(29, 10, 5, 1.0) - rr_alpha(29, 10, 5, 2.0)
        hl[5:] = 0
        composite(a, x0, 0, hl * 0.5, (255, 255, 255))
    return a


def knob(a, x, y, w, h, pressed):
    """The volume/balance thumb: a small wheel-coloured key with an accent tick."""
    edge = T["glyph"] if luma(T["wheel"]) > 90 else lerp(T["wheel_lo"], T["body_hi"], 0.5)
    face = [T["wheel_hi"], T["wheel"], lerp(T["wheel"], T["wheel_lo"], 0.6)]
    if pressed:
        face = [shade(c, 0.1) for c in face]
    shape(a, x, y, w, h, 3, face, edge)
    rect(a, x + w // 2 - 1, y + 3, 2, h - 6, T["mark"] if pressed else T["glyph"])


def slider_thumbs(a, main):
    for x, pressed in ((0, True), (15, False)):
        a[422:433, x:x + 14] = main[58:69, 108:122]
        knob(a, x, 422, 14, 11, pressed)


def track(a, x, y, w, h, fill_from, fill_to):
    """A small iPod bar: screen-coloured trough, selection-coloured fill over [fill_from, fill_to)."""
    composite(a, x, y, rr_alpha(w, h, h / 2), T["strip_line"] if T["model"] == "classic" else T["bezel"])
    inner = rr_alpha(w, h, h / 2, 1.0)
    composite(a, x, y, inner, vgrad(h, [T["faint"], T["scr"]]))
    if fill_to > fill_from:
        m = inner.copy()
        m[:, :fill_from] = 0
        m[:, fill_to:] = 0
        composite(a, x, y, m, vgrad(h, [T["acc_top"], T["acc_bot"]]))


def make_volume(main):
    a = new(68, 433)
    body(a, 0, 0, 68, 433)
    for i in range(28):
        y = i * 15
        a[y:y + 13, 0:68] = MAIN_BASE[57:70, 107:175]
        level = (i + 1) / 28
        track(a[y:y + 13], 2, 4, 64, 6, 0, 4 + round(level * 58))
    slider_thumbs(a, MAIN_BASE)
    return a


def make_balance(main):
    a = new(68, 433)
    body(a, 0, 0, 68, 433)
    for i in range(28):
        y = i * 15
        a[y:y + 13, 9:47] = MAIN_BASE[57:70, 177:215]
        reach = round(15 * i / 27)
        sub = a[y:y + 13, 9:47]
        track(sub, 2, 4, 34, 6, 17 - reach, 17 + reach)
        rect(sub, 18, 2, 1, 2, T["label_dim"])
    slider_thumbs(a, MAIN_BASE)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
EQ_TOGGLES = {"on": (14, 18, 26, 12, "ON"), "auto": (40, 18, 32, 12, "AUTO")}


def eq_titlebar(lit):
    a = new(275, 14)
    body(a, 0, 0, 275, 14, "win")
    rect(a, 0, 0, 275, 1, T["body_hi"])
    rect(a, 0, 0, 1, 14, T["body_hi"])
    rect(a, 274, 0, 1, 14, T["body_lo"])
    title = "EQUALIZER"
    tw = text_w(FONT5, title)
    pw = tw + 12
    px0 = (275 - pw) // 2
    plate_cap_left(a, px0 - 4, 2, 10)
    plate(a, px0, 2, pw, 10)
    plate_cap_right(a, px0 + pw, 2, 10)
    draw_text(a, FONT5, title, px0 + 6, 4, title_ink(lit))
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    """14x63: a vertical iPod bar whose fill rises with the value (n of 0..27)."""
    rect(a, x, y, 14, 63, T["scr"])
    v = n / 27
    top = round((1 - v) * 51) + 5
    sub = a[y:y + 63, x:x + 14]
    edge = T["strip_line"] if T["model"] == "classic" else T["bezel"]
    composite(sub, 4, 1, rr_alpha(6, 61, 3), edge)
    inner = rr_alpha(6, 61, 3, 1.0)
    composite(sub, 4, 1, inner, np.array([T["faint"]] * 61, dtype=float))
    m = inner.copy()
    m[:max(0, top - 1)] = 0
    hgrad = np.array([[ramp([T["acc_top"], T["acc_bot"]], c / 5) for c in range(6)]] * 61, dtype=float)
    composite(sub, 4, 1, m, hgrad)
    rect(sub, 1, 31, 2, 1, T["dim"])
    rect(sub, 11, 31, 2, 1, T["dim"])


def make_eqmain():
    a = new(275, 315)
    if T.get("metal"):
        body(a, 0, 0, 275, 116, "win")
        body(a, 0, 116, 275, 199)
    else:
        body(a, 0, 0, 275, 315)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = eq_titlebar(True)
    # the screen: graph on top, slider bay below, one T-shaped window
    m = np.zeros((315, 275), dtype=bool)
    m[17:36, 86:199] = True
    m[36:38, 86:199] = True
    m[38:103, 17:259] = True
    draw_screen_shape(a, m)
    # its title-strip line under the graph
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, T["dim"])
        rect(a, 42, yy + 2, 3, 1, T["faint"])
        rect(a, 71, yy + 2, 3, 1, T["faint"])
    rect(a, 39, 40, 1, 60, T["faint"])
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    text_center(a, TINY, "PREAMP", 28, 107, T["label"])
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 107, T["label"])
    # graph (blitted over the seat at 86,17)
    rect(a, 86, 17, 113, 19, T["scr"])
    base = a.copy()
    for k, (x, y, w, h, label) in EQ_TOGGLES.items():
        draw_toggle(a, x, y, w, h, label, False, False)
    draw_toggle(a, 217, 18, 44, 12, "PRESETS", False, False)

    # under the window
    t = a[0:14, :].copy()
    b = t[3:12, 264:273].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = b
    for x, kind, on, pressed in [
        (10, "on", False, False), (36, "auto", False, False), (69, "on", True, False), (95, "auto", True, False),
        (128, "on", False, True), (154, "auto", False, True), (187, "on", True, True), (213, "auto", True, True),
    ]:
        sx, sy, w, h, label = EQ_TOGGLES[kind]
        cellimg = base[sy:sy + h, sx:sx + w].copy()
        draw_toggle(cellimg, 0, 0, w, h, label, on, pressed)
        a[119:119 + h, x:x + w] = cellimg
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    for y, pressed in ((164, False), (176, True)):
        rect(a, 0, y, 11, 11, T["scr"])
        edge = T["glyph"] if luma(T["wheel"]) > 90 else T["wheel_lo"]
        face = [T["wheel_hi"], lerp(T["wheel"], T["wheel_lo"], 0.4)]
        if T["model"] == "classic" and luma(T["wheel"]) < 90:
            face = [T["wheel_hi"], T["wheel"]]
        if pressed:
            face = [shade(c, 0.1) for c in face]
        composite(a, 0, y, disc_alpha(11, 11, 5.5, 5.5, 5.4), edge)
        composite(a, 0, y, disc_alpha(11, 11, 5.5, 5.5, 4.4), vgrad(11, face))
        rect(a, 5, y + 5, 1, 1, T["mark"] if pressed else T["glyph"])
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        cellimg = base[18:30, 217:261].copy()
        draw_toggle(cellimg, 0, 0, 44, 12, "PRESETS", pressed, False)
        a[y:y + 12, 224:268] = cellimg
    # graph
    rect(a, 0, 294, 113, 19, T["scr"])
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, T["faint"])
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, T["faint"])
    gstops = ([T["acc_top"], T["acc_bot"], shade(T["acc_bot"], 0.3)] if T["model"] == "classic"
              else [T["dim"], T["ink"], shade(T["ink"], 0.3)])
    for r in range(19):
        px(a, 115, 294 + r, ramp(gstops, r / 18))
    for x in range(113):
        px(a, x, 314, T["dim"] if x % 3 != 2 else T["scr"])
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109)
# ------------------------------------------------------------------------------------------

PLATE_Y = 3


def bar20(w):
    a = new(w, 20)
    body(a, 0, 0, w, 20, "top")
    rect(a, 0, 0, w, 1, T["body_hi"])
    return a


def key(a, x, y, w, h, label, pressed=False):
    edge = T["wheel_lo"] if luma(T["wheel"]) > 90 else lerp(T["wheel_lo"], T["body_hi"], 0.25)
    if luma(T["body"]) > 150 and luma(T["wheel"]) > 200:
        edge = lerp(T["wheel_lo"], T["body_lo"], 0.5)
    face = [T["wheel_hi"], T["wheel"], lerp(T["wheel"], T["wheel_lo"], 0.5)]
    if pressed:
        face = [shade(c, 0.12) for c in face]
    shape(a, x, y, w, h, 4, face, edge)
    text_in(a, TINY, label, x, w, y + (h - 5) // 2, T["key_ink"] if not pressed else T["mark"])


def mini_transport_icon(a, kind, x, y, ink):
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


def grip(a, right, bottom, n=4):
    for k in range(n):
        for j in range(k + 1):
            gx, gy = right - 3 * k + 3 * j, bottom - 3 * j
            px(a, gx, gy, T["label_dim"])
            px(a, gx + 1, gy + 1, T["body_hi"])


def make_pledit():
    a = new(280, 186)
    body(a, 0, 0, 280, 186)
    bz = T["bezel"]
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25)
        rect(t, 0, 19, 25, 1, bz)
        a[y:y + 20, 127:152] = t
        t = bar20(25)
        rect(t, 0, 0, 1, 20, T["body_hi"])
        rect(t, 11, 19, 14, 1, bz)
        rect(t, 11, 19, 1, 1, lerp(bz, T["body"], 0.5))
        a[y:y + 20, 0:25] = t
        t = bar20(100)
        plate_cap_left(t, 0, PLATE_Y)
        plate(t, 4, PLATE_Y, 92)
        plate_cap_right(t, 96, PLATE_Y)
        text_center(t, FONT5, "PLAYLIST", 50, PLATE_Y + 2, title_ink(lit))
        rect(t, 0, 19, 100, 1, bz)
        a[y:y + 20, 26:126] = t
        t = bar20(25)
        rect(t, 24, 0, 1, 20, T["body_lo"])
        mini_button(t, 14, 3, "close", lit)
        rect(t, 0, 19, 20, 1, bz)
        rect(t, 19, 19, 1, 1, lerp(bz, T["body"], 0.5))
        a[y:y + 20, 153:178] = t

    # left side: body, the list's bezel at the inner edge
    t = new(12, 29)
    body(t, 0, 0, 12, 29)
    rect(t, 0, 0, 1, 29, T["body_hi"])
    rect(t, 11, 0, 1, 29, bz)
    a[42:71, 0:12] = t
    # right side: the screen continues into the scroll bar (cols 0..13), bezel, body
    t = new(20, 29)
    body(t, 0, 0, 20, 29)
    rect(t, 0, 0, 14, 29, T["scr"])
    rect(t, 14, 0, 1, 29, bz)
    rect(t, 19, 0, 1, 29, T["body_lo"])
    rect(t, 5, 0, 1, 29, T["faint"] if T["model"] == "classic" else T["dim"])
    rect(t, 6, 0, 6, 29, lerp(T["scr"], T["faint"], 0.6))
    rect(t, 12, 0, 1, 29, T["faint"] if T["model"] == "classic" else T["dim"])
    a[42:71, 31:51] = t
    b = new(9, 9)
    b[:] = a[3:12, 167:176]
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = b
    for x, sel in ((52, False), (61, True)):
        rect(a, x, 53, 8, 18, lerp(T["scr"], T["faint"], 0.6))
        stops = [T["acc_top"], T["acc_bot"]] if not sel else [tint(T["acc_top"], 0.2), shade(T["acc_bot"], 0.1)]
        shape(a, x, 53, 8, 18, 3, stops, shade(T["acc_bot"], 0.3))

    def bottom_base(w):
        t = new(w, 38)
        body(t, 0, 0, w, 38, "bottom38")
        rect(t, 0, 37, w, 1, T["body_lo"])
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, T["body_hi"])
    rect(t, 11, 0, 114, 1, bz)
    rect(t, 11, 0, 1, 1, lerp(bz, T["body"], 0.5))
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        key(t, bx, 8, 22, 18, lbl)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, T["body_lo"])
    rect(t, 0, 0, 145, 1, bz)
    rect(t, 144, 0, 1, 1, lerp(bz, T["body"], 0.5))
    screen_box(t, 6, 9, 56, 8)
    # mini transport: a little strip of the wheel
    edge = T["wheel_lo"] if luma(T["wheel"]) > 90 else lerp(T["wheel_lo"], T["body_hi"], 0.25)
    shape(t, 2, 22, 62, 10, 5, [T["wheel_hi"], T["wheel"]], edge)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        mini_transport_icon(t, kind, 3 + 10 * k, 22, T["glyph"])
    screen_box(t, 65, 22, 33, 8)
    rect(t, 84, 24, 1, 1, T["dim"])  # the colon between minutes and seconds
    rect(t, 84, 27, 1, 1, T["dim"])
    key(t, 106, 8, 22, 18, "LIST")
    grip(t, 145, 33)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    rect(t, 0, 0, 25, 1, bz)
    a[0:38, 179:204] = t
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_gen():
    a = new(194, 109)
    body(a, 0, 0, 194, 109)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn):
            t = bar20(25)
            fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 1, 20, T["body_hi"])

        def left_end(t):
            plate_cap_left(t, 17, PLATE_Y)
            plate(t, 21, PLATE_Y, 4)

        def centre(t):
            plate(t, 0, PLATE_Y, 25)

        def right_end(t):
            plate(t, 0, PLATE_Y, 4)
            plate_cap_right(t, 4, PLATE_Y)

        def fill(t):
            pass

        def right(t):
            mini_button(t, 14, 3, "close", lit)
            rect(t, 24, 0, 1, 20, T["body_lo"])

        piece(0, left)
        piece(26, left_end)
        piece(52, centre)
        piece(78, right_end)
        piece(104, fill)
        piece(130, right)

    def bottom(w, has_grip, left_edge):
        t = new(w, 14)
        body(t, 0, 0, w, 14, "bottom14")
        rect(t, 0, 13, w, 1, T["body_lo"])
        if left_edge:
            rect(t, 0, 0, 1, 14, T["body_hi"])
        else:
            rect(t, w - 1, 0, 1, 14, T["body_lo"])
        if has_grip:
            grip(t, w - 4, 10, 3)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        body(t, 0, 0, w, h)
        if outer_left:
            rect(t, 0, 0, 1, h, T["body_hi"])
        else:
            rect(t, w - 1, 0, 1, h, T["body_lo"])
        a[42:42 + h, x:x + w] = t
    b = new(9, 9)
    b[:] = a[3:12, 144:153]
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = b

    # letters: each row starts at x 1, letters in their own cells (the plate's rows 4..10 behind
    # them, so they sit in the plate seamlessly), 1px separators of x 0's colour
    rows = plate_rows(9)[1:8]
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            for r in range(7):
                rect(a, x, y + r, w, 1, rows[r])
            draw_text(a, FONT5, c, x, y + 1, title_ink(lit))
            x += w + 1
        assert x <= 194, x
    return a


def genex_colours():
    dark_body = luma(T["body"]) < 110
    win_text = (226, 226, 230) if dark_body else shade(T["body"], 0.82)
    return [
        T["scr"],                                   # item background
        T["ink"],                                   # item text
        T["body"],                                  # window background
        T["glyph"] if dark_body else shade(T["body"], 0.7),  # button text
        win_text,                                   # window text
        T["strip_line"],                            # dividers, sunken borders
        T["pl_sel"],                                # selection bar
        T["strip_bot"],                             # list header background
        T["strip_ink"],                             # list header text
        T["strip_top"],                             # header frame, light
        T["strip_line"],                            # header frame, dark
        T["pl_sel"],                                # header frame, pressed
        T["body"],                                  # header dead area
        T["faint"],                                 # scrollbar
        T["acc_bot"],                               # scrollbar 2
        T["faint"],                                 # scrollbar pressed
        T["acc_top"],                               # scrollbar pressed 2
        T["scr"],                                   # scrollbar dead area
    ]


def make_genex():
    a = new(256, 64)
    body(a, 0, 1, 256, 63)
    rect(a, 0, 0, 256, 1, T["body"])
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    key(a, 0, 1, 47, 15, "")
    key(a, 0, 16, 47, 15, "", pressed=True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    bg = T["scr"]
    dots = lerp(T["scr"], T["faint"], 0.6)
    spec = [(ramp(T["vis_spec"], i / 15), f"spectrum {i + 1}") for i in range(16)]
    osc = [(c, f"oscilloscope {i + 1}") for i, c in enumerate(T["vis_osc"])]
    return [(bg, "background"), (dots, "dots")] + spec + osc + [(T["vis_peak"], "peaks")]


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={hexc(T['pl_normal'])}\nCurrent={hexc(T['pl_current'])}\n"
                f"NormalBG={hexc(T['scr'])}\nSelectedBG={hexc(T['pl_sel'])}\n"
                f"MbBG={hexc(T['scr'])}\nMbFG={hexc(T['pl_normal'])}\nFont=Helvetica\n")
    model = "iPod " + T["model"]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        title = f"{model} ({T['name']})"
        f.write(
            f"{title}\n{'=' * len(title)}\n\n"
            f"{model} — a skin in the style of the {model}, drawn from scratch (apart from the\n"
            f"Apple logo).\n\n"
            "A classic (Winamp 2.x format) skin. Every bitmap except the logo was drawn by a script\n"
            "(gen_skin.py) from shapes, gradients, noise and hand-made pixel fonts.\n\n"
            "Apple logo © Apple Inc.\n"
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
    # genex.bmp completed for real Winamp and WACUP: all 24 colours, readable text, and the
    # standard 112x59 button and scrollbar layout (skins/genex_wacup.py).
    genex_wacup.process(os.path.join(HERE, T["wsz"]))
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


def draw_bitmap_text(dst, s, x, y):
    text = SHEETS["text"]
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, text, (col * 5, row * 6, 5, 6), x, y)
        x += 5


def ttf(size):
    for name in ("LiberationSans-Regular.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def preview_main(lit, state):
    S = SHEETS
    img = Image.new("RGB", (275, 116))
    img.paste(S["main"], (0, 0))
    blit(img, S["titlebar"], (27, 0 if lit else 15, 275, 14), 0, 0)
    pos = {"previous": 16, "play": 39, "pause": 62, "stop": 85, "next": 108}
    for k, x, w in CB_SPECS:
        blit(img, S["cbuttons"], (x, 18 if state["pressed"] == k else 0, w, 18), pos[k], 88)
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
    # title: text.bmp's space across the box, then the title in the playlist's font and colour
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    box = img.crop((111, 22, 265, 36))
    d = ImageDraw.Draw(box)
    d.text((0, 29 - 22), state["title"], fill=T["pl_normal"], font=ttf(11), anchor="lm")
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
    lx, lw = 12, w - 32
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=T["scr"])
    font = ttf(9)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=T["pl_sel"])
        col = T["pl_current"] if i == 1 else T["pl_normal"]
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
    arr = np.array(pic).astype(np.float32) / 255
    col = np.stack([70 + 120 * arr[..., 0], 80 + 110 * arr[..., 0], 100 + 120 * arr[..., 0]], -1)
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("Click Wheel - Centre Button", "4:12"), ("Pocket Sized - 1,000 Songs", "3:47"),
            ("White Earbuds - Silhouette", "5:03"), ("Hold Switch - Locked", "2:58"),
            ("Shuffle Songs - Now Playing", "6:21"), ("Cover Flow - Album Art", "3:33"),
            ("On-The-Go - Playlist", "4:40"), ("Dock Connector - Sync", "3:09"),
            ("Scrubbing - Fast Forward", "5:51"), ("Battery Full - Charged", "4:05"),
            ("Menu - Back", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=f"Now Playing - iPod {T['model']} {T['name']}", bars=bars)
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
    global T, OUT, _rng
    T = make_theme(key)
    OUT = os.path.join(OUT_ROOT, key)
    os.makedirs(OUT, exist_ok=True)
    _rng = np.random.default_rng(1729)
    names = build()
    preview()
    sizes = []
    for n in names:
        if n.endswith(".bmp"):
            im = Image.open(os.path.join(OUT, n))
            assert im.mode == "RGB", n
            sizes.append(f"{n[:-4]} {im.size[0]}x{im.size[1]}")
    print(f"{T['wsz']}: " + ", ".join(sizes))


if __name__ == "__main__":
    os.makedirs(SCRATCH, exist_ok=True)
    args = sys.argv[1:]
    if "--list" in args:
        print("\n".join(THEME_KEYS))
        sys.exit(0)
    for a in args:
        if a not in THEME_KEYS:
            sys.exit(f"unknown theme {a!r}; try --list")
    for k in args or THEME_KEYS:
        run(k)
