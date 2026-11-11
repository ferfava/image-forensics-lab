"""Optional ML route: never claim that a missing artifact is deployed."""
from io import BytesIO

import joblib
import numpy as np
import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image
from sklearn.dummy import DummyClassifier

import backend.main as api
from image_forensics.features.patches import FEATURE_NAMES


def _png(side=64):
    image = Image.fromarray(np.full((side, side, 3), 140, dtype=np.uint8))
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def test_ml_disabled_by_default(monkeypatch):
    monkeypatch.setattr(api, "ML_MODEL_PATH", "")
    api._trusted_ml_artifact.cache_clear()
    assert api.ml_status()["available"] is False
    with pytest.raises(HTTPException) as error:
        api.ml_predict(UploadFile(filename="sample.png", file=BytesIO(_png())))
    assert error.value.status_code == 503


def test_ml_configured_model_is_local_and_experimental(monkeypatch, tmp_path):
    model = DummyClassifier(strategy="constant", constant=0)
    model.fit(np.zeros((2, 8)), np.array([0, 1]))
    file = tmp_path / "trusted-model.joblib"
    joblib.dump({
        "estimator": model, "patch_size": 32,
        "feature_names": FEATURE_NAMES,
        "status": "EXPERIMENTAL_NO_VALIDADO",
    }, file)
    monkeypatch.setattr(api, "ML_MODEL_PATH", str(file))
    api._trusted_ml_artifact.cache_clear()
    assert api.ml_status()["available"] is True
    result = api.ml_predict(UploadFile(filename="sample.png", file=BytesIO(_png())))
    assert result["status"] == "EXPERIMENTAL_NO_VALIDADO"
    assert result["suspect_percent"] == 0
    assert result["patch_size"] == 32
    assert result["mask_png_base64"]
    assert "NO determina" in result["disclaimer"]


def test_ml_enforces_small_image_and_rejects_unknown_artifact(monkeypatch, tmp_path):
    file = tmp_path / "untrusted-schema.joblib"
    joblib.dump({"patch_size": 32, "status": "VALIDATED"}, file)
    monkeypatch.setattr(api, "ML_MODEL_PATH", str(file))
    api._trusted_ml_artifact.cache_clear()
    assert api.ml_status()["available"] is False
    with pytest.raises(HTTPException) as error:
        api.ml_predict(UploadFile(filename="sample.png", file=BytesIO(_png())))
    assert error.value.status_code == 503
