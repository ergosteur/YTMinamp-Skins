#!/usr/bin/python3
"""PlayStation: classic Winamp 2.x skins in the style of three Sony consoles, 1994-2000.

One procedural generator, one theme per skin:

  ps1    the original PlayStation (1994): the light grey ABS shell with its ribbed back, the
         black CD player and the blue-to-black Memory Card screen of the BIOS, round grey
         transport buttons with the controller's symbol colours, the colour PlayStation logo.
  psone  the PSone (2000) and its 5" LCD screen: a white rounded frame round one dark screen
         holding every display, soft white buttons, a speaker grille, the colour logo.
  ps2    the PlayStation 2 (2000): the black ribbed console, the dark-blue browser with its
         floating translucent towers and the boot's blue particles, glossy black DualShock 2
         buttons with coloured symbols, the blue PS2 logo in the titlebar.

Everything is drawn here from code (anti-aliased shapes, a system sans for the lettering, pixel
fonts for text.bmp), except the logos, rasterised from source/*/logo.svg.

    /usr/bin/python3 -I gen_skin.py              # every theme
    /usr/bin/python3 -I gen_skin.py ps2          # just these
    /usr/bin/python3 -I gen_skin.py --list       # the theme names

Writes out/<theme>/*.bmp + text files, <Name>.wsz and preview-<theme>.png beside this file.
Private use only.
"""

import os
import subprocess
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py, which finishes each .wsz
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.join(HERE, "out")
SCRATCH = os.path.join(OUT_ROOT, "scratch")
OUT = OUT_ROOT  # set per theme

SEP = (255, 0, 255)  # gen.bmp letter separators (never shown)

NOTO = "/usr/share/fonts/google-noto/NotoSans-{}.ttf"
LIBERATION = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# The controller's four symbols, in their printed colours.
SYM = {"tri": (40, 196, 150), "circle": (232, 72, 82), "cross": (104, 140, 232), "square": (222, 118, 200)}
# Which symbol each toggle wears; the transport glyphs take the same colours (play is the green
# triangle, stop the pink square, pause the red of the circle, the skips the blue of the cross).
TOGGLE_SYM = {"EQ": "tri", "PL": "square", "ON": "circle", "AUTO": "cross"}
GLYPH_SYM = {"play": "tri", "stop": "square", "pause": "circle", "previous": "cross", "next": "cross"}
LOGO_YELLOW = (243, 194, 2)

# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------
# bg: the body's flat colour; panel/panel_line: the displays (also text.bmp's and the analyzer's
# background); ink: text.bmp's letters (so the app's TrueType title too); text/text2/text3:
# lettering on the bars and body (strong, secondary, dim); plab/blab: labels on a panel and on
# the body; pl: pledit.txt; vis: the analyzer's stops, top to bottom.

THEMES = {
    "ps1": dict(
        style="ps1", name="PlayStation", wsz="PlayStation", owner="Sony Interactive Entertainment",
        subject="the original Sony PlayStation (1994)", logo="logo-ps1-colour",
        title="PlayStation", eq_title="EQUALIZER", pl_title="CD PLAYER", gen_title="ALBUM ART",
        font=NOTO.format("SemiBold"), font_bold=NOTO.format("Bold"), digit_font=NOTO.format("SemiBold"),
        bg="#c6c7ca", panel="#0d0e12", panel_line="#3a3c42", radius=2,
        ink="#d9dee9", text="#3c3e44", text2="#6c6f76", text3="#a2a5ab",
        plab="#8c93a6", blab="#c9cfe2",
        pl=dict(NormalBG="#0A1036", Normal="#C3CBE4", Current="#F3C202", SelectedBG="#2A3D94"),
        vis=["#de0029", "#f3c202", "#00aa9e", "#326db3"],
    ),
    "psone": dict(
        style="psone", name="PSone", wsz="PSone", owner="Sony Interactive Entertainment",
        subject="the Sony PSone (2000) and its LCD screen", logo="logo-ps1-colour",
        title="PSone", eq_title="EQUALIZER", pl_title="PLAYLIST", gen_title="ALBUM ART",
        font=NOTO.format("Medium"), font_bold=NOTO.format("SemiBold"), digit_font=NOTO.format("Medium"),
        bg="#eef0f2", panel="#141b28", panel_line="#b4bac3", radius=3,
        ink="#e4ecf8", text="#5c626c", text2="#8a9099", text3="#bcc1c8",
        plab="#7c8ba4", blab="#8a9099",
        pl=dict(NormalBG="#FFFFFF", Normal="#3C424C", Current="#2F68B0", SelectedBG="#DCE6F3"),
        vis=["#f4f9ff", "#a8ccf4", "#5a90d6", "#2c5596"],
    ),
    "ps2": dict(
        style="ps2", name="PlayStation 2", wsz="PlayStation-2", owner="Sony Interactive Entertainment",
        subject="the Sony PlayStation 2 (2000)", logo="logo-ps2",
        title="", eq_title="SYSTEM CONFIGURATION", pl_title="BROWSER", gen_title="ALBUM ART",
        font=NOTO.format("Regular"), font_bold=NOTO.format("SemiBold"), digit_font=NOTO.format("Regular"),
        bg="#0b0c10", panel="#040a20", panel_line="#2c62cc", radius=2,
        ink="#d2e6ff", text="#d8e2f4", text2="#7f9cd0", text3="#3d5688",
        plab="#7f9cd0", blab="#9db6e2",
        pl=dict(NormalBG="#030817", Normal="#B8CCEE", Current="#6FC8FF", SelectedBG="#173C8C"),
        vis=["#eaf6ff", "#7fc4ff", "#2f7ce0", "#123c9c"],
    ),
}

T = {}


def setup_theme(key):
    global T, OUT
    raw = dict(THEMES[key])
    raw["key"] = key
    for k, v in list(raw.items()):
        if isinstance(v, str) and v.startswith("#") and len(v) == 7:
            raw[k] = hexc(v)
    raw["vis"] = [hexc(c) for c in raw["vis"]]
    T = raw
    OUT = os.path.join(OUT_ROOT, key)
    os.makedirs(OUT, exist_ok=True)


def ST():
    return T["style"]


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def is_light():
    return sum(T["bg"]) > 384


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int) and anti-aliased masks
# ------------------------------------------------------------------------------------------


def new(w, h, col=(0, 0, 0)):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[y:y + h, x:x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def vgrad_fill(a, x, y, w, h, top, bot):
    for r in range(h):
        a[y + r, x:x + w] = lerp(top, bot, r / max(1, h - 1))


SS = 4


def mask(w, h, fn):
    im = Image.new("L", (w * SS, h * SS), 0)
    fn(ImageDraw.Draw(im), SS)
    return np.asarray(im.resize((w, h), Image.BOX), dtype=np.float32) / 255.0


def paint(a, x, y, m, col, alpha=1.0):
    h, w = m.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(a.shape[1], x + w), min(a.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    mm = (m[y0 - y:y1 - y, x0 - x:x1 - x] * alpha)[..., None]
    c = np.asarray(col, dtype=np.float32)
    if c.ndim == 3:
        c = c[y0 - y:y1 - y, x0 - x:x1 - x]
    reg = a[y0:y1, x0:x1].astype(np.float32)
    a[y0:y1, x0:x1] = np.round(reg * (1 - mm) + c * mm).astype(np.int32)


def rrect(a, x, y, w, h, r, col, alpha=1.0):
    """Anti-aliased rounded rectangle, integer box."""
    if w <= 0 or h <= 0:
        return
    r = min(r, w / 2, h / 2)
    m = mask(w, h, lambda d, S: d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), radius=r * S, fill=255))
    paint(a, x, y, m, col, alpha)


def disc(a, cx, cy, r, col, alpha=1.0):
    x0, y0 = int(np.floor(cx - r)) - 1, int(np.floor(cy - r)) - 1
    w = h = int(np.ceil(2 * r)) + 3
    m = mask(w, h, lambda d, S: d.ellipse(((cx - r - x0) * S, (cy - r - y0) * S, (cx + r - x0) * S - 1,
                                           (cy + r - y0) * S - 1), fill=255))
    paint(a, x0, y0, m, col, alpha)


def poly(a, pts, col, alpha=1.0):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, y0 = int(np.floor(min(xs))) - 1, int(np.floor(min(ys))) - 1
    w, h = int(np.ceil(max(xs))) - x0 + 2, int(np.ceil(max(ys))) - y0 + 2
    m = mask(w, h, lambda d, S: d.polygon([((p[0] - x0) * S, (p[1] - y0) * S) for p in pts], fill=255))
    paint(a, x0, y0, m, col, alpha)


def frect(a, x0, y0, x1, y1, col, r=0.0, alpha=1.0):
    """Anti-aliased (sub-pixel) rectangle from (x0, y0) to (x1, y1), optional corner radius."""
    bx, by = int(np.floor(x0)) - 1, int(np.floor(y0)) - 1
    w, h = int(np.ceil(x1)) - bx + 2, int(np.ceil(y1)) - by + 2
    m = mask(w, h, lambda d, S: d.rounded_rectangle(((x0 - bx) * S, (y0 - by) * S, (x1 - bx) * S - 1,
                                                     (y1 - by) * S - 1), radius=r * S, fill=255))
    paint(a, bx, by, m, col, alpha)


def strokes(a, x, y, w, h, fn, col, alpha=1.0):
    paint(a, x, y, mask(w, h, fn), col, alpha)


def stops_col(h, stops):
    """(h, 1, 3) int column through [(pos 0..1, colour), ...]."""
    t = new(1, h)
    for r in range(h):
        p = r / max(1, h - 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= p <= p1:
                t[r, 0] = lerp(hexc(c0) if isinstance(c0, str) else c0,
                               hexc(c1) if isinstance(c1, str) else c1, (p - p0) / max(1e-6, p1 - p0))
                break
    return t


def grad_box(w, h, top, bot):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top, bot = np.array(top, np.float32), np.array(bot, np.float32)
    return np.repeat(top * (1 - t) + bot * t, w, axis=1)


def grad_rrect(a, x, y, w, h, r, top, bot, alpha=1.0):
    if w <= 0 or h <= 0:
        return
    r = min(r, w / 2, h / 2)
    m = mask(w, h, lambda d, S: d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), radius=r * S, fill=255))
    paint(a, x, y, m, grad_box(w, h, top, bot), alpha)


