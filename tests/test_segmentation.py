"""Casos controlados para evaluación de máscaras binarias."""
import numpy as np
import pytest
from image_forensics.evaluation.segmentation import evaluate_mask


def test_perfect_overlap():
    mask = np.zeros((8, 8), dtype=np.uint8)
    mask[2:5, 1:4] = 255
    score = evaluate_mask(mask, mask)
    assert (score["precision"], score["recall"], score["f1"], score["iou"]) == (1, 1, 1, 1)
    assert score["tp"] == 9
    assert not score["empty_case"]


def test_partial_overlap_and_false_positives():
    gt = np.zeros((2, 4), dtype=np.uint8)
    gt[0, :2] = 255
    pred = np.zeros_like(gt)
    pred[0, 1:3] = 255
    result = evaluate_mask(pred, gt)
    assert result["tp"] == 1 and result["fp"] == 1 and result["fn"] == 1
    assert result["precision"] == .5 and result["recall"] == .5
    assert result["f1"] == .5
    assert result["iou"] == 0.3333


def test_missed_region():
    gt = np.ones((3, 3), dtype=np.uint8)
    pred = np.zeros_like(gt)
    result = evaluate_mask(pred, gt)
    assert result["recall"] == result["f1"] == result["iou"] == 0


def test_empty_both_reported_explicitly():
    empty = np.zeros((5, 5), dtype=np.uint8)
    score = evaluate_mask(empty, empty)
    assert score["empty_case"]
    assert score["iou"] == score["f1"] == 1


def test_size_mismatch_rejected():
    with pytest.raises(ValueError):
        evaluate_mask(np.zeros((2, 2)), np.zeros((3, 3)))
