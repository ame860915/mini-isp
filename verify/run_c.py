"""Run the C model with the same inputs/parameters the Python reference used.

Black level comes from the input metadata; AWB gains come from the Python
estimate (out/py/params.json) -- the firmware -> hardware hand-off.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--input", default="data/synth")
ap.add_argument("--py", default="out/py")
ap.add_argument("--out", default="out/c")
ap.add_argument("--bin", default="c_model/build/mini_isp_c")
a = ap.parse_args()

inp = Path(a.input)
meta = json.loads(inp.with_suffix(".json").read_text())
params = json.loads((Path(a.py) / "params.json").read_text())
gains = params.get("awb_gains", {"R": 1.0, "G": 1.0, "B": 1.0})

out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
cmd = [
    a.bin,
    "--input", str(inp.with_suffix(".raw")),
    "--width", str(meta["width"]), "--height", str(meta["height"]),
    "--cfa", meta["cfa"],
    "--black", str(meta["black_level"]), "--white", str(meta["white_level"]),
    "--gain_r", repr(gains["R"]), "--gain_g", repr(gains["G"]), "--gain_b", repr(gains["B"]),
    "--out", str(out),
]
r = subprocess.run(cmd, check=False)
if r.returncode:
    sys.exit(r.returncode)

# C writes only pixels; reuse the Python stage metadata so dumps load the same way.
for js in Path(a.py).glob("[0-9][0-9]_*.json"):
    shutil.copy(js, out / js.name)
