# Web Classic: deviantART, What.CD, Gmail 2004, old reddit

Four classic skins from one procedural generator (`gen_skin.py`, forked from
`skins/ember/gen_skin.py`: same sheets, layouts and preview logic), a theme each, in the style of
2000s websites. The real marks used are the deviantART "dA", the WHAT.CD lettering and the
"reddit" wordmark, each once, in the main titlebar. Drawn by hand in the script: the Gmail 2004
wordmark (blue G, red envelope M, a/i/l), the reddit alien (shapes drawn at 8x and reduced to a
15x13 sprite), the vote arrows, Gmail's star, the CD and the thumbnail emblems, and all lettering
(pixel fonts).

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py reddit         # some (deviantart, what-cd, gmail-2004, reddit)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `deviantArt.wsz`, `What-cd.wsz`, `Gmail-2004.wsz`, `Reddit-Classic.wsz` and
`preview-<theme>.png` here (both windows' states, 2x; the main title is drawn in a TrueType font
in text.bmp's ink, as the app does); sheets in `out/<theme>/` (`out/` is ignored). The build
asserts that text.bmp's space cell is the display colour and that its ink is the theme's ink. Each
.wsz is finished by `skins/genex_wacup.py`.

## Themes

- **deviantART** (`deviantart`, deviantART v5/v6): #475149 header, #dae4d9 body, the green "dA"
  mark, gallery-thumbnail frames round the displays, bevelled "devious" tabs (toggles, EQ and
  playlist titles).
- **What.CD** (`what-cd`, Gazelle's Kuro stylesheet): #222/#303030/#454545 greys, the WHAT.CD
  logo, the menu tabs (EQ titlebar), "Torrents" header, the user-stats bar with the ratio in its
  colour; sliders use the ratio colours (red to green).
- **Gmail 2004** (`gmail-2004`, early Gmail): white page, the #c3d9ff inbox frame, the red/blue
  logo with BETA, Settings/Help/Sign out links, "Compose Mail", "Inbox (3)", the light-blue
  selected row, a yellow star in the About spot.
- **Reddit Classic** (`reddit`, old.reddit.com): #cee3f8 header with the alien, the wordmark and
  hot/new/top tabs, blue link titles, orangered upvote (on) / periwinkle downvote (off) toggles, a
  vote widget in the About spot.

## Limits

- Logos at 9-10px are approximations of the real marks.
- The playlist rows come from pledit.txt only: no alternating torrent-table or read/unread rows.
- deviantART's palette follows the brief's #475149/#4b5d50/#dae4d9 plus nearby greens; no
  archived v6 stylesheet was available to check it against.
- What.CD's own default stylesheet changed over the years; Kuro (dark) was chosen for its WHAT.CD
  logo and the menu/stat-bar look. Gazelle's public release defaults to "postmod".

## Sources

Downloaded once into `source/` (images only opened with Pillow, SVG rasterised with rsvg-convert):

- `source/whatcd-gazelle/kuro-logo.png`: What.CD's open-sourced Gazelle,
  https://github.com/WhatCD/Gazelle/tree/master/static/styles/kuro (the WHAT.CD lettering, its
  reflection dropped, shrunk to 9px, composited once in the main titlebar). The Kuro, postmod and
  layer_cake `style.css` files there were read for the palette; the other logos are reference
  only.
- `source/commons-deviantart/DeviantArt_logo.png`:
  https://commons.wikimedia.org/wiki/File:DeviantArt_logo.png (the lime "dA" mark cut out of its
  frame, 10px, main titlebar). `Deviantart-logo.png` is reference only.
- `source/commons-reddit/Reddit_Old.svg`: https://commons.wikimedia.org/wiki/File:Reddit_Old.svg
  (the lowercase "reddit" wordmark, 9px, main titlebar).
- `source/commons-gmail/`, `source/commons-whatcd/`: reference only.
- deviantART logo (c) DeviantArt, Inc.
- What.CD logo (c) What.CD.
- Gmail logo (c) Google LLC.
- reddit logo (c) Reddit, Inc.
