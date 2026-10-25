# 架构设计 · 霓虹跑酷

> 模块规格、数据流、关键不变量、素材管线

## 1. 设计目标与约束

- **目标**：2 天 1 晚交付一款可玩、有打磨的楼顶跑酷。
- **约束**：个人参赛；无既有 codebase；引擎为 XBuilder（spx）；引擎有几条硬限制（见 §6）。
- **设计原则**
  1. **数据单一真源**：关卡几何只写在 `main.spx` 的矩形表里，美术由脚本读同一张表生成，
     校验脚本也读同一张表——三者不可能漂移。
  2. **状态机优先**：玩法与转场都用显式状态（`state`、`phase`）表达，不用时间猜测。
  3. **一切可复现**：地形、背景、音效、菜单图全部由 `scripts/` 生成，改参数重跑即可。
  4. **失败要静默可见**：所有"看不见"的坐标/尺寸计算都有实测依据，见 `docs/ENGINE-NOTES.md`。

## 2. 运行时架构（spx）

spx 是 Scratch 兼容引擎，代码是 XGo classfile：

- **Game（舞台）**：`main.spx`，全局唯一，存全局状态与主循环；
- **Sprite（角色类）**：每个 `.spx` 一个类，多个实例/克隆；
- **事件**：`onStart` / `onKey` / `onMsg` / `onClick` / `onCloned`；
- **消息**：`broadcast` / `broadcastAndWait` 解耦精灵；
- **资源**：`assets/index.json` 描述地图、底图、`zorder`（绘制顺序）、HUD Monitor、音频参数。

## 3. 模块划分

| 模块 | 文件 | 职责 | 关键依赖 |
|---|---|---|---|
| **舞台 / Game** | `main.spx` | 关卡矩形表、相机、`state` 状态机、黑罩转场、HUD 文本、舞台重建 | `Camera.viewportRect`、`getWidget(Monitor,"fixedHUD")` |
| **Player** | `Player.spx` | 输入、轴向分离碰撞、跳跃/二段跳、逐帧动画、坠落判死、被追上判死 | `main.spx` 的矩形表、`Fx`、`AudioCue` |
| **Chaser** | `Chaser.spx` | 四段状态机（chase/out/dash/surge）、悬停跟随、碰撞判定、尾焰发射 | `Player.xpos/ypos`、`Fx`、`broadcast "caught"` |
| **Fx** | `Fx.spx` | 粒子克隆池，5 种造型：`spark`/`bit`/`trailUp`/`trailDown`/`trailFlat` | 由 Player / Chaser 调用 |
| **AudioCue** | `AudioCue.spx` | 唯一音效发射源，贴着相机视口中心 | `play` / `pausePlaying` / `resumePlaying` |
| **ScreenDim** | `ScreenDim.spx` | 转场黑罩，钉在屏幕上，`veilScale` 决定厚度 | `wipeX`、`dimOpacity`、`veilScale` |
| **Start / Pause / Gameover** | 三个 `.spx` | 菜单面板，屏幕居中 + `GhostEffect` 淡入淡出 | `activeMenu`、`menuOpacity` |
| **Orb（道具） | `Orb.spx` | 3 个造型共用一个类：积分球（`orb`）/ 炮塔（`base`）/ 炮弹（`bullet`），靠 `costumeName` 分流 | `main.spx` 的 `orbRoof/orbSize/turretRoof`、`Player`、`Fx` |
| **Ground** | `Ground.spx` | 只负责绘图，不含逻辑 | `Ground.svg` |
| **Hud** | `Hud.spx` | 血量暗角（11 张连屏渐变造型），位置由 `placeHud` 在相机同一 tick 设置 | `health`、`Camera.viewportRect` |
| **Menu** | `Menu.spx` | 开始 / 暂停 / 结算三块面板合成一个精灵，靠造型区分；结算用 `say` 播报得分与死亡数 | `activeMenu`、`menuOpacity` |
| **血量数值** | `assets/index.json` 的 Monitor `hpView` | 原生 UI，显示 `hpText`，必须显式跟随 `state` 显隐 | `refreshHUD()`、`syncHudView()` |

## 4. 数据流与关键契约

### 4.1 全局状态（`main.spx`）

| 变量 | 说明 |
|---|---|
| `levelLength = 13500` / `levelStart = -6750` | 关卡区间，进度 = `xpos - levelStart` |
| `blockLeft/Right/Top` | 12 栋楼的矩形表（碰撞 + 美术的唯一真源） |
| `ceilingLeft/Right/Bottom/Top` | 6 组悬挂楼板 |
| `state` | `menu` / `playing` / `paused` / `dead` / `won` / `transition` |
| `uiBusy` | 转场互斥锁，期间忽略所有输入 |
| `wipeX` / `dimOpacity` / `veilScale` | 黑罩的水平偏移 / 不透明度 / 厚度倍率 |
| `menuOpacity` / `activeMenu` | 面板淡入淡出与当前面板 |
| `shakeTicks` | 镜头抖动的剩余帧数 |
| `score` / `distance` / `elapsed` / `health` / `best` | 计分与 HUD 数据 |

### 4.2 事件契约

| 消息 | 发布者 | 订阅者 | 含义 |
|---|---|---|---|
| `start` / `restart` | 面板点击、`Space`、`R` | Game | 开始 / 重开（→ `resumePlay(true)`） |
| `pause` | `ESC` | Game | 暂停 ↔ 继续（继续走 `resumePlay(false)`，不重置） |
| `toMenu` | `Q` / `M` | Game | 切到主菜单（黑罩已在位，不再滑入） |
| `finish` | Player 到达终点 | Game | 结算 |
| `caught` | Chaser 撞到玩家 / 血量归零 | Player | 死亡序列（先锁 `state`，再音效/粒子/抖动/开结算） |
| `hurt` | 炮弹命中、撞毁炮塔 | Player | 扣 25 血（8 帧冷却）、`hurt` 音效、抖动；归零转 `caught` |
| `resetOrbs` / `resetTurrets` | `resetStage()` | Orb | 只复位对应造型的克隆（`taken/dead = false` + `show`） |
| `resetPlayer` / `resetChaser` | `resetStage()` | Player / Chaser | 舞台重建时各自复位 |

