"""Portable, data-only binary RBF-SVM parameters (no pickle at runtime)."""
from pathlib import Path

import numpy as np

from image_forensics.features.patches import FEATURE_NAMES

STATUS = "EXPERIMENTAL_NO_VALIDADO"
MAX_SUPPORT_VECTORS = 250_000


class PortableRbfSvm:
    """Implement sklearn's binary RBF SVC decision_function via numerical arrays."""

    def __init__(self, mean, scale, sv, dual, intercept, gamma):
        self.mean = np.asarray(mean, dtype=np.float64)
        self.scale = np.asarray(scale, dtype=np.float64)
        self.sv = np.asarray(sv, dtype=np.float64)
        self.dual = np.asarray(dual, dtype=np.float64)
        self.intercept = float(intercept)
        self.gamma = float(gamma)
        if (self.mean.shape != (len(FEATURE_NAMES),)
                or self.scale.shape != self.mean.shape
                or self.sv.ndim != 2 or self.sv.shape[1] != len(FEATURE_NAMES)
                or len(self.sv) < 1 or len(self.sv) > MAX_SUPPORT_VECTORS
                or self.dual.shape != (len(self.sv),)
                or np.any(self.scale <= 0) or self.gamma <= 0):
            raise ValueError("Parámetros del modelo SVM incompatibles.")
        if not all(np.isfinite(a).all() for a in
                   (self.mean, self.scale, self.sv, self.dual)):
            raise ValueError("Parámetros SVM no finitos.")
        if not np.isfinite(self.intercept) or not np.isfinite(self.gamma):
            raise ValueError("Intercepto/gamma inválido.")
        self.sv_norm = np.einsum("ij,ij->i", self.sv, self.sv)
        self.max_batch = 64

    def decision_function(self, features):
        X = np.asarray(features, dtype=np.float64)
        if X.ndim != 2 or X.shape[1] != len(FEATURE_NAMES):
            raise ValueError("Características incompatibles.")
        X = (X - self.mean) / self.scale
        result = np.empty(len(X), dtype=np.float64)
        # Bound temporary RAM on low-cost cloud instances.
        for i in range(0, len(X), self.max_batch):
            x = X[i:i + self.max_batch]
            d2 = (np.einsum("ij,ij->i", x, x)[:, None]
                  + self.sv_norm[None, :] - 2.0 * (x @ self.sv.T))
            np.maximum(d2, 0, out=d2)
            result[i:i + len(x)] = (np.exp(-self.gamma * d2) @ self.dual
                                    + self.intercept)
        return result


def load_portable_artifact(path: str | Path) -> dict:
    """Load a trusted model exported as NPZ; never allow object arrays."""
    with np.load(path, allow_pickle=False) as stored:
        required = {"mean", "scale", "support_vectors", "dual_coef", "intercept",
                    "gamma", "threshold", "feature_names", "patch_size"}
        if set(stored.files) != required:
            raise ValueError("El archivo NPZ no contiene el esquema esperado.")
        names = tuple(str(x) for x in stored["feature_names"])
        size = int(stored["patch_size"].item())
        threshold = float(stored["threshold"].item())
        if names != FEATURE_NAMES or size != 32 or not np.isfinite(threshold):
            raise ValueError("Esquema/umbral del SVM exportado incompatible.")
        model = PortableRbfSvm(
            stored["mean"], stored["scale"], stored["support_vectors"],
            stored["dual_coef"], stored["intercept"].item(),
            stored["gamma"].item(),
        )
    return {
        "estimator": model, "threshold": threshold, "patch_size": size,
        "feature_names": FEATURE_NAMES, "feature_version": "v1", "status": STATUS,
    }
