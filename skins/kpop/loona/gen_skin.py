#!/usr/bin/python3
"""LOONA: personal fan skins for ytminamp's Winamp mode (classic Winamp 2.x format), never published.

Forked from skins/ember/gen_skin.py: the same sheets, layouts and preview logic, with the fixed
Ember palette turned into per-theme palettes. Everything is drawn here from code except the real
logo in each titlebar (the LOOΠΔ wordmark, or the Odd Eye Circle one), read from source/ at
generation time. The album covers under source/ were only looked at for palette and motifs.

Themes (no argument builds all ten; outputs beside this script, sheets in out/<theme>/):
  loona            LOONA.wsz                  the twelve: night sky, twelve moons, an eclipse
  1-3              LOONA-1-3.wsz              LOONA 1/3 (Love & Live): pastel aqua, YeoJin as the slash
  odd-eye-circle   LOONA-Odd-Eye-Circle.wsz   Odd Eye Circle (Max & Match): black/white, red/blue/purple
  yyxy             LOONA-yyxy.wsz             yyxy (beauty&thebeat): green school tartan, burgundy
  plus-plus x-x hash 12-00 and flip-that      the album eras: LOONA-Plus-Plus.wsz ... LOONA-Flip-That.wsz
Each also draws preview.png (loona) or preview-<theme>.png.
Light variants (light glass, dark ink, light playlist): loona-light, 1-3-light, odd-eye-circle-light,
yyxy-light, hash-light, and-light -> LOONA-<...>-Light.wsz.

    /usr/bin/python3 -I gen_skin.py                     # all
    /usr/bin/python3 -I gen_skin.py --theme yyxy        # one (repeatable; bare names work too)
    /usr/bin/python3 -I gen_skin.py --list

LOONA name, marks and logos (c) Blockberry Creative; private use only.
"""

import os
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.join(HERE, "out")
OUT = OUT_ROOT

# ------------------------------------------------------------------------------------------
# Members: reveal order, colour (the moons of LOONA's video openings, as sampled by fans; see
# README.md for the sources and the conflicts), name as shown.
# ------------------------------------------------------------------------------------------

MEMBERS = [
    ("heejin", "HEEJIN", (0xED, 0x00, 0x8E)),
    ("hyunjin", "HYUNJIN", (0xFF, 0xCA, 0x14)),
    ("haseul", "HASEUL", (0x03, 0xA2, 0x33)),
    ("yeojin", "YEOJIN", (0xFE, 0x97, 0x02)),
    ("vivi", "VIVI", (0xFF, 0xC5, 0xC8)),
    ("kimlip", "KIM LIP", (0xD9, 0x00, 0x11)),
    ("jinsoul", "JINSOUL", (0x08, 0x01, 0xD5)),
    ("choerry", "CHOERRY", (0xBA, 0x01, 0xDE)),
    ("yves", "YVES", (0x79, 0x01, 0x05)),
    ("chuu", "CHUU", (0xFE, 0xA8, 0x7D)),
    ("gowon", "GO WON", (0x02, 0xBC, 0xA1)),
    ("olivia", "OLIVIA HYE", (0xC0, 0xC0, 0xC0)),
]
MEMBER = {k: (n, c) for k, n, c in MEMBERS}
SEP = (255, 0, 255)          # gen.bmp letter separators (never shown)


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


def step(stops, t):
    """The stop nearest t (no blending: member colours stay themselves)."""
    t = max(0.0, min(1.0, t))
    return stops[int(round(t * (len(stops) - 1)))]


def luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def lift(c, floor=70):
    """A member colour made visible on a dark ground (JinSoul's blue, Yves's burgundy)."""
    if luma(c) >= floor:
        return c
    for i in range(1, 41):
        d = lerp(c, (255, 255, 255), i / 40)
        if luma(d) >= floor:
            return d
    return c


def sink(c, ceil=120):
    """A member colour made readable on a light ground (HyunJin's yellow, ViVi's pink)."""
    if luma(c) <= ceil:
        return c
    for i in range(1, 41):
        d = lerp(c, (0, 0, 0), i / 40)
        if luma(d) <= ceil:
            return d
    return c


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    # The group: a night sky, moonlight-white glass, the twelve moons.
    "loona": dict(
        wsz="LOONA.wsz", preview="preview.png", name="LOONA",
        members=[k for k, _, _ in MEMBERS],
        word=[("LOGO", None)],
        eq_title="LOOΠΔ EQUALIZER", pl_title="LOOΠΔ PLAYLIST",
        texture="stars", light=False, emblem="eclipse", names_strip=False,
        body=(12, 14, 34), body_hi=(48, 54, 92), body_lo=(2, 3, 12), slot=(7, 8, 22),
        face_top=(40, 44, 78), face_bot=(20, 22, 46), face_hi=(70, 76, 120), face_pr=(10, 11, 26),
        label=(170, 178, 220), label_dim=(100, 106, 150),
        trim=(150, 156, 206), trim_hi=(220, 226, 255), trim_lo=(62, 66, 116),
        disp=(4, 5, 16), ink=(232, 238, 255), ink_hi=(255, 255, 255), ghost=(20, 24, 50),
        ink_mid=(120, 128, 180), track=(22, 26, 52),
        accent=(255, 226, 140),                      # the moon
        thumb=MEMBER["olivia"][1],                   # the twelfth member: the seek/slider thumbs
        plate=(4, 5, 16), plate_dim=(16, 18, 36), title_dim=(110, 116, 160),
        pl_normal=(178, 186, 226), pl_current=(255, 226, 140), pl_selbg=(40, 30, 78),
        art=[(20, 22, 60), (60, 40, 110), (200, 180, 230)],
    ),
    # LOONA 1/3: HeeJin, HyunJin, HaSeul, ViVi; YeoJin is the slash. Pastel aqua and pink.
    "1-3": dict(
        wsz="LOONA-1-3.wsz", preview="preview-1-3.png", name="LOONA 1/3",
        members=["heejin", "hyunjin", "haseul", "vivi"],
        word=[("LOGO", None), ("1", None), ("/", "yeojin"), ("3", None)],
        eq_title="LOOΠΔ 1/3 EQUALIZER", pl_title="LOOΠΔ 1/3",
        texture="petals", light=True, emblem="orbit", names_strip=True, slash="yeojin",
        body=(176, 224, 226), body_hi=(236, 250, 250), body_lo=(92, 148, 156), slot=(150, 204, 208),
        face_top=(222, 244, 244), face_bot=(178, 220, 224), face_hi=(250, 255, 255), face_pr=(140, 192, 198),
        label=(30, 74, 86), label_dim=(84, 130, 138),
        trim=(232, 120, 168), trim_hi=(255, 196, 222), trim_lo=(176, 70, 120),
        disp=(14, 44, 52), ink=(196, 246, 244), ink_hi=(255, 255, 255), ghost=(28, 66, 74),
        ink_mid=(110, 176, 180), track=(30, 70, 78),
        accent=(240, 80, 150),
        thumb=(255, 176, 208),
        plate=(14, 44, 52), plate_dim=(56, 98, 106), title_dim=(150, 196, 200),
        pl_normal=(184, 236, 234), pl_current=(255, 182, 214), pl_selbg=(30, 86, 96),
        art=[(150, 214, 218), (255, 200, 220), (255, 240, 246)],
    ),
    # Odd Eye Circle: Kim Lip, JinSoul, Choerry. Black and white street, red/blue/purple.
    "odd-eye-circle": dict(
        wsz="LOONA-Odd-Eye-Circle.wsz", preview="preview-odd-eye-circle.png", name="ODD EYE CIRCLE",
        members=["kimlip", "jinsoul", "choerry"],
        word=[("OECLOGO", None)],
        eq_title="ODD EYE CIRCLE EQUALIZER", pl_title="ODD EYE CIRCLE",
        texture="concrete", light=False, emblem="oddeye", names_strip=True,
        body=(24, 24, 27), body_hi=(70, 70, 76), body_lo=(4, 4, 6), slot=(12, 12, 14),
        face_top=(56, 56, 62), face_bot=(30, 30, 34), face_hi=(92, 92, 100), face_pr=(14, 14, 16),
        label=(214, 214, 220), label_dim=(120, 120, 128),
        trim=(200, 200, 206), trim_hi=(250, 250, 252), trim_lo=(84, 84, 92),
        disp=(6, 6, 8), ink=(244, 244, 248), ink_hi=(255, 255, 255), ghost=(30, 30, 36),
        ink_mid=(140, 140, 150), track=(34, 34, 40),
        accent=lift(MEMBER["kimlip"][1], 80),
        thumb=(236, 236, 240),
        plate=(6, 6, 8), plate_dim=(30, 30, 34), title_dim=(130, 130, 138),
        pl_normal=(220, 220, 226), pl_current=(255, 90, 100), pl_selbg=(70, 20, 90),
        art=[(10, 10, 12), (120, 10, 40), (40, 30, 200), (180, 20, 210)],
    ),
    # yyxy: Yves, Chuu, Go Won, Olivia Hye. The uniforms' green tartan, white shirts, burgundy.
    "yyxy": dict(
        wsz="LOONA-yyxy.wsz", preview="preview-yyxy.png", name="yyxy",
        members=["yves", "chuu", "gowon", "olivia"],
        word=[("LOGO", None), ("y", None), ("y", None), ("x", None), ("y", None)],
        eq_title="YYXY EQUALIZER", pl_title="YYXY PLAYLIST",
        texture="tartan", light=False, emblem="orbit", names_strip=True,
        body=(20, 46, 42), body_hi=(58, 96, 86), body_lo=(4, 14, 12), slot=(10, 28, 26),
        face_top=(52, 84, 76), face_bot=(26, 52, 46), face_hi=(86, 124, 112), face_pr=(10, 26, 22),
        label=(232, 226, 206), label_dim=(130, 150, 136),
        trim=(220, 212, 186), trim_hi=(250, 246, 232), trim_lo=(110, 40, 48),
        disp=(6, 16, 14), ink=(246, 242, 228), ink_hi=(255, 255, 255), ghost=(24, 46, 42),
        ink_mid=(140, 160, 146), track=(26, 48, 44),
        accent=MEMBER["chuu"][1],
        thumb=(240, 236, 222),
        plate=(6, 16, 14), plate_dim=(24, 44, 40), title_dim=(140, 160, 146),
        pl_normal=(230, 226, 210), pl_current=(254, 168, 125), pl_selbg=(96, 18, 30),
        art=[(14, 40, 36), (121, 20, 30), (240, 236, 222)],
    ),
}


def era(key, wsz, name, word, plate_word, emblem, texture, light, **pal):
    THEMES[key] = dict(
        wsz=wsz, preview=f"preview-{key}.png", name=name, members=[k for k, _, _ in MEMBERS],
        word=[("LOGO", None)] + [(c, None) for c in word],
        eq_title=f"{plate_word} EQUALIZER", pl_title=f"LOOΠΔ {plate_word}",
        texture=texture, light=light, emblem=emblem, names_strip=False, **pal)


