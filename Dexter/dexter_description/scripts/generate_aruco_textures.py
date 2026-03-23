#!/usr/bin/env python3
"""
generate_aruco_textures.py
==========================
Generates ArUco PNG textures (DICT_4X4_50) for Gazebo PBR albedo maps.

Marker ID assignments:
  IDs 1-4   → floor reference corners      (200×200 mm in world)
  ID  5     → arm base floor marker        (150×150 mm)
  IDs 10-13 → box-top markers per slot     ( 90× 90 mm)
  ID  21    → gripper tip marker           (120×120 mm, on claw_support)

ID 20 removed — was on base_plate, always hidden by arm body.
ID 21 is on claw_support (gripper tip), visible from overhead camera
when arm bends toward the shelf to pick boxes.

Run:
    python3 generate_aruco_textures.py [output_dir]
"""

import sys
import os
from pathlib import Path

if len(sys.argv) > 1:
    out_dir = Path(sys.argv[1])
else:
    out_dir = Path(__file__).resolve().parent.parent / "textures"

out_dir.mkdir(parents=True, exist_ok=True)
print(f"Output directory: {out_dir}")

# ── Marker IDs ────────────────────────────────────────────────────────────────
FLOOR_REF_IDS  = [1, 2, 3, 4]
ARM_FLOOR_IDS  = [5]
BOX_TOP_IDS    = [10, 11, 12, 13]
GRIPPER_IDS    = [21]          # ← gripper tip, replaces old ID 20

MARKER_IDS = FLOOR_REF_IDS + ARM_FLOOR_IDS + BOX_TOP_IDS + GRIPPER_IDS

IMAGE_SIZE  = 512
BORDER_FRAC = 0.15

# ── OpenCV or fallback ────────────────────────────────────────────────────────
try:
    import cv2
    import numpy as np
    _CV2_OK = True
except ImportError:
    _CV2_OK = False
    print("WARNING: opencv-python not installed — using PIL fallback.")


def generate_aruco_png(marker_id: int, out_path: Path) -> None:
    if _CV2_OK:
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        inner      = int(IMAGE_SIZE * (1.0 - 2 * BORDER_FRAC))
        marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, inner)
        canvas     = np.full((IMAGE_SIZE, IMAGE_SIZE), 255, dtype=np.uint8)
        b          = int(IMAGE_SIZE * BORDER_FRAC)
        canvas[b:b + inner, b:b + inner] = marker_img
        cv2.imwrite(str(out_path), canvas)
        print(f"  ✓ {out_path.name}  (ID {marker_id}, {IMAGE_SIZE}px)")
    else:
        _fallback_png(out_path, marker_id)


def _fallback_png(out_path: Path, marker_id: int) -> None:
    try:
        from PIL import Image, ImageDraw
        img  = Image.new("L", (IMAGE_SIZE, IMAGE_SIZE), 255)
        draw = ImageDraw.Draw(img)
        sq   = IMAGE_SIZE // 8
        for r in range(8):
            for c in range(8):
                if (r + c) % 2 == 0:
                    draw.rectangle([c*sq, r*sq, (c+1)*sq-1, (r+1)*sq-1], fill=0)
        draw.text((10, 10), f"ID={marker_id}", fill=128)
        img.save(str(out_path))
        print(f"  ~ {out_path.name}  (PIL fallback, ID {marker_id})")
    except ImportError:
        _minimal_png(out_path, marker_id)


def _minimal_png(out_path: Path, marker_id: int) -> None:
    import struct, zlib
    def chunk(name, data):
        raw = name + data
        return struct.pack(">I", len(data)) + raw + struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF)
    s = 16
    header = b"\x89PNG\r\n\x1a\n"
    ihdr   = chunk(b"IHDR", struct.pack(">IIBBBBB", s, s, 8, 0, 0, 0, 0))
    row    = b"\x00" + b"\xff" * s
    idat   = chunk(b"IDAT", zlib.compress(row * s))
    iend   = chunk(b"IEND", b"")
    out_path.write_bytes(header + ihdr + idat + iend)
    print(f"  ! {out_path.name}  (minimal PNG, ID {marker_id})")


errors = 0
for mid in MARKER_IDS:
    try:
        generate_aruco_png(mid, out_dir / f"aruco_{mid}.png")
    except Exception as exc:
        print(f"  ERROR aruco_{mid}.png: {exc}")
        errors += 1

print()
if errors == 0:
    print(f"✓  All {len(MARKER_IDS)} textures generated in {out_dir}")
    print(f"   Floor corners : {FLOOR_REF_IDS}")
    print(f"   Arm base      : {ARM_FLOOR_IDS}")
    print(f"   Box tops      : {BOX_TOP_IDS}")
    print(f"   Gripper tip   : {GRIPPER_IDS}  (ID 21 on claw_support)")
else:
    print(f"✗  {errors} error(s)")
    sys.exit(1)
