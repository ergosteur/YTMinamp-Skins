#!/usr/bin/python3
"""Consoles: classic Winamp 2.x skins in the style of game console dashboards.

One procedural generator, one theme per skin:

  xbox-360  the original Xbox 360 "Blades" dashboard (2005-2008): the white console shell,
            glossy green bars, the five blades (Marketplace, Xbox Live, Games, Media, System)
            as the clutter bar's coloured edges, controller face buttons for the transport, the
            guide button's "X" sphere in its ring of light.
  ps3       the PlayStation 3 XrossMediaBar: the deep blue gradient with the flowing wave
            ribbon, thin white icons and lettering, piano-black glossy frames, the PlayStation
            logo.

Everything is drawn here from code (anti-aliased shapes, hinted system sans for the lettering,
pixel fonts for text.bmp), except the PlayStation logo, rasterised from
source/logo-playstation/logo.svg.

    /usr/bin/python3 -I gen_skin.py              # every theme
    /usr/bin/python3 -I gen_skin.py ps3          # just these
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


def hexs(c):
    return "#%02X%02X%02X" % tuple(c)


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------
# Two families share the drawing code: "light" (the Xbox 360 dashboards: a pale body, glossy or
# flat tabs) and "dark" (the PS3, the original Xbox, today's Xbox: a dark body, glyph or tile
# controls). Each theme is its family's defaults (LIGHT / DARK, the Blades and PS3 values) with
# its own overrides. Colours are "#rrggbb" anywhere (converted on setup) except in pl.
#
# bg: flat fill; body: the window body's vertical stops; panel/panel_line: the displays (also
# text.bmp's and the analyzer's background); ink: text.bmp's letters (so the app's TrueType
# title too); text/text2/text3: lettering on the body; pl: pledit.txt; vis: the analyzer.

# The Xbox 360 blades, left to right as the 2006+ dashboard had them. The colours are the
# default theme's as remembered from screenshots (no published values): two greens for
# Marketplace and Xbox Live, a lime for Games, the orange Media blade, the grey System blade.
BLADES = [("Marketplace", "#4e9a1e"), ("Xbox Live", "#8cc63f"), ("Games", "#bcd630"),
          ("Media", "#f39a1e"), ("System", "#a9aeb3")]

GLOSS_ON = ("#c4ec78", "#469a1c", "#2c7612")        # pill top, bottom, outline
GLOSS_OFF = ("#ffffff", "#dcdfe3", "#a0a6ac")

LIGHT = dict(
    family="light", radius=4, skip="bar",
    body=[(0, "#ffffff"), (0.45, "#f4f5f6"), (1, "#dcdfe2")], waves_main=[], waves_eq=[],
    wave_col="#e2ecff", edge=("#b2b7bc", "#a0a5aa", "#ffffff"),
    bar_lit=("#effae0", "#d2ee9a", "#a9d65a", "#8cc63f", "#4f9e1e", "#2d7a12"),
    bar_dim=("#ffffff", "#f7f8f9", "#e9ebed", "#dadde0", "#c6cacd", "#9fa4a9"),
    title_font="font", title_size=9, title_sp=0.6, title_shadow="#28640e", title_upper=False,
    title_extra=None, btn_pressed="#348014", tray=True, label="#6e9650",
    rail="groove", fill=("#bee86e", "#3c9618"), seek_thumb="tab", slider_thumb="pill",
    transport="face", toggle="pill", pill_on=GLOSS_ON, pill_off=GLOSS_OFF, pill_r=None,
    pill_ink_on="#ffffff", pill_ink_off="#545a60", pill_gloss=True,
    clutter="plain", emblem="guide", logo=None, logo_mode="colour", logo_crop=None,
    graph=["#82d23c", "#4caa1e", "#107c10"], eq_lab="#6b7177",
    side="shell", strip=[(0, "#f6f7f8"), (1, "#dde0e3")], strip_lines=("#cdd1d5", "#a0a5aa"),
    side_col="#f0f2f4", side_edge=("#b2b7bc", "#cdd1d5"), groove="#e2e5e8",
    scroll=("#2c7612", "#bee86e", "#469a1c", "#328214"), grip="#969ca2", pl_icon=None, mini_ink="#545a60",
    peaks="#107c10", panel_shadow=False, gen_font="font", gen_pad=0,
)

DARK = dict(
    family="dark", radius=3, skip="bar",
    body=[(0, "#0a2559"), (0.4, "#12479a"), (0.75, "#0c3478"), (1, "#061c48")],
    waves_main=[(106, 5, 18, 0.0, 1.0, [(88, 116, 4)]), (40, 5, 10, 2.2, 0.6, [(16, 50, 5)])],
    waves_eq=[(113, 3, 12, 1.1, 0.7, [(111, 116, 3)]), (27, 4, 10, 3.0, 0.5, [(15, 35, 3)])],
    wave_col="#e2ecff", wave_w=0.8, wave_glow=0.22, grid=None, edge=("#000000", "#000000", None),
    bar_lit=("#6e6e6e", "#3c3c3c", "#1c1c1c", "#070707", "#020202", "#1c1c1c"),
    bar_dim=("#4a4a4a", "#2c2c2c", "#171717", "#070707", "#030303", "#161616"),
    title_font="font_semi", title_size=8, title_sp=1.6, title_shadow=None, title_upper=True,
    title_extra=None, btn_pressed="#464646", tray=False,
    rail="line", fill="#ffffff", seek_thumb="dot", slider_thumb="bar", thumb_glow="#a0c8ff",
    transport="glyph", glyph="#ecf2fc", glyph_play="#ffffff", glow="#bedcff", shadow="#000a28",
    toggle="glyph", tog_on="#ffffff", tog_off="#9cb2d6", tog_press="#cedcf0",
    clutter="plain", emblem="logo", logo_mode="mono", logo_col="#ffffff", logo_crop=None,
    graph=["#ffffff", "#c8e1ff", "#96beff"], eq_lab="#c8d6ec",
    side="gloss_black", strip=[(0, "#1d1d1f"), (0.5, "#0a0a0a"), (1, "#000000")],
    strip_lines=("#24365a", "#3c3c3e"), side_edge=("#24365a",), groove="#081022",
    scroll=("#96acd2", "#ffffff"), grip="#6e6e74", pl_icon="note", mini_ink="#dce4f0",
    peaks="#ffffff", btn=("#46464a", "#28282c", "#0c0c0e", "#dcdce0"), toggle_tile=None,
    panel_shadow=False, gen_font="font_semi", gen_pad=1,
)

THEMES = {
    "xbox-360": dict(
        LIGHT, name="Xbox 360", wsz="Xbox-360", owner="Microsoft Corporation",
        subject="the Xbox 360 Blades dashboard (2005)", mark="Xbox and Xbox 360 marks",
        title="XBOX 360", eq_title="Equalizer", pl_title="Media", gen_title="ALBUM ART",
        font=(NOTO.format("Bold"), None), font_semi=(NOTO.format("SemiBold"), None),
        font_bold=(NOTO.format("Bold"), None), digit_font=(NOTO.format("SemiBold"), None), digit_size=13,
        bg="#f4f5f6", panel="#f3f8eb", panel_line="#a8cf6e",
        ink="#107c10", text="#2b2f33", text2="#6b7177", text3="#b4b9be", track="#c9cdd1",
        title_fg="#ffffff", title_dim="#8d9297", bar_icon="#ffffff", bar_icon_dim="#8d9297",
        title_extra="dots", clutter="blades", pl_icon="blade", play_ind="#4caa1e",
        pl=dict(NormalBG="#FFFFFF", Normal="#2B2F33", Current="#107C10", SelectedBG="#DCEFC2"),
        vis=["#c8f07a", "#9bc848", "#4f9e1e", "#107c10"],
        song="Still Alive (Blades Mix)",
    ),
    "ps3": dict(
        DARK, name="PS3", wsz="PS3", owner="Sony Interactive Entertainment",
        subject="the PlayStation 3 XrossMediaBar", mark="PlayStation logo", logo="logo-playstation",
        title="PLAYSTATION 3", eq_title="Equalizer", pl_title="Music", gen_title="ALBUM ART",
        font=(NOTO.format("Light"), None), font_semi=(NOTO.format("Regular"), None),
        font_bold=(NOTO.format("Regular"), None), digit_font=(NOTO.format("Light"), None), digit_size=14,
        bg="#0d3a86", panel="#08204f", panel_line="#3a6ab4",
        ink="#ffffff", text="#ffffff", text2="#a9bddc", text3="#5a77a6", track="#5a7bb0",
        title_fg="#e6e6e6", title_dim="#7a7a7a", bar_icon="#d8d8d8", bar_icon_dim="#6a6a6a", play_ind="#ffffff",
        pl=dict(NormalBG="#08204F", Normal="#C9D6EC", Current="#9AD8FF", SelectedBG="#1F4E96"),
        vis=["#ffffff", "#bcd6ff", "#5f95e6", "#1d4f9e"],
        song="Flow (XMB Theme)",
    ),
    "xbox-og": dict(
        DARK, name="Xbox Original", wsz="Xbox-Original", owner="Microsoft Corporation",
        subject="the original Xbox dashboard (2001)", mark="Xbox logo", logo="logo-xbox-2001",
        title="XBOX", eq_title="Equalizer", pl_title="Music", gen_title="ALBUM ART",
        font=(NOTO.format("Bold"), None), font_semi=(NOTO.format("SemiBold"), None),
        font_bold=(NOTO.format("Bold"), None), digit_font=(NOTO.format("SemiBold"), None), digit_size=13,
        title_font="font", title_size=9, title_sp=3.0,
        bg="#06240a", panel="#021204", panel_line="#2f8a1a", radius=4,
        body=[(0, "#020a03"), (0.35, "#0a3510"), (0.7, "#062a0a"), (1, "#010602")],
        waves_main=[(104, 6, 3, 0.4, 1.0, [(88, 116, 4)]), (42, 6, 3, 2.6, 0.8, [(16, 50, 5)])],
        waves_eq=[(112, 3, 3, 1.4, 0.9, [(111, 116, 3)]), (27, 4, 3, 3.3, 0.7, [(15, 35, 3)])],
        logo_mode="colour", logo_crop="top", gloss_off=0.15,
        wave_col="#7cf03a", wave_w=2.6, wave_glow=0.55, grid="#1c5a14", tail2="#6ad028",
        clutter_on="#8cff3c", clutter_ink="#d8ffa0",
        bar_lit=("#3a4a3a", "#1e261e", "#0c100c", "#030503", "#000000", "#1c4a12"),
        bar_dim=("#2a2e2a", "#161a16", "#0a0c0a", "#030403", "#000000", "#14200f"),
        ink="#b4f046", text="#d8ffa0", text2="#86c850", text3="#3a7a26", track="#2f7a1e",
        title_fg="#9cf03c", title_dim="#4a6a3a", bar_icon="#86c850", bar_icon_dim="#3e5a32",
        btn_pressed="#1e5a12", fill="#a4f03c", thumb_glow="#8cff3c", play_ind="#b4f046",
        transport="face", toggle="pill", slider_thumb="orb", seek_thumb="orb",
        face=dict(all=("#d4ff7a", "#2a8a10", "#0a3205"), play=("#eaffa0", "#46b41c", "#0a3205")),
        pill_on=("#c8ff6a", "#3aa014", "#1c5a0c"), pill_off=("#1e3a18", "#0a1a08", "#2f6a1e"),
        pill_ink_on="#0c3a06", pill_ink_off="#86c850", pill_r=None, pill_gloss=True,
        graph=["#e0ff9a", "#a4f03c", "#4cb41c"], eq_lab="#86c850",
        strip=[(0, "#1a1f1a"), (0.5, "#080a08"), (1, "#000000")], strip_lines=("#1c4a12", "#2e382e"),
        side_edge=("#1c4a12",), groove="#020c03", scroll=("#3a7a26", "#a4f03c"), grip="#3e6a32",
        pl_icon=None, mini_ink="#a4f03c", peaks="#e8ffb0", btn=("#2f6a1e", "#1a2a18", "#060c06", "#a4f03c"),
        glyph="#d8ffa0", glow="#8cff3c", shadow="#000000",
        pl=dict(NormalBG="#021204", Normal="#8CD84A", Current="#E8FF9A", SelectedBG="#1B5212"),
        vis=["#e8ffb0", "#a4f03c", "#4cb41c", "#14600c"],
        song="Blinx Theme (Dashboard Mix)",
    ),
    "xbox-series": dict(
        DARK, name="Xbox Series", wsz="Xbox-Series", owner="Microsoft Corporation",
        subject="the Xbox Series X|S dashboard (2020)", mark="Xbox logo", logo="logo-xbox-2019",
        logo_mode="colour", logo_crop="top",
        title="Xbox", eq_title="Equalizer", pl_title="Queue", gen_title="NOW PLAYING",
        font=(NOTO.format("SemiBold"), None), font_semi=(NOTO.format("Regular"), None),
        font_bold=(NOTO.format("SemiBold"), None), digit_font=(NOTO.format("Regular"), None), digit_size=14,
        title_font="font", title_size=9, title_sp=0.3, title_upper=False,
        bg="#1a1a1a", panel="#2b2b2b", panel_line="#383838", radius=4,
        body=[(0, "#1f1f1f"), (1, "#161616")], waves_main=[], waves_eq=[], edge=("#0c0c0c", "#0c0c0c", None),
        bar_lit=("#2a2a2a", "#242424", "#242424", "#242424", "#242424", "#141414"),
        bar_dim=("#1e1e1e", "#1a1a1a", "#1a1a1a", "#1a1a1a", "#1a1a1a", "#121212"),
        ink="#ffffff", text="#ffffff", text2="#a8a8a8", text3="#5e5e5e", track="#4a4a4a",
        title_fg="#ffffff", title_dim="#7a7a7a", bar_icon="#d0d0d0", bar_icon_dim="#666666",
        btn_pressed="#3c3c3c", fill="#1db21d", clutter_on="#2fd02f", thumb_glow=None, play_ind="#1db21d",
        rail="thin", slider_thumb="disc", seek_thumb="disc",
        transport="tile", tile=dict(r=4, face="#2d2d2d", play="#107c10", ink="#ffffff", press="#3d3d3d",
                                    play_press="#0c6a0c", ink_play="#ffffff"),
        toggle="tile", toggle_tile=dict(r=4, off="#2d2d2d", on="#107c10", press="#3d3d3d", on_press="#0c6a0c",
                                        ink_off="#c8c8c8", ink_on="#ffffff"),
        graph=["#4ce04c", "#1db21d", "#107c10"], eq_lab="#a8a8a8",
        side="flat", side_col="#1a1a1a", side_edge=("#2d2d2d",), groove="#222222",
        strip=[(0, "#1f1f1f"), (1, "#1a1a1a")], strip_lines=("#2d2d2d", "#1f1f1f"),
        scroll=("#5e5e5e", "#a8a8a8"), grip="#5e5e5e", pl_icon=None, mini_ink="#d0d0d0", peaks="#ffffff",
        btn=("#2d2d2d", "#2d2d2d", "#2d2d2d", "#e6e6e6"),
        pl=dict(NormalBG="#1A1A1A", Normal="#E0E0E0", Current="#5BD65B", SelectedBG="#2E3F2E"),
        vis=["#9bf00b", "#4ce04c", "#1db21d", "#0c5a0c"],
        song="Halo Theme (Series X Mix)",
    ),
    "xbox-360-metro": dict(
        LIGHT, name="Xbox 360 Metro", wsz="Xbox-360-Metro", owner="Microsoft Corporation",
        subject="the Xbox 360 Metro dashboard (2011)", mark="Xbox logo", logo="logo-xbox-2012",
        title="", eq_title="equalizer", pl_title="music", gen_title="ALBUM ART",
        font=(NOTO.format("Light"), None), font_semi=(NOTO.format("Regular"), None),
        font_bold=(NOTO.format("SemiBold"), None), digit_font=(NOTO.format("Light"), None), digit_size=14,
        title_font="font_semi", title_size=9, title_sp=0.2, title_shadow=None, title_extra="tabs",
        bg="#ffffff", panel="#ececec", panel_line=None, radius=0,
        body=[(0, "#ffffff"), (1, "#f4f4f4")], edge=("#c8c8c8", "#b4b4b4", None), tray=False,
        bar_lit=("#107c10",) * 6, bar_dim=("#d6d6d6",) * 6,
        ink="#1e1e1e", text="#1e1e1e", text2="#6e6e6e", text3="#bdbdbd", track="#c8c8c8", label="#6e6e6e",
        title_fg="#ffffff", title_dim="#7a7a7a", bar_icon="#ffffff", bar_icon_dim="#7a7a7a",
        btn_pressed="#0a5a0a", rail="flat", fill="#107c10", seek_thumb="square", slider_thumb="square",
        transport="tile", tile=dict(r=0, face="#107c10", play="#107c10", ink="#ffffff", press="#0a5a0a",
                                    play_press="#0a5a0a", ink_play="#ffffff", eject="#d0d0d0", ink_eject="#1e1e1e"),
        toggle="tile", toggle_tile=dict(r=0, off="#e0e0e0", on="#107c10", press="#c8c8c8", on_press="#0a5a0a",
                                        ink_off="#3a3a3a", ink_on="#ffffff"),
        pill_on=("#107c10", "#107c10", "#107c10"), pill_off=("#e0e0e0", "#e0e0e0", "#e0e0e0"),
        pill_ink_off="#3a3a3a", pill_r=0, pill_gloss=False,
        emblem="logo", logo_mode="colour", graph=["#2ca02c", "#107c10", "#0a5a0a"], eq_lab="#6e6e6e",
        side="flat", side_col="#ffffff", side_edge=("#c8c8c8", "#e6e6e6"), groove="#ececec",
        strip=[(0, "#ffffff"), (1, "#ffffff")], strip_lines=("#e0e0e0", "#b4b4b4"),
        scroll=("#107c10", "#107c10", "#107c10"), grip="#b4b4b4", mini_ink="#3a3a3a", play_ind="#107c10",
        pl=dict(NormalBG="#FFFFFF", Normal="#333333", Current="#107C10", SelectedBG="#D7EDD7"),
        vis=["#5cc05c", "#2ca02c", "#107c10", "#0a4a0a"],
        song="Kinect Sports Theme",
    ),
    "xbox-360-nxe": dict(
        LIGHT, name="Xbox 360 NXE", wsz="Xbox-360-NXE", owner="Microsoft Corporation",
        subject="the New Xbox Experience (2008)", mark="Xbox logo", logo="logo-xbox-2010",
        logo_crop="left",
        title="Xbox 360", eq_title="Equalizer", pl_title="Music Library", gen_title="ALBUM ART",
        font=(NOTO.format("SemiBold"), None), font_semi=(NOTO.format("Regular"), None),
        font_bold=(NOTO.format("Bold"), None), digit_font=(NOTO.format("Regular"), None), digit_size=14,
        title_font="font", title_size=9, title_sp=0.3, title_shadow="#ffffff", title_extra="logo",
        bg="#d8ecf8", panel="#ffffff", panel_line="#9ab6ca", radius=4, panel_shadow=True, carousel=True,
        body=[(0, "#eaf5fc"), (0.5, "#a9d4ef"), (1, "#86c39a")],
        waves_main=[(98, 9, 6, 0.6, 1.0, [(84, 116, 4)]), (34, 8, 6, 2.0, 0.9, [(15, 52, 4)])],
        waves_eq=[(112, 4, 6, 1.2, 0.9, [(110, 116, 3)]), (26, 5, 6, 2.8, 0.9, [(15, 35, 3)])],
        wave_col="#ffffff", wave_w=3.0, wave_glow=0.6, edge=("#7f9db3", "#6a8aa0", "#ffffff"),
        bar_lit=("#ffffff", "#ffffff", "#eef5fa", "#dce9f2", "#c6d9e6", "#8eaabd"),
        bar_dim=("#ffffff", "#f4f6f8", "#e8ecef", "#dde1e5", "#cdd2d7", "#a2a8ae"),
        ink="#1f4e79", text="#2b3a45", text2="#5a6e7c", text3="#a6b4be", track="#c0ccd4", label="#5a7a90",
        title_fg="#2b3a45", title_dim="#8d9aa4", bar_icon="#4a5a66", bar_icon_dim="#9aa4ac",
        btn_pressed="#b8cfdf", press_ink="#2b3a45", tray=True,
        tray_cols=("#8fb0c6", "#e2eef6", "#fbfdfe"), play_ind="#2e8b1e", eq_lab="#4a6070",
        side="shell", side_col="#eef5fa", side_edge=("#7f9db3", "#c8d6e0"), groove="#dde7ee",
        strip=[(0, "#f4f9fc"), (1, "#cfe1ed")], strip_lines=("#c8d6e0", "#7f9db3"),
        pl=dict(NormalBG="#FFFFFF", Normal="#2B3A45", Current="#2E8B1E", SelectedBG="#D3E8F6"),
        vis=["#9fd8ff", "#4aa3e0", "#2e8b1e", "#14501a"],
        song="Avatar Party (NXE Mix)",
    ),
}

T = {}


def _colours(v):
    if isinstance(v, str) and v.startswith("#") and len(v) == 7:
        return hexc(v)
    if isinstance(v, dict):
        return {k: _colours(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_colours(x) for x in v]
    if isinstance(v, tuple):
        return tuple(_colours(x) for x in v)
    return v


def setup_theme(key):
    global T, OUT
    raw = {k: (v if k == "pl" else _colours(v)) for k, v in THEMES[key].items()}
    raw["key"] = key
    T = raw
    OUT = os.path.join(OUT_ROOT, key)
    os.makedirs(OUT, exist_ok=True)


def XB():
    """The light family (the Xbox 360 dashboards' pale bodies and tabs)."""
    return T["family"] == "light"


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
    base = int(round(base))
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


def wave_mask(w, h, cy, amp, n=16, phase=0.0, period=300.0, spread=6.0, strength=1.0, lw=0.8, glow=0.22):
    """A ribbon of n lines that swell and pinch as they flow, plus a soft glow along its core:
    XMB's wave (many hairlines), the original Xbox's tubes (a few thick ones), NXE's light streaks."""
    xs = np.linspace(-6, w + 6, 360)
    acc = np.zeros((h, w), np.float32)
    core = cy + amp * np.sin(2 * np.pi * xs / period + 0.9 + phase)
    width = spread * (0.55 + 0.45 * np.sin(2 * np.pi * xs / (period * 0.62) + 2.0 + phase))
    for k in range(n):
        t = k / max(1, n - 1) - 0.5
        ys = core + t * 2 * width + 0.8 * np.sin(2 * np.pi * xs / 70 + k * 0.45 + phase)
        pts = list(zip(xs, ys))
        m = mask(w, h, lambda d, S: d.line([(x * S, y * S) for x, y in pts], fill=255, width=max(1, int(lw * S))))
        acc += m * (0.07 + 0.16 * (1 - abs(t) * 2))
    g = Image.new("L", (w, h), 0)
    ImageDraw.Draw(g).line(list(zip(xs, core)), fill=255, width=5)
    g = np.asarray(g.filter(ImageFilter.GaussianBlur(4)), np.float32) / 255.0
    return np.clip((acc + glow * g) * strength, 0, 0.85)


def row_weight(h, ranges):
    """Per-row weight: 1 inside [(y0, y1, fade)], 0 elsewhere, smooth at the ends."""
    w = np.zeros(h, np.float32)
    for y0, y1, fade in ranges:
        for y in range(h):
            if y0 <= y <= y1:
                w[y] = max(w[y], 1.0)
            elif y0 - fade < y < y0:
                w[y] = max(w[y], (y - (y0 - fade)) / fade)
            elif y1 < y < y1 + fade:
                w[y] = max(w[y], ((y1 + fade) - y) / fade)
    return w[:, None]


def wire_grid(w, h):
    """The original dashboard's wire-frame mesh: a warped grid of faint lines."""
    def fn(d, S):
        for gx in range(-20, w + 20, 11):
            pts = [((gx + 4 * np.sin(y / 13.0 + gx / 40.0)) * S, y * S) for y in range(0, h + 1, 2)]
            d.line(pts, fill=255, width=max(1, int(0.6 * S)))
        for gy in range(-10, h + 10, 9):
            pts = [(x * S, (gy + 3 * np.sin(x / 21.0 + gy / 17.0)) * S) for x in range(0, w + 1, 2)]
            d.line(pts, fill=255, width=max(1, int(0.6 * S)))
    return mask(w, h, fn)


# ------------------------------------------------------------------------------------------
# Logos
# ------------------------------------------------------------------------------------------


def logo_rgba(size):
    """The theme's logo as (size, size, 4) floats; logo_crop "left" keeps the symbol of a lockup."""
    src = os.path.join(HERE, "source", T["logo"], "logo.svg")
    os.makedirs(SCRATCH, exist_ok=True)
    big = os.path.join(SCRATCH, f"{T['logo']}-{size * 8}.png")
    S8 = size * 8
    crop = T.get("logo_crop")
    if crop in ("left", "top"):
        # a lockup: keep its symbol, the part before the first empty gap along the axis
        subprocess.run(["/usr/bin/rsvg-convert", "-h", str(S8 * 2), src, "-o", big], check=True)
        im = Image.open(big).convert("RGBA")
        al = np.asarray(im)[..., 3] > 8
        prof = al.any(axis=0 if crop == "left" else 1)
        idx = np.nonzero(prof)[0]
        start = idx[0]
        end = start
        while end < len(prof) and prof[end]:
            end += 1
        im = im.crop((start, 0, end, im.height) if crop == "left" else (0, start, im.width, end))
        im = im.crop(im.getbbox())
        k = S8 / max(im.width, im.height)
        im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    else:
        subprocess.run(["/usr/bin/rsvg-convert", "-w", str(S8), "-h", str(S8), "--keep-aspect-ratio",
                        src, "-o", big], check=True)
        im = Image.open(big).convert("RGBA")
    sq = Image.new("RGBA", (S8, S8), (0, 0, 0, 0))
    sq.alpha_composite(im, ((S8 - im.width) // 2, (S8 - im.height) // 2))
    return np.asarray(sq.resize((size, size), Image.BOX), dtype=np.float32)


def put_logo(a, x, y, size):
    rgba = logo_rgba(size)
    al = rgba[..., 3] / 255.0
    if T["logo_mode"] == "mono":
        paint(a, x, y, al, T["logo_col"], 0.95)
    else:
        # un-premultiplied colour from the box filter's average
        rgb = rgba[..., :3]
        paint(a, x, y, al, rgb)


def guide_sphere(a, cx, cy, lit=True):
    """The Xbox 360 guide button: a chrome sphere with the green X, in the four-quadrant ring of light."""
    disc(a, cx, cy + 0.5, 11.2, (0, 0, 0), 0.15)
    disc(a, cx, cy, 10.8, (150, 156, 162))
    grad_disc(a, cx, cy, 10.2, (236, 238, 240), (196, 200, 204))
    ring = (124, 222, 52) if lit else (150, 156, 162)
    m = mask(26, 26, lambda d, S: d.ellipse((1.6 * S, 1.6 * S, 24.4 * S - 1, 24.4 * S - 1), fill=255))
    m -= mask(26, 26, lambda d, S: d.ellipse((4.0 * S, 4.0 * S, 22.0 * S - 1, 22.0 * S - 1), fill=255))
    gaps = mask(26, 26, lambda d, S: (d.rectangle((12.2 * S, 0, 13.8 * S, 26 * S), fill=255),
                                      d.rectangle((0, 12.2 * S, 26 * S, 13.8 * S), fill=255)))
    m = np.clip(m - gaps, 0, 1)
    x0, y0 = int(round(cx - 13)), int(round(cy - 13))
    if lit:
        glow = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)),
                          np.float32) / 255.0
        paint(a, x0, y0, glow, (150, 240, 70), 0.55)
    paint(a, x0, y0, m, ring)
    disc(a, cx, cy, 7.4, (120, 126, 132))
    grad_disc(a, cx, cy, 7.0, (255, 255, 255), (170, 176, 182))
    xm = mask(26, 26, lambda d, S: (
        d.line([(8.6 * S, 8.4 * S), (13 * S, 13 * S), (17.4 * S, 17.6 * S)], fill=255, width=int(2.6 * S)),
        d.line([(17.4 * S, 8.4 * S), (13 * S, 13 * S), (8.6 * S, 17.6 * S)], fill=255, width=int(2.6 * S))))
    sph = mask(26, 26, lambda d, S: d.ellipse(((13 - 6.6) * S, (13 - 6.6) * S, (13 + 6.6) * S - 1,
                                               (13 + 6.6) * S - 1), fill=255))
    xm = xm * sph
    paint(a, x0, y0, xm, grad_box(26, 26, (110, 200, 50), (20, 120, 20)))
    ellipse(a, cx, cy - 3.0, 4.6, 2.8, (255, 255, 255), 0.55)


