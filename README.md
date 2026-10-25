# 霓虹跑酷 · Neon Parkour

> 用 **XBuilder（spx 引擎）** 做的赛博霓虹风 2D 楼顶跑酷：在霓虹都市的摩天楼顶之间跳跃，身后一颗球形无人机紧追不舍。

[![XBuilder](https://img.shields.io/badge/XBuilder-spx-blue)](https://x.qiniu.com)
[![XGo](https://img.shields.io/badge/XGo-classfile-teal)](https://xgo.dev)
[![spx](https://img.shields.io/badge/spx-4.0-orange)](https://github.com/goplus/spx)

## 🎮 玩什么

你操控一名火柴人在 **13 500px 的楼顶赛道**上前进：跳过楼与楼之间的空隙、别一头撞上悬挂楼板，同时提防身后那颗会俯冲的无人机。

- **手动操作**：左右移动带惯性，跳跃 + 二段跳（松手再按才算第二段），没有自动奔跑。
- **楼顶地形**：13 栋楼顶 + 7 个房顶小屋、12 条楼间空隙（423~545px，其中 8 条必须二段跳），楼顶高度按 5 档台阶起伏；掉下去即死亡。
- **积分球**：白色圆形，5 个 3×3 / 5×5 方阵悬在楼顶上方，每颗 +10 分。
- **炮塔**：3 座楼顶炮塔，炮管跟着你转，进画面才开火；被炮弹打中或撞上炮塔都扣 25 血，撞上会把炮塔拆掉。
- **追逐者**：品红球体无人机贴着背后追，被甩出画面后停半秒再猛冲回来，然后以 26px/tick 逼近到约 450px 处；撞上即死。
- **手感**：起跳扬尘 / 落地烟尘 / 坠亡爆散粒子、受击与坠亡的镜头抖动、受伤时四周泛红的暗角、8 个原创合成音效 + 8 秒循环合成器 BGM。
- **转场**：进入菜单时同色系渐变遮罩从左滑入并**常驻遮住舞台**，菜单消失后遮罩才滑出；舞台重建完全发生在遮罩之后，看不到任何重置过程。开机第一帧就是遮罩，不会露出舞台。

## 🕹️ 操作

| 操作 | 按键 |
|---|---|
| 左右移动 | `←` / `→` |
| 跳跃 / 二段跳 | `↑` / `Space`（松开再按第二次） |
| 暂停 / 继续 | `ESC` |
| 暂停 → 主菜单 | `Q` |
| 死亡/通关后重开 | `R` |
| 结算 → 主菜单 | `M` |
| 主菜单开始游戏 | `Space` 或点击面板 |

## 🚀 本地运行

需要 Go 环境与 spx（`go install github.com/goplus/spx/v4/cmd/spx@latest`）：

```bash
cd game
spx run          # 解释执行，秒级启动
```

无窗口的编译/启动冒烟检查：

```bash
cd game && spx run -headless -v      # 只看有没有编译错误，注意跑完要手动结束运行时进程
```

## 📁 项目结构

```
.
├── README.md
├── ARCHITECTURE.md          # 模块规格、数据流、关键不变量
├── PLAN.md                  # 进度与后续方向
├── docs/
│   ├── LEVEL.md             # 关卡几何、碰撞、校验方式
│   ├── UI.md                # 镜头、HUD、菜单与黑罩转场、音频
│   ├── ENGINE-NOTES.md      # 实测出来的 spx 引擎行为与踩坑记录
│   └── ASSETS.md            # 素材来源、授权、生成脚本
├── game/                    # spx 工程
│   ├── main.spx             # 舞台：关卡表、相机、状态机、转场
│   ├── Player.spx           # 火柴人：输入、物理、动画、死亡
│   ├── Chaser.spx           # 追逐者：四段状态机
│   ├── Fx.spx               # 粒子总控（5 种造型的克隆池）
│   ├── AudioCue.spx         # 音效发射器（贴着相机）
│   ├── ScreenDim.spx        # 转场黑罩
│   ├── Start/Pause/Gameover.spx
│   ├── Ground.spx           # 地形美术（碰撞在 main.spx）
│   └── assets/              # index.json、造型、音效、字体
├── scripts/                 # 全部美术/音频/校验脚本（可复现）
└── previews/                # 动画与背景预览
```

## 🛠️ 技术栈

- **引擎** [spx](https://github.com/goplus/spx)（Scratch 兼容 2D 引擎）
- **语言** XGo classfile（`.spx`，编译期严格：单 `var` 块、函数须写在事件处理器之前、没有 `break`）
- **素材** 除火柴人外全部程序化生成：地形、背景、血量暗角、转场遮罩、菜单面板都是脚本生成的 SVG，音效与 BGM 是 Python 现场合成
- **角色素材** TheRealGi 火柴人（作者宽泛许可，见 `docs/ASSETS.md`）

## 🧑‍💻 开发流程

- 每个变更走 feature 分支 → PR → 合并，提交信息用 [Conventional Commits](https://www.conventionalcommits.org/)；
- 改关卡几何后必须跑 `python3 scripts/test-level.py`（校验跳跃包线、可达性、相机取景）；
- 程序化素材改完要重跑对应 `scripts/build-*.py`，仓库里的产物是**可复现的生成结果**；
- 引擎侧的坑记录在 `docs/ENGINE-NOTES.md`，改代码前先看一眼能省很多时间。

## 📄 素材与授权

- 火柴人素材：TheRealGi《2D Stickman Character》，作者声明可自由用于游戏与原型，详见 `docs/ASSETS.md`；
- 场景美术与全部音频：本项目脚本生成，随代码一起发布；
- 字体：从 XBuilder 测试工程导出，许可证待补核。
