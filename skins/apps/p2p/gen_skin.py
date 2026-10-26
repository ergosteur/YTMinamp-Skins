#!/usr/bin/python3
"""P2P: classic Winamp 2.x skins in the style of the file-sharing clients of 1999-2006.

One procedural generator, a theme per client:

    napster   Napster 2.0 beta (1999-2001): dark navy / teal-grey, the cat-head logo
    limewire  LimeWire 4.x: lime-green caption, light grey panels, the lime slice
    kazaa     Kazaa Media Desktop 2.x (2002-2003): blue and white, the Theater player
    azureus   Azureus 2.x: native Windows grey (SWT), piece bars, the blue frog

Shared motifs: the client's tab row (EQ titlebar, and the playlist/gen titles as the active
tab), progress bars (volume, balance, EQ sliders, seek trough), the transfer list (playlist),
status LEDs (play/pause/stop as a green/amber/red light) and a status bar along the bottom of
the main window. Everything is drawn here from code; the clients' own logos (downloaded under
source/, private use only) appear once each.

    /usr/bin/python3 -I gen_skin.py [theme ...]     (no args: all four; --list lists them)

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
SOURCE = os.path.join(HERE, "source")
SCRATCH = os.path.join(HERE, "out", "scratch")
SEP = (255, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

F_SANS = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"
F_BOLD = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf"
F_ROUND = "/usr/share/fonts/aajohan-comfortaa-fonts/Comfortaa-Bold.otf"

# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

THEMES = {
    "napster": dict(
        wsz="Napster", subject="Napster (the original 1999-2001 client)", owner="Napster",
        style="dark", round=True,
        body=(40, 54, 72), hi=(84, 104, 128), lo=(10, 15, 24), slot=(24, 32, 44),
        cap=((66, 90, 118), (22, 32, 48)), cap_text=(240, 246, 250), cap_sub=(130, 196, 214),
        strip=((28, 38, 52), (34, 46, 62)), tab_on=((84, 112, 140), (40, 54, 72)),
        tab_off=((50, 66, 86), (36, 48, 64)), tab_text_on=(255, 255, 255), tab_text_off=(150, 172, 192),
        tab_hi=(130, 160, 186), tab_lo=(10, 15, 24), tab_mark=(96, 200, 224),
        disp=(4, 8, 16), disp_ink=(190, 232, 244), ghost=(16, 28, 38), disp_mid=(84, 132, 152),
        disp_edge=(70, 110, 130),
        acc=(64, 160, 188), acc_hi=(170, 228, 240), acc_lo=(26, 84, 108), trough=(8, 13, 22),
        trough_edge=(64, 84, 106), bar="flat",
        btn=((90, 112, 138), (44, 58, 78)), btn_dn=((22, 30, 42), (36, 48, 64)), btn_ink=(224, 238, 246),
        btn_ink_dn=(140, 226, 246), btn_edge=(8, 12, 20), btn_hi=(132, 156, 180),
        status_text=(168, 196, 212), status_bg=(26, 36, 50),
        pl=dict(normal="#C4DCE8", current="#FFFFFF", normal_bg="#060B14", selected_bg="#24425E",
                mb_bg="#060B14", mb_fg="#C4DCE8"),
        wordmark=("napster", F_ROUND, 11), version="v2.0 BETA 7",
        tabs=["SEARCH", "HOT LIST", "TRANSFER", "LIBRARY", "CHAT", "EQUALIZER"], tab_active="EQUALIZER",
        pl_title="TRANSFER", logo="napster",
        status=[("led", (90, 230, 120)), ("text", "ONLINE: 1,402,318 SONGS (5,623 GB) IN 12,987 LIBRARIES")],
        vis=[(230, 250, 255), (180, 236, 248), (130, 216, 238), (96, 196, 226), (70, 176, 210),
             (54, 156, 192), (44, 136, 172), (36, 116, 150), (30, 98, 130), (26, 84, 112),
             (22, 72, 98), (20, 62, 86), (18, 54, 76), (16, 46, 66), (14, 40, 58), (12, 34, 50)],
        osc=[(220, 248, 255), (150, 224, 242), (96, 196, 226), (60, 150, 184), (36, 104, 132)],
        peak=(255, 255, 255), vis_dots=(18, 30, 42),
        pic=((20, 40, 60), (70, 150, 180)),
    ),
    "limewire": dict(
        wsz="LimeWire", subject="LimeWire 4.x", owner="Lime Wire LLC",
        style="light", round=True,
        body=(228, 230, 226), hi=(255, 255, 255), lo=(140, 144, 138), slot=(206, 208, 204),
        cap=((142, 204, 84), (56, 136, 42)), cap_text=(255, 255, 255), cap_sub=(226, 248, 204),
        strip=((196, 202, 192), (214, 218, 210)), tab_on=((252, 253, 250), (228, 230, 226)),
        tab_off=((222, 226, 218), (204, 208, 200)), tab_text_on=(36, 104, 32), tab_text_off=(96, 100, 94),
        tab_hi=(255, 255, 255), tab_lo=(130, 134, 128), tab_mark=(96, 186, 64),
        disp=(255, 255, 255), disp_ink=(28, 74, 26), ghost=(232, 240, 228), disp_mid=(118, 156, 108),
        disp_edge=(150, 156, 146),
        acc=(80, 178, 64), acc_hi=(186, 236, 130), acc_lo=(42, 112, 34), trough=(248, 249, 246),
        trough_edge=(150, 156, 146), bar="glossy",
        btn=((255, 255, 254), (212, 216, 208)), btn_dn=((190, 216, 170), (226, 240, 212)),
        btn_ink=(54, 128, 40), btn_ink_dn=(30, 92, 24), btn_edge=(132, 138, 128), btn_hi=(255, 255, 255),
        status_text=(70, 80, 66), status_bg=(214, 218, 210),
        pl=dict(normal="#1E241C", current="#2E8A1E", normal_bg="#FFFFFF", selected_bg="#CFEBB6",
                mb_bg="#FFFFFF", mb_fg="#1E241C"),
        wordmark=("LimeWire", F_BOLD, 11), version="4.18",
        tabs=["SEARCH", "MONITOR", "LIBRARY", "CONNECTIONS", "EQUALIZER"], tab_active="EQUALIZER",
        pl_title="DOWNLOADS", logo="limewire",
        status=[("bars", 4), ("text", "TURBO-CHARGED"), ("gap", 8), ("text", "SHARING 1,024 FILES"),
                ("gap", 8), ("text", "DOWN 64 KB/S  UP 12 KB/S")],
        vis=[(30, 96, 20), (44, 120, 30), (58, 142, 38), (72, 160, 46), (86, 176, 54), (104, 190, 64),
             (122, 202, 76), (140, 212, 90), (156, 220, 104), (172, 228, 120), (186, 234, 138),
             (200, 240, 156), (212, 244, 174), (222, 247, 192), (232, 250, 210), (240, 252, 226)],
        osc=[(30, 96, 20), (60, 140, 40), (90, 176, 56), (130, 206, 84), (170, 228, 124)],
        peak=(20, 60, 16), vis_dots=(236, 240, 234),
        pic=((60, 140, 40), (210, 240, 170)),
    ),
    "kazaa": dict(
        wsz="Kazaa", subject="Kazaa Media Desktop 2.x", owner="Sharman Networks",
        style="light", round=True,
        body=(222, 232, 248), hi=(255, 255, 255), lo=(110, 138, 186), slot=(198, 214, 240),
        cap=((60, 116, 204), (18, 52, 124)), cap_text=(255, 255, 255), cap_sub=(184, 214, 255),
        strip=((168, 196, 238), (200, 218, 246)), tab_on=((255, 255, 255), (222, 232, 248)),
        tab_off=((206, 222, 248), (184, 204, 238)), tab_text_on=(18, 50, 120), tab_text_off=(64, 92, 140),
        tab_hi=(255, 255, 255), tab_lo=(96, 126, 178), tab_mark=(255, 146, 24),
        disp=(0, 0, 0), disp_ink=(236, 242, 255), ghost=(20, 26, 12), disp_mid=(120, 150, 196),
        disp_edge=(60, 90, 150), seg=(196, 232, 44),
        acc=(56, 120, 224), acc_hi=(156, 200, 255), acc_lo=(22, 64, 156), trough=(250, 252, 255),
        trough_edge=(110, 138, 186), bar="chunks",
        btn=((112, 162, 236), (28, 78, 168)), btn_dn=((16, 48, 116), (52, 102, 190)),
        btn_ink=(255, 255, 255), btn_ink_dn=(255, 190, 90), btn_edge=(14, 40, 100), btn_hi=(176, 210, 255),
        status_text=(30, 56, 110), status_bg=(200, 216, 242),
        pl=dict(normal="#10204A", current="#1E5FD0", normal_bg="#FFFFFF", selected_bg="#CFE0FA",
                mb_bg="#FFFFFF", mb_fg="#10204A"),
        wordmark=("Kazaa Media Desktop", F_BOLD, 10), version="",
        tabs=["WEB", "SEARCH", "MY KAZAA", "TRAFFIC", "THEATER"], tab_active="THEATER",
        pl_title="TRAFFIC", logo="kazaa",
        status=[("text", "PARTICIPATION LEVEL:"), ("meter", 0.55), ("text", "MEDIUM"), ("gap", 10),
                ("led", (60, 200, 60)), ("text", "3,412,987 USERS ONLINE")],
        vis=[(255, 236, 120), (240, 240, 80), (210, 236, 50), (180, 226, 44), (150, 210, 50),
             (120, 196, 70), (96, 180, 100), (76, 164, 136), (64, 148, 170), (56, 132, 200),
             (52, 116, 220), (48, 100, 220), (44, 84, 204), (40, 70, 180), (34, 56, 150), (28, 44, 120)],
        osc=[(255, 255, 255), (220, 240, 120), (196, 232, 44), (120, 180, 60), (60, 110, 180)],
        peak=(255, 170, 40), vis_dots=(16, 20, 30),
        pic=((12, 30, 80), (60, 120, 220)),
    ),
    "azureus": dict(
        wsz="Azureus", subject="Azureus 2.x (the BitTorrent client)", owner="Aelitis / Vuze",
        style="win", round=False,
        body=(212, 208, 200), hi=(255, 255, 255), lo=(64, 64, 64), shadow=(128, 128, 128),
        slot=(212, 208, 200),
        cap=((10, 36, 106), (166, 202, 240)), cap_text=(255, 255, 255), cap_sub=(214, 228, 246),
        cap_i=((128, 128, 128), (192, 192, 192)),
        strip=((212, 208, 200), (212, 208, 200)), tab_on=((222, 219, 212), (212, 208, 200)),
        tab_off=((200, 196, 188), (200, 196, 188)), tab_text_on=(0, 0, 0), tab_text_off=(70, 70, 70),
        tab_hi=(255, 255, 255), tab_lo=(64, 64, 64), tab_mark=(10, 36, 106),
        disp=(255, 255, 255), disp_ink=(0, 0, 0), ghost=(234, 234, 234), disp_mid=(128, 128, 128),
        disp_edge=(128, 128, 128),
        acc=(28, 84, 196), acc_hi=(120, 166, 236), acc_lo=(10, 40, 120), trough=(255, 255, 255),
        trough_edge=(128, 128, 128), bar="pieces",
        btn=((212, 208, 200), (212, 208, 200)), btn_dn=((212, 208, 200), (212, 208, 200)),
        btn_ink=(0, 0, 0), btn_ink_dn=(0, 0, 0), btn_edge=(64, 64, 64), btn_hi=(255, 255, 255),
        status_text=(0, 0, 0), status_bg=(212, 208, 200),
        pl=dict(normal="#000000", current="#0A246A", normal_bg="#FFFFFF", selected_bg="#C4D4EE",
                mb_bg="#FFFFFF", mb_fg="#000000"),
        wordmark=("Azureus", F_BOLD, 10), version="2.5.0.4",
        tabs=["MY TORRENTS", "PEERS", "PIECES", "FILES", "INFO", "EQUALIZER"], tab_active="EQUALIZER",
        pl_title="MY TORRENTS", logo="azureus",
        status=[("ratio", None), ("led", (0, 200, 0)), ("text", "NAT OK"), ("gap", 6),
                ("text", "DHT: 1,234,567 USERS"), ("gap", 6), ("text", "D: 64.0 KB/S  U: 12.0 KB/S")],
        vis=[(10, 36, 106), (16, 50, 130), (22, 64, 152), (28, 80, 176), (34, 94, 196), (44, 108, 210),
             (58, 122, 220), (74, 136, 228), (92, 150, 234), (110, 164, 238), (128, 178, 242),
             (146, 192, 245), (164, 204, 247), (182, 216, 249), (200, 226, 251), (216, 236, 253)],
        osc=[(10, 36, 106), (28, 84, 196), (80, 140, 230), (140, 186, 244), (190, 216, 250)],
        peak=(200, 20, 20), vis_dots=(238, 238, 238),
        pic=((10, 36, 106), (166, 202, 240)),
    ),
}

T = SimpleNamespace()
OUT = ""
_rng = None


def set_theme(name):
    global OUT, _rng
    T.__dict__.clear()
    T.name = name
    T.__dict__.update(THEMES[name])
    T.__dict__.setdefault("seg", T.disp_ink)
    T.__dict__.setdefault("shadow", lerp(T.lo, T.body, 0.5))
    OUT = os.path.join(HERE, "out", name)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    _rng = np.random.default_rng(1999)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    i = min(n - 1, int(t * n))
    return lerp(stops[i], stops[i + 1], t * n - i)


def hexcol(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int)
# ------------------------------------------------------------------------------------------


def new(w, h, col=None):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = T.body if col is None else col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0:
        a[max(0, y):max(0, y + h), max(0, x):max(0, x + w)] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def vgrad(a, x, y, w, h, top, bot):
    for r in range(h):
        rect(a, x, y + r, w, 1, lerp(top, bot, r / max(1, h - 1)))


def frame(a, x, y, w, h, tl, br):
    rect(a, x, y, w - 1, 1, tl)
    rect(a, x, y, 1, h - 1, tl)
    rect(a, x, y + h - 1, w, 1, br)
    rect(a, x + w - 1, y, 1, h, br)


def raised(a, x, y, w, h):
    if T.style == "win":
        frame(a, x, y, w, h, T.hi, T.lo)
        frame(a, x + 1, y + 1, w - 2, h - 2, T.body, T.shadow)
    else:
        frame(a, x, y, w, h, T.hi, T.lo)


def sunken(a, x, y, w, h):
    if T.style == "win":
        frame(a, x, y, w, h, T.shadow, T.hi)
        frame(a, x + 1, y + 1, w - 2, h - 2, T.lo, T.body)
    else:
        frame(a, x, y, w, h, T.lo, T.hi)


def field(a, x, y, w, h, fill):
    """A display/edit field; (x, y, w, h) is its inside; the border goes round it."""
    rect(a, x, y, w, h, fill)
    if T.style == "win":
        sunken(a, x - 2, y - 2, w + 4, h + 4)
    else:
        frame(a, x - 1, y - 1, w + 2, h + 2, T.disp_edge, T.disp_edge)
        if T.style == "dark":
            frame(a, x - 2, y - 2, w + 4, h + 4, T.lo, T.hi)


def round_corners(a, x, y, w, h, col_fn):
    """Knocks the four corner pixels back to the background (col_fn(x, y) gives it)."""
    for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
        px(a, cx, cy, col_fn(cx, cy))


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def unfocus(a):
    """The unfocused look of a bar: colours pulled most of the way to grey, a little toward body."""
    f = a.astype(np.float64)
    lum = (f[..., 0] * 0.3 + f[..., 1] * 0.59 + f[..., 2] * 0.11)[..., None]
    g = lum * 0.7 + f * 0.3
    g = g * 0.8 + np.array(T.body) * 0.2
    return np.round(g).astype(np.int32)


# ------------------------------------------------------------------------------------------
# Fonts: hand-made pixel fonts, plus TrueType for the wordmarks
# ------------------------------------------------------------------------------------------

def G(*rows):
    return list(rows)


FONT5 = {
    "A": G(".##.", "#..#", "####", "#..#", "#..#"), "B": G("###.", "#..#", "###.", "#..#", "###."),
    "C": G(".###", "#...", "#...", "#...", ".###"), "D": G("###.", "#..#", "#..#", "#..#", "###."),
    "E": G("####", "#...", "###.", "#...", "####"), "F": G("####", "#...", "###.", "#...", "#..."),
    "G": G(".###", "#...", "#.##", "#..#", ".###"), "H": G("#..#", "#..#", "####", "#..#", "#..#"),
    "I": G("###", ".#.", ".#.", ".#.", "###"), "J": G("...#", "...#", "...#", "#..#", ".##."),
    "K": G("#..#", "#.#.", "##..", "#.#.", "#..#"), "L": G("#...", "#...", "#...", "#...", "####"),
    "M": G("#...#", "##.##", "#.#.#", "#...#", "#...#"), "N": G("#..#", "##.#", "#.##", "#..#", "#..#"),
    "O": G(".##.", "#..#", "#..#", "#..#", ".##."), "P": G("###.", "#..#", "###.", "#...", "#..."),
    "Q": G(".##.", "#..#", "#..#", "#.#.", ".#.#"), "R": G("###.", "#..#", "###.", "#.#.", "#..#"),
    "S": G(".###", "#...", ".##.", "...#", "###."), "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#..#", "#..#", "#..#", "#..#", ".##."), "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#...#", "#...#", "#.#.#", "##.##", "#...#"), "X": G("#..#", "#..#", ".##.", "#..#", "#..#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."), "Z": G("####", "...#", ".##.", "#...", "####"),
    "0": G("###", "#.#", "#.#", "#.#", "###"), "1": G(".#.", "##.", ".#.", ".#.", "###"),
    "2": G("###", "..#", "###", "#..", "###"), "3": G("###", "..#", ".##", "..#", "###"),
    "4": G("#.#", "#.#", "###", "..#", "..#"), "5": G("###", "#..", "###", "..#", "###"),
    "6": G("###", "#..", "###", "#.#", "###"), "7": G("###", "..#", ".#.", ".#.", ".#."),
    "8": G("###", "#.#", "###", "#.#", "###"), "9": G("###", "#.#", "###", "..#", "###"),
    '"': G("#.#", "#.#", "...", "...", "..."), "@": G(".##.", "#.##", "#.##", "#...", ".###"),
    "…": G(".....", ".....", ".....", ".....", "#.#.#"), ".": G(".", ".", ".", ".", "#"),
    ":": G(".", "#", ".", "#", "."), "(": G(".#", "#.", "#.", "#.", ".#"), ")": G("#.", ".#", ".#", ".#", "#."),
    "-": G("...", "...", "###", "...", "..."), "'": G("#", "#", ".", ".", "."),
    "!": G("#", "#", "#", ".", "#"), "_": G("....", "....", "....", "....", "####"),
    "+": G("...", ".#.", "###", ".#.", "..."), "\\": G("#..", "#..", ".#.", "..#", "..#"),
    "/": G("..#", "..#", ".#.", "#..", "#.."), "[": G("##", "#.", "#.", "#.", "##"),
    "]": G("##", ".#", ".#", ".#", "##"), "^": G(".#.", "#.#", "...", "...", "..."),
    "&": G(".#..", "#.#.", ".#..", "#.#.", ".#.#"), "%": G("#.#", "..#", ".#.", "#..", "#.#"),
    ",": G("..", "..", "..", ".#", "#."), "=": G("...", "###", "...", "###", "..."),
    "$": G(".###", "#.#.", ".##.", ".#.#", "###."), "#": G(".#.#", "####", ".#.#", "####", ".#.#"),
    "å": G(".##.", ".##.", "#..#", "####", "#..#"), "ö": G("#..#", ".##.", "#..#", "#..#", ".##."),
    "ä": G("#..#", ".##.", "#..#", "####", "#..#"), "?": G("###.", "...#", ".##.", "....", ".#.."),
    "*": G("#.#", ".#.", "###", ".#.", "#.#"), " ": G("..", "..", "..", "..", ".."),
}
# text.bmp's cells are 5 wide: the 5-wide M and W only there get narrowed
FONT5_TXT = dict(FONT5)
FONT5_TXT["M"] = G("#..#", "####", "####", "#..#", "#..#")
FONT5_TXT["W"] = G("#..#", "#..#", "####", "####", "#..#")

TINY = {
    "A": G(".#.", "#.#", "###", "#.#", "#.#"), "B": G("##.", "#.#", "##.", "#.#", "##."),
    "C": G(".##", "#..", "#..", "#..", ".##"), "D": G("##.", "#.#", "#.#", "#.#", "##."),
    "E": G("###", "#..", "##.", "#..", "###"), "F": G("###", "#..", "##.", "#..", "#.."),
    "G": G(".##", "#..", "#.#", "#.#", ".##"), "H": G("#.#", "#.#", "###", "#.#", "#.#"),
    "I": G("###", ".#.", ".#.", ".#.", "###"), "J": G("..#", "..#", "..#", "#.#", ".#."),
    "K": G("#.#", "#.#", "##.", "#.#", "#.#"), "L": G("#..", "#..", "#..", "#..", "###"),
    "M": G("#...#", "##.##", "#.#.#", "#...#", "#...#"), "N": G("#..#", "##.#", "#.##", "#..#", "#..#"),
    "O": G(".#.", "#.#", "#.#", "#.#", ".#."), "P": G("##.", "#.#", "##.", "#..", "#.."),
    "Q": G(".#.", "#.#", "#.#", "##.", ".##"), "R": G("##.", "#.#", "##.", "#.#", "#.#"),
    "S": G(".##", "#..", ".#.", "..#", "##."), "T": G("###", ".#.", ".#.", ".#.", ".#."),
    "U": G("#.#", "#.#", "#.#", "#.#", "###"), "V": G("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": G("#...#", "#...#", "#.#.#", "##.##", "#...#"), "X": G("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": G("#.#", "#.#", ".#.", ".#.", ".#."), "Z": G("###", "..#", ".#.", "#..", "###"),
    " ": G("..", "..", "..", "..", ".."),
}
for _c in "0123456789+-.:,()/%":
    TINY[_c] = FONT5[_c]


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
                    px(a, x + k, y + r, col)
        x += len(g[0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1, shadow=None):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow)


def ttf(a, text, x, y, path, size, col, shadow=None, aa=True):
    """TrueType text with its cap tops near row y; returns the x after it."""
    font = ImageFont.truetype(path, size)
    im = Image.new("L", (a.shape[1], a.shape[0]), 0)
    d = ImageDraw.Draw(im)
    if not aa:
        d.fontmode = "1"
    top = font.getbbox("H")[1]
    for (dx, dy), c in ((((1, 1), shadow),) if shadow else ()) + (((0, 0), col),):
        im.paste(0, (0, 0, im.width, im.height))
        d.text((x + dx, y + dy - top), text, fill=255, font=font)
        m = np.array(im).astype(np.float64)[..., None] / 255
        a[:] = np.round(a * (1 - m) + np.array(c) * m).astype(np.int32)
    return x + int(round(d.textlength(text, font=font)))


def ttf_w(text, path, size):
    font = ImageFont.truetype(path, size)
    return int(round(ImageDraw.Draw(Image.new("L", (1, 1))).textlength(text, font=font)))


# ------------------------------------------------------------------------------------------
# Logos (source/, private use only)
# ------------------------------------------------------------------------------------------


def _load(path, h=400):
    src = os.path.join(SOURCE, path)
    if src.endswith(".svg"):
        png = os.path.join(SCRATCH, path.replace("/", "-") + ".png")
        subprocess.run(["/usr/bin/rsvg-convert", "-h", str(h), src, "-o", png], check=True)
        return Image.open(png).convert("RGBA")
    return Image.open(src).convert("RGBA")


def _crop_alpha(img):
    return img.crop(img.getchannel("A").getbbox())


def logo(name, box_w, box_h):
    """The client's mark, fitted into box_w x box_h (RGBA)."""
    if name == "napster":
        img = _crop_alpha(_load("napster/logo.svg"))
    elif name == "limewire":
        img = _crop_alpha(_load("limewire-png/logo.png"))
    elif name == "kazaa":
        img = _crop_alpha(_load("kazaa/logo.svg"))
        # the SVG's square white card behind the K: make it transparent
        arr = np.array(img).astype(np.int32)
        white = (arr[..., :3].min(-1) > 235)
        arr[white, 3] = 0
        img = _crop_alpha(Image.fromarray(arr.astype(np.uint8), "RGBA"))
    elif name == "azureus":
        # the frog off the torrent-file icon: its blue body and dark markings, not the white page
        img = _load("azureus/logo.png").crop((22, 10, 104, 96))     # the frog, above the label
        arr = np.array(img).astype(np.int32)
        r, g, b, al = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
        frog = (al > 40) & (((b - r) > 40) | ((r + g + b) < 210))
        arr[..., 3] = np.where(frog, 255, 0)
        img = _crop_alpha(Image.fromarray(arr.astype(np.uint8), "RGBA"))
    s = min(box_w / img.width, box_h / img.height)
    return img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)