### 4.3 转场时序（唯一允许的重建窗口）

```
openMenu(target):  黑罩滑入 → 停住 → 面板在黑罩之上淡入 → 常驻
resumePlay(rebuild):
    面板淡出 → (需要重建时)本体重建舞台 + 等相机落地 → 黑罩加厚/恢复 → 黑罩滑出 → 恢复玩法
```

重建（`resetStage`：清零计分、人物回起点、相机目标复位）**只发生在黑罩完全遮住舞台之后**，
所以玩家永远看不到重置过程；相机从死亡点飞回起点的那段飞行也藏在黑罩后面。

## 5. 关键不变量

1. **碰撞与美术同源**：`Ground.svg` 由 `scripts/build-ground.py` **解析 `main.spx`** 生成，
   不接受手改图；`scripts/test-level.py` 解析同一张表做几何断言。
   "房顶小屋"不是独立系统，就是一块更窄更高的碰撞块，靠"整段落在某栋楼顶内且更高"识别。
2. **跳跃包线**：`vy=22, g=1.2` → 峰值 202px、单跳水平 513px，二段跳合计约 905px。
   空隙 423~545px（12 条里 8 条必须二段跳），高差 ≤ 130px，小屋比楼顶高 140~180px。
3. **黑罩必须在菜单之下、舞台之上**：由 `assets/index.json` 的 `zorder` 保证，禁止脚本里用
   `setLayer Front` 抢层（四个精灵互相抢会变成执行顺序决定层级）。
4. **屏幕元素与相机同 tick 定位**：`Camera.xpos` 是目标位置（相机会滞后），`viewportRect()`
   是上一帧的实际相机；**小而静止**的屏幕元素如果自己跑循环摆位，会因相位差抖动 1~2px。
   要么放进相机更新的同一个 tick（`placeHud`），要么做成大面积图形（暗角、遮罩），
   要么干脆用原生 UI（监视器）。
5. **原生监视器盖在所有精灵之上**，黑罩盖不住它，必须显式 `show/hide`（`syncHudView`）。
6. **音效只从 `AudioCue` 发射**，且 `audioMaxDistance` 必须远大于地图宽度，否则会被 2D 距离裁切。
7. **持久道具用 hide 而不是 destroy**：积分球、炮塔都是常驻克隆，用掉后 `hide`，
   重开时广播复位。若"销毁 + 重建"，上一局残留 + 新建会顶到克隆上限 300，部分道具静默不生成。

## 6. 引擎硬限制（决定了很多实现细节）

| 限制 | 数值 | 影响 |
|---|---|---|
| 单张纹理边长 | 16384px | 地图宽 + 两侧余量必须 < 16384，所以关卡长度上限约 15000 |
| classfile 反射方法表 | 2560 | **实测 11 个精灵类型就会启动失败**（10 个可以）。所以炮塔/炮弹只能作为造型并进 `Orb`，三块面板合并成 `Menu`。当前 9 个类型 |
| 克隆总数 | 300 | 常驻克隆（积分球 136 颗）要算进预算，长跑时不能再无脑销毁重建 |
| 一个 classfile | 只能一个顶层 `var` 块 | 变量必须集中声明 |
| 相机 | 自带平滑（每帧追平剩余 16%） | 一切屏幕对齐要用 `viewportRect()` + 等相机落地 |

## 7. 构建与校验管线

| 脚本 | 作用 |
|---|---|
| `scripts/build-ground.py` | 解析 `main.spx` 矩形表 → 生成 `Ground.svg`（楼顶 + 立面 + 房顶小屋 + 终点信标） |
| `scripts/build-background.py` | 生成 `level-background.svg`（黄昏天空 + 三层城市 + 雾带 + 霓虹） |
| `scripts/build-audio.py` | 合成 8 个音效 + 8 秒循环 BGM（纯标准库） |
| `scripts/build-hud.py` | 生成血量暗角 11 档造型（`assets/sprites/Hud/`） |
| `scripts/build-ui-assets.py` | 生成渐变转场遮罩 + Menu 的三块面板（文字转矢量路径，避免缺字） |
| `scripts/test-level.py` | 关卡几何断言 + 自动跳跃机器人跑完全程 + 相机取景 |

生成器与产物的对应关系是硬约定：**不要手改生成物**，改参数重跑脚本。曾经的教训是
`build-ui-assets.py` 还按旧架构生成 `Start/Pause/Gameover` 与 101 张血条造型，重跑一次
就把渐变遮罩覆盖成纯黑、还复活了三个死目录 —— 现在脚本只产出当前架构在用的东西。

## 8. AI 协作方式（可复盘）

- **测量驱动**：所有"玄学"问题都先量化。例如相机平滑是用打印 `viewportRect()` 与 `Camera.xpos`
  的差值测出来的（每帧追平 16%），黑罩抖动、音频被裁切也都是这样定位的。
- **单一真源 + 脚本化**：没有任何手改的生成物；改参数 → 重跑脚本 → 跑校验，三步闭环。
- **每步可交付**：每个功能一个提交 + 实测数据写进 `docs/ENGINE-NOTES.md`，避免同类坑重复踩。
- **人机分工**：AI 负责实现、量化、写文档与自检；视觉与手感由人实机验收并给出方向性反馈。
