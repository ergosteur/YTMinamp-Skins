# Cisco: classic Cisco network hardware

Three skins from one generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`, whose
sheet layouts and preview renderer it keeps), a theme each. The one mark used is the Cisco logo
of each era (the 1996 "CISCO SYSTEMS" badge, the 2006 bridge-over-CISCO logo) in the titlebar,
redrawn as pixels in the skin's own pixel font (the Catalyst 2960 has it on its LED strip, which
reaches up into the titlebar). Everything else is drawn by the script; the console digits are
rendered from URW Nimbus Mono PS Bold, a Courier clone, and the 2960's "Catalyst 2960 Series SI"
print from URW Nimbus Sans (Helvetica).

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py cisco-2800     # some (cisco, cisco-2800, catalyst-2960)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Cisco.wsz`, `Cisco-2800.wsz`, `Cisco-Catalyst-2960.wsz` and `preview-<theme>.png` here; sheets in `out/<theme>/`
(`out/` is ignored). Each .wsz is finished by `skins/genex_wacup.py`.

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
- **Cisco Catalyst 2960** (`catalyst-2960`, the WS-C2960-8TC-L compact switch, 2006 on), drawn
  from a product photo. Its own main window, transport, mode keys, seek bar, digits and EQ.
  - Main window: the front bezel in steel blue-teal #38647C (sampled), around the charcoal inset
    panel (#52565B) with its embossed grid (two offset layers of rounded squares). The panel
    reaches up into the titlebar on the left and steps down under the "Catalyst 2960 Series SI"
    print on the right, as the bezel does. Left of it, the charcoal LED strip: the 2006 logo at its
    top (in the titlebar; it is also the options button, and lights green when pressed), and the
    clutterbar as its LED column (letter, then a round LED, green when on).
  - Readouts are smoked-black LED windows in port-LED green (#76EC5C): seven-segment digits with
    ghost segments, a green analyzer with amber tops and peaks, the TrueType title in the same
    green (text.bmp's ink). Between the kHz and mono/stereo windows, the strip's SYST STAT DPLX
    SPD legend with its LEDs (system and status lit).
  - Transport: ports 1x-5x, RJ-45 jacks in the row's silver surround, under yellow 1x-5x tags,
    above the gold tick row. Each port's LED triangle lights green, and its icon too, when pressed.
    Eject is the CONSOLE port in its light-blue surround, under CONSOLE in pale blue.
  - Shuffle and repeat are the uplink pair in its yellow outline: the RJ-45 (shuffle) and the SFP
    cage (repeat), with the "1" and an LED triangle each pointing at its port (green when on),
    labelled underneath. The About spot is the round MODE button on its own bit of strip.
  - Seek bar: a groove with an SFP transceiver (blue bail) as the thumb. Volume and balance are
    LED bar meters; EQ/PL are yellow tags with LED triangles.
  - EQ: the same panel, LED bargraph sliders, the band labels as yellow port tags.
  - Playlist and gen windows: plain bezel blue (no vents, no screws on this front), PLAYLIST and
    "CATALYST 2960 SERIES SI" in white. Playlist: #76EC5C on #0D0F10, #D6FFC4 current, #1C481E
    selection. Font: Arial.

## Limits

- The teal is from photos and forum lore; Cisco never published it.
- The Cisco 2800's LED legend row keeps the Catalyst labels (the 2800's own front LEDs were not
  verified).

- Catalyst 2960: the front's 8 RJ-45 ports become 5 (the transport) plus CONSOLE (eject), as
  Winamp's button row has room for; the uplink box holds shuffle and repeat. The MODE button and
  the status LEDs are separated from the strip (the clutterbar fixes the strip's width and height);
  their LEDs are decorative. The embossed "CISCO SYSTEMS" plate on the top cover is left out.

## Sources

- 1996 logo: Wikimedia Commons `File:Cisco_logo_1996.svg`
  (https://upload.wikimedia.org/wikipedia/commons/8/84/Cisco_logo_1996.svg), in
  `source/logo-1996/`.
- 2006 logo: Wikimedia Commons `File:Cisco_logo.svg`
  (https://upload.wikimedia.org/wikipedia/commons/6/64/Cisco_logo.svg), in `source/logo-2006/`.
- Both are rasterised with rsvg-convert at generation time only to measure the bridge's bar
  heights (reference only); the badges are redrawn as pixels.
- Catalyst 2960 reference: `source/catalyst-2960-8tc.jpg`, a product photo of the WS-C2960-8TC-L
  (local, provided), reference only: colours sampled from it, nothing composited.
- Cisco logo (c) Cisco Systems, Inc.
