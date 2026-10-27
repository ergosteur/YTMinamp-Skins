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
