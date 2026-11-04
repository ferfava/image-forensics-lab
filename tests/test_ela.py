"""Comportamiento numérico reproducible del ELA exploratorio."""
import numpy as np
import pytest
from image_forensics.processing.ela import compute_ela, compute_ela_raw


def test_ela_output_shape_dtype_and_range():
    rng = np.random.default_rng(42)
    image = rng.integers(0, 256, size=(80, 96, 3), dtype=np.uint8)
    result, mean, scale = compute_ela(image)
    assert result.shape == image.shape
    assert result.dtype == np.uint8
    assert 0 <= mean <= 255
    assert scale >= 1


def test_ela_rejects_invalid_input():
    with pytest.raises(ValueError):
        compute_ela(np.zeros((10, 10), dtype=np.uint8))
    with pytest.raises(ValueError):
        compute_ela(np.zeros((10, 10, 3), dtype=np.uint8), quality=100)


def test_ela_uniform_image_does_not_crash():
    image = np.full((32, 32, 3), 128, dtype=np.uint8)
    result, mean, _ = compute_ela(image)
    assert result.shape == image.shape
    assert mean >= 0


def test_raw_map_and_visual_scaling_do_not_change_error():
    rng = np.random.default_rng(17)
    image = rng.integers(0, 256, size=(40, 51, 3), dtype=np.uint8)
    raw, raw_mean, scale = compute_ela_raw(image)
    enhanced, enhanced_mean, enhanced_scale = compute_ela(image)
    expected = np.clip(raw.astype(np.float32) * scale, 0, 255).astype(np.uint8)
    assert np.array_equal(enhanced, expected)
    assert raw_mean == enhanced_mean
    assert scale == enhanced_scale
    assert raw.dtype == np.uint8


def test_raw_difference_of_uniform_black_image_is_zero():
    image = np.zeros((24, 24, 3), dtype=np.uint8)
    raw, mean, scale = compute_ela_raw(image)
    assert np.count_nonzero(raw) == 0
    assert mean == 0
    assert scale == 1