def grad_disc(a, cx, cy, r, top, bot, alpha=1.0):
    x0, y0 = int(np.floor(cx - r)) - 1, int(np.floor(cy - r)) - 1
    w = h = int(np.ceil(2 * r)) + 3
    m = mask(w, h, lambda d, S: d.ellipse(((cx - r - x0) * S, (cy - r - y0) * S, (cx + r - x0) * S - 1,
                                           (cy + r - y0) * S - 1), fill=255))
    t = np.clip((np.arange(h, dtype=np.float32) + y0 + 0.5 - (cy - r)) / (2 * r), 0, 1)[:, None, None]
    col = np.repeat(np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t, w, axis=1)
    paint(a, x0, y0, m, col, alpha)


def ellipse(a, cx, cy, rx, ry, col, alpha=1.0):
    x0, y0 = int(np.floor(cx - rx)) - 1, int(np.floor(cy - ry)) - 1
    w, h = int(np.ceil(2 * rx)) + 3, int(np.ceil(2 * ry)) + 3
    m = mask(w, h, lambda d, S: d.ellipse(((cx - rx - x0) * S, (cy - ry - y0) * S, (cx + rx - x0) * S - 1,
                                           (cy + ry - y0) * S - 1), fill=255))
    paint(a, x0, y0, m, col, alpha)


def blur_glow(a, draw_fn, col, radius, gain, alpha):
    """A soft glow: whatever draw_fn paints white on a black copy, blurred and painted in col."""
    g = new(a.shape[1], a.shape[0], (0, 0, 0))
    draw_fn(g)
    m = np.asarray(Image.fromarray(np.clip(g[..., 0], 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(radius)), np.float32) / 255.0
    paint(a, 0, 0, np.clip(m * gain, 0, 1), col, alpha)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


# ------------------------------------------------------------------------------------------
# Lettering: the system sans (hinted, anti-aliased) and pixel fonts for text.bmp
# ------------------------------------------------------------------------------------------

_fonts = {}


def font(path, size):
    key = (path, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]


def ttext(a, s, f, x, base, col, align="l", alpha=1.0):
    """TrueType text with its baseline on row `base`; x is the left edge or the centre."""
    if not s:
        return
    adv = f.getlength(s)
    if align == "c":
        x = x - adv / 2
    x = int(round(x))
    base = int(round(base))
    l, t, r, b = f.getbbox(s, anchor="ls")
    w, h = r - l + 2, b - t + 2
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).text((-l + 1, -t + 1), s, font=f, fill=255, anchor="ls")
    m = np.asarray(im, dtype=np.float32) / 255.0
    paint(a, x + l - 1, base + t - 1, m, col, alpha)


def spaced_w(s, f, sp):
    return sum(f.getlength(c) for c in s) + sp * (len(s) - 1)


def ttext_sp(a, s, f, cx, base, col, sp=1.0, alpha=1.0):
    """Letter-spaced TrueType text centred on cx."""
    x = cx - spaced_w(s, f, sp) / 2
    for c in s:
        if c != " ":
            ttext(a, c, f, x, base, col, alpha=alpha)
        x += f.getlength(c) + sp


def G(*rows):
    return list(rows)


# 5-row font for text.bmp (the readouts; the title itself is drawn by the app in TrueType).
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

# 3x5 font for the smallest labels.
TINY = {
    "A": G(".#.", "#.#", "###", "#.#", "#.#"),
    "B": G("##.", "#.#", "##.", "#.#", "##."),
    "D": G("##.", "#.#", "#.#", "#.#", "##."),
    "E": G("###", "#..", "##.", "#..", "###"),
    "H": G("#.#", "#.#", "###", "#.#", "#.#"),
    "I": G("###", ".#.", ".#.", ".#.", "###"),
    "K": G("#.#", "#.#", "##.", "#.#", "#.#"),
    "M": G("#.#", "###", "###", "#.#", "#.#"),
    "N": G("##.", "#.#", "#.#", "#.#", "#.#"),
    "O": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "P": G("##.", "#.#", "##.", "#..", "#.."),
    "R": G("##.", "#.#", "##.", "#.#", "#.#"),
    "S": G(".##", "#..", ".#.", "..#", "##."),
    "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#.#", "#.#", "#.#", "#.#", "###"),
    "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "Z": G("###", "..#", ".#.", "#..", "###"),
    " ": G("..", "..", "..", "..", ".."),
}
for _c in "0123456789+-.":
    TINY[_c] = FONT5[_c]


def glyph_w(fnt, c):
    return len(fnt[c][0])


def ptext_w(fnt, s, gap=1):
    s = [c for c in s if c in fnt]
    return sum(glyph_w(fnt, c) for c in s) + gap * max(0, len(s) - 1)


def ptext(a, fnt, s, x, y, col, gap=1):
    for c in s:
        if c not in fnt:
            continue
        g = fnt[c]
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col)
        x += len(g[0]) + gap
    return x