def paste_rgba(a, img, x, y):
    arr = np.array(img).astype(np.float64)
    h, w = arr.shape[:2]
    al = arr[..., 3:4] / 255
    reg = a[y:y + h, x:x + w].astype(np.float64)
    a[y:y + h, x:x + w] = np.round(reg * (1 - al) + arr[..., :3] * al).astype(np.int32)


# ------------------------------------------------------------------------------------------
# Shared pieces: buttons, tabs, progress bars, LEDs
# ------------------------------------------------------------------------------------------


def button_face(a, x, y, w, h, pressed, bg=None):
    bg = T.body if bg is None else bg
    if T.style == "win":
        rect(a, x, y, w, h, T.body)
        if pressed:
            frame(a, x, y, w, h, T.lo, T.lo)
            frame(a, x + 1, y + 1, w - 2, h - 2, T.shadow, T.shadow)
        else:
            frame(a, x, y, w, h, T.hi, T.lo)
            frame(a, x + 1, y + 1, w - 2, h - 2, T.body, T.shadow)
        return
    top, bot = T.btn_dn if pressed else T.btn
    vgrad(a, x, y, w, h, top, bot)
    frame(a, x, y, w, h, T.btn_edge, T.btn_edge)
    if not pressed:
        rect(a, x + 1, y + 1, w - 2, 1, T.btn_hi)
    else:
        rect(a, x + 1, y + 1, w - 2, 1, lerp(top, T.btn_edge, 0.5))
    if T.round:
        round_corners(a, x, y, w, h, lambda cx, cy: bg)
        for cx, cy in ((x + 1, y + 1), (x + w - 2, y + 1), (x + 1, y + h - 2), (x + w - 2, y + h - 2)):
            px(a, cx, cy, lerp(a[cy, cx], T.btn_edge, 0.5))


