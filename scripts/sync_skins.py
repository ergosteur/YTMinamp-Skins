#!/usr/bin/env python3
"""Copy skins from an upstream checkout into this repo and refresh gallery.json.

    python3 -I scripts/sync_skins.py --skins PATH [--bundled PATH] [--dry-run]

PATH is the upstream directory that holds the family folders (kpop, os, ...) for --skins, or
the bundled skin folders for --bundled. They can also come from SKINS_SRC and BUNDLED_SRC in the
environment. No path is stored in this file.

Only folders are copied (top-level files upstream are ignored, apart from genex_wacup.py for
--bundled), and each skin's out/ and __pycache__/ are skipped. Nothing is committed or pushed;
review `git status` first.
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ["--exclude", "out", "--exclude", "__pycache__"]


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def sync(src, dest, extra_files=(), dry=False):
    src = os.path.abspath(os.path.expanduser(src))
    if not os.path.isdir(src):
        sys.exit(f"not a directory: {os.path.basename(src) or src}")
    dirty = subprocess.run(["git", "-C", src, "status", "--porcelain", "--", "."],
                           capture_output=True, text=True).stdout.splitlines()
    if dirty:
        print(f"warning: {len(dirty)} uncommitted upstream change(s) will be copied as they are:")
        for line in dirty[:20]:
            print("  " + line)
    flags = ["-a", "-i"] + (["-n"] if dry else []) + SKIP
    os.makedirs(os.path.join(ROOT, dest), exist_ok=True)
    for name in sorted(os.listdir(src)):
        if name.startswith(".") or name == "__pycache__" or not os.path.isdir(os.path.join(src, name)):
            continue
        run(["rsync", *flags, os.path.join(src, name) + "/", os.path.join(ROOT, dest, name) + "/"])
    for name in extra_files:
        if os.path.isfile(os.path.join(src, name)):
            run(["rsync", *flags, os.path.join(src, name), os.path.join(ROOT, dest, name)])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--skins", default=os.environ.get("SKINS_SRC"),
                    help="upstream directory with the family folders (kpop, os, ...)")
    ap.add_argument("--bundled", default=os.environ.get("BUNDLED_SRC"),
                    help="upstream directory with the bundled skin folders")
    ap.add_argument("--dry-run", action="store_true", help="list what would change, copy nothing")
    a = ap.parse_args()
    if not (a.skins or a.bundled):
        ap.error("give --skins and/or --bundled (or set SKINS_SRC / BUNDLED_SRC)")

    if a.skins:
        sync(a.skins, "skins", dry=a.dry_run)
    if a.bundled:
        sync(a.bundled, "bundled-skins", extra_files=["genex_wacup.py"], dry=a.dry_run)
    if a.dry_run:
        return

    # build_gallery.py reads tracked files, so stage the copies before regenerating
    run(["git", "-C", ROOT, "add", "skins", "bundled-skins"])
    run([sys.executable, "-I", os.path.join(ROOT, "scripts", "build_gallery.py")])
    run(["git", "-C", ROOT, "add", "gallery.json"])
    run(["git", "-C", ROOT, "status", "--short"])


if __name__ == "__main__":
    main()
