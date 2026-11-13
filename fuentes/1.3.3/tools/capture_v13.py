#!/usr/bin/env python3
"""Produce only executed-Z80-memory captures, NOT illustration or Fuse timings."""
from pathlib import Path
import sys
from PIL import Image
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from mini_z80 import VM,SYM
v=VM();v.run_to(lambda x:x.pc==SYM['main_loop'],steps=900_000)
frames=[]
for t in range(1,81):
    controls={'SPACE'} if t%6==1 else set()
    if t%64<14:controls.add('P')
    elif t%64<28:controls.add('O')
    elif t%64<40:controls.add('Q')
    elif t%64<52:controls.add('A')
    v.keys=controls
    v.step();v.run_to(lambda q:q.pc==SYM['main_loop'],steps=700_000)
    if t in (10,30,50,75):v.render(R/f'build/ESF_V13_REAL_{t:03}.png',scale=3)
    if t%4==0:
        # 4 Z80 updates per GIF frame; the GIF delay does not claim real emulator speed.
        p=R/f'build/_anim_v13_{t:03}.png';v.render(p,scale=2)
        frames.append(Image.open(p).convert('P',palette=Image.Palette.ADAPTIVE,colors=16))
frames[0].save(R/'build/ESF_V13_ESTRELLAS_Z80.gif',save_all=True,append_images=frames[1:],duration=170,loop=0,optimize=False)
for p in (R/'build').glob('_anim_v13_*.png'):p.unlink()
print('Rendered 20 animation frames and 4 PNG captures, reading actual Z80 video memory.')
