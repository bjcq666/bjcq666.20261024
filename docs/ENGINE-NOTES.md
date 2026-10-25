# 引擎行为笔记（实测）

这里记录的是**实测出来**的 spx / 引擎行为，不是文档里写的。大部分是我们踩过的坑，
写下来是为了以后不再踩第二遍。

## 相机

- `Camera.setXYpos` 只设目标点，**渲染用的相机是平滑跟随的**：每 tick 追平剩余距离约
  16%（0.02s 一跳）。从 -5857 跳到 3000（8857px）时实测每跳位移：
  `1414 → 1189 → 999 → 839 → … → 8 → 0`，约 40 tick 收敛到 12px 以内。
- `Camera.xpos` 返回**目标位置**；`Camera.viewportRect()` 返回**真实可见矩形**
  （由 canvas transform 反算）。两者之差 = 还没飞完的距离，`waitCameraStill()` 就是这么判定的。
- 所以任何需要钉在屏幕上的东西都必须用 `viewportRect()` 定位，不能用 `Camera.xpos`。
- 窗口 1100×825、`cameraZoom=0.72` 时，实测视口 = **1527.8 × 1145.8** 世界像素。

## 世界与边界

- `map` 是居中坐标系：`width=13600` 表示 `x ∈ [-6800, 6800]`。
- 精灵有 `keepInFence`：精灵的**外接矩形**必须与世界矩形（内缩 15px）有交集，
  否则位置会被夹回边界。所以大尺寸精灵在地图边缘会被钳制，这一点在算黑罩/转场行程时要考虑。
- `stretchMode: true` 时窗口等比留黑边，`WindowWidth = min(run.width, map.width)`。

## 绘制层级

- 精灵层级完全由 `assets/index.json` 的 `zorder` 顺序决定（每项对应一个 render layer）。
- `setLayer Front` 是"把本精灵提到最上层"的动作，**四个精灵每帧互相 `Front` 会变成
  执行顺序决定层级**，不可控。层级要固定就只改 `zorder`。
- Monitor（HUD）是**原生 UI 层**，画在所有世界精灵之上：遮罩压不住它，只能在转场里
  用 `getWidget(Monitor, "名字")` 显式 `show/hide`。

## 声音（这块坑最深）

- spx 用 `AudioStreamPlayer2D`（**2D 定位音频**）播放，音量受发射点与 2D 听者的距离影响。
- **精灵级 `play`** 的参数来自工程配置：
  `assets/index.json` 的 `audioAttenuation` / `audioMaxDistance`；舞台级 `play` 走固定 2000px。
- 我们原来 `audioMaxDistance = 768`，关卡跨度 12000px，相机在 `x=-6036..6036`：
  离听者超过 768px 的**所有音效都被裁成静音**。表现是"开局一声、之后全哑"，
  因为开局相机从 x=0 滑向关卡起点时会路过原点。
- 修法（两层）：
  1. `audioMaxDistance: 100000`（远大于整张地图），距离裁切不再可能触发；
  2. 所有音效统一从 `AudioCue` 精灵发射，它贴着相机视口中心，让发射点与听者重合，
     避免 2D panning 把声音甩到单侧声道。
- 音效由 `scripts/build-audio.py` 现场合成（22050Hz 单声道 16bit），目录名即声音名，
  不需要在 `assets/index.json` 注册。

## XGo classfile 规则（报错很隐晦）

- **一个 classfile 只能有一个顶层 `var (...)` 块**，否则报
  `multiple top-level var declarations in classfile`。
- **函数定义必须写在事件处理器之前**。把 `onStart` 写在函数前面，报的却是
  `expected '(', found <函数名>`，完全指不到问题所在。
- `select` 是保留字，不能做函数名（`expected 'IDENT', found 'select'`）。
- 没有 `break` / `continue`：`undefined: break`，只能用标志位改写循环。
- 声明未使用的局部变量是**编译错误**（`declared and not used`），所以
  `Camera.viewportRect()` 这类多返回值要用 `_` 明确丢弃。
- `rand()` 返回 int，需要 `float64(...)` 才能参与浮点运算。

## 精灵实例化

- 只写 `.spx` 文件和 `assets/sprites/<名字>/` **不等于**精灵会被实例化：
  它会被加载成**原型**（日志里有 `LoadSprite: 名字`），但**不在 `zorder` 里的精灵
  不会作为舞台精灵创建，它的 `onStart` 不会执行**。
  `AudioCue` 第一版就是因为没进 `zorder` 而完全不生效（位置一直是 0）。
- `Coin` / `Obstacle` / `HUDPanel` 是反面例子：它们保留了文件但只写 `onStart => { hide }`，
  属于历史残留，不参与玩法。

## 渲染细节

- 跳跃/落地动画用 `setCostume name` 逐帧驱动，`Jump 1..21` 飞行、`22..40` 落地恢复。
- SVG 里的 `<text>` 在运行时会缺字，所以菜单文字在生成阶段就转成了矢量路径
  （`scripts/build-ui-assets.py` 里的 `GLYPHS`）。
