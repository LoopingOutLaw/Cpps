#!/usr/bin/env python3
"""
generate_aruco_textures.py
==========================
Generates ArUco PNG textures used as Gazebo material albedo maps.

DICT_4X4_50 markers generated:
  IDs 1-4    → aruco_1.png … aruco_4.png     (floor reference, 200×200 mm in world)
  IDs 10-13  → aruco_10.png … aruco_13.png   (box-top markers, 90×90 mm in world)

Each PNG is 512×512 pixels with a white border (required by ArUco spec so
the black outer frame is detectable).

Run once before or during colcon build:
    python3 generate_aruco_textures.py [output_dir]

If output_dir is omitted, writes to <script_dir>/../textures/
"""

import sys
import os
from pathlib import Path

# ── Output directory ──────────────────────────────────────────────────────────

if len(sys.argv) > 1:
    out_dir = Path(sys.argv[1])
else:
    script_dir = Path(__file__).resolve().parent
    out_dir    = script_dir.parent / "textures"

out_dir.mkdir(parents=True, exist_ok=True)
print(f"Output directory: {out_dir}")

# ── Marker IDs ────────────────────────────────────────────────────────────────

FLOOR_REF_IDS = [1, 2, 3, 4]          # reference corners on floor
BOX_TOP_IDS   = [10, 11, 12, 13]      # ArUco on each box slot
MARKER_IDS    = FLOOR_REF_IDS + BOX_TOP_IDS

IMAGE_SIZE  = 512    # px
BORDER_FRAC = 0.15   # white border fraction

# ── Generation ────────────────────────────────────────────────────────────────

try:
    import cv2
    import numpy as np
    _CV2_OK = True
except ImportError:
    _CV2_OK = False
    print("WARNING: opencv-python not installed.  Using PIL/minimal fallback.")
    print("         pip install opencv-python")


def generate_aruco_png(marker_id: int, out_path: Path) -> None:
    if _CV2_OK:
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        inner_size = int(IMAGE_SIZE * (1.0 - 2 * BORDER_FRAC))
        marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, inner_size)

        canvas = np.full((IMAGE_SIZE, IMAGE_SIZE), 255, dtype=np.uint8)
        b      = int(IMAGE_SIZE * BORDER_FRAC)
        canvas[b:b + inner_size, b:b + inner_size] = marker_img

        # Save greyscale PNG  (OGRE2 / Gazebo Harmonic accepts greyscale)
        cv2.imwrite(str(out_path), canvas)
        print(f"  ✓ {out_path.name}   (ArUco ID {marker_id}, {IMAGE_SIZE}px)")
    else:
        _fallback_png(out_path, marker_id)


def _fallback_png(out_path: Path, marker_id: int) -> None:
    """PIL checkerboard fallback when opencv is unavailable."""
    try:
        from PIL import Image, ImageDraw  # type: ignore[import]
        img  = Image.new("L", (IMAGE_SIZE, IMAGE_SIZE), 255)
        draw = ImageDraw.Draw(img)
        sq   = IMAGE_SIZE // 8
        for r in range(8):
            for c in range(8):
                if (r + c) % 2 == 0:
                    draw.rectangle([c*sq, r*sq, (c+1)*sq-1, (r+1)*sq-1], fill=0)
        draw.text((10, 10), f"ID={marker_id}", fill=128)
        img.save(str(out_path))
        print(f"  ~ {out_path.name}   (PIL fallback, ID {marker_id})")
    except ImportError:
        _minimal_png(out_path, marker_id)


def _minimal_png(out_path: Path, marker_id: int) -> None:
    """Pure-stdlib white PNG when neither cv2 nor PIL available."""
    import struct, zlib

    def chunk(name: bytes, data: bytes) -> bytes:
        raw = name + data
        return (struct.pack(">I", len(data)) + raw
                + struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF))

    size   = 16
    header = b"\x89PNG\r\n\x1a\n"
    ihdr   = chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 0, 0, 0, 0))
    row    = b"\x00" + b"\xff" * size
    idat   = chunk(b"IDAT", zlib.compress(row * size))
    iend   = chunk(b"IEND", b"")
    with open(out_path, "wb") as f:
        f.write(header + ihdr + idat + iend)
    print(f"  ! {out_path.name}   (minimal 16px PNG, ID {marker_id})")


# ── Run ───────────────────────────────────────────────────────────────────────

errors = 0
for mid in MARKER_IDS:
    try:
        generate_aruco_png(mid, out_dir / f"aruco_{mid}.png")
    except Exception as exc:
        print(f"  ERROR aruco_{mid}.png: {exc}")
        errors += 1

print()
if errors == 0:
    print(f"✓  All {len(MARKER_IDS)} ArUco textures generated in {out_dir}")
    print(f"   Floor reference IDs : {FLOOR_REF_IDS}")
    print(f"   Box-top IDs         : {BOX_TOP_IDS}")
    print("   Run:  colcon build --packages-select dexter_description")
else:
    print(f"✗  {errors} error(s) — check output above")
    sys.exit(1)
