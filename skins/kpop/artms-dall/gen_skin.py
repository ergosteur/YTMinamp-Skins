#!/usr/bin/python3
"""ARTMS Dall: a personal, private Winamp 2.x skin themed on ARTMS's first album "Dall"
("Devine All Love & Live", title track "Virtual Angel"). Never published.

Forked from skins/ember/gen_skin.py (same sheets, layouts and preview logic). The look: a
periwinkle -> lilac -> pink pastel body with glitter grain, pearl-chrome bubble buttons with
deep violet glyphs, deep violet glass displays with pearl-pink digits, the real ARTMS wordmark
plus our own italic "<Dall>" pixel lettering in the titlebar, and the album cover hazed into the
main window (one member's face in the free bottom-right corner).

Assets read at generation time (never copied here): source/cover.webp (the album cover) and the
ARTMS wordmark ink from objekts-archive's Atom02 template. ARTMS logo, album art and photos are
(c) MODHAUS; private use only.

Writes the sheets to out/, zips them flat into ARTMS-Dall.wsz and draws preview.png (the windows
assembled from the sprites at their real positions, 2x). Deterministic (fixed seeds).
"""

import os
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import sys
sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py, which finishes each .wsz
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
COVER = os.path.join(HERE, "source", "cover.webp")
LOGO_INK = "/home/matt/gitea/ergosteur/objekts-archive/back_templates/Atom02/template-ink.png"
SERIF_ITALIC = "/usr/share/fonts/google-noto-vf/NotoSerif-Italic[wght].ttf"

# ------------------------------------------------------------------------------------------
# Palette
# ------------------------------------------------------------------------------------------

PINK = (244, 182, 214)
LILAC = (201, 168, 232)
LAVENDER = (179, 157, 219)
PERI = (143, 168, 240)
SKY = (168, 212, 245)
PEARL = (248, 244, 251)
WHITE = (255, 255, 255)

INK = (52, 28, 104)          # deep violet glyphs on pearl
INK_SOFT = (104, 82, 158)    # quieter labels
INK_ON = (150, 30, 108)      # lit toggle labels (deep rose)
EDGE = (124, 100, 184)       # outlines of buttons and displays
EDGE_LO = (146, 124, 204)    # soft bevel shadow
DISP = (30, 20, 56)          # display glass
DISP_RIM = (70, 52, 120)
DTXT = (255, 224, 242)       # display text (pearl pink)
DTXT_TOP = (255, 250, 255)
DTXT_BOT = (255, 176, 216)
DTXT_DIM = (176, 150, 222)   # display labels
DTXT_OFF = (74, 58, 116)     # unlit display text
SEP = (255, 0, 255)          # gen.bmp letter separators (never shown)

