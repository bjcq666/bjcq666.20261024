# 镜头、HUD 与菜单转场

## 镜头

- 窗口 1100×825（`stretchMode: true`，等比留黑边），`cameraZoom = 0.72` → 视口 1528×1146 世界像素。
- `Camera.setXYpos Player.xpos + 80 / cameraZoom, 0`：目标把人物放在视口水平 40%。引擎相机**自带平滑**（实测每次 tick 追平剩余距离的约 16%），所以 `Camera.xpos` 是目标位置，`Camera.viewportRect()` 才是真实可见矩形，两者之差就是还没飞完的距离。

## HUD

- 原生 Monitor `fixedHUD`（`assets/index.json` 的 `zorder` 里，`getVar:hudText`，`mode: 2`，`style: default`，`x=-500, y=380`），屏幕坐标、不随镜头移动。
- 文案由 `main.spx` 的 `refreshHUD()` 拼：`HP xxx / 100 [20格血条]` + `SCORE / TIME / DIST / 12000`。
- Monitor 是原生 UI 层，画在所有世界精灵之上，**遮罩压不住它**：转场里用 `syncHUD()` 通过 `getWidget(Monitor, "fixedHUD")` 显式 `show/hide`，菜单期间 HUD 完全隐藏。

## 菜单面板

- `Start` / `Pause` / `Gameover` 是 480×300 的世界精灵面板（SVG，文字已转矢量字形，不依赖字体）。
- 每帧用 `Camera.viewportRect()` 把自己摆到屏幕正中，用 `GhostEffect`（`100 - menuOpacity`）做淡入淡出，由 `activeMenu` 决定显示哪一个。
- 绘制顺序完全由 `assets/index.json` 的 `zorder` 决定：`Ground → Player → DebugBox → fixedHUD → ScreenDim → Start → Gameover → Pause`。**不要用 `setLayer Front` 每帧抢层**，四个精灵互相抢会变成执行顺序决定层级。

## 黑罩（ScreenDim）

- 2600×1800 纯黑 SVG，`setSize veilScale / cameraZoom` 撑满视口。
- 位置 = `viewportRect()` 中心 + `wipeX`，所以它钉在屏幕上；**不要用 `Camera.xpos`**，那是目标位置，相机飞行时会把黑罩甩出画面。
- 生命周期由 `main.spx` 驱动：

| 阶段 | 行为 |
| --- | --- |
| `openMenu(target)` | 黑罩从左滑入（13×0.02s）→ 停在正中 → 面板在黑罩之上淡入（20×0.02s）→ **黑罩常驻** |
| 菜单期间 | `maskUp = true`，黑罩一动不动，`Camera` 也不动 |
| `resumePlay(rebuild)` | 面板先淡出 → 需要重建时才重置舞台 → 黑罩滑出（尾巴 4 帧淡出兜底世界边界夹取） |

- `maskIn()` 是幂等的：从暂停切到主菜单时黑罩已经在位，不会再滑一遍（否则会闪出舞台）。

## 舞台重置为什么藏在黑罩之后

1. 重开要把人物送回 `levelStart`，相机随之从死亡点飞回起点。飞行中每帧位移可达 **1400px**（实测），而所有 UI 都是世界精灵、位置来自比相机晚一帧的 `viewportRect()`，飞行时会被甩出去 → 抖动。
2. 因此流程固定为：面板淡出 → 屏幕只剩纯黑 → `resetStage()` → `waitCameraStill()`（约 40 tick，收敛到 12px 内）→ 黑罩滑出。
3. 飞行期间黑罩放大到 **3 倍**（`veilThick()`）：一帧 1400px 的摆放误差仍在黑罩内部，边缘不会漏出舞台。滑入/滑出时恢复 1 倍，否则黑罩挪不出画面。

## 输入锁

- `uiBusy` 覆盖整个转场，期间 ESC/Q/R/开始全部忽略，避免多个动画抢同一个变量。
- `state` 在转场中是 `"transition"`，`Player.spx` 只在 `state == "playing"` 时推进物理与动画。

## 已知边界

- 关卡终点附近，世界边界（`keepInFence`）会限制黑罩往右滑出的距离，差 90px 左右滑不干净，所以滑出尾部带 4 帧淡出兜底。
- 菜单与世界精灵都在相机坐标系里，没有原生 CanvasLayer/屏幕空间精灵可用；HUD 之所以固定是因为它是 Monitor。
