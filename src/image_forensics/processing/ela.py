"""ELA exploratorio: diferencia respecto de una recompresión JPEG controlada."""
from io import BytesIO

import numpy as np
from PIL import Image


def compute_ela(rgb: np.ndarray, quality: int = 90) -> tuple[np.ndarray, float, float]:
    """Devuelve mapa RGB amplificado, diferencia media y factor de escala.

    ELA no permite certificar autenticidad ni localizar ediciones de forma concluyente.
    """
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
        raise ValueError("Se requiere una imagen RGB uint8.")
    if not 1 <= quality <= 95:
        raise ValueError("La calidad JPEG debe estar entre 1 y 95.")
    buffer = BytesIO()
    Image.fromarray(rgb, mode="RGB").save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    with Image.open(buffer) as recompressed:
        reference = np.asarray(recompressed.convert("RGB"), dtype=np.uint8)
    difference = np.abs(rgb.astype(np.int16) - reference.astype(np.int16))
    peak = int(difference.max())
    scale = 255.0 / peak if peak else 1.0
    enhanced = np.clip(difference.astype(np.float32) * scale, 0, 255).astype(np.uint8)
    return enhanced, round(float(difference.mean()), 3), round(scale, 3)
