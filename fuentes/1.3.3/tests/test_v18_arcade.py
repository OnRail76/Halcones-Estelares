#!/usr/bin/env python3
"""Exercise actual V1.8 Z80 bytes in the partial VM; not a Fuse timing claim."""
from pathlib import Path
from mini_z80 import VM,SYM
from boot_v15 import boot_to_game
R=Path(__file__).resolve().parents[1]
v=boot_to_game(VM())

def tick(keys=()):
    v.keys=set(keys)
    v.step()
    v.run_to(lambda q:q.pc==SYM['main_loop'],steps=950_000)
    assert v.sp==0xfff0, f'stack changed: {v.sp:04x}'
    assert v.m[0xf000]==0xa5 and v.m[0xfdfa]==0x5a and v.m[0xff01]==0x5a and v.m[0xf400]==0x3c

def irq():
    """Inject one IM2 IRQ and execute its real Z80 handler to RETI."""
    pc=v.pc;sp=v.sp;regs=tuple(v.r);f=v.f;ix=v.ix;iy=v.iy
    v.push(pc);v.pc=0xfdfd
    v.run_to(lambda q:q.pc==pc and q.sp==sp,steps=100000)  # V1.3: puede tocar el trozo de sonido de mitad de tick
    assert tuple(v.r)==regs and v.f==f and v.ix==ix and v.iy==iy,'ISR clobbered registers'

assert v.val('ship_y')==152
assert v.val('shield_state')==0 and v.val('shield_meter')==8
tick(['Q']);tick(['Q','A']);assert v.val('ship_y')==152 and v.val('shield_state')==1
assert v.val('shield_meter')==0 and v.val('shield_meter_displayed')==0
# A held for several ticks cannot consume multiple activations.
for _ in range(3):tick(['A'])
assert v.val('shield_state')==1
# SPACE while protected cannot fire, and an approaching enemy projectile is absorbed.
v.keys=set();tick();tick(['SPACE']);assert not any(v.m[SYM['bullet_slots']+3*j+2] for j in range(2))
shoot=SYM['enemy_bullet_slots'];v.m[shoot:shoot+3]=bytes([v.val('ship_x')+8,149,1])
life_before=v.val('player_lives');tick();assert v.m[shoot+2]==0 and v.val('player_lives')==life_before
# Shield contact kills a bird, increments points without removing player lives.
a=SYM['enemy_slots'];phase=(v.val('frame_index')+1)&63;offset=v.m[SYM['wave_sinus']+phase];v.m[a:a+6]=bytes([v.val('ship_x')+2,146,1,0,(v.val('ship_x')-offset)&255,0]);old=v.val('kills');lives=v.val('player_lives')
tick(['A']);assert v.val('kills')>=old+1 and v.val('player_lives')==lives
# Timing driven only by 50Hz IRQ, independent of graphics ticks.
for _ in range(149):irq()
assert v.val('shield_state')==1
irq();assert v.val('shield_state')==2 and v.val('shield_meter')==0
for _ in range(37):irq()
assert v.val('shield_meter')==0
irq();assert v.val('shield_meter')==1
# Cannot activate mid-recharge even after releasing and pressing A again.
tick();tick(['A']);assert v.val('shield_state')==2
for _ in range(262):irq()
assert v.val('shield_state')==0 and v.val('shield_meter')==8
# Must release before a new press is accepted.
tick(['A']);assert v.val('shield_state')==0
tick();tick(['A']);assert v.val('shield_state')==1
v.render(R/'build/V18_ESCUDO_REAL_Z80.png',scale=3)
# Quit shield and stop recharging to force a legal unprotected collision.
v.set('shield_state',0);v.set('shield_key_held',0)
# V1.1: la caja de choque es la silueta (no 24x24): el pajaro se coloca con la
# formula real del vuelo en formacion (fase = (frame_index+1)>>2) para que toque.
a=SYM['enemy_slots'];phase=((v.val('frame_index')+1)>>2)&63;offset=v.m[SYM['wave_sinus']+phase];v.m[a:a+6]=bytes([v.val('ship_x')+2,144,1,0,(v.val('ship_x')+2-offset)&255,0]);life=v.val('player_lives')
tick();assert v.val('player_lives')==life-1, (life,v.val('player_lives'))
assert v.val('lives_displayed')==v.val('player_lives')
assert v.val('ship_y')==152
for t in range(80):tick(['O'] if t%20<10 else ['P'] if t%20<16 else ['SPACE'] if t%20==17 else [])
v.render(R/'build/V18_COMBATE_REAL_Z80.png',scale=3)
print('PASS horizontal-only, edge-triggered A/SPACE, enemy shield destruction, enemy collision loses life')
print('PASS 150 real IRQ for active, 300 IRQ to recharge, eight meter segments, balanced IM2 SP/registers')
print('PASS 80 additional combat updates, GUARDS and HUD intact, actual Z80 native framebuffer images')
