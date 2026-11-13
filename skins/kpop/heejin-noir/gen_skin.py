#!/usr/bin/python3
"""HeeJin: two personal skins (classic Winamp 2.x format), generated procedurally.

Two unrelated moods from two unrelated photo sets of HeeJin (ARTMS), both candid/fan photos
(not an album concept): "Lace Noir" (dark lace fan, folding parasol, grey cable-knit, deep red
lip, a vertical-ribbed black curtain backdrop) and "Bunny Pop" (a plush bunny-eared hood, teal
knit, Adventure Time plushies, pale blue backstage light). Each theme is its own design end to
end - palette, titlebar, buttons, EQ, playlist, font treatment - sharing only this file's generic
canvas/bevel/font plumbing and the genex_wacup finishing step every skin in this collection uses.
Not based on any other generator in this collection: every sheet is drawn here from rectangles,
bevels and a pixel font written for this skin, except the two photo crops (HeeJin's own, composited
with an eyes-to-chin feature box kept clear of 0 px of overlap from anything drawn on top - see
check_features()).

    /usr/bin/python3 -I gen_skin.py                 # both themes
    /usr/bin/python3 -I gen_skin.py noir             # just one
    /usr/bin/python3 -I gen_skin.py --list

Outputs: HeeJin-LaceNoir.wsz / HeeJin-BunnyPop.wsz and preview-<theme>.png here; sheets in
out/<theme>/. Deterministic. Each .wsz is finished by skins/genex_wacup.py.
"""

import os
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source")
OUT_ROOT = os.path.join(HERE, "out")

# ------------------------------------------------------------------------------------------
# Generic canvas helpers (numpy, H x W x 3, int) - shared plumbing, no theme content here.
# ------------------------------------------------------------------------------------------


def new(w, h, col=(0, 0, 0)):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):y + h, max(0, x):x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def lerp(c0, c1, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    local = t * n - i
    return lerp(stops[i], stops[i + 1], local)


def edge(a, x, y, w, h, top, left, bot, right):
    """A 1px frame: top/left one colour, bottom/right another (a bevel's two halves)."""
    rect(a, x, y, w, 1, top)
    rect(a, x, y, 1, h, left)
    rect(a, x, y + h - 1, w, 1, bot)
    rect(a, x + w - 1, y, 1, h, right)


def raised(a, x, y, w, h, hi, lo):
    edge(a, x, y, w, h, hi, hi, lo, lo)


def sunken(a, x, y, w, h, hi, lo):
    edge(a, x, y, w, h, lo, lo, hi, hi)


_rng = np.random.default_rng(20261112)


def rib(a, x, y, w, h, lo, hi, period=3, amp=1.0, phase=0):
    """Vertical-only ribbing: a soft sine band repeated every `period` columns, the same for
    every row (so the tile seam never shows), echoing both photo sets' backdrops (the curtain's
    pleats, a cable-knit's ridges)."""
    cols = np.arange(w)
    wave = 0.5 + 0.5 * np.cos(2 * np.pi * (cols + phase) / period)
    for c in range(w):
        col = lerp(lo, hi, wave[c] ** 1.6 * amp)
        a[y:y + h, x + c] = col


def speck(a, x, y, w, h, col, density=0.04, seed=0):
    """Sparse flecks (lace texture, knit fuzz)."""
    r = np.random.default_rng(seed)
    n = int(w * h * density)
    xs = r.integers(x, x + w, n)
    ys = r.integers(y, y + h, n)
    for xx, yy in zip(xs, ys):
        px(a, int(xx), int(yy), col)


def save(a, path):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(path)
    return img


# ------------------------------------------------------------------------------------------
# Pixel fonts, written for this skin. FONT5 fills text.bmp's fixed grid (sprites.js FONT_LOOKUP:
# 5 wide x 6 tall cells; the grid position of every character is an app fact, not a design choice)
# and is reused, at each glyph's own width, for gen.bmp's A-Z and the hand-set titlebar/window
# titles. TINY is a separate, smaller alphabet for the little button and band labels.
# ------------------------------------------------------------------------------------------


def G(*rows):
    return list(rows)


FONT5 = {
    "A": G(".#.", "#.#", "###", "#.#", "#.#"),
    "B": G("##.", "#.#", "##.", "#.#", "##."),
    "C": G(".##", "#..", "#..", "#..", ".##"),
    "D": G("##.", "#.#", "#.#", "#.#", "##."),
    "E": G("###", "#..", "##.", "#..", "###"),
    "F": G("###", "#..", "##.", "#..", "#.."),
    "G": G(".##", "#..", "#.#", "#.#", ".##"),
    "H": G("#.#", "#.#", "###", "#.#", "#.#"),
    "I": G("###", ".#.", ".#.", ".#.", "###"),
    "J": G("..#", "..#", "..#", "#.#", ".#."),
    "K": G("#.#", "#.#", "##.", "#.#", "#.#"),
    "L": G("#..", "#..", "#..", "#..", "###"),
    "M": G("#...#", "##.##", "#.#.#", "#...#", "#...#"),
    "N": G("#..#", "##.#", "#.##", "#..#", "#..#"),
    "O": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "P": G("##.", "#.#", "##.", "#..", "#.."),
    "Q": G(".#.", "#.#", "#.#", "#.#", ".##"),
    "R": G("##.", "#.#", "##.", "#.#", "#.#"),
    "S": G(".##", "#..", ".#.", "..#", "##."),
    "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#...#", "#...#", "#.#.#", "#.#.#", ".#.#."),
    "X": G("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": G("###", "..#", ".#.", "#..", "###"),
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
    "@": G(".##.", "#..#", "#.##", "#...", ".###"),
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
    "å": G(".#.", ".#.", "#.#", "###", "#.#"),
    "ö": G("#.#", ".#.", "#.#", "#.#", ".#."),
    "ä": G("#.#", "...", "#.#", "#.#", ".#."),
    "?": G("##.", "..#", ".#.", "...", ".#."),
    "*": G("#.#", ".#.", "###", ".#.", "#.#"),
    " ": G("...", "...", "...", "...", "..."),
}

# 3x5: a small, narrow alphabet for button/band labels (own design - not a scaled copy of FONT5).
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
    "J": G("..#", "..#", "..#", "#.#", ".#."),
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


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1, shadow=None):
    for c in s:
        if c not in font:
            x += 4
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


# Character grid for text.bmp: row, col is an app fact (ui/.../render/sprites.js FONT_LOOKUP),
# not a design choice. 31 columns x 3 rows, 5x6 cells.
FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]

# ------------------------------------------------------------------------------------------
# Layout facts (not a style choice): every rect below is where YTMinamp's renderer and real
# Winamp/WACUP read a sprite from or place one, transcribed from ui/src/lib/skin/render/
# {sprites,equalizer,playlist,albumArt}.js (itself ported from Webamp's skinSprites.ts - see that
# file's own header). Any skin for this app must match these or the app misreads it.
# ------------------------------------------------------------------------------------------

MAIN_W, MAIN_H = 275, 116
EQ_W, EQ_H = 275, 116
PL_W, PL_H = 275, 232

CBUTTONS_POS = {"previous": (16, 88, 23, 18), "play": (39, 88, 23, 18), "pause": (62, 88, 23, 18),
                 "stop": (85, 88, 23, 18), "next": (108, 88, 22, 18), "eject": (136, 89, 22, 16)}
PLAY_PAUSE_POS = (26, 28, 9, 9)
SHUFFLE_POS, REPEAT_POS = (164, 89), (210, 89)
EQ_TOGGLE_POS, PL_TOGGLE_POS = (219, 58), (242, 58)
MONO_POS, STEREO_POS = (212, 41), (239, 41)
VIS_POS = (24, 43, 76, 16)
POSBAR_POS = (16, 72, 248, 10)
VOLUME_POS = (107, 57, 68, 13)
BALANCE_POS = (177, 57, 38, 13)
TIME_POS = (39, 26, 59, 13)
KBPS_POS = (111, 43, 15, 6)
KHZ_POS = (156, 43, 10, 6)
MARQUEE_POS = (111, 27, 154, 6)
ABOUT_POS = (253, 91, 13, 15)
CLUTTER_POS = (10, 22, 8, 43)
OPTIONS_BTN, MIN_BTN, SHADE_BTN, CLOSE_BTN = (6, 3), (244, 3), (254, 3), (264, 3)
EQ_CLOSE, EQ_ON, EQ_AUTO, EQ_PRESETS = (264, 3, 9, 9), (14, 18, 26, 12), (40, 18, 32, 12), (217, 18, 44, 12)
EQ_GRAPH_POS, EQ_PREAMP_POS = (86, 17), (21, 38)
EQ_FIRST_BAND, EQ_BAND_STEP, EQ_SLIDER_TOP, EQ_SLIDER_W, EQ_SLIDER_H = 78, 18, 38, 14, 63
EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]

# ------------------------------------------------------------------------------------------
# Rects that main.bmp/eqmain.bmp draw at (everything the app itself never paints: displays,
# button trays, seats). These ARE a style choice - each theme's make_main() fills them in - but
# listed centrally so the occupancy mask (and the "what's free for a photo" accounting) has one
# source of truth per theme.
# ------------------------------------------------------------------------------------------


def occupancy(rects, size):
    """1 wherever something is drawn over the window background (the window's own 1px outline
    too - nothing may be drawn flush with the very edge either)."""
    W, H = size
    m = np.zeros((H, W), dtype=bool)
    for x, y, w, h in rects:
        m[max(0, y):y + h, max(0, x):x + w] = True
    m[0, :] = m[-1, :] = True
    m[:, 0] = m[:, -1] = True
    return m


def check_features(label, feat, occ, cov):
    x0, y0, x1, y1 = feat
    H, W = occ.shape
    inside = 0 <= x0 and 0 <= y0 and x1 <= W and y1 <= H
    n = int(occ[max(0, y0):y1, max(0, x0):x1].sum()) if inside else -1
    edge_min = float(cov[max(0, y0):y1, max(0, x0):x1].min()) if inside else -1
    print(f"    {label:28s} features x{x0}-{x1} y{y0}-{y1} ({x1 - x0}x{y1 - y0}): {n} px overlapped, "
          f"edge clearance {edge_min:.2f}")
    assert inside and n == 0, f"{label}: the face's features are under something drawn on top"
    assert edge_min > 0.99, f"{label}: the face runs into the photo's own feathered edge ({edge_min:.2f})"


