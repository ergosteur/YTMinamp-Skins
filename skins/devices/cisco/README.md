# Cisco: classic Cisco network hardware

Two classic skins from one generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`, whose
sheet layouts and preview renderer it keeps), a theme each. The one mark used is the Cisco logo
of each era (the 1996 "CISCO SYSTEMS" badge, the 2006 bridge-over-CISCO logo) in the titlebar,
redrawn as pixels in the skin's own pixel font. Everything else is drawn by the script; the
console digits are rendered from URW Nimbus Mono PS Bold, a Courier clone.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py cisco-2800     # some (cisco, cisco-2800)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Cisco.wsz`, `Cisco-2800.wsz` and `preview-<theme>.png` here; sheets in `out/<theme>/`
(`out/` is ignored).

## Themes

- **Cisco** (`cisco`, the teal powder-coat of the late-1990s gear: Catalyst 2900 XL, 2600
  routers): Cisco never published the colour (forum lore says Pantone 7477); the skin uses
  #3E8C8C, the sea-green teal those fronts photograph as, with a fine stipple rather than brushed
  grain.
  - Titlebar: the 1996 "CISCO SYSTEMS" badge over its bridge in white silkscreen (the only logo),
    between rows of punched vent slots.
  - Displays are console sessions: green phosphor on black, a `Switch#` prompt with a block cursor
    over the time, Courier digits, a TrueType title in the same green (text.bmp's ink).
  - Transport: a row of RJ-45 jacks (gold contacts, latch notch) with the icons inside and link
    (green) / activity (amber, when pressed) LEDs in the jack corners. The About spot is the
    CONSOLE port in Cisco's light-blue surround, and the seek bar is the light-blue console cable
    with its clear RJ-45 plug as the thumb.
  - LED legends: the Catalyst's SYST RPS STAT UTIL DUPLX SPEED row along the bottom (decorative);
    clutterbar, EQ/PL, shuffle/repeat and EQ ON/AUTO are LED keys (green when on, unlit when off).
  - Volume and balance are LED bar meters (green, amber at the top / off-centre); EQ sliders are
    vertical LED bargraphs with steel slide thumbs.
  - Playlist: a terminal (green on black, dark-green selection), titled PLAYLIST in silkscreen,
    with "CATALYST 2900 SERIES XL" printed under its buttons. Phillips screws at the corners.
    Font: Courier New.
- **Cisco 2800** (`cisco-2800`, the 2800-series ISR, 2005 on): dark blue-grey front (#3A4858), the
  2006 bridge-over-CISCO logo, an amber console with a `Router#` prompt, "CISCO 2800 SERIES"
  silkscreen. Same parts otherwise.

## Limits

- The teal is from photos and forum lore; Cisco never published it.
- The Cisco 2800's LED legend row keeps the Catalyst labels (the 2800's own front LEDs were not
  verified).

## Sources

- 1996 logo: Wikimedia Commons `File:Cisco_logo_1996.svg`
  (https://upload.wikimedia.org/wikipedia/commons/8/84/Cisco_logo_1996.svg), in
  `source/logo-1996/`.
- 2006 logo: Wikimedia Commons `File:Cisco_logo.svg`
  (https://upload.wikimedia.org/wikipedia/commons/6/64/Cisco_logo.svg), in `source/logo-2006/`.
- Both are rasterised with rsvg-convert at generation time only to measure the bridge's bar
  heights (reference only); the badges are redrawn as pixels.
- Cisco logo (c) Cisco Systems, Inc.
