# Office phones: the Nortel Norstar M7310 and the Cisco IP Phone 7945

Three skins from one generator (`gen_skin.py`, based on `skins/ember/gen_skin.py` by way of the
sibling `devices/honda-accord` generator's theme scaffold, keeping Ember's sheet layouts): two
colourways of the Nortel Meridian Norstar M7310 key phone sharing one layout, and the Cisco IP
Phone 7945 (a colour-LCD office phone, grouped here by device type rather than brand) with its own,
unrelated main-window layout. The cisco-7945 theme reuses this file's generic drawing helpers
(bevelled keys, wells, glass, sliders, pixel fonts) where they fit, and writes its own versions
only where the Norstar ones bake in Norstar-specific shapes (the speaker grille, the memory keys'
paper designation strips).

```sh
/usr/bin/python3 -I gen_skin.py                     # all of them
/usr/bin/python3 -I gen_skin.py m7310-ash cisco-7945  # some
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Nortel-Norstar-M7310.wsz`, `Nortel-Norstar-M7310-Ash.wsz`, `Cisco-IP-Phone-7945.wsz`,
and a `preview-<theme>.png` per theme, here; sheets in `out/<theme>/`, 4x detail crops (display,
keys, titlebar, EQ, playlist) in `out/scratch/` (`out/` is ignored). Deterministic. Each .wsz is
finished by `skins/genex_wacup.py`.

## Nortel Norstar M7310

