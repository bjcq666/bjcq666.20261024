#!/usr/bin/env python3
"""Generate flat HUD health-bar costumes and transparent menu panels."""
from pathlib import Path
import json
import re
# Small deterministic vector alphabet: SVG paths, no runtime font dependency.
GLYPHS = dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', [
'01110/10001/10001/11111/10001/10001/10001','11110/10001/10001/11110/10001/10001/11110','01111/10000/10000/10000/10000/10000/01111','11110/10001/10001/10001/10001/10001/11110','11111/10000/10000/11110/10000/10000/11111','11111/10000/10000/11110/10000/10000/10000','01111/10000/10000/10111/10001/10001/01111','10001/10001/10001/11111/10001/10001/10001','11111/00100/00100/00100/00100/00100/11111','00111/00010/00010/00010/10010/10010/01100','10001/10010/10100/11000/10100/10010/10001','10000/10000/10000/10000/10000/10000/11111','10001/11011/10101/10101/10001/10001/10001','10001/11001/10101/10011/10001/10001/10001','01110/10001/10001/10001/10001/10001/01110','11110/10001/10001/11110/10000/10000/10000','01110/10001/10001/10001/10101/10010/01101','11110/10001/10001/11110/10100/10010/10001','01111/10000/10000/01110/00001/00001/11110','11111/00100/00100/00100/00100/00100/00100','10001/10001/10001/10001/10001/10001/01110','10001/10001/10001/10001/10001/01010/00100','10001/10001/10001/10101/10101/10101/01010','10001/10001/01010/00100/01010/10001/10001','10001/10001/01010/00100/00100/00100/00100','11111/00001/00010/00100/01000/10000/11111',
'01110/10001/10011/10101/11001/10001/01110','00100/01100/00100/00100/00100/00100/01110','01110/10001/00001/00010/00100/01000/11111','11110/00001/00001/01110/00001/00001/11110','00010/00110/01010/10010/11111/00010/00010','11111/10000/10000/11110/00001/00001/11110','01110/10000/10000/11110/10001/10001/01110','11111/00001/00010/00100/01000/01000/01000','01110/10001/10001/01110/10001/10001/01110','01110/10001/10001/01111/00001/00001/01110']))
GLYPHS.update({'/':'00001/00010/00010/00100/01000/01000/10000','|':'00100/00100/00100/00100/00100/00100/00100',' ':'00000/00000/00000/00000/00000/00000/00000'})
def outline_text(body):
 def replace(m):
  attrs,text=m.group(1),m.group(2).upper();x=float(re.search(r'x="([\d.]+)"',attrs)[1]);y=float(re.search(r'y="([\d.]+)"',attrs)[1]);sz=re.search(r'font-size="([\d.]+)"',attrs);scale=float(sz[1]) / 7 if sz else 11/7
  color=re.search(r'fill="([^"]+)"',attrs);color=color[1] if color else '#d8e4f1'
  if 'text-anchor="middle"' in body:x-=len(text)*6*scale/2
  paths=[]
  for ch in text:
   for row,bits in enumerate(GLYPHS.get(ch,GLYPHS[' ']).split('/')):
    for col,v in enumerate(bits):
     if v=='1':paths.append(f'M{x+col*scale:.2f},{y-7*scale+row*scale:.2f}h{scale:.2f}v{scale:.2f}h-{scale:.2f}z')
   x+=6*scale
  return '<path fill="'+color+'" d="'+' '.join(paths)+'"/>'
 return re.sub(r'<text([^>]*)>([^<]*)</text>',replace,body)
R=Path(__file__).resolve().parents[1]/'game/assets/sprites'
def save(name,costumes,w,h,pivot):
 p=R/name;p.mkdir(parents=True,exist_ok=True)
 c=dict(heading=90,x=0,y=0,size=1,rotationStyle='normal',physicsMode='no',visible=False,costumeIndex=0,costumes=[])
 for title,svg in costumes:
  (p/(title+'.svg')).write_text(outline_text(svg))
  c['costumes'].append(dict(name=title,path=title+'.svg',x=pivot[0],y=pivot[1],bitmapResolution=1,imageWidth=w,imageHeight=h))
 (p/'index.json').write_text(json.dumps(c,indent=2)+'\n')
def svg(w,h,body):return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'
# 说明：血量 HUD 现在是 Hud.spx 的暗角（scripts/build-hud.py 生成），
# 这里只负责「转场遮罩」和「三块菜单面板」。

VEIL_W, VEIL_H = 2600, 1800
veil = f'''<defs>
<linearGradient id="sky" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="#0c1a2e"/>
<stop offset="0.42" stop-color="#091524"/>
<stop offset="0.78" stop-color="#060d18"/>
<stop offset="1" stop-color="#03070e"/>
</linearGradient>
<radialGradient id="halo" cx="16%" cy="50%" r="46%">
<stop offset="0" stop-color="#3fe0f0" stop-opacity="0.12"/>
<stop offset="1" stop-color="#3fe0f0" stop-opacity="0"/>
</radialGradient>
<radialGradient id="glow" cx="84%" cy="54%" r="50%">
<stop offset="0" stop-color="#ff0263" stop-opacity="0.16"/>
<stop offset="0.55" stop-color="#ff0263" stop-opacity="0.06"/>
<stop offset="1" stop-color="#ff0263" stop-opacity="0"/>
</radialGradient>
</defs>
<polygon points="-600,0 3200,0 2900,1800 -900,1800" fill="url(#sky)"/>
<polygon points="-600,0 3200,0 2900,1800 -900,1800" fill="url(#halo)"/>
<polygon points="-600,0 3200,0 2900,1800 -900,1800" fill="url(#glow)"/>
<g opacity="0.35">
<rect x="-600" y="1712" width="3800" height="2" fill="#3fe0f0" fill-opacity="0.18"/>
<rect x="-600" y="88" width="3800" height="2" fill="#ff0263" fill-opacity="0.14"/>
</g>'''
save('ScreenDim',[('dim',svg(VEIL_W,VEIL_H,veil))],VEIL_W,VEIL_H,(VEIL_W/2,VEIL_H/2))

# 三块面板合成一个 Menu 精灵（造型区分），和 Menu.spx 一致
panel_costumes=[]
for name,title,sub,hint in [('start','NEON PARKOUR','SPACE / CLICK TO START','ARROWS TO MOVE  |  SPACE / UP DOUBLE JUMP'),('pause','PAUSED','ESC TO CONTINUE','Q TO MAIN MENU'),('gameover','RESULTS','R TO RESTART','M TO MAIN MENU')]:
 b=f'<rect x="20" y="20" width="440" height="260" rx="18" fill="#142236" fill-opacity=".96" stroke="#3e566f"/><g text-anchor="middle" font-family="sans-serif" fill="#e9f0f9"><text x="240" y="100" font-size="34" font-weight="bold">{title}</text><text x="240" y="166" font-size="18" fill="#ff0263">{sub}</text><text x="240" y="220" font-size="12" fill="#aabdd2">{hint}</text></g>'
 panel_costumes.append((name,svg(480,300,b)))
save('Menu',panel_costumes,480,300,(240,150))
print('Generated the gradient veil and the three Menu panels.')