def photo_layer(path, box, free, size):
    """The photo (its own pixels) scaled and placed so its feature box `box` (x0,y0,x1,y1, the
    photo's own pixel coordinates, eyes to chin) fills `free` (x,y,w,h in window pixels), centred,
    on a canvas of `size`. Returns (rgb float HxWx3, coverage float HxW: 1 inside the photo,
    feathering to 0 at its own edge, the feature box in window pixels)."""
    im = Image.open(path).convert("RGB")
    bx0, by0, bx1, by1 = box
    fx, fy, fw, fh = free
    s = min(fw / (bx1 - bx0), fh / (by1 - by0))
    W, H = size
    sw, sh = max(1, round(im.width * s)), max(1, round(im.height * s))
    small = im.resize((sw, sh), Image.LANCZOS)
    cx, cy = fx + fw / 2, fy + fh / 2
    ox, oy = round(cx - (bx0 + bx1) / 2 * s), round(cy - (by0 + by1) / 2 * s)
    feat = (int(np.floor(ox + bx0 * s)), int(np.floor(oy + by0 * s)),
            int(np.ceil(ox + bx1 * s)), int(np.ceil(oy + by1 * s)))
    rgb = np.zeros((H, W, 3))
    cov = np.zeros((H, W))
    src = np.asarray(small).astype(np.float64)
    # The feather must resolve to fully opaque (1.0) before it reaches the feature box: cap it to
    # (a margin inside) the box's own tightest margin to the source photo's edge, in source pixels,
    # rather than a flat fraction of the scaled image - a tight crop (fan-04's chin close to the
    # frame's right edge) would otherwise feather straight into the box itself.
    margin = min(bx0, by0, im.width - bx1, im.height - by1)
    feather_src = max(1.0, min(0.12 * min(im.width, im.height), 0.85 * margin))
    feather = max(2, round(feather_src * s))
    yy, xx = np.mgrid[0:sh, 0:sw]
    edge_d = np.minimum.reduce([xx, yy, sw - 1 - xx, sh - 1 - yy]).astype(np.float64)
    fe = np.clip(edge_d / feather, 0, 1)
    x0, y0 = max(0, ox), max(0, oy)
    x1, y1 = min(W, ox + sw), min(H, oy + sh)
    if x1 > x0 and y1 > y0:
        rgb[y0:y1, x0:x1] = src[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
        cov[y0:y1, x0:x1] = fe[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return rgb, cov, feat


def lay_photo(body, rgb, cov):
    """Blends the photo into a body canvas where cov > 0 (feathered)."""
    c = cov[..., None]
    return body * (1 - c) + rgb * c


def photo_layer_explicit(path, box, scale, ox, oy, size, feather=10):
    """Like photo_layer, but placed at an exact (scale, ox, oy) instead of being centred on a
    free rect - used for the photo-forward main windows, where the placement is chosen by a
    search over the occupancy mask (see PHOTO_BIG below) rather than simple box-centring, because
    centring the feature box on the one clear pocket (which sits low in the window) pushes a
    portrait-orientated photo's top edge down past the window's own top - leaving a gap no amount
    of extra scale closes without the feature box outgrowing that pocket. `feather` is fixed in
    window pixels here (not derived from the photo's own margins): the image is so much larger
    than the window that its own edges are never near the feature box."""
    im = Image.open(path).convert("RGB")
    bx0, by0, bx1, by1 = box
    W, H = size
    sw, sh = max(1, round(im.width * scale)), max(1, round(im.height * scale))
    small = im.resize((sw, sh), Image.LANCZOS)
    ox_r, oy_r = round(ox), round(oy)
    feat = (int(np.floor(ox_r + bx0 * scale)), int(np.floor(oy_r + by0 * scale)),
            int(np.ceil(ox_r + bx1 * scale)), int(np.ceil(oy_r + by1 * scale)))
    rgb = np.zeros((H, W, 3))
    cov = np.zeros((H, W))
    src = np.asarray(small).astype(np.float64)
    yy, xx = np.mgrid[0:sh, 0:sw]
    # feather only the photo's edges that fall inside the window; an edge at or past the window's
    # own edge (the top and right here: a full-height, right-anchored bleed) stays hard, so the
    # photo runs right up under the titlebar instead of fading out below it
    big = 10 ** 6
    sides = [xx if ox_r > 0 else big, yy if oy_r > 0 else big,
             (sw - 1 - xx) if ox_r + sw < W else big, (sh - 1 - yy) if oy_r + sh < H else big]
    edge_d = np.minimum.reduce([np.broadcast_to(np.asarray(s_, dtype=np.float64), (sh, sw)) for s_ in sides])
    fe = np.clip(edge_d / feather, 0, 1)
    x0, y0 = max(0, ox_r), max(0, oy_r)
    x1, y1 = min(W, ox_r + sw), min(H, oy_r + sh)
    if x1 > x0 and y1 > y0:
        rgb[y0:y1, x0:x1] = src[y0 - oy_r:y1 - oy_r, x0 - ox_r:x1 - ox_r]
        cov[y0:y1, x0:x1] = fe[y0 - oy_r:y1 - oy_r, x0 - ox_r:x1 - ox_r]
    return rgb, cov, feat


# ------------------------------------------------------------------------------------------
# Theme configs: everything that differs between the two skins. Photo boxes were read by eye off
# a 100px reference grid overlaid on the source JPEGs (source/ is ground truth - see BRIEF.md).
# ------------------------------------------------------------------------------------------

NOIR = dict(
    key="noir", style="noir", wsz="HeeJin-LaceNoir.wsz",
    main_title="JEON HEEJIN", eq_title="NOIR EQUALIZER", pl_title="LACE PLAYLIST",
    photo_file=os.path.join(SOURCE, "heejin-fan-04.jpg"),
    # Profile, eyes closed, chin clear, nothing held near the face (fan 02/05/06 all bring lace or
    # a hand across the lower face - this is the one frame where eyes-to-chin reads clean).
    photo_box=(650, 380, 1150, 930),
    BODY=(19, 18, 23), BODY_HI=(46, 44, 54), BODY_LO=(6, 6, 8), PANEL=(13, 12, 16),
    DISP=(9, 7, 10), DISP_EDGE=(58, 24, 30), SLOT=(10, 9, 13),
    RIB_LO=(15, 14, 19), RIB_HI=(26, 24, 32),
    SILVER=(173, 176, 186), SILVER_HI=(219, 221, 228), SILVER_LO=(95, 97, 108),
    RED=(150, 36, 55), RED_HI=(205, 68, 90), RED_LO=(70, 16, 26),
    IVORY=(224, 213, 202), IVORY_DIM=(118, 108, 104),
    GREY_TXT=(140, 134, 142), GREY_DIM=(70, 68, 76),
)

BUNNY = dict(
    key="bunny", style="bunny", wsz="HeeJin-BunnyPop.wsz",
    main_title="JEON HEEJIN", eq_title="BUNNY EQUALIZER", pl_title="POP PLAYLIST",
    photo_file=os.path.join(SOURCE, "heejin-bunny-02.jpg"),
    # Full face to camera, peace sign, open smile - the cleanest eyes-to-chin of the four (01 pulls
    # the sweater collar up over the chin; 03/04 are angled down toward the plushies).
    photo_box=(420, 480, 820, 800),
    BODY=(205, 227, 247), BODY_HI=(236, 246, 253), BODY_LO=(151, 182, 210), PANEL=(183, 211, 237),
    DISP=(21, 35, 54), DISP_EDGE=(70, 130, 160), SLOT=(150, 182, 212),
    RIB_LO=(195, 220, 243), RIB_HI=(220, 236, 251),
    TEAL=(25, 103, 150), TEAL_HI=(70, 158, 199), TEAL_LO=(13, 56, 84),
    PINK=(231, 142, 177), PINK_HI=(247, 189, 208), PINK_LO=(176, 90, 121),
    YELLOW=(243, 223, 140), YELLOW_HI=(250, 240, 190),
    INK=(26, 40, 58), INK_DIM=(100, 124, 146),
)

THEMES = {"noir": NOIR, "bunny": BUNNY}

# Photo-forward companions to Noir/Bunny: same two palettes, a different (wider-angle) frame from
# the same ten source photos, and a bleeding-portrait main window (make_main_big) instead of the
# small corner box. EQ/playlist/gen windows reuse make_eqmain/make_pledit/make_gen unchanged (just
# their own window titles below) - the portrait is the main window's story, not every window's.

PARASOL = dict(
    NOIR, key="parasol", wsz="HeeJin-Parasol.wsz", big_photo=True,
    eq_title="HEEJIN EQUALIZER", pl_title="HEEJIN PLAYLIST",
    photo_file=os.path.join(SOURCE, "heejin-fan-03.jpg"),
    # Looking back over her shoulder, the parasol open overhead, fan held off to the side clear of
    # her face - a wider, more candid frame than -04's tight profile.
    photo_box=(480, 270, 745, 500),
    # (scale, ox, oy): the largest scale found by a brute-force search over BIG_MASK (see
    # make_main_big) that lands the feature box with 0px overlap while the photo still covers the
    # full window height and reaches its right edge. Box lands at x222-262, y36-72.
    photo_scale=0.15, photo_ox=150, photo_oy=-4,
    # Second photo, face in the EQ window's dB gap (EQ_MASK): profile, eyes closed, hair falling
    # down the frame - a tall composition that suits the narrow column. Same search (EQ_MASK).
    eq_photo_file=os.path.join(SOURCE, "heejin-fan-01.jpg"), eq_photo_box=(640, 235, 830, 425),
    eq_photo_scale=0.225, eq_photo_ox=-109, eq_photo_oy=10,
    eq_backdrop_box=(350, 0, 650, 120),  # plain curtain, above her head
)

PLUSHIE = dict(
    BUNNY, key="plushie", wsz="HeeJin-Plushie.wsz", big_photo=True,
    eq_title="HEEJIN EQUALIZER", pl_title="HEEJIN PLAYLIST",
    photo_file=os.path.join(SOURCE, "heejin-bunny-02.jpg"),
    # The bunny hood and the raised peace sign, on a plain pale-blue backdrop that blends into
    # the chassis (the user's pick over -03's busier plushie frame).
    photo_box=(420, 480, 820, 800),
    photo_scale=0.0985, photo_ox=181, photo_oy=-7,  # same search; box lands at x222-262, y40-72
    # EQ window: the pouting close-up with Finn - face straight on, clean chin.
    eq_photo_file=os.path.join(SOURCE, "heejin-bunny-04.jpg"), eq_photo_box=(380, 360, 760, 785),
    eq_photo_scale=0.1115, eq_photo_ox=-7, eq_photo_oy=14,
    eq_backdrop_box=(1000, 0, 1206, 250),  # the pale backstage wall, top right
)

THEMES["parasol"] = PARASOL
THEMES["plushie"] = PLUSHIE


# ------------------------------------------------------------------------------------------
# Themed widgets: each reads T["style"] ("noir" or "bunny") and draws its own way - Noir sharp
# and rectangular (a lace zig-zag trim, a diamond LED), Bunny soft and rounded (corners clipped
# to the surrounding colour, a scalloped plush-fur trim, a round LED) - rather than one shape
# recoloured per theme.
# ------------------------------------------------------------------------------------------


def round_corners(a, x, y, w, h, bg):
    px(a, x, y, bg)
    px(a, x + w - 1, y, bg)
    px(a, x, y + h - 1, bg)
    px(a, x + w - 1, y + h - 1, bg)


def panel_face(a, x, y, w, h, T, pressed=False, bg=None):
    """A button/plate face: a vertical gradient with a bevel, Noir sharp, Bunny round-cornered."""
    if T["style"] == "noir":
        top, bot = (T["BODY_LO"], T["BODY_HI"]) if pressed else (T["BODY_HI"], T["BODY_LO"])
        for r in range(h):
            rect(a, x, y + r, w, 1, lerp(top, bot, r / max(1, h - 1)))
        edge(a, x, y, w, h, top, top, bot, bot)
    else:
        top, bot = (T["PANEL"], T["BODY_HI"]) if pressed else (T["BODY_HI"], T["PANEL"])
        for r in range(h):
            rect(a, x, y + r, w, 1, lerp(top, bot, r / max(1, h - 1)))
        edge(a, x, y, w, h, top, top, bot, bot)
        if bg is not None:
            round_corners(a, x, y, w, h, bg)


def trim(a, x, y, w, T, bg=None):
    """A 3px decorative strip along one row: Noir a lace zig-zag in SILVER/RED, Bunny a row of
    plush scallops in YELLOW/PINK. `bg` is what shows between the picked-out points."""
    if T["style"] == "noir":
        for c in range(w):
            k = c % 6
            h = 3 if k in (0, 3) else (2 if k in (1, 2, 4, 5) else 1)
            col = T["RED_HI"] if k == 0 else T["SILVER"]
            rect(a, x + c, y + (3 - h), 1, h, col)
    else:
        for c in range(w):
            t = (c % 8) / 7
            bump = int(round(2 * (1 - (2 * t - 1) ** 2)))
            col = T["PINK_HI"] if (c // 8) % 2 == 0 else T["YELLOW_HI"]
            if bg is not None:
                rect(a, x + c, y, 1, 3 - bump, bg)
            rect(a, x + c, y + (3 - bump), 1, bump, col)


def led(a, x, y, on, T):
    if T["style"] == "noir":
        col = T["RED_HI"] if on else T["GREY_DIM"]
        for dx, dy in [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)]:
            px(a, x + dx, y + dy, col)
    else:
        col = T["PINK_HI"] if on else T["TEAL_LO"]
        for dx in range(3):
            for dy in range(3):
                if (dx, dy) != (0, 0) and (dx, dy) != (2, 0) and (dx, dy) != (0, 2) and (dx, dy) != (2, 2):
                    px(a, x + dx, y + dy, col)


def display_box(a, x, y, w, h, T):
    """A recessed display window."""
    rect(a, x, y, w, h, T["DISP"])
    sunken(a, x - 1, y - 1, w + 2, h + 2, T["BODY_HI"], T["BODY_LO"])
    rect(a, x, y, w, 1, T["DISP_EDGE"])
    rect(a, x, y, 1, h, T["DISP_EDGE"])
    if T["style"] == "bunny":
        round_corners(a, x, y, w, h, T["PANEL"])


def plate_ink(T, lit):
    """Text drawn on a dark DISP plate (titlebar nameplates, gen.bmp's letters): Noir's DISP is
    already near-black, so its own ivory/grey pair reads fine there; Bunny's DISP is a dark teal
    glass, so it needs a bright ink rather than the chassis's dark-on-light INK."""
    if T["style"] == "noir":
        return T["IVORY"] if lit else T["GREY_TXT"]
    return T["BODY_HI"] if lit else T["TEAL_HI"]


def mini_button(a, x, y, kind, T, lit=True, pressed=False):
    """9x9 titlebar button."""
    face = T["BODY_LO"] if pressed else T["BODY_HI"]
    rect(a, x, y, 9, 9, face)
    if pressed:
        sunken(a, x, y, 9, 9, T["BODY_HI"], T["BODY_LO"])
    else:
        raised(a, x, y, 9, 9, T["BODY_HI"], T["BODY_LO"])
    if T["style"] == "bunny":
        round_corners(a, x, y, 9, 9, T["BODY"])
    if T["style"] == "noir":
        ink = T["RED_HI"] if pressed else (T["SILVER_HI"] if lit else T["GREY_DIM"])
    else:
        ink = T["PINK"] if pressed else (T["TEAL"] if lit else T["INK_DIM"])
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        for dx, dy in [(3, 3), (4, 3), (5, 3), (3, 4), (4, 4), (5, 4), (3, 5), (4, 5), (5, 5)]:
            px(a, X + dx, Y + dy, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 2, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 2, ink)
        rect(a, X + 2, Y + 5, 5, 1, ink)
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


def toggle(a, x, y, w, h, label, on, pressed, T, dot=True):
    panel_face(a, x, y, w, h, T, pressed, bg=T["BODY"])
    o = 1 if pressed else 0
    if T["style"] == "noir":
        ink = T["RED_HI"] if on else T["GREY_TXT"]
    else:
        ink = T["TEAL"] if on else T["INK_DIM"]
    tw = text_w(TINY, label)
    ty = y + (h - 5) // 2 + o
    # the dot only if it (plus a gap) actually fits beside the centred label
    use_dot = dot and tw + 8 <= w - 2
    if use_dot:
        avail = w - 8
        tx = x + 8 + o + max(0, (avail - tw) // 2)
        led(a, x + 3 + o, y + (h - 3) // 2 + o, on, T)
    else:
        tx = x + o + max(0, (w - tw) // 2)
    draw_text(a, TINY, label, tx, ty, ink)


def seven_seg(a, x, y, lit_segs, T, ghost=True):
    SEG = {
        "a": [(0, c) for c in range(2, 7)], "g": [(6, c) for c in range(2, 7)],
        "d": [(12, c) for c in range(2, 7)],
        "f": [(r, c) for r in range(1, 6) for c in (1, 2)], "b": [(r, c) for r in range(1, 6) for c in (6, 7)],
        "e": [(r, c) for r in range(7, 12) for c in (1, 2)], "c": [(r, c) for r in range(7, 12) for c in (6, 7)],
    }
    rect(a, x, y, 9, 13, T["DISP"])
    on = T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"]
    ghost_col = lerp(T["DISP"], on, 0.14)
    for s, cells in SEG.items():
        if s not in lit_segs and ghost:
            for r, c in cells:
                px(a, x + c, y + r, ghost_col)
    for s, cells in SEG.items():
        if s in lit_segs:
            for r, c in cells:
                px(a, x + c, y + r, on)


DIGIT_SEGS = {
    0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc",
    5: "afgcd", 6: "afgedc", 7: "abc", 8: "abcdefg", 9: "abcdfg",
}


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87): the main window's two titlebar strips (lit/unlit), the window-shade
# bars (copies), the clutter bar's O A I D V column, and loose 9x9 button sprites.
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(T, lit_letters):
    a = new(8, 43, T["BODY"])
    rect(a, 0, 0, 8, 43, T["SLOT"])
    sunken(a, 0, 0, 8, 43, T["BODY_HI"], T["BODY_LO"])
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        ink = (T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"]) if on else T["GREY_TXT" if T["style"] == "noir" else "INK_DIM"]
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, ink)
    return a


def main_titlebar(T, lit):
    a = new(275, 14, T["BODY"])
    for r in range(14):
        rect(a, 0, r, 275, 1, lerp(T["BODY_HI"], T["BODY_LO"], r / 13))
    rect(a, 0, 0, 275, 1, T["BODY_HI"])
    rect(a, 0, 0, 1, 14, T["BODY_HI"])
    rect(a, 274, 0, 1, 14, T["BODY_LO"])
    word = T["main_title"]
    ww = text_w(FONT5, word, gap=1)
    wx = (275 - ww) // 2
    trim(a, 18, 2, wx - 6 - 18, T, bg=a[2, 18].tolist())
    trim(a, wx + ww + 6, 2, 240 - (wx + ww + 6), T, bg=a[2, wx + ww + 6].tolist())
    ink = (T["IVORY"] if lit else T["GREY_TXT"]) if T["style"] == "noir" else (T["INK"] if lit else T["INK_DIM"])
    shadow = T["BODY_LO"] if T["style"] == "noir" else None
    draw_text(a, FONT5, word, wx, 4, ink, gap=1, shadow=shadow)
    mini_button(a, *OPTIONS_BTN, "options", T, lit)
    mini_button(a, *MIN_BTN, "minimize", T, lit)
    mini_button(a, *SHADE_BTN, "shade", T, lit)
    mini_button(a, *CLOSE_BTN, "close", T, lit)
    return a


def make_titlebar(T):
    a = new(344, 87, T["BODY"])
    for kind, x, py_ in [("options", 0, 9), ("minimize", 9, 9), ("close", 18, 9)]:
        b = new(9, 9)
        mini_button(b, 0, 0, kind, T, True)
        a[0:9, x:x + 9] = b
        mini_button(b, 0, 0, kind, T, True, pressed=True)
        a[py_:py_ + 9, x:x + 9] = b
    b = new(9, 9)
    mini_button(b, 0, 0, "shade", T, True)
    a[18:27, 0:9] = b
    mini_button(b, 0, 0, "shade", T, True, pressed=True)
    a[18:27, 9:18] = b
    a[0:14, 27:302] = main_titlebar(T, True)
    a[15:29, 27:302] = main_titlebar(T, False)
    a[29:43, 27:302] = main_titlebar(T, True)
    a[42:56, 27:302] = main_titlebar(T, False)
    unlit = clutter_bar(T, "")
    lit = clutter_bar(T, "OAIDV")
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = lit[y:y + h]
    return a


def photo_titlebar(T, lit, main):
    """Parasol/Plushie's main titlebar: main.bmp's own top 14 rows (so the photo's hair runs up to
    the window's edge under it), with only a small title at the left over the chrome and the
    standard 9x9 buttons."""
    a = main[0:14, :].astype(np.int32).copy()
    if T["style"] == "noir":
        ink, shadow = (T["IVORY"] if lit else T["GREY_TXT"]), T["BODY_LO"]
    else:
        ink, shadow = (T["INK"] if lit else T["INK_DIM"]), T["BODY_HI"]
    draw_text(a, TINY, T["main_title"], 19, 5, ink, shadow=shadow)
    mini_button(a, *OPTIONS_BTN, "options", T, lit)
    mini_button(a, *MIN_BTN, "minimize", T, lit)
    mini_button(a, *SHADE_BTN, "shade", T, lit)
    mini_button(a, *CLOSE_BTN, "close", T, lit)
    return a


def make_titlebar_big(T, main):
    a = make_titlebar(T)
    a[0:14, 27:302] = photo_titlebar(T, True, main)
    a[15:29, 27:302] = photo_titlebar(T, False, main)
    return a


def eq_titlebar(T, lit):
    a = new(275, 14, T["BODY"])
    for r in range(14):
        rect(a, 0, r, 275, 1, lerp(T["BODY_HI"], T["BODY_LO"], r / 13))
    rect(a, 0, 0, 275, 1, T["BODY_HI"])
    rect(a, 0, 0, 1, 14, T["BODY_HI"])
    rect(a, 274, 0, 1, 14, T["BODY_LO"])
    title = T["eq_title"]
    tw = text_w(FONT5, title)
    wx = (275 - tw) // 2
    trim(a, 10, 2, wx - 10 - 6, T, bg=a[2, 10].tolist())
    trim(a, wx + tw + 6, 2, 254 - (wx + tw + 6), T, bg=a[2, wx + tw + 6].tolist())
    ink = (T["IVORY"] if lit else T["GREY_TXT"]) if T["style"] == "noir" else (T["INK"] if lit else T["INK_DIM"])
    shadow = T["BODY_LO"] if T["style"] == "noir" else None
    draw_text(a, FONT5, title, wx, 4, ink, gap=1, shadow=shadow)
    mini_button(a, 264, 3, "close", T, lit)
    return a


# 20px titled bars for pledit.bmp / gen.bmp: a lit row (y=0 in the "top" piece) and an unlit copy
# (y=21), tiled from a strip of plain chassis plus a titled plate in the middle.
BAR_PLATE_Y = 3


def bar20(w, T):
    a = new(w, 20, T["BODY"])
    for r in range(20):
        rect(a, 0, r, w, 1, lerp(T["BODY_HI"], T["BODY_LO"], r / 19))
    rect(a, 0, 0, w, 1, T["BODY_HI"])
    return a


def plate(a, x, y, w, lit, T, h=9):
    rect(a, x, y + 1, w, h - 2, T["DISP"] if lit else lerp(T["DISP"], T["BODY_LO"], 0.4))
    rect(a, x, y, w, 1, T["BODY_LO"])
    rect(a, x, y + h - 1, w, 1, T["BODY_HI"])


def plate_cap_left(a, x, y, lit, T, h=9):
    rect(a, x, y, 2, h, T["BODY"])
    rect(a, x + 2, y, 1, h, T["BODY_LO"])
    plate(a, x + 3, y, 1, lit, T, h)


def plate_cap_right(a, x, y, lit, T, h=9):
    plate(a, x, y, 1, lit, T, h)
    rect(a, x + 1, y, 1, h, T["BODY_HI"])
    rect(a, x + 2, y, 2, h, T["BODY"])


# ------------------------------------------------------------------------------------------
# main.bmp (275 x 116): HeeJin's portrait sits bottom-right, in the one block of the window
# nothing else is drawn over - clear of the posbar (ends x264,y82), the shuffle/repeat row (ends
# x239,y104) and the window's own 1px outline. The About-logo spot (253-266,91-106) falls inside
# it: rather than draw an emblem there (there's no HeeJin logo to use - BRIEF.md's "logos" rule is
# for marks that exist), the photo itself shows through it, same as the clutter bar's slot does
# through its own background tile.
# ------------------------------------------------------------------------------------------

FREE_MAIN = (241, 84, 32, 30)


def make_main(T):
    a = new(275, 116, T["BODY"])
    for r in range(116):
        rect(a, 0, r, 275, 1, lerp(T["BODY_HI"], T["BODY"], min(1, r / 90)))
    raised(a, 0, 0, 275, 116, T["BODY_HI"], T["BODY_LO"])
    rib(a, 1, 1, 273, 114, T["RIB_LO"], T["RIB_HI"], period=5, amp=0.5)

    # clutter slot + left display: indicator, time, analyzer
    rect(a, 10, 22, 8, 43, T["SLOT"])
    display_box(a, 21, 20, 84, 42, T)
    for x in (48, 60, 78, 90):
        seven_seg(a, x, 26, "", T)
    for yy in (29, 34):
        px(a, 73, yy, T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"])
        px(a, 74, yy, T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"])
    rect(a, 24, 60, 76, 1, lerp(T["DISP"], T["BODY"], 0.5))

    # right display: title row, kbps/kHz/mono/stereo row
    display_box(a, 109, 21, 159, 15, T)
    display_box(a, 109, 40, 159, 14, T)
    lbl_ink = T["GREY_TXT"] if T["style"] == "noir" else T["INK_DIM"]
    draw_text(a, TINY, "KBPS", 129, 44, lbl_ink)
    draw_text(a, TINY, "KHZ", 169, 44, lbl_ink)

    # slider seats (the sliders' own frames cover them)
    sunken(a, 106, 56, 70, 15, T["BODY_HI"], T["BODY_LO"])
    sunken(a, 176, 56, 40, 15, T["BODY_HI"], T["BODY_LO"])
    sunken(a, 218, 57, 48, 14, T["BODY_HI"], T["BODY_LO"])

    # seek bar seat
    sunken(a, 15, 71, 250, 12, T["BODY_HI"], T["BODY_LO"])

    # transport tray
    rect(a, 15, 87, 145, 20, T["SLOT"])
    sunken(a, 15, 87, 145, 20, T["BODY_HI"], T["BODY_LO"])
    sunken(a, 163, 88, 76, 17, T["BODY_HI"], T["BODY_LO"])  # stops at x238, clear of FREE_MAIN (240)

    # a hairline along the bottom, in the accent colour - stopping short of the portrait corner
    # (FREE_MAIN starts at x240) rather than running under it
    accent = T["RED_LO"] if T["style"] == "noir" else T["TEAL_LO"]
    hl_w = FREE_MAIN[0] - 4 - 2
    rect(a, 4, 111, hl_w, 1, accent)
    rect(a, 4, 112, hl_w, 1, T["BODY_LO"])

    # HeeJin's portrait, last (its feathered edge melts into the body already drawn).
    rgb, cov, feat = photo_layer(T["photo_file"], T["photo_box"], FREE_MAIN, (275, 116))
    a[:] = lay_photo(a.astype(np.float64), rgb, cov)

    drawn = [
        (0, 0, 275, 14),  # titlebar (blitted over main.bmp by the app, but keep it out of occupancy too)
        CLUTTER_POS, (21, 20, 84, 42), (109, 21, 159, 15), (109, 40, 159, 14),
        (106, 56, 70, 15), (176, 56, 40, 15), (218, 57, 48, 14),
        (15, 71, 250, 12), (15, 87, 145, 20), (163, 88, 76, 17),
        (4, 111, hl_w, 1), (4, 112, hl_w, 1),
        EQ_TOGGLE_POS + (23, 12), PL_TOGGLE_POS + (23, 12),
        (*SHUFFLE_POS, 47, 15), (*REPEAT_POS, 28, 15),
        MARQUEE_POS,
    ]
    occ = occupancy(drawn, (275, 116))
    check_features(f"{T['key']} main", feat, occ, cov)
    return a


# ------------------------------------------------------------------------------------------
# main.bmp, photo-forward variant (Parasol / Plushie): the portrait is meant to dominate the
# window, not sit in a small corner box. BRIEF.md's 0px rule is about the tight eyes-to-chin
# feature box alone, not the whole photo, so every other fixed app position (seek bar, volume/
# balance, EQ/PL toggle, shuffle/repeat, mono/stereo, title/kbps/kHz) is left to sit directly over
# the photo - and those sprites are redrawn here as the photo's own pixels plus a few small marks
# (make_*_big below), so they occlude nothing but those marks.
#
# BIG_MASK is therefore what the app paints OPAQUELY over main.bmp at runtime, not every control's
# hit rectangle: the hard keep-outs (title box, which marquee.js blanks with text.bmp's solid space
# cell and the TrueType title's caps/descenders cover, y24-35; the kbps/kHz and time digits; the
# play/work indicator; the visualizer; the clutter bar; the transport buttons), the travel lanes of
# the volume/balance and seek thumbs, and just the marks this file draws into the photo-sampled
# sprites (mono/stereo dots and the EQ/PL dot-and-letter columns, all pushed to their sprites'
# outer edges; shuffle/repeat sit below the seek lane anyway). The titlebar strip is photo-sampled
# too, so the hair runs up to the window's top edge. That leaves a clear face band right of the
# balance lane (x~216-274) between the title box and the seek lane (y36-72); the photo is placed
# (photo_scale/ox/oy, from a brute-force search over this mask) so the eyes-to-chin box fills that
# band while the photo still covers the full 116px height and reaches the right edge. The seek lane
# runs under the chin/neck, never across eyes-to-chin.
# ------------------------------------------------------------------------------------------

BIG_MASK = [
    (0, 0, 275, 14),                       # titlebar strip: its title text and buttons
    (111, 24, 154, 12),                    # title box (blanked + TrueType title)
    (111, 43, 15, 6), (156, 43, 10, 6),    # kbps / kHz digits
    (39, 26, 59, 13), (24, 28, 12, 9),     # time digits, work + play/pause indicator
    VIS_POS, CLUTTER_POS,                  # visualizer, clutter bar
    (16, 88, 142, 18),                     # transport buttons + eject
    (107, 57, 68, 13), (177, 57, 38, 13),  # volume / balance thumb lanes
    (16, 72, 248, 10),                     # seek thumb lane
    (212, 46, 2, 2), (266, 46, 2, 2),      # mono / stereo dots (at their sprites' outer edges)
    (219, 58, 3, 12), (262, 58, 3, 12),    # EQ / PL dot+letter columns (at their sprites' outer edges)
    (164, 89, 74, 15),                     # shuffle / repeat
]


def make_main_big(T):
    a = new(275, 116, T["BODY"])
    for r in range(116):
        rect(a, 0, r, 275, 1, lerp(T["BODY_HI"], T["BODY"], min(1, r / 90)))
    raised(a, 0, 0, 275, 116, T["BODY_HI"], T["BODY_LO"])

    # clutter slot + left display: indicator, time, analyzer (same fixed spots as every theme)
    rect(a, 10, 22, 8, 43, T["SLOT"])
    display_box(a, 21, 20, 84, 42, T)
    for x in (48, 60, 78, 90):
        seven_seg(a, x, 26, "", T)
    for yy in (29, 34):
        px(a, 73, yy, T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"])
        px(a, 74, yy, T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"])
    rect(a, 24, 60, 76, 1, lerp(T["DISP"], T["BODY"], 0.5))

    # transport tray - the one piece of chrome on the right of the displays that still fits
    # entirely left of where the portrait lands
    rect(a, 15, 87, 145, 20, T["SLOT"])
    sunken(a, 15, 87, 145, 20, T["BODY_HI"], T["BODY_LO"])

    rgb, cov, feat = photo_layer_explicit(T["photo_file"], T["photo_box"], T["photo_scale"],
                                           T["photo_ox"], T["photo_oy"], (275, 116))
    a[:] = lay_photo(a.astype(np.float64), rgb, cov)

    # kbps/khz: no boxed display (per the user: these readouts don't need a clearly defined
    # frame) - just the labels, drawn after the photo (KHZ can land on it) with a 1px shadow so
    # they hold up over either the chrome gradient or the photo
    lbl_ink = T["GREY_TXT"] if T["style"] == "noir" else T["INK_DIM"]
    shadow = T["BODY_LO"]
    draw_text(a, TINY, "KBPS", 129, 44, lbl_ink, shadow=shadow)
    draw_text(a, TINY, "KHZ", 169, 44, lbl_ink, shadow=shadow)

    # the chrome painted into main.bmp itself must stay off the face too
    drawn = BIG_MASK + [(21, 20, 84, 42), (15, 87, 145, 20), (129, 44, 16, 6), (169, 44, 12, 6)]
    occ = occupancy(drawn, (275, 116))
    check_features(f"{T['key']} main (photo-forward)", feat, occ, cov)
    return a


# ------------------------------------------------------------------------------------------
# The rest of Parasol/Plushie's chrome, redrawn small and photo-blended: monoster.bmp drops its
# MONO/STEREO text for a near-blank sheet with a tiny dot; shufrep.bmp's four buttons become a
# dot-plus-one-letter LED toggle; balance.bmp is one quiet backdrop with a thin tick instead of a
# coloured ramp; posbar.bmp's track is the photo itself (or the chrome gradient, left of it) with
# a slim line, not a separate opaque bevel. Each samples the final main.bmp (after the photo is
# composited) at its own fixed on-window rect, so the backdrop matches exactly.
# ------------------------------------------------------------------------------------------


def make_monoster_big(T, main):
    # sheet x0-29 (stereo) is drawn at STEREO_POS x239; sheet x29-56 (mono) at MONO_POS x212
    a = new(56, 24, T["BODY"])
    for y in (0, 12):
        a[y:y + 12, 0:29] = main[41:53, 239:268]
        a[y:y + 12, 29:56] = main[41:53, 212:239]
    on = T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"]
    dim = lerp(on, T["BODY"], 0.6)
    # one 2x2 dot each, at the outer edge (window x212 for mono, x266 for stereo), off the face
    for sx in (27, 29):
        rect(a, sx, 5, 2, 2, on)
        rect(a, sx, 17, 2, 2, dim)
    return a


def make_shufrep_big(T, main):
    a = new(92, 85, T["BODY"])
    sr_backdrop = main[89:104, 164:238].astype(np.int32)  # shuffle+repeat's combined on-window rect
    wnd_backdrop = main[58:70, 219:265].astype(np.int32)  # eq+pl toggle's combined on-window rect
    on = T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"]
    dim = T["GREY_TXT"] if T["style"] == "noir" else T["INK_DIM"]

    def dot_toggle(a, x, y, w, h, letter, on_state, pressed, backdrop, bx):
        a[y:y + h, x:x + w] = backdrop[:, bx:bx + w]
        o = 1 if pressed else 0
        ink = on if on_state else dim
        led(a, x + 3 + o, y + (h - 3) // 2 + o, on_state, T)
        draw_text(a, TINY, letter, x + 9 + o, y + (h - 5) // 2 + o, ink)

    for row, (on_s, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        # sheet cell 0 (w28) draws at REPEAT_POS=210 -> backdrop offset 210-164=46;
        # sheet cell 28 (w47) draws at SHUFFLE_POS=164 -> backdrop offset 0
        dot_toggle(a, 0, y, 28, 15, "R", on_s, pressed, sr_backdrop, 46)
        dot_toggle(a, 28, y, 47, 15, "S", on_s, pressed, sr_backdrop, 0)
    # EQ/PL sit right across the face band, so their mark is a dot over a letter, stacked in a
    # 3px column at the sprite's outer edge (EQ's left, x219-221; PL's right, x262-264); pressed
    # nudges it down a pixel, never sideways into the face
    def edge_toggle(x, y, letter, on_state, pressed, bx, col):
        a[y:y + 12, x:x + 23] = wnd_backdrop[:, bx:bx + 23]
        o = 1 if pressed else 0
        led(a, x + col, y + 1 + o, on_state, T)
        draw_text(a, TINY, letter, x + col, y + 5 + o, on if on_state else dim)

    for x, label, pressed in [(0, "E", False), (23, "P", False), (46, "E", True), (69, "P", True)]:
        bx, col = (0, 0) if label == "E" else (23, 20)
        edge_toggle(x, 61, label, False, pressed, bx, col)
        edge_toggle(x, 73, label, True, pressed, bx, col)
    return a


def make_balance_big(T, main):
    # as minimal as the seek bar: every frame is the photo-sampled track with one slim line; the
    # thumb's position is the only thing that changes
    a = new(68, 433, T["BODY"])
    backdrop = main[57:70, 177:215].astype(np.int32)  # balance's on-window rect, 38x13
    line = T["IVORY"] if T["style"] == "noir" else T["BODY_HI"]
    for i in range(28):
        y = i * 15
        a[y:y + 13, 9:47] = backdrop
        a[y + 13:y + 15, 9:47] = T["BODY"]
        rect(a, 11, y + 6, 34, 1, lerp(line, T["BODY"], 0.35))
    slider_thumbs(a, T)
    return a


def make_posbar_big(T, main):
    a = new(307, 10, T["BODY"])
    a[0:10, 0:248] = main[72:82, 16:264].astype(np.int32)
    line = T["IVORY"] if T["style"] == "noir" else T["BODY_HI"]
    rect(a, 2, 4, 244, 1, lerp(line, T["BODY"], 0.35))
    rail_thumb(a, 248, 0, 29, 10, T, False)
    rail_thumb(a, 278, 0, 29, 10, T, True)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36): transport buttons. Noir draws sharp triangular glyphs; Bunny draws the
# same shapes a touch smaller with rounded button corners.
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


def transport_icon(a, kind, x, y, w, h, T, pressed):
    ink = (T["RED_HI"] if T["style"] == "noir" else T["PINK"]) if pressed else \
        (T["SILVER_HI"] if T["style"] == "noir" else T["TEAL"])
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


def make_cbuttons(T):
    a = new(136, 36, T["BODY"])
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18)]
    for kind, x, w, h in specs:
        for pressed, y in ((False, 0), (True, 18)):
            panel_face(a, x, y, w, h, T, pressed, bg=T["BODY"])
            transport_icon(a, kind, x, y, w, h, T, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        panel_face(a, 114, y, 22, 16, T, pressed, bg=T["BODY"])
        transport_icon(a, "eject", 114, y, 22, 16, T, pressed)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85): SHUFFLE / REPEAT toggles, then the four EQ/PL toggle states.
# ------------------------------------------------------------------------------------------


def make_shufrep(T):
    a = new(92, 85, T["BODY"])
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        toggle(a, 0, y, 28, 15, "REPEAT", on, pressed, T)
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed, T)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        toggle(a, x, 61, 23, 12, label, False, pressed, T)
        toggle(a, x, 73, 23, 12, label, True, pressed, T)
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp (56 x 24), playpaus.bmp (48 x 9), numbers.bmp (99 x 13) / nums_ex.bmp (108 x 13),
# text.bmp (155 x 18 - the fixed character grid sprites.js's FONT_LOOKUP reads).
# ------------------------------------------------------------------------------------------


def make_monoster(T):
    a = new(56, 24, T["DISP"])
    on_col = T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"]
    dim_col = lerp(T["DISP"], on_col, 0.18)
    for y, on in ((0, True), (12, False)):
        col = on_col if on else dim_col
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 42, y + 3, col)
    return a


def make_playpaus(T):
    a = new(48, 9, T["DISP"])
    col = T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"]
    tri_right(a, 2, 1, 7, col)
    rect(a, 9 + 2, 1, 2, 7, col)
    rect(a, 9 + 5, 1, 2, 7, col)
    rect(a, 18 + 2, 2, 5, 5, col)
    rect(a, 36, 0, 3, 9, T["DISP"])
    rect(a, 39 + 1, 3, 1, 3, col)
    return a


def make_numbers(T, ex):
    a = new(108 if ex else 99, 13, T["DISP"])
    for n in range(10):
        seven_seg(a, 9 * n, 0, DIGIT_SEGS[n], T)
    seven_seg(a, 90, 0, "", T)
    if ex:
        rect(a, 99, 0, 9, 13, T["DISP"])
        on = T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"]
        rect(a, 99 + 2, 6, 5, 1, on)
    return a


def make_text(T):
    a = new(155, 18, T["DISP"])
    ink = T["RED_HI"] if T["style"] == "noir" else T["TEAL"]
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key, col * 5, row * 6, ink)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433): 28-frame sliders. Noir's fill ramps
# silver to red with travel; Bunny's ramps teal to yellow to pink - a little rainbow in the slot.
# ------------------------------------------------------------------------------------------


def level_ramp(T):
    if T["style"] == "noir":
        return [T["RED_LO"], T["RED"], T["RED_HI"], T["SILVER"], T["SILVER_HI"]]
    return [T["TEAL_LO"], T["TEAL"], T["TEAL_HI"], T["YELLOW"], T["PINK_HI"]]


def rail_thumb(a, x, y, w, h, T, selected, grip="v"):
    hi = T["IVORY"] if T["style"] == "noir" else T["BODY_HI"]
    ink = (T["RED_HI"] if T["style"] == "noir" else T["PINK"]) if selected else \
        (T["SILVER"] if T["style"] == "noir" else T["TEAL"])
    top, bot = (lerp(ink, hi, 0.5), ink) if not selected else (lerp(ink, hi, 0.75), lerp(ink, (0, 0, 0), 0.1))
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(top, bot, r / max(1, h - 1)))
    edge(a, x, y, w, h, hi, hi, T["BODY_LO"], T["BODY_LO"])
    if T["style"] == "bunny":
        round_corners(a, x, y, w, h, T["BODY"])
    cx, cy = x + w // 2, y + h // 2
    if grip == "v":
        for gx in (cx - 2, cx, cx + 2):
            rect(a, gx, y + 3, 1, h - 6, T["BODY_LO"])
    else:
        for gy in (cy - 2, cy, cy + 2):
            rect(a, x + 3, gy, w - 6, 1, T["BODY_LO"])


def make_posbar(T, main):
    a = new(307, 10, T["BODY"])
    a[0:10, 0:248] = main[72:82, 16:264]
    rect(a, 0, 2, 248, 6, T["SLOT"])
    sunken(a, 0, 2, 248, 6, T["BODY_HI"], T["BODY_LO"])
    rect(a, 2, 4, 244, 2, lerp(T["SLOT"], (0, 0, 0), 0.3))
    for x in range(8, 244, 12):
        px(a, x, 4, lerp(T["SLOT"], T["BODY_HI"], 0.3))
    rail_thumb(a, 248, 0, 29, 10, T, False)
    rail_thumb(a, 278, 0, 29, 10, T, True)
    return a


def slider_thumbs(a, T):
    rail_thumb(a, 0, 422, 14, 11, T, True)
    rail_thumb(a, 15, 422, 14, 11, T, False)


def make_volume(T, main):
    a = new(68, 433, T["BODY"])
    seat = main[57:72, 107:175]
    stops = level_ramp(T)
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        rect(a, 1, y + 3, 66, 7, T["SLOT"])
        sunken(a, 1, y + 3, 66, 7, T["BODY_HI"], T["BODY_LO"])
        level = (i + 1) / 28
        fill_to = 7 + round(level * 54)
        colour = ramp(stops, level)
        for x in range(2, 66):
            hgt = 1 + round(4 * (x - 2) / 63)
            top = y + 9 - hgt
            if x < fill_to:
                rect(a, x, top, 1, hgt, colour)
            else:
                rect(a, x, top, 1, hgt, lerp(T["SLOT"], (0, 0, 0), 0.4))
        rect(a, 0, y + 13, 68, 2, T["BODY"])
    slider_thumbs(a, T)
    return a


def make_balance(T, main):
    a = new(68, 433, T["BODY"])
    seat = main[57:72, 177:215]
    stops = level_ramp(T)
    neutral = T["GREY_TXT"] if T["style"] == "noir" else T["INK_DIM"]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        rect(a, 10, y + 3, 36, 7, T["SLOT"])
        sunken(a, 10, y + 3, 36, 7, T["BODY_HI"], T["BODY_LO"])
        t = i / 27
        colour = neutral if i == 0 else ramp(stops, t)
        reach = round(12 * t)
        for x in range(11, 45):
            d = abs(x - 28)
            hgt = 1 + round(4 * min(d, 16) / 16)
            top = y + 9 - hgt
            col = colour if d <= max(1, reach) else lerp(T["SLOT"], (0, 0, 0), 0.4)
            rect(a, x, top, 1, hgt, col)
        tick = T["IVORY"] if T["style"] == "noir" else T["INK"]
        rect(a, 28, y + 2, 1, 2, tick if i == 0 else neutral)
        rect(a, 9, y + 13, 38, 2, T["BODY"])
    slider_thumbs(a, T)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------


def eq_slider_frame(a, x, y, n, T):
    rect(a, x, y, 14, 63, T["SLOT"])
    sunken(a, x, y, 14, 63, T["BODY_HI"], T["BODY_LO"])
    rect(a, x + 4, y + 2, 5, 59, lerp(T["SLOT"], (0, 0, 0), 0.3))
    sunken(a, x + 4, y + 2, 5, 59, T["BODY_HI"], T["BODY_LO"])
    v = n / 27
    centre = round((1 - v) * 51) + 5
    colour = ramp(level_ramp(T), v)
    for r in range(3, 60):
        on = r >= centre
        rect(a, x + 5, y + r, 3, 1, colour if on else lerp(T["SLOT"], (0, 0, 0), 0.3))
    zero_ink = T["IVORY_DIM"] if T["style"] == "noir" else T["INK_DIM"]
    rect(a, x + 1, y + 30, 2, 1, zero_ink)
    rect(a, x + 11, y + 30, 2, 1, zero_ink)


def eq_toggle_variant(a, x, y, w, h, label, on, pressed, T):
    panel_face(a, x, y, w, h, T, pressed, bg=T["BODY"])
    ink = (T["RED_HI"] if T["style"] == "noir" else T["PINK"]) if on else \
        (T["GREY_TXT"] if T["style"] == "noir" else T["INK_DIM"])
    o = 1 if pressed else 0
    text_center(a, TINY, label, x + w // 2 + o, y + 3 + o, ink)


def make_eqmain(T):
    a = new(275, 315, T["BODY"])
    for r in range(116):
        rect(a, 0, r, 275, 1, lerp(T["BODY_HI"], T["BODY"], min(1, r / 90)))
    raised(a, 0, 0, 275, 116, T["BODY_HI"], T["BODY_LO"])
    rib(a, 1, 1, 273, 114, T["RIB_LO"], T["RIB_HI"], period=5, amp=0.5)
    a[0:14, :] = eq_titlebar(T, True)

    sunken(a, 85, 16, 115, 21, T["BODY_HI"], T["BODY_LO"])
    rect(a, 16, 36, 245, 68, T["SLOT"])
    sunken(a, 16, 36, 245, 68, T["BODY_HI"], T["BODY_LO"])
    rect(a, 39, 37, 1, 66, T["BODY_LO"])
    rect(a, 40, 37, 1, 66, T["BODY_HI"])
    lbl = T["GREY_TXT"] if T["style"] == "noir" else T["INK_DIM"]
    for txt, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, txt, 58, yy, lbl)
        rect(a, 42, yy + 2, 3, 1, lbl)
        rect(a, 71, yy + 2, 3, 1, lbl)
    for x in [21] + [EQ_FIRST_BAND + EQ_BAND_STEP * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14, T)
    text_center(a, TINY, "PREAMP", 28, 106, lbl)
    for i, bnd in enumerate(EQ_BANDS):
        text_center(a, TINY, bnd, EQ_FIRST_BAND + EQ_BAND_STEP * i + 7, 106, lbl)
    rect(a, 4, 113, 267, 1, T["RED_LO"] if T["style"] == "noir" else T["TEAL_LO"])

    mini_button(a, 0, 125, "close", T, True, pressed=True)
    # ON: normal(10), selected(69), depressed(128), selectedDepressed(187) - each w26
    eq_toggle_variant(a, 10, 119, 26, 12, "ON", False, False, T)
    eq_toggle_variant(a, 69, 119, 26, 12, "ON", True, False, T)
    eq_toggle_variant(a, 128, 119, 26, 12, "ON", False, True, T)
    eq_toggle_variant(a, 187, 119, 26, 12, "ON", True, True, T)
    # AUTO: normal(36), selected(95), depressed(154), selectedDepressed(213) - each w32
    eq_toggle_variant(a, 36, 119, 32, 12, "AUTO", False, False, T)
    eq_toggle_variant(a, 95, 119, 32, 12, "AUTO", True, False, T)
    eq_toggle_variant(a, 154, 119, 32, 12, "AUTO", False, True, T)
    eq_toggle_variant(a, 213, 119, 32, 12, "AUTO", True, True, T)

    a[134:148, :] = eq_titlebar(T, True)
    a[149:163, :] = eq_titlebar(T, False)
    rail_thumb(a, 0, 164, 11, 11, T, False, grip="h")
    rail_thumb(a, 0, 176, 11, 11, T, True, grip="h")
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n, T)
    for y, pressed in ((164, False), (176, True)):
        panel_face(a, 224, y, 44, 12, T, pressed, bg=T["BODY"])
        o = 1 if pressed else 0
        ink = (T["RED_HI"] if T["style"] == "noir" else T["PINK"]) if pressed else \
            (T["IVORY"] if T["style"] == "noir" else T["INK"])
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 3 + o, ink)

    # response graph: a small colour strip (graphColors) read per-row by the app, plus a blank
    # plotting field and a 1px preamp-line sprite.
    rect(a, 0, 294, 113, 19, T["DISP"])
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, lerp(T["DISP"], T["BODY_HI"], 0.2))
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, lerp(T["DISP"], T["BODY_HI"], 0.3))
    stops = level_ramp(T)
    for r in range(19):
        px(a, 115, 294 + r, ramp(list(reversed(stops)), r / 18))
    line_col = T["IVORY"] if T["style"] == "noir" else T["INK"]
    for x in range(113):
        px(a, x, 314, line_col if x % 3 != 2 else T["DISP"])
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp, photo-forward variant: a second HeeJin photo, its face in the dB-scale gap between
# the preamp slider and the first band, the rest of it running across the window behind the
# sliders. equalizer.js draws the preamp from the very same slider frames (x13+(n%14)*15,
# y164/229) and thumb (0,164/176) as the ten bands, so the preamp can't be styled alone: all
# eleven are made minimal together - each frame a flat column in the photo's own median tone
# (measured under the band lanes) with a 2px level line, each thumb that tone with a slim bar -
# so they read as thin lines over the picture. They are still opaque columns at runtime, and one
# frame serves all eleven positions. With pledit.txt's YTMinampTransparent key (see make_eqmain_big)
# the frames' backgrounds are see-through in YTMinamp, but each thumb still travels its lane's full
# height and the level line is drawn there, so the face stays clear of every lane: EQ_MASK is what
# equalizer.js paints opaquely over eqmain (titlebar, close, the On/Auto sprites, Presets, the
# graph, the eleven slider lanes) plus the PREAMP and band labels this file redraws over the
# photo. The graph's own background is photo-sampled too. The dB labels are dropped.
# ------------------------------------------------------------------------------------------

