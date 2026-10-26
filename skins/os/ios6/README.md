# iOS 6: the skeuomorphic iPhone look (2012)

One classic skin from a procedural generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`,
which holds the sheet layouts the app reads). The one mark used is the Apple logo, small and
silver in the main window's emblem (About) spot; no other Apple artwork or screenshots are used.
Everything else is drawn by the script: gradients, anti-aliased shapes from supersampled masks and
hand-made pixel fonts. It needs `/usr/bin/rsvg-convert`.

```sh
/usr/bin/python3 -I gen_skin.py
```

Outputs: `iOS6.wsz` and `preview.png` here (the windows assembled from the sprites, at 2x); sheets
in `out/` (ignored). Deterministic.

## Themes

- **iOS 6** (one theme, 2012):
  - Titlebars: the blue-grey glossy navigation bar with white embossed titles ("Now Playing",
    "Equalizer", "Playlist") and small glossy bar buttons. Inactive windows get a desaturated
    grey bar.
  - Main window: a glossy black body with dark-glass displays (white Helvetica-like digits) and a
    black glossy toolbar with white pictograms that glow when pressed. Shuffle, repeat, EQ and PL
    are segmented-style toggles that turn blue when on. Volume, balance and seek use blue-filled
    tracks with white round knobs.
  - Equalizer: a pinstripe background with white grouped panels and vertical iOS sliders.
  - Playlist and generic windows: navigation-bar tops, light frames and a blue-grey bottom
    toolbar.
  - Playlist: #000000 on #FFFFFF, #2A5FB0 (iOS blue) current, #CFE0F7 selection. Font: Arial.

## Limits

- None noted.

## Sources

- Apple logo: https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg (Wikimedia
  Commons, "Apple logo black.svg") in `source/apple-logo/logo.svg`, rasterised at build time with
  `/usr/bin/rsvg-convert` and composited once into the About spot.
- Apple logo (c) Apple Inc.
