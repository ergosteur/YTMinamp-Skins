# Dell OptiPlex: the OptiPlex 9010 desktop's front panel (2012), with a PowerEdge-style LCD

One skin from one generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`, with the theme
scaffolding and app-faithful title preview of `../payphone/gen_skin.py`, keeping Ember's sheet
layouts), a theme each. The one real mark is the Dell wordmark (the tilted-E "DELL", without its
circle), used once, on the aluminium badge in the About spot. `gen_skin.py` rasterises it at build
time from `source/dell-logo.svg` (the circle's group is dropped from a copy in `out/scratch/`,
then rendered with `rsvg-convert` at 1200 px, Lanczos-scaled down and painted through its mask).
Everything else is drawn by the script: gradients and grain for the satin bezel, a supersampled
signed-distance mesh of stadium holes, rectangles and bevels for the keys, ports and jacks,
Ember's pixel fonts for small print and text.bmp, and Open Sans (SIL OFL) Semibold Italic / Bold
Italic for the bezel's italic model print and the LCD's time digits.

```sh
/usr/bin/python3 -I gen_skin.py                   # all of them
/usr/bin/python3 -I gen_skin.py optiplex-9010     # some (<theme>, <theme>, ...)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Dell-OptiPlex-9010.wsz` and `preview-optiplex-9010.png` here; sheets in
`out/<theme>/`, 4x crops in `out/scratch/` (`out/` is ignored). Deterministic. Each .wsz is
finished by `skins/genex_wacup.py`.

## Themes

- **Dell OptiPlex 9010** (`optiplex-9010`, 2012): every window is satin black bezel (#2C2D32
  fading to #1E1F23) above and the silver steel mesh below (lands #D6D8DC to #ACAFB4, holes
  #16161A, staggered rows of 4x2 stadium holes, a lit lower lip and shaded upper lip on each).
  Main window: the titlebar prints "OptiPlex 9010" in white italic (as Dell prints model names
  on the bezel), the options button is the small round ID button, and minimize/shade/close are
  small dark-grey keys. The displays are a PowerEdge-style blue-backlit LCD in black glass: a
  lit field (#2F4FD8, sampled from the photos) with white text (#FAFBFF), italic time digits,
  white analyzer bars and a "KBPS / KHZ" info row; MONO/STEREO show the selected item as the
  LCD does, a pale box (#C4D2FA) with the text inverted into it, the other dimmed (#809AEE).
  The clutterbar is a column of the dark-grey keys beside the LCD (pressed = blue letter).
  Under the LCD: the two audio jacks and the drive light, the volume and balance as small LCD
  bars lighting segment by segment, and EQ/PL as grey keys with a check that lights when on.
  The slim optical drive crosses the bezel; its tray seam is the seek bar and the thumb is the
  light-blue "EST" pull-out tag (#96B2D6). On the mesh: a black recess with the transport as
  the PowerEdge's < check > keys (previous <, play check, pause, stop as the power symbol in
  green #60D66E, next >), the eject key, a second recess with shuffle and repeat as front USB
  ports (the tongue turns USB 3.0 blue #1666D6 and the tridents light when on), and the brushed
  aluminium DELL badge (white wordmark in relief) in the About spot. The EQ: bezel strip with
  "Equalizer", ON/AUTO keys with checks, the graph as a small LCD (white curve), and the mesh
  below with black slots whose LCD columns light up to each value, the dB scale and band labels
  on black plates. Playlist and album-art frames: a black bezel band ("Playlist" in white
  italic), black bezel sides, and a mesh foot with the keys and the timers' small LCDs on black
  plates. Playlist: #ACBEFA on #203ABE (the lit field), #FFFFFF current, #0E1A68 selection.
  Font: Arial.

## Limits

- The mesh is 2D, so it only goes where pieces don't tile vertically: the main window and EQ
  (single bitmaps) and the playlist/album-art feet. Its hole pitch is 6.25 px (4 holes per
  25 px), drawn supersampled, so the 25 px foot tiles (always placed on the 25 px grid) join
  seamlessly; the trade-off is that holes alternate slightly in sharpness. The playlist and
  album-art sides are plain bezel (vertical-only variation).
- The OptiPlex has no display; the LCD is borrowed from the PowerEdge servers' front panel (its
  < check > keys, EST tag and power symbol too), as asked. The model name in the titlebar is set
  in Open Sans italic, close to but not Dell's own face. The real OptiPlex print is small caps
  "OPTIPLEX 9010"; the italic follows the PowerEdge bezel print.
- At 32x19 px the badge's wordmark is about 8 px tall: the tilted E reads, but only just.
- The balance slider's frames can't show which side (format limit): it lights outward from the
  centre.
- text.bmp's background is the lit field (the space cell, so the title box is the field), and
  its ink is white #FAFBFF (the app's TrueType title colour); nothing in text.bmp is inverted,
  so the ink pick is unambiguous.

## Sources

- `source/optiplex-9010-family.png`: Dell's product shot of the four OptiPlex 9010 form
  factors (bezel, drive, ports, mesh, badge, print). Reference only.
- `source/poweredge-lcd.png`, `source/poweredge-r330-lcd.png`, `source/poweredge-t320-front.png`:
  PowerEdge front panels (the blue-backlit LCD, the < check > keys, EST tag, power button, USB
  trident). Reference only; the LCD blue (#2F4FD8) is sampled from them.
- `source/dell-logo.svg`: the Dell logo (blue circle and tilted-E wordmark). The wordmark alone
  is rendered at build time into the About badge; nothing else is composited.
- Dell logo (c) Dell Inc. OptiPlex and PowerEdge are names of Dell Inc.