def led(a, x, y, col, size=5, bg=None, on=True):
    """A round status light, size 5 or 7."""
    bg = T.body if bg is None else bg
    c = col if on else lerp(col, (40, 40, 40), 0.7)
    if size == 5:
        shape = [".###.", "#####", "#####", "#####", ".###."]
    else:
        shape = ["..###..", ".#####.", "#######", "#######", "#######", ".#####.", "..###.."]
    n = len(shape)
    for r, row in enumerate(shape):
        for k, ch in enumerate(row):
            if ch == "#":
                t = ((k - n / 2 + 1.2) ** 2 + (r - n / 2 + 1.2) ** 2) ** 0.5 / n
                px(a, x + k, y + r, lerp(lerp(c, WHITE, 0.55), lerp(c, BLACK, 0.3), min(1, t * 1.6)))
    rim = lerp(c, BLACK, 0.55)
    for r, row in enumerate(shape):
        for k, ch in enumerate(row):
            if ch == ".":
                nb = [(r + dr, k + dk) for dr, dk in ((0, 1), (0, -1), (1, 0), (-1, 0))]
                if any(0 <= rr < n and 0 <= kk < n and shape[rr][kk] == "#" for rr, kk in nb):
                    px(a, x + k, y + r, lerp(rim, bg, 0.55))


