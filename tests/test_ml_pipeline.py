"""Regression tests for feature extraction, group separation and toy pipeline."""
import csv

import numpy as np
import pytest

from image_forensics.features.patches import (
    FEATURE_NAMES, labels_from_mask, patch_features, patch_map
)
from image_forensics.detection.train import grouped_indices, train_and_evaluate
from image_forensics.detection.synthetic_data import make_dataset
from image_forensics.detection.infer import infer_image


def test_patch_feature_shape_and_finite_values():
    rng = np.random.default_rng(123)
    rgb = rng.integers(0, 256, (64, 96, 3), dtype=np.uint8)
    features, boxes, shape = patch_features(rgb)
    assert features.shape == (6, len(FEATURE_NAMES))
    assert len(boxes) == 6 and shape == (64, 96)
    assert np.isfinite(features).all()


def test_mask_label_and_reconstruction():
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[:32, :32] = 255
    _, boxes, shape = patch_features(np.zeros((64, 64, 3), dtype=np.uint8))
    labels = labels_from_mask(mask, boxes)
    assert labels.tolist() == [1, 0, 0, 0]
    assert np.array_equal(patch_map(labels, boxes, shape), mask)


def test_group_split_prevents_source_leakage():
    groups = np.repeat(np.arange(30), 16)
    train, val, test = grouped_indices(groups, seed=42)
    assert set(groups[train]).isdisjoint(set(groups[val]))
    assert set(groups[val]).isdisjoint(set(groups[test]))
    assert set(groups[train]).isdisjoint(set(groups[test]))
    assert len(train) + len(val) + len(test) == len(groups)


def test_synthetic_pipeline_trains_and_infers(tmp_path):
    manifest = make_dataset(tmp_path / "toy", count=36)
    report = train_and_evaluate(manifest, tmp_path / "trained")
    assert report["status"] == "EXPERIMENTAL_NO_VALIDADO"
    assert report["test"]["tp"] + report["test"]["fp"] + report["test"]["fn"] + report["test"]["tn"] > 0
    assert (tmp_path / "trained" / "model.joblib").exists()
    assert (tmp_path / "trained" / "metrics.json").exists()
    # Only read artifacts produced by this very test.
    import joblib
    artifact = joblib.load(tmp_path / "trained" / "model.joblib")
    rgb = np.full((64, 64, 3), 140, dtype=np.uint8)
    mask = infer_image(rgb, artifact)
    assert mask.shape == (64, 64)
    assert set(np.unique(mask)).issubset({0, 255})


def test_invalid_image_rejected():
    with pytest.raises(ValueError):
        patch_features(np.zeros((12, 12, 3), dtype=np.uint8))
