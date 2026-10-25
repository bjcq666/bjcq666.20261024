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

## 音频

- 音效与 BGM 全部由 `scripts/build-audio.py` 现场合成，放在 `game/assets/sounds/<名字>/`
  （`index.json` = `{path, rate, sampleCount}`，目录名即声音名，不用在 `assets/index.json` 注册）。
- 所有音效统一由 `AudioCue` 精灵发射（它贴着相机视口中心），原因和踩坑过程见
  `docs/ENGINE-NOTES.md` 的声音一节：spx 用 2D 定位音频，离听者超过 `audioMaxDistance`
  会被裁成静音，而我们的关卡跨度 12000px。
- `assets/index.json` 里 `audioMaxDistance` 调到 100000、`audioAttenuation` 保持 0。
- 触发点：跳跃/二段跳/落地（`Player.spx`）、死亡（坠坑）、通关、菜单确认；
  BGM 在开局循环播放，暂停菜单打开时 `pausePlaying`、恢复时 `resumePlaying`。

## 追逐者与粒子

### 追逐者（Chaser）

品红球体 + 白底椭圆眼白 + 品红圆眼珠，`setSize 1.35`。四段状态机，避免"目标点在移动导致冲刺永远收不了尾"：

| 阶段 | 行为 | 迁移条件 |
|---|---|---|
| `chase` | 速度 14 起，每帧 `-0.008` 衰减到 **12**（比玩家慢 2） | 整体出界（`xpos < 视口左边界 - 70`）→ `out` |
| `out` | 速度归零、停住 | 30 帧（0.6s）后 → `dash` |
| `dash` | 瞄准"视口左边缘+60"，速度 `剩余距离 * 0.35`，钳制在 **30~95** | 越过目标 → `surge` |
| `surge` | 速度 26（比玩家快 12）快速逼近 | 距离 ≤ **470px** 或超时 → `chase` |

垂直方向按距离阻尼向玩家胸口收拢：常规 `0.055`、贴近 320px 内 `0.14`、冲刺时 `0.24`（俯冲感）。
撞到玩家（`|dx|<58 && |dy|<96`）广播 `caught`，由 Player 统一执行死亡序列。

### 粒子（Fx）

一个精灵带 5 种造型，克隆继承造型，`onCloned` 里按 `costumeName` 分流：

| 造型 | 用途 | 初速 |
|---|---|---|
| `spark` | 起跳 / 落地 / 坠亡碎屑 | 随机四散 + 重力 |
| `bit` | 尾焰里的白方块 | 原地"放大缩小"呼吸一次 |
| `trailUp` | 无人机上升时 | **左下** |
| `trailDown` | 下落时 | **左上** |
| `trailFlat` | 平飞时 | 正左 |

所有粒子都是"速度每帧 ×0.92、尺寸递减、`GhostEffect` 渐隐、到期 `destroy`"，不会残留。
`Chaser` 冲刺时每帧发两颗尾焰，避免一帧 90px 的位移把尾迹拉断。

### 镜头抖动

`updateCamera()` 里按 `shakeTicks` 叠加随机偏移（±7px × 1.6），坠亡与撞死时置 12~14 帧，
几帧内自然衰减回 0；舞台重建时清零。

## 积分球（Orb）

白色圆形，5 个方阵（3×3 / 5×5 交替，格间距 46px）挂在第 4/5/9/10/11 栋楼顶上方，出生台与终点台不放。

- **位置由几何算出来**：方阵中心取楼顶矩形中点，高度取 `楼顶 + 90`（3×3）或 `+132`（5×5）；
  `scripts/test-level.py` 断言每个方阵都落在楼顶横向范围内、且不会压到房顶小屋。
- **克隆池只铺一次**：`main.spx` 用 `orbSpawned` 保证第一次之后不再克隆，重开时只
  `broadcast "resetOrbs"`。
- **吃到不销毁**：`taken = true` + `hide`，复位时 `taken = false` + `show`。
  这样做是因为克隆总数有上限（300）：如果"吃掉即 destroy + 重开再整套重建"，
  上一局没吃掉的球还在、新球又要生成，就会顶到上限，部分小球静默不出现（真实踩过的坑）。
- 判定半径 34×62（比视觉宽容），反馈：+10 分、`Fx.burst` 四颗碎屑、一声确认音。