EQ_MASK = [(0, 0, 275, 14), EQ_CLOSE, (14, 18, 58, 12), EQ_PRESETS, (86, 17, 113, 19),
           (21, 38, 14, 63)] + [(EQ_FIRST_BAND + EQ_BAND_STEP * i, 38, 14, 63) for i in range(10)] + \
          [(17, 106, 24, 5), (76, 106, 195, 5)]


def slim_eq_frame(a, x, y, n, T, tone):
    rect(a, x, y, 14, 63, tone)
    line = lerp(tone, T["IVORY"] if T["style"] == "noir" else T["BODY_HI"], 0.3)
    rect(a, x + 6, y + 3, 2, 57, line)
    v = n / 27
    top = round((1 - v) * 51) + 5
    rect(a, x + 6, y + top, 2, 60 - top, ramp(level_ramp(T), v))


def slim_eq_thumb(a, x, y, T, tone, selected):
    rect(a, x, y, 11, 11, tone)
    ink = (T["RED_HI"] if T["style"] == "noir" else T["PINK"]) if selected else \
        (T["IVORY"] if T["style"] == "noir" else T["INK"])
    # a 1px edge above and below the bar so it holds up over dark hair and pale backdrop alike
    halo = T["BODY_LO"] if T["style"] == "noir" else T["BODY_HI"]
    rect(a, x + 1, y + 3, 9, 1, halo)
    rect(a, x + 1, y + 7, 9, 1, halo)
    rect(a, x + 1, y + 4, 9, 3, ink)


