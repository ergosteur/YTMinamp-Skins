# Windows Modern: Windows 8, 10 and 11

Three classic skins from one procedural generator (`gen_skin.py`, forked from
`skins/ember/gen_skin.py`: same sheets, layouts and preview logic), a theme each. Each carries
that version's Windows logo, rasterised with rsvg-convert, box-filtered and contrast-curved to
stay crisp at 11-13 px. Everything else is drawn by the script. It needs Pillow, numpy and
`/usr/bin/rsvg-convert`.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py win10          # some (win8, win10, win11)
```

Outputs: `Windows-8.wsz`, `Windows-10.wsz`, `Windows-11.wsz` and `preview-<theme>.png` here (main
window, EQ, playlist and a gen.bmp frame, focused and unfocused, 2x); sheets in `out/<theme>/`
(`out/` is ignored). Deterministic: the noise has fixed seeds and the zip entries a fixed date.

## Themes

The outer window corners stay square in all three: the app applies `region.txt` to the main window
only, and the docked EQ/playlist panels are plain rectangles, so a rounded main window would not
meet them cleanly. Windows 11's rounding is on the cards and controls inside. Layout notes kept
from Ember: sprites that sit on the body copy their background from `main.bmp` at their own
position (so the Mica grain lines up); the slider thumbs carry the track under them (volume: filled
left, empty right; balance has no fill, since its frames don't know the direction); the EQ title is
centred so the album-art window's titlebar fill (x 25..40) stays plain; gen.bmp's letters are the
UI font's caps in rows 88/96; text.bmp's space cell is the plain display colour.

- **Windows 8** (`win8`, Metro, the Start screen): a saturated purple body (#4617b4), no window
  chrome, no gradients, shadows or rounding. The time display is a teal live tile; transport,
  shuffle/repeat and EQ/PL are flat tiles in Metro tile colours with white glyphs (a pressed tile
  sinks back); thin lowercase titles; thin tracks with a cyan fill and a solid white rectangle
  thumb; magenta playlist selection. The 2012 logo in white.
- **Windows 10** (`win10`, dark mode, black and blue): #000000 bars and displays, #1f1f1f body, a
  1px #0078d7 window border; MDL2-style 1px line glyphs (hamburger options button), square #2b2b2b
  buttons; #0078d7 is the only accent (slider fill and oblong thumb, lit toggles, the #003e6b
  selection); red #e81123 pressed close. The 2012 logo in #0078d7.
- **Windows 11** (`win11`, light Mica): a #f1f3f8 body with a faint blue vertical tint and grain;
  white rounded cards and buttons with a soft shadow and a darker bottom stroke; an accent-filled
  round play button; Fluent line icons; 3px rounded tracks with #005fb8 fill and circular white
  thumbs with an accent dot (larger when dragged); the #cce4f7 selection. The 2021 logo in
  #0078d4.

## Limits

- Balance has no fill (its frames don't know which side it is on).
- The generator takes theme names only; there is no `--list`.

## Sources

- Windows logo (2012): https://commons.wikimedia.org/wiki/File:Windows_logo_-_2012.svg in
  `source/logo-2012/logo.svg` (Windows 8 and 10), read at build time and composited once.
- Windows logo (2021): https://commons.wikimedia.org/wiki/File:Windows_logo_-_2021.svg in
  `source/logo-2021/logo.svg` (Windows 11), read at build time and composited once.
- Windows logos (c) Microsoft.
