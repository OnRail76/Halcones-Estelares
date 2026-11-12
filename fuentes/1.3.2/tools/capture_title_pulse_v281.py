#!/usr/bin/env python3
"""Capture genuine assembled-Z80 framebuffer states and export an animated GIF."""
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tests'))
from mini_z80 import VM,SYM
from PIL import Image
v=VM()
v.run_to(lambda q:q.pc==SYM['title_wait_release'],steps=1_000_000)
v.keys=set()
v.run_to(lambda q:q.pc==SYM['title_wait_press'],steps=10000)
shots=[];names=['AMARILLO_ORIGINAL','DESTELLO_1_BLANCO','AMARILLO_RESTAURADO','DESTELLO_2_BLANCO']
for i,(skip,name) in enumerate(zip([0,75,6,9],names)):
    for _ in range(skip):
        v.step();v.run_to(lambda q:q.pc==SYM['title_wait_press'],steps=15000)
    png=R/f'build/V281_PULSO_{name}.png'
    v.render(png,scale=3)
    img=Image.open(png).convert('RGB')
    shots.append(img)
    print(name, 'phase',v.m[SYM['title_pulse_phase']])
assert all(x.size==(768,576) for x in shots)
shots[0].save(R/'build/HALCONES_V281_PULSO_ARCADE_REAL_Z80.gif', save_all=True,append_images=shots[1:],duration=[1500,120,180,60],loop=0,optimize=False)
print('Pulse GIF rendered only from actual simulated Z80 VRAM (no generated mockups)')
