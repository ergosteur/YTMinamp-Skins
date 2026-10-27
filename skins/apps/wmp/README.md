# WMP: Windows Media Player 7, 8, 9 Series, 10 and 11, plus WMP Blue and WMP Dark

Seven classic skins in the style of Windows Media Player's full mode, from one procedural
generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`, with the anti-aliased shape helpers
of `private-repo/skins/apps/browsers/`), one theme per skin. WMP 8, 9 Series and 10 are drawn
after screenshots of the real players and use the real Windows flag (2002-2012) once: in the
About spot (8, 9 Series) or as the titlebar's menu button (10, where it is the window icon). WMP 7,
WMP 11, WMP Blue and WMP Dark redraw their era's mark from shapes in the script (`logo_flag`,
`logo_ring`), once, in the About spot. Everything else is drawn by the script too.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py wmp9 wmp10     # some (wmp7, wmp8, wmp9, wmp10, wmp11, wmp-blue, wmp-dark)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `WMP-7.wsz`, `WMP-8.wsz`, `WMP-9.wsz`, `WMP-10.wsz`, `WMP-11.wsz`, `WMP-Blue.wsz`,
`WMP-Dark.wsz` and `preview-<theme>.png` here; sheets in `out/<theme>/` (`out/` is ignored),
scratch in `out/scratch/`. Deterministic (fixed seed, fixed zip timestamps). Each .wsz is finished
by `skins/genex_wacup.py`.

## Themes

WMP 8, 9 Series and 10 share one mapping of the real player onto Winamp's layout: the left taskbar
(8, 9) or a column of 10's info-bar buttons as the clutter bar; one black display holding the
status line on top (play indicator, time, the song title in the status text's colour, which is
text.bmp's ink), a separator, the visualisation and stream info below; the info bar
("Ambience: Random") as a strip under the visualisation; the seek bar with WMP's rewind and
fast-forward end caps; the round glass transport (play the big button in its well, pause, stop and
eject round, previous and next as pills); the Graphic Equalizer as an enhancement pane under an
info-bar-coloured header. Playlist font: Tahoma for all seven.

- **WMP 8** (`wmp8`, Windows Media Player for Windows XP, 2001): periwinkle frame (#8492E4 to
  #545EB8) with the silver bar (#FEFEFF to #C6C6D6) inset along every titlebar, the round blue menu
  button as options and small round silver window buttons; the taskbar column (white letters, the
  chosen one darker #445CAC with an orange #FF9D30 underline); bright green #00FF00 status text,
  time and indicator (the play triangle lavender) on black, a grey separator, blue swirl-coloured
  visualisation; green seek tube and volume wedge with silver pill thumbs; the rounded periwinkle
  transport chin with pale lavender glass buttons, and the silver foot to its right holding
  shuffle/repeat and the flag. Playlist: #00D800 on #000000, #C8FFC8 current, #2E2E2E selection,
  under a "Sample Playlist" drop-down.
- **WMP 9 Series** (`wmp9`, 2003): pale silver-white frame (#FFFFFF to #D2DAEE) with a soft blue
  edge #6074B8, the pale round menu button, the white "Now Playing" drop-down by navy window
  glyphs; the taskbar column on a light grey-blue gradient (#D6E2F6 to #B4C6E8) with navy letters,
  the chosen one white; green #8CD646 status text and time on black, the navy #21273F info bar,
  white and violet "particle" visualisation; a pale seek groove and green volume wedge, white thumbs
  ringed in green; the white glass transport bar with grey glyphs; the flag in the About spot.
  Playlist: #DCE2F4 on #394472, #9CE650 current, #386AB3 selection, under the periwinkle
  "Now Playing List" header.
- **WMP 10** (`wmp10`, 2004): light blue frame (#7CBEF6 to #4A96E4); the titlebar is the pale task
  strip with the tabs (Now Playing raised and lighter #739FE7 in white, its drop-down arrow, then
  Library, Rip, Burn, Sync, Guide between hairlines), the flag as the menu button; the darker blue
  #386AB3 info bar wrapped round the display's left side and under the visualisation
  ("Ambience : Water"), its little buttons as the clutter bar; white title and time on black,
  purple "Ambience" visualisation; green #88D206 seek tube and volume wedge with pale glass thumbs;
  the pale glass transport bar with the slanted, recessed status panel round shuffle/repeat and
  the round "switch to skin mode" button in the About spot. Playlist: #FFFFFF on #5482C3, #B4C6FF
  current (lavender, as 10 shows it), #335B9D selection, under the "All Music" drop-down; the EQ's
  titlebar is a Graphic Equalizer tab.
- **WMP 11** (`wmp11`, 2006; this was called "WMP 10" before): near-black chrome, the task tabs
  across the titlebar (Now Playing lit in blue glass, then Library, Rip, Burn, Sync, Guide), the
  black deck with the blue rim and the blue glass play button, round blue thumbs, white text; the
  glossy ring logo. Playlist: #D8DEEA on #000000, #5CB0FF current, #1C3A7A selection.
- **WMP Blue** (`wmp-blue`, WMP-flavoured, no version; this was "WMP 8"): periwinkle Luna-matching
  frame, silver-blue deck and buttons, green pill thumbs, green bars and text on black,
  "Sample Playlist" drop-down; the XP-era four-colour ring logo with the dark play arrow.
  Playlist: #DCDCDC on #000000, #2CE82C current, #26408E selection.
- **WMP Dark** (`wmp-dark`, WMP-flavoured, no version; this was "WMP 9"): dark blue-black chrome
  with a sheen, "Windows Media Player" in the titlebar, glossy pale-blue buttons on a dark deck,
  green pill thumbs, pale-blue text and blue bars; the glossy ring logo with the blue arrow.
  Playlist: #C8D4F0 on #000000, #7CC4FF current, #1E2E66 selection.
- **WMP 7** (`wmp7`, 2000, Windows Me): brushed silver frame, blue-violet selected taskbar button,
  silver round buttons and block thumbs, green status text on black, a navy playlist, blue-violet
  bars; the Windows Media waving flag on a slate tile (as embossed in WMP 7's lower-left corner).
  Playlist: #E2E6F4 on #001A52, #4CE04C current, #3440B4 selection.

## Limits

- The app's seek bar can't show progress and the balance frames can't show a side, so 9's seek
  groove stays empty under its thumb (8's and 10's are green throughout, as their tracks are) and
  balance lights outwards from the centre.
- Winamp's transport order is fixed (previous, play, pause, stop, next, eject), so WMP's order
  (play/pause first, stop, previous/next as a pair, mute) is restyled, not rearranged; there is no
  mute button.
- The real players put the status line under the visualisation and the time at its right; here
  it runs along the display's top, where Winamp's title and time are.
- 8 and 9's full-mode frames have no title text; their main titlebars stay blank apart from the
  buttons (and 9's drop-down). Colours were sampled from the screenshots, which are small and
  compressed (10's especially).
- 10's current-track lavender is low in contrast on its blue playlist, as in the real player.
- WMP Dark lost its "9 Series" wordmark when it stopped claiming a version (main.bmp and
  titlebar.bmp changed there only).

## Sources

Reference screenshots (looked at only, never read by the script), in `source/`:

- `real-wmp8.png`, `real-wmp9.png`, `real-wmp10.png`: the user's screenshots of WMP 8, 9 Series
  and 10 in full mode, for WMP 8, 9 Series and 10.
- `ref-wmp7/wmp7.gif`: https://www.windows-media-player.com/wp-content/uploads/2019/12/Windows-Media-Player-7.gif
- `ref-wmp8/wmp8.png`: https://www.windows-media-player.com/wp-content/uploads/2019/12/Windows-Media-Player-8.png
- `ref-wmp9/wmp9-a.png`: https://www.windows-media-player.com/wp-content/uploads/2019/12/Windows-Media-Player-9.png
- `ref-wmp9/wmp9-b.png`: https://freesoft.ru/storage/images/213/2127/212607/212607_normal.png
- `ref-wmp9/wmp9-9seriesdefault.png` (WebP):
  https://static.wikia.nocookie.net/wmpskins/images/3/34/9SeriesDefault.png
- `ref-wmp10/wmp10.png` (what is now WMP 11's reference):
  https://www.windows-media-player.com/wp-content/uploads/2019/12/Windows-Media-Player-10.png

Logo, composited (rasterised with rsvg-convert, then scaled):

- `logo-windows-flag/flag-multicolored.svg`, the 2002-2012 Windows flag:
  https://commons.wikimedia.org/wiki/File:Unofficial_Windows_logo_variant_-_2002%E2%80%932012_(Multicolored).svg
  (copied from `private-repo/skins/os/mobile-classic/source/`); once per skin in WMP 8, 9 Series
  and 10.
- Windows logo (c) Microsoft Corporation. Windows Media Player logo (c) Microsoft Corporation.
