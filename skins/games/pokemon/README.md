# Pokemon: the handheld games' pixel UI, Gen 1 to Gen 3

Five classic skins from one procedural generator (`gen_skin.py`, built on the sheet layouts and
preview renderer of `skins/ember/gen_skin.py`), a theme each, in the style of the Pokemon handheld
games' in-game pixel UI. The real marks used are the games' own sprites, pasted unscaled in the
EQ's Pokedex box, the About spot and the playlist title. Everything else is drawn in whole pixels
(no smoothing) by the script, including the fonts: a 5x7 menu font (titles, gen.bmp letters), a
4x5 font for text.bmp and a 3x5 one for labels (Yellow's title bands use the games' own font
instead, read from its tile sheet). The main titlebar has a small "POKéMON" wordmark
(outlined letters in the logo's manner), drawn, not the real logo.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py gen2           # some (gen1 .. gen3, pokemon-yellow[-overworld])
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Pokemon-Gen1.wsz`, `Pokemon-Gen2.wsz`, `Pokemon-Gen3.wsz`, `Pokemon-Yellow.wsz`,
`Pokemon-Yellow-Overworld.wsz` and
`preview-<theme>.png`
here; sheets in `out/<theme>/` (`out/` is ignored). Deterministic. Each .wsz is finished by
`skins/genex_wacup.py`.

## Themes

All five share:

- Every window is a title band on top (focused/unfocused), then the window material with the
  frame down the sides and along the bottom. The band carries the menu cursor: a filled triangle
  when focused, the hollow one (the games' "last choice" cursor) when not.
- Volume is the battle **HP bar** (green above half, yellow, red below a fifth); balance is the
  **EXP bar** filling out from the centre; the EQ sliders are vertical HP bars. Every thumb is a
  Poke Ball. Shuffle/repeat/EQ/PL are START-menu-style words with the cursor when on.
- The EQ's dB labels are dropped for a **Pokedex entry**: the sprite in a box with its number.

- **Gen 1** (`gen1`, Red/Blue/Yellow, Game Boy): strict DMG four-shade green palette (#9BBC0F,
  #8BAC0F, #306230, #0F380F), not the Super Game Boy tint, so the HP bars are one shade as on
  DMG. The double-line text box (outer line, gap, inner line two pixels thick along the top and
  bottom, rounded corners) is copied in shape from the games' frame tiles. Darkest-green title
  bands. Sprites: Pikachu (Red/Blue front, NO.025) in the EQ, the Poke Ball item sprite in the
  About spot, Pikachu's Yellow overworld sprite in the playlist title.
- **Gen 2** (`gen2`, Gold/Silver/Crystal, Game Boy Color): the PokeGear radio card. Black
  PokeGear top bar, the PokeGear's pale screen colour (#E7FFA5) as the material, white text
  boxes, grey icon tiles for the transport (pressed: dark grey), the seek bar as the radio's grey
  TUNING dial with its darker blocks. GBC HP colours (green/yellow/red) and the blue EXP bar from
  pokecrystal's palettes, the cream bar background too. Sprites: Pichu (Crystal front, its
  palette, NO.172) in the EQ, Togepi (Crystal front) in the About spot, Pikachu's party icon in
  Crystal's red overworld palette (day) in the playlist title.
- **Gen 3** (`gen3`, Ruby/Sapphire/Emerald, GBA): the PokeNav's mint header bands (white lettering
  with a dark shadow) and mint/teal window frame; the title display is the rounded teal message
  box, the time display the cream battle healthbox with its olive outline. GBA HP bar colours
  (two-tone), dark track, the blue EXP bar on cream. Text has the GBA games' drop shadow.
  Sprites: Torchic (Emerald front, `normal.pal`, NO.255) in the EQ, Treecko's party icon in the
  About spot, Mudkip's party icon in the playlist title.
- **Yellow** (`pokemon-yellow`, Yellow Version: Special Pikachu Edition, played on a Game Boy
  Color): Yellow is GBC-enhanced, picking a four-colour palette per scene and per Pokemon; the
  colours are its CGB ones (`CGBBasePalettes`, raw 5-bit values, no LCD colour correction), not
  the SGB set. The material is the yellow every Pikachu palette shares (#FFFF00: colour 1 of
  `PAL_YELLOWMON`, `PAL_MEWMON` and the HP bars), with the Gen 1 double-line text box in white with
  near-black lines (colour 3, #191919). Title bands in the title-screen logo's blues (`PAL_LOGO2`:
  #0000AD focused, #3A3ACE unfocused), the drawn POKéMON wordmark in its yellow with the blue
  outline, all band titles in the games' own 8 px font (the font tile sheet, its ▶/▷ cursors
  included); gen.bmp's letters stay the 5x7 menu font, as 26 letters at the real font's width
  don't fit the sheet. Volume is the battle HP bar in `PAL_GREENBAR`/`YELLOWBAR`/`REDBAR` (green,
  orange, red fill on a white track); balance fills out in the logo blue (Gen 1 has no EXP bar).
  Poke Ball thumbs in `PAL_MEWMON`'s red, labels in the brown of Yellow's Pikachu portrait
  (`PAL_PIKACHU_PORTRAIT`), Current in the logo blue. Sprites, Yellow's own: Pikachu's Yellow
  front pic in its battle palette `PAL_YELLOWMON` (white, yellow, orange, black; BGP %11100100) in
  the EQ's Pokedex box (NO.025); the About spot shows the player with Pikachu following, both
  walking left, and the playlist title Pikachu's side frame mirrored to face the title. Overworld
  sprites on the GBC take the map's palette converted through OBP0 (%11010000: the sprite's light
  grey shows white, its dark grey as the palette's colour 1); these use Saffron City's
  (`PAL_SAFFRON`), whose colour 1 is yellow: Pikachu walks white with yellow touches, as there.
- **Yellow Overworld** (`pokemon-yellow-overworld`): the same Yellow, calmer, with yellow as an
  accent (the wordmark, the Pikachu pic, the HP bar's middle tier) instead of the body, and every
  colour (tiles, sprites, bands, frame, selection, HP bars, the Pokedex box) passed through
  **Gambatte's GBC LCD colour correction** (libgambatte `gbcToRgb32`: from the 5-bit values,
  R = (13r + 2g + b) >> 1, G = (3g + b) << 1, B = (3r + 2g + 11b) >> 1, so white is #F8F8F8), as
  emulators do to match the real screen. Key colours after it: white #F8F8F8, near-black #181818,
  grass green #89C24D (bands, frame stripe, selection, pressed buttons), light blue #6EC8D2
  (unfocused bands, lettered in the logo's dark blue #08225D), logo blue #415C9B (Current, the
  wordmark's outline), yellow #E8BA4D (the main titlebar), label brown #832C29, HP bars #1FBA1F /
  #DB6C40 / #C9002E. Behind the
  main window and the EQ, a bit of Route 1 from the overworld tileset in its GBC palette
  (`PAL_ROUTE`: white, grass green, light blue, black, corrected as above; BGP %11100100), 8x8 tiles
  unscaled: grass, flower and tall-grass tiles, the round 16x16 tree wherever a clear 16x16 cell
  fits, and the white path (with its speck tile) under everything the app draws (each control's
  rect plus 1 px), since those sprites' backgrounds are that white; the displays sit in the usual
  double-line boxes over it. The About spot is kept to plain grass, the player and Pikachu
  standing on it in the Route palette through OBP0 (white with green touches, as on Route 1).
  The other Yellow skin keeps the raw palette values.
  The tiled windows can't carry the map: their frame's middle column (between the two black
  lines) is the grass green on every window, the list and gen areas the text box's white, the
  title bands grass green with black lettering and a black edge row (unfocused: light blue with
  the logo's dark blue), except the main window's focused titlebar, which is Yellow's yellow
  (corrected, #E8BA4D) with the wordmark in white outlined in the logo blue. Selection is the
  grass green.

## Limits

- The playlist can't show a cursor on the current row (the app draws rows itself): Current is a
  colour only.

## Sources

Downloads are untrusted data, opened with Pillow only. All are from the pret disassembly projects
on GitHub (raw.githubusercontent.com/pret/...), the games' own graphics. Sprite exteriors are made
transparent (the white connected to the sprite's edge), first frame only, unscaled, and pasted
once each:

- Gen 1: `pokered/gfx/pokemon/front/pikachu.png` (EQ), `pokered/gfx/sprites/poke_ball.png` (About
  spot), `pokeyellow/gfx/sprites/pikachu.png` (playlist title); in `source/sprites-gen1/`.
- Gen 2: `pokecrystal/gfx/pokemon/pichu/front.png` (EQ), `pokecrystal/gfx/pokemon/togepi/front.png`
  (About spot), `pokecrystal/gfx/icons/pikachu.png` (playlist title); in `source/sprites-gen2/`.
- Gen 3: `pokeemerald/graphics/pokemon/torchic/` (EQ),
  `pokeemerald/graphics/pokemon/treecko/icon.png` (About spot),
  `pokeemerald/graphics/pokemon/mudkip/icon.png` (playlist title); in `source/sprites-gen3/`.
- Yellow Overworld: `gfx/tilesets/overworld.png` (grass $2C, flowers $03, tall grass $52, tree
  $40/$41/$50/$51, path $23/$39), with `gfx/blocksets/overworld.bst` used to find those tiles in
  the game's own blocks; `gfx/tilesets/forest.png` was looked at and not used. Same folder.
- Yellow: in `source/yellow/`, from `pokeyellow` (raw.githubusercontent.com/pret/pokeyellow/...):
  `gfx/pokemon/front/pikachu.png` (EQ), `gfx/sprites/red.png` and `gfx/sprites/pikachu.png`
  (About spot, playlist title), `gfx/font/font.png` (the band titles' font, read as tiles). The
  palettes are typed in from `data/sgb/sgb_palettes.asm` (`CGBBasePalettes`), chosen as the game
  does by `data/pokemon/palettes.asm`, `data/sgb/sgb_packets.asm` and `engine/gfx/palettes.asm`
  (all kept there); the OBP0 value is from `home/palettes.asm` (`GBPalNormal`). The other files
  there (frame and HUD tiles, Pokedex tiles, title logo, Poke Ball) are reference only.
- `source/ref-gen*/` holds UI graphics from the same repositories used only as reference for
  shapes and colours (frame tiles, HP/EXP bars and palettes, PokeGear, battle healthbox, message
  box, PokeNav header); nothing from there is pasted into the skins. Unused downloads (other
  starters) stay in `source/sprites-gen*/`.
- Yellow Overworld's colours: Gambatte's Game Boy Color LCD colour correction, the `gbcToRgb32`
  formula in libgambatte's `video.cpp` (Gambatte by sinamas, GPLv2,
  https://github.com/sinamas/gambatte), reimplemented in `gen_skin.py` (`gambatte()`); no code or
  files taken from it.
- Pokemon and its sprites (c) Nintendo / Creatures / GAME FREAK.
