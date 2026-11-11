"""Pruebas del comparador experimental de imágenes alineadas."""
import numpy as np
import pytest
from image_forensics.processing.comparison import compare_rgb


def test_identical_images_have_no_differences():
    rgb = np.full((24, 36, 3), 120, dtype=np.uint8)
    difference, mask, mae, changed = compare_rgb(rgb, rgb.copy())
    assert difference.shape == rgb.shape
    assert np.count_nonzero(difference) == 0
    assert np.count_nonzero(mask) == 0
    assert mae == 0
    assert changed == 0


def test_known_patch_is_counted_exactly():
    reference = np.zeros((10, 10, 3), dtype=np.uint8)
    candidate = reference.copy()
    candidate[2:5, 3:7, :] = 100
    difference, mask, mae, changed = compare_rgb(reference, candidate)
    assert difference[2, 3, 0] == 100
    assert np.count_nonzero(mask) == 12
    assert changed == 12.0
    assert mae == 12.0


def test_threshold_is_strict_and_affects_only_mask():
    reference = np.zeros((2, 2, 3), dtype=np.uint8)
    candidate = reference.copy()
    candidate[0, 0, 0] = 20
    candidate[0, 1, 0] = 21
    _, mask, mae, changed = compare_rgb(reference, candidate, threshold=20)
    assert mask[0, 0] == 0
    assert mask[0, 1] == 255
    assert changed == 25.0
    assert mae > 0


def test_different_dimensions_rejected():
    reference = np.zeros((10, 10, 3), dtype=np.uint8)
    candidate = np.zeros((11, 10, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="iguales dimensiones"):
        compare_rgb(reference, candidate)
