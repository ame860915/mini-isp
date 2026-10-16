"""Compare any two stage dumps of the same size (e.g. Python vs C, or before vs after).

    python tools/diff_raw.py out/step/01_blc out/c/01_blc
    python tools/diff_raw.py out/step/02_awb out/c/02_awb --png out/step/awb_diff.png
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_ref"))
from mini_isp.raw_io import load_raw

ap = argparse.ArgumentParser()
ap.add_argument("a", help="reference (path without suffix)")
ap.add_argument("b", help="compared (path without suffix); C dumps need no .json")
ap.add_argument("--png", help="save an error heat map")
a = ap.parse_args()

ref, meta = load_raw(a.a)
b_path = Path(a.b)
if b_path.with_suffix(".json").exists():
    dut, _ = load_raw(b_path)
else:  # C model writes pixels only -> reuse the reference's shape
    dut = np.fromfile(b_path.with_suffix(".raw"), dtype="<u2").reshape(ref.shape)

err = dut.astype(np.int32) - ref.astype(np.int32)
ae = np.abs(err)
print(f"b - a : max abs {ae.max()}  mean abs {ae.mean():.4f}  exact {(ae == 0).mean() * 100:.2f}%")
vals, counts = np.unique(err, return_counts=True)
if len(vals) <= 15:
    print("error histogram:", dict(zip(vals.tolist(), counts.tolist(), strict=True)))
else:
    p = np.percentile(err, [1, 5, 50, 95, 99])
    print("error percentiles 1/5/50/95/99%:", " / ".join(f"{x:.0f}" for x in p))
if ae.max() > 0:
    r, c = np.unravel_index(np.argmax(ae), ae.shape)
    print(f"worst pixel ({r},{c}): a={ref[r, c]} b={dut[r, c]}")

if a.png:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    m = max(1, int(ae.max()))
    Path(a.png).parent.mkdir(parents=True, exist_ok=True)
    plt.imsave(a.png, err, cmap="coolwarm", vmin=-m, vmax=m)
    print(f"heat map -> {a.png}")
