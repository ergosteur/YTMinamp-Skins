#!/usr/bin/python3
"""iOS 7 and iOS 26: classic Winamp 2.x skins in the style of Apple's two big redesigns.

Forked from skins/ember/gen_skin.py (same sheets, same layouts, same preview logic), redrawn:
antialiased shapes from signed distance fields, vector-stroked digits and glyphs, hand-made pixel
fonts. Private use only; the one real mark is the Apple logo in the About spot, rasterised at
generation time from source/logo-apple/apple-logo.svg (see README.md). Everything else is drawn here.

    /usr/bin/python3 -I gen_skin.py            # both themes
    /usr/bin/python3 -I gen_skin.py ios26      # just this one

Themes: "ios7" (2013: flat, white, hairlines, thin type, #007aff) and "ios26" (2025: Liquid Glass,
frosted and clear glass capsules floating over an invented vivid wallpaper). Each writes its sheets
into out/<theme>/, zips them flat into iOS7.wsz / iOS26.wsz and draws preview-<theme>.png.

How the sheets are built: each window gets a "base" (its background with every static panel, but no
state), and every state sprite (buttons, toggles, slider frames, titlebars) is a crop of that base
at the sprite's real position with its content drawn on top, so sprites sit seamlessly on the
glass and wallpaper. Anything that moves (slider and seek thumbs, EQ thumbs) or comes from text.bmp
sits on a uniform colour, since its sprite is drawn the same at every position.
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
SCRATCH = os.path.join(HERE, "out", "scratch")
APPLE_SVG = os.path.join(HERE, "source", "logo-apple", "apple-logo.svg")

T = None    # the theme being built
OUT = None  # its sheet folder

SEP = (255, 0, 255)  # gen.bmp letter separators (never shown)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def hexc(c):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in c)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------


def make_theme(key):
    t = SimpleNamespace(key=key)
    t.v2 = False
    if key == "ios7":
        t.name, t.wsz, t.ver = "iOS 7", "iOS7.wsz", "7"
        t.glass = False
        t.WHITE = (255, 255, 255)
        t.BODY = (255, 255, 255)
        t.BAR = (247, 247, 248)          # the frosted nav/tool bars
        t.HAIR = (200, 199, 204)         # #c8c7cc separators
        t.EDGE = (178, 178, 184)         # the window's own outline
        t.DISP = (255, 255, 255)         # displays: white, black thin digits
        t.INK = (0, 0, 0)
        t.TINT = rgb("#007aff")
        t.TINT_PRESSED = lerp(t.TINT, t.WHITE, 0.62)
        t.RED = rgb("#ff3b30")
        t.GREEN = rgb("#4cd964")
        t.GREY = rgb("#8e8e93")
        t.GREY_LT = rgb("#c7c7cc")
        t.TRACK = rgb("#b7b7b7")         # a slider's maximum track
        t.TITLE = (0, 0, 0)
        t.TITLE_DIM = (160, 160, 166)
        t.DIGIT_W = 1.0                  # digit stroke width: Helvetica Neue Light-ish
        t.pledit = dict(Normal="#000000", Current="#007AFF", NormalBG="#FFFFFF", SelectedBG="#D9D9DE")
        t.FRAME = t.BAR
    else:
        t.name, t.wsz, t.ver = "iOS 26", "iOS26.wsz", "26"
        t.glass = True
        t.WHITE = (255, 255, 255)
        t.DISP = (244, 245, 251)         # frosted display glass: legible first
        t.HAIR = (214, 216, 228)
        t.INK = (28, 28, 30)
        t.TINT = rgb("#0088ff")          # iOS 26's system blue
        t.TINT_PRESSED = lerp(t.TINT, t.WHITE, 0.45)
        t.RED = rgb("#ff383c")
        t.GREEN = rgb("#34c759")
        t.GREY = rgb("#8e8e93")
        t.GREY_LT = (196, 198, 210)
        t.TRACK = (212, 214, 226)
        t.TITLE = (255, 255, 255)
        t.TITLE_DIM = (255, 255, 255)
        t.DIGIT_W = 1.45                 # SF-like regular weight
        t.pledit = dict(Normal="#1C1C1E", Current="#0088FF", NormalBG="#F6F7FB", SelectedBG="#D3E5FF")
        t.FRAME = (214, 214, 240)        # playlist/gen frames: frosted glass (tiled, so uniform)
        t.BAR = t.FRAME
        t.EDGE = (120, 110, 170)
    t.v2 = key == "ios26-v2"
    t.SWITCH_ON = t.GREEN
    if t.v2:
        # cohesion first: one frosted chrome for every window, colour only in a few glass controls
        t.wsz = "iOS26-v2.wsz"
        t.CHROME = (234, 236, 245)       # the body of every window: soft, low-saturation, uniform
        t.CHROME_TOP = (250, 251, 255)   # the title band's top row, easing into CHROME by row 13
        t.FRAME = t.CHROME
        t.BAR = t.CHROME
        t.DISP = (251, 251, 254)
        t.HAIR = (212, 214, 228)
        t.EDGE_HI = (255, 255, 255)
        t.EDGE_LO = (168, 170, 194)
        t.TITLE = t.INK
        t.TITLE_DIM = (150, 150, 162)
        t.SWITCH_ON = t.TINT
        t.pledit = dict(Normal="#1C1C1E", Current="#0088FF", NormalBG="#FBFBFE", SelectedBG="#D6E7FF")
    return t


THEME_KEYS = ["ios7", "ios26", "ios26-v2"]

# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy float, H x W x 3)
# ------------------------------------------------------------------------------------------


def new(w, h, col=None):
    a = np.zeros((h, w, 3), dtype=np.float32)
    a[:, :] = T.DISP if col is None else col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):y + h, max(0, x):x + w] = col


def px(a, x, y, col, op=1.0):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = a[y, x] * (1 - op) + np.array(col, np.float32) * op


def coords(a):
    h, w = a.shape[:2]
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    return X + 0.5, Y + 0.5


def sd_rrect(a, x, y, w, h, r):
    """Signed distance to a rounded rectangle covering pixels x..x+w-1, y..y+h-1."""
    X, Y = coords(a)
    r = min(r, w / 2, h / 2)
    qx = np.abs(X - (x + w / 2)) - (w / 2 - r)
    qy = np.abs(Y - (y + h / 2)) - (h / 2 - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def sd_circle(a, cx, cy, r):
    X, Y = coords(a)
    return np.hypot(X - cx, Y - cy) - r


def cov(d):
    return np.clip(0.5 - d, 0, 1)


def ring(d, width=1.0):
    return np.clip(cov(d) - cov(d + width), 0, 1)


def comp(a, alpha, col, op=1.0):
    al = (alpha * op)[..., None].astype(np.float32)
    c = np.asarray(col, np.float32)
    a[:] = a * (1 - al) + c * al


def gblur(m, s):
    r = int(3 * s) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2)
    k /= k.sum()
    pad = [(r, r), (r, r)] + [(0, 0)] * (m.ndim - 2)
    p = np.pad(m, pad, mode="edge")
    h, w = m.shape[:2]
    out = sum(k[i] * p[i:i + h, :] for i in range(2 * r + 1))
    out = sum(k[i] * out[:, i:i + w] for i in range(2 * r + 1))
    return out.astype(np.float32)


def shift(m, dx, dy):
    out = np.zeros_like(m)
    h, w = m.shape[:2]
    out[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] = m[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
    return out


def save(a, name):
    img = Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def crop(base, x, y, w, h):
    return base[y:y + h, x:x + w].copy()


# ------------------------------------------------------------------------------------------
# Vector strokes (supersampled, for digits and glyphs)
# ------------------------------------------------------------------------------------------

SS = 8


def vec(w, h, fn):
    """Coverage (h, w) of shapes drawn by fn(draw, P, W) at SS x; P maps pixel coords, W widths."""
    im = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(im)

    def P(*xy):
        return [v * SS for v in xy]

    def W(v):
        return max(1, int(round(v * SS)))

    fn(d, P, W)
    im = im.resize((w, h), Image.BOX)
    return np.asarray(im, np.float32) / 255.0


def stamp(a, x, y, alpha, col, op=1.0):
    h, w = alpha.shape
    sub = a[y:y + h, x:x + w]
    comp(sub, alpha[:sub.shape[0], :sub.shape[1]], col, op)


def poly(d, P, W, pts, width):
    """A polyline with round joins."""
    flat = []
    for p in pts:
        flat += P(*p)
    d.line(flat, fill=255, width=W(width), joint="curve")
    r = width * SS / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], fill=255)


def arc(d, P, W, box, start, end, width):
    d.arc(P(*box), start, end, fill=255, width=W(width))


# ------------------------------------------------------------------------------------------
# Pixel fonts
# ------------------------------------------------------------------------------------------


def G(*rows):
    return list(rows)


# 5-row caps font (Ember's) for text.bmp and gen.bmp's titles.
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
    "0": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "1": G(".#", "##", ".#", ".#", ".#"),
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

# Mixed-case proportional sans (cap height 7, x-height 5, descenders 2: 9 rows). "+" = half ink.
_X = ["", ""]  # two blank rows above the x-height
SANS = {
    "a": _X + ["+##.", "...#", ".###", "#..#", ".###", "....", "...."],
    "b": ["#...", "#...", "###+", "#..#", "#..#", "#..#", "###+", "....", "...."],
    "c": _X + ["+##", "#..", "#..", "#..", "+##", "...", "..."],
    "d": ["...#", "...#", "+###", "#..#", "#..#", "#..#", "+###", "....", "...."],
    "e": _X + ["+##+", "#..#", "####", "#...", "+##.", "....", "...."],
    "f": [".+#", ".#.", "###", ".#.", ".#.", ".#.", ".#.", "...", "..."],
    "g": _X + ["+###", "#..#", "#..#", "#..#", "+###", "...#", "+##+"],
    "h": ["#...", "#...", "###+", "#..#", "#..#", "#..#", "#..#", "....", "...."],
    "i": ["#", ".", "#", "#", "#", "#", "#", ".", "."],
    "j": [".#", "..", ".#", ".#", ".#", ".#", ".#", ".#", "#+"],
    "k": ["#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#", "....", "...."],
    "l": ["#", "#", "#", "#", "#", "#", "#", ".", "."],
    "m": _X + ["##+#+", "#.#.#", "#.#.#", "#.#.#", "#.#.#", ".....", "....."],
    "n": _X + ["###+", "#..#", "#..#", "#..#", "#..#", "....", "...."],
    "o": _X + ["+##+", "#..#", "#..#", "#..#", "+##+", "....", "...."],
    "p": _X + ["###+", "#..#", "#..#", "#..#", "###+", "#...", "#..."],
    "q": _X + ["+###", "#..#", "#..#", "#..#", "+###", "...#", "...#"],
    "r": _X + ["#+#", "##.", "#..", "#..", "#..", "...", "..."],
    "s": _X + ["+##", "#..", "+#+", "..#", "##+", "...", "..."],
    "t": [".#.", ".#.", "###", ".#.", ".#.", ".#.", "..#", "...", "..."],
    "u": _X + ["#..#", "#..#", "#..#", "#..#", "+###", "....", "...."],
    "v": _X + ["#.#", "#.#", "#.#", "#.#", ".#.", "...", "..."],
    "w": _X + ["#...#", "#...#", "#.#.#", "#.#.#", "+#+#+", ".....", "....."],
    "x": _X + ["#.#", "#.#", ".#.", "#.#", "#.#", "...", "..."],
    "y": _X + ["#..#", "#..#", "#..#", "#..#", "+###", "...#", "+##+"],
    "z": _X + ["###", "..#", ".#.", "#..", "###", "...", "..."],
    "A": [".##.", "#..#", "#..#", "####", "#..#", "#..#", "#..#", "....", "...."],
    "B": ["###+", "#..#", "#..#", "###.", "#..#", "#..#", "###+", "....", "...."],
    "C": ["+###", "#...", "#...", "#...", "#...", "#...", "+###", "....", "...."],
    "D": ["###+", "#..#", "#..#", "#..#", "#..#", "#..#", "###+", "....", "...."],
    "E": ["####", "#...", "#...", "###.", "#...", "#...", "####", "....", "...."],
    "H": ["#..#", "#..#", "#..#", "####", "#..#", "#..#", "#..#", "....", "...."],
    "K": ["#..#", "#..#", "#.#.", "##..", "#.#.", "#..#", "#..#", "....", "...."],
    "L": ["#...", "#...", "#...", "#...", "#...", "#...", "####", "....", "...."],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#", ".....", "....."],
    "N": ["#..#", "##.#", "##.#", "#.##", "#.##", "#..#", "#..#", "....", "...."],
    "O": ["+##+", "#..#", "#..#", "#..#", "#..#", "#..#", "+##+", "....", "...."],
    "P": ["###+", "#..#", "#..#", "###+", "#...", "#...", "#...", "....", "...."],
    "R": ["###+", "#..#", "#..#", "###+", "#.#.", "#..#", "#..#", "....", "...."],
    "S": ["+##+", "#...", "#...", "+##+", "...#", "...#", "+##+", "....", "...."],
    "Q": ["+##+", "#..#", "#..#", "#..#", "#..#", "#.#+", "+#+#", "....", "...."],
    "F": ["####", "#...", "#...", "###.", "#...", "#...", "#...", "....", "...."],
    "G": ["+###", "#...", "#...", "#.##", "#..#", "#..#", "+###", "....", "...."],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###", "...", "..."],
    "J": ["..#", "..#", "..#", "..#", "..#", "#.#", "+#+", "...", "..."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#..", ".....", "....."],
    "U": ["#..#", "#..#", "#..#", "#..#", "#..#", "#..#", "+##+", "....", "...."],
    "V": ["#...#", "#...#", "#...#", "+#.#+", ".#.#.", ".+#+.", "..#..", ".....", "....."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##+##", "#...#", ".....", "....."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#", ".....", "....."],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..", ".....", "....."],
    "Z": ["####", "...#", "..#+", ".+#.", "+#..", "#...", "####", "....", "...."],
    "0": ["+##+", "#..#", "#..#", "#..#", "#..#", "#..#", "+##+", "....", "...."],
    "1": [".#", "##", ".#", ".#", ".#", ".#", ".#", "..", ".."],
    "2": ["+##+", "#..#", "...#", "..#+", ".#+.", "#+..", "####", "....", "...."],
    "3": ["###+", "...#", "...#", ".##+", "...#", "...#", "###+", "....", "...."],
    "4": ["..#.", ".##.", "#.#.", "#.#.", "####", "..#.", "..#.", "....", "...."],
    "5": ["####", "#...", "###+", "...#", "...#", "#..#", "+##+", "....", "...."],
    "6": ["+##+", "#...", "###+", "#..#", "#..#", "#..#", "+##+", "....", "...."],
    "7": ["####", "...#", "..#+", "..#.", ".#+.", ".#..", ".#..", "....", "...."],
    "8": ["+##+", "#..#", "#..#", "+##+", "#..#", "#..#", "+##+", "....", "...."],
    "9": ["+##+", "#..#", "#..#", "#..#", "+###", "...#", "+##+", "....", "...."],
    "+": ["...", "...", ".#.", "###", ".#.", "...", "...", "...", "..."],
    "-": ["...", "...", "...", "###", "...", "...", "...", "...", "..."],
    " ": ["..", "..", "..", "..", "..", "..", "..", "..", ".."],
}
for _k, _v in SANS.items():
    _w = max(len(r) for r in _v)
    SANS[_k] = [(r if r else "") .ljust(_w, ".") for r in _v]

# 3x5 caps for the smallest labels.
TINY = {k: v for k, v in FONT5.items() if k.isdigit()}


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1, op=1.0):
    for c in s:
        if c not in font:
            continue
        g = font[c]
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col, op)
                elif ch == "+":
                    px(a, x + k, y + r, col, 0.45 * op)
        x += len(g[0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1, op=1.0):
    draw_text(a, font, s, int(round(cx - text_w(font, s, gap) / 2)), y, col, gap, op)


def shadowed(a, font, s, cx, y, col, op=1.0):
    """White title text over the wallpaper: a soft dark halo, then the text."""
    m = new(a.shape[1], a.shape[0], (0, 0, 0))
    text_center(m, font, s, cx, y, (255, 255, 255))
    al = gblur(m[..., 0] / 255.0, 0.9)
    comp(a, np.clip(al * 0.9, 0, 0.55), (30, 20, 60), op)
    text_center(a, font, s, cx, y, col, op=op)


# ------------------------------------------------------------------------------------------
# The invented wallpaper (iOS 26) and glass
# ------------------------------------------------------------------------------------------

WALL_BLOBS = [
    # cx, cy, sigma, colour, weight over main (y 0..115) + EQ (y 116..231): a normalised mixture,
    # so each region keeps its own vivid hue and the seams between them stay soft
    (20, 10, 55, (20, 110, 255), 1.0),
    (260, 10, 60, (255, 45, 150), 1.0),
    (150, 80, 50, (130, 60, 245), 0.9),
    (10, 170, 60, (255, 140, 30), 1.0),
    (260, 180, 60, (0, 200, 220), 1.0),
    (140, 240, 55, (255, 70, 110), 0.8),
]


def wallpaper(w, h, oy=0):
    X, Y = coords(np.zeros((h, w, 1)))
    Y = Y + oy
    num = np.zeros((h, w, 3), np.float32)
    den = np.full((h, w, 1), 1e-3, np.float32)
    for cx, cy, s, col, k in WALL_BLOBS:
        wgt = (k * np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * s * s)))[..., None] ** 0.7
        num += wgt * np.array(col, np.float32)
        den += wgt
    return num / den


def glass(a, x, y, w, h, r=None, kind="frost", fill=None, shadow=0.26, rim=1.0):
    """A Liquid Glass shape: soft shadow, body, a bright specular rim top-left (and a fainter one
    bottom-right), a faint dark outline. kind 'frost' = uniform frosted body (displays and
    anything a moving sprite crosses); 'clear' = the blurred backdrop, lightened, showing through."""
    if r is None:
        r = h / 2
    d = sd_rrect(a, x, y, w, h, r)
    c = cov(d)
    if shadow:
        sh = gblur(shift(c, 0, 1), 1.5)
        comp(a, sh * (1 - c), (25, 10, 60), shadow)
    if kind == "frost":
        comp(a, c, fill or T.DISP)
    else:
        bd = gblur(a, 2.5)
        lum = bd.mean(axis=2, keepdims=True)
        bd = lum + (bd - lum) * 1.25                         # a little more saturated, like the lens
        body = bd * 0.5 + 255 * 0.5
        X, Y = coords(a)
        sheen = np.clip(1 - (Y - y) / max(1, h), 0, 1)[..., None] * 18   # brighter towards the top
        comp(a, c, 0, 0)
        a[:] = a * (1 - c[..., None]) + np.clip(body + sheen, 0, 255) * c[..., None]
        # refraction at the edge: a band just inside the rim picks up more of the colour beneath
        band = np.clip(cov(d) - cov(d + 2.2), 0, 1) * 0.35
        comp(a, band, 0, 0)
        a[:] = a * (1 - band[..., None]) + np.clip(bd * 0.85 + 30, 0, 255) * band[..., None]
    gy, gx = np.gradient(d)
    n = np.hypot(gx, gy) + 1e-6
    lit = np.clip(-(gx + gy) / n * 0.7071, 0, 1)
    back = np.clip((gx + gy) / n * 0.7071, 0, 1)
    rg = ring(d, 1.0)
    comp(a, rg * (0.30 + 0.70 * lit + 0.35 * back) * rim, (255, 255, 255))
    out = np.clip(cov(d - 1) - c, 0, 1)
    comp(a, out * 0.22 * rim, (40, 30, 80))


def hairline_box(a, x, y, w, h, r, col):
    comp(a, ring(sd_rrect(a, x, y, w, h, r), 1.0), col)


# ------------------------------------------------------------------------------------------
# Glyphs
# ------------------------------------------------------------------------------------------


def glyph(kind, w, h, line=1.0, solid=False):
    """Coverage of a transport/title glyph centred in a w x h cell."""
    cx, cy = w / 2, h / 2

    def fn(d, P, W):
        L = line
        if kind == "play":
            pts = [(cx - 3, cy - 4.5), (cx + 4.5, cy), (cx - 3, cy + 4.5)]
            if solid:
                d.polygon([v for p in pts for v in P(*p)], fill=255)
            else:
                poly(d, P, W, pts + [pts[0]], L)
        elif kind == "pause":
            for ox in (-2.5, 2.5):
                if solid:
                    d.rectangle(P(cx + ox - 1.2, cy - 4.5, cx + ox + 1.2, cy + 4.5), fill=255)
                else:
                    poly(d, P, W, [(cx + ox, cy - 4.5), (cx + ox, cy + 4.5)], L)
        elif kind == "stop":
            if solid:
                d.rounded_rectangle(P(cx - 4, cy - 4, cx + 4, cy + 4), radius=1.2 * SS, fill=255)
            else:
                d.rounded_rectangle(P(cx - 4, cy - 4, cx + 4, cy + 4), radius=1 * SS, outline=255, width=W(L))
        elif kind in ("previous", "next"):
            s = 1 if kind == "next" else -1
            if solid:
                for ox in (-3.5, 0.5):
                    x0 = cx + s * ox
                    pts = [(x0, cy - 3.5), (x0 + s * 4, cy), (x0, cy + 3.5)]
                    d.polygon([v for p in pts for v in P(*p)], fill=255)
                poly(d, P, W, [(cx + s * 4.7, cy - 3.5), (cx + s * 4.7, cy + 3.5)], 1.3)
            else:
                x0 = cx - s * 3
                pts = [(x0, cy - 4), (x0 + s * 6, cy), (x0, cy + 4)]
                poly(d, P, W, pts + [pts[0]], L)
                poly(d, P, W, [(cx + s * 4.5, cy - 4), (cx + s * 4.5, cy + 4)], L)
        elif kind == "eject":
            pts = [(cx - 4, cy + 0.5), (cx, cy - 4), (cx + 4, cy + 0.5)]
            if solid:
                d.polygon([v for p in pts for v in P(*p)], fill=255)
                d.rectangle(P(cx - 4, cy + 2, cx + 4, cy + 3.4), fill=255)
            else:
                poly(d, P, W, pts + [pts[0]], L)
                poly(d, P, W, [(cx - 4, cy + 3), (cx + 4, cy + 3)], L)
        elif kind == "shuffle":
            a0, a1 = cx - 6, cx + 5.5
            poly(d, P, W, [(a0, cy - 3), (cx - 2.5, cy - 3), (cx + 2, cy + 3), (a1, cy + 3)], L)
            poly(d, P, W, [(a0, cy + 3), (cx - 2.5, cy + 3), (cx + 2, cy - 3), (a1, cy - 3)], L)
            for yy in (cy - 3, cy + 3):
                poly(d, P, W, [(a1 - 1.8, yy - 1.8), (a1, yy), (a1 - 1.8, yy + 1.8)], L)
        elif kind == "repeat":
            d.rounded_rectangle(P(cx - 5, cy - 3, cx + 5, cy + 3), radius=2.5 * SS, outline=255, width=W(L))
            d.rectangle(P(cx - 1.5, cy - 4, cx + 1.5, cy - 2), fill=0)
            poly(d, P, W, [(cx - 0.5, cy - 5), (cx + 1.5, cy - 3), (cx - 0.5, cy - 1)], L)
        elif kind in ("dots", "options"):
            for ox in (-3, 0, 3):
                d.ellipse(P(cx + ox - 0.9, cy - 0.9, cx + ox + 0.9, cy + 0.9), fill=255)
        elif kind == "minimize":
            poly(d, P, W, [(cx - 3, cy + 2), (cx + 3, cy + 2)], L)
        elif kind == "shade":
            poly(d, P, W, [(cx - 3, cy + 1.5), (cx, cy - 1.5), (cx + 3, cy + 1.5)], L)
        elif kind == "close":
            poly(d, P, W, [(cx - 2.7, cy - 2.7), (cx + 2.7, cy + 2.7)], L)
            poly(d, P, W, [(cx + 2.7, cy - 2.7), (cx - 2.7, cy + 2.7)], L)
        elif kind == "note":
            d.ellipse(P(cx - 4, cy + 2, cx - 0.5, cy + 5), fill=255)
            poly(d, P, W, [(cx - 0.8, cy + 3.5), (cx - 0.8, cy - 5), (cx + 4, cy - 6.2), (cx + 4, cy + 1.5)], L)
            d.ellipse(P(cx + 0.7, cy + 0.5, cx + 4.2, cy + 3.5), fill=255)

    return vec(w, h, fn)


def apple_logo(h):
    """The Apple logo as coverage, h pixels tall (rasterised from the Wikimedia SVG)."""
    os.makedirs(SCRATCH, exist_ok=True)
    png = os.path.join(SCRATCH, f"apple-{h * SS}.png")
    if not os.path.exists(png):
        subprocess.run(["/usr/bin/rsvg-convert", "-h", str(h * SS), APPLE_SVG, "-o", png], check=True)
    im = Image.open(png).convert("RGBA")
    al = im.getchannel("A")
    w = max(1, round(im.width / SS))
    al = al.resize((w, h), Image.BOX)
    return np.asarray(al, np.float32) / 255.0


# ------------------------------------------------------------------------------------------
# Digits (numbers.bmp): vector strokes, Helvetica Neue Light / SF-like
# ------------------------------------------------------------------------------------------


def digit_alpha(n, w=9, h=13):
    L = T.DIGIT_W
    x0, x1, y0, y1 = 1.6, 7.4, 1.4, 11.6
    ym = (y0 + y1) / 2

    def fn(d, P, W):
        if n == 0:
            arc(d, P, W, (x0, y0, x1, y1), 0, 360, L)
        elif n == 1:
            poly(d, P, W, [(3.0, 3.2), (5.0, y0), (5.0, y1)], L)
        elif n == 2:
            arc(d, P, W, (x0, y0, x1, 7.4), 180, 360, L)
            arc(d, P, W, (x0, y0, x1, 7.4), 0, 40, L)
            poly(d, P, W, [(6.8, 6.4), (x0, y1), (x1, y1)], L)
        elif n == 3:
            arc(d, P, W, (x0 + 0.2, y0, x1 - 0.4, ym + 0.3), 200, 450, L)
            arc(d, P, W, (x0, ym - 0.3, x1, y1), 270, 520, L)
        elif n == 4:
            poly(d, P, W, [(5.6, y1), (5.6, y0), (x0 - 0.2, 8.6), (x1 + 0.3, 8.6)], L)
        elif n == 5:
            poly(d, P, W, [(x1 - 0.4, y0), (2.3, y0), (2.0, 6.0)], L)
            arc(d, P, W, (x0, 4.8, x1, y1), 205, 520, L)
        elif n == 6:
            arc(d, P, W, (x0, 5.6, x1, y1), 0, 360, L)
            arc(d, P, W, (x0, y0, x1 + 4.5, y1 + 6.5), 180, 255, L)
        elif n == 7:
            poly(d, P, W, [(x0, y0), (x1, y0), (3.6, y1)], L)
        elif n == 8:
            arc(d, P, W, (x0 + 0.5, y0, x1 - 0.5, ym + 0.2), 0, 360, L)
            arc(d, P, W, (x0, ym - 0.2, x1, y1), 0, 360, L)
        elif n == 9:
            arc(d, P, W, (x0, y0, x1, ym + 1), 0, 360, L)
            arc(d, P, W, (x0 - 4.5, y0 - 6.5, x1, y1), 0, 75, L)
        elif n == "-":
            poly(d, P, W, [(2.2, ym), (6.8, ym)], L)

    return vec(w, h, fn)


# ------------------------------------------------------------------------------------------
# Main window
# ------------------------------------------------------------------------------------------

TITLE_BTNS = {"options": (6, 3), "minimize": (244, 3), "shade": (254, 3), "close": (264, 3)}
CB_POS = {"previous": (16, 88, 23, 18), "play": (39, 88, 23, 18), "pause": (62, 88, 23, 18),
          "stop": (85, 88, 23, 18), "next": (108, 88, 22, 18), "eject": (136, 89, 22, 16)}
CB_SHEET = {"previous": (0, 23, 18), "play": (23, 23, 18), "pause": (46, 23, 18), "stop": (69, 23, 18),
            "next": (92, 22, 18)}
CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def window_edge(a):
    h, w = a.shape[:2]
    if T.v2:
        rect(a, 0, 0, w, 1, T.EDGE_HI)
        rect(a, 0, 0, 1, h, T.EDGE_HI)
        rect(a, 0, h - 1, w, 1, T.EDGE_LO)
        rect(a, w - 1, 0, 1, h, T.EDGE_LO)
    elif T.glass:
        rect_a = np.zeros((h, w), np.float32)
        rect_a[0, :] = 1
        rect_a[:, 0] = 1
        comp(a, rect_a, (255, 255, 255), 0.45)
        rect_a[:] = 0
        rect_a[h - 1, :] = 1
        rect_a[:, w - 1] = 1
        comp(a, rect_a, (30, 20, 70), 0.45)
    else:
        rect(a, 0, 0, w, 1, T.EDGE)
        rect(a, 0, h - 1, w, 1, T.EDGE)
        rect(a, 0, 0, 1, h, T.EDGE)
        rect(a, w - 1, 0, 1, h, T.EDGE)


def chrome_body(w, h):
    """v2: every window's body: uniform CHROME under a 14-row title band (vertical-only, so the
    tiled playlist and gen pieces repeat it exactly)."""
    a = new(w, h, T.CHROME)
    for r, c in enumerate(bar_rows(14)):
        a[r, :] = c
    return a


def chrome_title(a, text, cx, lit):
    """v2: the one title treatment: SF-like caps on rows 4..10, the same as gen.bmp's letters."""
    text_center(a, SANS, text.upper(), cx, 4, T.TITLE if lit else T.TITLE_DIM)


