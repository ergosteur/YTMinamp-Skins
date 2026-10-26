# Consoles: Xbox and PlayStation 3 dashboards

Six classic skins from one procedural generator (`gen_skin.py`, built on the sheet layouts and
preview renderer of `skins/ember/gen_skin.py`, by way of `private-repo/skins/apps/streaming/` for
its anti-aliased shape helpers), a theme each. The real marks used are the PlayStation logo and
four eras of the Xbox symbol, each once, in the About spot; everything else is drawn by the
script. The themes share the drawing code in two families, "light" (the 360 dashboards) and
"dark" (PS3, the original Xbox, Series), each theme being its family's defaults plus overrides in
`THEMES`.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py ps3 xbox-og    # some (xbox-360, ps3, xbox-og, xbox-series,
                                               #   xbox-360-metro, xbox-360-nxe)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Xbox-360.wsz`, `PS3.wsz`, `Xbox-Original.wsz`, `Xbox-360-NXE.wsz`,
`Xbox-360-Metro.wsz`, `Xbox-Series.wsz` and `preview-<theme>.png` here; sheets in `out/<theme>/`
(`out/` is ignored), scratch files (the rasterised logo) in `out/scratch/`. Deterministic. Each .wsz
is finished by `skins/genex_wacup.py`.

## Themes

- **Xbox 360** (`xbox-360`, the original "Blades" dashboard, 2005-2008):
  - The white console shell for the window bodies (a soft white-to-silver gradient, grey
    outline), glossy two-tone green bars (#d2ee9a to #4f9e1e, the dashboard's #9bc848 in
    between), white "XBOX 360" lettering, silver gloss bars when unfocused.
  - The five blades as the clutter bar: its five letters are stacked blade edges, top to bottom
    in the dashboard's left-to-right order: Marketplace (dark green), Xbox Live (green), Games
    (lime), Media (orange), System (grey). Pale when off, full colour with a white letter when
    on. The Media blade's orange also marks the main titlebar and the playlist title ("Media"),
    as the music player lived in that blade.
  - The transport as controller face buttons: play is the green A, stop the red B, pause the
    yellow Y, previous/next/eject silver; translucent gloss with the glow at the bottom edge.
  - Chunky rounded tabs for every toggle (shuffle/repeat, EQ/PL, ON/AUTO, PRESETS, the
    playlist's buttons): white gloss, green gloss when on. Seek and volume rails are recessed
    silver grooves with a green fill; the seek thumb is a green tab with a green tail behind it
    (the format can't fill the played part).
  - Displays are pale green-white with a green rim and #107c10 lettering (text.bmp's ink, so the
    app's title is #107c10 too).
  - The About spot holds the guide button, drawn from scratch: a chrome sphere with the green X in
    the four-quadrant ring of light (gaps at 12, 3, 6 and 9 o'clock, all four quadrants lit).
- **PS3** (`ps3`, the XrossMediaBar):
  - The main and EQ windows are the XMB: a deep blue vertical gradient (the classic blue
    background; the monthly colours are left out) with the wave ribbon flowing along the bottom,
    drawn as 18 thin translucent lines that swell and pinch around a soft glowing core, and a
    fainter strand behind the displays. The wave stays out of the rows the seek and volume thumbs
    slide along, which must be uniform across.
  - Frames and titlebars are piano-black gloss (a reflection over the upper half), with
    letter-spaced "PLAYSTATION 3" / "EQUALIZER" / "MUSIC" titles; the playlist title carries
    XMB's Music category note.
  - Thin white lettering and plain white glyphs throughout (Noto Sans Light/Regular stands in for
    the XMB's Rodin); pressed buttons glow. Displays are flat dark navy with a thin light-blue
    rim, white ink. Sliders are 1px lines with a white fill and a white dot or bar for the thumb.
  - The PlayStation logo, white, in the About spot.
- **Xbox Original** (`xbox-og`, the 2001 dashboard):
  - Near-black green body with the dashboard's organic green tubes (three thick glowing strands
    along the bottom and behind the displays) over a faint warped wire-frame mesh.
  - Black console-gloss bars with a widely spaced green "XBOX".
  - The transport and sliders as glowing green jewels (glossy orbs with a bright core and a
    halo); toggles are green jewel capsules when on, dark green when off.
  - Dark green displays with yellow-green (#b4f046) lettering; the 2001 X symbol (green and
    silver) in the About spot.
- **Xbox 360 NXE** (`xbox-360-nxe`, the 2008 New Xbox Experience):
  - The default theme's soft sky-blue-to-green gradient with white light streaks; the displays
    are white cards with soft drop shadows, and the EQ's slider card has two angled cards peeking
    from behind it at each side, as in the carousel.
  - White glass titlebars with dark lettering and the era's chrome sphere logo by the title.
  - Keeps the 360's controller face buttons, glossy tabs and the guide button in its ring of
    light.
- **Xbox 360 Metro** (`xbox-360-metro`, the 2011 dashboard):
  - Flat white panels and flat #107c10 tiles, no gloss, square corners, light type.
  - The main titlebar is the dashboard's pivot: home, social, video, games, **music** (current,
    bold), apps, settings; the other titles are lowercase ("equalizer", "music").
  - Transport and toggles as flat green tiles (eject and "off" toggles light grey), thin rails
    with a green fill and dark bar thumbs. The flat 2012 sphere logo in the About spot.
- **Xbox Series** (`xbox-series`, the 2020 dashboard):
  - The Fluent dashboard's dark greys (#1a1a1a body, #2b2b2b displays, #2d2d2d tiles), flat
    titlebars with "Xbox" in white.
  - Rounded tiles for the transport (play in Xbox green) and toggles (green when on), thin rails
    with a green fill and white disc thumbs with a green centre.
  - The current green sphere logo (the symbol from the stacked 2019 logo) in the About spot.

## Limits

- The Blades' exact colours aren't published and no source found online gives them per blade;
  they're from memory of the 2006+ default theme (with the Marketplace blade) and the brief: the
  two greens and the lime may not match screenshots exactly. They're the `BLADES` list at the top
  of `gen_skin.py`.
- The PS3's default background changes colour by month; this uses the classic blue.
- NXE's avatars aren't depicted; its "default" background is approximated as a blue-to-green sky.
- Metro and Series use Noto Sans in place of Segoe (not installed).
- The seek bar can't fill the played part (see the Xbox 360's tail).

## Sources

- PlayStation logo: https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/playstation.svg
  (Simple Icons), in `source/logo-playstation/`, rasterised with `rsvg-convert`.
- Xbox logos, from Wikimedia Commons, each composited once (rasterised with `rsvg-convert`;
  lockups are cut down to their symbol at generation time):
  - Original: https://commons.wikimedia.org/wiki/File:Xbox_2001_Symbol.svg
    (`source/logo-xbox-2001/`)
  - NXE: https://commons.wikimedia.org/wiki/File:Xbox_logo_(2010).svg (`source/logo-xbox-2010/`)
  - Metro: https://commons.wikimedia.org/wiki/File:Xbox_logo_2012_cropped.svg
    (`source/logo-xbox-2012/`)
  - Series: https://commons.wikimedia.org/wiki/File:Xbox_2019_Green.svg
    (`source/logo-xbox-2019/`)
- The Blades skin's guide button (and NXE's) is drawn, not downloaded.
- Xbox logos and marks (c) Microsoft Corporation.
- PlayStation logo (c) Sony Interactive Entertainment.
