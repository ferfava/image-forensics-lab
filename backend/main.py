"""API académica: validación y mapa exploratorio de bordes, no detector de falsificaciones."""
import base64
import os
import sys
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import joblib
import numpy as np

import cv2
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from image_forensics.preprocessing.image_io import decode_rgb, MAX_UPLOAD_BYTES  # noqa: E402
from image_forensics.processing.ela import compute_ela_raw  # noqa: E402
from image_forensics.processing.comparison import compare_rgb  # noqa: E402
from image_forensics.evaluation.segmentation import evaluate_mask  # noqa: E402
from image_forensics.detection.infer import infer_image  # noqa: E402
from image_forensics.features.patches import FEATURE_NAMES  # noqa: E402
from image_forensics.features.patches_v2 import FEATURE_NAMES_V2  # noqa: E402

app = FastAPI(title="Image Forensics Lab API", version="0.1.0")
# Configurar CORS_ORIGINS al desplegar (lista separada por comas).
origins = [s.strip() for s in os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,https://image-forensics-lab-frontend.vercel.app").split(",") if s.strip()]
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
async def compare_images(
    reference: UploadFile = File(...),
    candidate: UploadFile = File(...),
    ground_truth: UploadFile | None = File(None),
):
    """Comparación controlada de dos imágenes, sin guardar archivos."""
    reference_bytes = await reference.read(MAX_UPLOAD_BYTES + 1)
    candidate_bytes = await candidate.read(MAX_UPLOAD_BYTES + 1)
    ground_truth_bytes = await ground_truth.read(MAX_UPLOAD_BYTES + 1) if ground_truth else None
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
        gt_mask = None
        metrics = None
        if ground_truth_bytes is not None:
            gt_rgb = decode_rgb(ground_truth_bytes)
            if gt_rgb.shape != ref_rgb.shape:
                raise HTTPException(
                    status_code=400,
                    detail="La máscara de referencia debe tener las mismas dimensiones que las imágenes."
                )
            # Luminosidad >= 128 en la referencia indica región positiva.
            gt_gray = cv2.cvtColor(gt_rgb, cv2.COLOR_RGB2GRAY)
            gt_mask = (gt_gray >= 128).astype("uint8") * 255
            metrics = evaluate_mask(mask, gt_mask)
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
        "ground_truth_png_base64": preview_png(gt_mask) if gt_mask is not None else None,
        "evaluation": metrics,
        "mae": mae,
        "changed_percent": changed,
        "threshold": 20,
        "amplification": 4,
        "disclaimer": "La diferencia entre dos archivos no identifica la causa del cambio. "
                      "La compresión, el color, el registro y la edición influyen.",
    }


# Experimental ML is opt-in. Only operators may configure a trusted local model
# through the server environment. Never deserialize untrusted uploaded joblib files.
ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", "").strip()
ML_MAX_PIXELS = 1_000_000


@lru_cache(maxsize=1)
def _trusted_ml_artifact():
    if not ML_MODEL_PATH:
        raise FileNotFoundError("Modelo experimental no configurado.")
    source = Path(ML_MODEL_PATH).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError("No se encontró el modelo experimental configurado.")
    artifact = joblib.load(source)  # Trusted operator-controlled local file ONLY.
    if not isinstance(artifact, dict) or artifact.get("status") != "EXPERIMENTAL_NO_VALIDADO":
        raise ValueError("El artefacto no tiene un estado experimental válido.")
    if not isinstance(artifact.get("patch_size"), int) or artifact["patch_size"] != 32:
        raise ValueError("Tamaño de parche del modelo incompatible.")
    if tuple(artifact.get("feature_names", ())) not in (FEATURE_NAMES, FEATURE_NAMES_V2):
        raise ValueError("Esquema de características incompatible.")
    if not hasattr(artifact.get("estimator"), "predict"):
        raise ValueError("Clasificador faltante o incompatible.")
    return artifact


@app.get("/api/ml/status")
def ml_status():
    if not ML_MODEL_PATH:
        return {"available": False, "reason": "Modelo de investigación no instalado en el servidor."}
    try:
        artifact = _trusted_ml_artifact()
        return {"available": True, "model": str(artifact.get("feature_version", "v1")).upper(),
                "status": artifact["status"], "patch_size": artifact["patch_size"]}
    except (FileNotFoundError, ValueError, OSError):
        return {"available": False, "reason": "Modelo experimental no disponible."}


@app.post("/api/ml/predict")
def ml_predict(file: UploadFile = File(...)):
    """Research-only single-image patch map; never an authenticity verdict."""
    if not ML_MODEL_PATH:
        raise HTTPException(status_code=503, detail="El modelo experimental aún no está disponible.")
    try:
        artifact = _trusted_ml_artifact()
    except (FileNotFoundError, ValueError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Modelo experimental no disponible.") from exc
    # File reads/decoding are synchronous here so they execute in FastAPI's threadpool.
    # UploadFile.file is a SpooledTemporaryFile already bounded after reading.
    raw = file.file.read(MAX_UPLOAD_BYTES + 1)
    try:
        rgb = decode_rgb(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if rgb.shape[0] * rgb.shape[1] > ML_MAX_PIXELS:
        raise HTTPException(status_code=413, detail="Para ML experimental usá imágenes de hasta 1 megapíxel.")
    if min(rgb.shape[:2]) < artifact["patch_size"]:
        raise HTTPException(status_code=400, detail="La imagen es demasiado pequeña para los parches del modelo.")
    mask = infer_image(rgb, artifact)
    # Preserve native binary patch boundaries; only resize the PREVIEW for transport.
    overlay = rgb.copy()
    hit = mask > 0
    overlay[hit] = np.clip(overlay[hit].astype(np.float32) * 0.55
                           + np.array([255, 73, 83], dtype=np.float32) * 0.45,
                           0, 255).astype(np.uint8)
    def png_base64(arr):
        buffer = BytesIO()
        Image.fromarray(arr).save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")
    return {
        "model": str(artifact.get("feature_version", "v1")).upper(),
        "status": "EXPERIMENTAL_NO_VALIDADO",
        "width": int(rgb.shape[1]), "height": int(rgb.shape[0]),
        "patch_size": artifact["patch_size"],
        "suspect_percent": round(float((mask > 0).mean() * 100), 2),
        "overlay_png_base64": png_base64(overlay),
        "mask_png_base64": png_base64(mask),
        "disclaimer": ("Las marcas señalan parches que el modelo clasifica como sospechosos. "
                       "Contiene falsos positivos y falsos negativos; NO determina si una imagen es auténtica "
                       "ni indica una probabilidad de falsificación."),
    }