def titlebar_base(w, h=14, wall=None):
    """A window's top bar background."""
    if T.glass:
        a = wall[:h].copy() if wall is not None else new(w, h, T.FRAME)
    else:
        a = new(w, h, T.BAR)
        rect(a, 0, h - 1, w, 1, T.HAIR)
    return a


def title_button(a, x, y, kind, lit=True, pressed=False):
    """A 9x9 window button: iOS 7 a bare tinted glyph; iOS 26 a small clear-glass circle."""
    if T.v2:
        sub = a[y - 2:y + 11, x - 2:x + 11]
        d = sd_circle(sub, 6.5, 6.5, 4.0)
        c = cov(d)
        comp(sub, gblur(shift(c, 0, 1), 0.9) * (1 - c), (40, 30, 90), 0.22)
        comp(sub, c, (214, 228, 252) if pressed else (255, 255, 255), 0.9)
        comp(sub, ring(d), (255, 255, 255), 1.0)
        comp(sub, np.clip(cov(d - 1) - c, 0, 1), (120, 120, 160), 0.25)
        ink = T.TINT if pressed else (T.INK if lit else T.TITLE_DIM)
        stamp(a, x, y, glyph(kind, 9, 9, 1.0), ink)
    elif T.glass:
        sub = a[y - 2:y + 11, x - 2:x + 11]
        d = sd_circle(sub, 6.5, 6.5, 4.0)
        c = cov(d)
        comp(sub, gblur(shift(c, 0, 1), 1.0) * (1 - c), (25, 10, 60), 0.3)
        comp(sub, c, (255, 255, 255), 0.62 if pressed else 0.34)
        comp(sub, ring(d), (255, 255, 255), 0.75)
        ink = T.INK if pressed else ((255, 255, 255) if lit else (235, 235, 245))
        g = glyph(kind, 9, 9, 1.0)
        if not pressed:
            stamp(a, x, y + 1, gblur(g, 0.6), (40, 20, 80), 0.35)
        stamp(a, x, y, g, ink, 1.0 if lit or pressed else 0.7)
    else:
        ink = T.TINT_PRESSED if pressed else (T.TINT if lit else T.GREY_LT)
        stamp(a, x, y, glyph(kind, 9, 9, 1.0), ink)


