#!/usr/bin/python3
"""Nintendo: classic Winamp 2.x skins in the style of five Nintendo consoles and their menus.

One procedural generator, one theme per skin:

  ds      Nintendo DS Lite (Polar White) and the DS menu: the white gloss shell, the clamshell
          (main window = top screen, equalizer = bottom touch screen with the D-pad and ABXY
          either side), graph-paper screens, crisp pixel lettering, blue-cyan accents, the menu
          clock.
  dsi     Nintendo DSi (matte black) and DSi Sound: the menu's horizontal strip of icon tiles as
          the transport, white screens, an orange "Sound" accent, the inner camera, a little
          bird in headphones.
  3ds     Nintendo 3DS (Aqua Blue) and its HOME Menu: the soft top-screen gradient, the bottom
          screen's grid of app slots, glossy icon tiles, the circle pad, the 3D depth slider.
  wii     the Wii Menu: white with fine grey stripes, channel-tile frames, the #34beed accent,
          Wii Remote buttons, the curved bottom bar with its round Wii button, hand-drawn bubbly
          lettering.
  switch  Nintendo Switch HOME menu (Basic Black) between neon blue and neon red Joy-Cons, round
          HOME-menu buttons for the transport, the cyan selection ring.

Everything is drawn here from code, except the logos (source/logo-*/logo.svg, rasterised with
rsvg-convert): the DS and DSi wordmarks, the 3DS and Switch icons, the Wii logo.

    /usr/bin/python3 -I gen_skin.py              # every theme
    /usr/bin/python3 -I gen_skin.py wii ds       # just these
    /usr/bin/python3 -I gen_skin.py --list       # the theme names

Writes out/<theme>/*.bmp + text files, <Name>.wsz and preview-<theme>.png beside this file.
Built on skins/ember/gen_skin.py's sheet layouts and preview, by way of private-repo/skins/games/consoles/
(its anti-aliased helpers). Private use only.
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

NOTO = ("/usr/share/fonts/google-noto/NotoSans-{}.ttf", 0)
OPEN = "/usr/share/fonts/open-sans/OpenSans-{}.ttf"
WQY = ("/usr/share/fonts/wqy-zenhei-fonts/wqy-zenhei.ttc", 1)  # WenQuanYi Zen Hei Sharp: bitmap strikes
LIBERATION = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"


def noto(w):
    return (NOTO[0].format(w), 0)


def opens(w):
    return (OPEN.format(w), 0)


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------
# shell: the body (clamshells) or menu background; screen: the screens' insides; bezel: the dark
# ring round a screen; panel/panel_line: the displays (text.bmp's background too); ink: text.bmp's
# letters (so the app's title); text2: labels; accent: selection, fills; glyph: button pictograms;
# btn: the transport's style; knob_line: thumbs' outline; bar: titlebar stops (focused, unfocused).

THEMES = {
    "ds": dict(
        style="ds", name="Nintendo DS", wsz="Nintendo-DS", owner="Nintendo",
        subject="the Nintendo DS Lite and its DS menu", logo="logo-nintendods", logo_url=
        "https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/nintendods.svg", mark="Nintendo DS logo",
        title=None, eq_title="Equalizer", pl_title="Playlist", gen_title="ALBUM ART",
        font=WQY, crisp=True, title_size=11, digit_font=WQY, digit_size=16,
        shell="#f4f6f8", shell_line="#aab2bb", screen="#f6f8fa", grid="#dfe6ee", bezel="#3d4249",
        panel="#ffffff", panel_line="#8ccbee", ink="#283442", text2="#7a8794", accent="#18a6e6",
        accent_dk="#0a78c2", glyph="#4f5c69", track="#d5dde5", knob_line="#8995a2",
        bar=(("#ffffff", "#f1f4f7", "#dfe5eb", "#a8b2bd"), ("#fbfcfd", "#f3f5f7", "#e9edf1", "#c3cad1")),
        title_fg="#3a4552", title_dim="#a3acb6", bar_icon="#5a6673", bar_icon_dim="#b0b8c0",
        pl=dict(NormalBG="#FFFFFF", Normal="#283442", Current="#0A8AD6", SelectedBG="#CDEBFA"),
        vis=["#bfeaff", "#5cc6f2", "#18a6e6", "#0a6fb4"],
    ),
    "dsi": dict(
        style="dsi", name="Nintendo DSi", wsz="Nintendo-DSi", owner="Nintendo",
        subject="the Nintendo DSi and DSi Sound", logo="logo-nintendodsi", logo_url=
        "https://upload.wikimedia.org/wikipedia/commons/d/dd/Nintendo_DSi_logo.svg", mark="Nintendo DSi logo",
        title="Sound", eq_title="Equalizer", pl_title="Playlist", gen_title="ALBUM ART",
        font=noto("SemiBold"), crisp=False, title_size=9, digit_font=noto("SemiBold"), digit_size=14,
        shell="#232426", shell_line="#050505", screen="#f2f3f4", grid="#e3e5e7", bezel="#0b0b0c",
        panel="#ffffff", panel_line="#b9bec3", ink="#2e3134", text2="#8a8f94", accent="#f39200",
        accent_dk="#d06a00", glyph="#4a4e53", track="#d8dbde", knob_line="#7d8288",
        bar=(("#4a4b4e", "#323336", "#1e1f21", "#0a0a0b"), ("#3a3b3d", "#2e2f31", "#252628", "#111112")),
        title_fg="#ffffff", title_dim="#8a8c90", bar_icon="#e2e3e5", bar_icon_dim="#77797d",
        pl=dict(NormalBG="#FFFFFF", Normal="#2E3134", Current="#D96F00", SelectedBG="#FFE3BD"),
        vis=["#ffd27a", "#ffab2e", "#f39200", "#c05a00"],
    ),
    "3ds": dict(
        style="3ds", name="Nintendo 3DS", wsz="Nintendo-3DS", owner="Nintendo",
        subject="the Nintendo 3DS (Aqua Blue) and its HOME Menu", logo="logo-nintendo3ds", logo_url=
        "https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/nintendo3ds.svg", mark="Nintendo 3DS mark",
        title="Nintendo 3DS Sound", eq_title="Equalizer", pl_title="Playlist", gen_title="ALBUM ART",
        font=noto("SemiBold"), crisp=False, title_size=9, digit_font=noto("Medium"), digit_size=14,
        shell="#3db4c7", shell_line="#17707f", screen="#f3f5f7", grid="#e1e6eb", bezel="#121416",
        panel="#ffffff", panel_line="#bcc4cc", ink="#363c43", text2="#87919b", accent="#22a3ea",
        accent_dk="#0b78c4", glyph="#4c565f", track="#d6dce2", knob_line="#5f8f99",
        bar=(("#a8e6ef", "#62c9d8", "#38afc2", "#1a7f8f"), ("#b9dfe5", "#8fc9d2", "#79b8c2", "#4c8f9a")),
        title_fg="#ffffff", title_dim="#e2f1f4", bar_icon="#ffffff", bar_icon_dim="#d5ecf0",
        pl=dict(NormalBG="#FFFFFF", Normal="#363C43", Current="#0E86D2", SelectedBG="#D3EDFC"),
        vis=["#b8e6ff", "#5cc4f5", "#22a3ea", "#0b6fb8"],
    ),
    "wii": dict(
        style="wii", name="Wii", wsz="Wii", owner="Nintendo",
        subject="the Wii Menu", logo="logo-wii", logo_url=
        "https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/wii.svg", mark="Wii logo",
        title="Wii Menu", eq_title="Equalizer", pl_title="Playlist", gen_title="ALBUM ART",
        font=("/usr/share/fonts/aajohan-comfortaa-fonts/Comfortaa-Bold.otf", 0), crisp=False, title_size=9,
        digit_font=("/usr/share/fonts/aajohan-comfortaa-fonts/Comfortaa-Bold.otf", 0), digit_size=13,
        shell="#fafafa", shell_line="#c9c9c9", screen="#fafafa", grid="#ececec", bezel="#c9c9c9",
        panel="#ffffff", panel_line="#cfcfcf", ink="#4f4f4f", text2="#a0a0a0", accent="#34beed",
        accent_dk="#1a9ccc", glyph="#8a8a8a", track="#dedede", knob_line="#b5b5b5",
        bar=(("#ffffff", "#fdfdfd", "#efefef", "#d0d0d0"), ("#ffffff", "#fafafa", "#f2f2f2", "#dadada")),
        title_fg="#8c8c8c", title_dim="#c4c4c4", bar_icon="#9a9a9a", bar_icon_dim="#cdcdcd",
        pl=dict(NormalBG="#FFFFFF", Normal="#4F4F4F", Current="#1AA6DC", SelectedBG="#D6F1FB"),
        vis=["#bdeeff", "#6fd3f5", "#34beed", "#1590c0"],
    ),
    "switch": dict(
        style="switch", name="Nintendo Switch", wsz="Nintendo-Switch", owner="Nintendo",
        subject="the Nintendo Switch HOME menu (Basic Black) and its neon Joy-Con",
        logo="logo-nintendoswitch", logo_url="https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/"
        "nintendoswitch.svg", mark="Nintendo Switch logo",
        title="Nintendo Switch", eq_title="Equalizer", pl_title="Playlist", gen_title="ALBUM ART",
        font=opens("Semibold"), crisp=False, title_size=9, digit_font=opens("Regular"), digit_size=14,
        shell="#2d2d2d", shell_line="#111111", screen="#2d2d2d", grid="#353535", bezel="#0e0e0e",
        panel="#1f1f1f", panel_line="#4b4b4b", ink="#ffffff", text2="#9a9a9a", accent="#00c3e3",
        accent_dk="#00a0c0", glyph="#ffffff", track="#555555", knob_line="#bdbdbd",
        bar=(("#3a3a3a", "#2f2f2f", "#2b2b2b", "#454545"), ("#333333", "#2d2d2d", "#2a2a2a", "#3c3c3c")),
        title_fg="#ffffff", title_dim="#8a8a8a", bar_icon="#e6e6e6", bar_icon_dim="#7a7a7a",
        pl=dict(NormalBG="#2D2D2D", Normal="#FFFFFF", Current="#00C3E3", SelectedBG="#3E5560"),
        vis=["#9ff4ff", "#3fdcf2", "#00c3e3", "#0088aa"],
    ),
}

JOY_L = (10, 185, 230)   # neon blue #0ab9e6
JOY_R = (255, 60, 40)    # neon red #ff3c28
JOY_W = 4                # Joy-Con strip width on every Switch window side

T = {}


def setup_theme(key):
    global T, OUT
    raw = dict(THEMES[key])
    raw["key"] = key
    for k, v in list(raw.items()):
        if isinstance(v, str) and v.startswith("#") and len(v) == 7:
            raw[k] = hexc(v)
    raw["vis"] = [hexc(c) for c in raw["vis"]]
    raw["bar"] = tuple(tuple(hexc(c) for c in stops) for stops in raw["bar"])
    T = raw
    OUT = os.path.join(OUT_ROOT, key)
    os.makedirs(OUT, exist_ok=True)


def ST():
    return T["style"]


def CLAM():
    return T["style"] in ("ds", "dsi", "3ds")


def SW():
    return T["style"] == "switch"


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def is_light():
    return sum(T["shell"]) > 384


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
# Pixel fonts for text.bmp and the small labels
# ------------------------------------------------------------------------------------------

def text_width(s, f):
    return f.getlength(s)


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
        if T.get("skip") == "double":
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



# ------------------------------------------------------------------------------------------
# Extra drawing helpers: gradients, glossy shapes, the XMB wave, spaced lettering
# ------------------------------------------------------------------------------------------


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
    """(h, w, 3) float colour array, a vertical gradient (for paint's per-pixel colours)."""
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
    # the gradient spans the disc itself, not the padded box
    t = np.clip((np.arange(h, dtype=np.float32) + y0 + 0.5 - (cy - r)) / (2 * r), 0, 1)[:, None, None]
    col = np.repeat(np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t, w, axis=1)
    paint(a, x0, y0, m, col, alpha)


def ellipse(a, cx, cy, rx, ry, col, alpha=1.0):
    x0, y0 = int(np.floor(cx - rx)) - 1, int(np.floor(cy - ry)) - 1
    w, h = int(np.ceil(2 * rx)) + 3, int(np.ceil(2 * ry)) + 3
    m = mask(w, h, lambda d, S: d.ellipse(((cx - rx - x0) * S, (cy - ry - y0) * S, (cx + rx - x0) * S - 1,
                                           (cy + ry - y0) * S - 1), fill=255))
    paint(a, x0, y0, m, col, alpha)


def ttext_sp(a, s, f, cx, base, col, sp=1.0, alpha=1.0):
    """Letter-spaced TrueType text centred on cx."""
    widths = [f.getlength(c) for c in s]
    total = sum(widths) + sp * (len(s) - 1)
    x = cx - total / 2
    for c, w in zip(s, widths):
        if c != " ":
            ttext(a, c, f, x, base, col, alpha=alpha)
        x += w + sp



# ------------------------------------------------------------------------------------------
# Lettering: TrueType (smooth, or crisp from a bitmap strike), and the Wii's drawn stroke type
# ------------------------------------------------------------------------------------------

_fonts = {}


def font(spec, size):
    key = (spec, size)
    if key not in _fonts:
        path, idx = spec
        _fonts[key] = ImageFont.truetype(path, size, index=idx)
    return _fonts[key]


def ttext(a, s, f, x, base, col, align="l", alpha=1.0, crisp=False):
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
    d = ImageDraw.Draw(im)
    if crisp:
        d.fontmode = "1"
    d.text((-l + 1, -t + 1), s, font=f, fill=255, anchor="ls")
    m = np.asarray(im, dtype=np.float32) / 255.0
    paint(a, x + l - 1, base + t - 1, m, col, alpha)


def tt(a, s, x, base, col, size=None, align="l", alpha=1.0):
    """Theme lettering: the theme's face (crisp for the DS)."""
    size = size or T["title_size"]
    ttext(a, s, font(T["font"], size), x, base, col, align, alpha, crisp=T["crisp"])


def tt_w(s, size=None):
    return font(T["font"], size or T["title_size"]).getlength(s)


def _arc(cx, cy, rx, ry, a0, a1, n=None):
    n = n or max(4, int(abs(a1 - a0) / 12))
    return [(cx + rx * np.cos(np.radians(a0 + (a1 - a0) * i / n)), cy + ry * np.sin(np.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


# The Wii's lettering, drawn: round-capped strokes on a 10-unit cap height (y down, baseline 10,
# x-height 4). Each glyph: (advance, [polyline, ...], [dot, ...]).
def _glyphs():
    A = _arc
    g = {
        "A": (7, [[(0, 10), (3.5, 0), (7, 10)], [(1.4, 6.6), (5.6, 6.6)]], []),
        "B": (6, [[(0, 10), (0, 0), (3, 0)] + A(3, 2.5, 2.5, 2.5, -90, 90) + [(0, 5)],
                  [(0, 5), (3.4, 5)] + A(3.4, 7.5, 2.6, 2.5, -90, 90) + [(0, 10)]], []),
        "C": (8, [A(4.6, 5, 4.6, 5, -45, -315)], []),
        "D": (7, [[(0, 0), (0, 10), (2.2, 10)] + A(2.2, 5, 4.6, 5, 90, -90) + [(0, 0)]], []),
        "E": (5.5, [[(5.5, 0), (0, 0), (0, 10), (5.5, 10)], [(0, 5), (4.6, 5)]], []),
        "F": (5.5, [[(5.5, 0), (0, 0), (0, 10)], [(0, 5), (4.6, 5)]], []),
        "G": (9, [A(4.6, 5, 4.6, 5, -45, -360) + [(5.2, 5)]], []),
        "H": (6.5, [[(0, 0), (0, 10)], [(6.5, 0), (6.5, 10)], [(0, 5), (6.5, 5)]], []),
        "I": (0, [[(0, 0), (0, 10)]], []),
        "J": (4.5, [[(4.5, 0), (4.5, 7.4)] + A(2.25, 7.4, 2.25, 2.6, 0, 180)], []),
        "K": (6, [[(0, 0), (0, 10)], [(5.8, 0), (0, 6.2)], [(1.9, 4.4), (6, 10)]], []),
        "L": (5, [[(0, 0), (0, 10), (5, 10)]], []),
        "M": (8.5, [[(0, 10), (0, 0), (4.25, 8), (8.5, 0), (8.5, 10)]], []),
        "N": (6.5, [[(0, 10), (0, 0), (6.5, 10), (6.5, 0)]], []),
        "O": (10, [A(5, 5, 5, 5, 0, 360)], []),
        "P": (6, [[(0, 10), (0, 0), (3, 0)] + A(3, 2.8, 3, 2.8, -90, 90) + [(0, 5.6)]], []),
        "Q": (10, [A(5, 5, 5, 5, 0, 360), [(6.4, 7.2), (9.6, 10.4)]], []),
        "R": (6.2, [[(0, 10), (0, 0), (3, 0)] + A(3, 2.8, 3, 2.8, -90, 90) + [(0, 5.6)], [(2.8, 5.6), (6.2, 10)]], []),
        "S": (6, [A(3, 2.6, 2.9, 2.6, -25, -270) + A(3, 7.4, 3.1, 2.6, -90, 155)], []),
        "T": (6.5, [[(0, 0), (6.5, 0)], [(3.25, 0), (3.25, 10)]], []),
        "U": (6.5, [[(0, 0), (0, 6.6)] + A(3.25, 6.6, 3.25, 3.4, 180, 0) + [(6.5, 0)]], []),
        "V": (7, [[(0, 0), (3.5, 10), (7, 0)]], []),
        "W": (10, [[(0, 0), (2.5, 10), (5, 2.2), (7.5, 10), (10, 0)]], []),
        "X": (6.5, [[(0, 0), (6.5, 10)], [(6.5, 0), (0, 10)]], []),
        "Y": (6.5, [[(0, 0), (3.25, 5), (6.5, 0)], [(3.25, 5), (3.25, 10)]], []),
        "Z": (6, [[(0, 0), (6, 0), (0, 10), (6, 10)]], []),
        "a": (5.6, [A(2.8, 7, 2.8, 3, 0, 360), [(5.6, 4), (5.6, 10)]], []),
        "e": (5.6, [[(0.2, 7), (5.6, 7)] + A(2.8, 7, 2.8, 3, 0, -310)], []),
        "i": (0, [[(0, 4.6), (0, 10)]], [(0, 1.7)]),
        "l": (0, [[(0, 0), (0, 10)]], []),
        "n": (5.2, [[(0, 4), (0, 10)], [(0, 6.6)] + A(2.6, 6.6, 2.6, 2.6, 180, 360) + [(5.2, 10)]], []),
        "u": (5.2, [[(0, 4), (0, 7.4)] + A(2.6, 7.4, 2.6, 2.6, 180, 0), [(5.2, 4), (5.2, 10)]], []),
        "q": (5.6, [A(2.8, 7, 2.8, 3, 0, 360), [(5.6, 4), (5.6, 13)]], []),
        "r": (3.8, [[(0, 4), (0, 10)], [(0, 7)] + A(3.4, 7.2, 3.4, 3.2, 180, 275)], []),
        "y": (5.6, [[(0, 4), (2.8, 10)], [(5.6, 4), (2.0, 13)]], []),
        "z": (5, [[(0, 4), (5, 4), (0, 10), (5, 10)]], []),
        "s": (4.8, [A(2.4, 5.6, 2.3, 1.6, -25, -270) + A(2.4, 8.4, 2.5, 1.6, -90, 155)], []),
        "t": (3.8, [[(1.5, 1.6), (1.5, 8.4)] + A(3.4, 8.4, 1.9, 1.6, 180, 90), [(0, 4), (3.8, 4)]], []),
        " ": (2.5, [], []),
    }
    return g


WGLYPHS = _glyphs()


def stroke_w(s, cap, gap=2.6):
    k = cap / 10.0
    return sum(WGLYPHS[c][0] for c in s) * k + gap * k * max(0, len(s) - 1)


def stroke_text(a, s, x, y_top, cap, col, weight=1.7, gap=2.6, alpha=1.0, align="l"):
    """Bubbly round-capped lettering; cap = cap height in px, y_top = the cap line."""
    k = cap / 10.0
    if align == "c":
        x = x - stroke_w(s, cap, gap) / 2
    wpx = weight
    x0, y0 = int(np.floor(x)) - 3, int(np.floor(y_top)) - 3
    W = int(stroke_w(s, cap, gap) + 8)
    H = int(cap * 1.35 + 8)

    def fn(d, S):
        cx = x - x0
        for c in s:
            adv, lines, dots = WGLYPHS[c]
            for ln in lines:
                pts = [((cx + px_ * k) * S, (y_top - y0 + py_ * k) * S) for px_, py_ in ln]
                if len(pts) > 1:
                    d.line(pts, fill=255, width=max(1, int(wpx * S)), joint="curve")
                r = wpx * S / 2
                for (qx, qy) in (pts[0], pts[-1]):
                    d.ellipse((qx - r, qy - r, qx + r, qy + r), fill=255)
            for dx_, dy_ in dots:
                r = wpx * S * 0.62
                qx, qy = (cx + dx_ * k) * S, (y_top - y0 + dy_ * k) * S
                d.ellipse((qx - r, qy - r, qx + r, qy + r), fill=255)
            cx += adv * k + gap * k
    paint(a, x0, y0, mask(W, H, fn), col, alpha)


# ------------------------------------------------------------------------------------------
# Logos
# ------------------------------------------------------------------------------------------


def logo_alpha(h, w=None):
    """The theme's logo (a one-colour SVG) as an alpha mask cropped to its ink, h px tall
    (or fitted inside w x h)."""
    src = os.path.join(HERE, "source", T["logo"], "logo.svg")
    os.makedirs(SCRATCH, exist_ok=True)
    big = os.path.join(SCRATCH, f"{T['logo']}-big.png")
    subprocess.run(["/usr/bin/rsvg-convert", "-h", "800", "--keep-aspect-ratio", src, "-o", big], check=True)
    im = Image.open(big).convert("RGBA")
    alpha = im.getchannel("A")
    alpha = alpha.crop(alpha.getbbox())
    sc = h / alpha.height
    if w is not None and alpha.width * sc > w:
        sc = w / alpha.width
    tw, th = max(1, round(alpha.width * sc)), max(1, round(alpha.height * sc))
    return np.asarray(alpha.resize((tw, th), Image.LANCZOS), dtype=np.float32).clip(0, 255) / 255.0


# ------------------------------------------------------------------------------------------
# Surfaces: the shells (clamshell bodies or menu backgrounds) and the screens
# ------------------------------------------------------------------------------------------

_rng = np.random.default_rng(1989)


def shell(w, h, seed=7, flat=False):
    """The body fill for a w x h piece (flat: no vertical gradient, for tiles that repeat down)."""
    rng = np.random.default_rng(seed)
    s = ST()
    if flat and s in ("ds", "3ds"):
        a = new(w, h, T["shell"])
        if s == "3ds":
            fl = rng.random((h, w))
            a[fl > 0.992] += np.array([40, 40, 36])
    elif s == "ds":
        a = np.repeat(stops_col(h, [(0, "#ffffff"), (0.45, "#f5f7f9"), (1, "#e4e8ec")]), w, axis=1).copy()
    elif s == "dsi":
        a = new(w, h, T["shell"])
        a += np.round(rng.normal(0, 1.6, (h, w))).astype(np.int32)[..., None]
    elif s == "3ds":
        a = np.repeat(stops_col(h, [(0, "#64cbdb"), (0.5, "#3db4c7"), (1, "#2c9fb2")]), w, axis=1).copy()
        fl = rng.random((h, w))
        a[fl > 0.992] += np.array([40, 40, 36])
        a[(fl > 0.975) & (fl <= 0.992)] += np.array([12, 13, 12])
    elif s == "wii":
        a = new(w, h, (251, 251, 251))
        for y in range(h):
            if y % 3 == 2:
                a[y, :] = (238, 238, 238)
    else:
        a = new(w, h, T["shell"])
    return np.clip(a, 0, 255)


def screen_fill(a, x, y, w, h, kind="top"):
    """A screen's inside (clamshells): graph paper (DS), soft light (DSi), the 3DS's gradients."""
    s = ST()
    if s == "ds":
        rect(a, x, y, w, h, T["screen"])
        for gx in range(x + 3, x + w, 6):
            rect(a, gx, y, 1, h, T["grid"])
        for gy in range(y + 3, y + h, 6):
            rect(a, x, gy, w, 1, T["grid"])
    elif s == "dsi":
        a[y:y + h, x:x + w] = np.repeat(stops_col(h, [(0, "#ffffff"), (1, "#dcdfe2")]), w, axis=1)
        for gy in range(y + 1, y + h, 2):
            a[gy, x:x + w] = np.clip(a[gy, x:x + w] - 5, 0, 255)
    else:  # 3ds
        if kind == "top":
            a[y:y + h, x:x + w] = np.repeat(stops_col(h, [(0, "#ffffff"), (0.6, "#eef1f4"), (1, "#d3d9df")]), w,
                                            axis=1)
            ellipse(a, x + w * 0.5, y + h * 0.15, w * 0.45, h * 0.35, (255, 255, 255), 0.6)
        else:
            rect(a, x, y, w, h, (240, 243, 246))
            for gx in range(x + 2, x + w - 20, 25):
                for gy in range(y + 2, y + h - 20, 25):
                    rrect(a, gx, gy, 22, 22, 4, (226, 231, 236))
                    rrect(a, gx + 1, gy + 1, 20, 20, 3, (240, 243, 246))


def screen(a, x, y, w, h, kind="top"):
    """Bezel ring (1px dark + 1px shade) and the screen's inside (x, y, w, h = the inside)."""
    rrect(a, x - 2, y - 2, w + 4, h + 4, 3, lerp(T["bezel"], T["shell"], 0.35))
    rrect(a, x - 1, y - 1, w + 2, h + 2, 2, T["bezel"])
    screen_fill(a, x, y, w, h, kind)


def joycon(a, x, h, left, y0=0, top=False, bottom=False):
    """A Joy-Con strip down a Switch window's side (JOY_W wide), with rounded outer corners."""
    col = JOY_L if left else JOY_R
    m = np.ones((h, JOY_W), np.float32)
    if top or bottom:
        r = 4
        rm = mask(JOY_W, h, lambda d, S: d.rounded_rectangle(
            ((-r if not left else 0) * S, (0 if top else -r) * S, (JOY_W + (r if left else 0)) * S - 1,
             (h + (0 if bottom else r)) * S - 1), radius=r * S, fill=255))
        m = rm
    seg = new(JOY_W, h, col)
    for i in range(JOY_W):
        u = i / (JOY_W - 1)
        u = u if left else 1 - u
        seg[:, i] = lerp(lerp(col, (255, 255, 255), 0.18), lerp(col, (0, 0, 0), 0.12), u)
    sub = a[y0:y0 + h, x:x + JOY_W].astype(np.float32)
    a[y0:y0 + h, x:x + JOY_W] = np.round(sub * (1 - m[..., None]) + seg * m[..., None]).astype(np.int32)


def joy_details(a, left):
    """The Joy-Cons' buttons on the main window's strips (5px wide)."""
    x = 0 if left else 275 - JOY_W
    cx = x + JOY_W / 2
    dark = (34, 34, 36)
    if left:
        frect(a, cx - 1.5, 19.5, cx + 1.5, 20.5, dark)                      # minus
        disc(a, cx, 33, 2.3, dark)                                         # stick
        disc(a, cx, 33, 1.3, (60, 60, 64))
        for dx, dy in ((0, -1.8), (0, 1.8), (-1.8, 0), (1.8, 0)):          # the four direction buttons
            disc(a, cx + dx, 55 + dy, 0.85, dark)
        frect(a, cx - 1.2, 96, cx + 1.2, 98.4, dark, 0.4)                   # capture
    else:
        frect(a, cx - 1.5, 19.5, cx + 1.5, 20.5, dark)                      # plus
        frect(a, cx - 0.5, 18.5, cx + 0.5, 21.5, dark)
        for dx, dy in ((0, -1.8), (0, 1.8), (-1.8, 0), (1.8, 0)):          # A B X Y
            disc(a, cx + dx, 33 + dy, 0.85, dark)
        disc(a, cx, 55, 2.3, dark)                                         # stick
        disc(a, cx, 55, 1.3, (60, 60, 64))
        disc(a, cx, 97, 1.4, (70, 70, 74))                                 # HOME
        disc(a, cx, 97, 0.7, (200, 200, 200))


def switch_sides(a, h, top=False, bottom=False):
    joycon(a, 0, h, True, top=top, bottom=bottom)
    joycon(a, a.shape[1] - JOY_W, h, False, top=top, bottom=bottom)


def dpad(a, cx, cy, col, arm=4.5, th=1.6):
    frect(a, cx - th, cy - arm, cx + th, cy + arm, col, 0.6)
    frect(a, cx - arm, cy - th, cx + arm, cy + th, col, 0.6)
    disc(a, cx, cy, 0.8, lerp(col, (0, 0, 0), 0.3))


def abxy(a, cx, cy, col, line=None, d=3.0, r=1.5):
    for dx, dy in ((0, -d), (0, d), (-d, 0), (d, 0)):
        if line:
            disc(a, cx + dx, cy + dy, r + 0.5, line)
        disc(a, cx + dx, cy + dy, r, col)


def circle_pad(a, cx, cy):
    disc(a, cx, cy, 4.8, (24, 74, 84))
    grad_disc(a, cx, cy, 4.0, (122, 128, 134), (70, 74, 78))
    disc(a, cx, cy, 2.4, (92, 97, 102))
    ellipse(a, cx, cy - 1.6, 2.2, 1.0, (255, 255, 255), 0.25)


# ------------------------------------------------------------------------------------------
# Bars (titlebars), mini buttons
# ------------------------------------------------------------------------------------------


def bar_rows(h, lit):
    u0, u1, l1, line = T["bar"][0 if lit else 1]
    t = new(1, h)
    s = h // 2
    vgrad_fill(t, 0, 0, 1, s, u0, u1)
    vgrad_fill(t, 0, s, 1, h - s, u1, l1)
    t[h - 1, 0] = line
    if ST() == "wii" and lit:
        t[h - 1, 0] = T["accent"]
    if ST() == "switch":
        t[h - 1, 0] = (70, 70, 70) if lit else (56, 56, 56)
    if ST() == "dsi":
        t[0, 0] = (92, 93, 96) if lit else (70, 71, 74)
    return t


def bar(w, h, lit):
    a = np.repeat(bar_rows(h, lit), w, axis=1).copy()
    if ST() == "ds" and lit:
        rect(a, 0, h - 2, w, 1, lerp(T["accent"], (255, 255, 255), 0.35))
    return a


def bar_text(a, s, cx, base, lit, size=None):
    col = T["title_fg"] if lit else T["title_dim"]
    if ST() == "wii":
        cap = 8 if size is None else size
        stroke_text(a, s, cx, base - cap, cap, col, weight=1.45, gap=3.4, align="c")
        return
    if ST() in ("dsi", "3ds") and lit:
        tt(a, s, cx, base + 1, (0, 0, 0), size, "c", 0.25)
    tt(a, s, cx, base, col, size, "c")


def mini_button(a, x, y, kind, lit=True, pressed=False):
    if pressed:
        rrect(a, x, y, 9, 9, 2, T["accent"])
    col = T["bar_icon"] if lit else T["bar_icon_dim"]
    if pressed:
        col = (255, 255, 255)
    mini_glyph(a, x, y, kind, col)


# ------------------------------------------------------------------------------------------
# Controls: buttons, pills, knobs
# ------------------------------------------------------------------------------------------


def tile(a, x, y, w, h, pressed=False, r=None, on=False):
    """A button face in the theme's style (x, y, w, h: its box)."""
    s = ST()
    acc = T["accent"]
    if s == "ds":
        r = 3 if r is None else r
        line = acc if pressed or on else (150, 162, 174)
        rrect(a, x, y, w, h, r, line)
        if pressed:
            rrect(a, x + 1, y + 1, w - 2, h - 2, r - 1, (214, 240, 252))
        else:
            grad_rrect(a, x + 1, y + 1, w - 2, h - 2, r - 1, (255, 255, 255), (230, 236, 242) if not on else
                       (206, 236, 251))
    elif s == "dsi":
        r = 3 if r is None else r
        rrect(a, x, y, w, h, r, (130, 136, 142) if not (pressed or on) else T["accent_dk"])
        grad_rrect(a, x + 1, y + 1, w - 2, h - 2, r - 1, (255, 255, 255),
                   (226, 229, 232) if not (pressed or on) else (255, 222, 170))
        if pressed:
            rrect(a, x + 1, y + 1, w - 2, 1, 0, acc)
    elif s == "3ds":
        r = 4 if r is None else r
        if pressed:
            rrect(a, x, y, w, h, r, acc)
            grad_rrect(a, x + 2, y + 2, w - 4, h - 4, r - 1, (232, 246, 255), (200, 228, 248))
        else:
            rrect(a, x, y + 1, w, h - 1, r, (20, 100, 114), 0.5)
            rrect(a, x, y, w, h - 1, r, (148, 176, 184))
            grad_rrect(a, x + 1, y + 1, w - 2, h - 3, r - 1, (255, 255, 255), (222, 230, 236) if not on else
                       (196, 230, 252))
            grad_rrect(a, x + 2, y + 1, w - 4, (h - 3) // 2, r - 2, (255, 255, 255), (255, 255, 255), 0.6)
    elif s == "wii":
        r = 4 if r is None else r
        if pressed:
            rrect(a, x, y, w, h, r, acc)
            grad_rrect(a, x + 1, y + 1, w - 2, h - 2, r - 1, (240, 251, 255), (214, 240, 250))
        else:
            rrect(a, x, y + 1, w, h - 1, r, (0, 0, 0), 0.08)
            rrect(a, x, y, w, h - 1, r, (196, 196, 196) if not on else acc)
            grad_rrect(a, x + 1, y + 1, w - 2, h - 3, r - 1, (255, 255, 255), (236, 236, 236) if not on else
                       (220, 244, 252))
    else:  # switch
        r = h / 2 if r is None else r
        rrect(a, x, y, w, h, r, acc if pressed or on else (78, 78, 78))
        rrect(a, x + 1, y + 1, w - 2, h - 2, max(0, r - 1), (64, 64, 64) if not pressed else (40, 70, 78))


def knob(a, x, y, w, h, selected):
    """A slider thumb filling (x, y, w, h)."""
    s = ST()
    if s == "switch":
        cx, cy = x + w / 2, y + h / 2
        rr = min(w, h) / 2
        if selected:
            disc(a, cx, cy, rr, T["accent"])
        disc(a, cx, cy, rr - (1.3 if selected else 0.6), (255, 255, 255))
        return
    if s == "wii":
        rrect(a, x, y, w, h, min(w, h) / 2, T["accent"] if selected else T["knob_line"])
        grad_rrect(a, x + 1, y + 1, w - 2, h - 2, min(w, h) / 2 - 1, (255, 255, 255), (232, 232, 232))
        disc(a, x + w / 2, y + h / 2, 1.3, T["accent"])
        return
    line = T["accent"] if selected else T["knob_line"]
    rrect(a, x, y, w, h, 2.5, line)
    bot = (226, 232, 238) if s != "dsi" else (222, 224, 227)
    grad_rrect(a, x + 1, y + 1, w - 2, h - 2, 1.5, (255, 255, 255), bot if not selected else
               lerp(T["accent"], (255, 255, 255), 0.7))
    if w >= h:
        for gx in (-2, 0, 2):
            rect(a, int(x + w / 2) + gx, y + 3, 1, h - 6, lerp(line, (255, 255, 255), 0.3))
    else:
        for gy in (-2, 0, 2):
            rect(a, x + 3, int(y + h / 2) + gy, w - 6, 1, lerp(line, (255, 255, 255), 0.3))


def h_rail(t, x0, x1, fill_from=None, fill_to=None, y=5, h=3):
    """A horizontal slider rail (rows y..y+h-1) with an accent fill."""
    edge = lerp(T["track"], T["ink"], 0.22) if not is_dark_panel() else T["track"]
    rrect(t, x0, y, x1 - x0, h, h / 2, edge)
    rrect(t, x0 + 1, y + 1, x1 - x0 - 2, h - 2, (h - 2) / 2, T["track"])
    if fill_to is not None:
        f0 = x0 if fill_from is None else fill_from
        if fill_to - f0 >= 2:
            grad_rrect(t, int(f0), y, int(round(fill_to - f0)), h, h / 2, lerp(T["accent"], (255, 255, 255), 0.25),
                       T["accent_dk"])


# ------------------------------------------------------------------------------------------
# Emblems for the About spot
# ------------------------------------------------------------------------------------------


def ds_clock(a, cx, cy):
    """The DS menu's analogue clock, 10:08."""
    disc(a, cx, cy + 0.6, 9.4, (0, 0, 0), 0.10)
    disc(a, cx, cy, 9.2, (150, 162, 174))
    grad_disc(a, cx, cy, 8.3, (255, 255, 255), (228, 234, 240))
    for k in range(12):
        ang = np.radians(k * 30)
        r0, r1 = (5.8, 7.6) if k % 3 == 0 else (6.8, 7.6)
        strokes(a, int(cx) - 10, int(cy) - 10, 21, 21, lambda d, S, ang=ang, r0=r0, r1=r1: d.line(
            ((cx - int(cx) + 10 + r0 * np.sin(ang)) * S, (cy - int(cy) + 10 - r0 * np.cos(ang)) * S,
             (cx - int(cx) + 10 + r1 * np.sin(ang)) * S, (cy - int(cy) + 10 - r1 * np.cos(ang)) * S),
            fill=255, width=int(1.0 * S)), T["accent"] if k % 3 == 0 else (160, 172, 184))

    def hand(ang_deg, ln, wd, col):
        ang = np.radians(ang_deg)
        strokes(a, int(cx) - 10, int(cy) - 10, 21, 21, lambda d, S: d.line(
            ((cx - int(cx) + 10) * S, (cy - int(cy) + 10) * S, (cx - int(cx) + 10 + ln * np.sin(ang)) * S,
             (cy - int(cy) + 10 - ln * np.cos(ang)) * S), fill=255, width=int(wd * S)), col)
    hand(304, 4.2, 1.5, (60, 70, 82))
    hand(48, 6.0, 1.1, (60, 70, 82))
    disc(a, cx, cy, 1.1, T["accent_dk"])


def bird(a, cx, cy):
    """A round little bird in headphones (the DSi Sound mood), about 22 px."""
    disc(a, cx, cy + 1.6, 8.2, (0, 0, 0), 0.35)
    grad_disc(a, cx, cy + 1, 7.8, (255, 210, 96), (240, 138, 0))
    ellipse(a, cx + 0.6, cy + 4.6, 4.6, 2.9, (255, 238, 196))             # belly
    ellipse(a, cx - 5.4, cy + 3.0, 2.4, 1.6, (208, 106, 0))                 # wing
    disc(a, cx + 2.2, cy - 0.2, 1.6, (30, 26, 24))                         # eye
    disc(a, cx + 2.7, cy - 0.8, 0.55, (255, 255, 255))
    poly(a, [(cx + 6.6, cy + 0.6), (cx + 10.0, cy + 2.0), (cx + 6.6, cy + 3.4)], (255, 104, 30))  # beak
    # headphones: the band over the head and two cups
    ox, oy = int(cx) - 12, int(cy) - 12
    strokes(a, ox, oy, 25, 25, lambda d, S: d.arc(
        ((cx - ox - 8.6) * S, (cy - oy - 9.0) * S, (cx - ox + 8.6) * S, (cy - oy + 8.6) * S),
        195, 345, fill=255, width=int(1.8 * S)), (232, 234, 238))
    for sx in (-1, 1):
        rrect(a, int(round(cx + sx * 8.0 - 1.8)), int(round(cy - 3.6)), 4, 7, 1.6, (232, 234, 238))
        rect(a, int(round(cx + sx * 8.0 - 0.8)), int(round(cy - 2.4)), 2, 5, T["accent"])


def wii_button(a, cx, cy, r=10.5):
    """The Wii Menu's round Wii button: white gloss in a blue ring, the Wii logo inside."""
    disc(a, cx, cy + 0.8, r + 1.2, (0, 0, 0), 0.10)
    disc(a, cx, cy, r + 0.8, T["accent"])
    grad_disc(a, cx, cy, r - 0.4, (255, 255, 255), (226, 226, 226))
    ellipse(a, cx, cy - r * 0.42, r * 0.7, r * 0.38, (255, 255, 255), 0.7)
    m = logo_alpha(7, 15)
    paint(a, int(round(cx - m.shape[1] / 2)), int(round(cy - m.shape[0] / 2)), m, (138, 138, 138))


def switch_badge(a, cx, cy):
    """The Switch logo, white, on its red rounded square."""
    rrect(a, int(cx - 9.5), int(cy - 9.5) + 1, 19, 19, 4, (0, 0, 0), 0.35)
    grad_rrect(a, int(cx - 9.5), int(cy - 9.5), 19, 19, 4, (255, 50, 40), (214, 0, 18))
    m = logo_alpha(13)
    paint(a, int(round(cx - m.shape[1] / 2)), int(round(cy - m.shape[0] / 2)), m, (255, 255, 255))


def emblem(a):
    s = ST()
    if s == "ds":
        ds_clock(a, 258.5, 98.0)
    elif s == "dsi":
        bird(a, 258.5, 97.5)
    elif s == "3ds":
        m = logo_alpha(17)
        x, y = int(round(258.5 - m.shape[1] / 2)), int(round(97.5 - m.shape[0] / 2))
        paint(a, x, y + 1, m, (16, 92, 106), 0.6)
        paint(a, x, y, m, (255, 255, 255))
    elif s == "wii":
        wii_button(a, 258.5, 98.0)
    else:
        switch_badge(a, 258.5, 97.5)


# ------------------------------------------------------------------------------------------
# Backgrounds (main and EQ windows); sprites copy theirs from these
# ------------------------------------------------------------------------------------------

MAINBG = None
EQBG = None


def at(src, x, y, w, h):
    return src[y:y + h, x:x + w].copy()


def outline(a, h):
    w = a.shape[1]
    c = T["shell_line"]
    rect(a, 0, 0, 1, h, c)
    rect(a, w - 1, 0, 1, h, c)
    rect(a, 0, h - 1, w, 1, c)


def wii_bottom_bar(a):
    """The Wii Menu's bottom bar: light grey, a blue edge along its top, rising round the button."""
    w, h = 275, 116

    def fn(d, S):
        pts = [(0, 86)]
        for x in np.linspace(0, 275, 120):
            y = 86.0
            dx = x - 258.5
            if abs(dx) < 17:
                y = min(y, 98 - np.sqrt(max(0.0, 17 ** 2 - dx * dx)) * 0.86)
            if x > 241 and abs(dx) >= 17:
                y = 86 - (17 - abs(dx)) * 0 if x < 258.5 else 86
            pts.append((x, y))
        pts += [(275, 86), (275, 116), (0, 116)]
        d.polygon([(px_ * S, py_ * S) for px_, py_ in pts], fill=255)
    m = mask(w, h, fn)
    col = np.repeat(stops_col(h, [(0, "#eeeeee"), (0.72, "#eeeeee"), (0.82, "#e4e4e4"), (1, "#d6d6d6")]), w,
                    axis=1).astype(np.float32)
    # the blue edge: the mask's top boundary, 1.3 px
    edge = np.clip(m - np.vstack([np.zeros((2, w), np.float32), m[:-2]]), 0, 1)
    paint(a, 0, 0, m, col)
    paint(a, 0, 0, edge, T["accent"])


def make_main_bg():
    a = shell(275, 116, seed=11)
    s = ST()
    if CLAM():
        screen(a, 20, 17, 250, 54, "top")
    if s == "wii":
        wii_bottom_bar(a)
    if s == "switch":
        rect(a, JOY_W, 14, 275 - 2 * JOY_W, 102, (14, 14, 14))
        rect(a, JOY_W + 1, 15, 275 - 2 * JOY_W - 2, 100, T["shell"])
    # displays
    panel(a, 21, 20, 84, 42, r=3)
    for yy in (29, 34):
        disc(a, 74, yy + 1, 1.1, T["ink"])
    panel(a, 109, 21, 159, 15, r=3)
    panel(a, 109, 40, 159, 14, r=3)
    ptext(a, TINY, "KBPS", 129, 44, T["text2"])
    ptext(a, TINY, "KHZ", 169, 44, T["text2"])
    # seek rail
    if s == "switch":
        h_rail(a, 16, 264, y=76, h=3)
    elif CLAM():
        rrect(a, 16, 75, 248, 5, 2.5, lerp(T["shell"], (0, 0, 0), 0.28))
        rrect(a, 17, 76, 246, 3, 1.5, lerp(T["shell"], (0, 0, 0), 0.12) if s != "dsi" else (58, 60, 64))
    else:
        h_rail(a, 16, 264, y=75, h=4)
    # the strip behind the transport (DSi: the menu's icon strip)
    if s == "dsi":
        rrect(a, 13, 85, 147, 24, 5, (8, 8, 9))
        grad_rrect(a, 14, 86, 145, 22, 4, (236, 238, 240), (206, 210, 214))
        for k in range(5):
            disc(a, 60 + 10 * k + 0.5, 111.5, 0.9, (110, 112, 116) if k != 1 else T["accent"])
        # the inner camera on the hinge
        disc(a, 147.5, 111.5, 2.8, (52, 54, 58))
        disc(a, 147.5, 111.5, 2.0, (6, 6, 8))
        disc(a, 147.5, 111.5, 1.0, (30, 34, 60))
        disc(a, 147.0, 111.0, 0.4, (200, 210, 255))
    if s == "3ds":
        # the 3D depth slider beside the top screen
        rrect(a, 271, 26, 3, 26, 1.5, (18, 80, 92))
        rrect(a, 270, 32, 5, 5, 1.5, (230, 234, 236))
        rect(a, 271, 34, 3, 1, (150, 160, 166))
    if s == "switch":
        switch_sides(a, 116, bottom=True)
        joy_details(a, True)
        joy_details(a, False)
    else:
        outline(a, 116)
    emblem(a)
    return a


def make_eq_bg():
    a = shell(275, 116, seed=12)
    s = ST()
    if CLAM():
        screen(a, 13, 15, 251, 97, "bottom")
        # the controls either side of the touch screen
        if s == "ds":
            dpad(a, 6, 40, (52, 56, 62))
            abxy(a, 269.5, 40, (176, 184, 192), line=(112, 122, 134), d=2.9, r=1.3)
            for yy in (78, 84):
                disc(a, 269.5, yy, 0.9, (150, 158, 166))
        elif s == "dsi":
            dpad(a, 6, 40, (70, 72, 76))
            abxy(a, 269.5, 40, (88, 91, 96), line=(10, 10, 10), d=2.9, r=1.3)
            for yy in (78, 84):
                disc(a, 269.5, yy, 0.9, (80, 82, 86))
        else:
            circle_pad(a, 6, 32)
            dpad(a, 6, 70, (38, 42, 46))
            abxy(a, 269.5, 38, (40, 44, 48), line=(20, 96, 110), d=2.9, r=1.3)
            disc(a, 269.5, 72, 1.2, (230, 236, 238))
    if s == "switch":
        rect(a, JOY_W, 14, 275 - 2 * JOY_W, 102, (14, 14, 14))
        rect(a, JOY_W + 1, 14, 275 - 2 * JOY_W - 2, 101, T["shell"])
        switch_sides(a, 116)
    else:
        outline(a, 116)
    panel(a, 85, 16, 115, 21, r=3)
    if s == "wii":
        # the sliders sit in a channel-tile frame
        rrect(a, 14, 34, 249, 72, 6, (205, 205, 205))
        grad_rrect(a, 15, 35, 247, 70, 5, (245, 245, 245), (226, 226, 226))
    panel(a, 16, 36, 245, 68, r=4)
    return a


def panel(a, x, y, w, h, r=3, col=None, line=None):
    col = T["panel"] if col is None else col
    line = T["panel_line"] if line is None else line
    rrect(a, x - 1, y - 1, w + 2, h + 2, r + 1, line)
    rrect(a, x, y, w, h, r, col)
    # keep the inside exactly the panel colour except the very corners
    rect(a, x + 1, y, w - 2, h, col)
    rect(a, x, y + 1, w, h - 2, col)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = at(MAINBG, 10, 22, 8, 43)
    s = ST()
    if s == "switch":
        rrect(a, 0, 0, 8, 43, 4, (70, 70, 70))
        rrect(a, 1, 1, 6, 41, 3, (46, 46, 46))
    else:
        rrect(a, 0, 0, 8, 43, 3, T["panel_line"] if s != "dsi" else (8, 8, 9))
        rrect(a, 1, 1, 6, 41, 2, T["panel"])
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rrect(a, 1, y, 6, h, 1.5, T["accent"])
        gy = y + (h - 5) // 2
        ptext(a, TINY, letter, 2, gy, (255, 255, 255) if on else T["text2"])
    return a


def main_titlebar(lit):
    a = bar(275, 14, lit)
    s = ST()
    col = T["title_fg"] if lit else T["title_dim"]
    if s in ("ds", "dsi"):
        h = 10 if s == "ds" else 9
        m = logo_alpha(h)
        extra = 0
        if T["title"]:
            extra = tt_w(T["title"]) + 3
        x0 = int(round(137.5 - (m.shape[1] + extra) / 2))
        paint(a, x0, 2 if s == "ds" else 3, m, col)
        if T["title"]:
            tt(a, T["title"], x0 + m.shape[1] + 3, 10.5 if s == "dsi" else 11, col)
    else:
        bar_text(a, T["title"], 137.5, 10 if s != "wii" else 11, lit)
    if s == "switch":
        switch_sides(a, 14, top=True)
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, T["shell"])
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
# cbuttons.bmp (136 x 36)
# ------------------------------------------------------------------------------------------

CB_POS = {"previous": (16, 88), "play": (39, 88), "pause": (62, 88), "stop": (85, 88), "next": (108, 88)}
GLYPH_S = {"play": 4.4, "pause": 3.5, "stop": 3.2, "previous": 3.4, "next": 3.4, "eject": 3.4}


def transport_cell(kind, w, h, pressed):
    x, y = CB_POS.get(kind, (136, 89))
    a = at(MAINBG, x, y, w, h)
    s = ST()
    o = 0.5 if pressed and s not in ("switch",) else 0.0
    ink = T["glyph"]
    if pressed:
        ink = T["accent_dk"] if s != "switch" else (255, 255, 255)
    gs = GLYPH_S[kind] * (0.9 if h < 18 else 1.0)
    cx, cy = w / 2, h / 2
    if s == "switch":
        r = 7.6 if h == 18 else 6.8
        if pressed:
            disc(a, cx, cy, r + 1.2, T["accent"])
            disc(a, cx, cy, r - 0.2, (26, 26, 26))
        disc(a, cx, cy, r - (1.2 if pressed else 0), (70, 70, 70) if not pressed else (58, 58, 58))
        grad_disc(a, cx, cy, r - (1.8 if pressed else 0.7), (84, 84, 84), (62, 62, 62))
        icon(a, kind, cx + (0.5 if kind == "play" else 0), cy, gs * 0.82, (255, 255, 255))
        return a
    if s == "wii" and kind == "play":
        # the Wii Remote's round A button
        disc(a, cx, cy + 0.8, 8.6, (0, 0, 0), 0.10)
        disc(a, cx, cy, 8.6, T["accent"] if pressed else (190, 190, 190))
        grad_disc(a, cx, cy, 7.7, (255, 255, 255), (230, 230, 230) if not pressed else (210, 238, 250))
        if not pressed:
            ellipse(a, cx, cy - 3.4, 5.2, 2.6, (255, 255, 255), 0.8)
        icon(a, kind, cx + 0.6 + o, cy + o, gs * 0.9, ink)
        return a
    pad = 1 if s != "dsi" else 1
    tile(a, pad, pad if h == 18 else 0, w - 2 * pad, h - (2 * pad if h == 18 else 0), pressed)
    icon(a, kind, cx + (0.6 if kind == "play" else 0) + o, cy + o - (0.5 if s in ("3ds", "wii") and not pressed
                                                                       else 0), gs * 0.92, ink)
    return a


def make_cbuttons():
    a = new(136, 36, T["shell"])
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


def toggle_icon_cell(kind, w, on, pressed):
    x0 = 164 if kind == "shuffle" else 210
    a = at(MAINBG, x0, 89, w, 15)
    cx, cy = w / 2, 7.5
    tile(a, 1, 1, w - 2, 13, pressed, r=(6.5 if ST() in ("switch", "wii") else None), on=on)
    if ST() == "switch":
        col = T["accent"] if on else ((255, 255, 255) if pressed else (200, 200, 200))
    else:
        col = T["accent_dk"] if on else (T["glyph"] if not pressed else T["accent_dk"])
    o = 0.5 if pressed else 0
    (shuffle_icon if kind == "shuffle" else repeat_icon)(a, cx + o, cy + o - 0.3, col)
    return a


def text_toggle(a, x, y, w, h, txt, on, pressed):
    tile(a, x, y, w, h, pressed, r=(h / 2 if ST() in ("switch", "wii") else 2.5), on=on)
    if ST() == "switch":
        col = T["accent"] if on else (200, 200, 200)
    else:
        col = T["accent_dk"] if on else T["glyph"]
    o = 0.5 if pressed else 0
    ptext_c(a, TINY, txt, int(x + w / 2 + o), int(y + (h - 5) / 2 + o), col)


def make_shufrep():
    a = new(92, 85, T["shell"])
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
        col = T["accent_dk"] if on else lerp(T["panel"], T["ink"], 0.22)
        if SW() and on:
            col = T["accent"]
        ptext_c(a, TINY, "STEREO", 14, y + 4, col)
        ptext_c(a, TINY, "MONO", 29 + 13, y + 4, col)
    return a


def make_playpaus():
    a = new(48, 9, T["panel"])
    icon(a, "play", 4.6, 4.5, 3.4, T["accent"])
    icon(a, "pause", 9 + 4.5, 4.5, 3.2, T["ink"])
    icon(a, "stop", 18 + 4.5, 4.5, 3.0, T["ink"])
    disc(a, 39 + 1.5, 4.5, 1.0, lerp(T["panel"], T["ink"], 0.4))
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["panel"])
    f = font(T["digit_font"], T["digit_size"])
    for n in range(10):
        ttext(a, str(n), f, 9 * n + 4.5, 12 if T["crisp"] else 11, T["ink"], "c", crisp=T["crisp"])
    if ex:
        frect(a, 99 + 2, 6, 99 + 7, 7 if T["crisp"] else 7.4, T["ink"])
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
            ptext(a, FONT5, key, col * 5, row * 6, T["ink"])
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def seek_thumb(selected):
    a = at(MAINBG, 120, SEEK_Y, 29, 10)
    s = ST()
    if s == "switch":
        for x in range(0, 22):
            t = (x / 21) ** 2
            for yy in (4, 5, 6):
                a[yy, x] = lerp(a[yy, x], T["accent"], t)
        knob(a, 19, 0, 10, 10, selected)
    elif s == "wii":
        knob(a, 9, 1, 20, 8, selected)
    else:
        knob(a, 13, 0, 16, 10, selected)
    return a


def make_posbar(main):
    a = new(307, 10, T["shell"])
    a[0:10, 0:248] = MAINBG[SEEK_Y:SEEK_Y + 10, 16:264]
    a[0:10, 248:277] = seek_thumb(False)
    a[0:10, 278:307] = seek_thumb(True)
    a[0:10, 277] = MAINBG[SEEK_Y:SEEK_Y + 10, 140]
    return a


def slider_thumb(selected):
    t = at(MAINBG, 120, 58, 14, 11)
    if SW():
        knob(t, 2, 0, 11, 11, selected)
    else:
        knob(t, 0, 1, 14, 9, selected)
    return t


def slider_thumbs(a):
    a[422:433, 0:14] = slider_thumb(True)
    a[422:433, 15:29] = slider_thumb(False)


def make_volume():
    a = new(68, 433, T["shell"])
    for i in range(28):
        y = i * 15
        t = at(MAINBG, 107, 57, 68, 15)
        level = (i + 1) / 28
        h_rail(t, 3, 65, None, 7 + round(level * 54), y=4, h=5)
        a[y:y + 15, 0:68] = t
    slider_thumbs(a)
    return a


def make_balance():
    a = new(68, 433, T["shell"])
    for i in range(28):
        y = i * 15
        t = new(68, 15, T["shell"])
        t[:, 9:47] = at(MAINBG, 177, 57, 38, 15)
        reach = round(14 * i / 27)
        h_rail(t, 11, 45, y=4, h=5)
        if reach:
            grad_rrect(t, 28 - reach, 4, 2 * reach, 5, 2.5, lerp(T["accent"], (255, 255, 255), 0.25), T["accent_dk"])
        frect(t, 27.5, 1, 28.5, 3, T["text2"])
        a[y:y + 15, 0:68] = t
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = bar(275, 14, lit)
    bar_text(a, T["eq_title"], 137.5, 10 if ST() != "wii" else 11, lit)
    if SW():
        switch_sides(a, 14, top=True)
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    rect(a, x, y, 14, 63, T["panel"])
    v = n / 27
    centre = (1 - v) * 51 + 6.0
    zero = 31.5
    lo, hi = min(centre, zero), max(centre, zero)
    rrect(a, x + 5, y + 3, 4, 57, 2, T["track"])
    if hi - lo >= 1:
        m = mask(14, 63, lambda d, S: d.rounded_rectangle((5 * S, lo * S, 9 * S - 1, hi * S - 1), radius=2 * S,
                                                          fill=255))
        paint(a, x, y, m, grad_box(14, 63, lerp(T["accent"], (255, 255, 255), 0.3), T["accent_dk"]))
    rect(a, x + 2, y + 31, 2, 1, lerp(T["panel"], T["ink"], 0.25))
    rect(a, x + 10, y + 31, 2, 1, lerp(T["panel"], T["ink"], 0.25))


def eq_thumb(selected):
    t = new(11, 11, T["panel"])
    knob(t, 0, 1, 11, 9, selected) if not SW() else knob(t, 0, 0, 11, 11, selected)
    return t


def make_eqmain():
    global EQBG
    EQBG = make_eq_bg()
    a = new(275, 315, T["shell"])
    a[0:116] = EQBG
    a[0:14, :] = eq_titlebar(True)
    lab = T["text2"]
    rect(a, 40, 40, 1, 60, lerp(T["panel"], T["ink"], 0.15))
    for lbl, yy in (("+12DB", 41), ("+0DB", 67), ("-12DB", 92)):
        ptext_c(a, TINY, lbl, 58, yy, lab)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    blab = T["ink"] if CLAM() or ST() == "wii" else T["text2"]
    blab = lerp(blab, T["screen"], 0.25)
    ptext_c(a, TINY, "PREAMP", 28, 106, blab)
    for i, lbl in enumerate(EQ_BANDS):
        ptext_c(a, TINY, lbl, 78 + 18 * i + 7, 106, blab)

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
    for r in range(19):
        px(a, 115, 294 + r, ramp([T["vis"][1], T["vis"][2], T["vis"][3]], r / 18))
    for x in range(113):
        px(a, x, 314, lerp(T["panel"], T["ink"], 0.4) if x % 3 != 2 else T["panel"])
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------


def frame_side(w, h, left, seed=3):
    """A playlist/gen side tile: the shell, edged; Switch: a Joy-Con strip on the outer side."""
    t = shell(w, h, seed, flat=True)
    c = T["shell_line"]
    if SW():
        rect(t, 0, 0, w, h, T["shell"])
        joycon(t, 0 if left else w - JOY_W, h, left)
        rect(t, JOY_W if left else w - JOY_W - 1, 0, 1, h, (14, 14, 14))
        return t
    rect(t, 0 if left else w - 1, 0, 1, h, c)
    inner = lerp(T["shell"], (0, 0, 0), 0.18) if is_light() else lerp(T["shell"], (0, 0, 0), 0.6)
    rect(t, w - 1 if left else 0, 0, 1, h, inner)
    return t


def bottom_strip(w, h, seed=5):
    t = shell(w, h, seed)
    if SW():
        rect(t, 0, 0, w, h, T["shell"])
    rect(t, 0, 0, w, 1, lerp(T["shell"], (0, 0, 0), 0.18) if is_light() else lerp(T["shell"], (0, 0, 0), 0.6))
    rect(t, 0, h - 1, w, 1, T["shell_line"] if not SW() else (14, 14, 14))
    return t


def pill_button(t, x, y, w, h, txt):
    tile(t, x, y, w, h, False, r=(h / 2 if ST() in ("switch", "wii") else 3))
    ptext_c(t, TINY, txt, int(x + w / 2), int(y + (h - 5) / 2), T["glyph"] if not SW() else (220, 220, 220))


def readout(t, x, y, w, h):
    rrect(t, x - 1, y - 1, w + 2, h + 2, 2, T["panel_line"])
    rect(t, x, y, w, h, T["panel"])


def pl_title_tile(lit):
    t = bar(100, 20, lit)
    bar_text(t, T["pl_title"], 50, 13 if ST() != "wii" else 14, lit)
    return t


def bar_piece(w, lit, left=False, right=False):
    t = bar(w, 20, lit)
    if SW():
        if left:
            joycon(t, 0, 20, True, top=True)
        if right:
            joycon(t, w - JOY_W, 20, False, top=True)
    return t


def make_pledit():
    a = new(280, 186, T["shell"])
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar_piece(25, lit)
        a[y:y + 20, 0:25] = bar_piece(25, lit, left=True)
        a[y:y + 20, 26:126] = pl_title_tile(lit)
        t = bar_piece(25, lit, right=True)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    a[42:71, 0:12] = frame_side(12, 29, True)
    t = frame_side(20, 29, False)
    groove = lerp(T["panel"], T["ink"], 0.06)
    rect(t, 5, 0, 8, 29, groove)
    a[42:71, 31:51] = t
    b = bar(9, 20, True)[3:12].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = b
    for x, sel in ((52, False), (61, True)):
        t = new(8, 18, groove)
        rrect(t, 1, 1, 6, 16, 3, T["accent"] if sel else lerp(T["track"], T["ink"], 0.25))
        a[53:71, x:x + 8] = t

    # bottom
    t = bottom_strip(125, 38)
    if SW():
        joycon(t, 0, 38, True, bottom=True)
    else:
        rect(t, 0, 0, 1, 38, T["shell_line"])
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        pill_button(t, bx, 9, 22, 16, lbl)
    a[72:110, 0:125] = t

    t = bottom_strip(150, 38)
    if SW():
        joycon(t, 150 - JOY_W, 38, False, bottom=True)
    else:
        rect(t, 149, 0, 1, 38, T["shell_line"])
    readout(t, 6, 9, 56, 8)
    gcol = T["glyph"] if not SW() else (220, 220, 220)
    if ST() == "dsi":
        gcol = (200, 202, 206)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        icon(t, kind, bx + 5, 22 + 5, 2.6 if kind != "play" else 3.0, gcol)
    readout(t, 65, 22, 33, 8)
    rect(t, 84, 24, 1, 1, T["ink"])
    rect(t, 84, 27, 1, 1, T["ink"])
    pill_button(t, 106, 9, 22, 16, "LIST")
    gc = lerp(T["shell"], (0, 0, 0), 0.35) if is_light() else lerp(T["shell"], (255, 255, 255), 0.3)
    for k in range(4):
        for j in range(k + 1):
            disc(t, (146.5 if not SW() else 141.5) - 3 * k + 3 * j, 34.5 - 3 * j, 0.7, gc)
    a[72:110, 126:276] = t

    a[0:38, 179:204] = bottom_strip(25, 38)
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_letter_cells(lit):
    """Each capital in its own cell (the bar's rows 4..10), for gen.bmp's letter rows."""
    col = T["title_fg"] if lit else T["title_dim"]
    rows = bar_rows(20, lit)[4:11]
    cells = []
    for c in GEN_LETTERS:
        if ST() == "wii":
            w = max(3, int(np.ceil(WGLYPHS[c][0] * 0.6 + 1.4)))
            cell = np.repeat(rows, w, axis=1).copy()
            stroke_text(cell, c, w / 2, 0.4, 6, col, weight=1.3, align="c")
        else:
            f = font(T["font"], 8 if not T["crisp"] else 9)
            adv = int(round(f.getlength(c))) + 1
            w = max(3, adv)
            cell = np.repeat(rows, w, axis=1).copy()
            ttext(cell, c, f, w / 2, 7 if not T["crisp"] else 7, col, "c", crisp=T["crisp"])
        cells.append(cell)
    return cells


def make_gen():
    a = new(194, 109, T["shell"])
    for lit, y in ((True, 0), (False, 21)):
        for x0 in (26, 52, 78, 104):
            a[y:y + 20, x0:x0 + 25] = bar_piece(25, lit)
        a[y:y + 20, 0:25] = bar_piece(25, lit, left=True)
        t = bar_piece(25, lit, right=True)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 130:155] = t

    def bottom(w, grip):
        t = bottom_strip(w, 14)
        gc = lerp(T["shell"], (0, 0, 0), 0.35) if is_light() else lerp(T["shell"], (255, 255, 255), 0.3)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    disc(t, w - 3.5 - (JOY_W if SW() else 0) - 3 * k + 3 * j, 11.5 - 3 * j, 0.7, gc)
        return t

    t = bottom(125, False)
    if SW():
        joycon(t, 0, 14, True, bottom=True)
    else:
        rect(t, 0, 0, 1, 14, T["shell_line"])
    a[42:56, 0:125] = t
    t = bottom(125, True)
    if SW():
        joycon(t, 125 - JOY_W, 14, False, bottom=True)
    else:
        rect(t, 124, 0, 1, 14, T["shell_line"])
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
    sh = T["shell"]
    light = is_light() or CLAM() and ST() != "dsi"
    btn_bg = (240, 242, 244) if ST() != "switch" else (64, 64, 64)
    btn_fg = T["glyph"]
    return [pl["NormalBG"], pl["Normal"], T["screen"] if CLAM() else sh, T["ink"], T["ink"],
            lerp(pl["NormalBG"], pl["Normal"], 0.25), pl["SelectedBG"], btn_bg, btn_fg,
            (255, 255, 255) if light else (90, 90, 90), lerp(btn_bg, (0, 0, 0), 0.3),
            T["accent"], pl["NormalBG"], lerp(pl["NormalBG"], pl["Normal"], 0.08), T["track"],
            lerp(pl["NormalBG"], pl["Normal"], 0.15), T["accent"], pl["NormalBG"]]


def make_genex():
    a = new(256, 64, T["shell"])
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    for y, pressed in ((1, False), (16, True)):
        cell = new(47, 15, T["shell"] if not CLAM() else T["screen"])
        tile(cell, 0, 0, 47, 15, pressed)
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
        out.append((ramp(stops[::-1] if is_dark_panel() else stops[::-1], i / 15),
                    f"spectrum {i + 1} (top)" if i == 0 else f"spectrum {i + 1}"))
    for i in range(5):
        out.append((ramp(stops[1:][::-1], i / 4), f"oscilloscope {i + 1}"))
    out.append((T["accent_dk"] if not is_dark_panel() else (255, 255, 255), "peaks"))
    return out


def is_dark_panel():
    return sum(T["panel"]) < 384


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    pl = T["pl"]
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={pl['Normal']}\nCurrent={pl['Current']}\nNormalBG={pl['NormalBG']}\n"
                f"SelectedBG={pl['SelectedBG']}\nMbBG={pl['NormalBG']}\nMbFG={pl['Normal']}\nFont=Arial\n")
    n, o = T["name"], T["owner"]
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{n} — a skin in the style of {T['subject']}.\n"
            f"{T['mark']} © {o}.\n\n"
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
    rows = [("Mii Plaza - Sunday Walk", "4:12"), ("Shop Channel - Browsing", "3:47"),
            ("Download Play - Waiting", "5:03"), ("PictoChat - Room A", "2:58"),
            ("Pocket Cartridge - Slot 1", "6:21"), ("Touch Screen - Calibrate", "3:33"),
            ("Street Pass - Plaza", "4:40"), ("Hinge Theory - Fold", "3:09"),
            ("Neon Pair - Left & Right", "5:51"), ("Circle Pad - Drift", "4:05"),
            ("Stylus - Tap Tap", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=f"{T['name']} - Menu Theme (Remix)", bars=bars)
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
