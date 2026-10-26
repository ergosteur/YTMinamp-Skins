# ARTMS Club Icarus: the album "Club Icarus"

One classic skin from a generator (`gen_skin.py`, built on `skins/ember/gen_skin.py`, so the sprite
layouts are Ember's), themed on ARTMS's album "Club Icarus": the teal-green underground tunnel,
square wall tiles with a rust band, fluorescent tubes, black leather and the iridescent feather
wings. The real marks used are the album cover (the main window's backdrop), a wings-and-tunnel
photo (the EQ's backdrop) and the ARTMS wordmark (titlebar). The "Club Icarus" pixel serif and the
time digits are drawn by the script.

```sh
/usr/bin/python3 -I gen_skin.py
```

Outputs: `ARTMS-Club-Icarus.wsz` and `preview.png` here (main window, EQ, playlist and a gen.bmp
frame at their real positions, 2x); sheets in `out/` (ignored). Deterministic (fixed noise seed).
Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

- **Club Icarus** (one theme): the tunnel's teal-green, square wall tiles with a rust band,
  fluorescent tubes, black leather and iridescent feather wings; the cover behind the main window
  and the wings-tunnel photo behind the EQ. Font: Arial.

## Limits

- None noted.

## Sources

- `source/cover.webp`: the album cover, the main window's backdrop and the preview's album art.
- `source/wings-tunnel.jpg`: the EQ's backdrop.
- The ARTMS wordmark's ink alpha from the objekts-archive repo
  (`~/gitea/ergosteur/objekts-archive/back_templates/Atom02/template-ink.png`), composited once
  into the titlebar.
- ARTMS logo, album art and photos (c) MODHAUS.