# Album eras. All twelve members (the full group's releases), each era's own palette and motif.
era("plus-plus", "LOONA-Plus-Plus.wsz", "LOONA [+ +]", "[+ +]", "[+ +]", ("badge", "++"), "plus", True,
    # [+ +] (2018, "Hi High"): misty forest teal, white, the cover's ringed "+ +" badge
    body=(196, 214, 216), body_hi=(238, 246, 246), body_lo=(96, 122, 128), slot=(170, 190, 194),
    face_top=(226, 238, 238), face_bot=(186, 204, 206), face_hi=(252, 254, 254), face_pr=(150, 172, 176),
    label=(22, 56, 60), label_dim=(90, 116, 120),
    trim=(60, 132, 112), trim_hi=(150, 210, 190), trim_lo=(30, 80, 70),
    disp=(18, 42, 46), ink=(226, 246, 240), ink_hi=(255, 255, 255), ghost=(34, 62, 66),
    ink_mid=(110, 160, 156), track=(34, 64, 68), accent=(250, 104, 146), thumb=(240, 248, 248),
    plate=(18, 42, 46), plate_dim=(70, 96, 100), title_dim=(150, 180, 180),
    pl_normal=(200, 236, 228), pl_current=(255, 170, 200), pl_selbg=(40, 90, 84),
    level=[(30, 96, 90), (60, 150, 120), (150, 214, 196), (236, 246, 240), (250, 130, 166)],
    art=[(24, 43, 49), (67, 93, 94), (169, 180, 187), (227, 226, 239)])
era("x-x", "LOONA-X-X.wsz", "LOONA [X X]", "[X X]", "[X X]", ("butterfly", None), "ice", True,
    # [X X] (2019, "Butterfly"): ice blue, the cover's iridescent pink/lavender/teal wings
    body=(200, 226, 242), body_hi=(246, 251, 255), body_lo=(108, 138, 168), slot=(176, 206, 226),
    face_top=(234, 245, 252), face_bot=(192, 216, 236), face_hi=(255, 255, 255), face_pr=(156, 186, 212),
    label=(38, 54, 90), label_dim=(104, 124, 156),
    trim=(150, 120, 210), trim_hi=(224, 204, 250), trim_lo=(96, 70, 160),
    disp=(20, 26, 52), ink=(230, 236, 255), ink_hi=(255, 255, 255), ghost=(36, 44, 78),
    ink_mid=(130, 140, 190), track=(36, 44, 80), accent=(236, 100, 166), thumb=(250, 250, 255),
    plate=(20, 26, 52), plate_dim=(84, 100, 140), title_dim=(150, 170, 200),
    pl_normal=(206, 222, 250), pl_current=(255, 176, 214), pl_selbg=(64, 52, 116),
    level=[(110, 150, 200), (130, 210, 214), (196, 170, 246), (244, 140, 196), (255, 236, 248)],
    art=[(192, 223, 241), (203, 200, 215), (240, 182, 220), (156, 192, 205)])
era("hash", "LOONA-Hash.wsz", "LOONA [#]", "[#]", "[#]", ("badge", "#"), "dusk", False,
    # [#] (2020, "So What"): red uniforms against a slate-blue dusk, black
    body=(18, 17, 22), body_hi=(62, 60, 74), body_lo=(2, 2, 4), slot=(10, 10, 12),
    face_top=(54, 52, 62), face_bot=(28, 27, 34), face_hi=(88, 86, 98), face_pr=(12, 12, 14),
    label=(222, 216, 220), label_dim=(120, 116, 124),
    trim=(200, 30, 44), trim_hi=(250, 96, 104), trim_lo=(104, 14, 22),
    disp=(8, 8, 12), ink=(250, 240, 240), ink_hi=(255, 255, 255), ghost=(42, 22, 26),
    ink_mid=(150, 120, 128), track=(40, 24, 28), accent=(255, 64, 74), thumb=(214, 40, 52),
    plate=(8, 8, 12), plate_dim=(34, 30, 36), title_dim=(130, 120, 126),
    pl_normal=(226, 220, 224), pl_current=(255, 84, 94), pl_selbg=(92, 14, 24),
    level=[(90, 16, 26), (190, 26, 40), (250, 70, 80), (255, 170, 170), (255, 240, 240)],
    art=[(40, 52, 84), (72, 92, 132), (182, 30, 40), (20, 10, 14)])
era("12-00", "LOONA-12-00.wsz", "LOONA [12:00]", "[12:00]", "[12:00]", ("clock", None), "warmstars", False,
    # [12:00] (2020, "Why Not?"): the moonlight festival at midnight, night palms, gold
    body=(24, 14, 22), body_hi=(72, 52, 58), body_lo=(4, 2, 4), slot=(14, 8, 12),
    face_top=(62, 44, 46), face_bot=(34, 22, 28), face_hi=(102, 78, 70), face_pr=(14, 8, 10),
    label=(232, 208, 160), label_dim=(140, 118, 90),
    trim=(196, 156, 86), trim_hi=(246, 214, 140), trim_lo=(110, 80, 40),
    disp=(10, 6, 8), ink=(255, 226, 164), ink_hi=(255, 248, 220), ghost=(44, 30, 22),
    ink_mid=(160, 128, 84), track=(44, 30, 24), accent=(255, 236, 180), thumb=(214, 176, 106),
    plate=(10, 6, 8), plate_dim=(40, 28, 30), title_dim=(140, 118, 90),
    pl_normal=(232, 208, 162), pl_current=(255, 238, 176), pl_selbg=(82, 54, 36),
    level=[(110, 70, 40), (170, 126, 60), (220, 176, 96), (255, 220, 150), (255, 246, 220)],
    art=[(28, 14, 29), (92, 61, 47), (166, 133, 76), (188, 171, 149)])
era("and", "LOONA-And.wsz", "LOONA [&]", "[&]", "[&]", ("badge", "&"), "curtain", False,
    # [&] (2021, "PTT (Paint The Town)"): red velvet curtain, slate walls, cream, a gilt frame
    body=(82, 20, 30), body_hi=(134, 52, 62), body_lo=(22, 4, 8), slot=(42, 10, 16),
    face_top=(72, 74, 88), face_bot=(42, 44, 56), face_hi=(106, 108, 122), face_pr=(20, 22, 30),
    label=(228, 228, 208), label_dim=(160, 128, 128),
    trim=(215, 217, 191), trim_hi=(250, 250, 236), trim_lo=(125, 129, 137),
    disp=(16, 18, 28), ink=(238, 240, 222), ink_hi=(255, 255, 255), ghost=(36, 38, 54),
    ink_mid=(140, 144, 160), track=(38, 40, 58), accent=(234, 196, 110), thumb=(215, 217, 191),
    plate=(16, 18, 28), plate_dim=(56, 26, 34), title_dim=(170, 140, 140),
    pl_normal=(222, 224, 208), pl_current=(240, 202, 122), pl_selbg=(104, 24, 38),
    level=[(110, 24, 40), (190, 40, 56), (226, 120, 90), (234, 196, 110), (240, 240, 222)],
    art=[(73, 19, 24), (43, 43, 57), (125, 129, 137), (215, 217, 191)])
era("flip-that", "LOONA-Flip-That.wsz", "LOONA Flip That", "FLIP THAT", "FLIP THAT", ("flower", None),
    "garden", True,
    # Flip That (2022): a summer garden, white dresses, lavender and pink flowers, deep leaves
    body=(214, 228, 198), body_hi=(246, 250, 238), body_lo=(108, 134, 88), slot=(190, 206, 170),
    face_top=(238, 244, 226), face_bot=(202, 216, 184), face_hi=(255, 255, 250), face_pr=(168, 188, 150),
    label=(38, 68, 28), label_dim=(100, 124, 86),
    trim=(150, 112, 196), trim_hi=(222, 202, 242), trim_lo=(80, 106, 46),
    disp=(24, 44, 22), ink=(236, 250, 220), ink_hi=(255, 255, 255), ghost=(40, 64, 36),
    ink_mid=(130, 170, 110), track=(40, 64, 38), accent=(244, 120, 170), thumb=(250, 250, 244),
    plate=(24, 44, 22), plate_dim=(90, 112, 80), title_dim=(150, 176, 136),
    pl_normal=(220, 240, 200), pl_current=(255, 190, 220), pl_selbg=(72, 100, 42),
    level=[(70, 130, 50), (130, 190, 90), (190, 160, 236), (244, 140, 186), (250, 226, 120)],
    art=[(80, 115, 52), (166, 175, 143), (219, 207, 215), (206, 184, 182)])

THEME_ORDER = ["loona", "1-3", "odd-eye-circle", "yyxy", "plus-plus", "x-x", "hash", "12-00", "and", "flip-that"]


def light_variant(base, key, wsz, name, **over):
    """A light-display version of a theme: light body and glass, dark ink, a light playlist."""
    t = dict(THEMES[base])
    t.update(wsz=wsz, preview=f"preview-{key}.png", name=name, light=True, light_disp=True, base=base)
    t.update(over)
    THEMES[key] = t
    THEME_ORDER.append(key)


# The group in daylight / moonlit white: a pale sky, navy ink, the twelve moons as they are.
light_variant(
    "loona", "loona-light", "LOONA-Light.wsz", "LOONA (light)",
    body=(226, 232, 246), body_hi=(250, 252, 255), body_lo=(120, 128, 170), slot=(206, 212, 232),
    face_top=(244, 246, 252), face_bot=(208, 214, 234), face_hi=(255, 255, 255), face_pr=(178, 186, 214),
    label=(28, 34, 80), label_dim=(110, 118, 160),
    trim=(110, 116, 186), trim_hi=(180, 186, 236), trim_lo=(60, 64, 130),
    disp=(246, 248, 255), ink=(20, 24, 64), ink_hi=(0, 0, 24), ghost=(222, 226, 242),
    ink_mid=(120, 126, 170), track=(220, 224, 240), accent=(200, 146, 30), thumb=(160, 162, 176),
    plate=(246, 248, 255), plate_dim=(214, 218, 234), title_dim=(130, 136, 176),
    pl_normal=(30, 34, 76), pl_current=(206, 0, 124), pl_selbg=(214, 220, 246),
    art=[(236, 240, 252), (200, 190, 236), (120, 110, 190)], star_tone=(150, 156, 210))
# LOONA 1/3: the same pastel aqua, now with pale aqua glass and a white-aqua playlist.
light_variant(
    "1-3", "1-3-light", "LOONA-1-3-Light.wsz", "LOONA 1/3 (light)",
    body=(204, 236, 236), body_hi=(244, 253, 253), body_lo=(96, 152, 160), slot=(176, 218, 222),
    disp=(240, 251, 251), ink=(14, 60, 70), ink_hi=(0, 30, 36), ghost=(214, 236, 238),
    ink_mid=(100, 150, 156), track=(206, 230, 232), thumb=(236, 130, 176),
    plate=(240, 251, 251), plate_dim=(204, 228, 230), title_dim=(110, 150, 156),
    pl_normal=(20, 64, 74), pl_current=(200, 30, 116), pl_selbg=(196, 232, 234))
# Odd Eye Circle: white concrete, black ink and thumbs, the red / blue / purple as accents.
light_variant(
    "odd-eye-circle", "odd-eye-circle-light", "LOONA-Odd-Eye-Circle-Light.wsz", "ODD EYE CIRCLE (light)",
    body=(232, 232, 234), body_hi=(255, 255, 255), body_lo=(120, 120, 128), slot=(212, 212, 216),
    face_top=(248, 248, 250), face_bot=(214, 214, 218), face_hi=(255, 255, 255), face_pr=(184, 184, 190),
    label=(20, 20, 24), label_dim=(120, 120, 128),
    trim=(40, 40, 46), trim_hi=(110, 110, 118), trim_lo=(150, 150, 158),
    disp=(250, 250, 252), ink=(14, 14, 18), ink_hi=(0, 0, 0), ghost=(228, 228, 232),
    ink_mid=(130, 130, 138), track=(226, 226, 230), accent=(217, 0, 17), thumb=(44, 44, 50),
    plate=(250, 250, 252), plate_dim=(220, 220, 224), title_dim=(130, 130, 138),
    pl_normal=(20, 20, 24), pl_current=(200, 0, 20), pl_selbg=(228, 216, 242),
    art=[(245, 245, 246), (224, 225, 228), (217, 0, 17), (8, 1, 213), (186, 1, 222)])
