# LOONA: the group, its subunits and eras, dark and light

Sixteen classic skins from one generator (`gen_skin.py`, forked from `skins/ember/gen_skin.py`:
same sheets, layouts and preview logic, with Ember's fixed palette turned into per-theme
palettes), a theme each. The real logo appears once per skin, in the titlebar: the LOONA
wordmark, or the ODD EYE CIRCLE logo for Odd Eye Circle. Everything else is drawn by the script;
no cover imagery is composited into any skin. It needs Pillow and numpy (system Python). The
previews draw the main title the way the app does: an 11 px TrueType font (Liberation Sans in
place of Arial) in text.bmp's ink colour.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py --theme yyxy   # some (--theme is repeatable; bare names work too)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `LOONA.wsz`, `LOONA-<Theme>.wsz`, `LOONA-<Theme>-Light.wsz` and `preview.png` /
`preview-<theme>.png` here; sheets in `out/<theme>/` (`out/` is ignored). Deterministic (fixed
noise seeds, fixed zip timestamps). Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

The group and subunit themes run the members' own colours through the volume bar, balance, EQ
sliders and analyzer, stepping from one colour to the next without blending. In the group skin,
the EQ labels (preamp and ten bands) are the first eleven members, and Olivia Hye's silver is the
slider and seek thumbs. The era themes keep the twelve moons but use the album's own palette,
blended, for the volume bar, EQ and analyzer. Playlist font: Arial.

- **LOONA** (`loona`, `LOONA.wsz`): the twelve. A night sky with stars and the LOOΠΔ logo between
  two crescents. Twelve moons in member colours sit on a dotted orbit under the transport buttons.
  The About spot is an eclipse with the twelve as points on the corona.
- **LOONA 1/3** (`1-3`, `LOONA-1-3.wsz`): the pastel aqua and pink of *Love & Live*. The titlebar
  reads "LOOΠΔ 1/3" with the slash in YeoJin's orange. The strip shows HeeJin, HyunJin, HaSeul,
  the orange "/" for YeoJin, and ViVi.
- **Odd Eye Circle** (`odd-eye-circle`, `LOONA-Odd-Eye-Circle.wsz`): the black and white street
  look of *Max & Match*, with accents in Kim Lip's red, JinSoul's blue and Choerry's purple. The
  real ODD EYE CIRCLE logo is in the titlebar. The About spot is an odd eye: the iris is half red
  and half blue, with a purple ring.
- **yyxy** (`yyxy`, `LOONA-yyxy.wsz`): the green school tartan of *beauty&thebeat*'s uniforms,
  with burgundy lines (Yves), cream (the shirts) and Chuu's peach as the accent. The titlebar
  reads "LOOΠΔ yyxy" in lowercase.
- **[+ +]** (`plus-plus`, `LOONA-Plus-Plus.wsz`, "Hi High", 2018): the misty forest teal and
  white of the cover, with small "+" sparkles. The About spot is the cover's ringed "++" badge.
- **[X X]** (`x-x`, `LOONA-X-X.wsz`, "Butterfly", 2019): ice blue with the cover's iridescent
  pink, lavender and teal. The About spot is a butterfly.
