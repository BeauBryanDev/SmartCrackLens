"""
Group 2 — Image utilities (T08–T13)
"""
import numpy as np
import pytest

from app.utils.image_utils import clamp_confidence, preprocess


# ---------------------------------------------------------------------------
# T08 — Square image: no padding, scale = 1.0
# ---------------------------------------------------------------------------

def test_preprocess_square_image_no_padding():
    img = np.zeros((640, 640, 3), dtype=np.uint8)
    blob, scale, pad_x, pad_y = preprocess(img)
    assert blob.shape == (1, 3, 640, 640)
    assert scale == pytest.approx(1.0)
    assert pad_x == pytest.approx(0.0)
    assert pad_y == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# T09 — Landscape image (H=480, W=640): vertical padding, scale=1.0
# ---------------------------------------------------------------------------

def test_preprocess_landscape_pads_top_bottom():
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    blob, scale, pad_x, pad_y = preprocess(img)
    assert blob.shape == (1, 3, 640, 640)
    # scale = min(640/640, 640/480) = 1.0  (width is the bottleneck)
    assert scale == pytest.approx(1.0)
    assert pad_y > 0
    assert pad_x == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# T10 — Portrait image (H=640, W=480): horizontal padding
# ---------------------------------------------------------------------------

def test_preprocess_portrait_pads_left_right():
    img = np.zeros((640, 480, 3), dtype=np.uint8)
    blob, scale, pad_x, pad_y = preprocess(img)
    assert blob.shape == (1, 3, 640, 640)
    assert pad_x > 0
    assert pad_y == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# T11 — Output dtype is float32 and values are in [0, 1]
# ---------------------------------------------------------------------------

def test_preprocess_output_dtype_and_range():
    img = np.full((300, 400, 3), 255, dtype=np.uint8)
    blob, *_ = preprocess(img)
    assert blob.dtype == np.float32
    assert blob.max() <= 1.0
    assert blob.min() >= 0.0


# ---------------------------------------------------------------------------
# T12 — clamp_confidence clamps values above 1.0 to 0.968
# ---------------------------------------------------------------------------

def test_clamp_confidence_above_one():
    assert clamp_confidence(1.5) == pytest.approx(0.968)
    assert clamp_confidence(2.0) == pytest.approx(0.968)


# ---------------------------------------------------------------------------
# T13 — clamp_confidence leaves values ≤ 1.0 unchanged
# ---------------------------------------------------------------------------

def test_clamp_confidence_normal_value_unchanged():
    assert clamp_confidence(0.75) == pytest.approx(0.75)
    assert clamp_confidence(1.0) == pytest.approx(1.0)
