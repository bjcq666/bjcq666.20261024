"""HUD 血量暗角：11 张造型（0%..100%，10% 一档）。

血量越低，四周的品红暗角越浓。为什么不用血条：血条是"小而静止"的图形，
世界坐标转屏幕时那 1~2px 的相位差会非常刺眼；暗角是全屏均匀渐变，同样幅度的
抖动完全看不出来（实测结论见 docs/UI.md）。

渐变方向与转场遮罩一致（左亮右暗），和"向右奔跑"的镜头方向呼应。
"""
import os

W, H = 1600, 1200
OUT = os.path.join(os.path.dirname(__file__), "..", "game", "assets", "sprites", "Hud")


def vignette(k):
    """k = 0..10，血量档位；k=10 表示满血（完全透明）。"""
    alpha = 0.0 if k >= 10 else 0.92 * ((10 - k) / 10.0) ** 0.7
    inner = 18 + k * 2.4
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><radialGradient id="v" cx="50%" cy="50%" r="72%">
<stop offset="{inner:.0f}%" stop-color="#ff0263" stop-opacity="0"/>
<stop offset="100%" stop-color="#ff0263" stop-opacity="{alpha:.3f}"/>
</radialGradient></defs>
<rect width="{W}" height="{H}" fill="url(#v)"/>
</svg>
'''


def main():
    out = os.path.abspath(OUT)
    os.makedirs(out, exist_ok=True)
    for pct in range(0, 101, 10):
        with open(os.path.join(out, f"hp{pct}.svg"), "w") as f:
            f.write(vignette(pct // 10))
    print(f"{out}: 11 costumes (hp0..hp100), {W}x{H}")


if __name__ == "__main__":
    main()
