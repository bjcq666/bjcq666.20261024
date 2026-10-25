# TheRealGi 角色本地接入记录

- 来源：https://therealgi.itch.io/2d-stickman-character
- 输入：用户提供的 Stickman Basic Pack；由预览生成器读取 Unity anim/meta 并缩图。
- 转换：`python3 scripts/import-stickman.py`，从预览提取 PNG，保留 alpha，统一 RGB(255,2,99)，单独镜像跳跃帧修正朝向。输出 70 个造型约 547 KiB。原素材不修改。
- 游戏造型：480×270 全画布，统一锚点 (240,260)，size=0.48；站立可见高度约 119px。未逐帧裁剪，跳跃片段位置仍待实玩校准。
- Idle/Move 按作者时间采样到 50Hz。跳跃按物理状态拆为飞行源帧 1..21、静止落地源帧 22..40；移动落地直接进入跑步，不强制停顿。
- 左右方向用 heading + left-right 镜像。空中无方向输入保留 vx，地面无输入停止。
- 下蹲已移除。旧 SVG 仍在本地但不再注册。
- 当前仍是平地 y 钳制，不是矩形地形碰撞；新 PNG 不含旧 SVG 蓝色框。
- 验证：素材引用校验与 20 秒 headless 启动通过，不代表所有输入、朝向和动画衔接已实测。
- 授权：包内未发现许可证；未推送第三方 PNG。公开 GitHub 前确认素材再分发许可。
