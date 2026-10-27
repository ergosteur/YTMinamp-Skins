#!/usr/bin/python3
"""Mobile Classic: five classic Winamp 2.x skins in the style of BlackBerry OS 4.5, BlackBerry OS 5,
BlackBerry OS 6, BlackBerry 10 and Windows Mobile 6 (6.0/6.1, the classic Today/list look).

One procedural generator, a theme per platform (based on skins/ember/gen_skin.py, keeping its sheet
layouts). Everything is drawn here from code: gradients, rounded shapes, hand-made pixel fonts and
small text rendered from free system fonts (Open Sans, Droid Sans, Noto Sans, Liberation Sans),
except the BlackBerry pearls (the About spot of the four BlackBerry skins) and the Windows flag (the Windows
Mobile titlebar), rasterised from the files under source/ (private use only).

    /usr/bin/python3 -I gen_skin.py [bb45|bb5|bb6|bb10|wm6 ...]     (no args: all five; --list)

Writes the sheets into out/<theme>/, zips them flat into <Name>.wsz beside this file and draws
preview-<theme>.png (the windows put together from the sprites the way the app does, 2x).
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
SOURCE = os.path.join(HERE, "source")
OUT = ""


def hx(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


FONTDIR = "/usr/share/fonts"
FONTS = {
    "droid": f"{FONTDIR}/google-droid-sans-fonts/DroidSans.ttf",
    "droidb": f"{FONTDIR}/google-droid-sans-fonts/DroidSans-Bold.ttf",
    "noto": f"{FONTDIR}/google-noto/NotoSans-Regular.ttf",
    "notol": f"{FONTDIR}/google-noto/NotoSans-Light.ttf",
    "notom": f"{FONTDIR}/google-noto/NotoSans-Medium.ttf",
    "notob": f"{FONTDIR}/google-noto/NotoSans-SemiBold.ttf",
    "lib": f"{FONTDIR}/liberation-sans-fonts/LiberationSans-Regular.ttf",
    "libb": f"{FONTDIR}/liberation-sans-fonts/LiberationSans-Bold.ttf",
    "open": f"{FONTDIR}/open-sans/OpenSans-Regular.ttf",
    "opensb": f"{FONTDIR}/open-sans/OpenSans-Semibold.ttf",
}
_font_cache = {}


def font(key, size):
    k = (key, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(FONTS[key], size)
    return _font_cache[k]


# ------------------------------------------------------------------------------------------
# Themes. Gradient stops are (t, colour), t from 0 (top) to 1 (bottom); a repeated t is a hard
# edge (the glossy half-split).
# ------------------------------------------------------------------------------------------

THEMES = {
    # BlackBerry OS 4.5 (2008), the Curve 8300/8320 Zen and Today themes: the deep blue
    # wallpaper, a navy title band (smooth, not BB5's split gloss) with white bold text and the
    # status icons, white list screens with black text, the flat royal-blue trackball focus box
    # with its light rim, light rounded dialog buttons, and the Zen home screen's dark icon row
    # right across the bottom.
    "bb45": dict(
        file="BlackBerry-OS-4.5", subject="BlackBerry OS 4.5 (the Curve 8300 Zen/Today look)",
        owner="BlackBerry Limited", ui="open", uib="opensb", digits=("open", 16),
        title_main="Now Playing", title_eq="Equalizer", title_pl="Music",
        bar=[(0, hx("5a7cba")), (0.45, hx("2f5193")), (1, hx("1a3368"))],
        bar_i=[(0, hx("6a7488")), (1, hx("3d4556"))],
        bar_top=hx("8aa6d8"), bar_top_i=hx("848da0"), bar_bot=hx("0a1736"),
        bar_text=hx("ffffff"), bar_text_i=hx("b9c0cc"), bar_shadow=hx("0c1a3c"),
        body=[(0, hx("26508f")), (1, hx("0c1e45"))], edge_hi=hx("4c72b2"), edge_lo=hx("050d20"),
        panel=hx("ffffff"), rim=hx("091634"), rim2=hx("dde3ec"), radius=2,
        ink=hx("000000"), label=hx("9fb2d2"), label_in=hx("6b7a92"), ghost=hx("e3e8ef"),
        hil=[(0, hx("5486dc")), (1, hx("1f4aa6"))], hil_edge=hx("cfdcf5"), accent=hx("2f62c8"),
        tray=[(0, hx("10234b")), (1, hx("050c1e"))], tray_line=hx("3e5e9a"), tray_style="zen",
        icon=hx("ffffff"), icon_dim=hx("7d8fb2"), icon_on=hx("8fb8ff"),
        btn=[(0, hx("ffffff")), (1, hx("d0d7e3"))], btn_edge=hx("08142f"), btn_ink=hx("13254a"),
        side=hx("16326a"), side_hi=hx("3e5e9a"), side_lo=hx("050d20"),
        groove=hx("0a1736"), track=hx("0a1736"), track_fill=hx("79a4ee"),
        thumb=[(0, hx("ffffff")), (1, hx("bcc8db"))], thumb_edge=hx("08142f"),
        pl=dict(Normal="#000000", Current="#1D4FB0", NormalBG="#FFFFFF", SelectedBG="#ABC4EF",
                MbBG="#FFFFFF", MbFG="#000000", Font="BBAlpha Sans"),
        vis=[hx("0b2a6e"), hx("1d46a0"), hx("2f62c8"), hx("5b8ae0"), hx("8fb1ec"), hx("c4d5f4")],
        osc=[hx("0b2a6e"), hx("1d46a0"), hx("2f62c8"), hx("5b8ae0"), hx("8fb1ec")], peak=hx("000000"),
        logo="pearls", logo_col=hx("ffffff"), logo_shade=None,
    ),
    # BlackBerry OS 5, the Bold 9000/9700 "Precision" theme: dark glossy charcoal chrome, black
    # displays, blue-grey glossy focus/highlight bars, the home screen's dark icon dock.
    "bb5": dict(
        file="BlackBerry-OS-5", subject="BlackBerry OS 5 (the Bold 9000/9700 Precision theme)",
        owner="BlackBerry Limited", ui="droid", uib="droidb", digits=("droid", 16),
        title_main="Media", title_eq="Equalizer", title_pl="Media Playlist",
        bar=[(0, hx("5d636c")), (0.5, hx("383c43")), (0.5, hx("23262a")), (1, hx("16181b"))],
        bar_i=[(0, hx("3a3c40")), (0.5, hx("2b2d30")), (0.5, hx("212225")), (1, hx("1a1b1d"))],
        bar_top=hx("8a9099"), bar_top_i=hx("4c4e52"), bar_bot=hx("050506"),
        bar_text=hx("ffffff"), bar_text_i=hx("8e9196"), bar_shadow=hx("000000"),
        body=[(0, hx("2b2e33")), (1, hx("121315"))], edge_hi=hx("4a4e55"), edge_lo=hx("000000"),
        panel=hx("000000"), rim=hx("3e434a"), rim2=hx("17191c"), radius=3,
        ink=hx("f2f4f7"), label=hx("8d939b"), ghost=hx("1c1e21"),
        hil=[(0, hx("a7c0dc")), (0.5, hx("6688b1")), (0.5, hx("4f739e")), (1, hx("3a5b84"))],
        hil_edge=hx("c6d6ea"), accent=hx("8fb4e0"),
        tray=[(0, hx("101113")), (1, hx("060607"))], tray_line=hx("3a3e45"), tray_style="dock",
        icon=hx("e8ebef"), icon_dim=hx("6c7179"), icon_on=hx("9cc3f0"),
        btn=[(0, hx("50555d")), (0.5, hx("33373d")), (0.5, hx("25282c")), (1, hx("1b1d20"))],
        btn_edge=hx("0a0b0c"), btn_ink=hx("e8ebef"),
        side=hx("1b1d20"), side_hi=hx("3a3e45"), side_lo=hx("050506"),
        groove=hx("0b0c0d"), track=hx("2c3036"), track_fill=hx("7ea6d6"),
        thumb=[(0, hx("f4f6f8")), (1, hx("aab2bc"))], thumb_edge=hx("2a2e33"),
        pl=dict(Normal="#E4E7EB", Current="#9CC3F0", NormalBG="#0B0C0E", SelectedBG="#34506F",
                MbBG="#0B0C0E", MbFG="#E4E7EB", Font="BBAlpha Sans"),
        vis=[hx("ffffff"), hx("cfe0f4"), hx("8fb4e0"), hx("5b86bb"), hx("37608f"), hx("223f62")],
        osc=[hx("ffffff"), hx("cfe0f4"), hx("9cbde4"), hx("6f95c4"), hx("4c6f9a")], peak=hx("ffffff"),
        logo="pearls", logo_col=hx("e6e9ed"), logo_shade=hx("6f757d"),
    ),
    # BlackBerry OS 6 (2010): the lighter, cleaner redesign: white/silver app headers with dark
    # text, white lists, bright blue gradient highlight bars, and the dark pull-up drawer of the
    # home screen (the transport sits in it, under its handle).
    "bb6": dict(
        file="BlackBerry-OS-6", subject="BlackBerry OS 6", owner="BlackBerry Limited",
        ui="droid", uib="droidb", digits=("droid", 16),
        title_main="Music", title_eq="Equalizer", title_pl="Music Playlist",
        bar=[(0, hx("ffffff")), (0.5, hx("f1f2f4")), (0.5, hx("e6e8eb")), (1, hx("d3d7dc"))],
        bar_i=[(0, hx("f4f5f6")), (1, hx("e1e3e5"))],
        bar_top=hx("ffffff"), bar_top_i=hx("f8f8f8"), bar_bot=hx("9aa1a9"),
        bar_text=hx("23272c"), bar_text_i=hx("8f949a"), bar_shadow=hx("ffffff"),
        body=[(0, hx("f3f4f6")), (1, hx("d6d9dd"))], edge_hi=hx("ffffff"), edge_lo=hx("8e959d"),
        panel=hx("ffffff"), rim=hx("aab1b9"), rim2=hx("e9ecef"), radius=3,
        ink=hx("1f2328"), label=hx("6c737b"), ghost=hx("eef0f2"),
        hil=[(0, hx("6cb6f6")), (0.5, hx("3a8ee6")), (0.5, hx("2479da")), (1, hx("1a68c8"))],
        hil_edge=hx("a9d3fa"), accent=hx("2a7fdc"),
        tray=[(0, hx("3a3d42")), (0.12, hx("2a2c30")), (1, hx("18191c"))], tray_line=hx("5d6168"),
        tray_style="drawer",
        icon=hx("f2f4f6"), icon_dim=hx("7d828a"), icon_on=hx("5fb0f8"),
        btn=[(0, hx("ffffff")), (1, hx("dde1e5"))], btn_edge=hx("9aa1a9"), btn_ink=hx("2b3036"),
        side=hx("e4e7ea"), side_hi=hx("ffffff"), side_lo=hx("9aa1a9"),
        groove=hx("c9ced4"), track=hx("c3c8ce"), track_fill=hx("2f86e3"),
        thumb=[(0, hx("ffffff")), (1, hx("cfd4da"))], thumb_edge=hx("7f8790"),
        pl=dict(Normal="#22262B", Current="#1A6FD6", NormalBG="#FFFFFF", SelectedBG="#BCDAF8",
                MbBG="#FFFFFF", MbFG="#22262B", Font="BBAlpha Sans"),
        vis=[hx("0d4fa8"), hx("1a68c8"), hx("2f86e3"), hx("5aa6ee"), hx("8cc3f4"), hx("bcdcf8")],
        osc=[hx("0d4fa8"), hx("1a68c8"), hx("2f86e3"), hx("5aa6ee"), hx("8cc3f4")], peak=hx("1f2328"),
        logo="pearls", logo_col=hx("2b3036"), logo_shade=hx("ffffff"),
    ),
    # BlackBerry 10 (2013): flat black, #00a8df cyan accents, the dark action bar along the
    # bottom, the Hub's account rail, Active Frame tiles, Slate Pro's light, open letters.
    "bb10": dict(
        file="BlackBerry-10", subject="BlackBerry 10", owner="BlackBerry Limited",
        ui="noto", uib="notom", digits=("notol", 17),
        title_main="Music", title_eq="Equalizer", title_pl="Playlist",
        bar=[(0, hx("262626")), (1, hx("262626"))], bar_i=[(0, hx("161616")), (1, hx("161616"))],
        bar_top=hx("262626"), bar_top_i=hx("161616"), bar_bot=hx("00a8df"), bar_bot_i=hx("2a2a2a"),
        bar_text=hx("ffffff"), bar_text_i=hx("7a7a7a"), bar_shadow=None,
        body=[(0, hx("000000")), (1, hx("000000"))], edge_hi=hx("1e1e1e"), edge_lo=hx("1e1e1e"),
        panel=hx("121212"), rim=None, rim2=None, radius=0,
        ink=hx("ffffff"), label=hx("8a8a8a"), ghost=hx("1d1d1d"),
        hil=[(0, hx("00a8df")), (1, hx("00a8df"))], hil_edge=hx("00a8df"), accent=hx("00a8df"),
        tray=[(0, hx("1f1f1f")), (1, hx("1f1f1f"))], tray_line=hx("333333"), tray_style="actionbar",
        icon=hx("ffffff"), icon_dim=hx("6e6e6e"), icon_on=hx("00a8df"),
        btn=[(0, hx("2b2b2b")), (1, hx("2b2b2b"))], btn_edge=None, btn_ink=hx("ffffff"),
        side=hx("000000"), side_hi=hx("1e1e1e"), side_lo=hx("1e1e1e"),
        groove=hx("1a1a1a"), track=hx("3a3a3a"), track_fill=hx("00a8df"),
        thumb=[(0, hx("f0f0f0")), (1, hx("c8c8c8"))], thumb_edge=hx("000000"),
        pl=dict(Normal="#F2F2F2", Current="#00A8DF", NormalBG="#000000", SelectedBG="#08485E",
                MbBG="#000000", MbFG="#F2F2F2", Font="Slate Pro"),
        vis=[hx("bff0ff"), hx("66d4f5"), hx("00a8df"), hx("0088b8"), hx("006a91"), hx("004c69")],
        osc=[hx("ffffff"), hx("8fe2fb"), hx("00a8df"), hx("0086b3"), hx("00658a")], peak=hx("ffffff"),
        logo="pearls", logo_col=hx("ffffff"), logo_shade=None,
    ),
    # Windows Mobile 6.0/6.1 Professional, default theme: the glossy blue navigation bar with the
    # Start flag, the Today screen's blue, the dark soft-key bar along the bottom (with the input
    # panel's keyboard in its middle), white list views with blue selection.
    "wm6": dict(
        file="Windows-Mobile-6", subject="Windows Mobile 6", owner="Microsoft Corporation",
        ui="lib", uib="libb", digits=("lib", 16),
        title_main="Windows Media", title_eq="Equalizer", title_pl="Now Playing",
        bar=[(0, hx("86b2ee")), (0.5, hx("4378d2")), (0.5, hx("2a5cc0")), (1, hx("153f99"))],
        bar_i=[(0, hx("a3adbd")), (0.5, hx("7b8597")), (0.5, hx("6a7488")), (1, hx("566074"))],
        bar_top=hx("b8d3f6"), bar_top_i=hx("c4cad4"), bar_bot=hx("0a2a6e"),
        bar_text=hx("ffffff"), bar_text_i=hx("e1e5eb"), bar_shadow=hx("0b2f78"),
        body=[(0, hx("1d58b8")), (1, hx("0b2d72"))], edge_hi=hx("4f86da"), edge_lo=hx("061a46"),
        panel=hx("0c2c6b"), rim=hx("6f9be0"), rim2=hx("08214f"), radius=2,
        ink=hx("ffffff"), label=hx("a9c3ea"), ghost=hx("12357a"),
        hil=[(0, hx("7fb0f2")), (0.5, hx("4b82dc")), (0.5, hx("3a70cf")), (1, hx("2a5cbd"))],
        hil_edge=hx("bcd5f7"), accent=hx("ffcc33"),
        tray=[(0, hx("62676f")), (0.5, hx("33373d")), (0.5, hx("1f2226")), (1, hx("0c0d0f"))],
        tray_line=hx("8a9099"), tray_style="softkeys",
        icon=hx("ffffff"), icon_dim=hx("8f96a0"), icon_on=hx("ffcc33"),
        btn=[(0, hx("f6f6f6")), (1, hx("d9dce0"))], btn_edge=hx("6b7079"), btn_ink=hx("000000"),
        side=hx("2a5cc0"), side_hi=hx("86b2ee"), side_lo=hx("0a2a6e"),
        groove=hx("08214f"), track=hx("0a2459"), track_fill=hx("7fb0f2"),
        thumb=[(0, hx("ffffff")), (1, hx("b9c9e2"))], thumb_edge=hx("0a2a6e"),
        pl=dict(Normal="#000000", Current="#1A4FB5", NormalBG="#FFFFFF", SelectedBG="#B7CDF3",
                MbBG="#FFFFFF", MbFG="#000000", Font="Tahoma"),
        vis=[hx("ffffff"), hx("d6e6fb"), hx("a3c6f4"), hx("6f9fe6"), hx("467dd6"), hx("2a5cbd")],
        osc=[hx("ffffff"), hx("d6e6fb"), hx("a3c6f4"), hx("6f9fe6"), hx("467dd6")], peak=hx("ffcc33"),
        logo="flag",
    ),
}

T = SimpleNamespace()
SEP = (255, 0, 255)            # gen.bmp letter separators (never shown)


def set_theme(name):
    global OUT
    T.__dict__.clear()
    T.name = name
    T.__dict__.update(THEMES[name])
    T.__dict__.setdefault("bar_bot_i", T.bar_bot)
    OUT = os.path.join(HERE, "out", name)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, float)
# ------------------------------------------------------------------------------------------


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def ramp(stops, t):
    """Colour along stops [(t, col)...]; a repeated t is a hard edge."""
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1 and t1 > t0:
            if t == t1 and i + 2 < len(stops) and stops[i + 2][0] == t1:
                continue
            return lerp(c0, c1, (t - t0) / (t1 - t0))
    return stops[-1][1]


def even(cols):
    """Evenly spaced stops from a colour list."""
    n = len(cols) - 1
    return [(i / n, c) for i, c in enumerate(cols)]


def new(w, h, col=(0, 0, 0)):
    a = np.zeros((h, w, 3), dtype=np.float64)
    a[:, :] = col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):y + h, max(0, x):x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def vgrad(a, x, y, w, h, stops, y0=None, span=None):
    """A vertical gradient; y0/span place it on a taller band (so pieces line up)."""
    y0 = y if y0 is None else y0
    span = h if span is None else span
    for r in range(h):
        t = (y + r - y0 + 0.5) / span
        rect(a, x, y + r, w, 1, ramp(stops, t))


def blend(a, x, y, mask, col):
    """Paints col through a float mask (h x w, 0..1) at (x, y), clipped to the canvas."""
    h, w = mask.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(a.shape[1], x + w), min(a.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    m = mask[y0 - y:y1 - y, x0 - x:x1 - x, None]
    src = np.array(col, dtype=np.float64) if not isinstance(col, np.ndarray) else col[y0 - y:y1 - y, x0 - x:x1 - x]
    a[y0:y1, x0:x1] = a[y0:y1, x0:x1] * (1 - m) + src * m


def rr_mask(w, h, r, inset=0.0):
    """Anti-aliased rounded-rectangle mask, 4x supersampled."""
    S = 4
    im = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(im)
    i = inset * S
    if r <= 0:
        d.rectangle((i, i, w * S - 1 - i, h * S - 1 - i), fill=255)
    else:
        d.rounded_rectangle((i, i, w * S - 1 - i, h * S - 1 - i), radius=max(0, r * S - i), fill=255)
    im = im.resize((w, h), Image.BOX)
    return np.array(im, dtype=np.float64) / 255


def gradient_block(w, h, stops):
    g = new(w, h)
    vgrad(g, 0, 0, w, h, stops)
    return g


def rshape(a, x, y, w, h, r, fill, edge=None, inner_hi=None):
    """A rounded shape: fill (colour or stops), optional 1px edge and inner top highlight."""
    m = rr_mask(w, h, r)
    if edge is not None:
        blend(a, x, y, m, edge)
        mi = rr_mask(w, h, r, inset=1.0)
    else:
        mi = m
    src = gradient_block(w, h, fill) if isinstance(fill, list) else fill
    blend(a, x, y, mi, src)
    if inner_hi is not None:
        top = np.zeros_like(mi)
        top[1 if edge is not None else 0] = 1
        blend(a, x, y, np.minimum(mi, top) * 0.8, inner_hi)


def save(a, name):
    img = Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


# ------------------------------------------------------------------------------------------
# Text: TrueType for titles and labels (anti-aliased, as the phones drew them), pixel fonts
# for text.bmp and the tiniest labels.
# ------------------------------------------------------------------------------------------


def tt_w(s, key, size):
    return font(key, size).getlength(s)


def tt(a, s, x, y, key, size, col, anchor="ls", shadow=None, sdy=1):
    """Text at (x, y) with a PIL anchor (default: left, baseline)."""
    f = font(key, size)
    h, w = a.shape[:2]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((x, y), s, font=f, fill=255, anchor=anchor)
    mk = np.array(m, dtype=np.float64) / 255
    if shadow is not None:
        sh = np.zeros_like(mk)
        sh[sdy:, :] = mk[:-sdy, :]
        blend(a, 0, 0, sh * 0.75, shadow)
    blend(a, 0, 0, mk, col)


def G(*rows):
    return list(rows)


FONT5 = {
    "A": G(".##.", "#..#", "####", "#..#", "#..#"), "B": G("###.", "#..#", "###.", "#..#", "###."),
    "C": G(".###", "#...", "#...", "#...", ".###"), "D": G("###.", "#..#", "#..#", "#..#", "###."),
    "E": G("####", "#...", "###.", "#...", "####"), "F": G("####", "#...", "###.", "#...", "#..."),
    "G": G(".###", "#...", "#.##", "#..#", ".###"), "H": G("#..#", "#..#", "####", "#..#", "#..#"),
    "I": G("###", ".#.", ".#.", ".#.", "###"), "J": G("...#", "...#", "...#", "#..#", ".##."),
    "K": G("#..#", "#.#.", "##..", "#.#.", "#..#"), "L": G("#...", "#...", "#...", "#...", "####"),
    "M": G("#..#", "####", "####", "#..#", "#..#"), "N": G("#..#", "##.#", "#.##", "#..#", "#..#"),
    "O": G(".##.", "#..#", "#..#", "#..#", ".##."), "P": G("###.", "#..#", "###.", "#...", "#..."),
    "Q": G(".##.", "#..#", "#..#", "#.#.", ".#.#"), "R": G("###.", "#..#", "###.", "#.#.", "#..#"),
    "S": G(".###", "#...", ".##.", "...#", "###."), "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#..#", "#..#", "#..#", "#..#", ".##."), "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#..#", "#..#", "####", "####", "#..#"), "X": G("#..#", "#..#", ".##.", "#..#", "#..#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."), "Z": G("####", "...#", ".##.", "#...", "####"),
    "0": G("###", "#.#", "#.#", "#.#", "###"), "1": G(".#.", "##.", ".#.", ".#.", "###"),
    "2": G("###", "..#", "###", "#..", "###"), "3": G("###", "..#", ".##", "..#", "###"),
    "4": G("#.#", "#.#", "###", "..#", "..#"), "5": G("###", "#..", "###", "..#", "###"),
    "6": G("###", "#..", "###", "#.#", "###"), "7": G("###", "..#", ".#.", ".#.", ".#."),
    "8": G("###", "#.#", "###", "#.#", "###"), "9": G("###", "#.#", "###", "..#", "###"),
    '"': G("#.#", "#.#", "...", "...", "..."), "@": G(".##.", "#.##", "#.##", "#...", ".###"),
    "…": G(".....", ".....", ".....", ".....", "#.#.#"), ".": G(".", ".", ".", ".", "#"),
    ":": G(".", "#", ".", "#", "."), "(": G(".#", "#.", "#.", "#.", ".#"), ")": G("#.", ".#", ".#", ".#", "#."),
    "-": G("...", "...", "###", "...", "..."), "'": G("#", "#", ".", ".", "."), "!": G("#", "#", "#", ".", "#"),
    "_": G("....", "....", "....", "....", "####"), "+": G("...", ".#.", "###", ".#.", "..."),
    "\\": G("#..", "#..", ".#.", "..#", "..#"), "/": G("..#", "..#", ".#.", "#..", "#.."),
    "[": G("##", "#.", "#.", "#.", "##"), "]": G("##", ".#", ".#", ".#", "##"), "^": G(".#.", "#.#", "...", "...", "..."),
    "&": G(".#..", "#.#.", ".#..", "#.#.", ".#.#"), "%": G("#.#", "..#", ".#.", "#..", "#.#"),
    ",": G("..", "..", "..", ".#", "#."), "=": G("...", "###", "...", "###", "..."),
    "$": G(".###", "#.#.", ".##.", ".#.#", "###."), "#": G(".#.#", "####", ".#.#", "####", ".#.#"),
    "å": G(".##.", ".##.", "#..#", "####", "#..#"), "ö": G("#..#", ".##.", "#..#", "#..#", ".##."),
    "ä": G("#..#", ".##.", "#..#", "####", "#..#"), "?": G("###.", "...#", ".##.", "....", ".#.."),
    "*": G("#.#", ".#.", "###", ".#.", "#.#"), " ": G("...", "...", "...", "...", "..."),
}

TINY = {
    "A": G(".#.", "#.#", "###", "#.#", "#.#"), "B": G("##.", "#.#", "##.", "#.#", "##."),
    "C": G(".##", "#..", "#..", "#..", ".##"), "D": G("##.", "#.#", "#.#", "#.#", "##."),
    "E": G("###", "#..", "##.", "#..", "###"), "F": G("###", "#..", "##.", "#..", "#.."),
    "G": G(".##", "#..", "#.#", "#.#", ".##"), "H": G("#.#", "#.#", "###", "#.#", "#.#"),
    "I": G("###", ".#.", ".#.", ".#.", "###"), "J": G("..#", "..#", "..#", "#.#", ".#."),
    "K": G("#.#", "#.#", "##.", "#.#", "#.#"), "Q": G(".#.", "#.#", "#.#", "##.", ".##"),
    "L": G("#..", "#..", "#..", "#..", "###"), "M": G("#.#", "###", "###", "#.#", "#.#"),
    "N": G("#..#", "##.#", "#.##", "#..#", "#..#"), "O": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "P": G("##.", "#.#", "##.", "#..", "#.."), "R": G("##.", "#.#", "##.", "#.#", "#.#"),
    "S": G(".##", "#..", ".#.", "..#", "##."), "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#.#", "#.#", "#.#", "#.#", "###"), "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#.#", "#.#", "###", "###", "#.#"), "X": G("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."), "Z": G("###", "..#", ".#.", "#..", "###"),
    " ": G("..", "..", "..", "..", ".."),
}
for _c in "0123456789+-.:":
    TINY[_c] = FONT5[_c]


def glyph_w(fnt, c):
    return len(fnt[c][0])


def text_w(fnt, s, gap=1):
    s = [c for c in s if c in fnt]
    return sum(glyph_w(fnt, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, fnt, s, x, y, col, gap=1):
    for c in s:
        if c not in fnt:
            continue
        for r, row in enumerate(fnt[c]):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col)
        x += len(fnt[c][0]) + gap
    return x


def text_center(a, fnt, s, cx, y, col, gap=1):
    draw_text(a, fnt, s, cx - text_w(fnt, s, gap) // 2, y, col, gap)


def pix(a, x, y, rows, col, dim=None):
    """Pixel art: '#' col, '+' dim (a half-tone for anti-aliased edges)."""
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "#":
                px(a, x + c, y + r, col)
            elif ch == "+" and dim is not None:
                px(a, x + c, y + r, dim)


# ------------------------------------------------------------------------------------------
# Logos
# ------------------------------------------------------------------------------------------

_logo_cache = {}


def raster(svg, h, name):
    out = os.path.join(SCRATCH, f"{name}-{h}.png")
    if not os.path.exists(out):
        subprocess.run(["/usr/bin/rsvg-convert", "-h", str(h), svg, "-o", out], check=True)
    return Image.open(out).convert("RGBA")


def pearls_mask(h):
    """The BlackBerry pearls (simple-icons' copy of the mark), as an alpha mask cropped to it."""
    key = ("pearls", h)
    if key not in _logo_cache:
        im = raster(os.path.join(SOURCE, "logo-blackberry", "blackberry.svg"), h * 3, "pearls")
        al = im.getchannel("A")
        al = al.crop(al.getbbox())
        w = round(al.width * h / al.height)
        al = al.resize((w * 4, h * 4), Image.LANCZOS).resize((w, h), Image.BOX)
        _logo_cache[key] = np.array(al, dtype=np.float64) / 255
    return _logo_cache[key]


def flag_rgba(h):
    """The 2002-2012 Windows flag in its four colours, h tall, as (rgb, alpha) arrays."""
    key = ("flag", h)
    if key not in _logo_cache:
        im = raster(os.path.join(SOURCE, "logo-windows-flag", "flag-multicolored.svg"), h * 4, "flag")
        im = im.crop(im.getchannel("A").getbbox())
        w = round(im.width * h / im.height)
        im = im.resize((w, h), Image.LANCZOS)
        arr = np.array(im, dtype=np.float64)
        _logo_cache[key] = (arr[..., :3], np.clip(arr[..., 3] / 255 * 1.1, 0, 1))
    return _logo_cache[key]


def draw_pearls(a, x, y, h, col, shade=None):
    m = pearls_mask(h)
    if shade is not None:
        blend(a, x + 1, y + 1, m * 0.6, shade)
    blend(a, x, y, m, col)
    return m.shape[1]


def draw_flag(a, x, y, h, dim=False):
    rgb, al = flag_rgba(h)
    if dim:
        g = rgb.mean(axis=2, keepdims=True)
        rgb = rgb * 0.35 + g * 0.65
    blend(a, x, y, al, rgb)
    return rgb.shape[1]


# ------------------------------------------------------------------------------------------
# Shared pieces: bars, buttons, status icons
# ------------------------------------------------------------------------------------------


def bar(a, x, y, w, h, lit):
    vgrad(a, x, y, w, h, T.bar if lit else T.bar_i)
    rect(a, x, y, w, 1, T.bar_top if lit else T.bar_top_i)
    rect(a, x, y + h - 1, w, 1, T.bar_bot if lit else T.bar_bot_i)


def bar_text(a, s, x, base, lit, size=10, anchor="ls"):
    sh = T.bar_shadow if lit else None
    if sh is not None and T.name == "bb6":
        tt(a, s, x, base, T.uib, size, T.bar_text if lit else T.bar_text_i, anchor, shadow=sh, sdy=1)
    else:
        tt(a, s, x, base, T.uib, size, T.bar_text if lit else T.bar_text_i, anchor, shadow=sh)


def bar_ink(lit):
    return T.bar_text if lit else T.bar_text_i


MINI_GLYPHS = {
    "options": G(".......", ".......", "#######", ".......", "#######", ".......", "#######"),
    "minimize": G(".......", ".......", ".......", ".......", ".......", "#######", "#######"),
    "shade": G("#######", "#######", ".......", ".......", ".......", ".......", "......."),
    "close": G("##...##", ".##.##.", "..###..", "..###..", ".##.##.", "##...##", "......."),
}


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button. The bar behind must already be painted."""
    ink = bar_ink(lit)
    if T.name == "bb5":
        rshape(a, x, y, 9, 9, 2, T.hil if pressed else T.btn, edge=T.btn_edge,
               inner_hi=T.hil_edge if pressed else hx("6a7079"))
        ink = hx("ffffff") if (lit or pressed) else hx("9a9ea4")
    elif T.name == "bb45":
        rshape(a, x, y, 9, 9, 2, T.hil if pressed else [(0, hx("4a6dab")), (1, hx("1d3a74"))],
               edge=hx("cfdcf5") if pressed else hx("08142f"))
        ink = hx("ffffff") if (lit or pressed) else hx("c3c9d4")
    elif T.name == "bb6":
        rshape(a, x, y, 9, 9, 2, T.hil if pressed else T.btn, edge=T.btn_edge if not pressed else hx("1a5fb8"))
        ink = hx("ffffff") if pressed else (T.btn_ink if lit else hx("8f949a"))
    elif T.name == "bb10":
        if pressed:
            rect(a, x, y, 9, 9, T.accent)
        ink = hx("ffffff") if (lit or pressed) else hx("7a7a7a")
    else:  # wm6: glyphs straight on the blue bar; pressed is a darker sunken square
        if pressed:
            rshape(a, x, y, 9, 9, 1, [(0, hx("0d2f78")), (1, hx("1c4bab"))], edge=hx("08225a"))
        ink = hx("ffffff") if (lit or pressed) else hx("e1e5eb")
    g = MINI_GLYPHS[kind]
    if kind == "close":
        g = g[:6]
        pix(a, x + 1, y + 2 if T.name != "bb10" else y + 1, g, ink)
    else:
        pix(a, x + 1, y + 1, g, ink)


def signal_icon(a, x, y, col, dim):
    """Five rising bars, 11 x 8 (the bottom at y + 7)."""
    for i in range(5):
        hgt = 2 + i * 1.5
        hh = int(round(hgt))
        rect(a, x + i * 2 + i // 5, y + 8 - hh, 1, hh, col if i < 4 else dim)


def battery_icon(a, x, y, col, fill):
    """A 13 x 7 battery, nose to the right."""
    rect(a, x, y, 12, 1, col)
    rect(a, x, y + 6, 12, 1, col)
    rect(a, x, y, 1, 7, col)
    rect(a, x + 11, y, 1, 7, col)
    rect(a, x + 12, y + 2, 1, 3, col)
    rect(a, x + 2, y + 2, 7, 3, fill)


def speaker_icon(a, x, y, col):
    pix(a, x, y, G("...#..", "..##.#", "####..", "####.#", "####..", "..##.#", "...#.."), col)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43, T.panel)
    if T.rim is not None:
        rect(a, 0, 0, 8, 1, T.rim)
        rect(a, 0, 42, 8, 1, T.rim)
        rect(a, 0, 0, 1, 43, T.rim)
        rect(a, 7, 0, 1, 43, T.rim)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            vgrad(a, 1, y, 6, h, T.hil)
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, hx("ffffff") if on else T.label)
    return a


def status_cluster(a, right, lit):
    """The phone's status icons, ending at x right (the battery last)."""
    col = bar_ink(lit)
    dim = lerp(col, ramp(T.bar if lit else T.bar_i, 0.5), 0.6)
    if T.name == "wm6":
        # signal, speaker, the clock: the WM6 navigation bar's notification icons
        clock = "12:45"
        cw = tt_w(clock, T.ui, 9)
        tt(a, clock, right - cw, 10, T.ui, 9, col)
        speaker_icon(a, int(right - cw - 10), 3, col)
        signal_icon(a, int(right - cw - 23), 2, col, dim)
        return
    if T.name == "bb45":
        # the 4.x status corner: the clock, then signal bars and the battery
        battery_icon(a, right - 13, 4, col, hx("dbe5f6") if lit else col)
        signal_icon(a, right - 27, 2, col, dim)
        tt(a, "12:45", right - 31, 10, T.uib, 8, col, "rs")
        return
    battery_icon(a, right - 13, 4, col, T.accent if T.name != "bb6" else hx("3aa04a"))
    signal_icon(a, right - 27, 2, col, dim)
    if T.name == "bb5":
        tt(a, "EDGE", right - 32, 10, T.uib, 7, col, "rs")
    elif T.name == "bb6":
        tt(a, "3G", right - 32, 10, T.uib, 8, col, "rs")
    else:
        tt(a, "12:45", right - 32, 10, T.ui, 9, col, "rs")


def main_titlebar(lit):
    a = new(275, 14)
    bar(a, 0, 0, 275, 14, lit)
    mini_button(a, 6, 3, "options", lit)
    if T.name == "wm6":
        fw = draw_flag(a, 19, 2, 10, dim=not lit)
        bar_text(a, T.title_main, 19 + fw + 4, 11, lit, 10)
    else:
        bar_text(a, T.title_main, 20, 11, lit, 10)
    status_cluster(a, 238, lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87, ramp(T.bar_i, 0.5))
    for kind, x in [("options", 0), ("minimize", 9), ("close", 18)]:
        for pressed, y in ((False, 0), (True, 9)):
            b = new(9, 9)
            vgrad(b, 0, 0, 9, 9, T.bar, y0=-3, span=14)
            mini_button(b, 0, 0, kind, True, pressed)
            a[y:y + 9, x:x + 9] = b
    for pressed, x in ((False, 0), (True, 9)):
        b = new(9, 9)
        vgrad(b, 0, 0, 9, 9, T.bar, y0=-3, span=14)
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

TRAY_Y, TRAY_H = 86, 23          # the transport tray (dock / drawer / action bar / soft keys)


def tray_fill(a, x, y, w, h, y_abs):
    """The tray's colour at absolute main-window rows y_abs.., painted at (x, y)."""
    vgrad(a, x, y, w, h, T.tray, y0=y - (y_abs - TRAY_Y), span=TRAY_H)


def panel(a, x, y, w, h):
    """A display: flat panel colour inside (the title box must stay flat: text.bmp's space
    cell is tiled over it), a rounded rim round it."""
    if T.rim is not None:
        rshape(a, x - 1, y - 1, w + 2, h + 2, T.radius, T.panel, edge=T.rim)
        if T.rim2 is not None and T.name != "bb6":
            rect(a, x + 1, y, w - 2, 1, T.rim2)
    else:
        rect(a, x, y, w, h, T.panel)


def body_fill(a, x, y, w, h, span_h):
    vgrad(a, x, y, w, h, T.body, y0=0, span=span_h)


def frame_edges(a, w, h):
    rect(a, 0, 0, 1, h, T.edge_hi)
    rect(a, w - 1, 0, 1, h, T.edge_lo)
    rect(a, 0, h - 1, w, 1, T.edge_lo)


def make_tray(a):
    style = T.tray_style
    if style == "dock":                 # BB5: the home screen's dark icon dock
        rshape(a, 6, TRAY_Y, 263, TRAY_H, 3, T.tray, edge=T.tray_line)
        rect(a, 9, TRAY_Y + 1, 257, 1, hx("26292e"))
    elif style == "drawer":             # BB6: the pull-up drawer, its handle tab above it
        m = rr_mask(267, TRAY_H + 6, 5)
        m[TRAY_H:, :] = rr_mask(267, TRAY_H + 6, 0)[TRAY_H:, :]
        blend(a, 4, TRAY_Y, m[:TRAY_H + 6] * 1.0, T.tray_line)
        inner = rr_mask(265, TRAY_H + 6, 4)
        g = new(265, TRAY_H + 5)
        vgrad(g, 0, 0, 265, TRAY_H + 5, T.tray, y0=-1, span=TRAY_H)
        blend(a, 5, TRAY_Y + 1, inner[:TRAY_H + 5], g)
        # the handle: a small tab with an up chevron, centred over the drawer
        hx0, hw = 120, 36
        tab = rr_mask(hw, 8, 3)
        blend(a, hx0, TRAY_Y - 4, tab, T.tray_line)
        blend(a, hx0 + 1, TRAY_Y - 3, rr_mask(hw - 2, 7, 2), gradient_block(hw - 2, 7, [(0, hx("4a4d53")), (1, hx("3a3d42"))]))
        pix(a, hx0 + hw // 2 - 3, TRAY_Y - 2, G("...#...", "..#.#..", ".#...#."), hx("d6d9dd"))
    elif style == "zen":                # BB OS 4.5: the Zen home screen's dark icon row
        vgrad(a, 1, TRAY_Y, 273, TRAY_H + 6, T.tray, y0=TRAY_Y, span=TRAY_H)
        rect(a, 1, TRAY_Y, 273, 1, T.tray_line)
        rect(a, 1, TRAY_Y + 1, 273, 1, hx("1b3264"))
    elif style == "actionbar":          # BB10: a flat bar right across, a hairline on top
        rect(a, 1, TRAY_Y, 273, TRAY_H + 6, T.tray[0][1])
        rect(a, 1, TRAY_Y, 273, 1, T.tray_line)
    else:                               # WM6: the soft-key bar
        vgrad(a, 1, TRAY_Y, 273, TRAY_H, T.tray)
        rect(a, 1, TRAY_Y, 273, 1, T.tray_line)
        vgrad(a, 1, TRAY_Y + TRAY_H, 273, 6, [(0, hx("0c0d0f")), (1, hx("000000"))])


def make_main():
    a = new(275, 116)
    body_fill(a, 0, 0, 275, 116, 116)
    a[0:14, :] = main_titlebar(True)
    frame_edges(a, 275, 116)

    # clutterbar seat (drawn from titlebar.bmp)
    a[22:65, 10:18] = clutter_bar("")
    # left display: status, time, analyzer
    panel(a, 21, 20, 84, 42)
    # the clock's colon
    for yy in (29, 35):
        rect(a, 73, yy, 2, 2, T.ink)
    # right displays: title row, then kbps/kHz/mono/stereo row
    panel(a, 109, 21, 159, 15)
    panel(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, T.__dict__.get("label_in", T.label))
    draw_text(a, TINY, "KHZ", 169, 44, T.__dict__.get("label_in", T.label))

    # volume / balance seats: their tracks are drawn by the sliders' frames
    # seek bar: a groove (the thumb sprite carries the groove behind it)
    seek_track(a, 16, 72, 248)
    make_tray(a)
    # the About spot: the logo, or (WM6) the input panel's keyboard
    if T.logo == "pearls":
        draw_pearls(a, 253, 94, 10, T.logo_col if T.name != "bb6" else hx("e9ebee"), T.logo_shade if T.name == "bb5" else None)
    else:
        keyboard_icon(a, 251, 92)
    return a


def keyboard_icon(a, x, y):
    """The WM6 soft-key bar's input-panel button: a little keyboard, 16 x 11, its arrow below."""
    rshape(a, x, y, 16, 9, 1, hx("dfe3e8"), edge=hx("ffffff"))
    for r in range(2):
        for c in range(6):
            rect(a, x + 2 + c * 2, y + 2 + r * 2, 1, 1, hx("2a2d33"))
    rect(a, x + 4, y + 6, 8, 1, hx("2a2d33"))
    pix(a, x + 6, y + 10, G("#####", ".###.", "..#.."), hx("ffffff"))


def seek_track(a, x, y, w):
    """The seek groove inside the 10px posbar row (y..y+9)."""
    if T.name == "bb10":
        rect(a, x + 2, y + 4, w - 4, 2, T.track)
    else:
        rshape(a, x + 1, y + 2, w - 2, 6, 3, T.groove, edge=T.rim if T.rim else T.track)
        rect(a, x + 4, y + 4, w - 8, 2, T.track)


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


def transport_icon(a, kind, x, y, w, h, ink, shadow=None):
    cx, cy = x + w // 2, y + h // 2

    def both(fn):
        if shadow is not None:
            fn(1, shadow)
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
                rect(a, cx - r, cy - 4 + r + d, 2 * r + 1, 1, c)
            rect(a, cx - 3, cy + 1 + d, 7, 2, c)
        both(ej)


def tray_button(a, x, y, w, h, y_abs, pressed, divider=True):
    """A button sitting in the tray: the tray itself when up, the platform's focus when pressed."""
    tray_fill(a, x, y, w, h, y_abs)
    if T.name == "bb5":
        if pressed:
            rshape(a, x, y, w, h, 3, T.hil, edge=hx("2b4566"), inner_hi=T.hil_edge)
    elif T.name == "bb6":
        if pressed:
            rshape(a, x, y, w, h, 3, T.hil, edge=hx("114f9e"), inner_hi=T.hil_edge)
    elif T.name == "bb45":
        if pressed:
            # the trackball focus box: flat royal blue, a light rim
            rshape(a, x, y, w, h, 3, T.hil, edge=T.hil_edge)
    elif T.name == "bb10":
        if pressed:
            rect(a, x, y, w, h, lerp(T.tray[0][1], T.accent, 0.35))
            rect(a, x, y + h - 2, w, 2, T.accent)
    else:
        if pressed:
            vgrad(a, x, y, w, h, T.hil)
            rect(a, x, y, w, 1, T.hil_edge)
        elif divider:
            # soft-key separators: a dark line and a light one at the button's right edge
            rect(a, x + w - 1, y + 2, 1, h - 4, hx("0a0b0d"))


def make_cbuttons():
    a = new(136, 36, T.tray[0][1])
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18)]
    shadow = hx("000000") if T.name in ("bb5", "wm6", "bb45") else None
    for kind, x, w, h in specs:
        for pressed, y in ((False, 0), (True, 18)):
            tray_button(a, x, y, w, h, 88, pressed, divider=kind != "next")
            ink = hx("ffffff") if pressed else T.icon
            transport_icon(a, kind, x, y, w, h, ink, None if pressed else shadow)
    for pressed, y in ((False, 0), (True, 16)):
        tray_button(a, 114, y, 22, 16, 89, pressed, divider=False)
        transport_icon(a, "eject", 114, y, 22, 16, hx("ffffff") if pressed else T.icon,
                       None if pressed else shadow)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85): shuffle/repeat as the phones' media icons; EQ/PL as small pills
