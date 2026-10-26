# Pokemon: the handheld games' pixel UI, Gen 1 to Gen 3

Three classic skins from one procedural generator (`gen_skin.py`, built on the sheet layouts and
preview renderer of `skins/ember/gen_skin.py`), a theme each, in the style of the Pokemon handheld
games' in-game pixel UI. The real marks used are the games' own sprites, pasted unscaled in the
EQ's Pokedex box, the About spot and the playlist title. Everything else is drawn in whole pixels
(no smoothing) by the script, including the fonts: a 5x7 menu font (titles, gen.bmp letters), a
4x5 font for text.bmp and a 3x5 one for labels. The main titlebar has a small "POKéMON" wordmark
(outlined letters in the logo's manner), drawn, not the real logo.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py gen2           # some (gen1, gen2, gen3)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Pokemon-Gen1.wsz`, `Pokemon-Gen2.wsz`, `Pokemon-Gen3.wsz` and `preview-<theme>.png`
here; sheets in `out/<theme>/` (`out/` is ignored). Deterministic. Each .wsz is finished by
`skins/genex_wacup.py`.

## Themes

All three share:

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
- `source/ref-gen*/` holds UI graphics from the same repositories used only as reference for
  shapes and colours (frame tiles, HP/EXP bars and palettes, PokeGear, battle healthbox, message
  box, PokeNav header); nothing from there is pasted into the skins. Unused downloads (other
  starters) stay in `source/sprites-gen*/`.
- Pokemon and its sprites (c) Nintendo / Creatures / GAME FREAK.
