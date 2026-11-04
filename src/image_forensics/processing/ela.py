"""Error Level Analysis exploratorio mediante recompresión JPEG controlada."""
from io import BytesIO

import numpy as np
from PIL import Image


def compute_ela_raw(rgb: np.ndarray, quality: int = 90) -> tuple[np.ndarray, float, float]:
    """Diferencia absoluta RGB uint8 sin amplificar, error medio y factor auto.

    No permite autenticar imágenes. El factor auto es exclusivamente visual.
    """
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
        raise ValueError("Se requiere una imagen RGB uint8.")
    if not 1 <= quality <= 95:
        raise ValueError("La calidad JPEG debe estar entre 1 y 95.")
    buffer = BytesIO()
    Image.fromarray(rgb).save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    with Image.open(buffer) as recompressed:
        reference = np.asarray(recompressed.convert("RGB"), dtype=np.uint8)
    difference = np.abs(rgb.astype(np.int16) - reference.astype(np.int16)).astype(np.uint8)
    peak = int(difference.max())
    auto_scale = 255.0 / peak if peak else 1.0
    return difference, round(float(difference.mean()), 3), round(auto_scale, 3)


def compute_ela(rgb: np.ndarray, quality: int = 90) -> tuple[np.ndarray, float, float]:
    """Mapa ELA amplificado automáticamente, error medio y factor visual."""
    difference, mean, scale = compute_ela_raw(rgb, quality=quality)
    enhanced = np.clip(difference.astype(np.float32) * scale, 0, 255).astype(np.uint8)
    return enhanced, mean, scale