# slider / level ramp: saturated enough to read on the pastel body
LEVEL = [(118, 146, 238), (146, 134, 232), (180, 128, 226), (222, 128, 202), (244, 140, 196)]


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def light(c, t=0.35):
    return lerp(c, PEARL, t)


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def new(w, h, col=PEARL):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[y:y + h, x:x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def outline(a, x, y, w, h, col):
    rect(a, x, y, w, 1, col)
    rect(a, x, y + h - 1, w, 1, col)
    rect(a, x, y, 1, h, col)
    rect(a, x + w - 1, y, 1, h, col)


def raised(a, x, y, w, h, hi=WHITE, lo=EDGE_LO):
    rect(a, x, y, w, 1, hi)
    rect(a, x, y, 1, h, hi)
    rect(a, x, y + h - 1, w, 1, lo)
    rect(a, x + w - 1, y, 1, h, lo)


def composite(a, x, y, alpha, col, opacity=1.0):
    """Blends a solid colour (or an HxWx3 array) into a at (x, y) through alpha (float HxW)."""
    h, w = alpha.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(a.shape[1], x + w), min(a.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    al = alpha[y0 - y:y1 - y, x0 - x:x1 - x, None] * opacity
    dst = a[y0:y1, x0:x1].astype(np.float64)
    src = np.array(col, dtype=np.float64)
    if src.ndim == 3:
        src = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a[y0:y1, x0:x1] = np.round(dst * (1 - al) + src * al).astype(np.int32)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


# ------------------------------------------------------------------------------------------
# Body: pastel gradient, glitter grain, the cover photo hazed in
# ------------------------------------------------------------------------------------------

BODY_STOPS = [light(PERI, 0.30), light(LAVENDER, 0.32), light(LILAC, 0.30), light(PINK, 0.28)]


def gradient(w, h, stops=BODY_STOPS, ox=0, oy=0, W=None, H=None):
    """Diagonal gradient (top-left periwinkle to bottom-right pink) over a W x H window, of which
    this canvas is the w x h piece at (ox, oy)."""
    W = W or w
    H = H or h
    yy, xx = np.mgrid[0:h, 0:w]
    t = np.clip(((xx + ox) / max(1, W - 1)) * 0.62 + ((yy + oy) / max(1, H - 1)) * 0.38, 0, 1)
    n = len(stops) - 1
    i = np.minimum(n - 1, (t * n).astype(int))
    f = (t * n - i)[..., None]
    S = np.array(stops, dtype=np.float64)
    return np.round(S[i] * (1 - f) + S[i + 1] * f).astype(np.int32)


def glitter(a, x, y, w, h, seed, amp=2.5, density=0.012):
    """Fine grain plus sparse bright specks (some faintly pink or blue), like the package's glitter."""
    rng = np.random.default_rng(seed)
    g = rng.normal(0, 1, (h, w)) * amp
    a[y:y + h, x:x + w] += np.round(g).astype(np.int32)[:, :, None]
    sp = rng.random((h, w)) < density
    tints = np.array([WHITE, WHITE, WHITE, (255, 214, 238), (214, 228, 255)], dtype=np.float64)
    which = rng.integers(0, len(tints), (h, w))
    strength = rng.uniform(0.35, 0.8, (h, w))
    reg = a[y:y + h, x:x + w].astype(np.float64)
    col = tints[which]
    mix = (sp * strength)[..., None]
    a[y:y + h, x:x + w] = np.round(reg * (1 - mix) + col * mix).astype(np.int32)


_cover = None


def cover():
    global _cover
    if _cover is None:
        _cover = Image.open(COVER).convert("RGB")
    return _cover


def cover_layer(scale, anchor_src, anchor_dst, size, blur=0.0):
    """The cover scaled by `scale`, with source point anchor_src landing on anchor_dst, on a canvas
    of `size`; returns (rgb float HxWx3, coverage HxW with feathered edges)."""
    im = cover()
    sw, sh = max(1, round(im.width * scale)), max(1, round(im.height * scale))
    small = im.resize((sw, sh), Image.LANCZOS)
    if blur:
        small = small.filter(ImageFilter.GaussianBlur(blur))
    W, H = size
    ox = round(anchor_dst[0] - anchor_src[0] * scale)
    oy = round(anchor_dst[1] - anchor_src[1] * scale)
    rgb = np.zeros((H, W, 3))
    cov = np.zeros((H, W))
    src = np.asarray(small).astype(np.float64)
    feather = max(3, round(min(sw, sh) * 0.08))
    yy, xx = np.mgrid[0:sh, 0:sw]
    edge = np.minimum.reduce([xx, yy, sw - 1 - xx, sh - 1 - yy]).astype(np.float64)
    fe = np.clip(edge / feather, 0, 1)
    x0, y0 = max(0, ox), max(0, oy)
    x1, y1 = min(W, ox + sw), min(H, oy + sh)
    if x1 > x0 and y1 > y0:
        rgb[y0:y1, x0:x1] = src[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
        cov[y0:y1, x0:x1] = fe[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return rgb, cov


def control_mask(rects, size, pad=1, soft=5):
    W, H = size
    m = np.zeros((H, W))
    for x, y, w, h in rects:
        m[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad] = 1
    img = Image.fromarray(np.round(m * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(soft / 2))
    return np.maximum(m, np.asarray(img) / 255)


def lay(a, rgb, weight):
    w = np.clip(weight, 0, 1)[..., None]
    a[:] = np.round(a * (1 - w) + rgb * w).astype(np.int32)


def wash(rgb, t=0.25, col=PEARL):
    """Pushes a photo toward pearl, lifting it into the pastel body (an airy, bloomed look)."""
    return rgb * (1 - t) + np.array(col, dtype=np.float64) * t


# ------------------------------------------------------------------------------------------
# Pixel fonts
# ------------------------------------------------------------------------------------------

def G(*rows):
    return list(rows)


# 5-row font for text.bmp, titles and gen.bmp's letters (Ember's).
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

# 7x11 Didone-flavoured digits (thick stems, hairline joins) for numbers.bmp; sheared to an
# italic when drawn.
DIGITS = {
    0: G("..###..", ".##.##.", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##",
         "##...##", ".##.##.", "..###.."),
    1: G("...##..", "..###..", ".#.##..", "...##..", "...##..", "...##..", "...##..", "...##..",
         "...##..", "...##..", ".######"),
    2: G("..###..", ".#..##.", "#....##", ".....##", "....##.", "...##..", "..##...", ".##....",
         "##.....", "#.....#", "#######"),
    3: G("..###..", ".#..##.", ".....##", ".....##", "....##.", "..###..", "....##.", ".....##",
         "#....##", ".#..##.", "..###.."),
    4: G("....##.", "...###.", "..#.##.", ".#..##.", "#...##.", "#######", "....##.", "....##.",
         "....##.", "....##.", "...####"),
    5: G("#######", "##.....", "##.....", "##.###.", "###..##", ".....##", ".....##", ".....##",
         "#....##", ".#..##.", "..###.."),
    6: G("...###.", "..##...", ".##....", "##.....", "##.###.", "###..##", "##...##", "##...##",
         "##...##", ".##.##.", "..###.."),
    7: G("#######", "#....##", ".....#.", "....##.", "....##.", "...##..", "...##..", "..##...",
         "..##...", "..##...", "..##..."),
    8: G("..###..", ".##.##.", "##...##", ".##.##.", "..###..", ".##.##.", "##...##", "##...##",
         "##...##", ".##.##.", "..###.."),
    9: G("..###..", ".##.##.", "##...##", "##...##", "##...##", "##..###", ".###.##", ".....##",
         "....##.", "...##..", ".###..."),
}


def italic_shift(r, rows=11):
    """Columns to push row r right for the italic slant (top rows lean right by 1)."""
    return 1 if r < rows // 2 else 0


def draw_digit(a, n, x, y, bg=DISP):
    g = DIGITS[n]
    rows = len(g)
    for r, row in enumerate(g):
        col = ramp([DTXT_TOP, DTXT, DTXT_BOT], r / (rows - 1))
        sh = italic_shift(r, rows)
        for k, ch in enumerate(row):
            if ch == "#":
                px(a, x + k + sh, y + r, col)


# Our own italic serif "<Dall>" for the titlebar: 9 rows, hairline joins, 2px stems, sheared.
DALL = {
    "<": G("....", "...#", "..#.", ".#..", "#...", ".#..", "..#.", "...#", "...."),
    "D": G("#####....", ".##..##..", ".##...##.", ".##...##.", ".##...##.", ".##...##.", ".##...##.",
           ".##..##..", "#####...."),
    "a": G(".......", ".......", ".......", "..##.##", ".#..##.", "#...##.", "#...##.", "#..###.",
           ".##..##"),
    "l": G("###.", ".##.", ".##.", ".##.", ".##.", ".##.", ".##.", ".##.", "..##"),
    ">": G("....", "#...", ".#..", "..#.", "...#", "..#.", ".#..", "#...", "...."),
}
DALL_SHEAR = lambda r: (8 - r) // 3   # rows 0-2 +2, 3-5 +1, 6-8 0


def dall_width(s, gap=1):
    return sum(len(DALL[c][0]) for c in s) + gap * (len(s) - 1) + 2


def draw_dall(a, s, x, y, cols, shadow=None, gap=1, opacity=1.0):
    """cols(r) gives the row colour (chrome banding); shadow drawn 1px down-right first."""
    for pass_ in ("shadow", "ink"):
        if pass_ == "shadow" and shadow is None:
            continue
        cx = x
        for c in s:
            g = DALL[c]
            for r, row in enumerate(g):
                for k, ch in enumerate(row):
                    if ch != "#":
                        continue
                    X, Y = cx + k + DALL_SHEAR(r), y + r
                    if pass_ == "shadow":
                        if 0 <= Y + 1 < a.shape[0] and 0 <= X + 1 < a.shape[1]:
                            a[Y + 1, X + 1] = lerp(tuple(a[Y + 1, X + 1]), shadow, 0.75 * opacity)
                    else:
                        if 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]:
                            a[Y, X] = lerp(tuple(a[Y, X]), cols(r), opacity)
            cx += len(g[0]) + gap


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


# ------------------------------------------------------------------------------------------
# Ink: the ARTMS wordmark, and the "Devine All Love & Live" tagline
# ------------------------------------------------------------------------------------------

_logo = {}


def logo_alpha(h):
    """The horizontal ARTMS wordmark (top left of the Atom02 template ink), h rows tall."""
    if h not in _logo:
        al = np.asarray(Image.open(LOGO_INK).convert("RGBA"))[..., 3].astype(np.float64) / 255
        top = al[:600, :1000]
        m = top > 0.5
        rows = np.nonzero(m.any(1))[0]
        cols = np.nonzero(m.any(0))[0]
        crop = top[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
        w = max(1, round(crop.shape[1] * h / crop.shape[0]))
        img = Image.fromarray(np.round(crop * 255).astype(np.uint8), "L").resize((w, h), Image.LANCZOS)
        out = np.clip(np.asarray(img).astype(np.float64) / 255, 0, 1)
        _logo[h] = np.clip((out - 0.12) / 0.72, 0, 1)   # firm the edges up
    return _logo[h]


def tagline_alpha(h, text="Devine All Love & Live", weight="Medium Italic"):
    """The album's tagline in a serif italic, rendered large and boxed down to h rows."""
    f = ImageFont.truetype(SERIF_ITALIC, 96)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    l, t, r, b = f.getbbox(text)
    img = Image.new("L", (r - l + 8, b - t + 8), 0)
    ImageDraw.Draw(img).text((4 - l, 4 - t), text, fill=255, font=f)
    arr = np.asarray(img)
    m = arr > 40
    rows = np.nonzero(m.any(1))[0]
    cols = np.nonzero(m.any(0))[0]
    img = img.crop((cols.min(), rows.min(), cols.max() + 1, rows.max() + 1))
    w = max(1, round(img.width * h / img.height))
    small = img.resize((w, h), Image.LANCZOS)
    out = np.asarray(small).astype(np.float64) / 255
    return np.clip(out * 1.35, 0, 1)


def sparkle(a, cx, cy, r, col, opacity=1.0):
    """A four-point sparkle (the sticker sheet's), arms r long, fading outward."""
    composite(a, cx, cy, np.ones((1, 1)), col, opacity)
    for d in range(1, r + 1):
        f = (1 - (d - 1) / r) * opacity
        for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
            composite(a, cx + dx, cy + dy, np.ones((1, 1)), col, f)
    if r >= 3:
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            composite(a, cx + dx, cy + dy, np.ones((1, 1)), col, 0.35 * opacity)


# ------------------------------------------------------------------------------------------
# Pearl bubbles: buttons, toggles, thumbs
# ------------------------------------------------------------------------------------------

PEARL_UP = dict(top=WHITE, mid=(240, 233, 250), bot=(206, 192, 238), line=EDGE, irid=0.30)
PEARL_DOWN = dict(top=(186, 166, 226), mid=(206, 190, 238), bot=(232, 222, 248), line=(92, 66, 156), irid=0.15)
PINK_UP = dict(top=(255, 240, 248), mid=(250, 200, 228), bot=(236, 150, 200), line=(170, 80, 150), irid=0.15)
PINK_DOWN = dict(top=(220, 130, 186), mid=(236, 162, 208), bot=(250, 200, 228), line=(130, 50, 116), irid=0.08)


def round_mask(w, h, r):
    """Coverage (0..1) of a rounded rectangle, 4x supersampled."""
    s = 4
    yy, xx = np.mgrid[0:h * s, 0:w * s]
    fx = (xx + 0.5) / s
    fy = (yy + 0.5) / s
    dx = np.maximum(0, np.maximum(r - fx, fx - (w - r)))
    dy = np.maximum(0, np.maximum(r - fy, fy - (h - r)))
    inside = (dx * dx + dy * dy) <= r * r
    return inside.reshape(h, s, w, s).mean(axis=(1, 3))


def bubble(a, x, y, w, h, st=PEARL_UP, r=3):
    """A glossy pearl bubble over whatever is already at (x, y): shaded top to bottom, a pink sheen
    at the left edge and a blue one at the right (iridescence), a 1px outline, a white gloss line."""
    outer = round_mask(w, h, r)
    inner = round_mask(w - 2, h - 2, max(1, r - 1))
    face = np.zeros((h, w, 3))
    for row in range(h):
        t = row / max(1, h - 1)
        c = ramp([st["top"], st["mid"], st["mid"], st["bot"]], t)
        face[row, :] = c
    # iridescent edges
    xs = np.arange(w)
    left = np.clip(1 - xs / 4, 0, 1)[None, :, None] * st["irid"]
    right = np.clip(1 - (w - 1 - xs) / 4, 0, 1)[None, :, None] * st["irid"]
    face = face * (1 - left) + np.array((255, 196, 228)) * left
    face = face * (1 - right) + np.array((186, 216, 255)) * right
    # outline = outer minus inner
    ring = np.zeros((h, w))
    ring[:] = outer
    inn = np.zeros((h, w))
    inn[1:h - 1, 1:w - 1] = inner
    line_al = np.clip(outer - inn, 0, 1)
    region = a[y:y + h, x:x + w].astype(np.float64)
    region = region * (1 - inn[..., None]) + face * inn[..., None]
    region = region * (1 - line_al[..., None]) + np.array(st["line"]) * line_al[..., None]
    a[y:y + h, x:x + w] = np.round(region).astype(np.int32)
    # gloss: a white line under the top edge, short of the corners
    if st is PEARL_UP or st is PINK_UP:
        for k in range(r, w - r):
            px(a, x + k, y + 1, lerp(tuple(a[y + 1, x + k]), WHITE, 0.9))


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


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: a small pearl bubble."""
    bubble(a, x, y, 9, 9, PEARL_DOWN if pressed else PEARL_UP, r=2)
    ink = INK if lit else (120, 104, 156)
    if pressed:
        ink = INK_ON
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        for dx, dy in [(4, 3), (3, 4), (4, 4), (5, 4), (4, 5)]:
            px(a, X + dx, Y + dy, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 3, 5, 1, ink)
        rect(a, X + 2, Y + 5, 5, 1, lerp(ink, PEARL, 0.5))
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


# ------------------------------------------------------------------------------------------
# Titlebars
# ------------------------------------------------------------------------------------------

BAR_LIT = [(206, 212, 255), (146, 158, 238), (116, 110, 212), (100, 84, 194), (116, 88, 196),
           (160, 122, 210)]
BAR_DIM = [lerp(c, (200, 194, 214), 0.7) for c in BAR_LIT]
BAR_PINK = (236, 150, 204)


def bar_rows(h, lit):
    """The titlebars' chrome banding, top to bottom (flat across x, so tiles join anywhere)."""
    stops = BAR_LIT if lit else BAR_DIM
    rows = [ramp(stops, r / (h - 1)) for r in range(h)]
    rows[0] = (236, 238, 255) if lit else (226, 224, 234)
    rows[-1] = (98, 76, 168) if lit else (150, 142, 172)
    return rows


def bar(w, h, lit, pink_right=False):
    a = new(w, h)
    rows = bar_rows(h, lit)
    for r in range(h):
        a[r, :] = rows[r]
    if pink_right:
        # a soft pink bloom toward the right end (single, untiled bars only)
        xs = np.clip((np.arange(w) - w * 0.45) / (w * 0.55), 0, 1) ** 1.4 * (0.32 if lit else 0.12)
        a[:] = np.round(a * (1 - xs[None, :, None]) + np.array(BAR_PINK) * xs[None, :, None]).astype(np.int32)
        xs2 = np.clip(1 - np.arange(w) / (w * 0.3), 0, 1) * (0.18 if lit else 0.06)
        a[:] = np.round(a * (1 - xs2[None, :, None]) + np.array(SKY) * xs2[None, :, None]).astype(np.int32)
    return a


TXT_LIT = WHITE
TXT_DIM = (240, 236, 248)
SHADOW_LIT = (60, 36, 120)
SHADOW_DIM = (150, 140, 176)


def chrome_rows(lit):
    """Row colours for the chrome "<Dall>" lettering: bright top, a lavender band, pink below."""
    if lit:
        return lambda r: ramp([WHITE, WHITE, (232, 226, 255), (255, 242, 250), (255, 212, 236)], r / 8)
    return lambda r: ramp([(248, 246, 252), (230, 226, 240), (236, 230, 244)], r / 8)


def hrule(a, x, y, w, lit):
    if w <= 0:
        return
    rect(a, x, y, w, 1, (250, 248, 255) if lit else (232, 230, 240))
    rect(a, x, y + 1, w, 1, (96, 76, 168) if lit else (160, 152, 180))


def main_titlebar(lit):
    a = bar(275, 14, lit, pink_right=True)
    logo = logo_alpha(9)
    lw = logo.shape[1]
    dw = dall_width("<Dall>")
    total = lw + 7 + dw
    lx = (275 - total) // 2
    hrule(a, 20, 6, lx - 8 - 20, lit)
    hrule(a, lx + total + 8, 6, 240 - (lx + total + 8), lit)
    for sx in (lx - 5, lx + total + 4):
        sparkle(a, sx, 6, 2, WHITE if lit else (240, 238, 246), 1.0 if lit else 0.6)
    composite(a, lx + 1, 3, logo, SHADOW_LIT if lit else SHADOW_DIM, 0.8)
    composite(a, lx, 2, logo, TXT_LIT if lit else TXT_DIM)
    draw_dall(a, "<Dall>", lx + lw + 7, 2, chrome_rows(lit), shadow=SHADOW_LIT if lit else SHADOW_DIM)
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, (236, 228, 248))
    for r in range(43):
        a[r, :] = lerp((246, 240, 252), (222, 210, 244), r / 42)
    outline(a, 0, 0, 8, 43, EDGE)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, (246, 178, 214))
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, INK_ON if on else INK_SOFT)
    return a


def make_titlebar():
    a = new(344, 87)
    a[:] = gradient(344, 87)
    for kind, x, y, py_ in [("options", 0, 0, 9), ("minimize", 9, 0, 9), ("close", 18, 0, 9)]:
        b = bar(9, 14, True)[3:12].copy()
        mini_button(b, 0, 0, kind, True)
        a[y:y + 9, x:x + 9] = b
        b = bar(9, 14, True)[3:12].copy()
        mini_button(b, 0, 0, kind, True, pressed=True)
        a[py_:py_ + 9, x:x + 9] = b
    b = bar(9, 14, True)[3:12].copy()
    mini_button(b, 0, 0, "shade", True)
    a[18:27, 0:9] = b
    b = bar(9, 14, True)[3:12].copy()
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

# Where every drawn element sits on the main window (x, y, w, h): the photo fades under these.
MAIN_CONTROLS = [
    (0, 0, 275, 14), (10, 22, 8, 43), (20, 19, 86, 44), (108, 20, 161, 17), (108, 39, 161, 16),
    (107, 57, 68, 13), (177, 57, 38, 13), (219, 58, 46, 12), (16, 72, 248, 10), (16, 88, 114, 18),
    (136, 89, 22, 16), (164, 89, 75, 15),
]
TAG_Y, TAG_H = 107, 7       # the free strip under the transport buttons
FACE_C = (257, 100)         # the free bottom-right corner, where a face shows
FACE_SRC = (488, 132)       # that face in the cover (the member top right, head tilted)


def display_box(a, x, y, w, h):
    """Deep violet glass, a violet rim and a pearl highlight just outside it."""
    rect(a, x, y, w, h, DISP)
    outline(a, x - 1, y - 1, w + 2, h + 2, DISP_RIM)
    rect(a, x - 2, y + h + 1, w + 4, 1, (252, 248, 255))
    rect(a, x + w + 1, y - 2, 1, h + 4, (252, 248, 255))
    rect(a, x - 2, y - 2, w + 4, 1, EDGE_LO)
    rect(a, x - 2, y - 2, 1, h + 4, EDGE_LO)


def main_photo(a):
    W, H = 275, 116
    ctrl = control_mask(MAIN_CONTROLS + [(16, TAG_Y, 140, TAG_H)], (W, H), pad=1, soft=6)
    # a soft haze of the whole cover, members' faces across the window
    haze, hc = cover_layer(275 / 640 * 1.05, (320, 260), (137, 58), (W, H), blur=1.2)
    lay(a, wash(haze, 0.30), hc * 0.50 * (1 - 0.85 * ctrl))
    # one face, sharper, in the bottom-right corner
    face, fc = cover_layer(0.27, FACE_SRC, FACE_C, (W, H), blur=0.0)
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.hypot((xx - FACE_C[0]) / 1.15, (yy - FACE_C[1]))
    focus = np.clip(1.35 - d / 15, 0, 0.92)
    lay(a, wash(face, 0.10), fc * focus * (1 - ctrl))


def make_main():
    a = gradient(275, 116)
    glitter(a, 0, 0, 275, 116, seed=11)
    main_photo(a)
    raised(a, 0, 0, 275, 116, WHITE, EDGE)
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # left display: indicator, time, analyzer
    display_box(a, 21, 20, 84, 42)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, DTXT)
    # right display: title row, then kbps/kHz/mono/stereo row
    display_box(a, 109, 21, 159, 15)
    display_box(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, DTXT_DIM)
    draw_text(a, TINY, "KHZ", 169, 44, DTXT_DIM)

    # the tagline under the transport buttons
    tag = tagline_alpha(TAG_H)
    composite(a, 19, TAG_Y + 1, tag, WHITE, 0.7)
    composite(a, 18, TAG_Y, tag, INK, 0.92)
    # sparkles: by the face, and one beside the tagline
    sparkle(a, 244, 92, 3, WHITE)
    sparkle(a, 268, 110, 2, WHITE, 0.9)
    sparkle(a, 18 + tag.shape[1] + 5, TAG_Y + 3, 2, (255, 255, 255), 0.95)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36)
