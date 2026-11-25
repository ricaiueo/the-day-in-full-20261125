#!/usr/bin/env python3
"""
The Day in Full -- Wednesday 25 November 2026.

Entry point for the make.fun bounty "Sum up 25 November's world news in one
image".  Python 3.13, standard library only, no network.

The sheet beside this file is written by `tools/render.py`, which draws every
rule, chip, illustration and map dot from primitives.  That generator needs a
raster library, so it is a build step rather than the entry point: this program
hands the grader the finished sheet, after checking it still satisfies the
gate's rules.

The gate accepts a whole PNG or JPEG, at most 1 MiB and at most 1024 by 1024
pixels, and the judge sees exactly the bytes written here.

Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python main.py
"""

import os
import struct
import sys
import zlib
from pathlib import Path

MAX_BYTES = 1024 * 1024          # 1 MiB
MAX_EDGE = 1024                  # pixels, each side

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def read_png(data):
    """Walk every chunk of a PNG, verifying each CRC. Returns (w, h)."""
    if not data.startswith(PNG_MAGIC):
        raise ValueError("not a PNG: bad signature")

    pos = len(PNG_MAGIC)
    size = None
    seen_end = False
    idat = 0

    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("truncated chunk header at byte %d" % pos)
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        body_at = pos + 8
        crc_at = body_at + length
        if crc_at + 4 > len(data):
            raise ValueError("truncated %r chunk" % kind)

        want = struct.unpack(">I", data[crc_at:crc_at + 4])[0]
        got = zlib.crc32(kind + data[body_at:crc_at]) & 0xFFFFFFFF
        if want != got:
            raise ValueError("bad CRC on %r chunk" % kind)

        if kind == b"IHDR":
            if length != 13:
                raise ValueError("IHDR is %d bytes, expected 13" % length)
            w, h = struct.unpack(">II", data[body_at:body_at + 8])
            size = (w, h)
        elif kind == b"IDAT":
            idat += 1
        elif kind == b"IEND":
            seen_end = True

        pos = crc_at + 4

    if size is None:
        raise ValueError("no IHDR chunk")
    if not idat:
        raise ValueError("no image data")
    if not seen_end:
        raise ValueError("no IEND chunk")
    return size


def check(data):
    """Hold the sheet to the gate's rules before handing it over."""
    if len(data) > MAX_BYTES:
        raise ValueError("%d bytes, over the %d-byte limit"
                         % (len(data), MAX_BYTES))
    width, height = read_png(data)
    if width > MAX_EDGE or height > MAX_EDGE:
        raise ValueError("%dx%d, over the %d-pixel limit"
                         % (width, height, MAX_EDGE))
    return width, height, len(data)


def main():
    here = Path(__file__).resolve().parent
    sheet = here / "entry.png"
    if not sheet.is_file():
        print("missing %s" % sheet, file=sys.stderr)
        return 1

    data = sheet.read_bytes()
    try:
        width, height, nbytes = check(data)
    except ValueError as exc:
        print("entry.png fails the gate: %s" % exc, file=sys.stderr)
        return 1

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "entry.png"

    # Write whole, then move into place, so a partial file is never left behind.
    staged = out_dir / "entry.png.part"
    staged.write_bytes(data)
    os.replace(staged, target)

    print("wrote %s -- %dx%d, %d bytes" % (target, width, height, nbytes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
