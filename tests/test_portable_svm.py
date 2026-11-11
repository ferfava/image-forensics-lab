"""Portable RBF SVM must reproduce sklearn's numeric decisions exactly."""
import joblib
import numpy as np
import pytest
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from image_forensics.features.patches import FEATURE_NAMES
from image_forensics.detection.export_portable_v1 import export_v1
from image_forensics.detection.portable_svm import load_portable_artifact

def test_export_preserves_svm_scores(tmp_path):
    rng = np.random.default_rng(5)
    X = rng.normal(size=(50, 8))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    model = make_pipeline(StandardScaler(), SVC(kernel="rbf", gamma="scale", C=1))
    model.fit(X, y)
    original = tmp_path / "trusted.joblib"
    joblib.dump({
        "estimator": model, "threshold": 0.34, "patch_size": 32,
        "feature_names": FEATURE_NAMES, "feature_version": "v1",
        "status": "EXPERIMENTAL_NO_VALIDADO",
    }, original)
    target = tmp_path / "safe.npz"
    export_v1(original, target)
    artifact = load_portable_artifact(target)
    assert artifact["status"] == "EXPERIMENTAL_NO_VALIDADO"
    assert artifact["threshold"] == 0.34
    assert np.allclose(model.decision_function(X),
                       artifact["estimator"].decision_function(X),
                       rtol=1e-5, atol=1e-5)


def test_rejects_unexpected_npz_schema(tmp_path):
    path = tmp_path / "bad.npz"
    np.savez(path, only_array=np.zeros(8))
    with pytest.raises(ValueError, match="esquema"):
        load_portable_artifact(path)
