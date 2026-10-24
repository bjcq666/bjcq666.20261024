# 疾风行者 · Neon Dash

> 一款使用 **XBuilder（spx 引擎）** 制作的赛博霓虹风 2D 横向跑酷游戏。

[![XBuilder](https://img.shields.io/badge/XBuilder-spx-blue)](https://x.qiniu.com)
[![XGo](https://img.shields.io/badge/XGo-1.7+-teal)](https://xgo.dev)
[![spx](https://img.shields.io/badge/spx-4.0-orange)](https://github.com/goplus/spx)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 🎮 简介

《疾风行者》是一款横版无限跑酷游戏：在霓虹闪烁的赛博都市里，你操控一名疾行者向前奔跑，跳跃、滑铲、二段跳，躲避迎面而来的障碍，收集能量，挑战更高分数与更快速度。

- **自动奔跑**：角色持续向前，玩家专注「何时跳、何时滑、何时做动作」。
- **三档操作**：跳跃 / 滑铲 / 二段跳，组合出流畅的跑酷节奏。
- **动态难度**：速度随距离递增，障碍组合逐渐复杂。
- **Combo 连击**：连续收集能量触发加成，鼓励冒险。
- **Juice 手感**：屏幕震动、速度线、粒子、飘分、音效，强化速度感。
- **多阶段视觉**：背景与配色随进度切换（黎明 → 霓虹 → 深夜）。

## 🕹️ 操作

| 操作 | 按键 |
|---|---|
| 跳跃 / 二段跳 | `Space` / `↑` |
| 滑铲 | `↓` |
| 冲刺（可选） | `Shift` |
| 暂停 / 重开 | `P` / `R` |

## 🚀 快速开始

### 在线试玩

> Web 构建部署后补充链接（GitHub Pages / WASM）。

### 本地运行

环境要求：macOS / Linux（Windows 用 Git Bash），已安装 **Go ≥ 1.19** 与 **Homebrew**。

```bash
# 1) 安装 XGo 编译器
brew install xgo

# 2) 克隆并编译 spx 引擎，下载运行时
git clone https://github.com/goplus/spx.git
cd spx
go install -v ./...
export PATH="$HOME/go/bin:$PATH"          # 建议加入 ~/.zshrc 或 ~/.bash_profile
buildctl setup host --published-runtime   # 下载 Godot 运行时（约 150MB）

# 3) 运行游戏
cd <本仓库>/game
spx run         # 解释执行（最快，秒级启动）
spx runnative   # 原生 PC 运行时（更流畅）
```

### 在 XBuilder 中打开

1. 访问 [x.qiniu.com](https://x.qiniu.com) 并登录；
2. 新建项目，或把本仓库 `game/` 目录打包为 `.xbp`（zip 改后缀）导入；
3. 在 XBuilder 编辑器中可视化编辑 / 预览 / 发布。

## 📁 项目结构

```
.
├── README.md                 # 本文件
├── ARCHITECTURE.md           # 架构设计（模块规格、分工）
├── PLAN.md                   # 项目规划与方向
├── game/                     # spx 游戏工程（核心）
│   ├── main.spx              # 舞台 / Game
│   ├── Player.spx            # 主角
│   ├── Obstacle.spx          # 障碍
│   ├── Coin.spx              # 能量
│   ├── Background.spx        # 视差背景
│   ├── builder-meta.json
│   └── assets/               # 素材（index.json、贴图、音效）
├── scripts/                  # 构建 / 运行 / 导出脚本
├── docs/                     # 文档（GAMEPLAY / AI_PROCESS / ASSETS）
└── .github/                  # PR / Issue 模板
```

## 🛠️ 技术栈

- **引擎**：[spx](https://github.com/goplus/spx) — Scratch 兼容的 2D 游戏引擎
- **语言**：[XGo](https://xgo.dev) — XGo classfile（`.spx`）
- **编辑器**：[XBuilder](https://x.qiniu.com)
- **部署**：Web（WASM）+ GitHub Pages

## 🧑‍💻 开发流程

- **每个变更走 PR**：`feat/xxx`、`fix/xxx` 分支 → PR → Squash 合并；
- **提交规范**：[Conventional Commits](https://www.conventionalcommits.org/)（`feat:` / `fix:` / `docs:` / `chore:`）；
- **版本**：`v0`（初始化）→ 后续阶段性 tag；
- **过程留痕**：Issue / PR / commit 全保留。

## 📄 素材与授权

- 游戏素材来源与授权见 `docs/ASSETS.md`（待补充）。
- 代码以 MIT 协议开源（见 `LICENSE`，待补充）。

## 🙏 致谢

- [goplus/spx](https://github.com/goplus/spx) — 游戏引擎
- [XBuilder](https://x.qiniu.com) — 创作平台
- [Kenney](https://kenney.nl) 及其他 CC0 素材来源（如使用会标注）
