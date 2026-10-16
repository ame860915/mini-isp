import numpy as np
import pytest

from iq.metrics import psnr


def test_psnr_identical_is_inf():
    a = np.ones((4, 4))
    assert psnr(a, a, 1.0) == float("inf")


def test_psnr_known_value():
    a = np.zeros((10, 10))
    b = np.full((10, 10), 0.1)  # MSE = 0.01 -> 20 dB at peak 1
    assert abs(psnr(a, b, 1.0) - 20.0) < 1e-9


def test_psnr_matches_skimage():
    skm = pytest.importorskip("skimage.metrics")  # optional cross-check: pip install scikit-image
    rng = np.random.default_rng(0)
    a = rng.uniform(0, 1, (32, 32))
    b = np.clip(a + rng.normal(0, 0.05, a.shape), 0, 1)
    assert psnr(a, b, 1.0) == pytest.approx(skm.peak_signal_noise_ratio(a, b, data_range=1.0))
