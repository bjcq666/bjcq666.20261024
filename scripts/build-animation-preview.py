#!/usr/bin/env python3
"""Build a self-contained local preview, preserving Unity sprite timing and canvas.
macOS: python3 scripts/build-animation-preview.py [source-directory]
Uses sips (ships with macOS); never modifies source assets.
"""
from pathlib import Path
import base64
import json
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT.parent / 'Stickman Basic Pack'
OUTPUT = ROOT / 'previews' / 'stickman-preview.html'
CLIPS = ['Idle', 'StartMove', 'Move', 'Jump', 'Air', 'Land']

def extract():
    guids = {}
    for meta in (SOURCE / 'Sprites').rglob('*.png.meta'):
        match = re.search(r'^guid: (\w+)', meta.read_text(), re.M)
        if match:
            guids[match[1]] = Path(str(meta)[:-5])
    clips, images = {}, {}
    with tempfile.TemporaryDirectory() as temp:
        for name in CLIPS:
            text = (SOURCE / 'Animations' / (name + '.anim')).read_text()
            curve = text.split('m_PPtrCurves:', 1)[1].split('attribute: m_Sprite', 1)[0]
            keys = re.findall(r'- time: ([\d.eE+-]+)\s+value: \{fileID: \d+, guid: (\w+)', curve)
            duration = float(re.search(r'm_StopTime: ([\d.eE+-]+)', text)[1])
            frames = []
            for time, guid in keys:
                source = guids[guid]
                key = source.relative_to(SOURCE).as_posix()
                if key not in images:
                    target = Path(temp) / (guid + '.png')
                    subprocess.run(['sips', '-Z', '480', str(source), '--out', str(target)], check=True, stdout=subprocess.DEVNULL)
                    images[key] = 'data:image/png;base64,' + base64.b64encode(target.read_bytes()).decode()
                frames.append({'time': float(time), 'image': key})
            clips[name] = {'duration': duration, 'frames': frames}
        # The Unity Air clip reverses frames 20 -> 17, then Land restarts
        # at frame 20. For a one-shot jump preview, use the continuous source
        # sequence instead: no backtracking, repeated hold, or phase reset.
        jump_sources = sorted((SOURCE / 'Sprites' / 'Jump_Fall PNG').glob('Jump--*.png'),
                              key=lambda p: int(re.search(r'--(\d+)', p.name)[1]))
        frames = []
        for i, source in enumerate(jump_sources):
            key = source.relative_to(SOURCE).as_posix()
            if key not in images:
                target = Path(temp) / ('jump-' + str(i) + '.png')
                subprocess.run(['sips', '-Z', '480', str(source), '--out', str(target)], check=True, stdout=subprocess.DEVNULL)
                images[key] = 'data:image/png;base64,' + base64.b64encode(target.read_bytes()).decode()
            frames.append({'time': i / 30, 'image': key})
        clips['JumpContinuous'] = {'duration': len(frames) / 30, 'frames': frames}
    return {'clips': clips, 'images': images}

