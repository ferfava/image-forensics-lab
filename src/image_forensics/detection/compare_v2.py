"""Exploratory V1 vs V2 SVM comparison using exactly the SAME locked source split.

Both thresholds selected on validation only (F0.5). Test was previously
inspected; report is exploratory and NOT an independent final benchmark.
"""
import argparse
import csv
import json
from pathlib import Path

import joblib
import numpy as np
from PIL import Image
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from image_forensics.detection.calibrate import locked_group_split, choose_threshold, score
from image_forensics.features.patches import FEATURE_NAMES, labels_from_mask, patch_features
from image_forensics.features.patches_v2 import FEATURE_NAMES_V2, patch_features_v2


def prepare_features(manifest: Path, progress=True):
    with manifest.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("Manifiesto vacío.")
    v1_parts, v2_parts, label_parts, groups = [], [], [], []
    for i, row in enumerate(rows, 1):
        if not all(row.get(k) for k in ("image", "mask", "group")):
            raise ValueError(f"Fila {i}: faltan image, mask o group.")
        with Image.open(manifest.parent / row["image"]) as source:
            rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
        with Image.open(manifest.parent / row["mask"]) as source:
            mask = np.asarray(source.convert("L"), dtype=np.uint8)
        if rgb.shape[:2] != mask.shape:
            raise ValueError(f"Imagen y máscara desalineadas: {row['image']}")
        # V2 internally calls V1, ensuring both use the same schema and patches.
        v2, boxes, _ = patch_features_v2(rgb)
        labels = labels_from_mask(mask, boxes)
        v1_parts.append(v2[:, :len(FEATURE_NAMES)])
        v2_parts.append(v2)
        label_parts.append(labels)
        groups.extend([row["group"]] * len(labels))
        if progress and (i % 5 == 0 or i == len(rows)):
            print(f"[features] {i}/{len(rows)} imágenes", flush=True)
    return (np.vstack(v1_parts), np.vstack(v2_parts),
            np.concatenate(label_parts), np.asarray(groups))


def compare_v1_v2(manifest: Path, split_file: Path, out: Path):
    if not split_file.is_file():
        raise FileNotFoundError(
            "No se encontró el split bloqueado del experimento anterior. "
            "No se creará otro: indicar models/imd2020_60_calibrated/split.json."
        )
    X1, X2, labels, groups = prepare_features(manifest)
    partitions = locked_group_split(manifest, groups, split_file)
    train, validation, test = (partitions[k] for k in ("train", "validation", "test"))
    if len(np.unique(labels[train])) < 2 or len(np.unique(labels[validation])) < 2:
        raise ValueError("Faltan positivos o negativos en entrenamiento/validación.")
    results, artifacts = {}, {}
    for name, features, names in (
        ("v1", X1, FEATURE_NAMES), ("v2", X2, FEATURE_NAMES_V2)
    ):
        print(f"[training] Entrenando SVM {name.upper()}...", flush=True)
        model = make_pipeline(
            StandardScaler(),
            SVC(kernel="rbf", class_weight="balanced", C=1, gamma="scale"),
        )
        model.fit(features[train], labels[train])
        threshold_info = choose_threshold(
            labels[validation], model.decision_function(features[validation])
        )
        # Same test images, same patch labels and same indexes for BOTH models.
        test_scores = model.decision_function(features[test])
        pred = (test_scores >= threshold_info["threshold"]).astype(np.uint8)
        results[name] = {
            "n_features": len(names),
            "threshold": threshold_info["threshold"],
            "validation_f05": threshold_info["validation_f05"],
            "validation": threshold_info["validation_metrics"],
            "test": score(labels[test], pred),
        }
        artifacts[name] = {
            "estimator": model, "threshold": threshold_info["threshold"],
            "patch_size": 32, "feature_names": names, "feature_version": name,
            "status": "EXPERIMENTAL_NO_VALIDADO",
        }
        print(f"[test] {name.upper()} precisión={results[name]['test']['precision']:.3f} "
              f"recall={results[name]['test']['recall']:.3f} "
              f"FP={results[name]['test']['fp']}", flush=True)
    report = {
        "status": "EXPERIMENTAL_NO_VALIDADO",
        "warning": ("Este test ya fue inspeccionado en ensayos anteriores. "
                    "La comparación V1-V2 es exploratoria; no usar para seleccionar "
                    "un modelo definitivo ni para afirmar generalización."),
        "same_split": True, "split_file": str(split_file),
        "group_counts": {key: len(set(groups[idx])) for key, idx in partitions.items()},
        "test_patches": int(len(test)),
        "test_positive": int(labels[test].sum()),
        "models": results,
        "delta_v2_minus_v1": {
            key: float(results["v2"]["test"][key] - results["v1"]["test"][key])
            for key in ("precision", "recall", "f1", "false_positive_rate")
        },
        "false_positive_difference": int(
            results["v2"]["test"]["fp"] - results["v1"]["test"]["fp"]
        ),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparison_v1_v2.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    for name, artifact in artifacts.items():
        joblib.dump(artifact, out / f"{name}_model.joblib")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("models/imd2020_v1_v2"))
    args = parser.parse_args()
    print(json.dumps(compare_v1_v2(args.manifest, args.split, args.out),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
