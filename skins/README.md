# skins/

The full collection of Winamp 2.x skins (.wsz) for YTMinamp's Winamp mode. They also work in
real Winamp and WACUP.

## Use

These are personal, private-use skins and are not for commercial distribution. Many are homages
to products, services, games and artists, and some use their real logos, marks, sprites or
photos, which belong to their owners; credits are in each skin's `readme.txt` and each folder's
`README.md`. None of this is affiliated with or endorsed by any of them.

## Layout

| Folder | What |
|---|---|
| `kpop/` | ARTMS (group, members, objekts, light), its albums (Hyper-Ego, Club Icarus, Dall), LOONA (group, subunits, eras, light), NMIXX |
| `os/` | Windows 95 to 11, Mac OS 9 to Snow Leopard, iOS 6/7/26, Android, BlackBerry and Windows Mobile, KDE Breeze, Frutiger Aero |
| `devices/` | iPod classic and mini, iMac G3 and MacBook Pro, car audio (VW MIB II, Clarion, Honda Accord), Cisco Catalyst, Dell OptiPlex, Nortel Norstar and Millennium payphone, Panasonic boombox |
| `games/` | Xbox and PlayStation consoles, Nintendo handhelds and Wii/Switch, Steam/Minecraft/Twitch, Pokemon Gen 1-3 |
| `apps/` | Browsers and Discord, Office and MSN, Windows Media Player, streaming services, creative tools, file sharing, work tools |
| `web/` | 2000s web (MySpace, Facebook, Neopets), deviantArt, What.cd, Gmail, Reddit, 2012 social, Encarta and Tumblr |
| `variants/` | Alternate takes on the bundled designs: Ember, Pixel Pet, Vaporwave, VFD |

Each family folder is split into skin folders (for example `os/windows-xp/`). A skin folder holds
`gen_skin.py`, a `README.md`, the built `.wsz` files and their `preview*.png`, and, where the
skin uses downloaded references or logos, a `source/` folder. The generated sheets go in `out/`,
which each folder's own `.gitignore` excludes.
