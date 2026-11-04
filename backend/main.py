"""API académica: validación y mapa exploratorio de bordes, no detector de falsificaciones."""
import base64
import sys
from io import BytesIO
from pathlib import Path

import cv2
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from image_forensics.preprocessing.image_io import decode_rgb, MAX_UPLOAD_BYTES  # noqa: E402
from image_forensics.processing.ela import compute_ela_raw  # noqa: E402
from image_forensics.processing.comparison import compare_rgb  # noqa: E402

app = FastAPI(title="Image Forensics Lab API", version="0.1.0")
# Configurar CORS_ORIGINS al desplegar (lista separada por comas).
import os
origins = [s.strip() for s in os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",") if s.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    # Un archivo por solicitud, sin persistir fotografías.
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    try:
        rgb = decode_rgb(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    # Histogramas calculados con OpenCV: frecuencia de intensidades de 0 a 255.
    histograms = {
        "red": cv2.calcHist([rgb], [0], None, [256], [0, 256]).reshape(-1).astype(int).tolist(),
        "green": cv2.calcHist([rgb], [1], None, [256], [0, 256]).reshape(-1).astype(int).tolist(),
        "blue": cv2.calcHist([rgb], [2], None, [256], [0, 256]).reshape(-1).astype(int).tolist(),
        "gray": cv2.calcHist([gray], [0], None, [256], [0, 256]).reshape(-1).astype(int).tolist(),
    }
    # Filtrado clásico; mapas orientativos, no detectores de falsificación.
    gaussian = cv2.GaussianBlur(rgb, (5, 5), 0)
    median = cv2.medianBlur(rgb, 5)
    residual = cv2.absdiff(rgb, gaussian)
    # La visualización del residuo se amplifica para que pueda inspeccionarse.
    residual_view = cv2.convertScaleAbs(residual, alpha=4.0)
    ela_raw, ela_mean, ela_scale = compute_ela_raw(rgb, quality=90)

    def preview_png(array):
        height, width = array.shape[:2]
        if max(height, width) > 1000:
            scale = 1000 / max(height, width)
            array = cv2.resize(array, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)
        stream = BytesIO()
        Image.fromarray(array).save(stream, format="PNG")
        return base64.b64encode(stream.getvalue()).decode("ascii")

    output = BytesIO()
    Image.fromarray(edges).save(output, format="PNG")
    return {
        "width": int(rgb.shape[1]),
        "height": int(rgb.shape[0]),
        "method": "Canny (umbrales 100 y 200)",
        "histograms": histograms,
        "filters": {"gaussian_png_base64": preview_png(gaussian), "median_png_base64": preview_png(median), "residual_png_base64": preview_png(residual_view), "residual_mean": round(float(residual.mean()), 3)},
        "ela": {"raw_map_png_base64": preview_png(ela_raw), "quality": 90, "mean_absolute_error": ela_mean, "suggested_scale": ela_scale},
        "edge_map_png_base64": base64.b64encode(output.getvalue()).decode("ascii"),
        "disclaimer": "Los bordes no demuestran una manipulación de la imagen.",
    }


@app.post("/api/compare")
async def compare_images(reference: UploadFile = File(...), candidate: UploadFile = File(...)):
    """Comparación controlada de dos imágenes, sin guardar archivos."""
    reference_bytes = await reference.read(MAX_UPLOAD_BYTES + 1)
    candidate_bytes = await candidate.read(MAX_UPLOAD_BYTES + 1)
    try:
        ref_rgb = decode_rgb(reference_bytes)
        candidate_rgb = decode_rgb(candidate_bytes)
        if ref_rgb.shape != candidate_rgb.shape:
            raise HTTPException(
                status_code=400,
                detail="Las dos imágenes deben tener exactamente las mismas dimensiones. "
                       "No se realiza redimensionamiento ni alineación automática.",
            )
        diff, mask, mae, changed = compare_rgb(ref_rgb, candidate_rgb, threshold=20)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    def preview_png(array):
        height, width = array.shape[:2]
        if max(height, width) > 900:
            factor = 900 / max(height, width)
            array = cv2.resize(
                array, (round(width * factor), round(height * factor)),
                interpolation=cv2.INTER_AREA if array.ndim == 3 else cv2.INTER_NEAREST
            )
        stream = BytesIO()
        Image.fromarray(array).save(stream, format="PNG")
        return base64.b64encode(stream.getvalue()).decode("ascii")

    return {
        "width": int(ref_rgb.shape[1]),
        "height": int(ref_rgb.shape[0]),
        "reference_png_base64": preview_png(ref_rgb),
        "candidate_png_base64": preview_png(candidate_rgb),
        "difference_png_base64": preview_png(
            cv2.convertScaleAbs(diff, alpha=4.0)
        ),
        "mask_png_base64": preview_png(mask),
        "mae": mae,
        "changed_percent": changed,
        "threshold": 20,
        "amplification": 4,
        "disclaimer": "La diferencia entre dos archivos no identifica la causa del cambio. "
                      "La compresión, el color, el registro y la edición influyen.",
    }