def make_eqmain_big(T):
    a = make_eqmain(T)
    rgb, cov, feat = photo_layer_explicit(T["eq_photo_file"], T["eq_photo_box"], T["eq_photo_scale"],
                                           T["eq_photo_ox"], T["eq_photo_oy"], (275, 116), feather=24)
    body = np.zeros((116, 275))
    body[14:115, 1:274] = 1  # under the titlebar, inside the window's outline
    cov = cov * body
    # The photo is narrower than the window (a close-up's face is a third of its frame, and the
    # face has to fit the dB gap), so the rest of the window's body is filled with the photo's own
    # backdrop colour (median of a plain patch of the source, eq_backdrop_box) and the photo fades
    # into that: one picture, not a photo glued onto the chassis's slider bay.
    src = np.asarray(Image.open(T["eq_photo_file"]).convert("RGB").crop(T["eq_backdrop_box"]))
    backdrop = tuple(int(v) for v in np.median(src.reshape(-1, 3), axis=0))
    win = a[0:116].astype(np.float64)
    win[14:115, 1:274] = backdrop
    a[0:116] = lay_photo(win, rgb, cov)

    lbl = T["GREY_TXT"] if T["style"] == "noir" else T["INK_DIM"]
    sh = T["BODY_LO"] if T["style"] == "noir" else T["BODY_HI"]
    text_center(a, TINY, "PREAMP", 28, 106, lbl, shadow=sh)
    for i, bnd in enumerate(EQ_BANDS):
        text_center(a, TINY, bnd, EQ_FIRST_BAND + EQ_BAND_STEP * i + 7, 106, lbl, shadow=sh)

    # Slider frames: background in ONE key colour, the backdrop's, named in pledit.txt as
    # YTMinampTransparent - see-through in YTMinamp (the photo runs on behind all eleven
    # sliders, only the 2px level line and the thumb drawn over it), a flat backdrop-coloured
    # column in real Winamp. The key must not occur in the frames' marks (BMP is lossless and the
    # match exact), so it's checked after drawing.
    key = backdrop
    T["eq_key"] = key
    for n in range(28):
        fx, fy = 13 + (n % 14) * 15, 164 + (n // 14) * 65
        slim_eq_frame(a, fx, fy, n, T, key)
        marks = a[fy + 3:fy + 60, fx + 6:fx + 8]  # the level line and fill
        assert not (marks == np.array(key)).all(axis=-1).any(), f"{T['key']}: key colour inside a level mark"
    # thumbs (0,164) and (0,176) are inside the keyed region too: their surround is the key, so
    # only the slim bar shows over the photo in YTMinamp (a backdrop tab in real Winamp)
    slim_eq_thumb(a, 0, 164, T, key, False)
    slim_eq_thumb(a, 0, 176, T, key, True)
    for ty in (164, 176):
        bar = a[ty + 3:ty + 8, 1:10]
        assert not (bar == np.array(key)).all(axis=-1).any(), f"{T['key']}: key colour inside a thumb bar"
    a[294:313, 0:113] = a[17:36, 86:199]  # graph background: the photo where the graph sits

    # On / Auto: photo-sampled from the finished window, a dot and one letter each. Auto does
    # nothing in YTMinamp, so it's the quieter of the two.
    on_c = T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"]
    dim = T["GREY_TXT"] if T["style"] == "noir" else T["INK_DIM"]
    on_bg, auto_bg = a[18:30, 14:40].copy(), a[18:30, 40:72].copy()
    for x, sel, pressed in ((10, False, False), (69, True, False), (128, False, True), (187, True, True)):
        a[119:131, x:x + 26] = on_bg
        o = 1 if pressed else 0
        led(a, x + 1, 119 + 4 + o, sel, T)
        draw_text(a, TINY, "O", x + 5, 119 + 3 + o, on_c if sel else dim)
    for x, sel, pressed in ((36, False, False), (95, True, False), (154, False, True), (213, True, True)):
        a[119:131, x:x + 32] = auto_bg
        o = 1 if pressed else 0
        draw_text(a, TINY, "A", x + 24, 119 + 3 + o, lerp(on_c, T["BODY"], 0.3) if sel else lerp(dim, T["BODY"], 0.3))
        led(a, x + 28, 119 + 4 + o, sel, T)

    occ = occupancy(EQ_MASK, (275, 116))
    check_features(f"{T['key']} eq (photo)", feat, occ, cov)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186): the playlist editor frame, and gen.bmp (194 x 109): the generic window
