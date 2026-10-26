# Encarta and Tumblr: Microsoft Encarta 97 and the 2012 Tumblr dashboard

Two classic skins from one procedural generator (`gen_skin.py`, forked from
`skins/ember/gen_skin.py`: same sheets, layouts and preview logic, by way of
`private-repo/skins/web/social-2012/`), a theme each. Each skin uses one real mark, once, in the
main titlebar; the script draws everything else.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py tumblr         # some (encarta-97, tumblr)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Encarta-97.wsz`, `Tumblr.wsz` and `preview-<theme>.png` here; sheets in `out/<theme>/`,
scratch files (rasterised logos) in `out/scratch/` (`out/` is ignored). Deterministic (fixed zip
timestamps). The main title is previewed as the app draws it by default: TrueType, in text.bmp's
ink colour (#000000 on #d9d6c5; #444444 on #f3f4f6).

## Themes

- **Encarta 97** (`encarta-97`, Microsoft Encarta 97 Encyclopedia, with colours sampled from
  screenshots of the program): the black window bars carry letter-spaced taupe #a09683 capitals:
  MICROSOFT, the ENCARTA 97 lettering (cream, with the red #b95b5c 97), then ENCYCLOPEDIA, plus
  Encarta's own "v|" and "|- |[] |x" buttons. The main window is the article pane: cream #ebeae1
  with a black media box (gold digits and analyzer) and light taupe #d9d6c5 caption strips for the
  title and kbps rows. The transport is Encarta's black menu bar, with grey separators and white
  items (Play in gold), and pressed items turn into a taupe block. Shuffle and Repeat use the
  Pinpointer's "Start Over" style: a taupe outline when off, a gold block when on. Taupe
  scroll-thumb sliders, periwinkle #6571b4 levels, and a "?" help button at the About spot. The
  playlist is the **Pinpointer**: a black body, a taupe "Articles in list" header strip, a white
  list, the selection in taupe with the current article in the Pinpointer's dark red #972938, and
  gold-outline "Wizard" buttons. The equalizer is an **InterActivities chart**: a taupe heading
  band holds ON/AUTO/PRESETS and a black graph stage, with periwinkle bars on a gridded #dcd8c8
  plot and dark red dB labels.
- **Tumblr** (`tumblr`, the classic dashboard, 2012-2015): navy #36465d page and header with the
  white "t", the "Search Tumblr" field and the header icons (dashboard, explore, inbox, activity,
  account). White rounded post cards with a footer hairline. The footer's grey icons are the
  transport, and Play is the blue #529ecc "Post" button. The heart is Shuffle (red #d95e40 when
  on) and reblog is Repeat (green #56bc8a when on). A blue compose (pencil) button sits at the
  About spot. The equalizer's titlebar holds the post bar: Text, Photo, Quote, Link, Chat, Audio
  and Video in their own colours on a white pill. The analyzer and clutterbar letters use the same
  post-type colours. The playlist is the "Queue" (Tumblr's post queue).

## Limits

- Encarta gives each feature window its own titlebar colour: periwinkle for the Pinpointer, sage
  green for MindMaze and InterActivities. Here every window keeps the main black bar, so the skin
  reads as one piece (BRIEF: matching titlebars). The periwinkle survives in the levels and EQ
  bars.
- Encarta's "v|" glyph appears only on the main window, where it is the working options button;
  the EQ, Pinpointer and album-art bars leave it out.
- Tumblr's Repeat is the reblog arrows (a loop) and Shuffle is the heart with the word "shuffle",
  because Repeat's 28 px button has no room for a label.

## Sources

Sources are read at build time from `source/`: downloaded as is, never executed, and opened only
with Pillow or `rsvg-convert`.

- `source/encarta97-winworld/encarta97-title.png`: a screenshot of the Encarta 97 title screen,
  from WinWorld's Encarta 1997 page (https://winworldpc.com/product/encarta/1997, image
  `res/img/screenshots/1997-f0f78afcc664fcc1308da7418d427225-encarta_1.png`). The "ENCARTA"
  (black ink) and the "97" (red) are cut out of it as coverage masks, without "encyclopedia" or
  the engraving behind them, then drawn 14 px tall in cream and #b95b5c on the black bar. The
  Encarta logo on Wikimedia Commons is the later 2000s butterfly mark, so it was not used. The
  other WinWorld screenshots (the Pinpointer, the article pane, MindMaze, InterActivities) were
  used only as colour and layout references and are not kept.
- `source/logo-tumblr/Tumblr_Logo.svg`, from https://commons.wikimedia.org/wiki/File:Tumblr_Logo.svg
  (the wordmark). Its first glyph, the "t", is cut out and drawn in white 11 px tall: the
  dashboard's "t" logo.
- The Tumblr post-type colours (#d86042 photo, #f19f35 quote, #56bc89 link, #4da8d6 chat, #ab7dc2
  audio, #76818c video) were sampled from the 2012 icon set shown at
  https://sayyeah.com/digital-insights/tumblrs-new-icons-a-great-improvement/ (reference only).
  The icons themselves are hand-drawn 9 px pixel art.
- Encarta logo (c) Microsoft Corporation.
- Tumblr logo (c) Automattic Inc. (Tumblr).
