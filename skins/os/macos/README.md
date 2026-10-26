# macOS: Mac OS 9, Mac OS X Aqua and Snow Leopard

Three classic skins from one procedural generator (`gen_skin.py`, forked from
`skins/ember/gen_skin.py`, which holds the sheet layouts the app reads), a theme each. The one
mark used is the Apple logo, once, in the About spot (13x15 at 253,91 on the main window),
coloured per era. Everything else is drawn by the script: gradients, bevels, anti-aliased shapes
from supersampled masks and hand-made pixel fonts (`REG`, Lucida-like, and `BOLD`,
Chicago/Charcoal-like).

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py aqua           # some (macos9, aqua, snow-leopard)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Mac-OS-9.wsz`, `Mac-OS-X-Aqua.wsz`, `Mac-OS-X-Snow-Leopard.wsz` and
`preview-<theme>.png` here (the windows assembled from the sprites the way the app does, lit on
the left, unfocused and with buttons pressed on the right); sheets in `out/<theme>/` (`out/` is
ignored). Deterministic. The build checks every sheet's size, that gen.bmp's letter rows are found
the way the app scans them, and that text.bmp's space cell is the plain display colour. Each .wsz is
finished by `skins/genex_wacup.py`.

## Themes

All three put the titlebar buttons where Winamp's hit areas are (options at x 6, minimize 244,
shade 254, close 264), so the traffic lights keep their meanings rather than Apple's order: yellow
(minimize), green (shade/zoom), red (close), on the right. The main title scrolls in the app's
TrueType font in text.bmp's ink; text.bmp itself keeps Ember's 5-row cells. kbps/kHz/mono/stereo
are small caps on the display.

- **Mac OS 9** (`macos9`, Platinum): #dddddd bevelled surfaces, the ridged titlebar with its
  boxes, a Chicago/Charcoal-like bold pixel font, square bevel buttons, lavender (#ccccff)
  selection and progress fills, white fields with black text. Close is the plain box, shade the
  collapse box, minimize a box with a bottom line; an inactive window hides them, as OS 9 did.
  The Apple logo in the six-colour stripes.
- **Mac OS X Aqua** (`aqua`, 10.0-10.3): white pinstripes, the striped titlebar with gel traffic
  lights, blue gel transport buttons and slider knobs, clear gel toggles that turn blue when on,
  a striped-blue progress fill, an iTunes-style pale lime LCD. The Apple logo in blue gel.
- **Mac OS X Snow Leopard** (`snow-leopard`, 10.6): the unified grey toolbar gradient, softer
  traffic lights, glossy grey buttons (on: blue glyph), white glossy knobs, the iTunes 9 grey-blue
  display, a source-list blue-grey EQ panel. The Apple logo in glossy graphite.

## Limits

- gen.bmp's titlebar letters are capitals only (the app upper-cases titles), so "ALBUM ART".
- Aqua's pinstripes have a 2px period, so tiles 29 rows tall would break them: the playlist and
  album-art side tiles use the stripes' flat average instead; the EQ's slider bay is a flat group
  box so the thumbs (drawn at any row) don't jar against the stripes.

## Sources

- Apple logo: https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg (Wikimedia
  Commons) in `source/logo-apple/logo.svg`, rasterised at build time with `rsvg-convert` into
  `out/scratch/` and composited once into the About spot.
- Apple logo (c) Apple Inc.