# frame (used here for the Album Art window). Both are tiled pieces - Layout authority says their
# material must vary vertically only - so both themes keep their chassis texture's ribbing
# vertical and never tile a 2D pattern across them.
# ------------------------------------------------------------------------------------------


def make_pledit(T):
    a = new(280, 186, T["BODY"])
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, T)
        rib(t, 0, 0, 25, 20, T["RIB_LO"], T["RIB_HI"], period=5, amp=0.4)
        trim(t, 0, 1, 25, T, bg=t[1, 0].tolist())
        rect(t, 0, 19, 25, 1, T["BODY_LO"])
        a[y:y + 20, 127:152] = t

        t = bar20(25, T)
        rib(t, 4, 0, 21, 20, T["RIB_LO"], T["RIB_HI"], period=5, amp=0.4)
        rect(t, 0, 0, 1, 20, T["BODY_HI"])
        trim(t, 4, 1, 21, T, bg=t[1, 4].tolist())
        rect(t, 11, 19, 14, 1, T["BODY_LO"])
        a[y:y + 20, 0:25] = t

        t = bar20(100, T)
        title = T["pl_title"]
        plate_cap_left(t, 0, BAR_PLATE_Y, lit, T)
        plate(t, 4, BAR_PLATE_Y, 92, lit, T)
        plate_cap_right(t, 96, BAR_PLATE_Y, lit, T)
        text_center(t, FONT5, title, 50, BAR_PLATE_Y + 2, plate_ink(T, lit))
        rect(t, 0, 19, 100, 1, T["BODY_LO"])
        a[y:y + 20, 26:126] = t

        t = bar20(25, T)
        rect(t, 24, 0, 1, 20, T["BODY_LO"])
        rib(t, 0, 0, 12, 20, T["RIB_LO"], T["RIB_HI"], period=5, amp=0.4)
        mini_button(t, 14, 3, "close", T, lit)
        rect(t, 0, 19, 6, 1, T["BODY_LO"])
        rect(t, 5, 13, 1, 7, T["BODY_HI"])
        rect(t, 9, 14, 10, 6, T["SLOT"])
        rect(t, 9, 14, 10, 1, T["BODY_LO"])
        rect(t, 9, 14, 1, 6, T["BODY_LO"])
        rect(t, 18, 14, 1, 6, T["BODY_HI"])
        a[y:y + 20, 153:178] = t

    t = new(12, 29)
    rect(t, 0, 0, 12, 29, T["BODY"])
    rib(t, 0, 0, 12, 29, T["RIB_LO"], T["RIB_HI"], period=5, amp=0.4)
    rect(t, 0, 0, 1, 29, T["BODY_HI"])
    rect(t, 11, 0, 1, 29, T["BODY_LO"])
    a[42:71, 0:12] = t

    t = new(20, 29)
    rect(t, 0, 0, 20, 29, T["BODY"])
    rib(t, 0, 0, 20, 29, T["RIB_LO"], T["RIB_HI"], period=5, amp=0.4)
    rect(t, 0, 0, 1, 29, T["BODY_HI"])
    rect(t, 19, 0, 1, 29, T["BODY_LO"])
    rect(t, 4, 0, 10, 29, T["SLOT"])
    rect(t, 4, 0, 1, 29, T["BODY_LO"])
    rect(t, 13, 0, 1, 29, T["BODY_HI"])
    a[42:71, 31:51] = t

    t = new(9, 9)
    mini_button(t, 0, 0, "close", T, True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        rail_thumb(a, x, 53, 8, 18, T, sel, grip="h")

    def bottom_base(w):
        t = new(w, 38, T["BODY"])
        rib(t, 0, 0, w, 38, T["RIB_LO"], T["RIB_HI"], period=5, amp=0.4)
        rect(t, 0, 0, w, 1, T["BODY_HI"])
        rect(t, 0, 37, w, 1, T["BODY_LO"])
        rect(t, 0, 33, w, 1, T["RED_LO"] if T["style"] == "noir" else T["TEAL_LO"])
        rect(t, 0, 34, w, 1, T["BODY_LO"])
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, T["BODY_HI"])
    rect(t, 11, 0, 1, 1, T["BODY_LO"])
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        panel_face(t, bx, 8, 22, 18, T, False, bg=T["BODY"])
        ink = T["IVORY"] if T["style"] == "noir" else T["INK"]
        text_center(t, TINY, lbl, bx + 11, 15, ink)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, T["BODY_LO"])
    display_box(t, 6, 9, 56, 8, T)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        panel_face(t, bx, 22, 10, 10, T, False, bg=T["BODY"])
        mini_transport_icon(t, kind, bx, 22, T)
    display_box(t, 65, 22, 33, 8, T)
    colon = T["RED_HI"] if T["style"] == "noir" else T["PINK_HI"]
    rect(t, 84, 24, 1, 1, colon)
    rect(t, 84, 27, 1, 1, colon)
    panel_face(t, 106, 8, 22, 18, T, False, bg=T["BODY"])
    ink = T["IVORY"] if T["style"] == "noir" else T["INK"]
    text_center(t, TINY, "LIST", 117, 15, ink)
    grip_col = T["SILVER"] if T["style"] == "noir" else T["TEAL"]
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx, gy, grip_col)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


