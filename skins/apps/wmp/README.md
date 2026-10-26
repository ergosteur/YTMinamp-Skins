# WMP: Windows Media Player 7, 8, 9 Series and 10

Four classic skins in the style of Windows Media Player's full mode, from one procedural generator
(`gen_skin.py`, based on `skins/ember/gen_skin.py`, with the anti-aliased shape helpers of
`private-repo/skins/apps/browsers/`), one theme per version. No logo files are used: each era's
mark is redrawn from shapes in the script (`logo_flag`, `logo_ring`), once per skin, in the About
spot. Everything else is drawn by the script too.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py wmp9 wmp10     # some (wmp7, wmp8, wmp9, wmp10)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `WMP-7.wsz`, `WMP-8.wsz`, `WMP-9.wsz`, `WMP-10.wsz` and `preview-<theme>.png` here;
sheets in `out/<theme>/` (`out/` is ignored), scratch in `out/scratch/`. Deterministic (fixed
seed, fixed zip timestamps). Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

Shared layout, taken from WMP's full mode: the Now Playing panes in black glass, a transport deck
along the bottom with the big round play button in its well and the smaller round buttons in a
groove, WMP's wedge-shaped volume slider, the seek groove with its rewind/fast-forward end caps,
the clutter bar drawn as a miniature of WMP's left taskbar column (the chosen button lit), the
equalizer as WMP's Graphic Equalizer in a dark panel, the playlist title as WMP's playlist
drop-down, green status text (7, 8) on black. The title is drawn by the app in TrueType in
text.bmp's ink (green for 7/8, pale blue for 9, white for 10) on black. Playlist font: Tahoma.

- **WMP 7** (`wmp7`, 2000, Windows Me): brushed silver frame, blue-violet selected taskbar
  button, silver round buttons and block thumbs, a navy playlist, blue-violet bars; the Windows
  Media waving flag on a slate tile (as embossed in WMP 7's lower-left corner).
- **WMP 8** (`wmp8`, 2001, Windows XP): periwinkle Luna-matching frame, silver-blue deck and
  buttons, green pill thumbs, green bars and text on black, "Sample Playlist" drop-down; the
  XP-era four-colour ring logo with the dark play arrow.
- **WMP 9 Series** (`wmp9`, 2003): dark blue-black chrome with a sheen, "Windows Media Player 9
  Series" in the titlebar, glossy pale-blue buttons on a dark deck, green pill thumbs, pale-blue
  text and blue bars; the glossy ring logo with the blue arrow.
- **WMP 10** (`wmp10`, 2004): near-black chrome, WMP 10's task tabs across the titlebar (Now
  Playing lit in blue glass, then Library, Rip, Burn, Sync, Guide), the black deck with the blue
  rim and the blue glass play button, round blue thumbs, white text; the same ring logo as 9.

## Limits

- The app's seek bar can't show progress and the balance frames can't show a side, so the seek
  groove stays empty under its thumb and balance lights outwards from the centre.
- The volume thumb's corners show the empty wedge for a pixel or two where the fill passes under
  it.
- WMP 9 and 10's real default skins on XP were blue; 9 follows its dark "black/blue" colour
  scheme and 10 its darker look as asked, and both keep XP-era green or blue accents.

## Sources

Reference screenshots (looked at only, never read by the script), in `source/`:

- `ref-wmp7/wmp7.gif`: https://www.windows-media-player.com/wp-content/uploads/2019/12/Windows-Media-Player-7.gif
- `ref-wmp8/wmp8.png`: https://www.windows-media-player.com/wp-content/uploads/2019/12/Windows-Media-Player-8.png
- `ref-wmp9/wmp9-a.png`: https://www.windows-media-player.com/wp-content/uploads/2019/12/Windows-Media-Player-9.png
- `ref-wmp9/wmp9-b.png`: https://freesoft.ru/storage/images/213/2127/212607/212607_normal.png
- `ref-wmp9/wmp9-9seriesdefault.png` (WebP):
  https://static.wikia.nocookie.net/wmpskins/images/3/34/9SeriesDefault.png
- `ref-wmp10/wmp10.png`: https://www.windows-media-player.com/wp-content/uploads/2019/12/Windows-Media-Player-10.png
- Windows Media Player logo (c) Microsoft Corporation.
