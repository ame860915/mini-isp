"""Generate a synthetic Bayer RAW with ground truth: data/synth.raw + data/synth.json"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_ref"))

from mini_isp.raw_io import save_raw  # noqa: E402
from mini_isp.synth import make_raw  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="data/synth")
ap.add_argument("--width", type=int, default=768)
ap.add_argument("--height", type=int, default=512)
ap.add_argument("--cfa", default="RGGB")
ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()

raw, meta = make_raw(h=a.height, w=a.width, pattern=a.cfa, seed=a.seed)
save_raw(a.out, raw, meta)
g = meta["gt"]["awb_gains"]
print(f"[synth] {a.width}x{a.height} {a.cfa} -> {a.out}.raw  (gt gains R={g['R']:.4f} B={g['B']:.4f})")
