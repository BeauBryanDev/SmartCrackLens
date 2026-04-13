"""
Group 3 — Geometry utilities & severity (T14 - T24)
"""
import numpy as np
import pytest

from app.models.detections import Orientation, Severity
from app.utils.geometry_utils import (
    calculate_fractal_dimension,
    calculate_severity,
    sigmoid,
)
# T14 — sigmoid(0) = 0.5

def test_sigmoid_zero_returns_half():
    
    result = sigmoid(np.array([0.0]))
    assert result[0] == pytest.approx(0.5)


# T15 — sigmoid of large positive value is close to 1.0

def test_sigmoid_large_positive_near_one():
    
    result = sigmoid(np.array([100.0]))
    assert result[0] > 0.99



# T16 — sigmoid of large negative value is close to 0.0

def test_sigmoid_large_negative_near_zero():
    
    result = sigmoid(np.array([-100.0]))
    assert result[0] < 0.01


# T17 — HIGH severity by area (area > 15 000)

def test_calculate_severity_high_by_area():
    
    result = calculate_severity(
        mask_area_px=20000,
        max_width_px=5,
        fractal_dimension=1.1,
        orientation=Orientation.HORIZONTAL,
    )
    assert result == Severity.HIGH


# T18 — HIGH severity by width (width > 60)

def test_calculate_severity_high_by_width():
    
    result = calculate_severity(
        mask_area_px=100,
        max_width_px=70,
        fractal_dimension=1.1,
        orientation=Orientation.HORIZONTAL,
    )
    assert result == Severity.HIGH


# T19 — MEDIUM severity by area (5 000 < area ≤ 15 000)

def test_calculate_severity_medium_by_area():
    
    result = calculate_severity(
        mask_area_px=8000,
        max_width_px=5,
        fractal_dimension=1.1,
        orientation=Orientation.HORIZONTAL,
    )
    assert result == Severity.MEDIUM



# T20 — MEDIUM severity by width (20 < width ≤ 60)

def test_calculate_severity_medium_by_width():
    
    """T20 — 20 < max_width_px <= 60 must produce MEDIUM with low FD."""
    result = calculate_severity(
        mask_area_px=100,
        max_width_px=30,
        fractal_dimension=1.1,
        orientation=Orientation.HORIZONTAL,
    )
    assert result == Severity.MEDIUM


# T21 — LOW severity (below all MEDIUM thresholds)


def test_calculate_severity_low():
    
    assert calculate_severity(
        mask_area_px=100,
        max_width_px=5,
        fractal_dimension=1.1,
        orientation=Orientation.HORIZONTAL,
    ) == Severity.LOW

    assert calculate_severity(
        mask_area_px=0,
        max_width_px=0,
        fractal_dimension=1.0,
        orientation=Orientation.HORIZONTAL,
    ) == Severity.LOW



# T22 — T24  calculate_severity() — fractal dimension driven cases

def test_calculate_severity_high_by_fractal_dimension():
    
    result = calculate_severity(
        mask_area_px=500,
        max_width_px=5,
        fractal_dimension=1.52,
        orientation=Orientation.DIAGONAL,
    )
    assert result == Severity.HIGH
    
    
def test_calculate_severity_medium_by_fractal_dimension():
    
    result = calculate_severity(
        mask_area_px=500,
        max_width_px=5,
        fractal_dimension=1.31,
        orientation=Orientation.DIAGONAL,
    )
    assert result == Severity.MEDIUM
    
    
def test_calculate_severity_low_fractal_dimension_below_threshold():
    
    result = calculate_severity(
        mask_area_px=200,
        max_width_px=3,
        fractal_dimension=1.05,
        orientation=Orientation.VERTICAL,
    )
    assert result == Severity.LOW
    


# T25 — T26  Forked orientation escalation rule

def test_forked_escalates_low_to_medium():
    
    result = calculate_severity(
        mask_area_px=100,
        max_width_px=5,
        fractal_dimension=1.1,
        orientation=Orientation.FORKED,
    )
    assert result == Severity.MEDIUM
    
    
def test_forked_escalates_medium_to_high():

    result = calculate_severity(
        mask_area_px=100,
        max_width_px=5,
        fractal_dimension=1.25,
        orientation=Orientation.FORKED,
    )
    assert result == Severity.HIGH
  
  
# T27 — T28  calculate_fractal_dimension()

def test_fractal_dimension_empty_mask_returns_fallback():
    
    empty_mask = np.zeros((64, 64), dtype=np.uint8)
    result     = calculate_fractal_dimension(empty_mask)
    
    assert result == 1.0
    
    
    
def test_fractal_dimension_straight_line_is_near_one():
    
    mask = np.zeros((128, 128), dtype=np.uint8)
    mask[64, :] = 1   # single horizontal line of pixels

    result = calculate_fractal_dimension(mask)

    assert 1.0 <= result <= 1.20, (
        
        f"Expected FD in [1.0, 1.20] for a straight line, got {result}"
    )
