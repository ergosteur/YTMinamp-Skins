# NMIXX: a steel-blue night with neon and the six members' colours

One classic skin from a generator (`gen_skin.py`, forked from `skins/ember/gen_skin.py` by way of
`private-repo/skins/kpop/artms/gen_skin.py`, so it has the same sheets, layouts and preview
logic). The palette is new: a steel-blue night with neon, and the six members' colours. The one
real mark is the NMIXX logo, once, in the main titlebar, rasterised at generation time.
Everything else is drawn by the script. It needs Pillow, numpy and `/usr/bin/rsvg-convert`.

```sh
/usr/bin/python3 -I gen_skin.py                # the one theme, nmixx
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `NMIXX.wsz` and `preview.png` here; sheets in `out/nmixx/` and the rasterised logo in
`out/scratch/` (`out/` is ignored). Deterministic: noise seeds and zip timestamps are fixed.

## Themes

- **NMIXX** (`nmixx`, after *Ad Mare* / "O.O" (2022) and *Fe3O4: Break* / "DASH" (2024)):
  - Body: the dusk steel blue of the *Fe3O4: Break* cover (the overpass behind the "DASH" scene;
    the cover's main tones are #101826 to #223044). A faint horizontal brushed streak suggests
    magnetite, Fe3O4 itself, the "magnetic" theme of the trilogy. The displays are near-black
    glass with steel-blue rules, and the display ink is a cool white.
  - Titlebar: the NMIXX stencil wordmark in white, with six thin bars in the member colours on
    each side. The bars follow the logo's own vertical-bar rhythm and read as "mixx". The rules
    stop clear of the buttons.
  - Transport: one member per button, in member order: Lily (previous), Haewon (play), Sullyoon
    (pause), Bae (stop), Jiwoo (next) and Kyujin (eject). NMIXX has six members, so eject takes
    the sixth colour (ARTMS has five members and keeps a white eject). Icons are white on the
    dark colours and near-black on the light ones. The playlist's mini buttons follow the same
    order.
  - Under the buttons: each member's animal as a 7-row pixel face in her colour: koala, polar
    bear, deer, chick, puppy and cat.
  - About spot (bottom right): "O.O", the debut single, as two neon rings round a dot, in the red
    neon of the *Ad Mare* cover's "Pick N Mixx Donut Shop" sign. The current playlist entry uses
    the same neon.
  - Ramps: volume, EQ sliders, the EQ graph and the analyzer step through the members without
    blending, from cool to hot: Sullyoon, Lily, Haewon, Bae, Kyujin, Jiwoo. The analyzer has them
    stacked bottom to top. Sullyoon's dark blue is lifted toward light blue for small marks
    (`lift`), or it would vanish on the body.
  - Titles: "NMIXX EQUALIZER" and "NMIXX PLAYLIST". Titles and gen.bmp's letters use a 5-wide M
    and W (`FONTT`), so "NMIXX" doesn't read as "NNIXX". text.bmp keeps 4-wide glyphs because its
    cells are 5 px.
  - Kept invariants: text.bmp's space cell is the display colour. Its ink, #E2ECFA, is what the
    app uses for the TrueType title, and it contrasts with the near-black title box. gen.bmp's
    letter rows sit at 88/96 and the preview's `lettersOf`-style scan finds all 26.
  - Playlist: #E8E8E8 Normal, the red neon current, steel-blue #1E3054 selection (which keeps
    Normal readable). Font: Arial.

### Research

**Line-up.** Lily, Haewon (leader), Sullyoon, Bae, Jiwoo and Kyujin. Jinni left on 9 Dec 2022,
after debut (Wikipedia, "Nmixx"). The group debuted on 22 Feb 2022 with *Ad Mare* / "O.O". The
fandom is NSWER (엔써), short for North, South, East, West, Route (Soompi). In the name, "N" means
now/new/next/unknown and "MIX" means combination and diversity. Their genre-switching style is
called "MIXX POP" (Wikipedia).

**Group colour.** No official group colour was found. Kprofiles lists "N/A", and the "navy and
gold" or "blue and pink" claims on content-farm pages have no source. The steel blue here is
taken from the Fe3O4 cover, not from an official colour.

**Member colours.** NMIXX did not debut with member colours. Later, JYP's official store sold
per-member pouches, and photocards in the NMIXX collect book have per-member backing colours.
Sources are TV Tropes (quoted in search results; the page refused fetching) and fan posts on X by
xinyuthingker and loserrz. The colour names agree across those sources:

| member | colour (sources) | used here | animal |
|---|---|---|---|
| Lily | baby blue / soft blue | #8CC8F2 | koala |
| Haewon | white | #F4F6FA | polar bear |
| Sullyoon | dark blue | #1E349A (lifted to #4B65CC for small marks) | deer (some say rabbit) |
| Bae | yellow | #FFD22E | chick |
| Jiwoo | red | #E82230 | puppy |
| Kyujin | pink | #FF7CB8 | cat |
| (Jinni, former) | purple | not used | |

No official hex values exist; one fan thread says outright that the members don't have a set
shade. So the hex values are this skin's own, picked to match the names and to stay distinct side
by side. The animals follow the emoji order in a fan's display name (koala, polar bear, deer,
chick, puppy, cat). A fan wiki gives Haewon the polar bear and Sullyoon the rabbit or deer, and
gives none for Kyujin. These are fan conventions, not JYP's.

**Eras used.**

- *Ad Mare* / "O.O" (2022). Latin for "to the sea", the start of the voyage to "MIXXtopia" (Korea
  Times; kbizoom on the MV's ship and jellyfish). The cover is a night street with the "Pick N
  Mixx Donut Shop" in red and orange neon, with jellyfish floating above it. That gives the neon
  accent and the "O.O" emblem (two donut rings, two wide-open eyes).
- *Fe3O4: Break* / "DASH" (2024). Fe3O4 is magnetite: the members as girls who attract like
  magnets, breaking through barriers. "DASH" breaks out of prison-like spaces and traffic lights
  (Korea Times, Korea JoongAng Daily). The cover is a glass cube with a car and a traffic light
  under a steel-blue overpass at dusk. That gives the body colour and the brushed-metal grain.

Other eras, for a future theme: "DICE" (*Entwurf*), "Love Me Like This" (*Expérgo*), "Party
O'Clock", *Fe3O4: Stick Out* / *Forward*, *Blue Valentine* (2025), *Heavy Serenade* and *Strange
Muse* (2026).

## Limits

- The balance slider can't show a side, and the seek bar has no progress fill, only the white
  thumb. Both are Winamp's own limits.
- The EQ has one slider sprite per value, so a slider's colour follows its value, not its band.
- At 10 px tall, the logo's thin bars come out about 1 px wide. It stays legible, but only just.
- Member colours and animals are fan conventions; the hex values are this skin's own.

## Sources

Downloads in `source/` are untrusted and were opened only with Pillow and rsvg-convert.

- `source/logo-nmixx/NMIXX_logo.svg`, from https://commons.wikimedia.org/wiki/File:NMIXX_logo.svg:
  the stencil wordmark, rasterised at generation time and composited once, in the main titlebar.
- `source/cover-ad-mare/ad-mare.jpg`, the *Ad Mare* digital cover, from
  https://en.wikipedia.org/wiki/File:Nmixx_%E2%80%93_Ad_Mare.jpg. Reference only, for the palette
  and motif.
- `source/cover-fe3o4-break/fe3o4-break.jpg`, the *Fe3O4: Break* digital cover, from
  https://en.wikipedia.org/wiki/File:Nmixx_Fe3O4_Break.jpg. Reference only, for the palette.
- Other sources: en.wikipedia.org/wiki/Nmixx; soompi.com (NSWER announcement); koreatimes.co.kr
  (Fe3O4: Break, Ad Mare); koreajoongangdaily.com; kbizoom.com; kprofiles.com;
  x.com/xinyuthingker and x.com/loserrz (member colours). TV Tropes and the NMIXX fandom wiki
  refused automated fetches; their content came through search-result summaries.
- NMIXX name and logo (c) JYP Entertainment.
