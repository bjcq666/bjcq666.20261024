#!/usr/bin/env python3
"""Generate the level backdrop: flat-illustration cyberpunk skyline.

Wide 13600x1400 canvas, matching the spx `map` size, so the camera can never
show an empty margin. World y maps as `y = 700 - svgY`, which puts the running
surface at svgY 908 and the jump apex around svgY 500.

Vertical plan:

    svgY    0 .. 620   sky, dusk gradient, brighter towards the horizon
    svgY  615 .. 660   building baselines (far -> near, each layer lower)
    svgY  660 .. 860   street mass: low contrast, keeps the running band calm
    svgY  860 .. 1400  below the running surface, near flat dark

Three depth layers, each lighter as it gets further away (aerial perspective),
which is what makes a flat cartoon skyline read at all:

    far   pale, half dissolved in mist, short blocks
    mid   darker, taller, occasional antenna and lit window
    near  a few big anchors, darkest, crisp rim light plus neon strips

Everything is seeded, so re-running reproduces the exact same image.

Usage: python3 scripts/build-background.py
"""
import os
import random

W, H = 13600, 1400
FAR_BASE = 980
MID_BASE = 900
NEAR_BASE = 850
STREET_END = 1010

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "game", "assets", "level-background.svg")

SKY_TOP = "#101d31"
SKY_MID = "#24415f"
SKY_HORIZON = "#4c7799"
MIST = "#a8cbe4"
FAR = "#2c4d6d"
MID = "#17293f"
NEAR = "#080f1a"
NEAR_EDGE = "#5a90bd"
STREET = "#0b1522"
VOID = "#070c15"
CYAN = "#3fe0f0"
MAGENTA = "#ff2e7e"


def rect(x, y, w, h, fill, opacity=None):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{o}/>'


