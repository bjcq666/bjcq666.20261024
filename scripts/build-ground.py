#!/usr/bin/env python3
"""Generate Ground.svg: the rooftop level the player runs across.

Every collision block from main.spx becomes a building: parapet at the collision
height, facade with lit windows falling away below, neon strips on the corners.
The gaps between blocks are the alleys, where the background city shows through.

The block/ceiling tables are **parsed out of main.spx**, so the artwork can never
drift away from the collision data. main.spx stays the single source of truth;
re-run this script after editing it.

Canvas is 12400x1000 with the costume pivot at (6200, 300), so image space maps
to world space as:

    imgX = worldX + 6200
    imgY = 300 - worldY          (world y=-208 -> img 508, y=-78 -> img 378)

Usage: python3 scripts/build-ground.py
"""
import os
import random
import re
from pathlib import Path

IMG_W, IMG_H = 12400, 1000
X_OFFSET = 6200
Y_ORIGIN = 300

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "game" / "main.spx"
OUT = ROOT / "game" / "assets" / "sprites" / "Ground" / "Ground.svg"

FACADE = "#0a1320"
FACADE_DARK = "#070d17"
PARAPET = "#1b2f47"
EDGE = "#33587c"
CYAN = "#3fe0f0"
MAGENTA = "#ff2e7e"


def table(name):
    src = MAIN.read_text()
    m = re.search(name + r" = \[\]float64\{([^}]+)\}", src)
    if not m:
        raise SystemExit(f"{name} not found in main.spx")
    return [float(v) for v in m.group(1).split(",")]


def rect(x, y, w, h, fill, opacity=None):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{fill}"{o}/>'


def building(rnd, left, right, top):
    x0 = max(0, left + X_OFFSET)
    x1 = min(IMG_W, right + X_OFFSET)
    w = x1 - x0
    if w <= 0:
        return []

    o = []
    o.append(rect(x0, top, w, IMG_H - top, FACADE))
    # parapet, with the lit roof edge the player actually stands on
    o.append(rect(x0, top, w, 16, PARAPET))
    o.append(rect(x0, top, w, 4, CYAN, 0.55))
    o.append(rect(x0, top + 16, w, 3, "#060b14"))
    # corner edges
    o.append(rect(x0, top, 4, IMG_H - top, EDGE, 0.5))
    o.append(rect(x1 - 4, top, 4, IMG_H - top, EDGE, 0.5))
    # window grid: mostly dark glass, a few lit
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
    # neon tube down one corner
    if w > 260 and rnd.random() < 0.7:
        nx = x0 + 14 if rnd.random() < 0.5 else x1 - 20
        col = CYAN if rnd.random() < 0.75 else MAGENTA
        o.append(rect(nx, top + 40, 4, IMG_H - top - 60, col, 0.35))
    # low rooftop hardware near the corners: thin, never reads as a hazard
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


def ceiling(rnd, left, right, bottom, top):
    """Hanging slab: obstacle the player must not jump into."""
    x0 = max(0, left + X_OFFSET)
    x1 = min(IMG_W, right + X_OFFSET)
    w = x1 - x0
    img_bottom = Y_ORIGIN - bottom      # world y of the slab's underside
    img_top = Y_ORIGIN - top
    h = img_bottom - img_top
    if w <= 0 or h <= 0:
        return []
    o = [rect(x0, img_top, w, h, "#060b14")]
    o.append(rect(x0, img_top, w, 3, EDGE, 0.55))
    # hazard stripe along the underside
    o.append(rect(x0, img_bottom - 6, w, 6, MAGENTA, 0.85))
    for i in range(int(w // 26)):
        o.append(rect(x0 + 12 + i * 26, img_bottom - 13, 10, 5, MAGENTA, 0.45))
    return o


def build():
    rnd = random.Random(1024)
    left = table("blockLeft")
    right = table("blockRight")
    top = table("blockTop")

    body = []
    for l, r, t in zip(left, right, top):
        body += building(rnd, l, r, Y_ORIGIN - t)
    for l, r, b, t in zip(table("ceilingLeft"), table("ceilingRight"),
                          table("ceilingBottom"), table("ceilingTop")):
        body += ceiling(rnd, l, r, b, t)

    # finish beacon on the last roof
    fx = 6000 + X_OFFSET - 40
    fy = Y_ORIGIN - (-208)
    body.append(rect(fx, fy - 220, 5, 220, "#1b2f47"))
    body.append(f'<polygon points="{fx + 5},{fy - 220} {fx + 95},{fy - 196} {fx + 5},{fy - 172}" fill="{MAGENTA}" opacity="0.95"/>')
    body.append(rect(fx - 26, fy, 26, 6, MAGENTA, 0.9))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{IMG_W}" height="{IMG_H}" '
            f'viewBox="0 0 {IMG_W} {IMG_H}">' + "".join(body) + "</svg>")


def main():
    svg = build()
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"{OUT}\n  {len(svg) / 1024:.1f} KiB, {svg.count('<rect')} rects")


if __name__ == "__main__":
    main()
