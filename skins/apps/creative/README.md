# Creative: FL Studio, RealPlayer 10, Photoshop CS6, RealOne Player

Four classic skins from one procedural generator (`gen_skin.py`, built on
`skins/ember/gen_skin.py` by way of `private-repo/skins/apps/wmp/gen_skin.py`, keeping their sheet
layouts, helpers and preview renderer), a theme each. The first three carry one real logo in the
About spot; RealOne Player's blue "1" is drawn by the script, once, in the titlebar. The script
draws everything else.

```sh
/usr/bin/python3 -I gen_skin.py                         # all of them
/usr/bin/python3 -I gen_skin.py fl-studio photoshop     # some (fl-studio, realplayer, photoshop, realone)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `FL-Studio.wsz`, `RealPlayer-10.wsz`, `Photoshop-CS6.wsz`, `RealOne-Player.wsz` and
`preview-<theme>.png` here;
sheets in `out/<theme>/` and the rasterised logos in `out/scratch/` (`out/` is ignored).
Deterministic. Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

text.bmp's ink matches each title box (lime on black, ice blue on navy, light grey on dark grey,
near-black on lime). The preview draws the app's TrueType title in that ink (RealOne Player's on
the y 27 title row; the older three keep their previews as built).

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
- **RealOne Player** (`realone`, RealOne Player 2001-2002 on Windows XP, from the user's
  screenshot): a pale grey-green frame (#E2E8E2 to #D0D9D1) around white (#FAFAFA) panels.
  - The main titlebar is RealOne's menu row: the blue "1" as the options button, "RealOne" in
    #1868A8 and "Player" in grey on the darker left part, then File View Play Tools Help (access
    keys underlined) on a lighter shelf that rises in a curve, and XP-style minimise, maximise
    (shade) and close glyphs.
  - The displays are the lime status bar (#C8E060), one L-shaped bar: time and visualiser on the
    left, the title, kbps, kHz and mono/stereo across. text.bmp, the digits and the visualiser
    are near-black (#161E08) and olive on the lime.
  - The transport sits in a soft capsule: round grey-ringed buttons with pale faces, the big play
    button with its tail, all lime-tinted when pressed. The seek bar is RealOne's thin dark line
    with a silver knob. Volume is the wedge filled lime up to a round silver knob; balance a flat
    track filled lime from the centre.
  - Shuffle, repeat, EQ and PL are grey capsules that light lime when on; the clutterbar is a
    column of small grey keys, lime when on. The About spot is the status bar's Web key, a globe
    with a play badge on pale yellow.
  - The Equalizer's ON, AUTO and PRESETS are the home page's navy, purple and burgundy nav
    buttons with white arrows (ON and AUTO with a lime light); the graph is a lime display; the
    sliders are grey tracks filling lime under silver knobs; the band names sit on a blue
    section header (#1860A8).
  - Playlist and album-art titles are the bottom tab bar's raised white tab ("Now Playing" with
    its icon), open into the white list below. The playlist's ADD, REM, SEL, MISC and LIST are
    tab-bar items: a small coloured icon over the name.
  - Playlist: #1E2430 on #FAFAFA, #1868A8 current, #C8DCF0 selection. Font: Tahoma.

## Limits

- The playlist's side tiles repeat every 29 px and its rows are 15 px, so Photoshop's eye icons
  can't line up with layer rows. They are left out; the panel's footer carries the Layers look
  instead.
- Photoshop's volume and balance thumbs are opaque 14 px cells, so they carry their own piece of
  the line. Balance's is the line's centre colours, which matches exactly only near the centre.
- FL's channel rack and pattern clips are decoration only: the step pattern is fixed.
- RealPlayer 10's own window was darker and flatter than RealOne's. This skin leans on the
  RealOne-era chrome, glossy pills and swooshes, as asked. Its description ("RealPlayer 10 /
  RealOne Player") is also written into its readme.txt, so it is left as is to keep the .wsz
  unchanged; RealOne Player proper is the `realone` theme.
- RealOne Player: Winamp's transport order (previous, play, pause, stop, next) and fixed spots
  can't give RealOne's play, stop, previous|next pill pair, so every button is a separate round
  one; the browser toolbar, the Location field and the web page aren't drawn (only the page's
  nav-button and header colours, in the Equalizer). The volume and balance knobs are opaque
  cells carrying a piece of the track: the balance one shows it unfilled, as it can't know the
  side. Colours are sampled from the screenshot (a dithered 256-colour capture, so averaged).

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
- RealOne Player screenshot (2001-2002, Windows XP), the user's own: `source/realone-player.png`,
  reference only (colours sampled, nothing composited). The RealOne "1" is drawn by the script
  (the downloaded RealPlayer icon is the later "real" swoosh and "player" wordmark, not the "1").
- FL Studio logo (c) Image-Line.
- RealPlayer logo and RealOne "1" (c) RealNetworks.
- Photoshop icon (c) Adobe.
