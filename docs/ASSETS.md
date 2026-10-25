# 第三方素材来源与修改记录

## TheRealGi · 2D Stickman Character

- 作者：TheRealGi
- 来源：https://therealgi.itch.io/2d-stickman-character
- 用户提供的原始包：Stickman Basic Pack（不上传整个 Unity 包）。
- 2026-10-25 核对的作者页面原文：
  > I made this for everyone so he can use it for games or prototypes
  > No need for credits, you can use it any way you want to
- 页面标明 AI Assisted / Graphics。此为作者的宽泛使用许可，并非 CC0 或 MIT。下载包内未找到独立 LICENSE。
- 本项目仅使用游戏依赖的缩小、着色透明 PNG，不将素材作为独立素材包出售。保留作者署名与链接。作者未单独明确说明开源游戏仓库中的源素材再分发；如后续提出限制，移除对应文件并替换。
- 修改：统一480×270画布；RGB(255,2,99)；保留alpha；跳跃帧水平镜像。转换脚本保留在 scripts/。
- 游戏使用70个造型，包括待机、跑步、起跳/空中/落地；二段跳复用空中收腿帧。
- 此素材不因本仓库代码许可而转为 MIT；适用作者原许可声明。

## 音频（全部原创合成）

- 8 个音效与 1 段循环 BGM 全部由 `scripts/build-audio.py` 用 Python 标准库现场合成（正弦/方波/锯齿 + 噪声 + 包络），**不含任何第三方音频样本**，不需要额外的素材授权。
- 采样规格：22050Hz、单声道、16bit，与 spx 的 `assets/sounds/<name>/index.json`（`path/rate/sampleCount`）一致；音效按目录名查找，不需要在 `assets/index.json` 注册。

| 名字 | 用途 | 长度 |
| --- | --- | --- |
| `jump` | 一段跳 | 0.16s |
| `doublejump` | 二段跳 | 0.18s |
| `land` | 落地 | 0.14s |
| `death` | 坠亡 | 0.85s |
| `finish` | 通关 | 0.90s |
| `select` | 菜单确认 | 0.10s |
| `hurt` | 受击 / 撞毁炮塔 | 0.26s |
| `bgm` | 循环背景music（120BPM，4 小节 Am-F-C-G） | 8.00s |

- 重生成：`python3 scripts/build-audio.py`。改动合成参数后要重新生成并一起提交，仓库里的 wav 是可复现产物。

## 程序生成的场景美术

- `game/assets/level-background.svg`（城市天际线）和 `game/assets/sprites/Ground/Ground.svg`（楼顶地形）都不是手绘文件，而是由脚本按固定随机种子生成，改完后重跑脚本即可复现：
  - `python3 scripts/build-background.py`（天空/三层城市/雾/霓虹）
  - `python3 scripts/build-ground.py`（把 main.spx 的碰撞矩形表画成楼顶与立面，表必须与 main.spx 一致）
- 两者都是纯几何图形 + 渐变，无位图、无第三方素材，随仓库代码许可发布。

## 自制原型素材

原有几何图形角色、背景、菜单为项目原型制作。旧角色SVG目前不再注册。
中文字体来自用户从XBuilder导出的测试工程；字体具体许可证尚需补核，不应宣称整个素材目录均为MIT。

## 本仓库自产的程序化素材

| 产物 | 生成脚本 | 说明 |
|---|---|---|
| `assets/sprites/Ground/Ground.svg` | `scripts/build-ground.py` | 14700×1000，楼顶地形 + 房顶小屋 + 终点信标，矩形表直接解析自 `main.spx` |
| `assets/level-background.svg` | `scripts/build-background.py` | 15000×1400，黄昏城市远景 |
| `assets/sprites/Hud/hp0..100.svg` | `scripts/build-hud.py` | 血量暗角 11 档（0%..100%，10% 一档） |
| `assets/sprites/ScreenDim/dim.svg` | `scripts/build-ui-assets.py` | 2600×1800 渐变转场遮罩（左→右，与游戏同色系） |
| `assets/sprites/Menu/{start,pause,gameover}.svg` | `scripts/build-ui-assets.py` | 三块菜单面板，文字已转矢量路径，不依赖字体 |
| `assets/sounds/*` | `scripts/build-audio.py` | 8 个音效 + 1 段 BGM，纯 Python 标准库合成 |

**这些都是生成物，不要手改**；改参数重跑对应脚本即可，仓库里的文件就是生成结果。
