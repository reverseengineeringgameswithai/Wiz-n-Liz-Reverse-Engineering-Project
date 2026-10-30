"""Independent source-derived static plane model; no game or MAME execution."""
from bank_reference import pattern_indices
from rnc import RncError
from rnc_loader_probe import inspect_pattern_bank
from scene_probe import inspect_scene


def check_scene_image(scene, base, rgba, width, height):
    layout = inspect_scene(scene)
    bank_layout = inspect_pattern_bank(base)
    if (width, height) != (1024, 256) or len(rgba) != width * height * 4:
        raise RncError("reference scene image extent mismatch")
    lo, hi = bank_layout["regions"]["patterns"]["range"]
    patterns = base[lo:hi]
    lo, hi = layout["regions"]["patterns"]["range"]
    patterns += scene[lo:hi]
    tiles = [pattern_indices(patterns[p:p + 32]) for p in range(0, len(patterns), 32)]
    levels = (0, 36, 73, 109, 146, 182, 219, 255)
    palette = []
    for i in range(16):
        v = int.from_bytes(base[i * 2:i * 2 + 2], "big")
        palette.append(bytes((levels[(v // 512) % 8], levels[(v // 32) % 8],
                              levels[(v // 2) % 8], 0 if i == 0 else 255)))
    lo, hi = layout["regions"]["map"]["range"]
    expected = bytearray(len(rgba))
    for cell, offset in enumerate(range(lo, hi, 2)):
        word = int.from_bytes(scene[offset:offset + 2], "big")
        index = word % 2048
        if index >= len(tiles) or ((word // 8192) % 4 | 2) != 2:
            raise RncError("unsupported reference scene pattern or palette")
        rows = [tiles[index][r:r + 8] for r in range(0, 64, 8)]
        if word & 4096:
            rows.reverse()
        if word & 2048:
            rows = [list(reversed(row)) for row in rows]
        for row, pixels in enumerate(rows):
            begin = ((cell // 128 * 8 + row) * width + cell % 128 * 8) * 4
            expected[begin:begin + 32] = b"".join(palette[p] for p in pixels)
    if expected != rgba:
        raise RncError("native scene disagrees with independent plane model")
    return {"method": "source-derived bitplanes, row reversal and palette model; no emulator execution",
            "map_cells": 4096, "pixels_compared": width * height, "single_plane": True}
