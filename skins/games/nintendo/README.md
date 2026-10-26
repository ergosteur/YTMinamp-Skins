# Nintendo: the DS, DSi and 3DS handhelds, the Wii and the Switch

Five classic skins from one procedural generator (`gen_skin.py`, built on the sheet layouts and
preview renderer of `skins/ember/gen_skin.py`, by way of `private-repo/skins/games/consoles/` for
its anti-aliased shape helpers), a theme each. The real marks used are each console's logo or
wordmark, once per skin (in the main titlebar or the About spot); everything else is drawn by the
script.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py wii ds         # some (ds, dsi, 3ds, wii, switch)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Nintendo-DS.wsz`, `Nintendo-DSi.wsz`, `Nintendo-3DS.wsz`, `Wii.wsz`,
`Nintendo-Switch.wsz` and `preview-<theme>.png` here; sheets in `out/<theme>/` (`out/` is
ignored), scratch files (the rasterised logos) in `out/scratch/`. Deterministic.

## Themes

The handhelds are drawn as clamshells. For the DS, DSi and 3DS, the main window is the top screen
and the equalizer is the bottom touch screen. Each window body is the console's shell, and its
displays, sliders and EQ/PL buttons sit in one screen inside a dark bezel. The seek bar and
transport sit on the shell below. The equalizer's screen has the console's controls in its narrow
margins: the D-pad on the left (the 3DS adds the circle pad above it), ABXY on the right (the DS
models add Start/Select dots below).

- **Nintendo DS** (`ds`, DS Lite, Polar White, and the DS menu): white gloss shell. The screens
  are the menu's graph paper (a pale grid). Displays are white with a light blue-cyan rim.
  Lettering uses WenQuanYi Zen Hei Sharp's bitmap strike, drawn crisp (no anti-aliasing) as a
  stand-in for the DS's pixel system font, and the time digits use it too. Buttons are flat white
  with a grey outline; pressed or on, they turn blue-cyan. The real Nintendo DS wordmark is in the
  main titlebar, and the About spot has the menu's analogue clock.
- **Nintendo DSi** (`dsi`, matte black, and DSi Sound): a matte black shell with fine grain. The
  screens are a soft white gradient with faint pinstripes. The transport is the DSi menu's
  horizontal strip of icon tiles on a light strip, with the menu's position dots under it, and the
  inner camera lens sits on the hinge edge beside them. The accent is a "Sound" orange. The main
  titlebar has the real DSi wordmark followed by "Sound", and the About spot has a round orange
  bird in headphones.
- **Nintendo 3DS** (`3ds`, Aqua Blue, and the HOME Menu): aqua blue gloss with a faint metallic
  fleck. The top screen has the HOME Menu's soft white-to-grey gradient. The bottom screen shows
  faint rounded-square app slots, the HOME Menu's grid. Buttons are glossy white icon tiles, with
  a blue selection frame when pressed. The 3D depth slider is beside the top screen. The titlebar
  reads "Nintendo 3DS Sound", and the real 3DS mark (the console icon) is in the About spot,
  white.
- **Wii** (`wii`, the Wii Menu): near-white with the fine grey horizontal stripes, and #34beed as
  the accent throughout (the titlebars' bottom line, fills, selection). The displays and the EQ
  sliders sit in channel-tile frames. The main window's lower part is the menu's light grey bottom
  bar, with its blue top edge rising round the round **Wii button** in the About spot (a white
  gloss button in a blue ring, holding the real Wii logo). The transport is Wii Remote buttons:
  white gloss with grey glyphs, with play as the big round A button. All the titlebar lettering
  ("Wii Menu", "Equalizer", "Playlist", the album-art window's capitals) is drawn by the script as
  bubbly, round-capped strokes, designed for this skin. Comfortaa (OFL) is used only for the time
  digits.
- **Nintendo Switch** (`switch`, the HOME menu in **Basic Black**): #2d2d2d, white text, the cyan
  #00c3e3 selection ring. Every window is framed by the Joy-Con: a neon blue (#0ab9e6) strip on
  the left and a neon red (#ff3c28) strip on the right, with rounded outer corners at the top and
  bottom. The main window's strips carry tiny minus, stick, direction buttons and capture (left),
  and plus, ABXY, stick and HOME (right). The transport is the HOME menu's row of round dark
  buttons, ringed in cyan when pressed. Sliders are thin rails with a cyan fill and white round
  knobs. The real Switch logo, white on its red rounded square, is in the About spot. Lettering is
  Open Sans as a stand-in for the Switch's system font.

## Limits

- **DSi Sound:** no source found online describes the app's colours or a bird mascot (only its
  visualisers and its parakeet voice filter), so the orange accent and the bird in headphones
  follow the brief's description, not screenshots.
- **Colours:** the exact Aqua Blue, the DS menu's blue and the Wii grey come from memory, not
  published values. They're in `THEMES` at the top of `gen_skin.py`.
- **Size:** at Winamp's scale, the Switch Joy-Con are 4 px wide, so their buttons are only dots.
  The fixed close button (x 264) slightly overlaps the red strip in the titlebars.
- **DS menu theme colour:** the real menu lets the user pick one of 16. This skin uses blue-cyan,
  as the brief asks.

## Sources

Downloaded into `source/logo-*/logo.svg`, rasterised with `rsvg-convert` and composited once:

- DS wordmark: https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/nintendods.svg (Simple
  Icons)
- DSi wordmark: https://upload.wikimedia.org/wikipedia/commons/d/dd/Nintendo_DSi_logo.svg
  (Wikimedia Commons, "Nintendo DSi logo.svg"; Simple Icons has none)
- 3DS mark: https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/nintendo3ds.svg (Simple
  Icons; it is the console icon, not the wordmark)
- Switch logo: https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/nintendoswitch.svg
- Wii logo: https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/wii.svg
- Nintendo DS, DSi, 3DS, Wii and Nintendo Switch logos and marks (c) Nintendo.