# ------------------------------------------------------------------------------------------


def transport_icon(a, kind, x, y, w, h, pressed):
    ink = INK_ON if pressed else INK
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
    a = new(136, 36)
    specs = [("previous", 0, 23, 18, 16), ("play", 23, 23, 18, 39), ("pause", 46, 23, 18, 62),
             ("stop", 69, 23, 18, 85), ("next", 92, 22, 18, 108)]
    for kind, x, w, h, dx in specs:
        for pressed, y in ((False, 0), (True, 18)):
            a[y:y + h, x:x + w] = main[88:88 + h, dx:dx + w]
            bubble(a, x, y, w, h, PEARL_DOWN if pressed else PEARL_UP, r=5)
            transport_icon(a, kind, x, y, w, h, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        a[y:y + 16, 114:136] = main[89:105, 136:158]
        bubble(a, 114, y, 22, 16, PEARL_DOWN if pressed else PEARL_UP, r=5)
        transport_icon(a, "eject", 114, y, 22, 16, pressed)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle(a, x, y, w, h, label, on, pressed, r=4):
    st = (PINK_DOWN if pressed else PINK_UP) if on else (PEARL_DOWN if pressed else PEARL_UP)
    bubble(a, x, y, w, h, st, r=r)
    o = 1 if pressed else 0
    ink = INK_ON if on else INK_SOFT
    if on and pressed:
        ink = (110, 20, 80)
    tw = text_w(TINY, label)
    tx = x + (w - tw) // 2 + o
    ty = y + (h - 5) // 2 + o
    draw_text(a, TINY, label, tx, ty, ink)


def make_shufrep(main):
    a = new(92, 85)
    rep_bg = main[89:104, 210:238]
    shu_bg = main[89:104, 164:211]
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = rep_bg
        a[y:y + 15, 28:75] = shu_bg
        toggle(a, 0, y, 28, 15, "REPEAT", on, pressed)
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    eq_bg = main[58:70, 219:242]
    pl_bg = main[58:70, 242:265]
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        for y, on in ((61, False), (73, True)):
            a[y:y + 12, x:x + 23] = eq_bg if label == "EQ" else pl_bg
            toggle(a, x, y, 23, 12, label, on, pressed, r=3)
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, DISP)
    for y, on in ((0, True), (12, False)):
        col = DTXT if on else DTXT_OFF
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, DISP)
    tri_right(a, 2, 1, 7, DTXT)                       # playing
    rect(a, 9 + 2, 1, 2, 7, DTXT)                     # paused
    rect(a, 9 + 5, 1, 2, 7, DTXT)
    rect(a, 18 + 2, 2, 5, 5, DTXT)                    # stopped
    rect(a, 36, 0, 3, 9, DISP)                        # not working
    rect(a, 39 + 1, 3, 1, 3, PINK)                    # working
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, DISP)
    for n in range(10):
        draw_digit(a, n, 9 * n, 1)
    if ex:
        rect(a, 99 + 2, 6, 5, 1, DTXT)                # minus
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, DISP)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key, col * 5, row * 6, DTXT)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------