def glow_of(fn, w, h, blur):
    """A blurred mask of whatever fn(canvas) paints in white on black (for glows)."""
    g = new(w, h, (0, 0, 0))
    fn(g)
    return np.asarray(Image.fromarray(np.clip(g[..., 0], 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(blur)), np.float32) / 255.0


def orb(a, cx, cy, r, top, bot, glow=None, pressed=False):
    """The original Xbox's glowing green jewel: a glossy orb with a bright core."""
    if glow is not None:
        m = glow_of(lambda g: disc(g, cx, cy, r, (255, 255, 255)), a.shape[1], a.shape[0], r * 0.6)
        paint(a, 0, 0, np.clip(m * 1.6, 0, 1), glow, 0.6 if pressed else 0.4)
    disc(a, cx, cy, r + 0.5, lerp(bot, (0, 0, 0), 0.45))
    grad_disc(a, cx, cy, r, lerp(top, (0, 0, 0), 0.15) if pressed else top, bot)
    disc(a, cx, cy + r * 0.25, r * 0.55, top, 0.35)
    ellipse(a, cx, cy - r * 0.45, r * 0.62, r * 0.36, (255, 255, 255), 0.35 if pressed else 0.65)


# ------------------------------------------------------------------------------------------
# Bars (titlebars)
# ------------------------------------------------------------------------------------------


def bar_rows(h, lit):
    t = new(1, h)
    s = h // 2
    hi, u0, u1, l0, l1, lo = T["bar_lit"] if lit else T["bar_dim"]
    vgrad_fill(t, 0, 0, 1, s, u0, u1)
    vgrad_fill(t, 0, s, 1, h - s, l0, l1)
    t[0, 0] = hi
    t[h - 1, 0] = lo
    return t


def bar(w, h, lit):
    return np.repeat(bar_rows(h, lit), w, axis=1).copy()


def ttl(s):
    return s.upper() if T["title_upper"] else s


def title_font():
    return font(T[T["title_font"]], T["title_size"])


def title_width(s):
    f = title_font()
    w = f.getlength(s) if XB() else sum(f.getlength(c) for c in s)
    return w + T["title_sp"] * (len(s) - 1)


def bar_title(a, s, cx, base, lit):
    f = title_font()
    if lit and T["title_shadow"] is not None:
        ttext_sp(a, s, f, cx, base + 1, T["title_shadow"], T["title_sp"], 0.55)
    ttext_sp(a, s, f, cx, base, T["title_fg"] if lit else T["title_dim"], T["title_sp"])


def mini_button(a, x, y, kind, lit=True, pressed=False):
    if pressed:
        rrect(a, x, y, 9, 9, 2 if T["radius"] else 0, T["btn_pressed"])
    col = T["bar_icon"] if lit else T["bar_icon_dim"]
    if pressed:
        col = T.get("press_ink", (255, 255, 255))
    mini_glyph(a, x, y, kind, col)


# ------------------------------------------------------------------------------------------
# Backgrounds (main and EQ windows); sprites copy theirs from these
# ------------------------------------------------------------------------------------------

MAINBG = None
EQBG = None


def at(src, x, y, w, h):
    return src[y:y + h, x:x + w].copy()


def body_column(h):
    return stops_col(h, T["body"])


def window_body(w, h, waves=()):
    a = np.repeat(body_column(h), w, axis=1).copy()
    if T.get("grid") is not None and waves:
        rows = [r for wv in waves for r in wv[5]]
        paint(a, 0, 0, wire_grid(w, h) * row_weight(h, rows) * 0.55, T["grid"])
    for cy, amp, n, phase, strength, rows in waves:
        m = wave_mask(w, h, cy, amp, n=n, phase=phase, strength=strength, lw=T.get("wave_w", 0.8),
                      glow=T.get("wave_glow", 0.22)) * row_weight(h, rows)
        paint(a, 0, 0, m, T["wave_col"])
    side, bottom, inner = T["edge"]
    rect(a, 0, 0, 1, h, side)
    rect(a, w - 1, 0, 1, h, side)
    rect(a, 0, h - 1, w, 1, bottom)
    if inner is not None:
        rect(a, 1, 14, 1, h - 15, inner)
    return a


def tray(a, x, y, w, h):
    """The recessed tray behind the transport and toggles (the 360 dashboards)."""
    line, top, bot = T.get("tray_cols", ((190, 195, 200), (214, 218, 222), (238, 240, 242)))
    rrect(a, x, y, w, h, 7, line)
    grad_rrect(a, x + 1, y + 1, w - 2, h - 2, 6, top, bot)


def card(a, x, y, w, h):
    """A display: the theme's panel, NXE's with a soft drop shadow (a card)."""
    if T["panel_shadow"]:
        rrect(a, x + 1, y + 2, w + 1, h + 1, T["radius"] + 1, (20, 50, 80), 0.18)
    panel(a, x, y, w, h)


def make_main_bg():
    a = window_body(275, 116, waves=T["waves_main"])
    if T["tray"]:
        tray(a, 13, 85, 148, 24)
        tray(a, 162, 85, 80, 24)
    card(a, 21, 20, 84, 42)
    for yy in (29, 34):
        disc(a, 74, yy + 1, 1.1, T["ink"])
    card(a, 109, 21, 159, 15)
    card(a, 109, 40, 159, 14)
    lab = T.get("label") or T["text2"]
    ptext(a, TINY, "KBPS", 129, 44, lab)
    ptext(a, TINY, "KHZ", 169, 44, lab)
    rail = T["rail"]
    if rail == "groove":
        rrect(a, 16, 74, 248, 6, 3, (176, 181, 186))
        grad_rrect(a, 17, 75, 246, 4, 2, (205, 209, 213), (232, 235, 237))
    elif rail == "line":
        rect(a, 16, 76, 248, 1, T["track"])
        rect(a, 16, 77, 248, 1, lerp(T["track"], body_column(116)[77, 0], 0.6))
    elif rail == "thin":
        rrect(a, 16, 76, 248, 2, 1, T["track"])
    else:
        rect(a, 16, 76, 248, 2, T["track"])
    if T["emblem"] == "guide":
        guide_sphere(a, 257.5, 98.5)
    else:
        put_logo(a, 248, 89, 19)
    return a


def carousel_card(a, x0, x1, y0, y1, slant, alpha):
    """A card further back in NXE's carousel, seen at an angle: its far edge shorter."""
    pts = [(x0, y0 + slant), (x1, y0), (x1, y1), (x0, y1 - slant)] if slant > 0 else \
          [(x0, y0), (x1, y0 - slant), (x1, y1 + slant), (x0, y1)]
    poly(a, pts, T["panel_line"], alpha)
    inset = [(px_ + (0.8 if i in (0, 3) else -0.8), py_ + (0.8 if i in (0, 1) else -0.8)) for i, (px_, py_) in
             enumerate(pts)]
    poly(a, inset, (255, 255, 255), alpha * 0.9)
    poly(a, [inset[0], inset[1], (inset[1][0], inset[1][1] + 6), (inset[0][0], inset[0][1] + 6)],
         (255, 255, 255), alpha * 0.6)


def make_eq_bg():
    a = window_body(275, 116, waves=T["waves_eq"])
    if T.get("carousel"):
        carousel_card(a, 3, 15, 44, 98, 5, 0.55)
        carousel_card(a, 262, 273, 44, 98, -5, 0.55)
    card(a, 85, 16, 115, 21)
    card(a, 16, 36, 245, 68)
    return a


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = at(MAINBG, 10, 22, 8, 43)
    if T["clutter"] == "blades":
        # the five blades' edges, stacked the way the dashboard shows the blades either side
        rrect(a, 0, 1, 8, 41, 2.5, (150, 156, 162))
        bounds = [2, 11, 18, 25, 33, 41]
        for i, ((letter, y, h), (_, colour)) in enumerate(zip(CLUTTER_SLOTS, BLADES)):
            c = hexc(colour)
            on = letter in lit_letters
            face = c if on else lerp(c, (255, 255, 255), 0.55)
            y0, y1 = bounds[i], bounds[i + 1]
            a[y0:y1, 1:7] = grad_box(6, y1 - y0, lerp(face, (255, 255, 255), 0.3), face).astype(np.int32)
            if i:
                rect(a, 1, y0, 6, 1, lerp(face, (0, 0, 0), 0.25))
            gy = y + (h - 5) // 2
            if on:
                ptext(a, TINY, letter, 3, gy + 1, lerp(c, (0, 0, 0), 0.45))
                ptext(a, TINY, letter, 2, gy, (255, 255, 255))
            else:
                ptext(a, TINY, letter, 2, gy, lerp(c, (0, 0, 0), 0.45))
        for (yy, xs) in ((2, (1, 6)), (40, (1, 6))):
            for xx in xs:
                a[yy, xx] = lerp(a[yy, xx], (150, 156, 162), 0.6)
    elif XB():
        r = 3 if T["radius"] else 0
        rrect(a, 0, 0, 8, 43, r, T["panel_line"] or T["track"])
        rrect(a, 1, 1, 6, 41, max(0, r - 1), T["panel"])
        for letter, y, h in CLUTTER_SLOTS:
            on = letter in lit_letters
            if on:
                rrect(a, 1, y, 6, h, 1.5 if r else 0, T["pill_on"][1])
            gy = y + (h - 5) // 2
            ptext(a, TINY, letter, 2, gy, (255, 255, 255) if on else T["text3"])
    else:
        rrect(a, 0, 0, 8, 43, 3, T["panel_line"])
        rrect(a, 1, 1, 6, 41, 2, T["panel"])
        for letter, y, h in CLUTTER_SLOTS:
            on = letter in lit_letters
            if on:
                rrect(a, 1, y, 6, h, 1.5, lerp(T["panel"], T.get("clutter_on", (255, 255, 255)), 0.22))
            gy = y + (h - 5) // 2
            ptext(a, TINY, letter, 2, gy, T.get("clutter_ink", (255, 255, 255)) if on else T["text3"])
    return a


METRO_TABS = ["home", "social", "video", "games", "music", "apps", "settings"]


def main_titlebar(lit):
    a = bar(275, 14, lit)
    extra = T["title_extra"]
    if extra == "tabs":
        # the Metro dashboard's pivot across the top, on the music tab
        f = font(T["font_semi"], 8)
        fb = font(T["font_bold"], 8)
        x = 20.0
        for tab in METRO_TABS:
            cur = tab == "music"
            ff = fb if cur else f
            col = (T["title_fg"] if lit else T["title_dim"]) if cur else \
                lerp(T["bar_lit"][3] if lit else T["bar_dim"][3], T["title_fg"] if lit else T["title_dim"], 0.62)
            ttext(a, tab, ff, x, 10, col)
            x += ff.getlength(tab) + 8
        assert x < 240, x
    else:
        bar_title(a, T["title"], 137.5, 10, lit)
    if extra == "dots":
        # the current blade's swatch either side of the name: Media, where the music plays
        c = hexc(BLADES[3][1]) if lit else (190, 194, 198)
        tw = title_width(T["title"])
        for cx in (137.5 - tw / 2 - 8, 137.5 + tw / 2 + 8):
            disc(a, cx, 7, 2.6, lerp(c, (0, 0, 0), 0.25))
            grad_disc(a, cx, 7, 2.1, lerp(c, (255, 255, 255), 0.45), c)
    elif extra == "logo":
        tw = title_width(T["title"])
        rgba = logo_rgba(11)
        al = rgba[..., 3] / 255.0
        col = rgba[..., :3] if lit else np.repeat(rgba[..., :3].mean(-1, keepdims=True), 3, -1)
        paint(a, int(round(137.5 - tw / 2 - 15)), 1, al, col, 1.0 if lit else 0.6)
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
# cbuttons.bmp (136 x 36): controller face buttons, jewels, tiles or plain glyphs
# ------------------------------------------------------------------------------------------

FACE = {
    # face top, face bottom, glyph: the controller's A (green), B (red), Y (yellow), silver for the rest
    "play": ((150, 228, 96), (40, 140, 28), (255, 255, 255)),
    "stop": ((255, 120, 104), (196, 26, 30), (255, 255, 255)),
    "pause": ((255, 228, 110), (222, 160, 0), (96, 66, 0)),
    "previous": ((255, 255, 255), (184, 189, 194), (62, 67, 72)),
    "next": ((255, 255, 255), (184, 189, 194), (62, 67, 72)),
    "eject": ((255, 255, 255), (184, 189, 194), (62, 67, 72)),
}
GLYPH_S = {"play": 4.4, "pause": 3.6, "stop": 3.3, "previous": 3.5, "next": 3.5, "eject": 3.4}


def face_button(a, kind, cx, cy, r, pressed):
    if T.get("face"):
        top, bot, ink = T["face"].get(kind, T["face"]["all"])
        orb(a, cx, cy, r, top, bot, T.get("thumb_glow"), pressed)
        o = 0.5 if pressed else 0.0
        s = GLYPH_S[kind] * (r / 8.0)
        icon(a, kind, cx + (0.6 if kind == "play" else 0) + o, cy + o, s, ink)
        return
    top, bot, ink = FACE[kind]
    if pressed:
        top, bot = lerp(top, (0, 0, 0), 0.18), lerp(bot, (0, 0, 0), 0.18)
    disc(a, cx, cy + 0.7, r + 0.9, (0, 0, 0), 0.16)
    disc(a, cx, cy, r + 0.6, lerp(bot, (0, 0, 0), 0.3))
    grad_disc(a, cx, cy, r, top, bot)
    ellipse(a, cx, cy + r * 0.42, r * 0.62, r * 0.36, lerp(top, (255, 255, 255), 0.3), 0.45)
    ellipse(a, cx, cy - r * 0.45, r * 0.68, r * 0.40, (255, 255, 255), 0.30 if pressed else 0.62)
    o = 0.5 if pressed else 0.0
    s = GLYPH_S[kind] * (r / 8.0)
    gx = cx + (0.6 if kind == "play" else 0) + o
    icon(a, kind, gx, cy + o, s, ink)


def xmb_glyph(a, kind, cx, cy, s, pressed):
    if pressed:
        g = new(a.shape[1], a.shape[0], (0, 0, 0))
        icon(g, kind, cx, cy, s, (255, 255, 255))
        m = np.asarray(Image.fromarray(g[..., 0].astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)),
                       np.float32) / 255.0
        paint(a, 0, 0, np.clip(m * 2.2, 0, 1), T["glow"], 0.85)
    icon(a, kind, cx, cy + 0.8, s, T["shadow"])
    icon(a, kind, cx, cy, s, T["glyph_play"] if pressed or kind == "play" else T["glyph"])


