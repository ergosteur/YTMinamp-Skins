# Windows XP: the Luna Blue theme

One classic skin from a procedural generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`
and keeping its sheet layouts). The one mark used is the Windows flag, in the titlebar icon and the
About spot. Pixel fonts and all other artwork are drawn by the script. It needs Pillow, numpy and
`/usr/bin/rsvg-convert` (which rasterises the flag once into `out/scratch/`).

```sh
/usr/bin/python3 -I gen_skin.py
```

Outputs: `Windows-XP.wsz` and `preview.png` here (main window, EQ, playlist and a gen.bmp frame at
their real positions, 2x); sheets in `out/` (ignored). Deterministic.

## Themes

- **Windows XP** (one theme, Luna Blue): rounded glossy blue captions with white bold titles and
  blue/red-orange caption buttons, the beige dialog face inside a 4px blue frame, XP push buttons,
  white edit-box displays, trackbar sliders with green-rimmed thumbs filling with progress-bar
  green, Luna scrollbar thumbs, a white list view. Playlist: #000000 on #FFFFFF, #0054E3 current,
  #C1D2EE selection. Font: Arial.

## Limits

- None noted.

## Sources

- Windows flag: "File:Unofficial Windows logo variant - 2002-2012 (Multicolored).svg"
  (https://commons.wikimedia.org/wiki/File:Unofficial_Windows_logo_variant_-_2002%E2%80%932012_(Multicolored).svg,
  Wikimedia Commons) in `source/logo-windows-flag/flag-multicolored.svg`, rasterised once and used
  in the titlebar icon and the About spot.
- `source/logo-windows-flag/flag-2d.svg` ("File:Windows 2002 Home logo (2D).svg") was fetched for
  comparison and is unused.
- Windows logo (c) Microsoft.
