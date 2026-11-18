#!/usr/bin/env python3
"""Native screenshots from executed Z80 memory (partial interpreter, not Fuse)."""
from pathlib import Path
import sys
from PIL import Image
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from mini_z80 import VM,SYM
v=VM();v.run_to(lambda q:q.pc==SYM['main_loop'],steps=850000)
frames=[]
for t in range(1,61):
 v.keys=({'SPACE'} if t%6==1 else set())|({'P'} if t%36<11 else {'O'} if t%36<22 else set())
 v.step();v.run_to(lambda q:q.pc==SYM['main_loop'],steps=700000)
 if t%4==0:
  p=R/f'build/_preview_native_{t:03}.png'
  v.render(p,scale=2)
  frames.append(Image.open(p).convert('P',palette=Image.Palette.ADAPTIVE,colors=16))
frames[0].save(R/'build/ESF_V12_MOVIMIENTO_Z80.gif',save_all=True,append_images=frames[1:],duration=180,loop=0,optimize=False)
for p in (R/'build').glob('_preview_native_*.png'):p.unlink()
print('GIF built from 15 executed Z80 memory frames. This is NOT Fuse performance evidence.')
