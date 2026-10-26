# PlayStation: the original PlayStation, the PSone and the PlayStation 2

Three classic skins from one procedural generator (`gen_skin.py`, built on the sheet layouts and
preview renderer of `skins/ember/gen_skin.py`, by way of `private-repo/skins/games/consoles/` for
its anti-aliased shape helpers), a theme each. The real marks used are the colour PlayStation logo
(About spot of PlayStation and PSone) and the "PS2" letters of the PlayStation 2 logo (main
titlebar); everything else is drawn by the script.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py ps2            # some (ps1, psone, ps2)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `PlayStation.wsz`, `PSone.wsz`, `PlayStation-2.wsz` and `preview-<theme>.png` here;
sheets in `out/<theme>/` (`out/` is ignored), rasterised logos in `out/scratch/`. Deterministic.

## Themes

Shared across the three: the controller's four symbols in their printed colours. The transport
glyphs take them (play is the green triangle, stop the pink square, pause the circle's red, the
skips the cross's blue), each toggle wears one (EQ triangle, PL square, ON circle, AUTO cross,
grey when off, coloured when on), and the clutter bar's lit letters use them too (V in the logo's
yellow). The checks at the end of `gen_skin.py` keep the title box flat, the slider rows uniform
and text.bmp's ink well clear of the display colour.

- **PlayStation** (`ps1`, the original, 1994):
  - Light grey ABS (#c6c7ca) for every frame, with moulded ribs either side of the titles and
    along the front, like the console's ribbed back; dark grey lettering, "PlayStation" in the
    main titlebar, "CD PLAYER" (with a disc) over the playlist.
  - Black recessed displays like the BIOS CD player; the analyzer runs through the logo's red,
    yellow, green and blue.
  - Round grey ABS transport buttons set in a darker recess, as on the CD player screen; small
    rectangular keys (like RESET and POWER) for shuffle and repeat, with the green power LED lit
    when on. Grey slider knobs with grip lines.
  - The equalizer is the BIOS Memory Card screen: blue fading to black inside the grey frame, the
    displays outlined in pale grey like the card slots.
  - The colour PlayStation logo in the About spot.
- **PSone** (`psone`, 2000, with its LCD screen):
  - White, softly rounded: white gradient frames, pill keys and round white transport buttons,
    grey glyphs coloured as above, light blue slider fills, round knobs.
  - The main window is the PSone's 5" LCD: one dark screen in the white frame holding the time,
    analyzer, title and info rows, with thin dividers; a speaker grille of perforations below the
    buttons. "PSone" in the titlebar as the console spells it ("PS" bold, "one" light).
  - Playlist: white with dark grey text, the current track in blue.
  - The colour PlayStation logo in the About spot.
- **PlayStation 2** (`ps2`, 2000):
  - Matte black titlebars and frames with fine grooves, like the console's ribbed front; the blue
    "PS2" logo centred in the main titlebar.
  - The main and equalizer windows are the PS2 browser: a deep blue gradient with faint floating
    translucent towers of stacked cubes and specks of the boot sequence's blue particles (kept
    out of the rows the slider thumbs travel). The equalizer is titled "SYSTEM CONFIGURATION", the
    playlist "BROWSER", after the system menu's two screens.
  - Glossy black DualShock 2 buttons with the coloured symbol glyphs (pressed ones glow); toggles
    are the browser's blue outlined boxes, filled blue when on. Diamond thumbs, glowing blue
    fills.
  - The About spot holds the boot sequence's swirl of particles gathering into a blue orb.

## Limits

- Colours are from memory of the hardware and BIOS screens (no published values): the PS1 grey,
  the Memory Card gradient and the PS2 browser blue may not match screenshots exactly.
- The PS1 BIOS CD player and Memory Card screens are evoked (black displays, round buttons, the
  blue gradient) rather than reproduced; their layouts don't fit Winamp's.
- The PS2 towers are small and faint: the main window has little free background, and they must
  stay out of the slider rows.
- The PS2 logo is 10px tall in the titlebar; its thin strokes are anti-aliased rather than crisp.

## Sources

- PlayStation colour logo: https://commons.wikimedia.org/wiki/File:Playstation_logo_colour.svg
  (`source/logo-ps1-colour/logo.svg`), composited once in the About spot of PlayStation and PSone.
- PlayStation 2 logo: https://commons.wikimedia.org/wiki/File:PlayStation_2_logo.svg
  (`source/logo-ps2/logo.svg`); only the "PS2" letters are used (cropped, the TM and the
  "PlayStation 2" line left out), lightened slightly so the dark blue reads on black.
- Both rasterised with `rsvg-convert` and box-downsampled.
- PlayStation, PSone and PS2 marks and logos (c) Sony Interactive Entertainment.