def tile_glyph(a, kind, w, h, pressed):
    """Metro's flat squares, Fluent's rounded tiles: a tile with a white glyph, play in green."""
    tl = T["tile"]
    if kind == "play":
        face, ink = (tl["play_press"] if pressed else tl["play"]), tl["ink_play"]
    elif kind == "eject" and "eject" in tl:
        face, ink = (lerp(tl["eject"], (0, 0, 0), 0.12) if pressed else tl["eject"]), tl["ink_eject"]
    else:
        face, ink = (tl["press"] if pressed else tl["face"]), tl["ink"]
    rrect(a, 1, 1, w - 2, h - 2, tl["r"], face)
    s = {"play": 4.2, "pause": 3.4, "stop": 3.1, "previous": 3.3, "next": 3.3, "eject": 3.2}[kind]
    icon(a, kind, w / 2 + (0.5 if kind == "play" else 0), h / 2, s, ink)


CB_POS = {"previous": (16, 88), "play": (39, 88), "pause": (62, 88), "stop": (85, 88), "next": (108, 88)}


def transport_cell(kind, w, h, pressed):
    x, y = CB_POS.get(kind, (136, 89))
    a = at(MAINBG, x, y, w, h)
    cx, cy = w / 2, h / 2
    if T["transport"] == "face":
        face_button(a, kind, cx, cy, 7.9 if h == 18 else 6.7, pressed)
    elif T["transport"] == "tile":
        tile_glyph(a, kind, w, h, pressed)
    else:
        s = {"play": 5.0, "pause": 4.2, "stop": 3.8, "previous": 4.0, "next": 4.0, "eject": 3.8}[kind]
        xmb_glyph(a, kind, cx + (0.6 if kind == "play" else 0), cy, s, pressed)
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


