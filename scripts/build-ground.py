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

    imgX = worldX + X_OFFSET
    imgY = 300 - worldY          (world y=-208 -> img 508, y=-78 -> img 378)

Usage: python3 scripts/build-ground.py
"""
import os
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "game" / "main.spx"


def _level_span():
    src = MAIN.read_text()
    start = float(re.search(r"levelStart = (-?[\d.]+)", src).group(1))
    length = float(re.search(r"levelLength = (\d+)", src).group(1))
    return start, length


_START, _LEN = _level_span()
# 画布宽度 = 关卡长度 + 两侧各 600 余量，取偶数便于对半切
IMG_W, IMG_H = int(_LEN + 1200) // 2 * 2, 1000
X_OFFSET = IMG_W // 2
Y_ORIGIN = 300
SPRITES = ROOT / "game" / "assets" / "sprites" / "Ground"
OUT = SPRITES / "Ground.svg"

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


def level_end():
    m = re.search(r"levelStart = (-?[\d.]+)", MAIN.read_text())
    n = re.search(r"levelLength = (\d+)", MAIN.read_text())
    return float(m.group(1)) + float(n.group(1))


def last_roof():
    tops = table("blockTop")
    lefts = table("blockLeft")
    rights = table("blockRight")
    end = level_end()
    for l, r, t in zip(lefts, rights, tops):
        if l <= end - 40 <= r:
            return t
    return tops[-1]


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
    o.append(rect(x0, top, w, 5, CYAN, 0.75))
    o.append(rect(x0, top + 16, w, 3, "#060b14"))
    o.append(rect(x0, top + 19, w, 14, "#04070c", 0.85))   # 檐下阴影，压出"这是楼顶边缘"
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


def rooftop_room(rnd, left, right, top, roof_top):
    """房顶上的小房子：从自己的顶画到所在楼顶，带屋檐、门和霓虹招牌。"""
    x0 = max(0, left + X_OFFSET)
    x1 = min(IMG_W, right + X_OFFSET)
    w = x1 - x0
    if w <= 0 or roof_top <= top:
        return []
    o = []
    o.append(rect(x0, top, w, roof_top - top + 6, FACADE))
    # 屋檐
    o.append(rect(x0 - 8, top - 10, w + 16, 12, PARAPET))
    o.append(rect(x0 - 8, top - 10, w + 16, 3, CYAN, 0.6))
    # 门 + 两扇窗
    door_w = min(46, int(w * 0.3))
    dx = x0 + (w - door_w) // 2
    o.append(rect(dx, roof_top - 8 - 62, door_w, 62, "#0d1b2c"))
    o.append(rect(dx, roof_top - 8 - 62, door_w, 3, EDGE, 0.8))
    for k in range(2):
        wx = x0 + 14 + k * (w - 40 - 26)
        if wx + 20 < x1 - 10:
            o.append(rect(wx, top + 22, 20, 26, CYAN, 0.32))
    # 招牌
    if w > 150:
        o.append(rect(x0 + 12, top - 34, min(70, w - 24), 9, MAGENTA, 0.5))
    return o


def build():
    rnd = random.Random(1024)
    left = table("blockLeft")
    right = table("blockRight")
    top = table("blockTop")

    def host_of(i):
        """返回包住块 i 的那栋楼顶（= 小屋的主人）。"""
        for j in range(len(left)):
            if j != i and left[j] <= left[i] and right[i] <= right[j] \
                    and top[i] > top[j] and (right[j] - left[j]) > (right[i] - left[i]):
                return j
        return None

    body = []
    for i, (l, r, t) in enumerate(zip(left, right, top)):
        host = host_of(i)
        if host is None:
            body += building(rnd, l, r, Y_ORIGIN - t)
        else:
            body += rooftop_room(rnd, l, r, Y_ORIGIN - t, Y_ORIGIN - top[host])

    # finish beacon on the last roof, at the level end parsed from main.spx
    end = level_end()
    fy = Y_ORIGIN - last_roof()
    fx = end + X_OFFSET - 40
    body.append(rect(fx, fy - 220, 5, 220, "#1b2f47"))
    body.append(f'<polygon points="{fx + 5},{fy - 220} {fx + 95},{fy - 196} {fx + 5},{fy - 172}" fill="{MAGENTA}" opacity="0.95"/>')
    body.append(rect(fx - 26, fy, 26, 6, MAGENTA, 0.9))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{IMG_W}" height="{IMG_H}" '
            f'viewBox="0 0 {IMG_W} {IMG_H}">' + "".join(body) + "</svg>")


def main():
    # 单张纹理上限 16384：这张图 = 关卡长 + 两侧余量，还在上限内
    assert IMG_W < 16384, f"ground {IMG_W}px exceeds the 16384 texture limit"
    svg = build()
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"{OUT}\n  {len(svg) / 1024:.1f} KiB, {svg.count('<rect')} rects ({IMG_W}x{IMG_H})")


if __name__ == "__main__":
    main()
