"""Generate a small SYNTHETIC dataset to smoke-test the ML pipeline.

Not representative of real tampering; never use its test scores as validity evidence.
"""
import argparse
import csv
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def make_dataset(output: Path, count: int = 36, seed: int = 42):
    if count < 12:
        raise ValueError("Se requieren al menos 12 grupos para la prueba.")
    rng = np.random.default_rng(seed)
    image_dir, mask_dir = output / "images", output / "masks"
    image_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i in range(count):
        # Smooth heterogeneous synthetic patterns + sensor-like noise.
        y, x = np.mgrid[:128, :128]
        phase = rng.uniform(0, 6.28, size=3)
        base = np.stack([
            110 + 55 * np.sin(x / (9 + channel * 4) + phase[channel])
            + 35 * np.cos(y / (12 + channel * 3) + phase[channel])
            for channel in range(3)
        ], axis=-1)
        base += rng.normal(0, 9, size=base.shape)
        original = np.clip(base, 0, 255).astype(np.uint8)
        edited = original.copy()
        mask = np.zeros((128, 128), dtype=np.uint8)
        if i % 4 != 0:
            # Patch-aligned control region, never derived from prediction.
            col = int(rng.integers(0, 3))
            row = int(rng.integers(0, 3))
            x0, y0 = col * 32, row * 32
            mask[y0:y0 + 32, x0:x0 + 32] = 255
            if i % 2 == 0:
                edited[y0:y0 + 32, x0:x0 + 32] = np.clip(
                    edited[y0:y0 + 32, x0:x0 + 32].astype(np.int16) + 75,
                    0, 255
                ).astype(np.uint8)
            else:
                # Copy from a non-overlapping region of the same image.
                sx = ((col + 1) % 4) * 32
                sy = ((row + 1) % 4) * 32
                edited[y0:y0 + 32, x0:x0 + 32] = original[sy:sy + 32, sx:sx + 32]
        name = f"sample_{i:03d}"
        Image.fromarray(edited).save(image_dir / (name + ".png"))
        Image.fromarray(mask).save(mask_dir / (name + ".png"))
        manifest.append({"image": f"images/{name}.png",
                         "mask": f"masks/{name}.png",
                         "group": name, "source": "synthetic_demo"})
    with (output / "manifest.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["image", "mask", "group", "source"])
        writer.writeheader()
        writer.writerows(manifest)
    return output / "manifest.csv"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/ml_synthetic"))
    parser.add_argument("--count", type=int, default=36)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print("Dataset SOLO para verificar el pipeline:", make_dataset(args.out, args.count, args.seed))


if __name__ == "__main__":
    main()