def xb_pill(a, x, y, w, h, on, pressed):
    """A chunky rounded tab: white gloss, green gloss when on (Metro: flat squares)."""
    r = h / 2 if T["pill_r"] is None else T["pill_r"]
    top, bot, line = T["pill_on"] if on else T["pill_off"]
    if pressed:
        top, bot = lerp(top, (0, 0, 0), 0.12), lerp(bot, (0, 0, 0), 0.12)
    rrect(a, x, y, w, h, r, line)
    grad_rrect(a, x + 1, y + 1, w - 2, h - 2, max(0, r - 1), top, bot)
    if T["pill_gloss"]:
        k = 1.0 if on else T.get("gloss_off", 1.0)
        grad_rrect(a, x + 2, y + 1, w - 4, (h - 2) // 2, max(0, r - 2), (255, 255, 255), (255, 255, 255),
                   (0.25 if pressed else 0.5) * k)


def tile(a, x, y, w, h, on, pressed):
    tt = T["toggle_tile"]
    face = (tt["on_press"] if pressed else tt["on"]) if on else (tt["press"] if pressed else tt["off"])
    rrect(a, x, y, w, h, tt["r"], face)
    return tt["ink_on"] if on else tt["ink_off"]


def toggle_icon_cell(kind, w, on, pressed):
    x0 = 164 if kind == "shuffle" else 210
    a = at(MAINBG, x0, 89, w, 15)
    cx, cy = w / 2, 7.5
    ic = shuffle_icon if kind == "shuffle" else repeat_icon
    if T["toggle"] == "pill":
        xb_pill(a, 1, 1, w - 2, 13, on, pressed)
        col = T["pill_ink_on"] if on else T["pill_ink_off"]
        if on and T.get("pill_ink_shadow", (40, 110, 16)) is not None:
            ic(a, cx, cy + 0.6, T.get("pill_ink_shadow", (40, 110, 16)))
        ic(a, cx, cy, col)
    elif T["toggle"] == "tile":
        col = tile(a, 1, 1, w - 2, 13, on, pressed)
        ic(a, cx, cy, col)
    else:
        if pressed:
            rrect(a, int(cx - 10), 0, 20, 15, 4, (255, 255, 255), 0.14)
        col = T["tog_on"] if on else (T["tog_press"] if pressed else T["tog_off"])
        ic(a, cx, cy + 0.3, T["shadow"])
        ic(a, cx, cy - 0.5, col)
        if on:
            frect(a, cx - 5, 14, cx + 5, 15, T["tog_on"], 0.5)
            ellipse(a, cx, 14.5, 7, 1.6, T.get("tog_glow", (170, 210, 255)), 0.35)
    return a