def hbar(a, x, y, w, h, frac, seed=0, edge=True):
    """A horizontal progress bar (outer box x, y, w, h), filled to frac, in the theme's style."""
    if edge:
        rect(a, x, y, w, h, T.trough)
        frame(a, x, y, w, h, T.trough_edge, T.trough_edge if T.style != "win" else T.hi)
        if T.style == "win":
            frame(a, x, y, w, h, T.shadow, T.hi)
        x, y, w, h = x + 1, y + 1, w - 2, h - 2
    fill = int(round(w * frac))
    if T.bar == "flat":
        rect(a, x, y, fill, h, T.acc)
        rect(a, x, y, fill, 1, T.acc_hi)
        rect(a, x, y + h - 1, fill, 1, T.acc_lo)
        if 0 < fill < w:
            rect(a, x + fill - 1, y, 1, h, T.acc_hi)
    elif T.bar == "glossy":
        for r in range(h):
            t = r / max(1, h - 1)
            c = lerp(T.acc_hi, T.acc, t * 2) if t < 0.5 else lerp(T.acc, T.acc_lo, (t - 0.5) * 2)
            rect(a, x, y + r, fill, 1, c)
    elif T.bar == "chunks":
        cw, gap = 5, 1
        for cx in range(x + 1, x + fill, cw + gap):
            ww = min(cw, x + fill - cx)
            for r in range(h - 2):
                t = r / max(1, h - 3)
                c = lerp(T.acc_hi, T.acc, min(1, t * 2.2)) if t < 0.5 else lerp(T.acc, T.acc_lo, (t - 0.5) * 2)
                rect(a, cx, y + 1 + r, ww, 1, c)
    elif T.bar == "pieces":
        rng = np.random.default_rng(seed)
        pw = 2
        for i, cx in enumerate(range(x, x + w, pw)):
            ww = min(pw, x + w - cx)
            t = (cx - x) / w
            have = t < frac or rng.random() < 0.18 * (1 - t)
            if have:
                rect(a, cx, y, ww, h, T.acc)
                rect(a, cx, y, ww, 1, T.acc_hi)


def tab(a, x, y, w, h, label, active, font=TINY, bg=None, text_y=None):
    """A tab of the client's tab row; its bottom edge (y + h - 1) opens into the panel if active."""
    top, bot = T.tab_on if active else T.tab_off
    if not active:
        y, h = y + 1, h - 1
    vgrad(a, x, y, w, h, top, bot)
    rect(a, x, y, w, 1, T.tab_hi)
    rect(a, x, y, 1, h, T.tab_hi)
    rect(a, x + w - 1, y, 1, h, T.tab_lo)
    if T.style == "win":
        rect(a, x + w - 2, y + 1, 1, h - 1, T.shadow)
    if T.round:
        bgc = bg if bg is not None else None
        for cx, cy in ((x, y), (x + w - 1, y)):
            px(a, cx, cy, bgc if bgc is not None else a[cy, cx - 1 if cx > 0 else cx + 1])
        px(a, x + 1, y + 1, T.tab_hi)
        px(a, x + w - 2, y + 1, T.tab_lo)
    else:
        if bg is not None:
            px(a, x, y, bg)
            px(a, x + w - 1, y, bg)
    if active and T.tab_mark is not None and T.style != "win":
        rect(a, x + 2, y + 1, w - 4, 1, T.tab_mark)
    if label:
        fh = len(font["A"])
        ty = text_y if text_y is not None else y + (h - fh) // 2 + (0 if active else 0)
        text_center(a, font, label, x + w // 2, ty, T.tab_text_on if active else T.tab_text_off)


def strip_bg(a, x, y, w, h):
    vgrad(a, x, y, w, h, *T.strip)


# ------------------------------------------------------------------------------------------
# Titlebar buttons and bars
# ------------------------------------------------------------------------------------------


def mini_button(a, x, y, kind, lit=True, pressed=False, bg=None):
    """9x9 titlebar button."""
    if T.style == "win":
        rect(a, x, y, 9, 9, T.body)
        if pressed:
            frame(a, x, y, 9, 9, T.lo, T.lo)
            frame(a, x + 1, y + 1, 7, 7, T.shadow, T.shadow)
        else:
            frame(a, x, y, 9, 9, T.hi, T.lo)
            frame(a, x + 1, y + 1, 7, 7, T.body, T.shadow)
        ink = BLACK
    else:
        button_face(a, x, y, 9, 9, pressed, bg=bg if bg is not None else a[y, x].copy())
        ink = T.btn_ink_dn if pressed else T.btn_ink
    o = 1 if pressed else 0
    X, Y = x + o, y + o
    if kind == "options":
        if T.style == "win":
            rect(a, X + 2, Y + 3, 5, 1, ink)
            rect(a, X + 3, Y + 4, 3, 1, ink)
            px(a, X + 4, Y + 5, ink)
        else:
            rect(a, X + 3, Y + 3, 3, 3, ink)
    elif kind == "minimize":
        rect(a, X + 2, Y + 5, 4, 2, ink)
    elif kind == "shade":
        rect(a, X + 2, Y + 2, 5, 2, ink)
        rect(a, X + 2, Y + 2, 1, 5, ink)
        rect(a, X + 6, Y + 2, 1, 5, ink)
        rect(a, X + 2, Y + 6, 5, 1, ink)
    elif kind == "close":
        for i in range(5):
            px(a, X + 2 + i, Y + 2 + i, ink)
            px(a, X + 6 - i, Y + 2 + i, ink)
            if T.style == "win":
                px(a, X + 3 + i if i < 4 else X + 6, Y + 2 + i, ink)


def caption_bg(a, w, lit):
    """The main window's caption, 14 rows (rows 0-1 are the window frame's top)."""
    if T.style == "win":
        rect(a, 0, 0, w, 14, T.body)
        rect(a, 0, 0, w - 1, 1, T.body)
        rect(a, 1, 1, w - 2, 1, T.hi)
        rect(a, 0, 0, 1, 14, T.body)
        rect(a, 1, 1, 1, 13, T.hi)
        rect(a, w - 1, 0, 1, 14, T.lo)
        rect(a, w - 2, 1, 1, 13, T.shadow)
        c0, c1 = T.cap if lit else T.cap_i
        for x in range(2, w - 2):
            rect(a, x, 2, 1, 12, lerp(c0, c1, (x - 2) / (w - 5)))
    else:
        vgrad(a, 0, 0, w, 14, *T.cap)
        rect(a, 0, 0, w, 1, lerp(T.cap[0], WHITE, 0.35))
        rect(a, 0, 0, 1, 14, lerp(T.cap[0], WHITE, 0.2))
        rect(a, w - 1, 0, 1, 14, T.lo)
        rect(a, 0, 13, w, 1, lerp(T.cap[1], BLACK, 0.3))


def main_titlebar(lit):
    a = new(275, 14)
    caption_bg(a, 275, lit)
    word, path, size = T.wordmark
    x = 18
    if T.logo == "kazaa":
        paste_rgba(a, logo("kazaa", 14, 12), 18, 1)
        x = 33
    shadow = lerp(T.cap[1], BLACK, 0.5) if T.style != "win" else None
    if T.name == "limewire":
        shadow = (40, 100, 30)
    x = ttf(a, word, x, 3, path, size, T.cap_text, shadow=shadow)
    if T.version:
        draw_text(a, TINY, T.version, x + 4, 5, T.cap_sub)
    bg = None
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    return a if lit else unfocus(a)


def tab_row(a, x0, y, h, labels, active, bg_fn=None, gap=1):
    """Lays tabs left to right from x0; returns the x after the last."""
    x = x0
    for lab in labels:
        w = text_w(TINY, lab) + 8
        tab(a, x, y, w, h, lab, lab == active, bg=None)
        x += w + gap
    return x


def eq_titlebar(lit):
    a = new(275, 14)
    strip_bg(a, 0, 0, 275, 14)
    rect(a, 0, 0, 275, 1, T.hi)
    rect(a, 0, 0, 1, 14, T.hi)
    rect(a, 274, 0, 1, 14, T.lo)
    rect(a, 1, 13, 273, 1, T.tab_lo)
    gap = 1 if T.style != "win" else 0
    end = tab_row(a, 5, 2, 12, T.tabs, None, gap=gap)
    assert end < 258, (T.name, end)
    # draw the active one again on top, joined to the panel
    x = 5
    for lab in T.tabs:
        w = text_w(TINY, lab) + 8
        if lab == T.tab_active:
            tab(a, x - (1 if T.style == "win" else 0), 1, w + (2 if T.style == "win" else 0), 13, lab, True)
            rect(a, x + 1 - (1 if T.style == "win" else 0), 13, w - 2 + (2 if T.style == "win" else 0), 1,
                 T.tab_on[1])
        x += w + gap
    mini_button(a, 264, 3, "close", lit)
    return a if lit else unfocus(a)


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43)
    rect(a, 0, 0, 8, 43, T.slot)
    sunken(a, 0, 0, 8, 43) if T.style != "win" else frame(a, 0, 0, 8, 43, T.shadow, T.hi)
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, lerp(T.acc, T.slot, 0.35) if T.style != "win" else T.acc)
        gy = y + (h - 5) // 2
        ink = (WHITE if T.style in ("win", "light") else T.acc_hi) if on else (
            T.tab_text_off if T.style != "win" else BLACK)
        draw_text(a, TINY, letter, 2 if letter != "M" else 1, gy, ink)
    return a


