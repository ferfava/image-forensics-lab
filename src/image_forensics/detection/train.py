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


def load_manifest(manifest: Path, patch_size=32, return_ranges=False, progress=False):
    rows = list(csv.DictReader(manifest.open(encoding="utf-8", newline="")))
    if not rows:
        raise ValueError("Manifest vacío.")
    x_all, y_all, groups, ranges = [], [], [], []
    offset = 0
    for i, row in enumerate(rows, 1):
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
        ranges.append((offset, offset + len(labels)))
        offset += len(labels)
        if progress and (i % 5 == 0 or i == len(rows)):
            print(f"[features] {i}/{len(rows)} imágenes · {offset} parches", flush=True)
    result = (np.vstack(x_all), np.concatenate(y_all), np.asarray(groups), rows)
    return (*result, ranges) if return_ranges else result


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
    X, y, groups, rows, ranges = load_manifest(
        manifest, patch_size, return_ranges=True, progress=True
    )
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
        print(f"[training] entrenando {name} ...", flush=True)
        estimator.fit(X[train], y[train])
        predictions = estimator.predict(X[val])
        validation_f1[name] = float(f1_score(y[val], predictions, zero_division=0))
        print(f"[validation] {name}: F1={validation_f1[name]:.4f}", flush=True)
    winner = max(validation_f1, key=validation_f1.get)
    chosen = models[winner]
    print(f"[test] modelo seleccionado: {winner}", flush=True)
    predicted = chosen.predict(X[test])
    tn, fp, fn, tp = confusion_matrix(y[test], predicted, labels=[0, 1]).ravel()
    # Diagnostics use the already held-out test predictions, without tuning.
    split_by_group = {}
    for label, ids in (("train", train), ("validation", val), ("test", test)):
        split_by_group.update({str(group): label for group in np.unique(groups[ids])})
    class_balance = {}
    for label, ids in (("train", train), ("validation", val), ("test", test)):
        pos = int(np.count_nonzero(y[ids]))
        class_balance[label] = {
            "positive_patches": pos, "negative_patches": int(len(ids) - pos),
            "positive_percent": round(pos * 100 / len(ids), 3),
        }
    test_lookup = np.full(len(y), -1, dtype=np.int64)
    test_lookup[test] = np.arange(len(test))
    diagnostics = []
    for row, (start, stop) in zip(rows, ranges):
        if split_by_group[str(row["group"])] != "test":
            continue
        positions = test_lookup[start:stop]
        positions = positions[positions >= 0]
        real, pred = y[test[positions]], predicted[positions]
        local_tn, local_fp, local_fn, local_tp = confusion_matrix(
            real, pred, labels=[0, 1]
        ).ravel()
        diagnostics.append({
            "group": row["group"], "image": row["image"],
            "source": row.get("source", "unknown"),
            "total_patches": int(len(real)), "positive_patches": int(real.sum()),
            "tp": int(local_tp), "fp": int(local_fp),
            "fn": int(local_fn), "tn": int(local_tn),
            "precision": round(float(precision_score(real, pred, zero_division=0)), 4),
            "recall": round(float(recall_score(real, pred, zero_division=0)), 4),
            "f1": round(float(f1_score(real, pred, zero_division=0)), 4),
        })
    report = {
        "status": "EXPERIMENTAL_NO_VALIDADO",
        "source_types": sorted(set(row.get("source", "unknown") for row in rows)),
        "patch_size": patch_size, "seed": seed, "model": winner,
        "features": list(FEATURE_NAMES), "validation_f1": validation_f1,
        "class_balance": class_balance,
        "test_diagnostics": {
            "images": len(diagnostics),
            "images_with_false_positives": sum(item["fp"] > 0 for item in diagnostics),
            "images_with_false_negatives": sum(item["fn"] > 0 for item in diagnostics),
            "worst_false_positive_images": sorted(
                diagnostics, key=lambda item: item["fp"], reverse=True
            )[:5],
            "worst_false_negative_images": sorted(
                diagnostics, key=lambda item: item["fn"], reverse=True
            )[:5],
        },
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
    with (out / "test_by_image.csv").open("w", newline="", encoding="utf-8") as stream:
        fieldnames = [
            "group", "image", "source", "total_patches", "positive_patches",
            "tp", "fp", "fn", "tn", "precision", "recall", "f1"
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(diagnostics)
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