def text_toggle(a, x, y, w, h, txt, on, pressed):
    """EQ/PL, ON/AUTO and PRESETS: a tab, a tile, or XMB's thin outlined label."""
    if T["toggle"] == "pill":
        xb_pill(a, x, y, w, h, on, pressed)
        f = font(T["font_bold"], 7)
        if on and T.get("pill_ink_shadow", (40, 110, 16)) is not None:
            ttext(a, txt, f, x + w / 2, y + h - 3.0 + 0.6, T.get("pill_ink_shadow", (40, 110, 16)), "c", 0.6)
        ttext(a, txt, f, x + w / 2, y + h - 3.0, T["pill_ink_on"] if on else T["pill_ink_off"], "c")
    elif T["toggle"] == "tile":
        col = tile(a, x, y, w, h, on, pressed)
        ttext(a, txt, font(T["font_bold"], 7), x + w / 2, y + h - 3.0, col, "c")
    else:
        bgc = a[y + h // 2, x + 1].astype(np.float32)
        rrect(a, x, y, w, h, 3, lerp(bgc, T.get("tt_line", (160, 190, 235)), 0.55 if on else 0.3))
        rrect(a, x + 1, y + 1, w - 2, h - 2, 2, lerp(T["panel"], (255, 255, 255), 0.2 if on else (0.08 if pressed
                                                                                                    else 0)))
        f = font(T["font_semi"], 7)
        ttext(a, txt, f, x + w / 2, y + h - 3.0, (255, 255, 255) if on else T.get("tt_off", (140, 164, 204)), "c")


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
        col = T["ink"] if on else lerp(T["panel"], T["ink"], 0.25)
        ptext_c(a, TINY, "STEREO", 14, y + 4, col)
        ptext_c(a, TINY, "MONO", 29 + 13, y + 4, col)
    return a


def make_playpaus():
    a = new(48, 9, T["panel"])
    icon(a, "play", 4.6, 4.5, 3.4, T["play_ind"])
    icon(a, "pause", 9 + 4.5, 4.5, 3.2, T["ink"])
    icon(a, "stop", 18 + 4.5, 4.5, 3.0, T["ink"])
    disc(a, 39 + 1.5, 4.5, 1.0, lerp(T["panel"], T["ink"], 0.4))
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["panel"])
    f = font(T["digit_font"], T["digit_size"])
    for n in range(10):
        ttext(a, str(n), f, 9 * n + 4.5, 11, T["ink"], "c")
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
            key = ch if ch in FONT5 else ch.upper()
            ptext(a, FONT5, key, col * 5, row * 6, T["ink"])
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def xb_rail_fill(a, x0, x1, y, h):
    if x1 - x0 >= 2:
        grad_rrect(a, int(x0), y, int(round(x1 - x0)), h, h / 2, *T["fill"])