def ptext_c(a, fnt, s, cx, y, col, gap=1):
    ptext(a, fnt, s, cx - ptext_w(fnt, s, gap) // 2, y, col, gap)


# ------------------------------------------------------------------------------------------
# Pictograms: transport glyphs, the controller's symbols, shuffle/repeat
# ------------------------------------------------------------------------------------------


def icon(a, kind, cx, cy, s, col, alpha=1.0):
    """Transport pictograms centred at (cx, cy) (pixel-edge coordinates); s = half height."""
    if kind == "play":
        poly(a, [(cx - s * 0.8, cy - s), (cx - s * 0.8, cy + s), (cx + s * 0.95, cy)], col, alpha)
    elif kind == "pause":
        bw = max(1.6, s * 0.62)
        frect(a, cx - s * 0.85, cy - s, cx - s * 0.85 + bw, cy + s, col, 0.4, alpha)
        frect(a, cx + s * 0.85 - bw, cy - s, cx + s * 0.85, cy + s, col, 0.4, alpha)
    elif kind == "stop":
        frect(a, cx - s * 0.9, cy - s * 0.9, cx + s * 0.9, cy + s * 0.9, col, s * 0.2, alpha)
    elif kind in ("previous", "next"):
        sg = 1 if kind == "next" else -1
        for ox in (-s * 0.95, 0.0):
            bx = cx + sg * ox - sg * s * 0.25
            poly(a, [(bx, cy - s * 0.8), (bx, cy + s * 0.8), (bx + sg * s * 0.95, cy)], col, alpha)
        ex = cx + sg * s * 0.7
        x0, x1 = (ex, ex + 1.5) if sg == 1 else (ex - 1.5, ex)
        frect(a, x0, cy - s * 0.8, x1, cy + s * 0.8, col, 0.3, alpha)
    elif kind == "eject":
        poly(a, [(cx - s, cy + s * 0.2), (cx + s, cy + s * 0.2), (cx, cy - s * 0.9)], col, alpha)
        frect(a, cx - s, cy + s * 0.5, cx + s, cy + s * 0.5 + 1.6, col, 0.3, alpha)


def symbol(a, kind, cx, cy, r, col, w=1.15, alpha=1.0):
    """One of the controller's symbols (outline), radius r, centred at (cx, cy)."""
    x0, y0 = int(np.floor(cx - r)) - 2, int(np.floor(cy - r)) - 2
    n = int(np.ceil(2 * r)) + 5

    def fn(d, S):
        X = lambda v: (v - x0) * S
        Y = lambda v: (v - y0) * S
        lw = max(1, int(round(w * S)))
        h = w / 2
        if kind == "circle":
            d.ellipse((X(cx - r + h), Y(cy - r + h), X(cx + r - h), Y(cy + r - h)), outline=255, width=lw)
        elif kind == "square":
            k = r * 0.86
            d.rectangle((X(cx - k + h), Y(cy - k + h), X(cx + k - h), Y(cy + k - h)), outline=255, width=lw)
        elif kind == "tri":
            pts = [(cx, cy - r + h * 1.3), (cx + r * 0.98 - h, cy + r * 0.72 - h * 0.6),
                   (cx - r * 0.98 + h, cy + r * 0.72 - h * 0.6)]
            d.polygon([(X(x), Y(y)) for x, y in pts], outline=255, width=lw)
        elif kind == "cross":
            k = r * 0.78
            d.line((X(cx - k), Y(cy - k), X(cx + k), Y(cy + k)), fill=255, width=lw)
            d.line((X(cx - k), Y(cy + k), X(cx + k), Y(cy - k)), fill=255, width=lw)

    paint(a, x0, y0, mask(n, n, fn), col, alpha)


class _Shift:
    """An ImageDraw proxy that offsets every coordinate (so icons can use window coordinates)."""

    def __init__(self, d, dx, dy):
        self.d, self.dx, self.dy = d, dx, dy

    def _p(self, pts):
        if len(pts) == 4 and not isinstance(pts[0], (tuple, list)):
            return (pts[0] + self.dx, pts[1] + self.dy, pts[2] + self.dx, pts[3] + self.dy)
        return [(x + self.dx, y + self.dy) for x, y in pts]

    def line(self, pts, **k):
        self.d.line(self._p(pts), **k)

    def polygon(self, pts, **k):
        self.d.polygon(self._p(pts), **k)

    def arc(self, pts, a0, a1, **k):
        (x0, y0), (x1, y1) = self._p(pts)
        self.d.arc((x0, y0, x1, y1), a0, a1, **k)


def shuffle_icon(a, cx, cy, col):
    def fn(d, S):
        w = 1.25 * S
        L = lambda pts: [((cx - 5.5 + x) * S, (cy - 4 + y) * S) for x, y in pts]
        d.line(L([(0, 6.5), (2.5, 6.5), (6.5, 1.5), (8.5, 1.5)]), fill=255, width=int(w))
        d.line(L([(0, 1.5), (2.5, 1.5), (6.5, 6.5), (8.5, 6.5)]), fill=255, width=int(w))
        d.polygon(L([(8.0, -0.6), (11, 1.5), (8.0, 3.6)]), fill=255)
        d.polygon(L([(8.0, 4.4), (11, 6.5), (8.0, 8.6)]), fill=255)
    x0, y0 = int(cx) - 7, int(cy) - 6
    paint(a, x0, y0, mask(14, 12, lambda d, S: fn(_Shift(d, -x0 * S, -y0 * S), S)), col)


def repeat_icon(a, cx, cy, col):
    def fn(d, S):
        w = 1.25 * S
        L = lambda pts: [((cx - 5.5 + x) * S, (cy - 4 + y) * S) for x, y in pts]
        d.line(L([(2.5, 1.5), (9, 1.5)]), fill=255, width=int(w))
        d.line(L([(8.5, 6.5), (2, 6.5)]), fill=255, width=int(w))
        d.arc(L([(-0.1, 1.5 - 0.6), (5, 6.5 + 0.6)]), 90, 270, fill=255, width=int(w))
        d.arc(L([(6, 1.5 - 0.6), (11.1, 6.5 + 0.6)]), 270, 90, fill=255, width=int(w))
        d.polygon(L([(6.5, -0.7), (9.5, 1.5), (6.5, 3.7)]), fill=255)
        d.polygon(L([(4.5, 4.3), (1.5, 6.5), (4.5, 8.7)]), fill=255)
    x0, y0 = int(cx) - 7, int(cy) - 6
    paint(a, x0, y0, mask(14, 12, lambda d, S: fn(_Shift(d, -x0 * S, -y0 * S), S)), col)


def mini_glyph(a, x, y, kind, col):
    """9x9 titlebar button pictograms."""
    if kind == "options":
        for i in range(3):
            frect(a, x + 2, y + 2 + 2 * i, x + 7, y + 3 + 2 * i, col)
    elif kind == "minimize":
        frect(a, x + 2, y + 6, x + 7, y + 7, col)
    elif kind == "shade":
        frect(a, x + 2, y + 2, x + 7, y + 3, col)
        frect(a, x + 2, y + 5, x + 7, y + 6, col)
    elif kind == "close":
        strokes(a, x, y, 9, 9, lambda d, S: (d.line((2 * S, 2 * S, 7 * S, 7 * S), fill=255, width=int(1.2 * S)),
                                             d.line((2 * S, 7 * S, 7 * S, 2 * S), fill=255, width=int(1.2 * S))),
                col)


def sym_col(kind, on_light=False):
    c = SYM[kind]
    return lerp(c, (0, 0, 0), 0.22) if on_light else c


# ------------------------------------------------------------------------------------------
# Logos
# ------------------------------------------------------------------------------------------


def logo_rgba(name, height=None, width=None, crop=None):
    """A logo SVG as float RGB and alpha arrays, height (or width) px, box-downsampled from 8x."""
    src = os.path.join(HERE, "source", name, "logo.svg")
    os.makedirs(SCRATCH, exist_ok=True)
    big = os.path.join(SCRATCH, f"{name}-big.png")
    subprocess.run(["/usr/bin/rsvg-convert", "-h", "1600", src, "-o", big], check=True)
    im = Image.open(big).convert("RGBA")
    if crop:
        im = im.crop(crop(im))
    k = 8
    if height:
        tw = max(1, round(im.width * height / im.height))
        th = height
    else:
        tw, th = width, max(1, round(im.height * width / im.width))
    im = im.resize((tw * k, th * k), Image.LANCZOS)
    arr = np.asarray(im, np.float32) / 255.0
    rgb, al = arr[..., :3] * arr[..., 3:4], arr[..., 3]
    # box-downsample premultiplied colour, then un-premultiply
    rgb = rgb.reshape(th, k, tw, k, 3).mean((1, 3))
    al = al.reshape(th, k, tw, k).mean((1, 3))
    rgb = np.where(al[..., None] > 1e-4, rgb / np.maximum(al[..., None], 1e-4), 0) * 255
    return rgb, al


def ps2_wordmark_crop(im):
    """The "PS2" letters of the PlayStation 2 logo (not the TM, not the PlayStation 2 line)."""
    al = np.asarray(im)[..., 3]
    H = al.shape[0]
    top = al[: int(H * 0.33)]
    cols = np.where(top.max(0) > 40)[0]
    x0, x1 = cols.min(), cols.max() + 1
    rows = np.where(al[: int(H * 0.6), x0:x1].max(1) > 40)[0]
    return (int(x0), int(rows.min()), int(x1), int(rows.max()) + 1)


def put_logo(a, x, y, rgb, al, alpha=1.0, tint=None):
    col = rgb if tint is None else np.broadcast_to(np.array(tint, np.float32), rgb.shape)
    paint(a, x, y, al, col, alpha)


# ------------------------------------------------------------------------------------------
# Materials: the PS1's grey ABS, the PSone's white, the PS2's black and its browser
# ------------------------------------------------------------------------------------------


def body_column(h):
    if ST() == "ps1":
        return stops_col(h, [(0, "#d3d4d7"), (0.5, "#c6c7ca"), (1, "#b9babe")])
    if ST() == "psone":
        return stops_col(h, [(0, "#fbfbfc"), (0.5, "#f0f1f3"), (1, "#e2e4e8")])
    return stops_col(h, [(0, "#14151a"), (1, "#08090b")])


def ribs(a, x0, x1, rows, lit=True):
    """Moulded ribs (PS1) or grooves (PS2): a light line over a dark one, per row in rows."""
    if x1 <= x0:
        return
    if ST() == "ps1":
        hi, lo = ((238, 239, 241), (140, 142, 147)) if lit else ((228, 229, 231), (166, 168, 172))
    else:
        hi, lo = ((44, 46, 54), (0, 0, 0)) if lit else ((32, 33, 38), (2, 2, 3))
    for r in rows:
        a[r, x0:x1] = lo
        a[r + 1, x0:x1] = hi


def mc_column(h):
    """The PS1 BIOS Memory Card screen: blue at the top fading to black."""
    return stops_col(h, [(0, "#2f4ab8"), (0.5, "#15226a"), (1, "#020309")])


def browser_column(h):
    """The PS2 browser's deep blue."""
    return stops_col(h, [(0, "#020512"), (0.35, "#061748"), (0.7, "#0a2462"), (1, "#030a26")])


TOWER_COL = (70, 140, 255)


def tower(a, x, yb, w, h, alpha):
    """A floating translucent PS2 tower: a front face fading downwards, a side, a lit top."""
    d = w * 0.5
    dy = d * 0.55
    H, W = a.shape[0], a.shape[1]
    # front face, stacked cubes
    fm = mask(W, H, lambda dr, S: dr.rectangle((x * S, (yb - h) * S, (x + w) * S - 1, yb * S - 1), fill=255))
    fade = np.clip(1 - (np.arange(H, dtype=np.float32) - (yb - h)) / max(1, h) * 0.85, 0.12, 1)[:, None]
    paint(a, 0, 0, fm * fade, TOWER_COL, alpha)
    paint(a, 0, 0, mask(W, H, lambda dr, S: dr.polygon(
        [((x + w) * S, (yb - h) * S), ((x + w + d) * S, (yb - h - dy) * S), ((x + w + d) * S, (yb - dy) * S),
         ((x + w) * S, yb * S)], fill=255)) * fade, (40, 90, 210), alpha * 0.8)
    paint(a, 0, 0, mask(W, H, lambda dr, S: dr.polygon(
        [(x * S, (yb - h) * S), ((x + d) * S, (yb - h - dy) * S), ((x + w + d) * S, (yb - h - dy) * S),
         ((x + w) * S, (yb - h) * S)], fill=255)), (170, 210, 255), alpha * 1.6)
    # cube seams
    for k in range(1, int(h // w) + 1):
        yy = yb - h + k * w
        if yy < yb - 1:
            frect(a, x, yy, x + w, yy + 0.6, (150, 200, 255), 0, alpha * 0.9 * fade[min(H - 1, max(0, int(yy))), 0])
    frect(a, x, yb - h, x + 0.7, yb, (160, 205, 255), 0, alpha * 0.8)


def particles(a, rng, n, box, keep_out=(), big=0.15):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if any(k0 - 2 <= y <= k1 + 2 for k0, k1 in keep_out):
            continue
        r = rng.uniform(0.35, 0.8) if rng.random() > big else rng.uniform(0.9, 1.4)
        al = rng.uniform(0.3, 0.9)
        if r > 0.85:
            disc(a, x, y, r * 2.4, (60, 130, 255), al * 0.25)
        disc(a, x, y, r, (200, 228, 255), al)


def boot_orb(a, cx, cy, lit=True):
    """The PS2 boot sequence's swirl of blue particles gathering into a glowing orb."""
    rng = np.random.default_rng(2000)
    blur_glow(a, lambda g: disc(g, cx, cy, 5.0, (255, 255, 255)), (40, 110, 255), 4.0, 1.2, 0.85)
    for i in range(70):
        ang = rng.uniform(0, 2 * np.pi)
        rad = abs(rng.normal(0, 4.8)) + 1.0
        x, y = cx + np.cos(ang) * rad * 1.15, cy + np.sin(ang) * rad
        if abs(x - cx) > 11 or abs(y - cy) > 9.5:
            continue
        disc(a, x, y, rng.uniform(0.3, 0.7), (190, 226, 255), rng.uniform(0.35, 1.0) * max(0.3, 1 - rad / 12))
    disc(a, cx, cy, 2.6, (150, 205, 255), 0.75)
    disc(a, cx, cy, 1.4, (240, 250, 255))


# ------------------------------------------------------------------------------------------
# Bars (titlebars)
# ------------------------------------------------------------------------------------------


def bar_rows(h, lit):
    t = new(1, h)
    if ST() == "ps1":
        hi, top, bot, lo = (("#eeeff1", "#d8d9dc", "#bcbdc1", "#8c8e93") if lit
                            else ("#e8e9eb", "#dcdde0", "#cacbce", "#a2a4a8"))
    elif ST() == "psone":
        hi, top, bot, lo = (("#ffffff", "#fbfbfc", "#e4e7ea", "#b4b9c0") if lit
                            else ("#ffffff", "#f8f9fa", "#eceef0", "#c6cad0"))
    else:
        hi, top, bot, lo = (("#3a3c44", "#1d1e23", "#0b0c0f", "#000000") if lit
                            else ("#2a2b30", "#18191d", "#0c0d10", "#000000"))
    vgrad_fill(t, 0, 0, 1, h, hexc(top), hexc(bot))
    t[0, 0] = hexc(hi)
    t[h - 1, 0] = hexc(lo)
    return t


def bar(w, h, lit):
    return np.repeat(bar_rows(h, lit), w, axis=1).copy()


def title_col(lit):
    if ST() == "ps2":
        return (220, 232, 255) if lit else (110, 120, 140)
    if ST() == "psone":
        return (92, 98, 108) if lit else (170, 175, 182)
    return (60, 62, 68) if lit else (140, 142, 148)


TITLE_SP = {"ps1": 1.2, "psone": 1.4, "ps2": 1.5}


def title_font(size):
    return font(T["font_bold"] if ST() != "ps2" else NOTO.format("Regular"), size)


def bar_title(a, s, cx, base, lit, size=8):
    f = title_font(size)
    ttext_sp(a, s, f, cx, base, title_col(lit), TITLE_SP[ST()])
    return spaced_w(s, f, TITLE_SP[ST()])


def bar_icon_col(lit):
    if ST() == "ps2":
        return (200, 212, 236) if lit else (100, 106, 120)
    if ST() == "psone":
        return (110, 116, 126) if lit else (176, 180, 186)
    return (70, 72, 78) if lit else (140, 142, 148)


def mini_button(a, x, y, kind, lit=True, pressed=False):
    col = bar_icon_col(lit)
    if pressed:
        if ST() == "ps2":
            rrect(a, x, y, 9, 9, 2, (30, 80, 190))
            col = (255, 255, 255)
        elif ST() == "psone":
            rrect(a, x, y, 9, 9, 2, (200, 214, 234))
            col = (47, 104, 176)
        else:
            rrect(a, x, y, 9, 9, 1.5, (150, 152, 157))
            rrect(a, x + 1, y + 1, 8, 8, 1, (176, 178, 182))
            col = (30, 32, 36)
    mini_glyph(a, x, y, kind, col)


# ------------------------------------------------------------------------------------------
# Displays
# ------------------------------------------------------------------------------------------


def display(a, x, y, w, h, line=None):
    """A recessed display; the inner box is exactly the panel colour."""
    if ST() == "ps1":
        rrect(a, x - 2, y - 2, w + 4, h + 4, 3, (236, 237, 239))
        rrect(a, x - 2, y - 2, w + 3, h + 3, 3, (128, 130, 136))
        rrect(a, x - 1, y - 1, w + 2, h + 2, 2, line or T["panel_line"])
    elif ST() == "ps2":
        rrect(a, x - 2, y - 2, w + 4, h + 4, 3, (40, 100, 230), 0.25)
        rrect(a, x - 1, y - 1, w + 2, h + 2, 2, line or T["panel_line"])
    else:
        rrect(a, x - 1, y - 1, w + 2, h + 2, 2, line or T["panel_line"])
    rect(a, x, y, w, h, T["panel"])


def psone_screen(a):
    """The PSone LCD: one dark screen in a white frame holding every display of the main window."""
    W, H = a.shape[1], a.shape[0]

    def shape(grow):
        def fn(d, S):
            g = grow
            d.rounded_rectangle(((20 - g) * S, (18 - g) * S, (105 + g) * S - 1, (63 + g) * S - 1), radius=(3 + g) * S,
                                fill=255)
            d.rounded_rectangle(((20 - g) * S, (18 - g) * S, (270 + g) * S - 1, (56 + g) * S - 1), radius=(3 + g) * S,
                                fill=255)
        return mask(W, H, fn)

    paint(a, 0, 0, shape(2), (214, 218, 224))      # the frame's recess
    paint(a, 0, 0, shape(1), (60, 66, 78))         # the screen's dark border
    paint(a, 0, 0, shape(0), T["panel"])
    sep = lerp(T["panel"], (120, 150, 200), 0.22)
    rect(a, 105, 19, 1, 37, sep)
    rect(a, 106, 37, 164, 1, sep)
    # the screen's top-edge sheen
    rect(a, 23, 18, 244, 1, lerp(T["panel"], (255, 255, 255), 0.1))


# ------------------------------------------------------------------------------------------
# Backgrounds (main and EQ windows); sprites copy theirs from these
# ------------------------------------------------------------------------------------------

MAINBG = None
EQBG = None


def at(src, x, y, w, h):
    return src[y:y + h, x:x + w].copy()


def frame_edges(a):
    w, h = a.shape[1], a.shape[0]
    if ST() == "ps1":
        rect(a, 0, 0, 1, h, (140, 142, 147))
        rect(a, w - 1, 0, 1, h, (120, 122, 127))
        rect(a, 0, h - 1, w, 1, (120, 122, 127))
        rect(a, 1, 14, 1, h - 15, (232, 233, 235))
    elif ST() == "psone":
        rect(a, 0, 0, 1, h, (176, 181, 188))
        rect(a, w - 1, 0, 1, h, (176, 181, 188))
        rect(a, 0, h - 1, w, 1, (160, 165, 172))
        rect(a, 1, 14, 1, h - 15, (255, 255, 255))
    else:
        rect(a, 0, 0, 1, h, (0, 0, 0))
        rect(a, w - 1, 0, 1, h, (0, 0, 0))
        rect(a, 0, h - 1, w, 1, (0, 0, 0))


def ps2_body(w, h, towers, seed, keep_out=()):
    a = np.repeat(browser_column(h), w, axis=1).copy()
    rng = np.random.default_rng(seed)
    particles(a, rng, 70, (1, 14, w - 1, h - 1), keep_out)
    for x, yb, tw, th, al in towers:
        tower(a, x, yb, tw, th, al)
    return a


def band(a, x, y, w, h):
    """PS1: the darker grey recess of the console's front, behind the transport."""
    rrect(a, x, y, w, h, 4, (236, 237, 239))
    rrect(a, x, y, w - 1, h - 1, 4, (126, 128, 133))
    grad_rrect(a, x + 1, y + 1, w - 2, h - 2, 3, (160, 162, 167), (176, 178, 182))


def grille(a, x0, x1, y0, rows=2, step=3):
    for r in range(rows):
        for x in range(x0 + (r % 2) * (step // 2 + 0), x1, step):
            disc(a, x + 0.5, y0 + r * 3 + 0.5, 0.75, (150, 156, 164))


def make_main_bg():
    keep = [(55, 84)]
    if ST() == "ps2":
        a = ps2_body(275, 116, [(3, 114, 7, 26, 0.3), (150, 116, 5, 30, 0.24), (232, 113, 6, 24, 0.28),
                                (266, 50, 4, 32, 0.22), (2, 52, 5, 30, 0.2)], 7, keep)
        # keep the rows the sliders' thumbs travel along uniform
        a[55:85, 1:274] = browser_column(116)[55:85, 0][:, None, :]
    else:
        a = np.repeat(body_column(116), 275, axis=1).copy()
    frame_edges(a)

    if ST() == "psone":
        psone_screen(a)
    else:
        display(a, 21, 20, 84, 42)
        display(a, 109, 21, 159, 15)
        display(a, 109, 40, 159, 14)
    for yy in (29, 34):
        disc(a, 74, yy + 1, 1.1, T["ink"])
    lab = lerp(T["panel"], T["ink"], 0.5)
    ptext(a, TINY, "KBPS", 129, 44, lab)
    ptext(a, TINY, "KHZ", 169, 44, lab)

    # seek rail
    if ST() == "ps1":
        rect(a, 16, 74, 248, 1, (110, 112, 118))
        rect(a, 16, 75, 248, 4, (46, 48, 54))
        rect(a, 16, 79, 248, 1, (236, 237, 239))
    elif ST() == "psone":
        frect(a, 12, 75, 268, 79, (176, 182, 190), 2)
        frect(a, 13, 76, 267, 78, (214, 218, 224), 1)
    else:
        rect(a, 16, 76, 248, 1, (44, 98, 204))
        rect(a, 16, 77, 248, 1, (14, 40, 100))

    # the front: transport recess (PS1), speaker grille (PSone)
    if ST() == "ps1":
        band(a, 13, 85, 149, 24)
        band(a, 162, 86, 80, 22)
        ribs(a, 13, 242, (110, 113))
    elif ST() == "psone":
        grille(a, 18, 158, 109)
        grille(a, 165, 238, 109)

    # the emblem in the About spot (253, 91, 13 x 15)
    if ST() == "ps2":
        boot_orb(a, 259.5, 98.5)
    else:
        rgb, al = logo_rgba(T["logo"], height=18)
        lw = al.shape[1]
        put_logo(a, int(round(259.5 - lw / 2)), 90, rgb, al)
    return a


def make_eq_bg():
    if ST() == "ps2":
        a = ps2_body(275, 116, [(4, 104, 6, 34, 0.28), (204, 34, 5, 16, 0.22), (264, 112, 5, 40, 0.28),
                                (70, 112, 4, 12, 0.2)], 11, [(103, 113)])
        frame_edges(a)
        display(a, 85, 16, 115, 21)
        display(a, 16, 36, 245, 68)
    elif ST() == "ps1":
        a = np.repeat(body_column(116), 275, axis=1).copy()
        # the Memory Card screen inside a grey ABS frame
        inner = np.repeat(mc_column(98), 269, axis=1)
        a[14:112, 3:272] = inner
        rect(a, 3, 14, 269, 1, (120, 122, 127))
        rect(a, 2, 14, 1, 99, (120, 122, 127))
        rect(a, 3, 112, 269, 1, (236, 237, 239))
        rect(a, 272, 14, 1, 99, (236, 237, 239))
        frame_edges(a)
        mcl = (196, 202, 222)
        rect(a, 84, 15, 117, 23, mcl)
        rect(a, 15, 35, 247, 70, mcl)
        rect(a, 85, 16, 115, 21, T["panel"])
        rect(a, 16, 36, 245, 68, T["panel"])
    else:
        a = np.repeat(body_column(116), 275, axis=1).copy()
        frame_edges(a)
        display(a, 85, 16, 115, 21, (60, 66, 78))
        display(a, 16, 36, 245, 68, (60, 66, 78))
    return a


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]
CLUTTER_COL = {"O": SYM["circle"], "A": SYM["tri"], "I": SYM["cross"], "D": SYM["square"], "V": LOGO_YELLOW}


def clutter_bar(lit_letters):
    a = at(MAINBG, 10, 22, 8, 43)
    if ST() == "ps1":
        # a slot like the controller ports: dark, recessed
        rrect(a, 0, 0, 8, 43, 2, (236, 237, 239))
        rrect(a, 0, 0, 7, 42, 2, (110, 112, 118))
        rrect(a, 1, 1, 6, 41, 1.5, (52, 54, 60))
        off = (128, 131, 138)
    elif ST() == "psone":
        rrect(a, 0, 0, 8, 43, 3, (196, 201, 208))
        rrect(a, 1, 1, 6, 41, 2, (246, 247, 248))
        off = (170, 175, 182)
    else:
        rrect(a, 0, 0, 8, 43, 2, T["panel_line"], 0.8)
        rrect(a, 1, 1, 6, 41, 1.5, T["panel"])
        off = T["text3"]
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        c = CLUTTER_COL[letter]
        gy = y + (h - 5) // 2
        if on:
            if ST() == "psone":
                rrect(a, 1, y, 6, h, 1.5, lerp(c, (255, 255, 255), 0.75))
                ptext(a, TINY, letter, 2, gy, lerp(c, (0, 0, 0), 0.3))
            else:
                rrect(a, 1, y, 6, h, 1.5, lerp(c, (0, 0, 0), 0.55))
                ptext(a, TINY, letter, 2, gy, lerp(c, (255, 255, 255), 0.35))
        else:
            ptext(a, TINY, letter, 2, gy, off)
    return a


def ps2_logo_cells():
    if "ps2logo" not in T:
        T["ps2logo"] = logo_rgba("logo-ps2", height=10, crop=ps2_wordmark_crop)
    return T["ps2logo"]


def main_titlebar(lit):
    a = bar(275, 14, lit)
    rows = (4, 7, 10)
    if ST() == "ps2":
        rgb, al = ps2_logo_cells()
        lw = al.shape[1]
        x0 = int(round(137.5 - lw / 2))
        if lit:
            # lift the logo's darker blues a little so they read on the black
            put_logo(a, x0, 2, rgb + (255 - rgb) * 0.3, al)
        else:
            put_logo(a, x0, 2, rgb, al, tint=(100, 108, 126))
        ribs(a, 18, x0 - 8, rows, lit)
        ribs(a, x0 + lw + 8, 238, rows, lit)
    elif ST() == "psone":
        # "PS" bold and "one" light, the PSone's own lettering
        fb, fl = font(NOTO.format("Bold"), 10), font(NOTO.format("Light"), 10)
        wb, wl = fb.getlength("PS"), fl.getlength("one")
        x = 137.5 - (wb + wl + 0.5) / 2
        ttext(a, "PS", fb, x, 11, title_col(lit))
        ttext(a, "one", fl, x + wb + 0.5, 11, title_col(lit))
    else:
        tw = bar_title(a, T["title"], 137.5, 10, lit, 8)
        ribs(a, 18, int(137.5 - tw / 2) - 8, rows, lit)
        ribs(a, int(137.5 + tw / 2) + 9, 238, rows, lit)
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, T["bg"])
    for kind, x in [("options", 0), ("minimize", 9), ("close", 18)]:
        for pressed, y in ((False, 0), (True, 9)):
            b = bar(9, 14, True)[3:12].copy()
            mini_button(b, 0, 0, kind, True, pressed)
            a[y:y + 9, x:x + 9] = b
    for pressed, x in ((False, 0), (True, 9)):
        b = bar(9, 14, True)[3:12].copy()
        mini_button(b, 0, 0, "shade", True, pressed)
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
# main.bmp (275 x 116)
# ------------------------------------------------------------------------------------------

SEEK_Y = 72


def make_main():
    global MAINBG
    MAINBG = make_main_bg()
    a = MAINBG.copy()
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36): round buttons, the glyphs in the controller's symbol colours
# ------------------------------------------------------------------------------------------


def glyph_col(kind, pressed):
    if kind == "eject":
        if ST() == "ps2":
            return (200, 206, 218)
        return (78, 80, 86) if ST() == "ps1" else (120, 126, 136)
    c = SYM[GLYPH_SYM[kind]]
    if ST() == "ps1":
        return lerp(c, (0, 0, 0), 0.25)
    if ST() == "psone":
        return lerp(c, (0, 0, 0), 0.12)
    return lerp(c, (255, 255, 255), 0.25) if pressed else c


GLYPH_S = {"play": 4.2, "pause": 3.4, "stop": 3.1, "previous": 3.4, "next": 3.4, "eject": 3.2}


def round_button(a, kind, cx, cy, r, pressed):
    s = GLYPH_S[kind] * (r / 8.0)
    o = 0.5 if pressed else 0.0
    gx = cx + (0.6 if kind == "play" else 0) + o
    if ST() == "ps1":
        # grey ABS discs like the CD player's, set into the darker front
        disc(a, cx, cy + 0.6, r + 0.9, (236, 237, 239), 0.8)
        disc(a, cx, cy, r + 0.8, (96, 98, 104))
        top, bot = ((222, 223, 226), (176, 178, 183)) if not pressed else ((168, 170, 175), (200, 201, 205))
        grad_disc(a, cx, cy, r, top, bot)
        if not pressed:
            ellipse(a, cx, cy - r * 0.45, r * 0.6, r * 0.32, (255, 255, 255), 0.45)
        icon(a, kind, gx, cy + o, s, glyph_col(kind, pressed))
    elif ST() == "psone":
        disc(a, cx, cy + 0.8, r + 0.8, (0, 0, 0), 0.10)
        disc(a, cx, cy, r + 0.6, (184, 189, 196))
        top, bot = ((255, 255, 255), (226, 229, 233)) if not pressed else ((220, 224, 230), (240, 242, 245))
        grad_disc(a, cx, cy, r, top, bot)
        icon(a, kind, gx, cy + o, s, glyph_col(kind, pressed))
    else:
        # glossy black DualShock 2 buttons
        disc(a, cx, cy + 0.6, r + 1.0, (0, 0, 0), 0.6)
        disc(a, cx, cy, r + 0.6, (58, 62, 72))
        top, bot = ((44, 46, 54), (6, 6, 8)) if not pressed else ((20, 22, 28), (10, 10, 12))
        grad_disc(a, cx, cy, r, top, bot)
        ellipse(a, cx, cy - r * 0.5, r * 0.62, r * 0.3, (255, 255, 255), 0.10 if pressed else 0.2)
        col = glyph_col(kind, pressed)
        if pressed:
            blur_glow(a, lambda g: icon(g, kind, gx, cy + o, s, (255, 255, 255)), col, 2.0, 2.0, 0.8)
        icon(a, kind, gx, cy + o, s, col)


CB_POS = {"previous": (16, 88), "play": (39, 88), "pause": (62, 88), "stop": (85, 88), "next": (108, 88)}


def transport_cell(kind, w, h, pressed):
    x, y = CB_POS.get(kind, (136, 89))
    a = at(MAINBG, x, y, w, h)
    r = 7.8 if h == 18 else 6.8
    round_button(a, kind, w / 2, h / 2, r, pressed)
    return a


def make_cbuttons():
    a = new(136, 36, T["bg"])
    specs = [("previous", 0, 23), ("play", 23, 23), ("pause", 46, 23), ("stop", 69, 23), ("next", 92, 22)]
    for kind, x, w in specs:
        for pressed, y in ((False, 0), (True, 18)):
            a[y:y + 18, x:x + w] = transport_cell(kind, w, 18, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        a[y:y + 16, 114:136] = transport_cell("eject", 22, 16, pressed)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def keycap(a, x, y, w, h, on, pressed):
    """A rectangular key: PS1 grey (like RESET/POWER), PSone white, PS2 a browser box."""
    if ST() == "ps1":
        rrect(a, x, y, w, h, 2.5, (96, 98, 104))
        top, bot = ((226, 227, 230), (184, 186, 190)) if not pressed else ((170, 172, 177), (196, 198, 202))
        grad_rrect(a, x + 1, y + 1, w - 2, h - 2, 2, top, bot)
        if not pressed:
            rect(a, x + 2, y + 1, w - 4, 1, (244, 245, 246))
    elif ST() == "psone":
        rrect(a, x, y, w, h, h / 2, (186, 191, 198))
        top, bot = ((255, 255, 255), (230, 233, 237)) if not pressed else ((222, 226, 232), (242, 244, 246))
        if on:
            top, bot = (236, 243, 252), (208, 222, 242)
        grad_rrect(a, x + 1, y + 1, w - 2, h - 2, h / 2 - 1, top, bot)
    else:
        rrect(a, x, y, w, h, 2.5, (60, 120, 240), 0.95 if on else 0.55)
        fill_top, fill_bot = ((30, 84, 200), (12, 40, 120)) if on else ((10, 22, 58), (4, 10, 30))
        if pressed:
            fill_top, fill_bot = lerp(fill_top, (255, 255, 255), 0.12), lerp(fill_bot, (255, 255, 255), 0.08)
        grad_rrect(a, x + 1, y + 1, w - 2, h - 2, 1.5, fill_top, fill_bot)
        if on:
            rect(a, x + 2, y + 1, w - 4, 1, (120, 180, 255))


def led(a, cx, cy, on):
    """The PS1's green power LED."""
    if on:
        disc(a, cx, cy, 2.4, (90, 255, 110), 0.25)
        grad_disc(a, cx, cy, 1.5, (200, 255, 190), (40, 200, 60))
    else:
        disc(a, cx, cy, 1.5, (70, 90, 72))


def toggle_icon_cell(kind, w, on, pressed):
    x0 = 164 if kind == "shuffle" else 210
    a = at(MAINBG, x0, 89, w, 15)
    fn = shuffle_icon if kind == "shuffle" else repeat_icon
    o = 0.5 if pressed else 0.0
    keycap(a, 1, 1, w - 2, 13, on, pressed)
    if ST() == "ps1":
        led(a, 6.5 + o, 7.5 + o, on)
        fn(a, w / 2 + 3 + o, 7.5 + o, (60, 62, 68) if on else (110, 112, 118))
    elif ST() == "psone":
        fn(a, w / 2 + o, 7.5 + o, (47, 104, 176) if on else (130, 136, 146))
    else:
        if on:
            blur_glow(a, lambda g: fn(g, w / 2, 7.5, (255, 255, 255)), (120, 190, 255), 1.6, 1.4, 0.6)
        fn(a, w / 2 + o, 7.5 + o, (255, 255, 255) if on else (110, 140, 196))
    return a


def text_toggle(a, x, y, w, h, txt, on, pressed):
    """EQ/PL and ON/AUTO: a key with its controller symbol, coloured when on."""
    keycap(a, x, y, w, h, on, pressed)
    o = 0.5 if pressed else 0.0
    sk = TOGGLE_SYM.get(txt)
    f = font(NOTO.format("CondensedSemiBold" if ST() != "ps2" else "CondensedMedium"), 7)
    if ST() == "ps1":
        lab = (50, 52, 58) if on else (104, 106, 112)
        soff = (150, 152, 158)
    elif ST() == "psone":
        lab = (60, 66, 76) if on else (130, 136, 146)
        soff = (190, 194, 200)
    else:
        lab = (255, 255, 255) if on else (120, 148, 200)
        soff = (60, 84, 140)
    if sk:
        symbol(a, sk, x + 5.5 + o, y + h / 2 + o, 2.7, (sym_col(sk, ST() != "ps2") if on else soff), 1.1)
        ttext(a, txt, f, x + 9 + (w - 10) / 2 + o, y + h - 3.0 + o, lab, "c")
    else:
        ttext(a, txt, font(T["font_bold"], 7), x + w / 2 + o, y + h - 3.0 + o, lab, "c")


def make_shufrep():
    a = new(92, 85, T["bg"])
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = toggle_icon_cell("repeat", 28, on, pressed)
        a[y:y + 15, 28:75] = toggle_icon_cell("shuffle", 47, on, pressed)
    for x, txt, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        dst = 219 if txt == "EQ" else 242
        for on, y in ((False, 61), (True, 73)):
            cell = at(MAINBG, dst, 58, 23, 12)
            text_toggle(cell, 0, 0, 22, 12, txt, on, pressed)
            a[y:y + 12, x:x + 23] = cell
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T["panel"])
    for y, on in ((0, True), (12, False)):
        col = T["ink"] if on else lerp(T["panel"], T["ink"], 0.22)
        ptext_c(a, TINY, "STEREO", 14, y + 4, col)
        ptext_c(a, TINY, "MONO", 29 + 13, y + 4, col)
    return a


def make_playpaus():
    a = new(48, 9, T["panel"])
    icon(a, "play", 4.6, 4.5, 3.4, SYM["tri"])
    icon(a, "pause", 9 + 4.5, 4.5, 3.2, SYM["circle"])
    icon(a, "stop", 18 + 4.5, 4.5, 3.0, SYM["square"])
    disc(a, 39 + 1.5, 4.5, 1.0, lerp(T["panel"], T["ink"], 0.4))
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["panel"])
    f = font(T["digit_font"], 14)
    for n in range(10):
        ttext(a, str(n), f, 9 * n + 4.5, 12, T["ink"], "c")
    if ex:
        frect(a, 99 + 2, 6, 99 + 7, 7.4, T["ink"])
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, T["panel"])
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            k = ch if ch in FONT5 else ch.upper()
            ptext(a, FONT5, k, col * 5, row * 6, T["ink"])
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------

