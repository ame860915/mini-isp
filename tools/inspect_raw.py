"""Print what is inside a stage dump: metadata, per-CFA-channel statistics, a pixel block.

    python tools/inspect_raw.py data/synth
    python tools/inspect_raw.py out/step/01_blc --at 300 400      # 4x4 block at row 300, col 400
    python tools/inspect_raw.py out/step/02_awb --png out/step/02_awb.png
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_ref"))
from mini_isp.cfa import channel_view
from mini_isp.raw_io import load_raw

ap = argparse.ArgumentParser()
ap.add_argument("path", help="stage path without suffix")
ap.add_argument("--at", nargs=2, type=int, default=[256, 384], metavar=("ROW", "COL"))
ap.add_argument("--png", help="also save a half-res quick-look PNG")
a = ap.parse_args()

img, meta = load_raw(a.path)
shown = {k: v for k, v in meta.items() if k != "gt"}
print(f"== {a.path}  shape={img.shape} dtype={img.dtype}")
print("meta:", json.dumps(shown))
if "gt" in meta:
    print("ground truth AWB gains:", meta["gt"]["awb_gains"])

wl = meta["white_level"]
print(f"\n{'ch':<3}{'min':>7}{'max':>7}{'mean':>10}{'std':>9}{'@white':>8}{'==0':>8}")
for ch in ("R", "Gr", "Gb", "B"):
    p = channel_view(img, meta["cfa"], ch)
    print(f"{ch:<3}{p.min():>7}{p.max():>7}{p.mean():>10.2f}{p.std():>9.2f}"
          f"{int((p >= wl).sum()):>8}{int((p == 0).sum()):>8}")

r, c = a.at
r, c = r - r % 2, c - c % 2  # align to the 2x2 CFA tile so the pattern reads correctly
print(f"\n4x4 pixels at ({r},{c})  [CFA {meta['cfa']}]:")
print(img[r:r + 4, c:c + 4])

if a.png:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cfa = meta["cfa"]
    rgb = np.stack([channel_view(img, cfa, "R").astype(float),
                    0.5 * (channel_view(img, cfa, "Gr").astype(float) + channel_view(img, cfa, "Gb")),
                    channel_view(img, cfa, "B").astype(float)], -1)
    bl = meta.get("black_level", 0)
    rgb = np.clip((rgb - bl) / max(wl - bl, 1), 0, 1) ** (1 / 2.2)
    Path(a.png).parent.mkdir(parents=True, exist_ok=True)
    plt.imsave(a.png, rgb)
    print(f"\nquick-look -> {a.png}")
