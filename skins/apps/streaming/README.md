# Streaming: YouTube Music (dark and light), Spotify, Apple Music, SoundCloud

Five classic skins from one procedural generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`:
same sheet layouts and preview renderer), a theme each. Each carries its service's logo once, in
the About/emblem spot (bottom right of the main window); every other pixel is drawn by the script:
flat panels, anti-aliased shapes, hinted system sans fonts for the lettering (Noto Sans for
YouTube Music and SoundCloud, Adwaita Sans, an Inter derivative, for Spotify and Apple Music) and a
5x6 pixel font for text.bmp.

```sh
/usr/bin/python3 -I gen_skin.py                         # all of them
/usr/bin/python3 -I gen_skin.py youtube-music spotify   # some (youtube-music,
                                                        #   youtube-music-light, spotify,
                                                        #   apple-music, soundcloud)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `YouTube-Music.wsz`, `YouTube-Music-Light.wsz`, `Spotify.wsz`, `Apple-Music.wsz`,
`SoundCloud.wsz` and `preview-<theme>.png` here; sheets in `out/<theme>/` (`out/` is ignored),
scratch files (rasterised logos) in `out/scratch/`. Deterministic.

## Themes

All share:

- Flat, modern controls in place of bevels: rounded panels for the displays, anti-aliased round
  knobs, 3px rails with the accent filled up to the knob (volume, EQ from the 0 dB line).
- Shuffle and repeat are icons; "on" is the accent (Spotify adds its dot under the icon, the
  others a tinted rounded background).
- A "player bar" band behind the transport.
- The seek thumb carries the progress: a tail fading from grey into the accent behind the knob.
- Window titles: "YTMinamp", "Now Playing", "Music", "Now playing"; playlists "Up next", "Queue",
  "Playing Next", "Next up".
- The displays, text.bmp's background and viscolor's background are one panel colour. The app
  draws the song title in TrueType in text.bmp's ink colour (its commonest letter colour) on the
  blank text.bmp cell it tiles first; the preview does the same, and the generator asserts the
  ink contrasts with the title box. Playlist font: Arial.

- **YouTube Music** (`youtube-music`): dark; a round white play button with a black glyph; the
  #212121 player bar with the seek line on its top edge.
- **YouTube Music Light** (`youtube-music-light`): the dark theme's layout on YouTube's light
  palette: white body and titlebars with an #e5e5e5 hairline, #f2f2f2 cards and player bar,
  #0f0f0f/#606060 text, a black play circle with a white glyph, red fills, knobs, lit toggles and
  seek line. Playlist: white, #cc0000 current, #e5e5e5 selection.
- **Spotify** (`spotify`): a round white play button with a black glyph; a black player bar; the
  "on" dot under shuffle and repeat.
- **Apple Music** (`apple-music`): plain filled glyphs and double-arrow skips; a frosted grey
  player bar with a hairline.
- **SoundCloud** (`soundcloud`): an orange play button with a white glyph; the #f2f2f2 player
  bar; the seek thumb is a run of orange waveform bars ending in the playhead, over a grey
  waveform rail.

## Limits

- The seek bar can't show a played/unplayed split in this format (posbar.bmp is one static rail
  and a moving thumb), so the thumb carries it.

## Sources

Rasterised at generation time with `rsvg-convert` from `source/logo-*/logo.svg` (downloaded,
untouched), composited once per skin in the About/emblem spot:

- YouTube Music: https://commons.wikimedia.org/wiki/File:Youtube_Music_icon.svg
- Spotify: https://commons.wikimedia.org/wiki/File:Spotify_icon.svg
- Apple Music: https://commons.wikimedia.org/wiki/File:Apple_Music_icon.svg
- SoundCloud: https://commons.wikimedia.org/wiki/File:Antu_soundcloud.svg
- YouTube Music logo (c) Google LLC.
- Spotify logo (c) Spotify AB.
- Apple Music logo (c) Apple Inc.
- SoundCloud logo (c) SoundCloud.
