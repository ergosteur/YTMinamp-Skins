#!/usr/bin/python3
"""Gaming: classic Winamp 2.x skins in the style of Steam (2004 and modern), Minecraft and Twitch.

One procedural generator, one theme per skin: steam-2004, steam, minecraft, twitch. Two drawing
families: "flat" (steam, twitch: anti-aliased shapes and system sans lettering, by way of
private-repo/skins/apps/streaming/) and "pixel" (steam-2004, minecraft: bevels, textures and hand-made
pixel fonts, after skins/ember/). Everything is drawn here from code except each subject's logo,
used once in the About/emblem spot and rasterised from source/logo-*/logo.svg.

    /usr/bin/python3 -I gen_skin.py                # every theme
    /usr/bin/python3 -I gen_skin.py minecraft ...  # just these
    /usr/bin/python3 -I gen_skin.py --list

Writes out/<theme>/*.bmp + text files, <Name>.wsz and preview-<theme>.png beside this file.
The skins are for private use only (they carry the subjects' logos).
"""

import os
import subprocess
import sys
import zipfile
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py, which finishes each .wsz
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.join(HERE, "out")
SCRATCH = os.path.join(OUT_ROOT, "scratch")
OUT = OUT_ROOT  # set per theme

SEP = (255, 0, 255)  # gen.bmp letter separators (never shown)

NOTO = "/usr/share/fonts/google-noto/NotoSans-{}.ttf"
ADW = "/usr/share/fonts/adwaita-sans-fonts/AdwaitaSans-Regular.ttf"
LIBERATION = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexs(c):
    return "#%02X%02X%02X" % tuple(c)


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------
# Keys: bg (window body), bar_top/bar (titlebar gradient), bar_line (hairline under bars),
# band_y/band_top/band/band_line (the "player bar" behind the transport), panel/panel_line
# (displays: also text.bmp's and the analyzer's background), text/text2/text3 (primary,
# secondary, dim), accent/accent_hi, track (slider rails), knob (slider thumbs),
# play (round play button colours, or None for a plain glyph), seek ('line' or 'wave'),
# btn/btn_fg (pill buttons), hover (pressed highlight), fonts, playlist colours.

NOTO_SC = "/usr/share/fonts/google-noto/NotoSans-SemiCondensed{}.ttf"

