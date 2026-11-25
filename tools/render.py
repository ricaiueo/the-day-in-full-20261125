#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
THE DAY IN FULL -- Wednesday 25 November 2026
=============================================

A single-sheet, data-dense news broadsheet for one calendar day, drawn entirely
in code. No network access, no bundled photography: every illustration, the
world map and all rules and chips are generated from primitives at run time.

Design contract
---------------
* Output: /output/entry.png  (override with argv[1])
* Canvas: exactly 1024 x 1024 px, well under the 1 MiB cap
* Deterministic: no clock reads, no RNG without a fixed seed, no dict-order
  dependence. Two runs produce byte-identical files.

Editorial contract
------------------
* Every story carries a dateline, a certainty label and its sources.
* REPORTED = carried by the day's wires. CLAIM = one side's account, labelled
  as such. FORECAST = scheduled but not yet happened when this was drawn.
* Stories from adjacent days are *excluded* and listed in the DATE CHECK box,
  so the sheet can be audited against any other roundup of 25 November 2026.

Author: cherry-vodka
License: MIT
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------------------
# Geometry
# ----------------------------------------------------------------------------

W = H = 1024          # final canvas
SCALE = 2             # supersampling factor
M = 20                # outer margin
CW = W - 2 * M        # content width = 984

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(HERE, "assets", "fonts")

# ----------------------------------------------------------------------------
# Palette -- newsprint cream, iron-gall navy, vermilion
# ----------------------------------------------------------------------------

PAPER      = (246, 241, 229)
PAPER_DEEP = (238, 231, 214)
NAVY       = (27, 42, 74)
NAVY_SOFT  = (58, 74, 108)
INK        = (34, 36, 44)
GREY       = (124, 126, 134)
RULE       = (196, 188, 170)
RED        = (176, 42, 42)
RED_BRIGHT = (205, 56, 46)
GOLD       = (214, 154, 46)
TEAL       = (27, 107, 94)
BLUE       = (43, 75, 155)
GREEN      = (46, 125, 79)
PURPLE     = (107, 74, 138)
WHITE      = (255, 255, 255)
CREAM      = (242, 236, 222)

REGION_COLOR = {
    "EUROPE":       TEAL,
    "MIDDLE EAST":  RED,
    "AMERICAS":     BLUE,
    "ASIA-PACIFIC": GOLD,
    "AFRICA":       GREEN,
    "OCEANIA":      PURPLE,
    "WORLD":        NAVY,
}
REGION_ORDER = ["EUROPE", "MIDDLE EAST", "AMERICAS",
                "ASIA-PACIFIC", "AFRICA", "OCEANIA", "WORLD"]

# ----------------------------------------------------------------------------
# Fonts
# ----------------------------------------------------------------------------

_font_cache = {}


def font(name, size, variation=None):
    """Load a font at `size` *design* units (scaled internally)."""
    key = (name, size, variation)
    if key in _font_cache:
        return _font_cache[key]
    f = ImageFont.truetype(os.path.join(FONTS, name), int(round(size * SCALE)))
    if variation:
        try:
            f.set_variation_by_name(variation)
        except Exception:
            pass
    _font_cache[key] = f
    return f


def display(size, weight="Bold"):
    return font("PlayfairDisplay[wght].ttf", size, weight)


def display_it(size, weight="Medium"):
    return font("PlayfairDisplay-Italic[wght].ttf", size, weight)


def body(size):
    return font("LibreBaskerville[wght].ttf", size, "Regular")


def body_b(size):
    return font("LibreBaskerville[wght].ttf", size, "Bold")


def body_i(size):
    return font("LibreBaskerville-Italic[wght].ttf", size, "Italic")


def sans(size, weight="SemiBold"):
    return font("Archivo[wdth,wght].ttf", size, weight)


def cond(size, weight="Medium"):
    return font("Oswald[wght].ttf", size, weight)


# ----------------------------------------------------------------------------
# Drawing helpers -- all coordinates are in 1024-space; S() scales to canvas
# ----------------------------------------------------------------------------

def S(v):
    return int(round(v * SCALE))


class Sheet(object):
    def __init__(self):
        self.img = Image.new("RGB", (W * SCALE, H * SCALE), PAPER)
        self.d = ImageDraw.Draw(self.img)

    # -- primitives ---------------------------------------------------------

    def rect(self, x, y, w, h, fill=None, outline=None, width=1):
        self.d.rectangle(
            [S(x), S(y), S(x + w) - 1, S(y + h) - 1],
            fill=fill, outline=outline,
            width=max(1, S(width)) if outline else 1,
        )

    def line(self, x1, y1, x2, y2, fill=INK, width=1):
        self.d.line([S(x1), S(y1), S(x2), S(y2)], fill=fill,
                    width=max(1, S(width)))

    def hrule(self, x, y, w, fill=RULE, width=0.6):
        self.rect(x, y, w, max(0.6, width), fill=fill)

    def poly(self, pts, fill=None, outline=None):
        self.d.polygon([(S(p[0]), S(p[1])) for p in pts],
                       fill=fill, outline=outline)

    def ellipse(self, x, y, w, h, fill=None, outline=None, width=1):
        self.d.ellipse([S(x), S(y), S(x + w) - 1, S(y + h) - 1],
                       fill=fill, outline=outline,
                       width=max(1, S(width)) if outline else 1)

    def dot(self, cx, cy, r, fill):
        self.d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], fill=fill)

    def arc(self, x, y, w, h, start, end, fill, width=1):
        self.d.arc([S(x), S(y), S(x + w) - 1, S(y + h) - 1],
                   start, end, fill=fill, width=max(1, S(width)))

    # -- text ---------------------------------------------------------------

    def tw(self, text, f):
        """Text width in 1024-space."""
        return self.d.textlength(text, font=f) / float(SCALE)

    def text(self, x, y, s, f, fill=INK, anchor="la", spacing=0.0):
        """Draw text. `spacing` adds letter-spacing in 1024-space units."""
        if spacing:
            total = self.tw(s, f) + spacing * max(0, len(s) - 1)
            if anchor[0] == "m":
                x -= total / 2.0
            elif anchor[0] == "r":
                x -= total
            va = "a" if len(anchor) < 2 else anchor[1]
            cx = x
            for ch in s:
                self.d.text((S(cx), S(y)), ch, font=f, fill=fill,
                            anchor="l" + va)
                cx += self.tw(ch, f) + spacing
            return total
        self.d.text((S(x), S(y)), s, font=f, fill=fill, anchor=anchor)
        return self.tw(s, f)

    def wrap(self, s, f, width):
        """Greedy wrap; returns list of lines."""
        words = s.split()
        lines, cur = [], ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            if self.tw(trial, f) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, f, width, leading, fill=INK, max_lines=None,
             justify=False):
        """Draw a wrapped paragraph. Returns the y after the last line."""
        lines = self.wrap(s, f, width)
        if max_lines is not None and len(lines) > max_lines:
            lines = lines[:max_lines]
            # trim the last line so an ellipsis fits
            last = lines[-1]
            while last and self.tw(last + "…", f) > width:
                last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
            lines[-1] = last + "…"
        for i, ln in enumerate(lines):
            yy = y + i * leading
            if justify and i < len(lines) - 1 and " " in ln:
                self._justify(x, yy, ln, f, width, fill)
            else:
                self.text(x, yy, ln, f, fill)
        return y + len(lines) * leading

    def _justify(self, x, y, ln, f, width, fill):
        words = ln.split(" ")
        if len(words) < 2:
            self.text(x, y, ln, f, fill)
            return
        wsum = sum(self.tw(w, f) for w in words)
        gap = (width - wsum) / float(len(words) - 1)
        if gap > self.tw(" ", f) * 2.6:          # don't open rivers
            self.text(x, y, ln, f, fill)
            return
        cx = x
        for i, w in enumerate(words):
            self.text(cx, y, w, f, fill)
            cx += self.tw(w, f) + gap

    def fit(self, s, maker, hi, lo, width, max_lines):
        """Pick the largest size in [lo, hi] that wraps into <= max_lines."""
        size = hi
        while size > lo:
            f = maker(size)
            if len(self.wrap(s, f, width)) <= max_lines:
                return f
            size -= 0.5
        return maker(lo)


class Panel(Sheet):
    """A Sheet the size of one illustration, so art cannot bleed past its box."""

    def __init__(self, w, h):
        self.img = Image.new("RGB", (S(w), S(h)), PAPER)
        self.d = ImageDraw.Draw(self.img)


def paint(sh, fn, x, y, w, h):
    """Render an illustration into its own panel and paste it, hard-clipped."""
    p = Panel(w, h)
    fn(p, 0, 0, w, h)
    sh.img.paste(p.img, (S(x), S(y)))


# ----------------------------------------------------------------------------
# Vector illustrations.  Each takes (sheet, x, y, w, h) and paints a flat
# scene.  Deterministic by construction -- every value is derived from the box.
# ----------------------------------------------------------------------------

def _frame(sh, x, y, w, h, bg):
    sh.rect(x, y, w, h, fill=bg)


