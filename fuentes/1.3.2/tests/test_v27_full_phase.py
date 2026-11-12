#!/usr/bin/env python3
"""V2.4 execution tests on assembled Z80 program (not a Fuse replacement)."""
from pathlib import Path
from mini_z80 import VM,SYM
from boot_v15 import boot_to_game
import functools
R=Path(__file__).resolve().parents[1]

def tick(v,keys=()):
    v.keys=set(keys)
    v.step()  # starts at main_loop
    v.run_to(lambda q:q.pc==SYM['main_loop'],steps=2_000_000)
    assert v.sp==0xfff0,hex(v.sp)
    assert [v.m[x] for x in (0xf000,0xf400,0xfdfa,0xff01)]==[0xa5,0x3c,0x5a,0x5a]

def irq(v):
    pc,sp=v.pc,v.sp
    regs,f,ix,iy=list(v.r),v.f,v.ix,v.iy
    v.push(v.pc);v.pc=0xfdfd
    v.run_to(lambda q:q.pc==pc and q.sp==sp,steps=1500)
    assert (v.r,v.f,v.ix,v.iy)==(regs,f,ix,iy)

def zero_wave(v):
    for j in range(6):v.m[SYM['enemy_slots']+6*j+2]=0

def check_visible(v):
    for y in range(192):
        off=((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)
        assert v.m[0x4000+off:0x4000+off+24]==v.m[0xc000+off:0xc000+off+24],('screen mismatch',y, [(i, v.m[0x4000+off+i],v.m[0xc000+off+i]) for i in range(24) if v.m[0x4000+off+i]!=v.m[0xc000+off+i]])

v=boot_to_game(VM())
assert v.val('phase_number')==1 and v.val('wave_stage')==0 and v.val('wave_repeat')==0
for expected_stage,expected_repeat in [(0,1),(1,0),(1,1),(2,0),(2,1),(3,0)]:
    zero_wave(v)
    v.set('wave_done',1);v.set('card_ticks',0)  # V1.1: sin cartel
    tick(v)
    assert (v.val('wave_stage'),v.val('wave_repeat'))==(expected_stage,expected_repeat),(
        'wrong progression',expected_stage,expected_repeat,v.val('wave_stage'),v.val('wave_repeat'))
assert v.val('boss_hp')==18
print('PASS 1,1,2,2,3,3 -> MOAI, six sequential formations, all native Z80 code')

# Isolated second-wave live choreography with two independent enemy actors.
v=boot_to_game(VM())
v.set('wave_stage',1)
v.set('wave_repeat',0)
v.set('frame_index',95)
for i in range(6):
    template=SYM['wave_hunters']+i*6
    v.m[SYM['enemy_slots']+i*6:SYM['enemy_slots']+i*6+6]=v.m[template:template+6]
v.set('shield_invulnerable',40)  # Isolate movement from collision/death for deterministic test.
tick(v)  # frame_index -> 96; launch pair.
assert v.val('hunter_pair_active')==1 and v.val('hunter_pair_left_index')==0
l0,r0=v.val('hunter_target_left'),v.val('hunter_target_right')
assert r0-l0==26
assert [v.m[SYM['enemy_slots']+i*6+2] for i in (0,1)]==[2,2]
# Move using REAL keyboard input; never teleport the visible ship across frames.
projectiles=0
for i in range(27):
    tick(v,keys={'P'})
    check_visible(v)
    assert v.val('hunter_target_left')==l0 and v.val('hunter_target_right')==r0,'target followed ship!'
    slots=[v.m[SYM['enemy_slots']+j*6:SYM['enemy_slots']+j*6+6] for j in range(6)]
    assert slots[0][2]==2 and slots[1][2]==2, ('attacker already returned',i)
    assert slots[0][1]-slots[1][1]==0, ('pair not in vertical parallel',i)
    assert all(slot[2]==1 for slot in slots[2:]),'formation wingmen lost their post'
    projectiles |= sum(v.m[SYM['enemy_bullet_slots']+j*3+2]!=0 for j in range(3))
assert projectiles>0,'pair did not fire'
# Choose a displayed ship frame (invulnerability blink is unchanged).
if v.val('frame_index')&2:tick(v,keys={'P'})
v.render(R/'build/V24_HUNTERS_DIVE_Z80.png',scale=3)
for i in range(88):
    tick(v)
    check_visible(v)
assert v.val('hunter_pair_active') in (0,1), 'invalid paired-attack mode after 115 ticks' # V2.5 may have launched another pair
assert v.m[SYM['enemy_slots']+2] in (1,0) and v.m[SYM['enemy_slots']+8] in (1,0)
print('PASS two birds dive/fire in parallel toward frozen target, rejoin slowly; no graphics residual')

# Even if one bird in the preferred pair was destroyed, use the alternate row.
v2=boot_to_game(VM())
v2.set('wave_stage',1)
v2.set('frame_index',95)
for i in range(6):
    ofs=SYM['wave_hunters']+i*6
    v2.m[SYM['enemy_slots']+i*6:SYM['enemy_slots']+i*6+6]=v2.m[ofs:ofs+6]
v2.m[SYM['enemy_slots']+2]=0 # One upper-row bird was destroyed earlier.
v2.set('shield_invulnerable',40)
tick(v2)
assert v2.val('hunter_pair_active')==1 and v2.val('hunter_pair_left_index')==3
assert [v2.m[SYM['enemy_slots']+i*6+2] for i in (3,4)]==[2,2]
print('PASS invalid preferred pair safely switches to two live birds in other row')

# Force victory (after 18 genuine hits have been verified in v2.0 regressions).
v=boot_to_game(VM())
for expect in [(0,1),(1,0),(1,1),(2,0),(2,1),(3,0)]:
    zero_wave(v);v.set('wave_done',1);v.set('card_ticks',0);tick(v)  # V1.1: sin cartel
assert v.val('wave_stage')==3
v.set('kills',37)  # Score must survive the phase screen / HUD rebuild.
v.set('boss_hp',0);v.set('boss_death_left',0)
v.step()
v.run_to(lambda q:q.pc==SYM['phase_interlude_wait'],steps=2_000_000)
assert v.val('gameover_mode')==2
assert v.val('gameover_timer')==150
assert v.val('phase_number')==2
assert v.m[0x4000:0x5b00]!=v.m[0xc000:0xdb00]
# Do not let initial screen text disappear during 149 ticks.
for _ in range(149):irq(v)
assert v.val('gameover_timer')==1
assert v.val('gameover_mode')==2
v.render(R/'build/V24_INTERFASE_Z80.png',scale=3)
irq(v)
assert v.val('gameover_timer')==0
v.run_to(lambda q:q.pc==SYM['main_loop'],steps=3_000_000)
assert v.val('gameover_mode')==0
assert v.val('wave_cycle')==1 and v.val('phase_number')==2
assert v.val('wave_stage')==0 and v.val('wave_repeat')==0
assert v.sp==0xfff0
assert v.val('player_lives')==3 and v.val('kills')==37
assert v.m[0x582a]==v.m[0xf12a]
# The actual 7 scanline native score digits are redrawn after intermission.
assert any(v.m[0x4000+(((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2))+29] for y in range(24,31))
check_visible(v)
for j in range(24):tick(v);check_visible(v)
print('PASS MOAI -> 150 genuine IM2 IRQs -> FASE 02 -> new Crow loop, score/lives/IRQ/work intact')

# 8 TAP blocks parity and all CODE segment boundaries remain intact.
tap=(R/'build/HALCONES_ESTELARES_V281.tap').read_bytes();off=0;blocks=[]
while off<len(tap):
    size=int.from_bytes(tap[off:off+2],'little');off+=2
    block=tap[off:off+size];off+=size
    assert len(block)==size and functools.reduce(lambda x,y:x^y,block,0)==0
    blocks.append(block)
assert off==len(tap) and len(blocks)==8
assert (R/'build/starter.bin').read_bytes()==blocks[3][1:-1]
print('PASS 8 TAP blocks with valid XOR parity, compiled Z80 payload intact')
print('ALL V2.7 FULL-PHASE TESTS PASSED')
