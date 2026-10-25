#!/usr/bin/env python3
"""Generate Ground.svg: the rooftop level the player runs across.

The player stands on top of skyscrapers, so every collision block from
main.spx becomes a building: parapet at the collision height, facade with lit
windows falling away below, neon strips on the corners. The four pits are the
gaps between buildings, where the background city shows through.

Canvas is 12400x1000 with the costume pivot at (6200, 300), so image space maps
to world space as:

    imgX = worldX + 6200
    imgY = 300 - worldY          (world y=-208 -> img 508, y=-78 -> img 378)

Keep this table identical to main.spx (blockLeft/blockRight/blockTop); the
collision and the artwork must come from one source of truth.

Usage: python3 scripts/build-ground.py
"""
import os
import random

IMG_W, IMG_H = 12400, 1000
X_OFFSET = 6200
Y_ORIGIN = 300

BLOCK_LEFT = [-6600, -5400, -4750, -3950, -3080, -2350, -1450, -800, 120, 850,
              1450, 2200, 2920, 3900, 4700, 5600]
BLOCK_RIGHT = [-5400, -4750, -3950, -3480, -2350, -1450, -800, -200, 850, 1450,
               2200, 2920, 3500, 4700, 5250, 6600]
BLOCK_TOP = [-208, -118, -208, -78, -168, -208, -98, -208, -138, -208, -108,
             -208, -148, -208, -88, -208]

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "game", "assets", "sprites", "Ground", "Ground.svg")

FACADE = "#0a1320"
FACADE_DARK = "#070d17"
PARAPET = "#1b2f47"
EDGE = "#33587c"
CYAN = "#3fe0f0"
MAGENTA = "#ff2e7e"


def rect(x, y, w, h, fill, opacity=None):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{fill}"{o}/>'


def building(rnd, left, right, top):
    """One block: parapet + facade + windows + neon, from `top` down to the bottom."""
    x0 = max(0, left + X_OFFSET)
    x1 = min(IMG_W, right + X_OFFSET)
    w = x1 - x0
    if w <= 0:
        return []

    o = []
    # facade body
    o.append(rect(x0, top, w, IMG_H - top, FACADE))
    # parapet band, and the lit roof edge the player actually stands on
    o.append(rect(x0, top, w, 16, PARAPET))
    o.append(rect(x0, top, w, 4, CYAN, 0.55))
    o.append(rect(x0, top + 16, w, 3, "#060b14"))
    # corner edges
    o.append(rect(x0, top, 4, IMG_H - top, EDGE, 0.5))
    o.append(rect(x1 - 4, top, 4, IMG_H - top, EDGE, 0.5))
    # window grid
    cols = int((w - 40) // 34)
    rows = int((IMG_H - top - 60) // 52)
    for c in range(cols):
        wx = x0 + 24 + c * 34
        if wx + 12 > x1 - 12:
            break
        for r in range(rows):
            wy = top + 40 + r * 52
            roll = rnd.random()
            if roll > 0.20:
                col, alpha = "#122238", 1.0
            elif roll > 0.045:
                col, alpha = CYAN, 0.30
            else:
                col, alpha = MAGENTA, 0.30
            o.append(rect(wx, wy, 12, 20, col, alpha))
    # a neon tube down one corner of taller facades
    if w > 260 and rnd.random() < 0.7:
        nx = x0 + 14 if rnd.random() < 0.5 else x1 - 20
        col = CYAN if rnd.random() < 0.75 else MAGENTA
        o.append(rect(nx, top + 40, 4, IMG_H - top - 60, col, 0.35))
    # low rooftop hardware near the corners: thin, so it never reads as a hazard
    if rnd.random() < 0.6:
        bw = min(90, max(30, int(w * 0.12)))
        bx = x0 + 26 if rnd.random() < 0.5 else x1 - bw - 26
        o.append(rect(bx, top - 12, bw, 12, FACADE_DARK))
        o.append(rect(bx, top - 12, bw, 3, EDGE, 0.7))
    if rnd.random() < 0.45:
        ax = x1 - 18 if rnd.random() < 0.5 else x0 + 14
        o.append(rect(ax, top - 54, 3, 54, EDGE, 0.75))
        o.append(f'<circle cx="{ax + 1:.0f}" cy="{top - 56}" r="4" fill="{MAGENTA}" opacity="0.9"/>')
    return o


def build():
    rnd = random.Random(1024)
    body = []
    for left, right, top in zip(BLOCK_LEFT, BLOCK_RIGHT, BLOCK_TOP):
        body += building(rnd, left, right, 300 - top)

    # finish line: a beacon on the last roof edge
    fx = 6000 + X_OFFSET - 40
    fy = 300 - (-208)
    body.append(rect(fx, fy - 220, 5, 220, "#1b2f47"))
    body.append(f'<polygon points="{fx + 5},{fy - 220} {fx + 95},{fy - 196} {fx + 5},{fy - 172}" fill="{MAGENTA}" opacity="0.95"/>')
    body.append(rect(fx - 26, fy, 26, 6, MAGENTA, 0.9))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{IMG_W}" height="{IMG_H}" '
            f'viewBox="0 0 {IMG_W} {IMG_H}">' + "".join(body) + "</svg>")


def main():
    svg = build()
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"{OUT}\n  {len(svg) / 1024:.1f} KiB")


if __name__ == "__main__":
    main()
