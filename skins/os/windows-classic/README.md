# Windows Classic: Windows 95, 98 and 2000

Three classic skins from one procedural generator (`gen_skin.py`), a theme per version. The one
mark used is the era's Windows flag, as 13x10 pixel art in the emblem spot (bottom right of the
main window), in the shape Windows' own small renderings use and coloured from the logo files.
Everything else is drawn by the script, with hand-made fonts: a bold caption face (titles and
gen.bmp's A-Z), a small UI face for labels, a 4x5 face for text.bmp. The title-bar icon (the
options button) is a small compact disc of its own.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py win2000        # some (win95, win98, win2000)
```

Outputs: `Windows-95.wsz`, `Windows-98.wsz`, `Windows-2000.wsz` and `preview-<theme>.png` here
(active windows on the left, inactive and pressed states on the right, 2x); sheets in
`out/<theme>/` (`out/` is ignored), scratch (the rasterised logos, `compare.png` with the three
themes' active windows side by side) in `out/scratch/`. Deterministic.

## Themes

All three share the Windows Classic widgets:

- Bevels follow DrawEdge: window frames light-then-white outside-in; push buttons white
  outermost; pressed buttons a black outline round a grey one with the glyph 1px down-right;
  latched toggles (shuffle, repeat, EQ, PL, clutterbar letters) sunken with a white dither.
- The marquee title is drawn by the app in pledit.txt's font and Normal colour, so the title box
  and the kbps/kHz/mono/stereo row are white edit fields with black text; the time and analyzer
  sit in a black, CD-player style LED panel (green seven-segment digits).
- Trackbars: a 4px sunken groove, pointed raised thumbs (dithered while dragged), tick marks.
  The thumbs cover the groove completely, so their sprites need no groove behind them; the seek
  bar's 29px sprite paints the open groove either side of its 11px pointer, with the groove's
  ends drawn in main.bmp.
- EQ ON/AUTO are check boxes; PRESETS a push button; the graph a black LED readout.
- Playlist and album-art title bars are solid (their tiles repeat, so no gradient); main and EQ
  get the version's gradient.
- Highlight #ffffff and shadow #808080 throughout. Playlist font: `Font=Arial` (the field takes
  one name; the app appends Arial anyway).

What differs between the versions:

| | face | 3D light / dark shadow | active caption | inactive caption | list selection |
|---|---|---|---|---|---|
| 95 | `#c0c0c0` | `#c0c0c0` / `#000000` | solid `#000080` | solid `#808080` | `#c0c0e0` |
| 98 | `#c0c0c0` | `#dfdfdf` / `#000000` | `#000080` to `#1084d0` | `#808080` to `#c0c0c0` | `#c0c0e0` |
| 2000 | `#d4d0c8` | `#d4d0c8` / `#404040` | `#0a246a` to `#a6caf0` | `#808080` to `#c0c0c0` | `#a6caf0` |

- **Windows 95** (`win95`): solid captions; inactive caption text #c0c0c0.
- **Windows 98** (`win98`): gradient captions; inactive caption text #c0c0c0.
- **Windows 2000** (`win2000`): the warmer #d4d0c8 face and gradient captions; inactive caption
  text #d4d0c8. Its flag is brighter, from its logo file's own colours.

## Limits

- The playlist's scrollbar track is a flat white/face blend: a 1px dither can't tile across the
  29px side tiles.
- The generator takes theme names only; there is no `--list`.

## Sources

- Windows 95 logo: https://commons.wikimedia.org/wiki/File:Microsoft_Windows_95_logo_with_wordmark.svg
  in `source/logo-win95/logo.svg`.
- Windows 98 logo: https://commons.wikimedia.org/wiki/File:Microsoft_Windows_98_logo_with_wordmark.svg
  in `source/logo-win98/logo.svg`.
- Windows 2000 logo: https://commons.wikimedia.org/wiki/File:Windows_2000_logo_with_wordmark.png
  in `source/logo-win2000/logo.png`.
- Each is reference for the colours of the hand-drawn 13x10 flag in its skin's emblem spot.
- Windows logo (c) Microsoft Corporation.
