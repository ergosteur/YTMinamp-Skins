# Creative: FL Studio, RealPlayer 10, Photoshop CS6

Three classic skins from one procedural generator (`gen_skin.py`, built on
`skins/ember/gen_skin.py` by way of `private-repo/skins/apps/wmp/gen_skin.py`, keeping their sheet
layouts, helpers and preview renderer), a theme each. Each skin carries one real logo in the About
spot; the script draws everything else.

```sh
/usr/bin/python3 -I gen_skin.py                         # all of them
/usr/bin/python3 -I gen_skin.py fl-studio photoshop     # some (fl-studio, realplayer, photoshop)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `FL-Studio.wsz`, `RealPlayer-10.wsz`, `Photoshop-CS6.wsz` and `preview-<theme>.png` here;
sheets in `out/<theme>/` and the rasterised logos in `out/scratch/` (`out/` is ignored).
Deterministic. Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

text.bmp's ink matches each title box (lime on black, ice blue on navy, light grey on dark grey).
The preview draws the app's TrueType title in that ink.

- **FL Studio** (`fl-studio`, FL Studio 9 to 12, with grey-blue-green panels):
  - The main titlebar is FL's menu bar (FILE EDIT ADD PATTERNS VIEW OPTIONS TOOLS HELP), and the
    options button is FL's little window-menu arrow.
  - The time display is the song-position LCD, with lime digits over ghost segments. The
    visualiser is a green-yellow-red peak meter, and the title box is the hint bar.
  - The transport is a recessed panel of square FL buttons with a lime play glyph. A pressed
    button turns orange.
  - A channel-rack strip runs along the bottom: a mute LED, a KICK channel button and sixteen
    step buttons in groups of four, grey and red, some lit. The clutterbar is a column of step
    buttons too.
  - The seek bar is the playlist's time ruler, with the orange song-position marker as its thumb.
  - Volume is a horizontal peak meter with an FL fader cap. Balance lights orange outwards from
    the centre.
  - Toggles have FL's green LEDs, and shuffle and repeat turn orange when on.
  - The Equalizer is the Mixer ("Mixer - Master"). Each band is an insert strip with a peak
    meter, a fader groove, a fader cap and a name plate. PAN and VOL knobs replace the dB labels,
    and the EQ graph is drawn in orange.
  - The playlist is "Playlist - Song", with orange for the current track and a pattern-clip
    green for the selection. Pattern clips run along the bottom bar.
  - The FL fruit sits in the About spot.
- **RealPlayer 10** (`realplayer`, RealPlayer 10, 2004, with RealOne Player's millennium chrome):
  - The titlebars are metallic silver-blue with a glassy upper half. The main titlebar holds the
    tabs: a glossy blue "Now Playing" pill, then Music & My Library, CD and Burn.
  - The body is deep navy with translucent light-blue swooshes.
  - The control bar is a silver capsule, with a big glossy blue play button and glossy blue pill
    buttons for the rest of the transport and for shuffle and repeat.
  - The displays are navy glass with ice-blue text. The thumbs are silver beads and pills, and
    the clutterbar is a column of silver pills.
  - The Equalizer, playlist ("Now Playing") and album-art titles sit on glossy blue pills.
  - The blue "real" swoosh mark sits in the About spot.
- **Photoshop CS6** (`photoshop`, Photoshop CS6's dark interface: #535353 panels, #3c3c3c tab
  strips):
  - The main titlebar is the Move tool's Options bar: the tool-preset picker as the options
    button, then the "Auto-Select: Layer" checkbox and drop-down, and "Show Transform Controls".
  - The displays are dark fields, and the visualiser is a grey histogram.
  - The transport uses the Timeline panel's flat icons, which sit in a dark square when pressed.
  - Shuffle, Loop (repeat), EQ, PL, On and Auto are CS6 checkboxes.
  - The sliders are thin lines with triangle thumbs. Volume is an Opacity-style line filled in
    selection blue, balance is Color Balance's cyan-to-red line, the EQ sliders point left at
    their lines, and the seek bar is a ruler line.
  - The Equalizer is a panel with Equalizer, Adjustments and Styles tabs and a flyout menu. Its
    graph is the Curves grid, and its left edge carries the tool bar (move, marquee, lasso, crop,
    eyedropper, brush, stamp, eraser, gradient, pen) with the black and white colour swatches.
  - The playlist is the Layers panel, with Layers, Channels and Paths tabs and the #4a6fa5 layer
    selection. Its ADD, REM, SEL and MISC buttons are the panel's footer icons (new layer, trash,
    marquee, fx) above small labels.
  - The album-art title is an active panel tab, and the "Ps" CS6 icon sits in the About spot.

## Limits

- The playlist's side tiles repeat every 29 px and its rows are 15 px, so Photoshop's eye icons
  can't line up with layer rows. They are left out; the panel's footer carries the Layers look
  instead.
- Photoshop's volume and balance thumbs are opaque 14 px cells, so they carry their own piece of
  the line. Balance's is the line's centre colours, which matches exactly only near the centre.
- FL's channel rack and pattern clips are decoration only: the step pattern is fixed.
- RealPlayer 10's own window was darker and flatter than RealOne's. This skin leans on the
  RealOne-era chrome, glossy pills and swooshes, as asked.

## Sources

Each logo was downloaded into its own folder under `source/` and is opened only with Pillow (the
SVG is rasterised with `rsvg-convert`), then composited once in the About spot.

- FL Studio fruit (FL Studio 11/12 logo):
  https://en.wikipedia.org/wiki/File:FL_Studio_11_just_logo.png, in `source/logo-fl/`.
- RealPlayer logo: https://en.wikipedia.org/wiki/File:Realplayer_computer_icon.png, in
  `source/logo-real-icon/`. The script keeps only the blue "real" swoosh and drops the green
  "player".
- Photoshop CS6 icon: https://commons.wikimedia.org/wiki/File:Adobe_Photoshop_CS6_icon.svg, in
  `source/logo-ps/`.
- FL Studio logo (c) Image-Line.
- RealPlayer logo (c) RealNetworks.
- Photoshop icon (c) Adobe.