def art_market_rout(sh, x, y, w, h):
    """Falling candlesticks under a red downward arrow."""
    _frame(sh, x, y, w, h, (22, 33, 58))
    n = 11
    bw = w / float(n + 2)
    heights = [0.26, 0.34, 0.30, 0.46, 0.40, 0.58, 0.52, 0.70, 0.66, 0.82, 0.90]
    for i in range(n):
        cx = x + bw * (i + 1.5)
        hh = h * heights[i] * 0.62
        top = y + h * 0.16 + (h * 0.62 - hh)
        col = RED_BRIGHT if i >= 3 else (74, 104, 150)
        sh.rect(cx - bw * 0.30, top, bw * 0.60, hh, fill=col)
        sh.line(cx, top - h * 0.05, cx, top + hh + h * 0.04,
                fill=col, width=0.7)
    # trend line + arrow head
    x0, y0 = x + w * 0.10, y + h * 0.24
    x1, y1 = x + w * 0.88, y + h * 0.80
    sh.line(x0, y0, x1, y1, fill=(248, 214, 120), width=1.6)
    sh.poly([(x1 + 1, y1 + 2), (x1 - w * 0.075, y1 - h * 0.035),
             (x1 - w * 0.025, y1 - h * 0.14)], fill=(248, 214, 120))
    for i in range(4):
        sh.hrule(x + w * 0.06, y + h * (0.22 + i * 0.19), w * 0.88,
                 fill=(40, 56, 88), width=0.5)


