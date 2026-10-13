"""Synthetic Bayer RAW with known ground truth.

Why: real DNGs have no ground truth. A synthetic capture lets each module be
checked against a known answer (true black level, true illuminant gains,
known hot-pixel positions) before moving on to real data.
"""
from __future__ import annotations

import numpy as np

from .cfa import channel_view

# Sensor response to a neutral surface under the simulated illuminant
# (tungsten-ish: weak blue, weaker red relative to green).
DEFAULT_CAST = {"R": 0.55, "G": 1.0, "B": 0.70}


def make_scene(h: int = 512, w: int = 768, seed: int = 0, gray_only: bool = False) -> np.ndarray:
    """Linear RGB scene in [0, 1], shape (h, w, 3)."""
    rng = np.random.default_rng(seed)
    scene = np.empty((h, w, 3))
    ramp = np.linspace(0.02, 0.9, w)[None, :, None]
    scene[:] = ramp
    if not gray_only:
        # bottom half: 4 x 6 patches of random, mildly saturated colours
        top = h // 2
        ph, pw = (h - top) // 4, w // 6
        for i in range(4):
            for j in range(6):
                base = rng.uniform(0.1, 0.7)
                tint = rng.uniform(-0.15, 0.15, size=3)
                tint -= tint.mean()  # keep each patch's mean roughly neutral overall
                scene[top + i * ph: top + (i + 1) * ph, j * pw:(j + 1) * pw] = np.clip(base + tint, 0, 1)
    return scene


def mosaic(rgb: np.ndarray, pattern: str = "RGGB") -> np.ndarray:
    h, w, _ = rgb.shape
    out = np.empty((h, w))
    idx = {"R": 0, "Gr": 1, "Gb": 1, "B": 2}
    for ch, k in idx.items():
        channel_view(out, pattern, ch)[:] = channel_view(rgb[..., k], pattern, ch)
    return out


def make_raw(
    h: int = 512,
    w: int = 768,
    pattern: str = "RGGB",
    bit_depth: int = 12,
    black_level: int = 256,
    cast: dict | None = None,
    e_per_dn: float = 2.0,
    read_noise_dn: float = 2.0,
    n_hot: int = 20,
    seed: int = 0,
    gray_only: bool = False,
    noise: bool = True,
) -> tuple[np.ndarray, dict]:
    cast = cast or DEFAULT_CAST
    rng = np.random.default_rng(seed)
    white = 2**bit_depth - 1
    span = white - black_level

    scene = make_scene(h, w, seed, gray_only)
    sensor = scene * np.array([cast["R"], cast["G"], cast["B"]])
    signal = mosaic(sensor, pattern) * 0.85 * span  # DN above black

    if noise:
        signal = rng.poisson(np.clip(signal, 0, None) * e_per_dn) / e_per_dn  # shot noise
        signal = signal + rng.normal(0, read_noise_dn, signal.shape)          # read noise
    raw = np.clip(np.rint(signal + black_level), 0, white)

    hot = rng.choice(h * w, size=n_hot, replace=False) if n_hot else np.array([], int)
    raw.flat[hot] = white

    meta = {
        "cfa": pattern,
        "bit_depth": bit_depth,
        "black_level": black_level,
        "white_level": white,
        "source": "synthetic",
        "gt": {
            "awb_gains": {"R": cast["G"] / cast["R"], "G": 1.0, "B": cast["G"] / cast["B"]},
            "hot_pixels": [int(i) for i in hot],
            "e_per_dn": e_per_dn,
            "read_noise_dn": read_noise_dn,
        },
    }
    return raw.astype(np.uint16), meta