# ------------------------------------------------------------------------------------------

SHUFFLE_ICON = G(
    "...........#..",
    "##.......####.",
    "..#.....#..#..",
    "...#...#......",
    "....#.#.......",
    ".....#........",
    "....#.#.......",
    "...#...#......",
    "..#.....#..#..",
    "##.......####.",
    "...........#..",
)
REPEAT_ICON = G(
    "........#...",
    ".########...",
    "#.......#...",
    "#...........",
    "#..........#",
    "...........#",
    "...#.......#",
    "...########.",
    "...#........",
)


def toggle_icon(a, x, y, w, h, icon, on, pressed, y_abs):
    tray_button(a, x, y, w, h, y_abs, pressed, divider=False)
    ink = hx("ffffff") if pressed else (T.icon_on if on else T.icon_dim)
    iw, ih = len(icon[0]), len(icon)
    ix, iy = x + (w - iw) // 2, y + (h - ih) // 2 - (1 if on else 0)
    if T.name in ("bb5", "wm6", "bb45") and not pressed:
        pix(a, ix, iy + 1, icon, hx("000000"))
    pix(a, ix, iy, icon, ink)
    if on and not pressed:
        # a lit bar under the icon: the platforms' "on" marker
        rect(a, x + w // 2 - 5, y + h - 2, 10, 1, T.icon_on)


def pill(a, x, y, w, h, label, on, pressed, bg_fn):
    """EQ/PL/ON/AUTO/PRESETS: a small rounded button on the body."""
    bg_fn(a, x, y, w, h)
    if T.name == "bb10":
        if pressed:
            rect(a, x, y, w, h, lerp(hx("000000"), T.accent, 0.35))
        rect(a, x, y, w, h, hx("262626")) if not pressed else None
        ink = T.accent if on else (hx("ffffff") if pressed else hx("9a9a9a"))
        if on:
            rect(a, x, y + h - 1, w, 1, T.accent)
        text_center(a, TINY, label, x + w // 2, y + (h - 5) // 2, ink)
        return
    if pressed:
        rshape(a, x, y, w, h, 3, T.hil, edge=hx("1d3f6e") if T.name != "bb6" else hx("114f9e"))
        ink = hx("ffffff")
    else:
        rshape(a, x, y, w, h, 3, T.btn, edge=T.btn_edge,
               inner_hi=hx("767c85") if T.name == "bb5" else None)
        ink = T.btn_ink if not on else (T.accent if T.name != "wm6" else hx("1a4fb5"))
        if T.name == "bb5":
            ink = T.icon_on if on else hx("aab0b8")
    tw = text_w(TINY, label)
    lx = x + (w - tw - 4) // 2 + 4
    ly = y + (h - 5) // 2
    draw_text(a, TINY, label, lx, ly, ink)
    # the indicator dot
    dot = (hx("7cd36a") if T.name == "wm6" else T.icon_on) if on else (hx("5a5e64") if T.name == "bb5" else hx("aab0b8"))
    if T.name == "bb45" and on and not pressed:
        dot = T.accent
    rect(a, lx - 4, ly + 1, 2, 3, dot)


def make_shufrep(main):
    a = new(92, 85, T.tray[0][1])
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        toggle_icon(a, 0, y, 28, 15, REPEAT_ICON, on, pressed, 89)
        toggle_icon(a, 28, y, 47, 15, SHUFFLE_ICON, on, pressed, 89)

    def seat(dx, dy):
        return lambda arr, x, y, w, h: arr.__setitem__((slice(y, y + h), slice(x, x + w)),
                                                       main[dy:dy + h, dx:dx + w])

    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        dx = 219 if label == "EQ" else 242
        pill(a, x, 61, 23, 12, label, False, pressed, seat(dx, 58))
        pill(a, x, 73, 23, 12, label, True, pressed, seat(dx, 58))
    return a


# ------------------------------------------------------------------------------------------
# monoster, playpaus, numbers, nums_ex, text
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T.panel)
    for y, on in ((0, True), (12, False)):
        col = T.ink if on else T.ghost
        if on and T.name == "bb10":
            col = T.accent
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T.panel)
    c = T.ink if T.name != "bb10" else T.accent
    tri_right(a, 2, 1, 7, c)
    rect(a, 9 + 2, 1, 2, 7, c)
    rect(a, 9 + 5, 1, 2, 7, c)
    rect(a, 18 + 2, 2, 5, 5, c)
    rect(a, 36, 0, 3, 9, T.panel)
    rect(a, 39 + 1, 3, 1, 3, c)
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T.panel)
    key, size = T.digits
    for n in range(10):
        tt(a, str(n), 9 * n + 4.5, 12, key, size, T.ink, "ms")
    if ex:
        rect(a, 99 + 2, 6, 5, 2 if T.name != "bb10" else 1, T.ink)
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, T.panel)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key, col * 5, row * 6, T.ink)
    return a