def mini_transport_icon(a, kind, x, y, T):
    ink = T["SILVER_HI"] if T["style"] == "noir" else T["TEAL"]
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
GEN_SEP = (255, 0, 255)  # the row's reference/separator colour the app's letter-scan keys off of


def make_gen(T):
    a = new(194, 109, T["BODY"])
    rib(a, 0, 0, 194, 109, T["RIB_LO"], T["RIB_HI"], period=5, amp=0.4)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn):
            t = bar20(25, T)
            fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 1, 20, T["BODY_HI"])
            trim(t, 4, 1, 21, T, bg=t[1, 4].tolist())

        def left_end(t):
            trim(t, 0, 1, 16, T, bg=t[1, 0].tolist())
            plate_cap_left(t, 17, BAR_PLATE_Y, lit, T)
            plate(t, 21, BAR_PLATE_Y, 4, lit, T)

        def centre(t):
            plate(t, 0, BAR_PLATE_Y, 25, lit, T)

        def right_end(t):
            plate(t, 0, BAR_PLATE_Y, 4, lit, T)
            plate_cap_right(t, 4, BAR_PLATE_Y, lit, T)
            trim(t, 9, 1, 16, T, bg=t[1, 9].tolist())

        def fill(t):
            trim(t, 0, 1, 25, T, bg=t[1, 0].tolist())

        def right(t):
            trim(t, 0, 1, 12, T, bg=t[1, 0].tolist())
            mini_button(t, 14, 3, "close", T, lit)
            rect(t, 24, 0, 1, 20, T["BODY_LO"])

        piece(0, left)
        piece(26, left_end)
        piece(52, centre)
        piece(78, right_end)
        piece(104, fill)
        piece(130, right)

    def bottom(w, grip, left_edge):
        t = new(w, 14, T["BODY"])
        rib(t, 0, 0, w, 14, T["RIB_LO"], T["RIB_HI"], period=5, amp=0.4)
        rect(t, 0, 13, w, 1, T["BODY_LO"])
        rect(t, 0, 9, w, 1, T["RED_LO"] if T["style"] == "noir" else T["TEAL_LO"])
        rect(t, 0, 10, w, 1, T["BODY_LO"])
        rect(t, 0, 0, 1, 14, T["BODY_HI"] if left_edge else T["BODY"])
        if not left_edge:
            rect(t, w - 1, 0, 1, 14, T["BODY_LO"])
        if grip:
            grip_col = T["SILVER"] if T["style"] == "noir" else T["TEAL"]
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 7 - 3 * j
                    px(t, gx, gy, grip_col)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]

    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h, T["BODY"])
        rib(t, 0, 0, w, h, T["RIB_LO"], T["RIB_HI"], period=5, amp=0.4)
        if outer_left:
            rect(t, 0, 0, 1, h, T["BODY_HI"])
        else:
            rect(t, w - 1, 0, 1, h, T["BODY_LO"])
        a[42:42 + h, x:x + w] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", T, True, pressed=True)
    a[42:51, 148:157] = t

    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, GEN_SEP)
        x = 1
        ink = plate_ink(T, lit)
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            rect(a, x, y, w, 7, T["DISP"] if lit else lerp(T["DISP"], T["BODY_LO"], 0.4))
            draw_text(a, FONT5, c, x, y + 1, ink)
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp's 18 colours (skins/genex_wacup.py derives the rest + fixes contrast for real
# Winamp/WACUP's Media Library), viscolor.txt, pledit.txt, readme.txt
# ------------------------------------------------------------------------------------------