GROOVE = (226, 216, 244)


def groove(a, x, y, w, h):
    rect(a, x, y, w, h, GROOVE)
    outline(a, x, y, w, h, EDGE)
    rect(a, x + 1, y + 1, w - 2, 1, (204, 190, 232))   # inner shadow along the top


def make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    groove(a, 0, 3, 248, 4)
    for x in range(12, 240, 16):
        px(a, x, 5, (210, 196, 238))
    for x, sel in ((248, False), (278, True)):
        a[0:10, x:x + 29] = main[72:82, 100:129]
        bubble(a, x + 1, 0, 27, 10, PEARL_DOWN if sel else PEARL_UP, r=4)
        sparkle(a, x + 14, 5, 2, (238, 120, 184) if not sel else INK_ON)
    return a


def slider_thumbs(a, main):
    for x, sel in ((0, True), (15, False)):
        a[422:433, x:x + 14] = main[58:69, 140:154]
        bubble(a, x, 422, 14, 11, PEARL_DOWN if sel else PEARL_UP, r=4)
        rect(a, x + 6, 425, 2, 5, (236, 130, 190) if not sel else INK_ON)


def make_volume(main):
    a = new(68, 433)
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        level = (i + 1) / 28
        fill_to = 7 + round(level * 54)
        # a wedge that thickens to the right, filled through the pastel ramp
        for x in range(2, 66):
            hgt = 2 + round(4 * (x - 2) / 63)
            top = y + 10 - hgt
            if x < fill_to:
                col = ramp(LEVEL, (x - 2) / 63)
            else:
                col = GROOVE
            rect(a, x, top, 1, hgt, col)
            px(a, x, top - 1, EDGE if x >= fill_to else lerp(ramp(LEVEL, (x - 2) / 63), INK, 0.35))
        rect(a, 2, y + 10, 64, 1, EDGE)
        rect(a, 1, y + 9 - 1, 1, 3, EDGE)
        rect(a, 66, y + 3, 1, 8, EDGE)
    slider_thumbs(a, main)
    return a


