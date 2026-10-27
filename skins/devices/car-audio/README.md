# Car Audio: VW MIB II (two takes), Clarion, Clarion ADX5655z (three takes)

Six classic skins from one generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`, whose
sheet layouts it keeps), a theme each. The real marks used are the Volkswagen roundel (both MIB II
skins) and the Clarion wordmark (the four Clarion skins). Everything else is drawn by the script.
The v2 and ADX themes have their own sheet makers (`V2_MAKERS`, `AX_MAKERS`, and `AXS_MAKERS` for
the silver ADX, which reuses the `AX_MAKERS` VFD sprites; `AXW_MAKERS` for the swoop, the dark
ADX's with its own main window) so the earlier skins stay byte-identical.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py clarion        # some (vw-mib2, vw-mib2-v2, clarion,
                                               #   clarion-adx5655z, clarion-adx5655z-silver,
                                               #   clarion-adx5655z-swoop)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `VW-MIB-II.wsz`, `VW-MIB-II-v2.wsz`, `Clarion.wsz`, `Clarion-ADX5655z.wsz`,
`Clarion-ADX5655z-Silver.wsz`, `Clarion-ADX5655z-Swoop.wsz` and `preview-<theme>.png` here; sheets in `out/<theme>/` (`out/` is ignored). Each .wsz is finished by
`skins/genex_wacup.py`.

## Themes

- **VW MIB II** (`vw-mib2`, Volkswagen's Modular Infotainment Platform 2, Composition / Discover
  Media, 2015-2019): piano-black glass surround, chrome-ringed hard keys, two knobs under the
  screen, and the screen's blue-on-black UI with white text.
  - Titlebar: the hard-key row (RADIO MEDIA PHONE VOICE | MENU CAR SOUND SETUP) with the VW
    roundel in the middle (the only logo). MEDIA is lit on the main window, SOUND on the
    equalizer.
  - Main window: one screen with flat cards (time and analyzer tile, title card with kbps/kHz and
    mono/stereo, a "MEDIA / USB" source tile), thin MIB sliders with round white thumbs, on-screen
    EQ/PL soft buttons, a thin progress line. Below it, the transport, eject, shuffle and repeat
    (a loop icon) as chrome-ringed hard keys, with the volume/power knob bottom left and the tune
    knob bottom right (the About spot).
  - Time digits are rendered from Open Sans (system font) to look like the MIB's clean sans.
  - Playlist "TRACK LIST", album art, equalizer: the same glass, keys and slider style.
- **VW MIB II v2** (`vw-mib2-v2`): the MIB II screen UI alone, no hardware, after the Composition
  Media radio screen photos in `source/ref-mib2-ui/` (user-supplied). Black screen; titlebars are
  the status row (white Noto Sans Condensed title, thin grey rule; the main one carries the VW
  roundel at left and a grey "TP"). Time digits white Noto Sans Condensed; title white (text.bmp
  ink); kbps / kHz labels grey. Play / pause / stop / eject, shuffle (text) and repeat (loop
  icon), EQ / PL, ON / AUTO / PRESETS are light-grey gradient preset tiles with a red underline
  when lit or pressed (pressed tiles get brighter with a pale border, like the selected preset);
  previous / next are MIB's outlined square arrow buttons. Sliders are thin grey tracks with a
  red fill and white round thumbs. A red rule and the dark blue-grey soft-key bar run along the
  bottom; the playlist's buttons are soft keys (label over a small icon, thin separators), the EQ
  band labels sit in the soft-key bar, the Setup gear is in the About spot. Highlight red (232,
  52, 38), sampled from the photos (camera bloom makes it look pinker there). Font: Noto Sans
  (falls back to Arial where missing).
- **Clarion** (`clarion`): a representative 2000s single-DIN Clarion MP3 CD receiver, styled after
  the DXZ-series (c. 2003-2005: DXZ5xx/6xx/7xxMP).
  - Brushed silver faceplate, the Clarion wordmark top left (Clarion's own logo, the only
    logo), "MP3/WMA CD RECEIVER" and "50W X 4" silkscreen.
  - One black smoked display window holding everything down to the sliders: cyan seven-segment
    time with ghost segments, a dot-matrix-style title, lit/ghost indicator labels (MP3, TRK,
    TIME, SCN RPT RDM), segment bar graphs for volume and balance with a block cursor as the
    thumb, and EQ/PL as display indicators.
  - Small rubber keys for transport and OPEN (eject); RDM / RPT keys (Clarion's own labels) with a
    cyan LED; the big rotary volume knob with its blue illumination ring sits bottom right.
  - Equalizer: segment-bar columns in a display window ("BEAT EQ" silkscreen, Clarion's EQ name
    of the era); playlist and album-art titles on slim display plates.
- **Clarion ADX5655z** (`clarion-adx5655z`): after the Clarion ADX5655z (double-DIN tuner / CD /
  cassette with spectrum analyzer, c. 2002), from the photos in `source/ref-adx5655z/`
  (user-supplied: a product shot and a lit unit). Black gloss faceplate in a sculpted silver
  surround (side frames waisted in the middle); titlebar prints "HIGH POWER 45Wx4" and
  "ADX5655z" in light gold italic (#DED8BF, the brightest fifth of the print's pixels in the
  product photo; the unit prints both in the same light gold). One VFD window (dark violet-black) holds: the analyzer as
  the spectrum bank (viscolor: three orange/amber top rows over cyan to blue, orange peaks, violet
  dot grid), a white bracket at its outer end, 5x7 dot-matrix time digits in pale blue-white, the
  pale blue-white title, ghost labels TP TA INFO AF PTY REG, orange outlined lozenges "FUNCTION"
  round kbps and "CH" round kHz, segment bar graphs for volume / balance with an orange lozenge
  cursor, EQ / PL as orange lozenge indicators. Translucent pale-blue preset keys are the
  clutterbar and RDM / RPT (orange LED when on), grey rubber pill keys the transport, a silver
  eject, "CENET" and "MAGI-TUNE" print, the Clarion wordmark centred under the keys, the round
  silver four-way rocker in the About spot. EQ: the spectrum display with blue segment columns
  and an orange cap cursor, between white brackets; the graph sits in a tab with chamfered top
  corners whose sides flare out into the slider window, like the faceplate's angled cut-outs
  (Winamp's curve area, x 86-198, y 17-35, is untouched; all three ADX takes). Playlist: pale-blue VFD text on violet-black,
  orange current track, with the "FULL LOGIC CASSETTE SYSTEM" cassette door behind the ADD / REM
  / SEL / MISC keys.
- **Clarion ADX5655z Silver** (`clarion-adx5655z-silver`): the same unit and the same VFD content,
  with the balance inverted to match the real front more closely: the keys sit on the satin
  brushed silver faceplate (#EAEDF1 at the top to #B4B8C1, faint horizontal brush streaks, darker
  silver #9CA1AB bevels down the sides, waisted on the main window and EQ, straight on the tiled
  windows), and only the display sections are recessed VFD glass (black gloss rim, #100A16 glass,
  a light lip below). Print on the silver is dark grey (#181A20, #424650 for small print); unlit
  titlebars fade it to #8A8E97.
  - Titlebar: "HIGH POWER 45Wx4" and "ADX5655z" in dark italic, "SPECTRUM ANALYZER" small
    between; grey rubber caption keys.
  - Main window: one VFD window, its left bank deeper (time, analyzer) and its right part holding
    the title, the FUNCTION / CH lozenges round kbps / kHz and STEREO / MONO. On the silver: the
    pale-blue preset keys (clutterbar), volume and balance as dark recessed tracks lit with
    blue-to-orange VFD segments under a silver slider cap with a dark index line (orange when
    held), EQ / PL as grey rubber keys with an orange LED, the seek bar as a long recessed slot,
    grey rubber transport keys, a silver eject, pale-blue RDM / RPT keys, "CENET" and "MAGI-TUNE"
    print, the dark Clarion wordmark (the only one), the rocker pad on its silver ring (About).
  - Equalizer: silver body with the whole line "TUNER/COMPACT DISC/CASSETTE PLAYER WITH SPECTRUM
    ANALYZER" in the titlebar; the graph and the slider bank are one T-shaped VFD window (blue
    segment columns with an orange cap cursor between white brackets, pale band labels); ON /
    AUTO / PRESETS are pale-blue keys on the silver.
  - Playlist and album art: silver frames with straight sides, the list and the art in a black
    gloss rim, printed outline title boxes ("PLAYLIST", the album-art title in dark print). The
    playlist's bottom bar is silver with grey ADD / REM / SEL / MISC / LIST keys, the small time
    displays as VFD glass, and a smoked "FULL LOGIC CASSETTE SYSTEM" slot; the scrollbar is a
    dark groove with a silver thumb.
  Playlist: #96C8FF on #100A16, #FF9224 current, #34244E selection. Font: Arial.
- **Clarion ADX5655z Swoop** (`clarion-adx5655z-swoop`): the dark ADX5655z (same VFD content,
  keys, EQ, playlist and gen sheets) with the real faceplate's silver swoop on the main window,
  after `source/ref-adx5655z/user-crop-transport-silver.png`: the silver skin's satin brushed
  silver climbs from the left edge in two angled steps to surround the transport keys and the
  eject, drops steeply past them to a low band under RDM / RPT (left on the black, as TITLE is on
  the unit), then dips round the bottom of the four-way pad and rises into the right edge, with a
  dark seam above and a lit top edge. "CENET" and the Clarion wordmark sit on it in dark print.
  Only main.bmp and the sheets cut from it (cbuttons, posbar) differ from the dark take.

## Limits

- Clarion (`clarion`) is a composite, not a copy of one model: the research did not find a
  reliable spec sheet or photo set for a single unit's faceplate.
- Clarion's volume knob sits bottom right, since the About spot is the only free area big enough
  (most real Clarion units put it on the left).
- The MIB II v2 highlight red is sampled from photos, where camera bloom makes it look pinker.
- Clarion ADX5655z Silver: the real unit is mostly black gloss round the display with silver at
  the edges; this take puts the keys on silver on purpose. Winamp's main window has no slots for
  the photo's SPE-ANA / DISP / FUNC / ISR / BAND keys, so the pale-blue keys are the clutterbar,
  RDM / RPT and the EQ's ON / AUTO / PRESETS, and the cassette door is reduced to a slot in the
  playlist's bottom bar.

## Sources

- Volkswagen roundel: Simple Icons' `volkswagen.svg`
  (https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/volkswagen.svg), in
  `source/vw-logo/`, rasterised with rsvg-convert at generation time and composited once.
- Clarion wordmark: Clarion's own logo (Clarion Co., Ltd.), supplied by the user as a PNG,
  `source/clarion-wordmark.png` (2400x965, black on transparent). Only the word "clarion" is used:
  the "CAR AUDIO & BEYOND" tagline is cropped off and the (R) dropped (illegible at these sizes).
  Loaded at generation time (`clarion_mask`), area-averaged down (10 px tall in the Clarion
  titlebar, 8 px on the ADX5655z faceplates) with each letter hinted to the pixel grid, and
  painted in each skin's colour. It replaces the earlier hand-drawn pixel lettering.
- Reference photos supplied by the user: `source/ref-mib2-ui/` (MIB II radio screens) and
  `source/ref-adx5655z/` (ADX5655z); reference only, not used in any sheet.
- Noto Sans / Noto Sans Condensed (OFL, system fonts) for the v2 text and digits; Liberation Sans
  Bold Italic for the ADX5655z print.
- The Kenwood and Alpine car-stereo skins in the user's collection were looked at for layout ideas
  only; nothing was copied from them.
- Volkswagen logo (c) Volkswagen AG.
- Clarion logo (c) Clarion Co., Ltd.