def seek_thumb(selected):
    a = at(MAINBG, 120, SEEK_Y, 29, 10)
    st = T["seek_thumb"]
    if st == "tab":
        # the played part as a green tail, then a chunky green tab
        for x in range(0, 20):
            t = x / 19
            t = t * t * (3 - 2 * t)
            for yy in (3, 4, 5, 6):
                cg = (120, 196, 56) if yy < 5 else (90, 172, 36)
                a[yy, x] = lerp(a[yy, x], cg, t)
        xb_pill(a, 15, 0, 14, 10, True, selected)
        rect(a, 21, 3, 1, 4, (44, 118, 18))
        rect(a, 22, 3, 1, 4, (210, 240, 160))
    elif st in ("dot", "orb"):
        cx = 24.5
        for x in range(0, 24):
            t = x / 23
            a[4, x] = lerp(a[4, x], T["fill"], t * t)
            a[5, x] = lerp(a[5, x], T.get("tail2", (200, 220, 255)), t * t * 0.7)
        if st == "dot":
            disc(a, cx, 4.5, 4.4, T["thumb_glow"], 0.25 if not selected else 0.45)
            disc(a, cx, 4.5, 3.0, (255, 255, 255))
        else:
            orb(a, cx, 4.5, 3.8, (232, 255, 160), (52, 160, 24), T["thumb_glow"], selected)
    else:
        # flat: the played part in the fill colour fading in, then a disc (Fluent) or a bar (Metro)
        for x in range(0, 24):
            t = min(1.0, x / 14)
            for yy in (4, 5):
                a[yy, x] = lerp(a[yy, x], T["fill"], t)
        if st == "disc":
            disc(a, 24.5, 5, 4.6, (12, 12, 12))
            disc(a, 24.5, 5, 4.0, (255, 255, 255) if not selected else (220, 220, 220))
            disc(a, 24.5, 5, 1.8, T["fill"])
        else:
            rect(a, 23, 0, 4, 10, (30, 30, 30) if not selected else (16, 124, 16))
    return a


