# Norstar: the Nortel Meridian Norstar M7310 office phone, charcoal and ash

Two skins from one generator (`gen_skin.py`, based on `skins/ember/gen_skin.py` by way of the
sibling `devices/honda-accord` generator's theme scaffold, keeping Ember's sheet layouts), one
layout in two colourways. Two real marks are used, each once: the "meridian" logo is the main
titlebar's wordmark, its long rule running out towards the titlebar buttons, and the NORTEL mark
sits small on the groove line across the bottom of the main window (where the real phone has it,
top centre, the titlebar is already the meridian rule). Both are loaded from `source/` at build
time, masked (alpha times darkness against white), cropped to their bounding box, supersampled
down (LANCZOS to 4x, then BOX) and painted through the mask in the theme's print colour; the
meridian crop gets a sub-pixel vertical offset so its rule lands on one pixel row, and the rule's
own scaled columns are repeated to stretch it. Everything else is drawn by the script: flat
bevelled keys, fine noise for the matte plastic, hand-made pixel fonts (a mixed-case key font
after the phone's key lettering, a 5x7 dot-matrix clock font).

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py m7310-ash      # some (m7310-charcoal, m7310-ash)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Nortel-Norstar-M7310.wsz`, `Nortel-Norstar-M7310-Ash.wsz`, `preview-m7310-charcoal.png`
and `preview-m7310-ash.png` here; sheets in `out/<theme>/`, 4x detail crops (display, keys,
titlebar, EQ, playlist) in `out/scratch/` (`out/` is ignored). Deterministic. Each .wsz is
finished by `skins/genex_wacup.py`.

## Themes

Both share the layout. The main window is the phone's face:

- Display: the grey-green LCD in its dark bezel, L-shaped (time and analyzer left, title and
  kbps / kHz / STEREO right), dark pixels on pale glass. The clock is a 5x7 dot matrix filling
  numbers.bmp's 9x13 cells (one dot per pixel, joined by a half-tone, unlit dots as the LCD's faint
  grid). text.bmp is dark ink on the glass, so the TrueType title draws dark on the pale LCD.
  The analyzer is the LCD's ink in a few dark shades.
- Under the LCD, inside the bezel: the slotted grey ribs, the volume rocker as the volume slider
  (a long grey key with the small and large speaker icons and a slim LCD window whose dark bars
  show the level), balance as a short L / R rocker with a centre-out bar, and EQ / PL as the
  display's soft keys.
- Transport: the dial-pad grey keys for previous / next / eject, a sage-green Line key ("Line",
  play), the red Hold (pause) and Rls (stop) keys, each with its lettering and a small icon.
  Toggles (shuffle, repeat, EQ, PL, EQ on / auto) carry the M7310's LCD indicator to their left: a
  sliver of glass with a black triangle when on. The clutterbar is a column of tiny grey keys.
- Seek: the recessed groove across the body with a small grey key as the thumb; volume / balance
  thumbs are dark nubs on the grey rockers. The About spot is the triangular message-waiting
  lamp with a small grille beside it.
- Titlebars are speaker-grille slots; window titles (EQUALIZER, PLAYLIST, gen titles) sit on the
  memory keys' paper designation strips. The EQ graph is a small LCD in the bezel, PRESETS a
  memory key with a paper label, the sliders tall pale indicator strips (like the one between the
  Line keys) with dark bars, grey key thumbs, and a grille panel beside the dB print. The playlist
  is a paper designation strip; its timers are small LCDs; buttons are grey keys.

- **Nortel Norstar M7310** (`m7310-charcoal`, the 1990s M7310 in charcoal): body #2E2E2F, bezel
  #3C3D3F, keys #A0A09C, Hold / Rls #DE604C, Line #80A696, LCD glass #B6C4B9 with ink #222824,
  paper #DCD6C6, print #B8B8B4 (light grey wordmarks).
  Playlist: #222824 on #DCD6C6, #961E14 current, #96B0A4 selection. Font: Arial.
- **Nortel Norstar M7310 Ash** (`m7310-ash`, the ash / beige colourway): body #D6CFBC, bezel
  #44484E (dark, as on the real ash set), keys #B0B1AD, Hold / Rls #EA5C3C, Line #94C8B2, LCD
  glass #A8B8A4 with ink #1E241E, paper #EAE7D8, print #54524A (dark grey wordmarks).
  Playlist: #1E241E on #EAE7D8, #AA2414 current, #B0CCBA selection. Font: Arial.

## Limits

- The NORTEL mark is 8 px tall: the globe's swoosh reads as a broken O, the letters are clean.
  Both logos are painted in the print colour, not Nortel blue (the phones printed them
  monochrome; blue would not read on charcoal).
- The real phone has no transport keys: prev / next / eject use dial-pad greys with icons only;
  "Line", "Hold" and "Rls" keep the phone's own words. "Rpt" is abbreviated to fit 28 px.
- The volume rocker's level window can be covered by the thumb near the ends; the balance can't
  show which side (the format's limit).
- The handset, dial pad numerals, Feature / DND / Conf / Page / Intercom keys and the memory-key
  grid aren't drawn as such: the window's fixed sprite slots leave no room; their styles are used
  for the transport, toggles, PRESETS and the titles instead.
- Colours sampled from the reference photos and adjusted by eye (the ash photo is small and
  angled; its LCD and body were lightened / greened to match the charcoal set's glass).

## Sources

- `source/m7310-charcoal.png` (user-supplied photo, M7310 charcoal, straight on): reference only,
  for layout, keys, LCD, bezel, grille and colours.
- `source/m7310-ash.png` (user-supplied photo, M7310 ash, angled): reference only, for the ash
  palette.
- `source/meridian-logo.png` (user-supplied, black on white, 600x600): masked and painted once,
  as the main titlebar's wordmark and rule. Meridian logo (c) Nortel Networks (Meridian Norstar
  was Northern Telecom / Nortel's key telephone system).
- `source/nortel-logo.png` (user-supplied, blue on transparent, 2800x1400): masked and painted
  once, small on the main window's bottom groove. Nortel logo (c) Nortel Networks.