# yyxy: the white shirts: cream with a pale green tartan, green ink, burgundy thumbs.
light_variant(
    "yyxy", "yyxy-light", "LOONA-yyxy-Light.wsz", "yyxy (light)",
    body=(238, 234, 220), body_hi=(255, 253, 246), body_lo=(130, 140, 120), slot=(220, 216, 200),
    face_top=(250, 248, 240), face_bot=(222, 218, 204), face_hi=(255, 255, 255), face_pr=(196, 192, 176),
    label=(20, 52, 44), label_dim=(120, 130, 116),
    trim=(30, 90, 78), trim_hi=(120, 170, 150), trim_lo=(121, 20, 30),
    disp=(250, 248, 240), ink=(16, 44, 38), ink_hi=(0, 20, 16), ghost=(230, 228, 216),
    ink_mid=(120, 140, 126), track=(226, 224, 212), accent=(214, 104, 60), thumb=(140, 30, 44),
    plate=(250, 248, 240), plate_dim=(226, 222, 208), title_dim=(120, 140, 126),
    pl_normal=(18, 46, 40), pl_current=(150, 20, 34), pl_selbg=(214, 234, 224),
    art=[(240, 236, 222), (180, 200, 180), (121, 20, 30)], tartan_line2=(30, 90, 78))
# [#]: the Normal B / Limited B covers: black uniforms on a pale warm grey (#E4DBD9); the A
# versions' red kept as the accent.
light_variant(
    "hash", "hash-light", "LOONA-Hash-Light.wsz", "LOONA [#] (light)",
    texture="concrete",
    body=(228, 219, 217), body_hi=(250, 246, 245), body_lo=(110, 100, 104), slot=(210, 200, 199),
    face_top=(242, 236, 235), face_bot=(212, 202, 201), face_hi=(255, 252, 252), face_pr=(182, 172, 172),
    label=(36, 32, 38), label_dim=(130, 120, 124),
    trim=(52, 46, 52), trim_hi=(120, 112, 118), trim_lo=(150, 140, 142),
    disp=(244, 239, 238), ink=(30, 26, 32), ink_hi=(0, 0, 0), ghost=(228, 220, 219),
    ink_mid=(140, 126, 130), track=(226, 216, 215), accent=(200, 24, 38), thumb=(48, 44, 50),
    plate=(244, 239, 238), plate_dim=(220, 210, 209), title_dim=(140, 126, 130),
    pl_normal=(34, 30, 36), pl_current=(196, 18, 34), pl_selbg=(236, 214, 214),
    level=[(160, 150, 154), (97, 89, 96), (40, 36, 42), (150, 20, 34), (210, 24, 40)],
    art=[(228, 219, 217), (209, 199, 200), (97, 89, 96)])
# [&]: the B version's white arch room (#EBECF4 / #C7C2CA lavender greys, black and white outfits);
# the A version's red curtain kept as the accent.
light_variant(
    "and", "and-light", "LOONA-And-Light.wsz", "LOONA [&] (light)",
    texture="plain",
    body=(222, 220, 230), body_hi=(246, 246, 252), body_lo=(116, 108, 118), slot=(204, 200, 212),
    face_top=(240, 240, 247), face_bot=(206, 202, 214), face_hi=(255, 255, 255), face_pr=(178, 172, 186),
    label=(40, 34, 40), label_dim=(130, 122, 130),
    trim=(116, 104, 100), trim_hi=(176, 168, 170), trim_lo=(150, 30, 44),
    disp=(244, 244, 250), ink=(36, 30, 36), ink_hi=(0, 0, 0), ghost=(226, 224, 232),
    ink_mid=(130, 124, 132), track=(224, 222, 230), accent=(160, 24, 40), thumb=(116, 104, 100),
    plate=(244, 244, 250), plate_dim=(214, 210, 220), title_dim=(140, 132, 140),
    pl_normal=(36, 30, 36), pl_current=(160, 24, 40), pl_selbg=(226, 214, 226),
    level=[(193, 186, 193), (116, 104, 100), (60, 52, 56), (150, 30, 44), (200, 50, 64)],
    art=[(235, 236, 244), (199, 194, 202), (116, 104, 100)])

T = None
P = None   # the active theme's palette, also exported as module globals below


def set_theme(key):
    global T, OUT, _rng, LEVEL
    T = dict(THEMES[key], key=key)
    OUT = os.path.join(OUT_ROOT, key)
    os.makedirs(OUT, exist_ok=True)
    _rng = np.random.default_rng(1729)          # same seed per theme: order of builds doesn't matter
    g = globals()
    for k in ("body", "body_hi", "body_lo", "slot", "face_top", "face_bot", "face_hi", "face_pr", "label",
              "label_dim", "trim", "trim_hi", "trim_lo", "disp", "ink", "ink_hi", "ghost", "ink_mid", "track",
              "accent", "thumb", "plate", "plate_dim", "title_dim"):
        g[k.upper()] = T[k]
    T["cols"] = [MEMBER[m][1] for m in T["members"]]
    # member colours for the display glass: lifted on dark glass, darkened on light (light variants)
    T["vis"] = [sink(c, 150) for c in T["cols"]] if T.get("light_disp") else [lift(c) for c in T["cols"]]
    LEVEL = T.get("level") or T["vis"]
    SHEETS.clear()


def lvl(stops, t):
    """Level colours: the members' colours one after another, or an era's palette blended."""
    return ramp(stops, t) if T.get("level") else step(stops, t)


def on_body(c):
    """A member colour for small marks on the theme's body."""
    return sink(c) if T["light"] else lift(c, 100)


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def new(w, h, col=None):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = BODY if col is None else col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[y:y + h, x:x + w] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def raised(a, x, y, w, h, hi=None, lo=None):
    hi = BODY_HI if hi is None else hi
    lo = BODY_LO if lo is None else lo
    rect(a, x, y, w, 1, hi)
    rect(a, x, y, 1, h, hi)
    rect(a, x, y + h - 1, w, 1, lo)
    rect(a, x + w - 1, y, 1, h, lo)


def sunken(a, x, y, w, h, hi=None, lo=None):
    raised(a, x, y, w, h, BODY_LO if lo is None else lo, BODY_HI if hi is None else hi)


_rng = np.random.default_rng(1729)


def texture(a, x, y, w, h, tiled=False):
    """The theme's body surface. `tiled` pieces get no pattern with a period (they repeat at 25/29 px)."""
    kind = T["texture"]
    base = np.array(BODY, dtype=np.float64)
    n = _rng.normal(0, 1, (h, w))
    region = np.zeros((h, w, 3)) + base
    if kind == "stars":
        region += (n * 1.2)[:, :, None]
        # faint vertical deepening
        region += np.linspace(2, -2, h)[:, None, None]
        u = _rng.random((h, w))
        bright = _rng.random((h, w))
        star = u < 0.010
        tone = np.array(T.get("star_tone", (190, 200, 255)), dtype=np.float64)
        amt = np.where(bright > 0.85, 0.75, np.where(bright > 0.5, 0.42, 0.24))
        region[star] = region[star] * (1 - amt[star, None]) + tone * amt[star, None]
    elif kind == "petals":
        region += (n * 1.6)[:, :, None]
        u = _rng.random((h, w))
        petal = u < 0.006
        tone = np.array((255, 190, 214), dtype=np.float64)
        region[petal] = region[petal] * 0.45 + tone * 0.55
        light = (u > 0.006) & (u < 0.012)
        region[light] = region[light] * 0.6 + 255 * 0.4
    elif kind == "warmstars":
        region += (n * 1.2)[:, :, None]
        u = _rng.random((h, w))
        bright = _rng.random((h, w))
        star = u < 0.008
        tone = np.array(T.get("star_tone", (255, 222, 150)), dtype=np.float64)
        amt = np.where(bright > 0.85, 0.7, np.where(bright > 0.5, 0.4, 0.22))
        region[star] = region[star] * (1 - amt[star, None]) + tone * amt[star, None]
    elif kind == "plus":
        region += (n * 1.4)[:, :, None]
        u = _rng.random((h, w))
        for (yy, xx) in zip(*np.nonzero(u < 0.0035)):
            for dy, dx in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                ry, rx = yy + dy, xx + dx
                if 0 <= ry < h and 0 <= rx < w:
                    region[ry, rx] = region[ry, rx] * 0.55 + np.array((255, 255, 255)) * 0.45
    elif kind == "plain":
        region += (n * 1.0)[:, :, None]
    elif kind == "ice":
        region += (n * 1.2)[:, :, None]
        region += np.linspace(5, -5, h)[:, None, None]
        u = _rng.random((h, w))
        hue = _rng.random((h, w))
        sp = u < 0.006
        tones = np.array([(255, 190, 226), (210, 190, 255), (170, 236, 230), (255, 255, 255)], dtype=np.float64)
        pick = tones[(hue * 4).astype(int).clip(0, 3)]
        region[sp] = region[sp] * 0.45 + pick[sp] * 0.55
    elif kind == "dusk":
        sm = n + np.roll(n, 1, axis=0) * 0.6 + np.roll(n, 1, axis=1) * 0.6
        region += (sm * 2.0)[:, :, None]
        if not tiled:
            yy = np.arange(y, y + h)
            t = np.clip(1 - yy / 60.0, 0, 1) ** 1.5
            region += (t[:, None, None] * (np.array(T.get("dusk_top", (30, 40, 66))) - base))
    elif kind == "curtain":
        region += (n * 1.2)[:, :, None]
        if not tiled:
            xx = np.arange(x, x + w)
            fold = np.sin(2 * np.pi * xx / 11.0) * 0.5 + np.sin(2 * np.pi * xx / 4.6 + 1.3) * 0.18
            region *= (1 + 0.16 * fold)[None, :, None]
    elif kind == "garden":
        region += (n * 1.5)[:, :, None]
        u = _rng.random((h, w))
        hue = _rng.random((h, w))
        sp = u < 0.007
        tones = np.array([(250, 170, 200), (190, 160, 230), (250, 230, 130), (255, 255, 255)], dtype=np.float64)
        pick = tones[(hue * 4).astype(int).clip(0, 3)]
        region[sp] = region[sp] * 0.4 + pick[sp] * 0.6
        leaf = (u > 0.007) & (u < 0.013)
        region[leaf] = region[leaf] * 0.7 + np.array((90, 130, 60)) * 0.3
    elif kind == "concrete":
        sm = n + np.roll(n, 1, axis=0) * 0.6 + np.roll(n, 1, axis=1) * 0.6
        region += (sm * 2.4)[:, :, None]
        u = _rng.random((h, w))
        region[u < 0.004] += 14
    elif kind == "tartan":
        region += (n * 1.2)[:, :, None]
        if not tiled:
            yy, xx = np.mgrid[y:y + h, x:x + w]
            U, V = xx % 24, yy % 24
            band_u = (U < 8)
            band_v = (V < 8)
            sgn = -0.9 if T["light"] else 1.0
            region += (band_u.astype(float) * 7 + band_v.astype(float) * 7)[:, :, None] * np.array((0.5, 1.0, 0.9)) * sgn
            red = (U == 12) | (V == 12)
            yv = np.array(lift(MEMBER["yves"][1], 40), dtype=np.float64)
            mix = 0.2 if T["light"] else 0.38
            region[red] = region[red] * (1 - mix) + yv * mix
            cream = (U == 4) | (V == 4)
            line2 = np.array(T.get("tartan_line2", (240, 236, 220)), dtype=np.float64)
            region[cream] = region[cream] * 0.86 + line2 * 0.14
    a[y:y + h, x:x + w] = np.round(region).astype(np.int32)


