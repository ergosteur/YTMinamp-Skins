#!/usr/bin/python3
"""Vaporwave (private variant): the public generator, skins/vaporwave/gen_skin.py, run with a
full-width VAPORWAVE in the main titlebar instead of "YTMinamp".

Writes Vaporwave.wsz and preview.png into this folder (sheets in out/). Extra arguments (for
example --list) are passed through.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "skins", "vaporwave", "gen_skin.py"))
TITLE = "\uff36\uff21\uff30\uff2f\uff32\uff37\uff21\uff36\uff25"   # full-width VAPORWAVE

if __name__ == "__main__":
    sys.exit(subprocess.call([sys.executable, PUBLIC, "--title", TITLE, "--name", "Vaporwave", "--out", HERE]
                             + sys.argv[1:]))