def main_titlebar(base, lit):
    a = crop(base, 0, 0, 275, 14)
    if T.v2:
        chrome_title(a, "Now Playing", 137, lit)
    elif T.glass:
        shadowed(a, SANS, "Now Playing", 137, 3, T.TITLE, op=1.0 if lit else 0.62)
    else:
        text_center(a, SANS, "Now Playing", 137, 3, T.TITLE if lit else T.TITLE_DIM)
    for kind, (x, y) in TITLE_BTNS.items():
        title_button(a, x, y, kind, lit)
    return a


def clutter_bar(base, lit_letters):
    a = crop(base, 10, 22, 8, 43)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        gy = y + (h - 5) // 2
        if T.glass:
            if on:
                d = sd_rrect(a, 1, y, 6, h, 2.5)
                comp(a, cov(d), T.TINT, 0.9)
            draw_text(a, FONT5 if letter != "I" else {"I": G("#", "#", "#", "#", "#")}, letter,
                      2 if letter not in "IM" else (4 if letter == "I" else 2), gy,
                      (255, 255, 255) if on else (60, 60, 80))
        else:
            ink = T.TINT if on else T.GREY_LT
            draw_text(a, FONT5 if letter != "I" else {"I": G("#", "#", "#", "#", "#")}, letter,
                      2 if letter != "I" else 4, gy, ink)
    return a