FILL = {"ps1": (50, 109, 179), "psone": (79, 134, 208), "ps2": (90, 170, 255)}


def ps1_knob(a, x, y, w, h, selected):
    """A grey ABS slider knob with moulded grip lines."""
    rrect(a, x, y, w, h, 1.5, (84, 86, 92))
    top, bot = ((236, 237, 239), (184, 186, 190)) if not selected else ((206, 208, 212), (170, 172, 177))
    grad_rrect(a, x + 1, y + 1, w - 2, h - 2, 1, top, bot)
    cx = x + w // 2
    for gx in (cx - 2, cx, cx + 2):
        rect(a, gx, y + 2, 1, h - 4, (130, 132, 138))


def diamond(a, cx, cy, r, col, alpha=1.0):
    poly(a, [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], col, alpha)


def seek_thumb(selected):
    a = at(MAINBG, 120, SEEK_Y, 29, 10)
    if ST() == "ps1":
        ps1_knob(a, 8, 0, 13, 10, selected)
        rect(a, 14, 2, 1, 6, FILL["ps1"])
    elif ST() == "psone":
        disc(a, 14.5, 5.3, 4.6, (0, 0, 0), 0.12)
        disc(a, 14.5, 5.0, 4.5, (170, 176, 184))
        grad_disc(a, 14.5, 5.0, 3.8, (255, 255, 255), (226, 229, 233) if not selected else (206, 214, 226))
        disc(a, 14.5, 5.0, 1.3, FILL["psone"])
    else:
        for x in range(0, 24):
            t = x / 23
            a[4, x] = lerp(a[4, x], (140, 200, 255), t * t)
        diamond(a, 24.5, 4.5, 6.0, (60, 130, 255), 0.35 if not selected else 0.55)
        diamond(a, 24.5, 4.5, 3.8, (230, 244, 255))
    return a


