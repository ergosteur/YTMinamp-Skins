#!/usr/bin/python3
"""Tamagotchi: the public skins/pixel-pet generator with the toy's name in the titlebar.

Runs ../../../../skins/pixel-pet/gen_skin.py with the main titlebar lettering "TAMAGOTCHI"
(the generator's own chunky pixel letters, not Bandai's logo) instead of "YTMinamp", writing
Tamagotchi.wsz, preview.png and a readme.txt that names the toy here (sheets in out/).
Arguments pass through (--list lists the theme).

    /usr/bin/python3 -I gen_skin.py
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "skins", "pixel-pet", "gen_skin.py"))
TITLE = "TAMAGOTCHI"
NAME = "Tamagotchi"
README = """Tamagotchi - a skin in the style of the Tamagotchi.
===================================================

A classic (Winamp 2.x format) skin after the late-90s egg-shaped virtual-pet
keychain toy: glossy candy-pink plastic, round lemon buttons, a silver ball
chain, and a greenish-grey LCD with the care icons and a pixel creature in
headphones (an original character, not one of the toy's). The seek bar is the
creature taking a walk, and the volume is a row of hearts. Every bitmap was
drawn by a script; the titlebar lettering is drawn pixel by pixel, not the
toy's logo.

Tamagotchi (c) Bandai.
"""

if __name__ == "__main__":
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    readme = os.path.join(out, "readme-src.txt")
    with open(readme, "w", encoding="ascii") as f:
        f.write(README)
    cmd = [sys.executable, "-I", PUBLIC, "--title", TITLE, "--name", NAME, "--out", HERE,
           "--readme", readme] + sys.argv[1:]
    sys.exit(subprocess.run(cmd).returncode)
