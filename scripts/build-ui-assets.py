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
# Text kept ASCII for deterministic SVG rasterization; numbers remain engine Monitors.
costumes=[]
for hp in range(101):
 b='<rect width="320" height="96" rx="10" fill="#101827" fill-opacity=".9"/>'
 b+=f'<rect x="16" y="28" width="280" height="8" rx="4" fill="#344357"/><rect x="16" y="28" width="{2.8*hp}" height="8" rx="4" fill="#ff0263"/>'
 b+=f'<g font-family="sans-serif" font-size="11" fill="#d8e4f1"><text x="16" y="19">HP {hp} / 100</text><text x="16" y="57">SCORE</text><text x="110" y="57">TIME / s</text><text x="200" y="57">DIST / 6000</text></g>'
 costumes.append((str(hp),svg(320,96,b)))
save('HUDPanel',costumes,320,96,(0,0))
save('ScreenDim',[('dim',svg(1200,900,'<rect width="1200" height="900" fill="#000"/>'))],1200,900,(600,450))
for name,title,sub,hint in [('Start','NEON DASH','SPACE / CLICK TO START','ARROWS TO MOVE  |  SPACE / UP DOUBLE JUMP'),('Pause','PAUSED','ESC TO CONTINUE','Q TO MAIN MENU'),('Gameover','RESULTS','R TO RESTART','M TO MAIN MENU')]:
 b=f'<rect x="20" y="20" width="440" height="260" rx="18" fill="#142236" fill-opacity=".96" stroke="#3e566f"/><g text-anchor="middle" font-family="sans-serif" fill="#e9f0f9"><text x="240" y="100" font-size="34" font-weight="bold">{title}</text><text x="240" y="166" font-size="18" fill="#ff0263">{sub}</text><text x="240" y="220" font-size="12" fill="#aabdd2">{hint}</text></g>'
 save(name,[('panel',svg(480,300,b))],480,300,(240,150))
print('Generated 101 health values, screen dimmer and transparent menu panels.')
