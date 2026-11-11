"""V2 patch features and strictly identical V1/V2 evaluation splits."""
import json

import numpy as np
import pytest

from image_forensics.features.patches import FEATURE_NAMES, patch_features
from image_forensics.features.patches_v2 import FEATURE_NAMES_V2, patch_features_v2
from image_forensics.detection.calibrate import locked_group_split
from image_forensics.detection.compare_v2 import compare_v1_v2, prepare_features
from image_forensics.detection.infer import infer_image
from image_forensics.detection.synthetic_data import make_dataset


def test_v2_preserves_v1_and_has_finite_texture_features():
    rng = np.random.default_rng(7)
    rgb = rng.integers(0, 256, (64, 96, 3), dtype=np.uint8)
    v1, boxes, shape = patch_features(rgb)
    v2, boxes2, shape2 = patch_features_v2(rgb)
    assert boxes == boxes2 and shape == shape2
    assert v2.shape == (6, len(FEATURE_NAMES_V2))
    assert len(FEATURE_NAMES_V2) == len(FEATURE_NAMES) + 6
    assert np.array_equal(v1, v2[:, :len(FEATURE_NAMES)])
    assert np.isfinite(v2).all()
    assert np.all(v2[:, 8] >= 0)
    assert np.all(v2[:, 8] <= 1)


def test_uniform_image_has_no_context_disagreement():
    rgb = np.full((64, 64, 3), 121, dtype=np.uint8)
    v2, _, _ = patch_features_v2(rgb)
    assert np.all(v2[:, -4:] == 0)


def test_comparison_requires_existing_locked_split(tmp_path):
    manifest = make_dataset(tmp_path / "toy", count=18)
    with pytest.raises(FileNotFoundError, match="split bloqueado"):
        compare_v1_v2(manifest, tmp_path / "missing.json", tmp_path / "results")


def test_comparison_same_group_split_and_v2_inference(tmp_path):
    manifest = make_dataset(tmp_path / "toy", count=36)
    _, _, y, groups = prepare_features(manifest, progress=False)
    split = tmp_path / "locked.json"
    initial = locked_group_split(manifest, groups, split)
    result = compare_v1_v2(manifest, split, tmp_path / "results")
    assert result["same_split"] is True
    assert result["test_patches"] == len(initial["test"])
    assert result["test_positive"] == int(y[initial["test"]].sum())
    assert result["models"]["v1"]["n_features"] == 8
    assert result["models"]["v2"]["n_features"] == 14
    assert result["models"]["v1"]["test"]["tp"] + result["models"]["v1"]["test"]["fn"] == result["test_positive"]
    assert result["models"]["v2"]["test"]["tp"] + result["models"]["v2"]["test"]["fn"] == result["test_positive"]
    assert (tmp_path / "results" / "comparison_v1_v2.json").is_file()
    import joblib
    model = joblib.load(tmp_path / "results" / "v2_model.joblib")
    mask = infer_image(np.full((64, 64, 3), 120, dtype=np.uint8), model)
    assert mask.shape == (64, 64)
    assert set(np.unique(mask).tolist()).issubset({0, 255})


def test_locked_split_refuses_modified_manifest(tmp_path):
    manifest = make_dataset(tmp_path / "toy", count=18)
    _, _, _, groups = prepare_features(manifest, progress=False)
    split = tmp_path / "locked.json"
    locked_group_split(manifest, groups, split)
    manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="manifiesto cambió"):
        compare_v1_v2(manifest, split, tmp_path / "results")
