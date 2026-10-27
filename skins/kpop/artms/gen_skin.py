#!/usr/bin/python3
"""ARTMS: personal fan skins (classic Winamp 2.x format), generated procedurally.

Forked from skins/ember/gen_skin.py (same sheets, same layouts, same preview logic). Private use
only: the ARTMS logo, the members' signatures and the objekt photos are MODHAUS's and are read at
generation time from the objekts archive, never copied into the repo.

    /usr/bin/python3 -I gen_skin.py                  # every theme
    /usr/bin/python3 -I gen_skin.py artms heejin     # just these
    /usr/bin/python3 -I gen_skin.py --list

Themes: "artms" (the group: five member colours), "<member>" (her colour as the one accent, her
signature and name), "<member>-objekt" (the member theme over her objekt photos). Each writes its
sheets into out/<theme>/, zips them flat into ARTMS[-<Name>][-Objekt].wsz and draws
preview[-<member>][-objekt].png beside this script.
"""

import os
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py, which finishes each .wsz
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# Read-only assets (outside the repo).
ATOM02 = "/home/matt/gitea/ergosteur/objekts-archive/back_templates/Atom02"
OBJEKTS = "/home/matt/gitea/ergosteur/objekts-archive/artms-objekts"

# Official COSMO colours, in member order.
MEMBERS = [
    ("heejin", "HeeJin", (0xED, 0x00, 0x90)),
    ("haseul", "HaSeul", (0x00, 0xA6, 0x52)),
    ("kimlip", "KimLip", (0xEF, 0x18, 0x41)),
    ("jinsoul", "JinSoul", (0x17, 0x24, 0xA7)),
    ("choerry", "Choerry", (0xB5, 0x10, 0xB5)),
]
MEMBER = {k: (name, col) for k, name, col in MEMBERS}
DISPLAY = {"kimlip": "Kim Lip"}  # names as written, where the file name drops the space

# Objekt fronts used by the -objekt themes: (file in objekt.<member>/, feature box (x0, y0, x1, y1)
# in the photo's own 1083x1673 pixels: from just above the eyes down to the chin, both eyes inside).
# The photo is scaled and placed so that box fills a region of the window nothing is drawn over
# (FREE_MAIN / FREE_EQ below), and the build checks it against an occupancy mask of everything
# drawn on top. Swap freely, but redraw the box for a new photo. The coloured strip on the right
# of every front (x > ~950) is cropped away.
OBJEKT_PHOTOS = {
    "heejin": {"main": ("Atom01 HeeJin 114Z.png", (290, 460, 680, 900)),
               "eq": ("Divine01 HeeJin 319Z.png", (486, 340, 826, 800))},
    "haseul": {"main": ("Atom01 HaSeul 113Z.png", (192, 300, 662, 890)),
               "eq": ("Cream01 HaSeul 352Z.png", (388, 390, 778, 910))},
    "kimlip": {"main": ("Cream01 KimLip 339Z.png", (284, 440, 674, 860)),
               "eq": ("Divine01 KimLip 204Z.png", (270, 500, 710, 990))},
    "jinsoul": {"main": ("Atom01 JinSoul 106A.png", (326, 438, 826, 1130)),
                "eq": ("Cream01 JinSoul 349A.png", (322, 488, 772, 1038))},
    "choerry": {"main": ("Cream01 Choerry 100Z.png", (278, 280, 578, 698)),
                "eq": ("Ever01 Choerry 111Z.png", (274, 528, 694, 1058))},
}

# The -objekt-light themes use other fronts, with lighter backgrounds that suit a light body.
# Same format; boxes are in each photo's own pixels (Atom02 fronts are 1942x3000).
OBJEKT_PHOTOS_LIGHT = {
    "heejin": {"main": ("Ever01 HeeJin 302Z.png", (230, 370, 700, 950)),
               "eq": ("Cream01 HeeJin 358Z.png", (360, 420, 760, 980))},
    "haseul": {"main": ("Atom01 HaSeul 204Z.png", (110, 330, 620, 950)),
               "eq": ("Atom02 HaSeul 116Z.png", (322, 803, 1290, 1756))},
    "kimlip": {"main": ("Atom01 KimLip 100Z.png", (180, 340, 560, 840)),
               "eq": ("Divine01 KimLip 101Z.png", (168, 400, 720, 990))},
    "jinsoul": {"main": ("Atom01 JinSoul 114Z.png", (150, 430, 780, 1140)),
                "eq": ("Cream01 JinSoul 334Z.png", (480, 390, 770, 660))},
    "choerry": {"main": ("Atom01 Choerry 100Z.png", (260, 390, 660, 790)),
                "eq": ("Divine01 Choerry 314Z.png", (230, 380, 640, 900))},
}

# ------------------------------------------------------------------------------------------
# Palette (fixed: the black/white base)
# ------------------------------------------------------------------------------------------

# The neutrals below are written for the dark themes; the -light themes run every neutral through
# N(), which flips its lightness (black glass -> white, white ink -> near-black) and keeps its
# slight cool cast. Member colours, photos and the white glyphs on the member-coloured buttons are
# absolute and never flipped.
LIGHT = False


def N(c):
    """A neutral colour in the current mode."""
    if not LIGHT:
        return c
    m = sum(c) / 3
    return tuple(int(round(255 - 0.9 * m + (v - m))) for v in c)


DARK_NEUTRALS = dict(
    BODY=(11, 11, 13),
    BAR=(11, 11, 13),           # titlebars: flat, so gen.bmp's letter cells match them exactly
    DISP=(0, 0, 0),
    INK=(255, 255, 255),        # white ink on the dark themes (logo, lit labels, thumbs)
    TXT=(236, 236, 238),
    RULE=(44, 44, 50),          # thin outlines round the displays and buttons
    RULE_HI=(120, 120, 128),    # titlebar rules, focused
    RULE_DIM=(48, 48, 52),      # titlebar rules, unfocused
    GREY_TXT=(128, 128, 136),
    GREY_DIM=(62, 62, 68),
    TRACK=(34, 34, 38),         # unlit slider tracks
    FACE=(20, 20, 23),          # monochrome button faces
    FACE_PR=(6, 6, 7),
    TITLE_LIT=(255, 255, 255),
    TITLE_DIM=(110, 110, 116),
)
globals().update(DARK_NEUTRALS)


def set_mode(light):
    global LIGHT
    LIGHT = light
    globals().update({k: N(v) for k, v in DARK_NEUTRALS.items()})


WHITE = (255, 255, 255)         # absolute white (glyphs on member colours, tints)
SEP = (255, 0, 255)             # gen.bmp letter separators (never shown)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    """Colour along a list of stops, t in 0..1."""
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    if n == 0:
        return stops[0]
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def lift(c):
    """A member colour made visible on black for small glyphs, rules and ramps (JinSoul's blue)."""
    return lerp(c, (110, 128, 255), 0.55) if luma(c) < 50 else c


def tint(c, t):
    return lerp(c, WHITE, t)


def shade(c, t):
    return lerp(c, (0, 0, 0), t)


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------


def make_theme(key):
    light = key.endswith("-light")
    set_mode(light)  # before the theme: its colours go through N(), which reads the mode
    base = key[:-6] if light else key
    objekt = base.endswith("-objekt")
    mk = base[:-7] if objekt else base
    t = make_light_theme(key, mk, objekt) if light else make_dark_theme(key, mk, objekt)
    t.update(light=light, photos=OBJEKT_PHOTOS_LIGHT if light else OBJEKT_PHOTOS)
    return t


