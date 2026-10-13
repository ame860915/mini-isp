"""Auto White Balance: gray-world gain estimation + per-CFA-site gain apply.

Split the same way a real SoC does:
  * estimate_gains()  -> "firmware" side, float is fine (runs once per frame on statistics)
  * apply             -> "hardware" side, this is what the C fixed-point model implements
"""
from __future__ import annotations

import numpy as np

from ..cfa import channel_view
from .base import ISPModule


def estimate_gray_world(img: np.ndarray, meta: dict, sat_ratio: float = 0.95) -> dict:
    """Gray-world: assume the scene average is neutral -> gains = G_mean / C_mean.

    Pixels near saturation are excluded from the statistics, since a clipped
    channel no longer reflects the illuminant colour.
    """
    cfa = meta["cfa"]
    sat = sat_ratio * meta["white_level"]
    planes = {ch: channel_view(img, cfa, ch) for ch in ("R", "Gr", "Gb", "B")}
    valid = np.ones_like(planes["R"], dtype=bool)
    for p in planes.values():
        valid &= p < sat
    if valid.sum() == 0:
        return {"R": 1.0, "G": 1.0, "B": 1.0}
    mean = {ch: float(p[valid].mean()) for ch, p in planes.items()}
    g = 0.5 * (mean["Gr"] + mean["Gb"])
    return {"R": g / max(mean["R"], 1e-6), "G": 1.0, "B": g / max(mean["B"], 1e-6)}


class AWB(ISPModule):
    name = "awb"

    def run(self, img, meta):
        method = self.params.get("method", "gray_world")
        if method == "gray_world":
            gains = estimate_gray_world(img, meta, self.params.get("sat_ratio", 0.95))
        elif method == "manual":
            gains = dict(self.params["gains"])
        else:
            raise ValueError(f"Unknown AWB method {method!r}")

        cfa = meta["cfa"]
        for ch, key in (("R", "R"), ("Gr", "G"), ("Gb", "G"), ("B", "B")):
            v = channel_view(img, cfa, ch)
            v *= gains[key]
        img = np.clip(img, 0, meta["white_level"])
        meta["awb_gains"] = gains
        return img, meta