def body(a, x, y, w, h, tiled=False):
    texture(a, x, y, w, h, tiled)


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


# ------------------------------------------------------------------------------------------
# Pixel fonts (all designed for these skins)
# ------------------------------------------------------------------------------------------

def G(*rows):
    return list(rows)


# 5-row font for text.bmp, titles and gen.bmp's letters.
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
    # for the titles only (text.bmp has no cells for them)
    "Π": G("####", "#..#", "#..#", "#..#", "#..#"),
    "Δ": G("..#..", ".#.#.", ".#.#.", "#...#", "#####"),
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
for _c in "0123456789+-./":
    TINY[_c] = FONT5[_c]

# 7-row wordmark letters for the main titlebar: thin, geometric, round O's, the Π and Δ of the
# group's own spelling. Lowercase sits on rows 1..5 with y's tail on row 6.
WORDMARK = {
    "L": G("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "O": G(".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "Π": G("#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#"),
    "Δ": G("..#..", "..#..", ".#.#.", ".#.#.", "#...#", "#...#", "#####"),
    "1": G(".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"),
    "/": G("...#", "...#", "..#.", "..#.", ".#..", ".#..", "#..."),
    "3": G("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "D": G("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": G("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "Y": G("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "C": G(".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "I": G("###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"),
    "R": G("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "x": G(".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "....."),
    "y": G(".....", "#...#", "#...#", ".#.#.", "..#..", ".#...", "#...."),
    " ": G("..", "..", "..", "..", "..", "..", ".."),
    "[": G("##", "#.", "#.", "#.", "#.", "#.", "##"),
    "]": G("##", ".#", ".#", ".#", ".#", ".#", "##"),
    "+": G(".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "X": G("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "#": G(".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    ":": G(".", ".", "#", ".", "#", ".", "."),
    "2": G(".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "0": G(".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "&": G(".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "F": G("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "P": G("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "T": G("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "H": G("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "A": G(".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
}

# ------------------------------------------------------------------------------------------
# Real logos (allowed for these private skins, used once per skin: in the titlebar). Read from
# source/ at generation time; see README.md for where they came from.
# ------------------------------------------------------------------------------------------

LOGO_LOONA = os.path.join(HERE, "source", "logo-loona", "loona-logo.jpg")   # stacked + horizontal marks
LOGO_OEC = os.path.join(HERE, "source", "logo-oec", "oec-logo.png")
_LOGO_CACHE = {}


def _shrink_strokes(dark, h):
    """dark: float 0..1 image (1 = ink) with thin strokes. Thickens the strokes to about one target
    pixel, then box-downscales to height h. Returns alpha 0..1."""
    from PIL import ImageFilter
    im = Image.fromarray(np.round(dark * 255).astype(np.uint8), "L")
    k = max(3, (int(round(im.height / h)) | 1) - 2)
    im = im.filter(ImageFilter.MaxFilter(k))
    w = round(im.width * h / im.height)
    s = np.asarray(im.resize((w, h), Image.BOX)) / 255
    return np.clip((s - 0.12) / 0.5, 0, 1)


def logo(which, h):
    """(alpha, colour_mask) for a logo at height h. `loona`: the horizontal LOOΠΔ wordmark with its
    magenta slash; `oec`: the ODD EYE CIRCLE line of the Odd Eye Circle logo."""
    key = (which, h)
    if key in _LOGO_CACHE:
        return _LOGO_CACHE[key]
    if which == "loona":
        a = np.asarray(Image.open(LOGO_LOONA).convert("RGB").crop((298, 166, 691, 231))).astype(np.float64)
        dark = np.clip((255 - a.mean(-1)) / 255 * 1.4, 0, 1)
        sat = (a.max(-1) - a.min(-1)) > 60
        al = _shrink_strokes(dark, h)
        cm = _shrink_strokes(sat.astype(np.float64), h) > 0.35
    else:
        im = Image.open(LOGO_OEC).convert("RGBA")
        al0 = np.asarray(im)[224:308, 21:806, 3].astype(np.float64) / 255
        al = _shrink_strokes(al0, h)
        cm = np.zeros_like(al, dtype=bool)
    _LOGO_CACHE[key] = (al, cm)
    return al, cm


def paint_alpha(a, x, y, al, col, cm=None, ccol=None):
    for r in range(al.shape[0]):
        for c in range(al.shape[1]):
            v = al[r, c]
            if v <= 0.02:
                continue
            k = ccol if (cm is not None and cm[r, c] and ccol is not None) else col
            k = k(r) if callable(k) else k
            yy, xx = y + r, x + c
            if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1]:
                a[yy, xx] = lerp(tuple(a[yy, xx]), k, min(1.0, v))


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


# ------------------------------------------------------------------------------------------
# Moons
# ------------------------------------------------------------------------------------------


def disc(a, cx, cy, r, col, alpha=1.0):
    """Antialiased-ish filled disc centred on (cx, cy) (floats allowed)."""
    x0, x1 = int(np.floor(cx - r - 1)), int(np.ceil(cx + r + 1))
    y0, y1 = int(np.floor(cy - r - 1)), int(np.ceil(cy + r + 1))
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            if not (0 <= yy < a.shape[0] and 0 <= xx < a.shape[1]):
                continue
            d = np.hypot(xx - cx, yy - cy)
            cov = max(0.0, min(1.0, r + 0.5 - d)) * alpha
            if cov > 0:
                a[yy, xx] = lerp(tuple(a[yy, xx]), col, cov)


def moon(a, cx, cy, r, col, ground):
    """A small full moon: the member colour, a lighter cap, a darker limb at the lower right."""
    disc(a, cx, cy, r + 0.6, lerp(ground, col, 0.22))       # a faint halo
    disc(a, cx, cy, r, col)
    disc(a, cx + 0.8, cy + 0.8, r - 0.6, col)
    for yy in range(int(cy - r), int(cy + r) + 1):
        for xx in range(int(cx - r), int(cx + r) + 1):
            d = np.hypot(xx - cx, yy - cy)
            if d <= r - 0.2:
                lim = np.hypot(xx - (cx - 1.4), yy - (cy - 1.4))
                if lim > r + 0.3:
                    a[yy, xx] = lerp(col, (0, 0, 0), 0.35)
    px(a, int(round(cx - 1)), int(round(cy - 1)), lerp(col, (255, 255, 255), 0.55))


# ------------------------------------------------------------------------------------------
# Shared pieces
# ------------------------------------------------------------------------------------------


def grill(a, x, y0, w, rows, lit):
    """The titlebars' lines: a thin rule with a dark groove under it; the group's are dotted orbits."""
    if w <= 0:
        return
    line = TRIM if lit else lerp(BODY, LABEL_DIM, 0.6)
    for r in rows:
        if T["texture"] == "stars":
            for k in range(0, w):
                if (x + k) % 2 == 0:
                    px(a, x + k, y0 + r, line)
        else:
            rect(a, x, y0 + r, w, 1, line)
            rect(a, x, y0 + r + 1, w, 1, BODY_LO)


def plate(a, x, y, w, lit, h=9):
    """A recessed nameplate for a title (rows y..y+h-1)."""
    rect(a, x, y + 1, w, h - 2, PLATE if lit else PLATE_DIM)
    rect(a, x, y, w, 1, BODY_LO)
    rect(a, x, y + h - 1, w, 1, BODY_HI)


def plate_cap_left(a, x, y, lit, h=9):
    """4 columns: gap, light rim, dark rim, plate."""
    rect(a, x + 2, y, 1, h, BODY_LO)
    plate(a, x + 3, y, 1, lit, h)


def plate_cap_right(a, x, y, lit, h=9):
    plate(a, x, y, 1, lit, h)
    rect(a, x + 1, y, 1, h, BODY_HI)


def title_lit():
    return INK


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button."""
    face = FACE_PR if pressed else FACE_BOT
    rect(a, x, y, 9, 9, face)
    if pressed:
        sunken(a, x, y, 9, 9)
    else:
        raised(a, x, y, 9, 9, FACE_HI, BODY_LO)
    ink = ACCENT if pressed else (TRIM_HI if not T["light"] else LABEL) if lit else LABEL_DIM
    if T["light"] and pressed:
        ink = sink(ACCENT) if luma(FACE_PR) > 120 else ACCENT
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        for dx, dy in [(3, 3), (4, 3), (5, 3), (3, 4), (4, 4), (5, 4), (3, 5), (4, 5), (5, 5)]:
            if (dx, dy) not in [(3, 3), (5, 3), (3, 5), (5, 5)]:
                px(a, X + dx, Y + dy, ink)
            else:
                px(a, X + dx, Y + dy, lerp(ink, face, 0.55))
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 5, 2, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 2, ink)
        rect(a, X + 2, Y + 5, 5, 1, lerp(ink, face, 0.5))
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43)
    rect(a, 0, 0, 8, 43, SLOT)
    sunken(a, 0, 0, 8, 43)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, lerp(SLOT, ACCENT, 0.25))
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 2, gy, (sink(ACCENT) if T["light"] else ACCENT) if on else LABEL_DIM)
    return a


def crescent(a, cx, cy, r, col, off=(1.6, -0.9)):
    """A crescent: a disc less a disc shifted by `off`."""
    for yy in range(int(cy - r - 1), int(cy + r + 2)):
        for xx in range(int(cx - r - 1), int(cx + r + 2)):
            d = np.hypot(xx - cx, yy - cy)
            d2 = np.hypot(xx - cx - off[0], yy - cy - off[1])
            cov = max(0.0, min(1.0, r + 0.5 - d)) * max(0.0, min(1.0, d2 - r + 0.5))
            if cov > 0 and 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1]:
                a[yy, xx] = lerp(tuple(a[yy, xx]), col, cov)


LOGO_H = 8


def word_item_w(c):
    if c in ("LOGO", "OECLOGO"):
        return logo("loona" if c == "LOGO" else "oec", LOGO_H)[0].shape[1]
    return glyph_w(WORDMARK, c)


def wordmark(a, x, y, lit):
    """The theme's name: the real logo (once) and/or WORDMARK letters; returns its width when a is None."""
    gap = 2
    word = T["word"]
    w = sum(word_item_w(c) + (4 if c in ("LOGO", "OECLOGO") else 0) for c, _ in word) + gap * (len(word) - 1)
    if a is None:
        return w
    if T["light"]:
        top, bot = (LABEL, lerp(LABEL, TRIM_LO, 0.5)) if lit else (LABEL_DIM, LABEL_DIM)
        shadow = BODY_HI
    else:
        top, bot = (TRIM_HI, TRIM) if lit else (TITLE_DIM, lerp(TITLE_DIM, BODY, 0.3))
        shadow = BODY_LO
    for c, special in word:
        if c in ("LOGO", "OECLOGO"):
            al, cm = logo("loona" if c == "LOGO" else "oec", LOGO_H)
            slash = (on_body(MEMBER["heejin"][1]) if T["light"] else lift((240, 71, 176))) if lit else None
            paint_alpha(a, x, y, al, lambda r: lerp(top, bot, r / (LOGO_H - 1)), cm, slash)
            x += al.shape[1] + gap + 4
            continue
        if special in MEMBER and lit:
            mc = on_body(MEMBER[special][1])
            col = mc
        else:
            col = lambda r: lerp(top, bot, r / 6)
        draw_text(a, WORDMARK, c, x, y, col, shadow=shadow)
        if special == "eye":
            # the odd eye: a pupil in each of the first two members' colours
            px(a, x + 2, y + 3, on_body(T["cols"][0]) if lit else LABEL_DIM)
            px(a, x + 1, y + 3, on_body(T["cols"][1]) if lit else LABEL_DIM)
            px(a, x + 3, y + 3, on_body(T["cols"][2]) if lit else LABEL_DIM)
        x += glyph_w(WORDMARK, c) + gap
    return w


def main_titlebar(lit):
    a = new(275, 14)
    body(a, 0, 0, 275, 14)
    rect(a, 0, 0, 275, 1, BODY_HI)
    rect(a, 0, 0, 1, 14, BODY_HI)
    rect(a, 274, 0, 1, 14, BODY_LO)
    ww = wordmark(None, 0, 0, lit)
    wx = (275 - ww) // 2
    # a crescent either side of the name, then the rules out to the buttons
    grill(a, 18, 0, wx - 12 - 18, [5, 8] if T["texture"] != "stars" else [6], lit)
    grill(a, wx + ww + 12, 0, 240 - (wx + ww + 12), [5, 8] if T["texture"] != "stars" else [6], lit)
    wordmark(a, wx, 3, lit)
    mc = (TRIM_HI if not T["light"] else TRIM_LO) if lit else LABEL_DIM
    if T["key"] == "loona" and lit:
        mc = ACCENT
    crescent(a, wx - 7, 6.5, 3.0, mc)
    crescent(a, wx + ww + 6, 6.5, 3.0, mc, off=(-1.6, -0.9))
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def make_titlebar():
    a = new(344, 87)
    body(a, 0, 0, 344, 87)
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

SEG = {
    # 1px horizontals (rows 0, 6, 12), 2px verticals; numbers.bmp's minus is digit 2's row 6.
    "a": [(0, c) for c in range(2, 7)],
    "g": [(6, c) for c in range(2, 7)],
    "d": [(12, c) for c in range(2, 7)],
    "f": [(r, c) for r in range(1, 6) for c in (1, 2)],
    "b": [(r, c) for r in range(1, 6) for c in (6, 7)],
    "e": [(r, c) for r in range(7, 12) for c in (1, 2)],
    "c": [(r, c) for r in range(7, 12) for c in (6, 7)],
}
DIGIT_SEGS = {
    0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc",
    5: "afgcd", 6: "afgedc", 7: "abc", 8: "abcdefg", 9: "abcdfg",
}


def seven_seg(a, x, y, lit_segs, ghost=True):
    rect(a, x, y, 9, 13, DISP)
    for s, cells in SEG.items():
        if s not in lit_segs and ghost:
            for r, c in cells:
                px(a, x + c, y + r, GHOST)
    for s, cells in SEG.items():
        if s in lit_segs:
            for r, c in cells:
                px(a, x + c, y + r, INK)


def display_box(a, x, y, w, h):
    """A recessed display window: bevelled rim, flat dark glass."""
    rect(a, x, y, w, h, DISP)
    sunken(a, x - 1, y - 1, w + 2, h + 2)
    rect(a, x, y, w, 1, lerp(DISP, (0, 0, 0), 0.4))
    rect(a, x, y, 1, h, lerp(DISP, (0, 0, 0), 0.4))


def emblem(a, cx, cy):
    """The About spot (253, 91, 13x15): the theme's moon."""
    kind, arg = T["emblem"] if isinstance(T["emblem"], tuple) else (T["emblem"], None)
    dark_ink = TRIM_LO if T["light"] else TRIM_HI
    if kind == "badge":
        # the era covers' ringed symbol beside the Korean name
        for yy in range(cy - 9, cy + 10):
            for xx in range(cx - 9, cx + 10):
                d = np.hypot(xx - cx, yy - cy)
                cov = max(0.0, 1 - abs(d - 6.6) / 0.9)
                if cov > 0:
                    px(a, xx, yy, lerp(tuple(a[yy, xx]), dark_ink, cov))
        f = FONT5 if arg in ("#", "&") else TINY
        col = sink(ACCENT, 110) if T["light"] else ACCENT
        tw = text_w(f, arg)
        draw_text(a, f, arg, cx - tw // 2, cy - 2, col)
    elif kind == "butterfly":
        wing = [(lift((236, 100, 166), 90)), (190, 160, 240), (130, 210, 210)]
        shape = [
            "##.....##",
            "###...###",
            "####.####",
            "####.####",
            ".###.###.",
            "..##.##..",
            ".###.###.",
            ".##...##.",
        ]
        ox, oy = cx - 4, cy - 4
        for r, row in enumerate(shape):
            for c, ch in enumerate(row):
                if ch == "#":
                    t = (r / 7 + abs(c - 4) / 8) / 1.5
                    px(a, ox + c, oy + r, ramp(wing, t))
        for r in range(1, 7):
            px(a, ox + 4, oy + r, LABEL)
        px(a, ox + 3, oy - 1, LABEL)
        px(a, ox + 5, oy - 1, LABEL)
    elif kind == "clock":
        # a moon-clock at midnight
        disc(a, cx, cy, 6.6, lerp(TRIM, (255, 240, 200), 0.3))
        disc(a, cx, cy, 5.6, DISP)
        for i in range(12):
            ang = 2 * np.pi * i / 12
            px(a, int(round(cx + 4.6 * np.sin(ang))), int(round(cy - 4.6 * np.cos(ang))),
               ACCENT if i == 0 else INK_MID)
        for r in range(0, 4):
            px(a, cx, cy - r, ACCENT)
        px(a, cx, cy, INK_HI)
    elif kind == "flower":
        cols = [(244, 140, 186), (196, 160, 236), (244, 140, 186), (196, 160, 236), (250, 220, 120)]
        for i in range(5):
            ang = -np.pi / 2 + 2 * np.pi * i / 5
            disc(a, cx + 3.4 * np.cos(ang), cy + 3.4 * np.sin(ang), 2.2, sink(cols[i], 150))
        disc(a, cx, cy, 1.6, (250, 214, 90))
        for r in range(6, 9):
            px(a, cx, cy + r, TRIM_LO)
        px(a, cx + 1, cy + 7, TRIM_LO)
        px(a, cx + 2, cy + 6, TRIM_LO)
    elif kind == "eclipse":
        # a total eclipse: corona, dark disc, a thin returning crescent of light
        for yy in range(cy - 9, cy + 10):
            for xx in range(cx - 9, cx + 10):
                d = np.hypot(xx - cx, yy - cy)
                if 5.6 < d < 8.6:
                    t = 1 - abs(d - 6.4) / 2.2
                    px(a, xx, yy, lerp(tuple(a[yy, xx]), TRIM if T["light"] else TRIM_HI, max(0, t) * 0.55))
        disc(a, cx, cy, 5.6, (2, 2, 8))
        crescent(a, cx, cy, 5.6, (255, 236, 170), off=(1.3, 0.0))
        # the twelve, as points on the corona
        for i, c in enumerate(T["vis"]):
            ang = -np.pi / 2 + 2 * np.pi * i / 12
            px(a, int(round(cx + 8.0 * np.cos(ang))), int(round(cy + 8.0 * np.sin(ang))), c)
    elif kind == "orbit":
        col = TRIM_LO if T["light"] else TRIM_HI
        crescent(a, cx, cy, 5.2, col, off=(2.4, -1.2))
        n = len(T["cols"])
        for i, c in enumerate(T["cols"]):
            ang = np.pi * 0.15 + np.pi * 1.1 * i / max(1, n - 1) - np.pi * 0.5
            mx, my = cx + 2.6 + 6.4 * np.cos(ang) * 0.8, cy + 6.4 * np.sin(ang)
            disc(a, mx, my, 1.2, on_body(c) if T["light"] else lift(c, 90))
    elif kind == "oddeye":
        # an eye: almond outline, an iris split red / blue, a purple ring, the pupil
        cr, cj, cc = (lift(c, 80) for c in T["cols"])
        for yy in range(cy - 7, cy + 8):
            for xx in range(cx - 8, cx + 9):
                dx, dy = (xx - cx) / 8.0, (yy - cy) / 5.2
                # almond: |y| < (1 - x^2) shape
                edge = abs(dy) - (1 - dx * dx)
                if -0.18 < edge < 0.12 and abs(dx) <= 1:
                    px(a, xx, yy, LABEL if T["light"] else TRIM_HI)
        for yy in range(cy - 4, cy + 5):
            for xx in range(cx - 4, cx + 5):
                d = np.hypot(xx - cx, yy - cy)
                if d <= 4.2:
                    col = cc if d > 3.1 else (cr if xx < cx else cj if xx > cx else lerp(cr, cj, 0.5))
                    if d <= 1.3:
                        col = (0, 0, 0)
                    px(a, xx, yy, col)
        px(a, cx - 1, cy - 2, (255, 255, 255))


FREE_STRIP = (16, 107, 223, 8)     # under the transport and shuffle buttons: nothing drawn there


def member_strip(a):
    """The members in the free strip under the transport: moons on a dotted orbit (the twelve), or
    moons with names (a subunit; LOONA 1/3's slash is YeoJin)."""
    x0, y0, w, h = FREE_STRIP
    cy = y0 + 3
    ground = BODY
    if not T["names_strip"]:
        n = len(T["cols"])
        pitch = 18
        start = x0 + (w - pitch * (n - 1)) // 2
        for k in range(start, start + pitch * (n - 1)):
            if k % 2 == 0:
                px(a, k, cy, TRIM_LO)
        for i, c in enumerate(T["cols"]):
            moon(a, start + pitch * i, cy, 3.0, lift(c, 40), ground)
        return
    items = [(MEMBER[m][0], MEMBER[m][1], False) for m in T["members"]]
    if T.get("slash"):
        items.insert(3, (MEMBER[T["slash"]][0], MEMBER[T["slash"]][1], True))
    slot = w // len(items)
    for i, (name, c, is_slash) in enumerate(items):
        col = on_body(c)
        sx = x0 + slot * i
        tw = text_w(TINY, name)
        lead = 8
        bx = sx + (slot - (lead + tw)) // 2
        if is_slash:
            draw_text(a, FONT5, "/", bx + 1, cy - 2, col)
        else:
            moon(a, bx + 3, cy, 3.0, c if not T["light"] else c, ground)
        draw_text(a, TINY, name, bx + lead, cy - 2, col)


def make_main():
    a = new(275, 116)
    body(a, 0, 0, 275, 116)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # left display: indicator, time, analyzer
    display_box(a, 21, 20, 84, 42)
    for x in (48, 60, 78, 90):
        seven_seg(a, x, 26, "")
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, INK)
    rect(a, 24, 60, 76, 1, GHOST)

    # right display: title row, then kbps/kHz/mono/stereo row
    display_box(a, 109, 21, 159, 15)
    display_box(a, 109, 40, 159, 14)
    draw_text(a, TINY, "KBPS", 129, 44, INK_MID)
    draw_text(a, TINY, "KHZ", 169, 44, INK_MID)

    # slider seats (the sliders' own frames cover them)
    sunken(a, 106, 56, 70, 15)
    sunken(a, 176, 56, 40, 15)
    sunken(a, 218, 57, 48, 14)
    sunken(a, 15, 71, 250, 12)

    # transport tray
    rect(a, 15, 87, 145, 20, lerp(BODY, BODY_LO, 0.3))
    sunken(a, 15, 87, 145, 20)
    sunken(a, 163, 88, 77, 17)

    member_strip(a)
    emblem(a, 259, 98)
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36)
# ------------------------------------------------------------------------------------------


def button_face(a, x, y, w, h, pressed):
    if pressed:
        for r in range(h):
            rect(a, x, y + r, w, 1, lerp(FACE_PR, lerp(FACE_PR, FACE_BOT, 0.4), r / max(1, h - 1)))
        rect(a, x, y, w, 1, BODY_LO)
        rect(a, x, y, 1, h, BODY_LO)
        rect(a, x + w - 1, y, 1, h, FACE_HI)
        rect(a, x, y + h - 1, w, 1, FACE_HI)
    else:
        for r in range(h):
            rect(a, x, y + r, w, 1, lerp(FACE_TOP, FACE_BOT, r / max(1, h - 1)))
        rect(a, x, y, w, 1, FACE_HI)
        rect(a, x, y, 1, h, FACE_HI)
        rect(a, x + w - 1, y, 1, h, BODY_LO)
        rect(a, x, y + h - 1, w, 1, BODY_LO)


def tri_right(a, x, y, h, col):
    """Solid right-pointing triangle, h tall (odd), tip to the right."""
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x, y + r, n, 1, col)


def tri_left(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x + half + 1 - n, y + r, n, 1, col)


def icon_ink(pressed):
    if T["light"]:
        return (sink(ACCENT, 110) if pressed else LABEL), BODY_HI
    return (ACCENT if pressed else TRIM_HI), BODY_LO


def transport_icon(a, kind, x, y, w, h, pressed):
    ink, sh = icon_ink(pressed)
    shadow = None if pressed else sh
    o = 1 if pressed else 0
    cx, cy = x + w // 2 + o, y + h // 2 + o

    def both(fn):
        if shadow:
            fn(1, shadow)
        fn(0, ink)

    if kind == "previous":
        both(lambda d, c: (rect(a, cx - 6 + d, cy - 3 + d, 2, 7, c), tri_left(a, cx - 4 + d, cy - 3 + d, 7, c),
                           tri_left(a, cx + d, cy - 3 + d, 7, c)))
    elif kind == "play":
        both(lambda d, c: tri_right(a, cx - 2 + d, cy - 4 + d, 9, c))
    elif kind == "pause":
        both(lambda d, c: (rect(a, cx - 4 + d, cy - 3 + d, 3, 7, c), rect(a, cx + 1 + d, cy - 3 + d, 3, 7, c)))
    elif kind == "stop":
        both(lambda d, c: rect(a, cx - 3 + d, cy - 3 + d, 7, 7, c))
    elif kind == "next":
        both(lambda d, c: (tri_right(a, cx - 5 + d, cy - 3 + d, 7, c), tri_right(a, cx - 1 + d, cy - 3 + d, 7, c),
                           rect(a, cx + 3 + d, cy - 3 + d, 2, 7, c)))
    elif kind == "eject":
        def ej(d, c):
            for r in range(4):
                rect(a, cx - 1 - r + d, cy - 4 + r + d, 2 * r + 3, 1, c)
            rect(a, cx - 4 + d, cy + 1 + d, 9, 2, c)
        both(ej)


def make_cbuttons():
    a = new(136, 36)
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18)]
    for kind, x, w, h in specs:
        for pressed, y in ((False, 0), (True, 18)):
            button_face(a, x, y, w, h, pressed)
            transport_icon(a, kind, x, y, w, h, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        button_face(a, 114, y, 22, 16, pressed)
        transport_icon(a, "eject", 114, y, 22, 16, pressed)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85)
# ------------------------------------------------------------------------------------------


def toggle(a, x, y, w, h, label, on, pressed, led="under"):
    button_face(a, x, y, w, h, pressed)
    o = 1 if pressed else 0
    acc = sink(ACCENT, 110) if T["light"] else ACCENT
    ink = acc if on else LABEL
    sh = None if (pressed or T["light"]) else BODY_LO
    tw = text_w(TINY, label)
    if led == "under":
        tx = x + (w - tw) // 2 + o
        ty = y + 3 + o
        draw_text(a, TINY, label, tx, ty, ink, shadow=sh)
        rect(a, x + 4 + o, y + h - 5 + o, w - 9, 1, acc if on else lerp(FACE_BOT, BODY_LO, 0.3))
    else:  # LED dot at the left
        tx = x + 7 + (w - 9 - tw) // 2 + o
        ty = y + (h - 5) // 2 + o
        draw_text(a, TINY, label, tx, ty, ink, shadow=sh)
        rect(a, x + 3 + o, y + h // 2 - 1 + o, 2, 2, acc if on else lerp(FACE_BOT, BODY_LO, 0.4))


def make_shufrep():
    a = new(92, 85)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        toggle(a, 0, y, 28, 15, "REPEAT", on, pressed)
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        toggle(a, x, 61, 23, 12, label, False, pressed, led="dot")
        toggle(a, x, 73, 23, 12, label, True, pressed, led="dot")
    return a


# ------------------------------------------------------------------------------------------
# monoster.bmp (56 x 24), playpaus.bmp, numbers.bmp, nums_ex.bmp, text.bmp
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, DISP)
    for y, on in ((0, True), (12, False)):
        col = INK if on else GHOST
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 29 + 13, y + 3, col)
    return a


def make_playpaus():
    # Standard sheet is 42 wide; 48 so the 9px "working" cell at x 39 fits too.
    a = new(48, 9, DISP)
    tri_right(a, 2, 1, 7, INK)                      # playing
    rect(a, 9 + 2, 1, 2, 7, INK)                    # paused
    rect(a, 9 + 5, 1, 2, 7, INK)
    rect(a, 18 + 2, 2, 5, 5, INK)                   # stopped
    rect(a, 36, 0, 3, 9, DISP)                      # not working
    rect(a, 39 + 1, 3, 1, 3, ACCENT)                # working: a lit dot in its 3px slice
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, DISP)
    for n in range(10):
        seven_seg(a, 9 * n, 0, DIGIT_SEGS[n])
    seven_seg(a, 90, 0, "")                           # blank cell: unlit segments
    if ex:
        rect(a, 99, 0, 9, 13, DISP)                   # minus: the middle segment alone
        for r, c in SEG["g"]:
            px(a, 99 + c, r, INK)
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    # the space cell (x 150, row 0) stays the plain display colour: the app tiles it to blank the title box
    a = new(155, 18, DISP)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5 else ch.upper()
            draw_text(a, FONT5, key, col * 5, row * 6, INK)
    return a


# ------------------------------------------------------------------------------------------
# posbar.bmp (307 x 10), volume.bmp / balance.bmp (68 x 433)
# ------------------------------------------------------------------------------------------


def slider_thumb(a, x, y, w, h, selected, grip="v"):
    """A pill of the theme's thumb colour (the group's: Olivia Hye's silver)."""
    base = THUMB
    top = lerp(base, (255, 255, 255), 0.45 if selected else 0.25)
    bot = lerp(base, (0, 0, 0), 0.10 if selected else 0.22)
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(top, bot, r / max(1, h - 1)))
    hi = lerp(base, (255, 255, 255), 0.7)
    lo = lerp(base, (0, 0, 0), 0.6)
    rect(a, x, y, w, 1, hi)
    rect(a, x, y, 1, h, hi)
    rect(a, x + w - 1, y, 1, h, lo)
    rect(a, x, y + h - 1, w, 1, lo)
    groove = lerp(base, (0, 0, 0), 0.45)
    cx = x + w // 2
    if grip == "v":
        for gx in (cx - 2, cx, cx + 2):
            rect(a, gx, y + 3, 1, h - 6, groove)
    elif grip == "moon":
        disc(a, x + w / 2 - 0.5, y + h / 2 - 0.5, 2.2, ACCENT if selected else lerp(ACCENT, base, 0.35))
    else:
        for gy in (y + h // 2 - 2, y + h // 2, y + h // 2 + 2):
            rect(a, x + 3, gy, w - 6, 1, groove)


def make_posbar(main):
    a = new(307, 10)
    a[0:10, 0:248] = main[72:82, 16:264]
    rect(a, 0, 2, 248, 6, DISP)
    sunken(a, 0, 2, 248, 6)
    rect(a, 2, 4, 244, 2, TRACK)
    # the twelve (or the subunit's) colours as faint ticks along the track
    cols = LEVEL
    for i, x in enumerate(range(8, 244, 12)):
        px(a, x, 4, lerp(TRACK, cols[i % len(cols)], 0.6))
    slider_thumb(a, 248, 0, 29, 10, False, grip="moon")
    slider_thumb(a, 278, 0, 29, 10, True, grip="moon")
    return a


def slider_thumbs(a):
    slider_thumb(a, 0, 422, 14, 11, True)
    slider_thumb(a, 15, 422, 14, 11, False)


def make_volume(main):
    """28 frames: the fill steps through the members' colours, one after another."""
    a = new(68, 433)
    seat = main[57:72, 107:175]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 0:68] = seat
        rect(a, 1, y + 3, 66, 7, DISP)
        sunken(a, 1, y + 3, 66, 7)
        level = (i + 1) / 28
        fill_to = 7 + round(level * 54)
        colour = lvl(LEVEL, i / 27)
        for x in range(2, 66):
            hgt = 1 + round(4 * (x - 2) / 63)
            top = y + 9 - hgt
            if x < fill_to:
                rect(a, x, top, 1, hgt, lerp(colour, (255, 255, 255), 0.25 * (x - 2) / 63))
            else:
                rect(a, x, top, 1, hgt, TRACK)
        rect(a, 0, y + 13, 68, 2, BODY)
    slider_thumbs(a)
    return a


def make_balance(main):
    a = new(68, 433)
    seat = main[57:72, 177:215]
    for i in range(28):
        y = i * 15
        a[y:y + 15, 9:47] = seat
        rect(a, 10, y + 3, 36, 7, DISP)
        sunken(a, 10, y + 3, 36, 7)
        t = i / 27
        colour = INK_MID if i == 0 else lvl(LEVEL, t)
        reach = round(12 * t)
        for x in range(11, 45):
            d = abs(x - 28)
            hgt = 1 + round(4 * min(d, 16) / 16)
            top = y + 9 - hgt
            col = colour if d <= max(1, reach) else TRACK
            rect(a, x, top, 1, hgt, col)
        rect(a, 28, y + 2, 1, 2, INK if i == 0 else INK_MID)
        rect(a, 9, y + 13, 38, 2, BODY)
    slider_thumbs(a)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_titlebar(lit):
    a = new(275, 14)
    body(a, 0, 0, 275, 14)
    rect(a, 0, 0, 275, 1, BODY_HI)
    rect(a, 0, 0, 1, 14, BODY_HI)
    rect(a, 274, 0, 1, 14, BODY_LO)
    title = T["eq_title"]
    tw = text_w(FONT5, title)
    px0 = (275 - tw) // 2 - 4
    pw = tw + 8
    rows = [5, 8] if T["texture"] != "stars" else [6]
    grill(a, 6, 0, px0 - 4 - 6, rows, lit)
    grill(a, px0 + pw + 4, 0, 260 - (px0 + pw + 4), rows, lit)
    plate_cap_left(a, px0 - 3, 2, lit, 10)
    plate(a, px0 + 1, 2, pw - 2, lit, 10)
    plate_cap_right(a, px0 + pw - 1, 2, lit, 10)
    title_text(a, title, px0 + 4, 4, lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def title_text(a, title, x, y, lit):
    """A plate title in FONT5; LOONA 1/3's slash in YeoJin's orange."""
    for c in title:
        col = INK if lit else TITLE_DIM
        if c == "/" and T.get("slash") and lit:
            col = sink(MEMBER[T["slash"]][1], 130) if T.get("light_disp") else lift(MEMBER[T["slash"]][1])
        x = draw_text(a, FONT5, c, x, y, col)


def eq_slider_frame(a, x, y, n):
    """14x63 slot whose lit column rises with the value (n of 0..27), through the members' colours."""
    rect(a, x, y, 14, 63, lerp(BODY, BODY_LO, 0.45))
    sunken(a, x, y, 14, 63)
    rect(a, x + 4, y + 2, 5, 59, DISP)
    sunken(a, x + 4, y + 2, 5, 59)
    v = n / 27
    centre = round((1 - v) * 51) + 5
    colour = lvl(LEVEL, v)
    for r in range(3, 60):
        on = r >= centre
        rect(a, x + 5, y + r, 3, 1, colour if on else TRACK)
    rect(a, x + 1, y + 30, 2, 1, LABEL_DIM)
    rect(a, x + 11, y + 30, 2, 1, LABEL_DIM)


def eq_label_colours():
    """Preamp + 10 bands: the group's first eleven members (the twelfth is the thumbs), or the
    subunit's members in turn."""
    if T.get("level"):
        return [LABEL_DIM] * 11
    cols = T["cols"]
    return [on_body(cols[i % len(cols)]) for i in range(11)]


def make_eqmain():
    a = new(275, 315)
    body(a, 0, 0, 275, 315)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = eq_titlebar(True)
    sunken(a, 85, 16, 115, 21)
    rect(a, 16, 36, 245, 68, lerp(BODY, BODY_LO, 0.2))
    sunken(a, 16, 36, 245, 68)
    rect(a, 39, 37, 1, 66, BODY_LO)
    rect(a, 40, 37, 1, 66, BODY_HI)
    for lbl, yy in (("+12DB", 41), ("+0DB", 66), ("-12DB", 92)):
        text_center(a, TINY, lbl, 58, yy, LABEL_DIM)
        rect(a, 42, yy + 2, 3, 1, LABEL_DIM)
        rect(a, 71, yy + 2, 3, 1, LABEL_DIM)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    lc = eq_label_colours()
    text_center(a, TINY, "PREAMP", 28, 106, lc[0])
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, lc[i + 1])

    # under the window: buttons
    mini_button(a, 0, 125, "close", True, pressed=True)
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        toggle(a, x, 119, w, 12, label, on, pressed, led="dot")
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    slider_thumb(a, 0, 164, 11, 11, False, grip="h")
    slider_thumb(a, 0, 176, 11, 11, True, grip="h")
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        button_face(a, 224, y, 44, 12, pressed)
        o = 1 if pressed else 0
        acc = sink(ACCENT, 110) if T["light"] else ACCENT
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 3 + o, acc if pressed else LABEL,
                    shadow=None if (pressed or T["light"]) else BODY_LO)
    # graph
    rect(a, 0, 294, 113, 19, DISP)
    for x in range(0, 113, 12):
        for y in range(1, 19, 2):
            px(a, 2 + x, 294 + y, GHOST)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, lerp(GHOST, INK_MID, 0.4))
    for r in range(19):
        px(a, 115, 294 + r, lvl(list(reversed(LEVEL)), r / 18))
    for x in range(113):
        px(a, x, 314, INK_MID if x % 3 != 2 else DISP)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20px-titled frames