def main_base():
    if T.glass:
        a = chrome_body(275, 116) if T.v2 else wallpaper(275, 116, 0)
        # clutterbar: a slim clear capsule
        glass(a, 9, 22, 10, 43, 5, "clear", shadow=0.2)
        # displays: frosted, uniform inside
        glass(a, 20, 18, 86, 46, 8)                          # time + analyzer
        glass(a, 105, 19, 165, 19, 9.5)                      # title
        glass(a, 105, 40, 165, 14, 7)                        # kbps / kHz / mono / stereo
        glass(a, 103, 56, 167, 15, 7.5)                      # volume, balance, EQ/PL
        glass(a, 10, 72, 256, 10, 5)                         # seek
        glass(a, 13, 86, 148, 22, 11, "clear")               # transport
        glass(a, 162, 87, 78, 20, 10, "clear")               # shuffle / repeat
        glass(a, 249, 89, 21, 19, 9.5, "clear")              # about
        # seek track: thick, rounded (the thumb repeats its rows, so they're uniform)
        d = sd_rrect(a, 17, 75, 247, 4, 2)
        comp(a, cov(d), T.TRACK)
        # balance / volume separators and the EQ/PL pills' seats
        for x in (219, 242):
            hairline_box(a, x + 1, 58, 21, 11, 5.5, T.HAIR)
    else:
        a = new(275, 116, T.BODY)
        a[0:14] = titlebar_base(275)
        # displays: hairline cells
        hairline_box(a, 20, 19, 87, 45, 5, T.HAIR)
        rect(a, 111, 37, 157, 1, T.HAIR)                     # under the title, like a table cell
        rect(a, 111, 55, 157, 1, T.HAIR)
        # the seek track (the thumb carries its own copy of it)
        rect(a, 16, 76, 248, 2, T.TRACK)
        hairline_box(a, 9, 21, 10, 45, 4, T.HAIR)
    # the static labels
    lab = T.GREY
    draw_text(a, SANS, "kbps", 129, 41, lab)
    draw_text(a, SANS, "kHz", 169, 41, lab)
    # time colon
    for yy in (29, 35):
        d = sd_circle(a, 74.5, yy + 0.5, 0.85)
        comp(a, cov(d), T.INK)
    # about: the Apple logo
    logo = apple_logo(12)
    lw = logo.shape[1]
    stamp(a, 259 - lw // 2, 91 + 1, logo, (40, 40, 48) if T.glass else T.INK)
    window_edge(a)
    return a


def compose_main(base, sheets):
    """main.bmp: the base with every sprite in its resting state (for players that show it bare)."""
    a = base.copy()
    a[0:14] = sheets["titlebar"][0:14, 27:302]
    cb = sheets["cbuttons"]
    for k, (x, y, w, h) in CB_POS.items():
        sx = 114 if k == "eject" else CB_SHEET[k][0]
        a[y:y + h, x:x + w] = cb[0:h, sx:sx + w]
    a[22:65, 10:18] = sheets["titlebar"][0:43, 304:312]
    sr = sheets["shufrep"]
    a[89:104, 164:211] = sr[0:15, 28:75]
    a[89:104, 210:238] = sr[0:15, 0:28]
    a[58:70, 219:242] = sr[61:73, 0:23]
    a[58:70, 242:265] = sr[61:73, 23:46]
    return a


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------


def make_titlebar(base):
    a = new(344, 87, T.BAR if not T.glass else T.FRAME)
    lit_bar = main_titlebar(base, True)
    dim_bar = main_titlebar(base, False)
    clean = crop(base, 0, 0, 275, 14)
    for kind, sx, sy, pys in [("options", 0, 0, 9), ("minimize", 9, 0, 9), ("close", 18, 0, 9), ("shade", 0, 18, 18)]:
        x, y = TITLE_BTNS[kind]
        a[sy:sy + 9, sx:sx + 9] = lit_bar[y:y + 9, x:x + 9]
        p = clean.copy()
        title_button(p, x, y, kind, True, pressed=True)
        px_ = sx if kind != "shade" else 9
        py_ = pys if kind != "shade" else 18
        a[py_:py_ + 9, px_:px_ + 9] = p[y:y + 9, x:x + 9]
    a[0:14, 27:302] = lit_bar
    a[15:29, 27:302] = dim_bar
    a[29:43, 27:302] = lit_bar
    a[42:56, 27:302] = dim_bar
    unlit = clutter_bar(base, "")
    lit = clutter_bar(base, "OAIDV")
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = lit[y:y + h]
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36), shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def press_lens(a, w, h):
    """iOS 26's press: the glass under the finger brightens and swells."""
    d = sd_rrect(a, 1, 1, w - 2, h - 2, (h - 2) / 2)
    comp(a, cov(d), (255, 255, 255), 0.5)
    comp(a, ring(d), (255, 255, 255), 0.8)


