"""Export OUR trusted, locally trained V1 joblib into a data-only NPZ.

Run on the training machine, NEVER on arbitrary downloaded pickle files.
Usage: python -m image_forensics.detection.export_portable_v1 \
    --model models/imd2020_v1_v2/v1_model.joblib \
    --out backend/assets/svm_v1.npz
"""
import argparse
from pathlib import Path

import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from image_forensics.features.patches import FEATURE_NAMES
from image_forensics.detection.portable_svm import load_portable_artifact

def export_v1(model_file: Path, output: Path):
    artifact = joblib.load(model_file)  # ONLY local artifact trained by this project.
    if (not isinstance(artifact, dict)
            or artifact.get("status") != "EXPERIMENTAL_NO_VALIDADO"
            or tuple(artifact.get("feature_names", ())) != FEATURE_NAMES
            or artifact.get("patch_size") != 32
            or not isinstance(artifact.get("estimator"), Pipeline)):
        raise ValueError("No es el artefacto SVM V1 esperado.")
    model = artifact["estimator"]
    if len(model.steps) != 2:
        raise ValueError("El pipeline tiene pasos inesperados.")
    scaler, svc = model.steps[0][1], model.steps[1][1]
    if (not isinstance(scaler, StandardScaler) or not isinstance(svc, SVC)
            or svc.kernel != "rbf" or len(svc.classes_) != 2
            or not np.array_equal(svc.classes_, [0, 1])):
        raise ValueError("El pipeline no es StandardScaler + SVC binario RBF.")
    threshold = float(artifact["threshold"])
    if not np.isfinite(threshold):
        raise ValueError("Umbral inválido.")
    payload = {
        "mean": np.asarray(scaler.mean_, dtype=np.float64),
        "scale": np.asarray(scaler.scale_, dtype=np.float64),
        "support_vectors": np.asarray(svc.support_vectors_, dtype=np.float64),
        "dual_coef": np.asarray(svc.dual_coef_.reshape(-1), dtype=np.float64),
        "intercept": np.asarray(svc.intercept_[0], dtype=np.float64),
        "gamma": np.asarray(svc._gamma, dtype=np.float64),
        "threshold": np.asarray(threshold, dtype=np.float64),
        "feature_names": np.asarray(FEATURE_NAMES, dtype="U64"),
        "patch_size": np.asarray(32, dtype=np.int32),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, **payload)
    portable = load_portable_artifact(output)
    rng = np.random.default_rng(2026)
    # Compare scores on arbitrary feature vectors; not an accuracy test.
    reference = rng.normal(loc=70, scale=40, size=(20, len(FEATURE_NAMES)))
    expected = model.decision_function(reference)
    actual = portable["estimator"].decision_function(reference)
    max_diff = float(np.max(np.abs(expected - actual)))
    if not np.allclose(expected, actual, rtol=1e-5, atol=1e-5):
        output.unlink(missing_ok=True)
        raise ValueError(f"Exportación inconsistente, diferencia: {max_diff}")
    print(f"Exportación verificada: {output} ({output.stat().st_size:,} bytes)")
    print(f"Máxima diferencia numérica SVC/NPZ: {max_diff:.8g}")
    print("Estado: EXPERIMENTAL_NO_VALIDADO. No es una prueba de precisión.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("backend/assets/svm_v1.npz"))
    args = parser.parse_args()
    export_v1(args.model, args.out)

if __name__ == "__main__":
    main()
