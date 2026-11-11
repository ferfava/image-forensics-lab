"""Version 2: existing eight patch features plus local texture/context signals.

Single-image only. No ground-truth data nor pristine reference is used at inference.
The first eight columns are EXACTLY the V1 feature schema/order.
"""
import cv2
import numpy as np

from image_forensics.features.patches import FEATURE_NAMES, patch_features

FEATURE_NAMES_V2 = FEATURE_NAMES + (
    "lbp_uniformity", "lbp_entropy",
    "neighbor_gray_mean_delta", "neighbor_gray_std_delta",
    "neighbor_jpeg_residual_delta", "neighbor_lbp_entropy_delta",
)


def _lbp_codes(gray: np.ndarray):
    """Basic 8-neighbor, radius-1 LBP in uint8; no extra dependencies."""
    h, w = gray.shape
    padded = cv2.copyMakeBorder(gray, 1, 1, 1, 1, cv2.BORDER_REFLECT_101)
    code = np.zeros_like(gray, dtype=np.uint8)
    neighbors = [
        (0, 0), (0, 1), (0, 2), (1, 2),
        (2, 2), (2, 1), (2, 0), (1, 0),
    ]
    for bit, (dy, dx) in enumerate(neighbors):
        code |= ((padded[dy:dy + h, dx:dx + w] >= gray).astype(np.uint8) << bit)
    return code


def patch_features_v2(rgb: np.ndarray, patch_size: int = 32):
    """Return V1 features + LBP texture and *local neighbor* differences.

    No other image is consulted. Neighbor differences use adjacent patch features
    within this same photograph; boundary patches use available neighbors only.
    """
    original, boxes, shape = patch_features(rgb, patch_size)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    lbp = _lbp_codes(gray)
    n_rows = shape[0] // patch_size
    n_cols = shape[1] // patch_size
    extra = np.zeros((len(boxes), 2), dtype=np.float32)
    for i, (x1, y1, x2, y2) in enumerate(boxes):
        values = np.bincount(lbp[y1:y2, x1:x2].ravel(), minlength=256).astype(np.float64)
        probabilities = values / values.sum()
        nonzero = probabilities[probabilities > 0]
        extra[i, 0] = float((probabilities ** 2).sum())
        extra[i, 1] = float(-(nonzero * np.log2(nonzero)).sum())
    combined = np.column_stack([original, extra]).astype(np.float32)
    # Neighbor contrasts: differences from median of 4 spatially adjacent patches.
    selected = [0, 1, 6, 9]
    context = np.zeros((len(boxes), len(selected)), dtype=np.float32)
    for index in range(len(boxes)):
        row, col = divmod(index, n_cols)
        adjacent = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = row + dr, col + dc
            if 0 <= rr < n_rows and 0 <= cc < n_cols:
                adjacent.append(rr * n_cols + cc)
        if adjacent:
            for j, col_index in enumerate(selected):
                median = np.median(combined[adjacent, col_index])
                context[index, j] = abs(combined[index, col_index] - median)
    result = np.column_stack([combined, context]).astype(np.float32)
    if result.shape[1] != len(FEATURE_NAMES_V2) or not np.isfinite(result).all():
        raise ValueError("Características V2 inválidas o no finitas.")
    return result, boxes, shape
