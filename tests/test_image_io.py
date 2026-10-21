"""Pruebas de regresión para carga segura de imágenes."""

from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from image_forensics.preprocessing.image_io import decode_rgb


def test_decodes_png_to_rgb():
    image = Image.new("RGB", (8, 6), (10, 20, 30))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    result = decode_rgb(buffer.getvalue())
    assert result.shape == (6, 8, 3)
    assert result.dtype == np.uint8
    assert result[0, 0].tolist() == [10, 20, 30]


@pytest.mark.parametrize("payload", [b"", b"not an image"])
def test_rejects_invalid_upload(payload):
    with pytest.raises(ValueError):
        decode_rgb(payload)