def make_posbar(main):
    a = new(307, 10, T["bg"])
    a[0:10, 0:248] = MAINBG[SEEK_Y:SEEK_Y + 10, 16:264]
    a[0:10, 248:277] = seek_thumb(False)
    a[0:10, 278:307] = seek_thumb(True)
    a[0:10, 277] = MAINBG[SEEK_Y:SEEK_Y + 10, 140]
    return a


def h_rail(t, x0, x1, fill_from=None, fill_to=None):
    """A slider rail on a 15-row frame (the thumb's rows are 1..11), filled from fill_from to fill_to."""
    fc = FILL[ST()]
    if ST() == "ps1":
        rect(t, x0, 4, x1 - x0, 1, (110, 112, 118))
        rect(t, x0, 5, x1 - x0, 3, (46, 48, 54))
        rect(t, x0, 8, x1 - x0, 1, (236, 237, 239))
        if fill_to is not None:
            f0 = x0 if fill_from is None else fill_from
            if fill_to - f0 >= 1:
                frect(t, f0, 5, fill_to, 8, fc)
                frect(t, f0, 5, fill_to, 6, lerp(fc, (255, 255, 255), 0.35))
    elif ST() == "psone":
        frect(t, x0, 4.5, x1, 8.5, (176, 182, 190), 2)
        frect(t, x0 + 1, 5.5, x1 - 1, 7.5, (214, 218, 224), 1)
        if fill_to is not None:
            f0 = (x0 + 1) if fill_from is None else fill_from
            if fill_to - f0 >= 1:
                frect(t, f0, 5.5, fill_to, 7.5, fc, 1)
    else:
        frect(t, x0, 6, x1, 7, (44, 98, 204))
        if fill_to is not None:
            f0 = x0 if fill_from is None else fill_from
            if fill_to - f0 >= 1:
                frect(t, f0, 5.4, fill_to, 7.6, fc)
                frect(t, f0, 4.4, fill_to, 8.6, fc, 0, 0.25)