def make_dark_theme(key, mk, objekt):
    if mk == "artms":
        cols = [c for _, _, c in MEMBERS]
        lit = [lift(c) for c in cols]
        return dict(
            key=key, title="ARTMS", member=None, objekt=False,
            wsz="ARTMS.wsz", preview="preview.png",
            buttons=cols, mini=cols, eject=None,
            # volume / EQ: a ramp through the five colours
            level=lit, balance=[N((150, 150, 156))] + lit,
            shuffle=lit[3], repeat=lit[2], eq=lit[1], pl=lit[4], on=lit[0], auto=lit[3],
            vis=("bands", lit), graph=lit, sel_bg=(0x2A, 0x0A, 0x3A), current=(0xFF, 0x5C, 0xBE),
            genex_sel=(0x6E, 0x0A, 0x5A), accent=lit[0],
            sigs=[k for k, _, _ in MEMBERS], name_ink=None, name_in_title=None,
            readme_who="the group", sig=lambda c: tint(lift(c), 0.15),
        )
    name, c = MEMBER[mk]
    L = lift(c)
    dark = shade(L, 0.62)
    light = tint(L, 0.55)
    return dict(
        key=key, title=f"ARTMS {name}", member=mk, objekt=objekt,
        wsz=f"ARTMS-{name}{'-Objekt' if objekt else ''}.wsz",
        preview=f"preview-{mk}{'-objekt' if objekt else ''}.png",
        buttons=[c] * 5, mini=[c] * 5, eject=None,
        level=[dark, L, light], balance=[N((150, 150, 156)), L, light],
        shuffle=L, repeat=L, eq=L, pl=L, on=L, auto=L,
        vis=("ramp", [tint(L, 0.7), light, L, shade(L, 0.25), dark]), graph=[light, L, dark],
        sel_bg=shade(c, 0.72), current=tint(L, 0.45), genex_sel=shade(c, 0.35), accent=L,
        sigs=[mk], name_ink=mk, name_in_title=DISPLAY.get(mk, name).upper(),
        readme_who=DISPLAY.get(mk, name), sig=lambda c: tint(c, 0.15),
    )


def ink_on_white(c):
    """A member colour deepened just enough to read as small text or rules on a white body."""
    return shade(c, 0.18) if luma(c) > 55 else c


def make_light_theme(key, mk, objekt):
    """The light variants: the same design inverted (see N()); member colours are used as they are
    (on white they need no lifting), deepened a little where they are small text."""
    if mk == "artms":
        cols = [c for _, _, c in MEMBERS]
        return dict(
            key=key, title="ARTMS", member=None, objekt=False,
            wsz="ARTMS-Light.wsz", preview="preview-artms-light.png",
            buttons=cols, mini=cols, eject=None,
            level=cols, balance=[N((150, 150, 156))] + cols,
            shuffle=cols[3], repeat=cols[2], eq=cols[1], pl=cols[4], on=cols[0], auto=cols[3],
            vis=("bands", cols), graph=cols, sel_bg=tint(cols[4], 0.84), current=shade(cols[0], 0.12),
            genex_sel=tint(cols[0], 0.72), accent=ink_on_white(cols[0]),
            sigs=[k for k, _, _ in MEMBERS], name_ink=None, name_in_title=None,
            readme_who="the group", sig=lambda c: c,
        )
    name, c = MEMBER[mk]
    return dict(
        key=key, title=f"ARTMS {name}", member=mk, objekt=objekt,
        wsz=f"ARTMS-{name}{'-Objekt' if objekt else ''}-Light.wsz",
        preview=f"preview-{key}.png",
        buttons=[c] * 5, mini=[c] * 5, eject=None,
        level=[tint(c, 0.6), c, shade(c, 0.4)], balance=[N((150, 150, 156)), tint(c, 0.35), c],
        shuffle=c, repeat=c, eq=c, pl=c, on=c, auto=c,
        vis=("ramp", [shade(c, 0.35), c, tint(c, 0.3), tint(c, 0.55), tint(c, 0.72)]),
        graph=[shade(c, 0.3), c, tint(c, 0.45)],
        sel_bg=tint(c, 0.82), current=shade(c, 0.25), genex_sel=tint(c, 0.7), accent=ink_on_white(c),
        sigs=[mk], name_ink=mk, name_in_title=DISPLAY.get(mk, name).upper(),
        readme_who=DISPLAY.get(mk, name), sig=lambda c: c,
    )


THEME_KEYS = ["artms"] + [k for k, _, _ in MEMBERS] + [f"{k}-objekt" for k, _, _ in MEMBERS]
THEME_KEYS += [f"{k}-light" for k in THEME_KEYS]
T = None  # the theme being built
OUT = None

# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def new(w, h, col=None):
    col = BODY if col is None else col
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


def grain(a, x, y, w, h, amp=1.2, seed=1729):
    """A very fine, even noise: just enough to keep the black from looking flat."""
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w))
    n = (n + np.roll(n, 1, axis=1) * 0.5) / 1.2
    a[y:y + h, x:x + w] += np.round(n * amp).astype(np.int32)[:, :, None]


