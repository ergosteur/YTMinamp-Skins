# Boombox: the Panasonic RX-DS660 portable stereo component CD system

One classic skin from one generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`, whose
sheet layouts it keeps; theme structure and preview after `devices/car-audio/gen_skin.py`). The
only real mark is the Panasonic wordmark, once, in the main titlebar, as lettering rendered from
Liberation Sans Bold (system font); the "RX-DS660" model print is rendered from Noto Sans
ExtraCondensed Bold. Everything else is drawn by the script: matte plastic with a fine grain,
brushed silver, bevels, anti-aliased discs and lines for the knob, Ember's 5-row and 3x5 pixel
fonts, a segment-display alphabet for text.bmp, and the 9x13 seven-segment digits from the VFD generator's history (copied in, recoloured
for an LCD).

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py rx-ds660       # some
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Panasonic-RX-DS660.wsz` and `preview-rx-ds660.png` here; sheets in `out/rx-ds660/`
(`out/` is ignored). Deterministic. Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

- **Panasonic RX-DS660** (`rx-ds660`, c. 1991-92), after the photos of the user's own unit in
  `source/`. Matte charcoal body #2C2E31 with grey silkscreen #AAACAC / #707274, gold print
  #DEAA62, red LEDs #FF4036 (unlit #4E2220), red cap marks #D62E28.
  - Titlebar: the Panasonic wordmark in the grey print at left, a silkscreen rule, gold underlined
    "REMOTE CONTROL" at right; black mini keys. Unfocused: all of it dimmed.
  - Display: a black frame holding two panes of pale olive LCD glass #A6AB92 (a 1px shade along
    the top and left). Left pane: an inverted "CD" tag, the time in near-black #1E221C
    seven-segment digits with unlit segments as a slightly darker tint #999E85, the analyzer.
    Right pane: the title (text.bmp ink #1E221C, so the app's TrueType title is dark on the
    glass), kbps with a "KBPS" legend, kHz, the boxed program calendar 1-12 (a disc of nine
    tracks: 1-9 lit, 10-12 as ghosts), STEREO / MONO as LCD legends. "TIME/FREQUENCY" printed on
    the frame under the left pane.
  - text.bmp: the LCD's own lettering, a segment-display alphabet like the 14-segment
    characters of CD player LCDs, in each 5x6 cell's top-left 4x5 (1px gap column and row):
    full-width bars, side verticals, short diagonals for K, M, N, V, W, X, Y, Z; O/0 and S/5
    share shapes as on the real displays; lowercase maps to uppercase. It shows in the bitmap
    main title (Options > "Use bitmap font for main title display"), kbps / kHz and the playlist
    timers. The preview's left column draws the title with it, the right one in TrueType.
  - Clutterbar: a brushed-silver strip with five small black keys; a lit option is a pressed key
    with a red letter.
  - Volume: a black channel under a tick scale whose ticks turn red up to the level (the unit's red
    VOLUME arrows). Balance: the LEFT / RIGHT tick scale with a red centre tick and L / R. Both
    thumbs and the seek thumb are black slide caps with the red line of the unit's balance and
    EQ caps.
  - Transport: satin black keys (like II/E.P, play/stop, skip) with light grey icons in a recessed
    tray. Eject, SHUFFLE and REPEAT sit on the brushed-silver keypad as slim black keys with dark
    print above; SHUFFLE takes the ATLS key's look (red LED at left), REPEAT gets the same LED so
    its state shows. EQ / PL are black function keys (TAPE / CD style) with a red LED.
  - About spot: the MOTORIZED VOLUME knob in miniature (0-10 tick ring, black knob, red pointer).
    Along the bottom: "PORTABLE STEREO COMPONENT CD SYSTEM" and "RX-DS660".
  - Equalizer: titlebar "GRAPHIC EQUALIZER" on a section line, gold "XBS" at left; ON / AUTO keys
    with red LEDs; the graph on LCD glass in LCD ink; black slots with grey tick scales and black
    caps with a red line; the gold XBS LEVEL wedge with MAX / MIN beside the preamp, then +12 / 0
    / -12.
  - Playlist: the body with a silkscreen rule and "< PLAYLIST >" as the titlebar; the list is a big
    LCD; ADD / REM / SEL / MISC are the tape deck's satin keys in a tray with "< AUTO REVERSE >"
    under them; running time and mini time on LCD glass; the stretch tile between the bottom
    pieces is a band of speaker grille between chrome rules. Album art: the same frame and rule.
  Playlist: #262B22 on #A6AB92, #8A0F08 current (deep red), #8C9678 selection. Font: Arial.
  Visualizer: LCD (dark olive bars on the glass, ghost-tint dots).

## Limits

- No room for the real LCD's TRACK number or its TRACK / PROGRAM labels; the program calendar is
  a fixed decoration (Winamp can't light boxes per track), drawn 6x2 (the unit's is 4x3) to fit
  between kHz and STEREO, and the kHz legend was dropped for it.
- text.bmp has no ghost segments: in every cell they would outnumber the ink, so the app (which
  colours its TrueType title with text.bmp's commonest non-background colour) would draw the
  title in the ghost tint, and the space cell's ghosts would tile across the whole title box under
  it. Tried and dropped.
- The EQ window has Winamp's ten bands and preamp, not the unit's five; the real print reads +10 /
  0 / -10, the skin prints Winamp's +12 / 0 / -12.
- Shuffle has no counterpart on the unit (ATLS is the tape's auto level selector); it borrows the
  ATLS key with its red LED. REPEAT has no LED on the unit; one was added.
- The speakers appear only as the grille band in the playlist's stretch tile (hidden at the
  default 275 px width).
- Colours sampled from daylight photos and evened out; the LCD is shown unlit (no backlight).

## Sources

- `source/*.jpeg`: 8 photos of the user's own unit (front, keypad, display, speaker, top, back).
  Reference only; nothing from them is composited.
- Fonts: Liberation Sans Bold (SIL OFL) for the wordmark and Noto Sans ExtraCondensed Bold (SIL
  OFL) for the model print, both system fonts; Liberation Sans Regular for the preview's title
  and playlist text.
- Panasonic logo (c) Panasonic Holdings Corporation.