def make_titlebar():
    a = new(344, 87)
    for kind, x in (("options", 0), ("minimize", 9), ("close", 18)):
        b = main_titlebar(True)
        sx = {"options": 6, "minimize": 244, "close": 264}[kind]
        a[0:9, x:x + 9] = b[3:12, sx:sx + 9]
        bg = b[3, 6].copy()
        t2 = new(9, 9, tuple(bg))
        mini_button(t2, 0, 0, kind, True, pressed=True, bg=bg)
        a[9:18, x:x + 9] = t2
    full = main_titlebar(True)
    a[18:27, 0:9] = full[3:12, 254:263]
    t2 = new(9, 9, tuple(full[3, 254]))
    mini_button(t2, 0, 0, "shade", True, pressed=True, bg=full[3, 254].copy())
    a[18:27, 9:18] = t2
    a[0:14, 27:302] = full
    a[15:29, 27:302] = main_titlebar(False)
    a[29:43, 27:302] = full
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
    "a": [(0, c) for c in range(2, 7)], "g": [(6, c) for c in range(2, 7)], "d": [(12, c) for c in range(2, 7)],
    "f": [(r, c) for r in range(1, 6) for c in (1, 2)], "b": [(r, c) for r in range(1, 6) for c in (6, 7)],
    "e": [(r, c) for r in range(7, 12) for c in (1, 2)], "c": [(r, c) for r in range(7, 12) for c in (6, 7)],
}
DIGIT_SEGS = {0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc",
              5: "afgcd", 6: "afgedc", 7: "abc", 8: "abcdefg", 9: "abcdfg"}


def seven_seg(a, x, y, lit_segs):
    rect(a, x, y, 9, 13, T.disp)
    for s, cells in SEG.items():
        for r, c in cells:
            px(a, x + c, y + r, T.seg if s in lit_segs else T.ghost)


def status_bar(a, x0, y, w):
    """The client's status bar along the bottom of the main window (rows y..y+7)."""
    h = 8
    rect(a, x0, y, w, h, T.status_bg)
    if T.style == "win":
        frame(a, x0, y, w, h, T.shadow, T.hi)
    else:
        rect(a, x0, y, w, 1, lerp(T.status_bg, T.lo, 0.6))
    x = x0 + 3
    ty = y + 2
    for kind, val in T.status:
        if kind == "text":
            x = draw_text(a, TINY, val, x, ty, T.status_text) + 3
        elif kind == "gap":
            if T.style == "win":
                rect(a, x + val // 2 - 2, y + 1, 1, h - 2, T.shadow)
                rect(a, x + val // 2 - 1, y + 1, 1, h - 2, T.hi)
            else:
                rect(a, x + val // 2 - 2, y + 2, 1, h - 4, lerp(T.status_bg, T.status_text, 0.4))
            x += val
        elif kind == "led":
            led(a, x, y + 1, val, 5, bg=T.status_bg) if False else led(a, x, ty, val, 5, bg=T.status_bg)
            x += 8
        elif kind == "bars":                      # LimeWire's connection-strength bars
            for i in range(val):
                bh = 2 + i
                rect(a, x + 3 * i, ty + 5 - bh, 2, bh, T.acc if i < 4 else T.trough_edge)
            x += 3 * val + 3
        elif kind == "meter":                     # Kazaa's participation level
            hbar(a, x, ty - 1, 34, 7, val)
            x += 38
        elif kind == "ratio":                     # Azureus' share-ratio smiley, green
            for r, row in enumerate([".###.", "#.#.#", "#####", "#...#", ".###."]):
                for k, ch in enumerate(row):
                    if ch == "#":
                        px(a, x + k, ty + r, (0, 150, 0))
            x += 9
    assert x <= x0 + w, (T.name, x, x0 + w)


def make_main():
    a = new(275, 116)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")

    # left display: state light, time, analyzer
    field(a, 21, 20, 84, 42, T.disp)
    for x in (48, 60, 78, 90):
        seven_seg(a, x, 26, "")
    for yy in (29, 34):
        rect(a, 73, yy, 2, 2, T.seg)

    # right displays
    field(a, 109, 21, 159, 15, T.disp)
    field(a, 109, 40, 159, 14, T.disp)
    draw_text(a, TINY, "KB/S", 129, 44, T.disp_mid)
    draw_text(a, TINY, "KHZ", 169, 44, T.disp_mid)

    # slider seats and seek trough edges (the sliders' own frames cover them)
    # transport tray
    if T.style == "win":
        frame(a, 14, 86, 147, 22, T.shadow, T.hi)
    else:
        rect(a, 15, 87, 145, 20, T.slot)
        sunken(a, 15, 87, 145, 20)

    # the status bar
    status_bar(a, 3, 107, 269)

    # the emblem spot: the client's mark
    if T.logo != "kazaa":
        mark = logo(T.logo, 26, 19)
        paste_rgba(a, mark, 257 - mark.width // 2, 97 - mark.height // 2)
    else:
        # Kazaa's mark is in the titlebar: the Theater's film-frame icon here
        x, y = 247, 90
        rect(a, x, y, 20, 14, (24, 30, 46))
        for k in range(5):
            rect(a, x + 1 + 4 * k, y + 1, 2, 2, (220, 230, 250))
            rect(a, x + 1 + 4 * k, y + 11, 2, 2, (220, 230, 250))
        vgrad(a, x + 2, y + 4, 16, 6, (120, 170, 255), (30, 70, 170))
        rect(a, x + 8, y + 5, 1, 4, WHITE)
        rect(a, x + 9, y + 6, 1, 2, WHITE)
    return a


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


def transport_icon(a, kind, x, y, w, h, pressed):
    ink = T.btn_ink_dn if pressed else T.btn_ink
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
    a = new(136, 36, T.slot)
    for kind, x, w in (("previous", 0, 23), ("play", 23, 23), ("pause", 46, 23), ("stop", 69, 23),
                       ("next", 92, 22)):
        for pressed, y in ((False, 0), (True, 18)):
            button_face(a, x, y, w, 18, pressed, bg=T.slot)
            transport_icon(a, kind, x, y, w, 18, pressed)
    for pressed, y in ((False, 0), (True, 16)):
        button_face(a, 114, y, 22, 16, pressed)
        transport_icon(a, "eject", 114, y, 22, 16, pressed)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85): buttons with a status light
# ------------------------------------------------------------------------------------------

LED_GREEN = (40, 220, 60)


def toggle(a, x, y, w, h, label, on, pressed):
    button_face(a, x, y, w, h, pressed)
    o = 1 if pressed else 0
    tw = text_w(TINY, label)
    lw = 5
    tx = x + (w - tw - lw - 2) // 2 + lw + 2 + o
    ty = y + (h - 5) // 2 + o
    led(a, tx - lw - 2, ty, LED_GREEN, 5, bg=a[ty + 2, tx - lw - 3].copy(), on=on)
    ink = (T.btn_ink_dn if pressed else T.btn_ink)
    draw_text(a, TINY, label, tx, ty, ink)


def make_shufrep():
    a = new(92, 85)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        toggle(a, 0, y, 28, 15, "REP", on, pressed)
        toggle(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        toggle(a, x, 61, 23, 12, label, False, pressed)
        toggle(a, x, 73, 23, 12, label, True, pressed)
    return a


# ------------------------------------------------------------------------------------------
# monoster, playpaus (traffic lights), numbers, text
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T.disp)
    for y, on in ((0, True), (12, False)):
        col = T.disp_ink if on else T.ghost
        text_center(a, TINY, "STEREO", 14, y + 3, col)
        text_center(a, TINY, "MONO", 42, y + 3, col)
    return a


def make_playpaus():
    a = new(48, 9, T.disp)
    led(a, 1, 1, (40, 220, 60), 7, bg=T.disp)          # playing: green
    led(a, 10, 1, (255, 190, 30), 7, bg=T.disp)        # paused: amber
    led(a, 19, 1, (230, 40, 30), 7, bg=T.disp)         # stopped: red
    rect(a, 36, 0, 3, 9, T.disp)
    rect(a, 40, 3, 1, 3, (40, 220, 60))
    return a


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T.disp)
    for n in range(10):
        seven_seg(a, 9 * n, 0, DIGIT_SEGS[n])
    seven_seg(a, 90, 0, "")
    if ex:
        rect(a, 99, 0, 9, 13, T.disp)
        for r, c in SEG["g"]:
            px(a, 99 + c, r, T.seg)
    return a


FONT_GRID = [
    list("abcdefghijklmnopqrstuvwxyz\"@") + [None, None, " "],
    list("0123456789") + ["…", ".", ":", "(", ")", "-", "'", "!", "_", "+", "\\", "/", "[", "]", "^", "&", "%",
                          ",", "=", "$", "#"],
    ["å", "ö", "ä", "?", "*"] + [None] * 26,
]


def make_text():
    a = new(155, 18, T.disp)
    for row, chars in enumerate(FONT_GRID):
        for col, ch in enumerate(chars):
            if ch is None or ch == " ":
                continue
            key = ch if ch in FONT5_TXT else ch.upper()
            draw_text(a, FONT5_TXT, key, col * 5, row * 6, T.disp_ink)
    return a


# ------------------------------------------------------------------------------------------
# posbar (307 x 10), volume / balance (68 x 433)
# ------------------------------------------------------------------------------------------


def thumb(a, x, y, w, h, pressed):
    """The sliders' thumbs: a small button in the theme's style with a grip."""
    button_face(a, x, y, w, h, pressed, bg=a[y, x].copy())
    cx = x + w // 2 + (1 if pressed else 0)
    gc = T.btn_ink_dn if pressed else (T.acc if T.style != "win" else T.shadow)
    for gx in (cx - 2, cx, cx + 2):
        rect(a, gx, y + 3, 1, h - 6, gc)


def make_posbar(main):
    a = new(307, 10)
    a[:, 0:248] = main[72:82, 16:264]
    if T.bar == "pieces":
        # Azureus' availability bar: how many peers have each piece, deeper blue = more
        rect(a, 0, 1, 248, 8, T.trough)
        frame(a, 0, 1, 248, 8, T.shadow, T.hi)
        rng = np.random.default_rng(7)
        avail = np.convolve(rng.integers(0, 6, 246), np.ones(5) / 5, "same")
        for i in range(246):
            v = avail[i]
            c = (220, 30, 30) if v < 0.6 else lerp((190, 210, 250), T.acc_lo, min(1, v / 4))
            rect(a, 1 + i, 2, 1, 6, c)
    else:
        hbar(a, 0, 2, 248, 7, 0.0)
        # the unfilled trough of a transfer: faint ticks every 10 %
        for k in range(1, 10):
            rect(a, round(248 * k / 10), 3, 1, 5, lerp(T.trough, T.trough_edge, 0.45))
    for x, pressed in ((248, False), (278, True)):
        rect(a, x, 0, 29, 10, T.body)
        thumb(a, x, 0, 29, 10, pressed)
    return a


def make_volume(main):
    a = new(68, 433)
    for i in range(28):
        y = i * 15
        rect(a, 0, y, 68, 15, T.body)
        hbar(a, 0, y + 3, 68, 8, (i + 1) / 28, seed=i)
    for x, pressed in ((0, True), (15, False)):
        thumb(a, x, 422, 14, 11, pressed)
    return a


def make_balance(main):
    a = new(68, 433)
    for i in range(28):
        y = i * 15
        rect(a, 0, y, 68, 15, T.body)
        hbar(a, 9, y + 3, 38, 8, 0.0)
        reach = round(17 * i / 27)
        x0, y0 = 10, y + 4
        if T.bar == "pieces":
            for cx in range(28 - reach, 28 + reach + 1, 2):
                rect(a, cx, y0, 2, 6, T.acc)
                rect(a, cx, y0, 2, 1, T.acc_hi)
        else:
            sub = new(2 * reach + 1, 6, T.trough)
            if reach:
                tmp = new(2 * reach + 3, 8, T.trough)
                hbar(tmp, 0, 0, 2 * reach + 3, 8, 1.0, edge=True)
                a[y0:y0 + 6, 28 - reach:28 + reach + 1] = tmp[1:7, 1:-1]
        rect(a, 28, y + 2, 1, 2, T.trough_edge)
        rect(a, 28, y + 10, 1, 2, T.trough_edge)
    for x, pressed in ((0, True), (15, False)):
        thumb(a, x, 422, 14, 11, pressed)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


def eq_slider_frame(a, x, y, n):
    """14x63: a vertical progress bar, filled from the bottom to the value (n of 0..27)."""
    rect(a, x, y, 14, 63, T.body)
    bx, bw = x + 3, 8
    rect(a, bx, y + 1, bw, 61, T.trough)
    if T.style == "win":
        frame(a, bx, y + 1, bw, 61, T.shadow, T.hi)
    else:
        frame(a, bx, y + 1, bw, 61, T.trough_edge, T.trough_edge)
    v = n / 27
    top = y + 2 + round((1 - v) * 58)
    ih = y + 61 - top
    if T.bar == "chunks":
        for cy in range(y + 60, top - 1, -4):
            hh = min(3, cy - top + 1)
            if hh <= 0:
                break
            for k in range(6):
                c = lerp(T.acc_hi, T.acc_lo, k / 5)
                rect(a, bx + 1 + k, cy - hh + 1, 1, hh, c)
    elif T.bar == "pieces":
        for cy in range(y + 60, top - 1, -2):
            rect(a, bx + 1, max(top, cy - 1), 6, 2 if cy - 1 >= top else 1, T.acc)
            rect(a, bx + 1, max(top, cy - 1), 6, 1, T.acc_hi)
    else:
        for k in range(6):
            t = k / 5
            if T.bar == "glossy":
                c = lerp(T.acc_hi, T.acc, t * 2) if t < 0.5 else lerp(T.acc, T.acc_lo, (t - 0.5) * 2)
            else:
                c = lerp(T.acc_hi, T.acc_lo, t) if k in (0, 5) else T.acc
            rect(a, bx + 1 + k, top, 1, ih, c)
    rect(a, x, y + 31, 2, 1, T.trough_edge)
    rect(a, x + 12, y + 31, 2, 1, T.trough_edge)


def make_eqmain():
    a = new(275, 315)
    raised(a, 0, 0, 275, 116)
    a[0:14, :] = eq_titlebar(True)
    # graph seat
    field(a, 86, 17, 113, 19, T.disp)
    # slider bay
    if T.style == "win":
        frame(a, 16, 36, 246, 68, T.shadow, T.hi)
        frame(a, 17, 37, 244, 66, T.hi, T.shadow)
    else:
        rect(a, 16, 36, 245, 68, T.slot)
        sunken(a, 16, 36, 245, 68)
    for lbl, yy in (("+12", 40), ("0", 67), ("-12", 93)):
        text_center(a, TINY, lbl, 58, yy, T.tab_text_off)
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    text_center(a, TINY, "PREAMP", 28, 106, T.tab_text_off)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, T.tab_text_off)

    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True, bg=eq_titlebar(True)[3, 264].copy())
    a[125:134, 0:9] = t
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        w = 26 if label == "ON" else 32
        rect(a, x, 119, w, 12, T.body)
        toggle(a, x, 119, w, 12, label, on, pressed)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    for y, pressed in ((164, False), (176, True)):
        rect(a, 0, y, 11, 11, T.body)
        button_face(a, 0, y, 11, 11, pressed)
        c = T.btn_ink_dn if pressed else (T.acc if T.style != "win" else T.shadow)
        for gy in (y + 3, y + 5, y + 7):
            rect(a, 3, gy, 5, 1, c)
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        button_face(a, 224, y, 44, 12, pressed)
        o = 1 if pressed else 0
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 3 + o, T.btn_ink_dn if pressed else T.btn_ink)
    # graph
    rect(a, 0, 294, 113, 19, T.disp)
    for x in range(0, 113, 12):
        for y in range(0, 19, 2):
            px(a, 2 + x, 294 + y, T.ghost)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, lerp(T.disp, T.disp_mid, 0.6))
    for r in range(19):
        px(a, 115, 294 + r, ramp(T.vis[:12], r / 18) if T.style != "light" or T.name == "kazaa"
           else ramp([T.acc_lo, T.acc, (200, 120, 20)], r / 18))
    for x in range(113):
        px(a, x, 314, T.disp_mid if x % 3 != 2 else T.disp)
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): tab-strip titled frames
# ------------------------------------------------------------------------------------------

