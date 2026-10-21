"""Lectura de imágenes en memoria con validación de tamaño y formato."""

from io import BytesIO

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_PIXELS = 16_000_000
MAX_UPLOAD_BYTES = 12 * 1024 * 1024


def decode_rgb(data: bytes) -> np.ndarray:
    """Decodifica JPEG/PNG como RGB, rechazando entradas demasiado grandes."""
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("El archivo está vacío o supera el límite de 12 MB.")
    try:
        with Image.open(BytesIO(data)) as source:
            width, height = source.size
            if width * height > MAX_IMAGE_PIXELS:
                raise ValueError("La imagen supera el límite de 16 megapíxeles.")
            if source.format not in {"JPEG", "PNG"}:
                raise ValueError("Solo se admiten fotografías JPEG o PNG.")
            return np.asarray(ImageOps.exif_transpose(source).convert("RGB")).copy()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("No se pudo interpretar la imagen.") from exc
