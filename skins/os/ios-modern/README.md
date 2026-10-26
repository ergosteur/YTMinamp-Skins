# iOS Modern: iOS 7 (flat) and iOS 26 (Liquid Glass)

Three classic skins from one procedural generator (`gen_skin.py`, forked from
`skins/ember/gen_skin.py`: same sheets, layouts and preview logic), a theme each. The one mark
used is the Apple logo in the About spot, rasterised at build time with `rsvg-convert`. Everything
else is drawn by the script: shapes are anti-aliased signed distance fields (rounded rects,
circles, capsules); digits and transport glyphs are vector strokes rendered at 8x and
box-filtered; labels and titles use a hand-made mixed-case pixel sans, text.bmp and gen.bmp
letters a 5-row caps font.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py ios26-v2       # some (ios7, ios26, ios26-v2)
```

Outputs: `iOS7.wsz`, `iOS26.wsz`, `iOS26-v2.wsz` and `preview-<theme>.png` here; sheets in
`out/<theme>/` (`out/` is ignored, with `out/scratch/` for the rasterised logo). Deterministic:
two runs give identical files.

## Themes

Each window has a base (background plus static panels); every state sprite is a crop of that base
at its real position with its content drawn on top, so sprites sit seamlessly on glass and
wallpaper. Anything that moves (seek, volume, balance and EQ thumbs) or comes from text.bmp sits on
a uniform colour, since its sprite is the same at every position.

- **iOS 7** (`ios7`, 2013, flat): white body, #f7f7f7 bars with #c8c7cc hairlines, thin Helvetica
  Neue Light-like digits, outline transport glyphs in #007aff with no bezels (pressed = faded
  tint), the iOS 7 slider (2px track, blue fill, white round thumb with a soft shadow), a red
  playhead for the seek bar (the iOS 7 Music scrubber), the green switch for EQ On, filled-tint
  toggles for shuffle/repeat/EQ/PL.
- **iOS 26** (`ios26`, 2025, Liquid Glass): an invented vivid wallpaper (a normalised mix of soft
  colour blobs, continuous from the main window into the EQ) under frosted display panels
  (uniform inside, for legibility) and clear glass capsules (blurred backdrop, lightened, with an
  edge refraction band) for the transport, shuffle/repeat and About; every glass shape has a soft
  shadow, a bright specular rim top-left and a fainter one bottom-right. Thick rounded tracks;
  white pill thumbs that turn into a clear glass lens while dragged; a pill-knob switch; system
  blue #0088ff. Playlist and album-art frames (tiled, so uniform) are a lavender frosted glass.
- **iOS 26 v2** (`ios26-v2`, cohesion first, after feedback that `ios26` looked disjointed in the
  app: wallpaper main/EQ next to flat lavender playlist/gen frames, mismatched titlebars, a colour
  jump at the main/EQ join): no wallpaper. Every window's chrome is the same frosted, uniform
  #eaecf5 under the same 14-row title band (white easing into the chrome, vertical-only, so the
  tiled playlist and gen pieces repeat it exactly), with the same caps title lettering on rows
  4..10 (the gen.bmp letters are drawn in the same font), the same glass-circle window buttons,
  the same inactive state and the same edges (white top/left, grey bottom/right). Glass capsules,
  rims and shadows as in `ios26`; colour comes only from one accent, system blue #0088ff (fills,
  lit toggles, the EQ switch, current track, selection, visualizer). Its preview puts a tall
  gen-framed lyrics window (pledit colours inside) beside the docked stack, the way the app shows
  it.

## Limits

- numbers.bmp's thin digit 2 has no straight middle row, so a player that takes the minus sign
  from numbers.bmp (rather than nums_ex.bmp, which all of them have) shows a faint one.
- No region.txt: the app only shapes the main window, and docked panels stay rectangular.
- The generator takes theme names only; there is no `--list`.

## Sources

- Apple logo: https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg (page:
  https://commons.wikimedia.org/wiki/File:Apple_logo_black.svg, Wikimedia Commons) in
  `source/logo-apple/apple-logo.svg`, rasterised with `rsvg-convert` and composited once into the
  About spot.
- Apple logo (c) Apple Inc.
