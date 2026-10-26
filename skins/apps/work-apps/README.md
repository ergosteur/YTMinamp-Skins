# Work Apps: Microsoft Teams, Slack (dark and light), Palo Alto Networks

Four classic skins from one procedural generator (`gen_skin.py`, built on
`skins/ember/gen_skin.py` by way of `private-repo/skins/apps/browsers/gen_skin.py`, keeping their
sheet layouts, helpers and preview code), a theme each. Each skin carries one real logo, in the
About spot or (Palo Alto) the main titlebar; the script draws everything else (gradients, pixel
fonts, icons, anti-aliased shapes).

```sh
/usr/bin/python3 -I gen_skin.py                  # all of them
/usr/bin/python3 -I gen_skin.py teams slack      # some (teams, slack, palo-alto, slack-light)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Microsoft-Teams.wsz`, `Slack.wsz`, `Slack-Light.wsz`, `Palo-Alto-Networks.wsz` and
`preview-<theme>.png` here (the windows assembled from the sprites the way the app does, 2x);
sheets in `out/<theme>/` and the rasterised logos in `out/scratch/` (`out/` is ignored).
Deterministic. Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

text.bmp's ink is dark on the white display fields in all of them, so the app's TrueType title is
dark on white. The preview draws it that way.

- **Microsoft Teams** (`teams`, the new Teams, 2023, Fluent 2, light theme):
  - The window is #f5f5f5 with a light grey title bar and white cards with hairline borders. The
    app rail is in classic Teams' dark #33344a: on the main window it holds the clutterbar,
    Activity, Chat and Teams (selected, with the purple pill). The Equalizer's rail continues
    with Calendar, Calls (selected), Files and "...".
  - The main window is a meeting. Its title bar reads "Now playing" and has a search box, a
    camera and a muted mic. Play is the purple **Join** button and stop is the red **Leave**
    button with a hang-up handset. Eject is **Share**.
  - Toggles carry a presence badge: green "Available" when on, grey "Offline" when off, and
    yellow "Away" while held. On REPEAT, which has no room beside its label, the badge sits on
    the corner. The play/pause/stop indicator is presence too: Available (play), Away (pause), Do
    not disturb (stop).
  - Sliders are Fluent: a purple fill and a white thumb in a purple ring.
  - The playlist is "Chat": dark text on white, the current track purple, the selection Teams'
    pale lavender.
  - The album-art frame has a meeting tile's name tag ("NOW PLAYING" with a muted mic).
  - The Equalizer's title bar has a search box and a signed-in avatar with a green dot.
  - The Teams logo is in the About spot.
- **Slack** (`slack`, the 2019 brand with the 2023 layout):
  - The title bars are the aubergine top bar (#350d36) and carry channel names: "# now-playing"
    (with a search box), "# equalizer v" (with the member avatars and count), and "# playlist"
    (with a red mention badge). A focused title is bold white, like an unread channel; an
    unfocused one is plain lilac, like a read one.
  - The main window and Equalizer are the white message pane, with the aubergine rail on the
    left: the clutterbar, Activity with a red "3" badge, DMs, and the workspace tile.
  - The title and info displays are one rounded composer box. The transport is the composer
    toolbar, with grey icons and the green (#007a5a) send button as play.
  - The toggles are emoji-reaction pills, grey or blue-ringed when "reacted": SHUFFLE has a
    shuffle icon, and REPEAT shows a loop icon with a count of 0 or 1.
  - The playlist is the channel sidebar: lilac text on aubergine, the current track white, and
    the selection in the classic selected-channel blue (#1164a3).
  - The spectrum runs through the four brand colours (red, yellow, green, blue). This is the
    only place they all appear.
  - The album-art frame shows "HUDDLE - LIVE".
  - The Slack hashtag logo is in the About spot.
- **Slack Light** (`slack-light`, the same with a light message pane): Slack with white text
  areas, like its message pane: the playlist (and any pledit-coloured text in the gen.bmp frames)
  is white with Slack's text colour, with a light scrollbar groove; the aubergine chrome stays.
  Playlist: #1D1C1D on #FFFFFF, #1264A3 current, #E8F5FA selection.
- **Palo Alto Networks** (`palo-alto`, a PA-series firewall front framing the PAN-OS web UI):
  - The chassis is black and dark grey. A vertical orange (#fa582d) stripe runs down every
    window's left edge, and every title bar has vent slots.
  - The main title bar is the front panel: the Palo Alto Networks logo (wordmark recoloured
    white for the dark chassis, the mark stays orange), "PA-460", vents, and a config-lock
    padlock.
  - The displays are PAN-OS white panels. The left one has a dashboard-widget header strip.
    Digits are PAN-OS dark blue, and the spectrum is blue with orange peaks.
  - Play is the orange **Commit** key, with "COMMIT" silkscreened under it. The other keys are
    dark chassis keys.
  - Toggles are chassis keys with a link LED under the label, green when on.
  - The About spot holds front-panel status LEDs: PWR, STS, HA (amber) and ALM (off).
  - The Equalizer's title bar is the PAN-OS tab row (DASHBOARD ACC MONITOR POLICIES OBJECTS
    NETWORK DEVICE) with ACC selected and the orange underline. Its sliders are orange-filled
    grooves with metal thumbs.
  - The playlist is the traffic log, titled "MONITOR > TRAFFIC": dark text on white, the current
    track in "allow" green, and the selection PAN-OS light blue. Its frame has a MGT LED, and its
    stretchable bottom tile is a pair of RJ45 ports with link and activity LEDs. The ports only
    show when the playlist is wider than 275 px.
  - The album-art frame shows "HA - ACTIVE".

## Limits

- New Teams' own rail is light. The brief asked for a dark rail, so the skin uses classic Teams'
  #33344a. The rail is 20 px wide beside the clutterbar, then narrows to 14 px (12 on the
  Equalizer and playlist, 11 on album art) so it stays clear of the seek bar and transport at
  x 16 and the Equalizer's ON button at x 14.
- The Slack and Teams camera, mic and member icons in the title bars are decoration, not
  buttons.
- PAN-OS colours are from memory of the 9.x-11.x UI, not measured: a dark header, grey-blue
  tables, link blue #0f6eaa and the brand orange.
- The playlist's bottom fill tile (Palo Alto's ports) is only drawn when the window is wider than
  the default.

## Sources

Downloaded into `source/`, rasterised with rsvg-convert (never executed) and composited once:

- Teams: https://commons.wikimedia.org/wiki/File:Microsoft_Office_Teams_(2018%E2%80%93present).svg
  in `source/logo-teams/`.
- Slack: https://commons.wikimedia.org/wiki/File:Slack_icon_2019.svg in `source/logo-slack/`
  (both Slack skins).
- Palo Alto Networks: https://commons.wikimedia.org/wiki/File:PaloAltoNetworks_2020_Logo.svg in
  `source/logo-paloalto/`.
- Microsoft Teams logo (c) Microsoft.
- Slack logo (c) Slack Technologies (Salesforce).
- Palo Alto Networks logo (c) Palo Alto Networks.
