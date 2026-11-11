"""Dataset preflight smoke tests."""
import csv
import numpy as np
from PIL import Image
from image_forensics.detection.audit_dataset import audit_manifest


def write_manifest(root, entries):
    path = root / "manifest.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["image", "mask", "group", "source"])
        writer.writeheader()
        writer.writerows(entries)
    return path


def test_valid_controlled_pair(tmp_path):
    Image.fromarray(np.zeros((32, 32, 3), dtype=np.uint8)).save(tmp_path / "a.png")
    Image.fromarray(np.zeros((32, 32), dtype=np.uint8)).save(tmp_path / "mask.png")
    manifest = write_manifest(tmp_path, [{"image": "a.png", "mask": "mask.png",
                                          "group": "source1", "source": "controlled"}])
    report = audit_manifest(manifest)
    assert report["ready"]
    assert report["empty_masks"] == 1


def test_mismatched_shape_rejected(tmp_path):
    Image.fromarray(np.zeros((32, 32, 3), dtype=np.uint8)).save(tmp_path / "a.png")
    Image.fromarray(np.zeros((31, 32), dtype=np.uint8)).save(tmp_path / "mask.png")
    manifest = write_manifest(tmp_path, [{"image": "a.png", "mask": "mask.png",
                                          "group": "source1", "source": "controlled"}])
    report = audit_manifest(manifest)
    assert not report["ready"]
    assert any("dimensiones" in p for p in report["problems"])
