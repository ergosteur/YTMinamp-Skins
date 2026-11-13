# HeeJin: four personal skins built around two unrelated sets of candid HeeJin (ARTMS) photos

Four skins from one generator (`gen_skin.py`, written from scratch for this folder - not based on
`skins/ember/gen_skin.py` or any sibling generator), in two pairs. Lace Noir/Bunny Pop and their
photo-forward companions Parasol/Plushie each have their own complete design: palette, titlebar,
buttons, EQ, playlist and font treatment (Parasol/Plushie reuse Lace Noir/Bunny Pop's palette and
EQ/playlist/gen-window styling exactly - see "Themes" below for why - but the main window is a
different layout). The only things all four share are this file's generic canvas/bevel/pixel-font
plumbing and the `genex_wacup.py` finishing step every skin in this collection uses. Every theme
composites an actual cropped photo of HeeJin into the main window; everything else is drawn from
rectangles, bevels and a pixel font made for this skin. No logos or third-party marks are used.

```sh
/usr/bin/python3 -I gen_skin.py                 # all four
/usr/bin/python3 -I gen_skin.py noir parasol    # just these (noir, bunny, parasol, plushie)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `HeeJin-LaceNoir.wsz` / `HeeJin-BunnyPop.wsz` / `HeeJin-Parasol.wsz` /
`HeeJin-Plushie.wsz` and a matching `preview-<theme>.png` here; sheets in `out/<theme>/` (`out/`
is ignored). Deterministic. Each `.wsz` is finished by `skins/genex_wacup.py`.

## Themes

The `source/` photos are two unrelated shoots/moods, not one outfit: `heejin-fan-01..06.jpg` (dark
lace fan, folding parasol, grey cable-knit, deep red lip, a vertical-ribbed black curtain) and
`heejin-bunny-01..04.jpg` (a plush bunny-eared hood, teal knit, Adventure Time plushies, pale blue
backstage light, a fan-meet candid rather than a studio shoot). Both read as strong, distinct
Winamp-skin material on their own, so both got a full theme rather than picking one.

- **Lace Noir** (`noir`): near-black chassis (body `#131217`, highlight `#2e2c36`) with a vertical
  curtain-rib texture (echoing the photos' pleated backdrop) on every tiled frame.
  Deep red (`#962437`→ accent `#cd445a`) for the lit/selected state, pewter-silver (`#adb0ba`) for
  the idle one, warm ivory (`#e0d5ca`) text. Transport, EQ sliders and the volume/balance ramps go
  silver→red with level. The titlebar/frame tops get a small zig-zag "lace" trim instead of a
  grill. Portrait: `source/heejin-fan-04.jpg` (profile, eyes closed, chin clear - the one frame of
  the six where nothing crosses the lower face). Playlist: ivory `Normal` / red `Current` on
  near-black `NormalBG`, a dark maroon `SelectedBg`. Font: the shared pixel font, ivory on the
  dark chassis.
- **Bunny Pop** (`bunny`): a light, pastel chassis instead of a dark one - icy blue body
  (`#cde3f7`), teal accent (`#196796`→highlight `#469ec7`), pink (`#e78eb1`→highlight `#f7bdd0`)
  and pale yellow (`#f3df8c`) for the lit/selected states, dark navy ink (`#1a283a`) for text on
  the light chassis. Buttons and frames are corner-rounded (a few pixels clipped to the
  surrounding colour) rather than square, and the titlebar/frame-top trim is a row of small plush
  "scallops" in pink/yellow instead of a lace zig-zag. EQ sliders and volume/balance ramp teal→
  yellow→pink. Portrait: `source/heejin-bunny-02.jpg` (peace sign, open smile, full face to
  camera - the cleanest eyes-to-chin of the four; `01` pulls the sweater collar up over the chin,
  `03`/`04` look down at the plushies). Playlist: dark-navy `Normal` / muted-pink `Current` on a
  light `NormalBG`, a bright pink `SelectedBg`. Text drawn on a dark display plate (the titlebar
  nameplate, `gen.bmp`'s letters) switches to a bright ink there, since the chassis's dark-on-light
  ink would be unreadable on those.

- **Parasol** (`parasol`) and **Plushie** (`plushie`): photo-forward companions to Lace
  Noir/Bunny Pop, added after the fact at the user's request, once Lace Noir and Bunny Pop were
  already finished - their own code paths (`make_main`, `FREE_MAIN`, `photo_layer`) are untouched,
  so rebuilding still reproduces `HeeJin-LaceNoir.wsz`/`HeeJin-BunnyPop.wsz` byte-for-byte. Same
  two palettes and playlist/gen-window styling (window titles "HEEJIN EQUALIZER"/"HEEJIN
  PLAYLIST"), but the main window (`make_main_big()`) is a different layout and every other sheet
  it uses is redrawn small and photo-blended: `monoster.bmp` drops the "MONO"/"STEREO" text for a near-blank sheet with a tiny
  2x2 LED dot; `shufrep.bmp`'s four rectangular buttons become a dot-plus-one-letter accent ("+S",
  "+R", "+E", "+P"); `balance.bmp` is, like the seek bar, the photo-sampled track with one slim
  line in every frame, and only the thumb moves; `posbar.bmp`'s track is sampled straight from the composited main window (so
  its right two-thirds *is* the photo) with a slim line instead of a bevelled trough. Portraits:
  `source/heejin-fan-03.jpg` (looking back over her shoulder, the parasol open overhead, the fan
  held off to the side clear of her face - a wider, more candid frame than Lace Noir's tight `-04`
  profile) and `source/heejin-bunny-02.jpg` for Plushie (the bunny hood and raised peace sign, on
  a plain pale-blue backdrop that blends into the chassis - the user's pick). The EQ window (`make_eqmain_big()`) carries a second photo in the dB-scale gap between the
  preamp slider and the first band, the rest of the photo running across the window behind the
  sliders and fading into a flat fill of its own backdrop colour, with the dB labels dropped and On/Auto
  redrawn as photo-sampled dot-and-letter marks (Auto, which does nothing in YTMinamp, the quieter
  one): `heejin-fan-01.jpg` for Parasol (profile, eyes closed, hair falling down the frame) and
  `heejin-bunny-04.jpg` for Plushie (the pouting close-up with Finn). equalizer.js draws the
  preamp from the same slider frames and thumb as the ten bands, so it can't be styled alone: all
  eleven are minimal together - each frame a flat column in that backdrop colour with a 2px level
  line, each thumb a slim bar - and the response graph's background is photo-sampled too. The
  frames are still opaque at runtime (one frame serves all eleven positions), so the face stays in
  the gap between the preamp and band-1 lanes. Their frame backgrounds are all one colour, the backdrop's, named in pledit.txt as
  YTMinamp's `YTMinampTransparent` key (Parasol `#0C1016`, Plushie `#C7D7FC`): in YTMinamp they're
  see-through, so the photo runs on behind all eleven sliders with only the level lines and thumbs
  over it; real Winamp/WACUP ignore the key and show flat backdrop-coloured columns. The build
  asserts the key never occurs inside a level mark; the preview draws the keyed look, and
  `out/scratch/eq-<theme>-ytminamp-vs-winamp.png` shows both. The thumbs' surrounds are the
  key too (the keyed region covers them), so in YTMinamp only each thumb's slim bar (with a 1px
  light/dark edge) shows; real Winamp shows a small backdrop-coloured tab.

Every main-window titlebar reads "JEON HEEJIN" (her full name), by request; the EQ and playlist
window titles stay theme-named so all four skins still read apart at a glance when several windows
are open.

## Feature-box occupancy

Lace Noir and Bunny Pop place HeeJin's portrait in the main window's bottom-right corner
(`FREE_MAIN`, roughly x241-273, y84-114 of the 275x116 window) - the one block nothing else is
drawn over: clear of the seek bar (ends x264,y82), the shuffle/repeat row (ends x238,y104) and the
window's own 1px outline. Every theme's eyes-to-chin feature box is checked against an occupancy
mask of everything the generator draws on top of it (`check_features()` in `gen_skin.py`, printed
at build time) and asserts 0px overlap before the sheet is saved; the build fails loudly if a
future edit breaks that. The real Winamp "About" logo spot (253-266,91-106) falls inside this
corner in every theme - rather than draw an emblem there (there's no HeeJin logo to use), the
photo shows through it, the same way the clutter bar's own background tile shows through its slot.

Parasol and Plushie place the portrait with `photo_layer_explicit()` (an exact scale/x/y, not
`photo_layer`'s "centre the box on a free rect" fit), chosen by brute-force search against
`BIG_MASK`: what the app actually paints opaquely over main.bmp at runtime, not every control's
hit rectangle. Hard keep-outs are the title box (marquee.js blanks it with text.bmp's solid space
cell; the TrueType title's caps and descenders, y24-35), the kbps/kHz and time digits, the
play/work indicator, the visualizer, the clutter bar and the transport buttons; the volume/balance
and seek thumbs block only their travel lanes; and the photo-sampled sprites (titlebar strip,
mono/stereo, EQ/PL, shuffle/repeat, balance and seek track, all copied from the finished main.bmp
at their own on-window positions) block only the small marks drawn into them - which are pushed to
those sprites' outer edges (mono/stereo dots at x212/x266, EQ/PL dot-over-letter columns at
x219-221/x262-264). That leaves a clear face band right of the balance lane between the title box
and the seek lane. The search (largest scale whose box lands with 0px overlap while the photo still
covers all 116px of height and reaches the right edge) put both feature boxes at **x222-262,
y36-72** (Parasol 40x35 at scale 0.15, photo x150-275; Plushie y40-72, 40x32 at scale 0.0985,
photo x181-275): the hair runs up under the photo-sampled titlebar to the window's top edge, the seek
lane crosses the neck/shoulders below the chin, and the shuffle/repeat accents sit over the
shoulders. The EQ photo is placed the same way against `EQ_MASK` (what equalizer.js paints
opaquely over eqmain: titlebar, close, the On/Auto sprites, Presets, the graph, the eleven slider
lanes and the redrawn PREAMP and band labels), inside the dB gap: Parasol's box lands at **x35-78, y62-106**
(43x44, scale 0.225), Plushie's at **x35-78, y54-102** (43x48, scale 0.1115). The main titlebar's title is a small TINY-font "JEON HEEJIN" at the left, over the
chrome, with the standard 9x9 buttons.

## Limits

- Colours above are the palette as coded, read by eye off the photos (grey cable-knit, deep red
  lip, pale teal knit, pastel bunny plush) rather than picked from single sampled pixels - fabric
  texture and directional lighting in the photos make any one pixel noisy, so this is a curated,
  representative palette, not a pixel-exact one.
- Each photo crop is placed by eye from a 100px reference grid overlaid on the source JPEG, not
  measured precisely - fine for a feature box, not frame-accurate.
- Lace Noir and Bunny Pop use one photo each (the main window); Parasol and Plushie add a second
  in the EQ window's dB gap. Playlist and gen windows stay plain chassis in all four.
- The shared pixel font is one design recoloured per theme rather than four distinct typefaces;
  the themes differ instead in chassis colour, bevel shape (square vs. corner-rounded), trim motif
  (lace zig-zag vs. plush scallop) and where on the window the ink needs to flip bright instead of
  dark (see Bunny Pop's "Text drawn on a dark display plate" note above).
- Unused: `heejin-bunny-01.jpg` (the sweater collar pulled up over the chin), `heejin-bunny-03.jpg`
  (Plushie's main photo until the user picked `-02`), `heejin-fan-02.jpg`,
  `-05.jpg`, `-06.jpg` (the fan or lace crosses the lower face in each).
- Parasol's photo covers about 45% of the main window's width, Plushie's about a third: both fill
  the full height, but how far left each can reach follows from how much of the source frame lies
  left of the face (`bunny-02` has less), at the scale that fits the face band.

## Sources

- `source/heejin-fan-01..06.jpg`, `source/heejin-bunny-01..04.jpg`: candid HeeJin photos, already
  placed in this folder's `source/` for this skin's brief. No further attribution (photographer,
  original post) is known to this session to credit.
- Parasol/Plushie's photo-forward main-window layout (full-height, right-anchored portrait; chrome
  compressed to a left column; controls allowed to sit over the photo's lower/peripheral area) was
  described to this session from three photo-skin examples the user had downloaded elsewhere, as a
  layout idea only - no file from any of those three was read, copied or redistributed; nothing
  here is derived from their assets, code or exact proportions.
- Everything else (every bitmap, the pixel font, the lace/scallop trims, the textures) is drawn by
  `gen_skin.py` from rectangles, bevels and code - no other skin's assets or layout were copied.
