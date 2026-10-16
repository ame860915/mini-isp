"""Import a real DNG into the repo's exchange format: <out>.raw + <out>.json

The result is the same kind of .raw/.json pair as tools/make_synthetic.py, so every other
tool (run_stage, inspect_raw, preview, pipeline, verify) works on it unchanged.

    python3 tools/import_dng.py ~/Pictures/IMG_0001.dng                  # -> data/IMG_0001.raw/.json
    python3 tools/import_dng.py ~/Pictures/IMG_0001.dng --out data/room
    python3 tools/import_dng.py ~/Pictures/IMG_0001.dng --crop 1536 1024  # centre crop, faster to iterate
    python3 tools/import_dng.py ~/Pictures/IMG_0001.dng --png data/IMG_0001.png

Or in one go (import + Python ref + C model + verify + preview):

    make dng DNG=~/Pictures/IMG_0001.dng

Needs rawpy:  pip install rawpy
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_ref"))
from mini_isp.cfa import channel_view  # noqa: E402
from mini_isp.raw_io import load_dng, save_raw  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("dng", help="path to the .dng file")
ap.add_argument("--out", help="output path without suffix (default: data/<dng name>)")
ap.add_argument("--crop", nargs=2, type=int, metavar=("W", "H"),
                help="centre crop to W x H (rounded down to even, CFA phase kept)")
ap.add_argument("--png", help="also save a half-res quick-look PNG")
a = ap.parse_args()

src = Path(a.dng).expanduser()
if not src.is_file():
    sys.exit(f"[dng] file not found: {src}")
out = Path(a.out) if a.out else Path("data") / src.stem

try:
    img, meta = load_dng(src)
except ImportError:
    sys.exit("[dng] rawpy is not installed:  pip install rawpy")
except Exception as e:  # rawpy raises its own LibRaw* errors for unreadable files
    sys.exit(f"[dng] cannot read {src.name}: {e}")

full_h, full_w = img.shape
if a.crop:
    cw, ch = (min(a.crop[0], full_w) // 2) * 2, (min(a.crop[1], full_h) // 2) * 2
    # Start on an even row/col so the crop keeps the same CFA pattern.
    y0 = ((full_h - ch) // 2) // 2 * 2
    x0 = ((full_w - cw) // 2) // 2 * 2
    img = img[y0:y0 + ch, x0:x0 + cw]
    meta["crop"] = {"x": x0, "y": y0, "width": cw, "height": ch, "full_width": full_w, "full_height": full_h}

save_raw(out, img, meta)

h, w = img.shape
bl, wl = meta["black_level"], meta["white_level"]
print(f"[dng] {src.name} -> {out}.raw  {w}x{h} {meta['cfa']}  "
      f"black={bl} white={wl} ({meta.get('bit_depth', 'unknown')}-bit)")
if "crop" in meta:
    print(f"[dng] centre crop from {full_w}x{full_h} at (x={meta['crop']['x']}, y={meta['crop']['y']})")
if "as_shot_awb_gains" in meta:
    g = meta["as_shot_awb_gains"]
    print(f"[dng] camera as-shot gains R={g['R']:.4f} B={g['B']:.4f}  (reference only, not ground truth)")

# Sanity checks that catch most "the colours look wrong" problems early.
bl_ch = meta["black_level_per_channel"]
bl_ch = meta.get("black_level_per_channel")

if bl_ch is None:
    print("[dng] info: per-channel black levels unavailable; scalar black_level is used")
elif len(bl_ch) != 4:
    print(f"[dng] warning: unexpected per-channel black levels: {bl_ch}")
elif max(bl_ch) - min(bl_ch) > 1:
    print(f"[dng] warning: per-channel black levels differ {bl_ch}; BLC uses {bl}")
for name in ("R", "Gr", "Gb", "B"):
    p = channel_view(img, meta["cfa"], name)
    clipped = float((p >= wl).mean()) * 100
    below = float((p < bl).mean()) * 100
    if clipped > 1:
        print(f"[dng] warning: {name} has {clipped:.1f}% pixels at white level (overexposed)")
    if below > 5:
        print(f"[dng] warning: {name} has {below:.1f}% pixels below black level; check black_level")
if np.median(img) < bl + 0.01 * (wl - bl):
    print("[dng] warning: image is very dark (median within 1% of black level)")

if a.png:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cfa = meta["cfa"]
    rgb = np.stack([channel_view(img, cfa, "R").astype(float),
                    0.5 * (channel_view(img, cfa, "Gr").astype(float) + channel_view(img, cfa, "Gb")),
                    channel_view(img, cfa, "B").astype(float)], -1)
    rgb = np.clip((rgb - bl) / max(wl - bl, 1), 0, 1) ** (1 / 2.2)
    Path(a.png).parent.mkdir(parents=True, exist_ok=True)
    plt.imsave(a.png, rgb)
    print(f"[dng] quick-look -> {a.png}")

print(f"[dng] next:  make verify preview INPUT={out}")