TXT_Y = 5          # the gen title letters' glyph rows are 5..9 (cells drawn at 4..10)


def bar20(w):
    a = new(w, 20)
    strip_bg(a, 0, 0, w, 20)
    rect(a, 0, 0, w, 1, T.hi if T.style != "dark" else lerp(T.strip[0], T.hi, 0.5))
    rect(a, 0, 19, w, 1, T.tab_lo)
    return a


def bar20_tab(w, left_edge, right_edge):
    """A piece of an active tab spanning the 20px bar (rows 2..19), opening into the window."""
    a = bar20(w)
    top, bot = T.tab_on
    vgrad(a, 0, 2, w, 18, top, bot)
    rect(a, 0, 2, w, 1, T.tab_hi)
    if T.tab_mark is not None and T.style != "win":
        rect(a, 0, 3, w, 1, T.tab_mark)
    if left_edge:
        rect(a, 0, 2, 1, 18, T.tab_hi)
        if T.round:
            px(a, 0, 2, a[1, 0])
    if right_edge:
        rect(a, w - 1, 2, 1, 18, T.tab_lo)
        if T.round:
            px(a, w - 1, 2, a[1, w - 1])
    return a


def finish_bar(t, lit):
    return t if lit else unfocus(t)


def side_tile(w, h, left):
    t = new(w, h)
    if left:
        rect(t, 0, 0, 1, h, T.hi)
        if T.style == "win":
            rect(t, 1, 0, 1, h, T.hi if False else T.body)
        rect(t, w - 1, 0, 1, h, T.lo if T.style != "win" else T.shadow)
    return t


