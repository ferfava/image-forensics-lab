"""Create an IMD2020 manifest from case folders, keeping all variants grouped.

No data is copied to the repository. Generates binarized masks in <dataset>/_ifl_masks/
and a CSV next to the dataset. Only original photo and a mask-bearing modified
file count as usable case members.
"""
import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def import_imd2020(root: Path, max_groups: int | None = None, include_originals: bool = True):
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"No existe la carpeta: {root}")
    folders = sorted(folder for folder in root.iterdir() if folder.is_dir()
                     and folder.name != "_ifl_masks")
    if not folders:
        raise ValueError("No se encontraron subcarpetas de casos IMD2020.")
    mask_dir = root / "_ifl_masks"
    rows, warnings, groups = [], [], 0
    for folder in folders:
        files = {p.stem.lower(): p for p in folder.iterdir()
                 if p.is_file() and p.suffix.lower() in IMAGE_EXT}
        originals = [p for p in files.values() if p.stem.lower().endswith("_orig")]
        if len(originals) != 1:
            warnings.append(f"{folder.name}: esperado 1 original; encontrados {len(originals)}")
            continue
        original = originals[0]
        group_rows = []
        try:
            with Image.open(original) as stream:
                orig_rgb = ImageOps.exif_transpose(stream).convert("RGB")
                original_size = orig_rgb.size
        except OSError as exc:
            warnings.append(f"{folder.name}: original ilegible ({exc})")
            continue
        for stem, edited in sorted(files.items()):
            if stem.endswith("_mask") or stem.endswith("_orig"):
                continue
            mask_source = files.get(stem + "_mask")
            if not mask_source:
                warnings.append(f"{folder.name}: {edited.name} sin máscara")
                continue
            try:
                with Image.open(edited) as img, Image.open(mask_source) as mask_file:
                    if ImageOps.exif_transpose(img).size != original_size:
                        warnings.append(f"{folder.name}: {edited.name} con tamaño diferente")
                        continue
                    grayscale = ImageOps.exif_transpose(mask_file).convert("L")
                    if grayscale.size != original_size:
                        warnings.append(f"{folder.name}: máscara {mask_source.name} desalineada")
                        continue
                    raw = np.asarray(grayscale, dtype=np.uint8)
                    binary = (raw >= 128).astype(np.uint8) * 255
                    if not np.any(binary):
                        warnings.append(f"{folder.name}: máscara vacía {mask_source.name}")
                        continue
                    if np.all(binary):
                        warnings.append(f"{folder.name}: máscara totalmente blanca {mask_source.name}")
                        continue
                    mask_dir.mkdir(exist_ok=True)
                    target = mask_dir / f"{folder.name}_{edited.stem}_binary.png"
                    Image.fromarray(binary).save(target)
            except (OSError, ValueError) as exc:
                warnings.append(f"{folder.name}: archivo inválido {edited.name} ({exc})")
                continue
            group_rows.append({"image": edited.relative_to(root).as_posix(),
                               "mask": target.relative_to(root).as_posix(),
                               "group": folder.name, "source": "IMD2020"})
        if not group_rows:
            continue
        if include_originals:
            mask_dir.mkdir(exist_ok=True)
            empty_mask = mask_dir / f"{folder.name}_original_black.png"
            Image.fromarray(np.zeros((original_size[1], original_size[0]),
                                     dtype=np.uint8)).save(empty_mask)
            group_rows.insert(0, {"image": original.relative_to(root).as_posix(),
                                  "mask": empty_mask.relative_to(root).as_posix(),
                                  "group": folder.name, "source": "IMD2020"})
        rows.extend(group_rows)
        groups += 1
        if max_groups and groups >= max_groups:
            break
    if not rows:
        raise ValueError("No se encontraron tríos originales/edición/máscara válidos.")
    manifest = root / "manifest_imd2020.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["image", "mask", "group", "source"])
        writer.writeheader()
        writer.writerows(rows)
    return {"manifest": str(manifest), "groups": groups, "rows": len(rows),
            "warnings_count": len(warnings), "warning_examples": warnings[:15]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True,
                        help="Carpeta descomprimida que contiene casos como 1a1ogs/")
    parser.add_argument("--max-groups", type=int, default=30,
                        help="Número de casos válidos a importar (predeterminado 30)")
    parser.add_argument("--no-originals", action="store_true")
    args = parser.parse_args()
    import json
    report = import_imd2020(args.root, args.max_groups,
                            include_originals=not args.no_originals)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
