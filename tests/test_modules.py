import numpy as np
import pytest
from mini_isp.cfa import channel_view
from mini_isp.modules import AWB, BLC
from mini_isp.modules.awb import estimate_gray_world
from mini_isp.pipeline import build, run
from mini_isp.synth import make_raw


@pytest.fixture
def meta():
    return {"cfa": "RGGB", "black_level": 64, "white_level": 1023}


# ---------- CFA ----------
@pytest.mark.parametrize("pattern", ["RGGB", "BGGR", "GRBG", "GBRG"])
def test_cfa_views_partition_image(pattern):
    img = np.zeros((4, 6))
    for k, ch in enumerate(("R", "Gr", "Gb", "B"), 1):
        channel_view(img, pattern, ch)[:] = k
    assert set(np.unique(img)) == {1, 2, 3, 4}  # every pixel written exactly once


# ---------- BLC ----------
def test_blc_subtracts_and_clips(meta):
    img = np.array([[0, 64], [65, 1023]], dtype=np.uint16)
    out, m = BLC()(img, meta)
    np.testing.assert_array_equal(out, [[0, 0], [1, 959]])
    assert m["black_level"] == 0 and m["white_level"] == 959


def test_blc_does_not_mutate_input(meta):
    img = np.full((2, 2), 100, np.uint16)
    BLC()(img, meta)
    assert img[0, 0] == 100 and meta["black_level"] == 64


# ---------- AWB ----------
def test_gray_world_recovers_cast_on_gray_scene():
    raw, meta = make_raw(gray_only=True, noise=False, n_hot=0)
    img, meta = BLC()(raw, meta)
    g = estimate_gray_world(img, meta)
    gt = meta["gt"]["awb_gains"]
    assert g["R"] == pytest.approx(gt["R"], rel=0.01)
    assert g["B"] == pytest.approx(gt["B"], rel=0.01)


def test_awb_manual_gains_applied_per_site(meta):
    img = np.full((2, 2), 100.0)
    out, _ = AWB(method="manual", gains={"R": 2.0, "G": 1.0, "B": 1.5})(img, meta)
    np.testing.assert_allclose(out, [[200, 100], [100, 150]])


def test_awb_clips_to_white_level(meta):
    img = np.full((2, 2), 1000.0)
    out, _ = AWB(method="manual", gains={"R": 2.0, "G": 1.0, "B": 1.0})(img, meta)
    assert out.max() == meta["white_level"]


# ---------- pipeline ----------
def test_pipeline_from_config_runs():
    raw, meta = make_raw(h=64, w=96)
    stages = build({"pipeline": [{"module": "blc"}, {"module": "awb"}]})
    out, m = run(raw, meta, stages)
    assert out.shape == raw.shape and "awb_gains" in m


def test_unknown_module_rejected():
    with pytest.raises(KeyError):
        build({"pipeline": [{"module": "nope"}]})
