"""Métricas de segmentación de una máscara binaria frente a verdad terreno."""
import numpy as np


def evaluate_mask(predicted: np.ndarray, truth: np.ndarray) -> dict:
    """Evalúa máscaras binarias 2D usando valor positivo >0.

    Caso sin positivos en ambas máscaras: puntuaciones 1.0 por coincidencia
    perfecta, con flag empty_case para evitar interpretaciones erróneas.
    """
    if (predicted.ndim != 2 or truth.ndim != 2 or
            predicted.shape != truth.shape or predicted.size == 0):
        raise ValueError("Las máscaras deben tener iguales dimensiones y ser 2D.")
    pred = predicted > 0
    real = truth > 0
    tp = int(np.count_nonzero(pred & real))
    fp = int(np.count_nonzero(pred & ~real))
    fn = int(np.count_nonzero(~pred & real))
    tn = int(pred.size - tp - fp - fn)
    empty_case = tp + fp + fn == 0
    precision = tp / (tp + fp) if tp + fp else (1.0 if empty_case else 0.0)
    recall = tp / (tp + fn) if tp + fn else (1.0 if empty_case else 0.0)
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 1.0
    iou = tp / (tp + fp + fn) if tp + fp + fn else 1.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "iou": round(iou, 4),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "empty_case": empty_case,
    }
