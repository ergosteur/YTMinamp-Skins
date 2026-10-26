# Android: Android 2.3, 4.0 and 6.0

Three classic skins from one procedural generator (`gen_skin.py`, based on `skins/ember/gen_skin.py`
and keeping its sheet layouts), a theme each. The one mark used is the Android robot, drawn as a
13x15 pixel emblem in #a4c639 in the About spot (bottom right of the main window). Everything
else is drawn by the script: gradients, anti-aliased shapes, hand-made pixel fonts, and Droid Sans
(2.3) or Roboto (4.0, 6.0) for window titles, clock and time digits.

```sh
/usr/bin/python3 -I gen_skin.py                # all of them
/usr/bin/python3 -I gen_skin.py ics            # some (gingerbread, ics, marshmallow)
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Android-2.3.wsz`, `Android-4.0.wsz`, `Android-6.0.wsz` and `preview-<theme>.png` here;
sheets in `out/<theme>/` (`out/` is ignored). Deterministic (fixed zip timestamps, no noise).

## Themes

All three use the phone's status bar as the main window's titlebar: a notification icon (a note)
on the left, then the era's data, signal, battery icons and a 12:30 clock on the right. EQ,
playlist and other windows get the era's app title bar.

- **Gingerbread** (2.3, 2010): black body; status bar in a dark gradient with #99cc00 green icons,
  "3G" and signal bars and a white clock. The transport is the stock music player's dark media
  buttons, which turn the 2.x yellow-orange when pressed. Shuffle, repeat, EQ/PL, ON/AUTO and the
  playlist buttons are the light grey 2.x buttons; the toggles are ToggleButtons with a green
  light. The seek, volume and EQ sliders use the 1.x-2.3 grey progress track with its yellow fill
  and the silver round thumb. Title bars are the grey-gradient window titles. Playlist: white on
  black, #99cc00 current, orange selection. Font: Droid Sans.
- **Ice Cream Sandwich** (4.0, 2011, Holo Dark): black body fading to Holo's #272d33. Status bar:
  black, with Holo blue (#33b5e5) wifi and signal, a white battery and clock. Displays are Holo
  text fields (a blue underline with end ticks). Thin Roboto Light time digits, as on the ICS
  lockscreen; the title in Holo blue. The transport is flat white icons with thin dividers and a
  blue pressed state. Sliders are thin grey lines with a blue fill and Holo's blue dot-and-halo
  thumb. Toggles are Holo ToggleButtons (a blue indicator bar). Title bars are action bars with
  the blue underline. Playlist: light grey on black, Holo blue current, dark blue selection.
- **Marshmallow** (6.0, 2015, Material): light #fafafa body with white cards and soft shadows.
  Status bar in deep orange 700 (#e64a19) with white icons. The accent is **Google Play Music's
  deep orange #ff5722** rather than teal #009688: this is a music player, and Play Music was the
  stock Material music app of the time. Play is an orange floating action button; the other
  transport icons are grey with a grey ripple when pressed. Shuffle and repeat are Material icons
  (orange when on), EQ/PL are tabs with an orange indicator, ON is a Material switch, AUTO a
  checkbox, and PRESETS and the playlist buttons are flat orange text buttons. Sliders are a 2px
  track with an orange fill and dot thumb. Title bars are orange app bars with a shadow below.
  Playlist: #212121 on white, orange current, #ffccbc selection.

The app draws the main window's title in pledit.txt's font (`Droid Sans` or `Roboto`, falling back
to Arial) in text.bmp's ink: white (2.3), Holo blue (4.0), #212121 (6.0), each on its display.

## Limits

- The balance slider can't show which side it's on, so its track stays neutral. Only the centre
  mark changes: accent-coloured when centred. The seek bar has only its thumb.
- text.bmp, gen.bmp letters and small labels are pixel fonts (uppercase only), not Roboto.
- The Android 2.3 music app had no equalizer or playlist editor of this kind. Those windows borrow
  the era's dialog and title-bar look.
- The preview's "pressed close" on unfocused windows shows the focused bar's pressed sprite, as the
  app does (pressing a window focuses it).

## Sources

- Android robot: https://upload.wikimedia.org/wikipedia/commons/d/d7/Android_robot.svg (Wikimedia
  Commons, Google's robot, CC BY 3.0) in `source/android-robot/`. It served as the reference for the
  hand-drawn pixel emblem and its #a4c639 colour; the SVG itself isn't rasterised (at 15px its
  white separating strokes and eyes don't survive).
- Roboto: https://github.com/google/fonts/raw/main/ofl/roboto/Roboto%5Bwdth,wght%5D.ttf (Google
  Fonts, SIL Open Font License) in `source/roboto/`. It is used to render titles, clocks and digits
  into the bitmaps and for the previews; it is not shipped in the .wsz.
- Droid Sans: the system copy (`google-droid-sans-fonts`, Apache 2.0).
- Android robot logo (c) Google LLC (CC BY 3.0).
