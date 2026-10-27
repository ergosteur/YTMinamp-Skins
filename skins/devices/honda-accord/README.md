# Honda Accord: a late-80s / early-90s Accord centre stack (radio face, climate sliders)

One skin from one generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`, whose sheet layouts
it keeps; the seven-segment digit code is Ember's). It mixes two generations on purpose: the radio
face is the 4th-generation (1990-93) Honda head unit from the user's close-up, and the sliders and
keys come from the 3rd-generation (1986-89) climate panel (the 4th gen has climate dials). Honda's
real wordmark is used once, in the main titlebar: loaded from `source/honda-wordmark.png` at
generation time, masked from its alpha, scaled down to 8 px tall with a box filter and recoloured to
the radio's silver print. Everything else is drawn by the script (bevels, noise for the plastic
stipple and leather grain, hand-made pixel fonts).

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py accord         # some (accord)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Honda-Accord.wsz` and `preview-accord.png` here; sheets in `out/accord/`, 4x detail
crops in `out/scratch/` (`out/` is ignored). Deterministic. The .wsz is finished by
`skins/genex_wacup.py`.

## Themes

- **Honda Accord** (`accord`, 1990-93 radio, 1986-89 climate panel): black stippled dash plastic
  (#19191B).
  - Titlebars: the dash's air-vent louvres (three slats in a black cavity, a ribbed thumb tab)
    either side of the title; the main one carries Honda's wordmark (8 px tall), silver with a
    top-to-bottom shade and a dark drop shadow, grey when unfocused. Titlebar buttons are tiny rubber keys.
  - Display: one L-shaped teal VFD window (glass #050D0D, lit #6EF6DE) holding the time
    (seven-segment, ghost segments #0F2422 visible when unlit), the analyzer, the title, kbps / kHz
    legends and STEREO / MONO. text.bmp is teal FONT5 lettering on the glass, so the TrueType title
    draws in teal.
  - Transport: the radio's small rubber preset keys, each with its number, a dot and the transport
    symbol ("1 . <<" ... "5 . >>"), labelled REW PLAY PAUSE STOP FF in silver print above; EJECT
    likewise. Two small knobs bottom right (FAD / BAS, the About spot), and an "ELECTRONIC TUNING
    STEREO" print along the bottom.
  - Climate panel: volume, balance and the seek bar are long dark slots with chunky black knobs
    (lit top face, dark front, pointer line). Volume has the fan legend "OFF LO . . HI" over it,
    balance the blue-to-red temperature stripe (#5696CD / #CE3E3A). Shuffle / repeat (SHUFFLE,
    RPT), EQ / PL, ON / AUTO / PRESETS and the clutterbar are the climate key row's grey keys with
    an amber indicator slot (#FFA834 lit) and white lettering in a dark label window.
  - Equalizer: a recessed slider panel with vertical slots and the same knobs; the temperature
    stripe runs up beside the preamp (red for boost, blue for cut), dB marks and band labels in
    silver; the graph is a small teal VFD.
  - Playlist and gen windows: black plastic titlebars (vents and a dark title strip) and bottom
    bars (rubber keys ADD REM SEL MISC LIST, teal VFD timers), with burgundy dash leather
    (#462027) down the sides; the scrollbar is a climate slot with a knob.
  - Playlist: #5AE6CC on #050C0C, #E0FFF8 current, #18524A selection. Font: Arial.

## Limits

- The two generations are mixed by design (see above).
- The volume and balance frames are all the same (the knob alone shows the level), as on the real
  panel; the balance can't show which side.
- The VFD is L-shaped so the fan legend and temperature stripe fit above the volume and balance
  slots; STEREO / MONO's sprite carries the window's bottom rim.
- Colours were sampled from the user's (sunlit, dusty) photos and darkened by eye: the leather is a
  deeper burgundy than the photo shows. "ELECTRONIC TUNING STEREO" is a period-style print, not a
  copy of the unit's.

## Sources

- `source/accord-3g-dash-climate.png` (user-supplied photo, 3rd-gen Accord centre dash): reference
  only, for the vents, climate keys, slider panel, legend, stripe and leather colour.
- `source/honda-radio-head-unit.png` (user-supplied photo, 4th-gen Honda radio and CD unit):
  reference only, for the radio face, rubber keys, labels, knobs and the print's silver.
- `source/honda-wordmark.png` (user-supplied, Honda's wordmark, red on transparent, 1024x128):
  composited once into the main titlebar, recoloured silver (never red).
- Honda wordmark (c) Honda Motor Co., Ltd.
