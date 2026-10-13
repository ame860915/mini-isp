"""Quick-look PNG of a Bayer stage dump: half-resolution RGB (no demosaic) + display gamma.

Not part of the ISP -- just a way to *see* each stage before demosaic exists.

    python tools/preview.py out/py/01_blc out/py/02_awb --out docs/img/stages.png
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_ref"))
from mini_isp.cfa import channel_view  # noqa: E402
from mini_isp.raw_io import load_raw  # noqa: E402


def half_rgb(img, meta):
    c = meta["cfa"]
    r = channel_view(img, c, "R").astype(float)
    g = 0.5 * (channel_view(img, c, "Gr").astype(float) + channel_view(img, c, "Gb"))
    b = channel_view(img, c, "B").astype(float)
    rgb = np.stack([r, g, b], -1) - meta.get("black_level", 0)
    rgb /= max(meta["white_level"] - meta.get("black_level", 0), 1)
    return np.clip(rgb, 0, 1) ** (1 / 2.2)


ap = argparse.ArgumentParser()
ap.add_argument("stages", nargs="+", help="stage paths without suffix")
ap.add_argument("--out", default="out/preview.png")
a = ap.parse_args()

fig, axes = plt.subplots(1, len(a.stages), figsize=(5 * len(a.stages), 4), squeeze=False)
for ax, s in zip(axes[0], a.stages, strict=True):
    img, meta = load_raw(s)
    ax.imshow(half_rgb(img, meta))
    ax.set_title(Path(s).name)
    ax.axis("off")
fig.tight_layout()
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
fig.savefig(a.out, dpi=110)
print(f"[preview] -> {a.out}")
