"""Image-quality metrics. PSNR is done; the rest are yours to implement (milestone M6).

Implement each one yourself first, then cross-check against a library
(skimage.metrics, colour-science) in tests -- that cross-check is what makes
the number trustworthy in an interview.
"""
from __future__ import annotations

import numpy as np


def psnr(ref: np.ndarray, test: np.ndarray, peak: float) -> float:
    mse = np.mean((ref.astype(np.float64) - test.astype(np.float64)) ** 2)
    return float("inf") if mse == 0 else 10 * np.log10(peak**2 / mse)


def ssim(ref: np.ndarray, test: np.ndarray, peak: float) -> float:
    """TODO(M6): Wang et al. 2004, Gaussian window sigma=1.5, K1=0.01, K2=0.03."""
    raise NotImplementedError


def delta_e_2000(lab_ref: np.ndarray, lab_test: np.ndarray) -> np.ndarray:
    """TODO(M6): CIEDE2000 per patch. Verify with Sharma et al. 2005 test data."""
    raise NotImplementedError


def mtf_slanted_edge(roi: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """TODO(M6): ISO 12233 -> (freq cy/px, mtf, mtf50).
    edge fit -> 4x oversampled ESF -> LSF (derivative + window) -> |FFT|."""
    raise NotImplementedError