# ------------------------------------------------------------------------------------------
# posbar, volume, balance
# ------------------------------------------------------------------------------------------


def knob(a, cx, cy, d, selected):
    """A round slider handle centred at (cx, cy)."""
    x, y = int(round(cx - d / 2)), int(round(cy - d / 2))
    if T.name == "bb10":
        rshape(a, x, y, d, d, d / 2, T.accent if selected else hx("e6e6e6"), edge=hx("000000"))
        if not selected:
            blend(a, x + d // 2 - 1, y + d // 2 - 1, rr_mask(3, 3, 1.5), T.accent)
        return
    stops = T.hil if selected else T.thumb
    rshape(a, x, y, d, d, d / 2, stops, edge=T.thumb_edge)
    blend(a, x + 2, y + 1, rr_mask(d - 4, max(2, d // 2 - 1), d / 4) * 0.55, hx("ffffff"))


def make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    for x0, sel in ((248, False), (278, True)):
        a[0:10, x0:x0 + 29] = main[72:82, 100:129]
        if T.name == "bb10":
            knob(a, x0 + 14.5, 5, 10, sel)
        elif T.name == "wm6":
            rshape(a, x0 + 8, 0, 13, 10, 2, T.hil if sel else T.thumb, edge=T.thumb_edge)
            for gx in (x0 + 12, x0 + 14, x0 + 16):
                rect(a, gx, 3, 1, 4, hx("6f8fbf") if not sel else hx("ffffff"))
        else:
            rshape(a, x0 + 6, 1, 17, 8, 4, T.hil if sel else T.thumb, edge=T.thumb_edge)
            blend(a, x0 + 8, 2, rr_mask(13, 3, 1.5) * 0.6, hx("ffffff"))
    return a


def slider_thumbs(a, seat):
    """The volume/balance thumbs (14 x 11, drawn 1px below the frame's top): the seat and a
    half-filled track behind the round handle, so the corners match either side of it."""
    for x, sel in ((0, True), (15, False)):
        a[422:433, x:x + 14] = seat[1:12, 0:14]
        h_track(a, x - 4, 422 + 4, 22, fill_to=x + 7)
        a[422:433, x + 14:x + 15] = seat[1:12, 14:15] if x == 0 else a[422:433, x + 14:x + 15]
        knob(a, x + 7, 427.5, 11, sel)


def h_track(a, x, y, w, fill_to=None, centre=None, reach=0):
    """A slider track along row y..y+2 (3px), filled to fill_to or around centre by reach."""
    if T.name == "bb10":
        rect(a, x, y + 1, w, 1, T.track)
    else:
        rshape(a, x, y, w, 3, 1.5, T.track)
    if fill_to is not None and fill_to > x:
        if T.name == "bb10":
            rect(a, x, y, fill_to - x, 3, T.track_fill)
        else:
            rshape(a, x, y, fill_to - x, 3, 1.5, T.track_fill)
    if centre is not None:
        lo, hi = centre - reach, centre + reach
        if T.name == "bb10":
            rect(a, lo, y, hi - lo + 1, 3, T.track_fill if reach else T.track)
        else:
            rect(a, lo, y, hi - lo + 1, 3, T.track_fill if reach else T.label)


def make_volume(main):
    a = new(68, 433)
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        level = (i + 1) / 28
        h_track(a, 3, y + 5, 62, fill_to=7 + round(level * 54))
    slider_thumbs(a, seat)
    return a


def make_balance(main):
    a = new(68, 433)
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = main[57:72, 168:236]
        a[y:y + 15, 9:47] = seat
        h_track(a, 12, y + 5, 32, centre=28, reach=round(12 * i / 27))
        rect(a, 28, y + 2, 1, 2, T.label)
    slider_thumbs(a, seat)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = new(275, 14)
    bar(a, 0, 0, 275, 14, lit)
    # x 25..40 stays plain bar: the app tiles it when it uses this bar as a frame
    bar_text(a, T.title_eq, 137.5, 11, lit, 10, anchor="ms")
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_body(a):
    body_fill(a, 0, 0, 275, 116, 116)
    frame_edges(a, 275, 116)


def v_track(a, x, y, h, fill_from=None):
    if T.name == "bb10":
        rect(a, x + 1, y, 1, h, T.track)
    else:
        rshape(a, x, y, 3, h, 1.5, T.track)
    if fill_from is not None and fill_from < y + h:
        if T.name == "bb10":
            rect(a, x, fill_from, 3, y + h - fill_from, T.track_fill)
        else:
            rshape(a, x, fill_from, 3, y + h - fill_from, 1.5, T.track_fill)


def eq_slider_frame(a, x, y, n, seat):
    """14x63: a vertical track, filled from the bottom up to the value (n of 0..27)."""
    a[y:y + 63, x:x + 14] = seat
    v = n / 27
    centre = 38 + round((1 - v) * 51) + 5 - 38
    v_track(a, x + 5, y + 2, 59, fill_from=y + centre)
    rect(a, x + 1, y + 31, 3, 1, T.label)
    rect(a, x + 10, y + 31, 3, 1, T.label)


def make_eqmain():
    a = new(275, 315)
    body_fill(a, 0, 116, 275, 199, 116)
    rect(a, 0, 116, 275, 199, ramp(T.body, 1))
    eq_body(a)
    a[0:14, :] = eq_titlebar(True)
    # graph display
    panel(a, 86, 17, 113, 19)
    # slider bay
    seat = a[38:101, 21:35].copy()
    for lbl, yy in (("+12", 41), ("0", 67), ("-12", 92)):
        draw_text(a, TINY, lbl, 70 - text_w(TINY, lbl), yy, T.label)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14, seat)
    text_center(a, TINY, "PREAMP", 28, 106, T.label)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, T.label)

    # under the window
    sub = lambda yy: (lambda arr, x, y, w, h: arr.__setitem__(
        (slice(y, y + h), slice(x, x + w)), a[yy:yy + h, 14:14 + w].copy()))
    b = new(9, 9)
    vgrad(b, 0, 0, 9, 9, T.bar, y0=-3, span=14)
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = b
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        pill(a, x, 119, w, 12, label, on, pressed, sub(18))
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    for y, sel in ((164, False), (176, True)):
        a[y:y + 11, 0:11] = seat[20:31, 1:12]
        if T.name == "bb10":
            knob(a, 5.5, y + 5.5, 11, sel)
        else:
            rshape(a, 0, y + 2, 11, 7, 3, T.hil if sel else T.thumb, edge=T.thumb_edge)
            blend(a, 2, y + 3, rr_mask(7, 2, 1) * 0.6, hx("ffffff"))
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n, seat)
    for y, pressed in ((164, False), (176, True)):
        bg = lambda arr, x, yy, w, h: arr.__setitem__((slice(yy, yy + h), slice(x, x + w)),
                                                     a[18:18 + h, 217:217 + w].copy())
        pill(a, 224, y, 44, 12, "PRESETS", False, pressed, bg)
    # graph
    rect(a, 0, 294, 113, 19, T.panel)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, T.ghost if T.name != "bb6" else hx("d8dde3"))
    for r in range(19):
        px(a, 115, 294 + r, ramp(even(T.vis[::-1]) if T.name == "bb6" else even(T.vis), r / 18))
    for x in range(113):
        px(a, x, 314, T.label if x % 3 != 2 else T.panel)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109)