def make_balance(main):
    a = new(68, 433)
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        t = i / 27
        reach = round(16 * t)
        groove(a, 11, y + 4, 34, 5)
        col = ramp(LEVEL, t) if i else (196, 180, 232)
        rect(a, 28 - max(1, reach), y + 5, 2 * max(1, reach) + 1, 3, col)
        rect(a, 28, y + 2, 1, 2, INK_SOFT)
    slider_thumbs(a, main)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
BAY = (16, 36, 245, 68)


def bay_row(r):
    """The slider bay's pearl glass, flat across x so the slider frames match it anywhere."""
    return ramp([(250, 246, 255), (238, 230, 250), (232, 222, 248), (244, 232, 248)], r / (BAY[3] - 1))


def eq_titlebar(lit):
    a = bar(275, 14, lit, pink_right=True)
    logo = logo_alpha(9)
    lw = logo.shape[1]
    title = "EQUALIZER"
    tw = text_w(FONT5, title)
    total = lw + 7 + tw
    lx = (275 - total) // 2
    hrule(a, 6, 6, lx - 8 - 6, lit)
    hrule(a, lx + total + 8, 6, 260 - (lx + total + 8), lit)
    for sx in (lx - 5, lx + total + 4):
        sparkle(a, sx, 6, 2, WHITE if lit else (240, 238, 246), 1.0 if lit else 0.6)
    composite(a, lx + 1, 3, logo, SHADOW_LIT if lit else SHADOW_DIM, 0.8)
    composite(a, lx, 2, logo, TXT_LIT if lit else TXT_DIM)
    draw_text(a, FONT5, title, lx + lw + 7, 4, TXT_LIT if lit else TXT_DIM,
              shadow=SHADOW_LIT if lit else SHADOW_DIM)
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    """14x63 slot on the bay's glass; the lit column rises with the value (n of 0..27)."""
    for r in range(63):
        a[y + r, x:x + 14] = bay_row(r + 2)
    rect(a, x + 4, y + 1, 6, 61, GROOVE)
    outline(a, x + 4, y + 1, 6, 61, EDGE)
    v = n / 27
    top = round((1 - v) * 51) + 5
    for r in range(top, 61):
        rect(a, x + 5, y + r, 4, 1, ramp(LEVEL, (61 - r) / 56))
    # the zero mark
    rect(a, x + 1, y + 31, 2, 1, INK_SOFT)
    rect(a, x + 11, y + 31, 2, 1, INK_SOFT)


