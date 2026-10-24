# 架构设计 · 疾风行者

> 模块规格、数据流、素材管线、分工与开发流程

## 1. 设计目标与约束

- **目标**：2 天 1 晚内交付一款可玩、有打磨、可在线试玩的横向跑酷游戏。
- **约束**：个人参赛；无既有 codebase；以 XBuilder（spx）为引擎。
- **设计原则**：
  1. 玩法聚焦（无限跑酷），内容可控；
  2. 模块解耦（事件驱动），便于并行与迭代；
  3. 全部变更走 PR，保留过程痕迹；
  4. AI 深度参与开发，过程可量化复盘。

## 2. 运行时架构（spx）

spx 是 Scratch 兼容的 2D 引擎，基于 XGo classfile：

- **Game（舞台 / project class）**：`main.spx`，全局唯一，保存全局状态与舞台逻辑；
- **Sprite（worker class）**：每个精灵一个 `.spx` 文件，各自独立，可用 `clone` 复制；
- **事件驱动**：`onStart` / `onKey` / `onMsg` / `onClick` / `onTouchStart` / `onCloned`；
- **消息总线**：`broadcast` / `onMsg` 解耦精灵间通信；
- **资源**：`assets/index.json` 统一描述造型 / 动画 / 背景 / 声音。

## 3. 模块划分

| 模块 | 文件 | 职责 | 关键事件 / 依赖 |
|---|---|---|---|
| **Game / 舞台** | `main.spx` | 全局状态、生成调度、背景滚动、UI、开始 / 结束 | `onStart`、`broadcast` |
| **Player 主角** | `Player.spx` | 输入、位移、跳跃 / 滑铲 / 二段跳、碰撞、动画、无敌帧 | `onKey`、`onTouchStart` |
| **Obstacle 障碍** | `Obstacle.spx` | 克隆、移动、回收、类型（地面 / 低空） | `onCloned`、`onMsg` |
| **Coin 能量** | `Coin.spx` | 克隆、移动、收集、combo | `onCloned`、`onMsg` |
| **Background 背景** | `Background.spx` | 视差滚动、主题切换 | 由 Game 驱动 |
| **UI / HUD** | `main.spx` + Monitor | 分数 / 速度 / 连击 / 最高分 | 数据来自 Game |
| *(可选) AI 教练* | `AICoach.spx` | `ai.Player` 实时点评 | 暂不纳入 MVP |

## 4. 数据流与关键契约

### 4.1 全局状态（`main.spx` 的 `var`）

| 变量 | 类型 | 说明 |
|---|---|---|
| `score` | int | 当前分数 |
| `best` | int | 最高分（本地持久化） |
| `speed` | int | 当前滚动速度 |
| `combo` | int | 连击数 |
| `state` | string | `menu` / `playing` / `dead` |

### 4.2 事件契约

| 事件 | 载荷 | 发布者 | 订阅者 |
|---|---|---|---|
| `gameStart` | — | Game | Player / Obstacle / Coin |
| `hit` | — | Player | Game（扣命 / 结束） |
| `coin` | — | Coin | Game（加分 / combo） |
| `gameOver` | — | Game | 全部（重置） |
| `spawn` | — | Game | Obstacle / Coin |

### 4.3 碰撞与状态机

- `Player` 每帧检测 `touching("Obstacle")` → 触发 `hit`；
- 状态机：`menu` → `playing` → `dead` → `menu`；
- 无敌帧：受击后短暂闪烁、免伤。

## 5. 素材管线

- **来源**：XBuilder 内置「AI 生成」 + 简单 SVG 色块；或 Kenney CC0 素材包；
- **格式**：PNG（角色 / 障碍 / 金币）、SVG（背景 / 地面）、MP3/WAV（音效）；
- **规范**：统一 1x 分辨率、命名 `kebab-case`、在 `assets/index.json` 注册；
- **授权**：所有第三方素材记录在 `docs/ASSETS.md`。

## 6. 仓库结构

```
.
├── README.md
├── ARCHITECTURE.md
├── PLAN.md
├── game/
│   ├── main.spx
│   ├── Player.spx
│   ├── Obstacle.spx
│   ├── Coin.spx
│   ├── Background.spx
│   ├── builder-meta.json
│   └── assets/
├── scripts/
├── docs/
│   ├── GAMEPLAY.md
│   ├── AI_PROCESS.md
│   └── ASSETS.md
└── .github/
    └── PULL_REQUEST_TEMPLATE.md
```

## 7. 模块规格（接口约定）

每个模块以「职责 / 输入 / 输出 / 依赖」描述，详见各 `.spx` 文件头注释。核心约定：

- 精灵只通过 `broadcast` / `onMsg` 通信，不直接跨文件改状态；
- 全局状态只在 `main.spx` 声明，精灵通过 `onMsg` 或共享变量读写；
- 对象池：`Obstacle` / `Coin` 用 `clone` 生成，超出屏幕后 `die` 回收。

## 8. 分工（个人）

| 角色 | 负责内容 |
|---|---|
| 产品设计 | 玩法、数值、关卡节奏、UI/UX |
| 工程实现 | spx 模块开发、性能、Web 构建 |
| 素材 / 美术 | 素材生成 / 整合、视觉风格统一 |
| AI 工程 | 工作流搭建、提示词、过程留痕（`docs/AI_PROCESS.md`） |
| 文档 / 交付 | README、架构、demo 视频、部署 |

## 9. 开发流程

- **分支**：`main` 主干；`feat/*`、`fix/*`、`docs/*`；
- **PR**：每个变更一个 PR，Squash 合并，模板见 `.github/PULL_REQUEST_TEMPLATE.md`；
- **提交**：Conventional Commits（`feat:` / `fix:` / `docs:` / `chore:`）；
- **tag**：`v0`（初始化）→ `v0.1` → …；
- **CI（可选）**：GitHub Actions 跑 `spx` 构建检查。

## 10. AI 辅助工作流

- **工具**：DSH（DeepSeek Harness）+ 两个 skill（`xgo-language`、`spx-project`）+ 本地 `spx run`；
- **标准套路**：
  1. 设计 / 拆模块 →
  2. 本地写 `.spx`（文件工具）→
  3. `spx run` 秒级测试 →
  4. 小步 PR →
  5. 素材经 XBuilder 生成 / 预览；
- **记录**：`docs/AI_PROCESS.md` 记录目标、prompt 要点、产出、效率观察。

## 11. 风险与取舍

| 风险 | 应对 |
|---|---|
| 时间紧（2 天 1 晚） | 砍掉游戏内 AI、多关卡、联网排行；聚焦无限跑酷 |
| 素材制作耗时 | CC0 素材 / AI 生成，零手绘 |
| Web 构建不确定 | Day 2 提前验证 `spx buildweb` |
| 部署失败 | 本地演示兜底 + GitHub Pages |

## 12. 版本记录

| 版本 | 日期 | 内容 |
|---|---|---|
| v0 | 2026-10-24 | 仓库初始化、结构、文档骨架 |