# ------------------------------------------------------------------------------------------

BAR20_GRILL = [5, 8]
PLATE_Y = 3


def bar_rows():
    return [6] if T["texture"] == "stars" else BAR20_GRILL


def bar20(w, lit):
    a = new(w, 20)
    body(a, 0, 0, w, 20, tiled=True)
    rect(a, 0, 0, w, 1, BODY_HI)
    return a


def make_pledit():
    a = new(280, 186)
    body(a, 0, 0, 280, 186, tiled=True)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit)
        grill(t, 0, 0, 25, bar_rows(), lit)
        rect(t, 0, 19, 25, 1, BODY_LO)
        a[y:y + 20, 127:152] = t
        t = bar20(25, lit)
        rect(t, 0, 0, 1, 20, BODY_HI)
        grill(t, 4, 0, 21, bar_rows(), lit)
        rect(t, 11, 19, 14, 1, BODY_LO)
        rect(t, 11, 12, 1, 8, BODY_LO)
        a[y:y + 20, 0:25] = t
        # title
        t = bar20(100, lit)
        title = T["pl_title"]
        plate_cap_left(t, 0, PLATE_Y, lit)
        plate(t, 4, PLATE_Y, 92, lit)
        plate_cap_right(t, 96, PLATE_Y, lit)
        title_text(t, title, 50 - text_w(FONT5, title) // 2, PLATE_Y + 2, lit)
        rect(t, 0, 19, 100, 1, BODY_LO)
        a[y:y + 20, 26:126] = t
        # top-right corner: close button, the scrollbar groove's top
        t = bar20(25, lit)
        rect(t, 24, 0, 1, 20, BODY_LO)
        grill(t, 0, 0, 12, bar_rows(), lit)
        mini_button(t, 14, 3, "close", lit)
        rect(t, 0, 19, 6, 1, BODY_LO)
        rect(t, 5, 13, 1, 7, BODY_HI)
        rect(t, 9, 14, 10, 6, SLOT)
        rect(t, 9, 14, 10, 1, BODY_LO)
        rect(t, 9, 14, 1, 6, BODY_LO)
        rect(t, 18, 14, 1, 6, BODY_HI)
        a[y:y + 20, 153:178] = t

    # left side tile
    t = new(12, 29)
    body(t, 0, 0, 12, 29, tiled=True)
    rect(t, 0, 0, 1, 29, BODY_HI)
    rect(t, 11, 0, 1, 29, BODY_LO)
    rect(t, 4, 0, 1, 29, lerp(BODY, BODY_LO, 0.5))
    a[42:71, 0:12] = t
    # right side tile: list edge, scrollbar groove at 5..12, outer edge
    t = new(20, 29)
    body(t, 0, 0, 20, 29, tiled=True)
    rect(t, 0, 0, 1, 29, BODY_HI)
    rect(t, 19, 0, 1, 29, BODY_LO)
    rect(t, 4, 0, 10, 29, SLOT)
    rect(t, 4, 0, 1, 29, BODY_LO)
    rect(t, 13, 0, 1, 29, BODY_HI)
    rect(t, 8, 0, 2, 29, lerp(SLOT, BODY_LO, 0.4))
    a[42:71, 31:51] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        slider_thumb(a, x, 53, 8, 18, sel, grip="h")

    # bottom pieces
    def bottom_base(w):
        t = new(w, 38)
        body(t, 0, 0, w, 38, tiled=True)
        rect(t, 0, 0, w, 1, BODY_HI)
        rect(t, 0, 37, w, 1, BODY_LO)
        rect(t, 0, 33, w, 1, TRIM_LO)
        rect(t, 0, 34, w, 1, BODY_LO)
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, BODY_HI)
    rect(t, 11, 0, 1, 1, BODY_LO)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        button_face(t, bx, 8, 22, 18, False)
        text_center(t, TINY, lbl, bx + 11, 15, LABEL, shadow=None if T["light"] else BODY_LO)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, BODY_LO)
    rect(t, 130, 0, 1, 1, BODY_HI)
    display_box(t, 6, 9, 56, 8)
    icons = ["previous", "play", "pause", "stop", "next", "eject"]
    for k, kind in enumerate(icons):
        bx = 3 + 10 * k
        button_face(t, bx, 22, 10, 10, False)
        mini_transport_icon(t, kind, bx, 22)
    display_box(t, 65, 22, 33, 8)
    rect(t, 84, 22 + 2, 1, 1, INK_MID)  # the colon between minutes and seconds (text at 66+1/7/12/20/25)
    rect(t, 84, 22 + 5, 1, 1, INK_MID)
    button_face(t, 106, 8, 22, 18, False)
    text_center(t, TINY, "LIST", 117, 15, LABEL, shadow=None if T["light"] else BODY_LO)
    for k in range(4):
        for j in range(k + 1):
            gx, gy = 145 - 3 * k + 3 * j, 29 - 3 * j
            px(t, gx, gy, TRIM_HI if not T["light"] else TRIM_LO)
            px(t, gx + 1, gy + 1, BODY_LO)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