# ------------------------------------------------------------------------------------------


def bar20(w, lit):
    a = new(w, 20)
    bar(a, 0, 0, w, 20, lit)
    return a


def pl_bottom_bar(t, w):
    """The playlist's bottom: the platform's bottom bar (dock, drawer, action bar, soft keys)."""
    if T.name == "bb6":
        vgrad(t, 0, 0, w, 38, [(0, hx("3a3d42")), (0.08, hx("2a2c30")), (1, hx("18191c"))])
        rect(t, 0, 0, w, 1, T.tray_line)
    elif T.name == "bb10":
        rect(t, 0, 0, w, 38, T.tray[0][1])
        rect(t, 0, 0, w, 1, T.tray_line)
    elif T.name == "bb45":
        vgrad(t, 0, 0, w, 38, T.tray)
        rect(t, 0, 0, w, 1, T.tray_line)
        rect(t, 0, 1, w, 1, hx("1b3264"))
    elif T.name == "wm6":
        vgrad(t, 0, 0, w, 38, [(0, hx("62676f")), (0.5, hx("33373d")), (0.5, hx("1f2226")), (1, hx("0c0d0f"))])
        rect(t, 0, 0, w, 1, T.tray_line)
    else:
        vgrad(t, 0, 0, w, 38, [(0, hx("2a2d32")), (0.5, hx("1b1d20")), (0.5, hx("141518")), (1, hx("0b0c0d"))])
        rect(t, 0, 0, w, 1, hx("4a4e55"))
    rect(t, 0, 37, w, 1, hx("000000"))


