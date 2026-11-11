"""Features per non-overlapping patch for exploratory tamper classification.

All features are computed from one image; no pristine reference is used.
"""
import cv2
import numpy as np

FEATURE_NAMES = (
    "gray_mean", "gray_std", "laplacian_var", "edge_density",
    "gradient_mean", "rgb_std_mean", "jpeg_residual_mean",
    "jpeg_residual_std",
)


def patch_features(rgb: np.ndarray, patch_size: int = 32):
    """Return features (n,8), patch boxes (x1,y1,x2,y2), and image dimensions."""
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
        raise ValueError("Se requiere una imagen RGB uint8.")
    if patch_size < 16 or rgb.shape[0] < patch_size or rgb.shape[1] < patch_size:
        raise ValueError("Imagen demasiado pequeña o parche inválido.")
    h, w = rgb.shape[:2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    # Global JPEG recompression residual is a feature, not proof of forgery.
    success, buffer = cv2.imencode(".jpg", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR),
                                  [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not success:
        raise ValueError("No se pudo recomprimir la imagen.")
    recovered = cv2.cvtColor(cv2.imdecode(buffer, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    residual = cv2.absdiff(rgb, recovered).mean(axis=2)
    features, boxes = [], []
    for y in range(0, h - patch_size + 1, patch_size):
        for x in range(0, w - patch_size + 1, patch_size):
            ys, xs = slice(y, y + patch_size), slice(x, x + patch_size)
            g = gray[ys, xs]
            patch = rgb[ys, xs]
            lap = cv2.Laplacian(g, cv2.CV_32F)
            gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
            r = residual[ys, xs]
            features.append([
                float(g.mean()), float(g.std()), float(lap.var()),
                float((cv2.Canny(g, 80, 160) > 0).mean()),
                float(cv2.magnitude(gx, gy).mean()),
                float(patch.reshape(-1, 3).std(axis=0).mean()),
                float(r.mean()), float(r.std()),
            ])
            boxes.append((x, y, x + patch_size, y + patch_size))
    return np.asarray(features, dtype=np.float32), boxes, (h, w)


def labels_from_mask(mask: np.ndarray, boxes, min_fraction: float = 0.10):
    """Positive patch when >=10% is annotated; masks must be image-aligned."""
    if mask.ndim != 2 or not 0 < min_fraction <= 1:
        raise ValueError("Máscara 2D o proporción inválida.")
    if any(x2 > mask.shape[1] or y2 > mask.shape[0]
           for x1, y1, x2, y2 in boxes):
        raise ValueError("Máscara más pequeña que la imagen.")
    return np.asarray([
        int((mask[y1:y2, x1:x2] > 0).mean() >= min_fraction)
        for x1, y1, x2, y2 in boxes
    ], dtype=np.uint8)


def patch_map(labels, boxes, image_shape):
    """Expand patch labels to an image-sized binary mask; border remainder stays zero."""
    result = np.zeros(image_shape, dtype=np.uint8)
    for label, (x1, y1, x2, y2) in zip(labels, boxes):
        result[y1:y2, x1:x2] = 255 if label else 0
    return result
