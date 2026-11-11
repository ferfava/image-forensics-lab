"""Comparación por píxel entre fotografías ya alineadas y de igual tamaño.

Las diferencias no identifican la causa del cambio ni certifican manipulación.
"""
import numpy as np


def compare_rgb(reference: np.ndarray, candidate: np.ndarray, threshold: int = 20):
    """Retorna mapa RGB absoluto, máscara binaria, MAE y porcentaje por encima de umbral.

    El umbral se aplica al máximo de los tres canales de cada píxel. Los cálculos
    se hacen sobre imágenes originales a resolución completa y SIN amplificación.
    """
    if (reference.ndim != 3 or reference.shape[-1] != 3 or
            reference.dtype != np.uint8 or candidate.dtype != np.uint8 or
            candidate.shape != reference.shape):
        raise ValueError("Las imágenes deben ser RGB uint8 y tener iguales dimensiones.")
    if not 0 <= threshold <= 255:
        raise ValueError("El umbral debe estar entre 0 y 255.")
    difference = np.abs(reference.astype(np.int16) - candidate.astype(np.int16)).astype(np.uint8)
    mask = (difference.max(axis=2) > threshold).astype(np.uint8) * 255
    mae = round(float(difference.mean()), 3)
    changed_percent = round(float(np.count_nonzero(mask) / mask.size * 100), 2)
    return difference, mask, mae, changed_percent
