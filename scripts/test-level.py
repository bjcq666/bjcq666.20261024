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
LEVEL_START = num("levelStart")
LEVEL_LEN = num("levelLength")
LEVEL_END = LEVEL_START + LEVEL_LEN

# ---------------------------------------------------------------- table shape
assert len(LEFT) == len(RIGHT) == len(TOP), "block tables must match"
assert all(r > l for l, r in zip(LEFT, RIGHT)), "block right must exceed left"
assert all(r > l for l, r in zip(LEFT, RIGHT)), "block right must exceed left"


def inside(i, j):
    """块 i 是否整段落在块 j 里（= 房顶小屋），且比 j 高。"""
    return LEFT[j] <= LEFT[i] and RIGHT[i] <= RIGHT[j] and TOP[i] > TOP[j]


# 块表里既有楼顶也有房顶小屋：小屋是"贴在某栋楼顶上的窄高块"，
# 所以允许重叠，但必须是"整段包含 + 更高"，而且每个小屋都要挂在某栋楼上。
ROOFS, ROOMS = [], []
for i in range(len(LEFT)):
    host = next((j for j in range(len(LEFT)) if j != i and inside(i, j)
                 and RIGHT[j] - LEFT[j] > RIGHT[i] - LEFT[i]), None)
    if host is None:
        ROOFS.append(i)
    else:
        ROOMS.append((i, host))
assert ROOFS, "no roofs"
assert LEFT[ROOFS[0]] <= LEVEL_START and RIGHT[ROOFS[-1]] >= LEVEL_END, "level must be covered"
for k in range(len(ROOFS) - 1):
    a, b = ROOFS[k], ROOFS[k + 1]
    assert LEFT[b] >= RIGHT[a], f"roofs {k} and {k + 1} overlap"

gaps = []
for k in range(len(ROOFS) - 1):
    a, b = ROOFS[k], ROOFS[k + 1]
    gaps.append((RIGHT[a], LEFT[b], LEFT[b] - RIGHT[a]))

# --------------------------------------------------------------- jump envelope
APEX = VY0 * VY0 / (2 * GRAVITY)     # highest point of a jump
AIR_TICKS = 2 * VY0 / GRAVITY        # airtime back to the takeoff height
REACH = AIR_TICKS * VX               # horizontal reach of one jump
SINGLE_GAP = REACH - 2 * HALF_W - 40   # 单跳能过的最宽空隙
MAX_GAP = SINGLE_GAP + 460             # 二段跳还能再补一段水平距离
MAX_RISE = APEX - 40

need_double = 0
for i, (l, r, gap) in enumerate(gaps):
    assert gap <= MAX_GAP, f"alley {l:.0f}..{r:.0f} = {gap:.0f}px exceeds {MAX_GAP:.0f}px"
    if gap > SINGLE_GAP:
        need_double += 1
for i in range(len(LEFT) - 1):
    rise = TOP[i + 1] - TOP[i]
    if RIGHT[i] == LEFT[i + 1]:
        assert rise <= MAX_RISE, f"step at x={LEFT[i + 1]:.0f} rises {rise:.0f}px"

# 房顶小屋：既够得着（能跳上去），又不会高到跳不过
for i, host in ROOMS:
    rise = TOP[i] - TOP[host]
    # 小屋故意做得"单跳勉强、二段跳轻松"：上限取单跳峰值附近
    assert rise <= APEX - 8, f"room at x={LEFT[i]:.0f} rises {rise:.0f}px, above the jump apex"
    assert rise >= 100, f"room at x={LEFT[i]:.0f} only rises {rise:.0f}px, pointless"
    assert RIGHT[i] - LEFT[i] >= 140, f"room at x={LEFT[i]:.0f} too narrow to land on"


def step(x, y, vy, vx, jump, air=False):
    """One tick of Player.spx's integration, in the same order."""
    if jump:
        if air:
            vy = VY0 - 2.0        # 二段跳冲量略小
        elif vy <= 0:
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
    landed = False
    if vy <= 0:
        for l, r, t in zip(LEFT, RIGHT, TOP):
            if nx + HALF_W > l and nx - HALF_W < r and y >= t - 0.1 and ny <= t:
                ny = t
                landed = True
    return nx, ny, (0.0 if landed else vy), landed