def body(a, x, y, w, h, col=None, amp=1.2, seed=1729):
    col = BODY if col is None else col
    rect(a, x, y, w, h, col)
    grain(a, x, y, w, h, amp, seed)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def composite(a, x, y, alpha, col, opacity=1.0):
    """Blends a solid colour into a at (x, y) through an alpha mask (float 0..1, H x W)."""
    h, w = alpha.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(a.shape[1], x + w), min(a.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    al = alpha[y0 - y:y1 - y, x0 - x:x1 - x, None] * opacity
    dst = a[y0:y1, x0:x1].astype(np.float64)
    a[y0:y1, x0:x1] = np.round(dst * (1 - al) + np.array(col, dtype=np.float64) * al).astype(np.int32)


# ------------------------------------------------------------------------------------------
# Ink from the Atom02 templates: the ARTMS logo, the members' signatures and names
# ------------------------------------------------------------------------------------------

_ink_cache = {}


def _ink(path):
    if path not in _ink_cache:
        _ink_cache[path] = np.asarray(Image.open(path).convert("RGBA"))[..., 3].astype(np.float64) / 255
    return _ink_cache[path]


def _bbox(a, thr=0.4, min_count=4):
    m = a > thr
    rows = np.nonzero(m.sum(1) >= min_count)[0]
    cols = np.nonzero(m.sum(0) >= min_count)[0]
    return cols.min(), rows.min(), cols.max() + 1, rows.max() + 1


def _shrink(crop, h, stroke=0.0, gamma=1.0, w=None):
    """Downscales an ink crop to h rows (keeping its aspect unless w is given). stroke > 0 thickens
    hairlines first (a max filter at 4x the target size), so thin signature lines survive."""
    ch, cw = crop.shape
    if w is None:
        w = max(1, round(cw * h / ch))
    img = Image.fromarray(np.round(crop * 255).astype(np.uint8), "L")
    if stroke:
        mid = img.resize((w * 4, h * 4), Image.BOX)
        arr = np.asarray(mid).astype(np.float64)
        arr = np.clip(arr / max(1.0, np.percentile(arr[arr > 0], 97) if (arr > 0).any() else 1), 0, 1)
        mid = Image.fromarray(np.round(arr * 255).astype(np.uint8), "L")
        if stroke > 1:
            mid = mid.filter(ImageFilter.MaxFilter(3))
        img = mid.resize((w, h), Image.LANCZOS)
    else:
        img = img.resize((w, h), Image.LANCZOS)
    out = np.clip(np.asarray(img).astype(np.float64) / 255, 0, 1)
    return np.clip(out ** gamma, 0, 1)


def logo_alpha(h):
    """The horizontal ARTMS wordmark (top left of the template), h rows tall."""
    a = _ink(os.path.join(ATOM02, "white", "template-ink-white.png"))
    top = a[:600, :1000]
    x0, y0, x1, y1 = _bbox(top, 0.5, 1)
    crop = top[y0:y1, x0:x1]
    al = _shrink(crop, h)
    # firm the edges up: a small contrast stretch keeps the letters crisp at sprite size
    return np.clip((al - 0.12) / 0.72, 0, 1)


def signature_alpha(member, h):
    a = _ink(os.path.join(ATOM02, "white", f"stamp-{member}-white.png"))
    band = a[1650:2500]
    x0, y0, x1, y1 = _bbox(band, 0.4, 4)
    return _shrink(band[y0:y1, x0:x1], h, stroke=1, gamma=0.55)


def name_alpha(member, h):
    a = _ink(os.path.join(ATOM02, "white", f"stamp-{member}-white.png"))
    band = a[760:1040, :1300]
    x0, y0, x1, y1 = _bbox(band, 0.5, 2)
    al = _shrink(band[y0:y1, x0:x1], h)
    return np.clip((al - 0.1) / 0.75, 0, 1)


# ------------------------------------------------------------------------------------------
# Objekt photos (the -objekt themes)
# ------------------------------------------------------------------------------------------


def photo_layer(member, which, free, size):
    """The photo scaled and placed so its feature box (eyes to chin) fits inside the window rect
    `free` (x, y, w, h), centred, on a canvas of `size`. Returns (rgb float HxWx3, coverage float
    HxW: 1 inside the photo, fading at its edges, the feature box in window pixels (x0, y0, x1, y1))."""
    fn, (bx0, by0, bx1, by1) = T["photos"][member][which]
    im = Image.open(os.path.join(OBJEKTS, f"objekt.{member}", fn)).convert("RGB")
    im = im.crop((0, 0, round(im.width * 950 / 1083), im.height))  # drop the card's coloured name strip
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
    # feathered edges so the photo melts into the body
    feather = max(3, round(min(sw, sh) * 0.12))
    yy, xx = np.mgrid[0:sh, 0:sw]
    edge = np.minimum.reduce([xx, yy, sw - 1 - xx, sh - 1 - yy]).astype(np.float64)
    fe = np.clip(edge / feather, 0, 1)
    x0, y0 = max(0, ox), max(0, oy)
    x1, y1 = min(W, ox + sw), min(H, oy + sh)
    global PHOTO_EDGE
    PHOTO_EDGE = np.zeros((H, W))  # distance (px) to the photo's own edge, for wider fades
    if x1 > x0 and y1 > y0:
        rgb[y0:y1, x0:x1] = src[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
        cov[y0:y1, x0:x1] = fe[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
        PHOTO_EDGE[y0:y1, x0:x1] = edge[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return rgb, cov, feat


def occupancy(rects, size):
    """1 wherever something is drawn over the window background (the window's own 1px outline too)."""
    W, H = size
    m = np.zeros((H, W), dtype=bool)
    for x, y, w, h in rects:
        m[max(0, y):y + h, max(0, x):x + w] = True
    m[0, :] = m[-1, :] = True
    m[:, 0] = m[:, -1] = True
    return m


def check_features(where, feat, occ, cov):
    """Prints (and asserts) how many pixels of the placed feature box anything is drawn over, and
    that the box is clear of the photo's own feathered edge."""
    x0, y0, x1, y1 = feat
    H, W = occ.shape
    inside = 0 <= x0 and 0 <= y0 and x1 <= W and y1 <= H
    n = int(occ[max(0, y0):y1, max(0, x0):x1].sum())
    edge = float(cov[max(0, y0):y1, max(0, x0):x1].min())
    print(f"    {T['key']:21s} {where:4s} {T['photos'][T['member']][where][0]:28s} features "
          f"x{x0}-{x1} y{y0}-{y1} ({x1 - x0}x{y1 - y0}): {n} px overlapped")
    assert inside and n == 0, f"{T['key']} {where}: the face's features are under drawn elements"
    assert edge > 0.99, f"{T['key']} {where}: the face runs into the photo's feathered edge ({edge:.2f})"


def soft_rect(r, size, soft):
    """1 inside r (x, y, w, h), falling to 0 over `soft` px inside its edges."""
    x, y, w, h = r
    W, H = size
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.minimum.reduce([xx - x + 1, yy - y + 1, x + w - xx, y + h - yy]).astype(np.float64)
    return np.clip(d / soft, 0, 1)


def wash(rgb, ctrl, amount=0.6):
    """Desaturates the photo where controls sit (ctrl 1), so what shows through them stays quiet."""
    grey = rgb.mean(axis=2, keepdims=True)
    k = (ctrl * amount)[..., None]
    return rgb * (1 - k) + grey * k


def lay_photo(a, rgb, weight):
    """Blends the photo into the body: weight (HxW, 0..1) is how much of the photo shows."""
    w = weight[..., None]
    a[:] = np.round(a * (1 - w) + rgb * w).astype(np.int32)


# ------------------------------------------------------------------------------------------
# Pixel fonts (Ember's, a few glyphs redrawn for a plainer, Helvetica-like caps)
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
    "M": G("#..#", "####", "#..#", "#..#", "#..#"),
    "N": G("#..#", "##.#", "#.##", "#..#", "#..#"),
    "O": G(".##.", "#..#", "#..#", "#..#", ".##."),
    "P": G("###.", "#..#", "###.", "#...", "#..."),
    "Q": G(".##.", "#..#", "#..#", "#.#.", ".#.#"),
    "R": G("###.", "#..#", "###.", "#.#.", "#..#"),
    "S": G(".###", "#...", ".##.", "...#", "###."),
    "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#..#", "#..#", "#..#", "#..#", ".##."),
    "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#..#", "#..#", "#..#", "####", "#..#"),
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

# 7x11 thin digits for numbers.bmp (a plain grotesque, not segments).
DIGITS = {
    0: G("..###..", ".#...#.", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#",
         "#.....#", ".#...#.", "..###.."),
    1: G("...#...", "..##...", ".#.#...", "...#...", "...#...", "...#...", "...#...", "...#...",
         "...#...", "...#...", "...#..."),
    2: G("..###..", ".#...#.", "#.....#", "......#", ".....#.", "....#..", "...#...", "..#....",
         ".#.....", "#......", "#######"),
    3: G("..###..", ".#...#.", "......#", "......#", ".....#.", "...##..", ".....#.", "......#",
         "#.....#", ".#...#.", "..###.."),
    4: G(".....#.", "....##.", "...#.#.", "..#..#.", ".#...#.", "#....#.", "#######", ".....#.",
         ".....#.", ".....#.", ".....#."),
    5: G("#######", "#......", "#......", "#.###..", "##...#.", "......#", "......#", "......#",
         "#.....#", ".#...#.", "..###.."),
    6: G("..###..", ".#...#.", "#......", "#......", "#.###..", "##...#.", "#.....#", "#.....#",
         "#.....#", ".#...#.", "..###.."),
    7: G("#######", "......#", ".....#.", ".....#.", "....#..", "....#..", "...#...", "...#...",
         "..#....", "..#....", "..#...."),
    8: G("..###..", ".#...#.", "#.....#", ".#...#.", "..###..", ".#...#.", "#.....#", "#.....#",
         "#.....#", ".#...#.", "..###.."),
    9: G("..###..", ".#...#.", "#.....#", "#.....#", "#.....#", ".#...##", "..###.#", "......#",
         "......#", ".#...#.", "..###.."),
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
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    if shadow is not None:
                        px(a, x + k + 1, y + r + 1, shadow)
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col(r) if callable(col) else col)
        x += len(g[0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1, shadow=None):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow)


def draw_digit(a, n, x, y, col):
    """A 7x11 digit with its stair-steps softened (half-tone pixels in the inner corners)."""
    g = DIGITS[n]
    for r, row in enumerate(g):
        for k, ch in enumerate(row):
            if ch == "#":
                px(a, x + k, y + r, col)
    soft = lerp(DISP, col, 0.35)
    for r in range(len(g) - 1):
        for k in range(len(g[0]) - 1):
            q = (g[r][k], g[r][k + 1], g[r + 1][k], g[r + 1][k + 1])
            if q in (("#", ".", ".", "#"), (".", "#", "#", ".")):
                for dk, dr in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    if g[r + dr][k + dk] == ".":
                        px(a, x + k + dk, y + r + dr, soft)


# ------------------------------------------------------------------------------------------
# Shared pieces
# ------------------------------------------------------------------------------------------


def hrule(a, x, y, w, lit):
    rect(a, x, y, w, 1, RULE_HI if lit else RULE_DIM)




def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button: flat, outlined; pressed inverts to white."""
    face = N((228, 228, 232)) if pressed else BAR
    rect(a, x, y, 9, 9, face)
    outline(a, x, y, 9, 9, N((200, 200, 206)) if pressed else (N((92, 92, 100)) if lit else N((52, 52, 58))))
    ink = N((10, 10, 12)) if pressed else (N((236, 236, 240)) if lit else N((110, 110, 116)))
    X, Y = x, y
    if kind == "options":
        rect(a, X + 3, Y + 3, 3, 3, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 6, 5, 1, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 1, ink)
        rect(a, X + 2, Y + 4, 5, 1, lerp(ink, face, 0.5))
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


def flat_button(a, x, y, w, h, pressed, face=None, edge=None):
    face = FACE if face is None else face
    edge = RULE if edge is None else edge
    rect(a, x, y, w, h, FACE_PR if pressed else face)
    outline(a, x, y, w, h, lerp(edge, (0, 0, 0), 0.3) if pressed else edge)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, DISP)
    outline(a, 0, 0, 8, 43, RULE)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, INK if on else N((84, 84, 90)))
    return a


LOGO_H = 9


def main_titlebar(lit):
    a = new(275, 14, BAR)
    outline(a, 0, 0, 275, 14, N((30, 30, 34)))
    logo = logo_alpha(LOGO_H)
    lw = logo.shape[1]
    name = T["name_in_title"]
    if name:
        nw = text_w(FONT5, name)
        total = lw + 9 + nw
    else:
        total = lw
    lx = (275 - total) // 2
    # thin rules either side of the mark, clear of the buttons
    hrule(a, 18, 7, lx - 6 - 18, lit)
    hrule(a, lx + total + 6, 7, 241 - (lx + total + 6), lit)
    composite(a, lx, 3, logo, INK if lit else N((108, 108, 114)))
    if name:
        sx = lx + lw + 4
        rect(a, sx, 3, 1, 9, RULE_HI if lit else RULE_DIM)
        draw_text(a, FONT5, name, sx + 5, 5, T["accent"] if lit else N((96, 96, 102)))
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, BAR)
    for kind, x, y, py_ in [("options", 0, 0, 9), ("minimize", 9, 0, 9), ("close", 18, 0, 9)]:
        b = new(9, 9)
        mini_button(b, 0, 0, kind, True)
        a[y:y + 9, x:x + 9] = b
        mini_button(b, 0, 0, kind, True, pressed=True)
        a[py_:py_ + 9, x:x + 9] = b
    b = new(9, 9)
    mini_button(b, 0, 0, "shade", True)
    a[18:27, 0:9] = b
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


def display_box(a, x, y, w, h):
    """A display window: pure black glass with a thin grey rule round it."""
    rect(a, x, y, w, h, DISP)
    outline(a, x - 1, y - 1, w + 2, h + 2, RULE)


def member_dots(a, x, y, lit=True):
    """The About spot: five small squares in the member colours (or hers alone)."""
    cols = [lift(c) for _, _, c in MEMBERS] if T["member"] is None else [T["accent"]] * 5
    for i, c in enumerate(cols):
        rect(a, x + i * 5, y, 3, 3, c if lit else GREY_DIM)


# Where every drawn element sits on the main window (x, y, w, h): photo weight drops under these.
MAIN_CONTROLS = [
    (0, 0, 275, 14), (10, 22, 8, 43), (20, 19, 86, 44), (108, 20, 161, 17), (108, 39, 161, 16),
    (107, 57, 68, 13), (177, 57, 38, 13), (219, 58, 46, 12), (16, 72, 248, 10), (16, 88, 114, 18),
    (136, 89, 22, 16), (164, 89, 75, 15),
]

BOTTOM_Y, BOTTOM_H = 107, 8   # the free strip under the transport buttons

# The bottom-right corner (right of repeat, under the seek bar, inside the window's edge): the only
# free area of main.bmp big enough for a face. The -objekt themes draw no emblem there.
FREE_MAIN = (241, 85, 32, 29)


def main_decoration(a):
    """Signatures (and, for a member, her name) in the free strip under the transport buttons."""
    if T["member"] is None:
        # one signature under each member's button, in her colour
        for i, (k, _, c) in enumerate(MEMBERS):
            al = signature_alpha(k, BOTTOM_H)
            if al.shape[1] > 21:
                al = _shrink_w(al, 21)
            bx = 16 + 23 * i + (23 - al.shape[1]) // 2
            composite(a, bx, BOTTOM_Y, al, T["sig"](c), 0.65)
    else:
        k = T["member"]
        nm = name_alpha(k, 7)
        composite(a, 18, BOTTOM_Y, nm, INK, 0.9)
        al = signature_alpha(k, BOTTOM_H)
        composite(a, 18 + nm.shape[1] + 6, BOTTOM_Y, al, T["sig"](T["accent"]), 0.7)


def _shrink_w(al, w):
    h = max(1, round(al.shape[0] * w / al.shape[1]))
    img = Image.fromarray(np.round(al * 255).astype(np.uint8), "L").resize((w, h), Image.LANCZOS)
    out = np.zeros((al.shape[0], w))
    out[(al.shape[0] - h) // 2:(al.shape[0] - h) // 2 + h] = np.asarray(img) / 255
    return out


def control_mask(rects, size, pad=2, soft=5):
    """1 on the controls (grown by pad), falling to 0 over `soft` px around them."""
    W, H = size
    m = np.zeros((H, W))
    for x, y, w, h in rects:
        m[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad] = 1
    img = Image.fromarray(np.round(m * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(soft / 2))
    return np.maximum(m, np.asarray(img) / 255)


def make_main():
    a = new(275, 116, BODY)
    body(a, 0, 0, 275, 116)
    if T["objekt"]:
        main_photo(a)
    outline(a, 0, 0, 275, 116, N((30, 30, 34)))
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # left display: indicator, time, analyzer
    display_box(a, 21, 20, 84, 42)
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, N((220, 220, 224)))
    # right display: title row, then kbps/kHz/mono/stereo row
    display_box(a, 109, 21, 159, 15)
    display_box(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, GREY_TXT)
    draw_text(a, TINY, "KHZ", 169, 44, GREY_TXT)

    if not T["objekt"]:
        main_decoration(a)
        member_dots(a, 248, 97)
    else:
        main_decoration(a)
    return a


def main_photo(a):
    """The member's objekt photo: her face in the free bottom-right corner, the rest dark under the
    controls."""
    rgb, cov, feat = photo_layer(T["member"], "main", FREE_MAIN, (275, 116))
    drawn = MAIN_CONTROLS + [(16, BOTTOM_Y, 120, BOTTOM_H)]
    check_features("main", feat, occupancy(drawn, (275, 116)), cov)
    ctrl = control_mask(drawn, (275, 116), pad=1, soft=6)
    # strongest in the corner, a dim glow elsewhere
    yy, xx = np.mgrid[0:116, 0:275]
    fx, fy, fw, fh = FREE_MAIN
    d = np.hypot((xx - (fx + fw / 2)) / 1.3, yy - (fy + fh / 2))
    focus = np.clip(1.25 - d / 40, 0.22, 1.0)
    weight = cov * focus * (1 - 0.85 * ctrl)
    if LIGHT:
        # on the light body: a backdrop round her face that washes out into the body over a wide
        # gradient; under the controls it is washed (lightened, desaturated) further
        cx, cy = (feat[0] + feat[2]) / 2, (feat[1] + feat[3]) / 2
        d = np.hypot((xx - cx) / 1.2, yy - cy)
        weight = cov * np.clip(1 - np.maximum(0, d - 14) / 30, 0, 1) ** 1.3 * (1 - 0.8 * ctrl)
        weight *= np.clip(PHOTO_EDGE / 10, 0, 1)  # no hard photo edge
        rgb = wash(rgb, ctrl)
    rgb = rgb * 0.92 + np.array(T["accent"]) * 0.04  # a faint tone toward her colour
    lay_photo(a, rgb, np.clip(weight, 0, 1))


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36)
# ------------------------------------------------------------------------------------------


def colour_button(a, x, y, w, h, col, pressed):
    face = shade(col, 0.38) if pressed else col
    rect(a, x, y, w, h, face)
    if not pressed:
        rect(a, x, y, w, 1, tint(col, 0.28))
    rect(a, x + w - 1, y, 1, h, shade(col, 0.6))
    rect(a, x, y + h - 1, w, 1, shade(col, 0.6))


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


def transport_icon(a, kind, x, y, w, h, pressed, ink):
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


def make_cbuttons():
    a = new(136, 36, BODY)
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18)]
    for (kind, x, w, h), col in zip(specs, T["buttons"]):
        for pressed, y in ((False, 0), (True, 18)):
            colour_button(a, x, y, w, h, col, pressed)
            transport_icon(a, kind, x, y, w, h, pressed, WHITE if not pressed else (225, 225, 230))
    for pressed, y in ((False, 0), (True, 16)):
        face = N((150, 150, 156)) if pressed else N((228, 228, 232))
        rect(a, 114, y, 22, 16, face)
        rect(a, 135, y, 1, 16, N((110, 110, 116)))
        rect(a, 114, y + 15, 22, 1, N((110, 110, 116)))
        transport_icon(a, "eject", 114, y, 22, 16, pressed, N((12, 12, 14)))
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle(a, x, y, w, h, label, on, pressed, col, led="under"):
    flat_button(a, x, y, w, h, pressed)
    o = 1 if pressed else 0
    ink = INK if on else (N((150, 150, 156)) if pressed else N((120, 120, 128)))
    tw = text_w(TINY, label)
    if led == "under":
        draw_text(a, TINY, label, x + (w - tw) // 2 + o, y + 3 + o, ink)
        rect(a, x + 4 + o, y + h - 4 + o, w - 9, 1, col if on else N((34, 34, 38)))
    else:  # a small light at the left
        draw_text(a, TINY, label, x + 7 + (w - 9 - tw) // 2 + o, y + (h - 5) // 2 + o, ink)
        rect(a, x + 3 + o, y + h // 2 - 1 + o, 2, 2, col if on else N((40, 40, 44)))


def make_shufrep():
    a = new(92, 85, BODY)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        toggle(a, 0, y, 28, 15, "REPEAT", on, pressed, T["repeat"])
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed, T["shuffle"])
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        col = T["eq"] if label == "EQ" else T["pl"]
        toggle(a, x, 61, 23, 12, label, False, pressed, col, led="dot")
        toggle(a, x, 73, 23, 12, label, True, pressed, col, led="dot")
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, DISP)
    for y, on in ((0, True), (12, False)):
        col = INK if on else N((52, 52, 58))
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, DISP)
    tri_right(a, 2, 1, 7, INK)                      # playing
    rect(a, 9 + 2, 1, 2, 7, INK)                    # paused
    rect(a, 9 + 5, 1, 2, 7, INK)
    rect(a, 18 + 2, 2, 5, 5, INK)                   # stopped
    rect(a, 36, 0, 3, 9, DISP)                        # not working
    rect(a, 39 + 1, 3, 1, 3, T["accent"])             # working
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, DISP)
    for n in range(10):
        draw_digit(a, n, 9 * n + 1, 1, TXT)
    if ex:
        rect(a, 99 + 2, 6, 5, 1, TXT)                 # minus
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
            draw_text(a, FONT5, key, col * 5, row * 6, TXT)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def pill(a, x, y, w, h, col, edge=None):
    rect(a, x, y, w, h, col)
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        a[cy, cx] = lerp(col, a[cy, cx] if edge is None else edge, 0.6)


def make_posbar(main):
    a = new(307, 10, BODY)
    a[0:10, 0:248] = main[72:82, 16:264]
    rect(a, 0, 4, 248, 2, TRACK)
    # thumbs: a white pill on the track's own background
    for x, sel in ((248, False), (278, True)):
        a[0:10, x:x + 29] = a[0:10, 100:129]
        pill(a, x + 5, 2, 19, 6, N((200, 200, 206)) if sel else INK)
    return a


def slider_thumbs(a):
    for x, sel in ((0, True), (15, False)):
        rect(a, x, 422, 14, 11, BODY)
        pill(a, x + 4, 422, 6, 11, N((200, 200, 206)) if sel else INK)


def make_volume(main):
    a = new(68, 433, BODY)
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        level = (i + 1) / 28
        fill_to = 7 + round(level * 54)
        colour = ramp(T["level"], i / 27)
        rect(a, 3, y + 5, 62, 3, TRACK)
        rect(a, 3, y + 5, fill_to - 3, 3, colour)
    slider_thumbs(a)
    return a


def make_balance(main):
    a = new(68, 433, BODY)
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        t = i / 27
        colour = ramp(T["balance"], t)
        reach = round(16 * t)
        rect(a, 11, y + 5, 34, 3, TRACK)
        rect(a, 28 - max(1, reach), y + 5, 2 * max(1, reach) + 1, 3, colour)
        rect(a, 28, y + 2, 1, 2, N((200, 200, 206)))
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def titled_bar(w, title, lit, close_x):
    """A 14px titlebar: caps title centred between thin rules."""
    a = new(w, 14, BAR)
    outline(a, 0, 0, w, 14, N((30, 30, 34)))
    tw = text_w(FONT5, title)
    tx = (w - tw) // 2
    hrule(a, 6, 7, tx - 6 - 6, lit)
    hrule(a, tx + tw + 6, 7, close_x - 4 - (tx + tw + 6), lit)
    draw_text(a, FONT5, title, tx, 5, TITLE_LIT if lit else TITLE_DIM)
    mini_button(a, close_x, 3, "close", lit)
    return a


def eq_title():
    return "EQUALIZER" if T["member"] is None else f"{T['name_in_title']} EQUALIZER"


def eq_slider_frame(a, x, y, n, bg=None):
    """14x63 slot: a thin track whose fill rises with the value (n of 0..27)."""
    if bg is not None:
        a[y:y + 63, x:x + 14] = bg
    else:
        rect(a, x, y, 14, 63, BODY)
    v = n / 27
    centre = round((1 - v) * 51) + 5
    colour = ramp(T["level"], v)
    rect(a, x + 6, y + 3, 2, 57, TRACK)
    rect(a, x + 6, y + centre, 2, 60 - centre, colour)
    rect(a, x + 1, y + 30, 2, 1, N((80, 80, 86)))
    rect(a, x + 11, y + 30, 2, 1, N((80, 80, 86)))


EQ_CONTROLS = [(0, 0, 275, 14), (14, 18, 58, 12), (85, 16, 115, 21), (217, 18, 44, 12),
               (21, 38, 14, 63), (78, 38, 176, 63)]
# Also drawn over the EQ: the dB labels (left out of the -objekt themes) and the band labels row.
EQ_DB_LABELS = [(48, 41, 21, 5), (50, 66, 17, 5), (48, 92, 21, 5)]
EQ_BAND_LABELS = (0, 105, 275, 7)
# Between the preamp slider (x 21..34) and the 60 Hz band (x 78..), under ON/AUTO (to y 29) and
# above the band labels (y 105): free once the dB labels are gone.
FREE_EQ = (37, 33, 39, 70)


def make_eqmain():
    a = new(275, 315, BODY)
    body(a, 0, 0, 275, 315, seed=4242)
    if T["objekt"]:
        rgb, cov, feat = photo_layer(T["member"], "eq", FREE_EQ, (275, 116))
        check_features("eq", feat, occupancy(EQ_CONTROLS + [EQ_BAND_LABELS], (275, 116)), cov)
        yy, xx = np.mgrid[0:116, 0:275]
        fx, fy, fw, fh = FREE_EQ
        # full strength in the free column, falling off under the sliders
        dx = np.maximum(0, np.abs(xx - (fx + fw / 2)) - fw / 2)
        fade = np.clip(1.0 - dx / 40, 0.25, 1.0)
        weight = cov * fade * 0.8
        ctrl = control_mask(EQ_CONTROLS, (275, 116), pad=0, soft=3)
        weight = weight * (1 - 0.6 * ctrl)
        if LIGHT:
            # on the light body: strongest round her face in the free column, washing out into the
            # body over a wide gradient and paler under the controls
            out_x = np.maximum(0, np.abs(xx - (fx + fw / 2)) - fw / 2)
            out_y = np.maximum(0, np.abs(yy - (fy + fh / 2)) - fh / 2)
            d = np.hypot(out_x, out_y)
            ctrl = control_mask(EQ_CONTROLS + [EQ_BAND_LABELS], (275, 116), pad=0, soft=3)
            weight = cov * np.clip(1 - d / 34, 0, 1) ** 1.3 * (1 - 0.75 * ctrl) * 0.95
            weight *= np.clip(PHOTO_EDGE / 14, 0, 1)  # no hard photo edge
            rgb = wash(rgb, ctrl)
        top = a[0:116].copy()
        lay_photo(top, rgb, weight)
        a[0:116] = top
    outline(a, 0, 0, 275, 116, N((30, 30, 34)))
    a[0:14, :] = titled_bar(275, eq_title(), True, 264)
    outline(a, 85, 16, 115, 21, RULE)
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        if not T["objekt"]:  # the -objekt themes keep this column for her face
            text_center(a, TINY, lbl, 58, yy, GREY_TXT)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14, bg=a[38:101, x:x + 14].copy())
    text_center(a, TINY, "PREAMP", 28, 106, N((150, 150, 156)), shadow=N((0, 0, 0)) if T["objekt"] else None)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, N((150, 150, 156)))

    # under the window: buttons
    mini_button(a, 0, 125, "close", True, pressed=True)
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        toggle(a, x, 119, w, 12, label, on, pressed, T["on"] if label == "ON" else T["auto"], led="dot")
    a[134:148, :] = titled_bar(275, eq_title(), True, 264)
    a[149:163, :] = titled_bar(275, eq_title(), False, 264)
    for y, sel in ((164, False), (176, True)):
        rect(a, 0, y, 11, 11, BODY)
        pill(a, 0, y + 3, 11, 5, N((200, 200, 206)) if sel else INK)
    # the 28 frames (the app takes the band's background from these, not from the window)
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        flat_button(a, 224, y, 44, 12, pressed)
        o = 1 if pressed else 0
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 3 + o, INK if pressed else N((180, 180, 186)))
    # graph
    rect(a, 0, 294, 113, 19, DISP)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, N((30, 30, 34)))
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, N((44, 44, 48)))
    for r in range(19):
        px(a, 115, 294 + r, ramp(T["graph"], r / 18))
    for x in range(113):
        px(a, x, 314, N((120, 120, 126)) if x % 3 != 2 else DISP)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

RULE_Y = 7          # the titlebars' rule row (20px bars), through the middle of the title
TITLE_Y = 5         # FONT5 glyph top in 20px bars, level with gen.bmp's letters (5..9)


def bar20(w, lit, rule=True, x0=0, x1=None):
    a = new(w, 20, BAR)
    rect(a, 0, 0, w, 1, N((30, 30, 34)))
    if rule:
        hrule(a, x0, RULE_Y, (w if x1 is None else x1) - x0, lit)
    return a


def pl_title():
    return "PLAYLIST" if T["member"] is None else f"{T['name_in_title']} PLAYLIST"


def make_pledit():
    a = new(280, 186, BODY)
    body(a, 0, 0, 280, 186, seed=99)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit)
        a[y:y + 20, 127:152] = t
        t = bar20(25, lit, x0=6)
        rect(t, 0, 0, 1, 20, N((30, 30, 34)))
        a[y:y + 20, 0:25] = t
        # title (100 wide, centred)
        t = bar20(100, lit, rule=False)
        title = pl_title()
        tw = text_w(FONT5, title)
        hrule(t, 0, RULE_Y, (100 - tw) // 2 - 5, lit)
        hrule(t, (100 + tw) // 2 + 5, RULE_Y, 100 - ((100 + tw) // 2 + 5), lit)
        text_center(t, FONT5, title, 50, TITLE_Y, TITLE_LIT if lit else TITLE_DIM)
        a[y:y + 20, 26:126] = t
        # top-right: close button
        t = bar20(25, lit, x1=11)
        rect(t, 24, 0, 1, 20, N((30, 30, 34)))
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    # left side tile
    t = new(12, 29)
    body(t, 0, 0, 12, 29, amp=0)
    rect(t, 0, 0, 1, 29, N((30, 30, 34)))
    rect(t, 11, 0, 1, 29, RULE)
    a[42:71, 0:12] = t
    # right side tile: list edge, scrollbar groove, outer edge
    t = new(20, 29)
    body(t, 0, 0, 20, 29, amp=0)
    rect(t, 0, 0, 1, 29, RULE)
    rect(t, 19, 0, 1, 29, N((30, 30, 34)))
    rect(t, 8, 0, 2, 29, N((26, 26, 30)))
    a[42:71, 31:51] = t
    # close pressed, scroll handles (on the groove's colours)
    t = new(9, 9, BAR)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        rect(a, x, 53, 8, 18, BODY)
        pill(a, x + 1, 53, 6, 18, N((200, 200, 206)) if sel else INK)

    def bottom_base(w):
        t = new(w, 38)
        body(t, 0, 0, w, 38, amp=0)
        rect(t, 0, 0, w, 1, RULE)
        rect(t, 0, 37, w, 1, N((30, 30, 34)))
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, N((30, 30, 34)))
    rect(t, 0, 0, 12, 1, BODY)
    rect(t, 11, 0, 1, 1, RULE)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        flat_button(t, bx, 8, 22, 18, False)
        text_center(t, TINY, lbl, bx + 11, 15, N((200, 200, 206)))
    if T["member"] is not None:
        # her signature, small, in the strip under the buttons
        al = signature_alpha(T["member"], 8)
        composite(t, 14, 28, al, T["sig"](T["accent"]), 0.6)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, N((30, 30, 34)))
    rect(t, 130, 0, 20, 1, BODY)
    rect(t, 130, 0, 1, 1, RULE)
    display_box(t, 6, 9, 56, 8)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        if k < 5:
            colour_button(t, bx, 22, 10, 10, T["mini"][k], False)
            mini_transport_icon(t, kind, bx, 22, WHITE)
        else:
            rect(t, bx, 22, 10, 10, N((228, 228, 232)))
            mini_transport_icon(t, kind, bx, 22, N((12, 12, 14)))
    display_box(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, GREY_TXT)
    rect(t, 84, 22 + 5, 1, 1, GREY_TXT)
    flat_button(t, 106, 8, 22, 18, False)
    text_center(t, TINY, "LIST", 117, 15, N((200, 200, 206)))
    for k in range(4):
        for j in range(k + 1):
            px(t, 145 - 3 * k + 3 * j, 29 - 3 * j, N((150, 150, 156)))
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


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


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GEN_RULE_Y = 7      # gen titles sit at y 4..10 (letters 5..9), so its rule runs through their middle


def make_gen():
    a = new(194, 109, BODY)
    body(a, 0, 0, 194, 109, seed=7)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, x0=None, x1=None, close=False, left_edge=False, right_edge=False):
            t = new(25, 20, BAR)
            rect(t, 0, 0, 25, 1, N((30, 30, 34)))
            if x0 is not None:
                hrule(t, x0, GEN_RULE_Y, x1 - x0, lit)
            if left_edge:
                rect(t, 0, 0, 1, 20, N((30, 30, 34)))
            if right_edge:
                rect(t, 24, 0, 1, 20, N((30, 30, 34)))
            if close:
                mini_button(t, 14, 3, "close", lit)
            a[y:y + 20, px0:px0 + 25] = t

        piece(0, 6, 25, left_edge=True)       # left
        piece(26, 0, 19)                       # left end: the rule stops before the title
        piece(52)                              # centre: plain, under the letters
        piece(78, 6, 25)                       # right end
        piece(104, 0, 25)                      # fill
        piece(130, 0, 11, close=True, right_edge=True)

    def bottom(w, grip, left_edge):
        t = new(w, 14)
        body(t, 0, 0, w, 14, amp=0)
        rect(t, 0, 13, w, 1, N((30, 30, 34)))
        if left_edge:
            rect(t, 0, 0, 1, 14, N((30, 30, 34)))
        else:
            rect(t, w - 1, 0, 1, 14, N((30, 30, 34)))
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    px(t, w - 4 - 3 * k + 3 * j, 9 - 3 * j, N((150, 150, 156)))
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        body(t, 0, 0, w, h, amp=0)
        if outer_left:
            rect(t, 0, 0, 1, h, N((30, 30, 34)))
            rect(t, w - 1, 0, 1, h, RULE)
        else:
            rect(t, w - 1, 0, 1, h, N((30, 30, 34)))
            rect(t, 0, 0, 1, h, RULE)
        a[42:42 + h, x:x + w] = t
    t = new(9, 9, BAR)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: each row starts at x 1, letters in their own cells, 1px separators of x 0's colour
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            rect(a, x, y, w, 7, BAR)
            draw_text(a, FONT5, c, x, y + 1, TITLE_LIT if lit else TITLE_DIM)
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------


def genex_colours():
    return [
        N((0, 0, 0)),          # item background
        N((232, 232, 236)),    # item text
        BODY,               # window background
        N((255, 255, 255)),    # button text
        N((232, 232, 236)),    # window text
        N((52, 52, 58)),       # dividers, sunken borders
        T["genex_sel"],     # selection bar
        N((22, 22, 26)),       # list header background
        N((236, 236, 240)),    # list header text
        N((70, 70, 78)),       # header frame, light
        N((4, 4, 6)),          # header frame, dark
        T["genex_sel"],     # header frame, pressed
        BODY,               # header dead area
        N((30, 30, 34)),       # scrollbar
        N((200, 200, 206)),    # scrollbar 2
        N((44, 44, 50)),       # scrollbar pressed
        T["accent"],        # scrollbar pressed 2
        N((16, 16, 18)),       # scrollbar dead area
    ]


def make_genex():
    a = new(256, 64, BODY)
    rect(a, 0, 0, 256, 1, BODY)
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    flat_button(a, 0, 1, 47, 15, False)
    flat_button(a, 0, 16, 47, 15, True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    kind, stops = T["vis"]
    spec = []
    for i in range(16):
        if kind == "bands":
            # stacked bands, top to bottom in member order (16 rows: 3,3,3,3,4)
            k = min(4, i // 3)
            c = stops[k]
            c = tint(c, 0.18) if i % 3 == 0 and k < 4 else c
        else:
            c = ramp(stops, i / 15)
        spec.append((c, f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}"))
    return ([(N((0, 0, 0)), "background"), (N((26, 26, 30)), "dots")] + spec
            + [(N((255, 255, 255)), "oscilloscope 1"), (N((220, 220, 224)), "oscilloscope 2"),
               (N((180, 180, 186)), "oscilloscope 3"), (N((140, 140, 146)), "oscilloscope 4"),
               (N((100, 100, 106)), "oscilloscope 5"), (N((255, 255, 255)), "peaks")])


def hexc(c):
    return "#%02X%02X%02X" % tuple(c)


def pledit_colours():
    return dict(Normal=N((0xE8, 0xE8, 0xE8)), Current=T["current"], NormalBG=N((0, 0, 0)), SelectedBG=T["sel_bg"])


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    c = pledit_colours()
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={hexc(c['Normal'])}\nCurrent={hexc(c['Current'])}\nNormalBG={hexc(c['NormalBG'])}\n"
                f"SelectedBG={hexc(c['SelectedBG'])}\nMbBG={hexc(N((0, 0, 0)))}\nMbFG={hexc(N((0xE8, 0xE8, 0xE8)))}\nFont=Arial\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        who = T["readme_who"]
        f.write(f"{T['wsz'][:-4]}\n\n")
        if T["member"] is None:
            f.write("ARTMS — a fan skin. ARTMS logo and signatures © MODHAUS.\n")
        else:
            extra = " and objekt photos" if T["objekt"] else ""
            f.write(f"ARTMS — a fan skin for {who}. ARTMS logo, signatures{extra} © MODHAUS.\n")


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
    SHEETS.clear()
    for name, arr in sheets.items():
        SHEETS[name[:-4]] = save(arr, name)
    write_text_files()
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "readme.txt"]
    with zipfile.ZipFile(os.path.join(HERE, T["wsz"]), "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))  # fixed: reproducible zips
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(os.path.join(OUT, n), "rb") as f:
                z.writestr(info, f.read())
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
for _k, _v in {"<": "[", ">": "]", "{": "[", "}": "]"}.items():
    FONT_LOOKUP[_k] = FONT_LOOKUP[_v]


def draw_bitmap_text(dst, s, x, y):
    text = SHEETS["text"]
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, text, (col * 5, row * 6, 5, 6), x, y)
        x += 5


def preview_font(size):
    for name in ("LiberationSans-Regular.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def viscolors():
    return [c for c, _ in viscolor()]


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
    # the app draws the title in a TrueType font, in text.bmp's ink colour
    d = ImageDraw.Draw(img)
    d.text((112, 22), state["title"][:34], fill=tuple(TXT), font=preview_font(8))
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
            vp[x, y] = cols[min(17, max(2, 2 - 2 + y))]
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


def preview_playlist(lit, w, h, rows, pressed_close=False, drag=False, elapsed=207, current=1):
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
    c = pledit_colours()
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=c["NormalBG"])
    try:
        font = ImageFont.truetype("LiberationSans-Regular.ttf", 9)
    except OSError:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 9)
        except OSError:
            font = ImageFont.load_default()
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=c["SelectedBG"])
        col = c["Current"] if i == current else c["Normal"]
        # a title too long for the row is cut short of the duration, as Winamp does
        label, room = f"{i + 1}. {txt}", lw - 10 - d.textlength(dur, font=font)
        if d.textlength(label, font=font) > room:
            while d.textlength(label + "...", font=font) > room:
                label = label[:-1]
            label = label.rstrip() + "..."
        d.text((lx + 2, y + 2), label, fill=col, font=font)
        d.text((lx + lw - 3 - d.textlength(dur, font=font), y + 2), dur, fill=col, font=font)
    blit(img, sheet, (61 if drag else 52, 53, 8, 18), w - 15, 20 + 30)
    # the footer: the selected row's length / the whole list's, and the elapsed time
    def secs(t):
        m, s_ = t.split(":")
        return int(m) * 60 + int(s_)
    total = sum(secs(dur) for _, dur in rows)
    draw_bitmap_text(img, f"{rows[2][1]}/{total // 60}:{total % 60:02d}", w - 150 + 7, h - 38 + 10)
    for dx, ch in zip([1, 7, 12, 20, 25], f" {elapsed // 60:02d}{elapsed % 60:02d}"):
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
    c = np.array(T["accent"], dtype=np.float32)
    b0 = np.array(N((10, 10, 10)), dtype=np.float32)
    col = b0 + arr[..., 0:1] * (c - b0) * 0.8
    img.paste(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)), (11, 20))
    return img


# each member's ARTMS-era solo (MODHAUS), with the length YouTube Music lists
SOLOS = {"heejin": ("Algorithm", "3:09"), "haseul": ("Plastic Candy", "3:35"),
         "kimlip": ("Can You Entertain?", "2:49"), "jinsoul": ("Ring of Chaos", "2:42"),
         "choerry": ("Pressure", "2:42")}


def preview():
    # real ARTMS songs from DALL (2024), Club Icarus (2025) and Hyper-Ego (2026), with the lengths
    # YouTube Music lists; the group themes play Virtual Angel (row 2), each member's themes play
    # one of her ARTMS-era solos, put first
    rows = [("ARTMS - Birth", "2:43"), ("ARTMS - Virtual Angel", "2:54"), ("ARTMS - Flower Rhythm", "2:40"),
            ("ARTMS - Candy Crush", "3:01"), ("ARTMS - Air", "2:28"), ("ARTMS - Butterfly Effect", "3:27"),
            ("ARTMS - Icarus", "2:54"), ("ARTMS - Verified Beauty", "2:48"), ("ARTMS - BURN", "3:20"),
            ("ARTMS - Born Stunner", "2:30"), ("ARTMS - Blue Blood", "2:27")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    current = 1
    if T["member"] is not None:
        rows = [(f"{T['readme_who']} - {SOLOS[T['member']][0]}", SOLOS[T["member"]][1])] + rows[:10]
        current = 0
    song = rows[current][0]
    title = f"{song.upper()}  ***"
    # the timers follow it: elapsed at the seek bar's 0.38, remaining at its 0.8
    m, s_ = rows[current][1].split(":")
    length = int(m) * 60 + int(s_)
    played, left = round(length * 0.38), length - round(length * 0.8)
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=played, remaining=False,
             title=title, bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=left, remaining=True,
             title=f"PAUSED: {song.upper()}", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
        col.paste(preview_playlist(lit, 275, 232, rows, pressed_close=not lit, drag=not lit, elapsed=played,
                                     current=current), (0, 232))
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
        p = os.path.join(OUT, n)
        if n.endswith(".bmp"):
            im = Image.open(p)
            assert im.mode == "RGB", (n, im.mode)
    print(f"{key:16s} -> {T['wsz']}, {T['preview']}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    if "--list" in args:
        print("\n".join(THEME_KEYS))
        sys.exit(0)
    keys = []
    for a in args:
        a = a.lower().replace("--theme=", "")
        if a in ("all", "--all"):
            keys = THEME_KEYS[:]
        elif a == "--objekt":
            keys = [k if k.endswith("-objekt") or k == "artms" else f"{k}-objekt" for k in keys]
        elif a == "--light":
            keys = [k if k.endswith("-light") else f"{k}-light" for k in keys]
        elif a in THEME_KEYS:
            keys.append(a)
        elif a != "--theme":
            sys.exit(f"unknown theme {a!r}; try --list")
    for k in keys or THEME_KEYS:
        run(k)
