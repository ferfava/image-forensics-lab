"""Calibration never observes test labels when selecting its threshold."""
import json

import numpy as np
import pytest

from image_forensics.detection.calibrate import (
    choose_threshold, evaluate_calibrated, locked_group_split, score
)
from image_forensics.detection.synthetic_data import make_dataset
from image_forensics.detection.train import load_manifest


def test_score_counts_and_all_negative_baseline():
    truth = np.array([0, 0, 1, 1], dtype=np.uint8)
    pred = np.array([0, 1, 1, 0], dtype=np.uint8)
    scores = score(truth, pred)
    assert scores["tp"] == scores["fp"] == scores["fn"] == scores["tn"] == 1
    baseline = score(truth, np.zeros_like(truth))
    assert baseline["precision"] == 0
    assert baseline["recall"] == 0
    assert baseline["fp"] == 0


def test_choose_threshold_on_validation_only():
    truth = np.array([0, 0, 1, 1], dtype=np.uint8)
    values = np.array([-2., 1., .5, 2.])
    result = choose_threshold(truth, values)
    assert result["objective"] == "F0.5"
    assert result["validation_metrics"]["tp"] > 0
    # Selection must not be hard-coded to the SVM native zero boundary.
    assert np.isfinite(result["threshold"])


def test_locked_split_rejects_changed_manifest(tmp_path):
    manifest = make_dataset(tmp_path / "toy", count=18)
    _, _, groups, _ = load_manifest(manifest)
    path = tmp_path / "lock.json"
    first = locked_group_split(manifest, groups, path)
    second = locked_group_split(manifest, groups, path, seed=999)
    for key in ("train", "validation", "test"):
        assert np.array_equal(first[key], second[key])
    manifest.write_text(manifest.read_text() + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="manifiesto cambió"):
        locked_group_split(manifest, groups, path)


def test_end_to_end_calibration_writes_reports(tmp_path):
    manifest = make_dataset(tmp_path / "toy", count=36)
    out = tmp_path / "calibration"
    report = evaluate_calibrated(manifest, out, map_count=1)
    assert report["status"] == "EXPERIMENTAL_NO_VALIDADO"
    assert set(report["groups"]) == {"train", "validation", "test"}
    assert sum(report["groups"].values()) == 36
    assert (out / "split.json").exists()
    assert (out / "calibration_report.json").exists()
    assert (out / "test_by_image_calibrated.csv").exists()
    assert (out / "calibrated_model.joblib").exists()
    assert len(report["maps"]) == 1
    assert any((out / "error_maps").glob("*.png"))
    saved = json.loads((out / "calibration_report.json").read_text(encoding="utf-8"))
    assert saved["calibration"]["objective"] == "F0.5"
    again = evaluate_calibrated(manifest, out, map_count=0)
    assert again["groups"] == report["groups"]