EQ_CONTROLS = [(0, 0, 275, 14), (14, 18, 58, 12), (85, 16, 115, 21), (217, 18, 44, 12), BAY,
               (10, 104, 255, 9)]


def eq_body():
    W, H = 275, 116
    a = gradient(W, H)
    glitter(a, 0, 0, W, H, seed=23)
    ctrl = control_mask(EQ_CONTROLS, (W, H), pad=1, soft=5)
    haze, hc = cover_layer(275 / 640 * 1.1, (300, 470), (150, 60), (W, H), blur=1.4)
    lay(a, wash(haze, 0.30), hc * 0.45 * (1 - 0.9 * ctrl))
    return a


def make_eqmain():
    a = new(275, 315)
    a[:] = gradient(275, 315)
    glitter(a, 0, 116, 275, 199, seed=24, amp=1.5, density=0.004)
    a[0:116] = eq_body()
    raised(a, 0, 0, 275, 116, WHITE, EDGE)
    a[0:14, :] = eq_titlebar(True)
    # graph window
    display_box(a, 86, 17, 113, 19)
    # slider bay: pearl glass
    bx, by, bw, bh = BAY
    for r in range(bh):
        a[by + r, bx:bx + bw] = bay_row(r)
    outline(a, bx, by, bw, bh, EDGE_LO)
    rect(a, bx + 1, by + 1, bw - 2, 1, WHITE)
    rect(a, 39, 37, 1, 66, (214, 202, 240))
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, INK_SOFT)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    text_center(a, TINY, "PREAMP", 28, 106, INK, shadow=(250, 244, 255))
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, INK, shadow=(250, 244, 255))
    eq = a[0:116].copy()

    # under the window: buttons
    b = eq[3:12, 264:273].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = b
    on_bg, auto_bg = eq[18:30, 14:40], eq[18:30, 40:72]
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        a[119:131, x:x + w] = on_bg if label == "ON" else auto_bg
        toggle(a, x, 119, w, 12, label, on, pressed, r=3)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    for y, sel in ((164, False), (176, True)):
        for r in range(11):
            a[y + r, 0:11] = bay_row(30 + r)
        bubble(a, 0, y, 11, 11, PEARL_DOWN if sel else PEARL_UP, r=3)
        rect(a, 3, y + 5, 5, 1, (236, 130, 190) if not sel else INK_ON)
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        a[y:y + 12, 224:268] = eq[18:30, 217:261]
        toggle(a, 224, y, 44, 12, "PRESETS", False, pressed, r=3)
    # graph
    rect(a, 0, 294, 113, 19, DISP)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, (54, 40, 92))
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, (66, 50, 110))
    for r in range(19):
        px(a, 115, 294 + r, ramp([(255, 200, 230), PINK, LILAC, PERI, SKY], r / 18))
    for x in range(113):
        px(a, x, 314, (200, 176, 240) if x % 3 != 2 else DISP)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

TITLE_Y = 5       # FONT5 glyph top in 20px bars, level with gen.bmp's letters (5..9)
RULE_Y = 7
LIST_BG = (0x1E, 0x14, 0x38)
SIDE_COLS = [WHITE, (236, 230, 250), (226, 216, 246), (218, 206, 244), (214, 200, 242), (214, 200, 242),
             (216, 204, 244), (220, 208, 244), (224, 214, 246), (210, 196, 238), EDGE, DISP_RIM]