THEMES = {
    "steam-2004": dict(
        style="pixel", service="Steam", name="Steam 2004", wsz="Steam-2004", company="Valve Corporation",
        logo="logo-steam", logo_url="https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/steam.svg",
        logo_tint="#d8ded3", gen_title="NEWS",
        bg="#4c5844", panel="#3e4637", text="#d8ded3", text2="#a0aa98", text3="#6c7862", accent="#c4b550",
        btn="#4c5844", btn_fg="#d8ded3", btn_pressed="#3e4637",
        pl=dict(NormalBG="#3E4637", Normal="#D8DED3", Current="#C4B550", SelectedBG="#6E6630"),
        vis=["#e8dc8a", "#c4b550", "#958831", "#5c5420"],
    ),
    "steam": dict(
        service="Steam", name="Steam", wsz="Steam", company="Valve Corporation",
        logo="logo-steam", logo_url="https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/steam.svg",
        logo_tint="#c7d5e0",
        title=None, eq_title="EQUALIZER", pl_title="GAMES", gen_title="NOW PLAYING",
        font=(NOTO.format("Bold"), None), font_bold=(NOTO.format("Bold"), None),
        digit_font=(NOTO.format("Regular"), None), digit_size=13,
        bg="#1b2838", bar_top="#171a21", bar="#171a21", bar_line="#0b0d11", bar_dim="#1e222a",
        band_y=84, band_top="#2a475e", band="#1f3a4f", band_line="#3d6c8d",
        panel="#101822", panel_line="#2a3f55", radius=2,
        text="#c7d5e0", text2="#8f98a0", text3="#4b5966", title_dim="#6a7480",
        accent="#66c0f4", accent_hi="#8fd3ff", track="#3d4f61", knob="#66c0f4", knob_hi="#a3dcff",
        play="steam", icon="#c7d5e0", icon_pressed="#ffffff",
        skip="bar", seek="line", seek_rows=(4, 2), tail=True,
        btn="#2a475e", btn_fg="#c7d5e0", btn_pressed="#3d6c8d", hover="#2f4d66",
        toggle_on="tint", on_fg="#ffffff", on_face=("#67c1f5", "#417a9b"),
        pl=dict(NormalBG="#1B2838", Normal="#C7D5E0", Current="#66C0F4", SelectedBG="#2A475E"),
        vis=["#a3dcff", "#66c0f4", "#2f7fb5", "#1a4766"],
    ),
    "minecraft": dict(
        style="pixel", service="Minecraft", name="Minecraft", wsz="Minecraft", company="Mojang Studios / Microsoft",
        logo="logo-minecraft", logo_url="https://commons.wikimedia.org/wiki/File:Minecraft_cube.svg",
        logo_tint=None, gen_title="ALBUM ART", win_text="#404040",
        bg="#c6c6c6", panel="#000000", text="#e0e0e0", text2="#a0a0a0", text3="#505050", accent="#80ff20",
        btn="#6f6f6f", btn_fg="#e0e0e0", btn_pressed="#7e88bf",
        pl=dict(NormalBG="#000000", Normal="#E0E0E0", Current="#55FF55", SelectedBG="#3C3C3C"),
        vis=["#c8ff70", "#80ff20", "#3fa010", "#1f5008"],
    ),
    "twitch": dict(
        service="Twitch", name="Twitch", wsz="Twitch", company="Twitch Interactive, Inc.",
        logo="logo-twitch", logo_url="https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/twitch.svg",
        logo_tint="#9146ff", logo_fill="#ffffff",
        title=None, eq_title="Equalizer", pl_title="STREAM CHAT", gen_title="VIDEO",
        font=(NOTO.format("SemiBold"), None), font_bold=(NOTO.format("Bold"), None),
        digit_font=(NOTO.format("SemiBold"), None), digit_size=13,
        bg="#0e0e10", bar_top="#18181b", bar="#18181b", bar_line="#2f2f35", bar_dim="#18181b",
        band_y=84, band_top="#18181b", band="#18181b", band_line="#2f2f35",
        panel="#1f1f23", panel_line=None, radius=4,
        text="#efeff1", text2="#adadb8", text3="#53535f", title_dim="#7a7a85",
        accent="#9146ff", accent_hi="#a970ff", track="#3a3a3d", knob="#ffffff", knob_hi="#bf94ff",
        play="twitch", icon="#efeff1", icon_pressed="#bf94ff",
        skip="bar", seek="line", seek_rows=(4, 2), tail=True,
        btn="#2f2f35", btn_fg="#efeff1", btn_pressed="#3a3a3d", hover="#2f2f35",
        toggle_on="tint", on_fg="#ffffff",
        pl=dict(NormalBG="#18181B", Normal="#EFEFF1", Current="#BF94FF", SelectedBG="#2F2F35"),
        vis=["#bf94ff", "#9146ff", "#772ce8", "#451093"],
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
        elif isinstance(v, tuple) and v and isinstance(v[0], str) and v[0].startswith("#"):
            raw[k] = tuple(hexc(c) for c in v)
    raw["vis"] = [hexc(c) for c in raw["vis"]]
    raw.setdefault("title_fg", raw["text"])
    raw.setdefault("bar_icon", raw["text2"])
    raw.setdefault("style", "flat")
    T = raw
    OUT = os.path.join(OUT_ROOT, key)
    os.makedirs(OUT, exist_ok=True)


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


def panel(a, x, y, w, h, r=None, col=None, line=None):
    r = T["radius"] if r is None else r
    col = T["panel"] if col is None else col
    line = T["panel_line"] if line is None else line
    if line:
        rrect(a, x - 1, y - 1, w + 2, h + 2, r + 1, line)
        # keep the inner box exactly the panel colour (text.bmp's cells sit on it)
    rrect(a, x, y, w, h, r, col)


def disc(a, cx, cy, r, col, alpha=1.0):
    """Anti-aliased disc centred at (cx, cy) in pixel-edge coordinates."""
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


def frect(a, x0, y0, x1, y1, col, r=0.0):
    """Anti-aliased (sub-pixel) rectangle from (x0, y0) to (x1, y1), optional corner radius."""
    bx, by = int(np.floor(x0)) - 1, int(np.floor(y0)) - 1
    w, h = int(np.ceil(x1)) - bx + 2, int(np.ceil(y1)) - by + 2
    m = mask(w, h, lambda d, S: d.rounded_rectangle(((x0 - bx) * S, (y0 - by) * S, (x1 - bx) * S - 1,
                                                     (y1 - by) * S - 1), radius=r * S, fill=255))
    paint(a, bx, by, m, col)


def strokes(a, x, y, w, h, fn, col, alpha=1.0):
    """Paints whatever fn(draw, S) draws (in canvas-local coordinates from (x, y))."""
    paint(a, x, y, mask(w, h, fn), col, alpha)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


# ------------------------------------------------------------------------------------------
# Lettering: the system sans (hinted, anti-aliased) and pixel fonts for text.bmp
# ------------------------------------------------------------------------------------------

_fonts = {}


def font(spec, size):
    key = (spec, size)
    if key not in _fonts:
        path, var = spec
        f = ImageFont.truetype(path, size)
        if var:
            f.set_variation_by_name(var)
        _fonts[key] = f
    return _fonts[key]


def text_width(s, f):
    return f.getlength(s)


def ttext(a, s, f, x, base, col, align="l", alpha=1.0):
    """TrueType text with its baseline on row `base`; x is the left edge or the centre."""
    if not s:
        return
    adv = f.getlength(s)
    if align == "c":
        x = x - adv / 2
    x = int(round(x))
    l, t, r, b = f.getbbox(s, anchor="ls")
    w, h = r - l + 2, b - t + 2
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).text((-l + 1, -t + 1), s, font=f, fill=255, anchor="ls")
    m = np.asarray(im, dtype=np.float32) / 255.0
    paint(a, x + l - 1, base + t - 1, m, col, alpha)


def label(a, s, cx, base, col, size=8):
    ttext(a, s, font(T["font_bold"], size), cx, base, col, "c")


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
TINY.update({
    "C": G(".##", "#..", "#..", "#..", ".##"), "F": G("###", "#..", "##.", "#..", "#.."),
    "G": G(".##", "#..", "#.#", "#.#", ".##"), "L": G("#..", "#..", "#..", "#..", "###"),
    "W": G("#.#", "#.#", "###", "###", "#.#"), "X": G("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."),
})
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
# Logos (rasterised from the downloaded SVGs at generation time)
# ------------------------------------------------------------------------------------------


def logo_rgba(size):
    """The logo as float RGBA (size x size). Monochrome marks (Simple Icons) are tinted with
    logo_tint; logo_fill paints the shape's enclosed holes (the Glitch's face) in that colour."""
    src = os.path.join(HERE, "source", T["logo"], "logo.svg")
    os.makedirs(SCRATCH, exist_ok=True)
    big = os.path.join(SCRATCH, f"{T['logo']}-{size * 8}.png")
    subprocess.run(["/usr/bin/rsvg-convert", "-w", str(size * 8), "-h", str(size * 8), "--keep-aspect-ratio",
                    src, "-o", big], check=True)
    im = Image.open(big).convert("RGBA")
    sq = Image.new("RGBA", (size * 8, size * 8), (0, 0, 0, 0))
    sq.alpha_composite(im, ((size * 8 - im.width) // 2, (size * 8 - im.height) // 2))
    arr = np.asarray(sq, dtype=np.float32).copy()
    if T.get("logo_tint"):
        arr[..., :3] = np.array(T["logo_tint"], np.float32)
    if T.get("logo_fill"):
        # flood the outside from a corner; transparent pixels it can't reach are the holes
        m = Image.fromarray((arr[..., 3] > 127).astype(np.uint8) * 255, "L").copy()
        ImageDraw.floodfill(m, (0, 0), 128)
        holes = np.asarray(m) == 0
        arr[holes, :3] = np.array(T["logo_fill"], np.float32)
        arr[holes, 3] = 255
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA").resize((size, size), Image.BOX)
    return np.asarray(out, dtype=np.float32)


def put_logo(a, x, y, size):
    rgba = logo_rgba(size)
    paint(a, x, y, rgba[..., 3] / 255.0, rgba[..., :3])


# ------------------------------------------------------------------------------------------
# Backgrounds: the bars and the main window's body column
# ------------------------------------------------------------------------------------------


def bar_rows(h, lit):
    """(h, 1, 3) column of a titlebar of height h."""
    t = new(1, h)
    if lit:
        vgrad_fill(t, 0, 0, 1, h, T["bar_top"], T["bar"])
    else:
        vgrad_fill(t, 0, 0, 1, h, lerp(T["bar_top"], T["bar_dim"], 0.7), T["bar_dim"])
    if T["bar_line"]:
        t[h - 1, 0] = T["bar_line"] if lit else lerp(T["bar_line"], T["bar_dim"], 0.4)
    return t


def bar(w, h, lit):
    return np.repeat(bar_rows(h, lit), w, axis=1)


def main_column():
    """The main window's body colour per row (horizontally uniform, so sprites can copy it)."""
    t = new(1, 116, T["bg"])
    t[0:14] = bar_rows(14, True)
    by = T["band_y"]
    vgrad_fill(t, 0, by, 1, 116 - by, T["band_top"], T["band"])
    if T["band_line"]:
        t[by, 0] = T["band_line"]
    return t


MAIN_COL = None


def body_slice(y, h, w):
    return np.repeat(MAIN_COL[y:y + h], w, axis=1).copy()


# ------------------------------------------------------------------------------------------
# Icons
# ------------------------------------------------------------------------------------------


def icon(a, kind, cx, cy, s, col):
    """Transport pictograms centred at (cx, cy) (pixel-edge coordinates); s = half height."""
    if kind == "play":
        poly(a, [(cx - s * 0.8, cy - s), (cx - s * 0.8, cy + s), (cx + s * 0.95, cy)], col)
    elif kind == "pause":
        bw = max(1.6, s * 0.62)
        frect(a, cx - s * 0.85, cy - s, cx - s * 0.85 + bw, cy + s, col, 0.4)
        frect(a, cx + s * 0.85 - bw, cy - s, cx + s * 0.85, cy + s, col, 0.4)
    elif kind == "stop":
        frect(a, cx - s * 0.9, cy - s * 0.9, cx + s * 0.9, cy + s * 0.9, col, s * 0.25)
    elif kind in ("previous", "next"):
        sg = 1 if kind == "next" else -1
        if T["skip"] == "double":
            for ox in (-s * 0.95, 0.0):
                bx = cx + sg * ox
                poly(a, [(bx, cy - s * 0.85), (bx, cy + s * 0.85), (bx + sg * s * 0.95, cy)], col)
        else:
            bx = cx - sg * s * 0.55
            poly(a, [(bx, cy - s * 0.9), (bx, cy + s * 0.9), (bx + sg * s * 1.15, cy)], col)
            ex = bx + sg * s * 1.15
            x0, x1 = (ex, ex + sg * 1.6) if sg == 1 else (ex + sg * 1.6, ex)
            frect(a, min(x0, x1), cy - s * 0.9, max(x0, x1), cy + s * 0.9, col, 0.3)
    elif kind == "eject":
        poly(a, [(cx - s, cy + s * 0.2), (cx + s, cy + s * 0.2), (cx, cy - s * 0.9)], col)
        frect(a, cx - s, cy + s * 0.5, cx + s, cy + s * 0.5 + 1.6, col, 0.3)


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


def mini_glyph(a, x, y, kind, col):
    """9x9 titlebar button pictograms."""
    if kind == "options":
        for i in range(3):
            frect(a, x + 2, y + 2.5 + 2 * i, x + 7, y + 3.5 + 2 * i, col)
    elif kind == "minimize":
        frect(a, x + 2, y + 6, x + 7, y + 7, col)
    elif kind == "shade":
        frect(a, x + 2, y + 2, x + 7, y + 3, col)
        frect(a, x + 2, y + 5, x + 7, y + 6, col)
    elif kind == "close":
        strokes(a, x, y, 9, 9, lambda d, S: (d.line((2 * S, 2 * S, 7 * S, 7 * S), fill=255, width=int(1.2 * S)),
                                             d.line((2 * S, 7 * S, 7 * S, 2 * S), fill=255, width=int(1.2 * S))),
                col)


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """A flat 9x9 titlebar button: just its glyph; pressed, a soft rounded highlight behind it."""
    if pressed:
        bg = a[y + 4, x + 4]
        rrect(a, x, y, 9, 9, 2, lerp(bg, T["title_fg"], 0.18))
    col = T["bar_icon"] if lit else lerp(T["bar_icon"], T["bar_dim"], 0.45)
    if pressed:
        col = T["title_fg"]
    mini_glyph(a, x, y, kind, col)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = body_slice(22, 43, 8)
    rrect(a, 0, 0, 8, 43, 3, lerp(T["bg"], T["text"], 0.06))
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rrect(a, 1, y, 6, h, 1.5, T["accent"])
        gy = y + (h - 5) // 2
        ptext(a, TINY, letter, 2, gy, (255, 255, 255) if on else T["text3"])
    return a


def steam_nav(a, lit):
    """Steam's top navigation as the title: STORE LIBRARY COMMUNITY and the profile name."""
    f = font((NOTO_SC.format("Bold"), None), 9)
    items = ["STORE", "LIBRARY", "COMMUNITY", "PLAYER ONE"]
    gap = 10
    total = sum(f.getlength(s) for s in items) + gap * (len(items) - 1)
    x = 20.0
    assert x + total < 240, total
    for s in items:
        if s == "LIBRARY":
            col = T["accent"] if lit else T["title_dim"]
        else:
            col = (220, 222, 223) if lit else lerp(T["title_dim"], T["bar"], 0.25)
        ttext(a, s, f, x, 10, col)
        x += f.getlength(s) + gap


def twitch_bar(a, lit):
    """Twitch's channel header: the red LIVE badge, the channel name, the red viewer count."""
    red = hexc("#eb0400") if lit else (110, 40, 40)
    rrect(a, 19, 3, 23, 9, 2, red)
    ptext_c(a, TINY, "LIVE", 30, 5, (255, 255, 255) if lit else (200, 180, 180))
    ttext(a, "YTMinamp", font((NOTO.format("Bold"), None), 10), 47, 11, T["title_fg"] if lit else T["title_dim"])
    f = font((NOTO.format("SemiBold"), None), 9)
    num = "1,337"
    w = f.getlength(num)
    x1 = 238
    vc = hexc("#ff8280") if lit else (130, 90, 90)
    ttext(a, num, f, x1 - w, 10, vc)
    # the viewer glyph: a head and shoulders
    hx = x1 - w - 7
    disc(a, hx, 5.2, 1.8, vc)
    frect(a, hx - 3, 7.6, hx + 3, 10.5, vc, 1.5)


def main_titlebar(lit):
    a = bar(275, 14, lit)
    if T["key"] == "steam":
        steam_nav(a, lit)
    elif T["key"] == "twitch":
        twitch_bar(a, lit)
    else:
        f = font(T["font"], 10)
        ttext(a, T["title"], f, 137.5, 10, T["title_fg"] if lit else T["title_dim"], "c")
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
LOGO = (16, 250, 89)  # size, x, y: the About/emblem spot


def seek_track(a, x0, y0, w):
    """The seek rail, drawn into a (rows y0..y0+10) at columns x0..x0+w."""
    if T["seek"] == "wave":
        for i, (bx, hgt) in enumerate(wave_bars(w)):
            draw_wave_bar(a, x0 + bx, y0, hgt, T["track"], lerp(T["track"], T["bg"], 0.55))
        return
    ry, rh = T["seek_rows"]
    frect(a, x0, y0 + ry, x0 + w, y0 + ry + rh, T["track"], rh / 2)


def wave_bars(w):
    """A fixed, pseudo-random waveform: (x, height) per 2px bar on a 3px pitch."""
    rng = np.random.default_rng(4242)
    out = []
    for i, x in enumerate(range(1, w - 1, 3)):
        env = 0.52 + 0.26 * np.sin(i / 6.5) + 0.16 * np.sin(i / 2.1 + 1.3) + rng.normal(0, 0.12)
        hgt = max(1, min(7, int(round(1 + 6 * max(0.0, min(1.0, env))))))
        out.append((x, hgt))
    return out


def draw_wave_bar(a, x, y0, hgt, col, refl):
    """A SoundCloud-style bar: hgt rows up from row y0+7, a 2-row paler reflection under it."""
    rect(a, x, y0 + 7 - hgt, 2, hgt, col)
    rect(a, x, y0 + 8, 2, min(2, max(1, hgt // 3)), refl)


def make_main():
    global MAIN_COL
    MAIN_COL = main_column()
    a = np.repeat(MAIN_COL, 275, axis=1).copy()
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # left display: indicator, time, analyzer
    panel(a, 21, 20, 84, 42)
    for yy in (29, 34):
        disc(a, 74, yy + 1, 1.1, T["text"])
    # right displays: title, then kbps/kHz/mono/stereo
    panel(a, 109, 21, 159, 15)
    panel(a, 109, 40, 159, 14)
    ptext(a, TINY, "KBPS", 129, 44, T["text2"])
    ptext(a, TINY, "KHZ", 169, 44, T["text2"])

    # seek rail
    seek_track(a, 16, SEEK_Y, 248)

    # the service's logo in the About spot
    size, lx, ly = LOGO
    put_logo(a, lx, ly, size)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36)
# ------------------------------------------------------------------------------------------


def transport_cell(kind, w, h, y_main, pressed):
    a = body_slice(y_main, h, w)
    cx, cy = w / 2, h / 2
    if kind == "play" and T["play"] in ("steam", "twitch"):
        if T["play"] == "steam":
            # Steam's green Play button: the #a4d007 -> #536904 fade, white glyph
            top, bot = (hexc("#b6d908"), hexc("#80a006")) if pressed else (hexc("#a4d007"), hexc("#536904"))
            m = mask(w - 2, h - 2, lambda d, S: d.rounded_rectangle((0, 0, (w - 2) * S - 1, (h - 2) * S - 1),
                                                                 radius=2 * S, fill=255))
            g = np.zeros((h - 2, w - 2, 3), np.float32)
            for r in range(h - 2):
                g[r, :] = lerp(top, bot, r / (h - 3))
            paint(a, 1, 1, m, g)
            icon(a, "play", cx + 0.6, cy, 3.8, (255, 255, 255))
        else:
            # Twitch's purple Follow-button square
            rrect(a, 1, 0, w - 2, h, 4, hexc("#772ce8") if pressed else T["accent"])
            icon(a, "play", cx + 0.6, cy, 4.0, (255, 255, 255))
        return a
    if kind == "play" and T["play"]:
        face, ink, face_p = T["play"]
        r = 8.5 if not pressed else 8.0
        disc(a, cx, cy, r, face_p if pressed else face)
        icon(a, "play", cx + 0.6, cy, 3.6, ink)
        return a
    if pressed:
        disc(a, cx, cy, 8.5, T["hover"])
    col = T["icon_pressed"] if pressed else T["icon"]
    s = {"play": 5.2, "pause": 4.2, "stop": 3.9, "previous": 4.0, "next": 4.0, "eject": 4.0}[kind]
    if kind == "play" and not T["play"]:
        s = 5.6
    icon(a, kind, cx + (0.5 if kind == "play" else 0), cy, s, col)
    return a


def make_cbuttons():
    a = new(136, 36, T["band"])
    specs = [("previous", 0, 23), ("play", 23, 23), ("pause", 46, 23), ("stop", 69, 23), ("next", 92, 22)]
    for kind, x, w in specs:
        for pressed, y in ((False, 0), (True, 18)):
            a[y:y + 18, x:x + w] = transport_cell(kind, w, 18, 88, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        a[y:y + 16, 114:136] = transport_cell("eject", 22, 16, 89, pressed)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle_icon_cell(kind, w, on, pressed):
    a = body_slice(89, 15, w)
    cx, cy = w / 2, 7
    if T["toggle_on"] == "dot":
        cy = 6
    if pressed:
        rrect(a, int(cx - 9), 0, 18, 15, 4, T["hover"])
    if on and T["toggle_on"] == "tint":
        bg = a[7, 1]
        rrect(a, int(cx - 9), 1, 18, 13, 4, lerp(bg, T["accent"], 0.16 if is_light() else 0.22))
    col = T["accent"] if on else (T["text"] if pressed else T["text2"])
    (shuffle_icon if kind == "shuffle" else repeat_icon)(a, cx, cy + 0.5, col)
    if on and T["toggle_on"] == "dot":
        disc(a, cx, 12.6, 1.1, T["accent"])
    return a


def pill_toggle(a, x, y, w, h, text, on, pressed, bg_slice):
    """A small pill (EQ/PL, ON/AUTO): accent when on."""
    a[y:y + h, x:x + w] = bg_slice
    if on:
        face = T["accent"]
        fg = T.get("on_fg", (255, 255, 255))
        if pressed:
            face = lerp(face, (0, 0, 0), 0.18)
    else:
        face = T["btn_pressed"] if pressed else T["btn"]
        fg = T["text"] if pressed else T["text2"]
    if is_light() and not on:
        rrect(a, x, y, w, h, h / 2, T.get("panel_line_btn") or T["panel_line"] or T["track"])
        rrect(a, x + 1, y + 1, w - 2, h - 2, h / 2 - 1, face)
    else:
        rrect(a, x, y, w, h, h / 2, face)
    label(a, text, x + w / 2, y + h - 3, fg, 8)


def make_shufrep():
    a = new(92, 85, T["bg"])
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        a[y:y + 15, 0:28] = toggle_icon_cell("repeat", 28, on, pressed)
        a[y:y + 15, 28:75] = toggle_icon_cell("shuffle", 47, on, pressed)
    for x, txt, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        for on, y in ((False, 61), (True, 73)):
            cell = body_slice(58, 12, 23)
            # 22 wide, so the EQ and PL pills don't touch
            pill_toggle(cell, 0, 0, 22, 12, txt, on, pressed, cell[:, :22].copy())
            a[y:y + 12, x:x + 23] = cell
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp, playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T["panel"])
    for y, on in ((0, True), (12, False)):
        col = T["text"] if on else T["text3"]
        ptext_c(a, TINY, "STEREO", 14, y + 4, col)
        ptext_c(a, TINY, "MONO", 29 + 13, y + 4, col)
    return a


def make_playpaus():
    a = new(48, 9, T["panel"])
    icon(a, "play", 4.6, 4.5, 3.4, T["accent"])
    icon(a, "pause", 9 + 4.5, 4.5, 3.2, T["text"])
    icon(a, "stop", 18 + 4.5, 4.5, 3.0, T["text"])
    disc(a, 39 + 1.5, 4.5, 1.0, T["text3"])
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["panel"])
    f = font(T["digit_font"], T.get("digit_size", 13))
    for n in range(10):
        ttext(a, str(n), f, 9 * n + 4.5, 11, T["text"], "c")
    if ex:
        frect(a, 99 + 2, 6, 99 + 7, 7.4, T["text"])
    else:
        # numbers.bmp's minus is read from (20, 6, 5, 1): keep that row of digit 2 a clean dash
        pass
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
            key = ch if ch in FONT5 else ch.upper()
            ptext(a, FONT5, key, col * 5, row * 6, T["text"])
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def knob(a, cx, cy, r, selected, col=None, col_hi=None):
    col = T["knob"] if col is None else col
    col_hi = T["knob_hi"] if col_hi is None else col_hi
    if is_light() and col == (255, 255, 255):
        disc(a, cx, cy + 0.6, r + 0.4, (0, 0, 0), 0.18)
        disc(a, cx, cy, r + 0.3, (190, 190, 196))
        disc(a, cx, cy, r - 0.3, (236, 236, 240) if selected else col)
        return
    if selected:
        disc(a, cx, cy, r + 0.5, col_hi)
    else:
        disc(a, cx, cy, r, col)


def seek_thumb(selected):
    a = body_slice(SEEK_Y, 10, 29)
    if T["seek"] == "wave":
        # the playhead: a run of played (orange) bars, ending in the playhead line
        bars = wave_bars(400)[40:60]
        x = 0
        for i, (_, hgt) in enumerate(bars):
            if x + 2 > 27:
                break
            t = min(1.0, (x + 2) / 14)
            col = lerp(lerp(T["track"], T["accent"], 0.35), T["accent"], t)
            draw_wave_bar(a, x, 0, hgt, col, lerp(col, T["bg"], 0.55))
            x += 3
        rect(a, 27, 0, 2, 10, T["accent_hi"] if selected else T["accent"])
        return a
    ry, rh = T["seek_rows"]
    cx = 23.5
    rect(a, 0, ry, 29, rh, T["track"])
    for x in range(29):
        if x + 0.5 > cx:
            break
        t = max(0.0, min(1.0, x / 16))
        t = t * t * (3 - 2 * t)
        col = lerp(T["track"], T["accent"], t)
        a[ry:ry + rh, x] = col if T["tail"] else T["track"]
    # soften the rail's ends against the body above and below (kept 1px crisp rows)
    knob(a, cx, ry + rh / 2, 4.5, selected)
    return a


def make_posbar(main):
    a = new(307, 10, T["bg"])
    a[0:10, 0:248] = main[SEEK_Y:SEEK_Y + 10, 16:264]
    a[0:10, 248:277] = seek_thumb(False)
    a[0:10, 278:307] = seek_thumb(True)
    a[0:10, 277] = MAIN_COL[SEEK_Y:SEEK_Y + 10, 0]
    return a


def h_rail(a, x0, x1, y, fill_to=None, fill_from=None):
    """A 3px rounded rail over rows y..y+2 from x0 to x1, filled in the accent up to fill_to."""
    frect(a, x0, y, x1, y + 3, T["track"], 1.5)
    if fill_to is not None:
        f0 = x0 if fill_from is None else fill_from
        if fill_to - f0 >= 1:
            frect(a, f0, y, fill_to, y + 3, T["accent"], 1.5)


def slider_thumbs(a):
    for x, sel in ((0, True), (15, False)):
        t = body_slice(58, 11, 14)
        knob(t, 7, 5.5, 4.5, sel)
        a[422:433, x:x + 14] = t


def make_volume():
    a = new(68, 433, T["bg"])
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = body_slice(57, 15, 68)
        level = (i + 1) / 28
        h_rail(a[y:y + 15], 3, 65, 5, 7 + round(level * 54))
    slider_thumbs(a)
    return a


def make_balance():
    a = new(68, 433, T["bg"])
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = body_slice(57, 15, 68)
        t = a[y:y + 15]
        reach = round(12 * i / 27)
        h_rail(t, 12, 44, 5)
        if reach:
            frect(t, 28 - reach, 5, 28 + reach, 8, T["accent"], 1.5)
        frect(t, 27.5, 3, 28.5, 10, T["text3"])
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = bar(275, 14, lit)
    ttext(a, T["eq_title"], font(T["font"], 10), 137.5, 10, T["title_fg"] if lit else T["title_dim"], "c")
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    """14x63 cell: a vertical rail, filled from the 0 dB line to the value."""
    rect(a, x, y, 14, 63, T["panel"])
    v = n / 27
    centre = (1 - v) * 51 + 6.0
    zero = 31.5
    frect(a, x + 5, y + 3, x + 8, y + 60, T["track"], 1.5)
    lo, hi = min(centre, zero), max(centre, zero)
    if hi - lo >= 0.5:
        frect(a, x + 5, y + lo, x + 8, y + hi, T["accent"], 1.0)


def make_eqmain():
    a = new(275, 315, T["bg"])
    a[0:14, :] = eq_titlebar(True)
    # graph seat and slider card
    panel(a, 85, 16, 115, 21)
    panel(a, 16, 36, 245, 68)
    rect(a, 40, 40, 1, 60, lerp(T["panel"], T["text"], 0.1))
    for lbl, yy in (("+12DB", 41), ("+0DB", 67), ("-12DB", 92)):
        ptext_c(a, TINY, lbl, 58, yy, T["text2"])
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    ptext_c(a, TINY, "PREAMP", 28, 106, T["text2"])
    for i, lbl in enumerate(EQ_BANDS):
        ptext_c(a, TINY, lbl, 78 + 18 * i + 7, 106, T["text2"])

    # under the window: buttons
    b = bar(9, 14, True)[3:12].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = b
    bg12 = np.repeat(np.array(T["bg"], dtype=np.int32)[None, None, :], 12, axis=0)
    for x, txt, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if txt == "ON" else 32
        cell = new(w, 12, T["bg"])
        pill_toggle(cell, 1, 0, w - 2, 12, txt, on, pressed, np.repeat(bg12, w - 2, axis=1))
        a[119:131, x:x + w] = cell
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    for y, sel in ((164, False), (176, True)):
        t = new(11, 11, T["panel"])
        knob(t, 5.5, 5.5, 4.5, sel)
        a[y:y + 11, 0:11] = t
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        cell = new(44, 12, T["bg"])
        face = T["btn_pressed"] if pressed else T["btn"]
        if is_light():
            rrect(cell, 0, 0, 44, 12, 6, T.get("panel_line_btn") or T["panel_line"] or T["track"])
            rrect(cell, 1, 1, 42, 10, 5, face)
        else:
            rrect(cell, 0, 0, 44, 12, 6, face)
        label(cell, "PRESETS", 22, 9, T["text"] if pressed else T["btn_fg"], 8)
        a[y:y + 12, 224:268] = cell
    # graph
    rect(a, 0, 294, 113, 19, T["panel"])
    rect(a, 0, 294 + 9, 113, 1, lerp(T["panel"], T["text"], 0.12))
    for x in range(0, 113, 12):
        for y in range(0, 19, 3):
            px(a, x, 294 + y, lerp(T["panel"], T["text"], 0.07))
    for r in range(19):
        px(a, 115, 294 + r, T["accent"])
    for x in range(113):
        px(a, x, 314, T["text3"] if x % 3 != 2 else T["panel"])
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

BAR20_BASE = 11  # title baseline in the 20px bars (caps over rows 4..10, like gen.bmp's letters)


def bottom_strip(w, h):
    """The playlist's bottom strip: the theme's player-bar colour, a hairline along its top."""
    t = new(w, h)
    vgrad_fill(t, 0, 0, w, h, T["band_top"], T["band"])
    if T["band_line"]:
        rect(t, 0, 0, w, 1, T["band_line"])
    return t


def pill_button(t, x, y, w, h, txt):
    if is_light():
        rrect(t, x, y, w, h, 4, T.get("panel_line_btn") or T["panel_line"] or T["track"])
        rrect(t, x + 1, y + 1, w - 2, h - 2, 3, T["btn"])
    else:
        rrect(t, x, y, w, h, 4, T["btn"])
    label(t, txt, x + w / 2, y + h // 2 + 3, T["btn_fg"], 8)


def readout(t, x, y, w, h):
    rrect(t, x - 1, y - 1, w + 2, h + 2, 2, T["panel"])
    rect(t, x, y, w, h, T["panel"])


def make_pledit():
    a = new(280, 186, T["bg"])
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar(25, 20, lit)
        a[y:y + 20, 0:25] = bar(25, 20, lit)
        t = bar(100, 20, lit)
        ttext(t, T["pl_title"], font(T["font"], 10), 50, BAR20_BASE + 1, T["title_fg"] if lit else T["title_dim"],
              "c")
        a[y:y + 20, 26:126] = t
        t = bar(25, 20, lit)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    # sides: plain body, the scrollbar's lane in the right one
    a[42:71, 0:12] = T["bg"]
    a[42:71, 31:51] = T["bg"]
    b = bar(9, 20, True)[3:12].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = b
    for x, sel in ((52, False), (61, True)):
        t = new(8, 18, T["bg"])
        frect(t, 2, 1, 6, 17, T["text2"] if sel else T["text3"], 2)
        a[53:71, x:x + 8] = t

    # bottom
    t = bottom_strip(125, 38)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        pill_button(t, bx, 9, 22, 16, lbl)
    a[72:110, 0:125] = t

    t = bottom_strip(150, 38)
    readout(t, 6, 9, 56, 8)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        icon(t, kind, bx + 5, 22 + 5, 2.6 if kind != "play" else 3.0, T["text2"])
    readout(t, 65, 22, 33, 8)
    rect(t, 84, 24, 1, 1, T["text2"])  # the colon between minutes and seconds
    rect(t, 84, 27, 1, 1, T["text2"])
    pill_button(t, 106, 9, 22, 16, "LIST")
    for k in range(4):
        for j in range(k + 1):
            disc(t, 146.5 - 3 * k + 3 * j, 34.5 - 3 * j, 0.7, T["text3"])
    a[72:110, 126:276] = t

    a[0:38, 179:204] = bottom_strip(25, 38)
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_letter_cells(lit):
    """Each capital as its own cell (on the bar's rows 4..10), for gen.bmp's letter rows."""
    f = font(T["font"], 9)
    col = T["title_fg"] if lit else T["title_dim"]
    rows = bar_rows(20, lit)[4:11]
    cells = []
    for c in GEN_LETTERS:
        adv = int(round(f.getlength(c)))
        w = max(3, adv)
        cell = np.repeat(rows, w, axis=1).copy()
        ttext(cell, c, f, w / 2, 7, col, "c")
        cells.append(cell)
    return cells


def make_gen():
    a = new(194, 109, T["bg"])
    for lit, y in ((True, 0), (False, 21)):
        for x0 in (0, 26, 52, 78, 104, 130):
            a[y:y + 20, x0:x0 + 25] = bar(25, 20, lit)
        t = bar(25, 20, lit)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 130:155] = t

    def bottom(w, grip):
        t = new(w, 14, T["bg"])
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    disc(t, w - 3.5 - 3 * k + 3 * j, 11.5 - 3 * j, 0.7, T["text3"])
        return t

    a[42:56, 0:125] = bottom(125, False)
    a[57:71, 0:125] = bottom(125, True)
    a[72:86, 127:152] = bottom(25, False)
    for x, w, h in ((127, 11, 29), (158, 11, 24), (139, 8, 29), (170, 8, 24)):
        a[42:42 + h, x:x + w] = T["bg"]
    b = bar(9, 20, True)[3:12].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = b

    # letters: each row starts at x 1, letters in their own cells, 1px separators of x 0's colour
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
# Pixel family: fonts (drawn for these skins)
# ------------------------------------------------------------------------------------------


def pg(H, top, *rows):
    w = len(rows[0])
    return ["." * w] * top + list(rows) + ["." * w] * (H - top - len(rows))


def _font(H, spec):
    return {c: pg(H, top, *rows) for c, (top, rows) in spec.items()}


# VG: a Tahoma 8-like proportional font, the VGUI's small UI lettering (caps 7 rows, x-height 5,
# descenders 2; 9 rows in all).
VG = _font(9, {
    "A": (0, ["..#..", ".#.#.", ".#.#.", "#...#", "#####", "#...#", "#...#"]),
    "B": (0, ["###.", "#..#", "#..#", "###.", "#..#", "#..#", "###."]),
    "C": (0, [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."]),
    "D": (0, ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."]),
    "E": (0, ["####", "#...", "#...", "###.", "#...", "#...", "####"]),
    "F": (0, ["####", "#...", "#...", "###.", "#...", "#...", "#..."]),
    "G": (0, [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."]),
    "H": (0, ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"]),
    "I": (0, ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"]),
    "J": (0, ["..#", "..#", "..#", "..#", "..#", "..#", "##."]),
    "K": (0, ["#..#", "#.#.", "##..", "##..", "#.#.", "#..#", "#..#"]),
    "L": (0, ["#...", "#...", "#...", "#...", "#...", "#...", "####"]),
    "M": (0, ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"]),
    "N": (0, ["#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"]),
    "O": (0, [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."]),
    "P": (0, ["###.", "#..#", "#..#", "###.", "#...", "#...", "#..."]),
    "Q": (0, [".###.", "#...#", "#...#", "#...#", "#...#", "#..#.", ".##.#"]),
    "R": (0, ["###.", "#..#", "#..#", "###.", "#.#.", "#..#", "#..#"]),
    "S": (0, [".###", "#...", "#...", ".##.", "...#", "...#", "###."]),
    "T": (0, ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."]),
    "U": (0, ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."]),
    "V": (0, ["#...#", "#...#", "#...#", ".#.#.", ".#.#.", ".#.#.", "..#.."]),
    "W": (0, ["#..#..#", "#..#..#", ".#.#.#.", ".#.#.#.", ".#.#.#.", "..#.#..", "..#.#.."]),
    "X": (0, ["#...#", ".#.#.", ".#.#.", "..#..", ".#.#.", ".#.#.", "#...#"]),
    "Y": (0, ["#...#", ".#.#.", ".#.#.", "..#..", "..#..", "..#..", "..#.."]),
    "Z": (0, ["####", "...#", "..#.", ".#..", ".#..", "#...", "####"]),
    "a": (2, [".##.", "...#", ".###", "#..#", ".###"]),
    "b": (0, ["#...", "#...", "###.", "#..#", "#..#", "#..#", "###."]),
    "c": (2, [".##", "#..", "#..", "#..", ".##"]),
    "d": (0, ["...#", "...#", ".###", "#..#", "#..#", "#..#", ".###"]),
    "e": (2, [".##.", "#..#", "####", "#...", ".###"]),
    "f": (0, [".##", "#..", "###", "#..", "#..", "#..", "#.."]),
    "g": (2, [".###", "#..#", "#..#", "#..#", ".###", "...#", ".##."]),
    "h": (0, ["#...", "#...", "###.", "#..#", "#..#", "#..#", "#..#"]),
    "i": (0, ["#", ".", "#", "#", "#", "#", "#"]),
    "j": (0, [".#", "..", ".#", ".#", ".#", ".#", ".#", ".#", "#."]),
    "k": (0, ["#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#"]),
    "l": (0, ["#", "#", "#", "#", "#", "#", "#"]),
    "m": (2, ["####.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"]),
    "n": (2, ["###.", "#..#", "#..#", "#..#", "#..#"]),
    "o": (2, [".##.", "#..#", "#..#", "#..#", ".##."]),
    "p": (2, ["###.", "#..#", "#..#", "#..#", "###.", "#...", "#..."]),
    "q": (2, [".###", "#..#", "#..#", "#..#", ".###", "...#", "...#"]),
    "r": (2, ["#.#", "##.", "#..", "#..", "#.."]),
    "s": (2, [".##", "#..", ".#.", "..#", "##."]),
    "t": (1, [".#.", "###", ".#.", ".#.", ".#.", "..#"]),
    "u": (2, ["#..#", "#..#", "#..#", "#..#", ".###"]),
    "v": (2, ["#...#", "#...#", ".#.#.", ".#.#.", "..#.."]),
    "w": (2, ["#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."]),
    "x": (2, ["#...#", ".#.#.", "..#..", ".#.#.", "#...#"]),
    "y": (2, ["#..#", "#..#", "#..#", "#..#", ".###", "...#", ".##."]),
    "z": (2, ["####", "..#.", ".#..", "#...", "####"]),
    "0": (0, [".##.", "#..#", "#..#", "#..#", "#..#", "#..#", ".##."]),
    "1": (0, [".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"]),
    "2": (0, [".##.", "#..#", "...#", "..#.", ".#..", "#...", "####"]),
    "3": (0, [".##.", "#..#", "...#", ".##.", "...#", "#..#", ".##."]),
    "4": (0, ["..#.", ".##.", "#.#.", "#.#.", "####", "..#.", "..#."]),
    "5": (0, ["####", "#...", "###.", "...#", "...#", "#..#", ".##."]),
    "6": (0, [".##.", "#...", "###.", "#..#", "#..#", "#..#", ".##."]),
    "7": (0, ["####", "...#", "..#.", "..#.", ".#..", ".#..", ".#.."]),
    "8": (0, [".##.", "#..#", "#..#", ".##.", "#..#", "#..#", ".##."]),
    "9": (0, [".##.", "#..#", "#..#", "#..#", ".###", "...#", ".##."]),
    " ": (0, ["..", "..", "..", "..", "..", "..", ".."]),
    ".": (6, ["#"]),
    ":": (2, ["#", ".", ".", ".", "#"]),
    "-": (4, ["###"]),
})

# MC: a Minecraft-style font: blocky 5-wide glyphs, caps 7 rows, one descender row (8 rows).
MC = _font(8, {
    "A": (0, [".###.", "#...#", "#####", "#...#", "#...#", "#...#", "#...#"]),
    "B": (0, ["####.", "#...#", "####.", "#...#", "#...#", "#...#", "####."]),
    "C": (0, [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."]),
    "D": (0, ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."]),
    "E": (0, ["#####", "#....", "###..", "#....", "#....", "#....", "#####"]),
    "F": (0, ["#####", "#....", "###..", "#....", "#....", "#....", "#...."]),
    "G": (0, [".####", "#....", "#..##", "#...#", "#...#", "#...#", ".###."]),
    "H": (0, ["#...#", "#...#", "#####", "#...#", "#...#", "#...#", "#...#"]),
    "I": (0, ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"]),
    "J": (0, ["....#", "....#", "....#", "....#", "....#", "#...#", ".###."]),
    "K": (0, ["#...#", "#..#.", "###..", "#..#.", "#...#", "#...#", "#...#"]),
    "L": (0, ["#....", "#....", "#....", "#....", "#....", "#....", "#####"]),
    "M": (0, ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"]),
    "N": (0, ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"]),
    "O": (0, [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."]),
    "P": (0, ["####.", "#...#", "####.", "#....", "#....", "#....", "#...."]),
    "Q": (0, [".###.", "#...#", "#...#", "#...#", "#...#", "#..#.", ".##.#"]),
    "R": (0, ["####.", "#...#", "####.", "#...#", "#...#", "#...#", "#...#"]),
    "S": (0, [".####", "#....", ".###.", "....#", "....#", "#...#", ".###."]),
    "T": (0, ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."]),
    "U": (0, ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."]),
    "V": (0, ["#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#.."]),
    "W": (0, ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"]),
    "X": (0, ["#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#", "#...#"]),
    "Y": (0, ["#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..", "..#.."]),
    "Z": (0, ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"]),
    "a": (2, [".###.", "....#", ".####", "#...#", ".####"]),
    "b": (0, ["#....", "#....", "#.##.", "##..#", "#...#", "#...#", "####."]),
    "c": (2, [".###.", "#...#", "#....", "#...#", ".###."]),
    "d": (0, ["....#", "....#", ".##.#", "#..##", "#...#", "#...#", ".####"]),
    "e": (2, [".###.", "#...#", "#####", "#....", ".####"]),
    "f": (0, ["..##", ".#..", "####", ".#..", ".#..", ".#..", ".#.."]),
    "g": (2, [".####", "#...#", "#...#", ".####", "....#", "####."]),
    "h": (0, ["#....", "#....", "#.##.", "##..#", "#...#", "#...#", "#...#"]),
    "i": (0, ["#", ".", "#", "#", "#", "#", "#"]),
    "k": (0, ["#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#"]),
    "l": (0, ["#.", "#.", "#.", "#.", "#.", "#.", ".#"]),
    "m": (2, ["##.#.", "#.#.#", "#.#.#", "#...#", "#...#"]),
    "n": (2, ["####.", "#...#", "#...#", "#...#", "#...#"]),
    "o": (2, [".###.", "#...#", "#...#", "#...#", ".###."]),
    "p": (2, ["#.##.", "##..#", "#...#", "####.", "#....", "#...."]),
    "q": (2, [".##.#", "#..##", "#...#", ".####", "....#", "....#"]),
    "r": (2, ["#.##.", "##..#", "#....", "#....", "#...."]),
    "s": (2, [".####", "#....", ".###.", "....#", "####."]),
    "t": (0, ["...", ".#.", "###", ".#.", ".#.", ".#.", "..#"]),
    "u": (2, ["#...#", "#...#", "#...#", "#...#", ".####"]),
    "v": (2, ["#...#", "#...#", "#...#", ".#.#.", "..#.."]),
    "w": (2, ["#...#", "#...#", "#.#.#", "#.#.#", ".####"]),
    "x": (2, ["#...#", ".#.#.", "..#..", ".#.#.", "#...#"]),
    "y": (2, ["#...#", "#...#", "#...#", ".####", "....#", "####."]),
    "z": (2, ["#####", "...#.", "..#..", ".#...", "#####"]),
    "0": (0, [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."]),
    "1": (0, ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"]),
    "2": (0, [".###.", "#...#", "....#", "..##.", ".#...", "#...#", "#####"]),
    "3": (0, [".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."]),
    "4": (0, ["...##", "..#.#", ".#..#", "#...#", "#####", "....#", "....#"]),
    "5": (0, ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."]),
    "6": (0, ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."]),
    "7": (0, ["#####", "#...#", "....#", "...#.", "..#..", "..#..", "..#.."]),
    "8": (0, [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."]),
    "9": (0, [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."]),
    " ": (0, ["...", "...", "...", "...", "...", "...", "..."]),
    ".": (6, ["#"]),
    ":": (1, ["#", "#", ".", ".", "#", "#"]),
    "-": (3, ["#####"]),
})

# 4x6 digits, drawn at 2x for numbers.bmp (8x12 in the 9x13 cell, room for a 1px shadow).
BIGDIG = {
    0: [".##.", "#..#", "#..#", "#..#", "#..#", ".##."],
    1: [".#..", "##..", ".#..", ".#..", ".#..", "###."],
    2: [".##.", "#..#", "..#.", ".#..", "#...", "####"],
    3: ["###.", "...#", ".##.", "...#", "...#", "###."],
    4: ["#..#", "#..#", "####", "...#", "...#", "...#"],
    5: ["####", "#...", "###.", "...#", "...#", "###."],
    6: [".##.", "#...", "###.", "#..#", "#..#", ".##."],
    7: ["####", "...#", "..#.", ".#..", ".#..", ".#.."],
    8: [".##.", "#..#", ".##.", "#..#", "#..#", ".##."],
    9: [".##.", "#..#", "#..#", ".###", "...#", ".##."],
}

# The "STEAM" wordmark of the 2003-2008 client, heavy squared capitals (drawn here).
STEAM_WORD = {
    "S": [".#####", "##....", "##....", ".####.", "....##", "....##", "#####."],
    "T": ["######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##.."],
    "E": ["######", "##....", "##....", "#####.", "##....", "##....", "######"],
    "A": ["..##..", ".####.", "##..##", "##..##", "######", "##..##", "##..##"],
    "M": ["##...##", "###.###", "##.#.##", "##.#.##", "##...##", "##...##", "##...##"],
}

PIX_ICONS = {
    "shuffle": ["........#..", "###....####", "...#...##..", "....#.#....", ".....#.....", "....#.#....",
                "...#...##..", "###....####", "........#.."],
    "repeat": [".......#...", ".#########.", "#......#...", "#.........#", "#.........#", "#.........#",
               "...#......#", ".#########.", "...#......."],
}


def pt_w(fnt, s, gap=1):
    s = [c for c in s if c in fnt]
    return sum(len(fnt[c][0]) for c in s) + gap * max(0, len(s) - 1)


def pt(a, fnt, s, x, y, col, shadow=None, gap=1):
    """Pixel text; shadow is drawn one pixel down-right first (Minecraft's text shadow)."""
    for pass_, c_ in ((0, shadow), (1, col)):
        if c_ is None:
            continue
        xx = x
        for ch in s:
            if ch not in fnt:
                continue
            g = fnt[ch]
            o = 1 if pass_ == 0 else 0
            for r, row in enumerate(g):
                for k, v in enumerate(row):
                    if v == "#":
                        px(a, xx + k + o, y + r + o, c_)
            xx += len(g[0]) + gap
    return x + pt_w(fnt, s, gap)


def pt_c(a, fnt, s, cx, y, col, shadow=None, gap=1):
    pt(a, fnt, s, int(round(cx - pt_w(fnt, s, gap) / 2)), y, col, shadow, gap)


def bitmap(a, rows, x, y, col):
    for r, row in enumerate(rows):
        for k, v in enumerate(row):
            if v == "#":
                px(a, x + k, y + r, col)


# ------------------------------------------------------------------------------------------
# Pixel family: materials and controls
# ------------------------------------------------------------------------------------------
# Steam 2004: the VGUI2 "Steam" scheme (olive #4c5844 faces, #3e4637 lists and fields,
# Border.Bright #888f80 / Border.Dark #282e22, #d8ded3 text, #c4b550 highlights).
S_FACE, S_DK, S_HI, S_LO = (76, 88, 68), (62, 70, 55), (136, 145, 128), (40, 46, 34)
S_TXT, S_DIM, S_ACC = (216, 222, 211), (160, 170, 150), (196, 181, 80)
# Minecraft: the GUI panel (#c6c6c6, white / #555555 bevel, black outline), inventory slots
# (#8b8b8b, #373737 / white), text fields (black, #a0a0a0 border), #e0e0e0 text with a 1/4 shadow.
M_GUI, M_HI, M_LO, M_BLK = (198, 198, 198), (255, 255, 255), (85, 85, 85), (0, 0, 0)
M_SLOT, M_SLOT_D = (139, 139, 139), (55, 55, 55)
M_EDGE, M_TXT, M_SHD, M_LBL = (160, 160, 160), (224, 224, 224), (56, 56, 56), (64, 64, 64)
M_XP, M_XP_HI, M_XP_LO, M_XP_SHD = (128, 255, 32), (196, 255, 120), (70, 170, 14), (32, 63, 8)
M_PLATE = (44, 32, 22)


def is_mc():
    return T["key"] == "minecraft"


def seed(tag):
    return zlib.crc32(f"{T['key']}:{tag}".encode())


def bevel(a, x, y, w, h, tl, br):
    rect(a, x, y, w, 1, tl)
    rect(a, x, y, 1, h, tl)
    rect(a, x, y + h - 1, w, 1, br)
    rect(a, x + w - 1, y, 1, h, br)


def stone_noise(a, x, y, w, h, amp, tag):
    rng = np.random.default_rng(seed(tag))
    n = rng.integers(-amp, amp + 1, (h, w))
    a[y:y + h, x:x + w] += n[:, :, None]


GRASS = [(121, 192, 90), (104, 171, 70), (93, 156, 60), (82, 140, 52), (110, 180, 78)]
DIRT = [(134, 96, 67), (121, 85, 58), (150, 108, 74), (106, 75, 51), (185, 133, 92), (96, 67, 45)]
DIRT_W = [0.30, 0.26, 0.18, 0.14, 0.04, 0.08]


def grass(w, h, lit, tag):
    """A grass-block side strip: noisy green turf with ragged drips into dirt, a black top edge.
    Per-pixel noise only, so 25px tiles meet without seams."""
    rng = np.random.default_rng(seed(f"grass{w}x{h}:{tag}"))
    a = new(w, h)
    di = rng.choice(len(DIRT), size=(h, w), p=DIRT_W)
    gi = rng.integers(0, len(GRASS), size=(h, w))
    base = 4 if h == 14 else 5
    drips = rng.choice([0, 0, 0, 1, 1, 2, 3], size=w)
    for x in range(w):
        d = base + drips[x]
        for y in range(h):
            a[y, x] = GRASS[gi[y, x]] if y < d else DIRT[di[y, x]]
    rect(a, 0, 0, w, 1, M_BLK)
    if not lit:
        g = a.mean(axis=2, keepdims=True)
        a[:] = np.round((a * 0.45 + g * 0.55) * 0.82).astype(np.int32)
        rect(a, 0, 0, w, 1, M_BLK)
    return a


def pbar(w, h, lit, tag, baseline=True):
    """A titlebar tile (14 or 20 rows)."""
    if is_mc():
        return grass(w, h, lit, tag)
    a = new(w, h, S_FACE)
    rect(a, 0, 0, w, 1, S_HI)
    if baseline:
        rect(a, 0, h - 1, w, 1, S_HI)
    return a


def bar_edges(a, left=False, right=False):
    h = a.shape[0]
    if is_mc():
        if left:
            rect(a, 0, 0, 1, h, M_BLK)
        if right:
            rect(a, a.shape[1] - 1, 0, 1, h, M_BLK)
    else:
        if left:
            rect(a, 0, 0, 1, h, S_HI)
        if right:
            rect(a, a.shape[1] - 1, 1, 1, h - 1, S_LO)


def pdisplay(a, x, y, w, h):
    """A field whose inner box (x, y, w, h) is exactly the panel colour; its frame is outside."""
    if is_mc():
        rect(a, x - 1, y - 1, w + 2, h + 2, M_EDGE)
        rect(a, x, y, w, h, M_BLK)
    else:
        bevel(a, x - 1, y - 1, w + 2, h + 2, S_LO, S_HI)
        rect(a, x, y, w, h, S_DK)


def mc_slot(a, x, y, w, h, fill=M_SLOT):
    rect(a, x, y, w, h, fill)
    rect(a, x, y, w - 1, 1, M_SLOT_D)
    rect(a, x, y, 1, h - 1, M_SLOT_D)
    rect(a, x + 1, y + h - 1, w - 1, 1, M_HI)
    rect(a, x + w - 1, y + 1, 1, h - 1, M_HI)


def pbutton(a, x, y, w, h, pressed=False, on=False, default=False, tag="b"):
    """A button face; returns (ink, shadow, offset) for what goes on it."""
    if is_mc():
        if on:
            face, hi, lo = ((88, 168, 60), (130, 210, 100), (40, 100, 26)) if pressed else \
                ((60, 133, 39), (98, 176, 70), (30, 88, 20))
        elif pressed:
            face, hi, lo = (126, 136, 191), (188, 198, 255), (70, 78, 130)
        else:
            face, hi, lo = (111, 111, 111), (170, 170, 170), (70, 70, 70)
        rect(a, x, y, w, h, M_BLK)
        rect(a, x + 1, y + 1, w - 2, h - 2, face)
        stone_noise(a, x + 1, y + 1, w - 2, h - 2, 5, f"{tag}{x},{y},{w},{h},{on},{pressed}")
        rect(a, x + 1, y + 1, w - 2, 1, hi)
        rect(a, x + 1, y + 1, 1, h - 2, hi)
        rect(a, x + 1, y + h - 2, w - 2, 1, lo)
        rect(a, x + w - 2, y + 1, 1, h - 2, lo)
        ink = (255, 255, 160) if (pressed and not on) else M_TXT
        return ink, M_SHD, 0
    rect(a, x, y, w, h, S_FACE)
    bx, by, bw, bh = x, y, w, h
    if default:
        bevel(a, x, y, w, h, M_BLK, M_BLK)
        bx, by, bw, bh = x + 1, y + 1, w - 2, h - 2
    if pressed:
        bevel(a, bx, by, bw, bh, S_LO, S_HI)
    else:
        bevel(a, bx, by, bw, bh, S_HI, S_LO)
    ink = S_ACC if (on or pressed) else S_TXT
    return ink, None, 1 if pressed else 0


def pthumb(a, x, y, w, h, selected, grip="v", tag="t"):
    """Slider thumbs: a raised VGUI button with a grip / a stone button (blue when held)."""
    if is_mc():
        pbutton(a, x, y, w, h, pressed=selected, tag=tag)
        return
    rect(a, x, y, w, h, S_FACE if not selected else (88, 100, 78))
    bevel(a, x, y, w, h, S_HI, S_LO)
    cx, cy = x + w // 2, y + h // 2
    if grip == "v":
        for gx in (cx - 2, cx, cx + 2):
            rect(a, gx, y + 3, 1, h - 6, S_HI)
            rect(a, gx + 1, y + 3, 1, h - 6, S_LO)
    else:
        for gy in (cy - 2, cy, cy + 2):
            rect(a, x + 3, gy, w - 6, 1, S_HI)
            rect(a, x + 3, gy + 1, w - 6, 1, S_LO)


def tri_r(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        rect(a, x, y + r, half - abs(r - half) + 1, 1, col)


def tri_l(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x + half + 1 - n, y + r, n, 1, col)


def pglyph(a, kind, cx, cy, col, small=False):
    """Pixel transport pictograms centred on (cx, cy)."""
    if small:
        if kind == "previous":
            rect(a, cx - 3, cy - 2, 1, 5, col); tri_l(a, cx - 2, cy - 2, 5, col); tri_l(a, cx + 1, cy - 2, 5, col)
        elif kind == "play":
            tri_r(a, cx - 1, cy - 3, 7, col)
        elif kind == "pause":
            rect(a, cx - 2, cy - 2, 2, 5, col); rect(a, cx + 1, cy - 2, 2, 5, col)
        elif kind == "stop":
            rect(a, cx - 2, cy - 2, 5, 5, col)
        elif kind == "next":
            tri_r(a, cx - 3, cy - 2, 5, col); tri_r(a, cx, cy - 2, 5, col); rect(a, cx + 3, cy - 2, 1, 5, col)
        elif kind == "eject":
            for r in range(3):
                rect(a, cx - r, cy - 3 + r, 2 * r + 1, 1, col)
            rect(a, cx - 2, cy + 1, 5, 1, col)
        return
    if kind == "previous":
        rect(a, cx - 6, cy - 3, 2, 7, col); tri_l(a, cx - 4, cy - 3, 7, col); tri_l(a, cx, cy - 3, 7, col)
    elif kind == "play":
        tri_r(a, cx - 2, cy - 4, 9, col)
    elif kind == "pause":
        rect(a, cx - 4, cy - 3, 3, 7, col); rect(a, cx + 1, cy - 3, 3, 7, col)
    elif kind == "stop":
        rect(a, cx - 3, cy - 3, 7, 7, col)
    elif kind == "next":
        tri_r(a, cx - 5, cy - 3, 7, col); tri_r(a, cx - 1, cy - 3, 7, col); rect(a, cx + 3, cy - 3, 2, 7, col)
    elif kind == "eject":
        for r in range(4):
            rect(a, cx - 1 - r, cy - 4 + r, 2 * r + 3, 1, col)
        rect(a, cx - 4, cy + 1, 9, 2, col)


def pmini_glyph(a, x, y, kind, col):
    if kind == "options":
        for r in range(3):
            rect(a, x + 2 + r, y + 3 + r, 5 - 2 * r, 1, col)
    elif kind == "minimize":
        rect(a, x + 2, y + 6, 5, 1, col)
    elif kind == "shade":
        rect(a, x + 2, y + 2, 5, 2, col)
    elif kind == "close":
        for i in range(5):
            px(a, x + 2 + i, y + 2 + i, col)
            px(a, x + 6 - i, y + 2 + i, col)


def pmini(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar buttons."""
    if is_mc():
        ink, shd, _ = pbutton(a, x, y, 9, 9, pressed=pressed, tag="mini")
        if not lit and not pressed:
            ink = (170, 170, 170)
        pmini_glyph(a, x, y, kind, ink)
        return
    rect(a, x, y, 9, 9, S_FACE)
    bevel(a, x, y, 9, 9, *((S_LO, S_HI) if pressed else (S_HI, S_LO)))
    o = 1 if pressed else 0
    pmini_glyph(a, x + o, y + o, kind, S_ACC if pressed else (S_TXT if lit else S_DIM))


def s04_tab(a, x, w, label, active, lit, top=2):
    """A VGUI property-sheet tab from row `top` to the bar's bottom; text on rows 4..10."""
    h = a.shape[0]
    if active:
        rect(a, x, top, w, h - top, S_FACE)
        rect(a, x, top, w - 1, 1, S_HI)
        rect(a, x, top, 1, h - top, S_HI)
        rect(a, x + w - 1, top + 1, 1, h - top - 1, S_LO)
        col = S_TXT if lit else S_DIM
    else:
        rect(a, x, top + 1, w, h - top - 2, S_DK)
        rect(a, x, top + 1, w - 1, 1, S_HI)
        rect(a, x, top + 1, 1, h - top - 2, S_HI)
        rect(a, x + w - 1, top + 2, 1, h - top - 3, S_LO)
        rect(a, x, h - 1, w, 1, S_HI)
        col = S_DIM if lit else S_DK2
    pt_c(a, VG, label, x + w / 2, 4, col)


S_DK2 = (120, 128, 112)


def mc_plate(a, x, w, rows=(3, 13)):
    """A name-tag plate (flat dark) from x for w columns, over rows rows[0]..rows[1]-1."""
    rect(a, x, rows[0], w, rows[1] - rows[0], M_PLATE)


def mc_wordmark(a, cx, y, lit):
    """MINECRAFT in stone capitals: an outline, a darker extrusion row, a light-to-dark stone face."""
    word = "MINECRAFT"
    w = pt_w(MC, word)
    x0 = int(round(cx - w / 2))
    m = np.zeros((a.shape[0], a.shape[1]), bool)
    xx = x0
    for ch in word:
        g = MC[ch]
        for r in range(7):
            for k, v in enumerate(g[r]):
                if v == "#":
                    m[y + r, xx + k] = True
        xx += len(g[0]) + 1
    ext = np.zeros_like(m)
    ext[1:] = m[:-1]
    ext &= ~m
    body = m | ext
    out = np.zeros_like(body)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            out |= np.roll(np.roll(body, dy, 0), dx, 1)
    out &= ~body
    a[out] = M_BLK
    a[ext] = (70, 70, 70) if lit else (50, 50, 50)
    rng = np.random.default_rng(seed("wordmark"))
    tops = [(236, 236, 236), (220, 220, 220), (204, 204, 204), (186, 186, 186), (168, 168, 168),
            (150, 150, 150), (132, 132, 132)]
    for (yy, xx_) in zip(*np.nonzero(m)):
        c = np.array(tops[yy - y]) + rng.integers(-9, 10)
        if not lit:
            c = c * 0.62
        a[yy, xx_] = np.round(c).astype(np.int32)


def steam_wordmark(a, x, y, col):
    for ch in "STEAM":
        bitmap(a, STEAM_WORD[ch], x, y, col)
        x += len(STEAM_WORD[ch][0]) + 1
    return x


# ------------------------------------------------------------------------------------------
# Pixel family: sheets
# ------------------------------------------------------------------------------------------

S04_TABS = ["Games", "Friends", "Servers", "Settings", "News"]


def p_main_titlebar(lit):
    a = pbar(275, 14, lit, f"main{lit}", baseline=False)
    bar_edges(a, True, True)
    if is_mc():
        mc_wordmark(a, 137, 3, lit)
    else:
        rect(a, 0, 13, 275, 1, S_FACE)
        steam_wordmark(a, 20, 4, S_TXT if lit else S_DIM)
        # an etched line runs on from the wordmark to the buttons, like the VGUI frame's title rule
        rect(a, 60, 7, 178, 1, S_LO)
        rect(a, 60, 8, 178, 1, S_HI)
    pmini(a, 6, 3, "options", lit)
    pmini(a, 244, 3, "minimize", lit)
    pmini(a, 254, 3, "shade", lit)
    pmini(a, 264, 3, "close", lit)
    return a


def p_eq_titlebar(lit):
    a = pbar(275, 14, lit, f"eq{lit}")
    bar_edges(a, True, True)
    if is_mc():
        w = pt_w(MC, "Equalizer") + 8
        mc_plate(a, 137 - w // 2, w, (2, 12))
        pt_c(a, MC, "Equalizer", 137, 4, M_TXT if lit else (160, 160, 160))
    else:
        x = 6
        for name in S04_TABS:
            w = pt_w(VG, name) + 10
            s04_tab(a, x, w, name, name == "Settings", lit)
            x += w + 1
        assert x < 260, x
    pmini(a, 264, 3, "close", lit)
    return a


def p_clutter(lit_letters):
    a = new(8, 43, T["bg"])
    if is_mc():
        mc_slot(a, 0, 0, 8, 43)
    else:
        bevel(a, 0, 0, 8, 43, S_LO, S_HI)
        rect(a, 1, 1, 6, 41, S_DK)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, M_XP_LO if is_mc() else (100, 96, 52))
        gy = y + (h - 5) // 2
        col = (255, 255, 255) if on else (M_LBL if is_mc() else S_DIM)
        ptext(a, TINY, letter, 2, gy, col)
    return a


def p_make_titlebar():
    a = new(344, 87, T["bg"])
    for kind, x in [("options", 0), ("minimize", 9), ("close", 18)]:
        for pressed, y in ((False, 0), (True, 9)):
            pmini(a, x, y, kind, True, pressed)
    for pressed, x in ((False, 0), (True, 9)):
        pmini(a, x, 18, "shade", True, pressed)
    a[0:14, 27:302] = p_main_titlebar(True)
    a[15:29, 27:302] = p_main_titlebar(False)
    a[29:43, 27:302] = p_main_titlebar(True)
    a[42:56, 27:302] = p_main_titlebar(False)
    unlit = p_clutter("")
    lit = p_clutter("OAIDV")
    a[0:43, 304:312] = unlit
    a[0:43, 312:320] = unlit
    for (letter, y, h), sx, sy in zip(CLUTTER_SLOTS, [304, 312, 320, 328, 336], [47, 55, 62, 69, 77]):
        a[sy:sy + h, sx:sx + 8] = lit[y:y + h]
    return a


def window_frame(a, h, top=14):
    """The body's outer edges below the titlebar (main and EQ windows, 275 wide)."""
    w = a.shape[1]
    if is_mc():
        rect(a, 0, top, 1, h - top, M_BLK)
        rect(a, w - 1, top, 1, h - top, M_BLK)
        rect(a, 0, h - 1, w, 1, M_BLK)
        rect(a, 1, top, w - 2, 1, M_HI)
        rect(a, 1, top, 1, h - top - 1, M_HI)
        rect(a, 1, h - 2, w - 2, 1, M_LO)
        rect(a, w - 2, top, 1, h - top - 1, M_LO)
    else:
        rect(a, 0, top, 1, h - top, S_HI)
        rect(a, w - 1, top, 1, h - top, S_LO)
        rect(a, 0, h - 1, w, 1, S_LO)


XP_ROWS = (74, 5)  # the XP bar / progress groove: main rows 74..78


def p_seek_rail(a):
    y, h = XP_ROWS
    if is_mc():
        rect(a, 16, y, 248, h, M_BLK)
        rect(a, 17, y + 1, 246, h - 2, (44, 44, 44))
        rect(a, 17, y + 1, 246, 1, (64, 64, 64))
        for i in range(1, 18):
            x = 16 + round(i * 248 / 18)
            rect(a, x, y + 1, 1, h - 2, (20, 20, 20))
    else:
        bevel(a, 16, y - 1, 248, h + 2, S_LO, S_HI)
        rect(a, 17, y, 246, h, S_DK)


def p_make_main():
    global MAIN_COL
    a = new(275, 116, T["bg"])
    a[0:14, :] = p_main_titlebar(True)
    window_frame(a, 116)
    a[22:65, 10:18] = p_clutter("")
    pdisplay(a, 21, 20, 84, 42)
    colon = M_XP if is_mc() else S_TXT
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, colon)
    pdisplay(a, 109, 21, 159, 15)
    pdisplay(a, 109, 40, 159, 14)
    ptext(a, TINY, "KBPS", 129, 44, T["text2"])
    ptext(a, TINY, "KHZ", 169, 44, T["text2"])
    p_seek_rail(a)
    if is_mc():
        # the hotbar behind the transport
        rect(a, 15, 87, 145, 20, (24, 24, 24))
        rect(a, 16, 88, 143, 18, (60, 60, 60))
    else:
        # VGUI group box round the transport, etched
        bevel(a, 13, 85, 148, 24, S_LO, S_HI)
        bevel(a, 14, 86, 146, 22, S_HI, S_LO)
    MAIN_COL = np.repeat(a[:, 30:31], 1, axis=1)
    size, lx, ly = LOGO
    put_logo(a, lx, ly, size)
    return a


def p_transport(kind, w, h, pressed):
    a = new(w, h, T["bg"])
    cx, cy = w // 2, h // 2
    if is_mc():
        # a hotbar slot; held down it gets the selected-slot frame
        rect(a, 0, 0, w, h, (24, 24, 24))
        rect(a, 1, 1, w - 2, h - 2, (150, 150, 150))
        rect(a, 2, 2, w - 4, h - 4, (96, 96, 96))
        rect(a, 2, 2, w - 4, 1, (70, 70, 70))
        if pressed:
            bevel(a, 0, 0, w, h, (255, 255, 255), (255, 255, 255))
            bevel(a, 1, 1, w - 2, h - 2, (200, 200, 200), (200, 200, 200))
        ink = M_XP if kind == "play" else (255, 255, 255)
        shd = M_XP_SHD if kind == "play" else (63, 63, 63)
        pglyph(a, kind, cx + 1, cy + 1, shd)
        pglyph(a, kind, cx, cy, ink)
        return a
    ink, _, o = pbutton(a, 0, 0, w, h, pressed=pressed, default=(kind == "play"))
    pglyph(a, kind, cx + o, cy + o, ink)
    return a


def p_make_cbuttons():
    a = new(136, 36, T["bg"])
    specs = [("previous", 0, 23), ("play", 23, 23), ("pause", 46, 23), ("stop", 69, 23), ("next", 92, 22)]
    for kind, x, w in specs:
        for pressed, y in ((False, 0), (True, 18)):
            a[y:y + 18, x:x + w] = p_transport(kind, w, 18, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        a[y:y + 16, 114:136] = p_transport("eject", 22, 16, pressed)
    return a


def p_make_shufrep():
    a = new(92, 85, T["bg"])
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        for kind, x0, w in (("repeat", 0, 28), ("shuffle", 28, 47)):
            ink, shd, o = pbutton(a, x0, y, w, 15, pressed=pressed, on=on, tag=kind)
            if not is_mc() and on:
                # a lit indicator, like the VGUI check mark
                rect(a, x0 + 3 + o, y + 6 + o, 2, 3, S_ACC)
            gx, gy = x0 + (w - 11) // 2 + o + (2 if not is_mc() and w == 28 else 0), y + 3 + o
            if shd:
                bitmap(a, PIX_ICONS[kind], gx + 1, gy + 1, shd)
            bitmap(a, PIX_ICONS[kind], gx, gy, ink)
    for x, txt, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        for on, y in ((False, 61), (True, 73)):
            cell = new(23, 12, T["bg"])
            ink, shd, o = pbutton(cell, 0, 0, 22, 12, pressed=pressed, on=on, tag="eqpl" + txt)
            fnt = MC if is_mc() else VG
            pt_c(cell, fnt, txt, 11 + o, 2 + o, ink, shd)
            a[y:y + 12, x:x + 23] = cell
    return a


def p_make_monoster():
    a = new(56, 24, T["panel"])
    for y, on in ((0, True), (12, False)):
        col = T["text"] if on else T["text3"]
        ptext_c(a, TINY, "STEREO", 14, y + 4, col)
        ptext_c(a, TINY, "MONO", 29 + 13, y + 4, col)
    return a


def p_make_playpaus():
    a = new(48, 9, T["panel"])
    play = M_XP if is_mc() else S_ACC
    tri_r(a, 2, 1, 7, play)
    rect(a, 9 + 2, 1, 2, 7, T["text"])
    rect(a, 9 + 5, 1, 2, 7, T["text"])
    rect(a, 18 + 2, 2, 5, 5, T["text"])
    rect(a, 39 + 1, 3, 1, 3, T["text3"])
    return a


def p_make_numbers(ex):
    a = new(108 if ex else 99, 13, T["panel"])
    ink, shd = (M_XP, M_XP_SHD) if is_mc() else (S_TXT, None)

    def big(rows, x0):
        for pass_, col in ((0, shd), (1, ink)):
            if col is None:
                continue
            o = 1 if pass_ == 0 else 0
            for r, row in enumerate(rows):
                for k, v in enumerate(row):
                    if v == "#":
                        rect(a, x0 + 2 * k + o, 2 * r + o, 2, 2, col)

    for n in range(10):
        big(BIGDIG[n], 9 * n)
    if ex:
        big(["....", "....", "####", "....", "....", "...."], 99)
    return a


def p_make_text():
    a = new(155, 18, T["panel"])
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            ptext(a, FONT5, key, col * 5, row * 6, T["text"])
    return a


def xp_orb(a, cx, cy, sel):
    for y in range(-3, 4):
        for x in range(-3, 4):
            d = (x * x + y * y) ** 0.5
            if d <= 3.2:
                col = (40, 96, 0) if d > 2.3 else ((230, 255, 140) if (x <= 0 and y <= 0 and d < 1.6)
                                                    else (176, 240, 40))
                if sel and d <= 2.3:
                    col = lerp(col, (255, 255, 200), 0.4)
                px(a, cx + x, cy + y, col)


def p_make_posbar(main):
    a = new(307, 10, T["bg"])
    a[0:10, 0:248] = main[72:82, 16:264]
    y0 = XP_ROWS[0] - 72
    for x0, sel in ((248, False), (278, True)):
        if is_mc():
            t = main[72:82, 100:129].copy()
            for x in range(23):
                tt = min(1.0, (x + 1) / 10)
                c = lerp((44, 44, 44), M_XP, tt)
                rect(t, x, y0 + 1, 1, 3, c)
                px(t, x, y0 + 1, lerp(c, M_XP_HI, 0.6))
                px(t, x, y0 + 3, lerp(c, M_XP_LO, 0.6))
            xp_orb(t, 25, 4, sel)
            a[0:10, x0:x0 + 29] = t
        else:
            t = new(29, 10, S_FACE)
            if sel:
                pbutton(t, 0, 0, 29, 10, pressed=True)
                for gx in (12, 14, 16):
                    rect(t, gx + 1, 3, 1, 5, S_ACC)
            else:
                pthumb(t, 0, 0, 29, 10, False)
            a[0:10, x0:x0 + 29] = t
    a[0:10, 277] = T["bg"]
    return a


HEART = [".##...##.", "#ww#.#rr#", "#wrr#rrr#", "#rrrrrrr#", ".#rrrrr#.", "..#rrr#..", "...#r#...",
         "....#...."]


def _shank():
    """The hunger bar's drumstick (9x9): a round joint of meat lower left, the bone up to the right."""
    g = [["."] * 9 for _ in range(9)]
    for y in range(9):
        for x in range(9):
            if (x - 3.2) ** 2 + (y - 5.3) ** 2 <= 2.9 ** 2:
                g[y][x] = "h" if (x - 2.3) ** 2 + (y - 4.4) ** 2 <= 1.1 else "m"
    for x, y in ((5, 3), (6, 2), (7, 1), (7, 0), (8, 1)):
        g[y][x] = "w"
    out = [r[:] for r in g]
    for y in range(9):
        for x in range(9):
            if g[y][x] == ".":
                if any(0 <= y + dy < 9 and 0 <= x + dx < 9 and g[y + dy][x + dx] != "."
                       for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0))):
                    out[y][x] = "#"
    return ["".join(r) for r in out]


SHANK = _shank()


def sprite(a, rows, x, y, pal, half=None):
    """Paints a pixel sprite; with half='L'/'R', only that half is 'full', the rest 'empty'."""
    for r, row in enumerate(rows):
        for k, v in enumerate(row):
            if v == ".":
                continue
            key = v
            if half is not None and v != "#":
                full = (k <= 4) if half == "L" else (k >= 4)
                key = v if full else "e"
            px(a, x + k, y + r, pal[key])


HEART_PAL = {"#": (0, 0, 0), "w": (255, 190, 190), "r": (218, 22, 22), "e": (60, 60, 60)}
HEART_EMPTY = {"#": (0, 0, 0), "w": (60, 60, 60), "r": (60, 60, 60), "e": (60, 60, 60)}
SHANK_PAL = {"#": (0, 0, 0), "w": (236, 228, 212), "m": (176, 96, 40), "h": (226, 150, 80), "e": (60, 60, 60)}
SHANK_EMPTY = {"#": (0, 0, 0), "w": (60, 60, 60), "m": (60, 60, 60), "h": (60, 60, 60), "e": (60, 60, 60)}


def p_slider_thumbs(a):
    for x, sel in ((0, True), (15, False)):
        t = new(14, 11, T["bg"])
        pthumb(t, 0, 0, 14, 11, sel, tag="vol")
        a[422:433, x:x + 14] = t


def p_make_volume():
    a = new(68, 433, T["bg"])
    for i in range(28):
        y = i * 15
        level = (i + 1) / 28
        if is_mc():
            halves = round(level * 16)
            for k in range(8):
                hx = 2 + 8 * k
                if halves >= 2 * k + 2:
                    sprite(a, HEART, hx, y + 3, HEART_PAL)
                elif halves == 2 * k + 1:
                    sprite(a, HEART, hx, y + 3, HEART_PAL, half="L")
                else:
                    sprite(a, HEART, hx, y + 3, HEART_EMPTY)
        else:
            bevel(a, 2, y + 3, 64, 8, S_LO, S_HI)
            rect(a, 3, y + 4, 62, 6, S_DK)
            n = round(level * 15)
            for k in range(n):
                rect(a, 4 + 4 * k, y + 5, 3, 4, S_ACC)
    p_slider_thumbs(a)
    return a


def p_make_balance():
    a = new(68, 433, T["bg"])
    for i in range(28):
        y = i * 15
        t = i / 27
        if is_mc():
            gone = round(4 * t)  # halves emptied from each end, full at the centre
            for k in range(4):
                hx = 11 + 8 * k
                lo_half, hi_half = 2 * k, 2 * k + 1  # half-slots 0..7 left to right
                empty_l = lo_half < gone or lo_half >= 8 - gone
                empty_r = hi_half < gone or hi_half >= 8 - gone
                if empty_l and empty_r:
                    sprite(a, SHANK, hx, y + 2, SHANK_EMPTY)
                elif empty_l:
                    sprite(a, SHANK, hx, y + 2, SHANK_PAL, half="R")
                elif empty_r:
                    sprite(a, SHANK, hx, y + 2, SHANK_PAL, half="L")
                else:
                    sprite(a, SHANK, hx, y + 2, SHANK_PAL)
        else:
            bevel(a, 11, y + 3, 36, 8, S_LO, S_HI)
            rect(a, 12, y + 4, 34, 6, S_DK)
            reach = 1 + round(15 * (1 - t))
            rect(a, 29 - reach, y + 5, 2 * reach - 1, 4, S_ACC)
            rect(a, 28, y + 2, 1, 1, S_HI)
    p_slider_thumbs(a)
    return a


def p_eq_slider_frame(a, x, y, n):
    rect(a, x, y, 14, 63, T["bg"])
    v = n / 27
    centre = int(round((1 - v) * 51 + 6))
    zero = 31
    lo_, hi_ = sorted((centre, zero))
    if is_mc():
        mc_slot(a, x + 4, y + 1, 6, 61)
        rect(a, x + 5, y + 2, 4, 59, (100, 100, 100))
        rect(a, x + 5, y + lo_, 4, hi_ - lo_ + 1, M_XP)
        rect(a, x + 5, y + lo_, 1, hi_ - lo_ + 1, M_XP_HI)
        rect(a, x + 8, y + lo_, 1, hi_ - lo_ + 1, M_XP_LO)
        rect(a, x + 1, y + zero, 2, 1, M_LBL)
        rect(a, x + 11, y + zero, 2, 1, M_LBL)
    else:
        bevel(a, x + 4, y + 1, 6, 61, S_LO, S_HI)
        rect(a, x + 5, y + 2, 4, 59, S_DK)
        for r in range(lo_, hi_ + 1):
            if (r - zero) % 3 != 2:
                rect(a, x + 5, y + r, 4, 1, S_ACC)
        rect(a, x + 1, y + zero, 2, 1, S_HI)
        rect(a, x + 11, y + zero, 2, 1, S_HI)


def p_make_eqmain():
    a = new(275, 315, T["bg"])
    a[0:14, :] = p_eq_titlebar(True)
    win = a[0:116].copy()
    window_frame(win, 116)
    a[0:116] = win
    pdisplay(a, 86, 17, 113, 19)
    lbl = M_LBL if is_mc() else S_DIM
    if not is_mc():
        bevel(a, 15, 36, 247, 69, S_LO, S_HI)
        bevel(a, 16, 37, 245, 67, S_HI, S_LO)
    for t_, yy in (("+12DB", 41), ("+0DB", 67), ("-12DB", 92)):
        ptext_c(a, TINY, t_, 58, yy, lbl)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        p_eq_slider_frame(a, x, 38, 14)
    ptext_c(a, TINY, "PREAMP", 28, 106, lbl)
    for i, t_ in enumerate(EQ_BANDS):
        ptext_c(a, TINY, t_, 78 + 18 * i + 7, 106, lbl)
    # under the window
    pmini(a, 0, 125, "close", True, pressed=True)
    fnt = MC if is_mc() else VG
    for x, txt, on, pressed in [
        (10, "On", False, False), (36, "Auto", False, False), (69, "On", True, False), (95, "Auto", True, False),
        (128, "On", False, True), (154, "Auto", False, True), (187, "On", True, True), (213, "Auto", True, True),
    ]:
        w = 26 if txt == "On" else 32
        ink, shd, o = pbutton(a, x, 119, w, 12, pressed=pressed, on=on, tag="eqbtn" + txt)
        pt_c(a, fnt, txt, x + w / 2 + o, 121 + o, ink, shd)
    a[134:148, :] = p_eq_titlebar(True)
    a[149:163, :] = p_eq_titlebar(False)
    for y, sel in ((164, False), (176, True)):
        pthumb(a, 0, y, 11, 11, sel, grip="h", tag="eqthumb")
    for n in range(28):
        p_eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        ink, shd, o = pbutton(a, 224, y, 44, 12, pressed=pressed, tag="presets")
        pt_c(a, fnt, "Presets", 246 + o, y + 2 + o, ink, shd)
    # graph
    rect(a, 0, 294, 113, 19, T["panel"])
    grid = (36, 36, 36) if is_mc() else (74, 84, 66)
    rect(a, 0, 294 + 9, 113, 1, grid)
    for x in range(0, 113, 12):
        for y in range(0, 19, 3):
            px(a, x, 294 + y, grid)
    line = M_XP if is_mc() else S_ACC
    for r in range(19):
        px(a, 115, 294 + r, line)
    for x in range(113):
        px(a, x, 314, T["text3"] if x % 3 != 2 else T["panel"])
    return a


def p_side_left(w, h):
    t = new(w, h, T["bg"])
    if is_mc():
        rect(t, 0, 0, 1, h, M_BLK)
        rect(t, 1, 0, 1, h, M_HI)
        rect(t, w - 1, 0, 1, h, M_SLOT_D)
    else:
        rect(t, 0, 0, 1, h, S_HI)
        rect(t, w - 1, 0, 1, h, S_LO)
    return t


def p_side_right(w, h, groove=None):
    t = new(w, h, T["bg"])
    if is_mc():
        rect(t, 0, 0, 1, h, M_HI)
        rect(t, w - 2, 0, 1, h, M_LO)
        rect(t, w - 1, 0, 1, h, M_BLK)
        if groove:
            g0, gw = groove
            rect(t, g0, 0, gw, h, M_SLOT)
            rect(t, g0, 0, 1, h, M_SLOT_D)
            rect(t, g0 + gw - 1, 0, 1, h, M_HI)
    else:
        rect(t, 0, 0, 1, h, S_HI)
        rect(t, w - 1, 0, 1, h, S_LO)
        if groove:
            g0, gw = groove
            rect(t, g0, 0, gw, h, S_DK)
            rect(t, g0, 0, 1, h, S_LO)
            rect(t, g0 + gw - 1, 0, 1, h, S_HI)
    return t


def p_bottom(w, h, left=False, right=False):
    t = new(w, h, T["bg"])
    if is_mc():
        rect(t, 0, 0, w, 1, M_HI)
        rect(t, 0, h - 1, w, 1, M_BLK)
        rect(t, 0, h - 2, w, 1, M_LO)
        if left:
            rect(t, 0, 0, 1, h, M_BLK)
            rect(t, 1, 0, 1, h - 1, M_HI)
        if right:
            rect(t, w - 1, 0, 1, h, M_BLK)
            rect(t, w - 2, 0, 1, h - 1, M_LO)
    else:
        rect(t, 0, 0, w, 1, S_HI)
        rect(t, 0, h - 1, w, 1, S_LO)
        if left:
            rect(t, 0, 0, 1, h, S_HI)
        if right:
            rect(t, w - 1, 0, 1, h, S_LO)
    return t


def p_grip(t, x, y, n):
    col = M_LO if is_mc() else S_HI
    sh = M_HI if is_mc() else S_LO
    for k in range(n):
        for j in range(k + 1):
            gx, gy = x - 3 * k + 3 * j, y - 3 * j
            px(t, gx, gy, col)
            px(t, gx + 1, gy + 1, sh)


def p_make_pledit():
    a = new(280, 186, T["bg"])
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = pbar(25, 20, lit, f"pltile{lit}")
        t = pbar(25, 20, lit, f"plleft{lit}")
        bar_edges(t, left=True)
        a[y:y + 20, 0:25] = t
        t = pbar(100, 20, lit, f"pltitle{lit}")
        if is_mc():
            w = pt_w(MC, "Playlist") + 8
            mc_plate(t, 50 - w // 2, w)
            pt_c(t, MC, "Playlist", 50, 4, M_TXT if lit else (160, 160, 160))
        else:
            w = pt_w(VG, "Games") + 12
            s04_tab(t, 50 - w // 2, w, "Games", True, lit)
        a[y:y + 20, 26:126] = t
        t = pbar(25, 20, lit, f"plright{lit}")
        bar_edges(t, right=True)
        pmini(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t
    a[42:71, 0:12] = p_side_left(12, 29)
    a[42:71, 31:51] = p_side_right(20, 29, groove=(4, 10))
    pmini(a, 52, 42, "close", True, pressed=True)
    for x, sel in ((52, False), (61, True)):
        t = new(8, 18, T["bg"])
        pthumb(t, 0, 0, 8, 18, sel, grip="h", tag="scroll")
        a[53:71, x:x + 8] = t

    fnt = MC if is_mc() else VG
    t = p_bottom(125, 38, left=True)
    for bx, lbl in ((14, "Add"), (43, "Rem"), (72, "Sel"), (101, "Misc")):
        ink, shd, o = pbutton(t, bx, 8, 22, 18, tag="plb" + lbl)
        pt_c(t, fnt, lbl, bx + 11 + o, 13 + o - (1 if is_mc() else 0), ink, shd)
    a[72:110, 0:125] = t

    t = p_bottom(150, 38, right=True)
    pdisplay(t, 6, 9, 56, 8)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        col = M_LBL if is_mc() else S_TXT
        pglyph(t, kind, bx + 5, 27, col, small=True)
    pdisplay(t, 65, 22, 33, 8)
    rect(t, 84, 24, 1, 1, T["text2"])
    rect(t, 84, 27, 1, 1, T["text2"])
    ink, shd, o = pbutton(t, 106, 8, 22, 18, tag="pllist")
    pt_c(t, fnt, "List", 117 + o, 13 + o - (1 if is_mc() else 0), ink, shd)
    p_grip(t, 145, 33, 4)
    a[72:110, 126:276] = t
    a[0:38, 179:204] = p_bottom(25, 38)
    return a


def p_gen_letter_cells(lit):
    fnt = MC if is_mc() else VG
    bg = M_PLATE if is_mc() else S_FACE
    col = (M_TXT if lit else (160, 160, 160)) if is_mc() else (S_TXT if lit else S_DIM)
    cells = []
    for c in GEN_LETTERS:
        g = fnt[c]
        w = len(g[0]) + 1
        cell = new(w, 7, bg)
        bitmap(cell, g[:7], 0, 0, col)
        cells.append(cell)
    return cells


def p_make_gen():
    a = new(194, 109, T["bg"])
    for lit, y in ((True, 0), (False, 21)):
        def piece(x0, fn):
            t = pbar(25, 20, lit, f"gen{x0}{lit}")
            fn(t)
            a[y:y + 20, x0:x0 + 25] = t

        def left(t):
            bar_edges(t, left=True)

        def left_end(t):
            if is_mc():
                mc_plate(t, 21, 4)
            else:
                rect(t, 20, 2, 5, 18, S_FACE)
                rect(t, 20, 2, 5, 1, S_HI)
                rect(t, 20, 2, 1, 18, S_HI)

        def centre(t):
            if is_mc():
                mc_plate(t, 0, 25)
            else:
                rect(t, 0, 2, 25, 18, S_FACE)
                rect(t, 0, 2, 25, 1, S_HI)

        def right_end(t):
            if is_mc():
                mc_plate(t, 0, 4)
            else:
                rect(t, 0, 2, 5, 18, S_FACE)
                rect(t, 0, 2, 4, 1, S_HI)
                rect(t, 4, 3, 1, 17, S_LO)

        def fill(t):
            pass

        def right(t):
            bar_edges(t, right=True)
            pmini(t, 14, 3, "close", lit)

        piece(0, left)
        piece(26, left_end)
        piece(52, centre)
        piece(78, right_end)
        piece(104, fill)
        piece(130, right)

    a[42:56, 0:125] = p_bottom(125, 14, left=True)
    t = p_bottom(125, 14, right=True)
    p_grip(t, 120, 9, 3)
    a[57:71, 0:125] = t
    a[72:86, 127:152] = p_bottom(25, 14)
    a[42:71, 127:138] = p_side_left(11, 29)
    a[42:66, 158:169] = p_side_left(11, 24)
    for x0, h in ((139, 29), (170, 24)):
        t = p_side_right(8, h)
        t[:, 0] = T["bg"]
        a[42:42 + h, x0:x0 + 8] = t
    pmini(a, 148, 42, "close", True, pressed=True)
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for cell in p_gen_letter_cells(lit):
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
    light = is_light()
    return [
        pl["NormalBG"],                                     # item background
        pl["Normal"],                                       # item text
        T["bg"],                                            # window background
        T["btn_fg"],                                        # button text
        T.get("win_text", T["text"]),                       # window text
        lerp(T["bg"], T["text"], 0.15),                     # dividers, sunken borders
        pl["SelectedBG"],                                   # selection bar
        T["panel"],                                         # list header background
        T["text2"],                                         # list header text
        lerp(T["panel"], (255, 255, 255) if not light else T["text"], 0.12),  # header frame, light
        lerp(T["panel"], (0, 0, 0), 0.3),                   # header frame, dark
        T["accent"],                                        # header frame, pressed
        T["bg"],                                            # header dead area
        T["panel"],                                         # scrollbar
        T["text3"],                                         # scrollbar 2
        T["btn_pressed"],                                   # scrollbar pressed
        T["text2"],                                         # scrollbar pressed 2
        T["bg"],                                            # scrollbar dead area
    ]


def make_genex():
    a = new(256, 64, T["bg"])
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    for y, pressed in ((1, False), (16, True)):
        cell = new(47, 15, T["bg"])
        rrect(cell, 0, 0, 47, 15, 4, T["btn_pressed"] if pressed else T["btn"])
        a[y:y + 15, 0:47] = cell
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    p = T["panel"]
    stops = T["vis"]
    out = [(p, "background"), (lerp(p, T["text"], 0.05), "dots")]
    for i in range(16):
        out.append((ramp(stops, i / 15), f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}"))
    for i in range(5):
        out.append((ramp(stops[:3], i / 4), f"oscilloscope {i + 1}"))
    out.append((T["text"], "peaks"))
    return out


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    pl = T["pl"]
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={pl['Normal']}\nCurrent={pl['Current']}\nNormalBG={pl['NormalBG']}\n"
                f"SelectedBG={pl['SelectedBG']}\nMbBG={pl['NormalBG']}\nMbFG={pl['Normal']}\nFont=Arial\n")
    n, s, c = T["name"], T["service"], T["company"]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{n} — a skin in the style of {s}. {s} logo © {c}.\n\n"
            f"A classic (Winamp 2.x format) skin, generated by a script (gen_skin.py); everything\n"
            f"but the logo is drawn from code.\n"
        )


# ------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------

SHEETS = {}


def build():
    SHEETS.clear()
    if T["style"] == "pixel":
        main = p_make_main()
        sheets = {
            "main.bmp": main,
            "titlebar.bmp": p_make_titlebar(),
            "cbuttons.bmp": p_make_cbuttons(),
            "shufrep.bmp": p_make_shufrep(),
            "posbar.bmp": p_make_posbar(main),
            "volume.bmp": p_make_volume(),
            "balance.bmp": p_make_balance(),
            "monoster.bmp": p_make_monoster(),
            "playpaus.bmp": p_make_playpaus(),
            "numbers.bmp": p_make_numbers(False),
            "nums_ex.bmp": p_make_numbers(True),
            "text.bmp": p_make_text(),
            "pledit.bmp": p_make_pledit(),
            "eqmain.bmp": p_make_eqmain(),
            "gen.bmp": p_make_gen(),
            "genex.bmp": make_genex(),
        }
        return finish(sheets)
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
    return finish(sheets)


def finish(sheets):
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


def draw_bitmap_text(dst, s, x, y):
    text = SHEETS["text"]
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, text, (col * 5, row * 6, 5, 6), x, y)
        x += 5


def text_ink():
    """text.bmp's ink as the app takes it (marquee.js textInk): the commonest colour in the letter
    and digit rows clearly unlike the space cell's; pledit's Normal if there's none."""
    a = np.asarray(SHEETS["text"], dtype=np.int32)[0:12, 0:155]
    bg = a[0, 150]
    far = np.abs(a - bg).sum(-1) >= 96
    if not far.any():
        return hexc(T["pl"]["Normal"])
    cols, counts = np.unique(a[far].reshape(-1, 3), axis=0, return_counts=True)
    return tuple(int(v) for v in cols[counts.argmax()])


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
    # title: text.bmp's space across the box, then the title in TrueType in pledit's Normal colour
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(LIBERATION, 11)
    tmp = img.crop((111, 22, 265, 36))
    dt = ImageDraw.Draw(tmp)
    dt.text((0, 29 - 22), state["title"], fill=text_ink(), font=f, anchor="lm")
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
    # a stand-in picture: a gradient in the theme's accents
    pw, ph = w - 22, h - 34
    yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
    t = (xx / pw * 0.4 + yy / ph * 0.6)[..., None]
    c0, c1 = np.array(T["vis"][0], np.float32), np.array(T["vis"][3], np.float32)
    pic = c0 * (1 - t) + c1 * t
    img.paste(Image.fromarray(pic.astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("Night Drive - Copper Wire", "4:12"), ("Slow Burn - Lantern Hours", "3:47"),
            ("Kiln - Second Firing", "5:03"), ("Ash & Smoke - Afterglow", "2:58"),
            ("Ember Trio - Coal Seam", "6:21"), ("Field Notes - Warm Static", "3:33"),
            ("Tinder - Small Hours", "4:40"), ("The Forge - Bellows", "3:09"),
            ("Hearth - Long Winter", "5:51"), ("Glowworm - Low Light", "4:05"),
            ("Foundry - Pour", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=f"{T['name']} - a skin in that style", bars=bars)
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
    # the title box in main.bmp is the panel colour too (where the app's TrueType title sits)
    m = np.asarray(S["main"])
    box = m[22:35, 111:265]
    assert (box == np.array(T["panel"], np.uint8)).all(), "title box not flat"
    ink = text_ink()
    assert sum(abs(ink[i] - T["panel"][i]) for i in range(3)) >= 300, ("title ink too faint", ink)


if __name__ == "__main__":
    if "--list" in sys.argv:
        print("\n".join(THEMES))
        sys.exit(0)
    keys = sys.argv[1:] or list(THEMES)
    for key in keys:
        if key not in THEMES:
            sys.exit(f"unknown theme {key!r}; one of {', '.join(THEMES)}")
        setup_theme(key)
        names = build()
        check()
        preview()
        print(f"{key}: {T['wsz']}.wsz, preview-{key}.png, out/{key}/ ({len(names)} files)")
