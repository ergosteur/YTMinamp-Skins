#!/usr/bin/python3
"""Pokémon: classic Winamp 2.x skins in the style of the Pokémon handheld games' pixel UI.

One procedural generator, one theme per skin:

  gen1  Pokémon Red/Blue (Game Boy), the classic DMG four-shade green palette: the double-line
        text box, the ▶ menu cursor, START-menu-style toggles, the battle HP bar (one shade on
        DMG) for the volume, Gen 1 front sprite of Pikachu.
  gen2  Pokémon Gold/Silver/Crystal (Game Boy Color): the PokéGear radio card (black top bar,
        pale screen, grey icon tiles, the tuning dial as the seek bar), the green/yellow/red HP
        bars and the blue EXP bar, Crystal sprites of Pichu and Togepi.
  gen3  Pokémon Ruby/Sapphire/Emerald (Game Boy Advance): the PokéNav's mint header and dotted
        screen, the rounded teal message box, the cream battle healthbox with its HP and EXP
        bars, the Hoenn starters (Emerald sprites).
  pokemon-yellow  Pokémon Yellow as it looks on a Game Boy Color: Yellow's own CGB palettes
        (pokeyellow CGBBasePalettes), the Gen 1 text box on yellow, the title logo's blue, the GBC
        HP bars, the games' own font in the title bands, Yellow's Pikachu (front, and following
        the player in the About spot).
  pokemon-yellow-overworld  The same, calmer: a Route 1 tile map (overworld tileset, PAL_ROUTE)
        behind the main window and the EQ, controls on the white path, grass-green bands and
        frame stripe, a white list; all its colours through Gambatte's GBC LCD correction.

Everything is drawn here in integer pixels (rectangles and hand-made pixel fonts, no smoothing),
except the in-game sprites, which are pasted unscaled from source/sprites-gen*/ (downloaded from
the pret disassemblies, see README.md), and Yellow's title font, read from
source/yellow/gfx_font_font.png.

    /usr/bin/python3 -I gen_skin.py              # every theme
    /usr/bin/python3 -I gen_skin.py gen2         # just this one
    /usr/bin/python3 -I gen_skin.py --list

Writes out/<theme>/*.bmp + text files, <Name>.wsz and preview-<theme>.png beside this file.
Built on skins/ember/gen_skin.py's sheet layouts and preview. Private use only.
"""

import os
import sys
import warnings
import zipfile

warnings.filterwarnings("ignore", category=UserWarning)

import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/matt/gitea/ergosteur/ytminamp/skins")  # skins/genex_wacup.py, which finishes each .wsz
import genex_wacup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.join(HERE, "out")
SRC = os.path.join(HERE, "source")
OUT = OUT_ROOT
SEP = (255, 0, 255)  # gen.bmp letter separators (never shown)
LIBERATION = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf"


def gbc(r, g, b):
    """A Game Boy Color 5-bit RGB triple as 8-bit."""
    return tuple(int(round(v * 255 / 31)) for v in (r, g, b))


# ------------------------------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------------------------------

DMG = [(155, 188, 15), (139, 172, 15), (48, 98, 48), (15, 56, 15)]  # lightest .. darkest

G2_PALE = gbc(28, 31, 20)     # PokéGear screen (pokegear.pal "border" colour 0)
G2_GREY = gbc(21, 21, 21)
G2_DGREY = gbc(13, 13, 13)
G2_BLACK = (0, 0, 0)
G2_WHITE = (255, 255, 255)

# Pokémon Yellow on a Game Boy Color: pokeyellow data/sgb/sgb_palettes.asm, CGBBasePalettes
Y_WHITE = gbc(31, 31, 31)
Y_YEL = gbc(31, 31, 0)        # colour 1 of PAL_YELLOWMON / PAL_MEWMON / PAL_SAFFRON / the HP bars
Y_BLACK = gbc(3, 3, 3)        # colour 3 of every palette (text, frames)
Y_BLUE = gbc(7, 7, 25)        # PAL_LOGO2 (the title screen's POKéMON logo): outline
Y_DBLUE = gbc(0, 0, 17)       # PAL_LOGO2: the logo's dark shadow
Y_LBLUE = gbc(11, 23, 31)     # colour 2 of the town palettes
Y_BROWN = gbc(19, 7, 1)       # PAL_PIKACHU_PORTRAIT, colour 2
Y_PAL_YELLOWMON = [Y_WHITE, Y_YEL, gbc(28, 14, 0), Y_BLACK]
Y_PAL_SAFFRON = [Y_WHITE, Y_YEL, Y_LBLUE, Y_BLACK]
OBP0 = [0, 0, 1, 3]           # rOBP0 = %11010000 (home/palettes.asm GBPalNormal): sprite shade -> colour

THEMES = {
    "gen1": dict(
        style="gb", name="Pokémon Gen 1", wsz="Pokemon-Gen1",
        games="Red, Blue and Yellow (Game Boy)",
        sub="RED/BLUE", eq_title="EQUALIZER", pl_title="PLAYLIST", gen_title="POKEDEX",
        body=DMG[0], body2=DMG[0], band=DMG[3], band_un=DMG[2], txt_band=DMG[0], txt_band_un=DMG[1],
        line=DMG[3], panel=DMG[0], panel_l=DMG[0], ink=DMG[3], ink2=DMG[2], shadow=None,
        hp=[DMG[3], DMG[3], DMG[3]], hp_shade=None, track=DMG[0], bar_line=DMG[3], exp=DMG[2],
        ball=dict(top=DMG[2], bot=DMG[0], line=DMG[3], shine=DMG[0], top_p=DMG[1]),
        btn_face=DMG[0], btn_line=DMG[3], btn_glyph=DMG[3], btnp_face=DMG[2], btnp_glyph=DMG[0],
        logo_fill=DMG[0], logo_line=DMG[2], logo_fill_un=DMG[1], logo_line_un=DMG[3],
        cursor=DMG[3], off=DMG[2], sel=DMG[1], cur=DMG[3], normal=DMG[2],
        vis_bars=[DMG[3]] * 8 + [DMG[2]] * 8, vis_dots=DMG[1], vis_peak=DMG[3],
        pref="DMG", dexno="NO.025",
        sprites=dict(eq=("sprites-gen1", "gfx_pokemon_front_pikachu.png", "gb1", 0),
                     about=("sprites-gen1", "gfx_sprites_poke_ball.png", "gb1", 0),
                     pl=("sprites-gen1", "gfx_sprites_pikachu.png", "gb1", 0)),
    ),
    "gen2": dict(
        style="gb", name="Pokémon Gen 2", wsz="Pokemon-Gen2",
        games="Gold, Silver and Crystal (Game Boy Color)",
        sub="POKEGEAR RADIO", eq_title="EQUALIZER", pl_title="PLAYLIST", gen_title="POKEDEX",
        body=G2_PALE, body2=G2_PALE, band=G2_BLACK, band_un=G2_DGREY, txt_band=G2_WHITE, txt_band_un=G2_GREY,
        line=G2_BLACK, panel=G2_WHITE, panel_l=G2_WHITE, ink=G2_BLACK, ink2=G2_DGREY, shadow=None,
        hp=[gbc(0, 23, 0), gbc(31, 21, 0), gbc(31, 0, 0)], hp_shade=None, track=gbc(30, 26, 15),
        bar_line=G2_BLACK, exp=gbc(4, 17, 31),
        ball=dict(top=gbc(31, 7, 1), bot=G2_WHITE, line=G2_BLACK, shine=gbc(31, 19, 10), top_p=gbc(31, 19, 10)),
        btn_face=G2_GREY, btn_line=G2_BLACK, btn_glyph=G2_BLACK, btnp_face=G2_DGREY, btnp_glyph=G2_PALE,
        btn_hi=G2_WHITE, btn_lo=G2_DGREY,
        logo_fill=gbc(31, 26, 0), logo_line=gbc(5, 9, 22), logo_fill_un=G2_GREY, logo_line_un=G2_DGREY,
        cursor=G2_BLACK, off=G2_DGREY, sel=G2_GREY, cur=gbc(31, 7, 1), normal=G2_BLACK,
        vis_bars=[gbc(31, 0, 0)] * 3 + [gbc(31, 21, 0)] * 5 + [gbc(0, 23, 0)] * 8, vis_dots=(232, 232, 232),
        vis_peak=G2_BLACK, pref="GBC", dexno="NO.172",
        sprites=dict(eq=("sprites-gen2", "gfx_pokemon_pichu_front.png", "png", 0),
                     about=("sprites-gen2", "gfx_pokemon_togepi_front.png", "png", 0),
                     pl=("sprites-gen2", "gfx_icons_pikachu.png", "ow_red", 0)),
    ),
    "gen3": dict(
        style="gba", name="Pokémon Gen 3", wsz="Pokemon-Gen3",
        games="Ruby, Sapphire and Emerald (Game Boy Advance)",
        sub="POKENAV", eq_title="EQUALIZER", pl_title="PLAYLIST", gen_title="POKENAV",
        body=(255, 255, 255), body2=(255, 255, 255),
        band=(32, 222, 148), band_hi=(180, 255, 213), band_mid=(106, 238, 180), band_lo=(16, 140, 100),
        band_un=(168, 200, 188), band_un_hi=(226, 238, 232), band_un_mid=(196, 220, 210), band_un_lo=(120, 148, 138),
        txt_band=(255, 255, 255), txt_band_un=(250, 252, 250), band_shadow=(16, 120, 90),
        band_shadow_un=(116, 140, 132),
        frame=[(24, 110, 96), (32, 222, 148), (180, 255, 213)],
        msg=[(0, 160, 150), (0, 200, 184), (0, 248, 152), (224, 232, 224)],
        health=[(32, 57, 0), (82, 106, 98), (123, 148, 131), (57, 82, 65)],
        line=(57, 82, 65), panel=(248, 248, 248), panel_l=(255, 255, 222), ink=(72, 72, 80), ink2=(120, 120, 128),
        shadow=(208, 208, 200),
        hp=[(115, 255, 172), (255, 225, 66), (255, 112, 90)], hp_shade=[(90, 213, 131), (214, 172, 16), (214, 64, 57)],
        track=(74, 65, 90), bar_line=(57, 82, 65), exp=(65, 205, 255), exp_track=(222, 213, 180),
        ball=dict(top=(232, 56, 48), bot=(255, 255, 255), line=(48, 48, 56), shine=(255, 160, 140),
                  top_p=(255, 112, 90)),
        btn_face=(255, 255, 255), btn_line=(0, 160, 150), btn_glyph=(72, 72, 80), btnp_face=(106, 238, 180),
        btnp_glyph=(24, 90, 80),
        logo_fill=(255, 214, 0), logo_line=(40, 80, 168), logo_fill_un=(240, 244, 240), logo_line_un=(120, 148, 138),
        cursor=(72, 72, 80), off=(150, 150, 158), sel=(196, 240, 222), cur=(214, 64, 57), normal=(72, 72, 80),
        vis_bars=[(255, 112, 90)] * 3 + [(255, 214, 40)] * 5 + [(90, 213, 131)] * 8, vis_dots=(240, 236, 200),
        vis_peak=(72, 72, 80), pref="GBA", dexno="NO.255",
        sprites=dict(eq=("sprites-gen3", "graphics_pokemon_torchic_front.png", "gba", "graphics_pokemon_torchic_normal.pal"),
                     about=("sprites-gen3", "graphics_pokemon_treecko_icon.png", "gba", None),
                     pl=("sprites-gen3", "graphics_pokemon_mudkip_icon.png", "gba", None)),
    ),
    "pokemon-yellow": dict(
        style="gb", name="Pokémon Yellow", wsz="Pokemon-Yellow",
        games="Yellow Version: Special Pikachu Edition (Game Boy Color)",
        sub="YELLOW", eq_title="EQUALIZER", pl_title="PLAYLIST", gen_title="POKEDEX",
        body=Y_YEL, body2=Y_YEL, band=Y_DBLUE, band_un=Y_BLUE, txt_band=Y_YEL, txt_band_un=Y_LBLUE,
        line=Y_BLACK, panel=Y_WHITE, panel_l=Y_WHITE, ink=Y_BLACK, ink2=Y_BROWN, shadow=None,
        hp=[gbc(0, 31, 0), gbc(31, 18, 0), gbc(31, 0, 0)], hp_shade=None, track=Y_WHITE,
        bar_line=Y_BLACK, exp=Y_BLUE,
        ball=dict(top=gbc(31, 1, 1), bot=Y_WHITE, line=Y_BLACK, shine=Y_WHITE, top_p=gbc(31, 18, 0)),
        btn_face=Y_WHITE, btn_line=Y_BLACK, btn_glyph=Y_BLACK, btnp_face=Y_BLUE, btnp_glyph=Y_YEL,
        logo_fill=Y_YEL, logo_line=Y_BLUE, logo_fill_un=Y_LBLUE, logo_line_un=Y_DBLUE,
        cursor=Y_BLACK, off=Y_BROWN, sel=Y_WHITE, dim=(206, 206, 206), cur=Y_BLUE, normal=Y_BLACK,
        vis_bars=[gbc(31, 0, 0)] * 3 + [gbc(31, 18, 0)] * 5 + [gbc(0, 31, 0)] * 8, vis_dots=(222, 222, 222),
        vis_peak=Y_BLACK, pref="GBC", dexno="NO.025",
        # Yellow's own sprites; the front pic in Pikachu's battle palette (PAL_YELLOWMON), the
        # overworld ones in an OBJ palette converted through OBP0 from Saffron City's (PAL_SAFFRON,
        # whose colour 1 is yellow), as on a Game Boy Color
        sprites=dict(eq=("yellow", "gfx_pokemon_front_pikachu.png", "gbc_bg", Y_PAL_YELLOWMON),
                     about=[("yellow", "gfx_sprites_red.png", "gbc_obj", (Y_PAL_SAFFRON, 2)),
                            ("yellow", "gfx_sprites_pikachu.png", "gbc_obj", (Y_PAL_SAFFRON, 2))],
                     pl=("yellow", "gfx_sprites_pikachu.png", "gbc_obj", (Y_PAL_SAFFRON, 2, True))),
    ),
}

