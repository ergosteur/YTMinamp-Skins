# VFD: the public VFD skins with a head-unit titlebar

Two skins from the public generator `skins/vfd/gen_skin.py` (see its README for the look), run by
this folder's `gen_skin.py` with the main titlebar printing "HIGH POWER 50W×4" (a generic
head-unit power rating, no brand) instead of "YTMinamp". Nothing else differs.

```sh
/usr/bin/python3 -I gen_skin.py                # both
/usr/bin/python3 -I gen_skin.py vfd-silver     # one
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `VFD.wsz`, `VFD-Silver.wsz` and `preview-<theme>.png` here; sheets in `out/<theme>/`
(`out/` is ignored). Deterministic. Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

- **VFD** (`vfd`): black gloss faceplate, one wide VFD window.
- **VFD Silver** (`vfd-silver`): satin silver faceplate, the displays as VFD glass.

## Limits

- None beyond the public skins'.

## Sources

- None: everything is drawn by the public generator.