def slider_thumb(selected):
    t = at(MAINBG, 120, 58, 14, 11)
    if ST() == "ps1":
        ps1_knob(t, 2, 0, 10, 11, selected)
    elif ST() == "psone":
        disc(t, 7, 5.8, 5.0, (0, 0, 0), 0.12)
        disc(t, 7, 5.5, 4.9, (170, 176, 184))
        grad_disc(t, 7, 5.5, 4.2, (255, 255, 255), (226, 229, 233) if not selected else (206, 214, 226))
        disc(t, 7, 5.5, 1.3, FILL["psone"])
    else:
        diamond(t, 7, 5.5, 5.5, (60, 130, 255), 0.35 if not selected else 0.55)
        diamond(t, 7, 5.5, 3.6, (230, 244, 255))
    return t


def slider_thumbs(a):
    a[422:433, 0:14] = slider_thumb(True)
    a[422:433, 15:29] = slider_thumb(False)


def make_volume():
    a = new(68, 433, T["bg"])
    for i in range(28):
        y = i * 15
        t = at(MAINBG, 107, 57, 68, 15)
        level = (i + 1) / 28
        h_rail(t, 3, 65, None, 7 + round(level * 54))
        a[y:y + 15, 0:68] = t
    slider_thumbs(a)
    return a


