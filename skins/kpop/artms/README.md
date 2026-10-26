# ARTMS: the group, its members, their objekts, light and dark

Twenty-two classic skins from one generator (`gen_skin.py`, forked from `skins/ember/gen_skin.py`:
same sheets, layouts and preview logic), a theme each, with a clean black/white body and the
members' COSMO colours as accents. The real marks used are the ARTMS wordmark in the titlebar, the
members' names and signatures, and (in the objekt themes) their objekt photos; everything else is
drawn by the script. It needs Pillow and numpy (system Python).

```sh
/usr/bin/python3 -I gen_skin.py                    # all of them
/usr/bin/python3 -I gen_skin.py artms kimlip       # some (see Themes)
/usr/bin/python3 -I gen_skin.py heejin --objekt    # = heejin-objekt
/usr/bin/python3 -I gen_skin.py artms --light      # = artms-light
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `ARTMS.wsz` and `preview.png`, `ARTMS-<Name>.wsz`, `ARTMS-<Name>-Objekt.wsz`,
`ARTMS-Light.wsz`, `ARTMS-<Name>-Light.wsz`, `ARTMS-<Name>-Objekt-Light.wsz` and
`preview-<theme>.png` here; sheets in `out/<theme>/` (`out/` is ignored). Deterministic (fixed
noise seeds, fixed zip timestamps). Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

Theme keys: `artms`, the members `heejin`, `haseul`, `kimlip`, `jinsoul`, `choerry`, each member
with `-objekt`, and every one of those with `-light`.

- **ARTMS** (`artms`): five member colours: transport buttons in member order, volume/EQ/analyzer
  ramps through all five, one signature under each member's button.
- **Member** (`heejin`, `haseul`, `kimlip`, `jinsoul`, `choerry`): her colour as the single
  accent, her name beside the logo and in the EQ/playlist titles, her name ink and signature in
  the main window.
- **Member objekt** (`<member>-objekt`): the member theme plus her objekt photos: her face in the
  main window's free bottom-right corner, a second photo darkened behind the EQ's label column.
  Photos and face boxes are in `OBJEKT_PHOTOS` near the top of the script, each with a feature box
  (eyes to chin). The photo is placed so that box sits where nothing is drawn over it; the build
  asserts 0 px of overlap with an occupancy mask of everything drawn on top (the EQ's dB labels
  are dropped to free that column).
- **Light** (`<any of the above>-light`): the same design inverted (every neutral runs through
  `N()`: near-white body, dark ink, black logo, white displays with dark digits and text); member
  colours unchanged. The objekt-light themes use other photos, `OBJEKT_PHOTOS_LIGHT`, framed in
  the free areas and melting into the light body.
- Playlist font: Arial.

## Limits

- None noted.

## Sources

- Assets are read at generation time, never copied here: the ARTMS logo, signatures and names
  from `ATOM02` (the objekts-archive repo's `back_templates/Atom02/white/`), photos from
  `OBJEKTS` (`artms-objekts/objekt.<member>/` in the same repo), composited into the sheets.
- ARTMS logo, signatures and photos (c) MODHAUS.
