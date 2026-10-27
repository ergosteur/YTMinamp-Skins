# scripts/

Maintainer notes. Not linked from the user-facing READMEs.

## build_gallery.py

The [gallery](https://ergosteur.github.io/YTMinamp-Skins/) is a GitHub Pages site served from the
repo root (branch `main`, `/`). It is a single static page, `index.html`, that loads
`gallery.json` and shows every committed `preview*.png` in a searchable grid, with a family
filter and a larger view that links the `.wsz` downloads. `.nojekyll` keeps GitHub from running
Jekyll over the repo.

`gallery.json` is generated, so after adding or renaming a skin:

```sh
python3 -I scripts/build_gallery.py   # rewrites gallery.json
git add gallery.json                  # then commit and push; Pages redeploys in a minute or so
```

- The script lists tracked files only, so `git add` the new skin's previews and `.wsz` first.
- Each folder with a `preview*.png` is one entry, titled from the first line of its `README.md`
  (`# Title`). The part before the first `:` is the tile's heading.
- A skin folder under `bundled-skins/` or one of the `skins/` families (`kpop`, `os`, `devices`,
  `games`, `apps`, `web`, `variants`) lands in that family. A new family needs a line in
  `FAMILIES` in `build_gallery.py`, or it shows under "Other".
- A preview is linked to one `.wsz` only when its name matches exactly (`preview-foo.png` and
  `Foo.wsz`, ignoring case and punctuation). Otherwise the larger view lists every `.wsz` in the
  folder.

## sync_skins.py

Copies skins from an upstream checkout into this repo, then stages them and regenerates
`gallery.json` (it runs `build_gallery.py` for you).

```sh
python3 -I scripts/sync_skins.py --skins PATH --dry-run   # list what would change
python3 -I scripts/sync_skins.py --skins PATH --bundled PATH2
git commit -am "Sync skins" && git push                   # nothing is committed for you
```

- `--skins` is the upstream directory that holds the family folders (`kpop`, `os`, ...), and
  `--bundled` the one with the bundled skin folders (it also picks up `genex_wacup.py`). Either can
  be set once in the environment as `SKINS_SRC` / `BUNDLED_SRC`. No path is stored in the repo.
- Only folders are copied: files at the top of the upstream directory are ignored, as are each
  skin's `out/` and `__pycache__/`. Nothing is deleted here, so a skin removed upstream stays
  until you remove it.
- If the upstream checkout has uncommitted changes under that directory, the script lists them
  before copying, since they are copied as they are. A half-finished generator can end up newer
  than its built `.wsz`, so commit upstream first or drop those files here.
- Use `git status` to review before committing. The Pages site rebuilds after a push.
