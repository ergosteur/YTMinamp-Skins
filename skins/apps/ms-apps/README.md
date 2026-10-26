# MS Apps: MSN Messenger, Office 2007, Office 2010

Three classic skins from one procedural generator (`gen_skin.py`, built on
`skins/ember/gen_skin.py` by way of `private-repo/skins/apps/browsers/gen_skin.py`, keeping their
sheet layouts), a theme each. Each skin carries one real logo (in the About spot, or inside
Office 2007's orb); the script draws everything else: gradients, anti-aliased shapes and
hand-made pixel fonts.

```sh
/usr/bin/python3 -I gen_skin.py                      # all of them
/usr/bin/python3 -I gen_skin.py msn office2010       # some (msn, office2007, office2010)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `MSN-Messenger.wsz`, `Office-2007.wsz`, `Office-2010.wsz` and `preview-<theme>.png`
here; sheets in `out/<theme>/` and the rasterised logos in `out/scratch/` (`out/` is ignored).
Deterministic. Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

text.bmp's ink is black on the white display fields, so the app's TrueType title is drawn in black
on white. The preview draws it that way too, using the app's `textInk` rule.

- **MSN Messenger** (`msn`, MSN Messenger 7.5, 2005, on Windows XP, the last "MSN"-named version
  and the one with the classic green and blue buddies):
  - The window is light blue and white with a soft white swoosh.
  - The buddies icon is the options button. A small green buddy sits beside the Equalizer and
    Playlist titles.
  - The transport buttons are glossy and round. Play is the big green one, and a pressed button
    turns deep blue.
  - Every toggle (shuffle, repeat, EQ, PL, EQ on/auto) carries a status dot: green "online" when
    on, red "busy" when off.
  - The seek thumb is a little green buddy, which turns blue while dragged.
  - Playlist: like the contact list: black on white, light blue selection, and the current track
    in online green.
  - The real buddies logo sits in the About spot.
- **Office 2007** (`office2007`, Office 2007 with the Blue colour scheme):
  - The round Office Button (glass orb with the four-colour Office logo) is the options button.
    It glows orange when pressed.
  - The Quick Access Toolbar (save, undo, redo, drop-down) sits beside it, and the title is
    two-tone dark blue.
  - The main window is a ribbon: boxed glossy groups, with PLAYBACK and OPTIONS label bands.
  - The transport is a joined strip of glossy small buttons.
  - Office colours the states: amber when checked, orange when pressed.
  - The Equalizer titlebar is the tab row (Home, Insert, then the selected Equalizer tab), and
    the playlist and album-art titles are selected tabs.
  - The visualiser uses the Office 2007 chart colours (accent 1 #4F81BD, red peaks).
  - The About spot is Office's blue round Help button.
- **Office 2010** (`office2010`, Word 2010 with the Silver scheme):
  - The ribbon is flatter and silver-white, with groups split by hairline dividers instead of
    boxes.
  - The Word icon (W tile on a page) is the window menu, which is the options button.
  - The Equalizer tab row starts with the blue File tab (#2B579A).
  - The playlist's ADD/REM/SEL/MISC panel is a Backstage-blue strip with white commands.
  - Checked and pressed states use the flatter yellow-orange.
  - The visualiser runs in Word blue with orange peaks.
  - The real Office 2010 logo sits in the About spot.

## Limits

- The Office ribbon tab row has no room in the 14px main titlebar, so it moved to the
  Equalizer's titlebar.
- The 2007 orb can be no larger than the 14px bar (Office's overhangs the tab row).
- "Help" in the About spot is a stand-in: Office 2007's logo is already in the orb.

## Sources

All three were fetched from Wikimedia Commons and are stored in `source/`. SVGs are rasterised
with `rsvg-convert`. The Office files are cut to their square mark, without the wordmark.

- MSN Messenger buddies: https://commons.wikimedia.org/wiki/File:WLM_logo.svg in
  `source/logo-msn/`, composited once in the About spot.
- Office 2007: https://commons.wikimedia.org/wiki/File:Microsoft_Office_2007_logo.svg in
  `source/logo-office2007/`, composited once inside the Office Button orb.
- Office 2010: https://commons.wikimedia.org/wiki/File:Microsoft_Office_2010_logo.svg in
  `source/logo-office2010/`, composited once in the About spot.
- Logos (c) Microsoft Corporation.
