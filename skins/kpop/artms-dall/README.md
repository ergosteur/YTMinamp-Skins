# ARTMS Dall: the album "Dall"

One classic skin from a generator (`gen_skin.py`, forked from `skins/ember/gen_skin.py`, so it has
the same sheets, layouts and preview logic), themed on ARTMS's first album "Dall" ("Devine All
Love & Live", title track "Virtual Angel"). The real marks used are the ARTMS wordmark in the
titlebar and the album cover, hazed into the main window and the EQ, with one member's face in the
main window's bottom-right corner. Everything else is drawn by the script, including an original
italic "<Dall>" in pixel lettering; the tagline is set in Noto Serif Italic. It needs Pillow and
numpy (system Python).

```sh
/usr/bin/python3 -I gen_skin.py
```

Outputs: `ARTMS-Dall.wsz` and `preview.png` here; sheets in `out/` (ignored). Deterministic (fixed
seeds).

## Themes

- **Dall** (one theme): a periwinkle to lilac to pink pastel body with glitter grain, and
  pearl-chrome bubble buttons with deep violet glyphs. The displays are deep violet glass with
  pearl-pink italic serif digits. The titlebar has the ARTMS wordmark and the "<Dall>" lettering.
  "Devine All Love & Live" runs under the transport buttons. The playlist and Media Library use
  dark violet lists in pastel frames. Playlist: #E8D8F8 on #1E1438, #FFB6D9 current, #4A3080
  selection. Font: Arial.

## Limits

- None noted.

## Sources

- The script reads its assets when it runs and never copies them into this folder:
  `source/cover.webp` (the cover, composited into the main window and EQ) and the ARTMS wordmark
  ink from the objekts-archive repo's `back_templates/Atom02/template-ink.png`.
- `source/package-a.webp`, `source/package-b.webp`: palette and texture references only.
- Noto Serif Italic (system font) for the tagline.
- ARTMS logo, album art and photos (c) MODHAUS.