def skyline(rnd, base, lo, hi, wlo, whi, gap, fill, opacity, antenna_chance=0.0,
            windows=0.0):
    out = []
    x = -120
    while x < W + 120:
        w = rnd.randint(wlo, whi)
        h = rnd.randint(lo, hi)
        if rnd.random() < 0.10:                       # landmark tower
            h = int(h * rnd.uniform(1.25, 1.7))
        top = base - h
        out.append(rect(x, top, w, H - top, fill, opacity))
        if rnd.random() < antenna_chance and w > 70:
            ax = x + w * rnd.uniform(0.3, 0.7)
            ah = rnd.randint(24, 70)
            out.append(f'<rect x="{ax:.0f}" y="{top - ah}" width="3" height="{ah}" fill="{fill}" opacity="{opacity}"/>')
        if windows and h > 90:
            for cy in range(h // 26):
                for cx in range(w // 30):
                    if rnd.random() > windows:
                        continue
                    out.append(rect(x + 12 + cx * 30, top + 18 + cy * 26, 5, 9, CYAN, 0.35))
        x += w + rnd.randint(gap, gap * 3)
    return out


def near_anchor(rnd, x, w, h):
    """One near building: darkest value, crisp rim light, neon accents."""
    top = NEAR_BASE - h
    o = [rect(x, top, w, h, NEAR, 1.0)]
    # stepped crown
    cw = int(w * rnd.uniform(0.42, 0.68))
    cx = x + (w - cw) // 2
    ch = rnd.randint(30, 90)
    o.append(rect(cx, top - ch, cw, ch, NEAR, 1.0))
    o.append(rect(cx, top - ch, cw, 3, NEAR_EDGE, 0.75))
    # rim light: top edge + one side
    o.append(rect(x, top, w, 3, NEAR_EDGE, 0.8))
    side_left = rnd.random() < 0.5
    o.append(rect(x if side_left else x + w - 3, top, 3, h, NEAR_EDGE, 0.55))
    # antenna with a warning light
    if rnd.random() < 0.5:
        ax = x + w * rnd.uniform(0.3, 0.7)
        ah = rnd.randint(70, 170)
        o.append(rect(round(ax), top - ch - ah, 4, ah, NEAR, 1.0))
        o.append(f'<circle cx="{ax:.0f}" cy="{top - ch - ah}" r="5" fill="{MAGENTA}" opacity="0.9"/>')
    # neon tube down an edge
    if rnd.random() < 0.75:
        nx = x + 12 if side_left else x + w - 15
        col = CYAN if rnd.random() < 0.7 else MAGENTA
        o.append(rect(nx, top + 34, 3, h - 80, col, 0.45))
    # signage
    if rnd.random() < 0.6:
        bw = rnd.randint(50, 130)
        bh = rnd.randint(9, 20)
        bx = int(x + rnd.uniform(20, max(21, w - bw - 20)))
        by = int(top + rnd.uniform(24, max(25, h * 0.4)))
        col = CYAN if rnd.random() < 0.55 else MAGENTA
        o.append(rect(bx, by, bw, bh, col, 0.32))
    # faint horizontal floor lines, very low contrast
    for r in range(h // 52):
        if rnd.random() < 0.5:
            o.append(rect(x + 18, top + 34 + r * 52, w - 36, 2, NEAR_EDGE, 0.12))
    return o


def build():
    rnd = random.Random(20261025)
    b = []

    b.append(f'''<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{SKY_TOP}"/>
<stop offset="0.34" stop-color="{SKY_MID}"/>
<stop offset="0.62" stop-color="{SKY_HORIZON}"/>
<stop offset="1" stop-color="{SKY_HORIZON}"/>
</linearGradient>
<linearGradient id="mist" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{MIST}" stop-opacity="0"/>
<stop offset="0.5" stop-color="{MIST}" stop-opacity="0.20"/>
<stop offset="1" stop-color="{MIST}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="glow" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{CYAN}" stop-opacity="0.05"/>
<stop offset="1" stop-color="{CYAN}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="depth" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{STREET}" stop-opacity="0"/>
<stop offset="0.35" stop-color="{STREET}" stop-opacity="0.55"/>
<stop offset="1" stop-color="{STREET}" stop-opacity="0.85"/>
</linearGradient>
<linearGradient id="fadeDown" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{STREET}" stop-opacity="0"/>
<stop offset="1" stop-color="{VOID}" stop-opacity="1"/>
</linearGradient>
</defs>''')

    # sky + horizon glow
    b.append(rect(0, 0, W, H, "url(#sky)"))
    b.append(rect(0, 520, W, 320, "url(#glow)"))

    # far layer: palest, shortest, dissolving into mist
    b += skyline(rnd, FAR_BASE, 150, 340, 90, 210, 12, FAR, 0.55, antenna_chance=0.25)
    b.append(rect(0, 640, W, 420, "url(#mist)"))

    # mid layer
    b += skyline(rnd, MID_BASE, 240, 580, 80, 210, 16, MID, 1, antenna_chance=0.35,
                 windows=0.10)
    b.append(rect(0, 700, W, 340, "url(#mist)"))

    # opaque base: the sky above was bright, everything below the skyline is a
    # dark street plane so the running band stays calm and readable
    b.append(rect(0, 700, W, H - 700, "url(#depth)"))
    b.append(rect(0, MID_BASE - 4, W, 3, "#1b3049", 1))
    rnd2 = random.Random(77)
    x = 0
    while x < W:
        w = rnd2.randint(180, 460)
        h = rnd2.randint(14, 44)
        b.append(rect(x, MID_BASE - 4 - h, w, h, STREET, 1))
        if rnd2.random() < 0.4:
            b.append(rect(x + 12, MID_BASE - 4 - h + 9, w - 24, 2, NEAR_EDGE, 0.14))
        x += w + rnd2.randint(30, 240)

    # near anchors
    x = -80
    while x < W + 80:
        w = rnd.randint(320, 620)
        h = rnd.randint(300, 640)
        b += near_anchor(rnd, x, w, h)
        x += w + rnd.randint(420, 1100)

    # street light spill, then fade to the void below the play surface
    b.append(rect(0, NEAR_BASE - 8, W, 4, CYAN, 0.10))
    b.append(rect(0, NEAR_BASE - 8, W, 170, "url(#glow)"))
    b.append(rect(0, 1150, W, H - 1150, "url(#fadeDown)"))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">' + "".join(b) + "</svg>")


def main():
    svg = build()
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"{OUT}\n  {len(svg) / 1024:.1f} KiB")

    def variant(width, height, view):
        _, rest = svg.split(">", 1)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
                f'height="{height}" viewBox="{view}">' + rest)

    for path, args in (
        ("/tmp/bg-preview.svg", (1600, 165, f"0 0 {W} {H}")),
        ("/tmp/bg-crop.svg", (1500, 750, "2200 0 2800 1400")),
    ):
        with open(path, "w") as f:
            f.write(variant(*args))
    print("/tmp/bg-preview.svg /tmp/bg-crop.svg")


if __name__ == "__main__":
    main()