FRAME_BOT = [(236, 228, 250), (222, 210, 246), (214, 200, 242), (220, 204, 242), (230, 206, 238)]


def bar20(w, lit, rule=True, x0=0, x1=None):
    a = bar(w, 20, lit)
    if rule:
        hrule(a, x0, RULE_Y, (w if x1 is None else x1) - x0, lit)
    return a


def frame_side(w, h, cols):
    t = new(w, h)
    for k, c in enumerate(cols[:w]):
        t[:, k] = c
    return t


def frame_bottom(w, h=38, sparkly=False, seed=0):
    t = new(w, h)
    for r in range(h):
        t[r, :] = ramp(FRAME_BOT, r / (h - 1))
    if sparkly:
        glitter(t, 0, 2, w, h - 4, seed=seed, amp=0.0, density=0.01)
    rect(t, 0, h - 1, w, 1, EDGE)
    return t


def pl_button(t, x, y, w, h, label):
    bubble(t, x, y, w, h, PEARL_UP, r=4)
    text_center(t, TINY, label, x + w // 2, y + (h - 5) // 2, INK)


def mini_transport_icon(a, kind, x, y):
    ink = INK
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


def make_pledit():
    a = new(280, 186)
    a[:] = gradient(280, 186)
    for lit, y in ((True, 0), (False, 21)):
        # top tile
        a[y:y + 20, 127:152] = bar20(25, lit)
        # top-left corner
        t = bar20(25, lit, x0=4)
        rect(t, 0, 0, 1, 20, WHITE if lit else (230, 228, 238))
        a[y:y + 20, 0:25] = t
        # title (100 wide, centred)
        t = bar20(100, lit, rule=False)
        title = "DALL PLAYLIST"
        tw = text_w(FONT5, title)
        tx = (100 - tw) // 2
        hrule(t, 0, RULE_Y, tx - 7, lit)
        hrule(t, tx + tw + 7, RULE_Y, 100 - (tx + tw + 7), lit)
        sparkle(t, tx - 4, RULE_Y, 2, WHITE if lit else (240, 238, 246), 1.0 if lit else 0.6)
        sparkle(t, tx + tw + 3, RULE_Y, 2, WHITE if lit else (240, 238, 246), 1.0 if lit else 0.6)
        draw_text(t, FONT5, title, tx, TITLE_Y, TXT_LIT if lit else TXT_DIM,
                  shadow=SHADOW_LIT if lit else SHADOW_DIM)
        a[y:y + 20, 26:126] = t
        # top-right corner: close button
        t = bar20(25, lit, x1=12)
        rect(t, 24, 0, 1, 20, EDGE)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    # left side tile (12 wide): pearl bevel, then the list's rim
    a[42:71, 0:12] = frame_side(12, 29, SIDE_COLS)
    # right side tile (20 wide): list rim, scrollbar groove at 5..12, pearl, outer edge
    rcols = [DISP_RIM, (226, 216, 246), (232, 222, 248), (232, 222, 248), (232, 222, 248),
             LIST_BG, LIST_BG, LIST_BG, LIST_BG, LIST_BG, LIST_BG, LIST_BG, LIST_BG,
             (232, 222, 248), (226, 216, 246), (220, 208, 244), (214, 200, 242), (210, 196, 238),
             (196, 180, 232), EDGE]
    t = frame_side(20, 29, rcols)
    for r in range(29):
        if r % 2 == 0:
            px(t, 8, r, (56, 42, 96))
    a[42:71, 31:51] = t
    # close pressed, scroll handles
    t = bar20(25, True)[3:12, 14:23].copy()
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        a[53:71, x:x + 8] = LIST_BG
        bubble(a, x, 53, 8, 18, PEARL_DOWN if sel else PEARL_UP, r=3)
        for gy in (59, 61, 63):
            rect(a, x + 2, gy, 4, 1, EDGE if not sel else INK_ON)

    # bottom pieces
    t = frame_bottom(125, sparkly=True, seed=31)
    rect(t, 0, 0, 1, 38, WHITE)
    for k, c in enumerate(SIDE_COLS):
        if k < 11:
            pass
    rect(t, 11, 0, 114, 1, DISP_RIM)
    rect(t, 11, 0, 1, 1, DISP_RIM)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        pl_button(t, bx, 8, 22, 18, lbl)
    sparkle(t, 7, 30, 2, WHITE)
    a[72:110, 0:125] = t

    t = frame_bottom(150, sparkly=True, seed=32)
    rect(t, 149, 0, 1, 38, EDGE)
    rect(t, 0, 0, 131, 1, DISP_RIM)
    # running time readout
    display_box(t, 6, 9, 56, 8)
    # mini transport
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        bubble(t, bx, 22, 10, 10, PEARL_UP, r=2)
        mini_transport_icon(t, kind, bx, 22)
    # mini time
    display_box(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, DTXT_DIM)
    rect(t, 84, 22 + 5, 1, 1, DTXT_DIM)
    pl_button(t, 106, 8, 22, 18, "LIST")
    # resize grip
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx, gy, INK_SOFT)
            px(t, gx + 1, gy + 1, WHITE)
    a[72:110, 126:276] = t

    t = frame_bottom(25)
    rect(t, 0, 0, 25, 1, DISP_RIM)
    a[0:38, 179:204] = t
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_gen():
    a = new(194, 109)
    a[:] = gradient(194, 109)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, t):
            a[y:y + 20, px0:px0 + 25] = t

        t = bar20(25, lit, x0=4)
        rect(t, 0, 0, 1, 20, WHITE if lit else (230, 228, 238))
        piece(0, t)
        t = bar20(25, lit, x1=17)
        sparkle(t, 21, RULE_Y, 2, WHITE if lit else (240, 238, 246), 1.0 if lit else 0.6)
        piece(26, t)
        piece(52, bar20(25, lit, rule=False))
        t = bar20(25, lit, x0=8)
        sparkle(t, 3, RULE_Y, 2, WHITE if lit else (240, 238, 246), 1.0 if lit else 0.6)
        piece(78, t)
        piece(104, bar20(25, lit))
        t = bar20(25, lit, x1=12)
        mini_button(t, 14, 3, "close", lit)
        rect(t, 24, 0, 1, 20, EDGE)
        piece(130, t)

    # bottom caps and fill (14 tall)
    def bottom(w, grip, left_edge):
        t = new(w, 14)
        for r in range(14):
            t[r, :] = ramp(FRAME_BOT, r / 13)
        rect(t, 0, 13, w, 1, EDGE)
        if left_edge:
            rect(t, 0, 0, 1, 14, WHITE)
        else:
            rect(t, w - 1, 0, 1, 14, EDGE)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 7 - 3 * j
                    px(t, gx, gy, INK_SOFT)
                    px(t, gx + 1, gy + 1, WHITE)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]  # fill tile: no right edge
    # sides
    lcols = SIDE_COLS[:10] + [EDGE]
    rcols8 = [EDGE, (226, 216, 246), (232, 222, 248), (226, 216, 246), (220, 208, 244), (214, 200, 242),
              (196, 180, 232), EDGE]
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        a[42:42 + h, x:x + w] = frame_side(w, h, lcols if left else rcols8)
    t = bar20(25, True)[3:12, 14:23].copy()
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: each row starts at x 1, letters in their own cells (the bar's own rows 4..10 behind
    # them), 1px separators of x 0's colour
    for lit, y in ((True, 88), (False, 96)):
        rows = bar_rows(20, lit)
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            for r in range(7):
                rect(a, x, y + r, w, 1, rows[4 + r])
            draw_text(a, FONT5, c, x, y + 1, TXT_LIT if lit else TXT_DIM, shadow=SHADOW_LIT if lit else SHADOW_DIM)
            # the shadow's right column belongs to this cell; keep the separator clean
            x += w + 1
            rect(a, x - 1, y, 1, 7, SEP)
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------

GENEX_COLOURS = [
    LIST_BG,           # item background
    (232, 216, 248),   # item text
    (230, 220, 246),   # window background
    INK,               # button text
    (58, 36, 104),     # window text
    (150, 128, 204),   # dividers, sunken borders
    (106, 66, 170),    # selection bar
    (44, 30, 82),      # list header background
    (255, 206, 232),   # list header text
    (96, 76, 150),     # header frame, light
    (16, 10, 32),      # header frame, dark
    (150, 70, 140),    # header frame, pressed
    (30, 20, 56),      # header dead area
    (52, 38, 92),      # scrollbar
    (196, 168, 236),   # scrollbar 2
    (70, 52, 120),     # scrollbar pressed
    (244, 160, 206),   # scrollbar pressed 2
    (24, 16, 44),      # scrollbar dead area
]


def make_genex():
    a = new(256, 64)
    a[:] = gradient(256, 64)
    rect(a, 0, 0, 256, 1, (230, 220, 246))
    for i, c in enumerate(GENEX_COLOURS):
        px(a, 48 + 2 * i, 0, c)
    bubble(a, 0, 1, 47, 15, PEARL_UP, r=4)
    bubble(a, 0, 16, 47, 15, PEARL_DOWN, r=4)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------

VISCOLOR = (
    [(DISP, "background"), ((48, 36, 84), "dots")]
    + [(ramp([(255, 214, 236), PINK, (230, 160, 220), LILAC, LAVENDER, PERI, SKY, (140, 196, 240)], i / 15),
        f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}") for i in range(16)]
    + [((255, 236, 248), "oscilloscope 1"), ((244, 182, 214), "oscilloscope 2"), ((201, 168, 232), "oscilloscope 3"),
       ((143, 168, 240), "oscilloscope 4"), ((168, 212, 245), "oscilloscope 5"), ((255, 255, 255), "peaks")]
)

PLEDIT = dict(Normal="#E8D8F8", Current="#FFB6D9", NormalBG="#1E1438", SelectedBG="#4A3080",
              MbBG="#1E1438", MbFG="#E8D8F8", Font="Arial")


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in VISCOLOR:
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write("[Text]\n" + "".join(f"{k}={v}\n" for k, v in PLEDIT.items()))
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n", encoding="utf-8") as f:
        f.write("ARTMS Dall — a fan skin. ARTMS logo, album art and photos © MODHAUS.\n")


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
    wsz = os.path.join(HERE, "ARTMS-Dall.wsz")
    with zipfile.ZipFile(wsz, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(os.path.join(OUT, n), n)
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


def viscolors():
    return [c for c, _ in VISCOLOR]


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
    draw_bitmap_text(img, "320", 111, 43)
    draw_bitmap_text(img, "44", 156, 43)
    cols = viscolors()
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=hexrgb(PLEDIT["NormalBG"]))
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 9)
    except OSError:
        font = ImageFont.load_default()
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=hexrgb(PLEDIT["SelectedBG"]))
        col = hexrgb(PLEDIT["Current"]) if i == 0 else hexrgb(PLEDIT["Normal"])
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
    # the album art window's picture: the cover itself
    pw, ph = w - 22, h - 34
    side = min(pw, ph)
    art = Image.new("RGB", (pw, ph), (0, 0, 0))
    art.paste(cover().resize((side, side), Image.LANCZOS), ((pw - side) // 2, (ph - side) // 2))
    img.paste(art, (11, 20))
    return img


def preview():
    rows = [("ARTMS - Virtual Angel", "3:21"), ("Track 02", "3:05"), ("Track 03", "2:58"),
            ("Track 04", "3:33"), ("Track 05", "3:12"), ("Track 06", "3:40"), ("Track 07", "2:49"),
            ("Track 08", "3:26"), ("Track 09", "3:01"), ("Track 10", "3:18"), ("Track 11", "3:55")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title="ARTMS - VIRTUAL ANGEL  ***", bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="DEVINE ALL LOVE & LIVE (0:58)", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
    out = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), (64, 56, 84))
    out.paste(cols[0], (gap, gap))
    out.paste(cols[1], (275 + 2 * gap, gap))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, "preview.png"))


if __name__ == "__main__":
    if "--list" in sys.argv[1:]:
        print("ARTMS-Dall")  # the one theme
        sys.exit(0)
    names = build()
    preview()
    for n in names:
        p = os.path.join(OUT, n)
        if n.endswith(".bmp"):
            im = Image.open(p)
            print(f"{n:14s} {im.size[0]}x{im.size[1]} {im.mode}")
        else:
            print(f"{n:14s} {os.path.getsize(p)} bytes")
