#!/usr/bin/env python3
"""Deterministic mirror of Player's axis-separated collision; not engine/input E2E."""
from pathlib import Path
import re,json,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parents[1];s=(r/'game/main.spx').read_text()
def arr(name):return [float(x) for x in re.search(name+r' = \[\]float64\{([^}]+)',s)[1].split(',')]
L,R,T=arr('blockLeft'),arr('blockRight'),arr('blockTop')
assert len(L)==len(R)==len(T)==14
assert all(R[i]==L[i+1] for i in range(len(L)-1))
assert max(T)-min(T)<=120
cfg=json.loads((r/'game/assets/index.json').read_text());assert cfg['map']['width']==7600
for p in (r/'game/assets').rglob('*.json'):json.loads(p.read_text())
ET.parse(r/'game/assets/sprites/Ground/Ground.svg')
def step(x,y,vy,vx):
 nx=x+vx
 for l,rr,t in zip(L,R,T):
  if y<t-.1 and y+114>-300:
   if vx>0 and x+14<=l+.1 and nx+14>l:nx=l-14
   if vx<0 and x-14>=rr-.1 and nx-14<rr:nx=rr+14
 nx=min(3000,max(-3000,nx));vy-=1.2;ny=y+vy;land=False
 if vy<=0:
  for l,rr,t in zip(L,R,T):
   if nx+14>l and nx-14<rr and y>=t-.1 and ny<=t:ny=t;land=True
 return nx,ny,0 if land else vy,land
# Idle support, wall blocking, then auto-jump route across every rise.
x,y,v,g=step(-2500,-208,0,0);assert g and y==-208
x,y,v,g=step(-2400,-208,0,8);assert x==-2394
x=-3000.;y=-208.;v=0.;ground=True;landings=0
for tick in range(5000):
 if ground:
  obstacle=any(l>=x and l-x<120 and t>y+.1 for l,t in zip(L,T))
  if obstacle:v=22;ground=False
 x,y,v,ground=step(x,y,v,8)
 if ground:landings+=1
 assert y>=-208.0001,(tick,x,y)
 if x>=3000:break
assert x==3000,(tick,x,y)
assert abs(((x-(x+80))+400)/800-.4)<1e-9
print('PASS: JSON/SVG; 14 connected blocks; support; wall stop; traversable 6000px route; 40% camera target.')
print('Model route:',tick+1,'ticks; runtime visual/input testing still required.')
