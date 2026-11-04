"""Train and evaluate grouped patch classifiers from a manifest of image/mask pairs."""
import argparse
import csv
import json
from pathlib import Path

import joblib
import numpy as np
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, jaccard_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from image_forensics.features.patches import FEATURE_NAMES, patch_features, labels_from_mask


def load_manifest(manifest: Path, patch_size=32):
    rows = list(csv.DictReader(manifest.open(encoding="utf-8", newline="")))
    if not rows:
        raise ValueError("Manifest vacío.")
    x_all, y_all, groups = [], [], []
    for row in rows:
        if not all(row.get(key) for key in ("image", "mask", "group")):
            raise ValueError("El CSV requiere image, mask y group.")
        image_path = (manifest.parent / row["image"]).resolve()
        mask_path = (manifest.parent / row["mask"]).resolve()
        with Image.open(image_path) as inp, Image.open(mask_path) as annotated:
            rgb = np.asarray(inp.convert("RGB"), dtype=np.uint8)
            mask = np.asarray(annotated.convert("L"), dtype=np.uint8)
        if rgb.shape[:2] != mask.shape:
            raise ValueError(f"Máscara desalineada: {image_path.name}")
        feats, boxes, _ = patch_features(rgb, patch_size)
        labels = labels_from_mask(mask, boxes)
        x_all.append(feats)
        y_all.append(labels)
        groups.extend([row["group"]] * len(labels))
    return np.vstack(x_all), np.concatenate(y_all), np.asarray(groups), rows


def grouped_indices(groups, seed):
    """Disjoint source-image groups in train/validation/test, 60/20/20 approximate."""
    indices = np.arange(len(groups))
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
    train_val, test = next(splitter.split(indices, groups=groups))
    splitter2 = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed + 1)
    sub_train, sub_val = next(splitter2.split(train_val, groups=groups[train_val]))
    train, val = train_val[sub_train], train_val[sub_val]
    for a, b in [(train, val), (train, test), (val, test)]:
        assert set(groups[a]).isdisjoint(set(groups[b])), "Fuga de grupo"
    return train, val, test


def train_and_evaluate(manifest: Path, out: Path, patch_size=32, seed=42):
    X, y, groups, rows = load_manifest(manifest, patch_size)
    train, val, test = grouped_indices(groups, seed)
    if len(np.unique(y[train])) != 2:
        raise ValueError("El entrenamiento necesita parches positivos y negativos.")
    models = {
        "random_forest": RandomForestClassifier(
            n_estimators=160, min_samples_leaf=2,
            class_weight="balanced_subsample", random_state=seed, n_jobs=-1
        ),
        "svm": make_pipeline(
            StandardScaler(), SVC(kernel="rbf", class_weight="balanced", C=1, gamma="scale")
        ),
    }
    # Fixed model hyperparameters. Validation used only to choose model, NOT test scores.
    validation_f1 = {}
    for name, estimator in models.items():
        estimator.fit(X[train], y[train])
        predictions = estimator.predict(X[val])
        validation_f1[name] = float(f1_score(y[val], predictions, zero_division=0))
    winner = max(validation_f1, key=validation_f1.get)
    chosen = models[winner]
    predicted = chosen.predict(X[test])
    tn, fp, fn, tp = confusion_matrix(y[test], predicted, labels=[0, 1]).ravel()
    report = {
        "status": "EXPERIMENTAL_NO_VALIDADO",
        "source_types": sorted(set(row.get("source", "unknown") for row in rows)),
        "patch_size": patch_size, "seed": seed, "model": winner,
        "features": list(FEATURE_NAMES), "validation_f1": validation_f1,
        "group_counts": {name: int(len(set(groups[idx]))) for name, idx in
                         (("train", train), ("validation", val), ("test", test))},
        "test": {
            "precision": float(precision_score(y[test], predicted, zero_division=0)),
            "recall": float(recall_score(y[test], predicted, zero_division=0)),
            "f1": float(f1_score(y[test], predicted, zero_division=0)),
            "iou_patch": float(jaccard_score(y[test], predicted, zero_division=0)),
            "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
        },
        "warning": "Métricas por parche; no equivalen a IoU por píxel ni demuestran "
                   "generalización a imágenes reales. Solo cargar modelos de origen confiable.",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                     encoding="utf-8")
    joblib.dump({"estimator": chosen, "patch_size": patch_size,
                 "feature_names": FEATURE_NAMES, "status": report["status"]},
                out / "model.joblib")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("models/experimental"))
    parser.add_argument("--patch-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    report = train_and_evaluate(args.manifest, args.out, args.patch_size, args.seed)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