def make_cbuttons(base):
    a = new(136, 36, T.BODY if not T.glass else T.DISP)
    for kind, (x, y, w, h) in CB_POS.items():
        sx = 114 if kind == "eject" else CB_SHEET[kind][0]
        for pressed in (False, True):
            sy = (16 if kind == "eject" else 18) if pressed else 0
            t = crop(base, x, y, w, h)
            if T.glass:
                if pressed:
                    press_lens(t, w, h)
                g = glyph(kind, w, h, solid=True)
                stamp(t, 0, 0, g, T.INK)
            else:
                g = glyph(kind, w, h, line=1.0)
                stamp(t, 0, 0, g, T.TINT_PRESSED if pressed else T.TINT)
            a[sy:sy + h, sx:sx + w] = t
    return a


def toggle_cell(base, x, y, w, h, on, pressed, draw, box=None):
    """A toggle on the base: tinted box when on (box = (bx, by, bw, bh) within the cell, default all)."""
    t = crop(base, x, y, w, h)
    bx, by, bw, bh = box or (1, 1, w - 2, h - 2)
    if T.glass:
        if on:
            d = sd_rrect(t, bx, by, bw, bh, bh / 2)
            comp(t, cov(d), T.TINT_PRESSED if pressed else T.TINT, 0.92)
            comp(t, ring(d), (255, 255, 255), 0.5)
            ink = (255, 255, 255)
        else:
            if pressed:
                press_lens(t, w, h)
            ink = T.INK
    else:
        if on:
            d = sd_rrect(t, bx, by, bw, bh, 3)
            comp(t, cov(d), T.TINT_PRESSED if pressed else T.TINT)
            ink = (255, 255, 255)
        else:
            ink = T.TINT_PRESSED if pressed else T.TINT
    draw(t, ink)
    return t


def make_shufrep(base):
    a = new(92, 85, T.BODY if not T.glass else T.DISP)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = toggle_cell(base, 210, 89, 28, 15, on, pressed,
                                        lambda t, ink: stamp(t, 0, 0, glyph("repeat", 28, 15, 1.1), ink), box=(4, 1, 20, 13))
        a[y:y + 15, 28:75] = toggle_cell(base, 164, 89, 47, 15, on, pressed,
                                         lambda t, ink: stamp(t, 0, 0, glyph("shuffle", 47, 15, 1.1), ink), box=(12, 1, 23, 13))
    for sx, label, dx, pressed in [(0, "EQ", 219, False), (23, "PL", 242, False), (46, "EQ", 219, True),
                                   (69, "PL", 242, True)]:
        for on, sy in ((False, 61), (True, 73)):
            def draw(t, ink, label=label):
                text_center(t, SANS, label, 11.5, 2, ink)
            cell = toggle_cell(base, dx, 58, 23, 12, on, pressed, draw)
            a[sy:sy + 12, sx:sx + 23] = cell
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster(base):
    a = new(56, 24)
    for y, on in ((0, True), (12, False)):
        col = T.TINT if on else T.GREY_LT
        t = crop(base, 239, 41, 29, 12)
        text_center(t, SANS, "stereo", 14, 0, col)
        a[y:y + 12, 0:29] = t
        t = crop(base, 212, 41, 27, 12)
        text_center(t, SANS, "mono", 13, 0, col)
        a[y:y + 12, 29:56] = t
    return a


def make_playpaus():
    a = new(48, 9)
    ink = T.TINT
    stamp(a, 0, 0, vec(9, 9, lambda d, P, W: d.polygon(
        [v for p in [(2.5, 1.5), (7.5, 4.5), (2.5, 7.5)] for v in P(*p)], fill=255)), ink)
    stamp(a, 9, 0, vec(9, 9, lambda d, P, W: (d.rectangle(P(2.5, 1.5, 4, 7.5), fill=255),
                                              d.rectangle(P(5.5, 1.5, 7, 7.5), fill=255))), ink)
    stamp(a, 18, 0, vec(9, 9, lambda d, P, W: d.rounded_rectangle(P(2, 2, 7, 7), radius=SS, fill=255)), ink)
    stamp(a, 39, 0, vec(3, 9, lambda d, P, W: d.ellipse(P(0.3, 3.3, 2.7, 5.7), fill=255)), T.SWITCH_ON)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13)
    for n in range(10):
        stamp(a, 9 * n, 0, digit_alpha(n), T.INK)
    if ex:
        stamp(a, 99, 0, digit_alpha("-"), T.INK)
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key, col * 5, row * 6, T.INK)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def knob(a, cx, cy, w, h, selected):
    """A slider thumb: iOS 7's white circle with a soft shadow; iOS 26's white pill, which turns to
    clear glass (a lens over the track) while dragged."""
    d = sd_rrect(a, cx - w / 2, cy - h / 2, w, h, h / 2)
    c = cov(d)
    if T.glass and selected:
        comp(a, gblur(shift(c, 0, 1), 1.0) * (1 - c), (25, 10, 60), 0.25)
        comp(a, c, (255, 255, 255), 0.35)
        comp(a, ring(d), (255, 255, 255), 0.95)
        comp(a, np.clip(cov(d - 1) - c, 0, 1), (40, 30, 90), 0.35)
        return
    comp(a, gblur(shift(c, 0, 1), 1.0) * (1 - c), (0, 0, 0), 0.32 if not T.glass else 0.28)
    comp(a, c, (255, 255, 255))
    comp(a, ring(d), (0, 0, 0), 0.10 if not selected else 0.18)
    if selected and not T.glass:
        comp(a, c, (226, 226, 232), 0.6)


def make_posbar(base):
    a = new(307, 10)
    a[0:10, 0:248] = crop(base, 16, 72, 248, 10)
    seat = crop(base, 120, 72, 29, 10)        # a stretch of the track the thumb carries
    for sx, selected in ((248, False), (278, True)):
        t = seat.copy()
        if T.glass:
            knob(t, 14.5, 5, 18, 8, selected)
        else:
            # iOS 7 Music's playhead: a thin red line
            rect(t, 14, 1, 2, 8, T.RED if not selected else lerp(T.RED, (0, 0, 0), 0.2))
            if selected:
                rect(t, 13, 0, 4, 10, T.RED)
        a[:, sx:sx + 29] = t
    return a


def track(a, x0, x1, cy, fill_to, thick, centre=None):
    """A horizontal rounded track, tint up to fill_to (or between centre and fill_to)."""
    d = sd_rrect(a, x0, cy - thick / 2, x1 - x0, thick, thick / 2)
    c = cov(d)
    comp(a, c, T.TRACK)
    X, _ = coords(a)
    if centre is None:
        m = (X < fill_to).astype(np.float32)
    else:
        lo, hi = min(centre, fill_to), max(centre, fill_to)
        m = ((X >= lo) & (X < hi)).astype(np.float32)
    comp(a, c * m, T.TINT)


def slider_thumbs(a, seat):
    for sx, selected in ((0, True), (15, False)):
        t = seat.copy()
        # half the track either side of the knob: tint to its left, grey to its right
        track(t, -3, 17, 5.5, 7, 4 if T.glass else 2)
        if T.glass:
            knob(t, 7, 5.5, 14, 10, selected)
        else:
            knob(t, 7, 5.5, 10, 10, selected)
        a[422:433, sx:sx + 14] = t


def make_volume(base):
    a = new(68, 433)
    thick = 4 if T.glass else 2
    for i in range(28):
        y = i * 15
        t = crop(base, 107, 57, 68, 13)
        level = (i + 1) / 28
        track(t, 3, 65, 6.5, 7 + round(level * 54), thick)
        a[y:y + 13, 0:68] = t
        a[y + 13:y + 15, 0:68] = base[70:72, 107:175]
    slider_thumbs(a, crop(base, 120, 58, 14, 11))
    return a


def make_balance(base):
    a = new(68, 433)
    thick = 4 if T.glass else 2
    for i in range(28):
        y = i * 15
        t = crop(base, 177, 57, 38, 13)
        reach = round(12 * i / 27)
        track(t, 3, 35, 6.5, 19 + reach + (1 if i else 0), thick, centre=19)
        rect(t, 19, 3, 1, 2, T.GREY_LT)        # the centre mark
        a[y:y + 13, 9:47] = t
        a[y:y + 13, 0:9] = base[57:70, 168:177]
        a[y:y + 13, 47:68] = base[57:70, 215:236]
        a[y + 13:y + 15, :] = base[70:72, 168:236]
    slider_thumbs(a, crop(base, 120, 58, 14, 11))
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
EQ_SLIDERS = [21] + [78 + 18 * i for i in range(10)]


def eq_base():
    if T.glass:
        a = chrome_body(275, 116) if T.v2 else wallpaper(275, 116, 116)
        glass(a, 11, 16, 64, 16, 8, "clear", shadow=0.2)       # ON / AUTO
        glass(a, 84, 15, 117, 22, 6)                           # graph
        glass(a, 215, 16, 48, 16, 8, "clear", shadow=0.2)      # presets
        glass(a, 9, 38, 257, 75, 7)                          # sliders and their labels
    else:
        a = new(275, 116, T.BODY)
        a[0:14] = titlebar_base(275)
        hairline_box(a, 84, 15, 117, 23, 4, T.HAIR)
        rect(a, 12, 37, 251, 1, T.HAIR)
    lab = T.GREY
    for lbl, yy in (("+12 dB", 41), ("0 dB", 66), ("-12 dB", 90)):
        text_center(a, SANS, lbl, 57, yy, lab)
    text_center(a, SANS, "Preamp", 28, 103, lab)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, SANS, lbl, 78 + 18 * i + 7, 103, lab)
    window_edge(a)
    return a