def art_leaked_files(sh, x, y, w, h):
    """A death register: name rows, heavy redactions, a running red tally."""
    _frame(sh, x, y, w, h, (28, 38, 60))
    pad = w * 0.045
    rows = 9
    rh = (h - pad * 1.6) / float(rows)
    widths = [0.74, 0.55, 0.84, 0.47, 0.69, 0.60, 0.78, 0.52, 0.66]
    for i in range(rows):
        yy = y + pad * 0.8 + i * rh + rh * 0.20
        # record number
        sh.rect(x + pad, yy, w * 0.048, rh * 0.46, fill=(128, 150, 192))
        # name field
        sh.rect(x + pad + w * 0.072, yy,
                (w - pad * 2 - w * 0.085) * widths[i] * 0.72, rh * 0.46,
                fill=(96, 118, 162))
        # cause-of-death field, in red where the war is named
        if i % 2 == 0:
            sh.rect(x + w * 0.62, yy, w * 0.16, rh * 0.46,
                    fill=(150, 56, 50))
    # redaction blocks
    for fx, fy, fw in [(0.30, 1, 0.30), (0.17, 3, 0.26), (0.40, 5, 0.24),
                       (0.24, 7, 0.20)]:
        yy = y + pad * 0.8 + fy * rh + rh * 0.12
        sh.rect(x + w * fx, yy, w * fw, rh * 0.62, fill=(14, 18, 28))
    # running tally, five-bar gates
    tx, ty = x + w * 0.795, y + h * 0.13
    for g in range(3):
        gx = tx + g * w * 0.062
        gy = ty + (g // 3) * h * 0.30
        for i in range(4):
            sh.line(gx + i * w * 0.011, gy, gx + i * w * 0.011,
                    gy + h * 0.155, fill=RED_BRIGHT, width=0.9)
        sh.line(gx - w * 0.005, gy + h * 0.148, gx + w * 0.040,
                gy + h * 0.012, fill=RED_BRIGHT, width=0.9)
    # a cracked seal over the stack
    sh.dot(x + w * 0.885, y + h * 0.66, w * 0.062, (150, 56, 50))
    sh.poly([(x + w * 0.885, y + h * 0.60), (x + w * 0.902, y + h * 0.66),
             (x + w * 0.878, y + h * 0.69), (x + w * 0.895, y + h * 0.74)],
            outline=(238, 226, 200))


def art_rocket(sh, x, y, w, h):
    """Long March on a column of flame against a star field."""
    _frame(sh, x, y, w, h, (18, 28, 56))
    stars = [(0.08, 0.18), (0.20, 0.40), (0.14, 0.72), (0.84, 0.22),
             (0.90, 0.54), (0.76, 0.78), (0.30, 0.14), (0.66, 0.34),
             (0.94, 0.80), (0.04, 0.52)]
    for sx, sy in stars:
        sh.dot(x + w * sx, y + h * sy, max(0.6, w * 0.006), (226, 220, 196))
    cx = x + w * 0.50
    bodyw = w * 0.085
    top = y + h * 0.12
    bot = y + h * 0.63
    sh.rect(cx - bodyw / 2, top, bodyw, bot - top, fill=(236, 232, 220))
    sh.poly([(cx, top - h * 0.11), (cx - bodyw / 2, top),
             (cx + bodyw / 2, top)], fill=RED_BRIGHT)
    sh.rect(cx - bodyw / 2, y + h * 0.33, bodyw, h * 0.05, fill=RED_BRIGHT)
    # boosters
    for s in (-1, 1):
        bx = cx + s * bodyw * 0.92
        sh.rect(bx - bodyw * 0.28, y + h * 0.26, bodyw * 0.56,
                bot - y - h * 0.26, fill=(206, 202, 190))
        sh.poly([(bx, y + h * 0.20), (bx - bodyw * 0.28, y + h * 0.26),
                 (bx + bodyw * 0.28, y + h * 0.26)], fill=(236, 232, 220))
    # flame
    sh.poly([(cx - bodyw * 1.30, bot), (cx + bodyw * 1.30, bot),
             (cx + bodyw * 0.30, y + h * 0.94), (cx, y + h * 1.00),
             (cx - bodyw * 0.30, y + h * 0.94)], fill=GOLD)
    sh.poly([(cx - bodyw * 0.70, bot), (cx + bodyw * 0.70, bot),
             (cx, y + h * 0.90)], fill=(248, 226, 150))
    # exhaust billowing out along the pad
    for sgn in (-1, 1):
        for i, (ox, oy, r) in enumerate([(1.6, 0.86, 0.050),
                                         (2.5, 0.92, 0.062),
                                         (3.5, 0.97, 0.048),
                                         (2.0, 1.00, 0.040)]):
            sh.dot(cx + sgn * bodyw * ox, y + h * oy, w * r, (48, 62, 94))
            sh.dot(cx + sgn * bodyw * ox, y + h * (oy - 0.015), w * r * 0.62,
                   (66, 82, 118))


def art_port_strike(sh, x, y, w, h):
    """Gantry cranes over a quay, with blast flashes."""
    _frame(sh, x, y, w, h, (26, 38, 62))
    sea = y + h * 0.72
    sh.rect(x, sea, w, h - (sea - y), fill=(32, 56, 86))
    for i in range(3):
        qx = x + w * (0.14 + i * 0.28)
        sh.rect(qx, y + h * 0.26, w * 0.018, h * 0.46, fill=(206, 200, 184))
        sh.rect(qx - w * 0.07, y + h * 0.26, w * 0.17, h * 0.030,
                fill=(206, 200, 184))
        sh.line(qx + w * 0.009, y + h * 0.29, qx + w * 0.009, y + h * 0.42,
                fill=(150, 150, 150), width=0.6)
    # containers
    cols = [(188, 76, 56), (64, 110, 150), (200, 160, 70), (90, 140, 110)]
    for i in range(8):
        sh.rect(x + w * (0.08 + i * 0.105), y + h * 0.60, w * 0.085,
                h * 0.055, fill=cols[i % 4])
    for i in range(5):
        sh.rect(x + w * (0.14 + i * 0.125), y + h * 0.545, w * 0.085,
                h * 0.055, fill=cols[(i + 2) % 4])
    # blast
    bx, by = x + w * 0.70, y + h * 0.46
    for r, c in [(0.13, (120, 54, 44)), (0.09, RED_BRIGHT), (0.05, GOLD)]:
        sh.dot(bx, by, w * r, c)
    for ang in range(0, 360, 45):
        import math
        a = math.radians(ang)
        sh.line(bx + math.cos(a) * w * 0.10, by + math.sin(a) * w * 0.10,
                bx + math.cos(a) * w * 0.17, by + math.sin(a) * w * 0.17,
                fill=GOLD, width=0.8)


def art_strike_block(sh, x, y, w, h):
    """Night apartment block, lit windows, incoming drones."""
    _frame(sh, x, y, w, h, (20, 28, 52))
    # drones
    for dx, dy in [(0.12, 0.18), (0.26, 0.11), (0.38, 0.22)]:
        px, py = x + w * dx, y + h * dy
        sh.poly([(px, py), (px + w * 0.045, py + h * 0.03),
                 (px, py + h * 0.055)], fill=(230, 226, 210))
        sh.line(px - w * 0.03, py + h * 0.026, px, py + h * 0.026,
                fill=(120, 134, 164), width=0.6)
    # block
    bx, bw = x + w * 0.42, w * 0.50
    sh.rect(bx, y + h * 0.30, bw, h * 0.70, fill=(44, 58, 90))
    for r in range(5):
        for c in range(5):
            lit = (r * 5 + c) % 4 != 1
            col = (250, 214, 112) if lit else (26, 36, 60)
            sh.rect(bx + bw * (0.09 + c * 0.175), y + h * (0.36 + r * 0.125),
                    bw * 0.115, h * 0.072, fill=col)
    # impact scar
    sh.poly([(bx + bw * 0.30, y + h * 0.30), (bx + bw * 0.62, y + h * 0.30),
             (bx + bw * 0.50, y + h * 0.60), (bx + bw * 0.34, y + h * 0.52)],
            fill=(26, 30, 44))
    for r, c in [(0.075, RED_BRIGHT), (0.040, GOLD)]:
        sh.dot(bx + bw * 0.46, y + h * 0.34, w * r, c)
    # searchlight
    sh.poly([(x + w * 0.02, y + h * 1.00), (x + w * 0.30, y + h * 0.04),
             (x + w * 0.40, y + h * 0.06)], fill=(34, 46, 76))


def art_tariffs(sh, x, y, w, h):
    """Container stack behind a struck percentage stamp."""
    _frame(sh, x, y, w, h, (24, 36, 60))
    cols = [(176, 72, 56), (56, 96, 140), (196, 154, 66), (78, 126, 100),
            (120, 92, 150)]
    for r in range(4):
        for c in range(7):
            if (r + c) % 5 == 3 and r > 1:
                continue
            sh.rect(x + w * (0.05 + c * 0.132), y + h * (0.86 - r * 0.175),
                    w * 0.112, h * 0.145, fill=cols[(r * 3 + c) % 5])
            sh.hrule(x + w * (0.05 + c * 0.132), y + h * (0.86 - r * 0.175),
                     w * 0.112, fill=(16, 24, 40), width=0.5)
    # stamp
    sx, sy, sw, shh = x + w * 0.30, y + h * 0.16, w * 0.40, h * 0.34
    sh.rect(sx, sy, sw, shh, fill=None, outline=RED_BRIGHT, width=1.4)
    sh.rect(sx + w * 0.012, sy + h * 0.035, sw - w * 0.024, shh - h * 0.07,
            fill=None, outline=RED_BRIGHT, width=0.6)
    f = cond(h * 0.19, "Bold")
    sh.text(sx + sw / 2, sy + shh / 2, "16", f, RED_BRIGHT, anchor="mm")


def art_treaty(sh, x, y, w, h):
    """Two pennants over a sealed document."""
    _frame(sh, x, y, w, h, (28, 58, 78))
    # sea horizon
    sh.rect(x, y + h * 0.74, w, h * 0.26, fill=(34, 80, 102))
    for i in range(4):
        sh.hrule(x + w * (0.06 + 0.24 * i), y + h * (0.82 + 0.045 * (i % 2)),
                 w * 0.14, fill=(58, 112, 134), width=0.7)
    # document
    dx, dw = x + w * 0.33, w * 0.34
    sh.rect(dx, y + h * 0.26, dw, h * 0.46, fill=(240, 236, 222))
    for i in range(5):
        sh.hrule(dx + dw * 0.14, y + h * (0.34 + i * 0.066), dw * 0.72,
                 fill=(150, 152, 158), width=0.7)
    sh.dot(dx + dw * 0.50, y + h * 0.655, w * 0.030, RED_BRIGHT)
    # flag poles
    for s, col in ((-1, (46, 128, 150)), (1, (200, 164, 80))):
        px = x + w * (0.50 + s * 0.33)
        sh.line(px, y + h * 0.16, px, y + h * 0.78, fill=(222, 218, 204),
                width=0.9)
        sh.poly([(px, y + h * 0.18), (px + s * w * 0.15, y + h * 0.25),
                 (px, y + h * 0.33)], fill=col)


def art_asteroid(sh, x, y, w, h):
    """Dimorphos: cratered moonlet, bright ejecta, dashed orbit, probe."""
    import math
    _frame(sh, x, y, w, h, (14, 20, 42))
    for sx, sy in [(0.09, 0.14), (0.90, 0.12), (0.80, 0.90), (0.20, 0.88),
                   (0.46, 0.06), (0.97, 0.44), (0.33, 0.95), (0.63, 0.14)]:
        sh.dot(x + w * sx, y + h * sy, max(0.6, w * 0.007), (226, 220, 196))

    # dashed orbit, drawn first and bright enough to read
    ox, oy = x + w * 0.46, y + h * 0.52
    rx, ry = w * 0.38, h * 0.36
    for k in range(30):
        if k % 2:
            continue
        a0 = math.radians(k * 12.0)
        a1 = math.radians((k + 1.1) * 12.0)
        sh.line(ox + math.cos(a0) * rx, oy + math.sin(a0) * ry,
                ox + math.cos(a1) * rx, oy + math.sin(a1) * ry,
                fill=(118, 140, 196), width=0.8)

    # Didymos, the primary, small and cropped at the left
    sh.dot(x + w * 0.06, y + h * 0.80, w * 0.105, (78, 72, 64))
    sh.dot(x + w * 0.11, y + h * 0.74, w * 0.024, (56, 52, 46))

    # Dimorphos
    cx, cy, r = x + w * 0.60, y + h * 0.50, w * 0.165
    sh.dot(cx, cy, r, (154, 143, 124))
    sh.dot(cx - r * 0.42, cy + r * 0.34, r * 0.26, (120, 110, 95))
    sh.dot(cx + r * 0.46, cy + r * 0.10, r * 0.18, (120, 110, 95))
    # the DART crater, with ejecta thrown clear
    sh.dot(cx + r * 0.06, cy - r * 0.58, r * 0.40, (58, 52, 46))
    sh.dot(cx + r * 0.06, cy - r * 0.58, r * 0.22, (36, 32, 28))
    for ang, ln in [(252, 0.55), (268, 0.78), (284, 0.62), (300, 0.44),
                    (236, 0.40)]:
        aa = math.radians(ang)
        sh.line(cx + math.cos(aa) * r * 0.9, cy + math.sin(aa) * r * 0.9,
                cx + math.cos(aa) * r * (1.0 + ln),
                cy + math.sin(aa) * r * (1.0 + ln),
                fill=(226, 214, 184), width=0.8)

    # Hera, station-keeping
    px, py = x + w * 0.19, y + h * 0.26
    sh.rect(px - w * 0.026, py - h * 0.030, w * 0.052, h * 0.060,
            fill=(236, 232, 218))
    for sgn in (-1, 1):
        sh.line(px + sgn * w * 0.026, py, px + sgn * w * 0.052, py,
                fill=(236, 232, 218), width=0.7)
        sh.rect(px + sgn * w * 0.082 - w * 0.030, py - h * 0.022,
                w * 0.060, h * 0.044, fill=(96, 146, 206))
    sh.dot(px, py - h * 0.050, w * 0.010, RED_BRIGHT)


def art_coalition(sh, x, y, w, h):
    """Benches filling up: a coalition assembling seat by seat."""
    _frame(sh, x, y, w, h, (210, 228, 230))
    sh.rect(x, y + h * 0.78, w, h * 0.22, fill=(182, 206, 210))
    rows = 3
    for r in range(rows):
        yy = y + h * (0.30 + r * 0.20)
        n = 7 + r
        for c in range(n):
            cx = x + w * (0.5 - (n - 1) * 0.052 + c * 0.104)
            filled = (r * 9 + c) % 3 != 2
            col = (36, 62, 108) if filled else (156, 170, 186)
            sh.dot(cx, yy, w * 0.026, col)
            sh.rect(cx - w * 0.024, yy + h * 0.030, w * 0.048, h * 0.055,
                    fill=col)
        sh.rect(x + w * 0.10, yy + h * 0.095, w * 0.80, h * 0.030,
                fill=(118, 96, 70))
    # the rostrum the chamber faces
    sh.rect(x + w * 0.42, y + h * 0.06, w * 0.16, h * 0.11, fill=RED_BRIGHT)
    sh.rect(x + w * 0.485, y + h * 0.17, w * 0.030, h * 0.07,
            fill=(150, 44, 40))
    sh.rect(x + w * 0.44, y + h * 0.24, w * 0.12, h * 0.025,
            fill=(150, 44, 40))


def art_sabotage(sh, x, y, w, h):
    """Plant silhouette, severed cable, warning triangle."""
    _frame(sh, x, y, w, h, (26, 36, 58))
    sh.rect(x, y + h * 0.80, w, h * 0.20, fill=(36, 48, 74))
    # works
    for i, (bx, bw_, bh_) in enumerate([(0.06, 0.16, 0.34), (0.24, 0.13, 0.46),
                                        (0.39, 0.10, 0.28)]):
        sh.rect(x + w * bx, y + h * (0.80 - bh_), w * bw_, h * bh_,
                fill=(52, 68, 100))
        for k in range(3):
            sh.rect(x + w * (bx + 0.02 + k * 0.035), y + h * (0.84 - bh_),
                    w * 0.022, h * 0.045, fill=(238, 204, 116))
    # chimney + plume
    sh.rect(x + w * 0.56, y + h * 0.34, w * 0.055, h * 0.46, fill=(66, 84, 118))
    for i, (ox, oy, r) in enumerate([(0.60, 0.26, 0.042), (0.655, 0.19, 0.034),
                                     (0.70, 0.14, 0.026)]):
        sh.dot(x + w * ox, y + h * oy, w * r, (62, 78, 112))
    # cable, cut
    sh.line(x + w * 0.00, y + h * 0.66, x + w * 0.40, y + h * 0.60,
            fill=(206, 200, 184), width=1.1)
    sh.line(x + w * 0.52, y + h * 0.63, x + w * 1.00, y + h * 0.70,
            fill=(206, 200, 184), width=1.1)
    for r, c in [(0.055, (118, 52, 44)), (0.032, RED_BRIGHT)]:
        sh.dot(x + w * 0.46, y + h * 0.615, w * r, c)
    # warning triangle
    tx, ty, ts = x + w * 0.80, y + h * 0.28, w * 0.085
    sh.poly([(tx, ty - ts), (tx - ts * 0.92, ty + ts * 0.70),
             (tx + ts * 0.92, ty + ts * 0.70)], fill=GOLD)
    sh.rect(tx - ts * 0.09, ty - ts * 0.42, ts * 0.18, ts * 0.70,
            fill=(26, 36, 58))
    sh.dot(tx, ty + ts * 0.46, ts * 0.11, (26, 36, 58))


def art_investigation(sh, x, y, w, h):
    """Party building under a magnifier."""
    _frame(sh, x, y, w, h, (182, 56, 48))
    sh.rect(x, y + h * 0.80, w, h * 0.20, fill=(150, 44, 38))
    # building
    bx, bw = x + w * 0.16, w * 0.52
    sh.rect(bx, y + h * 0.34, bw, h * 0.46, fill=(238, 232, 216))
    sh.poly([(bx - w * 0.04, y + h * 0.34), (bx + bw / 2, y + h * 0.16),
             (bx + bw + w * 0.04, y + h * 0.34)], fill=(248, 244, 232))
    for c in range(5):
        sh.rect(bx + bw * (0.10 + c * 0.18), y + h * 0.42, bw * 0.09,
                h * 0.38, fill=(196, 188, 170))
    sh.dot(bx + bw / 2, y + h * 0.235, w * 0.028, GOLD)
    # magnifier
    mx, my, mr = x + w * 0.70, y + h * 0.44, w * 0.155
    sh.ellipse(mx - mr, my - mr, mr * 2, mr * 2, fill=(252, 248, 236))
    sh.ellipse(mx - mr, my - mr, mr * 2, mr * 2, outline=(32, 40, 60),
               width=1.6)
    sh.line(mx + mr * 0.72, my + mr * 0.72, mx + mr * 1.55, my + mr * 1.55,
            fill=(32, 40, 60), width=2.0)
    sh.rect(mx - mr * 0.40, my - mr * 0.34, mr * 0.80, mr * 0.16,
            fill=(182, 56, 48))
    sh.rect(mx - mr * 0.40, my - mr * 0.06, mr * 0.56, mr * 0.16,
            fill=(182, 56, 48))
    sh.rect(mx - mr * 0.40, my + mr * 0.22, mr * 0.68, mr * 0.16,
            fill=(182, 56, 48))


def art_departure(sh, x, y, w, h):
    """Aircraft leaving, stamped passport below."""
    _frame(sh, x, y, w, h, (38, 62, 112))
    # clouds
    for ox, oy, r in [(0.16, 0.26, 0.055), (0.22, 0.24, 0.042),
                      (0.80, 0.18, 0.048), (0.86, 0.21, 0.036)]:
        sh.dot(x + w * ox, y + h * oy, w * r, (62, 90, 146))
    # plane
    cx, cy = x + w * 0.46, y + h * 0.33
    sh.poly([(cx - w * 0.22, cy), (cx + w * 0.20, cy - h * 0.055),
             (cx + w * 0.26, cy), (cx + w * 0.20, cy + h * 0.055)],
            fill=(240, 236, 222))
    sh.poly([(cx - w * 0.02, cy), (cx - w * 0.13, cy - h * 0.20),
             (cx - w * 0.03, cy - h * 0.02)], fill=(206, 200, 184))
    sh.poly([(cx - w * 0.02, cy), (cx - w * 0.13, cy + h * 0.20),
             (cx - w * 0.03, cy + h * 0.02)], fill=(222, 216, 200))
    sh.poly([(cx - w * 0.20, cy), (cx - w * 0.26, cy - h * 0.11),
             (cx - w * 0.17, cy - h * 0.01)], fill=(206, 200, 184))
    # contrail
    for i in range(5):
        sh.hrule(x + w * (0.02 + i * 0.055), cy + h * 0.005,
                 w * 0.035, fill=(96, 124, 176), width=0.8)
    # passport
    px, py, pw, ph = x + w * 0.58, y + h * 0.54, w * 0.33, h * 0.40
    sh.rect(px, py, pw, ph, fill=(126, 44, 48))
    sh.rect(px + pw * 0.10, py + ph * 0.14, pw * 0.80, ph * 0.10,
            fill=(214, 182, 110))
    sh.dot(px + pw * 0.50, py + ph * 0.52, pw * 0.16, (214, 182, 110))
    sh.rect(px + pw * 0.18, py + ph * 0.80, pw * 0.64, ph * 0.08,
            fill=(214, 182, 110))


def art_hostage(sh, x, y, w, h):
    """Colonial waterfront under a cordon line."""
    _frame(sh, x, y, w, h, (236, 206, 158))
    sh.rect(x, y, w, h * 0.46, fill=(132, 186, 206))
    sh.rect(x, y + h * 0.78, w, h * 0.22, fill=(74, 138, 162))
    # old town facades
    cols = [(226, 176, 120), (212, 142, 118), (238, 206, 150), (196, 160, 130),
            (230, 186, 140), (208, 170, 112)]
    for i in range(6):
        bx = x + w * (0.04 + i * 0.158)
        bh = h * (0.30 + 0.055 * ((i * 3) % 4))
        sh.rect(bx, y + h * 0.78 - bh, w * 0.135, bh, fill=cols[i])
        sh.rect(bx, y + h * 0.78 - bh, w * 0.135, h * 0.026,
                fill=(168, 96, 78))
        for r in range(2):
            sh.rect(bx + w * 0.030, y + h * 0.80 - bh + h * (0.055 + r * 0.085),
                    w * 0.028, h * 0.052, fill=(92, 74, 66))
            sh.rect(bx + w * 0.078, y + h * 0.80 - bh + h * (0.055 + r * 0.085),
                    w * 0.028, h * 0.052, fill=(92, 74, 66))
    # cordon tape
    sh.rect(x, y + h * 0.50, w, h * 0.085, fill=GOLD)
    for i in range(9):
        sh.poly([(x + w * (i * 0.118), y + h * 0.50),
                 (x + w * (i * 0.118 + 0.045), y + h * 0.50),
                 (x + w * (i * 0.118 + 0.018), y + h * 0.585),
                 (x + w * (i * 0.118 - 0.027), y + h * 0.585)],
                fill=(40, 44, 54))


def art_detonation(sh, x, y, w, h):
    """Blast rings over a bermed storage pit."""
    _frame(sh, x, y, w, h, (32, 42, 46))
    sh.rect(x, y + h * 0.72, w, h * 0.28, fill=(74, 72, 56))
    # berm
    sh.poly([(x + w * 0.16, y + h * 0.78), (x + w * 0.34, y + h * 0.56),
             (x + w * 0.66, y + h * 0.56), (x + w * 0.84, y + h * 0.78)],
            fill=(104, 98, 74))
    sh.rect(x + w * 0.42, y + h * 0.60, w * 0.16, h * 0.18, fill=(54, 54, 46))
    # rings
    cx, cy = x + w * 0.50, y + h * 0.50
    for i, r in enumerate([0.46, 0.36, 0.26]):
        sh.ellipse(cx - w * r, cy - h * r * 0.78, w * r * 2, h * r * 1.56,
                   outline=(118, 128, 120), width=0.7)
    # fireball
    for r, c in [(0.155, (134, 58, 40)), (0.110, RED_BRIGHT),
                 (0.070, GOLD), (0.034, (250, 240, 200))]:
        sh.dot(cx, cy, w * r, c)
    # debris
    import math
    for ang in [20, 55, 110, 150, 205, 250, 300, 335]:
        a = math.radians(ang)
        sh.line(cx + math.cos(a) * w * 0.17, cy + math.sin(a) * w * 0.17,
                cx + math.cos(a) * w * 0.27, cy + math.sin(a) * w * 0.27,
                fill=GOLD, width=0.8)
    # hazard placard
    sh.poly([(x + w * 0.86, y + h * 0.20), (x + w * 0.95, y + h * 0.29),
             (x + w * 0.86, y + h * 0.38), (x + w * 0.77, y + h * 0.29)],
            fill=(214, 70, 52))


def art_orange_day(sh, x, y, w, h):
    """Sixteen marks and a ribbon: the day against violence toward women."""
    _frame(sh, x, y, w, h, (226, 124, 44))
    # sixteen days as a bar of marks
    for i in range(16):
        sh.rect(x + w * (0.055 + i * 0.056), y + h * 0.80, w * 0.030,
                h * 0.095, fill=(252, 240, 220) if i < 1 else (198, 98, 32))
    # ribbon: a thick loop with two crossing tails
    cx, cy = x + w * 0.50, y + h * 0.345
    lw = w * 0.085
    rx, ry = w * 0.115, h * 0.195
    IVORY = (252, 240, 220)
    sh.ellipse(cx - rx, cy - ry, rx * 2, ry * 2, outline=IVORY,
               width=max(1.0, lw * 0.52))
    # knock the bottom of the loop out so the tails read as crossing over
    sh.poly([(cx - rx * 1.25, cy + ry * 0.45), (cx + rx * 1.25, cy + ry * 0.45),
             (cx + rx * 1.25, cy + ry * 1.45), (cx - rx * 1.25, cy + ry * 1.45)],
            fill=(226, 124, 44))
    # two tails, crossing just under the loop
    sh.poly([(cx - rx * 0.78, cy + ry * 0.18), (cx - rx * 0.16, cy + ry * 0.30),
             (cx + rx * 1.05, cy + ry * 2.25), (cx + rx * 0.40, cy + ry * 2.32)],
            fill=IVORY)
    sh.poly([(cx + rx * 0.78, cy + ry * 0.18), (cx + rx * 0.16, cy + ry * 0.30),
             (cx - rx * 1.05, cy + ry * 2.25), (cx - rx * 0.40, cy + ry * 2.32)],
            fill=IVORY)

    # silhouetted figures
    for i, ox in enumerate([0.10, 0.19, 0.81, 0.90]):
        fx = x + w * ox
        sh.dot(fx, y + h * 0.46, w * 0.030, (150, 66, 20))
        sh.poly([(fx - w * 0.045, y + h * 0.80), (fx - w * 0.028, y + h * 0.53),
                 (fx + w * 0.028, y + h * 0.53), (fx + w * 0.045, y + h * 0.80)],
                fill=(150, 66, 20))


# ----------------------------------------------------------------------------
# Stat pictograms -- 14 x 14 marks that sit beside each headline figure
# ----------------------------------------------------------------------------

def g_helmet(sh, x, y, u, c):
    """A combat helmet: the war-dead count."""
    sh.d.pieslice([S(x), S(y + u * 0.10), S(x + u), S(y + u * 0.98)],
                  180, 360, fill=c)
    sh.rect(x - u * 0.06, y + u * 0.52, u * 1.12, u * 0.14, fill=c)
    sh.rect(x + u * 0.42, y + u * 0.02, u * 0.16, u * 0.16, fill=c)


def g_containers(sh, x, y, u, c):
    """Stacked boxes: the tariff list."""
    for r in range(2):
        for k in range(3):
            if r == 1 and k == 2:
                continue
            sh.rect(x + k * u * 0.345, y + u * 0.34 + r * u * 0.33,
                    u * 0.30, u * 0.28, fill=c)


def g_downarrow(sh, x, y, u, c):
    """A falling index."""
    sh.line(x + u * 0.06, y + u * 0.18, x + u * 0.62, y + u * 0.66, c, 1.5)
    sh.line(x + u * 0.62, y + u * 0.66, x + u * 0.94, y + u * 0.34, c, 1.5)
    sh.poly([(x + u * 0.94, y + u * 0.92), (x + u * 0.66, y + u * 0.56),
             (x + u * 1.00, y + u * 0.50)], fill=c)


def g_rocket(sh, x, y, u, c):
    """A crewed launch."""
    sh.poly([(x + u * 0.50, y), (x + u * 0.30, y + u * 0.34),
             (x + u * 0.70, y + u * 0.34)], fill=c)
    sh.rect(x + u * 0.32, y + u * 0.32, u * 0.36, u * 0.40, fill=c)
    sh.poly([(x + u * 0.32, y + u * 0.58), (x + u * 0.12, y + u * 0.84),
             (x + u * 0.32, y + u * 0.76)], fill=c)
    sh.poly([(x + u * 0.68, y + u * 0.58), (x + u * 0.88, y + u * 0.84),
             (x + u * 0.68, y + u * 0.76)], fill=c)
    sh.poly([(x + u * 0.38, y + u * 0.72), (x + u * 0.62, y + u * 0.72),
             (x + u * 0.50, y + u * 1.02)], fill=c)


def g_treaty(sh, x, y, u, c):
    """A sealed document: the Pacific pledge."""
    sh.rect(x + u * 0.16, y + u * 0.06, u * 0.68, u * 0.74, fill=c)
    for i in range(3):
        sh.hrule(x + u * 0.28, y + u * (0.22 + i * 0.15), u * 0.44,
                 fill=(246, 241, 229), width=1.0)
    sh.dot(x + u * 0.50, y + u * 0.86, u * 0.17, c)


def g_orbit(sh, x, y, u, c):
    """A moonlet on a dashed orbit."""
    import math
    for k in range(16):
        if k % 2:
            continue
        a0 = math.radians(k * 22.5)
        a1 = math.radians((k + 1) * 22.5)
        sh.line(x + u * 0.5 + math.cos(a0) * u * 0.48,
                y + u * 0.5 + math.sin(a0) * u * 0.44,
                x + u * 0.5 + math.cos(a1) * u * 0.48,
                y + u * 0.5 + math.sin(a1) * u * 0.44, c, 0.9)
    sh.dot(x + u * 0.5, y + u * 0.5, u * 0.17, c)
    sh.dot(x + u * 0.98, y + u * 0.5, u * 0.10, c)


STAT_GLYPHS = [g_helmet, g_containers, g_downarrow, g_rocket, g_treaty,
               g_orbit]


# ----------------------------------------------------------------------------
# The day's record.  Every entry is auditable: dateline, certainty, sources.
# ----------------------------------------------------------------------------

HEROES = [
    dict(
        n=1, chip="AI ROUT WIDENS", tag="TAIEX −6%",
        kicker="TAIPEI · SEOUL · TOKYO · MARKETS",
        region="ASIA-PACIFIC", cert="REPORTED",
        head="Asia's AI trade cracks as Taiex sheds 6%",
        text="Taiwan's Taiex tumbled more than 6% as TSMC sank 8.1% and "
             "MediaTek 10%. Seoul's Kospi lost 5.6% to 4,725.84, Samsung "
             "−9.1%; the Nikkei fell 3.6% to 56,502.97 with SoftBank "
             "−16.1%. Hong Kong bucked it, +1%. Relief at Jensen Huang's "
             "return to Nvidia is tempered by governance questions.",
        src="(AP, Reuters)", art=art_market_rout, ll=(121.5, 25.0),
    ),
    dict(
        n=2, chip="LEAKED REGISTRY", tag="490,334",
        kicker="MOSCOW · LONDON · WAR DEAD",
        region="EUROPE", cert="REPORTED",
        head="Russia's own records show almost 490,000 war dead",
        text="BBC Russian and Mediazona matched a leak of more than 11m "
             "Rosstat death records, 2021 to September 2026, and count "
             "490,334 soldiers killed since February 2022 — 425,174 "
             "explicitly tied to military activity. Rosstat admits a "
             "cyber-attack but denies protected data left its systems.",
        src="(BBC Russian, Mediazona)", art=art_leaked_files,
        ll=(37.6, 55.8),
    ),
    dict(
        n=3, chip="FIRST FOR PAKISTAN", tag="00:18 UTC",
        kicker="JIUQUAN, CHINA · SPACE",
        region="ASIA-PACIFIC", cert="REPORTED",
        head="Shenzhou-24 carries a Pakistani into orbit",
        text="A Long March-2F lifted off at 00:18 UTC (08:18 Beijing) with "
             "commander Tang Hongbo, engineer Wu Yi and Muhammad Zeeshan "
             "Ali, 40, a former fighter pilot and the first foreigner on a "
             "Chinese crewed flight. He flies as payload specialist to "
             "Tiangong for five to ten days, under a 2025 accord.",
        src="(Reuters, Xinhua, Dawn)", art=art_rocket, ll=(100.3, 41.1),
    ),
]

CARDS = [
    dict(n=4, chip="PORT BOMBED", tag="RED SEA",
         kicker="HODEIDAH, YEMEN · WAR", region="MIDDLE EAST",
         cert="REPORTED",
         head="Coalition bombs Hodeidah port",
         text="Saudi-led jets hit the port's “operational capabilities” "
              "plus targets in Saada and Amran, after civilians were warned "
              "off. Houthis had threatened Jeddah.",
         src="(Al Jazeera, Arab News)", art=art_port_strike, ll=(42.95, 14.8)),
    dict(n=5, chip="2 DEAD, 48 HURT", tag="NEW FRONT",
         kicker="KYIV, UKRAINE · WAR", region="EUROPE", cert="REPORTED",
         head="Russian strike kills two as Kyiv explains Libya raid",
         text="Overnight missiles killed two and wounded 48. Kyiv set out its "
              "account of the sea-drone attack on a Russian corvette at "
              "Benghazi — a Mediterranean front.",
         src="(AP, Reuters)", art=art_strike_block, ll=(30.5, 50.45)),
    dict(n=6, chip="16 ECONOMIES", tag="SOURCES",
         kicker="WASHINGTON · TRADE", region="AMERICAS", cert="REPORTED",
         head="US readies subsidy tariffs on 16 economies",
         text="A Section 301 finding would hit China, the EU, Japan, Korea, "
              "Taiwan, India and ten more, replacing duties the Supreme Court "
              "struck down. China faces the steepest rates.",
         src="(AP sources)", art=art_tariffs, ll=(-77.0, 38.9)),
    dict(n=7, chip="A$740M", tag="NO FOREIGN BASE",
         kicker="CANBERRA · PACIFIC", region="OCEANIA", cert="REPORTED",
         head="Australia and Solomons sign a China-shaped treaty",
         text="Canberra becomes “primary security partner”; no foreign "
              "base, and consultation on critical infrastructure. A$740m over "
              "ten years. Sogavare attacks the fast-track.",
         src="(AFP, ABC)", art=art_treaty, ll=(149.1, -35.3)),
    dict(n=8, chip="FIRST CLOSE-UPS", tag="TONIGHT",
         kicker="DIDYMOS SYSTEM · SPACE", region="WORLD",
         cert="FORECAST",
         head="Hera reaches the asteroid NASA punched",
         text="ESA's probe is on station at Dimorphos, the 151 m moonlet DART "
              "hit in 2022, shortening its orbit by 33 minutes. First "
              "close-ups were due to be shown this evening.",
         src="(ESA)", art=art_asteroid, ll=None),
    dict(n=9, chip="FIRST PARTNER", tag="COALITION",
         kicker="JERUSALEM · POLITICS", region="MIDDLE EAST",
         cert="REPORTED",
         head="Eisenkot lands his first coalition partner",
         text="The former chief of staff secured an opening partner in his "
              "bid to assemble a governing majority, the first hard number in "
              "a fragmented post-election Knesset.",
         src="(Al Jazeera)", art=art_coalition, ll=(35.2, 31.8)),
    dict(n=10, chip="SABOTAGE WARNING", tag="ADVISORY",
         kicker="LONDON · SECURITY", region="EUROPE", cert="REPORTED",
         head="Britain tells firms aiding Ukraine to brace",
         text="Officials warned UK companies supplying Ukraine to expect "
              "Russian sabotage attempts against plant, logistics and "
              "undersea or land cable infrastructure.",
         src="(BBC, Al Jazeera)", art=art_sabotage, ll=(-0.1, 51.5)),
    dict(n=11, chip="POLITBURO", tag="INVESTIGATED",
         kicker="SHANGHAI · CHINA", region="ASIA-PACIFIC",
         cert="REPORTED",
         head="China investigates Shanghai's party chief",
         text="Chen Jining, a Politburo member and party secretary of China's "
              "financial capital, is under investigation — among the most "
              "senior figures taken in years.",
         src="(AP, Xinhua)", art=art_investigation, ll=(121.5, 31.2)),
    dict(n=12, chip="CASE CLOSED", tag="LEFT US",
         kicker="MADRID · MIGRATION", region="AMERICAS", cert="REPORTED",
         head="Abrego Garcia leaves the US for Spain",
         text="Kilmar Abrego Garcia, whose mistaken deportation to El "
              "Salvador became a flashpoint, departed voluntarily for Spain, "
              "ending a long legal fight.",
         src="(AP, BBC)", art=art_departure, ll=(-3.7, 40.4)),
    dict(n=13, chip="HOSTAGES", tag="TOURIST CITY",
         kicker="CARTAGENA, COLOMBIA · CRIME", region="AMERICAS",
         cert="REPORTED",
         head="Armed men seize hostages in Cartagena",
         text="Gunmen took hostages in one of Colombia's foremost tourist "
              "cities, days after a bomb in a central city wounded 23 as "
              "violence moves into urban centres.",
         src="(AP)", art=art_hostage, ll=(-75.5, 10.4)),
    dict(n=14, chip="4 TONNES", tag="SCHEDULED",
         kicker="BURLINGTON, IOWA · US", region="AMERICAS",
         cert="FORECAST",
         head="Army to blow up a lead azide stockpile",
         text="More than four tonnes of unstable primary explosive were set "
              "for controlled detonation. “This could be apocalyptic,” "
              "one resident told the BBC.",
         src="(AP, BBC, Al Jazeera)", art=art_detonation, ll=(-91.1, 40.8)),
    dict(n=15, chip="16 DAYS BEGIN", tag="25 NOV",
         kicker="WORLDWIDE · UN DAY", region="WORLD", cert="REPORTED",
         head="The day the world counts violence against women",
         text="The UN day opening the 16 Days campaign landed as a rights "
              "group reported 28 women and girls abducted fleeing Blue Nile "
              "fighting, and South Africa reckoned with a wave of killings.",
         src="(UN, allAfrica, BBC)", art=art_orange_day, ll=(34.0, 11.5)),
]

# Secondary wire budget -- one line each, numbered on from the cards.
ALSO = [
    ("EUROPE", "ICC president thanks Japan for an early 2027 payment as US "
               "sanctions squeeze the court. (AP)"),
    ("EUROPE", "Slovak MPs approve Fico's plan to scrap postal voting from "
               "abroad. (AP)"),
    ("EUROPE", "Spain's campaign closes with conservatives and the far right "
               "pressing Sanchez. (AP)"),
    ("EUROPE", "Russia backs tax rises as a 2027 budget lifts military "
               "spending. (AP)"),
    ("EUROPE", "Two arrested over a suspected burglary at William and Kate's "
               "country home. (AP)"),
    ("ASIA-PACIFIC", "Seoul subway strike averted: a pre-dawn wage deal keeps "
                     "lines 1–8 running. (SBS)"),
    ("ASIA-PACIFIC", "A blast at a Hanoi hot-pot restaurant kills six and "
                     "injures more than a dozen. (AP)"),
    ("ASIA-PACIFIC", "Bangladesh lifts the garment minimum wage after weeks "
                     "of protests. (AP)"),
    ("ASIA-PACIFIC", "Malaysia Airlines' parent to buy 10 Boeing Dreamliners, "
                     "with options for six. (AP)"),
    ("ASIA-PACIFIC", "Hasina says she will return to Bangladesh from exile on "
                     "16 December. (AP)"),
    ("ASIA-PACIFIC", "North Korea orders a Swiss diplomat out and demands the "
                     "new office shut. (AP)"),
    ("ASIA-PACIFIC", "Russian military aircraft skirt Korean airspace; Moscow "
                     "calls the flight planned. (SBS)"),
    ("ASIA-PACIFIC", "Malaysia to repatriate 6,803 more Myanmar nationals "
                     "despite an ICJ ruling. (AP)"),
    ("OCEANIA", "Australia set to pass a digital duty-of-care law, fines to "
                "5% of global revenue. (AP)"),
    ("OCEANIA", "Sydney policeman Beau Lamarre convicted of a double murder. "
                "(BBC)"),
    ("AMERICAS", "Shein to pay $100m to settle FTC allegations of deceptive "
                 "practices. (AP)"),
    ("AMERICAS", "A federal grand jury indicts Thomas Markle over child sex "
                 "abuse material. (AP, BBC)"),
    ("AMERICAS", "An unclassified CIA system was breached in a cyberattack, a "
                 "source says. (AP)"),
    ("AMERICAS", "WHO's chief urges an end to the US fuel blockade on Cuba. "
                 "(Al Jazeera)"),
    ("AFRICA", "Dozens killed in fresh land-dispute attacks in Nigeria's "
               "Niger state. (AP)"),
    ("AFRICA", "Nollywood veteran Pete Edochie dies at 79. (BBC)"),
    ("AFRICA", "A court is to rule on Ramaphosa's bid to set aside the "
               "'Farmgate' report. (BBC)"),
    ("WORLD", "UNAIDS warns a $4.3bn funding gap could reverse progress on "
              "HIV. (allAfrica)"),
    ("WORLD", "Astronomers report a quasar formed just 630m years after the "
              "Big Bang. (AP)"),
    ("WORLD", "Gaza's children face threats unmatched elsewhere, a new report "
              "says. (AP)"),
    ("MIDDLE EAST", "Syria's new rulers struggle to absorb foreign fighters "
                    "as IS fears linger. (AP)"),
    ("MIDDLE EAST", "Photographs show UN peacekeepers amid the wreckage of "
                    "south Lebanon. (AP)"),
    ("AMERICAS", "Bukele says three Salvadoran soldiers died fighting gangs "
                 "in Haiti. (AP)"),
    ("EUROPE", "A Turkish military helicopter crashes in training, killing "
               "five crew. (AP)"),
    ("EUROPE", "A vast new London Museum opens, from the Romans to Banksy. "
               "(AP)"),
    ("AFRICA", "South Africa convicts a Zimbabwean who tried to fight for "
               "Russia. (AP)"),
    ("ASIA-PACIFIC", "A year after Hong Kong's deadly fire, survivors still "
                     "press for justice. (AP)"),
]

# Keep the wire list in the same order as the region bar above it.
ALSO = sorted(ALSO, key=lambda it: REGION_ORDER.index(it[0]))

STATS = [
    ("490,334", "Russian soldiers dead in leaked files"),
    ("16", "economies facing new US subsidy tariffs"),
    ("6%", "fall in Taiwan's Taiex as AI selling spreads"),
    ("3", "aboard Shenzhou-24, one a first for Pakistan"),
    ("A$740m", "Australia's ten-year pledge to Solomons"),
    ("33 min", "orbit shift Hera arrived to measure"),
]

TIMELINE = [
    ("00:18", "Shenzhou-24 lifts off, Jiuquan"),
    ("00:30", "Tokyo opens; Nikkei heads for −3.6%"),
    ("01:00", "Taipei opens; Taiex slides past −6%"),
    ("06:30", "Kospi closes −5.6% at 4,725.84"),
    ("15:00", "Ghana's debt buyback window shuts"),
    ("18:00", "ESA due to show Hera's first close-ups"),
]

DATE_CHECK = (
    "Left out as other days' news: the Benghazi corvette strike (Sun 22 Nov) "
    "· Nvidia's reinstatement of Jensen Huang (Mon 23) · Huawei's New "
    "York verdict, the Landmine Monitor's 6,929 casualties, the Riyadh tower "
    "drone that hurt 11, and Israel's killing of Hamas security chief Naim Abu "
    "Nahal (all Tue 24). Today's falls are Wednesday's Asian sessions."
)

SOURCES_LINE = (
    "Sources: AP, Reuters, BBC, BBC Russian, Mediazona, Al Jazeera, AFP, "
    "Xinhua, Dawn, SBS, ESA, allAfrica, Arab News and the wires named with "
    "each story. Pictures and map: original, drawn in code."
)

LEGEND_LINE = (
    "CERTAINTY:  REPORTED = carried by the day's wires  ·  CLAIM = one "
    "side's account, labelled as such  ·  FORECAST = scheduled, not yet "
    "happened when drawn"
)

# ----------------------------------------------------------------------------
# World map -- 72 x 36 coarse land mask, equirectangular, 5 deg per column
# ----------------------------------------------------------------------------

_ROWS = [
    [(12, 22), (24, 32), (39, 39), (48, 71)],                 # 78 N
    [(10, 24), (23, 32), (44, 71)],                           # 74 N
    [(3, 8), (9, 25), (22, 33), (37, 42), (42, 71)],          # 70 N
    [(2, 9), (10, 26), (22, 32), (32, 32), (36, 42), (42, 71)],
    [(1, 8), (9, 27), (24, 31), (35, 42), (42, 71)],           # 61 N
    [(1, 7), (8, 28), (35, 35), (36, 41), (41, 71)],           # 57 N
    [(7, 29), (34, 36), (37, 42), (42, 71)],                   # 53 N
    [(8, 29), (35, 43), (43, 70)],                             # 49 N
    [(8, 29), (34, 44), (44, 64), (66, 67)],                   # 45 N
    [(8, 29), (33, 37), (37, 44), (44, 63), (65, 67)],         # 40 N
    [(9, 28), (33, 36), (36, 40), (42, 46), (46, 63), (64, 66)],
    [(10, 27), (32, 42), (42, 47), (47, 52), (52, 63), (64, 65)],
    [(12, 26), (32, 43), (43, 48), (49, 53), (53, 63)],        # 28 N
    [(14, 25), (25, 27), (32, 44), (44, 48), (49, 54), (55, 60)],
    [(15, 24), (25, 28), (32, 45), (44, 47), (50, 54), (55, 61)],
    [(17, 24), (26, 28), (32, 46), (45, 47), (50, 53), (56, 61)],
    [(19, 23), (24, 30), (32, 47), (52, 52), (56, 61)],        # 11 N
    [(20, 23), (24, 31), (32, 47), (56, 59), (60, 62)],        # 7 N
    [(24, 34), (33, 46), (55, 62)],                            # 3 N
    [(25, 35), (33, 46), (55, 63), (64, 67)],                  # 1 S
    [(25, 36), (33, 45), (56, 64), (64, 68)],                  # 5 S
    [(24, 36), (33, 44), (57, 63), (65, 68)],                  # 10 S
    [(24, 36), (33, 44), (45, 46), (61, 68)],                  # 14 S
    [(24, 36), (33, 43), (45, 46), (59, 69)],                  # 18 S
    [(25, 36), (33, 42), (45, 46), (58, 70)],                  # 22 S
    [(25, 35), (34, 42), (58, 70)],                            # 26 S
    [(26, 34), (34, 41), (59, 69)],                            # 30 S
    [(26, 33), (35, 40), (60, 68)],                            # 35 S
    [(27, 32), (61, 65), (70, 71)],                            # 39 S
    [(27, 31), (62, 63), (70, 71)],                            # 43 S
    [(28, 31), (71, 71)],                                      # 47 S
    [(28, 31)],
    [(29, 31)],
    [(29, 30)],
    [],
    [],
]

MAP_COLS = 72
MAP_ROWS = 36
LAT_TOP = 80.0
LAT_STEP = 4.1667


def ll_to_cell(lon, lat):
    col = (lon + 180.0) / 5.0
    row = (LAT_TOP - lat) / LAT_STEP
    return col, row


# ----------------------------------------------------------------------------
# Composition
# ----------------------------------------------------------------------------

def chip(sh, x, y, w, h, label, color, fg=WHITE, size=6.2):
    sh.rect(x, y, w, h, fill=color)
    sh.text(x + 4.0, y + h / 2.0, label, cond(size, "Medium"), fg,
            anchor="lm", spacing=0.35)


def certainty_mark(sh, x, y, cert, size=5.4):
    """Right-aligned certainty flag; returns width used."""
    col = {"REPORTED": NAVY_SOFT, "CLAIM": RED, "FORECAST": GOLD}[cert]
    glyph = {"REPORTED": "⊠", "CLAIM": "⊠", "FORECAST": "⊠"}[cert]
    f = cond(size, "Medium")
    txt = glyph + " " + cert
    wdt = sh.tw(txt, f) + 0.35 * (len(txt) - 1)
    sh.text(x - wdt, y, txt, f, col, anchor="la", spacing=0.35)
    return wdt


# Fixed vertical plan for the sheet (1024 tall).  Keeping these explicit
# stops one overlong headline from cascading into the block below.
Y_MAST     = 4
Y_SUB      = 63
Y_RULE1    = 79
Y_STATS    = 84
H_STATS    = 48
Y_REGION   = 136
H_REGION   = 17
Y_TIME     = 157
H_TIME     = 17
Y_HERO     = 181
H_HERO     = 218
Y_ROW1     = 404
Y_ROW2     = 566
H_ROW      = 162
Y_BOTHDR   = 731
Y_BOTTOM   = 747
H_MAP      = 152
Y_DATECHK  = 906
H_DATECHK  = 36
Y_FOOT     = 948


def build():
    sh = Sheet()

    # ---- paper tone: a faint top-to-bottom warm gradient ------------------
    for i in range(H):
        t = i / float(H)
        c = (int(246 - 5 * t), int(241 - 6 * t), int(229 - 7 * t))
        sh.d.line([(0, S(i)), (S(W), S(i))], fill=c, width=SCALE)

    # ======================= MASTHEAD =====================================
    f_mast = sh.fit("Wednesday 25 November 2026",
                    lambda s: display(s, "Bold"), 44, 30, CW - 8, 1)
    sh.text(W / 2.0, Y_MAST, "Wednesday 25 November 2026", f_mast, NAVY,
            anchor="ma")

    sub = ("Asia's AI trade cracks · Leaked files put Russia's war dead "
           "near 490,000 · A Pakistani rides Shenzhou-24 to Tiangong")
    f_sub = sh.fit(sub, lambda s: display_it(s, "Medium"), 11.5, 8.0,
                   CW - 10, 1)
    sh.text(W / 2.0, Y_SUB, sub, f_sub, RED, anchor="ma")

    sh.rect(M, Y_RULE1, CW, 2.2, fill=NAVY)

    # ======================= STAT STRIP ===================================
    cellw = CW / 6.0
    for i, (num, cap) in enumerate(STATS):
        cx = M + cellw * i
        if i:
            sh.line(cx, Y_STATS + 5, cx, Y_STATS + H_STATS - 7, fill=RULE,
                    width=0.6)
        col = RED if i % 2 == 0 else NAVY
        f_n = sh.fit(num, lambda s: display(s, "Bold"), 23, 12,
                     cellw - 30, 1)
        numw = sh.tw(num, f_n)
        nx = cx + cellw / 2.0 + 9
        sh.text(nx, Y_STATS + 1, num, f_n, col, anchor="ma")
        gu = 13.0
        STAT_GLYPHS[i](sh, nx - numw / 2.0 - gu - 5.0, Y_STATS + 6.5, gu, col)
        f_c = sans(5.5, "Medium")
        lines = sh.wrap(cap, f_c, cellw - 10)[:2]
        y0 = Y_STATS + H_STATS - 8 - 7.0 * (len(lines) - 1)
        for k, ln in enumerate(lines):
            sh.text(cx + cellw / 2.0, y0 + k * 7.0, ln, f_c, GREY,
                    anchor="ma")
    sh.hrule(M, Y_STATS + H_STATS, CW, fill=NAVY, width=0.8)

    # ======================= REGION TALLY =================================
    counts = {r: 0 for r in REGION_ORDER}
    for s in HEROES + CARDS:
        counts[s["region"]] += 1
    for r, _ in ALSO:
        counts[r] += 1
    total = sum(counts.values())

    x = M
    for i, r in enumerate(REGION_ORDER):
        bw = CW * (counts[r] / float(total))
        if i == len(REGION_ORDER) - 1:
            bw = M + CW - x
        sh.rect(x, Y_REGION, bw - 1.2, H_REGION, fill=REGION_COLOR[r])
        label = "%s %d" % (r, counts[r])
        f_r = cond(7.0, "Medium")
        if sh.tw(label, f_r) + 6 > bw:
            label = "%s %d" % (r.split("-")[0].split(" ")[0], counts[r])
            f_r = cond(6.0, "Medium")
        sh.text(x + (bw - 1.2) / 2.0, Y_REGION + H_REGION / 2.0, label, f_r,
                WHITE, anchor="mm", spacing=0.3)
        x += bw

    # ======================= UTC TIMELINE =================================
    sh.rect(M, Y_TIME, CW, H_TIME, fill=NAVY)
    mid = Y_TIME + H_TIME / 2.0
    sh.text(M + 6, mid, "THE DAY IN UTC", cond(6.6, "SemiBold"), GOLD,
            anchor="lm", spacing=0.5)
    tx = M + 80
    slot = ((M + CW - 6) - tx) / float(len(TIMELINE))
    f_t = cond(6.4, "Medium")
    f_e = sans(5.9, "Regular")
    for i, (t, ev) in enumerate(TIMELINE):
        cx = tx + slot * i
        sh.text(cx, mid, t, f_t, GOLD, anchor="lm")
        ex = cx + sh.tw(t, f_t) + 3.5
        ev2 = ev
        while sh.tw(ev2, f_e) > slot - (ex - cx) - 5 and len(ev2) > 6:
            ev2 = ev2[:-2]
        if ev2 != ev:
            ev2 += "…"
        sh.text(ex, mid, ev2, f_e, (214, 220, 232), anchor="lm")

    # ======================= HERO CARDS ===================================
    gut = 9
    hw = (CW - gut * 2) / 3.0
    chip_h = 13
    illo_h = 92

    for i, s in enumerate(HEROES):
        x = M + (hw + gut) * i
        yy = Y_HERO
        chip(sh, x, yy, hw * 0.63, chip_h, s["chip"],
             REGION_COLOR[s["region"]])
        f_tag = cond(6.0, "SemiBold")
        tagw = sh.tw(s["tag"], f_tag) + 10
        sh.rect(x + hw - tagw, yy, tagw, chip_h, fill=PAPER_DEEP)
        sh.rect(x + hw - tagw, yy, tagw, chip_h, outline=NAVY, width=0.5)
        sh.text(x + hw - tagw / 2.0, yy + chip_h / 2.0, s["tag"], f_tag,
                NAVY, anchor="mm")
        yy += chip_h
        paint(sh, s["art"], x, yy, hw, illo_h)
        sh.rect(x, yy, hw, illo_h, outline=(198, 190, 174), width=0.5)
        sh.rect(x, yy + illo_h - 11, 12, 11, fill=(255, 255, 255))
        sh.text(x + 6, yy + illo_h - 5.5, str(s["n"]), cond(6.6, "SemiBold"),
                NAVY, anchor="mm")
        yy += illo_h + 4.5
        sh.text(x, yy, s["kicker"], cond(6.2, "Medium"), RED, anchor="la",
                spacing=0.3)
        certainty_mark(sh, x + hw, yy, s["cert"], 5.4)
        yy += 9
        sh.hrule(x, yy, hw, fill=NAVY, width=0.7)
        yy += 4.5
        f_h = sh.fit(s["head"], lambda t: display(t, "Bold"), 16.5, 11.0,
                     hw, 2)
        lines = sh.wrap(s["head"], f_h, hw)[:2]
        for k, ln in enumerate(lines):
            sh.text(x, yy + k * 17.5, ln, f_h, NAVY)
        yy += 17.5 * 2 + 3.5
        end = sh.para(x, yy, s["text"], body(7.1), hw, 9.4, INK,
                      max_lines=5, justify=True)
        sh.text(x, end + 0.5, s["src"], body_i(6.3), GREY)

    sh.hrule(M, Y_HERO + H_HERO, CW, fill=NAVY, width=0.9)

    # ======================= CARD ROWS ====================================
    cgut = 7
    cw = (CW - cgut * 5) / 6.0
    c_chip = 11
    c_illo = 60

    for row, ry in enumerate((Y_ROW1, Y_ROW2)):
        for i, s in enumerate(CARDS[row * 6:(row + 1) * 6]):
            x = M + (cw + cgut) * i
            yy = ry
            chip(sh, x, yy, cw, c_chip, s["chip"],
                 REGION_COLOR[s["region"]], size=5.5)
            yy += c_chip
            paint(sh, s["art"], x, yy, cw, c_illo)
            sh.rect(x, yy, cw, c_illo, outline=(198, 190, 174), width=0.5)
            sh.rect(x, yy + c_illo - 9, 10, 9, fill=(255, 255, 255))
            sh.text(x + 5, yy + c_illo - 4.5, str(s["n"]),
                    cond(5.8, "SemiBold"), NAVY, anchor="mm")
            f_tg = cond(5.2, "SemiBold")
            tgw = sh.tw(s["tag"], f_tg) + 6
            sh.rect(x + cw - tgw, yy, tgw, 9, fill=(252, 249, 240))
            sh.text(x + cw - tgw / 2.0, yy + 4.5, s["tag"], f_tg, NAVY,
                    anchor="mm")
            yy += c_illo + 3.5
            sh.text(x, yy, s["kicker"], cond(5.3, "Medium"), RED,
                    spacing=0.25)
            certainty_mark(sh, x + cw, yy, s["cert"], 4.6)
            yy += 7.5
            sh.hrule(x, yy, cw, fill=NAVY, width=0.6)
            yy += 4.0
            f_h = sh.fit(s["head"], lambda t: display(t, "Bold"), 10.5, 7.2,
                         cw, 3)
            lines = sh.wrap(s["head"], f_h, cw)[:3]
            for k, ln in enumerate(lines):
                sh.text(x, yy + k * 11.2, ln, f_h, NAVY)
            yy += 11.2 * 3 + 2.5
            end = sh.para(x, yy, s["text"], body(6.0), cw, 8.0, INK,
                          max_lines=4)
            sh.text(x, end + 0.4, s["src"], body_i(5.4), GREY)
        sh.hrule(M, ry + H_ROW - 8, CW,
                 fill=NAVY if row else RULE, width=0.9 if row else 0.7)

    # ======================= MAP + ALSO ===================================
    map_w = 346
    also_x = M + map_w + 16
    sh.text(M, Y_BOTHDR, "WHERE IT HAPPENED", cond(7.4, "SemiBold"), NAVY,
            spacing=0.6)
    sh.text(M + map_w, Y_BOTHDR + 1.6, "pins match story numbers",
            body_i(5.6), GREY, anchor="ra")
    hdr = "ALSO ON WEDNESDAY 25 NOVEMBER — %d MORE STORIES" % len(ALSO)
    sh.text(also_x, Y_BOTHDR, hdr, cond(7.4, "SemiBold"), NAVY, spacing=0.4)
    sh.hrule(M, Y_BOTHDR + 11, map_w, fill=NAVY, width=0.6)
    sh.hrule(also_x, Y_BOTHDR + 11, M + CW - also_x, fill=NAVY, width=0.6)

    # --- dot map -----------------------------------------------------------
    my = Y_BOTTOM
    sh.rect(M, my, map_w, H_MAP, fill=(239, 233, 218))
    sh.rect(M, my, map_w, H_MAP, outline=(212, 204, 188), width=0.5)
    cell = map_w / float(MAP_COLS)
    rcell = H_MAP / float(MAP_ROWS)
    dr = min(cell, rcell) * 0.36
    for r, spans in enumerate(_ROWS):
        for (a, b) in spans:
            for c in range(a, b + 1):
                sh.dot(M + (c + 0.5) * cell, my + (r + 0.5) * rcell, dr,
                       (140, 152, 166))

    # pins, with deterministic de-overlap
    placed = []
    pins = []
    for s in HEROES + CARDS:
        if not s["ll"]:
            continue
        col, row_ = ll_to_cell(s["ll"][0], s["ll"][1])
        pins.append((s["n"], M + (col + 0.5) * cell, my + (row_ + 0.5) * rcell))
    pins.sort(key=lambda p: (p[1], p[2]))
    R = 4.8
    for n, px, py in pins:
        ox, oy = px, py
        for _ in range(28):
            clash = [q for q in placed
                     if (q[0] - px) ** 2 + (q[1] - py) ** 2 < (R * 2.02) ** 2]
            if not clash:
                break
            qx, qy = clash[0]
            dx, dy = px - qx, py - qy
            if abs(dx) < 0.01 and abs(dy) < 0.01:
                dx, dy = 1.0, -1.0
            mag = (dx * dx + dy * dy) ** 0.5
            px += dx / mag * 1.6
            py += dy / mag * 1.6
            # never let a pin wander far from where the story happened
            ddx, ddy = px - ox, py - oy
            dd = (ddx * ddx + ddy * ddy) ** 0.5
            if dd > 7.0:
                px, py = ox + ddx / dd * 7.0, oy + ddy / dd * 7.0
                break
        px = min(max(px, M + R + 1), M + map_w - R - 1)
        py = min(max(py, my + R + 1), my + H_MAP - R - 10)
        placed.append((px, py))
        sh.dot(px, py, R + 1.2, (252, 248, 238))
        sh.dot(px, py, R, RED_BRIGHT)
        sh.text(px, py + 0.2, str(n), cond(5.6, "SemiBold"), WHITE,
                anchor="mm")
    sh.rect(M + 1, my + H_MAP - 10, map_w - 2, 9, fill=(246, 241, 229))
    sh.text(M + 4, my + H_MAP - 9, "Story 8 (Hera) is in orbit — not "
            "plotted. Equirectangular; dots are land.", body_i(5.3), GREY)

    # --- also-on columns ---------------------------------------------------
    col_gap = 13
    ncols = 2
    colw = (M + CW - also_x - col_gap * (ncols - 1)) / float(ncols)
    f_a = body(5.85)
    f_an = cond(6.1, "SemiBold")
    f_rb = body_b(5.85)
    per = (len(ALSO) + ncols - 1) // ncols
    for ci in range(ncols):
        cx = also_x + (colw + col_gap) * ci
        cy = my
        for k in range(per):
            idx = ci * per + k
            if idx >= len(ALSO):
                break
            region, txt = ALSO[idx]
            num = len(HEROES) + len(CARDS) + idx + 1
            col = REGION_COLOR[region]
            lead = "%d" % num
            sh.text(cx, cy, lead, f_an, col)
            lx = cx + sh.tw(lead, f_an) + 2.6
            rl = region.title().replace("Asia-Pacific", "Asia-Pac.")
            sh.text(lx, cy, rl + ":", f_rb, col)
            tx0 = lx + sh.tw(rl + ":", f_rb) + 2.4
            lines = sh.wrap(txt, f_a, colw - (tx0 - cx))
            if lines:
                sh.text(tx0, cy, lines[0], f_a, INK)
            cy += 7.5
            rest = " ".join(lines[1:])
            if rest:
                cy = sh.para(cx + 7, cy, rest, f_a, colw - 7, 7.5, INK,
                             max_lines=2)
            cy += 0.6

    # ======================= DATE CHECK ===================================
    sh.rect(M, Y_DATECHK, CW, H_DATECHK, fill=(250, 243, 232))
    sh.rect(M, Y_DATECHK, CW, H_DATECHK, outline=RED, width=1.0)
    sh.text(M + 8, Y_DATECHK + 7.5, "DATE CHECK", cond(7.2, "SemiBold"), RED,
            spacing=0.6)
    sh.para(M + 78, Y_DATECHK + 6.5, DATE_CHECK, body(5.9), CW - 90, 8.0,
            INK, max_lines=3)

    # ======================= FOOTER =======================================
    sh.hrule(M, Y_FOOT, CW, fill=RULE, width=0.6)
    sh.para(M, Y_FOOT + 4, SOURCES_LINE, body(5.5), CW, 7.4, GREY,
            max_lines=2)
    sh.text(W / 2.0, Y_FOOT + 24, LEGEND_LINE, cond(5.8, "Medium"), NAVY,
            anchor="ma", spacing=0.25)
    sh.text(W / 2.0, Y_FOOT + 36,
            "Drawn in code for make.fun · one sheet, one day · "
            "@cherry-vodka", body_i(5.4), GREY, anchor="ma")

    return sh.img


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/output/entry.png"
    d = os.path.dirname(out)
    if d:
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass

    big = build()
    img = big.resize((W, H), Image.LANCZOS)

    img.save(out, "PNG", optimize=True)

    # Stay under the 1 MiB ceiling; palette-reduce only if we must.
    limit = 1024 * 1024
    if os.path.getsize(out) > limit:
        for colors in (256, 192, 128):
            q = img.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT,
                                            dither=Image.NONE)
            q.save(out, "PNG", optimize=True)
            if os.path.getsize(out) <= limit:
                break

    print("wrote %s (%d bytes)" % (out, os.path.getsize(out)))


if __name__ == "__main__":
    main()
