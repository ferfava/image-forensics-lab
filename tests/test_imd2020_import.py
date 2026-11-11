"""Importer tests using the observed IMD2020 folder naming convention."""
import csv

import numpy as np
from PIL import Image

from image_forensics.detection.import_imd2020 import import_imd2020


def test_import_groups_original_and_multiple_edits(tmp_path):
    folder = tmp_path / "1a1ogs"
    folder.mkdir()
    photo = np.full((64, 64, 3), 100, dtype=np.uint8)
    Image.fromarray(photo).save(folder / "1a1ogs_orig.png")
    for name in ("c8tf5mq_0", "c8tf6mq_0"):
        variant = photo.copy()
        variant[8:24, 8:24] = 220
        mask = np.zeros((64, 64), dtype=np.uint8)
        mask[8:24, 8:24] = 240
        Image.fromarray(variant).save(folder / (name + ".png"))
        Image.fromarray(mask).save(folder / (name + "_mask.png"))
    result = import_imd2020(tmp_path, max_groups=1)
    assert result["groups"] == 1
    assert result["rows"] == 3
    with open(result["manifest"], encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(set(row["group"] for row in rows)) == 1
    assert all(row["group"] == "1a1ogs" for row in rows)
    for row in rows:
        with Image.open(tmp_path / row["mask"]) as stream:
            assert set(np.unique(np.asarray(stream)).tolist()).issubset({0, 255})


def test_unpaired_edits_are_skipped(tmp_path):
    folder = tmp_path / "case123"
    folder.mkdir()
    photo = np.full((64, 64, 3), 100, dtype=np.uint8)
    Image.fromarray(photo).save(folder / "case123_orig.png")
    Image.fromarray(photo).save(folder / "unpaired_0.png")
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[0:10, 0:10] = 255
    Image.fromarray(photo).save(folder / "paired_0.png")
    Image.fromarray(mask).save(folder / "paired_0_mask.png")
    result = import_imd2020(tmp_path)
    assert result["rows"] == 2
    assert result["warnings_count"] > 0
