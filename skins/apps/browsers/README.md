# Browsers: Chrome, Firefox, Discord, Netscape

Five classic skins from one procedural generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`
and keeping its sheet layouts), a theme each. Each carries its app's real logo once, in the About
spot under the EQ/PL buttons; everything else is drawn by the script.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py chrome discord # some (chrome, firefox, discord, chrome-blue,
                                               #   netscape)
/usr/bin/python3 -I gen_skin.py --list         # themes and their .wsz names
```

Outputs: `Chrome.wsz`, `Firefox.wsz`, `Discord.wsz`, `Chrome-Classic-Blue.wsz`, `Netscape-4.8.wsz`
and `preview-<theme>.png` here; sheets in `out/<theme>/`, rasterised logos in `out/scratch/`
(`out/` is ignored). Deterministic. Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

The app draws the main window's title in a TrueType font in text.bmp's ink colour, so each title
box contrasts with it (dark on white, #dbdee1 on #383a40); the previews draw it the same way.

- **Chrome** (`chrome`, Chrome 1 to 10, 2008 to early 2011, Windows, the era of the 3D logo):
  light blue gradient frame, trapezoid tabs ("New Tab" plus the slanted new-tab button), the
  wrench menu as the options button, flat caption glyphs, the pale toolbar, a white omnibox for
  the displays, flat grey toolbar glyphs for the transport (back/forward arrows for
  previous/next, the stop-loading cross for stop), thin blue progress and sliders.
- **Firefox** (`firefox`, Firefox 4, 2011, on Windows 7): Aero-glass blue frame, the orange
  Firefox menu button as the options button, rounded tabs on top, Windows 7 caption buttons, pale
  blue toolbar, white awesomebar displays, the transport as one rounded bar with the round
  "keyhole" button (play) in it, orange accents. Logo: the 2009 to 2013 one Firefox 4 shipped
  with.
- **Discord** (`discord`, today's dark theme): #1e1f22 titlebars with channel names
  (`# now-playing`), a server rail with the selected-server pill, #313338/#2b2d31 surfaces,
  #383a40 message-box displays, round "server icon" transport buttons that become blurple rounded
  squares when pressed (play is blurple), green status pills for toggles, red for the pressed
  close button, white slider grabbers. Logo: Clyde, white on a blurple circle.
- **Chrome Classic Blue** (`chrome-blue`): the `chrome` theme in classic Chrome's saturated blue
  window (the non-glass frame of Chrome on XP and Vista/7 basic, about #5b8fd6 to #2f5ea8): white
  caption glyphs and wrench, a white active tab, and a 3px blue frame round every window.
- **Netscape** (`netscape`, Netscape Communicator 4.8, 2002, the last 4.x, on Windows 9x): grey
  face with bevels, navy captions (the window icon is a hand-drawn Navigator ship's wheel),
  toolbar bands with collapse tabs and etched separators, the Navigation Toolbar as the transport
  with drawn coloured icons and labels (Back, Reload for play, Pause, Stop, Forward, Home for
  eject), Bookmarks/Location over the location field, latched toggles with the dithered face,
  progress-block sliders, and the N throbber (the real logo) in the About spot. The playlist's
  bottom carries the status bar (padlock, "Document: Done"), the Component Bar icons (Navigator,
  Mail, Composer, drawn) and a size grip.

## Limits

- None noted.

## Sources

- Chrome: https://commons.wikimedia.org/wiki/File:Google_Chrome_icon_(2011).png (the 2008-2011
  3D icon) in `source/logo-chrome/`, composited once.
- Firefox: https://commons.wikimedia.org/wiki/File:Mozilla_Firefox_3.5_logo.png in
  `source/logo-firefox/`, composited once.
- Discord: https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/discord.svg (Simple Icons'
  copy of the symbol from Discord's brand kit) in `source/logo-discord/`, rasterised with
  `rsvg-convert` and composited once.
- Netscape: https://commons.wikimedia.org/wiki/File:Netscape_icon.svg (the 4.x N over the
  horizon) in `source/logo-netscape/`, rasterised with `rsvg-convert` and cropped into the
  throbber box.
- Chrome logo (c) Google LLC.
- Firefox logo (c) the Mozilla Foundation.
- Discord logo (c) Discord Inc.
- Netscape logo (c) Netscape Communications (AOL).