- **[#]** (`hash`, `LOONA-Hash.wsz`, "So What", 2020): the red uniforms of the cover on black,
  under a slate-blue dusk. The About spot is a ringed "#".
- **[12:00]** (`12-00`, `LOONA-12-00.wsz`, "Why Not?", 2020): the midnight moonlight festival:
  warm black, gold stars and gold trim. The About spot is a moon-clock at midnight.
- **[&]** (`and`, `LOONA-And.wsz`, "PTT (Paint The Town)", 2021): a red velvet curtain with
  folds, slate buttons and displays, cream trim and gilt accents. The About spot is a ringed "&".
- **Flip That** (`flip-that`, `LOONA-Flip-That.wsz`, 2022): a summer garden: sage white with
  small flowers, deep leaf-green displays, lavender trim and pink accents. The About spot is a
  flower.
- **LOONA Light** (`loona-light`, `LOONA-Light.wsz`): a pale moonlit sky with faint lavender stars
  and navy ink. The LOOΠΔ logo is navy with its magenta slash, the twelve moons are unchanged, and
  the current track is HeeJin pink.
- **LOONA 1/3 Light** (`1-3-light`, `LOONA-1-3-Light.wsz`): the pastel aqua body with pale aqua
  glass and dark teal ink.
- **Odd Eye Circle Light** (`odd-eye-circle-light`, `LOONA-Odd-Eye-Circle-Light.wsz`): white
  concrete with black ink, black thumbs and a black logo, plus red, blue and purple accents.
- **yyxy Light** (`yyxy-light`, `LOONA-yyxy-Light.wsz`): the white shirts: cream with a faint
  green and burgundy tartan, green ink and burgundy thumbs.
- **[#] Light** (`hash-light`, `LOONA-Hash-Light.wsz`): from its Normal B and Limited B covers:
  black uniforms on a pale warm grey (#E4DBD9), with the A covers' red as the accent.
- **[&] Light** (`and-light`, `LOONA-And-Light.wsz`): from its B version: a white arch room in
  lavender greys (#EBECF4 / #C7C2CA) with black and white outfits, and the A cover's curtain red
  as the accent.

### Light variants

These are separate themes and leave every original skin byte-identical. Each has a light body,
light display glass with dark digits, and dark text.bmp ink, which the app also uses for the
TrueType title. The playlist is light, with a light selection that keeps Normal readable and a
current-track colour that reads on white. On light glass, the members' colours are darkened to a
luma of 150 or less (`sink`): HyunJin's yellow, ViVi's pink, Chuu's peach and Olivia's silver.
JinSoul's blue and Yves's burgundy stay as they are.

An era got a light variant only if it has a real light version. The evidence is the retailer
product photos from sound-wave.co.kr (site search for 이달의 소녀, page 2), saved under
`source/pkg-versions/`:

- **[#]:** Normal A and Limited A are red and blue. Normal B and Limited B are black outfits on a
  pale grey-white backdrop. This qualifies, based on the B covers.
- **[&]:** A is the red curtain. B is the white arch room. C is dark. D is white dresses with
  flowers on cream. This qualifies, based on B (D would also do).
- **[12:00]:** no light version was found. The album came in four lettered versions, but retailer
  and wiki searches gave no cover descriptions, and fandom wikis refused fetches. Without
  evidence, no light variant was made.
- **[+ +], [X X], Flip That:** these are already light skins, so they were skipped.

### Members (reveal order) and colours

The colours are the members' moons from LOONA's video openings, as sampled by a fan post ("Loona
Color Codes", tumblr, maruthesagwa/deobistay, 2018). That post calls them close to official
because they match the opening's moons. Olivia Hye's silver came from a teaser. The post itself
blocked fetching, so these values come from a search engine's summary of it. They were
cross-checked against two independent fan palettes on color-hex.com: synovelle's "LOONA 1/3 /
OEC / yyxy Official Colors" (palettes 73258, 73259, 73260) and ymmfl11's "LOONA Representative
Colors 1-3" (1007282-4). The colour names (bright pink, yellow, green, orange, pastel rose, red,
blue, purple, burgundy, peach, turquoise/emerald, black/silver) agree across kprofiles, the LOONA
fandom wiki and Fanlore. The hex values differ by source, as the table shows.

| # | member | used | synovelle | ymmfl11 | ARTMS COSMO (2024) | animal |
|---|---|---|---|---|---|---|
| 1 | HeeJin | #ED008E | #ED008E | #D80087 | #ED0090 | rabbit |
| 2 | HyunJin | #FFCA14 | #FDCA14 | #F7EE0B | | cat |
| 3 | HaSeul | #03A233 | #7FC201 | #0EB935 | #00A652 | white bird |
| 4 | YeoJin | #FE9702 | #FD9701 | #F29607 | | frog |
| 5 | ViVi | #FFC5C8 | #FFA5B6 | #F7BEC4 | | deer |
| 6 | Kim Lip | #D90011 | #990036 | #C30011 | #EF1841 | owl |
| 7 | JinSoul | #0801D5 | #1A24D5 | #0700CA | #1724A7 | blue betta fish |
| 8 | Choerry | #BA01DE | #832BCD | #AA00D3 | #B510B5 | fruit bat |
| 9 | Yves | #790105 | #7D0B24 | #6D0005 | | swan |
| 10 | Chuu | #FEA87D | #FF896E | #F4A27A | | penguin |
| 11 | Go Won | #02BCA1 | #40CAA8 | #11D69E | | butterfly |
| 12 | Olivia Hye | #C0C0C0 (silver) | #7F7F7F (grey) | #010101 (black) | | wolf |

The biggest conflicts are HaSeul (from deep green to lime), Kim Lip (from crimson to wine), and
Olivia Hye, whose colour is given as black, grey or silver. Silver was chosen because it reads on
a dark skin and suits the moon theme. JinSoul's blue and Yves's burgundy are too dark to read on
dark grounds, so the generator lifts them toward white for small marks (`lift`). On light grounds
it darkens HyunJin's yellow and ViVi's pink the same way (`sink`). The animals come from kprofiles
and the zendari wiki member table. HaSeul's animal is also given as a fox in later sources.

### Group identity

- **Name.** 이달의 소녀 means "Girl of the Month": one member was revealed each month from Oct 2016
  to Mar 2018 (Wikipedia). The initial consonants of the Hangul, rearranged, look like "LOOΠΔ"
  (Wikipedia). That gives the wordmark its Π and Δ, and gives the moon (달) its place in the
  motif.
- **Logo.** The stacked mark is ㅇ ㄷ / ㅇ / ㅿ ㄹ with a magenta slash. The horizontal wordmark is
  "LOOΠΔ" in thin geometric strokes, followed by the slash.
- **Loonaverse.** The members are grouped into three "orbits": 1/3, Odd Eye Circle and yyxy. The
  group's lore uses moons, eclipses and a Mobius strip.

### Subunits

- **LOONA 1/3.** The canonical line-up is HeeJin, HyunJin, HaSeul and ViVi. They released *Love &
  Live* (13 Mar 2017) and the reissue *Love & Evil* (27 Apr 2017, "Sonatine"). ViVi, the fifth
  member, joined the unit although YeoJin had been revealed before her. YeoJin was left out of
  the unit's promotions. Fan sources give school or the lore ("lost in the forest") as the reason,
  and call her "the slash in 1/3" (LOOΠΔ TV #200). No official statement was found. The *Love &
  Live* cover is pastel aqua, with the members in blue blazers and pink "love & live" script.
- **Odd Eye Circle.** Kim Lip, JinSoul and Choerry. They released *Mix & Match* (21 Sep 2017,
  "Girl Front") and *Max & Match* (31 Oct 2017, "Sweet Crazy Love"). They came back under Modhaus
  with *Version Up* (Jul 2023, "Air Force One") and later became part of ARTMS. The cover is black
  and white streetwear against grey shutters, with handwritten "Max & Match". "Odd eye" means
  heterochromia, which suits the members' red, blue and purple.
- **yyxy** ("youth youth by young"). Yves, Chuu, Go Won and Olivia Hye. They released
  *beauty&thebeat* (30 May 2018, "love4eva" featuring Grimes). Chuu was removed from LOONA in Nov
  2022. The skin uses the 2018 line-up of four. The cover shows white shirts and green tartan
  skirts, with lowercase handwritten "yyxy beauty&thebeat".

### Eras

The six requested eras were kept, with no swaps. Each has a recognisable cover look, and five of
the six covers put a ringed symbol beside the Korean name. Flip That is the exception.

- **[+ +]** (Aug 2018, "Hi High"; "Favorite" pre-release). The debut EP. The cover shows a white
  diving tower in a misty green forest and the ringed "+ +" badge.
- **[X X]** (19 Feb 2019, "Butterfly"). The reissue. The cover is icy pale blue, with the members
  wearing iridescent pastel butterfly wings. The MV's theme is metamorphosis.
- **[#]** (5 Feb 2020, "So What"). Girl-crush concept. The cover shows red uniforms under a
  slate-blue dusk with a moon.
- **[12:00]** (19 Oct 2020, "Why Not?"). A moonlight festival at midnight. The cover is a night
  scene with palms, warm browns and gold.
- **[&]** (Jun 2021, "PTT (Paint The Town)"). The cover shows a red velvet curtain beside a slate
  wall and cream and yellow outfits.
- **Flip That** (Jun 2022). Summer special. The cover is a garden of white dresses and pastel
  flowers. The trailer was described as "ethereal, bright and floral" (Soompi).

## Limits

- The app has one EQ slider sprite per value, not one per band, so a slider's fill follows its
  value and not its band.
- Member colours are fan-sampled, not official, and differ by source (see the table above).
- [12:00] has no light variant: no evidence of a light version was found.

## Sources

Each reference is in its own directory under `source/`, comes from Wikipedia / Wikimedia Commons
unless noted, and was opened only with `/usr/bin/python3 -I` and Pillow.

- `source/logo-loona/loona-logo.jpg`: commons.wikimedia.org File:Loona_logo.jpg. Used: the
  horizontal LOOΠΔ wordmark, crop (298,166)-(691,231), is thickened and box-scaled to 8 px for
  every titlebar except OEC's. The slash keeps its magenta.
- `source/logo-oec/oec-logo.png`: commons File:LOONA_ODD_EYE_CIRCLE_Logo.png. Used: the "ODD EYE
  CIRCLE" line (rows 224-307) at 8 px in the OEC titlebar.
- `source/logo-loona-alt/`, `source/logo-loona-alt2/`: commons File:LOONA_logo_(1).jpg,
  File:LOONA_Logo.jpg. Reference only: the stacked mark.
- `source/cover-plusplus`, `cover-xx`, `cover-hash`, `cover-1200`, `cover-and`, `cover-flipthat`:
  en.wikipedia album infobox covers. Reference only: era palettes and motifs.
- `source/cover-love-live`, `cover-max-match`, `cover-beauty-beat`: en.wikipedia subunit covers.
  Reference only: subunit palettes.
- `source/pkg-hash-limited-b/`, `source/pkg-versions/`: sound-wave.co.kr product photos ([#]
  Normal/Limited A/B, [&] A-D). Reference only: evidence and palettes for the light era variants.
- Research pages fetched: kprofiles.com/loona-13-profile-facts, zendari.miraheze.org/wiki/LOONA,
  the color-hex.com palettes, and en.wikipedia.org (Loona, Loona 1/3, Loona Odd Eye Circle, Loona
  yyxy). The LOONA fandom wiki, Namu wiki and Fanlore refused automated fetches (402/403).
- LOONA name, marks and logos (c) Blockberry Creative.