def make_pledit():
    a = new(280, 186)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25)
        a[y:y + 20, 127:152] = finish_bar(t, lit)
        t = bar20(25)
        rect(t, 0, 0, 1, 20, T.hi)
        a[y:y + 20, 0:25] = finish_bar(t, lit)
        # title: the active tab, with a progress-bar's ghost under the word
        t = bar20(100)
        title = T.pl_title
        tw = text_w(FONT5, title)
        tx = 50 - (tw + 16) // 2
        tb = bar20_tab(tw + 16, True, True)
        t[:, tx:tx + tw + 16] = tb
        draw_text(t, FONT5, title, tx + 8, TXT_Y + 1, T.tab_text_on)
        a[y:y + 20, 26:126] = finish_bar(t, lit)
        # top-right corner: close button
        t = bar20(25)
        rect(t, 24, 0, 1, 20, T.lo)
        mini_button(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = finish_bar(t, lit)

    # left side tile
    t = new(12, 29)
    rect(t, 0, 0, 1, 29, T.hi)
    rect(t, 11, 0, 1, 29, T.lo if T.style != "win" else T.shadow)
    if T.style == "win":
        rect(t, 10, 0, 1, 29, T.lo)
    a[42:71, 0:12] = t
    # right side tile: list edge, scrollbar groove at 5..12, outer edge
    t = new(20, 29)
    rect(t, 19, 0, 1, 29, T.lo)
    rect(t, 0, 0, 1, 29, T.hi)
    rect(t, 4, 0, 10, 29, T.trough if T.style == "win" else T.slot)
    rect(t, 4, 0, 1, 29, T.lo if T.style != "light" else T.trough_edge)
    rect(t, 13, 0, 1, 29, T.hi if T.style != "light" else T.trough_edge)
    a[42:71, 31:51] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True, bg=bar20(25)[3, 14].copy())
    a[42:51, 52:61] = t
    for x, sel in ((52, False), (61, True)):
        rect(a, x, 53, 8, 18, T.slot)
        button_face(a, x, 53, 8, 18, sel, bg=T.slot)
        c = T.btn_ink_dn if sel else (T.acc if T.style != "win" else T.shadow)
        for gy in (60, 62, 64):
            rect(a, x + 2, gy, 4, 1, c)

    def bottom_base(w):
        t = new(w, 38)
        rect(t, 0, 37, w, 1, T.lo)
        rect(t, 0, 0, w, 1, T.lo if T.style == "light" else T.hi)
        if T.style == "win":
            rect(t, 0, 36, w, 1, T.shadow)
        return t

    t = bottom_base(125)
    rect(t, 0, 0, 1, 38, T.hi)
    rect(t, 0, 0, 12, 1, T.body)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        button_face(t, bx, 8, 22, 18, False)
        text_center(t, TINY, lbl, bx + 11, 15, T.btn_ink)
    a[72:110, 0:125] = t

    t = bottom_base(150)
    rect(t, 149, 0, 1, 38, T.lo)
    rect(t, 130, 0, 20, 1, T.body)
    field(t, 6, 9, 56, 8, T.disp)
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        bx = 3 + 10 * k
        button_face(t, bx, 22, 10, 10, False)
        mini_transport_icon(t, kind, bx, 22)
    field(t, 65, 22, 33, 8, T.disp)
    rect(t, 84, 24, 1, 1, T.disp_mid)
    rect(t, 84, 27, 1, 1, T.disp_mid)
    # a running transfer: a little progress bar next to the time
    hbar(t, 66, 9, 34, 8, 0.62, seed=3)
    button_face(t, 106, 8, 22, 18, False)
    text_center(t, TINY, "LIST", 117, 15, T.btn_ink)
    grip(t, 147, 35)
    a[72:110, 126:276] = t

    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


def grip(t, rx, by):
    """The resize grip: dotted diagonal, bottom-right corner at (rx, by)."""
    hi = T.hi
    lo = T.lo if T.style != "light" else T.trough_edge
    for k in range(4):
        for j in range(k + 1):
            gx, gy = rx - 2 - 3 * k + 3 * j, by - 2 - 3 * j
            px(t, gx, gy, hi)
            px(t, gx + 1, gy + 1, lo)


def mini_transport_icon(a, kind, x, y):
    ink = T.btn_ink
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
    for lit, y in ((True, 0), (False, 21)):
        def piece(px0, t):
            a[y:y + 20, px0:px0 + 25] = finish_bar(t, lit)

        t = bar20(25)
        rect(t, 0, 0, 1, 20, T.hi)
        piece(0, t)
        # left end: strip, then the tab's left edge at column 17
        t = bar20(25)
        t[:, 17:25] = bar20_tab(8, True, False)
        piece(26, t)
        piece(52, bar20_tab(25, False, False))
        t = bar20(25)
        t[:, 0:8] = bar20_tab(8, False, True)
        piece(78, t)
        piece(104, bar20(25))
        t = bar20(25)
        mini_button(t, 14, 3, "close", lit)
        rect(t, 24, 0, 1, 20, T.lo)
        piece(130, t)

    def bottom(w, has_grip, left_edge):
        t = new(w, 14)
        rect(t, 0, 13, w, 1, T.lo)
        if left_edge:
            rect(t, 0, 0, 1, 14, T.hi)
        else:
            rect(t, w - 1, 0, 1, 14, T.lo)
        if has_grip:
            grip(t, w - 1, 12)
        return t

    a[42:56, 0:125] = bottom(125, False, True)
    a[57:71, 0:125] = bottom(125, True, False)
    a[72:86, 127:152] = bottom(25, False, False)
    a[72:86, 151] = a[72:86, 150]
    for x, w, h, outer_left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        if outer_left:
            rect(t, 0, 0, 1, h, T.hi)
            rect(t, w - 1, 0, 1, h, T.lo if T.style != "light" else T.trough_edge)
        else:
            rect(t, w - 1, 0, 1, h, T.lo)
            rect(t, 0, 0, 1, h, T.hi if T.style != "light" else T.trough_edge)
        a[42:42 + h, x:x + w] = t
    t = new(9, 9)
    mini_button(t, 0, 0, "close", True, pressed=True, bg=bar20(25)[3, 14].copy())
    a[42:51, 148:157] = t

    # letters: cells carry the active tab's rows 4..10, so they sit on the tab seamlessly
    cell = bar20_tab(1, False, False)[4:11, 0]
    for lit, y in ((True, 88), (False, 96)):
        row = np.zeros((7, 194, 3), dtype=np.int32)
        row[:, :] = SEP
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(FONT5, c) + 1
            row[:, x:x + w] = cell[:, None, :]
            draw_text(row, FONT5, c, x, 1, T.tab_text_on)
            x += w + 1
        assert x <= 194, x
        if not lit:
            sepmask = (row == np.array(SEP)).all(-1)
            row = unfocus(row)
            row[sepmask] = SEP
        a[y:y + 7] = row
    return a


# ------------------------------------------------------------------------------------------
# genex.bmp
# ------------------------------------------------------------------------------------------


def genex_colours():
    p = {k: hexcol(v) for k, v in T.pl.items() if v.startswith("#")}
    return [
        p["normal_bg"], p["normal"],                       # item background, text
        T.body, T.tab_text_on,                             # window background, button text
        T.tab_text_on if T.style != "dark" else (220, 232, 240),   # window text
        T.trough_edge, hexcol(T.pl["selected_bg"]),        # dividers, selection bar
        T.tab_off[0], T.tab_text_on,                       # header background, text
        T.hi, T.lo, T.shadow, T.body,                      # header frame light/dark/pressed, dead area
        T.acc, T.slot, T.acc_hi, T.slot, T.slot,           # scrollbar thumb, track, pressed, dead
    ]


def make_genex():
    a = new(256, 64)
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    button_face(a, 0, 1, 47, 15, False)
    button_face(a, 0, 16, 47, 15, True)
    return a


# ------------------------------------------------------------------------------------------
# Text files
# ------------------------------------------------------------------------------------------


def viscolor():
    return ([(T.disp, "background"), (T.vis_dots, "dots")]
            + [(c, f"spectrum {i + 1}" + (" (top)" if i == 0 else "")) for i, c in enumerate(T.vis)]
            + [(c, f"oscilloscope {i + 1}") for i, c in enumerate(T.osc)] + [(T.peak, "peaks")])


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    p = T.pl
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={p['normal']}\nCurrent={p['current']}\nNormalBG={p['normal_bg']}\n"
                f"SelectedBG={p['selected_bg']}\nMbBG={p['mb_bg']}\nMbFG={p['mb_fg']}\nFont=Arial\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n") as f:
        f.write(
            f"{T.wsz} — a skin in the style of {T.subject}.\n"
            f"{T.owner} logo © {T.owner}.\n\n"
            "A classic (Winamp 2.x format) skin generated by a script (gen_skin.py): the client's tab\n"
            "row, progress bars for the sliders, the playlist as a transfer list, status lights and a\n"
            "status bar.\n"
        )


# ------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------

SHEETS = {}


