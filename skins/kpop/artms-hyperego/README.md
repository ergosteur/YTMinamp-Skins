# ARTMS Hyper-Ego: the album "Hyper-Ego"

One classic skin from a generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`, same sheet
layouts), after ARTMS's album "Hyper-Ego". The real marks used are the cover's eye strips (behind
the main and EQ windows) and the ARTMS wordmark. Block caps are the wordmark and hand-drawn pixel
letters; the playlist's script title is set in the system font URW Z003.

```sh
/usr/bin/python3 -I gen_skin.py
```

Outputs: `ARTMS-Hyper-Ego.wsz` and `preview.png` here; sheets in `out/` (ignored).

## Themes

- **Hyper-Ego** (one theme): the cover's eye strips behind the main and EQ windows, the ARTMS
  wordmark, a script playlist title. Playlist: #2A2C30 on #F4F5F7, #000000 current, #C9D6E0
  selection. Font: Arial.

## Limits

- None noted.

## Sources

- `source/eyes-cover.webp`: the eye strips behind the main and EQ windows (composited).
- The ARTMS wordmark's ink from the objekts-archive repo's
  `back_templates/Atom02/template-ink.png`.
- URW Z003 (system font, AGPL with font exception) for the playlist's script title.
- ARTMS logo, album art and photos (c) MODHAUS.