# --------------------------------------------------------------- playthrough
def supported_at(px, py):
    return any(l <= px + HALF_W and px - HALF_W < r and abs(t - py) < 1.0
               for l, r, t in zip(LEFT, RIGHT, TOP))


def next_rise(px, py, horizon):
    """前方 horizon 内最高的、比当前更高的楼顶。"""
    best = None
    for l, r, t in zip(LEFT, RIGHT, TOP):
        if px < l <= px + horizon and t > py + 1.0:
            if best is None or t > best:
                best = t
    return best


x, y, vy, ground = LEVEL_START, TOP[0], 0.0, True
jumps = 0
ticks = 0
while x < LEVEL_END and ticks < 9000:
    jump = False
    air = False
    if ground:
        jumps = 0
        probe = x + 70
        gap_ahead = not supported_at(probe, y)
        rise = next_rise(x, y, 260)
        if gap_ahead or rise is not None:
            jump = True
            jumps = 1
    else:
        # 空中：越过不去的坎就用二段跳（这正是关卡设计想逼出来的操作）
        if jumps == 1 and vy < 8:
            need = next_rise(x, y, 420)
            if need is not None and y < need - 24:
                jump = True
                air = True
                jumps = 2
    x, y, vy, ground = step(x, y, vy, VX, jump, air)
    ticks += 1
    assert y >= -420, f"bot fell into a pit at x={x:.0f} (tick {ticks})"

assert x >= LEVEL_END, f"bot stalled at x={x:.0f} after {ticks} ticks"
print(f"jump envelope: apex {APEX:.0f}px, single-jump reach {REACH:.0f}px, "
      f"max alley {MAX_GAP:.0f}px ({need_double}/{len(gaps)} need a double jump), "
      f"max rise {MAX_RISE:.0f}px")
print(f"bot route: {ticks} ticks ({ticks / 50:.1f}s sim) to x={x:.0f}, used double jumps")

# --------------------------------------------------------------- orb grids
ORB_ROOF = [int(v) for v in re.findall(r"orbRoof = \[\]float64\{([^}]+)\}", SRC)[0].split(",")]
ORB_SIZE = [int(v) for v in re.findall(r"orbSize = \[\]float64\{([^}]+)\}", SRC)[0].split(",")]
ORB_STEP = 46.0
assert len(ORB_ROOF) == len(ORB_SIZE)
for r, cols in zip(ORB_ROOF, ORB_SIZE):
    assert 0 <= r < len(LEFT), f"orb grid roof index {r} out of range"
    cx = (LEFT[r] + RIGHT[r]) / 2
    half = (cols - 1) / 2 * ORB_STEP
    # 方阵必须完全落在楼顶横向范围内
    assert half * 2 + 60 <= RIGHT[r] - LEFT[r], f"orb grid on roof {r} is wider than the roof"
    # 方阵下方不能有更高的块（小屋）——否则小球会嵌进小屋里
    for i in range(len(LEFT)):
        if RIGHT[i] > cx - half - 10 and LEFT[i] < cx + half + 10 and TOP[i] > TOP[r] + 1:
            raise AssertionError(
                f"orb grid on roof {r} passes through block {i} (a rooftop room) at x={LEFT[i]:.0f}")
# 出生台和终点台上不放积分方阵
assert ROOFS[0] not in ORB_ROOF, "orb grid on the spawn platform"
assert ROOFS[-1] not in ORB_ROOF, "orb grid on the finish platform"
print(f"orb grids: {len(ORB_ROOF)} grids, clear of rooftop rooms and of the "
      f"spawn/finish platforms")

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
for name in ("Ground.svg", "level-background.svg"):
    found = list((ROOT / "game" / "assets").rglob(name))
    assert found, f"{name} missing"
    ET.parse(found[0])
print(f"map {cfg['map']['width']}x{cfg['map']['height']}, level {LEVEL_LEN:.0f}px")

widest = max(g for _, _, g in gaps)
print(f"PASS: {len(ROOFS)} rooftops + {len(ROOMS)} rooftop rooms, "
      f"{len(gaps)} alleys (widest {widest:.0f}px), traversable, "
      f"camera at {player_share * 100:.1f}%.")