Two skins, `m7310-charcoal` and `m7310-ash`, sharing one layout. Two real marks are used, each
once: the "meridian" logo is the main titlebar's wordmark, its long rule running out towards the
titlebar buttons, and the NORTEL mark sits small on the groove line across the bottom of the main
window (where the real phone has it, top centre, the titlebar is already the meridian rule). Both
are loaded from `source/` at build time, masked (alpha times darkness against white), cropped to
their bounding box, supersampled down (LANCZOS to 4x, then BOX) and painted through the mask in
the theme's print colour; the meridian crop gets a sub-pixel vertical offset so its rule lands on
one pixel row, and the rule's own scaled columns are repeated to stretch it. Everything else is
drawn by the script: flat bevelled keys, fine noise for the matte plastic, hand-made pixel fonts
(a mixed-case key font after the phone's key lettering, a 5x7 dot-matrix clock font).

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

### Limits

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

### Sources

- `source/m7310-charcoal.png` (user-supplied photo, M7310 charcoal, straight on): reference only,
  for layout, keys, LCD, bezel, grille and colours.
- `source/m7310-ash.png` (user-supplied photo, M7310 ash, angled): reference only, for the ash
  palette.
- `source/meridian-logo.png` (user-supplied, black on white, 600x600): masked and painted once,
  as the main titlebar's wordmark and rule. Meridian logo (c) Nortel Networks (Meridian Norstar
  was Northern Telecom / Nortel's key telephone system).
- `source/nortel-logo.png` (user-supplied, blue on transparent, 2800x1400): masked and painted
  once, small on the main window's bottom groove. Nortel logo (c) Nortel Networks.

## Cisco IP Phone 7945

One skin, `cisco-7945`, a 2007 colour-LCD office phone (Cisco Unified Communications Manager
desk sets) grouped in this phone folder rather than `devices/cisco/`'s networking-gear family.
Its own main window: this is the same fixed classic-Winamp control grid every skin in this
collection draws onto (titlebar buttons, transport row, shuffle / repeat, EQ / PL toggles,
volume / balance, seek bar, clutterbar — all at the app's own fixed pixel positions, per
`ui/src/lib/skin/render/sprites.js`), but reskinned and remapped to the 7945's own controls
instead of the Norstar's:

- Two-tone body, prominent rather than subtle: the whole upper half of the main window — the
  titlebar (the Cisco badge and "Cisco IP Phone 7945" print) and the screen bezel below it — is
  one continuous light silver shoulder with no seam between them, exactly as the real unit's
  moulding reads (the logo and model name sit on the same silver plate the screen does, not on
  the charcoal body); the lower half (keypad, nav cluster, icon-grid, volume, headset row) is
  charcoal. That's the opposite of the Norstar skins' dark-bezel / light-key scheme, carried
  through to the keys too: charcoal key faces with near-white ink (the 7945's keys are dark
  plastic with white icons; the Norstar's are the reverse).
- Rounded, not boxy: the silver shoulder's top two corners and the bottom corners where it meets
  the charcoal body are chamfered, and every key (transport, eject, shuffle / repeat, EQ / PL,
  EQ On / Auto, Presets) has its corners rounded off the same way — classic Winamp windows can't
  actually be non-rectangular, so this softens the shapes drawn *within* the window rather than
  the window itself, after the boxier, flat-bevelled Norstar look. The About badge and the nav
  cluster's Play key read round on their own (a filled disc, a checkmark on a teal accent key).
- Display: the phone's own pale blue-grey colour-LCD look (not the Norstar's grey-green), same
  L-shaped split (time and analyzer left, title and kbps / kHz / STEREO right) and the same 5x7
  dot-matrix clock technique, recoloured — dark navy ink on the pale blue glass, so the TrueType
  title draws dark on the LCD as the layout requires.
- The nav cluster's centre checkmark is Play (a teal accent key, the one colour accent on the
  skin); the ring's left / right arrows are Previous / Next and the up / down arrows Stop / Pause
  — so the whole core transport comes from the one five-way cluster, as on the real unit. The
  headset key is Eject (a headset icon; the "pick up to eject" pairing). The round, lit "?" Help
  button at the centre of the icon-key grid is the About spot (a filled teal disc that is also
  where the one spare slot the control grid doesn't otherwise ask for gets used).
- Shuffle and Repeat sit where two of the icon-key grid's keys are (an icon in the key instead of
  a text label, each with a round lit LED to its left where the Norstar skins use a triangle —
  this phone's own look), but not drawn as that grid's own globe / directory icons: redrawn that
  small (20px) those read as a crossed-out circle and two flat bars, not as anything in particular,
  so the keys carry the standard crossing-arrows (shuffle) and looping-arrow (repeat) glyphs
  instead — unmistakable at this size where the literal icons weren't. The two round line /
  feature keys beside the screen are EQ and PL (small labelled toggles with the same round LED).
  EQ On / Auto, in the EQ window, match.
- Volume is the volume rocker (reusing the Norstar skins' own slider art unmodified — a long key
  with small / large speaker icons and a slim LCD level window, which fits this phone's rocker
  just as well); balance is a short L / R rocker built the same way (the real phone has no second
  rocker). Seek is the body's recessed seam, as on the Norstar skins.
- The main titlebar is the silver shoulder itself (see above) and carries the one real mark used,
  the Cisco badge (the bridge bars redrawn as pixels, "cisco" in the skin's own pixel font) plus
  "CISCO IP PHONE 7945" printed beside it in dark ink, as the real unit prints its model name on
  that same plate. The EQ / PLAYLIST / gen window titlebars are a smaller silver label plate (the
  same material) inset in an otherwise plain charcoal bar — no speaker grille (this phone doesn't
  have one).

Palette: body / keys #5A5D61 (charcoal, near-white key ink #E6E8E9), screen bezel #C4C4C3, LCD
glass #9EC3D6 with ink #122838, teal accent #426A7E (Play, the lit LEDs, the About badge).
Playlist: #122838 on #D6DCE0, #C65C26 current, #96BCD0 selection. Font: Arial.

### Limits

- The real phone's dial pad, the handset and cradle, and two of the icon-grid's four keys aren't
  drawn as such, for the same reason as the Norstar skins' unused controls: the window's fixed
  sprite slots don't ask for them, and nothing is left over to spend on them once the rest of the
  control list is covered.
- The on-screen soft-key labels ("Dial / EditDial / Exit / more", from the straight-on reference
  photo) aren't reproduced on the LCD itself; EQ and PL are the two round line keys beside the
  screen instead (see above), which the fixed control grid has room for.
- The Cisco bridge logo's text is redrawn in the skin's own pixel font rather than the exact
  typeface; its bar count (9) and the general soundwave silhouette are measured from the
  downloaded SVG, not reproduced bar-for-bar.

### Sources

- `source/cisco-7945.png` (user-supplied photo, straight on): the idle Directories screen, the
  screen bezel and keypad layout, colours for the LCD / selection / body.
- `source/cisco-7945-angle.png` (user-supplied photo, 3/4 angle, sharper): the icon-key grid's
  actual arrangement and the lit "?" Help button, the nav cluster's checkmark colour, the volume
  rocker's end caps, the headset / mute / speaker row.
- `source/cisco-logo-2006/Cisco_logo.svg`: Wikimedia Commons `File:Cisco_logo.svg`
  (https://upload.wikimedia.org/wikipedia/commons/6/64/Cisco_logo.svg), downloaded into this
  folder's own `source/` (not read from `devices/cisco/`'s copy). Rasterised at build time
  (`rsvg-convert`, cached in `out/scratch/`) only to measure the bridge's bar heights and the
  badge's two inks (a dark teal and a red, both embedded in the SVG's paths); the badge itself is
  redrawn as pixels, in the skin's own font, in those two inks.
- Cisco logo (c) Cisco Systems, Inc.