def mini_transport_icon(a, kind, x, y):
    ink, _ = icon_ink(False)
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
    a = new(194, 109)
    body(a, 0, 0, 194, 109, tiled=True)
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, fn):
            t = bar20(25, lit)
            fn(t)
            a[y:y + 20, px0:px0 + 25] = t

        def left(t):
            rect(t, 0, 0, 1, 20, BODY_HI)
            grill(t, 4, 0, 21, bar_rows(), lit)

        def left_end(t):
            grill(t, 0, 0, 16, bar_rows(), lit)
            plate_cap_left(t, 17, PLATE_Y, lit)
            plate(t, 21, PLATE_Y, 4, lit)

        def centre(t):
            plate(t, 0, PLATE_Y, 25, lit)

        def right_end(t):
            plate(t, 0, PLATE_Y, 4, lit)
            plate_cap_right(t, 4, PLATE_Y, lit)
            grill(t, 9, 0, 16, bar_rows(), lit)

        def fill(t):
            grill(t, 0, 0, 25, bar_rows(), lit)

        def right(t):
            grill(t, 0, 0, 12, bar_rows(), lit)
            mini_button(t, 14, 3, "close", lit)
            rect(t, 24, 0, 1, 20, BODY_LO)

        piece(0, left)
        piece(26, left_end)
        piece(52, centre)
        piece(78, right_end)
        piece(104, fill)
        piece(130, right)

    def bottom(w, grip, left_edge):
        t = new(w, 14)
        body(t, 0, 0, w, 14, tiled=True)
        rect(t, 0, 13, w, 1, BODY_LO)
        rect(t, 0, 9, w, 1, TRIM_LO)
        rect(t, 0, 10, w, 1, BODY_LO)
        if left_edge:
            rect(t, 0, 0, 1, 14, BODY_HI)
        else:
            rect(t, w - 1, 0, 1, 14, BODY_LO)
        if grip:
            for k in range(3):
                for j in range(k + 1):
                    gx, gy = w - 4 - 3 * k + 3 * j, 7 - 3 * j
                    px(t, gx, gy, TRIM_HI if not T["light"] else TRIM_LO)
                    px(t, gx + 1, gy + 1, BODY_LO)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]  # fill tile: no right edge
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        body(t, 0, 0, w, h, tiled=True)
        if outer_left:
            rect(t, 0, 0, 1, h, BODY_HI)
            rect(t, 4, 0, 1, h, lerp(BODY, BODY_LO, 0.5))
        else:
            rect(t, w - 1, 0, 1, h, BODY_LO)
            rect(t, w - 5, 0, 1, h, lerp(BODY, BODY_LO, 0.5))
        a[42:42 + h, x:x + w] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = t

    # letters: each row starts at x 1, letters in their own cells, 1px separators of x 0's colour
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            rect(a, x, y, w, 7, PLATE if lit else PLATE_DIM)
            draw_text(a, FONT5, c, x, y + 1, INK if lit else TITLE_DIM)
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp: Media Library colours along the top row, every other pixel from x 48
# ------------------------------------------------------------------------------------------


