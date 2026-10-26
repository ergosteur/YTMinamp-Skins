# Social 2012: Twitter, Instagram and Google+ around 2012

Three classic skins from one procedural generator (`gen_skin.py`, forked from
`skins/ember/gen_skin.py`: same sheets, layouts and preview logic, by way of
`private-repo/skins/web/web-nostalgia/`), a theme each. Two real marks are used, each once, in the
main titlebar (the Twitter bird and the Instagram wordmark); everything else is drawn by the
script, including the Instagram camera icon and the Google+ g+ square as hand-drawn 13px pixel
art.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py google-plus    # some (twitter-2012, instagram-2012, google-plus)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Twitter-2012.wsz`, `Instagram-2012.wsz`, `Google-Plus.wsz` and `preview-<theme>.png`
here; sheets in `out/<theme>/`, scratch files (rasterised logos) in `out/scratch/` (`out/` is
ignored). Deterministic (fixed noise seed, fixed zip timestamps). The main title is previewed as
the app draws it by default: TrueType, in text.bmp's ink colour (#333333, #2d5d88, #333333).

## Themes

- **Twitter 2012** (`twitter-2012`, the 2012 web redesign): dark #333 to #222 top bar with Home /
  Connect / Discover (icons + text, Home in bold white), the June 2012 bird in #2fc2ef (grey when
  the window is unfocused) and a blue compose button; white rounded modules on the #c0deed page
  with a #f5f8fa footer; grey #fff to #e6e6e6 buttons, the blue #33bcef to #019ad2 "Tweet" button
  for Play and for toggles that are on; `#equalizer` / `#playlist` titles; a quill compose button
  at the About spot.
- **Instagram 2012** (`instagram-2012`, the iOS app): blue leather-textured nav bar with the white
  script wordmark (shadow above, iOS style), linen background, white photo cards with cream
  "filtered" displays, the dark tab bar along the bottom with the raised blue camera-style Play
  button, round iOS slider knobs, a rainbow-stripe analyzer, the retro camera icon (hand-drawn)
  at the About spot.
- **Google+** (`google-plus`): the black #2d2d2d Google bar: +You in bold white under a red rule,
  Search / Images / Mail / Drive / More, a red notification count; white pages with a grey left
  ribbon and #f1f1f1 panels, Google's grey #f8f8f8 to #ececec buttons and the red #dd4b39 "Share"
  button for Play and "on" toggles; a circles icon in the playlist title, red rules over the
  EQ/album-art titles, a hand-drawn red g+ square at the About spot.

## Limits

- None noted.

## Sources

Read at build time from `source/` (downloaded as-is, never executed), rasterised with
`/usr/bin/rsvg-convert`, and used as coverage masks recoloured in Pillow, composited once:

- `source/logo-twitter/Logo_of_Twitter.svg`, from
  https://commons.wikimedia.org/wiki/File:Logo_of_Twitter.svg (the 2012 bird; drawn in #2fc2ef,
  grey when the window is unfocused).
- `source/logo-instagram/Instagram_logo.svg`, from
  https://commons.wikimedia.org/wiki/File:Instagram_logo.svg (the script wordmark, in white).
- Twitter logo (c) X Corp. (formerly Twitter, Inc.).
- Instagram logo (c) Meta Platforms, Inc. (Instagram).
- Google+ (c) Google LLC.
