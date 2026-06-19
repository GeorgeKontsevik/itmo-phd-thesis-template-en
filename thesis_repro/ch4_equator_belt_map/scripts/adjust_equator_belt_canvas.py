#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR.parent
THESIS_DIR = PACKAGE_DIR.parents[1]
DEFAULT_SOURCE = PACKAGE_DIR / "data/equator_belt_map_ru.png"
DEFAULT_OUT = PACKAGE_DIR / "outputs/equator_belt_map_ru_cropped_taller.png"
DEFAULT_THESIS_IMAGE = THESIS_DIR / "images/ch4/equator_belt_map_ru_cropped_taller.png"


def main() -> None:
    parser = argparse.ArgumentParser(description="Crop the thesis equator belt map and increase canvas height.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--thesis-image", type=Path, default=DEFAULT_THESIS_IMAGE)
    parser.add_argument("--left", type=int, default=150)
    parser.add_argument("--right", type=int, default=160)
    parser.add_argument("--height-scale", type=float, default=1.3)
    parser.add_argument("--no-copy-to-thesis", action="store_true")
    args = parser.parse_args()

    image = Image.open(args.source).convert("RGBA")
    width, height = image.size
    cropped = image.crop((args.left, 0, width - args.right, height))
    new_height = round(cropped.height * args.height_scale)
    output = Image.new("RGBA", (cropped.width, new_height), (255, 255, 255, 255))
    output.alpha_composite(cropped, (0, (new_height - cropped.height) // 2))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    output.save(args.out)
    print(f"wrote={args.out} size={output.width}x{output.height}")

    if not args.no_copy_to_thesis:
        args.thesis_image.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.out, args.thesis_image)
        print(f"copied={args.thesis_image}")


if __name__ == "__main__":
    main()