def make_posbar(main):
    a = new(307, 10, T["bg"])
    a[0:10, 0:248] = MAINBG[SEEK_Y:SEEK_Y + 10, 16:264]
    a[0:10, 248:277] = seek_thumb(False)
    a[0:10, 278:307] = seek_thumb(True)
    a[0:10, 277] = MAINBG[SEEK_Y:SEEK_Y + 10, 140]
    return a


def h_fill(t, x0, x1):
    rail = T["rail"]
    if rail == "groove":
        xb_rail_fill(t, x0, x1, 5, 3)
    elif rail == "line":
        if x1 - x0 >= 1:
            frect(t, x0, 5.6, x1, 7.4, T["fill"])
    else:
        if x1 - x0 >= 1:
            frect(t, x0, 6, x1, 8, T["fill"], 1 if rail == "thin" else 0)


def h_rail(t, x0, x1, fill_from=None, fill_to=None):
    """A slider rail on a 15-row frame (the thumb's row is 1..11), filled between fill_from and fill_to."""
    rail = T["rail"]
    if rail == "groove":
        rrect(t, x0, 4, x1 - x0, 5, 2.5, (176, 181, 186))
        grad_rrect(t, x0 + 1, 5, x1 - x0 - 2, 3, 1.5, (205, 209, 213), (232, 235, 237))
        if fill_to is not None:
            h_fill(t, x0 + 1 if fill_from is None else fill_from, fill_to)
    elif rail == "line":
        frect(t, x0, 6, x1, 7, T["track"])
        if fill_to is not None:
            h_fill(t, x0 if fill_from is None else fill_from, fill_to)
    else:
        frect(t, x0, 6, x1, 8, T["track"], 1 if rail == "thin" else 0)
        if fill_to is not None:
            h_fill(t, x0 if fill_from is None else fill_from, fill_to)


