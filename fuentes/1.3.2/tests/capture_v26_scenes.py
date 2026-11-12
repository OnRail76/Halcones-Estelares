#!/usr/bin/env python3
"""Capture unchanged native video memory after executing real assembled Z80.
No Photoshop/model-generated frames; 3x nearest-neighbour enlargement only.
"""
from pathlib import Path
from PIL import Image
from mini_z80 import VM,SYM
from boot_v15 import boot_to_game
R=Path(__file__).resolve().parents[1]

def tick(v):
    v.keys=set();v.step();v.run_to(lambda q:q.pc==SYM['main_loop'],steps=2600000)
    assert v.sp==0xfff0

# All six survivors gathered above the ESF: freeze and sway as one living squad.
v=boot_to_game(VM());v.set('wave_stage',2);v.set('wave_done',0)
for i in range(6):
    off=SYM['wave_rush']+i*6;slot=SYM['enemy_slots']+i*6
    v.m[slot:slot+6]=v.m[off:off+6]
    v.m[slot+2]=5
    v.m[slot+1]=5+(i%3)*9
v.set('shield_invulnerable',0)
for _ in range(19):tick(v)
assert v.val('rush_rest_ticks')==100
v.render(R/'build/V26_KAMIKAZES_EN_REPOSO_Z80.png',scale=3)
assert any(v.m[SYM['enemy_bullet_slots']+i*3+2] for i in range(3)), 'Idle birds must shoot'

# Four successive light states from real engine, not simulated pixel mockups.
v=boot_to_game(VM())
led_frames=[]
for t in range(4):
    for _ in range(8):tick(v)
    fn=R/f'build/V26_LEDS_{t+1}.png'
    v.render(fn,scale=3)
    led_frames.append(Image.open(fn).convert('RGB'))
# note one image every 8 ticks; GIF can loop over actual render captures.
led_frames[0].save(R/'build/V26_LEDS_RECORRIDO.gif',save_all=True,append_images=led_frames[1:],duration=320,loop=0,optimize=False)

# MOAI magenta with bright red eyes on the exact native screen.
v=boot_to_game(VM())
for stage,repeat in [(0,1),(1,0),(1,1),(2,0),(2,1),(3,0)]:
    for i in range(6):v.m[SYM['enemy_slots']+6*i+2]=0
    v.set('wave_done',1);tick(v)
assert v.val('wave_stage')==3
v.set('frame_index',0)
tick(v)
assert v.m[0x586a]==0x42 and v.m[0x586d]==0x42
v.render(R/'build/V26_MOAI_MAGENTA_ROJO_Z80.png',scale=3)
print('PASS screenshot captures from Z80 execution: regroup, three LEDs and magenta boss.')
