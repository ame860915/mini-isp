"""Black Level Correction.

out = max(raw - black_level, 0); the usable range becomes [0, white_level - black_level].
"""
from __future__ import annotations

import numpy as np

from .base import ISPModule


class BLC(ISPModule):
    name = "blc"

    def run(self, img, meta):
        bl = self.params.get("black_level", meta["black_level"])
        out = np.clip(img - bl, 0, None)
        meta["white_level"] = meta["white_level"] - bl
        meta["black_level"] = 0
        meta["blc_applied"] = bl
        return out, meta
