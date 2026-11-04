"""Comportamiento numérico reproducible del ELA exploratorio."""
import numpy as np
import pytest
from image_forensics.processing.ela import compute_ela


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
