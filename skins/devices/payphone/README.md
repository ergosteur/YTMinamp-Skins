# Payphone: the Nortel Millennium card phone in Bell Canada's 2000s livery

One skin from one generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`, keeping Ember's
sheet layouts and preview), a theme each. Bell's real 2000s mark (the gold ring with the head
profile over "Bell") appears once, in the main titlebar (titlebar.bmp, and main.bmp's own titlebar rows under it), read from `source/bell-logo-2000s.png`
at generation time and painted as on the phone's band: the ring in its gold, "Bell" in white
(the source's blue wouldn't read on the royal-blue band). Everything else is drawn: satin
gradients with horizontal grain for the faceplate, rectangles and bevels for the keys and tabs,
hand-made pixel fonts for the print, the VFD's text cells and its 5x7 dot-matrix digits. No
system fonts in the bitmaps (the preview's title uses Liberation Sans, as the app's Arial).

```sh
/usr/bin/python3 -I gen_skin.py                     # all of them
/usr/bin/python3 -I gen_skin.py millennium-bell     # some (<theme>, <theme>, ...)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Nortel-Millennium-Bell.wsz` and `preview-millennium-bell.png` here; sheets in
`out/<theme>/`, 4x crops in `out/scratch/` (`out/` is ignored). Deterministic. Each .wsz is
finished by `skins/genex_wacup.py`.

## Themes

- **Nortel Millennium (Bell)** (`millennium-bell`, Bell Canada livery of the mid 2000s): a black
  housing (#141518) round a satin-silver faceplate (#D6D9DC to #AAAEB3). Titlebars are the
  royal-blue top band (#3458C8 to #163092, #1E3EAC mid) with the phone's bilingual print "CARD
  PHONE ONLY / APPAREIL POUR CARTES SEULEMENT" in white and the gold-ring Bell mark at the right;
  the caption buttons are tiny silver soft keys. The main window is the instruction card behind
  its window (#F6F6F0) holding a long VFD: near-black (#040D0F) with teal phosphor (#70E2CC) and
  ghost cells (#0F2224): 5x7 dot-matrix time digits (1px dots on a 2px pitch, strokes bloomed
  between lit dots), dot-matrix play/pause/stop icons, three rows of ghost character cells
  under the title (text.bmp's grid, so the bitmap title and the TrueType one both sit in them),
  a cell row with kbps / KBPS / kHz / KHZ, and MONO/STEREO lit or ghosted. Under the display the
  card's printed blue tabs (#0C4E96): "FRANCAIS" (with its cedilla) and a speaker "VOLUME" tab,
  then the volume and balance sliders as blue tabs holding a VFD bar that lights up with the
  level (thumbs are small soft keys), and EQ/PL as the light-blue "Next call" tabs (#3C84B2;
  filled when on, outlined when off). The seek bar is the card reader's slot, the thumb a blue
  chip card. Transport and eject are the silver soft keys with black glyphs; shuffle and repeat
  are chrome keypad keys with a teal dot strip that lights when on; a red "911" and the black
  handset fill the About spot. The clutterbar is a column of small soft keys (lit: pressed in,
  blue letter). The EQ is the instruction card: a blue left column behind ON/AUTO (soft keys
  with a teal LED), a yellow tab (#F6C62C) round the graph (a small VFD with ghost dots and a teal
  curve), a light-blue tab round PRESETS, grey row rules, "+12DB" in the card's red (#CE202A),
  the rest in blue, sliders as grey slots filled in Bell blue. The playlist and album-art frames
  repeat the blue band (title "PLAYLIST / LISTE"), satin sides with the black housing at the
  outer edge, and a satin foot with soft keys and small VFDs for the timers.
  Playlist: #14285C on #F6F6F0 (the card), #CE202A current (the 911 red), #FAD65C selection
  (the yellow tab). Font: Arial.

## Limits

- The Bell mark is re-proportioned for legibility: the ring and the word are separated by
  colour against the source's transparent ground and scaled separately, the word to 9 px tall at
  its own proportions (38 x 9, a steep contrast curve keeps it crisp) and the ring flattened to
  46 x 7, sweeping over the word's top as on the real mark (rows 0-6 over rows 5-13, the word
  drawn on top). Both are thickened in the source before a Lanczos reduction. At the mark's real
  proportions "Bell" would be about 5 px tall and unreadable. Trial arrangements:
  `out/scratch/logo-trials.png`.
- Colours are taken from the reference photos and adjusted (the 2006 photo is washed out by
  winter light); the blue band is a plausible royal blue, not a sampled brand value.
- The main window can't hold the whole phone: the instruction card's rows (Local, Long
  Distance, 911, 611, 411) appear in spirit in the EQ (red/blue labels, rules) and the playlist
  colours, and the keypad's numerals are left off the transport keys (icons only).
- The volume, balance and EQ/PL sprites start inside the VFD (y 57/58); their top rows are the
  display's plain background, so the tabs read as printed under it. The VFD's bottom three rows
  carry no ghost cells for that reason.
- text.bmp's cells keep their gap column and row at the cell's left and top, so the space cell's
  corner is the plain display colour; its ghost dots (53 summed RGB from the background) show
  across the title row under both kinds of title, matching the ghost rows main.bmp draws above
  and below it. The ink pick lands on #70E2CC.

## Sources

- `source/millennium-bell-canada-2006.png` (c) 2006 Barraclou.com: the Bell Canada livery
  (band, print, logo placement, card layout, yellow coin return). Reference only.
- `source/millennium-bell-aliant.png`: the same phone in Bell Aliant livery, for shapes (keypad,
  soft keys, display window, card slot, handset). Reference only.
- `source/millennium-vfd-closeup.png`: the VFD (teal 5x7 dot matrix with ghost cells on black),
  the blue VOLUME / FRANCAIS / Next call tabs, the soft keys and chrome keypad. Reference only;
  colours sampled from it.
- `source/bell-logo-2000s.png` (supplied by the user; 300x169 palette PNG on a transparent
  ground): Bell Canada's 2000s logo. Composited once, into titlebar.bmp's main titlebars, from
  colour masks at generation time.
- Nothing was downloaded; nothing is composited from the photos.
- Bell logo (c) Bell Canada. Nortel and Millennium are names of Nortel Networks.
