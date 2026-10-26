#!/usr/bin/python3
"""VFD and VFD Silver: the public skins/vfd generator with a head-unit titlebar.

Runs ../../../../skins/vfd/gen_skin.py with the main titlebar printing "HIGH POWER 50W×4"
instead of "YTMinamp", writing VFD.wsz, VFD-Silver.wsz and their previews here (sheets in out/).
Arguments pass through: a theme name (vfd, vfd-silver) builds one; --list lists them.

    /usr/bin/python3 -I gen_skin.py [vfd|vfd-silver ...]
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "skins", "vfd", "gen_skin.py"))
TITLE = "HIGH POWER 50W×4"

if __name__ == "__main__":
    cmd = [sys.executable, "-I", PUBLIC, "--title", TITLE, "--name", "VFD", "--out", HERE] + sys.argv[1:]
    sys.exit(subprocess.run(cmd).returncode)
