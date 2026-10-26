# Windows 7: the Aero theme

One classic skin from a procedural generator (`gen_skin.py`, starting from Ember's generator
`skins/ember/gen_skin.py`; layouts follow the app's sprite map in `ui/src/lib/skin/render/*.js`
and `crates/skin/src/genex.rs`). The one outside asset is the Windows flag, once, in the About spot
(bottom right of the main window), rasterised at build time. Everything else is drawn by the
script, with captions ("YTMinamp", "Equalizer", "Playlist") in a mixed-case pixel font and gen.bmp's
letters (album art, lyrics, search titles) in capitals of the same font. It needs Pillow, numpy and
`/usr/bin/rsvg-convert`.

```sh
/usr/bin/python3 -I gen_skin.py
```

Outputs: `Windows-7.wsz` and `preview.png` here (main window, EQ, playlist and a gen.bmp frame at
their real positions, 2x); sheets in `out/` (ignored; scratch files in `out/scratch/`).
Deterministic.

## Themes

- **Windows 7** (one theme, Aero): faked Aero glass frames (a #a9c9ec to #6fa0d8 gradient with a
  soft mottle and diagonal light streaks, dark outer edge, light inner highlight), the light
  #f0f0f0 window face, black captions on a white glow, glassy min/shade buttons and the red close
  button, Windows 7 command buttons (lit blue when on), trackbars with a blue-tinted thumb, a green
  progress-bar segment as the seek thumb, a WMP12-style dark glass transport strip with a round
  play button, and a dark glossy display. The main window's title is drawn by the app in
  pledit.txt's Normal colour (#000000), so the title and kbps/kHz rows are white Windows 7 text
  boxes, and text.bmp is dark on white (its space cell is plain white, which the app tiles to blank
  the title box). `region.txt` rounds the main window's top corners. Playlist: a white
  Explorer-style list, #000000 on #FFFFFF, #1E5FB4 current, #CCE8FF selection. Font: Arial.

## Limits

- numbers.bmp holds the same Segoe-like digits as nums_ex.bmp (which the app prefers); its 5x1
  minus/no-minus slices at (20,6)/(9,6) are not a clean dash, as in most non-7-segment skins.

## Sources

- Windows flag (the four-colour 2002-2012 flag):
  https://commons.wikimedia.org/wiki/File:Unofficial_Windows_logo_variant_-_2002%E2%80%932012_(Multicolored).svg
  (Wikimedia Commons) in `source/logo-windows-flag/flag.svg` (with pre-rendered `flag-13.png`,
  `flag-26.png`, `flag-52.png` beside it), rasterised at build time and composited once into the
  About spot.
- Windows logo (c) Microsoft.
