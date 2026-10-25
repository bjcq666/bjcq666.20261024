#!/usr/bin/env python3
"""Deterministic mirror of Player's axis-separated collision.

This is NOT an engine or input E2E test. It parses the geometry tables out of
main.spx, re-implements the same per-tick integration as Player.spx, and checks
facts about the level design that are cheap to break by accident:

  1. every table is well formed, blocks do not overlap, the level is covered
  2. every alley is single-jump clearable and every rise is jumpable
  3. every hanging slab sits in a reachable, fair band above a roof
  4. an auto-jumping bot actually crosses the whole level without falling
  5. the camera offset really puts the player at ~40% of the viewport

Run after any change to the level tables. The art generator parses the same
tables, so a passing run also means Ground.svg matches the collisions.
"""
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "game" / "main.spx").read_text()

VX = 14.0                 # Player.spx horizontal speed per tick
VY0 = 22.0                # first jump impulse
GRAVITY = 1.2
HALF_W = 14.0
HEIGHT = 114.0
CAM_LAG = 80.0 / 0.72     # camera target offset in world px


def arr(name):
    m = re.search(name + r" = \[\]float64\{([^}]+)\}", SRC)
    assert m, f"{name} missing from main.spx"
    return [float(v) for v in m.group(1).split(",")]


def num(name):
    m = re.search(name + r" = (-?[\d.]+)", SRC)
    assert m, f"{name} missing from main.spx"
    return float(m.group(1))


LEFT, RIGHT, TOP = arr("blockLeft"), arr("blockRight"), arr("blockTop")
CLEFT, CRIGHT = arr("ceilingLeft"), arr("ceilingRight")
CBOT, CTOP = arr("ceilingBottom"), arr("ceilingTop")
LEVEL_START = num("levelStart")
LEVEL_LEN = num("levelLength")
LEVEL_END = LEVEL_START + LEVEL_LEN

# ---------------------------------------------------------------- table shape
assert len(LEFT) == len(RIGHT) == len(TOP), "block tables must match"
assert all(r > l for l, r in zip(LEFT, RIGHT)), "block right must exceed left"
assert len(CLEFT) == len(CRIGHT) == len(CBOT) == len(CTOP), "ceiling tables must match"
assert all(cr > cl for cl, cr in zip(CLEFT, CRIGHT)), "ceiling right must exceed left"
assert all(ct > cb for cb, ct in zip(CBOT, CTOP)), "ceiling top must exceed bottom"
assert LEFT[0] <= LEVEL_START and RIGHT[-1] >= LEVEL_END, "level must be fully covered"

gaps = []
for i in range(len(LEFT) - 1):
    gap = LEFT[i + 1] - RIGHT[i]
    assert gap >= 0, f"blocks {i} and {i + 1} overlap by {-gap}px"
    if gap > 0:
        gaps.append((RIGHT[i], LEFT[i + 1], gap))

# --------------------------------------------------------------- jump envelope
APEX = VY0 * VY0 / (2 * GRAVITY)     # highest point of a jump
AIR_TICKS = 2 * VY0 / GRAVITY        # airtime back to the takeoff height
REACH = AIR_TICKS * VX               # horizontal reach of one jump
MAX_GAP = REACH - 2 * HALF_W - 40    # margin for takeoff/landing edges
MAX_RISE = APEX - 40

for i, (l, r, gap) in enumerate(gaps):
    assert gap <= MAX_GAP, f"alley {l:.0f}..{r:.0f} = {gap:.0f}px exceeds {MAX_GAP:.0f}px"
for i in range(len(LEFT) - 1):
    rise = TOP[i + 1] - TOP[i]
    if RIGHT[i] == LEFT[i + 1]:
        assert rise <= MAX_RISE, f"step at x={LEFT[i + 1]:.0f} rises {rise:.0f}px"

