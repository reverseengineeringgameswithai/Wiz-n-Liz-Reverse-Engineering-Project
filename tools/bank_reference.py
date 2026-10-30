"""Independent research model derived from pinned MAME's bitplane layout.

This is project-authored specification checking, not execution of MAME or the
game. See third_party/vdp_reference.lock.json and FIND-0008. The native decoder
uses packed nibbles; this model reads individual planes from word storage.
"""
from rnc import RncError


def pattern_indices(packed):
    if len(packed) != 32:
        raise RncError("reference pattern must contain 32 bytes")
    # Model the u16 VRAM backing store of the inspected x86_64 MAME layout.
    storage = bytearray(32)
    storage[0::2], storage[1::2] = packed[1::2], packed[0::2]
    offsets = (8, 12, 0, 4, 24, 28, 16, 20)
    result = []
    for row in range(8):
        for column in range(8):
            value = 0
            for plane, weight in enumerate((8, 4, 2, 1)):
                address = row * 32 + offsets[column] + plane
                if storage[address // 8] & (128 >> (address % 8)):
                    value += weight
            result.append(value)
    return result


def check_atlas(data, rgba, width, height, columns):
    if len(data) < 34 or not 1 <= columns <= 256:
        raise RncError("invalid reference bank/columns")
    count = int.from_bytes(data[32:34], "big") + 1
    if len(data) != 34 + 40 * count or width != columns * 8 or height != ((count - 1) // columns + 1) * 8:
        raise RncError("reference bank/atlas extent mismatch")
    if len(rgba) != width * height * 4:
        raise RncError("reference raster extent mismatch")
    levels = (0, 36, 73, 109, 146, 182, 219, 255)  # Chosen digital policy, not MAME's analog LUT.
    palette = []
    for index in range(16):
        value = int.from_bytes(data[index * 2:index * 2 + 2], "big")
        palette.append(bytes((levels[(value // 512) % 8], levels[(value // 32) % 8],
                              levels[(value // 2) % 8], 0 if index == 0 else 255)))
    expected = bytearray(len(rgba))
    for tile in range(count):
        indices = pattern_indices(data[34 + tile * 32:66 + tile * 32])
        for p, index in enumerate(indices):
            destination = ((tile // columns * 8 + p // 8) * width + tile % columns * 8 + p % 8) * 4
            expected[destination:destination + 4] = palette[index]
    if expected != rgba:
        raise RncError("native atlas disagrees with independent bitplane/palette model")
    return {"method": "source-derived bitplane model; no MAME or game execution",
            "patterns": count, "pattern_pixels": count * 64, "padding_pixels": width * height - count * 64,
            "palette_policy": "normal-rgb3-rounded-v1", "reference_lock": "third_party/vdp_reference.lock.json"}
