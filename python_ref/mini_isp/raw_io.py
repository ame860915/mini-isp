"""RAW I/O shared by the Python reference model and the C model.

Exchange format (kept deliberately simple so the C side needs no library):
    <name>.raw   little-endian uint16, row-major, height x width
    <name>.json  metadata: width, height, cfa, black_level, white_level, bit_depth, ...
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def save_raw(path: str | Path, img: np.ndarray, meta: dict) -> None:
    """Save a single-plane Bayer image. Float input is rounded and clipped to uint16."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if img.dtype != np.uint16:
        img = np.clip(np.rint(img), 0, 65535).astype(np.uint16)
    img.astype("<u2").tofile(path.with_suffix(".raw"))
    meta = dict(meta, width=int(img.shape[1]), height=int(img.shape[0]))
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2))


def load_raw(path: str | Path) -> tuple[np.ndarray, dict]:
    path = Path(path)
    meta = json.loads(path.with_suffix(".json").read_text())
    img = np.fromfile(path.with_suffix(".raw"), dtype="<u2")
    return img.reshape(meta["height"], meta["width"]), meta


def load_dng(path: str | Path) -> tuple[np.ndarray, dict]:
    """Read a DNG with rawpy (optional dependency) into the same (img, meta) form."""
    import rawpy  # imported lazily so the rest of the repo works without it

    with rawpy.imread(str(path)) as r:
        img = r.raw_image_visible.astype(np.uint16).copy()
        desc = r.color_desc.decode()  # usually "RGBG"
        pattern = "".join(desc[i] for i in r.raw_pattern.flatten())
        meta = {
            "cfa": pattern,
            "black_level": int(np.mean(r.black_level_per_channel)),
            "white_level": int(r.white_level),
            "camera_wb": [float(x) for x in r.camera_whitebalance],
            "color_matrix": np.asarray(r.color_matrix).tolist(),
            "source": str(path),
        }
    meta["width"], meta["height"] = img.shape[1], img.shape[0]
    return img, meta