# The same Yellow, calmer: Route 1 in its GBC palette (PAL_ROUTE) as a tile map behind the main
# window and the EQ, the controls on the white path, grass-green title bands, a white list.
Y_GREEN = gbc(16, 31, 4)      # PAL_ROUTE colour 1 (grass)
Y_PAL_ROUTE = [Y_WHITE, Y_GREEN, Y_LBLUE, Y_BLACK]
THEMES["pokemon-yellow-overworld"] = dict(
    THEMES["pokemon-yellow"], name="Pokémon Yellow Overworld", wsz="Pokemon-Yellow-Overworld",
    games="Yellow Version: Special Pikachu Edition (Game Boy Color), Route 1",
    body=Y_WHITE, body2=Y_WHITE, band=Y_GREEN, band_un=Y_LBLUE, txt_band=Y_BLACK, txt_band_un=Y_DBLUE,
    logo_fill=Y_WHITE, logo_line=Y_BLUE, logo_fill_un=Y_WHITE, logo_line_un=Y_BLUE,
    btnp_face=Y_GREEN, btnp_glyph=Y_BLACK, sel=Y_GREEN, map=Y_PAL_ROUTE, frame_mid=Y_GREEN,
    band_edge=Y_BLACK, lcd=True, main_band=Y_YEL,
    sprites=dict(eq=("yellow", "gfx_pokemon_front_pikachu.png", "gbc_bg", Y_PAL_YELLOWMON),
                 about=[("yellow", "gfx_sprites_red.png", "gbc_obj", (Y_PAL_ROUTE, 2)),
                        ("yellow", "gfx_sprites_pikachu.png", "gbc_obj", (Y_PAL_ROUTE, 2))],
                 pl=("yellow", "gfx_sprites_pikachu.png", "gbc_obj", (Y_PAL_ROUTE, 2, True))),
)

T = {}


def setup_theme(key):
    global T, OUT
    T = dict(THEMES[key])
    if T.get("lcd"):
        T = gbc_lcd(T)
    T["key"] = key
    if key.startswith("pokemon-yellow"):
        T["tfont"] = real_font()
    OUT = os.path.join(OUT_ROOT, key)
    os.makedirs(OUT, exist_ok=True)


def gambatte(c):
    """Gambatte's Game Boy Color LCD colour correction (libgambatte video.cpp gbcToRgb32) of an
    8-bit colour made by gbc(): back to 5-bit, then
    R = (13r + 2g + b) >> 1,  G = (3g + b) << 1,  B = (3r + 2g + 11b) >> 1   (0..248)."""
    r, g, b = (int(round(v * 31 / 255)) for v in c)
    return ((13 * r + 2 * g + b) >> 1, (3 * g + b) << 1, (3 * r + 2 * g + 11 * b) >> 1)


def gbc_lcd(x):
    """Every colour in a theme (nested dicts, lists, sprite specs) through the LCD correction."""
    if isinstance(x, dict):
        return {k: gbc_lcd(v) for k, v in x.items()}
    if isinstance(x, list):
        return [gbc_lcd(v) for v in x]
    if isinstance(x, tuple):
        if len(x) == 3 and all(type(v) is int and 0 <= v <= 255 for v in x):
            return gambatte(x)
        return tuple(gbc_lcd(v) for v in x)
    return x


def GBA():
    return T["style"] == "gba"


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ------------------------------------------------------------------------------------------
# Canvas helpers (numpy, H x W x 3, int); everything is whole pixels
# ------------------------------------------------------------------------------------------


def new(w, h, col=None):
    a = np.zeros((h, w, 3), dtype=np.int32)
    a[:, :] = T["body"] if col is None else col
    return a


def rect(a, x, y, w, h, col):
    if w > 0 and h > 0 and col is not None:
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(a.shape[1], x + w), min(a.shape[0], y + h)
        if x1 > x0 and y1 > y0:
            a[y0:y1, x0:x1] = col


def px(a, x, y, col):
    if col is not None and 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def save(a, name):
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img.save(os.path.join(OUT, name))
    return img


def body_rows(a, x, y, w, h, y0=0):
    """The window material: flat, or the PokéNav's faint mint pinstripes (vertical-only)."""
    for r in range(h):
        yy = y0 + y + r
        rect(a, x, y + r, w, 1, T["body2"] if (GBA() and yy % 4 >= 2) else T["body"])


def pat(a, x, y, rows, colmap):
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch in colmap:
                px(a, x + c, y + r, colmap[ch])


# ------------------------------------------------------------------------------------------
# Pixel fonts (designed for this skin)
# ------------------------------------------------------------------------------------------

def G(*rows):
    return list(rows)


# 4x5 font for text.bmp (5x6 cells) and small readouts.
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
    "0": G(".##.", "#..#", "#..#", "#..#", ".##."), "1": G(".#.", "##.", ".#.", ".#.", "###"),
    "2": G("###.", "...#", ".##.", "#...", "####"), "3": G("###.", "...#", ".##.", "...#", "###."),
    "4": G("#..#", "#..#", "####", "...#", "...#"), "5": G("####", "#...", "###.", "...#", "###."),
    "6": G(".##.", "#...", "###.", "#..#", ".##."), "7": G("####", "...#", "..#.", ".#..", ".#.."),
    "8": G(".##.", "#..#", ".##.", "#..#", ".##."), "9": G(".##.", "#..#", ".###", "...#", ".##."),
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

