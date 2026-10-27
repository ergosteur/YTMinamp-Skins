# YTMinamp-Skins

Classic Winamp 2.x skins (.wsz) for YTMinamp's Winamp mode, each drawn by a script
(`gen_skin.py` in its folder). They also work in real Winamp and WACUP.

| Folder | What |
|---|---|
| [`bundled-skins/`](bundled-skins/) | The skins that ship with [YTMinamp-limusic](https://github.com/ergosteur/YTMinamp-limusic) releases (original designs, CC0) |
| [`skins/`](skins/) | The larger collection: K-pop, OS, device, game, app and web homages, plus extra variants |

**[Browse the skin gallery](https://ergosteur.github.io/YTMinamp-Skins/)** for a preview of every skin, with downloads.

## Using a skin

Each skin folder has a ready-built `.wsz` and a `preview*.png`. Load the `.wsz` in YTMinamp's
Winamp mode, or drop it in the `Skins` folder of Winamp or WACUP.

## Building a skin

Each generator needs Python 3 with Pillow and numpy:

```sh
cd skins/os/windows-xp        # or any folder with a gen_skin.py
python3 -I gen_skin.py        # build the .wsz and preview
python3 -I gen_skin.py --list # list theme names, where the script has several
```

## Use

The skins in `bundled-skins/` are original and CC0. Those in `skins/` are personal, private-use
skins and are not for commercial distribution. Many are homages to products, services, games and
artists, and some use their real logos, marks, sprites or photos, which belong to their owners;
credits are in each skin's `readme.txt` and each folder's `README.md`. None of this is
affiliated with or endorsed by any of them.
