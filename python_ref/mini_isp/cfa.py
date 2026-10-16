"""Bayer CFA helpers."""
from __future__ import annotations

import numpy as np

# Offset (row, col) of each colour site inside the 2x2 tile.
_PATTERNS = {
    "RGGB": {"R": (0, 0), "Gr": (0, 1), "Gb": (1, 0), "B": (1, 1)},
    "BGGR": {"B": (0, 0), "Gb": (0, 1), "Gr": (1, 0), "R": (1, 1)},
    "GRBG": {"Gr": (0, 0), "R": (0, 1), "B": (1, 0), "Gb": (1, 1)},
    "GBRG": {"Gb": (0, 0), "B": (0, 1), "R": (1, 0), "Gr": (1, 1)},
}


def cfa_offsets(pattern: str) -> dict[str, tuple[int, int]]:
    try:
        return _PATTERNS[pattern.upper()]
    except KeyError as e:
        raise ValueError(f"Unsupported CFA pattern {pattern!r}") from e


def channel_view(img: np.ndarray, pattern: str, ch: str) -> np.ndarray:
    """Strided view of one colour site (writes go back into img)."""
    r, c = cfa_offsets(pattern)[ch]
    return img[r::2, c::2]
