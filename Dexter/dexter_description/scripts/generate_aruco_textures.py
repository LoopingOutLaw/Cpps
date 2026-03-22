#!/usr/bin/env python3
"""
generate_aruco_textures.py
Generates actual ArUco marker PNG images for use as Gazebo material textures.

Run ONCE before colcon build:
    cd ~/Cpps/Dexter
    python3 Dexter/dexter_description/scripts/generate_aruco_textures.py

Or from anywhere:
    python3 /path/to/generate_aruco_textures.py [output_dir]

Output: dexter_description/textures/aruco_*.png
  aruco_1.png  ... aruco_4.png   — reference corner markers (IDs 1-4)
  aruco_10.png ... aruco_13.png  — box-top markers (IDs 10-13)

All images are 512×512 px with a white border (as required by the ArUco spec
so the detector can find the black outer frame).
"""

import sys
import os
from pathlib import Path

# ── Locate output directory ───────────────────────────────────────────────────

if len(sys.argv) > 1:
    out_dir = Path(sys.argv[1])
else:
    # Default: textures/ next to this script's parent (dexter_description/)
    script_dir = Path(__file__).resolve().parent
    out_dir    = script_dir.parent / "textures"

out_dir.mkdir(parents=True, exist_ok=True)
print(f"Output directory: {out_dir}")

# ── Generate markers ──────────────────────────────────────────────────────────

try:
    import cv2
    import numpy as np
    _CV2_OK = True
except ImportError:
    _CV2_OK = False
    print("WARNING: opencv-python not installed.  Generating placeholder images.")
    print("         Install with:  pip install opencv-python")
    print("         Then re-run this script for actual ArUco patterns.")

MARKER_IDS = [1, 2, 3, 4, 10, 11, 12, 13]
IMAGE_SIZE  = 512   # px, final image (marker + border)
BORDER_FRAC = 0.15  # white border as fraction of image size


def generate_aruco_png(marker_id: int, out_path: Path) -> None:
    """Generate a single ArUco marker PNG at out_path."""
    if _CV2_OK:
        aruco_dict  = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        # Size of the inner marker pattern
        inner_size  = int(IMAGE_SIZE * (1.0 - 2 * BORDER_FRAC))

        marker_img  = cv2.aruco.generateImageMarker(aruco_dict, marker_id, inner_size)

        # Embed in white canvas (white border is required for detection)
        canvas = np.full((IMAGE_SIZE, IMAGE_SIZE), 255, dtype=np.uint8)
        border = int(IMAGE_SIZE * BORDER_FRAC)
        canvas[border:border + inner_size, border:border + inner_size] = marker_img

        # Save as grayscale PNG (Gazebo PBR textures work with grayscale)
        cv2.imwrite(str(out_path), canvas)
        print(f"  Wrote {out_path.name}  (ArUco ID {marker_id}, {IMAGE_SIZE}px)")
    else:
        # Fallback: generate a simple black-on-white checkerboard so Gazebo
        # loads without errors (ArUco detection won't work in sim mode).
        try:
            from PIL import Image, ImageDraw, ImageFont  # type: ignore[import]
            img  = Image.new("L", (IMAGE_SIZE, IMAGE_SIZE), 255)
            draw = ImageDraw.Draw(img)
            sq   = IMAGE_SIZE // 8
            for r in range(8):
                for c in range(8):
                    if (r + c) % 2 == 0:
                        draw.rectangle(
                            [c * sq, r * sq, (c + 1) * sq - 1, (r + 1) * sq - 1],
                            fill=0,
                        )
            draw.text((10, 10), f"ID={marker_id}", fill=128)
            img.save(str(out_path))
            print(f"  Wrote {out_path.name}  (placeholder, ID {marker_id})")
        except ImportError:
            # Last resort: write a minimal 2×2 white PNG (won't detect in sim)
            _write_minimal_png(out_path, marker_id)


def _write_minimal_png(out_path: Path, marker_id: int) -> None:
    """Write a tiny valid white PNG when neither cv2 nor PIL is available."""
    import struct, zlib

    def _chunk(name: bytes, data: bytes) -> bytes:
        c   = struct.pack(">I", len(data)) + name + data
        crc = zlib.crc32(name + data) & 0xFFFFFFFF
        return c + struct.pack(">I", crc)

    size    = 16
    header  = b"\x89PNG\r\n\x1a\n"
    ihdr    = _chunk(b"IHDR",
                     struct.pack(">IIBBBBB", size, size, 8, 0, 0, 0, 0))
    row     = b"\x00" + b"\xff" * size
    idat    = _chunk(b"IDAT",
                     zlib.compress(row * size))
    iend    = _chunk(b"IEND", b"")
    png     = header + ihdr + idat + iend

    with open(out_path, "wb") as f:
        f.write(png)
    print(f"  Wrote {out_path.name}  (minimal 16px PNG, ID {marker_id})")


# ── Main ──────────────────────────────────────────────────────────────────────

errors = 0
for mid in MARKER_IDS:
    try:
        generate_aruco_png(mid, out_dir / f"aruco_{mid}.png")
    except Exception as exc:
        print(f"  ERROR generating aruco_{mid}.png: {exc}")
        errors += 1

print()
if errors == 0:
    print(f"✓ All {len(MARKER_IDS)} ArUco textures generated in {out_dir}")
    print("  Now run:  colcon build --packages-select dexter_description")
else:
    print(f"✗ {errors} error(s) — check output above")
    sys.exit(1)