def pl_label(t, x, y, w, h, s):
    """A label button in the bottom bar."""
    if T.name == "bb5":
        rshape(t, x, y, w, h, 3, T.btn, edge=T.btn_edge, inner_hi=hx("6a7079"))
    elif T.name == "bb10":
        rect(t, x, y, w, h, hx("2b2b2b"))
    elif T.name == "bb45":
        rshape(t, x, y, w, h, 3, [(0, hx("4a6dab")), (1, hx("1d3a74"))], edge=hx("02060f"),
               inner_hi=hx("7f9cd2"))
    elif T.name == "bb6":
        rshape(t, x, y, w, h, 3, [(0, hx("4a4d53")), (1, hx("34363b"))], edge=hx("15161a"))
    else:
        rect(t, x + w, y + 2, 1, h - 4, hx("0a0b0d"))
        rect(t, x + w + 1, y + 2, 1, h - 4, hx("5d626a"))
    size = 9
    while tt_w(s, T.ui, size) > w - 2 and size > 7:
        size -= 1
    tt(t, s, x + w / 2, y + h / 2 + 3.5, T.ui, size, hx("ffffff"), "ms")


def scroll_groove(t, x, h):
    if T.name == "bb10":
        rect(t, x + 3, 0, 2, h, hx("1e1e1e"))
    else:
        rect(t, x, 0, 8, h, T.groove)
        rect(t, x, 0, 1, h, T.side_lo)
        rect(t, x + 7, 0, 1, h, T.side_hi)


