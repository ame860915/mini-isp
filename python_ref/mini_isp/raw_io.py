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
    """Read a DNG with rawpy (optional dependency) into the same (img, meta) form.

    Only 2x2 Bayer RAWs are accepted (no X-Trans, no linear/demosaiced DNG). The image is
    cropped to even width/height so every 2x2 CFA tile is complete.
    """
    import rawpy  # imported lazily so the rest of the repo works without it

    with rawpy.imread(str(path)) as r:
        pat = r.raw_pattern
        if pat is None or pat.shape != (2, 2) or r.num_colors != 3:
            raise ValueError(f"{path}: not a 2x2 Bayer RAW (X-Trans / linear DNG are not supported)")
        desc = r.color_desc.decode()  # usually "RGBG"; index 3 is the second green
        pattern = "".join(desc[i] for i in pat.flatten())
        img = r.raw_image_visible.astype(np.uint16).copy()
        black_ch = [int(x) for x in r.black_level_per_channel]
        white = int(r.white_level)
        wb = [float(x) for x in r.camera_whitebalance]
        color_matrix = np.asarray(r.color_matrix).tolist()

    h, w = img.shape
    img = img[: h - h % 2, : w - w % 2]

    meta = {
        "cfa": pattern,
        "bit_depth": white.bit_length(),
        # The C model takes one black level; keep the per-channel values for reference.
        "black_level": int(round(float(np.mean(black_ch)))),
        "black_level_per_channel": black_ch,
        "white_level": white,
        "camera_wb": wb,
        "color_matrix": color_matrix,
        "source": str(path),
    }
    if wb[1] > 0 and wb[0] > 0 and wb[2] > 0:
        # Camera's own as-shot white balance, normalised to G = 1. A reference, not ground truth.
        meta["as_shot_awb_gains"] = {"R": wb[0] / wb[1], "G": 1.0, "B": wb[2] / wb[1]}
    meta["width"], meta["height"] = int(img.shape[1]), int(img.shape[0])
    return img, meta