def make_balance():
    a = new(68, 433, T["bg"])
    for i in range(28):
        y = i * 15
        t = new(68, 15, T["bg"])
        t[:, 9:47] = at(MAINBG, 177, 57, 38, 15)
        reach = round(14 * i / 27)
        h_rail(t, 11, 45)
        if reach:
            h_rail_fill = FILL[ST()]
            if ST() == "ps2":
                frect(t, 28 - reach, 5.4, 28 + reach, 7.6, h_rail_fill)
            elif ST() == "ps1":
                frect(t, 28 - reach, 5, 28 + reach, 8, h_rail_fill)
            else:
                frect(t, 28 - reach, 5.5, 28 + reach, 7.5, h_rail_fill, 1)
        mark = {"ps1": (70, 72, 78), "psone": (138, 144, 154), "ps2": (160, 190, 240)}[ST()]
        frect(t, 27.5, 1.5, 28.5, 3.5, mark)
        a[y:y + 15, 0:68] = t
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = bar(275, 14, lit)
    tw = bar_title(a, T["eq_title"], 137.5, 10, lit, 8)
    if ST() != "psone":
        ribs(a, 8, int(137.5 - tw / 2) - 8, (4, 7, 10), lit)
        ribs(a, int(137.5 + tw / 2) + 9, 258, (4, 7, 10), lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_fill(v):
    return FILL[ST()] if ST() != "ps2" else (110, 184, 255)


def eq_slider_frame(a, x, y, n):
    rect(a, x, y, 14, 63, T["panel"])
    v = n / 27
    centre = (1 - v) * 51 + 6.0
    zero = 31.5
    lo, hi = min(centre, zero), max(centre, zero)
    track = lerp(T["panel"], T["ink"], 0.22)
    frect(a, x + 6.5, y + 3, x + 7.5, y + 60, track)
    for yy in (3, 31, 59):
        frect(a, x + 4.5, y + yy, x + 9.5, y + yy + 1, track)
    if hi - lo >= 0.5:
        c = eq_fill(v)
        if ST() == "ps2":
            frect(a, x + 5, y + lo, x + 9, y + hi, c, 0, 0.3)
        frect(a, x + 6, y + lo, x + 8, y + hi, c)


def eq_thumb(selected):
    t = new(11, 11, T["panel"])
    if ST() == "ps1":
        ps1_knob(t, 0, 2, 11, 7, selected)
    elif ST() == "psone":
        disc(t, 5.5, 5.5, 4.9, (120, 128, 140))
        grad_disc(t, 5.5, 5.5, 4.2, (255, 255, 255), (220, 224, 230) if not selected else (196, 206, 222))
        disc(t, 5.5, 5.5, 1.3, FILL["psone"])
    else:
        diamond(t, 5.5, 5.5, 5.4, (60, 130, 255), 0.35 if not selected else 0.55)
        diamond(t, 5.5, 5.5, 3.6, (230, 244, 255))
    return t


def make_eqmain():
    global EQBG
    EQBG = make_eq_bg()
    a = new(275, 315, T["bg"])
    a[0:116] = EQBG
    a[0:14, :] = eq_titlebar(True)
    rect(a, 40, 40, 1, 60, lerp(T["panel"], T["ink"], 0.15))
    for lbl, yy in (("+12DB", 41), ("+0DB", 67), ("-12DB", 92)):
        ptext_c(a, TINY, lbl, 58, yy, T["plab"])
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    ptext_c(a, TINY, "PREAMP", 28, 106, T["blab"])
    for i, lbl in enumerate(EQ_BANDS):
        ptext_c(a, TINY, lbl, 78 + 18 * i + 7, 106, T["blab"])

    b = bar(9, 14, True)[3:12].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = b
    for x, txt, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if txt == "ON" else 32
        cell = at(EQBG, 14 if txt == "ON" else 40, 18, w, 12)
        text_toggle(cell, 1, 0, w - 2, 12, txt, on, pressed)
        a[119:131, x:x + w] = cell
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    a[164:175, 0:11] = eq_thumb(False)
    a[176:187, 0:11] = eq_thumb(True)
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        cell = at(EQBG, 217, 18, 44, 12)
        text_toggle(cell, 0, 0, 44, 12, "PRESETS", False, pressed)
        a[y:y + 12, 224:268] = cell
    # graph
    rect(a, 0, 294, 113, 19, T["panel"])
    rect(a, 0, 294 + 9, 113, 1, lerp(T["panel"], T["ink"], 0.15))
    for x in range(0, 113, 12):
        for y in range(0, 19, 3):
            px(a, x, 294 + y, lerp(T["panel"], T["ink"], 0.12))
    stops = {"ps1": [hexc("#de0029"), hexc("#f3c202"), hexc("#00aa9e"), hexc("#326db3")],
             "psone": [(200, 224, 255), (120, 168, 230), (60, 110, 190)],
             "ps2": [(255, 255, 255), (150, 210, 255), (70, 140, 255)]}[ST()]
    for r in range(19):
        px(a, 115, 294 + r, ramp(stops, r / 18))
    for x in range(113):
        px(a, x, 314, lerp(T["panel"], T["ink"], 0.4) if x % 3 != 2 else T["panel"])
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

BAR20_RIBS = (6, 9, 12)


def ribbed():
    return ST() in ("ps1", "ps2")


def frame_side(w, h, left):
    t = new(w, h)
    if ST() == "ps1":
        t[:, :] = (198, 199, 202)
        if left:
            rect(t, 0, 0, 1, h, (140, 142, 147))
            rect(t, 1, 0, 1, h, (232, 233, 235))
            rect(t, w - 1, 0, 1, h, (120, 122, 127))
        else:
            rect(t, w - 1, 0, 1, h, (120, 122, 127))
            rect(t, 1, 0, 1, h, (236, 237, 239))
    elif ST() == "psone":
        t[:, :] = (240, 241, 243)
        if left:
            rect(t, 0, 0, 1, h, (176, 181, 188))
            rect(t, 1, 0, 1, h, (255, 255, 255))
            rect(t, w - 1, 0, 1, h, (206, 210, 216))
        else:
            rect(t, w - 1, 0, 1, h, (176, 181, 188))
            rect(t, 0, 0, 1, h, (206, 210, 216))
    else:
        t[:, :] = (14, 15, 19)
        for gx in range(2, w - 1, 3):
            rect(t, gx, 0, 1, h, (4, 4, 6))
            rect(t, gx + 1, 0, 1, h, (30, 32, 38))
        rect(t, w - 1 if left else 0, 0, 1, h, (30, 70, 150))
        rect(t, 0 if left else w - 1, 0, 1, h, (0, 0, 0))
    return t


def bottom_strip(w, h):
    t = new(w, h)
    if ST() == "ps1":
        t[:, :] = stops_col(h, [(0, "#d0d1d4"), (1, "#b6b7bb")])
        rect(t, 0, 0, w, 1, (120, 122, 127))
        rect(t, 0, 1, w, 1, (236, 237, 239))
        rect(t, 0, h - 1, w, 1, (120, 122, 127))
    elif ST() == "psone":
        t[:, :] = stops_col(h, [(0, "#f8f9fa"), (1, "#e2e4e8")])
        rect(t, 0, 0, w, 1, (206, 210, 216))
        rect(t, 0, h - 1, w, 1, (160, 165, 172))
    else:
        t[:, :] = stops_col(h, [(0, "#18191e"), (1, "#060608")])
        rect(t, 0, 0, w, 1, (30, 70, 150))
        rect(t, 0, 1, w, 1, (40, 42, 48))
    return t


def pill_button(t, x, y, w, h, txt):
    keycap(t, x, y, w, h, False, False)
    col = {"ps1": (60, 62, 68), "psone": (92, 98, 108), "ps2": (190, 210, 245)}[ST()]
    if txt:
        ttext(t, txt, font(T["font_bold"], 7), x + w / 2, y + h // 2 + 3, col, "c")


def readout(t, x, y, w, h):
    if ST() == "ps1":
        rrect(t, x - 1, y - 1, w + 2, h + 2, 1.5, (100, 102, 108))
    else:
        rrect(t, x - 1, y - 1, w + 2, h + 2, 2, T["panel_line"] if ST() == "ps2" else (60, 66, 78))
    rect(t, x, y, w, h, T["panel"])


def cd_icon(a, cx, cy, col, bg):
    disc(a, cx, cy, 4.2, col)
    disc(a, cx, cy, 1.4, bg)


def pl_title_tile(lit):
    t = bar(100, 20, lit)
    s = T["pl_title"]
    f = title_font(8)
    tw = spaced_w(s, f, TITLE_SP[ST()])
    cx = 50 + (5 if ST() == "ps1" else 0)
    bar_title(t, s, cx, 13, lit)
    if ST() == "ps1":
        cd_icon(t, cx - tw / 2 - 8, 9.5, title_col(lit), tuple(bar_rows(20, lit)[9, 0]))
    if ribbed():
        x0 = int(cx - tw / 2) - (16 if ST() == "ps1" else 6)
        x1 = int(cx + tw / 2) + 6
        ribs(t, 0, max(0, x0), BAR20_RIBS, lit)
        ribs(t, min(100, x1), 100, BAR20_RIBS, lit)
    return t


def bar20(w, lit, rib=True, rx0=0, rx1=None):
    t = bar(w, 20, lit)
    if rib and ribbed():
        ribs(t, rx0, w if rx1 is None else rx1, BAR20_RIBS, lit)
    return t


def scroll_groove():
    return {"ps1": (52, 54, 60), "psone": (224, 227, 231), "ps2": (6, 16, 46)}[ST()]


def make_pledit():
    a = new(280, 186, T["bg"])
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar20(25, lit)
        a[y:y + 20, 0:25] = bar20(25, lit, rx0=4)
        a[y:y + 20, 26:126] = pl_title_tile(lit)
        t = bar20(25, lit, rx1=12)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    a[42:71, 0:12] = frame_side(12, 29, True)
    t = frame_side(20, 29, False)
    rect(t, 5, 0, 8, 29, scroll_groove())
    a[42:71, 31:51] = t
    b = bar(9, 20, True)[3:12].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = b
    for x, sel in ((52, False), (61, True)):
        t = new(8, 18, scroll_groove())
        if ST() == "ps1":
            ps1_knob(t, 0, 0, 8, 18, sel)
            rect(t, 2, 2, 4, 14, (0, 0, 0))
            for gy in (6, 8, 10, 12):
                rect(t, 1, gy, 6, 1, (130, 132, 138))
            grad_rrect(t, 1, 1, 6, 16, 1, (236, 237, 239) if not sel else (206, 208, 212), (184, 186, 190))
            for gy in (6, 8, 10):
                rect(t, 2, gy, 4, 1, (130, 132, 138))
        elif ST() == "psone":
            frect(t, 1.5, 1, 6.5, 17, (160, 168, 178) if not sel else FILL["psone"], 2.5)
        else:
            frect(t, 1, 1, 7, 17, (60, 130, 255), 1.5, 0.35)
            frect(t, 2.5, 2, 5.5, 16, (200, 228, 255) if sel else (120, 170, 240), 1.5)
        a[53:71, x:x + 8] = t

    # bottom
    edge = {"ps1": (140, 142, 147), "psone": (176, 181, 188), "ps2": (0, 0, 0)}[ST()]
    t = bottom_strip(125, 38)
    rect(t, 0, 0, 1, 38, edge)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        pill_button(t, bx, 9, 22, 16, lbl)
    a[72:110, 0:125] = t

    t = bottom_strip(150, 38)
    rect(t, 149, 0, 1, 38, edge)
    readout(t, 6, 9, 56, 8)
    gcol = {"ps1": (70, 72, 78), "psone": (110, 116, 126), "ps2": (190, 210, 245)}[ST()]
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        c = gcol
        if kind in GLYPH_SYM and ST() != "psone":
            c = glyph_col(kind, False)
        icon(t, kind, bx + 5, 22 + 5, 2.6 if kind != "play" else 3.0, c)
    readout(t, 65, 22, 33, 8)
    rect(t, 84, 24, 1, 1, T["ink"])
    rect(t, 84, 27, 1, 1, T["ink"])
    pill_button(t, 106, 9, 22, 16, "LIST")
    grip = {"ps1": (110, 112, 118), "psone": (160, 166, 174), "ps2": (70, 110, 190)}[ST()]
    for k in range(4):
        for j in range(k + 1):
            disc(t, 146.5 - 3 * k + 3 * j, 34.5 - 3 * j, 0.7, grip)
    a[72:110, 126:276] = t

    a[0:38, 179:204] = bottom_strip(25, 38)
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_letter_cells(lit):
    """Each capital in its own cell (the bar's rows 4..10), for gen.bmp's letter rows."""
    f = title_font(8)
    col = title_col(lit)
    rows = bar_rows(20, lit)[4:11]
    cells = []
    for c in GEN_LETTERS:
        adv = int(round(f.getlength(c))) + 1
        w = max(3, adv)
        cell = np.repeat(rows, w, axis=1).copy()
        ttext(cell, c, f, w / 2, 7, col, "c")
        cells.append(cell)
    return cells


def make_gen():
    a = new(194, 109, T["bg"])
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 0:25] = bar20(25, lit, rx0=4)
        a[y:y + 20, 26:51] = bar20(25, lit, rx1=16)
        a[y:y + 20, 52:77] = bar20(25, lit, rib=False)
        a[y:y + 20, 78:103] = bar20(25, lit, rx0=9)
        a[y:y + 20, 104:129] = bar20(25, lit)
        t = bar20(25, lit, rx1=12)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 130:155] = t

    grip = {"ps1": (110, 112, 118), "psone": (160, 166, 174), "ps2": (70, 110, 190)}[ST()]
    edge = {"ps1": (140, 142, 147), "psone": (176, 181, 188), "ps2": (0, 0, 0)}[ST()]

    def bottom(w, g):
        t = bottom_strip(w, 14)
        if g:
            for k in range(3):
                for j in range(k + 1):
                    disc(t, w - 3.5 - 3 * k + 3 * j, 11.5 - 3 * j, 0.7, grip)
        return t

    t = bottom(125, False)
    rect(t, 0, 0, 1, 14, edge)
    a[42:56, 0:125] = t
    t = bottom(125, True)
    rect(t, 124, 0, 1, 14, edge)
    a[57:71, 0:125] = t
    a[72:86, 127:152] = bottom(25, False)
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = frame_side(w, h, left)
    b = bar(9, 20, True)[3:12].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = b

    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for cell in gen_letter_cells(lit):
            w = cell.shape[1]
            a[y:y + 7, x:x + w] = cell
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------


