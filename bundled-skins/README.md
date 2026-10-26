# bundled-skins/

The skins that ship with [YTMinamp-limusic](https://github.com/ergosteur/YTMinamp-limusic)
releases. Each is drawn from scratch by its `gen_skin.py`, uses no third-party marks, and is
CC0 (see the skin's own `readme.txt`).

| Folder | Skin |
|---|---|
| `ytminamp/` | YTMinamp Dark and Light |
| `classic/` | Classic, the grey 3D desktop look |
| `breeze/` | Breeze Dark and Light |
| `material/` | Material Music |
| `frutiger-aero/` | Frutiger Aero |
| `green/` | Green |
| `slick/` | Slick |
| `vfd/` | VFD and VFD Silver |
| `ember/` | Ember |
| `pixel-pet/` | Pixel Pet |
| `vaporwave/` | Vaporwave |

Each folder holds `gen_skin.py`, a `README.md`, the built `.wsz` and a `preview*.png`; the
sheets in `out/` are ignored. Build one with `python3 -I gen_skin.py` (needs Pillow and numpy).

`ember/`, `pixel-pet/`, `vaporwave/` and `vfd/` also exist in
[`../skins/variants/`](../skins/variants/). The copies here carry the YTMinamp titlebar
branding; the ones in `skins/variants/` don't.
