# iPod: the iPod classic (6th/7th generation) and the iPod mini

Twelve classic skins from one procedural generator (`gen_skin.py`, based on the structure of
`skins/ember/gen_skin.py`), a theme each. The one mark used is the Apple logo in the About spot
(bottom right), as on the back of the device; "iPod classic" / "iPod mini" is engraved on the
titlebar in pixel lettering drawn by the script. Everything else is drawn by the script.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py classic-black  # some (classic-silver, classic-black,
                                               #   mini-<colour>, mini-<colour>-metal)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `iPod-classic-Silver.wsz`, `iPod-classic-Black.wsz`, `iPod-mini-<Colour>.wsz`,
`iPod-mini-<Colour>-Metal.wsz` and `preview-<theme>.png` here; sheets in `out/<theme>/` (`out/` is
ignored), scratch files (the rasterised logo) in `out/scratch/`. Deterministic (fixed noise seed,
fixed zip timestamps). Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

All of them share:

- **Body**: anodised aluminium with a fine horizontal brushing.
- **Display**: the main window's two displays are one L-shaped screen behind a black bezel, with
  the iPod's title strip along the top ("NOW PLAYING" and a battery glyph). The clock uses a bold
  sans pixel font instead of seven-segment digits.
- **text.bmp** (the bitmap title, kbps/kHz, the playlist timers): bold pixel lettering in the
  style of Apple's Chicago, the 1st-4th generation iPods' screen face: wide, rounded-square bowls,
  a flat-topped A, a straight-legged R, a boxy S, a slashed zero, 2x2 dots. Glyphs are 4x5 in the
  5x6 cells (row 6 only for descenders); the weight comes from a doubled left stem, since two 2px
  stems don't fit in four columns. The iPod classic uses it too: its own Helvetica Bold can't be
  told apart from a generic bold sans at this size. The previews' right-hand main window draws its
  title from text.bmp (Options > "Use bitmap font for main title display").
- **Transport**: previous/play/pause/stop/next form one strip of the click wheel, with the
  wheel's thin grey labels (previous, play/pause, next) and play as the round centre button.
  Eject is drawn as the wheel's MENU key.
- **Toggles** (shuffle, repeat, EQ, PL, ON, AUTO, PRESETS) are rows of the iPod's menu: a plain
  row when off, the selection bar when on.
- **Bars**: seek, volume, balance and the EQ sliders are iPod progress bars: a screen-coloured
  trough with a selection-coloured fill. The EQ's graph and slider bay are one T-shaped screen.
- **Playlist**: a list in the screen colours. The scroll bar is inside the screen, as on the iPod.

- **iPod classic Silver** (`classic-silver`): light silver body, white wheel. White screen,
  grey-gradient strip, black text, blue accents; the selection bar a blue gradient with white
  text. Playlist: black on white, the playing track in blue, light blue #B9D4F5 selection.
  viscolor: a blue ramp on the white screen.
- **iPod classic Black** (`classic-black`): dark graphite body, black wheel; screen, playlist and
  viscolor as Silver.
- **iPod mini** (`mini-silver`, `mini-gold`, `mini-pink`, `mini-blue`, `mini-green`): the 2nd
  generation's vivid pink, blue and green, its unchanged silver, and the 1st generation's
  champagne gold (gold was dropped in the 2nd). A light grey wheel with labels in the body colour,
  as on the 2nd generation. The pale grey-blue monochrome LCD with dark grey pixels; the selection
  bar an inverted dark bar. Playlist: dark grey text on the LCD background. viscolor: greyscale on
  the LCD.
- **iPod mini Metal** (`mini-<colour>-metal`, the same five colours): the same minis with a body
  that reads as anodised metal. Dense horizontal brushing (noise blurred along x only at several
  streak lengths, per-row strength, a few long glints), a broad specular band desaturated toward
  white with deeper, more saturated falloff toward the bottom and sides, and crisp near-white /
  dark 1px chamfers on the edges. Silver is lifted toward a cool grey. The sheen is computed in
  window coordinates (the main and EQ windows' separate pieces line up). Tiled playlist and gen
  pieces vary only along the axis they don't tile on, and the brushing wraps, so tile joins stay
  seamless. Screens, the wheel and the controls are unchanged.

## Limits

- None noted.

## Sources

- Apple logo: `source/logo-apple/apple-logo.svg`, from Wikimedia Commons,
  https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg, rasterised at build
  time with `/usr/bin/rsvg-convert` and composited once into the About spot.
- Apple logo (c) Apple Inc.
