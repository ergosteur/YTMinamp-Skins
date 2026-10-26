# Apple Hardware: the iMac G3 in its translucent colours and the unibody MacBook Pro

Eight classic skins from one procedural generator (`gen_skin.py`, based on the structure of
`skins/ember/gen_skin.py`: pieces, sheet layouts, preview; with techniques from the sibling
`private-repo/skins/devices/ipod/` generator), a theme each. The one mark used is the Apple logo,
once per skin, in the About spot (bottom right): the six-colour logo of the era on the iMacs, the
lid's glowing white logo on the MacBook Pro. Everything else is drawn by the script, including
the "iMac" pixel wordmark.

```sh
/usr/bin/python3 -I gen_skin.py                         # all of them
/usr/bin/python3 -I gen_skin.py imac-lime macbook-pro   # some (imac-bondi, imac-blueberry,
                                                        #   imac-strawberry, imac-lime, imac-grape,
                                                        #   imac-tangerine, imac-graphite,
                                                        #   macbook-pro)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `iMac-G3-Bondi-Blue.wsz`, `iMac-G3-<Colour>.wsz` (Blueberry, Strawberry, Lime, Grape,
Tangerine, Graphite), `MacBook-Pro-Unibody.wsz` and `preview-<theme>.png` here; sheets in
`out/<theme>/` (`out/` is ignored), scratch files (the rasterised logos) in `out/scratch/`.
Deterministic (fixed noise seed, fixed zip timestamps).

## Themes

The iMac G3 themes share one design, in each colour:

- **Plastic**: each colour is drawn as translucent plastic over a white inner shell: fine
  horizontal pinstripes, soft bright patches where the shell is thin, darker sides, a glossy
  curved highlight on the titlebars and the lower half, a saturated rim. Through the lower half
  of the main window (and the playlist's bottom) the inner structure shows faintly: a logic board
  with chips, screw bosses, a ribbon cable, moulded ribs.
- **Front**: the screens sit in an "ice" (translucent white) panel, as the iMac's CRT sat in its
  ice surround; the screens are one L-shaped piece of dark CRT glass, lit in a pale tint of the
  plastic colour. The seek bar is the CD drive's slot (its thumb a disc peeking out).
- **Buttons**: ice-white translucent keys with glyphs in a deep shade of the body colour; the
  play button is the round "hockey puck" USB mouse seen from above (coloured disc, its button
  half behind a seam, gloss spot). Toggles (shuffle, repeat, EQ, PL, ON, AUTO) carry the iMac's
  green power light when on. Titlebar buttons are round ice buttons; the "iMac" wordmark sits on
  an ice capsule.
- **Logo**: the six-colour Apple logo. Each of its 15 rows takes the stripe colour at that height
  in the source raster, so the bands stay crisp.

Apple published no colour values, so the tones are read off product photos:

- **iMac G3 Bondi Blue** (`imac-bondi`, the 1998 original): #008EAA (the paint chip "Bondi blue"
  is #0095B6; the plastic reads deeper and greener over white).
- **iMac G3 Blueberry** (`imac-blueberry`, 1999): #1E60C0.
- **iMac G3 Strawberry** (`imac-strawberry`, 1999): #DA3462.
- **iMac G3 Lime** (`imac-lime`, 1999): #6ABA2C.
- **iMac G3 Grape** (`imac-grape`, 1999): #683E9C.
- **iMac G3 Tangerine** (`imac-tangerine`, 1999): #F6841E.
- **iMac G3 Graphite** (`imac-graphite`, iMac DV Special Edition, late 1999): #62666E.
- **MacBook Pro Unibody** (`macbook-pro`, 2008-2012):
  - Body: bead-blasted aluminium: a soft top-to-bottom gradient with a fine isotropic grain and a
    faint mottle, a bright chamfered edge; "MacBook Pro" engraved in the titlebar.
  - Displays: glossy black glass bezel (with a faint diagonal reflection and the iSight camera
    dot) round a black screen; white text, Aqua-blue analyser. The playlist and album art sit
    behind the same black bezel.
  - Keys: the transport, toggles and playlist buttons are black chiclet keys with white glyphs,
    sunk into wells cut in the aluminium; pressed keys go darker. Eject is the keyboard's eject
    key. Toggles light the caps-lock key's green LED when on. Slider thumbs are small black keys;
    slider fills are white, like the backlit keys and the volume HUD.
  - Logo: the lid's glowing white Apple logo in the About spot, with a soft halo.

## Limits

- The balance slider can't show its side, so its fill grows out from the centre both ways.
- The seek bar shows no progress fill (only the thumb moves), so it's drawn as a drive slot.
- The main title is drawn by the app in TrueType in text.bmp's ink (each theme's pale display
  colour), which reads on the dark glass; the preview draws it that way.
- The iMac colours are sampled by eye from photos, not published values.

## Sources

- Six-colour Apple logo: `source/logo-rainbow/apple-rainbow.svg`, from Wikimedia Commons,
  https://upload.wikimedia.org/wikipedia/commons/8/84/Apple_Computer_Logo_rainbow.svg
- Apple logo: `source/logo-apple/apple-logo.svg`, from Wikimedia Commons,
  https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg
- Both are rasterised at build time with `/usr/bin/rsvg-convert` and used only as alpha shapes /
  colour samples (opened with Pillow), composited once per skin.
- Colour research: model and colour names from EveryMac's iMac G3 colour guide
  (https://everymac.com/systems/apple/imac/faq/imac-g3-which-models-are-which-colors.html); tones
  sampled by eye from photos.
- Apple logo (c) Apple Inc.
