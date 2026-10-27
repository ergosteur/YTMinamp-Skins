#!/usr/bin/env python3
"""Build gallery.json, the index behind the GitHub Pages gallery (index.html).

Run from anywhere: python3 -I scripts/build_gallery.py
Reads the committed files: each folder with a preview*.png becomes one entry, titled from its
README.md's H1, with its previews and every .wsz in the folder.
"""
import json
import os
import re
import subprocess
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAMILIES = [
    ("bundled-skins", "Bundled"),
    ("skins/kpop", "K-pop"),
    ("skins/os", "Operating systems"),
    ("skins/devices", "Devices"),
    ("skins/games", "Games"),
    ("skins/apps", "Apps"),
    ("skins/web", "Web"),
    ("skins/variants", "Variants"),
]


def family_of(folder):
    for prefix, name in FAMILIES:
        if folder == prefix or folder.startswith(prefix + "/"):
            return name
    return "Other"


def title_of(folder):
    try:
        with open(os.path.join(ROOT, folder, "README.md"), encoding="utf-8") as f:
            line = f.readline().strip()
        if line.startswith("# "):
            return line[2:]
    except OSError:
        pass
    return os.path.basename(folder)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def label_of(png):
    name = os.path.splitext(os.path.basename(png))[0]
    name = name[len("preview"):].lstrip("-_") or "default"
    return name.replace("-", " ")


def exact_wsz(png, wsz_names):
    """The .wsz this preview is named after, only when exactly one fits (else None)."""
    key = norm(os.path.splitext(png)[0][len("preview"):])
    hits = [w for w in wsz_names if key and norm(os.path.splitext(w)[0]) == key]
    return hits[0] if len(hits) == 1 else None


def main():
    files = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True,
                           check=True).stdout.splitlines()
    folders = defaultdict(lambda: {"previews": [], "wsz": []})
    for f in files:
        d, base = os.path.dirname(f), os.path.basename(f)
        if re.fullmatch(r"preview.*\.png", base):
            folders[d]["previews"].append(base)
        elif base.endswith(".wsz"):
            folders[d]["wsz"].append(base)

    order = [name for _, name in FAMILIES]
    entries = []
    for d in sorted(folders):
        v = folders[d]
        if not v["previews"]:
            continue
        entries.append({
            "family": family_of(d),
            "folder": d,
            "title": title_of(d),
            "previews": [{"file": p, "label": label_of(p), "wsz": exact_wsz(p, v["wsz"])}
                         for p in sorted(v["previews"])],
            "wsz": sorted(v["wsz"]),
        })
    entries.sort(key=lambda e: (order.index(e["family"]) if e["family"] in order else 99,
                                e["folder"]))
    with open(os.path.join(ROOT, "gallery.json"), "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"{sum(len(e['previews']) for e in entries)} previews, {len(entries)} folders")


if __name__ == "__main__":
    main()
