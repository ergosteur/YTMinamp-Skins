# Mobile Classic: BlackBerry OS 4.5, BlackBerry OS 5, BlackBerry OS 6, BlackBerry 10, Windows Mobile 6

Five classic skins from one procedural generator (`gen_skin.py`, based on
`skins/ember/gen_skin.py` and keeping its sheet layouts), a theme each. The marks used are the
BlackBerry pearls, once per BlackBerry skin in the About spot, and the 2002-2012 Windows flag,
once, in the Windows Mobile main titlebar (as its Start flag). Everything else is drawn by the
script. Titles and labels are anti-aliased TrueType (Open Sans for BlackBerry OS 4.5, Droid Sans
for BlackBerry OS 5/6, Noto Sans
for BB10, Liberation Sans for Windows Mobile), as the phones drew them; text.bmp and the smallest
labels are hand-made pixel fonts.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py bb10 wm6       # some (bb45, bb5, bb6, bb10, wm6)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `BlackBerry-OS-4.5.wsz`, `BlackBerry-OS-5.wsz`, `BlackBerry-OS-6.wsz`, `BlackBerry-10.wsz`,
`Windows-Mobile-6.wsz` and `preview-<theme>.png` here (active windows left, inactive and pressed
states right, 2x); sheets in `out/<theme>/` (`out/` is ignored), rasterised logos and
`compare.png` (all five side by side) in `out/scratch/`. Deterministic (fixed zip timestamps, no
randomness). Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

gen.bmp's A-Z are drawn in the bold face on the bar's own rows. text.bmp's ink is the display
text colour (white, or black on BB OS 4.5's and 6's white displays), so the app's TrueType title takes
it; the title box is flat panel colour, the same as text.bmp's space.

- **BlackBerry OS 4.5** (`bb45`, 2008, the Curve 8300/8320 era's stock Zen/Today look, before
  the Bold's Precision theme): the deep blue wallpaper as the body (#26508f to #0c1e45), a navy
  title band with a smooth gradient (#5a7cba to #1a3368, no split gloss) and white bold text, the
  4.x status corner (clock, signal bars, battery) in the titlebar, white list-screen displays with
  black text, the flat royal-blue trackball focus box with a light rim (#5486dc to #1f4aa6,
  #cfdcf5 edge) for pressed buttons and lit toggles, light rounded dialog buttons for EQ/PL and
  ON/AUTO/PRESETS, and the Zen home screen's dark icon row right across the bottom holding the
  transport, the pearls in white at its end. Playlist: #000000 on #FFFFFF, #1D4FB0 current,
  #ABC4EF selection (the real selection is navy with white text, which pledit.txt can't do).
  Font: BBAlpha Sans (Open Sans drawn in the bitmaps).
- **BlackBerry OS 5** (`bb5`, the Bold 9000/9700 "Precision" theme): dark glossy charcoal bars
  (split-gloss gradient), black displays, white text, the blue-grey glossy focus bar for pressed
  buttons and lit toggles, the transport in the home screen's dark rounded icon dock, status icons
  (EDGE, signal, battery) in the titlebar. The pearls in silver.
- **BlackBerry OS 6** (`bb6`): lighter and cleaner. White-to-silver app headers with dark text, a
  light body, white displays and lists, the bright blue gradient highlight, and the dark pull-up
  drawer (with its handle tab and chevron) holding the transport; the playlist's bottom bar is the
  same dark drawer. The pearls in white on the drawer.
- **BlackBerry 10** (`bb10`): flat black, #00a8df cyan accents (titlebar underline, track fills,
  current track, on states), the flat dark action bar along the bottom with a cyan bar under a
  pressed action, round white slider handles, Noto Sans standing in for Slate Pro. The pearls in
  white.
- **Windows Mobile 6** (`wm6`): 6.0/6.1 Professional's classic look rather than 6.5's honeycomb
  (the look most people remember, and it suits Winamp's list-and-buttons layout better). The
  glossy blue navigation bar with the Start flag, "Windows Media", signal/speaker/clock; the Today
  screen's blue for the body; the dark soft-key bar holding the transport (with separators and the
  input panel's keyboard icon in the About spot); white list views with blue selection; Liberation
  Sans standing in for Tahoma.

## Limits

- The balance thumb carries a track filled on its left (shared with volume's), so a couple of
  blue pixels show beside it when balance is centred or right.
- BB OS 4.5's colours are from memory of the stock themes' screenshots (no theme files were
  read); Open Sans stands in for BBAlpha Sans.
- pledit.txt names `BBAlpha Sans`, `Slate Pro` and `Tahoma`; where they're missing the app falls
  back to Arial.

## Sources

- BlackBerry pearls: https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/blackberry.svg
  (Simple Icons' copy of the mark) in `source/logo-blackberry/`, rasterised with `rsvg-convert`
  and composited once per BlackBerry skin (four), in the About spot.
- Windows flag (2002-2012):
  https://commons.wikimedia.org/wiki/File:Unofficial_Windows_logo_variant_-_2002%E2%80%932012_(Multicolored).svg
  in `source/logo-windows-flag/`, composited once, in the main titlebar.
- BlackBerry logo (c) BlackBerry Limited.
- Windows logo (c) Microsoft Corporation.