# 3x5 font for small labels.
TINY = {
    "A": G(".#.", "#.#", "###", "#.#", "#.#"), "B": G("##.", "#.#", "##.", "#.#", "##."),
    "C": G(".##", "#..", "#..", "#..", ".##"), "D": G("##.", "#.#", "#.#", "#.#", "##."),
    "E": G("###", "#..", "##.", "#..", "###"), "F": G("###", "#..", "##.", "#..", "#.."),
    "G": G(".##", "#..", "#.#", "#.#", ".##"), "H": G("#.#", "#.#", "###", "#.#", "#.#"),
    "I": G("###", ".#.", ".#.", ".#.", "###"), "K": G("#.#", "#.#", "##.", "#.#", "#.#"),
    "L": G("#..", "#..", "#..", "#..", "###"), "M": G("#.#", "###", "###", "#.#", "#.#"),
    "N": G("##.", "#.#", "#.#", "#.#", "#.#"), "O": G(".#.", "#.#", "#.#", "#.#", ".#."),
    "P": G("##.", "#.#", "##.", "#..", "#.."), "Q": G(".#.", "#.#", "#.#", "##.", ".##"),
    "R": G("##.", "#.#", "##.", "#.#", "#.#"), "S": G(".##", "#..", ".#.", "..#", "##."),
    "T": G("###", ".#.", ".#.", ".#.", ".#."), "U": G("#.#", "#.#", "#.#", "#.#", "###"),
    "V": G("#.#", "#.#", "#.#", "#.#", ".#."), "W": G("#.#", "#.#", "###", "###", "#.#"),
    "X": G("#.#", "#.#", ".#.", "#.#", "#.#"), "Y": G("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": G("###", "..#", ".#.", "#..", "###"), " ": G("..", "..", "..", "..", ".."),
    ":": G(".", "#", ".", "#", "."),
}
for _c in "0123456789+-.":
    TINY[_c] = FONT5[_c] if len(FONT5[_c][0]) <= 3 else None
TINY.update({"0": G("###", "#.#", "#.#", "#.#", "###"), "2": G("##.", "..#", ".#.", "#..", "###"),
             "3": G("##.", "..#", ".#.", "..#", "##."), "4": G("#.#", "#.#", "###", "..#", "..#"),
             "5": G("###", "#..", "##.", "..#", "##."), "6": G(".##", "#..", "###", "#.#", "###"),
             "7": G("###", "..#", ".#.", ".#.", ".#."), "8": G("###", "#.#", "###", "#.#", "###"),
             "9": G("###", "#.#", "###", "..#", "##.")})
# the menu cursor: filled (selected) and hollow (the last choice, an unfocused menu)
TINY[">"] = G("#..", "##.", "###", "##.", "#..")
TINY["}"] = G("#..", "##.", "#.#", "##.", "#..")

# 5x7 font in the spirit of the Game Boy games' menu lettering (titles, labels, gen.bmp).
F7 = {
    "A": G(".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": G("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": G(".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": G("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."),
    "E": G("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": G("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": G(".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"),
    "H": G("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": G("###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"),
    "J": G("..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."),
    "K": G("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": G("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": G("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": G("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": G(".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": G("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": G(".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": G("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": G(".###.", "#...#", "#....", ".###.", "....#", "#...#", ".###."),
    "T": G("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": G("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": G("#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#.."),
    "W": G("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": G("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": G("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": G("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "é": G("...#.", "..#..", ".###.", "#...#", "#####", "#....", ".###."),
    "/": G("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "-": G("....", "....", "....", "####", "....", "....", "...."),
    " ": G("...", "...", "...", "...", "...", "...", "..."),
    ">": G("#...", "##..", "###.", "####", "###.", "##..", "#..."),
    "}": G("#...", "##..", "#.#.", "#..#", "#.#.", "##..", "#..."),
}


def glyph_w(font, c):
    return len(font[c][0])


def text_w(font, s, gap=1):
    s = [c for c in s if c in font]
    return sum(glyph_w(font, c) for c in s) + gap * max(0, len(s) - 1)


def draw_text(a, font, s, x, y, col, gap=1, shadow=None):
    """Text, with the GBA games' drop shadow (right, below and diagonal) when shadow is set."""
    x0 = x
    if shadow is not None:
        for dx, dy in ((1, 0), (0, 1), (1, 1)):
            draw_text(a, font, s, x0 + dx, y + dy, shadow, gap)
    for c in s:
        if c not in font:
            continue
        for r, row in enumerate(font[c]):
            for k, ch in enumerate(row):
                if ch == "#":
                    px(a, x + k, y + r, col)
        x += len(font[c][0]) + gap
    return x


def text_center(a, font, s, cx, y, col, gap=1, shadow=None):
    draw_text(a, font, s, cx - text_w(font, s, gap) // 2, y, col, gap, shadow)


REAL_FONT = {}


def real_font():
    """The Gen 1 games' own font (pokeyellow gfx/font/font.png, $80-$FF in 8x8 tiles), as glyphs
    7 wide (the tile minus its blank last column), so text keeps the games' 8 px pitch."""
    if not REAL_FONT:
        f = np.array(Image.open(os.path.join(SRC, "yellow", "gfx_font_font.png")).convert("L")) < 128

        def tile(code, rows=range(7)):
            r, c = divmod(code - 0x80, 16)
            g = f[r * 8:r * 8 + 8, c * 8:c * 8 + 7]
            return ["".join("#" if g[y, x] else "." for x in range(7)) for y in rows]
        for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            REAL_FONT[ch] = tile(0x80 + i)
        for i in range(10):
            REAL_FONT[str(i)] = tile(0xF6 + i)
        REAL_FONT["é"] = tile(0xBA)
        REAL_FONT["/"] = tile(0xF3)
        REAL_FONT["-"] = tile(0xE3)
        REAL_FONT[" "] = ["......."] * 7
        # ▶ / ▷ ($ED / $EC) sit one row lower in their tile than the capitals
        REAL_FONT[">"] = tile(0xED, range(8))
        REAL_FONT["}"] = tile(0xEC, range(8))
    return REAL_FONT


def TF():
    """The title bands' font: the games' own for Yellow, else the 5x7 menu font."""
    return T.get("tfont", F7)


def logo_w():
    return LOGO_W if "tfont" not in T else text_w(TF(), "POKéMON", 1) + 2


def logo(a, x, y, lit=True):
    """POKéMON in the logo's manner: chunky letters with a thick outline (9 rows tall)."""
    fill = T["logo_fill"] if lit else T["logo_fill_un"]
    line = T["logo_line"] if lit else T["logo_line_un"]
    s = "POKéMON"
    font = TF()
    gap = 2 if font is F7 else 1
    m = np.zeros((9, text_w(font, s, gap) + 2), bool)
    xx = 1
    for c in s:
        for r, row in enumerate(font[c]):
            for k, ch in enumerate(row):
                if ch == "#":
                    m[r + 1, xx + k] = True
        xx += glyph_w(font, c) + gap
    bold = m
    ol = np.zeros_like(bold)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ol |= np.roll(np.roll(bold, dy, 0), dx, 1)
    h, w = bold.shape
    for r in range(h):
        for c in range(w):
            if bold[r, c]:
                px(a, x + c, y + r, fill)
            elif ol[r, c]:
                px(a, x + c, y + r, line)
    return x + w


LOGO_W = text_w(F7, "POKéMON", 2) + 2


# ------------------------------------------------------------------------------------------
# Boxes: the Game Boy double-line text box, and the GBA rounded windows
# ------------------------------------------------------------------------------------------

# top-left corner of the Gen 1/2 text box frame (pokered/pokecrystal frame 1), 4 wide x 5 tall:
# outer line, gap, inner line (2 px thick along the top and bottom, 1 px down the sides).
GB_CORNER = ["..##", ".#..", "#..#", "#.##", "#.##"]


def gb_box(a, x, y, w, h, line=None, fill=None, top=True, bottom=True):
    line = T["line"] if line is None else line
    if fill is not None:
        rect(a, x + 3, y + (4 if top else 0), w - 6, h - (4 if top else 0) - (4 if bottom else 0), fill)
    y0 = y + (5 if top else 0)
    y1 = y + h - (5 if bottom else 0)
    for xx in (x, x + w - 1):
        rect(a, xx, y0, 1, y1 - y0, line)
    for xx in (x + 2, x + w - 3):
        rect(a, xx, y0, 1, y1 - y0, line)
    if fill is not None:
        rect(a, x + 1, y0, 1, y1 - y0, fill)
        rect(a, x + w - 2, y0, 1, y1 - y0, fill)
    for want, yy, flip in ((top, y, False), (bottom, y + h - 5, True)):
        if not want:
            continue
        rows = GB_CORNER[::-1] if flip else GB_CORNER
        if fill is not None:
            rect(a, x + 4, yy + (4 if flip else 0), w - 8, 1, fill)
            rect(a, x + 1, yy, w - 2, 5, None)
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                col = line if ch == "#" else fill
                if ch == "." and (r, c) in (((0, 0), (0, 1), (1, 0)) if not flip else ((4, 0), (4, 1), (3, 0))):
                    continue  # outside the rounded corner
                px(a, x + c, yy + r, col)
                px(a, x + w - 1 - c, yy + r, col)
        # the straight runs between the corners
        prof = [line, fill, line, line, fill]
        if flip:
            prof = prof[::-1]
        for r, col in enumerate(prof):
            rect(a, x + 4, yy + r, w - 8, 1, col)


CUTS = {0: [], 1: [1], 2: [2, 1], 3: [3, 1, 1], 4: [4, 2, 1, 1]}


def round_rect(a, x, y, w, h, r, col, top=True, bottom=True):
    """A filled rectangle with cut (pixel-rounded) corners."""
    cuts = CUTS[max(0, r)]
    for yy in range(h):
        c = 0
        if top and yy < len(cuts):
            c = cuts[yy]
        if bottom and h - 1 - yy < len(cuts):
            c = max(c, cuts[h - 1 - yy])
        rect(a, x + c, y + yy, w - 2 * c, 1, col)


def layered(a, x, y, w, h, layers, fill, r=3, top=True, bottom=True):
    """Concentric rounded rings, outermost first, then the fill."""
    for i, col in enumerate(layers):
        round_rect(a, x + i, y + (i if top else 0), w - 2 * i, h - (i if top else 0) - (i if bottom else 0),
                   max(0, r - i), col, top, bottom)
    i = len(layers)
    round_rect(a, x + i, y + (i if top else 0), w - 2 * i, h - (i if top else 0) - (i if bottom else 0),
               max(0, r - i), fill, top, bottom)


def thin_box(a, x, y, w, h, line, fill):
    """A 1 px rounded outline (the corner pixel cut)."""
    rect(a, x + 1, y, w - 2, 1, line)
    rect(a, x + 1, y + h - 1, w - 2, 1, line)
    rect(a, x, y + 1, 1, h - 2, line)
    rect(a, x + w - 1, y + 1, 1, h - 2, line)
    rect(a, x + 1, y + 1, w - 2, h - 2, fill)


def display(a, x, y, w, h, kind="msg"):
    """A display panel: the text box (Gen 1/2), or the message box / battle healthbox (Gen 3).
    The inside starts 3 px in from the sides and 4 px (top, bottom) in every style."""
    if not GBA():
        gb_box(a, x, y, w, h, fill=T["panel_l"] if kind == "health" else T["panel"])
    elif kind == "health":
        hl = T["health"]
        layered(a, x, y + 1, w, h - 2, [hl[0], hl[1], hl[0]], T["panel_l"], r=3)
        rect(a, x + 3, y + h - 5, w - 6, 1, (222, 213, 180))  # the cream panel's lower shade
    else:
        m = T["msg"]
        layered(a, x, y + 1, w, h - 2, [m[0], m[1], m[3]], T["panel"], r=3)


# ------------------------------------------------------------------------------------------
# Window chrome: a title band on top, the frame down the sides and along the bottom
# ------------------------------------------------------------------------------------------


def band_rows(h, lit):
    """Colours of the title band's rows (gen 3: the PokéNav header's mint stripes)."""
    if not GBA():
        rows = [T["band"] if lit else T["band_un"]] * h
        if T.get("band_edge"):
            rows[-1] = T["band_edge"]   # a dark line under the band, like a ledge's edge
        return rows
    s = "" if lit else "_un"
    hi, mid, base, lo = T["band" + s + "_hi"], T["band" + s + "_mid"], T["band" if lit else "band_un"], T["band" + s + "_lo"]
    rows = [hi, mid] + [base] * (h - 4) + [mid, lo]
    return rows


def band(w, h, lit):
    a = new(w, h)
    for r, col in enumerate(band_rows(h, lit)):
        rect(a, 0, r, w, 1, col)
    return a


def band_text(a, s, x, y, lit, font=None):
    font = TF() if font is None else font
    col = T["txt_band"] if lit else T["txt_band_un"]
    sh = (T["band_shadow"] if lit else T["band_shadow_un"]) if GBA() else None
    return draw_text(a, font, s, x, y, col, shadow=sh)


def band_text_center(a, s, cx, y, lit, font=None):
    font = TF() if font is None else font
    band_text(a, s, cx - text_w(font, s) // 2, y, lit, font)


def frame_cols():
    """Side profile from the outside in (None = window material)."""
    if GBA():
        return T["frame"]
    return [T["line"], T.get("frame_mid"), T["line"]]


def side(a, x, y, h, left=True):
    """The window frame down one side (3 columns)."""
    for i, col in enumerate(frame_cols()):
        xx = x + i if left else x - i
        if col is None:
            continue
        rect(a, xx, y, 1, h, col)


def bottom_frame(a, x, y, w, left_corner, right_corner):
    """The bottom 4 rows of the frame (y is the first of them), with rounded corners."""
    if not GBA():
        mid = T.get("frame_mid")
        prof = [T["line"], T["line"], mid, T["line"]]
        cmap = {"#": T["line"], ".": T["body"], "g": mid}
        corner = GB_CORNER[::-1]  # rows y-1 .. y+3, the side's last row first
        if mid is not None:
            corner = ["#g##", "#g##", "#gg#", ".#gg", "..##"]  # the same, its gap filled
    else:
        fr = T["frame"]
        prof = [fr[2], fr[1], fr[1], fr[0]]
        cmap = {"0": fr[0], "1": fr[1], "2": fr[2], ".": T["body"]}
        corner = ["0122", "0122", "0111", ".011", "..00"]
    for r, col in enumerate(prof):
        if col is not None:
            rect(a, x, y + r, w, 1, col)
    for want, cx, sgn in ((left_corner, x, 1), (right_corner, x + w - 1, -1)):
        if want:
            for r, row in enumerate(corner):
                for c, ch in enumerate(row):
                    px(a, cx + sgn * c, y - 1 + r, cmap[ch])


def window(w, h, band_h):
    """A whole window body: material, band space, frame on sides and bottom."""
    a = new(w, h)
    body_rows(a, 0, 0, w, h)
    side(a, 0, band_h, h - band_h - 4, True)
    side(a, w - 1, band_h, h - band_h - 4, False)
    bottom_frame(a, 0, h - 4, w, True, True)
    if not GBA():
        # the corners' outside is the desktop: show the material there too
        pass
    return a


# ------------------------------------------------------------------------------------------
# Small parts: titlebar buttons, the menu cursor, the Poké Ball
# ------------------------------------------------------------------------------------------

MINI = {
    "options": [".......", ".#####.", "..###..", "...#...", "......."],
    "minimize": [".......", ".......", ".......", ".......", "#######"],
    "shade": ["#######", ".......", "#######", ".......", "......."],
    "close": ["#.....#", ".#...#.", "..#.#..", "...#...", "..#.#..", ".#...#.", "#.....#"],
}


def mini_button(a, x, y, kind, lit=True, pressed=False):
    """9x9 titlebar button on the band: a light glyph; pressed, a light tile with a dark glyph."""
    rows = band_rows(14, lit)
    for r in range(9):
        rect(a, x, y + r, 9, 1, rows[min(13, 3 + r)])
    ink = T["txt_band"] if lit else T["txt_band_un"]
    if pressed:
        thin_box(a, x, y, 9, 9, ink, ink)
        ink = T["band"]
    g = MINI[kind]
    gy = y + (9 - len(g)) // 2
    if GBA() and not pressed:
        pat(a, x + 2, gy + 1, g, {"#": T["band_shadow"] if lit else T["band_shadow_un"]})
    pat(a, x + 1, gy, g, {"#": ink})


def tiny_cursor(a, x, y, col, hollow=False):
    pat(a, x, y, TINY["}" if hollow else ">"], {"#": col})


def ball(a, x, y, w, h, pressed=False):
    """A Poké Ball filling a w x h ellipse (corners left as they are)."""
    B = T["ball"]
    cx, cy = (w - 1) / 2, (h - 1) / 2
    rx, ry = w / 2, h / 2
    mid = h // 2
    for r in range(h):
        for c in range(w):
            d = ((c - cx) / rx) ** 2 + ((r - cy) / ry) ** 2
            if d > 1.0:
                continue
            # outline: an outside neighbour
            edge = False
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c2, r2 = c + dc, r + dr
                if not (0 <= c2 < w and 0 <= r2 < h) or ((c2 - cx) / rx) ** 2 + ((r2 - cy) / ry) ** 2 > 1.0:
                    edge = True
            if edge:
                col = B["line"]
            elif r == mid - (1 if h % 2 == 0 else 0) and h >= 9:
                col = B["line"]
            elif r < mid - (1 if h % 2 == 0 else 0):
                col = B["top_p"] if pressed else B["top"]
            else:
                col = B["bot"]
            px(a, x + c, y + r, col)
    # the button
    bx = x + w // 2 - (1 if w % 2 == 0 else 1)
    by = y + mid - (2 if h % 2 == 0 else 1) - (0 if h % 2 else 0)
    if h >= 9:
        bw = 3 if w % 2 else 4
        rect(a, bx - (0 if w % 2 else 0), by, bw, 3, B["line"])
        rect(a, bx + 1 - (0 if w % 2 else 0), by + 1, bw - 2, 1, B["bot"])
    # a shine on the top half
    if h >= 9:
        px(a, x + max(2, w // 4), y + 2, B["shine"])


# ------------------------------------------------------------------------------------------
# Sprites (downloaded; exterior made transparent; pasted unscaled)
# ------------------------------------------------------------------------------------------

OW_RED = [gbc(27, 31, 27), gbc(31, 19, 10), gbc(31, 7, 1), (0, 0, 0)]  # pokecrystal npc_sprites.pal, day "red"


def read_jasc(path):
    lines = open(path, encoding="ascii").read().split()
    n = int(lines[2])
    vals = list(map(int, lines[3:3 + 3 * n]))
    return [tuple(vals[i:i + 3]) for i in range(0, 3 * n, 3)]


def load_sprite(spec):
    """RGBA numpy array of a sprite's first frame, cropped to its content."""
    folder, fname, kind, extra = spec
    im = Image.open(os.path.join(SRC, folder, fname))
    if kind in ("gbc_bg", "gbc_obj"):
        return load_gbc_sprite(im, kind, extra)
    w = im.width
    fh = w if kind != "gba" or "icon" not in fname else 32
    if kind == "gba":
        idx = np.array(im)[:fh]
        pal = im.getpalette()
        if extra:
            p = read_jasc(os.path.join(SRC, folder, extra))
            pal = [v for c in p for v in c]
        rgb = np.array([pal[3 * i:3 * i + 3] for i in range(len(pal) // 3)], np.int32)[idx]
        alpha = idx != 0
    else:
        g = np.array(im.convert("L"))[:fh] if kind != "png" else None
        if kind == "png":
            rgb = np.array(im.convert("RGB"))[:fh].astype(np.int32)
        else:
            levels = sorted(set(g.reshape(-1).tolist()), reverse=True)  # light .. dark
            # pad to four shades: 255, ~170, ~85, 0
            shade = {v: min(3, int(round((255 - v) / 85))) for v in levels}
            pal = DMG if kind == "gb1" else OW_RED
            rgb = np.array([[pal[shade[v]] for v in row] for row in g], np.int32)
        # transparent: the white connected to the border
        white = (rgb == rgb[0, 0]).all(-1)
        alpha = np.ones(white.shape, bool)
        stack = [(0, c) for c in range(w)] + [(fh - 1, c) for c in range(w)] + \
                [(r, 0) for r in range(fh)] + [(r, w - 1) for r in range(fh)]
        while stack:
            r, c = stack.pop()
            if 0 <= r < fh and 0 <= c < w and alpha[r, c] and white[r, c]:
                alpha[r, c] = False
                stack += [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
    ys, xs = np.nonzero(alpha)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]


def load_gbc_sprite(im, kind, extra):
    """A Game Boy 2bpp sprite (pret PNG: white, light grey, dark grey, black = shades 0..3) in
    Game Boy Color colours. gbc_bg: a battle/Pokédex pic in a palette, BGP %11100100 (shade n is
    colour n), the white connected to the edge left out. gbc_obj: an overworld sprite frame
    (extra = (palette, frame[, mirrored]); 16x16 frames), through OBP0, shade 0 transparent as on the hardware."""
    g = np.array(im.convert("L"))
    shade = np.rint((255 - g.astype(np.int32)) / 85).astype(np.int32)
    if kind == "gbc_bg":
        pal = extra
        idx = shade
        h, w = idx.shape
        alpha = np.ones((h, w), bool)
        stack = [(0, c) for c in range(w)] + [(h - 1, c) for c in range(w)] + \
                [(r, 0) for r in range(h)] + [(r, w - 1) for r in range(h)]
        while stack:
            r, c = stack.pop()
            if 0 <= r < h and 0 <= c < w and alpha[r, c] and idx[r, c] == 0:
                alpha[r, c] = False
                stack += [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
    else:
        pal, frame = extra[:2]
        sh = shade[frame * 16:frame * 16 + 16]
        if len(extra) > 2 and extra[2]:
            sh = sh[:, ::-1]  # facing right: the left-facing frame mirrored, as the games do (OAM X flip)
        idx = np.vectorize(lambda v: OBP0[v])(sh)
        alpha = sh != 0
    rgb = np.array([[pal[v] for v in row] for row in idx], np.int32)
    ys, xs = np.nonzero(alpha)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]


# ------------------------------------------------------------------------------------------
# The overworld backdrop (pokemon-yellow-overworld): pokeyellow's overworld tileset, 8x8 tiles
# unscaled, coloured through BGP %11100100 with the map palette as on a Game Boy Color
# ------------------------------------------------------------------------------------------

OW_PATH, OW_SPECK, OW_GRASS, OW_FLOWER, OW_TALL = 0x23, 0x39, 0x2C, 0x03, 0x52
OW_TREE = ((0x40, 0x41), (0x50, 0x51))   # the round tree, 16x16 (block $0F)


def ow_tile(n):
    im = Image.open(os.path.join(SRC, "yellow", "gfx_tilesets_overworld.png")).convert("L")
    r, c = divmod(n, 16)
    g = np.array(im.crop((c * 8, r * 8, c * 8 + 8, r * 8 + 8)))
    shade = np.rint((255 - g.astype(np.int32)) / 85).astype(np.int32)
    return np.array(T["map"], np.int32)[shade]


def overworld(a, w, h, controls, seed, open_ground=()):
    """Lay a little Route 1 inside the window frame (y 14 .. h-4): grass tiles with trees where a
    16x16 cell is clear of everything the app draws, flowers and tall grass sprinkled, and the
    white path (with its specks) under the controls (their rects, 1 px around), whose own
    backgrounds are that white. open_ground: rects kept to plain grass (no trees, flowers or tall
    grass), where sprites stand. Then the frame goes back on top."""
    rng = np.random.RandomState(seed)
    x0, y0 = 3, 14
    cols, rows = -(-(w - 6) // 8), -(-(h - 18) // 8)
    busy = np.zeros((rows * 8, cols * 8), bool)
    for x, y, cw, ch in controls:
        busy[max(0, y - 1 - y0):max(0, y + ch + 1 - y0), max(0, x - 1 - x0):max(0, x + cw + 1 - x0)] = True
    calm = np.zeros_like(busy)
    for x, y, cw, ch in open_ground:
        calm[max(0, y - y0):max(0, y + ch - y0), max(0, x - x0):max(0, x + cw - x0)] = True
    canvas = np.zeros((rows * 8, cols * 8, 3), np.int32)
    path = np.zeros_like(canvas)
    done = np.zeros((rows, cols), bool)
    for r in range(rows - 1):
        for c in range(cols - 1):
            cell = (slice(8 * r, 8 * r + 16), slice(8 * c, 8 * c + 16))
            if not (busy[cell].any() or calm[cell].any() or done[r:r + 2, c:c + 2].any()):
                for dr in (0, 1):
                    for dc in (0, 1):
                        canvas[8 * (r + dr):8 * (r + dr) + 8, 8 * (c + dc):8 * (c + dc) + 8] = ow_tile(OW_TREE[dr][dc])
                done[r:r + 2, c:c + 2] = True
    for r in range(rows):
        for c in range(cols):
            v = rng.randint(16)
            path[8 * r:8 * r + 8, 8 * c:8 * c + 8] = ow_tile(OW_SPECK if v < 2 else OW_PATH)
            if not done[r, c]:
                n = OW_FLOWER if v < 3 else OW_TALL if v < 5 else OW_GRASS
                if calm[8 * r:8 * r + 8, 8 * c:8 * c + 8].any():
                    n = OW_GRASS
                canvas[8 * r:8 * r + 8, 8 * c:8 * c + 8] = ow_tile(n)
    canvas[busy] = path[busy]
    a[y0:h - 4, x0:w - 3] = canvas[:h - 4 - y0, :w - 6]
    side(a, 0, 14, h - 14 - 4, True)
    side(a, w - 1, 14, h - 14 - 4, False)
    bottom_frame(a, 0, h - 4, w, True, True)


OCC = {}  # sheet name -> occupancy of the sprite, for the overlap checks


def paste_sprite(a, spec, x, y, sheet=None):
    rgb, al = load_sprite(spec)
    h, w = al.shape
    region = a[y:y + h, x:x + w]
    region[al] = rgb[al]
    if sheet:
        OCC.setdefault(sheet, []).append((x, y, w, h, al.copy()))
    return w, h


def sprite_size(spec):
    rgb, al = load_sprite(spec)
    return al.shape[1], al.shape[0]


# ------------------------------------------------------------------------------------------
# titlebar.bmp (344 x 87)
# ------------------------------------------------------------------------------------------

CLUTTER_SLOTS = [("O", 3, 8), ("A", 11, 7), ("I", 18, 7), ("D", 25, 8), ("V", 33, 7)]


def clutter_bar(lit_letters):
    a = new(8, 43)
    thin_box(a, 0, 0, 8, 43, T["line"] if not GBA() else T["msg"][1], T["panel"])
    for letter, y, h in CLUTTER_SLOTS:
        on = letter in lit_letters
        if on:
            rect(a, 1, y, 6, h, band_rows(14, True)[6])
        gy = y + (h - 5) // 2
        draw_text(a, TINY, letter, 3 if letter == "I" else 2, gy,
                  T["txt_band"] if on else T["ink"])
    return a


class main_band:
    """While drawing the main window's titlebar pieces: its own band colour when the theme has
    one (main_band), the other windows keeping theirs."""
    def __enter__(self):
        self.saved = T["band"]
        T["band"] = T.get("main_band", T["band"])

    def __exit__(self, *exc):
        T["band"] = self.saved


def main_titlebar(lit):
    with main_band():
        return _main_titlebar(lit)


def _main_titlebar(lit):
    a = band(275, 14, lit)
    mini_button(a, 6, 3, "options", lit)
    mini_button(a, 244, 3, "minimize", lit)
    mini_button(a, 254, 3, "shade", lit)
    mini_button(a, 264, 3, "close", lit)
    col = T["txt_band"] if lit else T["txt_band_un"]
    sh = (T["band_shadow"] if lit else T["band_shadow_un"]) if GBA() else None
    sub = T["sub"].replace("POKE", "POKé")
    cw = glyph_w(TF(), ">")
    total = cw + 4 + logo_w() + 5 + text_w(TF(), sub)
    x = (275 - total) // 2
    draw_text(a, TF(), ">" if lit else "}", x, 4, col, shadow=sh)
    x = logo(a, x + cw + 4, 2, lit)
    draw_text(a, TF(), sub, x + 5, 4, col, shadow=sh)
    return a


def make_titlebar():
    with main_band():
        return _make_titlebar()


def _make_titlebar():
    a = new(344, 87)
    for kind, x in (("options", 0), ("minimize", 9), ("close", 18)):
        for pressed, y in ((False, 0), (True, 9)):
            b = new(9, 9)
            mini_button(b, 0, 0, kind, True, pressed)
            a[y:y + 9, x:x + 9] = b
    for pressed, x in ((False, 0), (True, 9)):
        b = new(9, 9)
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

ABOUT = (239, 83, 32, 28)   # the free corner (the About spot), x y w h


def make_main():
    a = window(275, 116, 14)
    if T.get("map"):
        overworld(a, 275, 116, MAIN_CONTROLS[1:], seed=1, open_ground=[ABOUT])
    a[0:14, :] = main_titlebar(True)
    a[22:65, 10:18] = clutter_bar("")
    display(a, 20, 18, 86, 45, "health")      # time + analyser (inside 23..102 x 22..58)
    display(a, 107, 18, 162, 39, "msg")       # title + kbps/khz/stereo (inside 110..265 x 22..52)
    for x in range(112, 264, 2):              # a dotted rule under the title row
        px(a, x, 38, T["ink2"] if not GBA() else T["msg"][3])
    draw_text(a, TINY, "KBPS", 129, 44, T["ink2"])
    draw_text(a, TINY, "KHZ", 169, 44, T["ink2"])
    # the emblem / sprite in the About spot
    spec = T["sprites"]["about"]
    ax, ay, aw, ah = ABOUT
    if isinstance(spec, list):
        # a row of overworld sprites on one ground line (Yellow: Pikachu following the player)
        sizes = [sprite_size(s) for s in spec]
        tw, th = sum(w for w, h in sizes), max(h for w, h in sizes)
        x = ax + (aw - tw) // 2
        for s, (w, h) in zip(spec, sizes):
            paste_sprite(a, s, x, ay + (ah - th) // 2 + 1 + th - h, "main")
            x += w
    else:
        w, h = sprite_size(spec)
        paste_sprite(a, spec, ax + (aw - w) // 2, ay + (ah - h) // 2 + (1 if h < 20 else 0), "main")
    return a


# ------------------------------------------------------------------------------------------
# cbuttons.bmp (136 x 36)
# ------------------------------------------------------------------------------------------


def button(a, x, y, w, h, pressed, on=False):
    """A transport / menu button: GB box, PokéGear icon tile, or GBA rounded button."""
    if T["key"] == "gen2":
        face = T["btnp_face"] if pressed else T["btn_face"]
        thin_box(a, x, y, w, h, T["btn_line"], face)
        if not pressed:
            rect(a, x + 1, y + 1, w - 2, 1, T["btn_hi"])
            rect(a, x + 1, y + 1, 1, h - 2, T["btn_hi"])
            rect(a, x + 1, y + h - 2, w - 2, 1, T["btn_lo"])
            rect(a, x + w - 2, y + 1, 1, h - 2, T["btn_lo"])
        else:
            rect(a, x + 1, y + 1, w - 2, 1, (60, 60, 60))
            rect(a, x + 1, y + 1, 1, h - 2, (60, 60, 60))
    elif GBA():
        face = T["btnp_face"] if pressed else T["btn_face"]
        layered(a, x, y, w, h, [T["btn_line"]], face, r=2)
        if not pressed:
            rect(a, x + 2, y + h - 2, w - 4, 1, (200, 228, 220))
    else:
        thin_box(a, x, y, w, h, T["btn_line"], T["btnp_face"] if pressed else T["btn_face"])


def tri_right(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        rect(a, x, y + r, half - abs(r - half) + 1, 1, col)


def tri_left(a, x, y, h, col):
    half = h // 2
    for r in range(h):
        n = half - abs(r - half) + 1
        rect(a, x + half + 1 - n, y + r, n, 1, col)


def transport_icon(a, kind, x, y, w, h, col):
    cx, cy = x + w // 2, y + h // 2
    if kind == "previous":
        rect(a, cx - 5, cy - 3, 2, 7, col)
        tri_left(a, cx - 3, cy - 3, 7, col)
        tri_left(a, cx + 1, cy - 3, 7, col)
    elif kind == "play":
        tri_right(a, cx - 2, cy - 4, 9, col)
    elif kind == "pause":
        rect(a, cx - 4, cy - 3, 3, 7, col)
        rect(a, cx + 1, cy - 3, 3, 7, col)
    elif kind == "stop":
        rect(a, cx - 3, cy - 3, 7, 7, col)
    elif kind == "next":
        tri_right(a, cx - 4, cy - 3, 7, col)
        tri_right(a, cx, cy - 3, 7, col)
        rect(a, cx + 4, cy - 3, 2, 7, col)
    elif kind == "eject":
        for r in range(4):
            rect(a, cx - 1 - r, cy - 4 + r, 2 * r + 3, 1, col)
        rect(a, cx - 4, cy + 1, 9, 2, col)


def glyph_cols(pressed):
    ink = T["btnp_glyph"] if pressed else T["btn_glyph"]
    sh = T["shadow"] if GBA() and not pressed else None
    return ink, sh


def make_cbuttons():
    a = new(136, 36)
    specs = [("previous", 0, 23, 18), ("play", 23, 23, 18), ("pause", 46, 23, 18),
             ("stop", 69, 23, 18), ("next", 92, 22, 18)]
    for kind, x, w, h in specs:
        for pressed, y in ((False, 0), (True, 18)):
            button(a, x, y, w - 1, h, pressed)
            ink, sh = glyph_cols(pressed)
            o = 1 if pressed else 0
            if sh:
                transport_icon(a, kind, x + o + 1, y + o + 1, w - 1, h, sh)
            transport_icon(a, kind, x + o, y + o, w - 1, h, ink)
    for pressed, y in ((False, 0), (True, 16)):
        button(a, 114, y, 22, 16, pressed)
        ink, sh = glyph_cols(pressed)
        o = 1 if pressed else 0
        if sh:
            transport_icon(a, "eject", 115 + o, y + 1 + o, 22, 16, sh)
        transport_icon(a, "eject", 114 + o, y + o, 22, 16, ink)
    return a


# ------------------------------------------------------------------------------------------
# shufrep.bmp (92 x 85): START-menu-style items, ▶ when on
# ------------------------------------------------------------------------------------------


def menu_item(a, x, y, w, h, label, on, pressed):
    rect(a, x, y, w, h, T["body"])
    if pressed:
        thin_box(a, x, y, w, h, T["sel"], T["sel"])
    tw = 4 + text_w(TINY, label)
    tx = x + (w - tw) // 2 + (1 if pressed else 0)
    ty = y + (h - 5) // 2 + (1 if pressed else 0)
    ink = T["ink"] if on else T["off"]
    sh = T["shadow"] if GBA() and on else None
    if on:
        if sh:
            tiny_cursor(a, tx + 1, ty + 1, sh)
        tiny_cursor(a, tx, ty, T["cursor"])
    draw_text(a, TINY, label, tx + 4, ty, ink, shadow=sh)


def make_shufrep():
    a = new(92, 85)
    for row, (on, pressed) in enumerate([(False, False), (False, True), (True, False), (True, True)]):
        y = row * 15
        menu_item(a, 0, y, 28, 15, "REPEAT", on, pressed)
        menu_item(a, 28, y, 47, 15, "SHUFFLE", on, pressed)
    for x, label, pressed in [(0, "EQ", False), (23, "PL", False), (46, "EQ", True), (69, "PL", True)]:
        menu_item(a, x, 61, 23, 12, label, False, pressed)
        menu_item(a, x, 73, 23, 12, label, True, pressed)
    return a


# ------------------------------------------------------------------------------------------
# monoster, playpaus, numbers, nums_ex, text
# ------------------------------------------------------------------------------------------


def make_monoster():
    a = new(56, 24, T["panel"])
    for y, on in ((0, True), (12, False)):
        col = T["ink"] if on else T.get("dim", T["sel"]) if not GBA() else (214, 214, 214)
        text_center(a, TINY, "STEREO", 14, y + 4, col)
        text_center(a, TINY, "MONO", 42, y + 4, col)
    return a


def make_playpaus():
    a = new(48, 9, T["panel_l"])
    ink = T["ink"]
    pat(a, 3, 1, F7[">"], {"#": ink})                 # playing: the menu cursor
    rect(a, 9 + 2, 1, 2, 7, ink)                      # paused
    rect(a, 9 + 5, 1, 2, 7, ink)
    rect(a, 18 + 2, 2, 5, 5, ink)                     # stopped
    px(a, 40, 4, ink)                                 # working
    return a


DIG = {
    0: [".##.", "#..#", "#..#", "#..#", "#..#", ".##."], 1: [".#..", "##..", ".#..", ".#..", ".#..", "###."],
    2: [".##.", "#..#", "..#.", ".#..", "#...", "####"], 3: ["###.", "...#", ".##.", "...#", "...#", "###."],
    4: ["..#.", ".##.", "#.#.", "####", "..#.", "..#."], 5: ["####", "#...", "###.", "...#", "#..#", ".##."],
    6: [".##.", "#...", "###.", "#..#", "#..#", ".##."], 7: ["####", "...#", "..#.", ".#..", ".#..", ".#.."],
    8: [".##.", "#..#", ".##.", "#..#", "#..#", ".##."], 9: [".##.", "#..#", "#..#", ".###", "...#", ".##."],
    "-": ["....", "....", "####", "....", "....", "...."],
}


def big_digit(a, x, y, rows):
    def put(dx, dy, col):
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch == "#":
                    rect(a, x + dx + 2 * c, y + dy + 2 * r, 2, 2, col)
    if GBA():
        put(1, 1, T["shadow"])
    put(0, 0, T["ink"])


def make_numbers(ex):
    a = new(108 if ex else 99, 13, T["panel_l"])
    for n in range(10):
        big_digit(a, 9 * n, 0, DIG[n])
    if ex:
        big_digit(a, 99, 0, DIG["-"])
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
            draw_text(a, FONT5, key, col * 5, row * 6, T["ink"],
                      shadow=(228, 228, 222) if GBA() else None)
    # the shadow may spill into the next cell's first column: keep each cell's last column clear
    return a


# ------------------------------------------------------------------------------------------
# posbar (the seek bar: an HP-bar groove / the PokéGear tuning dial), volume (HP), balance (EXP)
# ------------------------------------------------------------------------------------------


def hbar(a, x, y, w, inner, fill=None, fill_to=None, shade=None, h=5):
    """A horizontal bar w wide, h tall at y: outline, rounded ends, inner colour, optional fill."""
    line = T["bar_line"]
    rect(a, x + 1, y, w - 2, 1, line)
    rect(a, x + 1, y + h - 1, w - 2, 1, line)
    rect(a, x, y + 1, 1, h - 2, line)
    rect(a, x + w - 1, y + 1, 1, h - 2, line)
    rect(a, x + 1, y + 1, w - 2, h - 2, inner)
    if fill is not None and fill_to is not None and fill_to > x + 1:
        rect(a, x + 1, y + 1, fill_to - (x + 1), h - 2, fill)
        if shade is not None:
            rect(a, x + 1, y + h - 2, fill_to - (x + 1), 1, shade)


def hp_tier(v):
    return 0 if v > 0.5 else 1 if v > 0.2 else 2


def groove_inner():
    if T["key"] == "gen2":
        return G2_GREY
    if GBA():
        return T["track"]
    return T["panel"]


def make_posbar():
    a = new(307, 10)
    hbar(a, 0, 2, 248, groove_inner(), h=6)
    if T["key"] == "gen2":
        # the tuning dial's darker blocks along the bar (pokegear.png)
        for x in range(10, 240, 24):
            rect(a, x, 3, 2, 4, G2_DGREY)
    for x0, pressed in ((248, False), (278, True)):
        t = new(29, 10)
        hbar(t, -10, 2, 49, groove_inner(), h=6)
        ball(t, 9, 0, 11, 10, pressed)
        a[:, x0:x0 + 29] = t
    a[:, 277] = a[:, 247]
    return a


def thumbs(a, x, y):
    for xx, sel in ((x, True), (x + 15, False)):
        rect(a, xx, y, 14, 11, T["body"])
        ball(a, xx, y, 14, 11, sel)


def make_volume():
    a = new(68, 433)
    for i in range(28):
        y = i * 15
        v = (i + 1) / 28
        tier = hp_tier(v)
        fill_to = 2 + round(v * 64)
        shade = T["hp_shade"][tier] if T["hp_shade"] else None
        hbar(a, 0, y + 4, 68, T["track"], T["hp"][tier], fill_to, shade)
    thumbs(a, 0, 422)
    return a


def make_balance():
    a = new(68, 433)
    track = T.get("exp_track", T["track"])
    for i in range(28):
        y = i * 15
        hbar(a, 9, y + 4, 38, track)
        reach = round(17 * i / 27)
        if i:
            rect(a, 28 - reach, y + 5, 2 * reach, 3, T["exp"])
        rect(a, 27, y + 2, 2, 2, T["ink2"])
    thumbs(a, 0, 422)
    return a


# ------------------------------------------------------------------------------------------
# eqmain.bmp (275 x 315)
# ------------------------------------------------------------------------------------------

EQ_BANDS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
EQ_SPRITE_BOX = (36, 38, 41, 64)   # between the preamp and the first band (the dB labels' place)


def eq_titlebar(lit):
    a = band(275, 14, lit)
    s = T["eq_title"]
    cw = glyph_w(TF(), ">") + 2
    tw = cw + text_w(TF(), s)
    x = (275 - tw) // 2
    col = T["txt_band"] if lit else T["txt_band_un"]
    sh = (T["band_shadow"] if lit else T["band_shadow_un"]) if GBA() else None
    draw_text(a, TF(), ">" if lit else "}", x, 4, col, shadow=sh)
    band_text(a, s, x + cw, 4, lit)
    mini_button(a, 264, 3, "close", lit)
    return a


def eq_slider_frame(a, x, y, n):
    """14x63: a vertical HP bar (cols 4..8) filling up with the value (n of 0..27)."""
    rect(a, x, y, 14, 63, T["body"])
    v = n / 27
    line = T["bar_line"]
    rect(a, x + 5, y + 1, 3, 1, line)
    rect(a, x + 5, y + 61, 3, 1, line)
    rect(a, x + 4, y + 2, 1, 59, line)
    rect(a, x + 8, y + 2, 1, 59, line)
    rect(a, x + 5, y + 2, 3, 59, T["track"])
    top = 2 + round((1 - v) * 58)
    tier = hp_tier(v)
    rect(a, x + 5, y + top, 3, 61 - top, T["hp"][tier])
    if T["hp_shade"]:
        rect(a, x + 7, y + top, 1, 61 - top, T["hp_shade"][tier])
    for cx in (x + 1, x + 10):
        rect(a, cx, y + 31, 3, 1, T["ink2"])


def make_eqmain():
    a = window(275, 116, 14)
    if T.get("map"):
        overworld(a, 275, 116, EQ_CONTROLS[1:] + [(36, 38, 41, 64)], seed=2)
    a = np.concatenate([a, new(275, 315 - 116)], 0)
    a[0:14, :] = eq_titlebar(True)
    if GBA():
        layered(a, 85, 16, 115, 21, [T["msg"][1]], T["panel"], r=2)
    else:
        thin_box(a, 85, 16, 115, 21, T["line"], T["panel"])
    for x in [21] + [78 + 18 * i for i in range(10)]:
        eq_slider_frame(a, x, 38, 14)
    lab = T["ink2"]
    text_center(a, TINY, "PREAMP", 28, 106, lab)
    for i, lbl in enumerate(EQ_BANDS):
        text_center(a, TINY, lbl, 78 + 18 * i + 7, 106, lab)
    # a Pokédex entry: the sprite in a box, its number under it
    spec = T["sprites"]["eq"]
    w, h = sprite_size(spec)
    bx, by, bw, bh = EQ_SPRITE_BOX
    if GBA():
        layered(a, bx, by, bw, bh, [T["msg"][1]], T["panel"], r=2)
    else:
        thin_box(a, bx, by, bw, bh, T["line"], T["panel"])
    sy = by + 2 + (bh - 11 - h) // 2
    paste_sprite(a, spec, bx + (bw - w) // 2, sy, "eqmain")
    text_center(a, TINY, T["dexno"], bx + bw // 2, by + bh - 8, T["ink"])

    # under the window
    rect(a, 0, 116, 275, 315 - 116, T["body"])
    b = new(9, 9)
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[125:134, 0:9] = b
    for x, label, on, pressed in [
        (10, "ON", False, False), (36, "AUTO", False, False), (69, "ON", True, False), (95, "AUTO", True, False),
        (128, "ON", False, True), (154, "AUTO", False, True), (187, "ON", True, True), (213, "AUTO", True, True),
    ]:
        menu_item(a, x, 119, 26 if label == "ON" else 32, 12, label, on, pressed)
    a[134:148, :] = eq_titlebar(True)
    a[149:163, :] = eq_titlebar(False)
    for y, sel in ((164, False), (176, True)):
        rect(a, 0, y, 11, 11, T["body"])
        ball(a, 0, y, 11, 11, sel)
    for n in range(28):
        eq_slider_frame(a, 13 + (n % 14) * 15, 164 + (n // 14) * 65, n)
    for y, pressed in ((164, False), (176, True)):
        rect(a, 224, y, 44, 12, T["body"])
        button(a, 224, y, 44, 12, pressed)
        ink, sh = glyph_cols(pressed)
        o = 1 if pressed else 0
        text_center(a, TINY, "PRESETS", 224 + 22 + o, y + 4 + o - (1 if GBA() else 0), ink, shadow=sh)
    # graph
    rect(a, 0, 294, 113, 19, T["panel"])
    grid = T.get("dim", T["sel"]) if not GBA() else (224, 232, 224)
    for x in range(0, 113, 12):
        for y in range(0, 19, 2):
            px(a, 2 + x, 294 + y, grid)
    for x in range(0, 113, 2):
        px(a, x, 294 + 9, grid)
    for r in range(19):
        t = r / 18
        px(a, 115, 294 + r, T["hp"][0] if t < 0.45 else T["hp"][1] if t < 0.75 else T["hp"][2])
        if not GBA() and T["key"] == "gen1":
            px(a, 115, 294 + r, T["ink"])
    for x in range(113):
        px(a, x, 314, T["ink2"] if x % 3 != 2 else T["panel"])
    return a


# ------------------------------------------------------------------------------------------
# pledit.bmp (280 x 186) and gen.bmp (194 x 109): the 20 px titled frames
# ------------------------------------------------------------------------------------------

BAND20 = 15   # the 20 px titlebars: a 15-row band, then 5 rows of window material


def bar20(w, lit, left=False, right=False):
    a = new(w, 20)
    body_rows(a, 0, 0, w, 20)
    a[0:BAND20] = band(w, BAND20, lit)
    if left:
        side(a, 0, BAND20, 20 - BAND20, True)
    if right:
        side(a, w - 1, BAND20, 20 - BAND20, False)
    return a


def mini20(a, x, y, kind, lit, pressed=False):
    b = new(9, 9)
    mini_button(b, 0, 0, kind, lit, pressed)
    # the 14 px band's rows 3..11 match the 15-row band's 3..11 (same colours in every style)
    a[y:y + 9, x:x + 9] = b


def scroll_groove(t, x, h):
    rect(t, x + 3, 0, 2, h, T["sel"] if not GBA() else (214, 240, 230))


def make_pledit():
    a = new(280, 186)
    body_rows(a, 0, 0, 280, 186)
    for lit, y in ((True, 0), (False, 21)):
        t = bar20(25, lit)
        a[y:y + 20, 127:152] = t
        t = bar20(25, lit, left=True)
        a[y:y + 20, 0:25] = t
        # title tile: sprite + PLAYLIST
        t = bar20(100, lit)
        spec = T["sprites"]["pl"]
        sw, sh_ = sprite_size(spec)
        s = T["pl_title"]
        total = sw + 4 + text_w(TF(), s)
        x0 = (100 - total) // 2
        sy = max(0, (BAND20 - sh_) // 2) if sh_ <= BAND20 else BAND20 + 2 - sh_
        paste_sprite(t, spec, x0, sy, "pledit" if lit else None)
        band_text(t, s, x0 + sw + 4, 4, lit)
        a[y:y + 20, 26:126] = t
        t = bar20(25, lit, right=True)
        scroll_groove(t, 10, 20)
        t[0:BAND20] = band(25, BAND20, lit)
        mini20(t, 14, 3, "close", lit)
        a[y:y + 20, 153:178] = t
    # sides
    t = new(12, 29)
    body_rows(t, 0, 0, 12, 29)
    side(t, 0, 0, 29, True)
    a[42:71, 0:12] = t
    t = new(20, 29)
    body_rows(t, 0, 0, 20, 29)
    scroll_groove(t, 5, 29)
    side(t, 19, 0, 29, False)
    a[42:71, 31:51] = t
    b = new(9, 9)
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 52:61] = b
    for x, sel in ((52, False), (61, True)):
        rect(a, x, 53, 8, 18, T["body"])
        button(a, x, 53, 8, 18, sel)
        for gy in (59, 61, 63):
            rect(a, x + 2, gy, 4, 1, T["btnp_glyph"] if sel else T["btn_glyph"])

    def bottom_base(w, left=False, right=False):
        t = new(w, 38)
        body_rows(t, 0, 0, w, 38)
        if left:
            side(t, 0, 0, 34, True)
        if right:
            side(t, w - 1, 0, 34, False)
        bottom_frame(t, 0, 34, w, left, right)
        return t

    def word_button(t, x, y, w, h, s):
        button(t, x, y, w, h, False)
        ink, sh = glyph_cols(False)
        text_center(t, TINY, s, x + w // 2, y + (h - 5) // 2, ink, shadow=sh)

    t = bottom_base(125, left=True)
    for bx, lbl in ((14, "ADD"), (43, "REM"), (72, "SEL"), (101, "MISC")):
        word_button(t, bx, 9, 22, 13, lbl)
    a[72:110, 0:125] = t

    t = bottom_base(150, right=True)
    thin_box(t, 5, 8, 58, 10, T["line"] if not GBA() else T["msg"][1], T["panel"])
    thin_box(t, 2, 21, 62, 12, T["line"] if not GBA() else T["msg"][1], T["panel"])
    for k, kind in enumerate(["previous", "play", "pause", "stop", "next", "eject"]):
        mini_transport_icon(t, kind, 3 + 10 * k, 22)
    thin_box(t, 64, 21, 35, 10, T["line"] if not GBA() else T["msg"][1], T["panel"])
    px(t, 84, 24, T["ink2"])
    px(t, 84, 27, T["ink2"])
    word_button(t, 105, 9, 24, 13, "LIST")
    for k in range(4):
        for j in range(k + 1):
            px(t, 143 - 2 * k + 2 * j, 31 - 2 * j, T["ink2"])
    a[72:110, 126:276] = t
    t = bottom_base(25)
    a[0:38, 179:204] = t
    return a


def mini_transport_icon(a, kind, x, y):
    ink = T["ink"]
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
    body_rows(a, 0, 0, 194, 109)
    for lit, y in ((True, 0), (False, 21)):
        a[y:y + 20, 0:25] = bar20(25, lit, left=True)
        t = bar20(25, lit)
        col = T["txt_band"] if lit else T["txt_band_un"]
        sh = (T["band_shadow"] if lit else T["band_shadow_un"]) if GBA() else None
        draw_text(t, F7, ">" if lit else "}", 18, 4, col, shadow=sh)
        a[y:y + 20, 26:51] = t
        for x in (52, 78, 104):
            a[y:y + 20, x:x + 25] = bar20(25, lit)
        t = bar20(25, lit, right=True)
        mini20(t, 14, 3, "close", lit)
        a[y:y + 20, 130:155] = t

    def bottom(w, left, right):
        t = new(w, 14)
        body_rows(t, 0, 0, w, 14)
        if left:
            side(t, 0, 0, 10, True)
        if right:
            side(t, w - 1, 0, 10, False)
            for k in range(3):
                for j in range(k + 1):
                    px(t, w - 6 - 2 * k + 2 * j, 7 - 2 * j, T["ink2"])
        bottom_frame(t, 0, 10, w, left, right)
        return t

    a[42:56, 0:125] = bottom(125, True, False)
    a[57:71, 0:125] = bottom(125, False, True)
    a[72:86, 127:152] = bottom(25, False, False)
    for x, w, h, left in ((127, 11, 29, True), (158, 11, 24, True), (139, 8, 29, False), (170, 8, 24, False)):
        t = new(w, h)
        body_rows(t, 0, 0, w, h)
        side(t, 0 if left else w - 1, 0, h, left)
        a[42:42 + h, x:x + w] = t
    b = new(9, 9)
    mini_button(b, 0, 0, "close", True, pressed=True)
    a[42:51, 148:157] = b

    # letters: rows 88 (focused) and 96 (unfocused); cells of band colour split by SEP columns
    for lit, y in ((True, 88), (False, 96)):
        rect(a, 0, y, 194, 7, SEP)
        rows = band_rows(BAND20, lit)
        col = T["txt_band"] if lit else T["txt_band_un"]
        x = 1
        for c in GEN_LETTERS:
            w = glyph_w(F7, c) + 1
            for r in range(7):
                rect(a, x, y + r, w, 1, rows[4 + r])
            if GBA():
                pat(a, x + 1, y, F7[c], {"#": T["band_shadow"] if lit else T["band_shadow_un"]})
            pat(a, x, y, F7[c], {"#": col})
            x += w + 1
        assert x <= 194, x
    return a


# ------------------------------------------------------------------------------------------
# genex (18 colours; genex_wacup.py completes the sheet), viscolor, pledit.txt, readme
# ------------------------------------------------------------------------------------------


def genex_colours():
    b = band_rows(14, True)
    return [
        T["body"],            # item background
        T["ink"],             # item text
        T["body"],            # window background
        T["ink"],             # button text
        T["ink"],             # window text
        T["ink2"],            # dividers
        T["sel"],             # selection bar
        b[6],                 # list header background
        T["txt_band"],        # list header text
        b[0] if GBA() else T["txt_band_un"],   # header frame light
        b[-1] if GBA() else T["line"],          # header frame dark
        T["sel"],             # header pressed
        T["body"],            # header dead area
        T["btn_face"],        # scrollbar
        T["btnp_face"],       # scrollbar 2
        T["sel"],             # scrollbar pressed
        T["ink2"],            # scrollbar pressed 2
        T["body"],            # scrollbar dead area
    ]


def make_genex():
    a = new(256, 64)
    for i, c in enumerate(genex_colours()):
        px(a, 48 + 2 * i, 0, c)
    button(a, 0, 1, 47, 15, False)
    button(a, 0, 16, 47, 15, True)
    return a


def viscolor():
    bars = T["vis_bars"]
    ink, ink2 = T["ink"], T["ink2"]
    return ([(T["panel_l"], "background"), (T["vis_dots"], "dots")]
            + [(bars[i], f"spectrum {i + 1}") for i in range(16)]
            + [(ink, "oscilloscope 1"), (ink, "oscilloscope 2"), (ink2, "oscilloscope 3"),
               (ink2, "oscilloscope 4"), (ink2, "oscilloscope 5"), (T["vis_peak"], "peaks")])


def hexs(c):
    return "#%02X%02X%02X" % tuple(c)


def write_text_files():
    with open(os.path.join(OUT, "viscolor.txt"), "w", newline="\r\n") as f:
        for (r, g, b), note in viscolor():
            f.write(f"{r},{g},{b}, // {note}\n")
    with open(os.path.join(OUT, "pledit.txt"), "w", newline="\r\n") as f:
        f.write(f"[Text]\nNormal={hexs(T['normal'])}\nCurrent={hexs(T['cur'])}\nNormalBG={hexs(T['body'])}\n"
                f"SelectedBG={hexs(T['sel'])}\nMbBG={hexs(T['body'])}\nMbFG={hexs(T['normal'])}\nFont=Arial\n")
    with open(os.path.join(OUT, "readme.txt"), "w", newline="\r\n", encoding="utf-8") as f:
        f.write(
            f"{T['name']} — a skin in the style of Pokémon {T['games']}.\n"
            f"Pokémon and its sprites © Nintendo / Creatures / GAME FREAK.\n\n"
            f"A classic (Winamp 2.x format) skin, generated by a script (gen_skin.py).\n"
            + ("Colours through Gambatte's Game Boy Color LCD colour correction (gbcToRgb32,\n"
               "libgambatte, GPLv2, github.com/sinamas/gambatte), as the real screen showed them.\n"
               if T.get("lcd") else "")
        )


# ------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------

SHEETS = {}


def build():
    SHEETS.clear()
    OCC.clear()
    sheets = {
        "main.bmp": make_main(),
        "titlebar.bmp": make_titlebar(),
        "cbuttons.bmp": make_cbuttons(),
        "shufrep.bmp": make_shufrep(),
        "posbar.bmp": make_posbar(),
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
    return names, wsz


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
    # title: text.bmp's space across the box, then the title in TrueType in text.bmp's ink
    for x in range(0, 154, 5):
        blit(img, S["text"], (150, 0, min(5, 154 - x), 6), 111 + x, 24)
    f = ImageFont.truetype(LIBERATION, 11)
    tmp = img.crop((111, 22, 265, 36))
    ImageDraw.Draw(tmp).text((0, 7), state["title"], fill=text_ink(), font=f, anchor="lm")
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
    d.rectangle((lx, 20, lx + lw - 1, h - 39), fill=T["body"])
    f = ImageFont.truetype(LIBERATION, 10)
    for i, (txt, dur) in enumerate(rows):
        y = 23 + i * 15
        if y + 15 > h - 38:
            break
        if i == 2:
            d.rectangle((lx, y, lx + lw - 1, y + 14), fill=T["sel"])
        col = T["cur"] if i == 1 else T["normal"]
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
    c0, c1 = np.array(T["panel_l"], np.float32), np.array(T["ink2"], np.float32)
    col = c0 + (c1 - c0) * arr[..., :1]
    img.paste(Image.fromarray(col.astype(np.uint8)), (11, 20))
    return img


def preview():
    rows = [("Pallet Town Theme", "1:02"), ("Route 1", "1:07"), ("Pokemon Center", "1:15"),
            ("Battle! (Wild Pokemon)", "1:48"), ("Viridian Forest", "2:01"), ("Pewter City", "1:30"),
            ("Mt. Moon", "1:41"), ("Cerulean City", "1:12"), ("Bicycle", "1:33"), ("Lavender Town", "1:56"),
            ("Ending", "3:21")]
    bars = [12, 15, 14, 11, 13, 10, 9, 11, 8, 7, 9, 6, 5, 6, 4, 3, 4, 2, 3]
    A = dict(pressed=None, eq=True, pl=True, clutter="AV", shuffle=True, repeat=False, playing=True, stereo=True,
             pos=0.38, seek=False, volume=72, vdrag=False, balance=0, time=207, remaining=False,
             title="Junichi Masuda - Pokemon Theme (Radio)", bars=bars)
    B = dict(pressed="play", eq=False, pl=True, clutter="", shuffle=False, repeat=True, playing=False, stereo=False,
             pos=0.8, seek=True, volume=15, vdrag=True, balance=-60, time=95, remaining=True,
             title="Paused: Lavender Town (Live)", bars=[3, 2, 4, 1, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
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
    out = Image.new("RGB", (275 * 2 + gap * 3, cols[0].height + gap * 2), (60, 60, 64))
    out.paste(cols[0], (gap, gap))
    out.paste(cols[1], (275 + 2 * gap, gap))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, f"preview-{T['key']}.png"))


# ------------------------------------------------------------------------------------------
# Checks
# ------------------------------------------------------------------------------------------

MAIN_CONTROLS = [  # x, y, w, h of everything the app draws over main.bmp
    (0, 0, 275, 14), (10, 22, 8, 43), (24, 28, 76, 11), (24, 43, 76, 16), (111, 22, 154, 14),
    (111, 43, 15, 6), (156, 43, 10, 6), (212, 41, 54, 12), (107, 57, 68, 13), (177, 57, 38, 13),
    (219, 58, 46, 12), (16, 72, 248, 10), (16, 88, 114, 18), (136, 89, 22, 16), (164, 89, 74, 15),
]
EQ_CONTROLS = [(0, 0, 275, 14), (14, 18, 58, 12), (217, 18, 44, 12), (85, 16, 115, 21), (21, 38, 14, 63),
               (16, 104, 260, 8)] + [(78 + 18 * i, 38, 14, 63) for i in range(10)]


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
    m = np.asarray(S["main"])
    assert (m[22:35, 111:265] == np.array(T["panel"], np.uint8)).all(), "title box not flat"
    ink = text_ink()
    assert sum(abs(a - b) for a, b in zip(ink, T["panel"])) > 200, ("title ink vs box", ink)
    # sprites: zero overlap with anything drawn over them
    for sheet, controls in (("main", MAIN_CONTROLS), ("eqmain", EQ_CONTROLS)):
        for (x, y, w, h, al) in OCC.get(sheet, []):
            occ = np.zeros((116, 275), bool)
            occ[y:y + h, x:x + w] = al
            for cx, cy, cw, ch in controls:
                n = int(occ[cy:cy + ch, cx:cx + cw].sum())
                assert n == 0, (sheet, "sprite overlaps", (cx, cy, cw, ch), n)
            assert x >= 3 and x + w <= 272 and y + h <= 112, (sheet, "sprite on the frame", x, y, w, h)
    for (x, y, w, h, al) in OCC.get("pledit", []):
        assert x + w <= 26 + 100 - 26 + 100 and y >= 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        for k, v in THEMES.items():
            print(f"{k}\t{v['wsz']}.wsz\tPokémon {v['games']}")
        sys.exit(0)
    keys = args or list(THEMES)
    for key in keys:
        if key not in THEMES:
            sys.exit(f"unknown theme {key!r}; one of {', '.join(THEMES)}")
        setup_theme(key)
        names, wsz = build()
        check()
        preview()
        print(f"{key}: {T['wsz']}.wsz, preview-{key}.png, out/{key}/ ({len(names)} files)")
