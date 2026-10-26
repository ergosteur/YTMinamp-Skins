# Web Nostalgia: MySpace, Facebook 2006, Neopets

Three classic skins from one procedural generator (`gen_skin.py`, forked from
`skins/ember/gen_skin.py`: same sheets, layouts and preview logic), a theme each, in the style of
2000s websites. Each skin uses the site's real wordmark once, in the main titlebar; everything
else is drawn by the script. No Neopets characters are used.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py neopets        # some (myspace, facebook-2006, neopets)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `MySpace.wsz`, `Facebook-2006.wsz`, `Neopets.wsz` and `preview-<theme>.png` here; sheets
in `out/<theme>/`, scratch files (rasterised logos) in `out/scratch/` (`out/` is ignored).
Deterministic.

## Themes

- **MySpace** (`myspace`, a 2005-07 profile): #003399 header with the #6698cb nav strip,
  light-blue boxes bordered #6698cb, #ffcc99/#ff6600 header bands, the dark music-player bar for
  the displays, a nav-link EQ titlebar, an "online now" figure, a little pink glitter. The
  titlebar's tagline is the skin's own wording.
- **Facebook 2006** (`facebook-2006`): #3b5998 bar with white links, white body with the #f7f7f7
  sidebar column, #d8dfea section bars with a #3b5998 top rule, flat blue buttons with the
  light/dark 1px bevel, bracketed bold titles, a small "f" square.
- **Neopets** (`neopets`): sky-blue header, yellow tiled diamond pattern, rounded orange-trimmed
  cream panels, glossy blue buttons, yellow/orange toggles, chunky outlined lettering, yellow
  stars, a gold NP coin drawn by the script.

## Limits

- None noted.

## Sources

The logos are read at build time from `source/` (downloaded as-is, never executed); SVGs are
rasterised with `/usr/bin/rsvg-convert`, then cropped, scaled and firmed up in Pillow, and
composited once:

- `source/logo-myspace/MySpace_logo.svg`, from
  https://commons.wikimedia.org/wiki/File:MySpace_logo.svg (the figures and "myspace.com"; the
  tagline under them is cropped off).
- `source/logo-facebook/Facebook.svg`, from https://commons.wikimedia.org/wiki/File:Facebook.svg
  (the 2005-2015 wordmark; the white letters are pulled off the blue box).
- `source/logo-neopets/Neopets_logo_2024.png`, from
  https://en.wikipedia.org/wiki/File:Neopets_logo_2024.png (the lettering only; its stars are
  removed and replaced by stars drawn by the script, so the word can be bigger in a 14px bar).
- MySpace logo (c) Myspace LLC (formerly MySpace, Inc.).
- Facebook logo (c) Meta Platforms, Inc. (Facebook).
- Neopets logo (c) Neopets, Inc.
