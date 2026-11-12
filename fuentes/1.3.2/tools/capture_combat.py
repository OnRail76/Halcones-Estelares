#!/usr/bin/env python3
"""Capture the *executed* Z80 RAM, never synthesize game imagery or mockups.
Partial interpreter captures are functional visualization, not Fuse or ULA timing.
"""
from pathlib import Path
import sys
from PIL import Image
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from mini_z80 import VM,SYM
v=VM();v.run_to(lambda q:q.pc==SYM['main_loop'],steps=850000)
frames=[]
for i in range(1,61):
 v.keys={'SPACE'}
 v.step()
 v.run_to(lambda q:q.pc==SYM['main_loop'],steps=200000)
 if i%4==0:
  fn=R/f'build/COMBAT_GIF_{i:03d}.png'
  v.render(fn,scale=2)
  frames.append(Image.open(fn).convert('P',palette=Image.Palette.ADAPTIVE,colors=16))
assert len(frames)==15
frames[0].save(R/'build/ESF_COMBATE_REAL_Z80.gif',save_all=True,append_images=frames[1:],duration=230,loop=0,optimize=False)
# Four stills are images of literal executed Z80 memory; no synthetic pixel layers.
print('CAPTURE:',len(frames),'real-VM frames, animated GIF (no mockup).')
