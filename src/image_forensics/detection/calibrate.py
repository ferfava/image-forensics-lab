"""Experimental SVM calibration, reproducible group split and held-out error maps.

Run after the original IMD2020 dataset importer and audit. This is exploratory;
the 60-group dataset test images have already been inspected in earlier work,
so the held-out test here is NOT an untouched final benchmark.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from PIL import Image, ImageDraw
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from image_forensics.detection.train import grouped_indices, load_manifest
from image_forensics.features.patches import FEATURE_NAMES, patch_features, patch_map


def locked_group_split(manifest: Path, groups: np.ndarray, split_file: Path, seed=42):
    """Create/reuse group assignments. Fail closed if manifest changes."""
    fingerprint = hashlib.sha256(manifest.read_bytes()).hexdigest()
    unique = sorted(map(str, np.unique(groups)))
    if split_file.exists():
        saved = json.loads(split_file.read_text(encoding="utf-8"))
        if saved["manifest_sha256"] != fingerprint or saved["groups"] != unique:
            raise ValueError("El manifiesto cambió. No reutilizar este split; crear experimento nuevo.")
        lookup = saved["split_by_group"]
    else:
        train, val, test = grouped_indices(groups, seed)
        lookup = {}
        for name, indices in (("train", train), ("validation", val), ("test", test)):
            lookup.update({str(group): name for group in np.unique(groups[indices])})
        split_file.parent.mkdir(parents=True, exist_ok=True)
        split_file.write_text(json.dumps({
            "manifest_sha256": fingerprint, "seed": seed,
            "groups": unique, "split_by_group": lookup
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    parts = {name: np.flatnonzero(np.asarray([
        lookup[str(group)] == name for group in groups
    ])) for name in ("train", "validation", "test")}
    if any(len(v) == 0 for v in parts.values()):
        raise ValueError("Una partición está vacía.")
    if set(parts["train"]).intersection(parts["test"]):
        raise ValueError("Solapamiento entre particiones.")
    return parts


def score(y_true, y_pred):
    tn, fp, fn, tp = (int(n) for n in confusion_matrix(
        y_true, y_pred, labels=[0, 1]
    ).ravel())
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    return {"precision": float(precision), "recall": float(recall),
            "f1": float(f1), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "false_positive_rate": float(fp / (fp + tn)) if fp + tn else 0.0}


def choose_threshold(y_validation, decision_scores):
    """Choose a threshold for F-beta(beta=0.5), on validation ONLY.

    Also consider the native SVM threshold (0) and all-negative threshold.
    Ties prefer fewer FP and then a higher threshold.
    """
    if len(np.unique(y_validation)) != 2:
        raise ValueError("Validación necesita positivos y negativos.")
    candidates = sorted(set(
        [0.0, float(np.nextafter(decision_scores.max(), np.inf))]
        + np.quantile(decision_scores, np.linspace(0, 1, 101)).tolist()
    ))
    best = None
    for threshold in candidates:
        pred = (decision_scores >= threshold).astype(np.uint8)
        metrics = score(y_validation, pred)
        tp, fp, fn = metrics["tp"], metrics["fp"], metrics["fn"]
        beta2 = 0.25
        denominator = (1 + beta2) * tp + beta2 * fn + fp
        f05 = ((1 + beta2) * tp / denominator) if denominator else 0.0
        rank = (f05, -fp, threshold)
        if best is None or rank > best[0]:
            best = (rank, float(threshold), metrics, f05)
    return {"threshold": best[1], "validation_f05": float(best[3]),
            "validation_metrics": best[2], "objective": "F0.5",
            "candidate_thresholds": len(candidates)}


def save_error_panels(manifest, model, selected, out, threshold, max_images=4):
    """Render input, GT, and predicted mask for worst held-out images."""
    out.mkdir(parents=True, exist_ok=True)
    generated = []
    for row in selected[:max_images]:
        with Image.open(manifest.parent / row["image"]) as source:
            rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
        with Image.open(manifest.parent / row["mask"]) as mask_img:
            truth = np.asarray(mask_img.convert("L"), dtype=np.uint8)
        features, boxes, shape = patch_features(rgb)
        pred = model.decision_function(features) >= threshold
        predicted_mask = patch_map(pred, boxes, shape)
        true_mask = (truth >= 128).astype(np.uint8) * 255
        # TP green, FP red, FN blue (computed from the actual GT).
        tp = (predicted_mask > 0) & (true_mask > 0)
        fp = (predicted_mask > 0) & (true_mask == 0)
        fn = (predicted_mask == 0) & (true_mask > 0)
        overlay = rgb.copy()
        color = np.zeros_like(overlay)
        color[tp] = (40, 220, 100)
        color[fp] = (255, 60, 65)
        color[fn] = (50, 120, 255)
        changed = tp | fp | fn
        overlay[changed] = np.clip(
            0.55 * overlay[changed] + 0.45 * color[changed], 0, 255
        ).astype(np.uint8)
        max_width = 480
        size = (max(1, round(rgb.shape[1] * min(1, max_width / rgb.shape[1]))),
                max(1, round(rgb.shape[0] * min(1, max_width / rgb.shape[1]))))
        panels = [Image.fromarray(a).resize(size) for a in (rgb, overlay)]
        canvas = Image.new("RGB", (size[0] * 2, size[1] + 28), (12, 24, 40))
        for index, panel in enumerate(panels):
            canvas.paste(panel, (index * size[0], 28))
        draw = ImageDraw.Draw(canvas)
        draw.text((8, 8), "Imagen", fill=(240, 240, 240))
        draw.text((size[0] + 8, 8), "TP verde / FP rojo / FN azul", fill=(240, 240, 240))
        filename = f"{len(generated) + 1:02d}_{row['group']}.png"
        canvas.save(out / filename)
        generated.append({"file": str(out / filename), "image": row["image"],
                          "group": row["group"]})
    return generated


def evaluate_calibrated(manifest: Path, out: Path, seed=42, map_count=4):
    out.mkdir(parents=True, exist_ok=True)
    print("[features] Extrayendo características...", flush=True)
    X, y, groups, rows, ranges = load_manifest(
        manifest, 32, return_ranges=True, progress=True
    )
    splits = locked_group_split(manifest, groups, out / "split.json", seed)
    train, val, test = (splits[key] for key in ("train", "validation", "test"))
    if len(np.unique(y[train])) != 2 or len(np.unique(y[val])) != 2:
        raise ValueError("Train y validación necesitan ambas clases.")
    estimator = make_pipeline(
        StandardScaler(),
        SVC(kernel="rbf", class_weight="balanced", C=1, gamma="scale")
    )
    print("[training] SVM con características existentes...", flush=True)
    estimator.fit(X[train], y[train])
    print("[validation] Buscando umbral con F0.5...", flush=True)
    tuning = choose_threshold(y[val], estimator.decision_function(X[val]))
    threshold = tuning["threshold"]
    print(f"[validation] Umbral: {threshold:.5f}", flush=True)

    # Test is accessed exactly here, after model and threshold are fixed.
    test_scores = estimator.decision_function(X[test])
    prediction = (test_scores >= threshold).astype(np.uint8)
    native_prediction = (test_scores >= 0).astype(np.uint8)
    group_partitions = {str(g): name for name, ids in splits.items()
                        for g in np.unique(groups[ids])}
    test_positions = np.full(len(y), -1, dtype=np.int64)
    test_positions[test] = np.arange(len(test))
    image_rows = []
    for row, (start, stop) in zip(rows, ranges):
        if group_partitions[str(row["group"])] != "test":
            continue
        pos = test_positions[start:stop]
        local_y = y[test[pos]]
        local_p = prediction[pos]
        item = {"group": row["group"], "image": row["image"], "mask": row["mask"],
                "patches": int(len(local_y)), "positive_patches": int(local_y.sum())}
        item.update(score(local_y, local_p))
        image_rows.append(item)
    fieldnames = list(image_rows[0].keys())
    with (out / "test_by_image_calibrated.csv").open("w", encoding="utf-8",
                                                    newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(image_rows)
    offenders = sorted(image_rows, key=lambda item: item["fp"], reverse=True)
    maps = save_error_panels(manifest, estimator, offenders,
                             out / "error_maps", threshold, map_count) if map_count else []
    report = {
        "status": "EXPERIMENTAL_NO_VALIDADO",
        "warning": ("Prueba exploratoria: el conjunto de 60 grupos ya fue inspeccionado "
                    "en trabajo previo; no es un benchmark final independiente."),
        "groups": {k: len(set(groups[v])) for k, v in splits.items()},
        "patches": {k: {"total": int(len(v)), "positive": int(y[v].sum())}
                    for k, v in splits.items()},
        "calibration": tuning,
        "test_baseline_all_normal": score(y[test], np.zeros_like(y[test])),
        "test_svm_default": score(y[test], native_prediction),
        "test_svm_calibrated": score(y[test], prediction),
        "maps": maps,
    }
    (out / "calibration_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    joblib.dump({
        "estimator": estimator, "threshold": threshold,
        "patch_size": 32, "feature_names": FEATURE_NAMES,
        "status": "EXPERIMENTAL_NO_VALIDADO"
    }, out / "calibrated_model.joblib")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("models/imd2020_60_calibrated"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--map-count", type=int, default=4)
    args = parser.parse_args()
    result = evaluate_calibrated(args.manifest, args.out, args.seed, args.map_count)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