def eq_titlebar(base, lit):
    a = crop(base, 0, 0, 275, 14)
    if T.v2:
        chrome_title(a, "Equalizer", 137, lit)
    elif T.glass:
        shadowed(a, SANS, "Equalizer", 137, 3, T.TITLE, op=1.0 if lit else 0.62)
    else:
        text_center(a, SANS, "Equalizer", 137, 3, T.TITLE if lit else T.TITLE_DIM)
    title_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(seat, n):
    """14x63: a vertical track, tint from the bottom up to the thumb's centre (n of 0..27)."""
    t = seat.copy()
    thick = 4 if T.glass else 2
    centre = round((1 - n / 27) * 51) + 5 + 0.5
    cx = 6.5
    d = sd_rrect(t, cx - thick / 2, 3, thick, 57, thick / 2)
    c = cov(d)
    comp(t, c, T.TRACK)
    _, Y = coords(t)
    comp(t, c * (Y > centre), T.TINT)
    # the 0 dB tick
    rect(t, 1, 31, 2, 1, T.GREY_LT)
    rect(t, 11, 31, 2, 1, T.GREY_LT)
    return t


def switch(t, x, y, w, h, on, pressed):
    """iOS's switch: green when on; iOS 7's round knob (stretching while pressed), iOS 26's pill."""
    d = sd_rrect(t, x, y, w, h, h / 2)
    c = cov(d)
    if on:
        comp(t, c, T.SWITCH_ON)
    else:
        comp(t, c, (255, 255, 255) if not T.glass else (233, 233, 238))
        if not T.glass:
            comp(t, ring(d), (229, 229, 234))
            comp(t, ring(d), T.HAIR, 0.8)
    kh = h - 2
    kw = kh + (3 if pressed else 0) + (3 if T.glass else 0)
    kx = x + w - 1 - kw if on else x + 1
    if T.glass and pressed:
        dk = sd_rrect(t, kx, y + 1, kw, kh, kh / 2)
        comp(t, cov(dk), (255, 255, 255), 0.45)
        comp(t, ring(dk), (255, 255, 255), 0.95)
    else:
        dk = sd_rrect(t, kx, y + 1, kw, kh, kh / 2)
        ck = cov(dk)
        comp(t, gblur(shift(ck, 0, 1), 0.8) * (1 - ck) * c, (0, 0, 0), 0.3)
        comp(t, ck, (255, 255, 255))
        comp(t, ring(dk), (0, 0, 0), 0.08)


def make_eqmain():
    base = eq_base()
    a = new(275, 315, T.BODY if not T.glass else T.DISP)
    a[0:116] = base
    a[0:14] = eq_titlebar(base, True)
    seat = crop(base, 21, 38, 14, 63)
    for x in EQ_SLIDERS:
        a[38:101, x:x + 14] = eq_slider_frame(seat, 14)

    # ON (a switch) and AUTO (a text button), at (14, 18) and (40, 18)
    def on_cell(on, pressed):
        t = crop(base, 14, 18, 26, 12)
        switch(t, 2, 0, 22 if not T.glass else 22, 12, on, pressed)
        return t

    def auto_cell(on, pressed):
        def draw(t, ink):
            text_center(t, SANS, "Auto", 16, 2, ink)
        return toggle_cell(base, 40, 18, 32, 12, on, pressed, draw)

    for x, kind, on, pressed in [
        (10, "on", False, False), (36, "auto", False, False), (69, "on", True, False), (95, "auto", True, False),
        (128, "on", False, True), (154, "auto", False, True), (187, "on", True, True), (213, "auto", True, True),
    ]:
        if kind == "on":
            a[119:131, x:x + 26] = on_cell(on, pressed)
        else:
            a[119:131, x:x + 32] = auto_cell(on, pressed)
    a[18:30, 14:40] = a[119:131, 69:95]
    a[18:30, 40:72] = a[119:131, 36:68]

    clean = crop(base, 0, 0, 275, 14)
    p = clean.copy()
    title_button(p, 264, 3, "close", True, pressed=True)
    a[125:134, 0:9] = p[3:12, 264:273]
    a[134:148] = eq_titlebar(base, True)
    a[149:163] = eq_titlebar(base, False)
    # thumbs
    tseat = crop(base, 22, 50, 11, 11)
    for y, sel in ((164, False), (176, True)):
        t = tseat.copy()
        thick = 4 if T.glass else 2
        d = sd_rrect(t, 5.5 - thick / 2 - 0.5, -3, thick, 17, thick / 2)
        _, Y = coords(t)
        comp(t, cov(d) * (Y < 5.5), T.TRACK)
        comp(t, cov(d) * (Y >= 5.5), T.TINT)
        if T.glass:
            knob_v(t, sel)
        else:
            knob(t, 5.5, 5.5, 10, 10, sel)
        a[y:y + 11, 0:11] = t
    for n in range(28):
        a[164 + (n // 14) * 65:164 + (n // 14) * 65 + 63, 13 + (n % 14) * 15:13 + (n % 14) * 15 + 14] = \
            eq_slider_frame(seat, n)
    for y, pressed in ((164, False), (176, True)):
        def draw(t, ink):
            text_center(t, SANS, "Presets", 22, 2, ink)
        a[y:y + 12, 224:268] = toggle_cell(base, 217, 18, 44, 12, False, pressed, draw)
    a[18:30, 217:261] = a[164:176, 224:268]
    # graph
    g = crop(base, 86, 17, 113, 19)
    for x in range(1, 113, 12):
        for yy in range(0, 19, 2):
            px(g, x, yy, T.HAIR, 0.8)
    for x in range(0, 113, 2):
        px(g, x, 9, T.HAIR)
    a[294:313, 0:113] = g
    a[17:36, 86:199] = g
    for r in range(19):
        a[294 + r, 115] = ramp([T.TINT, lerp(T.TINT, T.RED, 0.2), T.RED] if not T.glass else
                               ([T.TINT, (90, 180, 255)] if T.v2 else
                                [(255, 60, 160), (150, 70, 240), T.TINT, (40, 200, 230)]), r / 18)
    for x in range(113):
        a[314, x] = T.GREY_LT if x % 3 != 2 else g[9, x]
    return a


def knob_v(t, sel):
    """iOS 26 EQ thumb: a round white knob (glass while dragged)."""
    d = sd_circle(t, 5.5, 5.5, 4.8)
    c = cov(d)
    if sel:
        comp(t, gblur(shift(c, 0, 1), 0.9) * (1 - c), (25, 10, 60), 0.25)
        comp(t, c, (255, 255, 255), 0.35)
        comp(t, ring(d), (255, 255, 255), 0.95)
        comp(t, np.clip(cov(d - 1) - c, 0, 1), (40, 30, 90), 0.35)
    else:
        comp(t, gblur(shift(c, 0, 1), 0.9) * (1 - c), (0, 0, 0), 0.28)
        comp(t, c, (255, 255, 255))
        comp(t, ring(d), (0, 0, 0), 0.1)


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------


def bar_rows(h=20):
    """The frame bars' colour per row (horizontally uniform, so the pieces tile)."""
    if T.v2:
        return [lerp(T.CHROME_TOP, T.CHROME, min(1, r / 13)) for r in range(h)]
    if T.glass:
        return [lerp((248, 249, 255), T.FRAME, min(1, r / (h - 1) * 1.3)) for r in range(h)]
    return [T.BAR] * h


def bar20(w, lit):
    a = new(w, 20)
    for r, c in enumerate(bar_rows()):
        a[r, :] = c
    if T.v2:
        a[0, :] = T.EDGE_HI
    elif T.glass:
        a[0, :] = (255, 255, 255)
        a[19, :] = lerp(T.FRAME, (120, 120, 160), 0.35)
    else:
        a[19, :] = T.HAIR
    return a


def frame_side(w, h, list_edge_x=None):
    a = new(w, h, T.FRAME)
    if list_edge_x is not None:
        # a hairline along the list's edge
        a[:, list_edge_x] = T.HAIR if not T.glass or T.v2 else lerp(T.FRAME, (120, 120, 160), 0.35)
    return a


def frame_close(a, x, y, lit, pressed=False):
    if T.v2:
        title_button(a, x, y, "close", lit, pressed)
    elif T.glass:
        d = sd_circle(a, x + 4.5, y + 4.5, 4.6)
        comp(a, cov(d), (255, 255, 255), 0.95 if pressed else 0.7)
        comp(a, ring(d), (150, 150, 180), 0.4)
        stamp(a, x, y, glyph("close", 9, 9, 1.0), T.INK if lit or pressed else T.GREY)
    else:
        stamp(a, x, y, glyph("close", 9, 9, 1.0), T.TINT_PRESSED if pressed else (T.TINT if lit else T.GREY_LT))


def edge_left(a):
    a[:, 0] = T.EDGE_HI if T.v2 else (T.EDGE if not T.glass else (255, 255, 255))


def edge_right(a):
    a[:, -1] = T.EDGE_LO if T.v2 else (T.EDGE if not T.glass else lerp(T.FRAME, (60, 50, 110), 0.5))


def make_pledit():
    a = new(280, 186, T.FRAME)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit)
        a[y:y + 20, 127:152] = t
        t = bar20(25, lit)
        edge_left(t)
        a[y:y + 20, 0:25] = t
        t = bar20(100, lit)
        if T.v2:
            chrome_title(t, "Playlist", 50, lit)
        else:
            text_center(t, SANS, "Playlist", 50, 5, T.INK if lit else T.GREY)
        a[y:y + 20, 26:126] = t
        t = bar20(25, lit)
        edge_right(t)
        frame_close(t, 14, 3, lit)
        a[y:y + 20, 153:178] = t
        if not T.glass:
            for yy in (y,):
                a[yy, 0:178] = T.EDGE
        else:
            a[y, 0:178] = (255, 255, 255)

    # left side tile; right side tile with the scroll indicator's groove
    t = frame_side(12, 29, 11)
    edge_left(t)
    a[42:71, 0:12] = t
    t = frame_side(20, 29, 0)
    edge_right(t)
    a[42:71, 31:51] = t
    t = bar20(25, True)
    frame_close(t, 14, 3, True, pressed=True)
    a[42:51, 52:61] = t[3:12, 14:23]
    # scroll handles: iOS's thin rounded indicator
    for x, sel in ((52, False), (61, True)):
        h = frame_side(8, 18)
        d = sd_rrect(h, 2.5, 1, 3, 16, 1.5)
        comp(h, cov(d), (0, 0, 0) if not T.glass else (40, 40, 60), 0.45 if not sel else 0.7)
        a[53:71, x:x + 8] = h

    def bottom_base(w):
        t = new(w, 38)
        for r in range(38):
            t[r, :] = T.BAR if not T.glass or T.v2 else lerp(T.FRAME, (238, 240, 250), r / 37)
        if not T.v2:
            t[0, :] = T.HAIR if not T.glass else lerp(T.FRAME, (120, 120, 160), 0.35)
        t[37, :] = T.EDGE_LO if T.v2 else (T.EDGE if not T.glass else lerp(T.FRAME, (60, 50, 110), 0.5))
        return t

    def text_btn(t, cx, label):
        if T.glass:
            glass(t, cx - 12, 9, 24, 15, 7.5, "frost", fill=(250, 251, 255), shadow=0.18, rim=0.8)
            text_center(t, SANS, label, cx, 11, T.TINT)
        else:
            text_center(t, SANS, label, cx, 11, T.TINT)

    t = bottom_base(125)
    edge_left(t)
    for bx, lbl in ((14, "Add"), (43, "Rem"), (72, "Sel"), (101, "Misc")):
        text_btn(t, bx + 11, lbl)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    edge_right(t)
    # running time readout and mini time: display-coloured cells (text.bmp sits on them)
    for (x, y, w, h) in ((5, 8, 58, 9), (64, 21, 35, 10)):
        if T.glass:
            glass(t, x, y, w, h, h / 2, shadow=0.15, rim=0.8)
        else:
            hairline_box(t, x, y, w, h, 3, T.HAIR)
            rect(t, x + 1, y + 1, w - 2, h - 2, T.DISP)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        stamp(t, bx, 22, mini_glyph(kind), T.INK if T.glass else T.TINT)
    rect(t, 84, 24, 1, 1, T.GREY)
    rect(t, 84, 27, 1, 1, T.GREY)
    text_btn(t, 117, "List")
    # resize grip
    for k in range(3):
        for j in range(k + 1):
            px(t, 145 - 3 * k + 3 * j, 31 - 3 * j, T.GREY_LT if not T.glass else (150, 150, 180))
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


def mini_glyph(kind):
    """Small transport glyphs for the playlist's bottom bar (10x10)."""
    def fn(d, P, W):
        cx, cy = 5, 5
        if kind == "play":
            d.polygon([v for p in [(cx - 2, cy - 3), (cx + 3, cy), (cx - 2, cy + 3)] for v in P(*p)], fill=255)
        elif kind == "pause":
            d.rectangle(P(cx - 2.5, cy - 3, cx - 1, cy + 3), fill=255)
            d.rectangle(P(cx + 1, cy - 3, cx + 2.5, cy + 3), fill=255)
        elif kind == "stop":
            d.rectangle(P(cx - 2.5, cy - 2.5, cx + 2.5, cy + 2.5), fill=255)
        elif kind in ("previous", "next"):
            s = 1 if kind == "next" else -1
            for ox in (-2.5, 0):
                x0 = cx + s * ox
                d.polygon([v for p in [(x0, cy - 2.5), (x0 + s * 2.5, cy), (x0, cy + 2.5)] for v in P(*p)], fill=255)
            xb = cx + s * 2.8
            d.rectangle(P(min(xb, xb + s), cy - 2.5, max(xb, xb + s), cy + 2.5), fill=255)
        elif kind == "eject":
            d.polygon([v for p in [(cx - 3, cy + 0.5), (cx, cy - 3), (cx + 3, cy + 0.5)] for v in P(*p)], fill=255)
            d.rectangle(P(cx - 3, cy + 1.6, cx + 3, cy + 2.8), fill=255)
    return vec(10, 10, fn)


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_gen():
    a = new(194, 109, T.FRAME)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn=None):
            t = bar20(25, lit)
            if fn:
                fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        piece(0, edge_left)
        piece(26)
        piece(52)
        piece(78)
        piece(104)

        def right(t):
            edge_right(t)
            frame_close(t, 14, 3, lit)
        piece(130, right)
        if not T.glass:
            a[y, 0:155] = T.EDGE

    def bottom(w, grip, left_edge):
        t = new(w, 14)
        for r in range(14):
            t[r, :] = T.BAR if not T.glass or T.v2 else lerp(T.FRAME, (238, 240, 250), r / 13)
        t[13, :] = T.EDGE_LO if T.v2 else (T.EDGE if not T.glass else lerp(T.FRAME, (60, 50, 110), 0.5))
        if left_edge:
            edge_left(t)
        else:
            edge_right(t)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    px(t, w - 4 - 3 * k + 3 * j, 10 - 3 * j, T.GREY_LT if not T.glass else (150, 150, 180))
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    t = bottom(25, False, False)
    t[:, 24] = t[:, 23]
    a[72:86, 127:152] = t
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h, T.FRAME)
        if outer_left:
            edge_left(t)
        else:
            edge_right(t)
        a[42:42 + h, x:x + w] = t
    t = bar20(25, True)
    frame_close(t, 14, 3, True, pressed=True)
    a[42:51, 148:157] = t[3:12, 14:23]

    # letters: section-header caps, on cells painted with the bar's own rows 4..10
    rows = bar_rows()
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            if T.v2:
                w = glyph_w(SANS, c) + 1
                for r in range(7):
                    a[y + r, x:x + w] = rows[4 + r]
                draw_text(a, {c: SANS[c][:7]}, c, x, y, T.TITLE if lit else T.TITLE_DIM)
                x += w + 1
                continue
            w = glyph_w(FONT5, c) + 2
            for r in range(7):
                a[y + r, x:x + w] = rows[4 + r]
            draw_text(a, FONT5, c, x + 1, y + 1, (T.GREY if not T.glass else (60, 62, 80)) if lit else (T.GREY_LT if not T.glass else (140, 140, 168)))
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp, viscolor.txt, pledit.txt, readme.txt
# ------------------------------------------------------------------------------------------