def side_tile(w, h, left):
    t = new(w, h, T.side)
    if T.name == "bb10":
        # the Hub's account rail on the left: a dark strip with a cyan marker
        if left:
            rect(t, 0, 0, 1, h, T.edge_hi)
            rect(t, w - 2, 0, 1, h, hx("141414"))
        else:
            rect(t, w - 1, 0, 1, h, T.edge_hi)
        return t
    if left:
        rect(t, 0, 0, 1, h, T.side_hi)
        rect(t, w - 1, 0, 1, h, T.side_lo)
    else:
        rect(t, 0, 0, 1, h, T.side_lo)
        rect(t, w - 1, 0, 1, h, T.side_lo)
        rect(t, w - 2, 0, 1, h, T.side_hi)
    return t


def make_pledit():
    a = new(280, 186, T.side)
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar20(25, lit)
        t = bar20(25, lit)
        a[y:y + 20, 0:25] = t
        t = bar20(100, lit)
        bar_text(t, T.title_pl, 50, 14, lit, 10, anchor="ms")
        a[y:y + 20, 26:126] = t
        t = bar20(25, lit)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    # left side tile
    a[42:71, 0:12] = side_tile(12, 29, True)
    t = side_tile(20, 29, False)
    scroll_groove(t, 5, 29)
    a[42:71, 31:51] = t
    t = new(9, 9)
    vgrad(t, 0, 0, 9, 9, T.bar, y0=-3, span=20)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        if T.name == "bb10":
            rect(a, x, 53, 8, 18, T.side)
            rect(a, x + 2, 53, 4, 18, T.accent if sel else hx("5a5a5a"))
        else:
            a[53:71, x:x + 8] = T.groove
            rshape(a, x, 53, 8, 18, 3, T.hil if sel else T.thumb, edge=T.thumb_edge)

    def bottom(w):
        t = new(w, 38)
        pl_bottom_bar(t, w)
        return t

    t = bottom(125)
    rect(t, 0, 0, 1, 38, T.edge_hi if T.name != "bb10" else T.tray_line)
    for bx, lbl in ((14, "Add"), (43, "Rem"), (72, "Sel"), (101, "Misc")):
        pl_label(t, bx, 8, 22, 18, lbl)
    a[72:110, 0:125] = t

    t = bottom(150)
    rect(t, 149, 0, 1, 38, T.edge_lo if T.name != "bb10" else T.tray_line)
    # running time readout (text.bmp: the panel colour behind it)
    panel(t, 6, 9, 56, 8)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        mini_transport_icon(t, kind, 3 + 10 * k, 22)
    panel(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, T.label)
    rect(t, 84, 22 + 5, 1, 1, T.label)
    pl_label(t, 106, 8, 22, 18, "List")
    # resize grip
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 31 - 3 * j
            px(t, gx, gy, hx("9aa1a9") if T.name != "bb10" else T.accent)
    a[72:110, 126:276] = t

    a[0:38, 179:204] = bottom(25)
    return a