def slider_thumb(selected):
    t = at(MAINBG, 120, 58, 14, 11)
    st = T["slider_thumb"]
    if st == "pill":
        xb_pill(t, 1, 1, 12, 9, False, selected)
        rect(t, 6, 3, 1, 5, (150, 156, 162))
        rect(t, 7, 3, 1, 5, (255, 255, 255))
    elif st == "bar":
        disc(t, 7, 5.5, 5, T["thumb_glow"], 0.3 if not selected else 0.5)
        frect(t, 5.5, 1.5, 8.5, 9.5, (255, 255, 255), 1.5)
    elif st == "orb":
        orb(t, 7, 5.5, 4.0, (232, 255, 160), (52, 160, 24), T["thumb_glow"], selected)
    elif st == "disc":
        disc(t, 7, 6, 4.8, (12, 12, 12))
        disc(t, 7, 6, 4.2, (255, 255, 255) if not selected else (220, 220, 220))
        disc(t, 7, 6, 1.8, T["fill"])
    else:
        rect(t, 5, 1, 4, 10, (30, 30, 30) if not selected else (16, 124, 16))
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
            h_fill(t, 28 - reach, 28 + reach)
        frect(t, 27.5, 2, 28.5, 4, T["text2"] if XB() else T["eq_lab"])
        a[y:y + 15, 0:68] = t
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = bar(275, 14, lit)
    bar_title(a, ttl(T["eq_title"]), 137.5, 10, lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    rect(a, x, y, 14, 63, T["panel"])
    v = n / 27
    centre = (1 - v) * 51 + 6.0
    zero = 31.5
    lo, hi = min(centre, zero), max(centre, zero)
    rail = T["rail"]
    if rail == "groove":
        rrect(a, x + 4, y + 3, 6, 57, 3, (190, 200, 180))
        grad_rrect(a, x + 5, y + 4, 4, 55, 2, (214, 222, 206), (236, 241, 230))
        if hi - lo >= 1:
            m = mask(14, 63, lambda d, S: d.rounded_rectangle((5 * S, lo * S, 9 * S - 1, hi * S - 1), radius=2 * S,
                                                              fill=255))
            paint(a, x, y, m, grad_box(14, 63, (170, 224, 90), (40, 140, 20)))
    elif rail == "line":
        frect(a, x + 6.5, y + 3, x + 7.5, y + 60, T["track"])
        if hi - lo >= 0.5:
            frect(a, x + 6, y + lo, x + 8, y + hi, T["fill"])
    else:
        frect(a, x + 6, y + 3, x + 8, y + 60, T["track"], 1 if rail == "thin" else 0)
        if hi - lo >= 0.5:
            frect(a, x + 6, y + lo, x + 8, y + hi, T["fill"], 1 if rail == "thin" else 0)


def eq_thumb(selected):
    t = new(11, 11, T["panel"])
    st = T["slider_thumb"]
    if st == "pill":
        disc(t, 5.5, 5.9, 4.9, (0, 0, 0), 0.15)
        disc(t, 5.5, 5.5, 4.8, (150, 156, 162))
        grad_disc(t, 5.5, 5.5, 4.1, (255, 255, 255), (206, 210, 214) if not selected else (180, 186, 192))
        disc(t, 5.5, 5.5, 1.5, (76, 170, 30))
    elif st == "bar":
        disc(t, 5.5, 5.5, 5.0, T["thumb_glow"], 0.3 if not selected else 0.5)
        disc(t, 5.5, 5.5, 3.2, (255, 255, 255))
    elif st == "orb":
        orb(t, 5.5, 5.5, 3.8, (232, 255, 160), (52, 160, 24), T["thumb_glow"], selected)
    elif st == "disc":
        disc(t, 5.5, 5.5, 4.8, (12, 12, 12))
        disc(t, 5.5, 5.5, 4.2, (255, 255, 255) if not selected else (220, 220, 220))
        disc(t, 5.5, 5.5, 1.8, T["fill"])
    else:
        rect(t, 1, 3, 9, 5, (30, 30, 30) if not selected else (16, 124, 16))
    return t


def make_eqmain():
    global EQBG
    EQBG = make_eq_bg()
    a = new(275, 315, T["bg"])
    a[0:116] = EQBG
    a[0:14, :] = eq_titlebar(True)
    lab = T.get("label") or T["text2"]
    rect(a, 40, 40, 1, 60, lerp(T["panel"], T["ink"], 0.15))
    for lbl, yy in (("+12DB", 41), ("+0DB", 67), ("-12DB", 92)):
        ptext_c(a, TINY, lbl, 58, yy, lab)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    blab = T["eq_lab"]
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
        if T["toggle"] == "pill":
            xb_pill(cell, 0, 0, 44, 12, False, pressed)
            ttext(cell, "PRESETS", font(T["font_bold"], 7), 22, 9, T["pill_ink_off"], "c")
        elif T["toggle"] == "tile":
            text_toggle(cell, 0, 0, 44, 12, "PRESETS", False, pressed)
        else:
            text_toggle(cell, 0, 0, 44, 12, "PRESETS", pressed, False)
        a[y:y + 12, 224:268] = cell
    rect(a, 0, 294, 113, 19, T["panel"])
    rect(a, 0, 294 + 9, 113, 1, lerp(T["panel"], T["ink"], 0.15))
    for x in range(0, 113, 12):
        for y in range(0, 19, 3):
            px(a, x, 294 + y, lerp(T["panel"], T["ink"], 0.12))
    for r in range(19):
        px(a, 115, 294 + r, ramp(T["graph"], r / 18))
    for x in range(113):
        px(a, x, 314, lerp(T["panel"], T["ink"], 0.4) if x % 3 != 2 else T["panel"])
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------


def frame_side(w, h, left):
    """A playlist/gen side tile: the white shell edge, a piano-black strip, or a flat edge."""
    t = new(w, h)
    side = T["side"]
    if side == "shell":
        t[:, :] = T["side_col"]
        outer, inner = T["side_edge"]
        if left:
            rect(t, 0, 0, 1, h, outer)
            rect(t, 1, 0, 1, h, (255, 255, 255))
            rect(t, w - 1, 0, 1, h, inner)
        else:
            rect(t, w - 1, 0, 1, h, outer)
            rect(t, 0, 0, 1, h, inner)
    elif side == "gloss_black":
        for x in range(w):
            u = x / max(1, w - 1)
            u = u if left else 1 - u
            t[:, x] = lerp((0, 0, 0), (26, 26, 28), np.sin(u * np.pi) * 0.9)
        rect(t, w - 1 if left else 0, 0, 1, h, T["side_edge"][0])
    else:
        t[:, :] = T["side_col"]
        rect(t, 0 if left else w - 1, 0, 1, h, T["side_edge"][0])
        if len(T["side_edge"]) > 1:
            rect(t, w - 1 if left else 0, 0, 1, h, T["side_edge"][1])
    return t


def bottom_strip(w, h):
    t = new(w, h)
    t[:, :] = stops_col(h, T["strip"])
    top, second = T["strip_lines"]
    rect(t, 0, 0, w, 1, top)
    if XB():
        rect(t, 0, h - 1, w, 1, second)
    else:
        rect(t, 0, 1, w, 1, second)
    return t


def pill_button(t, x, y, w, h, txt):
    if T["toggle"] == "pill" and XB():
        xb_pill(t, x, y, w, h, False, False)
        ttext(t, txt, font(T["font_bold"], 7), x + w / 2, y + h // 2 + 3, T["pill_ink_off"], "c")
    elif T["toggle"] == "tile":
        col = tile(t, x, y, w, h, False, False)
        ttext(t, txt, font(T["font_bold"], 7), x + w / 2, y + h // 2 + 3, col, "c")
    else:
        line, top, bot, ink = T["btn"]
        rrect(t, x, y, w, h, 3, line)
        grad_rrect(t, x + 1, y + 1, w - 2, h - 2, 2, top, bot)
        ttext(t, txt, font(T["font_semi"], 7), x + w / 2, y + h // 2 + 3, ink, "c")


def readout(t, x, y, w, h):
    rrect(t, x - 1, y - 1, w + 2, h + 2, 2 if T["radius"] else 0, T["panel_line"] or T["track"])
    rect(t, x, y, w, h, T["panel"])


def music_note(a, x, y, col):
    """XMB's Music category icon, 8x9."""
    disc(a, x + 2.0, y + 7.2, 1.8, col)
    disc(a, x + 6.4, y + 6.2, 1.8, col)
    frect(a, x + 3.1, y + 1.2, x + 3.9, y + 7.2, col)
    frect(a, x + 7.5, y + 0.2, x + 8.3, y + 6.2, col)
    poly(a, [(x + 3.1, y + 1.2), (x + 8.3, y + 0.2), (x + 8.3, y + 1.6), (x + 3.1, y + 2.6)], col)


def pl_title_tile(lit):
    t = bar(100, 20, lit)
    s = ttl(T["pl_title"])
    icon_ = T["pl_icon"]
    shift = 5 if icon_ == "blade" else (6 if icon_ == "note" else 0)
    bar_title(t, s, 50 + shift, 13, lit)
    tw = title_width(s)
    if icon_ == "blade":
        c = hexc(BLADES[3][1]) if lit else (190, 194, 198)
        x0 = 50 + shift - tw / 2 - 11
        rrect(t, int(x0), 6, 7, 9, 2, lerp(c, (0, 0, 0), 0.25))
        grad_rrect(t, int(x0) + 1, 7, 5, 7, 1.5, lerp(c, (255, 255, 255), 0.45), c)
    elif icon_ == "note":
        music_note(t, 50 + shift - tw / 2 - 13, 5, T["title_fg"] if lit else T["title_dim"])
    return t


def scroll_thumb(sel):
    t = new(8, 18, T["groove"])
    sc = T["scroll"]
    if XB():
        if T["pill_gloss"]:
            m = mask(8, 18, lambda d, S: d.rounded_rectangle((1 * S, 1 * S, 7 * S - 1, 17 * S - 1), radius=3 * S,
                                                             fill=255))
            paint(t, 0, 0, m, sc[0])
            grad_rrect(t, 2, 2, 4, 14, 2, sc[1], sc[2] if not sel else sc[3])
        else:
            rect(t, 2, 1, 4, 16, sc[0] if not sel else lerp(sc[0], (0, 0, 0), 0.3))
    else:
        frect(t, 2.5, 1, 5.5, 17, sc[1] if sel else sc[0], 1.5)
    return t


def make_pledit():
    a = new(280, 186, T["bg"])
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 127:152] = bar(25, 20, lit)
        a[y:y + 20, 0:25] = bar(25, 20, lit)
        a[y:y + 20, 26:126] = pl_title_tile(lit)
        t = bar(25, 20, lit)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t

    a[42:71, 0:12] = frame_side(12, 29, True)
    t = frame_side(20, 29, False)
    rect(t, 5, 0, 8, 29, T["groove"])
    a[42:71, 31:51] = t
    b = bar(9, 20, True)[3:12].copy()
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = b
    for x, sel in ((52, False), (61, True)):
        a[53:71, x:x + 8] = scroll_thumb(sel)

    t = bottom_strip(125, 38)
    rect(t, 0, 0, 1, 38, T["edge"][0])
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        pill_button(t, bx, 9, 22, 16, lbl)
    a[72:110, 0:125] = t

    t = bottom_strip(150, 38)
    rect(t, 149, 0, 1, 38, T["edge"][0])
    readout(t, 6, 9, 56, 8)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        icon(t, kind, bx + 5, 22 + 5, 2.6 if kind != "play" else 3.0, T["mini_ink"])
    readout(t, 65, 22, 33, 8)
    rect(t, 84, 24, 1, 1, T["ink"])
    rect(t, 84, 27, 1, 1, T["ink"])
    pill_button(t, 106, 9, 22, 16, "LIST")
    for k in range(4):
        for j in range(k + 1):
            disc(t, 146.5 - 3 * k + 3 * j, 34.5 - 3 * j, 0.7, T["grip"])
    a[72:110, 126:276] = t

    a[0:38, 179:204] = bottom_strip(25, 38)
    return a


GEN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gen_letter_cells(lit):
    """Each capital in its own cell (the bar's rows 4..10), for gen.bmp's letter rows."""
    f = font(T[T["gen_font"]], 8)
    col = T["title_fg"] if lit else T["title_dim"]
    rows = bar_rows(20, lit)[4:11]
    cells = []
    for c in GEN_LETTERS:
        adv = int(round(f.getlength(c))) + T["gen_pad"]
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
        t = bottom_strip(w, 14)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    disc(t, w - 3.5 - 3 * k + 3 * j, 11.5 - 3 * j, 0.7, T["grip"])
        return t

    t = bottom(125, False)
    rect(t, 0, 0, 1, 14, T["edge"][0])
    a[42:56, 0:125] = t
    t = bottom(125, True)
    rect(t, 124, 0, 1, 14, T["edge"][0])
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
    if T["key"] == "xbox-360":
        return [pl["NormalBG"], pl["Normal"], (244, 245, 246), (60, 66, 72), (43, 47, 51), (200, 205, 210),
                pl["SelectedBG"], (232, 242, 216), (16, 124, 16), (255, 255, 255), (170, 176, 182),
                (155, 200, 72), (244, 245, 246), (226, 229, 232), (120, 196, 56), (210, 214, 218), (76, 170, 30),
                (244, 245, 246)]
    if T["key"] == "ps3":
        return [pl["NormalBG"], pl["Normal"], (6, 26, 64), (230, 236, 246), (255, 255, 255), (40, 70, 120),
                pl["SelectedBG"], (12, 12, 14), (200, 214, 236), (70, 70, 74), (0, 0, 0), (90, 140, 220),
                (6, 26, 64), (8, 16, 34), (150, 172, 210), (30, 50, 90), (255, 255, 255), (6, 26, 64)]
    bg, text, panel_ = T["bg"], T["text"], T["panel"]
    white, black = (255, 255, 255), (0, 0, 0)
    return [pl["NormalBG"], pl["Normal"], bg, text, text, lerp(bg, text, 0.15), pl["SelectedBG"], panel_,
            T["text2"], lerp(panel_, white, 0.25), lerp(panel_, black, 0.3), pl["Current"],
            bg, lerp(bg, text, 0.06), T["text3"], lerp(bg, text, 0.12), T["text2"], bg]


def make_genex():
    a = new(256, 64, T["bg"])
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    for y, pressed in ((1, False), (16, True)):
        cell = new(47, 15, T["bg"])
        if T["toggle"] == "pill" and XB():
            xb_pill(cell, 0, 0, 47, 15, False, pressed)
        elif T["toggle"] == "tile":
            tile(cell, 0, 0, 47, 15, False, pressed)
        else:
            pill_button(cell, 0, 0, 47, 15, "")
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
    out.append((T["peaks"], "peaks"))
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
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{n} — a personal skin in the style of {T['subject']}.\n"
            f"{T['mark']} © {o}; private use only.\n\n"
            f"A classic (Winamp 2.x format) skin, generated by a script (gen_skin.py). Not affiliated\n"
            f"with {o}.\n"
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
             title=f"{T['name']} - {T['song']}", bars=bars)
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