def genex_colours():
    if not T.glass:
        return [(255, 255, 255), (0, 0, 0), rgb("#efeff4"), T.TINT, (0, 0, 0), T.HAIR, rgb("#d9d9de"),
                rgb("#f7f7f7"), rgb("#6d6d72"), (255, 255, 255), T.HAIR, rgb("#d9d9de"), rgb("#efeff4"),
                rgb("#f7f7f7"), T.GREY_LT, rgb("#e5e5ea"), T.GREY, rgb("#f7f7f7")]
    if T.v2:
        return [rgb("#fbfbfe"), rgb("#1c1c1e"), T.CHROME, T.TINT, rgb("#1c1c1e"), T.HAIR, rgb("#d6e7ff"),
                (244, 245, 251), rgb("#3c3c43"), (255, 255, 255), T.EDGE_LO, rgb("#d6e7ff"), T.CHROME,
                (244, 245, 251), (176, 178, 198), (222, 226, 240), T.TINT, (244, 245, 251)]
    return [rgb("#f6f7fb"), rgb("#1c1c1e"), T.FRAME, T.TINT, rgb("#1c1c1e"), T.HAIR, rgb("#d3e5ff"),
            (238, 240, 250), rgb("#3c3c43"), (255, 255, 255), (186, 188, 206), rgb("#d3e5ff"), T.FRAME,
            (236, 238, 248), (170, 172, 192), (220, 224, 240), T.TINT, (236, 238, 248)]


def make_genex():
    a = new(256, 64, T.FRAME if T.glass else rgb("#efeff4"))
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    for y, pressed in ((1, False), (16, True)):
        d = sd_rrect(a, 1, y + 1, 45, 13, 5)
        comp(a, cov(d), (255, 255, 255) if not pressed else rgb("#d9d9de"))
        comp(a, ring(d), T.HAIR)
    return a


def viscolor():
    if not T.glass:
        bg, dots = T.DISP, (235, 235, 240)
        spec = [ramp([T.TINT, rgb("#34aadc"), rgb("#5ac8fa"), (190, 228, 252)], i / 15) for i in range(16)]
        osc = [T.TINT, lerp(T.TINT, (255, 255, 255), 0.2), lerp(T.TINT, (255, 255, 255), 0.4),
               lerp(T.TINT, (255, 255, 255), 0.55), lerp(T.TINT, (255, 255, 255), 0.7)]
        peak = T.RED
    elif T.v2:
        bg, dots = T.DISP, (230, 232, 242)
        spec = [ramp([T.TINT, (60, 165, 255), (150, 205, 255)], i / 15) for i in range(16)]
        osc = [T.TINT, (40, 155, 255), (80, 175, 255), (120, 195, 255), (160, 212, 255)]
        peak = (28, 28, 30)
    else:
        bg, dots = T.DISP, (226, 228, 240)
        spec = [ramp([(255, 45, 140), (175, 60, 235), (0, 136, 255), (40, 205, 235)], i / 15) for i in range(16)]
        osc = [(0, 136, 255), (60, 120, 250), (130, 90, 240), (190, 70, 210), (240, 60, 160)]
        peak = (28, 28, 30)
    rows = [(bg, "background"), (dots, "dots")]
    rows += [(c, f"spectrum {i + 1}" + (" (top)" if i == 0 else "")) for i, c in enumerate(spec)]
    rows += [(c, f"oscilloscope {i + 1}") for i, c in enumerate(osc)]
    rows += [(peak, "peaks")]
    return [(tuple(int(round(v)) for v in c), n) for c, n in rows]


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    p = T.pledit
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={p['Normal']}\nCurrent={p['Current']}\nNormalBG={p['NormalBG']}\n"
                f"SelectedBG={p['SelectedBG']}\nMbBG={p['NormalBG']}\nMbFG={p['Normal']}\nFont=Arial\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"iOS {T.ver} — a skin in the style of iOS {T.ver}, drawn from scratch (apart from the Apple logo).\n\n"
            "A classic (Winamp 2.x format) skin generated by a script (gen_skin.py): every bitmap is drawn\n"
            "from code, shapes, strokes and hand-made pixel fonts, apart from the Apple logo in the About spot.\n\n"
            "Apple logo © Apple Inc.\n"
        )


