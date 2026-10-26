# Pixel Pet: the public Pixel Pet skin titled for the Tamagotchi

One skin from the public generator `skins/pixel-pet/gen_skin.py` (see its README for the look),
run by this folder's `gen_skin.py` with the main titlebar lettering "TAMAGOTCHI" (the generator's
own chunky pixel letters, not Bandai's logo) instead of "YTMinamp", and a readme.txt that names
the toy and credits it. Nothing else differs; the pet is still the original headphone creature.

```sh
/usr/bin/python3 -I gen_skin.py
/usr/bin/python3 -I gen_skin.py --list
```

Outputs: `Tamagotchi.wsz` and `preview.png` here; sheets in `out/` (`out/` is ignored).
Deterministic. Each .wsz is finished by `skins/genex_wacup.py`.

## Themes

- **Tamagotchi** (`pixel-pet`): the Pixel Pet theme with "TAMAGOTCHI" in the main titlebar.

## Limits

- None beyond the public skin's.

## Sources

- None: everything is drawn by the public generator. Tamagotchi (c) Bandai.
