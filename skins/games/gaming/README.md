# Gaming: Steam (2004 and modern), Minecraft, Twitch

Four classic skins from one procedural generator (`gen_skin.py`), a theme each. Each carries its
subject's real logo once, in the About/emblem spot at the main window's bottom right; everything
else is drawn by the script. The generator has two drawing families. **Flat** (steam, twitch) is
`private-repo/skins/apps/streaming/`'s code (itself built on `skins/ember/gen_skin.py`):
anti-aliased shapes and Noto Sans lettering. **Pixel** (steam-2004, minecraft) is new and follows
Ember's bevels: hard pixels, textures, and two pixel fonts drawn for these skins: a Tahoma 8-like
proportional font (`VG`) for the VGUI and a blocky Minecraft-style font (`MC`).

```sh
/usr/bin/python3 -I gen_skin.py                     # all of them
/usr/bin/python3 -I gen_skin.py minecraft twitch    # some (steam-2004, steam, minecraft, twitch)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Steam-2004.wsz`, `Steam.wsz`, `Minecraft.wsz`, `Twitch.wsz` and `preview-<theme>.png`
here; sheets in `out/<theme>/` and the rasterised logos in `out/scratch/` (`out/` is ignored).
Deterministic. Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

- **Steam 2004** (`steam-2004`, the 2003 to 2008 VGUI2 client): olive #4c5844 faces, #3e4637
  fields and lists, Border.Bright #888f80 and Border.Dark #282e22 one-pixel bevels, #d8ded3 text,
  #c4b550 khaki highlights. The main titlebar has a heavy "STEAM" wordmark (drawn by the script)
  and an etched rule. The EQ titlebar is the property-sheet tab row (Games, Friends, Servers,
  Settings, News, with Settings active). The playlist is the "Games" tab and the album-art window
  the "News" tab. Transport buttons are VGUI buttons, with Play as the default button (black
  outline). An etched group box sits round the transport. Volume, balance and the EQ use
  segmented khaki progress bars. The seek thumb is a scrollbar thumb. Shuffle and repeat use pixel
  icons, and "on" is a khaki glyph and indicator. The logo in #d8ded3.
- **Steam** (`steam`, the 2010s to 2020s client): the #171a21 top bar carries the navigation as
  the title (STORE, LIBRARY in #66c0f4, COMMUNITY, and a profile name, "PLAYER ONE", as a
  stand-in). The body is #1b2838 and the transport strip runs #2a475e to #1f3a4f. Play is the
  green #a4d007 to #536904 Play button with a white triangle. Sliders and toggles use the #66c0f4
  accent. The playlist ("GAMES") is the library list, with the current game in light blue.
- **Minecraft** (`minecraft`, Minecraft in general, at native pixel resolution):
  - Every titlebar is a grass-block side strip: per-pixel noise turf with ragged drips into dirt.
    The noise has no pattern, so the 25px tiles meet without seams.
  - The main titlebar has a stone "MINECRAFT" wordmark drawn by the script (outlined, extruded,
    stone gradient). The other titles sit on dark name-tag plates.
  - The bodies are the #c6c6c6 GUI panel (white / #555555 bevel, black outline). The displays are
    text fields (black, #a0a0a0 border), with the time in XP-green digits.
  - The transport is the hotbar. A held button gets the white selected-slot frame, and play is
    green.
  - The seek bar is the XP bar; its thumb is a green fill tail ending in an XP orb.
  - Volume is a row of hearts, filled by half-hearts. Balance is the hunger bar: full at the
    centre, emptying from both ends.
  - The EQ sliders are inventory-slot columns filled in XP green.
  - Buttons are stone buttons: blue-tinted when held, green when on (EQ, PL, shuffle, repeat,
    On/Auto).
  - Playlist: #e0e0e0 on black, #55ff55 current.
- **Twitch** (`twitch`, today's dark UI): #18181b bars, a #0e0e10 body, #1f1f23 panels and the
  #9146ff purple. The main titlebar is a channel header: the red LIVE badge, the channel name and
  a red viewer count. Play is a purple Follow-style square. Toggles, sliders and EQ fills are
  purple. The playlist is "STREAM CHAT" (#18181b, the current track in #bf94ff) and the album-art
  window is "VIDEO".

## Limits

- Steam 2004's colours come from memory of the VGUI2 scheme; no scheme file could be fetched to
  confirm them.
- The Steam 2004 logo is today's Simple Icons Steam mark (close to the 2003 one), in #d8ded3.
- The seek bar can't show progress, so the thumbs carry it: a fading tail (Steam, Twitch) or an
  XP-bar tail (Minecraft).
- Twitch's per-user chat colours can't exist in a playlist; the current track is purple.
- The Minecraft volume thumb (a 14px stone button) covers about one and a half hearts where it
  sits.

## Sources

- Steam: https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/steam.svg (Simple Icons) in
  `source/logo-steam/`, tinted per theme.
- Twitch: https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/twitch.svg (Simple Icons) in
  `source/logo-twitch/`, in #9146ff, with its face filled white to match the official Glitch.
- Minecraft: https://commons.wikimedia.org/wiki/File:Minecraft_cube.svg (the grass-block icon) in
  `source/logo-minecraft/`.
- All are rasterised with `rsvg-convert`, box-filtered down to 16px and composited once.
- Steam logo (c) Valve Corporation.
- Twitch logo (c) Twitch Interactive, Inc.
- Minecraft logo (c) Mojang Studios / Microsoft.
