# Vaporwave (private variant)

The public Vaporwave skin (`skins/vaporwave/`, CC0) with a different main titlebar: a full-width
"VAPORWAVE" in the skin's spaced, cyan-ghosted pixel lettering instead of "YTMinamp".
`gen_skin.py` here only runs the public generator (by its path relative to this folder) with
`--title`, `--name Vaporwave` and `--out` set to this folder; the look lives in the public
generator, so changes go there.

```sh
/usr/bin/python3 -I gen_skin.py
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Vaporwave.wsz` and `preview.png` here; sheets in `out/` (ignored). Deterministic. The
.wsz is finished by `skins/genex_wacup.py`, as the public one is.