def mini_transport_icon(a, kind, x, y):
    ink = hx("ffffff") if T.name != "bb10" else hx("d0d0d0")
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
    a = new(194, 109, T.side)
    for lit, y in ((True, 0), (False, 21)):
        for px0 in (0, 26, 52, 78, 104):
            a[y:y + 20, px0:px0 + 25] = bar20(25, lit)
        t = bar20(25, lit)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 130:155] = t

    # bottom caps and fill (14 tall): an Active Frame / the bottom bar's colours
    def bottom(w, grip):
        t = new(w, 14, T.side)
        if T.name == "bb10":
            rect(t, 0, 13, w, 1, T.edge_lo)
        else:
            rect(t, 0, 12, w, 1, T.side_hi if T.name != "bb6" else hx("ffffff"))
            rect(t, 0, 13, w, 1, T.side_lo)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 9 - 3 * j
                    px(t, gx, gy, hx("9aa1a9") if T.name != "bb10" else T.accent)
        return t

    t = bottom(125, False)
    rect(t, 0, 0, 1, 14, T.side_hi if T.name != "bb10" else T.edge_hi)
    a[42:56, 0:125] = t
    t = bottom(125, True)
    rect(t, 124, 0, 1, 14, T.side_lo if T.name != "bb10" else T.edge_hi)
    a[57:71, 0:125] = t
    a[72:86, 127:152] = bottom(25, False)
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h, T.side)
        if left:
            rect(t, 0, 0, 1, h, T.side_hi if T.name != "bb10" else T.edge_hi)
            rect(t, w - 1, 0, 1, h, T.side_lo if T.name != "bb10" else hx("101010"))
        else:
            rect(t, 0, 0, 1, h, T.side_lo if T.name != "bb10" else hx("101010"))
            rect(t, w - 1, 0, 1, h, T.side_lo if T.name != "bb10" else T.edge_hi)
        a[42:42 + h, x:x + w] = t
    t = new(9, 9)
    vgrad(t, 0, 0, 9, 9, T.bar, y0=-3, span=20)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: each row starts at x 1, letters in their own cells on the bar's own rows 4..10,
    # separated by 1px columns of x 0's colour
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        strip = bar20(194, lit)[4:11]
        x = 1
        f = font(T.uib, 9)
        for c in GEN_LETTERS:
            w = max(3, round(f.getlength(c)))
            cell = strip[:, x:x + w].copy()
            tt(cell, c, w / 2, 6.6 if T.name != "bb10" else 6.6, T.uib, 9, bar_ink(lit), "ms")
            a[y:y + 7, x:x + w] = cell
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp, text files
# ------------------------------------------------------------------------------------------