def build():
    main = make_main()
    sheets = {
        "main.bmp": main, "titlebar.bmp": make_titlebar(), "cbuttons.bmp": make_cbuttons(),
        "shufrep.bmp": make_shufrep(), "posbar.bmp": make_posbar(main), "volume.bmp": make_volume(main),
        "balance.bmp": make_balance(main), "monoster.bmp": make_monoster(), "playpaus.bmp": make_playpaus(),
        "numbers.bmp": make_numbers(False), "nums_ex.bmp": make_numbers(True), "text.bmp": make_text(),
        "pledit.bmp": make_pledit(), "eqmain.bmp": make_eqmain(), "gen.bmp": make_gen(), "genex.bmp": make_genex(),
    }
    SHEETS.clear()
    for name, arr in sheets.items():
        SHEETS[name[:-4]] = save(arr, name)
    write_text_files()
    names = list(sheets) + ["pledit.txt", "viscolor.txt", "readme.txt"]
    with zipfile.ZipFile(os.path.join(HERE, f"{T.wsz}.wsz"), "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=(2026, 10, 26, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(OUT, n), "rb") as fh:
                z.writestr(info, fh.read())
    # genex.bmp completed for real Winamp and WACUP: all 24 colours, readable text, and the
    # standard 112x59 button and scrollbar layout (skins/genex_wacup.py).
    genex_wacup.process(os.path.join(HERE, f"{T.wsz}.wsz"))
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
    for ch in s:
        row, col = FONT_LOOKUP.get(ch.lower(), FONT_LOOKUP[" "])
        blit(dst, SHEETS["text"], (col * 5, row * 6, 5, 6), x, y)
        x += 5


def ui_font(size=11):
    return ImageFont.truetype(F_SANS, size)


def text_ink():
    """The app's title colour: the commonest non-background colour of text.bmp's letters."""
    arr = np.array(SHEETS["text"]).reshape(-1, 3)
    bg = tuple(arr[150 // 5 * 0 + 150 + 0]) if False else tuple(np.array(SHEETS["text"])[0, 152])
    cols, counts = np.unique(arr, axis=0, return_counts=True)
    best = None
    for c, n in sorted(zip(map(tuple, cols), counts), key=lambda t: -t[1]):
        if c != bg:
            best = c
            break
    return best


def preview_main(lit, state):
    S = SHEETS
    img = Image.new("RGB", (275, 116))
    img.paste(S["main"], (0, 0))
    blit(img, S["titlebar"], (27, 0 if lit else 15, 275, 14), 0, 0)
    for k, x, w in (("previous", 0, 23), ("play", 23, 23), ("pause", 46, 23), ("stop", 69, 23), ("next", 92, 22)):
        pos = {"previous": 16, "play": 39, "pause": 62, "stop": 85, "next": 108}[k]
        blit(img, S["cbuttons"], (x, 18 if state["pressed"] == k else 0, w, 18), pos, 88)
    blit(img, S["cbuttons"], (114, 16 if state["pressed"] == "eject" else 0, 22, 16), 136, 89)
    for name, x0, on in (("eq", 0, state["eq"]), ("pl", 23, state["pl"])):
        sx = x0 + (46 if state["pressed"] == name else 0)
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
    blit(img, S["playpaus"], ({"play": 0, "pause": 9, "stop": 18}[state["mode"]], 0, 9, 9), 26, 28)
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
    if state["remaining"]:
        blit(img, S["nums_ex"], (99, 0, 9, 13), 38, 26)
    for d, x in ((m // 10, 48), (m % 10, 60), (s // 10, 78), (s % 10, 90)):
        blit(img, S["nums_ex"], (9 * d, 0, 9, 13), x, 26)
    for x in range(0, 154, 5):
        blit(img, S["text"], (150, 0, min(5, 154 - x), 6), 111 + x, 24)
    title = img.crop((111, 22, 265, 36))
    ImageDraw.Draw(title).text((0, 7), state["title"], fill=text_ink(), font=ui_font(), anchor="lm")
    img.paste(title, (111, 22))
    draw_bitmap_text(img, "192", 111, 43)
    draw_bitmap_text(img, "44", 156, 43)
    cols = [c for c, _ in viscolor()]
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
            vp[x, y] = cols[2 + y]
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
    p = T.pl
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=hexcol(p["normal_bg"]))
    font = ui_font()
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=hexcol(p["selected_bg"]))
        col = hexcol(p["current"] if i == 1 else p["normal"])
        d.text((lx + 2, y + 7), f"{i + 1}. {txt}", fill=col, font=font, anchor="lm")
        d.text((lx + lw - 3, y + 7), dur, fill=col, font=font, anchor="rm")
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
    pic = Image.linear_gradient("L").resize((w - 22, h - 34))
    arr = np.array(pic).astype(np.float32)[..., None] / 255
    c0, c1 = np.array(T.pic[0]), np.array(T.pic[1])
    img.paste(Image.fromarray((c0 + (c1 - c0) * arr).astype(np.uint8)), (11, 20))
    return img


TRACKS = {
    "napster": [("Metallica - I Disappear.mp3", "4:26"), ("Dr. Dre - Forgot About Dre.mp3", "3:42"),
                ("Eminem - The Real Slim Shady.mp3", "4:44"), ("Blink-182 - All The Small Things.mp3", "2:48"),
                ("Moby - Porcelain.mp3", "4:01"), ("Radiohead - Idioteque.mp3", "5:09"),
                ("Madonna - Music.mp3", "3:45"), ("Santana - Smooth.mp3", "4:56"),
                ("Fatboy Slim - Praise You.mp3", "3:43"), ("Eiffel 65 - Blue.mp3", "3:41"),
                ("Sisqo - Thong Song.mp3", "4:13")],
    "limewire": [("Linkin Park - Numb.mp3", "3:07"), ("Outkast - Hey Ya!.mp3", "3:55"),
                 ("Green Day - Holiday.mp3", "3:52"), ("Gorillaz - Feel Good Inc.mp3", "3:42"),
                 ("The Killers - Mr. Brightside.mp3", "3:42"), ("Coldplay - Clocks.mp3", "5:07"),
                 ("Usher - Yeah!.mp3", "4:10"), ("Franz Ferdinand - Take Me Out.mp3", "3:57"),
                 ("Daft Punk - One More Time.mp3", "5:20"), ("Coldplay - Fix You.mp3", "4:55"),
                 ("Crazy Frog - Axel F.mp3", "2:48")],
    "kazaa": [("Nelly - Hot In Herre.mp3", "3:48"), ("Avril Lavigne - Complicated.mp3", "4:04"),
              ("Shakira - Whenever, Wherever.mp3", "3:16"), ("Eminem - Without Me.mp3", "4:50"),
              ("Norah Jones - Don't Know Why.mp3", "3:06"), ("Coldplay - In My Place.mp3", "3:48"),
              ("Las Ketchup - The Ketchup Song.mp3", "3:33"), ("t.A.T.u. - All The Things She Said.mp3", "3:34"),
              ("Justin Timberlake - Cry Me a River.mp3", "4:48"), ("Evanescence - Bring Me To Life.mp3", "3:56"),
              ("Sean Paul - Get Busy.mp3", "3:31")],
    "azureus": [("Arcade Fire - Funeral (2004) [FLAC]", "48:00"), ("LCD Soundsystem - Losing My Edge", "7:52"),
                ("Boards of Canada - Dayvan Cowboy", "5:00"), ("Bloc Party - Banquet", "3:22"),
                ("Justice - D.A.N.C.E.", "4:02"), ("MGMT - Time to Pretend", "4:21"),
                ("Daft Punk - Alive 2007", "73:01"), ("Elephants Dream (Blender)", "10:54"),
                ("M83 - Kim & Jessie", "5:24"), ("Vampire Weekend - A-Punk", "2:17"),
                ("Big Buck Bunny (Blender)", "9:56")],
}
TITLES = {"napster": "Metallica - I Disappear.mp3", "limewire": "Linkin Park - Numb.mp3",
          "kazaa": "Nelly - Hot In Herre.mp3", "azureus": "Arcade Fire - Funeral (2004)"}


def preview():
    rows = TRACKS[T.name]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, mode="play", stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title=TITLES[T.name], bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, mode="pause", stereo=False,
             pos=0.8, seek=True, volume=25, vdrag=True, balance=-60, time=95, remaining=True,
             title="Paused: Quiet Hours (Live)", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    EA = dict(pressed=None, on=True, auto=False, preamp=50, drag=None, bands=[75, 68, 56, 49, 49, 33, 30, 30, 49, 49])
    EB = dict(pressed="close", on=False, auto=True, preamp=70, drag=3, bands=[51, 51, 59, 65, 65, 100, 59, 51, 0, 51])
    cols = []
    for lit, st, est in ((True, A, EA), (False, B, EB)):
        col = Image.new("RGB", (275, 116 + 116 + 232 + 140))
        col.paste(preview_main(lit, st), (0, 0))
        col.paste(preview_eq(lit, est), (0, 116))
        col.paste(preview_playlist(lit, 275, 232, rows, pressed_close=not lit, drag=not lit), (0, 232))
        col.paste(preview_gen(lit, 275, 140, "album art", pressed_close=not lit), (0, 464))
        cols.append(col)
    gap = 12
    out = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), (58, 62, 70))
    out.paste(cols[0], (gap, gap))
    out.paste(cols[1], (275 + 2 * gap, gap))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, f"preview-{T.name}.png"))


def check():
    """In-bounds and format checks on what the app reads."""
    sizes = {"main": (275, 116), "titlebar": (344, 87), "cbuttons": (136, 36), "shufrep": (92, 85),
             "posbar": (307, 10), "volume": (68, 433), "balance": (68, 433), "monoster": (56, 24),
             "playpaus": (48, 9), "numbers": (99, 13), "nums_ex": (108, 13), "text": (155, 18),
             "pledit": (280, 186), "eqmain": (275, 315), "gen": (194, 109)}
    for k, sz in sizes.items():
        assert SHEETS[k].size == sz and SHEETS[k].mode == "RGB", (k, SHEETS[k].size)
    gen_letters()
    ink = text_ink()
    bg = T.disp
    assert sum(abs(int(ink[i]) - bg[i]) for i in range(3)) > 300, (ink, bg)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        for k, v in THEMES.items():
            print(f"{k:10s} {v['wsz']}.wsz  ({v['subject']})")
        sys.exit(0)
    for name in args or list(THEMES):
        set_theme(name)
        build()
        check()
        preview()
        print(f"{name}: {T.wsz}.wsz, preview-{name}.png")
