# P2P: the file-sharing clients of 1999-2006

Four classic skins from one procedural generator (`gen_skin.py`), a theme per client. Each carries
its client's real logo once (the main window's bottom-right emblem spot, or Kazaa's main
titlebar); wordmarks are set in Comfortaa Bold (Napster) and Liberation Sans Bold (the others),
both system fonts under open licences. Everything else is drawn by the script.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py kazaa          # some (napster, limewire, kazaa, azureus)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Napster.wsz`, `LimeWire.wsz`, `Kazaa.wsz`, `Azureus.wsz` and `preview-<theme>.png`
here; sheets in `out/<theme>/` (`out/` is ignored). Each .wsz is finished by
`skins/genex_wacup.py`.

## Themes

Shared motifs:

- **Tab rows.** The EQ titlebar is the client's tab row (Search / Hot List / Transfer / Library /
  Chat; Search / Monitor / Library / Connections; Web / Search / My Kazaa / Traffic / Theater; My
  Torrents / Peers / Pieces / Files / Info). Napster, LimeWire and Azureus add an active
  "Equalizer" tab; on Kazaa, Theater is the active tab. The playlist and gen titles are drawn as
  the active tab (Transfer, Downloads, Traffic, My Torrents). The gen letters' cells carry the
  tab's rows so they sit on it seamlessly.
- **Progress bars.** Volume, balance (from the centre out) and EQ sliders are transfer progress
  bars in each client's style. The seek bar is an empty transfer trough with 10 % ticks, or
  Azureus' availability bar (red = no peers).
- **Status lights.** The play/pause/stop indicator is a green/amber/red light. Shuffle, repeat,
  EQ, PL, ON and AUTO each have an LED.
- **Status bar.** Along the bottom of the main window: Napster's "Online: ... songs in ...
  libraries", LimeWire's connection bars, "Turbo-Charged" and bandwidth, Kazaa's participation
  level meter, Azureus' share-ratio smiley, NAT OK light, DHT users and speeds. The text is static
  decoration.
- **Mini progress bar** next to the playlist's running-time readout.
- The title box uses text.bmp's ink colour: light on dark (Napster, Kazaa) or dark on white
  (LimeWire, Azureus). The checks in `check()` assert the contrast, the sheet sizes and the gen
  letter scan.
- `gen_skin.py` writes 18 Media Library colours (window, items, header, selection, scrollbar from
  each theme's palette); `skins/genex_wacup.py` then derives the other six, fixes contrast and
  redraws genex.bmp in Winamp's real 112x59 layout. Lowest text contrast after that: Napster
  7.3:1, LimeWire 5.2:1, Kazaa 8.8:1, Azureus 12.1:1. Playlist font: Arial.

- **Napster** (`napster`, Napster 2.0 beta, 1999-2001): dark navy / teal-grey, rounded lowercase
  wordmark, flat teal progress bars; the cat-head logo in the emblem spot.
- **LimeWire** (`limewire`, LimeWire 4.x): lime-green caption, light grey panels, white fields,
  glossy green bars; the lime slice in the emblem spot.
- **Kazaa** (`kazaa`, Kazaa Media Desktop 2.x, 2002-2003): blue and white; the main window is the
  Theater player (black screen, lime digits); chunked blue bars. The "K" icon is in the main
  titlebar before "Kazaa Media Desktop"; the emblem spot has a drawn Theater film-frame icon.
- **Azureus** (`azureus`, Azureus 2.x): native Windows grey (SWT on the classic theme), blue piece
  bars, the availability bar as the seek trough; the blue poison-dart frog in the emblem spot.

## Limits

- The seek bar can't show a fill, so it stays a trough with a moving thumb.
- The status-bar text is static decoration.

## Sources

Each logo is used once:

- Napster cat-head logo: `source/napster/logo.svg`, from
  https://commons.wikimedia.org/wiki/File:Napster_logo.svg. In the main window's bottom-right
  emblem spot.
- LimeWire lime slice: `source/limewire-png/logo.png`, from
  https://commons.wikimedia.org/wiki/File:LimeWire.png. In the emblem spot.
  (`source/limewire/logo.svg`, File:LimeWire_logo.svg, the later flat mark, was downloaded but
  isn't used.)
- Kazaa "K" icon: `source/kazaa/logo.svg`, from
  https://commons.wikimedia.org/wiki/File:KaZaa_logo.svg (white card knocked out). In the main
  titlebar. (`source/kazaa-png/logo.png`, File:Kazaa_(logo).png, the silver KaZaA wordmark with
  lime ring, is too detailed at 14 px and isn't used.)
- Azureus blue poison-dart frog: cut from `source/azureus/logo.png`, from
  https://commons.wikimedia.org/wiki/File:Azureus_torrent.png (the .torrent file icon; the page and
  label are masked out). In the emblem spot.
- Napster logo (c) Napster.
- LimeWire logo (c) Lime Wire LLC.
- Kazaa logo (c) Sharman Networks.
- Azureus logo (c) Aelitis / Vuze.