def genex_colours():
    pl = {k: hexc(v) for k, v in T["pl"].items()}
    if ST() == "ps1":
        return [pl["NormalBG"], pl["Normal"], (198, 199, 202), (50, 52, 58), (40, 42, 48), (120, 122, 127),
                pl["SelectedBG"], (184, 186, 190), (40, 42, 48), (236, 237, 239), (110, 112, 118),
                (50, 109, 179), (198, 199, 202), (184, 186, 190), (150, 152, 158), (170, 172, 177), (50, 109, 179),
                (198, 199, 202)]
    if ST() == "psone":
        return [pl["NormalBG"], pl["Normal"], (240, 241, 243), (92, 98, 108), (60, 66, 76), (206, 210, 216),
                pl["SelectedBG"], (232, 235, 239), (60, 66, 76), (255, 255, 255), (176, 181, 188),
                (79, 134, 208), (240, 241, 243), (226, 229, 233), (176, 182, 190), (210, 214, 220), (79, 134, 208),
                (240, 241, 243)]
    return [pl["NormalBG"], pl["Normal"], (6, 20, 58), (210, 226, 250), (230, 238, 252), (30, 70, 150),
            pl["SelectedBG"], (12, 14, 20), (180, 205, 245), (44, 100, 220), (0, 0, 0), (90, 170, 255),
            (6, 20, 58), (6, 16, 46), (120, 170, 240), (30, 60, 130), (200, 228, 255), (6, 20, 58)]


def make_genex():
    a = new(256, 64, T["bg"])
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    for y, pressed in ((1, False), (16, True)):
        cell = new(47, 15, T["bg"])
        keycap(cell, 0, 0, 47, 15, False, pressed)
        a[y:y + 15, 0:47] = cell
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    p = T["panel"]
    stops = T["vis"]
    out = [(p, "background"), (lerp(p, T["ink"], 0.08), "dots")]
    for i in range(16):
        out.append((ramp(stops, i / 15), f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}"))
    for i in range(5):
        out.append((ramp(stops[:3], i / 4), f"oscilloscope {i + 1}"))
    out.append(((255, 255, 255), "peaks"))
    return out


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    pl = T["pl"]
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={pl['Normal']}\nCurrent={pl['Current']}\nNormalBG={pl['NormalBG']}\n"
                f"SelectedBG={pl['SelectedBG']}\nMbBG={pl['NormalBG']}\nMbFG={pl['Normal']}\nFont=Arial\n")
    n, o = T["name"], T["owner"]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n", encoding="utf-8") as f:
        f.write(
            f"{n} — a skin in the style of {T['subject']}.\n"
            f"PlayStation logo © {o}.\n\n"
            f"A classic (Winamp 2.x format) skin, generated by a script (gen_skin.py).\n"
        )


# ------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------

SHEETS = {}


def build():
    SHEETS.clear()
    main = make_main()
    sheets = {
        "main.bmp": main,
        "titlebar.bmp": make_titlebar(),
        "cbuttons.bmp": make_cbuttons(),
        "shufrep.bmp": make_shufrep(),
        "posbar.bmp": make_posbar(main),
        "volume.bmp": make_volume(),
        "balance.bmp": make_balance(),
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
    wsz = os.path.join(HERE, T["wsz"] + ".wsz")
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


def text_ink():
    """text.bmp's ink as the app finds it: the commonest colour in the letter rows unlike the space cell."""
    a = np.asarray(SHEETS["text"], np.int32)[0:12, 0:155]
    bg = a[0, 150]
    far = np.abs(a - bg).sum(-1) >= 96
    cols, counts = np.unique(a[far].reshape(-1, 3), axis=0, return_counts=True)
    return tuple(int(v) for v in cols[counts.argmax()])


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
    for k, (x, w, h) in cb.items():
        blit(img, S["cbuttons"], (x, 18 if state["pressed"] == k else 0, w, h), *CB_POS[k])
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
    blit(img, S["playpaus"], (39, 0, 3, 9), 24, 28)
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
    # title: text.bmp's space across the box, then the title in TrueType in text.bmp's ink
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    f = ImageFont.truetype(LIBERATION, 11)
    tmp = img.crop((111, 22, 265, 36))
    ImageDraw.Draw(tmp).text((0, 29 - 22), state["title"], fill=text_ink(), font=f, anchor="lm")
    img.paste(tmp, (111, 22))
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
    pl = {k: hexc(v) for k, v in T["pl"].items()}
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=pl["NormalBG"])
    f = ImageFont.truetype(LIBERATION, 10)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=pl["SelectedBG"])
        col = pl["Current"] if i == 1 else pl["Normal"]
        d.text((lx + 2, y + 2), f"{i + 1}. {txt}", fill=col, font=f)
        d.text((lx + lw - 3 - d.textlength(dur, font=f), y + 2), dur, fill=col, font=f)
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
    pw, ph = w - 22, h - 34
    yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
    t = (xx / pw * 0.4 + yy / ph * 0.6)[..., None]
    c0, c1 = np.array(T["vis"][0], np.float32), np.array(T["vis"][3], np.float32)
    pic = c0 * (1 - t) + c1 * t
    img.paste(Image.fromarray(pic.astype(np.uint8)), (11, 20))
    return img


PREVIEW_TITLES = {
    "ps1": ("PlayStation - Startup Chime (1994)", "Paused: Memory Card Blues"),
    "psone": ("PSone - Little Screen (Live)", "Paused: Pocket Edition"),
    "ps2": ("PlayStation 2 - Boot Sequence", "Paused: Towers (Browser Mix)"),
}


def preview():
    rows = [("Night Drive - Copper Wire", "4:12"), ("Slow Burn - Lantern Hours", "3:47"),
            ("Kiln - Second Firing", "5:03"), ("Ash & Smoke - Afterglow", "2:58"),
            ("Ember Trio - Coal Seam", "6:21"), ("Field Notes - Warm Static", "3:33"),
            ("Tinder - Small Hours", "4:40"), ("The Forge - Bellows", "3:09"),
            ("Hearth - Long Winter", "5:51"), ("Glowworm - Low Light", "4:05"),
            ("Foundry - Pour", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    t1, t2 = PREVIEW_TITLES[T["key"]]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False, title=t1, bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True, title=t2,
             bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
        col.paste(preview_gen(lit, 275, 140, T["gen_title"], pressed_close=not lit), (0, 464))
        cols.append(col)
    gap = 12
    out = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), (60, 60, 64) if not is_light()
                    else (150, 150, 156))
    out.paste(cols[0], (gap, gap))
    out.paste(cols[1], (275 + 2 * gap, gap))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, f"preview-{T['key']}.png"))


# ------------------------------------------------------------------------------------------
# Checks
# ------------------------------------------------------------------------------------------


def check():
    S = SHEETS
    sizes = {"main": (275, 116), "titlebar": (344, 87), "cbuttons": (136, 36), "shufrep": (92, 85),
             "posbar": (307, 10), "volume": (68, 433), "balance": (68, 433), "monoster": (56, 24),
             "playpaus": (48, 9), "numbers": (99, 13), "nums_ex": (108, 13), "text": (155, 18),
             "pledit": (280, 186), "eqmain": (275, 315), "gen": (194, 109), "genex": (256, 64)}
    for k, sz in sizes.items():
        assert S[k].size == sz, (k, S[k].size, sz)
        assert S[k].mode == "RGB", k
    gen_letters()
    sp = S["text"].getpixel((150, 0))
    assert sp == tuple(T["panel"]), (sp, T["panel"])
    for x in range(150, 155):
        for y in range(6):
            assert S["text"].getpixel((x, y)) == sp
    m = np.asarray(S["main"]).astype(int)
    box = m[22:35, 111:265]
    assert (box == np.array(T["panel"])).all(), "title box not flat"
    # the rows the seek and volume/balance thumbs slide along are uniform across their travel
    for (y0, y1, x0, x1) in ((72, 82, 16, 264), (58, 69, 107, 175), (58, 69, 177, 215)):
        reg = MAINBG[y0:y1, x0:x1]
        spread = np.abs(reg - reg[:, :1]).max()
        assert spread <= 2, ("slider rows not uniform", y0, x0, spread)
    ink = text_ink()
    contrast = sum(abs(ink[i] - T["panel"][i]) for i in range(3))
    assert contrast > 300, ("title ink too close to the panel", ink)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        for k, v in THEMES.items():
            print(f"{k}\t{v['wsz']}.wsz\t{v['subject']}")
        sys.exit(0)
    keys = args or list(THEMES)
    for key in keys:
        if key not in THEMES:
            sys.exit(f"unknown theme {key!r}; one of {', '.join(THEMES)}")
        setup_theme(key)
        names = build()
        check()
        preview()
        print(f"{key}: {T['wsz']}.wsz, preview-{key}.png, out/{key}/ ({len(names)} files)")
