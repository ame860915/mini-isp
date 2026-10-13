import numpy as np

from iq.metrics import psnr


def test_psnr_identical_is_inf():
    a = np.ones((4, 4))
    assert psnr(a, a, 1.0) == float("inf")


def test_psnr_known_value():
    a = np.zeros((10, 10))
    b = np.full((10, 10), 0.1)  # MSE = 0.01 -> 20 dB at peak 1
    assert abs(psnr(a, b, 1.0) - 20.0) < 1e-9