def genex_colours():
    dark_item = DISP
    return [
        dark_item,                                   # item background
        T["pl_normal"],                              # item text
        BODY,                                        # window background
        LABEL,                                       # button text
        LABEL if T["light"] else T["pl_normal"],     # window text
        BODY_LO if not T["light"] else TRIM_LO,      # dividers, sunken borders
        T["pl_selbg"],                               # selection bar
        FACE_BOT,                                    # list header background
        LABEL,                                       # list header text
        FACE_HI,                                     # header frame, light
        BODY_LO,                                     # header frame, dark
        FACE_PR,                                     # header frame, pressed
        BODY,                                        # header dead area
        FACE_BOT,                                    # scrollbar
        THUMB,                                       # scrollbar 2
        FACE_TOP,                                    # scrollbar pressed
        ACCENT,                                      # scrollbar pressed 2
        SLOT,                                        # scrollbar dead area
    ]


def make_genex():
    a = new(256, 64)
    body(a, 0, 1, 256, 63, tiled=True)
    rect(a, 0, 0, 256, 1, BODY)
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    button_face(a, 0, 1, 47, 15, False)
    button_face(a, 0, 16, 47, 15, True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    """Background, dots, 16 spectrum rows (top first) through the members (last member at the top),
    5 oscilloscope shades, peaks."""
    cols = list(reversed(LEVEL))
    spec = [lvl(cols, i / 15) for i in range(16)]
    osc = [lerp(INK, DISP, t) for t in (0.0, 0.15, 0.3, 0.45, 0.6)]
    return ([(DISP, "background"), (GHOST, "dots")]
            + [(c, f"spectrum {i + 1}" + (" (top)" if i == 0 else "")) for i, c in enumerate(spec)]
            + [(c, f"oscilloscope {i + 1}") for i, c in enumerate(osc)]
            + [(INK_HI, "peaks")])


def hexc(c):
    return "#%02X%02X%02X" % tuple(c)


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={hexc(T['pl_normal'])}\nCurrent={hexc(T['pl_current'])}\n"
                f"NormalBG={hexc(DISP)}\nSelectedBG={hexc(T['pl_selbg'])}\n"
                f"MbBG={hexc(DISP)}\nMbFG={hexc(T['pl_normal'])}\nFont=Arial\n")
    mark = "Odd Eye Circle logo" if T["key"] == "odd-eye-circle" else "LOONA logo"
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n", encoding="utf-8") as f:
        f.write(f"{T['name']} — a personal fan skin. LOONA name and marks © Blockberry Creative; "
                "for private use only.\n"
                f"{mark} © Blockberry Creative; private use only. Everything else is drawn from scratch "
                "by gen_skin.py.\n")


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
    for name, arr in sheets.items():
        SHEETS[name[:-4]] = save(arr, name)
    write_text_files()
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "readme.txt"]
    wsz = os.path.join(HERE, T["wsz"])
    with zipfile.ZipFile(wsz, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))   # deterministic archive
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
for _k, _v in {"<": "[", ">": "]", "{": "[", "}": "]"}.items():
    FONT_LOOKUP[_k] = FONT_LOOKUP[_v]