TEMPLATE = '''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Neon Dash · 火柴人动画试片</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#101827;color:#e6edf7;font:15px system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:28px}h1{margin:0 0 10px}.muted{color:#a7b6ca;line-height:1.7}nav{display:flex;gap:18px;align-items:center;flex-wrap:wrap;margin:22px 0}button,select{padding:9px 14px;border:1px solid #516981;border-radius:8px;background:#24374b;color:white}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}article{background:#1c2a3b;padding:16px;border-radius:14px}h2{font-size:19px;margin:0 0 8px}.stage{position:relative;height:280px;background:#e8edf1;border-radius:8px;overflow:hidden}.stage:after{content:"";position:absolute;left:0;right:0;top:264px;border-top:1px dashed #678}.stage img{position:absolute;width:480px;height:270px;max-width:none;left:50%;top:4px;transform:translateX(-50%);object-fit:contain}body.dark .stage{background:#182438}body.cyan img{filter:brightness(0) saturate(100%) invert(82%) sepia(83%) saturate(2885%) hue-rotate(135deg) brightness(103%) contrast(104%)}.info{min-height:48px;margin-top:12px;color:#c2d2e5;font:13px monospace}.foot{margin-top:25px}
</style><main>
<h1>火柴人动画试片</h1><div class="muted">仅检查素材动作，不是游戏演示。保留原始画布；待机和跑步使用作者时间，跳跃按连续源帧 30fps 播放，不倒放或重复停帧。下蹲已取消。</div>
<nav><button id="play">暂停</button><button id="reset">从头播放</button><label>速度 <select id="speed"><option value="0.5">0.5× 慢放</option><option value="1" selected>1× 原速</option><option value="1.5">1.5×</option></select></label><label><input id="dark" type="checkbox">深色背景</label><label><input id="cyan" type="checkbox">青色剪影预览</label><label><input id="mirror" type="checkbox">朝向镜像</label></nav>
<section><article><h2>待机</h2><div class="stage"><img id="idle" alt="待机动画"></div><div class="info" id="idle-info"></div></article>
<article><h2>起步 → 跑步循环</h2><div class="stage"><img id="move" alt="起步和跑步动画"></div><div class="info" id="move-info"></div></article>
<article><h2>起跳 → 空中 → 落地</h2><div class="stage"><img id="jump" alt="跳跃各阶段动画"></div><div class="info" id="jump-info"></div></article></section>
<div class="muted foot">虚线是画布参考线，不是碰撞体。跳跃栏只播放原始姿态，没有附加模拟位移；不同片段若出现偏移，接入时需校准锚点。跑步循环保持不变。跳跃使用 Jump--1 至最后一帧连续播放，去掉原空中片段的回放和落地后错误停留；循环末尾到开头仍是预览重播边界。</div>
<p class="muted">来源：<a href="https://therealgi.itch.io/2d-stickman-character">TheRealGi · 2D Stickman Character</a>。用户提供素材，仅本地评估；公开仓库分发前需确认授权。</p><div id="status" role="status">加载图片中…</div>
</main><script>
const data=__DATA__;
let elapsed=0,last=performance.now(),playing=true;
const imageCache=Object.values(data.images).map(src=>{const im=new Image();im.src=src;return im});
Promise.all(imageCache.map(im=>im.decode())).then(()=>document.getElementById('status').textContent=`已加载 ${imageCache.length} 张缩小图片，可离线播放。`).catch(()=>document.getElementById('status').textContent='图片加载失败，请重新生成预览。');
function render(slot,name,t){const c=data.clips[name];let i=0;for(let j=0;j<c.frames.length;j++){if(c.frames[j].time<=t)i=j;else break}const f=c.frames[i],img=document.getElementById(slot);if(img.dataset.key!==f.image){img.src=data.images[f.image];img.dataset.key=f.image}document.getElementById(slot+'-info').textContent=`${name} · ${i+1}/${c.frames.length} 关键帧 · ${Math.min(t,c.duration).toFixed(2)}s / ${c.duration.toFixed(2)}s`;}
function tick(now){if(playing)elapsed+=(now-last)/1000*Number(document.getElementById('speed').value);last=now;
render('idle','Idle',elapsed%data.clips.Idle.duration);
const start=data.clips.StartMove.duration;elapsed<start?render('move','StartMove',elapsed):render('move','Move',(elapsed-start)%data.clips.Move.duration);
render('jump','JumpContinuous',elapsed%data.clips.JumpContinuous.duration);
requestAnimationFrame(tick)}
document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'暂停':'继续'};
document.getElementById('reset').onclick=()=>elapsed=0;
for(const id of ['dark','cyan'])document.getElementById(id).onchange=e=>document.body.classList.toggle(id,e.target.checked);
document.getElementById('mirror').onchange=e=>document.querySelectorAll('.stage img').forEach(im=>im.style.transform=`translateX(-50%) scaleX(${e.target.checked?-1:1})`);
requestAnimationFrame(tick);
</script></html>'''

if __name__ == '__main__':
    data = extract()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(TEMPLATE.replace('__DATA__', json.dumps(data, ensure_ascii=False)))
    print(f'Created {OUTPUT}: {len(data["images"])} unique frames, {OUTPUT.stat().st_size / 1024:.0f} KiB')