def genex_colours():
    P = {k: hx(v) for k, v in T.pl.items() if k != "Font"}
    hilmid = ramp(T.hil, 0.5)
    light = T.name in ("bb6", "wm6")
    win_bg = ramp(T.body, 0.3) if T.name != "wm6" else hx("ffffff")
    win_txt = hx("1f2328") if light else hx("f0f2f4")
    if T.name == "wm6":
        win_txt = hx("000000")
    return [
        P["NormalBG"], P["Normal"], win_bg, hx("ffffff") if not light else hx("1f2328"), win_txt,
        T.rim or T.edge_hi, hilmid, ramp(T.bar, 0.6), bar_ink(True), T.bar_top, T.bar_bot,
        hilmid, ramp(T.bar, 0.6), T.side, T.thumb[-1][1] if T.name != "bb10" else T.accent,
        T.side_hi, T.accent, T.groove,
    ]


def make_genex():
    a = new(256, 64, ramp(T.body, 0.3))
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    rshape(a, 0, 1, 47, 15, 3, T.btn if T.name != "bb10" else hx("2b2b2b"), edge=T.btn_edge)
    rshape(a, 0, 16, 47, 15, 3, T.hil, edge=T.btn_edge)
    return a


def viscolor():
    spec = [ramp(even(T.vis), i / 15) for i in range(16)]
    dots = lerp(T.panel, T.ink, 0.12)
    return ([(T.panel, "background"), (dots, "dots")]
            + [(c, f"spectrum {i + 1}" + (" (top)" if i == 0 else "")) for i, c in enumerate(spec)]
            + [(c, f"oscilloscope {i + 1}") for i, c in enumerate(T.osc)]
            + [(T.peak, "peaks")])


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for c, note in viscolor():
            r, g, b = (int(round(v)) for v in c)
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write("[Text]\n")
        for k in ("Normal", "Current", "NormalBG", "SelectedBG", "MbBG", "MbFG", "Font"):
            f.write(f"{k}={T.pl[k]}\n")
    logo_note = {"pearls": "BlackBerry logo", "flag": "Windows logo"}[T.logo]
    name = T.file.replace("-", " ")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{name} - a skin in the style of {T.subject}.\n"
            f"{logo_note} (c) {T.owner}.\n\n"
            "A classic (Winamp 2.x format) skin, every bitmap drawn by a script (gen_skin.py)\n"
            + ("from gradients, rounded shapes, pixel fonts and a free system font (Open Sans),\n"
               "apart from the logo.\n" if T.name == "bb45" else
               "from gradients, rounded shapes, pixel fonts and free system fonts (Droid Sans,\n"
               "Noto Sans, Liberation Sans), apart from the logo.\n")
        )


def build():
    main = make_main()
    sheets = {
        "main.bmp": main,
        "titlebar.bmp": make_titlebar(),
        "cbuttons.bmp": make_cbuttons(),
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
    wsz = os.path.join(HERE, f"{T.file}.wsz")
    with zipfile.ZipFile(wsz, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2026, 10, 26, 0, 0, 0))
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

SHEETS = {}


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
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, SHEETS["text"], (col * 5, row * 6, 5, 6), x, y)
        x += 5


def text_ink():
    """As the app: the commonest colour of text.bmp's two letter rows clearly unlike the space."""
    im = SHEETS["text"]
    arr = np.array(im.crop((0, 0, min(im.width, 155), 12))).reshape(-1, 3).astype(int)
    bg = np.array(im.getpixel((150, 0)))
    keep = arr[np.abs(arr - bg).sum(1) >= 96]
    vals, counts = np.unique(keep, axis=0, return_counts=True)
    return tuple(int(v) for v in vals[counts.argmax()])


def title_font():
    return ImageFont.truetype(FONTS["lib"], 11)


def hexcol(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


def preview_main(lit, state):
    S = SHEETS
    img = Image.new("RGB", (275, 116))
    img.paste(S["main"], (0, 0))
    blit(img, S["titlebar"], (27, 0 if lit else 15, 275, 14), 0, 0)
    if state["pressed"] in ("options", "minimize", "close", "shade"):
        r = {"options": (0, 9), "minimize": (9, 9), "close": (18, 9), "shade": (9, 18)}[state["pressed"]]
        dx = {"options": 6, "minimize": 244, "close": 264, "shade": 254}[state["pressed"]]
        blit(img, S["titlebar"], (r[0], r[1], 9, 9), dx, 3)
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
    # title: text.bmp's space across the box, then the TrueType title in text.bmp's ink
    for x in range(0, 154, 5):
        w = min(5, 154 - x)
        blit(img, S["text"], (150, 0, w, 6), 111 + x, 24)
    t = Image.new("RGB", (154, 14))
    t.paste(img.crop((111, 22, 265, 36)), (0, 0))
    ImageDraw.Draw(t).text((0, 7 + 2 - 2), state["title"], font=title_font(), fill=text_ink(), anchor="lm")
    img.paste(t, (111, 22))
    draw_bitmap_text(img, "192", 111, 43)
    draw_bitmap_text(img, "44", 156, 43)
    cols = [c for c, _ in viscolor()]
    cols = [tuple(int(round(v)) for v in c) for c in cols]
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
    P = {k: v for k, v in T.pl.items()}
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=hexcol(P["NormalBG"]))
    f = ImageFont.truetype(FONTS["lib"], 9)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=hexcol(P["SelectedBG"]))
        col = hexcol(P["Current"]) if i == 1 else hexcol(P["Normal"])
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
    pic = Image.linear_gradient("L").resize((w - 22, h - 34)).convert("RGB")
    arr = np.array(pic).astype(np.float32) / 255
    c0, c1 = np.array(ramp(T.hil, 0)), np.array(ramp(T.body, 1))
    col = c1 + (c0 - c1) * arr[..., :1]
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("Pocket Symphony - Trackball", "4:12"), ("Push Mail - Always On", "3:47"),
            ("Red Light Blinking - LED", "5:03"), ("Soft Keys - Left & Right", "2:58"),
            ("QWERTY - Thumb Typing", "6:21"), ("Signal Bars - Edge of Town", "3:33"),
            ("Ping Me - BBM", "4:40"), ("Stylus - Tap & Hold", "3:09"),
            ("Today Screen - Morning", "5:51"), ("Low Battery - Last Call", "4:05"),
            ("Holster - Sleep Mode", "3:22")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=f"{T.file.replace('-', ' ')} - Pocket Symphony (Live)", bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="Paused: Quiet Hours", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    EA = dict(pressed=None, on=True, auto=False, preamp=50, drag=None, bands=[75, 68, 56, 49, 49, 33, 30, 30, 49, 49])
    EB = dict(pressed="close", on=False, auto=True, preamp=70, drag=3, bands=[51, 51, 59, 65, 65, 100, 59, 51, 0, 51])
    cols = []
    for lit, st, est in ((True, A, EA), (False, B, EB)):
        col = Image.new("RGB", (275, 604))
        col.paste(preview_main(lit, st), (0, 0))
        col.paste(preview_eq(lit, est), (0, 116))
        col.paste(preview_playlist(lit, 275, 232, rows, pressed_close=not lit, drag=not lit), (0, 232))
        col.paste(preview_gen(lit, 275, 140, "album art", pressed_close=not lit), (0, 464))
        cols.append(col)
    gap = 12
    out = Image.new("RGB", (275 * 2 + gap * 3, 604 + gap * 2), (90, 92, 96))
    out.paste(cols[0], (gap, gap))
    out.paste(cols[1], (275 + 2 * gap, gap))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, f"preview-{T.name}.png"))
    return cols[0]


if __name__ == "__main__":
    if "--list" in sys.argv:
        for k, v in THEMES.items():
            print(f"{k:5s} {v['file']}.wsz  ({v['subject']})")
        sys.exit(0)
    names = sys.argv[1:] or list(THEMES)
    firsts = []
    for name in names:
        set_theme(name)
        build()
        firsts.append(preview())
        print(f"{name}: {T.file}.wsz, preview-{name}.png")
    cmp_ = Image.new("RGB", (len(firsts) * 287 + 12, 604 + 24), (90, 92, 96))
    for i, im in enumerate(firsts):
        cmp_.paste(im, (12 + i * 287, 12))
    cmp_.resize((cmp_.width * 2, cmp_.height * 2), Image.NEAREST).save(os.path.join(SCRATCH, "compare.png"))