def hexc(c):
    return f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}"


def make_genex18(T):
    if T["style"] == "noir":
        return [
            T["DISP"], T["IVORY"], T["BODY"], T["IVORY"], T["IVORY"],
            T["BODY_LO"], T["RED"], T["PANEL"], T["SILVER_HI"],
            T["BODY_HI"], T["BODY"], T["BODY_LO"], T["BODY"],
            T["SILVER"], T["BODY_LO"], T["RED_HI"], T["BODY_HI"], T["BODY_LO"],
        ]
    return [
        T["PANEL"], T["INK"], T["BODY"], T["INK"], T["INK"],
        T["BODY_LO"], T["PINK"], T["TEAL"], T["BODY_HI"],
        T["BODY_HI"], T["PANEL"], T["BODY_LO"], T["BODY"],
        T["TEAL"], T["PANEL"], T["PINK_HI"], T["BODY_HI"], T["BODY_LO"],
    ]


def make_genex(T):
    a = new(256, 64, T["BODY"])
    rect(a, 0, 1, 256, 63, T["BODY"])
    rect(a, 0, 0, 256, 1, T["BODY"])
    for i, c in enumerate(make_genex18(T)):
        px(a, 48 + 2 * i, 0, c)
    panel_face(a, 0, 1, 47, 15, T, False, bg=T["BODY"])
    panel_face(a, 0, 16, 47, 15, T, True, bg=T["BODY"])
    return a