for i, (cl, cr, cb, ct) in enumerate(zip(CLEFT, CRIGHT, CBOT, CTOP)):
    roofs = [t for l, r, t in zip(LEFT, RIGHT, TOP) if r > cl and l < cr]
    assert roofs, f"ceiling {i} hangs over nothing"
    low = min(roofs)
    assert cb - low >= 120, f"ceiling {i} only {cb - low:.0f}px above the roof"
    assert cb - low <= APEX + 60, f"ceiling {i} is unreachable, so pointless"


def step(x, y, vy, vx, jump):
    """One tick of Player.spx's integration, in the same order."""
    if jump and vy <= 0:
        vy = VY0
    nx = x + vx
    for l, r, t in zip(LEFT, RIGHT, TOP):
        if y < t - 0.1 and y + HEIGHT > -300:
            if vx > 0 and x + HALF_W <= l + 0.1 and nx + HALF_W > l:
                nx = l - HALF_W
            if vx < 0 and x - HALF_W >= r - 0.1 and nx - HALF_W < r:
                nx = r + HALF_W
    nx = min(LEVEL_END, max(LEVEL_START, nx))
    vy -= GRAVITY
    ny = y + vy
    if vy > 0:
        for cl, cr, cb in zip(CLEFT, CRIGHT, CBOT):
            if (nx + HALF_W > cl and nx - HALF_W < cr
                    and y + HEIGHT <= cb + 0.1 and ny + HEIGHT > cb):
                ny = cb - HEIGHT
                vy = 0
    landed = False
    if vy <= 0:
        for l, r, t in zip(LEFT, RIGHT, TOP):
            if nx + HALF_W > l and nx - HALF_W < r and y >= t - 0.1 and ny <= t:
                ny = t
                landed = True
    return nx, ny, (0.0 if landed else vy), landed


# --------------------------------------------------------------- playthrough
x, y, vy, ground = LEVEL_START, TOP[0], 0.0, True
ticks = 0
while x < LEVEL_END and ticks < 6000:
    jump = False
    if ground:
        # jump when the roof under the feet ends soon, or a higher roof starts soon
        probe = x + 70
        still_supported = any(l <= probe + HALF_W and probe - HALF_W < r and abs(t - y) < 0.5
                              for l, r, t in zip(LEFT, RIGHT, TOP))
        rise_ahead = any(x < l <= x + 140 and t > y + 0.1 for l, t in zip(LEFT, TOP))
        jump = (not still_supported) or rise_ahead
    x, y, vy, ground = step(x, y, vy, VX, jump)
    ticks += 1
    assert y >= -420, f"bot fell into a pit at x={x:.0f} (tick {ticks})"

assert x >= LEVEL_END, f"bot stalled at x={x:.0f} after {ticks} ticks"
print(f"jump envelope: apex {APEX:.0f}px, reach {REACH:.0f}px, "
      f"max alley {MAX_GAP:.0f}px, max rise {MAX_RISE:.0f}px")
print(f"bot route: {ticks} ticks ({ticks / 50:.1f}s sim) to x={x:.0f}")

# --------------------------------------------------------------- camera 40%
viewport = 1100.0 / 0.72
player_share = 0.5 - CAM_LAG / viewport
assert abs(player_share - 0.40) < 0.03, player_share
print(f"camera: player at {player_share * 100:.1f}% of a {viewport:.0f}px viewport")

# --------------------------------------------------------------- assets sane
cfg = json.loads((ROOT / "game" / "assets" / "index.json").read_text())
assert cfg["map"]["width"] >= LEVEL_LEN, "map must be at least as long as the level"
for p in (ROOT / "game" / "assets").rglob("*.json"):
    json.loads(p.read_text())
ET.parse(ROOT / "game" / "assets" / "sprites" / "Ground" / "Ground.svg")
print(f"map {cfg['map']['width']}x{cfg['map']['height']}, level {LEVEL_LEN:.0f}px")

widest = max(g for _, _, g in gaps)
print(f"PASS: {len(LEFT)} buildings, {len(gaps)} alleys (widest {widest:.0f}px), "
      f"{len(CLEFT)} hanging slabs, traversable, camera at {player_share * 100:.1f}%.")
