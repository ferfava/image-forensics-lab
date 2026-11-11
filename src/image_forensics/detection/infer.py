"""Local single-image experimental inference from a trusted model artifact."""
import argparse
from pathlib import Path

import joblib
import numpy as np
from PIL import Image

from image_forensics.features.patches import FEATURE_NAMES, patch_features, patch_map
from image_forensics.features.patches_v2 import FEATURE_NAMES_V2, patch_features_v2


def infer_image(rgb: np.ndarray, artifact: dict):
    schema = tuple(artifact["feature_names"])
    if schema == FEATURE_NAMES:
        extraction = patch_features
    elif schema == FEATURE_NAMES_V2:
        extraction = patch_features_v2
    else:
        raise ValueError("Esquema de características incompatible.")
    features, boxes, shape = extraction(rgb, artifact["patch_size"])
    estimator = artifact["estimator"]
    if "threshold" in artifact:
        if not hasattr(estimator, "decision_function"):
            raise ValueError("El modelo calibrado debe ofrecer decision_function.")
        labels = estimator.decision_function(features) >= float(artifact["threshold"])
    else:
        labels = estimator.predict(features)
    return patch_map(labels, boxes, shape)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("models/experimental/model.joblib"))
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("outputs/ml_suspect_mask.png"))
    args = parser.parse_args()
    # joblib/pickle must never load from an unknown or untrusted source.
    artifact = joblib.load(args.model)
    with Image.open(args.image) as source:
        rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    mask = infer_image(rgb, artifact)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(mask).save(args.out)
    print(f"Máscara experimental guardada: {args.out}. No certifica autenticidad.")


if __name__ == "__main__":
    main()