def viscolor(T):
    if T["style"] == "noir":
        spec = ramp_series([T["IVORY"], T["RED_HI"], T["RED"], T["RED_LO"], (40, 10, 14)], 16)
        osc = [T["IVORY"], T["SILVER_HI"], T["SILVER"], T["RED"], T["RED_LO"]]
        return ([(T["DISP"], "background"), (T["RED_LO"], "dots")]
                + [(c, f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}") for i, c in enumerate(spec)]
                + [(osc[0], "oscilloscope 1"), (osc[1], "oscilloscope 2"), (osc[2], "oscilloscope 3"),
                   (osc[3], "oscilloscope 4"), (osc[4], "oscilloscope 5"), (T["IVORY"], "peaks")])
    spec = ramp_series([T["PINK_HI"], T["PINK"], T["YELLOW"], T["TEAL_HI"], T["TEAL"]], 16)
    osc = [T["INK"], T["TEAL"], T["TEAL_HI"], T["PINK"], T["PINK_LO"]]
    return ([(T["DISP"], "background"), (T["TEAL_LO"], "dots")]
            + [(c, f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}") for i, c in enumerate(spec)]
            + [(osc[0], "oscilloscope 1"), (osc[1], "oscilloscope 2"), (osc[2], "oscilloscope 3"),
               (osc[3], "oscilloscope 4"), (osc[4], "oscilloscope 5"), (T["YELLOW_HI"], "peaks")])


def ramp_series(stops, n):
    return [ramp(stops, i / (n - 1)) for i in range(n)]


def pledit_colours(T):
    if T["style"] == "noir":
        return dict(Normal=T["IVORY"], Current=T["RED_HI"], NormalBG=T["DISP"],
                    SelectedBG=lerp(T["RED_LO"], T["BODY_HI"], 0.35))
    return dict(Normal=T["INK"], Current=T["PINK_LO"], NormalBG=T["PANEL"],
                SelectedBG=T["PINK_HI"])


def write_text_files(T, out):
    with open(os.path.join(out, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor(T):
            f.write(f"{r},{g},{b}, // {note}\n")
    c = pledit_colours(T)
    with open(os.path.join(out, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={hexc(c['Normal'])}\nCurrent={hexc(c['Current'])}\n"
                f"NormalBG={hexc(c['NormalBG'])}\nSelectedBG={hexc(c['SelectedBG'])}\n"
                f"MbBG={hexc(c['NormalBG'])}\nMbFG={hexc(c['Normal'])}\nFont=Arial\n")
        if T.get("eq_key"):
            # YTMinamp's one skin extension: this exact colour is see-through in the EQ slider
            # frames (eqmain.bmp x13 y164, 28 frames of 14x63); real Winamp ignores the key
            f.write(f"YTMinampTransparent={hexc(T['eq_key'])}\n")
    DISPLAY_NAME = {"noir": "Lace Noir", "bunny": "Bunny Pop", "parasol": "Parasol", "plushie": "Plushie"}
    with open(os.path.join(out, "readme.txt"), "w", newline="\r\n") as f:
        photo_rel = os.path.relpath(T["photo_file"], HERE)
        f.write(
            f"HeeJin: {DISPLAY_NAME[T['key']]} - a personal fan skin for HeeJin (ARTMS), generated procedurally.\n\n"
            "Every bitmap is drawn by a script (gen_skin.py) from rectangles, bevels and a pixel font\n"
            "made for this skin; the one exception is the main window's portrait, a crop of a real\n"
            f"candid photo of HeeJin ({photo_rel}, already provided with this skin's\n"
            "brief; no further attribution is known to credit). No logos or third-party marks appear.\n\n"
            "License: CC0 1.0 Universal (public domain dedication) for everything but the photo crop.\n"
            "https://creativecommons.org/publicdomain/zero/1.0/\n"
        )


# ------------------------------------------------------------------------------------------
# Build: write every sheet + text file, zip the .wsz, finish it with genex_wacup.
# ------------------------------------------------------------------------------------------


def build(key):
    T = THEMES[key]
    out = os.path.join(OUT_ROOT, key)
    os.makedirs(out, exist_ok=True)
    big = T.get("big_photo")
    main = make_main_big(T) if big else make_main(T)
    sheets = {
        "main.bmp": main,
        "titlebar.bmp": make_titlebar_big(T, main) if big else make_titlebar(T),
        "cbuttons.bmp": make_cbuttons(T),
        "shufrep.bmp": make_shufrep_big(T, main) if big else make_shufrep(T),
        "posbar.bmp": make_posbar_big(T, main) if big else make_posbar(T, main),
        "volume.bmp": make_volume(T, main),
        "balance.bmp": make_balance_big(T, main) if big else make_balance(T, main),
        "monoster.bmp": make_monoster_big(T, main) if big else make_monoster(T),
        "playpaus.bmp": make_playpaus(T),
        "numbers.bmp": make_numbers(T, False),
        "nums_ex.bmp": make_numbers(T, True),
        "text.bmp": make_text(T),
        "pledit.bmp": make_pledit(T),
        "eqmain.bmp": make_eqmain_big(T) if big else make_eqmain(T),
        "gen.bmp": make_gen(T),
        "genex.bmp": make_genex(T),
    }
    imgs = {}
    for name, arr in sheets.items():
        imgs[name[:-4]] = save(arr, os.path.join(out, name))
    write_text_files(T, out)
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "readme.txt"]
    wsz = os.path.join(HERE, T["wsz"])
    with zipfile.ZipFile(wsz, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(os.path.join(out, n), n)
    genex_wacup.process(wsz)  # a complete 24-colour genex.bmp + the standard ML button/scrollbar art
    return imgs, names


# ------------------------------------------------------------------------------------------
# Preview: the windows put together from the sprites the way the app does.
# ------------------------------------------------------------------------------------------


def blit(dst, sheet, r, dx, dy, w=None):
    x, y, rw, rh = r
    w = rw if w is None else w
    dst.paste(sheet.crop((x, y, x + w, y + rh)), (dx, dy))


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


def draw_bitmap_text(dst, sheets, s, x, y):
    text = sheets["text"]
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, text, (col * 5, row * 6, 5, 6), x, y)
        x += 5


def preview_main(T, sheets, lit, state):
    S = sheets
    img = Image.new("RGB", (275, 116))
    img.paste(S["main"], (0, 0))
    blit(img, S["titlebar"], (27, 0 if lit else 15, 275, 14), 0, 0)
    cb_src = {"previous": (0, 23, 18), "play": (23, 23, 18), "pause": (46, 23, 18), "stop": (69, 23, 18),
              "next": (92, 22, 18)}
    for name, (sx, w, h) in cb_src.items():
        wx, wy, _, _ = CBUTTONS_POS[name]
        sy = 18 if state["pressed"] == name else 0
        blit(img, S["cbuttons"], (sx, sy, w, h), wx, wy)
    ex, ey, ew, eh = CBUTTONS_POS["eject"]
    blit(img, S["cbuttons"], (114, 16 if state["pressed"] == "eject" else 0, 22, 16), ex, ey)
    for name, pos, on in (("eq", EQ_TOGGLE_POS, state["eq"]), ("pl", PL_TOGGLE_POS, state["pl"])):
        pressed = state["pressed"] == name
        sx = (0 if name == "eq" else 23) + (46 if pressed else 0)
        blit(img, S["shufrep"], (sx, 73 if on else 61, 23, 12), *pos)
    blit(img, S["titlebar"], (304, 0, 8, 43), *CLUTTER_POS[:2])
    spr = {"O": (304, 47, 8, 8, 3), "A": (312, 55, 8, 7, 11), "I": (320, 62, 8, 7, 18), "D": (328, 69, 8, 8, 25),
           "V": (336, 77, 8, 7, 33)}
    for L in state["clutter"]:
        x, y, w, h, oy = spr[L]
        blit(img, S["titlebar"], (x, y, w, h), CLUTTER_POS[0], CLUTTER_POS[1] + oy)
    for name, x0, w, on, dst in (("shuffle", 28, 47, state["shuffle"], SHUFFLE_POS),
                                  ("repeat", 0, 28, state["repeat"], REPEAT_POS)):
        row = (2 if on else 0) + (1 if state["pressed"] == name else 0)
        blit(img, S["shufrep"], (x0, row * 15, w, 15), *dst)
    blit(img, S["playpaus"], (0 if state["playing"] else 9, 0, 9, 9), *PLAY_PAUSE_POS[:2])
    blit(img, S["monoster"], (29, 12 if state["stereo"] else 0, 27, 12), *MONO_POS)
    blit(img, S["monoster"], (0, 0 if state["stereo"] else 12, 29, 12), *STEREO_POS)
    blit(img, S["posbar"], (0, 0, 248, 10), POSBAR_POS[0], POSBAR_POS[1])
    tl = round(state["pos"] * 219)
    blit(img, S["posbar"], (278 if state["seek"] else 248, 0, 29, 10), POSBAR_POS[0] + tl, POSBAR_POS[1])
    v = state["volume"]
    idx = max(0, round(v / 100 * 28) - 1)
    blit(img, S["volume"], (0, idx * 15, 68, 13), VOLUME_POS[0], VOLUME_POS[1])
    blit(img, S["volume"], (0 if state["vdrag"] else 15, 422, 14, 11),
         VOLUME_POS[0] + round(v / 100 * 54), VOLUME_POS[1] + 1)
    bal = state["balance"]
    idx = int(abs(bal) / 100 * 27)
    blit(img, S["balance"], (9, idx * 15, 38, 13), BALANCE_POS[0], BALANCE_POS[1])
    blit(img, S["balance"], (15, 422, 14, 11), BALANCE_POS[0] + round((bal + 100) / 200 * 24), BALANCE_POS[1] + 1)
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
    draw_bitmap_text(img, S, state["title"][:30], 111, 24)
    draw_bitmap_text(img, S, "192", KBPS_POS[0], KBPS_POS[1])
    draw_bitmap_text(img, S, "44", KHZ_POS[0], KHZ_POS[1])
    cols = [c for c, _ in viscolor(T)]
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
            vp[x, y] = cols[min(17, max(2, y))]
        pk = heights[x // 4] + 2
        if 0 <= 16 - pk < 16:
            vp[x, 16 - pk] = cols[23]
    img.paste(vis, (VIS_POS[0], VIS_POS[1]))
    return img


def preview_eq(sheets, lit, state, key=None):
    """`key`: pledit.txt's YTMinampTransparent - drawn see-through in the slider frames and thumbs
    (eqmain.bmp x0-222, y164-292), as YTMinamp does (None: real Winamp's look)."""
    def keyed(tile, at):
        if key is None:
            img.paste(tile, at)
        else:
            mask = Image.fromarray(((np.asarray(tile) != np.array(key)).any(axis=-1) * 255).astype(np.uint8), "L")
            img.paste(tile, at, mask)

    S = sheets
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
        fr = sheet.crop((13 + (n % 14) * 15, 164 + (n // 14) * 65, 13 + (n % 14) * 15 + 14, 164 + (n // 14) * 65 + 63))
        keyed(fr, (x, 38))
        ty = 38 + round((1 - value / 100) * 51)
        sy = 176 if drag else 164
        keyed(sheet.crop((0, sy, 11, sy + 11)), (x + 1, ty))

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


def preview_playlist(T, sheets, lit, w, h, rows, pressed_close=False, drag=False):
    S = sheets
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
    c = pledit_colours(T)
    lx, lw = 12, w - 32
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=c["NormalBG"])
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("DejaVuSans.ttf", 9)
    except Exception:
        from PIL import ImageFont
        font = ImageFont.load_default()
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=c["SelectedBG"])
        col = c["Current"] if i == 1 else c["Normal"]
        d.text((lx + 2, y + 2), f"{i + 1}. {txt}", fill=col, font=font)
        d.text((lx + lw - 3 - d.textlength(dur, font=font), y + 2), dur, fill=col, font=font)
    blit(img, sheet, (61 if drag else 52, 53, 8, 18), w - 15, 20 + 30)
    draw_bitmap_text(img, S, "3:27/41:10", w - 150 + 7, h - 38 + 10)
    for dx, ch in zip([1, 7, 12, 20, 25], " 0327"):
        draw_bitmap_text(img, S, ch, w - 150 + 66 + dx, h - 38 + 23)
    return img


def gen_letters(sheets):
    g = sheets["gen"]
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


def preview_gen(sheets, lit, w, h, title, pressed_close=False):
    g = sheets["gen"]
    L = gen_letters(sheets)
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
    blit(img, g, (0, 57, 125, 14), w - rw_, by, rw_)
    pic = Image.linear_gradient("L").resize((w - 22, h - 34)).convert("RGB")
    arr = np.array(pic).astype(np.float32) / 255
    col = np.stack([40 + 90 * arr[..., 0], 36 + 70 * arr[..., 0], 60 + 120 * arr[..., 0]], -1)
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


def preview(T, sheets):
    if T["key"] == "noir":
        rows = [("HeeJin - Lace & Parasol", "4:12"), ("Umbrella - Still Rain", "3:47"),
                ("Fan Dance - Silk Static", "5:03"), ("Velvet Curtain - Reprise", "2:58"),
                ("Red Ink - Midnight", "6:21"), ("Pleats - Slow Bow", "3:33"),
                ("Lace Letter - B-side", "4:40"), ("Porcelain - Interlude", "3:09"),
                ("After Hours - Noir", "5:51"), ("Hairpin Turn", "4:05"), ("Closing Fan", "3:22")]
        title = "HEEJIN - LACE NOIR  ***"
    elif T["key"] == "parasol":
        rows = [("HeeJin - Over the Shoulder", "4:08"), ("Parasol - Open Overhead", "3:51"),
                ("Fan Dance - Silk Static", "5:03"), ("Velvet Curtain - Reprise", "2:58"),
                ("Red Ink - Midnight", "6:21"), ("Pleats - Slow Bow", "3:33"),
                ("Lace Letter - B-side", "4:40"), ("Porcelain - Interlude", "3:09"),
                ("After Hours - Noir", "5:51"), ("Hairpin Turn", "4:05"), ("Closing Fan", "3:22")]
        title = "HEEJIN - PARASOL  ***"
    elif T["key"] == "bunny":
        rows = [("HeeJin - Bunny Ears On", "3:58"), ("BMO & Finn - Backstage", "2:41"),
                ("Peace Sign - Fan Meet", "3:15"), ("Teal Knit - Candid Cut", "4:02"),
                ("Pastel Static - Interlude", "2:12"), ("Plushie Pile - B-side", "3:47"),
                ("Hood Up - Giggle Take", "3:30"), ("Backstage Blue", "4:18"),
                ("Adventure Time - Reprise", "2:55"), ("Soft Focus", "3:41"), ("Cutest Take", "4:00")]
        title = "HEEJIN - BUNNY POP  ***"
    else:
        rows = [("HeeJin - BMO & Finn", "3:44"), ("Both Hands Full - Backstage", "2:50"),
                ("Peace Sign - Fan Meet", "3:15"), ("Teal Knit - Candid Cut", "4:02"),
                ("Pastel Static - Interlude", "2:12"), ("Plushie Pile - B-side", "3:47"),
                ("Hood Up - Giggle Take", "3:30"), ("Backstage Blue", "4:18"),
                ("Adventure Time - Reprise", "2:55"), ("Soft Focus", "3:41"), ("Cutest Take", "4:00")]
        title = "HEEJIN - PLUSHIE  ***"
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=title, bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="PAUSED  ***", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    EA = dict(pressed=None, on=True, auto=False, preamp=50, drag=None,
              bands=[75, 68, 56, 49, 49, 33, 30, 30, 49, 49])
    EB = dict(pressed="close", on=False, auto=True, preamp=70, drag=3,
              bands=[51, 51, 59, 65, 65, 100, 59, 51, 0, 51])
    cols = []
    for lit, st, est in ((True, A, EA), (False, B, EB)):
        h = 116 + 116 + 232 + 140
        col = Image.new("RGB", (275, h))
        col.paste(preview_main(T, sheets, lit, st), (0, 0))
        col.paste(preview_eq(sheets, lit, est, T.get("eq_key")), (0, 116))
        col.paste(preview_playlist(T, sheets, lit, 275, 232, rows, pressed_close=not lit, drag=not lit), (0, 232))
        col.paste(preview_gen(sheets, lit, 275, 140, "album art", pressed_close=not lit), (0, 464))
        cols.append(col)
    gap = 12
    out_img = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), (60, 60, 64))
    out_img.paste(cols[0], (gap, gap))
    out_img.paste(cols[1], (275 + 2 * gap, gap))
    out_img = out_img.resize((out_img.width * 2, out_img.height * 2), Image.NEAREST)
    out_img.save(os.path.join(HERE, f"preview-{T['key']}.png"))
    if T.get("eq_key"):
        # the EQ both ways: as YTMinamp draws it (keyed) and as real Winamp/WACUP do (not)
        scratch = os.path.join(OUT_ROOT, "scratch")
        os.makedirs(scratch, exist_ok=True)
        pair = Image.new("RGB", (275 * 2 + 12 * 3, 116 + 24), (60, 60, 64))
        pair.paste(preview_eq(sheets, True, EA, T["eq_key"]), (12, 12))
        pair.paste(preview_eq(sheets, True, EA, None), (275 + 24, 12))
        pair.resize((pair.width * 2, pair.height * 2), Image.NEAREST).save(
            os.path.join(scratch, f"eq-{T['key']}-ytminamp-vs-winamp.png"))


# ------------------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------------------


def main():
    args = sys.argv[1:]
    if "--list" in args:
        for k in THEMES:
            print(k)
        return
    keys = [a for a in args if a in THEMES] or list(THEMES)
    for key in keys:
        print(f"-- {key} --")
        imgs, names = build(key)
        preview(THEMES[key], imgs)
        for n in names:
            p = os.path.join(OUT_ROOT, key, n)
            if n.endswith(".bmp"):
                im = Image.open(p)
                print(f"    {n:14s} {im.size[0]}x{im.size[1]} {im.mode}")
            else:
                print(f"    {n:14s} {os.path.getsize(p)} bytes")
        print(f"    -> {THEMES[key]['wsz']}, preview-{key}.png")


if __name__ == "__main__":
    main()
