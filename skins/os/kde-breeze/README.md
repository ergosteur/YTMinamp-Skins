# KDE Breeze: KDE Plasma's Breeze, light and dark

Two classic skins from one procedural generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`
and keeping its sheet layouts), a theme each, made to sit beside Plasma 6 windows. The one mark
used is the KDE logo, rasterised at 16px into the About spot of main.bmp. Everything else is drawn
by the script, with the time digits, labels and titles in hand-made pixel fonts (a mixed-case
Noto-ish UI font, 5px capitals for text.bmp and gen.bmp). It needs Pillow, numpy and
`/usr/bin/rsvg-convert`.

```sh
/usr/bin/python3 -I gen_skin.py                     # all of them
/usr/bin/python3 -I gen_skin.py breeze-dark         # some (breeze-light, breeze-dark)
/usr/bin/python3 -I gen_skin.py --accent=#e93d58    # another accent colour
/usr/bin/python3 -I gen_skin.py --list              # theme names
```

Outputs: `KDE-Breeze-Light.wsz`, `KDE-Breeze-Dark.wsz` and `preview-<theme>.png` here; sheets in
`out/<theme>/` (`out/` is ignored). Deterministic (fixed zip timestamps, no noise). Each .wsz is
finished by `skins/genex_wacup.py`.

## Themes

Both share the Breeze widget style:

- Colours are copied from `/usr/share/color-schemes/BreezeLight.colors` / `BreezeDark.colors`:
  Window, Button, View and Header backgrounds, Normal/Inactive text, Link, Negative. Frames and
  outlines are the window colour mixed 20-30% towards the text, as Breeze draws them.
- Accent: Breeze blue #3daee9, or `[General] AccentColor` from `~/.config/kdeglobals` when set
  (it wasn't on the machine that built them), or `--accent`.
- Titlebars use the Header colour, title centred, plain glyph buttons (menu, minimise chevron,
  shade chevron, close); pressed shows a round backdrop, the close button's red #da4453 with a
  white cross.
- Buttons: flat, 1px rounded outline, accent outline and tint when pressed or checked (shuffle,
  repeat, EQ, PL). Shuffle/repeat are icons. EQ On/Auto are Breeze check boxes.
- Sliders: thin groove, accent fill (volume, EQ), round outlined handles.
- Displays and the playlist use the View colours. pledit.txt names Noto Sans for the title and
  playlist.

- **Breeze Light** (`breeze-light`): BreezeLight.colors. Playlist: View text on the View
  background, Link-coloured current track, #B5E0F7 selection (the accent mixed into the View
  background). Font: Noto Sans.
- **Breeze Dark** (`breeze-dark`): BreezeDark.colors. Playlist: View text on the View background,
  accent-coloured current track, #255670 selection. Font: Noto Sans.

## Limits

- The seek bar has no fill: posbar.bmp can't show progress.

## Sources

- KDE logo: `source/logo-kde/kdeapp-48.svg`, copied from the system's Breeze icon theme
  (`/usr/share/icons/breeze/apps/48/kdeapp.svg`, LGPL, KDE), rasterised at 16px and composited
  once into the About spot.
- Breeze colour schemes: `/usr/share/color-schemes/BreezeLight.colors` and `BreezeDark.colors`
  (reference only, for the colours).
- KDE logo (c) KDE e.V.