# ------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------

SHEETS = {}


def build():
    base = main_base()
    sheets = {
        "titlebar": make_titlebar(base),
        "cbuttons": make_cbuttons(base),
        "shufrep": make_shufrep(base),
        "posbar": make_posbar(base),
        "volume": make_volume(base),
        "balance": make_balance(base),
        "monoster": make_monoster(base),
        "playpaus": make_playpaus(),
        "numbers": make_numbers(False),
        "nums_ex": make_numbers(True),
        "text": make_text(),
        "pledit": make_pledit(),
        "eqmain": make_eqmain(),
        "gen": make_gen(),
        "genex": make_genex(),
    }
    sheets["main"] = compose_main(base, sheets)
    order = ["main", "titlebar", "cbuttons", "shufrep", "posbar", "volume", "balance", "monoster", "playpaus",
             "numbers", "nums_ex", "text", "pledit", "eqmain", "gen", "genex"]
    SHEETS.clear()
    for n in order:
        SHEETS[n] = save(sheets[n], n + ".bmp")
    write_text_files()
    names = [n + ".bmp" for n in order] + ["pledit.txt", "viscolor.txt", "readme.txt"]
    with zipfile.ZipFile(os.path.join(HERE, T.wsz), "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            zi = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(OUT, n), "rb") as fh:
                z.writestr(zi, fh.read())
    # genex.bmp completed for real Winamp and WACUP: all 24 colours, readable text, and the
    # standard 112x59 button and scrollbar layout (skins/genex_wacup.py).
    genex_wacup.process(os.path.join(HERE, T.wsz))
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


def ttf(size=11):
    for p in ("/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
              "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    try:
        return ImageFont.truetype("LiberationSans-Regular.ttf", size)
    except OSError:
        return ImageFont.load_default()


def preview_main(lit, state):
    S = SHEETS
    img = Image.new("RGB", (275, 116))
    img.paste(S["main"], (0, 0))
    blit(img, S["titlebar"], (27, 0 if lit else 15, 275, 14), 0, 0)
    tb = {"options": (0, 0), "minimize": (9, 0), "close": (18, 0), "shade": (0, 18)}
    tbp = {"options": (0, 9), "minimize": (9, 9), "close": (18, 9), "shade": (9, 18)}
    for k, (x, y) in TITLE_BTNS.items():
        if state["pressed"] == k:
            blit(img, S["titlebar"], (*tbp[k], 9, 9), x, y)
    for k, (x, w, h) in CB_SHEET.items():
        blit(img, S["cbuttons"], (x, 18 if state["pressed"] == k else 0, w, h), *CB_POS[k][:2])
    blit(img, S["cbuttons"], (114, 16 if state["pressed"] == "eject" else 0, 22, 16), 136, 89)
    for name, x0, on in (("eq", 0, state["eq"]), ("pl", 23, state["pl"])):
        pressed = state["pressed"] == name
        blit(img, S["shufrep"], (x0 + (46 if pressed else 0), 73 if on else 61, 23, 12), 219 + x0, 58)
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
    blit(img, nums, (99 if state["remaining"] else 90, 0, 9, 13), 38, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, nums, (9 * d, 0, 9, 13), x, 26)
    # title: text.bmp's blank cell across the box, then the title in pledit's font and colour
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    img_clip = img.crop((111, 22, 265, 36))
    dc = ImageDraw.Draw(img_clip)
    dc.text((0, 29 - 22), state["title"], fill=T.pledit["Normal"], font=ttf(11), anchor="lm")
    img.paste(img_clip, (111, 22))
    draw_bitmap_text(img, "256", 111, 43)
    draw_bitmap_text(img, "48", 156, 43)
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
    p = T.pledit
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=p["NormalBG"])
    font = ttf(11)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=p["SelectedBG"])
        col = p["Current"] if i == 1 else p["Normal"]
        d.text((lx + 2, y + 7), f"{i + 1}. {txt}", fill=col, font=font, anchor="lm")
        d.text((lx + lw - 3 - d.textlength(dur, font=font), y + 7), dur, fill=col, font=font, anchor="lm")
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


def preview_gen(lit, w, h, title, pressed_close=False, lyrics=None):
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
    if lyrics is not None:
        # the lyrics window: the gen frame with pledit's colours inside
        p = T.pledit
        inner = Image.new("RGB", (pw, ph), p["NormalBG"])
        d = ImageDraw.Draw(inner)
        font = ttf(11)
        for i, line in enumerate(lyrics):
            y = 10 + i * 17
            if y + 10 > ph:
                break
            d.text((pw / 2, y + 6), line, fill=p["Current"] if i == 4 else p["Normal"], font=font, anchor="mm")
        img.paste(inner, (11, 20))
        return img
    # a stand-in picture
    pic = wallpaper(pw, ph, 40) if T.glass else None
    if pic is None:
        X, Y = coords(np.zeros((ph, pw, 1)))
        t = (X / pw * 0.6 + Y / ph * 0.4)[..., None]
        pic = np.array((90, 200, 250), np.float32) * (1 - t) + np.array((0, 122, 255), np.float32) * t
    img.paste(Image.fromarray(np.clip(pic, 0, 255).astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("Glass Harbor - Low Tide", "4:12"), ("Paper Planes - Morning Air", "3:47"),
            ("Signal Lights - Blue Hour", "5:03"), ("The Quiet Set - Halflight", "2:58"),
            ("North Pier - Weathervane", "6:21"), ("Field Notes - Clear Skies", "3:33"),
            ("Satellite - Small Hours", "4:40"), ("Lumen - Prism", "3:09"),
            ("Weekend Club - Long Summer", "5:51"), ("Cloudline - Drift", "4:05"),
            ("Harbour Lights - Return", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=f"Glass Harbor - Low Tide (iOS {T.ver})", bars=bars)
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
    if T.v2:
        # the user's screen: the docked stack with a tall gen-framed lyrics window beside it
        lyr = ["(instrumental)", "", "Light through the harbour glass,", "the tide goes out slow,",
               "and every window in the town", "holds a little of the glow.", "", "Count the boats back in,",
               "count the lamps along the pier,", "the night is only blue", "because you are still here.", "",
               "Light through the harbour glass,", "the tide comes in again,", "and all the little windows",
               "hold the morning now and then.", "", "(instrumental)", "", "", "", "", "", "", ""]
        side = preview_gen(True, 275, 464, "lyrics", lyrics=lyr)
        out = Image.new("RGB", (275 * 3 + gap * 4, cols[0].height + gap * 2), (60, 60, 64))
        out.paste(cols[0], (gap, gap))
        out.paste(side, (275 + 2 * gap, gap))
        out.paste(cols[1], (550 + 3 * gap, gap))
    else:
        out = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), (60, 60, 64))
        out.paste(cols[0], (gap, gap))
        out.paste(cols[1], (275 + 2 * gap, gap))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, f"preview-{T.key}.png"))


def check_sizes():
    want = {"main": (275, 116), "titlebar": (344, 87), "cbuttons": (136, 36), "shufrep": (92, 85),
            "posbar": (307, 10), "volume": (68, 433), "balance": (68, 433), "monoster": (56, 24),
            "playpaus": (48, 9), "numbers": (99, 13), "nums_ex": (108, 13), "text": (155, 18),
            "pledit": (280, 186), "eqmain": (275, 315), "gen": (194, 109), "genex": (256, 64)}
    for n, size in want.items():
        assert SHEETS[n].size == size, (n, SHEETS[n].size)
        assert SHEETS[n].mode == "RGB"
    # text.bmp's space cell must be exactly the title box colour (the app tiles it there)
    t = np.asarray(SHEETS["text"])[0:6, 150:155]
    m = np.asarray(SHEETS["main"])[22:36, 111:265]
    assert (t == t[0, 0]).all() and (m == t[0, 0]).all(), "title box isn't the space cell's colour"


def run(key):
    global T, OUT
    T = make_theme(key)
    OUT = os.path.join(HERE, "out", key)
    os.makedirs(OUT, exist_ok=True)
    build()
    check_sizes()
    gen_letters()
    preview()
    print(f"{key}: {T.wsz}, preview-{key}.png")


if __name__ == "__main__":
    if "--list" in sys.argv[1:]:
        print("\n".join(THEME_KEYS))
        sys.exit(0)
    keys = [a.lower() for a in sys.argv[1:]] or THEME_KEYS
    for k in keys:
        if k not in THEME_KEYS:
            sys.exit(f"unknown theme {k!r}; themes: {', '.join(THEME_KEYS)}")
        run(k)