def draw_bitmap_text(dst, s, x, y):
    text = SHEETS["text"]
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, text, (col * 5, row * 6, 5, 6), x, y)
        x += 5


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
    # the app draws the title in a TrueType font (11px Arial) in text.bmp's ink colour
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("LiberationSans-Regular.ttf", 11)
    except OSError:
        font = ImageFont.load_default()
    clip = Image.new("RGB", (154, 14))
    clip.paste(img.crop((111, 22, 265, 36)))
    ImageDraw.Draw(clip).text((0, 2 + 3 + 2), state["title"],
                              fill=tuple(INK), font=font, anchor="lm")
    img.paste(clip, (111, 22))
    draw_bitmap_text(img, "192", 111, 43)
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=tuple(DISP))
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 9)
    except OSError:
        font = ImageFont.load_default()
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=tuple(T["pl_selbg"]))
        col = tuple(T["pl_current"]) if i == 1 else tuple(T["pl_normal"])
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
    # a stand-in picture: a gradient through the theme's art colours
    pw, ph = w - 22, h - 34
    arr = np.zeros((ph, pw, 3), dtype=np.uint8)
    for yy in range(ph):
        arr[yy, :] = ramp(T["art"], yy / max(1, ph - 1))
    img.paste(Image.fromarray(arr), (11, 20))
    return img


SONGS = {
    "loona": [("LOONA - Butterfly", "3:51"), ("LOONA - Hi High", "3:21"), ("LOONA - Why Not?", "3:21"),
              ("LOONA - So What", "3:27"), ("LOONA - Star", "3:07"), ("LOONA - PTT (Paint The Town)", "3:23"),
              ("LOONA - Favorite", "3:15"), ("LOONA - Flip That", "3:26"), ("LOONA - Heart Attack", "3:35"),
              ("LOONA - Eclipse", "3:27"), ("LOONA - Love Cherry Motion", "3:31")],
    "1-3": [("LOONA 1/3 - Love & Live", "3:23"), ("LOONA 1/3 - Sonatine", "3:44"),
            ("LOONA 1/3 - Into the New Heart", "1:56"), ("LOONA 1/3 - You and Me Together", "3:42"),
            ("LOONA 1/3 - Valentine Girl", "3:20"), ("LOONA 1/3 - Rain 51db", "3:39"),
            ("HeeJin - ViViD", "3:10"), ("HyunJin - Around You", "3:12"), ("HaSeul - Let Me In", "3:41"),
            ("YeoJin - Kiss Later", "3:11"), ("ViVi - Everyday I Love You", "3:26")],
    "odd-eye-circle": [("Odd Eye Circle - Girl Front", "3:36"), ("Odd Eye Circle - Sweet Crazy Love", "3:30"),
                       ("Odd Eye Circle - Loonatic", "3:24"), ("Odd Eye Circle - Chaotic", "3:25"),
                       ("Odd Eye Circle - Starlight", "3:30"), ("Odd Eye Circle - Air Force One", "3:16"),
                       ("Kim Lip - Eclipse", "3:27"), ("JinSoul - Singing in the Rain", "3:18"),
                       ("Choerry - Love Cherry Motion", "3:31"), ("Odd Eye Circle - Je Ne Sais Quoi", "3:24"),
                       ("Odd Eye Circle - Lucid", "3:20")],
    "yyxy": [("yyxy - love4eva", "3:16"), ("yyxy - Frozen", "3:51"), ("yyxy - one&only", "3:31"),
             ("yyxy - Dal Segno", "3:47"), ("yyxy - Love Me Like", "3:26"), ("yyxy - Rendezvous", "3:12"),
             ("Yves - New", "3:22"), ("Chuu - Heart Attack", "3:35"), ("Go Won - One&Only", "3:31"),
             ("Olivia Hye - Egoist", "3:30"), ("yyxy - Beauty & the Beat", "3:40")],
    "plus-plus": [("LOONA - Hi High", "3:21"), ("LOONA - Favorite", "3:15"), ("LOONA - Stylish", "3:27"),
                  ("LOONA - Perfect Love", "3:26"), ("LOONA - Heat", "3:20"), ("LOONA - Love4eva", "3:16")],
    "x-x": [("LOONA - Butterfly", "3:51"), ("LOONA - Satellite", "3:13"), ("LOONA - Colors", "3:30"),
            ("LOONA - Curiosity", "3:13"), ("LOONA - Where You At", "3:12"), ("LOONA - Hi High", "3:21")],
    "hash": [("LOONA - So What", "3:27"), ("LOONA - Load", "3:43"), ("LOONA - Number 1", "3:28"),
             ("LOONA - Day & Night", "3:36"), ("LOONA - 365", "3:12"), ("LOONA - Oh (Yes I Am)", "3:18")],
    "12-00": [("LOONA - Why Not?", "3:21"), ("LOONA - Star", "3:07"), ("LOONA - Voice", "3:08"),
              ("LOONA - Universe", "3:27"), ("LOONA - Fly Up", "3:24"), ("LOONA - Hide & Seek", "3:02")],
    "and": [("LOONA - PTT (Paint The Town)", "3:23"), ("LOONA - Be Honest", "3:12"), ("LOONA - Dance On My Own", "3:22"),
            ("LOONA - Wow", "3:07"), ("LOONA - Hello", "3:20"), ("LOONA - Paint The Town", "3:23")],
    "flip-that": [("LOONA - Flip That", "3:26"), ("LOONA - Pale Blue", "3:04"), ("LOONA - Playground", "3:09"),
                  ("LOONA - Need U", "3:17"), ("LOONA - Day By Day", "3:06"), ("LOONA - Feel It", "3:20")],
}
TICKER = {"loona": "LOONA - BUTTERFLY  ***", "1-3": "LOONA 1/3 - SONATINE  ***",
          "odd-eye-circle": "ODD EYE CIRCLE - GIRL FRONT", "yyxy": "YYXY - LOVE4EVA  ***",
          "plus-plus": "LOONA - HI HIGH  ***", "x-x": "LOONA - BUTTERFLY  ***", "hash": "LOONA - SO WHAT  ***",
          "12-00": "LOONA - WHY NOT?  ***", "and": "LOONA - PTT (PAINT THE TOWN)", "flip-that": "LOONA - FLIP THAT  ***"}


def preview():
    rows = SONGS[T.get("base", T["key"])]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=TICKER[T.get("base", T["key"])], bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="PAUSED: ECLIPSE (LIVE)", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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


def main(argv):
    keys = []
    it = iter(argv)
    for a in it:
        if a == "--theme":
            keys.append(next(it))
        elif a.startswith("--theme="):
            keys.append(a.split("=", 1)[1])
        elif a == "--list":
            print("\n".join(THEME_ORDER))
            return
        else:
            keys.append(a)
    for k in keys:
        if k not in THEMES:
            sys.exit(f"unknown theme {k!r}; themes: {', '.join(THEME_ORDER)}")
    for k in keys or THEME_ORDER:
        set_theme(k)
        names = build()
        preview()
        bad = [n for n in names if n.endswith(".bmp") and Image.open(os.path.join(OUT, n)).mode != "RGB"]
        assert not bad, bad
        print(f"{k:15s} -> {T['wsz']}, {T['preview']} ({len(names)} files)")


if __name__ == "__main__":
    main(sys.argv[1:])
