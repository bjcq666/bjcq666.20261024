#!/usr/bin/env python3
"""Import approved frames, tint #FF0263 and normalize jump facing; preserve alpha.
Uses the generated offline preview; no third-party Python dependencies.
"""
from pathlib import Path
import base64,json,runpy
transform = runpy.run_path(str(Path(__file__).with_name('tint-stickman-png.py')))['transform']
ROOT=Path(__file__).resolve().parents[1]

if __name__=='__main__':
    html=(ROOT/'previews/stickman-preview.html').read_text()
    data=json.loads(html.split('const data=',1)[1].split(';\nlet elapsed=',1)[0])
    out=ROOT/'game/assets/sprites/Player/imported';out.mkdir(parents=True,exist_ok=True)
    paths={};costumes=[]
    for key,uri in data['images'].items():
        name=Path(key).stem
        # Jump source faces opposite to Idle/Run; normalize only those frames.
        blob = transform(base64.b64decode(uri.split(',',1)[1]), mirror=name.startswith('Jump--'))
        (out/(name+'.png')).write_bytes(blob)
        paths[key]=len(costumes)
        costumes.append(dict(name=name,path='imported/'+name+'.png',x=240,y=260,bitmapResolution=1,faceRight=0,imageWidth=480,imageHeight=270))
    cfgpath=ROOT/'game/assets/sprites/Player/index.json';cfg=json.loads(cfgpath.read_text());cfg.update(size=0.48,costumeIndex=0,costumes=costumes)
    cfgpath.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    timelines={}
    for name in ('Idle','Move'):
        clip=data['clips'][name];frames=clip['frames'];samples=[]
        for i in range(round(clip['duration']*50)):
            t=i/50;f=frames[0]
            for entry in frames:
                if entry['time']<=t:f=entry
            samples.append(paths[f['image']])
        timelines[name]=samples
    timelines['Jump']=[paths[f['image']] for f in data['clips']['JumpContinuous']['frames']]
    (ROOT/'scripts/stickman-timelines.json').write_text(json.dumps(timelines,indent=2)+'\n')
    print('Imported',len(costumes),'#FF0263 costumes (jump mirrored); bytes',sum(p.stat().st_size for p in out.glob('*.png')))
