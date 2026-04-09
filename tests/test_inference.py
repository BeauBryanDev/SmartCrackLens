"""
Group 3 — Geometry utilities & severity (T14–T21)
"""
import numpy as np
import pytest

from app.models.detections import Severity
from app.utils.geometry_utils import calculate_severity, sigmoid


# ---------------------------------------------------------------------------
# T14 — sigmoid(0) = 0.5
# ---------------------------------------------------------------------------

def test_sigmoid_zero_returns_half():
    result = sigmoid(np.array([0.0]))
    assert result[0] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# T15 — sigmoid of large positive value is close to 1.0
# ---------------------------------------------------------------------------

def test_sigmoid_large_positive_near_one():
    result = sigmoid(np.array([100.0]))
    assert result[0] > 0.99


# ---------------------------------------------------------------------------
# T16 — sigmoid of large negative value is close to 0.0
# ---------------------------------------------------------------------------

def test_sigmoid_large_negative_near_zero():
    result = sigmoid(np.array([-100.0]))
    assert result[0] < 0.01


# ---------------------------------------------------------------------------
# T17 — HIGH severity by area (area > 15 000)
# ---------------------------------------------------------------------------

def test_calculate_severity_high_by_area():
    assert calculate_severity(20000, 5) == Severity.HIGH


# ---------------------------------------------------------------------------
# T18 — HIGH severity by width (width > 60)
# ---------------------------------------------------------------------------

def test_calculate_severity_high_by_width():
    assert calculate_severity(100, 70) == Severity.HIGH


# ---------------------------------------------------------------------------
# T19 — MEDIUM severity by area (5 000 < area ≤ 15 000)
# ---------------------------------------------------------------------------

def test_calculate_severity_medium_by_area():
    assert calculate_severity(8000, 5) == Severity.MEDIUM


# ---------------------------------------------------------------------------
# T20 — MEDIUM severity by width (20 < width ≤ 60)
# ---------------------------------------------------------------------------

def test_calculate_severity_medium_by_width():
    assert calculate_severity(100, 30) == Severity.MEDIUM


# ---------------------------------------------------------------------------
# T21 — LOW severity (below all MEDIUM thresholds)
# ---------------------------------------------------------------------------

def test_calculate_severity_low():
    assert calculate_severity(100, 5) == Severity.LOW
    assert calculate_severity(0, 0) == Severity.LOW
