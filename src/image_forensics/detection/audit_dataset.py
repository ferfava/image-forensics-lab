"""Audit a real-image localization manifest before any model training.

Usage:
python -m image_forensics.detection.audit_dataset --manifest data/real/manifest.csv
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image


def audit_manifest(manifest: Path) -> dict:
    with manifest.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("El manifiesto está vacío.")
    required = {"image", "mask", "group", "source"}
    if not required.issubset(rows[0]):
        raise ValueError("Faltan columnas: " + ", ".join(sorted(required - set(rows[0]))))
    problems, n_positive, n_negative, groups = [], 0, 0, Counter()
    seen = set()
    for index, row in enumerate(rows, 2):
        image_rel, mask_rel, group, source = (row.get(k, "").strip() for k in
                                               ("image", "mask", "group", "source"))
        if not all((image_rel, mask_rel, group, source)):
            problems.append(f"Fila {index}: campos vacíos")
            continue
        groups[group] += 1
        key = (image_rel, mask_rel)
        if key in seen:
            problems.append(f"Fila {index}: duplicado de imagen/máscara")
        seen.add(key)
        # Resolve paths without allowing traversal outside the dataset folder.
        root = manifest.parent.resolve()
        image_path = (root / image_rel).resolve()
        mask_path = (root / mask_rel).resolve()
        if not image_path.is_relative_to(root) or not mask_path.is_relative_to(root):
            problems.append(f"Fila {index}: ruta fuera del dataset")
            continue
        try:
            with Image.open(image_path) as img, Image.open(mask_path) as mask:
                if img.size != mask.size:
                    problems.append(f"Fila {index}: dimensiones distintas")
                    continue
                gray = np.asarray(mask.convert("L"), dtype=np.uint8)
                if gray.max() == 0:
                    n_negative += 1
                elif gray.min() >= 128:
                    problems.append(f"Fila {index}: máscara completamente positiva")
                    n_positive += 1
                else:
                    n_positive += 1
                values = set(np.unique(gray).tolist())
                if not values.issubset({0, 255}):
                    problems.append(f"Fila {index}: máscara no binaria; valores {len(values)}")
        except (OSError, ValueError) as exc:
            problems.append(f"Fila {index}: lectura fallida ({exc})")
    return {
        "images": len(rows), "groups": len(groups),
        "positive_masks": n_positive, "empty_masks": n_negative,
        "group_sizes": dict(groups), "problems": problems, "ready": not problems,
        "recommendation": (
            "Comprobar licencia, proveniencia y que todas las variantes de una misma foto "
            "compartan group. No entrenar si ready es false."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    report = audit_manifest(args.manifest)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ready"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
